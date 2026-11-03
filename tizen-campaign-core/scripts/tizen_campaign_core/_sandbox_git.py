"""Git process boundary for sandbox submission (P5 section 4.4)."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

OVERRIDES = (
    "core.hooksPath=/dev/null",
    "core.fsmonitor=false",
    "core.askPass=",
    "credential.helper=",
    "push.followTags=false",
    "push.recurseSubmodules=no",
    "push.gpgSign=false",
    "push.pushOption=",
)
UNSAFE_KEYS = (
    r"^(url\..*\.(insteadof|pushinsteadof)|"
    r"core\.(sshcommand|fsmonitor|gitproxy|askpass)|credential\..*|"
    r"filter\..*\.(clean|smudge|process)|diff\.external|"
    r"diff\..*\.(command|textconv)|protocol\..*\.allow)$"
)


@dataclass(frozen=True)
class SandboxGit:
    ssh_command: str = "ssh"
    remote_timeout: int = 300

    def run(
        self,
        cwd: Path | None,
        *args: str,
        check: bool = True,
        remote: bool = False,
        git_dir: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        env.update(
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL="/dev/null",
            GIT_TERMINAL_PROMPT="0",
            GIT_ALLOW_PROTOCOL="file:ssh",
            GIT_SSH_COMMAND=self.ssh_command,
        )
        command = ["git"]
        if cwd is not None:
            command += ["-C", str(cwd)]
        if git_dir is not None:
            command += ["--git-dir=" + str(git_dir)]
        for override in OVERRIDES:
            command += ["-c", override]
        command += list(args)
        if args and args[0] == "diff":
            command[len(command) - len(args) + 1 : len(command) - len(args) + 1] = [
                "--no-ext-diff",
                "--no-textconv",
            ]
        return subprocess.run(
            command,
            env=env,
            check=check,
            capture_output=True,
            text=True,
            timeout=self.remote_timeout if remote else 60,
        )

    def unsafe_reason(self, cwd: Path) -> str | None:
        try:
            version = self.run(None, "--version")
            match = re.match(r"git version (\d+)\.(\d+)(?:\.|\s|$)", version.stdout)
            if match is None or tuple(map(int, match.groups())) < (2, 26):
                return "git version below required 2.26 (or unrecognized version)"
            result = self.run(
                cwd,
                "config",
                "--null",
                "--name-only",
                "--show-scope",
                "--get-regexp",
                UNSAFE_KEYS,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return "git configuration could not be inspected"
        if result.returncode == 1 and not result.stdout:
            return None
        if result.returncode != 0:
            return "git configuration query failed"
        # NUL-delimited scope/key pairs avoid reading or accidentally echoing values.
        if not result.stdout.endswith("\0"):
            return "unparseable git configuration scope"
        fields = result.stdout[:-1].split("\0")
        if len(fields) % 2:
            return "unparseable git configuration scope"
        keys = [fields[i + 1] for i in range(0, len(fields), 2) if fields[i] != "command"]
        return "unsafe git configuration keys: " + ", ".join(sorted(set(keys))) if keys else None

    def clean(self, cwd: Path) -> bool:
        return all(
            self.run(cwd, *args, check=False).returncode == 0
            for args in (
                ("diff", "--quiet", "HEAD", "--"),
                ("diff", "--cached", "--quiet"),
            )
        )
