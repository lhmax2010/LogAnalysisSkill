"""Disposable source tree management for build verification.

Real-machine validation showed that gbs 2.0.1 does not recognize source
packages inside Git worktrees because their ``.git`` entry is a gitdir pointer
file. The public API intentionally keeps the ``DisposableWorktree`` naming from
Stage 1, but the implementation now creates one-shot full source copies that
preserve the repository's real ``.git`` directory. Callers can keep treating the
returned path as an isolated disposable checkout.
"""

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
DEFAULT_MIN_FREE_BYTES = 5 * 1024**3


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


def create_worktree(
    baseline_repo: str,
    base_commit: str,
    workspace_root: str,
    iter_index: int,
) -> DisposableWorktree:
    """Create a disposable full repository copy for one verification iteration."""

    baseline = Path(baseline_repo).resolve()
    root = Path(workspace_root).resolve()
    worktree_path = root / f"iter_{iter_index}"
    marker_path = worktree_path / MARKER_FILENAME
    root.mkdir(parents=True, exist_ok=True)

    if worktree_path.exists():
        raise WorkspaceViolation(f"disposable worktree already exists: {worktree_path}")
    _copy_repository(baseline, worktree_path)
    _exclude_private_files(worktree_path)
    marker = {
        "workspace_root": str(root),
        "baseline_repo": str(baseline),
        "base_commit": base_commit,
        "iter_index": iter_index,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    marker_path.write_text(json.dumps(marker, sort_keys=True) + "\n", encoding="utf-8")
    _run_git(["-C", str(worktree_path), "checkout", "--detach", base_commit])
    _run_git(["-C", str(worktree_path), "reset", "--hard", base_commit])
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
    return DisposableWorktree(
        path=str(worktree_path),
        baseline_repo=str(baseline),
        base_commit=base_commit,
        workspace_root=str(root),
        iter_index=iter_index,
        marker_path=str(marker_path),
    )


def cleanup_worktree(handle: DisposableWorktree) -> None:
    """Remove a disposable source copy after marker-based safety checks."""

    _verify_cleanup_handle(handle)
    shutil.rmtree(handle.path)


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


def check_disk_and_maybe_cleanup(
    workspace_root: str,
    min_free_bytes: int = DEFAULT_MIN_FREE_BYTES,
) -> list[str]:
    """Clean oldest disposable worktrees when free space is below the threshold."""

    root = Path(workspace_root).resolve()
    warnings: list[str] = []
    if not root.exists():
        return warnings
    free = shutil.disk_usage(root).free
    if free >= min_free_bytes:
        return warnings

    skipped_protected: list[str] = []
    for handle in _oldest_worktrees(root):
        if is_protected(handle.path):
            skipped_protected.append(handle.path)
            continue
        try:
            cleanup_worktree(handle)
        except (OSError, WorkspaceViolation, subprocess.CalledProcessError) as exc:
            warnings.append(f"failed to clean {handle.path}: {exc}")
            continue
        warnings.append(f"cleaned disposable worktree {handle.path}")
        if shutil.disk_usage(root).free >= min_free_bytes:
            break
    if shutil.disk_usage(root).free < min_free_bytes:
        if skipped_protected:
            warnings.append(
                "disk_low_protected_worktrees_skipped: " + ", ".join(skipped_protected)
            )
        warnings.append(
            f"free space below threshold after cleanup: {shutil.disk_usage(root).free} bytes"
        )
    return warnings


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


def _copy_repository(src: Path, dst: Path) -> None:
    # Use cp -a to match the real-machine validation path: it preserves the
    # full .git directory, symlinks, permissions, and timestamps for gbs.
    subprocess.run(["cp", "-a", str(src), str(dst)], check=True, text=True, capture_output=True)


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
