"""Compatibility exports for shared workspace and the build-verify skill."""

from tizen_build_verify.workspace import DEFAULT_MIN_FREE_BYTES as DEFAULT_MIN_FREE_BYTES
from tizen_build_verify.workspace import _copy_repository as _copy_repository
from tizen_build_verify.workspace import (
    check_disk_and_maybe_cleanup as check_disk_and_maybe_cleanup,
)
from tizen_build_verify.workspace import create_worktree as create_worktree
from tizen_ci_shared.workspace import MARKER_FILENAME as MARKER_FILENAME
from tizen_ci_shared.workspace import PROTECTED_FILENAME as PROTECTED_FILENAME
from tizen_ci_shared.workspace import DisposableWorktree as DisposableWorktree
from tizen_ci_shared.workspace import WorkspaceViolation as WorkspaceViolation
from tizen_ci_shared.workspace import _exclude_private_files as _exclude_private_files
from tizen_ci_shared.workspace import _is_relative_to as _is_relative_to
from tizen_ci_shared.workspace import _oldest_worktrees as _oldest_worktrees
from tizen_ci_shared.workspace import _read_marker as _read_marker
from tizen_ci_shared.workspace import _run_git as _run_git
from tizen_ci_shared.workspace import _verify_cleanup_handle as _verify_cleanup_handle
from tizen_ci_shared.workspace import (
    clean_repository_preserving_markers as clean_repository_preserving_markers,
)
from tizen_ci_shared.workspace import cleanup_disposable_copy as cleanup_disposable_copy
from tizen_ci_shared.workspace import cleanup_worktree as cleanup_worktree
from tizen_ci_shared.workspace import is_protected as is_protected
from tizen_ci_shared.workspace import mark_worktree_protected as mark_worktree_protected
from tizen_ci_shared.workspace import (
    release_worktree_protection as release_worktree_protection,
)
from tizen_ci_shared.workspace import write_workdir_marker as write_workdir_marker

__all__ = [
    "DEFAULT_MIN_FREE_BYTES",
    "DisposableWorktree",
    "MARKER_FILENAME",
    "PROTECTED_FILENAME",
    "WorkspaceViolation",
    "check_disk_and_maybe_cleanup",
    "clean_repository_preserving_markers",
    "cleanup_disposable_copy",
    "cleanup_worktree",
    "create_worktree",
    "is_protected",
    "mark_worktree_protected",
    "release_worktree_protection",
    "write_workdir_marker",
]
