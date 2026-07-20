"""Dry-run Gerrit submission gate for verified CI triage repairs.

Stage 1 deliberately has no push path. This module only verifies that the
worktree still matches the PASS verification record and prints the push command a
human or later Stage 2 service may run.
"""

from __future__ import annotations

import json
import shlex
import subprocess
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ci_triage.state import (
    GERRIT_READY,
    StateDatabase,
    VerificationRecord,
    build_submission_key,
    get_latest_status_row,
    get_record,
)
from ci_triage.verify.workspace import release_worktree_protection

SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class GerritSubmitOptions:
    verification_id: str
    state_db: StateDatabase
    gerrit_host: str
    gerrit_port: str
    gerrit_user: str
    submit_target: str
    submit_mode: str = "dry-run"
    git_ssh_command: str | None = None


@dataclass(frozen=True)
class GerritSubmitResult:
    action: str
    verification_id: str
    submission_key: str | None
    submit_target: str | None
    submit_mode: str | None
    command: str | None
    command_argv: list[str]
    warnings: list[str]
    provenance: dict[str, str]
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True)
class ReleaseWorktreeResult:
    action: str
    verification_id: str
    worktree_path: str | None
    released: bool
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


def gerrit_submit(
    options: GerritSubmitOptions,
    *,
    subprocess_runner: SubprocessRunner = subprocess.run,
) -> GerritSubmitResult:
    """Validate a verified worktree and return a dry-run Gerrit push command."""

    record = get_record(options.state_db, options.verification_id)
    if record is None:
        return _result(
            action="record_not_found",
            verification_id=options.verification_id,
            reason="verification record does not exist",
            options=options,
        )

    submission_key = build_submission_key(
        failure_key=record.failure_key,
        verified_tree_sha=record.verified_tree_sha,
    )
    latest = get_latest_status_row(options.state_db, record.failure_key)
    if latest is None or latest.status != GERRIT_READY:
        return _record_result(
            action="rejected_not_ready",
            record=record,
            submission_key=submission_key,
            options=options,
            reason="latest status is not GERRIT_READY",
        )
    if latest.verification_id != options.verification_id:
        return _record_result(
            action="rejected_not_ready",
            record=record,
            submission_key=submission_key,
            options=options,
            reason="latest GERRIT_READY belongs to a different verification_id",
        )

    worktree = Path(record.worktree_path)
    if not worktree.is_dir():
        return _record_result(
            action="rejected_worktree_missing",
            record=record,
            submission_key=submission_key,
            options=options,
            reason="verified worktree is missing; refusing to fall back to patch files",
        )

    mismatch = _verification_mismatch(record, worktree, subprocess_runner)
    if mismatch is not None:
        return _record_result(
            action="rejected_verification_mismatch",
            record=record,
            submission_key=submission_key,
            options=options,
            reason=mismatch,
        )
    dirty = _dirty_reason(worktree, subprocess_runner)
    if dirty is not None:
        return _record_result(
            action="rejected_worktree_dirty",
            record=record,
            submission_key=submission_key,
            options=options,
            reason=dirty,
        )

    warnings = _target_warnings(record, options, subprocess_runner)
    if options.submit_mode == "submit":
        return _record_result(
            action="rejected_submit_not_enabled",
            record=record,
            submission_key=submission_key,
            options=options,
            reason="Stage 1 submit mode is disabled; no git push was executed",
            warnings=warnings,
        )

    if options.state_db.get_submission(submission_key) is not None:
        return _record_result(
            action="skipped_duplicate",
            record=record,
            submission_key=submission_key,
            options=options,
            reason="submission key already exists",
            warnings=warnings,
        )

    command_argv = _push_command(record, options)
    remote_unknown = _target_head_unknown_warning(warnings)
    return _record_result(
        action="dry_run_unverified_remote" if remote_unknown else "dry_run",
        record=record,
        submission_key=submission_key,
        options=options,
        command_argv=command_argv,
        reason=(
            "remote state could not be verified "
            f"({remote_unknown}); duplicate/drift checks did not run"
            if remote_unknown
            else None
        ),
        warnings=[
            *warnings,
            (
                "verified worktree remains protected; run "
                "ci_triage release-worktree --verification-id "
                f"{options.verification_id} --state-db <path> when it is no longer needed"
            ),
        ],
    )


def _target_head_unknown_warning(warnings: list[str]) -> str | None:
    for warning in warnings:
        if warning.startswith("target_head_unknown:"):
            reason = warning.removeprefix("target_head_unknown:")
            if reason == "ls_remote_failed":
                return "ls-remote failed"
            return reason.replace("_", " ")
    return None


def release_verified_worktree(
    db: StateDatabase,
    verification_id: str,
) -> ReleaseWorktreeResult:
    """Release the protected worktree marker for one verification record."""

    record = get_record(db, verification_id)
    if record is None:
        return ReleaseWorktreeResult(
            action="record_not_found",
            verification_id=verification_id,
            worktree_path=None,
            released=False,
            reason="verification record does not exist",
        )
    released = release_worktree_protection(record.worktree_path)
    return ReleaseWorktreeResult(
        action="released" if released else "not_protected",
        verification_id=verification_id,
        worktree_path=record.worktree_path,
        released=released,
    )


def write_gerrit_submit_result(result: GerritSubmitResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_release_result(result: ReleaseWorktreeResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def exit_code_for_submit(result: GerritSubmitResult) -> int:
    if result.action == "record_not_found":
        return 2
    if result.action.startswith("rejected_"):
        return 3
    return 0


def exit_code_for_release(result: ReleaseWorktreeResult) -> int:
    return 2 if result.action == "record_not_found" else 0


def _verification_mismatch(
    record: VerificationRecord,
    worktree: Path,
    subprocess_runner: SubprocessRunner,
) -> str | None:
    try:
        head = _git_stdout(worktree, ["rev-parse", "HEAD"], subprocess_runner)
        tree = _git_stdout(worktree, ["rev-parse", "HEAD^{tree}"], subprocess_runner)
    except subprocess.CalledProcessError as exc:
        return f"failed to read verified git object: exit {exc.returncode}"
    if head != record.verified_commit_sha:
        return "verified commit SHA does not match worktree HEAD"
    if tree != record.verified_tree_sha:
        return "verified tree SHA does not match worktree HEAD tree"
    return None


def _dirty_reason(worktree: Path, subprocess_runner: SubprocessRunner) -> str | None:
    tracked = _run_git(worktree, ["diff", "--quiet", "HEAD", "--"], subprocess_runner)
    if tracked.returncode != 0:
        return "tracked worktree changes exist after verified commit"
    staged = _run_git(worktree, ["diff", "--cached", "--quiet"], subprocess_runner)
    if staged.returncode != 0:
        return "staged changes exist after verified commit"
    return None


def _target_warnings(
    record: VerificationRecord,
    options: GerritSubmitOptions,
    subprocess_runner: SubprocessRunner,
) -> list[str]:
    branch = _target_branch(options.submit_target)
    if branch is None:
        return ["target_head_unknown:sandbox_target_not_checked"]
    remote = _remote_url(record, options)
    try:
        completed = subprocess_runner(
            ["git", "ls-remote", remote, f"refs/heads/{branch}"],
            check=False,
            text=True,
            capture_output=True,
            env=_subprocess_env(options.git_ssh_command),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return [f"target_head_unknown:{exc}"]
    if completed.returncode != 0:
        return ["target_head_unknown:ls_remote_failed"]
    first = (completed.stdout or "").splitlines()[0:1]
    if not first:
        return ["target_head_unknown:not_found"]
    target_head = first[0].split()[0]
    if target_head != record.base_commit:
        return [f"target_branch_drifted:{target_head}"]
    return []


def _target_branch(submit_target: str) -> str | None:
    if submit_target.startswith("refs/for/"):
        branch = submit_target.removeprefix("refs/for/")
        return branch.split("%", 1)[0]
    if submit_target.startswith("refs/drafts/"):
        return submit_target.removeprefix("refs/drafts/").split("%", 1)[0]
    if submit_target.startswith("refs/heads/sandbox/"):
        return None
    if submit_target.startswith("refs/heads/"):
        return submit_target.removeprefix("refs/heads/")
    return None


def _push_command(record: VerificationRecord, options: GerritSubmitOptions) -> list[str]:
    return [
        "git",
        "-C",
        record.worktree_path,
        "push",
        _remote_url(record, options),
        f"HEAD:{options.submit_target}",
    ]


def _remote_url(record: VerificationRecord, options: GerritSubmitOptions) -> str:
    return f"ssh://{options.gerrit_user}@{options.gerrit_host}:{options.gerrit_port}/{record.project}"


def _git_stdout(
    worktree: Path,
    args: list[str],
    subprocess_runner: SubprocessRunner,
) -> str:
    completed = _run_git(worktree, args, subprocess_runner, check=True)
    return (completed.stdout or "").strip()


def _run_git(
    worktree: Path,
    args: list[str],
    subprocess_runner: SubprocessRunner,
    *,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess_runner(
        ["git", "-C", str(worktree), *args],
        check=check,
        text=True,
        capture_output=True,
    )


def _result(
    *,
    action: str,
    verification_id: str,
    reason: str,
    options: GerritSubmitOptions,
) -> GerritSubmitResult:
    return GerritSubmitResult(
        action=action,
        verification_id=verification_id,
        submission_key=None,
        submit_target=options.submit_target,
        submit_mode=options.submit_mode,
        command=None,
        command_argv=[],
        warnings=[],
        provenance={},
        reason=reason,
    )


def _record_result(
    *,
    action: str,
    record: VerificationRecord,
    submission_key: str,
    options: GerritSubmitOptions,
    reason: str | None = None,
    command_argv: list[str] | None = None,
    warnings: list[str] | None = None,
) -> GerritSubmitResult:
    argv = command_argv or []
    return GerritSubmitResult(
        action=action,
        verification_id=record.verification_id,
        submission_key=submission_key,
        submit_target=options.submit_target,
        submit_mode=options.submit_mode,
        command=" ".join(shlex.quote(part) for part in argv) if argv else None,
        command_argv=argv,
        warnings=warnings or [],
        provenance={
            "build_id": _build_id_from_failure_key(record.failure_key),
            "failure_key": record.failure_key,
            "base_commit": record.base_commit,
            "verified_commit_sha": record.verified_commit_sha,
            "verified_tree_sha": record.verified_tree_sha,
        },
        reason=reason,
    )


def _build_id_from_failure_key(failure_key: str) -> str:
    parts = failure_key.split("/", 2)
    return parts[1] if len(parts) > 1 else ""


def _subprocess_env(git_ssh_command: str | None) -> dict[str, str] | None:
    if git_ssh_command is None:
        return None
    import os

    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = git_ssh_command
    return env
