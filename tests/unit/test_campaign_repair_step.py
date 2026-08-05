from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
from ci_triage import campaign_repair_step as repair_step
from ci_triage import cli
from ci_triage.campaign_repair_step import (
    CAMPAIGN_STATE_BUSY,
    REJECTED_IDENTITY_MISMATCH,
    REJECTED_PREVIOUS_EVIDENCE_MISSING,
    CampaignRepairStepOptions,
    campaign_repair_step,
)
from ci_triage.campaign_state import (
    HELD_FOR_INVESTIGATION,
    ReconcileResult,
    append_event,
    consume_build_invocation,
    create_round,
    create_unit,
    ensure_schema,
    is_rebaseline_authorized,
    link_verification_with_convergence,
    reconcile_pass_and_invocations,
)
from ci_triage.previous_evidence import MissingEvidence, ResolvedEvidence, resolve
from ci_triage.state import (
    StateDatabase,
    VerificationRecord,
    build_failure_key,
    write_pass_record,
)
from ci_triage.verify.build_verify import BuildVerifyOptions, BuildVerifyResult
from ci_triage.verify.convergence import ConvergenceResult

UNIT_KEY = "campaign:repair-step"
ARCH_RAW = "standard-aarch64"
ARCH_NORM = "aarch64"
PROJECT = "platform/core/appfw/united-service"
BASE_PACKET = {
    "schema_version": "evidence_packet/v1",
    "primary_error": {
        "kind": "werror",
        "file": "src/main.c",
        "line": 1,
        "message": "error: unused field [-Werror,-Wunused-private-field]",
    },
    "error_clusters": {
        "schema_version": "error_clusters/v1",
        "clusters": [],
        "truncated": False,
    },
    "root_cause_candidates": [],
}
RESULT_KEYS = {
    "result",
    "verdict",
    "repair_allowed",
    "failure_class",
    "failure_stage",
    "adopted",
    "convergence_reason",
    "previous_basis",
    "round_index",
    "arch_norm",
    "verification_id",
    "evidence_path",
    "reconciliation",
    "warnings",
    "invocations_used",
    "error_code",
}


@dataclass(frozen=True)
class Fixture:
    db: StateDatabase
    options: CampaignRepairStepOptions
    workspace: Path
    src: Path
    evidence: Path
    conf: Path
    edit_spec: Path
    base_commit: str


def _git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _fixture(tmp_path: Path, *, max_rounds: int = 3) -> Fixture:
    db = StateDatabase(tmp_path / "state.sqlite3")
    ensure_schema(db)
    workspace = tmp_path / "campaign-ws"
    unit_hash = hashlib.sha256(UNIT_KEY.encode()).hexdigest()[:12]
    src = workspace / unit_hash / "src"
    src.mkdir(parents=True)
    _git(src, "init")
    _git(src, "config", "user.email", "ci-triage-test@example.invalid")
    _git(src, "config", "user.name", "CI Triage Test")
    (src / "src").mkdir()
    (src / "src/main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
    _git(src, "add", "src/main.c")
    _git(src, "commit", "-m", "base")
    base_commit = _git(src, "rev-parse", "HEAD")
    _git(src, "remote", "add", "origin", f"ssh://review.tizen.org:29418/{PROJECT}")
    (src / ".campaign_clone").write_text(
        json.dumps(
            {"unit_key": UNIT_KEY, "project": PROJECT, "base_commit": base_commit},
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    evidence = tmp_path / "baseline.json"
    evidence.write_text(json.dumps(BASE_PACKET, sort_keys=True) + "\n", encoding="utf-8")
    conf = tmp_path / "gbs.conf"
    conf.write_text("[general]\n", encoding="utf-8")
    edit_spec = tmp_path / "input-edit-spec.json"
    edit_spec.write_text(
        json.dumps(
            {
                "schema_version": "gbs_patch_suggest/edit-spec/v1",
                "patch_name": "repair",
                "edits": [
                    {"file": "src/main.c", "old": "return 0", "new": "return 1"}
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    ci_hash = "c" * 64
    create_unit(
        db,
        campaign_unit_key=UNIT_KEY,
        submission_identity_key="submission:repair-step",
        primary_arch=ARCH_RAW,
        failed_arches=(ARCH_RAW,),
        toolchain_profile="tizen_unified_standard",
        ci_evidence_ref=str(tmp_path / "ci-evidence.json"),
        ci_evidence_sha256=ci_hash,
        max_rounds=max_rounds,
        max_build_invocations=9,
        ci_system="quickbuild",
        source_build_id="1127447",
        project=PROJECT,
        branch="tizen",
        spec_name="united-service",
        base_commit=base_commit,
    )
    append_event(
        db,
        UNIT_KEY,
        "REPRODUCE",
        {
            "arch_norm": ARCH_NORM,
            "outcome": "matched",
            "evidence_local": str(evidence),
            "evidence_sha256": _sha(evidence),
            "synthetic_zero_error": False,
            "gbs_conf_sha256": _sha(conf),
            "ci_evidence_sha256_used": ci_hash,
            "build_log": str(tmp_path / "baseline.log"),
            "basis": {},
        },
    )
    config = tmp_path / "campaign.yaml"
    config.write_text(
        f"campaign_workspace: {workspace}\nclang_conf_path: {conf}\n",
        encoding="utf-8",
    )
    return Fixture(
        db=db,
        options=CampaignRepairStepOptions(
            campaign_unit_key=UNIT_KEY,
            state_db=db,
            config_path=config,
            round_index=1,
            edit_spec_path=edit_spec,
            arch_raw=ARCH_RAW,
            extra_pythonpath=(),
        ),
        workspace=workspace,
        src=src,
        evidence=evidence,
        conf=conf,
        edit_spec=edit_spec,
        base_commit=base_commit,
    )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _failure_key(fixture: Fixture) -> str:
    return build_failure_key(
        ci_system="quickbuild",
        build_id="1127447",
        project=PROJECT,
        branch="tizen",
        arch=ARCH_RAW,
        spec_name="united-service",
        base_commit=fixture.base_commit,
    )


def _write_pass_record(
    fixture: Fixture,
    options: BuildVerifyOptions,
    verification_id: str = "verify-pass",
    edit_sha: str | None = None,
) -> None:
    write_pass_record(
        fixture.db,
        VerificationRecord(
            verification_id=verification_id,
            result="PASS",
            timestamp="2026-08-05T00:00:00+00:00",
            failure_key=_failure_key(fixture),
            base_commit=fixture.base_commit,
            verified_commit_sha=fixture.base_commit,
            verified_tree_sha=_git(fixture.src, "rev-parse", "HEAD^{tree}"),
            canonical_diff_sha256="d" * 64,
            patch_sha256="p" * 64,
            edit_spec_sha256=edit_sha or _sha(options.edit_spec_path),
            project=PROJECT,
            branch="tizen",
            spec_name="united-service",
            arch=ARCH_RAW,
            gbs_conf_sha256=_sha(fixture.conf),
            build_log_sha256="b" * 64,
            worktree_path=str(fixture.src),
            command_line="gbs -c conf build -A aarch64 --include-all",
        ),
    )


def _pass_builder(fixture: Fixture) -> Callable[[BuildVerifyOptions], BuildVerifyResult]:
    def fake(options: BuildVerifyOptions) -> BuildVerifyResult:
        _write_pass_record(fixture, options)
        return BuildVerifyResult(
            result="PASS",
            actual_changed_paths=["src/main.c"],
            verification_id="verify-pass",
            worktree_path=str(fixture.src),
        )

    return fake


def _assert_fixed_schema(value: dict[str, object]) -> None:
    assert set(value) == RESULT_KEYS
    reconciliation = value["reconciliation"]
    assert isinstance(reconciliation, dict)
    assert set(reconciliation) == {
        "other_round_relinks",
        "non_campaign_verification_ids",
    }
    assert isinstance(value["warnings"], list)


def test_pass_runs_frozen_order_and_emits_fixed_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    order: list[str] = []
    originals: dict[str, Callable[..., object]] = {
        "create": create_round,
        "reconcile": reconcile_pass_and_invocations,
        "consume": consume_build_invocation,
        "link": link_verification_with_convergence,
    }

    def track(name: str) -> Callable[..., object]:
        original = originals[name]

        def wrapper(*args: object, **kwargs: object) -> object:
            order.append(name)
            return original(*args, **kwargs)

        return wrapper

    for name, attribute in (
        ("create", "create_round"),
        ("reconcile", "reconcile_pass_and_invocations"),
        ("consume", "consume_build_invocation"),
        ("link", "link_verification_with_convergence"),
    ):
        monkeypatch.setattr(repair_step, attribute, track(name))

    def build(options: BuildVerifyOptions) -> BuildVerifyResult:
        order.append("build")
        _write_pass_record(fixture, options)
        return BuildVerifyResult(
            result="PASS",
            actual_changed_paths=["src/main.c"],
            verification_id="verify-pass",
            worktree_path=str(fixture.src),
        )

    outcome = campaign_repair_step(fixture.options, build_verify_fn=build)

    assert outcome.exit_code == 0
    assert order == ["create", "reconcile", "consume", "build", "link"]
    value = outcome.result.to_dict()
    _assert_fixed_schema(value)
    assert value["result"] == "PASS"
    assert value["verification_id"] == "verify-pass"
    assert value["invocations_used"] == 1


def test_new_round_with_old_hash_dies_in_create_round_before_reconcile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    create_round(
        fixture.db,
        UNIT_KEY,
        round_index=1,
        edit_spec_ref=str(tmp_path / "round-1.json"),
        edit_spec_sha256=_sha(fixture.edit_spec),
    )
    called = {"reconcile": False}

    def forbidden(*args: object, **kwargs: object) -> ReconcileResult:
        called["reconcile"] = True
        raise AssertionError("reconciliation must not run")

    monkeypatch.setattr(repair_step, "reconcile_pass_and_invocations", forbidden)
    options = CampaignRepairStepOptions(
        **{
            **fixture.options.__dict__,
            "round_index": 2,
        }
    )
    outcome = campaign_repair_step(options, build_verify_fn=_pass_builder(fixture))

    assert outcome.exit_code == 4
    _assert_fixed_schema(outcome.result.to_dict())
    assert outcome.result.error_code == REJECTED_IDENTITY_MISMATCH
    assert called["reconcile"] is False


def test_previous_precheck_writes_arch_scoped_held_and_enables_rebaseline(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture.evidence.unlink()

    outcome = campaign_repair_step(fixture.options, build_verify_fn=_pass_builder(fixture))

    assert outcome.exit_code == 4
    _assert_fixed_schema(outcome.result.to_dict())
    assert outcome.result.error_code == REJECTED_PREVIOUS_EVIDENCE_MISSING
    assert is_rebaseline_authorized(fixture.db, UNIT_KEY, arch_norm=ARCH_NORM) is True
    assert is_rebaseline_authorized(fixture.db, UNIT_KEY, arch_norm="armv7l") is False
    conn = fixture.db.connect()
    try:
        row = conn.execute(
            "SELECT status, reason, arch_norm FROM campaign_status_log "
            "WHERE campaign_unit_key = ? ORDER BY log_id DESC LIMIT 1",
            (UNIT_KEY,),
        ).fetchone()
        count = conn.execute(
            "SELECT COUNT(*) AS count FROM campaign_gate_events "
            "WHERE campaign_unit_key = ? AND event_type = 'CONVERGENCE'",
            (UNIT_KEY,),
        ).fetchone()
    finally:
        conn.close()
    assert tuple(row) == (HELD_FOR_INVESTIGATION, "previous_evidence_missing", ARCH_NORM)
    assert count["count"] == 0


def test_removing_precheck_status_write_makes_rebaseline_unreachable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    fixture.evidence.unlink()
    monkeypatch.setattr(repair_step, "append_status", lambda *args, **kwargs: None)

    outcome = campaign_repair_step(fixture.options, build_verify_fn=_pass_builder(fixture))

    assert outcome.exit_code == 4
    assert is_rebaseline_authorized(fixture.db, UNIT_KEY, arch_norm=ARCH_NORM) is False


def test_linked_recovery_runs_before_missing_previous_precheck(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    unit_hash = hashlib.sha256(UNIT_KEY.encode()).hexdigest()[:12]
    canonical = fixture.workspace / unit_hash / ARCH_NORM / "out/round_1/edit_spec.json"
    canonical.parent.mkdir(parents=True)
    canonical.write_bytes(fixture.edit_spec.read_bytes())
    create_round(
        fixture.db,
        UNIT_KEY,
        round_index=1,
        edit_spec_ref=str(canonical),
        edit_spec_sha256=_sha(canonical),
    )
    receipt = consume_build_invocation(
        fixture.db,
        UNIT_KEY,
        round_index=1,
        arch_norm=ARCH_NORM,
    )
    build_options = BuildVerifyOptions(
        src_clean=fixture.src,
        base_commit=fixture.base_commit,
        edit_spec_path=canonical,
        gbs_conf=fixture.conf,
        package="united-service",
        workspace_root=canonical.parents[2],
        baseline_evidence=fixture.evidence,
        output_dir=canonical.parent,
        iter_index=1,
        wall_timeout=3600,
        state_db=fixture.db,
        ci_system="quickbuild",
        build_id="1127447",
        project=PROJECT,
        branch="tizen",
        arch=ARCH_RAW,
    )
    _write_pass_record(fixture, build_options)
    link_verification_with_convergence(
        fixture.db,
        UNIT_KEY,
        convergence_payload={
            "round_index": 1,
            "arch_norm": ARCH_NORM,
            "invocation_event_id": receipt.event_id,
            "result": "PASS",
            "verdict": "n_a",
            "reason": "build_passed",
            "evidence_path": None,
            "evidence_sha256": None,
            "verification_id": "verify-pass",
            "actual_changed_paths": ["src/main.c"],
            "previous_basis": "none",
            "at": "2026-08-05T00:00:00+00:00",
        },
        arch_raw=ARCH_RAW,
        arch_norm=ARCH_NORM,
        verification_id="verify-pass",
        round_index=1,
        edit_spec_sha256=_sha(canonical),
    )
    fixture.evidence.unlink()

    outcome = campaign_repair_step(
        fixture.options,
        build_verify_fn=lambda options: pytest.fail("build must not run"),
    )

    assert outcome.exit_code == 0
    _assert_fixed_schema(outcome.result.to_dict())
    assert outcome.result.result == "PASS"
    assert outcome.result.convergence_reason == "linked_already"
    assert outcome.result.invocations_used == 1


@pytest.mark.parametrize("repair_allowed", ["auto", "needs_confirmation"])
def test_fail_stalled_records_convergence_and_terminal_status(
    tmp_path: Path,
    repair_allowed: str,
) -> None:
    fixture = _fixture(tmp_path)
    current = tmp_path / "current.json"
    current.write_text(json.dumps(BASE_PACKET, sort_keys=True) + "\n", encoding="utf-8")

    outcome = campaign_repair_step(
        fixture.options,
        build_verify_fn=lambda options: BuildVerifyResult(
            result="FAIL",
            actual_changed_paths=["src/main.c"],
            failure_stage="gbs_build_failed",
            failure_class="source_repairable",
            repair_allowed=repair_allowed,
            evidence=str(current),
        ),
    )

    assert outcome.exit_code == 0
    _assert_fixed_schema(outcome.result.to_dict())
    assert outcome.result.verdict == "stalled"
    assert outcome.result.repair_allowed == repair_allowed
    assert outcome.result.previous_basis == "reproduce"
    conn = fixture.db.connect()
    try:
        status = conn.execute(
            "SELECT status FROM campaign_status_log WHERE campaign_unit_key = ? "
            "ORDER BY log_id DESC LIMIT 1",
            (UNIT_KEY,),
        ).fetchone()
    finally:
        conn.close()
    assert status["status"] == "STALLED"


def test_denied_failure_short_circuits_convergence(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    current = tmp_path / "current.json"
    current.write_text(json.dumps(BASE_PACKET) + "\n", encoding="utf-8")

    def forbidden(*args: object, **kwargs: object) -> ConvergenceResult:
        raise AssertionError("denied failure must not call convergence")

    outcome = campaign_repair_step(
        fixture.options,
        build_verify_fn=lambda options: BuildVerifyResult(
            result="FAIL",
            failure_stage="gbs_build_failed",
            failure_class="toolchain",
            repair_allowed="denied",
            evidence=str(current),
            error="toolchain flag denied",
        ),
        convergence_fn=forbidden,
    )

    assert outcome.exit_code == 0
    _assert_fixed_schema(outcome.result.to_dict())
    assert outcome.result.verdict == "denied"
    assert outcome.result.repair_allowed == "denied"


def test_post_build_previous_toctou_failure_records_na_and_held(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    current = tmp_path / "current.json"
    current.write_text(json.dumps(BASE_PACKET) + "\n", encoding="utf-8")

    def build(options: BuildVerifyOptions) -> BuildVerifyResult:
        fixture.evidence.unlink()
        return BuildVerifyResult(
            result="FAIL",
            actual_changed_paths=["src/main.c"],
            failure_stage="gbs_build_failed",
            failure_class="source_repairable",
            repair_allowed="auto",
            evidence=str(current),
        )

    outcome = campaign_repair_step(fixture.options, build_verify_fn=build)

    assert outcome.exit_code == 4
    _assert_fixed_schema(outcome.result.to_dict())
    assert outcome.result.error_code == REJECTED_PREVIOUS_EVIDENCE_MISSING
    conn = fixture.db.connect()
    try:
        event = conn.execute(
            "SELECT payload_json FROM campaign_gate_events "
            "WHERE campaign_unit_key = ? AND event_type = 'CONVERGENCE' "
            "ORDER BY event_id DESC LIMIT 1",
            (UNIT_KEY,),
        ).fetchone()
    finally:
        conn.close()
    payload = json.loads(event["payload_json"])
    assert payload["result"] == "n_a"
    assert payload["verdict"] == "n_a"
    assert payload["reason"] == "previous_evidence_missing"
    assert is_rebaseline_authorized(fixture.db, UNIT_KEY, arch_norm=ARCH_NORM) is True


def test_lock_busy_returns_exit_five_without_creating_round(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    unit_hash = hashlib.sha256(UNIT_KEY.encode()).hexdigest()[:12]
    lock_root = fixture.workspace / unit_hash / ARCH_NORM
    lock_root.mkdir(parents=True)
    with (lock_root / ".repair_step.lock").open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        outcome = campaign_repair_step(fixture.options, build_verify_fn=_pass_builder(fixture))

    assert outcome.exit_code == 5
    _assert_fixed_schema(outcome.result.to_dict())
    assert outcome.result.error_code == CAMPAIGN_STATE_BUSY
    conn = fixture.db.connect()
    try:
        count = conn.execute("SELECT COUNT(*) AS count FROM campaign_rounds").fetchone()
    finally:
        conn.close()
    assert count["count"] == 0


@pytest.mark.parametrize("damage", ["head", "origin", "marker"])
def test_source_identity_joint_check_rejects_each_mismatch(
    tmp_path: Path,
    damage: str,
) -> None:
    fixture = _fixture(tmp_path)
    if damage == "head":
        (fixture.src / "src/main.c").write_text("int changed;\n", encoding="utf-8")
        _git(fixture.src, "add", "src/main.c")
        _git(fixture.src, "commit", "-m", "wrong head")
    elif damage == "origin":
        _git(fixture.src, "remote", "set-url", "origin", "ssh://review.tizen.org/wrong")
    else:
        (fixture.src / ".campaign_clone").write_text("{}\n", encoding="utf-8")
    called = {"build": False}

    def forbidden(options: BuildVerifyOptions) -> BuildVerifyResult:
        called["build"] = True
        raise AssertionError("identity mismatch must stop before build")

    outcome = campaign_repair_step(fixture.options, build_verify_fn=forbidden)

    assert outcome.exit_code == 4
    assert outcome.result.error_code == REJECTED_IDENTITY_MISMATCH
    assert called["build"] is False


def test_conf_drift_is_rejected_after_invocation_without_build(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture.conf.write_text("[general]\nchanged=true\n", encoding="utf-8")
    called = {"build": False}

    def forbidden(options: BuildVerifyOptions) -> BuildVerifyResult:
        called["build"] = True
        raise AssertionError("conf drift must stop before build")

    outcome = campaign_repair_step(fixture.options, build_verify_fn=forbidden)

    assert outcome.exit_code == 4
    assert outcome.result.error_code == "REJECTED_CONF_DRIFT"
    assert outcome.result.invocations_used == 1
    assert called["build"] is False


def test_reconciliation_arrays_use_objects_and_deterministic_sorting() -> None:
    reconciliation, warnings = repair_step._serialize_reconciliation(
        ReconcileResult(
            branch="proceed",
            current_verification_id=None,
            current_relinked_invocation_event_id=None,
            other_round_relinks=((2, "V2", 8), (1, "V9", 9), (1, "V1", 7)),
            backfilled_invocation_event_ids=(),
            orphan_pass_verification_ids=(),
            held_rounds=(),
            non_campaign_verification_ids=("V9", "V1", "V9"),
        )
    )

    assert reconciliation["other_round_relinks"] == [
        {"round_index": 1, "verification_id": "V1", "invocation_event_id": 7},
        {"round_index": 1, "verification_id": "V9", "invocation_event_id": 9},
        {"round_index": 2, "verification_id": "V2", "invocation_event_id": 8},
    ]
    assert reconciliation["non_campaign_verification_ids"] == ["V1", "V9"]
    assert warnings == [
        {"code": "non_campaign_verification", "verification_id": "V1"},
        {"code": "non_campaign_verification", "verification_id": "V9"},
    ]


def test_non_campaign_record_is_reported_as_sorted_structured_warning(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    dummy = BuildVerifyOptions(
        src_clean=fixture.src,
        base_commit=fixture.base_commit,
        edit_spec_path=fixture.edit_spec,
        gbs_conf=fixture.conf,
        package="united-service",
        workspace_root=fixture.workspace,
        baseline_evidence=fixture.evidence,
        output_dir=tmp_path / "dummy",
        iter_index=1,
        wall_timeout=3600,
        state_db=fixture.db,
        ci_system="quickbuild",
        build_id="1127447",
        project=PROJECT,
        branch="tizen",
        arch=ARCH_RAW,
    )
    _write_pass_record(
        fixture,
        dummy,
        verification_id="verify-external",
        edit_sha="f" * 64,
    )

    outcome = campaign_repair_step(fixture.options, build_verify_fn=_pass_builder(fixture))

    assert outcome.exit_code == 0
    assert outcome.result.reconciliation["non_campaign_verification_ids"] == [
        "verify-external"
    ]
    assert outcome.result.warnings == [
        {
            "code": "non_campaign_verification",
            "verification_id": "verify-external",
        }
    ]


def test_previous_resolver_handles_pass_and_na_history(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    first = consume_build_invocation(
        fixture.db,
        UNIT_KEY,
        round_index=_ensure_round(fixture),
        arch_norm=ARCH_NORM,
    )
    current = tmp_path / "first-fail.json"
    current.write_text(json.dumps(BASE_PACKET) + "\n", encoding="utf-8")
    append_event(
        fixture.db,
        UNIT_KEY,
        "CONVERGENCE",
        _fail_convergence(first.event_id, current),
    )
    second = consume_build_invocation(
        fixture.db,
        UNIT_KEY,
        round_index=1,
        arch_norm=ARCH_NORM,
    )
    append_event(
        fixture.db,
        UNIT_KEY,
        "CONVERGENCE",
        _na_convergence(second.event_id, "orphan_invocation"),
    )

    resolved = resolve(fixture.db, UNIT_KEY, arch_norm=ARCH_NORM)

    assert isinstance(resolved, ResolvedEvidence)
    assert resolved.basis == "prev_build"
    assert resolved.evidence_path == str(current)

    third = consume_build_invocation(
        fixture.db,
        UNIT_KEY,
        round_index=1,
        arch_norm=ARCH_NORM,
    )
    append_event(
        fixture.db,
        UNIT_KEY,
        "CONVERGENCE",
        {
            **_na_convergence(third.event_id, "orphan_invocation"),
            "result": "PASS",
            "reason": "build_passed",
            "verification_id": "verify-synthetic",
        },
    )
    synthetic = resolve(fixture.db, UNIT_KEY, arch_norm=ARCH_NORM)
    assert isinstance(synthetic, ResolvedEvidence)
    assert synthetic.basis == "synthetic_zero"
    assert synthetic.evidence["primary_error"] is None


def test_previous_resolver_rebaselined_falls_back_to_latest_reproduce(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _ensure_round(fixture)
    append_event(
        fixture.db,
        UNIT_KEY,
        "CONVERGENCE",
        {
            "round_index": 1,
            "arch_norm": ARCH_NORM,
            "invocation_event_id": None,
            "result": "n_a",
            "verdict": "n_a",
            "reason": "rebaselined",
            "evidence_path": None,
            "evidence_sha256": None,
            "verification_id": None,
            "actual_changed_paths": [],
            "previous_basis": "none",
            "at": "2026-08-05T00:00:00+00:00",
        },
    )

    resolved = resolve(fixture.db, UNIT_KEY, arch_norm=ARCH_NORM)

    assert isinstance(resolved, ResolvedEvidence)
    assert resolved.basis == "reproduce"
    assert resolved.evidence_path == str(fixture.evidence)


def test_previous_resolver_fails_closed_for_missing_substantive_file(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    invocation = consume_build_invocation(
        fixture.db,
        UNIT_KEY,
        round_index=_ensure_round(fixture),
        arch_norm=ARCH_NORM,
    )
    missing = tmp_path / "missing-current.json"
    append_event(
        fixture.db,
        UNIT_KEY,
        "CONVERGENCE",
        {
            **_fail_convergence(invocation.event_id, fixture.evidence),
            "evidence_path": str(missing),
            "evidence_sha256": "f" * 64,
        },
    )

    resolved = resolve(fixture.db, UNIT_KEY, arch_norm=ARCH_NORM)

    assert isinstance(resolved, MissingEvidence)


def test_campaign_repair_step_help_uses_dedicated_parser(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["campaign-repair-step", "--help"])

    assert excinfo.value.code == 0
    output = capsys.readouterr().out
    assert "--campaign-unit-key" in output
    assert "--round-index" in output
    assert "--edit-spec" in output
    assert "--src-clean" not in output


def test_python_m_campaign_repair_step_emits_one_json_document(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    # Prepare an already-linked round so the subprocess smoke never invokes gbs.
    unit_hash = hashlib.sha256(UNIT_KEY.encode()).hexdigest()[:12]
    canonical = fixture.workspace / unit_hash / ARCH_NORM / "out/round_1/edit_spec.json"
    canonical.parent.mkdir(parents=True)
    canonical.write_bytes(fixture.edit_spec.read_bytes())
    create_round(
        fixture.db,
        UNIT_KEY,
        round_index=1,
        edit_spec_ref=str(canonical),
        edit_spec_sha256=_sha(canonical),
    )
    receipt = consume_build_invocation(
        fixture.db,
        UNIT_KEY,
        round_index=1,
        arch_norm=ARCH_NORM,
    )
    dummy = BuildVerifyOptions(
        src_clean=fixture.src,
        base_commit=fixture.base_commit,
        edit_spec_path=canonical,
        gbs_conf=fixture.conf,
        package="united-service",
        workspace_root=canonical.parents[2],
        baseline_evidence=fixture.evidence,
        output_dir=canonical.parent,
        iter_index=1,
        wall_timeout=3600,
        state_db=fixture.db,
        ci_system="quickbuild",
        build_id="1127447",
        project=PROJECT,
        branch="tizen",
        arch=ARCH_RAW,
    )
    _write_pass_record(fixture, dummy)
    link_verification_with_convergence(
        fixture.db,
        UNIT_KEY,
        convergence_payload={
            "round_index": 1,
            "arch_norm": ARCH_NORM,
            "invocation_event_id": receipt.event_id,
            "result": "PASS",
            "verdict": "n_a",
            "reason": "build_passed",
            "evidence_path": None,
            "evidence_sha256": None,
            "verification_id": "verify-pass",
            "actual_changed_paths": ["src/main.c"],
            "previous_basis": "none",
            "at": "2026-08-05T00:00:00+00:00",
        },
        arch_raw=ARCH_RAW,
        arch_norm=ARCH_NORM,
        verification_id="verify-pass",
        round_index=1,
        edit_spec_sha256=_sha(canonical),
    )
    env = os.environ.copy()
    scripts = str(Path("tizen-ci-triage/scripts").resolve())
    env["PYTHONPATH"] = (
        scripts
        if not env.get("PYTHONPATH")
        else scripts + os.pathsep + env["PYTHONPATH"]
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ci_triage",
            "campaign-repair-step",
            "--campaign-unit-key",
            UNIT_KEY,
            "--state-db",
            str(fixture.db.path),
            "--config",
            str(fixture.options.config_path),
            "--round-index",
            "1",
            "--edit-spec",
            str(fixture.edit_spec),
            "--arch",
            ARCH_RAW,
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.returncode == 0
    lines = completed.stdout.splitlines()
    assert len(lines) == 1
    value = json.loads(lines[0])
    _assert_fixed_schema(value)
    assert value["result"] == "PASS"
    assert completed.stderr == ""


def _ensure_round(fixture: Fixture) -> int:
    create_round(
        fixture.db,
        UNIT_KEY,
        round_index=1,
        edit_spec_ref=str(fixture.edit_spec),
        edit_spec_sha256=_sha(fixture.edit_spec),
    )
    return 1


def _fail_convergence(invocation_event_id: int, evidence: Path) -> dict[str, object]:
    return {
        "round_index": 1,
        "arch_norm": ARCH_NORM,
        "invocation_event_id": invocation_event_id,
        "result": "FAIL",
        "verdict": "advance",
        "reason": "fingerprint_changed",
        "evidence_path": str(evidence),
        "evidence_sha256": _sha(evidence),
        "verification_id": None,
        "actual_changed_paths": ["src/main.c"],
        "previous_basis": "reproduce",
        "at": "2026-08-05T00:00:00+00:00",
    }


def _na_convergence(invocation_event_id: int, reason: str) -> dict[str, object]:
    return {
        "round_index": 1,
        "arch_norm": ARCH_NORM,
        "invocation_event_id": invocation_event_id,
        "result": "n_a",
        "verdict": "n_a",
        "reason": reason,
        "evidence_path": None,
        "evidence_sha256": None,
        "verification_id": None,
        "actual_changed_paths": [],
        "previous_basis": "none",
        "at": "2026-08-05T00:00:00+00:00",
    }
