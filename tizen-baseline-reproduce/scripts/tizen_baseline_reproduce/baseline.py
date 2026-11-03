"""Locked, uncharged baseline builds using the existing runner and analyzer."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, TextIO

from gbs_build_skill.runner import BuildOptions, run_gbs_build
from tizen_build_verify.workspace import create_worktree
from tizen_campaign_core import campaign_state as state
from tizen_campaign_core import reproduce
from tizen_campaign_core._campaign_io import JsonParser, analyze, config, lock, sha256
from tizen_campaign_core._campaign_workspace import (
    _StepError,
    _unit_hash,
    _validate_source_identity,
)
from tizen_campaign_core._sandbox_git import SandboxGit
from tizen_campaign_core.campaign_lifecycle import is_abandoned
from tizen_ci_shared.state import StateDatabase
from tizen_ci_shared.workspace import cleanup_disposable_copy
from tizen_convergence_judge.convergence import primary_fingerprint

BASELINE_TOOLING_FAILED = "BASELINE_TOOLING_FAILED"
EMPTY = dict(
    schema_version="evidence_packet/v1",
    synthetic=True,
    reason="baseline_pass",
    primary_error=None,
    error_clusters=dict(schema_version="error_clusters/v1", clusters=[], truncated=False),
    cascade_summary="",
    root_cause_candidates=[],
)


def _identity_runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return SandboxGit().run(Path(argv[2]), *argv[3:])


def run(args: Any) -> tuple[int, dict[str, Any]]:
    settings = config(args.config)
    db = StateDatabase(args.state_db)
    arch = state.ARCH_RAW_TO_NORM.get(args.arch)
    if arch is None or args.wall_timeout < 1:
        raise ValueError("invalid arch or timeout")
    root = Path(settings["campaign_workspace"]).resolve() / _unit_hash(args.campaign_unit_key)
    with lock(root / arch / ".repair_step.lock"):
        unit = state.get_unit(db, args.campaign_unit_key)
        if unit is None:
            raise ValueError("unknown unit")
        if is_abandoned(db, unit.campaign_unit_key):
            raise _StepError("REJECTED_UNIT_ABANDONED", "unit abandoned", 4)
        if (
            args.package != unit.spec_name
            or args.base_commit != unit.base_commit
            or args.profile != unit.toolchain_profile
        ):
            raise ValueError("identity arguments differ from unit")
        if args.gbs_conf.resolve() != Path(settings["clang_conf_path"]).resolve():
            raise ValueError("gbs-conf differs from config")
        _validate_source_identity(args.src_clean, unit, subprocess_runner=_identity_runner)
        evidence_ci = Path(unit.ci_evidence_ref or "").resolve()
        try:
            if sha256(evidence_ci) != unit.ci_evidence_sha256 or (
                args.evidence_ci is not None
                and (
                    args.evidence_ci.resolve() != evidence_ci
                    or sha256(args.evidence_ci) != unit.ci_evidence_sha256
                )
            ):
                raise ValueError("CI evidence mismatch")
            ci = json.loads(evidence_ci.read_text())
        except (OSError, ValueError) as exc:
            raise _StepError(
                "REJECTED_CI_EVIDENCE_MISMATCH", "CI evidence anchor differs", 4
            ) from exc
        primary_arch = state.ARCH_RAW_TO_NORM[unit.primary_arch or ""]
        primary = state.latest_reproduce(db, unit.campaign_unit_key, arch_norm=primary_arch)
        is_primary = arch == primary_arch
        if not is_primary and primary is None:
            raise _StepError("REJECTED_PRIMARY_BASELINE_MISSING", "run primary first", 4)
        output = args.output_dir.resolve()
        output.mkdir(parents=True, exist_ok=True)
        workspace = output / "baseline_ws"
        path = workspace / "iter_0"
        if path.exists():
            cleanup_disposable_copy(str(path), str(workspace))
            state.append_event(
                db,
                unit.campaign_unit_key,
                "WORKSPACE_CLEANUP",
                dict(paths=[str(path)], reason="baseline_residual"),
            )
        state.append_status(db, unit.campaign_unit_key, "BASELINE_RUNNING")
        conf_sha = sha256(args.gbs_conf)
        try:
            handle = create_worktree(str(args.src_clean), unit.base_commit, str(workspace), 0)
            result = run_gbs_build(
                BuildOptions(
                    conf=args.gbs_conf.resolve(),
                    arch=arch,
                    include_all=True,
                    output_log=output / "baseline.log",
                    timeout=args.wall_timeout,
                    cwd=Path(handle.path),
                )
            )
            if result.timed_out or result.exit_code == 127:
                raise _StepError(BASELINE_TOOLING_FAILED, "build tooling failed", 5)
            if result.exit_code == 0:
                local_path = output / "empty_baseline.json"
                local_path.write_bytes(
                    (
                        json.dumps(EMPTY, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                        + "\n"
                    ).encode("utf-8")
                )
                local = EMPTY
                outcome = "baseline_pass"
            else:
                local_path = analyze(
                    result.analysis_log_path or result.log_path, output / "ev_local", src_root=path
                )
                local = json.loads(local_path.read_text())
                outcome = "different_failure"
            reference = ci
            if not is_primary:
                assert primary is not None
                primary_payload = primary["payload"]
                assert isinstance(primary_payload, dict)
                reference = json.loads(Path(str(primary_payload["evidence_local"])).read_text())
            comparison = reproduce.check(
                reference,
                local,
                package=unit.spec_name,
                arch_norm=arch,
                toolchain_profile=unit.toolchain_profile,
            )
            if result.exit_code != 0:
                if is_primary:
                    outcome = "matched" if comparison.reproduced else "different_failure"
                else:
                    local_fp = primary_fingerprint(local, touched_files=None)
                    reference_fp = primary_fingerprint(reference, touched_files=None)
                    outcome = (
                        "matched"
                        if local_fp is not None and local_fp == reference_fp
                        else "different_failure"
                    )
            payload = dict(
                arch_norm=arch,
                outcome=outcome,
                evidence_local=str(local_path),
                evidence_sha256=sha256(local_path),
                synthetic_zero_error=outcome == "baseline_pass",
                gbs_conf_sha256=conf_sha,
                ci_evidence_sha256_used=unit.ci_evidence_sha256,
                build_log=str(result.analysis_log_path or result.log_path),
                basis=comparison.basis,
            )
            state.append_event(db, unit.campaign_unit_key, "REPRODUCE", payload)
            code = 0
            if is_primary and outcome != "matched":
                state.append_status(db, unit.campaign_unit_key, "NOT_REPRODUCED")
                code = 4
            elif state.gate_view(db, unit.campaign_unit_key).reproduced:
                state.append_status(db, unit.campaign_unit_key, "BASELINE_REPRODUCED")
            return code, dict(
                payload, is_primary=is_primary, error_code="NOT_REPRODUCED" if code else None
            )
        except _StepError:
            raise
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            raise _StepError(BASELINE_TOOLING_FAILED, type(exc).__name__, 5) from exc
        finally:
            if path.exists() and not args.keep_copy:
                cleanup_disposable_copy(str(path), str(workspace))


def main(argv: list[str], *, stdout: TextIO) -> int:
    parser = JsonParser(prog="tizen_baseline_reproduce baseline-reproduce")
    for name in ("state-db", "config", "src-clean", "gbs-conf", "output-dir"):
        parser.add_argument("--" + name, required=True, type=Path)
    for name in ("campaign-unit-key", "base-commit", "package", "arch", "profile"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--evidence-ci", type=Path)
    parser.add_argument("--wall-timeout", type=int, default=7200)
    parser.add_argument("--keep-copy", action="store_true")
    try:
        code, result = run(parser.parse_args(argv))
    except _StepError as exc:
        code, result = exc.exit_code, dict(error_code=exc.code, reason=exc.reason)
    except state.CampaignStateBusy as exc:
        code, result = 4, dict(error_code="CAMPAIGN_STATE_BUSY", reason=str(exc))
    except state.StateInconsistent as exc:
        code, result = 4, dict(error_code="REJECTED_STATE_INCONSISTENT", reason=str(exc))
    except (OSError, ValueError) as exc:
        code, result = 2, dict(error_code="INVALID_ARGS", reason=str(exc))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), file=stdout)
    return code
