"""Build-verification composition for disposable source copies.

Real-machine validation showed that gbs 2.0.1 does not recognize source
packages inside Git worktrees because their ``.git`` entry is a gitdir pointer
file. The public API intentionally keeps the ``DisposableWorktree`` naming from
Stage 1, but the implementation now creates one-shot full source copies that
preserve the repository's real ``.git`` directory. Callers can keep treating the
returned path as an isolated disposable checkout.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from tizen_ci_shared.workspace import (
    DisposableWorktree,
    WorkspaceViolation,
    _exclude_private_files,
    _oldest_worktrees,
    _run_git,
    clean_repository_preserving_markers,
    cleanup_worktree,
    is_protected,
    write_workdir_marker,
)

DEFAULT_MIN_FREE_BYTES = 5 * 1024**3


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
    root.mkdir(parents=True, exist_ok=True)

    if worktree_path.exists():
        raise WorkspaceViolation(f"disposable worktree already exists: {worktree_path}")
    _copy_repository(baseline, worktree_path)
    _exclude_private_files(worktree_path)
    marker_path = write_workdir_marker(
        worktree_path,
        workspace_root=root,
        baseline_repo=baseline,
        base_commit=base_commit,
        iter_index=iter_index,
    )
    _run_git(["-C", str(worktree_path), "checkout", "--detach", base_commit])
    _run_git(["-C", str(worktree_path), "reset", "--hard", base_commit])
    clean_repository_preserving_markers(worktree_path)
    return DisposableWorktree(
        path=str(worktree_path),
        baseline_repo=str(baseline),
        base_commit=base_commit,
        workspace_root=str(root),
        iter_index=iter_index,
        marker_path=str(marker_path),
    )


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


def _copy_repository(src: Path, dst: Path) -> None:
    # Use cp -a to match the real-machine validation path: it preserves the
    # full .git directory, symlinks, permissions, and timestamps for gbs.
    subprocess.run(["cp", "-a", str(src), str(dst)], check=True, text=True, capture_output=True)
