"""Build verification loop core for CI triage repairs.

This module integrates the Stage 1 filesystem guards, append-only verification
state DB, and failure classifier. ``workspace.py`` provides disposable source
copies with the same handle API used by earlier worktree-based experiments, so
build verification can run gbs from a clean package root without depending on
Git worktree compatibility.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from gbs_patch_suggest.formatter import FormatPatchOptions, format_patch

from ci_triage.runner import discover_sibling_pythonpath
from ci_triage.state import (
    StateDatabase,
    VerificationRecord,
    build_failure_key,
    failure_key_sha12,
    write_pass_record,
)
from ci_triage.verify.edit_spec_guard import EditSpecViolation, validate_edit_spec
from ci_triage.verify.failure_classify import FailureClassification, classify_failure
from ci_triage.verify.workspace import (
    check_disk_and_maybe_cleanup,
    cleanup_worktree,
    create_worktree,
    mark_worktree_protected,
)

SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class BuildVerifyOptions:
    """Inputs for one build-verify attempt."""

    src_clean: Path
    base_commit: str
    edit_spec_path: Path
    gbs_conf: Path
    package: str
    workspace_root: Path
    baseline_evidence: Path
    output_dir: Path
    iter_index: int
    wall_timeout: int
    state_db: StateDatabase
    ci_system: str
    build_id: str
    project: str
    branch: str
    arch: str
    python_executable: str = sys.executable
    extra_pythonpath: tuple[Path, ...] = ()


@dataclass(frozen=True)
class BuildVerifyResult:
    """Machine-readable build-verify result."""

    result: str
    # Actual normalized paths changed by this build-verify attempt. The workflow
    # feeds this into check-convergence as touched_files instead of asking an
    # agent to infer touched files from edit_spec.
    actual_changed_paths: list[str] = field(default_factory=list)
    failure_stage: str | None = None
    failure_class: str | None = None
    repair_allowed: bool | None = None
    verification_id: str | None = None
    verified_commit_sha: str | None = None
    verified_tree_sha: str | None = None
    worktree_path: str | None = None
    build_log: str | None = None
    evidence: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True)
class _ApplyPatchResult:
    error: str | None = None
    no_changes: bool = False


def build_verify(
    options: BuildVerifyOptions,
    *,
    subprocess_runner: SubprocessRunner = subprocess.run,
) -> BuildVerifyResult:
    """Verify one edit spec by applying it, committing it, and running gbs build."""

    failure_key = build_failure_key(
        ci_system=options.ci_system,
        build_id=options.build_id,
        project=options.project,
        branch=options.branch,
        arch=options.arch,
        spec_name=options.package,
        base_commit=options.base_commit,
    )
    options.output_dir.mkdir(parents=True, exist_ok=True)
    audit_dir = options.output_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    if options.baseline_evidence.is_file():
        shutil.copyfile(options.baseline_evidence, audit_dir / "baseline_evidence.json")
    warnings = check_disk_and_maybe_cleanup(str(options.workspace_root))
    if warnings:
        (audit_dir / "workspace_cleanup_warnings.txt").write_text(
            "\n".join(warnings) + "\n",
            encoding="utf-8",
        )

    handle = create_worktree(
        str(options.src_clean),
        options.base_commit,
        str(options.workspace_root),
        options.iter_index,
    )
    edit_spec = _read_json(options.edit_spec_path)
    try:
        validate_edit_spec(edit_spec, handle.path)
    except EditSpecViolation as exc:
        cleanup_worktree(handle)
        return _fail("apply_failed", "not_applicable", False, audit_dir, error=str(exc))

    allowed_paths = _allowed_paths(edit_spec)
    patch_path = audit_dir / "candidate.patch"
    apply_result = _format_and_apply_patch(
        options.edit_spec_path,
        src_root=Path(handle.path),
        output_patch=patch_path,
        subprocess_runner=subprocess_runner,
    )
    if apply_result.no_changes:
        return _fail(
            "no_effective_changes",
            "not_applicable",
            False,
            audit_dir,
            error="edit spec produced no effective worktree changes",
        )
    if apply_result.error is not None:
        return _fail(
            "apply_failed",
            "not_applicable",
            False,
            audit_dir,
            error=apply_result.error,
        )

    diff_check_error = _run_git_diff_check(Path(handle.path), subprocess_runner)
    if diff_check_error is not None:
        return _fail("apply_failed", "not_applicable", False, audit_dir, error=diff_check_error)

    changed_paths = _actual_changed_paths(Path(handle.path), subprocess_runner)
    actual_changed_paths = sorted(changed_paths)
    unexpected = sorted(changed_paths - allowed_paths)
    if unexpected:
        return _fail(
            "apply_unexpected_paths",
            "not_applicable",
            False,
            audit_dir,
            error="unexpected changed paths: " + ", ".join(unexpected),
            actual_changed_paths=actual_changed_paths,
        )
    if not changed_paths:
        return _fail(
            "no_effective_changes",
            "not_applicable",
            False,
            audit_dir,
            error="edit spec produced no effective worktree changes",
        )

    _git(Path(handle.path), ["add", "-A"], subprocess_runner)
    _git(
        Path(handle.path),
        ["commit", "-m", f"CI triage repair: {failure_key_sha12(failure_key)}"],
        subprocess_runner,
    )
    verified_commit_sha = _git_stdout(
        Path(handle.path),
        ["rev-parse", "HEAD"],
        subprocess_runner,
    )
    verified_tree_sha = _git_stdout(
        Path(handle.path),
        ["rev-parse", "HEAD^{tree}"],
        subprocess_runner,
    )

    build_log_path = audit_dir / "gbs_build.log"
    build_result = _run_gbs_build(options, Path(handle.path), subprocess_runner)
    build_log_path.write_text(build_result.stdout + build_result.stderr, encoding="utf-8")

    if build_result.timed_out:
        return BuildVerifyResult(
            result="FAIL",
            actual_changed_paths=actual_changed_paths,
            failure_stage="build_timeout",
            failure_class="build_timeout",
            repair_allowed=False,
            worktree_path=handle.path,
            build_log=str(build_log_path),
            error=build_result.error,
        )

    mutated = _tracked_worktree_mutated(Path(handle.path), subprocess_runner)
    if mutated:
        return BuildVerifyResult(
            result="FAIL",
            actual_changed_paths=actual_changed_paths,
            failure_stage="build_mutated_source",
            failure_class="build_mutated_source",
            repair_allowed=False,
            worktree_path=handle.path,
            build_log=str(build_log_path),
            error="gbs build modified tracked source after verification commit",
        )

    if build_result.returncode != 0:
        evidence_path = _analyze_failure(options, build_log_path, Path(handle.path), audit_dir)
        evidence = _read_json(evidence_path) if evidence_path is not None else {}
        classification = classify_failure(
            evidence,
            build_log=build_log_path.read_text(encoding="utf-8", errors="replace"),
            failure_stage="gbs_build_failed",
        )
        return _classification_fail(
            classification,
            worktree_path=handle.path,
            build_log_path=build_log_path,
            evidence_path=evidence_path,
            actual_changed_paths=actual_changed_paths,
        )

    build_log_text = build_log_path.read_text(encoding="utf-8")
    build_log_hash = _sha256_text(_normalize_build_log(build_log_text))
    record = VerificationRecord(
        verification_id=str(uuid.uuid4()),
        result="PASS",
        timestamp=_git_stdout(
            Path(handle.path),
            ["show", "-s", "--format=%cI", "HEAD"],
            subprocess_runner,
        ),
        failure_key=failure_key,
        base_commit=options.base_commit,
        verified_commit_sha=verified_commit_sha,
        verified_tree_sha=verified_tree_sha,
        canonical_diff_sha256=_canonical_diff_sha256(
            Path(handle.path),
            options.base_commit,
            verified_commit_sha,
            subprocess_runner,
        ),
        patch_sha256=_sha256_file(patch_path),
        edit_spec_sha256=_sha256_file(options.edit_spec_path),
        project=options.project,
        branch=options.branch,
        spec_name=options.package,
        arch=options.arch,
        gbs_conf_sha256=_sha256_file(options.gbs_conf),
        build_log_sha256=build_log_hash,
        worktree_path=handle.path,
        command_line=" ".join(_gbs_command(options)),
    )
    mark_worktree_protected(handle, verification_id=record.verification_id, failure_key=failure_key)
    verification_id = write_pass_record(options.state_db, record)
    return BuildVerifyResult(
        result="PASS",
        actual_changed_paths=actual_changed_paths,
        verification_id=verification_id,
        verified_commit_sha=verified_commit_sha,
        verified_tree_sha=verified_tree_sha,
        worktree_path=handle.path,
        build_log=str(build_log_path),
    )


@dataclass(frozen=True)
class _BuildProcessResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    error: str | None = None


def _format_and_apply_patch(
    edit_spec_path: Path,
    *,
    src_root: Path,
    output_patch: Path,
    subprocess_runner: SubprocessRunner,
) -> _ApplyPatchResult:
    output_patch = output_patch.resolve()
    result = format_patch(
        FormatPatchOptions(
            src_root=src_root,
            edit_spec=edit_spec_path,
            output=output_patch,
            check=True,
        ),
        subprocess_runner=subprocess_runner,
    )
    if result.exit_code != 0:
        if result.error_code == "no_changes":
            return _ApplyPatchResult(no_changes=True)
        return _ApplyPatchResult(error=f"{result.error_code}: {result.error}")
    try:
        _run(
            ["git", "-C", str(src_root), "apply", str(output_patch)],
            subprocess_runner,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        return _ApplyPatchResult(error=f"git apply failed with exit {exc.returncode}")
    return _ApplyPatchResult()


def _run_gbs_build(
    options: BuildVerifyOptions,
    worktree: Path,
    subprocess_runner: SubprocessRunner,
) -> _BuildProcessResult:
    command = _gbs_command(options)
    try:
        completed = _run(
            command,
            subprocess_runner,
            cwd=worktree,
            timeout=options.wall_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return _BuildProcessResult(
            returncode=124,
            stdout=_string_or_empty(exc.stdout),
            stderr=_string_or_empty(exc.stderr),
            timed_out=True,
            error=f"gbs build timed out after {options.wall_timeout}s",
        )
    return _BuildProcessResult(
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )


def _gbs_command(options: BuildVerifyOptions) -> list[str]:
    return [
        "gbs",
        "-c",
        str(options.gbs_conf),
        "build",
        "-A",
        _gbs_arch(options.arch),
        "--include-all",
    ]


def _gbs_arch(arch: str) -> str:
    return arch.removeprefix("standard-")


def _analyze_failure(
    options: BuildVerifyOptions,
    build_log_path: Path,
    worktree: Path,
    audit_dir: Path,
) -> Path | None:
    analyzer_dir = audit_dir / "analyzer_output"
    analyzer_dir.mkdir(parents=True, exist_ok=True)
    command = [
        options.python_executable,
        "-m",
        "gbs_analyzer",
        "analyze",
        str(build_log_path),
        "--src-root",
        str(worktree),
        "--output-dir",
        str(analyzer_dir),
        "--package",
        options.package,
    ]
    env = _build_subprocess_env(options.extra_pythonpath)
    try:
        subprocess.run(command, check=True, text=True, env=env)
    except subprocess.CalledProcessError:
        return None
    evidence_path = analyzer_dir / "evidence_packet.json"
    if not evidence_path.is_file():
        return None
    return evidence_path


def _classification_fail(
    classification: FailureClassification,
    *,
    worktree_path: str,
    build_log_path: Path,
    evidence_path: Path | None,
    actual_changed_paths: list[str],
) -> BuildVerifyResult:
    return BuildVerifyResult(
        result="FAIL",
        actual_changed_paths=actual_changed_paths,
        failure_stage="gbs_build_failed",
        failure_class=classification.failure_class,
        repair_allowed=classification.repair_allowed,
        worktree_path=worktree_path,
        build_log=str(build_log_path),
        evidence=str(evidence_path) if evidence_path is not None else None,
        error=classification.reason,
    )


def _fail(
    failure_stage: str,
    failure_class: str,
    repair_allowed: bool,
    audit_dir: Path,
    *,
    error: str,
    actual_changed_paths: list[str] | None = None,
) -> BuildVerifyResult:
    return BuildVerifyResult(
        result="FAIL",
        actual_changed_paths=actual_changed_paths or [],
        failure_stage=failure_stage,
        failure_class=failure_class,
        repair_allowed=repair_allowed,
        build_log=str(audit_dir / "gbs_build.log"),
        error=error,
    )


def _actual_changed_paths(
    worktree: Path,
    subprocess_runner: SubprocessRunner,
) -> set[str]:
    commands = (
        ["diff", "--name-only", "HEAD", "--"],
        ["diff", "--cached", "--name-only"],
        ["ls-files", "--others", "--exclude-standard"],
    )
    paths: set[str] = set()
    for command in commands:
        output = _git_stdout(worktree, command, subprocess_runner, allow_empty=True)
        paths.update(line for line in output.splitlines() if line)
    return paths


def _tracked_worktree_mutated(
    worktree: Path,
    subprocess_runner: SubprocessRunner,
) -> bool:
    unstaged = _run(
        ["git", "-C", str(worktree), "diff", "--quiet", "HEAD", "--"],
        subprocess_runner,
        check=False,
    )
    staged = _run(
        ["git", "-C", str(worktree), "diff", "--cached", "--quiet"],
        subprocess_runner,
        check=False,
    )
    return unstaged.returncode != 0 or staged.returncode != 0


def _allowed_paths(edit_spec: dict[str, Any]) -> set[str]:
    raw_edits = edit_spec.get("edits")
    if not isinstance(raw_edits, list):
        return set()
    paths: set[str] = set()
    for raw in raw_edits:
        if not isinstance(raw, dict):
            continue
        file_value = raw.get("file")
        if isinstance(file_value, str):
            normalized = os.path.normpath(file_value.replace("\\", "/")).replace("\\", "/")
            paths.add(normalized.strip("/"))
    return paths


def _run_git_diff_check(worktree: Path, subprocess_runner: SubprocessRunner) -> str | None:
    result = _run(
        ["git", "-C", str(worktree), "diff", "--check"],
        subprocess_runner,
        check=False,
    )
    if result.returncode == 0:
        return None
    return result.stdout or result.stderr or "git diff --check failed"


def _canonical_diff_sha256(
    worktree: Path,
    base_commit: str,
    verified_commit_sha: str,
    subprocess_runner: SubprocessRunner,
) -> str:
    diff = _git_stdout(
        worktree,
        ["diff", "--full-index", "--binary", f"{base_commit}..{verified_commit_sha}"],
        subprocess_runner,
        allow_empty=True,
    )
    return _sha256_text(diff)


def _normalize_build_log(text: str) -> str:
    text = re.sub(r"/home/abuild/rpmbuild/BUILD/[^/\s]+", "<BUILD_ROOT>", text)
    text = re.sub(r"/tmp/[^\s]+", "<TMP>", text)
    text = re.sub(r"\b20\d\d-\d\d-\d\d[ T]\d\d:\d\d:\d\d(?:\.\d+)?\b", "<TIMESTAMP>", text)
    text = re.sub(r"\r", "", text)
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"


def _git(
    worktree: Path,
    args: list[str],
    subprocess_runner: SubprocessRunner,
) -> None:
    _run(["git", "-C", str(worktree), *args], subprocess_runner, check=True)


def _git_stdout(
    worktree: Path,
    args: list[str],
    subprocess_runner: SubprocessRunner,
    *,
    allow_empty: bool = False,
) -> str:
    completed = _run(["git", "-C", str(worktree), *args], subprocess_runner, check=True)
    output = completed.stdout or ""
    stripped = output.strip()
    if stripped or allow_empty:
        return stripped
    return ""


def _run(
    command: Sequence[str],
    subprocess_runner: SubprocessRunner,
    *,
    check: bool,
    cwd: Path | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess_runner(
        list(command),
        check=check,
        text=True,
        capture_output=True,
        cwd=cwd,
        timeout=timeout,
    )


def _read_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"expected JSON object: {path}")
    return raw


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="surrogateescape")).hexdigest()


def _build_subprocess_env(extra_pythonpath: Sequence[Path]) -> dict[str, str] | None:
    if not extra_pythonpath:
        return None
    env = os.environ.copy()
    entries = [str(path) for path in extra_pythonpath]
    existing = env.get("PYTHONPATH")
    if existing:
        entries.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(entries)
    return env


def _string_or_empty(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def build_verify_to_json(result: BuildVerifyResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def default_extra_pythonpath() -> tuple[Path, ...]:
    return discover_sibling_pythonpath(
        launcher_path=Path(__file__).resolve().parents[2] / "run_ci_triage.py"
    )
