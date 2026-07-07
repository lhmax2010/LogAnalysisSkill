from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from ci_triage.verify.workspace import (
    MARKER_FILENAME,
    WorkspaceViolation,
    check_disk_and_maybe_cleanup,
    cleanup_worktree,
    create_worktree,
)


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )


def _repo(tmp_path: Path, *, checkout_hook: bool = False) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init"], repo)
    _git(["config", "user.name", "CI Triage"], repo)
    _git(["config", "user.email", "ci-triage@example.test"], repo)
    (repo / "src").mkdir()
    (repo / "src" / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
    _git(["add", "src/main.c"], repo)
    _git(["commit", "-m", "initial"], repo)
    if checkout_hook:
        hook = repo / ".git" / "hooks" / "post-checkout"
        hook.write_text("#!/bin/sh\ntouch hook-untracked.tmp\n", encoding="utf-8")
        hook.chmod(0o755)
    head = _git(["rev-parse", "HEAD"], repo).stdout.strip()
    return repo, head


def test_create_worktree_writes_marker_and_leaves_clean_status(tmp_path: Path) -> None:
    repo, head = _repo(tmp_path, checkout_hook=True)
    root = tmp_path / "workspaces"

    handle = create_worktree(str(repo), head, str(root), 1)

    path = Path(handle.path)
    assert path.is_dir()
    assert (path / ".git").is_dir()
    assert _git(["rev-parse", "HEAD"], path).stdout.strip() == head
    marker_path = path / MARKER_FILENAME
    assert marker_path.is_file()
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker["workspace_root"] == str(root.resolve())
    assert marker["base_commit"] == head
    assert marker["iter_index"] == 1
    assert not (path / "hook-untracked.tmp").exists()
    assert _git(["status", "--porcelain"], path).stdout == ""

    cleanup_worktree(handle)


def test_cleanup_worktree_removes_directory_and_git_metadata(tmp_path: Path) -> None:
    repo, head = _repo(tmp_path)
    handle = create_worktree(str(repo), head, str(tmp_path / "workspaces"), 2)

    cleanup_worktree(handle)

    assert not Path(handle.path).exists()


def test_cleanup_without_marker_raises(tmp_path: Path) -> None:
    repo, head = _repo(tmp_path)
    handle = create_worktree(str(repo), head, str(tmp_path / "workspaces"), 3)
    Path(handle.marker_path).unlink()

    with pytest.raises(WorkspaceViolation, match="missing"):
        cleanup_worktree(handle)

    shutil.rmtree(handle.path)


def test_cleanup_marker_workspace_root_mismatch_raises(tmp_path: Path) -> None:
    repo, head = _repo(tmp_path)
    handle = create_worktree(str(repo), head, str(tmp_path / "workspaces"), 4)
    marker_path = Path(handle.marker_path)
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    marker["workspace_root"] = str((tmp_path / "different").resolve())
    marker_path.write_text(json.dumps(marker), encoding="utf-8")

    with pytest.raises(WorkspaceViolation, match="workspace_root"):
        cleanup_worktree(handle)

    marker["workspace_root"] = handle.workspace_root
    marker_path.write_text(json.dumps(marker), encoding="utf-8")
    cleanup_worktree(handle)


def test_cleanup_path_outside_workspace_root_raises(tmp_path: Path) -> None:
    repo, head = _repo(tmp_path)
    handle = create_worktree(str(repo), head, str(tmp_path / "workspaces"), 5)
    bad_handle = replace(handle, path=str(tmp_path / "outside"))

    with pytest.raises(WorkspaceViolation, match="outside workspace_root"):
        cleanup_worktree(bad_handle)

    cleanup_worktree(handle)


def test_check_disk_cleans_oldest_iter_with_marker_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, head = _repo(tmp_path)
    root = tmp_path / "workspaces"
    old = create_worktree(str(repo), head, str(root), 0)
    new = create_worktree(str(repo), head, str(root), 1)
    calls = {"count": 0}

    def fake_disk_usage(path: object) -> object:
        calls["count"] += 1
        if calls["count"] == 1:
            return SimpleNamespace(free=0)
        return SimpleNamespace(free=10 * 1024**3)

    monkeypatch.setattr(shutil, "disk_usage", fake_disk_usage)

    warnings = check_disk_and_maybe_cleanup(str(root), min_free_bytes=5 * 1024**3)

    assert any("cleaned disposable worktree" in warning for warning in warnings)
    assert not Path(old.path).exists()
    assert Path(new.path).exists()
    cleanup_worktree(new)


def test_cleanup_uses_rmtree_after_marker_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, head = _repo(tmp_path)
    handle = create_worktree(str(repo), head, str(tmp_path / "workspaces"), 6)
    calls: list[str] = []
    real_rmtree = shutil.rmtree

    def fake_rmtree(path: str | Path) -> None:
        calls.append(str(path))
        real_rmtree(path)

    monkeypatch.setattr(shutil, "rmtree", fake_rmtree)

    cleanup_worktree(handle)

    assert calls == [handle.path]
    assert not Path(handle.path).exists()
