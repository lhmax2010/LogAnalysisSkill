from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from ci_triage.state import (
    GERRIT_READY,
    StateDatabase,
    VerificationRecord,
    build_failure_key,
    build_submission_key,
    failure_key_sha12,
    get_latest_status,
    get_latest_status_row,
    get_record,
    record_status,
    write_pass_record,
)


def _db(tmp_path: Path) -> StateDatabase:
    return StateDatabase(tmp_path / "triage_state.sqlite3")


def _failure_key() -> str:
    return build_failure_key(
        ci_system="quickbuild",
        build_id="1118258",
        project="platform/core/multimedia/inference-engine-interface",
        branch="tizen",
        arch="standard-armv7l",
        spec_name="inference-engine-interface",
        base_commit="a" * 40,
    )


def _record() -> VerificationRecord:
    return VerificationRecord(
        verification_id="11111111-2222-3333-4444-555555555555",
        result="PASS",
        timestamp="2026-07-07T10:00:00+08:00",
        failure_key=_failure_key(),
        base_commit="a" * 40,
        verified_commit_sha="b" * 40,
        verified_tree_sha="c" * 40,
        canonical_diff_sha256="d" * 64,
        patch_sha256="e" * 64,
        edit_spec_sha256="f" * 64,
        project="platform/core/multimedia/inference-engine-interface",
        branch="tizen",
        spec_name="inference-engine-interface",
        arch="standard-armv7l",
        gbs_conf_sha256="1" * 64,
        build_log_sha256="2" * 64,
        worktree_path="/tmp/ci-triage/worktree",
        command_line="gbs build -A armv7l",
    )


def test_write_pass_record_round_trips_all_fields(tmp_path: Path) -> None:
    db = _db(tmp_path)
    record = _record()

    verification_id = write_pass_record(db, record)

    assert verification_id == record.verification_id
    assert get_record(db, record.verification_id) == record


def test_write_pass_record_appends_gerrit_ready_status(tmp_path: Path) -> None:
    db = _db(tmp_path)
    record = _record()

    write_pass_record(db, record)

    assert get_latest_status(db, record.failure_key) == GERRIT_READY
    rows = db.get_status_log(record.failure_key)
    assert len(rows) == 1
    assert rows[0]["status"] == GERRIT_READY
    assert rows[0]["verification_id"] == record.verification_id


def test_get_latest_status_row_returns_status_verification_id_and_timestamp(tmp_path: Path) -> None:
    db = _db(tmp_path)
    record = _record()
    record_status(db, record.failure_key, "DISCOVERED")
    write_pass_record(db, record)

    row = get_latest_status_row(db, record.failure_key)

    assert row is not None
    assert row.status == GERRIT_READY
    assert row.verification_id == record.verification_id
    assert row.timestamp


def test_status_log_is_append_only_and_latest_status_uses_newest_row(tmp_path: Path) -> None:
    db = _db(tmp_path)
    unit_key = _failure_key()

    record_status(db, unit_key, "DISCOVERED", reason="found in QuickBuild")
    record_status(db, unit_key, "REPAIR_EXHAUSTED", reason="all candidates failed")

    rows = db.get_status_log(unit_key)
    assert [row["status"] for row in rows] == ["DISCOVERED", "REPAIR_EXHAUSTED"]
    assert get_latest_status(db, unit_key) == "REPAIR_EXHAUSTED"


def test_record_status_rejects_gerrit_ready(tmp_path: Path) -> None:
    db = _db(tmp_path)

    with pytest.raises(ValueError, match="GERRIT_READY"):
        record_status(db, _failure_key(), GERRIT_READY)

    assert db.get_status_log(_failure_key()) == ()


def test_write_pass_record_rejects_non_pass_result(tmp_path: Path) -> None:
    db = _db(tmp_path)

    with pytest.raises(ValueError, match="PASS"):
        write_pass_record(db, replace(_record(), result="FAIL"))


def test_failure_and_submission_keys_are_stable() -> None:
    failure_key = _failure_key()
    submission_key = build_submission_key(failure_key=failure_key, verified_tree_sha="c" * 40)

    assert failure_key == (
        "quickbuild/1118258/platform/core/multimedia/inference-engine-interface/"
        "tizen/standard-armv7l/inference-engine-interface/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    )
    assert _failure_key() == failure_key
    assert submission_key == build_submission_key(
        failure_key=failure_key,
        verified_tree_sha="c" * 40,
    )
    assert len(submission_key) == 64
    assert all(char in "0123456789abcdef" for char in submission_key)
    assert "/" not in submission_key
    assert ":" not in submission_key
    assert failure_key not in submission_key
    assert submission_key != build_submission_key(
        failure_key=failure_key,
        verified_tree_sha="d" * 40,
    )


def test_failure_key_sha12_is_stable_and_short() -> None:
    digest = failure_key_sha12(_failure_key())

    assert digest == failure_key_sha12(_failure_key())
    assert len(digest) == 12
    assert all(char in "0123456789abcdef" for char in digest)


def test_wal_allows_same_process_connections_to_read_after_alternating_writes(
    tmp_path: Path,
) -> None:
    db1 = _db(tmp_path)
    db2 = _db(tmp_path)
    unit_key = _failure_key()

    record_status(db1, unit_key, "DISCOVERED")
    assert get_latest_status(db2, unit_key) == "DISCOVERED"

    record_status(db2, unit_key, "GERRIT_DRY_RUN", reason="dry run ok")
    assert get_latest_status(db1, unit_key) == "GERRIT_DRY_RUN"

    conn = db1.connect()
    try:
        mode = conn.execute("PRAGMA journal_mode").fetchone()
    finally:
        conn.close()
    assert mode is not None
    assert mode[0] == "wal"
