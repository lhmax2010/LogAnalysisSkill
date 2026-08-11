"""Shared disposable-workspace types, markers, and cleanup primitives."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MARKER_FILENAME = ".ci_triage_workdir"
PROTECTED_FILENAME = ".ci_triage_protected"


class WorkspaceViolation(RuntimeError):
    """Raised when a disposable worktree operation would be unsafe."""


@dataclass(frozen=True)
class DisposableWorktree:
    """Handle returned by ``create_worktree``."""

    path: str
    baseline_repo: str
    base_commit: str
    workspace_root: str
    iter_index: int
    marker_path: str


def write_workdir_marker(
    worktree_path: Path,
    *,
    workspace_root: Path,
    baseline_repo: Path,
    base_commit: str,
    iter_index: int,
) -> Path:
    """Write the workdir marker and return its concrete path."""

    marker_path = worktree_path / MARKER_FILENAME
    marker = {
        "workspace_root": str(workspace_root),
        "baseline_repo": str(baseline_repo),
        "base_commit": base_commit,
        "iter_index": iter_index,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    marker_path.write_text(json.dumps(marker, sort_keys=True) + "\n", encoding="utf-8")
    return marker_path


def clean_repository_preserving_markers(worktree_path: Path) -> None:
    """Clean the disposable repository while retaining both authority markers."""

    _run_git(
        [
            "-C",
            str(worktree_path),
            "clean",
            "-ffdx",
            "-e",
            MARKER_FILENAME,
            "-e",
            PROTECTED_FILENAME,
        ]
    )


def cleanup_worktree(handle: DisposableWorktree) -> None:
    """Remove a disposable source copy after marker-based safety checks."""

    _verify_cleanup_handle(handle)
    shutil.rmtree(handle.path)


def cleanup_disposable_copy(
    worktree_path: str,
    expected_workspace_root: str,
    *,
    reject_protected: bool = True,
) -> None:
    """Clean one residual disposable copy through the marker-verified path."""

    path = Path(worktree_path).resolve()
    root = Path(expected_workspace_root).resolve()
    if reject_protected and is_protected(path):
        raise WorkspaceViolation(f"protected disposable copy cannot be cleaned: {path}")
    marker_path = path / MARKER_FILENAME
    marker = _read_marker(marker_path)
    try:
        handle = DisposableWorktree(
            path=str(path),
            baseline_repo=str(marker["baseline_repo"]),
            base_commit=str(marker["base_commit"]),
            workspace_root=str(root),
            iter_index=int(marker["iter_index"]),
            marker_path=str(marker_path),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise WorkspaceViolation(f"invalid disposable worktree marker: {marker_path}") from exc
    cleanup_worktree(handle)


def mark_worktree_protected(
    handle: DisposableWorktree,
    *,
    verification_id: str,
    failure_key: str,
) -> None:
    """Protect a verified worktree from automatic cleanup until explicit release."""

    _verify_cleanup_handle(handle)
    path = Path(handle.path)
    _exclude_private_files(path)
    protected = {
        "protected_reason": "GERRIT_READY",
        "verification_id": verification_id,
        "failure_key": failure_key,
        "protected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (path / PROTECTED_FILENAME).write_text(
        json.dumps(protected, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def release_worktree_protection(worktree_path: str) -> bool:
    """Remove a protected-worktree marker when a human confirms it is no longer needed."""

    path = Path(worktree_path).resolve() / PROTECTED_FILENAME
    if not path.exists():
        return False
    path.unlink()
    return True


def is_protected(worktree_path: str | Path) -> bool:
    """Return whether a disposable worktree is protected from automatic cleanup."""

    return (Path(worktree_path) / PROTECTED_FILENAME).is_file()


def _verify_cleanup_handle(handle: DisposableWorktree) -> None:
    marker_path = Path(handle.marker_path)
    if not marker_path.is_file():
        raise WorkspaceViolation(f"missing disposable worktree marker: {marker_path}")

    marker = _read_marker(marker_path)
    handle_root = Path(handle.workspace_root).resolve()
    handle_path = Path(handle.path).resolve()
    marker_root = Path(str(marker.get("workspace_root", ""))).resolve()

    if marker_root != handle_root:
        raise WorkspaceViolation("marker workspace_root does not match handle workspace_root")
    if not _is_relative_to(handle_path, handle_root):
        raise WorkspaceViolation("worktree path is outside workspace_root")


def _oldest_worktrees(root: Path) -> list[DisposableWorktree]:
    handles: list[DisposableWorktree] = []
    for child in root.iterdir():
        if not child.is_dir() or not child.name.startswith("iter_"):
            continue
        marker_path = child / MARKER_FILENAME
        if not marker_path.is_file():
            continue
        try:
            marker = _read_marker(marker_path)
            baseline_repo = str(marker["baseline_repo"])
            base_commit = str(marker["base_commit"])
            iter_index = int(marker["iter_index"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, OSError):
            continue
        handles.append(
            DisposableWorktree(
                path=str(child.resolve()),
                baseline_repo=baseline_repo,
                base_commit=base_commit,
                workspace_root=str(root),
                iter_index=iter_index,
                marker_path=str(marker_path),
            )
        )
    return sorted(handles, key=lambda handle: handle.iter_index)


def _read_marker(marker_path: Path) -> dict[str, Any]:
    raw = json.loads(marker_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise WorkspaceViolation("disposable worktree marker is not a JSON object")
    return raw


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _run_git(args: list[str]) -> None:
    subprocess.run(["git", *args], check=True, text=True, capture_output=True)


def _exclude_private_files(worktree_path: Path) -> None:
    result = subprocess.run(
        ["git", "-C", str(worktree_path), "rev-parse", "--git-path", "info/exclude"],
        check=True,
        text=True,
        capture_output=True,
    )
    exclude_path = Path(result.stdout.strip())
    if not exclude_path.is_absolute():
        exclude_path = worktree_path / exclude_path
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    current = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    lines = set(current.splitlines())
    missing = [
        filename for filename in (MARKER_FILENAME, PROTECTED_FILENAME) if filename not in lines
    ]
    if missing:
        with exclude_path.open("a", encoding="utf-8") as handle:
            if current and not current.endswith("\n"):
                handle.write("\n")
            for filename in missing:
                handle.write(f"{filename}\n")
