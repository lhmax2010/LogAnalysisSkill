from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast

from ci_triage.verify.gerrit_submit import (
    GerritSubmitOptions,
    exit_code_for_release,
    exit_code_for_submit,
    gerrit_submit,
    release_verified_worktree,
)
from tizen_ci_shared.state import (
    GERRIT_READY,
    StateDatabase,
    VerificationRecord,
    build_failure_key,
    build_submission_key,
    get_latest_status,
    record_status,
    write_pass_record,
)
from tizen_ci_shared.workspace import PROTECTED_FILENAME


class SubmitRunner:
    def __init__(
        self,
        *,
        target_head: str | None,
        ls_remote_returncode: int = 0,
        ls_remote_exception: OSError | None = None,
    ) -> None:
        self.target_head = target_head
        self.ls_remote_returncode = ls_remote_returncode
        self.ls_remote_exception = ls_remote_exception
        self.commands: list[list[str]] = []

    def __call__(self, args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if isinstance(args, list):
            self.commands.append([str(item) for item in args])
            if args[:2] == ["git", "ls-remote"]:
                if self.ls_remote_exception is not None:
                    raise self.ls_remote_exception
                stdout = ""
                if self.target_head is not None:
                    stdout = f"{self.target_head}\trefs/heads/tizen\n"
                return subprocess.CompletedProcess(args, self.ls_remote_returncode, stdout, "")
        return cast(subprocess.CompletedProcess[str], subprocess.run(args, **kwargs))


def _git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def _repo(tmp_path: Path) -> tuple[Path, str, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init"], repo)
    _git(["config", "user.name", "CI Triage"], repo)
    _git(["config", "user.email", "ci-triage@example.test"], repo)
    (repo / "src").mkdir()
    (repo / "src" / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
    _git(["add", "src/main.c"], repo)
    _git(["commit", "-m", "base"], repo)
    base_commit = _git(["rev-parse", "HEAD"], repo)
    (repo / "src" / "main.c").write_text("int main(void) { return 1; }\n", encoding="utf-8")
    _git(["add", "src/main.c"], repo)
    _git(["commit", "-m", "verified"], repo)
    verified_commit = _git(["rev-parse", "HEAD"], repo)
    verified_tree = _git(["rev-parse", "HEAD^{tree}"], repo)
    return repo, base_commit, verified_commit, verified_tree


def _record(tmp_path: Path) -> tuple[StateDatabase, VerificationRecord, str]:
    repo, base_commit, verified_commit, verified_tree = _repo(tmp_path)
    db = StateDatabase(tmp_path / "state.sqlite3")
    failure_key = build_failure_key(
        ci_system="quickbuild",
        build_id="1095003",
        project="platform/test/demo",
        branch="tizen",
        arch="standard-aarch64",
        spec_name="demo",
        base_commit=base_commit,
    )
    record = VerificationRecord(
        verification_id="verify-1",
        result="PASS",
        timestamp="2026-07-08T00:00:00+00:00",
        failure_key=failure_key,
        base_commit=base_commit,
        verified_commit_sha=verified_commit,
        verified_tree_sha=verified_tree,
        canonical_diff_sha256="a" * 64,
        patch_sha256="b" * 64,
        edit_spec_sha256="c" * 64,
        project="platform/test/demo",
        branch="tizen",
        spec_name="demo",
        arch="standard-aarch64",
        gbs_conf_sha256="d" * 64,
        build_log_sha256="e" * 64,
        worktree_path=str(repo),
        command_line="gbs -c conf build -A aarch64 --include-all",
    )
    write_pass_record(db, record)
    (repo / PROTECTED_FILENAME).write_text(
        json.dumps({"verification_id": record.verification_id}),
        encoding="utf-8",
    )
    return db, record, base_commit


def _options(
    db: StateDatabase,
    verification_id: str,
    *,
    mode: str = "dry-run",
    submit_target: str = "refs/for/tizen%wip",
) -> GerritSubmitOptions:
    return GerritSubmitOptions(
        verification_id=verification_id,
        state_db=db,
        gerrit_host="review.tizen.org",
        gerrit_port="29418",
        gerrit_user="ci-user",
        submit_target=submit_target,
        submit_mode=mode,
    )


def _expected_push_command(record: VerificationRecord) -> list[str]:
    return [
        "git",
        "-C",
        record.worktree_path,
        "push",
        "ssh://ci-user@review.tizen.org:29418/platform/test/demo",
        "HEAD:refs/for/tizen%wip",
    ]


def test_gerrit_submit_dry_run_returns_command_without_push(tmp_path: Path) -> None:
    db, record, base_commit = _record(tmp_path)
    runner = SubmitRunner(target_head=base_commit)

    result = gerrit_submit(_options(db, record.verification_id), subprocess_runner=runner)

    assert result.action == "dry_run"
    assert result.command_argv == _expected_push_command(record)
    assert result.command is not None
    assert all("push" not in command for command in runner.commands)
    assert result.submission_key == build_submission_key(
        failure_key=record.failure_key,
        verified_tree_sha=record.verified_tree_sha,
    )
    assert result.submission_key is not None
    assert len(result.submission_key) == 64
    assert "/" not in result.submission_key
    assert ":" not in result.submission_key
    assert record.failure_key not in result.submission_key
    assert result.provenance["failure_key"] == record.failure_key
    assert db.get_submission(result.submission_key or "") is None
    assert get_latest_status(db, record.failure_key) == GERRIT_READY


def test_gerrit_submit_record_not_found(tmp_path: Path) -> None:
    db = StateDatabase(tmp_path / "state.sqlite3")

    result = gerrit_submit(_options(db, "missing"))

    assert result.action == "record_not_found"
    assert exit_code_for_submit(result) == 2


def test_gerrit_submit_rejects_latest_non_ready(tmp_path: Path) -> None:
    db, record, base_commit = _record(tmp_path)
    record_status(db, record.failure_key, "REPAIR_EXHAUSTED")

    result = gerrit_submit(
        _options(db, record.verification_id),
        subprocess_runner=SubmitRunner(target_head=base_commit),
    )

    assert result.action == "rejected_not_ready"
    assert exit_code_for_submit(result) == 3


def test_gerrit_submit_rejects_ready_for_different_verification_id(tmp_path: Path) -> None:
    db, record, base_commit = _record(tmp_path)
    newer = VerificationRecord(**{**record.__dict__, "verification_id": "verify-2"})
    write_pass_record(db, newer)

    result = gerrit_submit(
        _options(db, record.verification_id),
        subprocess_runner=SubmitRunner(target_head=base_commit),
    )

    assert result.action == "rejected_not_ready"
    assert "different verification_id" in (result.reason or "")


def test_gerrit_submit_rejects_commit_or_tree_mismatch(tmp_path: Path) -> None:
    db, record, base_commit = _record(tmp_path)
    _git(["reset", "--hard", "HEAD~1"], Path(record.worktree_path))

    result = gerrit_submit(
        _options(db, record.verification_id),
        subprocess_runner=SubmitRunner(target_head=base_commit),
    )

    assert result.action == "rejected_verification_mismatch"


def test_gerrit_submit_rejects_tracked_dirty_worktree(tmp_path: Path) -> None:
    db, record, base_commit = _record(tmp_path)
    (Path(record.worktree_path) / "src" / "main.c").write_text(
        "int main(void) { return 2; }\n",
        encoding="utf-8",
    )

    result = gerrit_submit(
        _options(db, record.verification_id),
        subprocess_runner=SubmitRunner(target_head=base_commit),
    )

    assert result.action == "rejected_worktree_dirty"


def test_gerrit_submit_rejects_staged_dirty_worktree(tmp_path: Path) -> None:
    db, record, base_commit = _record(tmp_path)
    (Path(record.worktree_path) / "src" / "staged.c").write_text("int staged;\n", encoding="utf-8")
    _git(["add", "src/staged.c"], Path(record.worktree_path))

    result = gerrit_submit(
        _options(db, record.verification_id),
        subprocess_runner=SubmitRunner(target_head=base_commit),
    )

    assert result.action == "rejected_worktree_dirty"


def test_gerrit_submit_rejects_missing_worktree_without_patch_fallback(tmp_path: Path) -> None:
    db, record, base_commit = _record(tmp_path)
    subprocess.run(["rm", "-rf", record.worktree_path], check=True)

    result = gerrit_submit(
        _options(db, record.verification_id),
        subprocess_runner=SubmitRunner(target_head=base_commit),
    )

    assert result.action == "rejected_worktree_missing"


def test_gerrit_submit_warns_on_target_branch_drift(tmp_path: Path) -> None:
    db, record, _base_commit = _record(tmp_path)

    result = gerrit_submit(
        _options(db, record.verification_id),
        subprocess_runner=SubmitRunner(target_head="f" * 40),
    )

    assert result.action == "dry_run"
    assert any(warning.startswith("target_branch_drifted") for warning in result.warnings)


def test_gerrit_submit_marks_dry_run_unverified_when_ls_remote_fails(tmp_path: Path) -> None:
    db, record, _base_commit = _record(tmp_path)

    result = gerrit_submit(
        _options(db, record.verification_id),
        subprocess_runner=SubmitRunner(target_head=None, ls_remote_returncode=1),
    )

    assert result.action == "dry_run_unverified_remote"
    assert result.command_argv == _expected_push_command(record)
    assert result.reason is not None
    assert "remote state could not be verified" in result.reason
    assert "ls-remote failed" in result.reason
    assert any(warning.startswith("target_head_unknown") for warning in result.warnings)


def test_gerrit_submit_marks_dry_run_unverified_when_ls_remote_raises(tmp_path: Path) -> None:
    db, record, _base_commit = _record(tmp_path)

    result = gerrit_submit(
        _options(db, record.verification_id),
        subprocess_runner=SubmitRunner(
            target_head=None,
            ls_remote_exception=OSError("network unavailable"),
        ),
    )

    assert result.action == "dry_run_unverified_remote"
    assert result.command_argv == _expected_push_command(record)
    assert any(
        warning.startswith("target_head_unknown:network unavailable")
        for warning in result.warnings
    )


def test_gerrit_submit_marks_dry_run_unverified_when_target_head_missing(tmp_path: Path) -> None:
    db, record, _base_commit = _record(tmp_path)

    result = gerrit_submit(
        _options(db, record.verification_id),
        subprocess_runner=SubmitRunner(target_head=None),
    )

    assert result.action == "dry_run_unverified_remote"
    assert result.command_argv == _expected_push_command(record)
    assert any(warning == "target_head_unknown:not_found" for warning in result.warnings)


def test_gerrit_submit_marks_dry_run_unverified_for_sandbox_target(tmp_path: Path) -> None:
    db, record, _base_commit = _record(tmp_path)

    result = gerrit_submit(
        _options(
            db,
            record.verification_id,
            submit_target="refs/heads/sandbox/ci-user/demo",
        ),
        subprocess_runner=SubmitRunner(target_head=record.base_commit),
    )

    assert result.action == "dry_run_unverified_remote"
    assert result.command_argv == [
        "git",
        "-C",
        record.worktree_path,
        "push",
        "ssh://ci-user@review.tizen.org:29418/platform/test/demo",
        "HEAD:refs/heads/sandbox/ci-user/demo",
    ]
    assert any(
        warning == "target_head_unknown:sandbox_target_not_checked"
        for warning in result.warnings
    )


def test_gerrit_submit_skips_duplicate_submission_key(tmp_path: Path) -> None:
    db, record, base_commit = _record(tmp_path)
    submission_key = build_submission_key(
        failure_key=record.failure_key,
        verified_tree_sha=record.verified_tree_sha,
    )
    db.insert_submission(
        submission_key=submission_key,
        verification_id=record.verification_id,
        action="submitted",
    )

    result = gerrit_submit(
        _options(db, record.verification_id),
        subprocess_runner=SubmitRunner(target_head=base_commit),
    )

    assert result.action == "skipped_duplicate"


def test_gerrit_submit_skips_duplicate_before_unverified_remote_action(tmp_path: Path) -> None:
    db, record, _base_commit = _record(tmp_path)
    submission_key = build_submission_key(
        failure_key=record.failure_key,
        verified_tree_sha=record.verified_tree_sha,
    )
    db.insert_submission(
        submission_key=submission_key,
        verification_id=record.verification_id,
        action="submitted",
    )

    result = gerrit_submit(
        _options(db, record.verification_id),
        subprocess_runner=SubmitRunner(target_head=None, ls_remote_returncode=1),
    )

    assert result.action == "skipped_duplicate"
    assert any(warning.startswith("target_head_unknown") for warning in result.warnings)


def test_gerrit_submit_submit_mode_is_rejected_without_push(tmp_path: Path) -> None:
    db, record, base_commit = _record(tmp_path)
    runner = SubmitRunner(target_head=base_commit)

    result = gerrit_submit(
        _options(db, record.verification_id, mode="submit"),
        subprocess_runner=runner,
    )

    assert result.action == "rejected_submit_not_enabled"
    assert all("push" not in command for command in runner.commands)
    assert exit_code_for_submit(result) == 3


def test_release_verified_worktree_removes_protection(tmp_path: Path) -> None:
    db, record, _base_commit = _record(tmp_path)

    result = release_verified_worktree(db, record.verification_id)

    assert result.action == "released"
    assert result.released is True
    assert not (Path(record.worktree_path) / PROTECTED_FILENAME).exists()
    assert exit_code_for_release(result) == 0
