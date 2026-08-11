"""Atomic campaign repair-step orchestration around the existing build verifier."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
import tempfile
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml
from tizen_ci_shared.classify import (
    REPAIR_AUTO,
    REPAIR_DENIED,
    REPAIR_NEEDS_CONFIRMATION,
)
from tizen_ci_shared.state import StateDatabase, build_failure_key, get_record
from tizen_ci_shared.workspace import (
    WorkspaceViolation,
    cleanup_disposable_copy,
    is_protected,
)

from ci_triage.campaign_state import (
    ARCH_RAW_TO_NORM,
    HELD_FOR_INVESTIGATION,
    BudgetExhausted,
    CampaignStateBusy,
    CampaignStateError,
    ReconcileResult,
    RoundsExhausted,
    StateInconsistent,
    Unit,
    adopt_secondary_target_with_convergence,
    append_event,
    append_status,
    consume_build_invocation,
    create_round,
    get_round,
    get_unit,
    invocations_used,
    latest_reproduce,
    latest_status,
    link_verification_with_convergence,
    reconcile_pass_and_invocations,
)
from ci_triage.previous_evidence import MissingEvidence, ResolvedEvidence, resolve
from ci_triage.verify.build_verify import BuildVerifyOptions, BuildVerifyResult, build_verify
from ci_triage.verify.convergence import ConvergenceResult, check_convergence

EXIT_OK = 0
EXIT_INVALID_ARGS = 5
EXIT_REJECTED = 4
EXIT_TOOLING = 5

REJECTED_IDENTITY_MISMATCH = "REJECTED_IDENTITY_MISMATCH"
REJECTED_PREVIOUS_EVIDENCE_MISSING = "REJECTED_PREVIOUS_EVIDENCE_MISSING"
REJECTED_BASELINE_EVIDENCE_MISMATCH = "REJECTED_BASELINE_EVIDENCE_MISMATCH"
REJECTED_CONF_DRIFT = "REJECTED_CONF_DRIFT"
REJECTED_STATE_INCONSISTENT = "REJECTED_STATE_INCONSISTENT"
REJECTED_ORPHAN_PASS_HELD = "REJECTED_ORPHAN_PASS_HELD"
CAMPAIGN_STATE_BUSY = "CAMPAIGN_STATE_BUSY"

REPAIR_ROUND_RUNNING = "REPAIR_ROUND_RUNNING"
ROUNDS_EXHAUSTED = "ROUNDS_EXHAUSTED"
DENIED = "DENIED"
STALLED = "STALLED"
REGRESSED = "REGRESSED"
_EXECUTABLE_UNIT_STATUSES = frozenset({REPAIR_ROUND_RUNNING})

BuildVerifyFn = Callable[[BuildVerifyOptions], BuildVerifyResult]
ConvergenceFn = Callable[..., ConvergenceResult]
SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class CampaignRepairStepOptions:
    """Authoritative inputs accepted by ``campaign-repair-step``."""

    campaign_unit_key: str
    state_db: StateDatabase
    config_path: Path
    round_index: int
    edit_spec_path: Path
    arch_raw: str
    wall_timeout: int | None = None
    extra_pythonpath: tuple[Path, ...] = ()


@dataclass(frozen=True)
class CampaignRepairStepResult:
    """Fixed stdout schema consumed by the campaign workflow."""

    result: str
    verdict: str
    repair_allowed: str
    failure_class: str | None
    failure_stage: str | None
    adopted: bool
    convergence_reason: str
    previous_basis: str
    round_index: int
    arch_norm: str
    verification_id: str | None
    evidence_path: str | None
    reconciliation: dict[str, list[object]]
    warnings: list[dict[str, str]]
    invocations_used: int
    error_code: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CampaignRepairStepOutcome:
    """Result payload plus the process exit code."""

    result: CampaignRepairStepResult
    exit_code: int


@dataclass(frozen=True)
class _CampaignConfig:
    campaign_workspace: Path
    clang_conf_path: Path
    wall_timeout: int


class _StepError(RuntimeError):
    def __init__(self, code: str, reason: str, exit_code: int) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason
        self.exit_code = exit_code


def campaign_repair_step(
    options: CampaignRepairStepOptions,
    *,
    build_verify_fn: BuildVerifyFn = build_verify,
    convergence_fn: ConvergenceFn = check_convergence,
    subprocess_runner: SubprocessRunner = subprocess.run,
) -> CampaignRepairStepOutcome:
    """Run the frozen lock-to-link repair sequence for one unit and architecture."""

    arch_norm = ARCH_RAW_TO_NORM.get(options.arch_raw, "")
    try:
        if not arch_norm:
            raise _StepError(
                REJECTED_IDENTITY_MISMATCH,
                f"arch is not in the verified whitelist: {options.arch_raw!r}",
                EXIT_REJECTED,
            )
        config = _load_config(options.config_path, options.wall_timeout)
        workspace_root = _workspace_root(config, options.campaign_unit_key, arch_norm)
        with _repair_step_lock(workspace_root):
            unit, reproduce = _read_only_identity(options, arch_norm)
            return _run_locked(
                options,
                unit=unit,
                reproduce=reproduce,
                config=config,
                arch_norm=arch_norm,
                workspace_root=workspace_root,
                build_verify_fn=build_verify_fn,
                convergence_fn=convergence_fn,
                subprocess_runner=subprocess_runner,
            )
    except _StepError as exc:
        return _error_outcome(options, arch_norm, exc)
    except BlockingIOError:
        return _error_outcome(
            options,
            arch_norm,
            _StepError(CAMPAIGN_STATE_BUSY, "repair-step lock is already held", EXIT_TOOLING),
        )
    except CampaignStateBusy as exc:
        return _error_outcome(
            options,
            arch_norm,
            _StepError(CAMPAIGN_STATE_BUSY, str(exc), EXIT_TOOLING),
        )
    except CampaignStateError as exc:
        return _error_outcome(
            options,
            arch_norm,
            _StepError(REJECTED_STATE_INCONSISTENT, str(exc), EXIT_REJECTED),
        )
    except OSError as exc:
        return _error_outcome(
            options,
            arch_norm,
            _StepError("BASELINE_TOOLING_FAILED", str(exc), EXIT_TOOLING),
        )
    except Exception as exc:
        return _error_outcome(
            options,
            arch_norm,
            _StepError(
                "BASELINE_TOOLING_FAILED",
                f"unexpected campaign repair-step failure: {type(exc).__name__}: {exc}",
                EXIT_TOOLING,
            ),
        )


def _run_locked(
    options: CampaignRepairStepOptions,
    *,
    unit: Unit,
    reproduce: dict[str, object],
    config: _CampaignConfig,
    arch_norm: str,
    workspace_root: Path,
    build_verify_fn: BuildVerifyFn,
    convergence_fn: ConvergenceFn,
    subprocess_runner: SubprocessRunner,
) -> CampaignRepairStepOutcome:
    # Step 2: bind the requested edit bytes to a per-round canonical path before
    # any reconciliation success can return.
    edit_bytes, edit_sha = _read_edit_spec(options.edit_spec_path)
    unit_root = config.campaign_workspace / _unit_hash(options.campaign_unit_key)
    output_dir = workspace_root / "out" / f"round_{options.round_index}"
    canonical_edit_spec = unit_root / "rounds" / f"round_{options.round_index}" / "edit_spec.json"
    _materialize_canonical_edit_spec(canonical_edit_spec, edit_bytes, edit_sha)
    try:
        create_round(
            options.state_db,
            options.campaign_unit_key,
            round_index=options.round_index,
            edit_spec_ref=str(canonical_edit_spec),
            edit_spec_sha256=edit_sha,
        )
    except RoundsExhausted as exc:
        append_status(options.state_db, options.campaign_unit_key, ROUNDS_EXHAUSTED, "rounds")
        raise _StepError("RoundsExhausted", str(exc), EXIT_REJECTED) from exc
    except StateInconsistent as exc:
        raise _StepError(REJECTED_IDENTITY_MISMATCH, str(exc), EXIT_REJECTED) from exc
    _revalidate_round(options, canonical_edit_spec, edit_sha)
    build_edit_spec = output_dir / "edit_spec.json"
    _materialize_canonical_edit_spec(build_edit_spec, edit_bytes, edit_sha)

    failure_key = _failure_key(unit, options.arch_raw)

    # Step 3: this API is the sole reconciliation read/classify/write boundary.
    reconciliation = reconcile_pass_and_invocations(
        options.state_db,
        options.campaign_unit_key,
        round_index=options.round_index,
        arch_norm=arch_norm,
        failure_key=failure_key,
        edit_spec_sha256=edit_sha,
    )
    reconciliation_json, warnings = _serialize_reconciliation(reconciliation)
    if reconciliation.branch in {"linked_already", "relinked"}:
        return CampaignRepairStepOutcome(
            result=_result(
                options,
                arch_norm,
                result="PASS",
                verdict="n_a",
                repair_allowed=REPAIR_AUTO,
                reason=reconciliation.branch,
                verification_id=reconciliation.current_verification_id,
                reconciliation=reconciliation_json,
                warnings=warnings,
            ),
            exit_code=EXIT_OK,
        )
    if reconciliation.branch in {"state_inconsistent_held", "orphan_pass_held"}:
        error_code = (
            REJECTED_ORPHAN_PASS_HELD
            if reconciliation.branch == "orphan_pass_held"
            else REJECTED_STATE_INCONSISTENT
        )
        return CampaignRepairStepOutcome(
            result=_result(
                options,
                arch_norm,
                result="FAIL",
                verdict="n_a",
                repair_allowed=REPAIR_DENIED,
                reason=reconciliation.branch,
                reconciliation=reconciliation_json,
                warnings=warnings,
                error_code=error_code,
            ),
            exit_code=EXIT_REJECTED,
        )
    if reconciliation.branch != "proceed":
        raise _StepError(
            REJECTED_STATE_INCONSISTENT,
            f"unknown reconciliation branch {reconciliation.branch!r}",
            EXIT_REJECTED,
        )

    # Step 4: previous evidence is checked only after recovery exits have run.
    previous = resolve(options.state_db, options.campaign_unit_key, arch_norm=arch_norm)
    if isinstance(previous, MissingEvidence):
        append_status(
            options.state_db,
            options.campaign_unit_key,
            HELD_FOR_INVESTIGATION,
            "previous_evidence_missing",
            arch_norm,
        )
        return CampaignRepairStepOutcome(
            result=_result(
                options,
                arch_norm,
                result="FAIL",
                verdict="n_a",
                repair_allowed=REPAIR_DENIED,
                reason=previous.reason,
                reconciliation=reconciliation_json,
                warnings=warnings,
                error_code=REJECTED_PREVIOUS_EVIDENCE_MISSING,
            ),
            exit_code=EXIT_REJECTED,
        )

    residual_error = _prepare_build_workspace(
        options,
        workspace_root=workspace_root,
        failure_key=failure_key,
        arch_norm=arch_norm,
    )
    if residual_error is not None:
        return CampaignRepairStepOutcome(
            result=_result(
                options,
                arch_norm,
                result="FAIL",
                verdict="n_a",
                repair_allowed=REPAIR_DENIED,
                reason=residual_error,
                reconciliation=reconciliation_json,
                warnings=warnings,
                error_code=REJECTED_STATE_INCONSISTENT,
            ),
            exit_code=EXIT_REJECTED,
        )

    try:
        receipt = consume_build_invocation(
            options.state_db,
            options.campaign_unit_key,
            round_index=options.round_index,
            arch_norm=arch_norm,
        )
    except BudgetExhausted as exc:
        append_status(options.state_db, options.campaign_unit_key, ROUNDS_EXHAUSTED, "budget")
        raise _StepError("BudgetExhausted", str(exc), EXIT_REJECTED) from exc

    # Step 5: filesystem identity is deliberately checked only once a new build
    # is known to be necessary; relink recovery does not depend on these files.
    try:
        build_options = _build_options(
            options,
            unit=unit,
            reproduce=reproduce,
            config=config,
            arch_norm=arch_norm,
            workspace_root=workspace_root,
            output_dir=output_dir,
            canonical_edit_spec=build_edit_spec,
            subprocess_runner=subprocess_runner,
        )
    except _StepError as exc:
        return CampaignRepairStepOutcome(
            result=_result(
                options,
                arch_norm,
                result="FAIL",
                verdict="n_a",
                repair_allowed=REPAIR_DENIED,
                reason=exc.reason,
                reconciliation=reconciliation_json,
                warnings=warnings,
                invocations_used_count=receipt.invocations_used,
                error_code=exc.code,
            ),
            exit_code=exc.exit_code,
        )
    build_result = build_verify_fn(build_options)

    if build_result.result == "PASS":
        return _handle_pass(
            options,
            arch_norm=arch_norm,
            edit_sha=edit_sha,
            build_result=build_result,
            invocation_event_id=receipt.event_id,
            invocations_used_count=receipt.invocations_used,
            reconciliation=reconciliation_json,
            warnings=warnings,
        )
    return _handle_fail(
        options,
        arch_norm=arch_norm,
        reproduce=reproduce,
        previous=previous,
        build_result=build_result,
        invocation_event_id=receipt.event_id,
        invocations_used_count=receipt.invocations_used,
        reconciliation=reconciliation_json,
        warnings=warnings,
        convergence_fn=convergence_fn,
    )


def _handle_pass(
    options: CampaignRepairStepOptions,
    *,
    arch_norm: str,
    edit_sha: str,
    build_result: BuildVerifyResult,
    invocation_event_id: int,
    invocations_used_count: int,
    reconciliation: dict[str, list[object]],
    warnings: list[dict[str, str]],
) -> CampaignRepairStepOutcome:
    verification_id = build_result.verification_id
    if not verification_id or get_record(options.state_db, verification_id) is None:
        raise _StepError(
            REJECTED_STATE_INCONSISTENT,
            "build PASS did not produce a persisted verification record",
            EXIT_REJECTED,
        )
    payload = _convergence_payload(
        options,
        arch_norm=arch_norm,
        invocation_event_id=invocation_event_id,
        result="PASS",
        verdict="n_a",
        reason="build_passed",
        evidence_path=None,
        evidence_sha256=None,
        verification_id=verification_id,
        actual_changed_paths=build_result.actual_changed_paths,
        previous_basis="none",
    )
    try:
        link_verification_with_convergence(
            options.state_db,
            options.campaign_unit_key,
            convergence_payload=payload,
            arch_raw=options.arch_raw,
            arch_norm=arch_norm,
            verification_id=verification_id,
            round_index=options.round_index,
            edit_spec_sha256=edit_sha,
        )
    except StateInconsistent as exc:
        _record_link_failure(options, arch_norm, build_result, verification_id)
        return CampaignRepairStepOutcome(
            result=_result(
                options,
                arch_norm,
                result="FAIL",
                verdict="n_a",
                repair_allowed=REPAIR_DENIED,
                reason=str(exc),
                failure_stage="link_failed",
                verification_id=verification_id,
                reconciliation=reconciliation,
                warnings=warnings,
                invocations_used_count=invocations_used_count,
                error_code=REJECTED_STATE_INCONSISTENT,
            ),
            exit_code=EXIT_REJECTED,
        )
    return CampaignRepairStepOutcome(
        result=_result(
            options,
            arch_norm,
            result="PASS",
            verdict="n_a",
            repair_allowed=REPAIR_AUTO,
            reason="build_passed",
            verification_id=verification_id,
            reconciliation=reconciliation,
            warnings=warnings,
            invocations_used_count=invocations_used_count,
        ),
        exit_code=EXIT_OK,
    )


def _handle_fail(
    options: CampaignRepairStepOptions,
    *,
    arch_norm: str,
    reproduce: dict[str, object],
    previous: ResolvedEvidence,
    build_result: BuildVerifyResult,
    invocation_event_id: int,
    invocations_used_count: int,
    reconciliation: dict[str, list[object]],
    warnings: list[dict[str, str]],
    convergence_fn: ConvergenceFn,
) -> CampaignRepairStepOutcome:
    repair_allowed = build_result.repair_allowed or REPAIR_DENIED
    if repair_allowed not in {REPAIR_AUTO, REPAIR_NEEDS_CONFIRMATION, REPAIR_DENIED}:
        repair_allowed = REPAIR_DENIED

    stage_reason = _non_substantive_reason(build_result)
    if stage_reason is not None:
        payload = _convergence_payload(
            options,
            arch_norm=arch_norm,
            invocation_event_id=invocation_event_id,
            result="n_a",
            verdict="n_a",
            reason=stage_reason,
            evidence_path=None,
            evidence_sha256=None,
            verification_id=None,
            actual_changed_paths=build_result.actual_changed_paths,
            previous_basis="none",
        )
        append_event(options.state_db, options.campaign_unit_key, "CONVERGENCE", payload)
        exit_code = (
            EXIT_TOOLING
            if stage_reason in {"analyzer_failed", "toolchain_failed"}
            else EXIT_OK
        )
        return CampaignRepairStepOutcome(
            result=_result(
                options,
                arch_norm,
                result="FAIL",
                verdict="n_a",
                repair_allowed=repair_allowed,
                reason=stage_reason,
                failure_class=build_result.failure_class,
                failure_stage=build_result.failure_stage,
                reconciliation=reconciliation,
                warnings=warnings,
                invocations_used_count=invocations_used_count,
                error_code=None,
            ),
            exit_code=exit_code,
        )

    current = _load_current_evidence(build_result.evidence)
    if isinstance(current, MissingEvidence):
        payload = _convergence_payload(
            options,
            arch_norm=arch_norm,
            invocation_event_id=invocation_event_id,
            result="n_a",
            verdict="n_a",
            reason="analyzer_failed",
            evidence_path=None,
            evidence_sha256=None,
            verification_id=None,
            actual_changed_paths=build_result.actual_changed_paths,
            previous_basis="none",
        )
        append_event(options.state_db, options.campaign_unit_key, "CONVERGENCE", payload)
        return CampaignRepairStepOutcome(
            result=_result(
                options,
                arch_norm,
                result="FAIL",
                verdict="n_a",
                repair_allowed=REPAIR_DENIED,
                reason=current.reason,
                failure_class="analyzer_failed",
                failure_stage="analyzer_failed",
                reconciliation=reconciliation,
                warnings=warnings,
                invocations_used_count=invocations_used_count,
                error_code=None,
            ),
            exit_code=EXIT_TOOLING,
        )

    # Step 6a repeats the exact resolver used by step 4 to close the TOCTOU gap.
    checked_previous = resolve(options.state_db, options.campaign_unit_key, arch_norm=arch_norm)
    if isinstance(checked_previous, MissingEvidence):
        return _record_previous_missing_after_consume(
            options,
            arch_norm=arch_norm,
            invocation_event_id=invocation_event_id,
            invocations_used_count=invocations_used_count,
            reconciliation=reconciliation,
            warnings=warnings,
            reason=checked_previous.reason,
        )
    previous = checked_previous

    if repair_allowed == REPAIR_DENIED:
        verdict = "denied"
        reason = build_result.error or "repair denied by failure classifier"
        adopted = False
    else:
        convergence = convergence_fn(
            current.evidence,
            previous.evidence,
            touched_files=set(build_result.actual_changed_paths),
        )
        verdict = convergence.verdict
        reason = convergence.reason
        adopted = False

    payload = _convergence_payload(
        options,
        arch_norm=arch_norm,
        invocation_event_id=invocation_event_id,
        result="FAIL",
        verdict=verdict,
        reason=reason,
        evidence_path=current.evidence_path,
        evidence_sha256=current.evidence_sha256,
        verification_id=None,
        actual_changed_paths=build_result.actual_changed_paths,
        previous_basis=previous.basis,
    )
    if verdict == "stalled":
        reproduce_event_id = reproduce.get("event_id")
        if not isinstance(reproduce_event_id, int):
            raise _StepError(
                REJECTED_STATE_INCONSISTENT,
                "REPRODUCE event id is invalid",
                EXIT_REJECTED,
            )
        adopted = adopt_secondary_target_with_convergence(
            options.state_db,
            options.campaign_unit_key,
            arch_norm=arch_norm,
            expected_reproduce_event_id=reproduce_event_id,
            convergence_payload=payload,
        )
        if adopted:
            verdict = "advance"
        else:
            append_event(options.state_db, options.campaign_unit_key, "CONVERGENCE", payload)
    else:
        append_event(options.state_db, options.campaign_unit_key, "CONVERGENCE", payload)

    _append_verdict_status(options, verdict)
    return CampaignRepairStepOutcome(
        result=_result(
            options,
            arch_norm,
            result="FAIL",
            verdict=verdict,
            repair_allowed=repair_allowed,
            reason=reason,
            failure_class=build_result.failure_class,
            failure_stage=build_result.failure_stage,
            adopted=adopted,
            previous_basis=previous.basis,
            evidence_path=current.evidence_path,
            reconciliation=reconciliation,
            warnings=warnings,
            invocations_used_count=invocations_used_count,
        ),
        exit_code=EXIT_OK,
    )


def _read_only_identity(
    options: CampaignRepairStepOptions,
    arch_norm: str,
) -> tuple[Unit, dict[str, object]]:
    if options.round_index < 1:
        raise _StepError("INVALID_ARGS", "round-index must be positive", EXIT_INVALID_ARGS)
    unit = get_unit(options.state_db, options.campaign_unit_key)
    if unit is None:
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            f"campaign unit does not exist: {options.campaign_unit_key}",
            EXIT_REJECTED,
        )
    status = latest_status(options.state_db, options.campaign_unit_key)
    if status not in _EXECUTABLE_UNIT_STATUSES:
        raise _StepError(
            REJECTED_STATE_INCONSISTENT,
            f"campaign unit status is not executable: {status!r}",
            EXIT_REJECTED,
        )
    _read_edit_spec(options.edit_spec_path)
    reproduce = latest_reproduce(
        options.state_db,
        options.campaign_unit_key,
        arch_norm=arch_norm,
    )
    if reproduce is None:
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            f"REPRODUCE metadata is missing for arch {arch_norm}",
            EXIT_REJECTED,
        )
    payload = reproduce.get("payload")
    if not isinstance(payload, dict) or payload.get("arch_norm") != arch_norm:
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            "REPRODUCE metadata does not match requested architecture",
            EXIT_REJECTED,
        )
    if payload.get("ci_evidence_sha256_used") != unit.ci_evidence_sha256:
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            "REPRODUCE metadata does not match the unit CI evidence identity",
            EXIT_REJECTED,
        )
    return unit, reproduce


def _build_options(
    options: CampaignRepairStepOptions,
    *,
    unit: Unit,
    reproduce: dict[str, object],
    config: _CampaignConfig,
    arch_norm: str,
    workspace_root: Path,
    output_dir: Path,
    canonical_edit_spec: Path,
    subprocess_runner: SubprocessRunner,
) -> BuildVerifyOptions:
    payload = reproduce.get("payload")
    if not isinstance(payload, dict):
        raise _StepError(REJECTED_STATE_INCONSISTENT, "invalid REPRODUCE payload", EXIT_REJECTED)
    conf_sha = payload.get("gbs_conf_sha256")
    if not config.clang_conf_path.is_file() or _sha256_file(config.clang_conf_path) != conf_sha:
        raise _StepError(REJECTED_CONF_DRIFT, "clang configuration hash changed", EXIT_REJECTED)
    evidence_value = payload.get("evidence_local")
    evidence_sha = payload.get("evidence_sha256")
    if not isinstance(evidence_value, str) or not isinstance(evidence_sha, str):
        raise _StepError(
            REJECTED_BASELINE_EVIDENCE_MISMATCH,
            "REPRODUCE baseline evidence binding is invalid",
            EXIT_REJECTED,
        )
    baseline_evidence = Path(evidence_value)
    if not baseline_evidence.is_file() or _sha256_file(baseline_evidence) != evidence_sha:
        raise _StepError(
            REJECTED_BASELINE_EVIDENCE_MISMATCH,
            "baseline evidence file is missing or changed",
            EXIT_REJECTED,
        )
    src_clean = config.campaign_workspace / _unit_hash(unit.campaign_unit_key) / "src"
    _validate_source_identity(
        src_clean,
        unit,
        subprocess_runner=subprocess_runner,
    )
    return BuildVerifyOptions(
        src_clean=src_clean,
        base_commit=unit.base_commit,
        edit_spec_path=canonical_edit_spec,
        gbs_conf=config.clang_conf_path,
        package=unit.spec_name,
        workspace_root=workspace_root,
        baseline_evidence=baseline_evidence,
        output_dir=output_dir,
        iter_index=options.round_index,
        wall_timeout=options.wall_timeout or config.wall_timeout,
        state_db=options.state_db,
        ci_system=unit.ci_system,
        build_id=unit.source_build_id,
        project=unit.project,
        branch=unit.branch,
        arch=options.arch_raw,
        extra_pythonpath=options.extra_pythonpath,
    )


def _validate_source_identity(
    src_clean: Path,
    unit: Unit,
    *,
    subprocess_runner: SubprocessRunner,
) -> None:
    try:
        head = _git_stdout(src_clean, ["rev-parse", "HEAD"], subprocess_runner)
        origin = _git_stdout(src_clean, ["remote", "get-url", "origin"], subprocess_runner)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            f"source identity could not be read: {exc}",
            EXIT_REJECTED,
        ) from exc
    if head != unit.base_commit or _normalize_project(origin) != unit.project:
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            "source HEAD or origin does not match campaign unit",
            EXIT_REJECTED,
        )
    marker = src_clean / ".campaign_clone"
    try:
        marker_value: Any = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            f"campaign clone marker is unreadable: {exc}",
            EXIT_REJECTED,
        ) from exc
    expected = {
        "unit_key": unit.campaign_unit_key,
        "project": unit.project,
        "base_commit": unit.base_commit,
    }
    if marker_value != expected:
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            "campaign clone marker does not match campaign unit",
            EXIT_REJECTED,
        )


def _prepare_build_workspace(
    options: CampaignRepairStepOptions,
    *,
    workspace_root: Path,
    failure_key: str,
    arch_norm: str,
) -> str | None:
    worktree_path = workspace_root / f"iter_{options.round_index}"
    if not worktree_path.exists():
        return None
    if is_protected(worktree_path) or _has_matching_pass_record(
        options.state_db,
        failure_key=failure_key,
        worktree_path=worktree_path,
    ):
        append_status(
            options.state_db,
            options.campaign_unit_key,
            HELD_FOR_INVESTIGATION,
            "state_inconsistent",
            arch_norm,
        )
        return f"residual disposable copy is protected or PASS-bound: {worktree_path}"
    try:
        cleanup_disposable_copy(str(worktree_path), str(workspace_root))
    except (OSError, WorkspaceViolation) as exc:
        append_status(
            options.state_db,
            options.campaign_unit_key,
            HELD_FOR_INVESTIGATION,
            "state_inconsistent",
            arch_norm,
        )
        return f"residual disposable copy could not be safely cleaned: {exc}"
    append_event(
        options.state_db,
        options.campaign_unit_key,
        "WORKSPACE_CLEANUP",
        {"paths": [str(worktree_path)], "reason": "residual_unprotected_copy"},
    )
    return None


def _has_matching_pass_record(
    state_db: StateDatabase,
    *,
    failure_key: str,
    worktree_path: Path,
) -> bool:
    conn = state_db.connect()
    try:
        row = conn.execute(
            "SELECT 1 FROM verification_records WHERE result = 'PASS' "
            "AND failure_key = ? AND worktree_path = ? LIMIT 1",
            (failure_key, str(worktree_path)),
        ).fetchone()
    finally:
        conn.close()
    return row is not None


def _load_current_evidence(path_value: str | None) -> ResolvedEvidence | MissingEvidence:
    if not path_value:
        return MissingEvidence("build failure did not produce analyzer evidence")
    path = Path(path_value)
    try:
        raw = path.read_bytes()
        value: Any = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return MissingEvidence(f"current evidence is unreadable: {exc}")
    if not isinstance(value, dict):
        return MissingEvidence("current evidence must be a JSON object")
    return ResolvedEvidence(
        evidence=value,
        basis="prev_build",
        evidence_path=str(path),
        evidence_sha256=hashlib.sha256(raw).hexdigest(),
    )


def _record_previous_missing_after_consume(
    options: CampaignRepairStepOptions,
    *,
    arch_norm: str,
    invocation_event_id: int,
    invocations_used_count: int,
    reconciliation: dict[str, list[object]],
    warnings: list[dict[str, str]],
    reason: str,
) -> CampaignRepairStepOutcome:
    payload = _convergence_payload(
        options,
        arch_norm=arch_norm,
        invocation_event_id=invocation_event_id,
        result="n_a",
        verdict="n_a",
        reason="previous_evidence_missing",
        evidence_path=None,
        evidence_sha256=None,
        verification_id=None,
        actual_changed_paths=[],
        previous_basis="none",
    )
    append_event(options.state_db, options.campaign_unit_key, "CONVERGENCE", payload)
    append_status(
        options.state_db,
        options.campaign_unit_key,
        HELD_FOR_INVESTIGATION,
        "previous_evidence_missing",
        arch_norm,
    )
    return CampaignRepairStepOutcome(
        result=_result(
            options,
            arch_norm,
            result="FAIL",
            verdict="n_a",
            repair_allowed=REPAIR_DENIED,
            reason=reason,
            reconciliation=reconciliation,
            warnings=warnings,
            invocations_used_count=invocations_used_count,
            error_code=REJECTED_PREVIOUS_EVIDENCE_MISSING,
        ),
        exit_code=EXIT_REJECTED,
    )


def _record_link_failure(
    options: CampaignRepairStepOptions,
    arch_norm: str,
    result: BuildVerifyResult,
    verification_id: str,
) -> None:
    append_event(
        options.state_db,
        options.campaign_unit_key,
        "ORPHAN_PASS",
        {
            "round_index": options.round_index,
            "arch_norm": arch_norm,
            "verification_id": verification_id,
            "worktree_path": result.worktree_path or "<unknown>",
            "reason": "link_failed",
            "detected_at": _now(),
        },
    )
    append_status(
        options.state_db,
        options.campaign_unit_key,
        HELD_FOR_INVESTIGATION,
        "link_mismatch",
        arch_norm,
    )


def _append_verdict_status(options: CampaignRepairStepOptions, verdict: str) -> None:
    statuses = {"denied": DENIED, "stalled": STALLED, "regressed": REGRESSED}
    status = statuses.get(verdict)
    if status is not None:
        append_status(options.state_db, options.campaign_unit_key, status, verdict)


def _non_substantive_reason(result: BuildVerifyResult) -> str | None:
    stage = result.failure_stage or ""
    if stage in {"apply_failed", "apply_unexpected_paths", "no_effective_changes"}:
        return "apply_failed"
    if stage in {"analyzer_failed"} or (stage == "gbs_build_failed" and not result.evidence):
        return "analyzer_failed"
    if stage in {
        "build_timeout",
        "build_mutated_source",
        "infrastructure_failed",
        "toolchain_failed",
    }:
        return "toolchain_failed"
    return None


def _convergence_payload(
    options: CampaignRepairStepOptions,
    *,
    arch_norm: str,
    invocation_event_id: int,
    result: str,
    verdict: str,
    reason: str,
    evidence_path: str | None,
    evidence_sha256: str | None,
    verification_id: str | None,
    actual_changed_paths: list[str],
    previous_basis: str,
) -> dict[str, object]:
    return {
        "round_index": options.round_index,
        "arch_norm": arch_norm,
        "invocation_event_id": invocation_event_id,
        "result": result,
        "verdict": verdict,
        "reason": reason,
        "evidence_path": evidence_path,
        "evidence_sha256": evidence_sha256,
        "verification_id": verification_id,
        "actual_changed_paths": sorted(actual_changed_paths),
        "previous_basis": previous_basis,
        "at": _now(),
    }


def _serialize_reconciliation(
    value: ReconcileResult,
) -> tuple[dict[str, list[object]], list[dict[str, str]]]:
    relinks: list[object] = [
        {
            "round_index": round_index,
            "verification_id": verification_id,
            "invocation_event_id": invocation_event_id,
        }
        for round_index, verification_id, invocation_event_id in sorted(
            value.other_round_relinks,
            key=lambda item: (item[0], item[1], item[2]),
        )
    ]
    non_campaign = sorted(set(value.non_campaign_verification_ids))
    warnings = [
        {"code": "non_campaign_verification", "verification_id": verification_id}
        for verification_id in non_campaign
    ]
    return (
        {
            "other_round_relinks": relinks,
            "non_campaign_verification_ids": list(non_campaign),
        },
        warnings,
    )


def _empty_reconciliation() -> dict[str, list[object]]:
    return {"other_round_relinks": [], "non_campaign_verification_ids": []}


def _result(
    options: CampaignRepairStepOptions,
    arch_norm: str,
    *,
    result: str,
    verdict: str,
    repair_allowed: str,
    reason: str,
    failure_class: str | None = None,
    failure_stage: str | None = None,
    adopted: bool = False,
    previous_basis: str = "none",
    verification_id: str | None = None,
    evidence_path: str | None = None,
    reconciliation: dict[str, list[object]] | None = None,
    warnings: list[dict[str, str]] | None = None,
    invocations_used_count: int | None = None,
    error_code: str | None = None,
) -> CampaignRepairStepResult:
    used = (
        invocations_used_count
        if invocations_used_count is not None
        else _safe_invocations_used(options)
    )
    return CampaignRepairStepResult(
        result=result,
        verdict=verdict,
        repair_allowed=repair_allowed,
        failure_class=failure_class,
        failure_stage=failure_stage,
        adopted=adopted,
        convergence_reason=reason,
        previous_basis=previous_basis,
        round_index=options.round_index,
        arch_norm=arch_norm,
        verification_id=verification_id,
        evidence_path=evidence_path,
        reconciliation=reconciliation or _empty_reconciliation(),
        warnings=warnings or [],
        invocations_used=used,
        error_code=error_code,
    )


def _error_outcome(
    options: CampaignRepairStepOptions,
    arch_norm: str,
    error: _StepError,
) -> CampaignRepairStepOutcome:
    return CampaignRepairStepOutcome(
        result=_result(
            options,
            arch_norm,
            result="FAIL",
            verdict="n_a",
            repair_allowed=REPAIR_DENIED,
            reason=error.reason,
            error_code=error.code,
        ),
        exit_code=error.exit_code,
    )


def _safe_invocations_used(options: CampaignRepairStepOptions) -> int:
    try:
        return invocations_used(options.state_db, options.campaign_unit_key)
    except Exception:
        return 0


def _read_edit_spec(path: Path) -> tuple[bytes, str]:
    try:
        real_path = Path(os.path.realpath(path))
        raw = real_path.read_bytes()
        value: Any = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            f"edit_spec is unreadable or invalid JSON: {exc}",
            EXIT_REJECTED,
        ) from exc
    if not isinstance(value, dict):
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            "edit_spec must be a JSON object",
            EXIT_REJECTED,
        )
    return raw, hashlib.sha256(raw).hexdigest()


def _materialize_canonical_edit_spec(path: Path, raw: bytes, digest: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        _verify_canonical_edit_spec(path, digest)
        return
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError:
            _verify_canonical_edit_spec(path, digest)
    finally:
        temporary_path.unlink(missing_ok=True)


def _verify_canonical_edit_spec(path: Path, digest: str) -> None:
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            f"canonical edit_spec conflicts with round output: {path}",
            EXIT_REJECTED,
        )


def _revalidate_round(
    options: CampaignRepairStepOptions,
    canonical_edit_spec: Path,
    edit_sha: str,
) -> None:
    round_row = get_round(options.state_db, options.campaign_unit_key, options.round_index)
    if (
        round_row is None
        or round_row.edit_spec_sha256 != edit_sha
        or round_row.edit_spec_ref != os.path.realpath(canonical_edit_spec)
    ):
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            "stored round identity does not match this invocation",
            EXIT_REJECTED,
        )


def _load_config(path: Path, wall_timeout_override: int | None) -> _CampaignConfig:
    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise _StepError(
            "INVALID_ARGS",
            f"campaign config is unreadable: {exc}",
            EXIT_INVALID_ARGS,
        ) from exc
    if not isinstance(raw, Mapping):
        raise _StepError("INVALID_ARGS", "campaign config must be a mapping", EXIT_INVALID_ARGS)
    workspace = raw.get("campaign_workspace")
    conf = raw.get("clang_conf_path")
    if not isinstance(workspace, str) or not workspace or not isinstance(conf, str) or not conf:
        raise _StepError(
            "INVALID_ARGS",
            "config requires campaign_workspace and clang_conf_path",
            EXIT_INVALID_ARGS,
        )
    configured_timeout = raw.get("wall_timeout", 3600)
    timeout = wall_timeout_override if wall_timeout_override is not None else configured_timeout
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        raise _StepError("INVALID_ARGS", "wall timeout must be positive", EXIT_INVALID_ARGS)
    return _CampaignConfig(
        campaign_workspace=Path(workspace).expanduser().resolve(),
        clang_conf_path=Path(conf).expanduser().resolve(),
        wall_timeout=timeout,
    )


@contextmanager
def _repair_step_lock(workspace_root: Path) -> Iterator[None]:
    workspace_root.mkdir(parents=True, exist_ok=True)
    lock_path = workspace_root / ".repair_step.lock"
    with lock_path.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _workspace_root(config: _CampaignConfig, unit_key: str, arch_norm: str) -> Path:
    return config.campaign_workspace / _unit_hash(unit_key) / arch_norm


def _unit_hash(unit_key: str) -> str:
    return hashlib.sha256(unit_key.encode("utf-8")).hexdigest()[:12]


def _failure_key(unit: Unit, arch_raw: str) -> str:
    return build_failure_key(
        ci_system=unit.ci_system,
        build_id=unit.source_build_id,
        project=unit.project,
        branch=unit.branch,
        arch=arch_raw,
        spec_name=unit.spec_name,
        base_commit=unit.base_commit,
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_stdout(
    cwd: Path,
    args: list[str],
    subprocess_runner: SubprocessRunner,
) -> str:
    completed = subprocess_runner(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return (completed.stdout or "").strip()


def _normalize_project(remote: str) -> str:
    value = remote.strip()
    if "://" in value:
        path = urlsplit(value).path
    elif ":" in value and "@" in value.split(":", 1)[0]:
        path = value.split(":", 1)[1]
    else:
        path = value
    normalized = path.strip("/")
    if normalized.startswith("git/"):
        normalized = normalized[4:]
    return normalized.removesuffix(".git")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")
