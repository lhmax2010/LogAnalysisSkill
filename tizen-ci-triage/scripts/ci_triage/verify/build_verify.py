"""Compatibility shim for the extracted build-verify skill."""

from tizen_build_verify.build_verify import BuildVerifyOptions as BuildVerifyOptions
from tizen_build_verify.build_verify import BuildVerifyResult as BuildVerifyResult
from tizen_build_verify.build_verify import SubprocessRunner as SubprocessRunner
from tizen_build_verify.build_verify import _actual_changed_paths as _actual_changed_paths
from tizen_build_verify.build_verify import _allowed_paths as _allowed_paths
from tizen_build_verify.build_verify import _analyze_failure as _analyze_failure
from tizen_build_verify.build_verify import _ApplyPatchResult as _ApplyPatchResult
from tizen_build_verify.build_verify import _build_subprocess_env as _build_subprocess_env
from tizen_build_verify.build_verify import _BuildProcessResult as _BuildProcessResult
from tizen_build_verify.build_verify import _canonical_diff_sha256 as _canonical_diff_sha256
from tizen_build_verify.build_verify import _classification_fail as _classification_fail
from tizen_build_verify.build_verify import _fail as _fail
from tizen_build_verify.build_verify import _format_and_apply_patch as _format_and_apply_patch
from tizen_build_verify.build_verify import _gbs_arch as _gbs_arch
from tizen_build_verify.build_verify import _gbs_command as _gbs_command
from tizen_build_verify.build_verify import _git as _git
from tizen_build_verify.build_verify import _git_stdout as _git_stdout
from tizen_build_verify.build_verify import _normalize_build_log as _normalize_build_log
from tizen_build_verify.build_verify import _read_json as _read_json
from tizen_build_verify.build_verify import _run as _run
from tizen_build_verify.build_verify import _run_gbs_build as _run_gbs_build
from tizen_build_verify.build_verify import _run_git_diff_check as _run_git_diff_check
from tizen_build_verify.build_verify import _sha256_file as _sha256_file
from tizen_build_verify.build_verify import _sha256_text as _sha256_text
from tizen_build_verify.build_verify import _string_or_empty as _string_or_empty
from tizen_build_verify.build_verify import (
    _tracked_worktree_mutated as _tracked_worktree_mutated,
)
from tizen_build_verify.build_verify import build_verify as build_verify
from tizen_build_verify.build_verify import build_verify_to_json as build_verify_to_json
from tizen_build_verify.build_verify import default_extra_pythonpath as default_extra_pythonpath

__all__ = [
    "BuildVerifyOptions",
    "BuildVerifyResult",
    "build_verify",
    "build_verify_to_json",
    "default_extra_pythonpath",
]
