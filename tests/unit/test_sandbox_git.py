from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from ci_triage._sandbox_git import OVERRIDES, SandboxGit


def repository(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    return tmp_path


def test_fresh_repository_ignores_only_command_overrides(tmp_path: Path) -> None:
    git = SandboxGit()
    assert git.unsafe_reason(repository(tmp_path)) is None
    output = git.run(tmp_path, "config", "--show-scope", "--get-regexp", "core.fsmonitor").stdout
    assert output.split() == ["command", "core.fsmonitor", "false"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("core.fsmonitor", "false"),
        ("credential.helper", ""),
        ("core.sshCommand", "secret value"),
        ("url./tmp/x.pushInsteadOf", "/tmp/y"),
        ("filter.x.clean", "secret value"),
        ("diff.x.textconv", "secret value"),
    ],
)
def test_local_config_rejected_even_when_overridden(tmp_path: Path, key: str, value: str) -> None:
    repository(tmp_path)
    subprocess.run(["git", "-C", str(tmp_path), "config", key, value], check=True)
    reason = SandboxGit().unsafe_reason(tmp_path)
    assert reason is not None and key.lower() in reason.lower()
    assert "secret value" not in reason


def test_include_config_rejected(tmp_path: Path) -> None:
    repository(tmp_path)
    included = tmp_path / "included.conf"
    included.write_text("[core]\n sshCommand = secret value\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "include.path", str(included)], check=True
    )
    reason = SandboxGit().unsafe_reason(tmp_path)
    assert reason is not None and "core.sshcommand" in reason
    assert "secret value" not in reason


def test_multiline_config_value_never_echoed(tmp_path: Path) -> None:
    repository(tmp_path)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "config",
            "credential.helper",
            "first\nlocal secret-credential",
        ],
        check=True,
    )
    assert (
        SandboxGit().unsafe_reason(tmp_path) == "unsafe git configuration keys: credential.helper"
    )


def test_worktree_scope_is_not_exempt(tmp_path: Path) -> None:
    repository(tmp_path)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "extensions.worktreeConfig", "true"], check=True
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "--worktree", "core.fsmonitor", "false"], check=True
    )
    assert SandboxGit().unsafe_reason(tmp_path) == "unsafe git configuration keys: core.fsmonitor"


def test_old_git_rejected_before_scope_query(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    def run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "git version 2.25.9\n", "")

    monkeypatch.setattr(subprocess, "run", run)
    assert "below required 2.26" in str(SandboxGit().unsafe_reason(tmp_path))
    assert len(calls) == 1


def test_every_call_has_isolated_environment_and_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_DIR", "/hostile")
    monkeypatch.setenv("GIT_SSH_COMMAND", "hostile")

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        env = kwargs["env"]
        assert isinstance(env, dict)
        assert "GIT_DIR" not in env
        assert env["GIT_SSH_COMMAND"] == "ssh"
        assert env["GIT_ALLOW_PROTOCOL"] == "file:ssh"
        assert env["GIT_CONFIG_GLOBAL"] == "/dev/null"
        assert env.get("PATH") == os.environ.get("PATH")
        for value in OVERRIDES:
            assert command[command.index(value) - 1] == "-c"
        assert "--no-ext-diff" in command and "--no-textconv" in command
        assert kwargs["timeout"] == 60
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", run)
    assert SandboxGit().clean(Path("/repository"))
