"""Build verification helpers for CI triage."""

from __future__ import annotations

from ci_triage.verify.edit_spec_guard import EditSpecViolation, validate_edit_spec
from ci_triage.verify.failure_classify import (
    REPAIR_AUTO,
    REPAIR_DENIED,
    REPAIR_NEEDS_CONFIRMATION,
    FailureClassification,
    classify_failure,
)
from ci_triage.verify.workspace import (
    PROTECTED_FILENAME,
    DisposableWorktree,
    WorkspaceViolation,
    check_disk_and_maybe_cleanup,
    cleanup_worktree,
    create_worktree,
    is_protected,
    mark_worktree_protected,
    release_worktree_protection,
)

__all__ = [
    "DisposableWorktree",
    "EditSpecViolation",
    "FailureClassification",
    "PROTECTED_FILENAME",
    "REPAIR_AUTO",
    "REPAIR_DENIED",
    "REPAIR_NEEDS_CONFIRMATION",
    "WorkspaceViolation",
    "classify_failure",
    "cleanup_worktree",
    "check_disk_and_maybe_cleanup",
    "create_worktree",
    "is_protected",
    "mark_worktree_protected",
    "release_worktree_protection",
    "validate_edit_spec",
]
