"""Build verification helpers for CI triage."""

from __future__ import annotations

from tizen_build_verify import (
    EditSpecViolation,
    check_disk_and_maybe_cleanup,
    create_worktree,
    validate_edit_spec,
)
from tizen_ci_shared.workspace import (
    PROTECTED_FILENAME,
    DisposableWorktree,
    WorkspaceViolation,
    cleanup_worktree,
    is_protected,
    mark_worktree_protected,
    release_worktree_protection,
)

from ci_triage.verify.failure_classify import (
    REPAIR_AUTO,
    REPAIR_DENIED,
    REPAIR_NEEDS_CONFIRMATION,
    FailureClassification,
    classify_failure,
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
