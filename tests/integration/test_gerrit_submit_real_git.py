from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest
from ci_triage.state import StateDatabase, VerificationRecord, build_failure_key, write_pass_record
from ci_triage.verify.gerrit_submit import GerritSubmitOptions, gerrit_submit

if shutil.which("git") is None:
    pytest.skip("git not available", allow_module_level=True)

pytestmark = pytest.mark.integration


class RealGitSubmitRunner:
    def __init__(self, *, target_head: str) -> None:
        self.target_head = target_head

    def __call__(self, args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if isinstance(args, list) and args[:2] == ["git", "ls-remote"]:
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=f"{self.target_head}\trefs/heads/tizen\n",
                stderr="",
            )
        return cast(subprocess.CompletedProcess[str], subprocess.run(args, **kwargs))


def git(args: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        text=True,
        capture_output=True,
    )


def git_stdout(args: list[str], cwd: Path) -> str:
    return git(args, cwd).stdout.strip()


def make_verified_repo(tmp_path: Path) -> tuple[Path, str, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(["init"], repo)
    git(["config", "user.email", "ci-triage-test@example.invalid"], repo)
    git(["config", "user.name", "CI Triage Test"], repo)
    (repo / "src").mkdir()
    (repo / "src" / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
    git(["add", "src/main.c"], repo)
    git(["commit", "-m", "base"], repo)
    base_commit = git_stdout(["rev-parse", "HEAD"], repo)
    (repo / "src" / "main.c").write_text("int main(void) { return 1; }\n", encoding="utf-8")
    git(["add", "src/main.c"], repo)
    git(["commit", "-m", "verified"], repo)
    verified_commit = git_stdout(["rev-parse", "HEAD"], repo)
    verified_tree = git_stdout(["rev-parse", "HEAD^{tree}"], repo)
    return repo, base_commit, verified_commit, verified_tree


def write_record(
    tmp_path: Path,
    *,
    repo: Path,
    base_commit: str,
    verified_commit: str,
    verified_tree: str,
) -> tuple[StateDatabase, VerificationRecord]:
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
    return db, record


def options(db: StateDatabase, verification_id: str) -> GerritSubmitOptions:
    return GerritSubmitOptions(
        verification_id=verification_id,
        state_db=db,
        gerrit_host="review.tizen.org",
        gerrit_port="29418",
        gerrit_user="ci-user",
        submit_target="refs/for/tizen%wip",
    )


def test_gerrit_submit_dry_run_uses_real_git_commit_and_tree_checks(tmp_path: Path) -> None:
    repo, base_commit, verified_commit, verified_tree = make_verified_repo(tmp_path)
    db, record = write_record(
        tmp_path,
        repo=repo,
        base_commit=base_commit,
        verified_commit=verified_commit,
        verified_tree=verified_tree,
    )

    result = gerrit_submit(
        options(db, record.verification_id),
        subprocess_runner=RealGitSubmitRunner(target_head=base_commit),
    )

    assert result.action == "dry_run"
    assert result.command_argv[:3] == ["git", "-C", str(repo)]


def test_gerrit_submit_rejects_real_git_commit_tree_mismatch(tmp_path: Path) -> None:
    repo, base_commit, verified_commit, verified_tree = make_verified_repo(tmp_path)
    db, record = write_record(
        tmp_path,
        repo=repo,
        base_commit=base_commit,
        verified_commit=verified_commit,
        verified_tree=verified_tree,
    )
    git(["reset", "--hard", base_commit], repo)

    result = gerrit_submit(
        options(db, record.verification_id),
        subprocess_runner=RealGitSubmitRunner(target_head=base_commit),
    )

    assert result.action == "rejected_verification_mismatch"


def test_gerrit_submit_rejects_real_git_dirty_worktree(tmp_path: Path) -> None:
    repo, base_commit, verified_commit, verified_tree = make_verified_repo(tmp_path)
    db, record = write_record(
        tmp_path,
        repo=repo,
        base_commit=base_commit,
        verified_commit=verified_commit,
        verified_tree=verified_tree,
    )
    (repo / "src" / "main.c").write_text("int main(void) { return 2; }\n", encoding="utf-8")

    result = gerrit_submit(
        options(db, record.verification_id),
        subprocess_runner=RealGitSubmitRunner(target_head=base_commit),
    )

    assert result.action == "rejected_worktree_dirty"
