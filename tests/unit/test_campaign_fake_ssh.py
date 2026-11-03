from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from tizen_campaign_core._sandbox_git import SandboxGit

FAKE = Path(__file__).resolve().parents[1] / "fixtures" / "campaign_fake_ssh.py"


@pytest.fixture
def transport(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    root = tmp_path / "remotes"
    repo = root / "platform/upstream/example"
    repo.parent.mkdir(parents=True)
    subprocess.run(["git", "init", "--bare", str(repo)], check=True, capture_output=True)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    ssh = bindir / "ssh"
    shutil.copyfile(FAKE, ssh)
    ssh.chmod(0o700)
    log = tmp_path / "ssh.jsonl"
    monkeypatch.setenv("PATH", str(bindir) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("SKEL_FAKE_SSH_ROOT", str(root))
    monkeypatch.setenv("SKEL_FAKE_SSH_LOG", str(log))
    return root, repo, log


def test_upload_pack_via_unmodified_sandbox_environment(
    transport: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_SSH_COMMAND", "/must-be-overridden")
    result = SandboxGit().run(
        None, "ls-remote", "ssh://gerrit.invalid:29418/platform/upstream/example", remote=True
    )
    assert result.returncode == 0
    assert json.loads(transport[2].read_text()) == {
        "command": "git-upload-pack",
        "path": str(transport[1]),
    }


def test_receive_pack_via_unmodified_sandbox_environment(
    transport: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    git = SandboxGit()
    source = tmp_path / "source"
    git.run(None, "init", str(source))
    git.run(
        source,
        "-c",
        "user.name=Offline Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--allow-empty",
        "-m",
        "test",
    )
    git.run(
        source,
        "push",
        "ssh://gerrit.invalid:29418/platform/upstream/example",
        "HEAD:refs/heads/test",
        remote=True,
    )
    assert json.loads(transport[2].read_text())["command"] == "git-receive-pack"
    assert git.run(None, "rev-parse", "refs/heads/test", git_dir=transport[1]).stdout.strip()


@pytest.mark.parametrize(
    "command",
    [
        "uname -a",
        "git-upload-pack /outside/not-a-repository",
        "git-upload-pack ../outside",
        "git-upload-pack platform/../upstream/example",
        "git-upload-pack escape",
    ],
)
def test_fake_ssh_rejects_unsafe_requests(
    transport: tuple[Path, Path, Path], tmp_path: Path, command: str
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (transport[0] / "escape").symlink_to(outside, target_is_directory=True)
    result = subprocess.run(
        [sys.executable, str(FAKE), "gerrit.invalid", command], capture_output=True
    )
    assert result.returncode != 0
    assert not transport[2].exists()
