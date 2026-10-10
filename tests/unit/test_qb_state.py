from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest
from ci_triage import campaign_state as state
from ci_triage.qb_config import canonical_profile_json
from tizen_ci_shared.state import StateDatabase


@pytest.fixture
def db(tmp_path):
    database = StateDatabase(tmp_path / "campaign.sqlite3")
    state.create_unit(
        database,
        campaign_unit_key="unit",
        submission_identity_key="submission",
        ci_system="quickbuild",
        source_build_id="build",
        project="repo/pkg",
        branch="tizen_base",
        spec_name="pkg",
        base_commit="a" * 40,
        primary_arch="standard-aarch64",
        failed_arches=["standard-aarch64"],
        toolchain_profile="toolchain",
        ci_evidence_ref="evidence.json",
        ci_evidence_sha256="b" * 64,
        max_rounds=3,
        max_build_invocations=9,
    )
    return database


def profile(branch="tizen_base", snapshot="20261010"):
    return canonical_profile_json(
        {
            "configuration_path": "root/" + branch + "/RBS/TRIGGER",
            "overview_id": 1,
            "project_name": "test-工程",
            "qb_pass_requires_accept": False,
            "form": {
                "BUILD_TYPE": "Full",
                "REPO_TYPE": "ALL",
                "BUILD_REFERENCE": "Ref. Snapshot",
                "SNAPSHOT_NUM": snapshot,
                "PROJECT_BRANCH": branch,
                "Immediate Stop With Error": True,
                "CHILD_CONFIGURATIONS": ["standard-armv7l:aarch64:x86_64"],
                "TARGET_IMAGE": [],
                "Add Package List": "",
                "Remove Package List": "",
            },
        }
    )


def snapshot(db):
    conn = db.connect()
    try:
        return {
            table: [tuple(row) for row in conn.execute(f"SELECT * FROM {table}")]
            for table in (
                "campaign_qb_profiles",
                "campaign_qb_requests",
                "campaign_qb_events",
                "campaign_status_log",
            )
        }
    finally:
        conn.close()


def intent(conn):
    state._insert_qb_profile_on_connection(conn, "tizen_base", profile_json=profile())
    seq = state._create_qb_request_on_connection(
        conn,
        "unit",
        request_id="request",
        sbs_target="repo/pkg@commit",
    )
    state._append_status_on_connection(conn, "unit", "QB_REQUESTED")
    return seq


def test_all_primitives_accept_outer_transaction_and_do_not_manage_it(db, monkeypatch):
    conn = db.connect()
    sql = []
    conn.execute("BEGIN IMMEDIATE")
    conn.set_trace_callback(sql.append)
    monkeypatch.setattr(state, "_connect", lambda *a: pytest.fail("primitive opened connection"))
    try:
        seq = intent(conn)
        state._append_qb_event_on_connection(
            conn,
            request_seq=seq,
            event_type="BUILD_BOUND",
            qb_build_id="build",
        )
        state._append_qb_event_on_connection(
            conn,
            request_seq=seq,
            event_type="RESULT",
            qb_build_id="build",
            status="PASS",
            sbs_target_echo="repo/pkg@commit",
            qb_result_sha256="c" * 64,
        )
        assert conn.in_transaction
        assert not any(
            s.lstrip().split()[0] in {"BEGIN", "COMMIT", "ROLLBACK", "CREATE"} for s in sql
        )
        assert snapshot(db)["campaign_qb_requests"] == []
        conn.commit()
        assert len(snapshot(db)["campaign_qb_events"]) == 3
        assert state.qb_profile(db, "tizen_base")["profile_json"] == profile()
    finally:
        conn.close()


@pytest.mark.parametrize("point", ["intent", "not_released", "binding", "pending", "result"])
def test_each_write_group_rolls_back_on_injected_failure(db, point):
    seq = None
    if point != "intent":
        seq = state.create_qb_request(
            db, "unit", request_id="request", sbs_target="repo/pkg@commit"
        )
    if point == "result":
        state.append_qb_event(db, request_seq=seq, event_type="BUILD_BOUND", qb_build_id="build")
    before = snapshot(db)
    conn = db.connect()
    try:
        with pytest.raises(RuntimeError, match="injected"):
            with state._immediate_transaction(conn):
                if point == "intent":
                    intent(conn)
                elif point == "binding":
                    state._append_qb_event_on_connection(
                        conn,
                        request_seq=seq,
                        event_type="BUILD_BOUND",
                        qb_build_id="build",
                    )
                elif point == "result":
                    state._append_qb_event_on_connection(
                        conn,
                        request_seq=seq,
                        event_type="RESULT",
                        status="PASS",
                        sbs_target_echo="repo/pkg@commit",
                        qb_result_sha256="c" * 64,
                    )
                else:
                    status = "QB_SUBMIT_FAILED" if point == "not_released" else "SANDBOX_QB_PENDING"
                    state._append_status_on_connection(conn, "unit", status)
                raise RuntimeError("injected")
        assert not conn.in_transaction
    finally:
        conn.close()
    assert snapshot(db) == before


def test_profile_first_write_idempotence_and_bytes(db):
    conn = db.connect()
    try:
        with state._immediate_transaction(conn):
            state._insert_qb_profile_on_connection(conn, "tizen_base", profile_json=profile())
        first = state.qb_profile(db, "tizen_base")
        assert first["profile_sha256"] == hashlib.sha256(profile().encode()).hexdigest()
        assert datetime.fromisoformat(first["created_at"]).utcoffset() == timezone.utc.utcoffset(
            None
        )
        with state._immediate_transaction(conn):
            state._insert_qb_profile_on_connection(conn, "tizen_base", profile_json=profile())
        assert state.qb_profile(db, "tizen_base") == first
        with pytest.raises(state.StateInconsistent), state._immediate_transaction(conn):
            state._insert_qb_profile_on_connection(conn, "tizen_base", profile_json=profile() + " ")
        assert state.qb_profile(db, "tizen_base") == first
    finally:
        conn.close()


@pytest.mark.parametrize("changed", [False, True])
def test_other_connection_wins_concurrent_freeze(db, changed):
    first = db.connect()
    first.execute("BEGIN IMMEDIATE")
    state._insert_qb_profile_on_connection(first, "tizen_base", profile_json=profile())
    started = threading.Event()
    outcome = []

    def contender():
        conn = db.connect()
        started.set()
        try:
            with state._immediate_transaction(conn):
                state._insert_qb_profile_on_connection(
                    conn,
                    "tizen_base",
                    profile_json=profile(snapshot="other") if changed else profile(),
                )
                state._create_qb_request_on_connection(
                    conn,
                    "unit",
                    request_id="contender",
                    sbs_target="repo@commit",
                )
            outcome.append("ok")
        except state.StateInconsistent:
            outcome.append("different")
        finally:
            conn.close()

    thread = threading.Thread(target=contender)
    thread.start()
    try:
        assert started.wait(5)
        first.commit()
    finally:
        first.close()
        thread.join(10)
    assert not thread.is_alive()
    assert outcome == (["different"] if changed else ["ok"])
    rows = snapshot(db)
    assert len(rows["campaign_qb_profiles"]) == 1
    assert len(rows["campaign_qb_requests"]) == (0 if changed else 1)
    assert state.qb_profile(db, "tizen_base")["profile_json"] == profile()


def test_branches_and_campaigns_have_independent_profiles(db, tmp_path):
    conn = db.connect()
    try:
        with state._immediate_transaction(conn):
            for branch in ("tizen_base", "tizen"):
                state._insert_qb_profile_on_connection(conn, branch, profile_json=profile(branch))
    finally:
        conn.close()
    for branch in ("tizen_base", "tizen"):
        assert state.qb_profile(db, branch)["profile_json"] == profile(branch)
    assert state.qb_profile(db, "unknown") is None
    other = StateDatabase(tmp_path / "other.sqlite3")
    state.ensure_schema(other)
    conn = other.connect()
    try:
        with state._immediate_transaction(conn):
            state._insert_qb_profile_on_connection(
                conn, "tizen_base", profile_json=profile(snapshot="new")
            )
    finally:
        conn.close()
    assert state.qb_profile(other, "tizen_base")["profile_json"] != profile()
    assert state.qb_profile(db, "tizen_base")["profile_json"] == profile()


@pytest.mark.parametrize("digest", ["", "a" * 63, "a" * 65, "A" * 64, "g" * 64, "１" * 64])
def test_profile_sha256_check_rejects_invalid_values(db, digest):
    conn = db.connect()
    try:
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
            conn.execute(
                "INSERT INTO campaign_qb_profiles VALUES (?, ?, ?, ?)",
                ("tizen_base", profile(), digest, "2026-10-10T00:00:00Z"),
            )
    finally:
        conn.close()


def test_qb_profile_query_is_read_only(db, monkeypatch):
    monkeypatch.setattr(
        state, "_connect", lambda *a: pytest.fail("read must not initialize schema")
    )
    before = db.path.read_bytes()
    assert state.qb_profile(db, "missing") is None
    assert db.path.read_bytes() == before


def test_request_primitive_keeps_submitted_and_idempotence(db):
    conn = db.connect()
    try:
        with state._immediate_transaction(conn):
            seq = intent(conn)
            assert (
                state._create_qb_request_on_connection(
                    conn,
                    "unit",
                    request_id="request",
                    sbs_target="repo/pkg@commit",
                )
                == seq
            )
            assert conn.execute("SELECT COUNT(*) FROM campaign_qb_events").fetchone()[0] == 1
            with pytest.raises(state.StateInconsistent):
                state._create_qb_request_on_connection(
                    conn,
                    "unit",
                    request_id="request",
                    sbs_target="other",
                )
            assert conn.in_transaction
            with pytest.raises(state.PayloadSchemaError):
                state._append_qb_event_on_connection(conn, request_seq=seq, event_type="SUBMITTED")
            assert conn.in_transaction
    finally:
        conn.close()


def test_primitives_do_not_initialize_schema():
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("BEGIN IMMEDIATE")
        for call in (
            lambda: state._insert_qb_profile_on_connection(conn, "tizen", profile_json=profile()),
            lambda: state._create_qb_request_on_connection(
                conn, "u", request_id="r", sbs_target="s"
            ),
            lambda: state._append_qb_event_on_connection(
                conn, request_seq=1, event_type="BUILD_BOUND"
            ),
            lambda: state._append_status_on_connection(conn, "u", "QB_REQUESTED"),
        ):
            with pytest.raises(sqlite3.OperationalError, match="no such table"):
                call()
            assert conn.in_transaction
        assert conn.execute("SELECT name FROM sqlite_master").fetchall() == []
    finally:
        conn.close()


@pytest.mark.parametrize(
    "key", ["configuration_path", "overview_id", "project_name", "form", "qb_pass_requires_accept"]
)
def test_each_profile_key_change_conflicts_without_request(db, key):
    original = json.loads(profile())
    changed = copy.deepcopy(original)
    changed[key] = not original[key] if isinstance(original[key], bool) else "changed"
    conn = db.connect()
    try:
        with state._immediate_transaction(conn):
            state._insert_qb_profile_on_connection(conn, "tizen_base", profile_json=profile())
        with pytest.raises(state.StateInconsistent), state._immediate_transaction(conn):
            state._insert_qb_profile_on_connection(
                conn,
                "tizen_base",
                profile_json=json.dumps(changed, sort_keys=True),
            )
            state._create_qb_request_on_connection(conn, "unit", request_id="r", sbs_target="s")
    finally:
        conn.close()
    assert snapshot(db)["campaign_qb_requests"] == []


def test_profile_ddl_is_frozen_verbatim():
    design = (
        Path(__file__).resolve().parents[2] / "docs/clang-fix-campaign/"
        "p5q-qb-trigger-design-v1.2-FROZEN.md"
    ).read_text()
    start = design.index("CREATE TABLE IF NOT EXISTS campaign_qb_profiles")
    assert design[start : design.index(";", start) + 1] in state._SCHEMA_SQL


@pytest.mark.parametrize(
    "key",
    [
        "BUILD_TYPE",
        "REPO_TYPE",
        "BUILD_REFERENCE",
        "SNAPSHOT_NUM",
        "PROJECT_BRANCH",
        "Immediate Stop With Error",
        "CHILD_CONFIGURATIONS",
        "TARGET_IMAGE",
        "Add Package List",
        "Remove Package List",
    ],
)
def test_frozen_profile_detects_each_form_field_change(db, key):
    modified = json.loads(profile())
    modified["form"][key] = "changed"
    conn = db.connect()
    try:
        with state._immediate_transaction(conn):
            state._insert_qb_profile_on_connection(conn, "tizen_base", profile_json=profile())
        with pytest.raises(state.StateInconsistent), state._immediate_transaction(conn):
            state._insert_qb_profile_on_connection(
                conn,
                "tizen_base",
                profile_json=json.dumps(
                    modified, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                ),
            )
    finally:
        conn.close()
    assert state.qb_profile(db, "tizen_base")["profile_json"] == profile()
