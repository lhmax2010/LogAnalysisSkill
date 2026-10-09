"""Reproduce the frozen configuration-check conflict, without P5 implementation."""

import os
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(
        GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_TERMINAL_PROMPT="0",
        GIT_ALLOW_PROTOCOL="file:ssh", GIT_SSH_COMMAND="ssh",
    )
    overrides = [
        "core.hooksPath=/dev/null", "core.fsmonitor=false", "core.askPass=",
        "credential.helper=", "push.followTags=false", "push.recurseSubmodules=no",
        "push.gpgSign=false", "push.pushOption=",
    ]
    pattern = (
        r"^(url\..*\.(insteadof|pushinsteadof)|core\.(sshcommand|fsmonitor|gitproxy|askpass)"
        r"|credential\..*|filter\..*\.(clean|smudge|process)"
        r"|diff\.(external|.*\.(command|textconv))|protocol\..*\.allow)$"
    )
    with tempfile.TemporaryDirectory(prefix="p5-c4-config-preflight-") as directory:
        root = Path(directory)
        subprocess.run(["git", "init", "-q", str(root)], env=env, check=True)
        prefix = ["git", "-C", str(root)]
        for item in overrides:
            prefix.extend(["-c", item])
        result = subprocess.run(
            prefix + ["config", "--get-regexp", pattern], env=env,
            text=True, capture_output=True, timeout=60,
        )
        print("fresh_local_repository=True")
        print(f"git_config_with_section_4_4_overrides: exit={result.returncode}")
        print(f"stdout={result.stdout!r}")
        print(f"stderr={result.stderr!r}")
        control = subprocess.run(
            ["git", "-C", str(root), "config", "--get-regexp", pattern], env=env,
            text=True, capture_output=True, timeout=60,
        )
        print(f"same_repository_without_command_overrides: exit={control.returncode}")
        print(f"stdout={control.stdout!r}")


if __name__ == "__main__":
    main()
