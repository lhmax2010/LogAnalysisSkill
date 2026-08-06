from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from pathlib import Path

import pytest
from ci_triage.campaign_state import (
    ARCH_NORMS,
    CAMPAIGN_SCHEMA_VERSION,
    HELD_FOR_INVESTIGATION,
    REJECTED_ARCH_NOT_ALLOWED,
    AmbiguousQbReference,
    BudgetExhausted,
    CampaignStateBusy,
    PayloadSchemaError,
    RoundsExhausted,
    StateInconsistent,
    UnknownEventType,
    adopt_secondary_target_with_convergence,
    append_event,
    append_qb_event,
    append_status,
    consume_build_invocation,
    create_arch_rejected_unit,
    create_qb_request,
    create_round,
    create_unit,
    ensure_schema,
    find_unit_by_qb_build_id,
    find_unit_by_request_id,
    find_unlinked_pass,
    get_round,
    get_unit,
    invocations_used,
    latest_event,
    latest_qb_result,
    latest_reproduce,
    latest_round,
    latest_status,
    link_verification_with_convergence,
)
from ci_triage.state import StateDatabase, VerificationRecord, write_pass_record

UNIT_KEY = "campaign-unit-1"
OTHER_UNIT_KEY = "campaign-unit-2"
EDIT_SHA = "e" * 64


def _db(tmp_path: Path, name: str = "state.sqlite3") -> StateDatabase:
    return StateDatabase(tmp_path / name)


def _identity(*, build_id: str = "1127447") -> dict[str, str]:
    return {
        "ci_system": "quickbuild",
        "source_build_id": build_id,
        "project": "platform/core/appfw/united-service",
        "branch": "tizen",
        "spec_name": "united-service",
        "base_commit": "a" * 40,
    }


def _create_unit(
    db: StateDatabase,
    *,
    unit_key: str = UNIT_KEY,
    max_rounds: int = 3,
    max_build_invocations: int = 9,
    build_id: str = "1127447",
) -> None:
    create_unit(
        db,
        campaign_unit_key=unit_key,
        submission_identity_key=f"submission-{unit_key}",
        primary_arch="standard-aarch64",
        failed_arches=("standard-x86_64", "standard-aarch64", "standard-armv7l"),
        toolchain_profile="tizen_unified_standard",
        ci_evidence_ref="/tmp/evidence.json",
        ci_evidence_sha256="c" * 64,
        max_rounds=max_rounds,
        max_build_invocations=max_build_invocations,
        **_identity(build_id=build_id),
    )


def _create_round(
    db: StateDatabase,
    *,
    unit_key: str = UNIT_KEY,
    round_index: int = 1,
    edit_sha: str = EDIT_SHA,
    suffix: str = "one",
) -> None:
    create_round(
        db,
        unit_key,
        round_index=round_index,
        edit_spec_ref=f"relative/{suffix}.json",
        edit_spec_sha256=edit_sha,
    )


def _fail_payload(
    invocation_event_id: int,
    *,
    round_index: int = 1,
    arch_norm: str = "aarch64",
) -> dict[str, object]:
    return {
        "round_index": round_index,
        "arch_norm": arch_norm,
        "invocation_event_id": invocation_event_id,
        "result": "FAIL",
        "verdict": "advance",
        "reason": "fingerprint_changed",
        "evidence_path": "/tmp/current.json",
        "evidence_sha256": "d" * 64,
        "verification_id": None,
        "actual_changed_paths": ["src/main.c"],
        "previous_basis": "reproduce",
        "at": "2026-08-05T00:00:00+00:00",
    }


def _pass_payload(invocation_event_id: int, verification_id: str) -> dict[str, object]:
    return {
        "round_index": 1,
        "arch_norm": "aarch64",
        "invocation_event_id": invocation_event_id,
        "result": "PASS",
        "verdict": "n_a",
        "reason": "build_passed",
        "evidence_path": None,
        "evidence_sha256": None,
        "verification_id": verification_id,
        "actual_changed_paths": ["src/main.c"],
        "previous_basis": "none",
        "at": "2026-08-05T00:00:00+00:00",
    }


def _orphan_payload(invocation_event_id: int) -> dict[str, object]:
    payload = _fail_payload(invocation_event_id)
    payload.update(
        {
            "result": "n_a",
            "verdict": "n_a",
            "reason": "orphan_invocation",
            "evidence_path": None,
            "evidence_sha256": None,
            "actual_changed_paths": [],
            "previous_basis": "none",
        }
    )
    return payload


def _record(
    verification_id: str,
    *,
    arch: str = "standard-aarch64",
    edit_sha: str = EDIT_SHA,
    failure_key: str = "failure-key",
) -> VerificationRecord:
    return VerificationRecord(
        verification_id=verification_id,
        result="PASS",
        timestamp="2026-08-05T00:00:00+00:00",
        failure_key=failure_key,
        base_commit="a" * 40,
        verified_commit_sha="b" * 40,
        verified_tree_sha="c" * 40,
        canonical_diff_sha256="d" * 64,
        patch_sha256="f" * 64,
        edit_spec_sha256=edit_sha,
        project="platform/core/appfw/united-service",
        branch="tizen",
        spec_name="united-service",
        arch=arch,
        gbs_conf_sha256="1" * 64,
        build_log_sha256="2" * 64,
        worktree_path="/tmp/worktree",
        command_line="gbs build",
    )


def test_ensure_schema_creates_exact_campaign_tables_and_required_guards(
    tmp_path: Path,
) -> None:
    db = _db(tmp_path)

    ensure_schema(db)

    conn = db.connect()
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'campaign_%'"
            )
        }
        index_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'index' "
            "AND name = 'ux_convergence_per_invocation'"
        ).fetchone()
        unit_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'campaign_units'"
        ).fetchone()
        status_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(campaign_status_log)")
        }
    finally:
        conn.close()

    assert tables == {
        "campaign_units",
        "campaign_gate_events",
        "campaign_status_log",
        "campaign_rounds",
        "campaign_verifications",
        "campaign_qb_requests",
        "campaign_qb_events",
    }
    assert index_sql is not None
    normalized_index = " ".join(str(index_sql[0]).split())
    assert "WHERE event_type = 'CONVERGENCE' AND invocation_event_id IS NOT NULL" in (
        normalized_index
    )
    assert unit_sql is not None
    assert "primary_arch IS NULL AND ci_evidence_ref IS NULL" in str(unit_sql[0])
    assert "primary_arch IS NOT NULL AND ci_evidence_ref IS NOT NULL" in str(unit_sql[0])
    assert "arch_norm" in status_columns


def test_create_unit_round_trip_is_idempotent_and_canonicalizes_arch_order(
    tmp_path: Path,
) -> None:
    db = _db(tmp_path)

    _create_unit(db)
    _create_unit(db)

    unit = get_unit(db, UNIT_KEY)
    assert unit is not None
    assert unit.failed_arches == (
        "standard-aarch64",
        "standard-armv7l",
        "standard-x86_64",
    )
    assert unit.schema_version == CAMPAIGN_SCHEMA_VERSION
    conn = db.connect()
    try:
        assert conn.execute("SELECT COUNT(*) FROM campaign_units").fetchone()[0] == 1
    finally:
        conn.close()


def test_create_unit_rejects_conflicting_retry(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)

    with pytest.raises(StateInconsistent, match="differs"):
        create_unit(
            db,
            campaign_unit_key=UNIT_KEY,
            submission_identity_key="changed",
            primary_arch="standard-aarch64",
            failed_arches=("standard-aarch64",),
            toolchain_profile="tizen_unified_standard",
            ci_evidence_ref="/tmp/evidence.json",
            ci_evidence_sha256="c" * 64,
            max_rounds=3,
            max_build_invocations=9,
            **_identity(),
        )


def test_create_arch_rejected_unit_atomically_writes_null_tuple_and_status(
    tmp_path: Path,
) -> None:
    db = _db(tmp_path)

    create_arch_rejected_unit(
        db,
        campaign_unit_key=UNIT_KEY,
        submission_identity_key="submission",
        failed_arches=("emulator-x86_64",),
        reason="unverified profile",
        toolchain_profile="tizen_unified_emulator",
        max_rounds=3,
        max_build_invocations=9,
        **_identity(),
    )

    unit = get_unit(db, UNIT_KEY)
    assert unit is not None
    assert (unit.primary_arch, unit.ci_evidence_ref, unit.ci_evidence_sha256) == (
        None,
        None,
        None,
    )
    assert latest_status(db, UNIT_KEY) == REJECTED_ARCH_NOT_ALLOWED


def test_campaign_unit_half_empty_evidence_tuple_is_blocked_by_check(
    tmp_path: Path,
) -> None:
    db = _db(tmp_path)
    ensure_schema(db)
    conn = db.connect()
    try:
        with pytest.raises(sqlite3.IntegrityError):
            _insert_raw_unit(conn, primary_arch="standard-aarch64", evidence_ref=None)
    finally:
        conn.close()


def test_campaign_unit_check_reverse_validation_fails_when_check_is_removed(
    tmp_path: Path,
) -> None:
    db = _db(tmp_path)
    ensure_schema(db)
    source = db.connect()
    try:
        row = source.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'campaign_units'"
        ).fetchone()
    finally:
        source.close()
    assert row is not None
    table_sql = str(row[0])
    marker = ",\n  CHECK (\n"
    assert marker in table_sql
    schema_without_check = table_sql[: table_sql.index(marker)] + "\n)"
    conn = sqlite3.connect(tmp_path / "without-check.sqlite3")
    try:
        conn.execute(schema_without_check)
        _insert_raw_unit(conn, primary_arch="standard-aarch64", evidence_ref=None)
        assert conn.execute("SELECT COUNT(*) FROM campaign_units").fetchone()[0] == 1
    finally:
        conn.close()


def test_round_crud_enforces_identity_sequence_and_budget(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db, max_rounds=2)

    _create_round(db)
    _create_round(db)
    first = get_round(db, UNIT_KEY, 1)
    assert first is not None
    assert first.edit_spec_ref == str(Path("relative/one.json").resolve())
    assert latest_round(db, UNIT_KEY) == first

    with pytest.raises(StateInconsistent):
        _create_round(db, round_index=1, edit_sha="f" * 64, suffix="other")
    with pytest.raises(StateInconsistent):
        _create_round(db, round_index=2, edit_sha=EDIT_SHA, suffix="two")
    with pytest.raises(StateInconsistent, match="must be 2"):
        _create_round(db, round_index=3, edit_sha="3" * 64, suffix="three")

    _create_round(db, round_index=2, edit_sha="2" * 64, suffix="two")
    with pytest.raises(RoundsExhausted):
        _create_round(db, round_index=3, edit_sha="3" * 64, suffix="three")


def test_round_exact_retry_precedes_exhaustion_check(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db, max_rounds=1)
    _create_round(db)

    _create_round(db)

    conn = db.connect()
    try:
        assert conn.execute("SELECT COUNT(*) FROM campaign_rounds").fetchone()[0] == 1
    finally:
        conn.close()


@pytest.mark.parametrize("edit_spec_ref", ["", "   ", "\t\n"])
def test_create_round_rejects_blank_ref_before_realpath(
    tmp_path: Path,
    edit_spec_ref: str,
) -> None:
    db = _db(tmp_path)
    _create_unit(db)

    with pytest.raises(ValueError, match="edit_spec_ref must be non-empty"):
        create_round(
            db,
            UNIT_KEY,
            round_index=1,
            edit_spec_ref=edit_spec_ref,
            edit_spec_sha256=EDIT_SHA,
        )

    conn = db.connect()
    try:
        assert conn.execute("SELECT COUNT(*) FROM campaign_rounds").fetchone()[0] == 0
    finally:
        conn.close()


def test_consume_returns_inserted_receipt_and_enforces_db_budget(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db, max_build_invocations=2)
    _create_round(db)

    first = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    second = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="armv7l")

    assert first.invocations_used == 1
    assert first.invocations_remaining == 1
    assert second.event_id > first.event_id
    assert second.invocations_used == 2
    assert second.invocations_remaining == 0
    assert invocations_used(db, UNIT_KEY) == 2
    with pytest.raises(BudgetExhausted):
        consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="x86_64")
    assert invocations_used(db, UNIT_KEY) == 2


def test_two_connections_cannot_overspend_one_invocation_budget(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db, max_build_invocations=1)
    _create_round(db)
    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    def consume() -> None:
        barrier.wait()
        try:
            consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
        except BudgetExhausted:
            outcomes.append("exhausted")
        else:
            outcomes.append("consumed")

    threads = [threading.Thread(target=consume), threading.Thread(target=consume)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(outcomes) == ["consumed", "exhausted"]
    assert invocations_used(db, UNIT_KEY) == 1


def test_consume_maps_immediate_lock_timeout_to_busy_without_writing(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    _create_round(db)
    holder = db.connect()
    try:
        holder.execute("BEGIN IMMEDIATE")
        with pytest.raises(CampaignStateBusy, match="CAMPAIGN_STATE_BUSY"):
            consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    finally:
        holder.rollback()
        holder.close()
    assert invocations_used(db, UNIT_KEY) == 0


@pytest.mark.parametrize("second_kind", ["pass", "substantive"])
def test_convergence_index_rejects_second_outcome_for_same_invocation(
    tmp_path: Path,
    second_kind: str,
) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    _create_round(db)
    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    append_event(db, UNIT_KEY, "CONVERGENCE", _fail_payload(receipt.event_id))

    with pytest.raises(StateInconsistent):
        if second_kind == "pass":
            write_pass_record(db, _record("V2"))
            link_verification_with_convergence(
                db,
                UNIT_KEY,
                convergence_payload=_pass_payload(receipt.event_id, "V2"),
                arch_raw="standard-aarch64",
                arch_norm="aarch64",
                verification_id="V2",
                round_index=1,
                edit_spec_sha256=EDIT_SHA,
            )
        else:
            append_event(db, UNIT_KEY, "CONVERGENCE", _fail_payload(receipt.event_id))
    if second_kind == "pass":
        conn = db.connect()
        try:
            assert conn.execute(
                "SELECT COUNT(*) FROM campaign_verifications WHERE verification_id = 'V2'"
            ).fetchone()[0] == 0
        finally:
            conn.close()


def test_convergence_index_allows_orphan_then_new_invocation_outcome(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    _create_round(db)
    old = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    append_event(db, UNIT_KEY, "CONVERGENCE", _orphan_payload(old.event_id))
    new = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")

    append_event(db, UNIT_KEY, "CONVERGENCE", _fail_payload(new.event_id))

    conn = db.connect()
    try:
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM campaign_gate_events WHERE event_type = 'CONVERGENCE'"
            ).fetchone()[0]
            == 2
        )
    finally:
        conn.close()


def test_convergence_index_reverse_validation_allows_duplicate_when_dropped(
    tmp_path: Path,
) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    conn = db.connect()
    try:
        conn.execute("DROP INDEX ux_convergence_per_invocation")
        _insert_raw_convergence(conn, invocation_event_id=77, verification_id="V1")
        _insert_raw_convergence(conn, invocation_event_id=77, verification_id="V2")
        assert conn.execute(
            "SELECT COUNT(*) FROM campaign_gate_events WHERE invocation_event_id = 77"
        ).fetchone()[0] == 2
    finally:
        conn.close()


def test_convergence_binding_accepts_receipt_and_rejects_four_mismatches(
    tmp_path: Path,
) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    _create_unit(db, unit_key=OTHER_UNIT_KEY, build_id="1127448")
    _create_round(db)
    _create_round(db, unit_key=OTHER_UNIT_KEY)
    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    other_receipt = consume_build_invocation(
        db, OTHER_UNIT_KEY, round_index=1, arch_norm="aarch64"
    )
    policy_id = append_event(
        db,
        UNIT_KEY,
        "POLICY",
        {
            "round_index": 1,
            "verdict": "allowed",
            "hits": [],
            "fix_strategy_initial": "code",
            "fix_strategy_final": "code",
            "edit_source_kind": "generated",
        },
    )

    append_event(db, UNIT_KEY, "CONVERGENCE", _fail_payload(receipt.event_id))

    invalid_payloads = [
        _fail_payload(999999),
        _fail_payload(policy_id),
        _fail_payload(other_receipt.event_id),
        _fail_payload(receipt.event_id, round_index=2),
        _fail_payload(receipt.event_id, arch_norm="armv7l"),
    ]
    for payload in invalid_payloads:
        with pytest.raises(StateInconsistent):
            append_event(db, UNIT_KEY, "CONVERGENCE", payload)


def test_convergence_conditional_enums_are_fail_closed(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    _create_round(db)
    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")

    missing_invocation = _orphan_payload(receipt.event_id)
    missing_invocation["invocation_event_id"] = None
    wrong_orphan_result = _orphan_payload(receipt.event_id)
    wrong_orphan_result["result"] = "FAIL"
    wrong_build_result = _fail_payload(receipt.event_id)
    wrong_build_result["result"] = "n_a"
    rebaselined_with_invocation = _orphan_payload(receipt.event_id)
    rebaselined_with_invocation["reason"] = "rebaselined"
    for payload in (
        missing_invocation,
        wrong_orphan_result,
        wrong_build_result,
        rebaselined_with_invocation,
    ):
        with pytest.raises(PayloadSchemaError):
            append_event(db, UNIT_KEY, "CONVERGENCE", payload)


def test_append_status_requires_arch_for_arch_scoped_held_reason(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)

    with pytest.raises(PayloadSchemaError, match="requires arch_norm"):
        append_status(
            db,
            UNIT_KEY,
            HELD_FOR_INVESTIGATION,
            reason="previous_evidence_missing",
        )

    append_status(
        db,
        UNIT_KEY,
        HELD_FOR_INVESTIGATION,
        reason="previous_evidence_missing",
        arch_norm="aarch64",
    )
    assert latest_status(db, UNIT_KEY) == HELD_FOR_INVESTIGATION


def test_append_status_rejects_unknown_held_reason(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)

    with pytest.raises(PayloadSchemaError, match="invalid HELD reason"):
        append_status(
            db,
            UNIT_KEY,
            HELD_FOR_INVESTIGATION,
            reason="invented_reason",
            arch_norm="aarch64",
        )


def test_reproduce_latest_is_filtered_by_arch(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    for arch, outcome in (("aarch64", "matched"), ("armv7l", "baseline_pass")):
        append_event(
            db,
            UNIT_KEY,
            "REPRODUCE",
            {
                "arch_norm": arch,
                "outcome": outcome,
                "evidence_local": f"/tmp/{arch}.json",
                "evidence_sha256": "a" * 64,
                "synthetic_zero_error": outcome == "baseline_pass",
                "gbs_conf_sha256": "b" * 64,
                "ci_evidence_sha256_used": "c" * 64,
                "build_log": f"/tmp/{arch}.log",
                "basis": {},
            },
        )

    event = latest_reproduce(db, UNIT_KEY, arch_norm="armv7l")
    assert event is not None
    assert event["payload"]["outcome"] == "baseline_pass"  # type: ignore[index]


def test_secondary_adoption_and_convergence_commit_atomically(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    _create_round(db)
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    evidence = _evidence("same warning")
    _write_json(baseline, evidence)
    _write_json(current, evidence)
    reproduce_id = append_event(
        db,
        UNIT_KEY,
        "REPRODUCE",
        _reproduce_payload("armv7l", baseline),
    )
    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="armv7l")
    convergence = _fail_payload(receipt.event_id, arch_norm="armv7l")
    convergence["verdict"] = "stalled"
    convergence["evidence_path"] = str(current)
    convergence["evidence_sha256"] = _file_sha(current)

    adopted = adopt_secondary_target_with_convergence(
        db,
        UNIT_KEY,
        arch_norm="armv7l",
        expected_reproduce_event_id=reproduce_id,
        convergence_payload=convergence,
    )

    assert adopted is True
    adoption = latest_event(db, UNIT_KEY, "SECONDARY_TARGET_ADOPTED")
    outcome = latest_event(db, UNIT_KEY, "CONVERGENCE")
    assert adoption is not None
    assert outcome is not None
    assert adoption["payload"]["baseline_error_count"] == 1  # type: ignore[index]
    assert outcome["payload"]["verdict"] == "advance"  # type: ignore[index]
    assert (
        adopt_secondary_target_with_convergence(
            db,
            UNIT_KEY,
            arch_norm="armv7l",
            expected_reproduce_event_id=reproduce_id,
            convergence_payload=convergence,
        )
        is False
    )


def test_secondary_adoption_rejects_changed_or_truncated_evidence(tmp_path: Path) -> None:
    for suffix, current_evidence in (
        ("changed", _evidence("different warning")),
        ("truncated", {**_evidence("same warning"), "truncated": True}),
        (
            "clusters-truncated",
            {
                **_evidence("same warning"),
                "error_clusters": {
                    **_evidence("same warning")["error_clusters"],  # type: ignore[dict-item]
                    "truncated": True,
                },
            },
        ),
    ):
        db = _db(tmp_path, f"{suffix}.sqlite3")
        _create_unit(db)
        _create_round(db)
        baseline = tmp_path / f"{suffix}-baseline.json"
        current = tmp_path / f"{suffix}-current.json"
        _write_json(baseline, _evidence("same warning"))
        _write_json(current, current_evidence)
        reproduce_id = append_event(
            db,
            UNIT_KEY,
            "REPRODUCE",
            _reproduce_payload("armv7l", baseline),
        )
        receipt = consume_build_invocation(
            db, UNIT_KEY, round_index=1, arch_norm="armv7l"
        )
        convergence = _fail_payload(receipt.event_id, arch_norm="armv7l")
        convergence["verdict"] = "stalled"
        convergence["evidence_path"] = str(current)
        convergence["evidence_sha256"] = _file_sha(current)

        assert (
            adopt_secondary_target_with_convergence(
                db,
                UNIT_KEY,
                arch_norm="armv7l",
                expected_reproduce_event_id=reproduce_id,
                convergence_payload=convergence,
            )
            is False
        )
        assert latest_event(db, UNIT_KEY, "SECONDARY_TARGET_ADOPTED") is None
        assert latest_event(db, UNIT_KEY, "CONVERGENCE") is None


def test_secondary_adoption_rolls_back_if_convergence_slot_is_already_filled(
    tmp_path: Path,
) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    _create_round(db)
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    _write_json(baseline, _evidence("same warning"))
    _write_json(current, _evidence("same warning"))
    reproduce_id = append_event(
        db,
        UNIT_KEY,
        "REPRODUCE",
        _reproduce_payload("armv7l", baseline),
    )
    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="armv7l")
    convergence = _fail_payload(receipt.event_id, arch_norm="armv7l")
    convergence["verdict"] = "stalled"
    convergence["evidence_path"] = str(current)
    convergence["evidence_sha256"] = _file_sha(current)
    append_event(db, UNIT_KEY, "CONVERGENCE", convergence)

    with pytest.raises(StateInconsistent):
        adopt_secondary_target_with_convergence(
            db,
            UNIT_KEY,
            arch_norm="armv7l",
            expected_reproduce_event_id=reproduce_id,
            convergence_payload=convergence,
        )

    assert latest_event(db, UNIT_KEY, "SECONDARY_TARGET_ADOPTED") is None


def test_concurrent_secondary_adoption_has_exactly_one_winner(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    _create_round(db)
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    _write_json(baseline, _evidence("same warning"))
    _write_json(current, _evidence("same warning"))
    reproduce_id = append_event(
        db,
        UNIT_KEY,
        "REPRODUCE",
        _reproduce_payload("armv7l", baseline),
    )
    first = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="armv7l")
    second = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="armv7l")
    barrier = threading.Barrier(2)
    outcomes: list[bool] = []

    def adopt(invocation_event_id: int) -> None:
        convergence = _fail_payload(invocation_event_id, arch_norm="armv7l")
        convergence["verdict"] = "stalled"
        convergence["evidence_path"] = str(current)
        convergence["evidence_sha256"] = _file_sha(current)
        barrier.wait()
        outcomes.append(
            adopt_secondary_target_with_convergence(
                db,
                UNIT_KEY,
                arch_norm="armv7l",
                expected_reproduce_event_id=reproduce_id,
                convergence_payload=convergence,
            )
        )

    threads = [
        threading.Thread(target=adopt, args=(first.event_id,)),
        threading.Thread(target=adopt, args=(second.event_id,)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(outcomes) == [False, True]
    conn = db.connect()
    try:
        assert conn.execute(
            "SELECT COUNT(*) FROM campaign_gate_events "
            "WHERE event_type = 'SECONDARY_TARGET_ADOPTED'"
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM campaign_gate_events WHERE event_type = 'CONVERGENCE'"
        ).fetchone()[0] == 1
    finally:
        conn.close()


def test_link_verification_and_pass_convergence_are_atomic(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    _create_round(db)
    record = _record("V-LINK")
    write_pass_record(db, record)
    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")

    link_verification_with_convergence(
        db,
        UNIT_KEY,
        convergence_payload=_pass_payload(receipt.event_id, record.verification_id),
        arch_raw="standard-aarch64",
        arch_norm="aarch64",
        verification_id=record.verification_id,
        round_index=1,
        edit_spec_sha256=EDIT_SHA,
    )

    conn = db.connect()
    try:
        assert conn.execute("SELECT COUNT(*) FROM campaign_verifications").fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM campaign_gate_events "
            "WHERE event_type = 'CONVERGENCE' AND verdict = 'n_a'"
        ).fetchone()[0] == 1
    finally:
        conn.close()


def test_link_mismatch_rolls_back_link_and_event(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    _create_round(db)
    record = _record("V-BAD")
    write_pass_record(db, record)
    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
    payload = _pass_payload(receipt.event_id, record.verification_id)

    with pytest.raises(StateInconsistent):
        link_verification_with_convergence(
            db,
            UNIT_KEY,
            convergence_payload=replace_payload(payload, arch_norm="armv7l"),
            arch_raw="standard-aarch64",
            arch_norm="aarch64",
            verification_id=record.verification_id,
            round_index=1,
            edit_spec_sha256=EDIT_SHA,
        )

    conn = db.connect()
    try:
        assert conn.execute("SELECT COUNT(*) FROM campaign_verifications").fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM campaign_gate_events WHERE event_type = 'CONVERGENCE'"
        ).fetchone()[0] == 0
    finally:
        conn.close()


def test_campaign_verification_raw_sql_enforces_both_unique_guards(
    tmp_path: Path,
) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    _create_unit(db, unit_key=OTHER_UNIT_KEY, build_id="1127448")
    _create_round(db)
    _create_round(db, unit_key=OTHER_UNIT_KEY)
    write_pass_record(db, _record("V1"))
    write_pass_record(db, _record("V2"))
    conn = db.connect()
    try:
        conn.execute(
            "INSERT INTO campaign_verifications "
            "(campaign_unit_key, arch_raw, arch_norm, verification_id, round_index, "
            "edit_spec_sha256, campaign_schema_version, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                UNIT_KEY,
                "standard-aarch64",
                "aarch64",
                "V1",
                1,
                EDIT_SHA,
                CAMPAIGN_SCHEMA_VERSION,
                "2026-08-05T00:00:00+00:00",
            ),
        )
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO campaign_verifications "
                "(campaign_unit_key, arch_raw, arch_norm, verification_id, round_index, "
                "edit_spec_sha256, campaign_schema_version, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    OTHER_UNIT_KEY,
                    "standard-armv7l",
                    "armv7l",
                    "V1",
                    1,
                    EDIT_SHA,
                    CAMPAIGN_SCHEMA_VERSION,
                    "2026-08-05T00:01:00+00:00",
                ),
            )
        conn.rollback()

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO campaign_verifications "
                "(campaign_unit_key, arch_raw, arch_norm, verification_id, round_index, "
                "edit_spec_sha256, campaign_schema_version, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    UNIT_KEY,
                    "standard-aarch64",
                    "aarch64",
                    "V2",
                    1,
                    EDIT_SHA,
                    CAMPAIGN_SCHEMA_VERSION,
                    "2026-08-05T00:02:00+00:00",
                ),
            )
    finally:
        conn.close()


def test_campaign_verification_fk_guard_depends_on_foreign_keys_pragma(
    tmp_path: Path,
) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    _create_round(db)
    write_pass_record(db, _record("V-FK"))
    values = (
        UNIT_KEY,
        "standard-aarch64",
        "aarch64",
        "V-FK",
        1,
        "9" * 64,
        CAMPAIGN_SCHEMA_VERSION,
        "2026-08-05T00:00:00+00:00",
    )
    statement = (
        "INSERT INTO campaign_verifications "
        "(campaign_unit_key, arch_raw, arch_norm, verification_id, round_index, "
        "edit_spec_sha256, campaign_schema_version, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    )
    guarded = db.connect()
    try:
        assert guarded.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            guarded.execute(statement, values)
    finally:
        guarded.close()

    unguarded = sqlite3.connect(db.path)
    try:
        assert unguarded.execute("PRAGMA foreign_keys").fetchone()[0] == 0
        unguarded.execute(statement, values)
        assert unguarded.execute(
            "SELECT edit_spec_sha256 FROM campaign_verifications "
            "WHERE verification_id = 'V-FK'"
        ).fetchone()[0] == "9" * 64
    finally:
        unguarded.close()


def test_find_unlinked_pass_returns_all_matches_without_round_argument(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    write_pass_record(db, _record("V1"))
    write_pass_record(db, _record("V2"))
    write_pass_record(db, _record("V3", arch="standard-armv7l"))

    rows = find_unlinked_pass(
        db,
        UNIT_KEY,
        arch_norm="aarch64",
        failure_key="failure-key",
    )

    assert [row["verification_id"] for row in rows] == ["V1", "V2"]


def test_qb_request_and_result_follow_two_level_latest_semantics(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    first = create_qb_request(db, UNIT_KEY, request_id="R1", sbs_target="target")
    append_qb_event(db, request_seq=first, event_type="BUILD_BOUND", qb_build_id="B1")
    append_qb_event(
        db,
        request_seq=first,
        event_type="RESULT",
        qb_build_id="B1",
        status="FAIL",
        sbs_target_echo="target",
        qb_result_sha256="1" * 64,
    )
    second = create_qb_request(db, UNIT_KEY, request_id="R2", sbs_target="target")
    append_qb_event(db, request_seq=second, event_type="BUILD_BOUND", qb_build_id="B2")
    append_qb_event(
        db,
        request_seq=second,
        event_type="RESULT",
        qb_build_id="B2",
        status="PASS",
        accepted=True,
        sbs_target_echo="target",
        qb_result_sha256="2" * 64,
    )

    result = latest_qb_result(db, UNIT_KEY)
    assert result is not None
    assert result["request_seq"] == second
    assert result["status"] == "PASS"
    assert find_unit_by_request_id(db, "R2") == UNIT_KEY
    assert find_unit_by_qb_build_id(db, "B2") == UNIT_KEY


def test_find_unit_by_qb_build_id_rejects_ambiguous_reference(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)
    _create_unit(db, unit_key=OTHER_UNIT_KEY, build_id="1127448")
    first = create_qb_request(db, UNIT_KEY, request_id="R1", sbs_target="target")
    second = create_qb_request(db, OTHER_UNIT_KEY, request_id="R2", sbs_target="target")
    append_qb_event(db, request_seq=first, event_type="BUILD_BOUND", qb_build_id="B1")
    append_qb_event(db, request_seq=second, event_type="BUILD_BOUND", qb_build_id="B1")

    with pytest.raises(AmbiguousQbReference):
        find_unit_by_qb_build_id(db, "B1")


def test_unknown_and_stronger_transaction_event_types_are_rejected(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _create_unit(db)

    with pytest.raises(UnknownEventType):
        append_event(db, UNIT_KEY, "INVENTED", {})
    with pytest.raises(PayloadSchemaError, match="consume_build_invocation"):
        append_event(
            db,
            UNIT_KEY,
            "BUILD_INVOCATION",
            {"round_index": 1, "arch_norm": "aarch64"},
        )
    with pytest.raises(PayloadSchemaError, match="atomic adoption"):
        append_event(db, UNIT_KEY, "SECONDARY_TARGET_ADOPTED", {})
    with pytest.raises(PayloadSchemaError, match="link_verification_with_convergence"):
        append_event(db, UNIT_KEY, "CONVERGENCE", {"result": "PASS"})
    assert latest_event(db, UNIT_KEY, "CONVERGENCE") is None


def _insert_raw_unit(
    conn: sqlite3.Connection,
    *,
    primary_arch: str | None,
    evidence_ref: str | None,
) -> None:
    conn.execute(
        "INSERT INTO campaign_units "
        "(campaign_unit_key, ci_system, source_build_id, project, branch, spec_name, "
        "base_commit, submission_identity_key, toolchain_profile, ci_evidence_ref, "
        "ci_evidence_sha256, primary_arch, max_rounds, max_build_invocations, "
        "failed_arches, created_at, schema_version) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "raw-unit",
            "quickbuild",
            "1",
            "platform/test",
            "tizen",
            "pkg",
            "a" * 40,
            "submission",
            "standard",
            evidence_ref,
            "b" * 64,
            primary_arch,
            3,
            9,
            '["standard-aarch64"]',
            "2026-08-05T00:00:00+00:00",
            CAMPAIGN_SCHEMA_VERSION,
        ),
    )


def _insert_raw_convergence(
    conn: sqlite3.Connection,
    *,
    invocation_event_id: int,
    verification_id: str,
) -> None:
    payload = _pass_payload(invocation_event_id, verification_id)
    conn.execute(
        "INSERT INTO campaign_gate_events "
        "(campaign_unit_key, round_index, arch_norm, verdict, invocation_event_id, "
        "event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            UNIT_KEY,
            1,
            "aarch64",
            "n_a",
            invocation_event_id,
            "CONVERGENCE",
            json.dumps(payload, sort_keys=True),
            "2026-08-05T00:00:00+00:00",
        ),
    )


def replace_payload(payload: dict[str, object], **changes: object) -> dict[str, object]:
    result = dict(payload)
    result.update(changes)
    return result


def _evidence(message: str) -> dict[str, object]:
    return {
        "primary_error": {
            "kind": "werror",
            "normalized_file": "src/main.c",
            "warning_option": "-Wunused-variable",
            "symbol": "value",
            "message": message,
        },
        "error_clusters": {
            "clusters": [
                {
                    "kind": "werror",
                    "diagnostic_kinds": ["werror"],
                    "count": 1,
                    "files": ["src/main.c"],
                    "locations_truncated": False,
                }
            ]
        },
        "truncated": False,
    }


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reproduce_payload(arch_norm: str, evidence: Path) -> dict[str, object]:
    return {
        "arch_norm": arch_norm,
        "outcome": "different_failure",
        "evidence_local": str(evidence),
        "evidence_sha256": _file_sha(evidence),
        "synthetic_zero_error": False,
        "gbs_conf_sha256": "b" * 64,
        "ci_evidence_sha256_used": "c" * 64,
        "build_log": "/tmp/build.log",
        "basis": {},
    }


def test_arch_norm_contract_is_exact_three_value_whitelist() -> None:
    assert ARCH_NORMS == {"aarch64", "armv7l", "x86_64"}
