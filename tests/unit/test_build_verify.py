from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest
from ci_triage.state import StateDatabase, get_latest_status, get_record
from ci_triage.verify.build_verify import BuildVerifyOptions, build_verify


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

    def __call__(self, args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if isinstance(args, list) and args and args[0] == "gbs":
            self.events.append("gbs")
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


def test_pass_writes_verification_record_and_commits_before_build(tmp_path: Path) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(returncode=0, stdout="PASS\n")

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "PASS"
    assert result.verification_id is not None
    assert result.verified_commit_sha
    assert result.verified_tree_sha
    record = get_record(options.state_db, result.verification_id)
    assert record is not None
    assert record.verified_commit_sha == result.verified_commit_sha
    assert record.verified_tree_sha == result.verified_tree_sha
    assert record.project == "platform/test/demo"
    assert get_latest_status(options.state_db, record.failure_key) == "GERRIT_READY"
    assert runner.events.index("commit") < runner.events.index("gbs")
    assert Path(result.build_log or "").is_file()
    assert (options.output_dir / "audit" / "baseline_evidence.json").is_file()


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

    monkeypatch.setattr("ci_triage.verify.build_verify._analyze_failure", fake_analyze)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.failure_class == "source_repairable"
    assert result.repair_allowed is True
    assert result.evidence is not None


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

    monkeypatch.setattr("ci_triage.verify.build_verify._analyze_failure", fake_analyze)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.failure_class == "toolchain"
    assert result.repair_allowed is False


def test_build_mutated_tracked_source_after_commit_fails(tmp_path: Path) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(returncode=0, mutate_tracked=True)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.failure_stage == "build_mutated_source"
    assert result.failure_class == "build_mutated_source"
    assert result.repair_allowed is False


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
    assert "gbs" not in runner.events


def test_apply_failure_fails_before_build(tmp_path: Path) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(fail_apply=True)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.failure_stage == "apply_failed"
    assert "gbs" not in runner.events


def test_gbs_timeout_fails_without_repair(tmp_path: Path) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(timeout=True)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.failure_stage == "build_timeout"
    assert result.repair_allowed is False


def test_unexpected_changed_paths_are_checked_before_no_effective_changes(
    tmp_path: Path,
) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(add_unexpected=True)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.failure_stage == "apply_unexpected_paths"
    assert result.error is not None
    assert "src/unexpected.c" in result.error
    assert "gbs" not in runner.events


def test_no_effective_changes_fails_before_build(tmp_path: Path) -> None:
    options = _options(tmp_path, edit_spec=_edit_spec(tmp_path, old="return 0", new="return 0"))
    runner = GbsRunner()

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "FAIL"
    assert result.failure_stage == "no_effective_changes"
    assert "gbs" not in runner.events


def test_marker_is_excluded_from_actual_changed_paths(tmp_path: Path) -> None:
    options = _options(tmp_path)
    runner = GbsRunner(returncode=0)

    result = build_verify(options, subprocess_runner=runner)

    assert result.result == "PASS"
    assert result.error is None
