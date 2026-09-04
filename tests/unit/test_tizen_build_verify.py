from __future__ import annotations

import importlib
import json
import os
import subprocess
import unicodedata
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import ci_triage
import pytest
import tizen_build_verify
from tizen_build_verify.build_verify import (
    BuildVerifyOptions,
    _format_and_apply_patch,
    _gbs_arch,
    _gbs_command,
    build_verify,
    build_verify_to_json,
    default_extra_pythonpath,
)
from tizen_build_verify.edit_spec_guard import EditSpecViolation, validate_edit_spec
from tizen_ci_shared.classify import REPAIR_AUTO, REPAIR_DENIED
from tizen_ci_shared.env import discover_sibling_pythonpath
from tizen_ci_shared.state import (
    StateDatabase,
    build_failure_key,
    get_latest_status,
    get_record,
)
from tizen_ci_shared.workspace import PROTECTED_FILENAME

_BUILD_VERIFY_MODULE = importlib.import_module("tizen_build_verify.build_verify")
_EDIT_SPEC_MODULE = importlib.import_module("tizen_build_verify.edit_spec_guard")
_WORKSPACE_MODULE = importlib.import_module("tizen_build_verify.workspace")

# Test ownership boundary:
# - this file: tizen_build_verify skill behavior;
# - ci_triage unit/integration files: orchestration integration;
# - test_build_verify_legacy_wiring.py: compatibility-shim identity only.


class GbsRunner:
    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: str = "build ok\n",
        stderr: str = "",
        mutate_tracked: bool = False,
        fail_apply: bool = False,
        add_unexpected: bool = False,
        timeout: bool = False,
    ) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.mutate_tracked = mutate_tracked
        self.fail_apply = fail_apply
        self.add_unexpected = add_unexpected
        self.timeout = timeout
        self.events: list[str] = []
        self.gbs_commands: list[list[str]] = []

    def __call__(self, args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if isinstance(args, list) and args and args[0] == "gbs":
            self.events.append("gbs")
            self.gbs_commands.append(list(args))
            if self.timeout:
                raise subprocess.TimeoutExpired(args, kwargs.get("timeout") or 1)
            cwd = kwargs.get("cwd")
            if self.mutate_tracked and isinstance(cwd, Path):
                (cwd / "src" / "main.c").write_text(
                    "int main(void) { return 2; }\n",
                    encoding="utf-8",
                )
            return subprocess.CompletedProcess(
                args,
                self.returncode,
                stdout=self.stdout,
                stderr=self.stderr,
            )
        if isinstance(args, list) and "commit" in args:
            self.events.append("commit")
        if (
            self.fail_apply
            and isinstance(args, list)
            and len(args) >= 5
            and args[0] == "git"
            and args[3] == "apply"
            and "--check" not in args
        ):
            raise subprocess.CalledProcessError(1, args, stderr="mock apply failed")
        completed = subprocess.run(args, **kwargs)
        if (
            self.add_unexpected
            and isinstance(args, list)
            and len(args) >= 5
            and args[0] == "git"
            and args[3] == "apply"
            and "--check" not in args
        ):
            worktree = Path(args[2])
            (worktree / "src" / "unexpected.c").write_text("int surprise;\n", encoding="utf-8")
        return cast(subprocess.CompletedProcess[str], completed)


def _git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def _repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init"], repo)
    _git(["config", "user.name", "CI Triage"], repo)
    _git(["config", "user.email", "ci-triage@example.test"], repo)
    (repo / "src").mkdir()
    (repo / "src" / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
    _git(["add", "src/main.c"], repo)
    _git(["commit", "-m", "base"], repo)
    return repo, _git(["rev-parse", "HEAD"], repo)


def _write_json(path: Path, data: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _edit_spec(tmp_path: Path, *, old: str = "return 0", new: str = "return 1") -> Path:
    return _write_json(
        tmp_path / "edit_spec.json",
        {
            "schema_version": "gbs_patch_suggest/edit-spec/v1",
            "patch_name": "candidate.patch",
            "edits": [
                {
                    "file": "src/main.c",
                    "line": 1,
                    "old": old,
                    "new": new,
                }
            ],
        },
    )


def _options(tmp_path: Path, *, edit_spec: Path | None = None) -> BuildVerifyOptions:
    repo, head = _repo(tmp_path)
    gbs_conf = tmp_path / "gbs.conf"
    gbs_conf.write_text("[general]\n", encoding="utf-8")
    baseline = _write_json(tmp_path / "baseline_evidence.json", {"primary_error": {}})
    return BuildVerifyOptions(
        src_clean=repo,
        base_commit=head,
        edit_spec_path=edit_spec or _edit_spec(tmp_path),
        gbs_conf=gbs_conf,
        package="demo",
        workspace_root=tmp_path / "workspaces",
        baseline_evidence=baseline,
        output_dir=tmp_path / "out",
        iter_index=1,
        wall_timeout=30,
        state_db=StateDatabase(tmp_path / "state.sqlite3"),
        ci_system="quickbuild",
        build_id="1095003",
        project="platform/test/demo",
        branch="tizen",
        arch="standard-armv7l",
    )


def _worktree_path(options: BuildVerifyOptions) -> Path:
    return options.workspace_root.resolve() / f"iter_{options.iter_index}"


def _failure_key(options: BuildVerifyOptions) -> str:
    return build_failure_key(
        ci_system=options.ci_system,
        build_id=options.build_id,
        project=options.project,
        branch=options.branch,
        arch=options.arch,
        spec_name=options.package,
        base_commit=options.base_commit,
    )


def _is_analyzer_command(args: object) -> bool:
    return (
        isinstance(args, list)
        and len(args) >= 3
        and args[1:3] == ["-m", "gbs_analyzer"]
    )


# Skill behavior: existing build-verify coverage moved from the legacy owner.
def test_pass_writes_verification_record_and_commits_before_build(tmp_path: Path) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(returncode=0, stdout="PASS\n")

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "PASS"
    assert result.actual_changed_paths == ["src/main.c"]
    assert result.verification_id is not None
    assert result.verified_commit_sha
    assert result.verified_tree_sha
    record = get_record(options.state_db, result.verification_id)
    assert record is not None
    assert record.verified_commit_sha == result.verified_commit_sha
    assert record.verified_tree_sha == result.verified_tree_sha
    assert record.project == "platform/test/demo"
    assert record.command_line == f"gbs -c {options.gbs_conf} build -A armv7l --include-all"
    assert get_latest_status(options.state_db, record.failure_key) == "GERRIT_READY"
    assert runner.events.index("commit") < runner.events.index("gbs")
    assert Path(result.build_log or "").is_file()
    assert (options.output_dir / "audit" / "baseline_evidence.json").is_file()
    assert result.worktree_path is not None
    assert (Path(result.worktree_path) / PROTECTED_FILENAME).is_file()
    assert _git(["status", "--porcelain"], Path(result.worktree_path)) == ""
    result_json = tmp_path / "result.json"
    build_verify_to_json(result, result_json)
    assert json.loads(result_json.read_text(encoding="utf-8"))["actual_changed_paths"] == [
        "src/main.c"
    ]


def test_gbs_command_matches_verified_real_machine_shape(tmp_path: Path) -> None:
    options = _options(tmp_path)

    command = _gbs_command(options)

    assert command == [
        "gbs",
        "-c",
        str(options.gbs_conf),
        "build",
        "-A",
        "armv7l",
        "--include-all",
    ]
    assert "--package" not in command


@pytest.mark.parametrize(
    ("arch", "expected"),
    [
        ("standard-aarch64", "aarch64"),
        ("standard-armv7l", "armv7l"),
        ("standard-x86_64", "x86_64"),
        ("aarch64", "aarch64"),
    ],
)
def test_gbs_arch_removes_standard_prefix(arch: str, expected: str) -> None:
    assert _gbs_arch(arch) == expected


def test_gbs_fail_source_werror_returns_repair_allowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(returncode=1, stderr="src/main.c:1: error: no member [-Werror]\n")

    def fake_analyze(*args: object, **kwargs: object) -> Path:
        path = options.output_dir / "audit" / "evidence_packet.json"
        return _write_json(
            path,
            {
                "primary_error": {
                    "kind": "werror",
                    "file": "src/main.c",
                    "line": 1,
                    "message": "error: no member [-Werror]",
                    "type_fixability": "probably_fixable",
                    "source_reachable": True,
                    "source_owned": True,
                }
            },
        )

    monkeypatch.setattr(_BUILD_VERIFY_MODULE, "_analyze_failure", fake_analyze)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.actual_changed_paths == ["src/main.c"]
    assert result.failure_class == "source_repairable"
    assert result.repair_allowed == REPAIR_AUTO
    assert result.evidence is not None
    result_json = tmp_path / "result.json"
    build_verify_to_json(result, result_json)
    assert json.loads(result_json.read_text(encoding="utf-8"))["repair_allowed"] == REPAIR_AUTO


def test_gbs_fail_toolchain_denylist_not_repair_allowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(
        returncode=1,
        stderr="clang: error: unknown argument '-enable-ml-inliner=release'\n",
    )

    def fake_analyze(*args: object, **kwargs: object) -> Path:
        return _write_json(
            options.output_dir / "audit" / "evidence_packet.json",
            {
                "primary_error": {
                    "kind": "raw_error",
                    "message": "clang: error: unknown argument '-enable-ml-inliner=release'",
                }
            },
        )

    monkeypatch.setattr(_BUILD_VERIFY_MODULE, "_analyze_failure", fake_analyze)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.failure_class == "toolchain"
    assert result.repair_allowed == REPAIR_DENIED


def test_build_mutated_tracked_source_after_commit_fails(tmp_path: Path) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(returncode=0, mutate_tracked=True)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.actual_changed_paths == ["src/main.c"]
    assert result.failure_stage == "build_mutated_source"
    assert result.failure_class == "build_mutated_source"
    assert result.repair_allowed == REPAIR_DENIED


def test_invalid_edit_spec_fails_before_build(tmp_path: Path) -> None:
    bad_spec = _write_json(
        tmp_path / "bad.json",
        {
            "schema_version": "gbs_patch_suggest/edit-spec/v1",
            "patch_name": "candidate.patch",
            "edits": [{"file": "/etc/passwd", "old": "x", "new": "y"}],
        },
    )
    options = _options(tmp_path, edit_spec=bad_spec)
    runner = GbsRunner()

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.failure_stage == "apply_failed"
    assert result.actual_changed_paths == []
    assert "gbs" not in runner.events


def test_apply_failure_fails_before_build(tmp_path: Path) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(fail_apply=True)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.failure_stage == "apply_failed"
    assert result.actual_changed_paths == []
    assert "gbs" not in runner.events


def test_format_and_apply_patch_uses_absolute_patch_path_for_git_c(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path)
    worktree = tmp_path / "manual-worktree"
    subprocess.run(
        ["git", "clone", str(options.src_clean), str(worktree)],
        check=True,
        text=True,
        capture_output=True,
    )
    monkeypatch.chdir(tmp_path)

    result = _format_and_apply_patch(
        options.edit_spec_path,
        src_root=worktree,
        output_patch=Path("relative-audit/candidate.patch"),
        subprocess_runner=subprocess.run,
    )

    assert result.error is None
    assert (worktree / "src" / "main.c").read_text(encoding="utf-8") == (
        "int main(void) { return 1; }\n"
    )


def test_gbs_timeout_fails_without_repair(tmp_path: Path) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(timeout=True)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.failure_stage == "build_timeout"
    assert result.repair_allowed == REPAIR_DENIED


def test_unexpected_changed_paths_are_checked_before_no_effective_changes(
    tmp_path: Path,
) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(add_unexpected=True)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.failure_stage == "apply_unexpected_paths"
    assert result.actual_changed_paths == ["src/main.c", "src/unexpected.c"]
    assert result.error is not None
    assert "src/unexpected.c" in result.error
    assert "gbs" not in runner.events


def test_no_effective_changes_fails_before_build(tmp_path: Path) -> None:
    options = _options(tmp_path, edit_spec=_edit_spec(tmp_path, old="return 0", new="return 0"))
    runner = GbsRunner()

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.failure_stage == "no_effective_changes"
    assert result.actual_changed_paths == []
    assert "gbs" not in runner.events


def test_marker_is_excluded_from_actual_changed_paths(tmp_path: Path) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(returncode=0)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "PASS"
    assert result.actual_changed_paths == ["src/main.c"]
    assert result.error is None


def test_pass_marks_worktree_protected_before_writing_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(returncode=0)
    events: list[str] = []

    def fake_mark(handle: object, *, verification_id: str, failure_key: str) -> None:
        events.append("mark")

    def fake_write(db: object, record: object) -> str:
        events.append("write")
        return "verify-1"

    monkeypatch.setattr(_BUILD_VERIFY_MODULE, "mark_worktree_protected", fake_mark)
    monkeypatch.setattr(_BUILD_VERIFY_MODULE, "write_pass_record", fake_write)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "PASS"
    assert events == ["mark", "write"]


def test_pass_write_record_failure_is_not_silent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(returncode=0)

    def fake_write(db: object, record: object) -> str:
        raise RuntimeError("db is down")

    monkeypatch.setattr(_BUILD_VERIFY_MODULE, "write_pass_record", fake_write)

    with pytest.raises(RuntimeError, match="db is down"):
        build_verify(options, subprocess_runner=runner)


# Skill behavior: §4 branch-matrix deltas and side-effect assertions.
def test_diff_check_failure_returns_apply_failed_and_preserves_applied_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path)
    runner = GbsRunner()

    monkeypatch.setattr(
        _BUILD_VERIFY_MODULE,
        "_run_git_diff_check",
        lambda *_args: "git diff --check failed with exit 2",
    )

    result = build_verify(options, subprocess_runner=runner)

    worktree = _worktree_path(options)
    assert result.result == "FAIL"
    assert result.failure_stage == "apply_failed"
    assert result.repair_allowed == REPAIR_DENIED
    assert result.actual_changed_paths == []
    assert worktree.is_dir()
    assert "return 1" in (worktree / "src" / "main.c").read_text(encoding="utf-8")
    assert "gbs" not in runner.events


def test_successful_apply_with_no_changed_paths_returns_no_effective_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path)
    runner = GbsRunner()

    monkeypatch.setattr(
        _BUILD_VERIFY_MODULE,
        "_format_and_apply_patch",
        lambda *_args, **_kwargs: _BUILD_VERIFY_MODULE._ApplyPatchResult(),
    )

    result = build_verify(options, subprocess_runner=runner)

    worktree = _worktree_path(options)
    assert result.result == "FAIL"
    assert result.failure_stage == "no_effective_changes"
    assert result.repair_allowed == REPAIR_DENIED
    assert result.actual_changed_paths == []
    assert worktree.is_dir()
    assert "return 0" in (worktree / "src" / "main.c").read_text(encoding="utf-8")
    assert "gbs" not in runner.events


def test_invalid_edit_spec_failure_removes_disposable_worktree(tmp_path: Path) -> None:
    bad_spec = _write_json(
        tmp_path / "bad-cleanup.json",
        {
            "schema_version": "gbs_patch_suggest/edit-spec/v1",
            "patch_name": "candidate.patch",
            "edits": [{"file": "/etc/passwd", "old": "x", "new": "y"}],
        },
    )
    options = _options(tmp_path, edit_spec=bad_spec)

    result = build_verify(options, subprocess_runner=GbsRunner())

    assert result.failure_stage == "apply_failed"
    assert not _worktree_path(options).exists()


def test_analyzer_nonzero_exit_returns_no_evidence_and_preserves_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(returncode=1, stderr="compiler failed\n")
    real_run = subprocess.run

    def analyzer_fails(args: Any, *runner_args: Any, **runner_kwargs: Any) -> Any:
        if _is_analyzer_command(args):
            raise subprocess.CalledProcessError(7, args)
        return real_run(args, *runner_args, **runner_kwargs)

    monkeypatch.setattr(_BUILD_VERIFY_MODULE.subprocess, "run", analyzer_fails)

    result = build_verify(options, subprocess_runner=runner)

    analyzer_dir = options.output_dir / "audit" / "analyzer_output"
    assert result.result == "FAIL"
    assert result.failure_stage == "gbs_build_failed"
    assert result.evidence is None
    assert analyzer_dir.is_dir()
    assert not (analyzer_dir / "evidence_packet.json").exists()
    assert _worktree_path(options).is_dir()


def test_analyzer_success_without_evidence_returns_none_and_preserves_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(returncode=1, stderr="compiler failed\n")
    real_run = subprocess.run

    def analyzer_writes_nothing(args: Any, *runner_args: Any, **runner_kwargs: Any) -> Any:
        if _is_analyzer_command(args):
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        return real_run(args, *runner_args, **runner_kwargs)

    monkeypatch.setattr(_BUILD_VERIFY_MODULE.subprocess, "run", analyzer_writes_nothing)

    result = build_verify(options, subprocess_runner=runner)

    analyzer_dir = options.output_dir / "audit" / "analyzer_output"
    assert result.result == "FAIL"
    assert result.failure_stage == "gbs_build_failed"
    assert result.evidence is None
    assert analyzer_dir.is_dir()
    assert not (analyzer_dir / "evidence_packet.json").exists()
    assert _worktree_path(options).is_dir()


def test_marker_write_exception_propagates_before_db_write_and_leaves_clean_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path)

    def fail_mark(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("marker write failed")

    monkeypatch.setattr(_BUILD_VERIFY_MODULE, "mark_worktree_protected", fail_mark)

    with pytest.raises(RuntimeError, match="marker write failed"):
        build_verify(options, subprocess_runner=GbsRunner(returncode=0))

    worktree = _worktree_path(options)
    assert worktree.is_dir()
    assert not (worktree / PROTECTED_FILENAME).exists()
    assert _git(["status", "--porcelain"], worktree) == ""
    assert get_latest_status(options.state_db, _failure_key(options)) is None


def test_db_write_exception_propagates_after_marker_and_preserves_protected_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    options = _options(tmp_path)

    def fail_write(*_args: object, **_kwargs: object) -> str:
        raise RuntimeError("db write failed")

    monkeypatch.setattr(_BUILD_VERIFY_MODULE, "write_pass_record", fail_write)

    with pytest.raises(RuntimeError, match="db write failed"):
        build_verify(options, subprocess_runner=GbsRunner(returncode=0))

    worktree = _worktree_path(options)
    assert worktree.is_dir()
    assert (worktree / PROTECTED_FILENAME).is_file()
    assert _git(["status", "--porcelain"], worktree) == ""
    assert get_latest_status(options.state_db, _failure_key(options)) is None


@pytest.mark.parametrize(
    ("arch_raw", "arch_norm"),
    [
        ("standard-aarch64", "aarch64"),
        ("standard-armv7l", "armv7l"),
        ("standard-x86_64", "x86_64"),
        ("aarch64", "aarch64"),
    ],
)
def test_arch_matrix_normalizes_gbs_argv_and_preserves_raw_state(
    tmp_path: Path,
    arch_raw: str,
    arch_norm: str,
) -> None:
    options = replace(_options(tmp_path), arch=arch_raw)
    runner = GbsRunner(returncode=0)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "PASS"
    assert len(runner.gbs_commands) == 1
    command = runner.gbs_commands[0]
    assert command[command.index("-A") + 1] == arch_norm
    assert result.verification_id is not None
    record = get_record(options.state_db, result.verification_id)
    assert record is not None
    assert record.arch == arch_raw
    assert record.failure_key == _failure_key(options)
    assert f"/{arch_raw}/" in record.failure_key


def test_default_extra_pythonpath_matches_legacy_anchor_and_is_nonempty() -> None:
    legacy_launcher = (
        Path(cast(str, ci_triage.__file__)).resolve().parents[1] / "run_ci_triage.py"
    )

    before = discover_sibling_pythonpath(launcher_path=legacy_launcher)
    after = default_extra_pythonpath()

    assert after == before
    assert after


def test_package_root_exports_only_public_contract_and_not_workspace_s9() -> None:
    public_contract = {
        "BuildVerifyOptions": _BUILD_VERIFY_MODULE.BuildVerifyOptions,
        "BuildVerifyResult": _BUILD_VERIFY_MODULE.BuildVerifyResult,
        "EditSpecViolation": _EDIT_SPEC_MODULE.EditSpecViolation,
        "build_verify": _BUILD_VERIFY_MODULE.build_verify,
        "build_verify_to_json": _BUILD_VERIFY_MODULE.build_verify_to_json,
        "check_disk_and_maybe_cleanup": _WORKSPACE_MODULE.check_disk_and_maybe_cleanup,
        "create_worktree": _WORKSPACE_MODULE.create_worktree,
        "default_extra_pythonpath": _BUILD_VERIFY_MODULE.default_extra_pythonpath,
        "validate_edit_spec": _EDIT_SPEC_MODULE.validate_edit_spec,
    }
    private_contract = {
        "SubprocessRunner",
        "_ApplyPatchResult",
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
        "EDIT_SPEC_SCHEMA",
        "_LocatedEdit",
        "_validate_schema",
        "_validate_target_path",
        "_locate_edit",
        "_find_old_from_line",
        "_find_unique_old",
        "_line_starts",
        "_check_no_overlaps",
        "_is_relative_to",
        "DEFAULT_MIN_FREE_BYTES",
        "_copy_repository",
    }

    assert len(public_contract) == 9
    assert len(private_contract) == 36
    assert set(tizen_build_verify.__all__) == set(public_contract)
    for name, implementation in public_contract.items():
        assert getattr(tizen_build_verify, name) is implementation
    for name in private_contract:
        assert not hasattr(tizen_build_verify, name)


# Skill behavior: edit-spec path and schema guards moved from the legacy owner.
def _write(root: Path, relative: str, text: str = "alpha\nbeta\ngamma\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _spec(file_value: str, *, old: str = "beta", line: int | None = 2) -> dict[str, object]:
    edit: dict[str, object] = {"file": file_value, "old": old, "new": "BETA"}
    if line is not None:
        edit["line"] = line
    return {
        "schema_version": "gbs_patch_suggest/edit-spec/v1",
        "patch_name": "candidate.patch",
        "edits": [edit],
    }


def test_normal_relative_path_passes(tmp_path: Path) -> None:
    _write(tmp_path, "tools/include/OutputMetadata.h")

    validate_edit_spec(_spec("tools/include/OutputMetadata.h"), str(tmp_path))


def test_absolute_path_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(EditSpecViolation, match="absolute"):
        validate_edit_spec(_spec("/etc/passwd"), str(tmp_path))


def test_parent_traversal_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(EditSpecViolation, match="escapes|parent"):
        validate_edit_spec(_spec("../../outside.c"), str(tmp_path))


def test_intermediate_symlink_to_outside_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "target.c").write_text("beta\n", encoding="utf-8")
    (root / "link").symlink_to(outside, target_is_directory=True)

    with pytest.raises(EditSpecViolation, match="symlink escapes"):
        validate_edit_spec(_spec("link/target.c", old="beta", line=1), str(root))


def test_final_symlink_to_outside_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.c"
    outside.write_text("beta\n", encoding="utf-8")
    src = root / "src"
    src.mkdir()
    (src / "link.c").symlink_to(outside)

    with pytest.raises(EditSpecViolation, match="symlink escapes"):
        validate_edit_spec(_spec("src/link.c", old="beta", line=1), str(root))


def test_git_internal_path_is_rejected(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("beta\n", encoding="utf-8")

    with pytest.raises(EditSpecViolation, match=".git"):
        validate_edit_spec(_spec(".git/config", old="beta", line=1), str(tmp_path))


def test_empty_and_directory_paths_are_rejected(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()

    with pytest.raises(EditSpecViolation, match="empty"):
        validate_edit_spec(_spec(""), str(tmp_path))
    with pytest.raises(EditSpecViolation, match="directory"):
        validate_edit_spec(_spec("src"), str(tmp_path))


def test_nfd_path_normalizes_to_existing_nfc_file(tmp_path: Path) -> None:
    nfc_name = unicodedata.normalize("NFC", "café.c")
    nfd_name = unicodedata.normalize("NFD", "café.c")
    _write(tmp_path, nfc_name, "beta\n")

    validate_edit_spec(_spec(nfd_name, old="beta", line=1), str(tmp_path))


def test_case_insensitive_bypass_is_platform_specific(tmp_path: Path) -> None:
    if os.path.normcase("A") == "A":
        pytest.skip("case-sensitive filesystem")
    _write(tmp_path, "Src/File.c", "beta\n")
    validate_edit_spec(_spec("src/file.c", old="beta", line=1), str(tmp_path))


def test_overlapping_edits_are_rejected(tmp_path: Path) -> None:
    _write(tmp_path, "src/file.c", "abcdef\n")
    spec = {
        "schema_version": "gbs_patch_suggest/edit-spec/v1",
        "patch_name": "candidate.patch",
        "edits": [
            {"file": "src/file.c", "line": 1, "old": "abc", "new": "ABC"},
            {"file": "src/file.c", "line": 1, "old": "bcd", "new": "BCD"},
        ],
    }

    with pytest.raises(EditSpecViolation, match="overlapping"):
        validate_edit_spec(spec, str(tmp_path))


@pytest.mark.parametrize(
    "bad_spec",
    [
        {"schema_version": "wrong", "patch_name": "x.patch", "edits": []},
        {
            "schema_version": "gbs_patch_suggest/edit-spec/v1",
            "patch_name": "x.patch",
            "edits": [],
        },
        {
            "schema_version": "gbs_patch_suggest/edit-spec/v1",
            "patch_name": "x.patch",
            "edits": [{"old": "x", "new": "y"}],
        },
        {
            "schema_version": "gbs_patch_suggest/edit-spec/v1",
            "patch_name": "x.patch",
            "edits": [{"file": "x.c", "new": "y"}],
        },
    ],
)
def test_invalid_schema_is_rejected(tmp_path: Path, bad_spec: dict[str, object]) -> None:
    with pytest.raises(EditSpecViolation):
        validate_edit_spec(bad_spec, str(tmp_path))
