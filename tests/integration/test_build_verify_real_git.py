from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from ci_triage.verify.build_verify import (
    BuildVerifyOptions,
    _format_and_apply_patch,
    build_verify,
)
from ci_triage.verify.workspace import (
    MARKER_FILENAME,
    PROTECTED_FILENAME,
    DisposableWorktree,
    WorkspaceViolation,
    cleanup_worktree,
    create_worktree,
    mark_worktree_protected,
)
from tizen_ci_shared.state import StateDatabase, get_latest_status, get_record

if shutil.which("git") is None:
    pytest.skip("git not available", allow_module_level=True)

pytestmark = pytest.mark.integration


class RealGitGbsRunner:
    def __init__(
        self,
        *,
        gbs_returncode: int = 0,
        gbs_stdout: str = "gbs ok\n",
        gbs_stderr: str = "",
        side_effect: Callable[[Path], None] | None = None,
    ) -> None:
        self.gbs_returncode = gbs_returncode
        self.gbs_stdout = gbs_stdout
        self.gbs_stderr = gbs_stderr
        self.side_effect = side_effect
        self.gbs_commands: list[list[str]] = []
        self.gbs_cwds: list[Path] = []

    def __call__(self, args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if isinstance(args, list) and args and Path(str(args[0])).name == "gbs":
            cwd = kwargs.get("cwd")
            cwd_path = cwd if isinstance(cwd, Path) else Path(str(cwd))
            self.gbs_commands.append([str(item) for item in args])
            self.gbs_cwds.append(cwd_path)
            if self.side_effect is not None:
                self.side_effect(cwd_path)
            return subprocess.CompletedProcess(
                args,
                self.gbs_returncode,
                stdout=self.gbs_stdout,
                stderr=self.gbs_stderr,
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


def make_repo(tmp_path: Path, files: dict[str, str]) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(["init"], repo)
    git(["config", "user.email", "ci-triage-test@example.invalid"], repo)
    git(["config", "user.name", "CI Triage Test"], repo)
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    git(["add", "."], repo)
    git(["commit", "-m", "base"], repo)
    return repo, git_stdout(["rev-parse", "HEAD"], repo)


def write_json(path: Path, data: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def edit_spec(tmp_path: Path, edits: list[dict[str, object]]) -> Path:
    return write_json(
        tmp_path / "edit_spec.json",
        {
            "schema_version": "gbs_patch_suggest/edit-spec/v1",
            "patch_name": "candidate.patch",
            "edits": edits,
        },
    )


def default_edit_spec(tmp_path: Path) -> Path:
    return edit_spec(
        tmp_path,
        [
            {
                "file": "src/main.c",
                "line": 1,
                "old": "return 0",
                "new": "return 1",
            }
        ],
    )


def build_options(
    tmp_path: Path,
    *,
    repo: Path,
    base_commit: str,
    edit_spec_path: Path,
    iter_index: int = 1,
    state_db: StateDatabase | None = None,
    output_name: str = "out",
    arch: str = "standard-aarch64",
) -> BuildVerifyOptions:
    gbs_conf = tmp_path / f"{output_name}.gbs.conf"
    gbs_conf.write_text("[general]\n", encoding="utf-8")
    baseline = write_json(tmp_path / f"{output_name}.baseline.json", {"primary_error": {}})
    return BuildVerifyOptions(
        src_clean=repo,
        base_commit=base_commit,
        edit_spec_path=edit_spec_path,
        gbs_conf=gbs_conf,
        package="demo",
        workspace_root=tmp_path / "workspaces",
        baseline_evidence=baseline,
        output_dir=tmp_path / output_name,
        iter_index=iter_index,
        wall_timeout=30,
        state_db=state_db or StateDatabase(tmp_path / "state.sqlite3"),
        ci_system="quickbuild",
        build_id="1095003",
        project="platform/test/demo",
        branch="tizen",
        arch=arch,
    )


def test_create_uses_disposable_copy_with_real_git(tmp_path: Path) -> None:
    repo, base_commit = make_repo(
        tmp_path,
        {"src/main.c": "int main(void) { return 0; }\n"},
    )
    (repo / "src" / "main.c").write_text("int main(void) { return 99; }\n", encoding="utf-8")
    git(["add", "src/main.c"], repo)
    git(["commit", "-m", "later"], repo)
    (repo / "untracked.tmp").write_text("noise\n", encoding="utf-8")

    handle = create_worktree(str(repo), base_commit, str(tmp_path / "workspaces"), 1)
    copy = Path(handle.path)

    assert (copy / ".git").is_dir()
    assert git_stdout(["rev-parse", "HEAD"], copy) == base_commit
    assert (copy / "src" / "main.c").read_text(encoding="utf-8") == (
        "int main(void) { return 0; }\n"
    )
    assert not (copy / "untracked.tmp").exists()
    assert (copy / MARKER_FILENAME).is_file()
    assert git_stdout(["status", "--porcelain"], copy) == ""


def test_format_and_apply_patch_accepts_relative_output_patch_with_real_git(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, base_commit = make_repo(
        tmp_path,
        {"src/main.c": "int main(void) { return 0; }\n"},
    )
    handle = create_worktree(str(repo), base_commit, str(tmp_path / "workspaces"), 1)
    monkeypatch.chdir(tmp_path)

    result = _format_and_apply_patch(
        default_edit_spec(tmp_path),
        src_root=Path(handle.path),
        output_patch=Path("relative-audit/candidate.patch"),
        subprocess_runner=subprocess.run,
    )

    assert result.error is None
    assert (Path(handle.path) / "src" / "main.c").read_text(encoding="utf-8") == (
        "int main(void) { return 1; }\n"
    )


def test_build_verify_pass_uses_real_git_and_captures_changed_paths_and_gbs_command(
    tmp_path: Path,
) -> None:
    repo, base_commit = make_repo(
        tmp_path,
        {
            "src/main.c": "int main(void) { return 0; }\n",
            "src/other.c": "int other(void) { return 0; }\n",
        },
    )
    spec = edit_spec(
        tmp_path,
        [
            {"file": "src/main.c", "line": 1, "old": "return 0", "new": "return 1"},
            {"file": "src/other.c", "line": 1, "old": "return 0", "new": "return 2"},
        ],
    )
    options = build_options(
        tmp_path,
        repo=repo,
        base_commit=base_commit,
        edit_spec_path=spec,
        arch="standard-armv7l",
    )
    runner = RealGitGbsRunner()

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "PASS"
    assert result.verification_id is not None
    assert result.verified_commit_sha
    assert result.verified_tree_sha
    assert result.actual_changed_paths == ["src/main.c", "src/other.c"]
    assert result.worktree_path is not None
    assert (Path(result.worktree_path) / ".git").is_dir()
    assert git_stdout(["status", "--porcelain"], Path(result.worktree_path)) == ""
    record = get_record(options.state_db, result.verification_id)
    assert record is not None
    assert get_latest_status(options.state_db, record.failure_key) == "GERRIT_READY"
    assert runner.gbs_commands == [
        [
            "gbs",
            "-c",
            str(options.gbs_conf),
            "build",
            "-A",
            "armv7l",
            "--include-all",
        ]
    ]
    assert "--package" not in runner.gbs_commands[0]
    assert runner.gbs_cwds == [Path(result.worktree_path)]


def test_verified_tree_sha_is_reproducible_with_real_git(tmp_path: Path) -> None:
    repo, base_commit = make_repo(
        tmp_path,
        {"src/main.c": "int main(void) { return 0; }\n"},
    )
    spec = default_edit_spec(tmp_path)
    state_db = StateDatabase(tmp_path / "state.sqlite3")

    first = build_verify(
        build_options(
            tmp_path,
            repo=repo,
            base_commit=base_commit,
            edit_spec_path=spec,
            iter_index=1,
            state_db=state_db,
            output_name="out1",
        ),
        subprocess_runner=RealGitGbsRunner(),
    )
    second = build_verify(
        build_options(
            tmp_path,
            repo=repo,
            base_commit=base_commit,
            edit_spec_path=spec,
            iter_index=2,
            state_db=state_db,
            output_name="out2",
        ),
        subprocess_runner=RealGitGbsRunner(),
    )

    assert first.result == "PASS"
    assert second.result == "PASS"
    assert first.verified_tree_sha == second.verified_tree_sha


def test_build_verify_detects_tracked_mutation_after_mock_gbs_success(tmp_path: Path) -> None:
    repo, base_commit = make_repo(
        tmp_path,
        {"src/main.c": "int main(void) { return 0; }\n"},
    )
    options = build_options(
        tmp_path,
        repo=repo,
        base_commit=base_commit,
        edit_spec_path=default_edit_spec(tmp_path),
    )

    def mutate_tracked(cwd: Path) -> None:
        (cwd / "src" / "main.c").write_text("int main(void) { return 2; }\n", encoding="utf-8")

    result = build_verify(options, subprocess_runner=RealGitGbsRunner(side_effect=mutate_tracked))

    assert result.result == "FAIL"
    assert result.failure_stage == "build_mutated_source"
    assert result.actual_changed_paths == ["src/main.c"]


def test_build_verify_rejects_unexpected_paths_using_real_git_diff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, base_commit = make_repo(
        tmp_path,
        {"src/main.c": "int main(void) { return 0; }\n"},
    )
    options = build_options(
        tmp_path,
        repo=repo,
        base_commit=base_commit,
        edit_spec_path=default_edit_spec(tmp_path),
    )

    def fake_apply(*args: object, src_root: Path, **kwargs: object) -> SimpleNamespace:
        (src_root / "src" / "main.c").write_text(
            "int main(void) { return 1; }\n",
            encoding="utf-8",
        )
        (src_root / "src" / "unexpected.c").write_text("int unexpected;\n", encoding="utf-8")
        return SimpleNamespace(error=None, no_changes=False)

    monkeypatch.setattr("ci_triage.verify.build_verify._format_and_apply_patch", fake_apply)

    result = build_verify(options, subprocess_runner=RealGitGbsRunner())

    assert result.result == "FAIL"
    assert result.failure_stage == "apply_unexpected_paths"
    assert result.actual_changed_paths == ["src/main.c", "src/unexpected.c"]
    assert result.error is not None
    assert "src/unexpected.c" in result.error


def test_protected_marker_is_transparent_to_real_git_dirty_checks(tmp_path: Path) -> None:
    repo, base_commit = make_repo(
        tmp_path,
        {"src/main.c": "int main(void) { return 0; }\n"},
    )
    handle = create_worktree(str(repo), base_commit, str(tmp_path / "workspaces"), 1)

    mark_worktree_protected(handle, verification_id="verify-1", failure_key="failure")
    copy = Path(handle.path)

    assert (copy / PROTECTED_FILENAME).is_file()
    assert git_stdout(["status", "--porcelain"], copy) == ""
    assert git(["diff", "--quiet", "HEAD", "--"], copy, check=False).returncode == 0


def test_cleanup_worktree_real_copy_safety_checks(tmp_path: Path) -> None:
    repo, base_commit = make_repo(
        tmp_path,
        {"src/main.c": "int main(void) { return 0; }\n"},
    )
    root = tmp_path / "workspaces"

    valid = create_worktree(str(repo), base_commit, str(root), 1)
    cleanup_worktree(valid)
    assert not Path(valid.path).exists()

    missing_marker = create_worktree(str(repo), base_commit, str(root), 2)
    Path(missing_marker.marker_path).unlink()
    with pytest.raises(WorkspaceViolation, match="missing"):
        cleanup_worktree(missing_marker)

    mismatched_root = create_worktree(str(repo), base_commit, str(root), 3)
    bad_root_handle = replace(mismatched_root, workspace_root=str(tmp_path / "other-root"))
    with pytest.raises(WorkspaceViolation, match="workspace_root"):
        cleanup_worktree(bad_root_handle)

    outside = tmp_path / "outside-copy"
    outside.mkdir()
    outside_marker = outside / MARKER_FILENAME
    outside_marker.write_text(
        json.dumps({"workspace_root": str(root.resolve())}) + "\n",
        encoding="utf-8",
    )
    outside_handle = DisposableWorktree(
        path=str(outside),
        baseline_repo=str(repo.resolve()),
        base_commit=base_commit,
        workspace_root=str(root.resolve()),
        iter_index=4,
        marker_path=str(outside_marker),
    )
    with pytest.raises(WorkspaceViolation, match="outside"):
        cleanup_worktree(outside_handle)
