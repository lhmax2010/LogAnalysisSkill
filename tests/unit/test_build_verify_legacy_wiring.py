from __future__ import annotations

import importlib


# Legacy wiring: compatibility shims only. Skill behavior lives in
# test_tizen_build_verify.py; orchestration integration remains in ci_triage tests.
def test_legacy_shims_preserve_all_migrated_symbol_identities() -> None:
    module_symbols = {
        "build_verify": (
            "SubprocessRunner",
            "BuildVerifyOptions",
            "BuildVerifyResult",
            "_ApplyPatchResult",
            "build_verify",
            "_BuildProcessResult",
            "_format_and_apply_patch",
            "_run_gbs_build",
            "_gbs_command",
            "_gbs_arch",
            "_analyze_failure",
            "_classification_fail",
            "_fail",
            "_actual_changed_paths",
            "_tracked_worktree_mutated",
            "_allowed_paths",
            "_run_git_diff_check",
            "_canonical_diff_sha256",
            "_normalize_build_log",
            "_git",
            "_git_stdout",
            "_run",
            "_read_json",
            "_sha256_file",
            "_sha256_text",
            "_build_subprocess_env",
            "_string_or_empty",
            "build_verify_to_json",
            "default_extra_pythonpath",
        ),
        "edit_spec_guard": (
            "EDIT_SPEC_SCHEMA",
            "EditSpecViolation",
            "_LocatedEdit",
            "validate_edit_spec",
            "_validate_schema",
            "_validate_target_path",
            "_locate_edit",
            "_find_old_from_line",
            "_find_unique_old",
            "_line_starts",
            "_check_no_overlaps",
            "_is_relative_to",
        ),
        "workspace": (
            "DEFAULT_MIN_FREE_BYTES",
            "create_worktree",
            "check_disk_and_maybe_cleanup",
            "_copy_repository",
        ),
    }
    for module_name, symbols in module_symbols.items():
        legacy = importlib.import_module(f"ci_triage.verify.{module_name}")
        skill = importlib.import_module(f"tizen_build_verify.{module_name}")
        for symbol in symbols:
            assert getattr(legacy, symbol) is getattr(skill, symbol)

    legacy_workspace = importlib.import_module("ci_triage.verify.workspace")
    shared_workspace = importlib.import_module("tizen_ci_shared.workspace")
    for symbol in (
        "MARKER_FILENAME",
        "PROTECTED_FILENAME",
        "DisposableWorktree",
        "WorkspaceViolation",
        "_exclude_private_files",
        "_is_relative_to",
        "_oldest_worktrees",
        "_read_marker",
        "_run_git",
        "_verify_cleanup_handle",
        "clean_repository_preserving_markers",
        "cleanup_disposable_copy",
        "cleanup_worktree",
        "is_protected",
        "mark_worktree_protected",
        "release_worktree_protection",
        "write_workdir_marker",
    ):
        assert getattr(legacy_workspace, symbol) is getattr(shared_workspace, symbol)
