from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from ci_triage import campaign_state as state
from ci_triage import submission_identity as identity
from tizen_ci_shared.state import StateDatabase

KEY = "a" * 64
HOOK_SHA = "b" * 64
CHANGE_ID = "I" + "c" * 40


@pytest.fixture
def db(tmp_path: Path) -> StateDatabase:
    result = StateDatabase(tmp_path / "state.sqlite3")
    state.ensure_schema(result)
    state.create_unit(
        result,
        campaign_unit_key="unit",
        submission_identity_key="identity",
        primary_arch="standard-aarch64",
        failed_arches=("standard-aarch64",),
        toolchain_profile="profile",
        ci_evidence_ref="evidence.json",
        ci_evidence_sha256="a" * 64,
        max_rounds=3,
        max_build_invocations=9,
        ci_system="quickbuild",
        source_build_id="1",
        project="platform/a",
        branch="tizen",
        spec_name="a",
        base_commit="a" * 40,
    )
    return result


def _derive(db: StateDatabase) -> None:
    state.append_event(
        db,
        "unit",
        "DERIVE",
        dict(
            message_brief="Fix build error",
            author_identity="a <a@invalid>",
            committer_identity="c <c@invalid>",
            author_date="2026-10-08T00:00:00Z",
            committer_date="2026-10-08T00:00:00Z",
            derived_commit_sha="a" * 40,
            verified_tree_sha="b" * 40,
        ),
    )


def _rows(db: StateDatabase) -> list[dict[str, object]]:
    conn = db.connect()
    try:
        return [dict(row) for row in conn.execute("SELECT * FROM campaign_change_ids")]
    finally:
        conn.close()


@pytest.mark.parametrize("field", [
    "message_brief", "author_identity", "committer_identity", "author_date", "committer_date",
])
def test_all_derive_identity_fields_are_immutable(db: StateDatabase, field: str) -> None:
    _derive(db)
    original = state.latest_event(db, "unit", "DERIVE")
    assert original is not None
    payload = dict(original["payload"])
    payload[field] = "2026-10-09T00:00:00Z" if field.endswith("date") else "changed"
    with pytest.raises(state.StateInconsistent, match="first-write identity fields changed"):
        state.append_event(db, "unit", "DERIVE", payload)
    conn = db.connect()
    try:
        assert conn.execute(
            "SELECT COUNT(*) FROM campaign_gate_events WHERE event_type = 'DERIVE'"
        ).fetchone()[0] == 1
    finally:
        conn.close()


def _get(db: StateDatabase, generate=None, **kwargs: object) -> str:
    values = dict(campaign_unit_key="unit", submission_key=KEY, hook_sha256=HOOK_SHA)
    values.update(kwargs)
    return state.get_or_create_change_id(db, generate=generate, **values)


@pytest.mark.parametrize("key", [KEY + "\nChange-Id: injected", KEY[:-1], KEY.upper()])
def test_invalid_submission_key_refuses_before_generation(
    db: StateDatabase, monkeypatch: pytest.MonkeyPatch, key: str,
) -> None:
    generate = Mock(return_value=CHANGE_ID)
    mkdtemp = Mock()
    monkeypatch.setattr(identity.tempfile, "mkdtemp", mkdtemp)
    with pytest.raises(state.StateInconsistent, match="64 lowercase hexadecimal"):
        _get(db, generate, submission_key=key)
    generate.assert_not_called()
    mkdtemp.assert_not_called()
    assert _rows(db) == []


def test_missing_unit_refuses_before_generation(tmp_path: Path) -> None:
    db = StateDatabase(tmp_path / "empty.sqlite3")
    state.ensure_schema(db)
    generate = Mock(return_value=CHANGE_ID)
    with pytest.raises(state.StateInconsistent, match="campaign unit not found"):
        _get(db, generate)
    generate.assert_not_called()
    assert _rows(db) == []


def test_cached_identity_reused_across_builds_hook_upgrades_and_derive(db: StateDatabase) -> None:
    calls = []

    def generate() -> str:
        calls.append(True)
        return CHANGE_ID

    assert _get(db, generate) == CHANGE_ID
    first = _rows(db)
    assert first[0]["hook_sha256"] == HOOK_SHA
    assert first[0]["source"] == "commit_msg_hook"
    assert datetime.fromisoformat(str(first[0]["created_at"])).utcoffset().total_seconds() == 0
    _derive(db)
    assert _get(db, generate, hook_sha256="d" * 64) == CHANGE_ID
    assert _get(db, generate, campaign_unit_key="other-build") == CHANGE_ID
    assert _get(db) == CHANGE_ID
    assert calls == [True]
    assert _rows(db) == first


@pytest.mark.parametrize("has_derive", [False, True])
def test_read_only_cache_miss_does_not_write(db: StateDatabase, has_derive: bool) -> None:
    if has_derive:
        _derive(db)
    with pytest.raises(state.StateInconsistent):
        _get(db)
    assert _rows(db) == []


@pytest.mark.parametrize("with_generator", [False, True])
def test_deleted_cache_with_derive_never_regenerates(
    db: StateDatabase,
    with_generator: bool,
) -> None:
    assert _get(db, lambda: CHANGE_ID) == CHANGE_ID
    _derive(db)
    conn = db.connect()
    try:
        conn.execute("DELETE FROM campaign_change_ids")
        conn.commit()
    finally:
        conn.close()
    calls = []

    def generate() -> str:
        calls.append(True)
        return CHANGE_ID

    with pytest.raises(state.StateInconsistent):
        _get(db, generate if with_generator else None)
    assert calls == []
    assert _rows(db) == []


def test_deleted_cache_without_derive_read_only_refuses(db: StateDatabase) -> None:
    _get(db, lambda: CHANGE_ID)
    conn = db.connect()
    try:
        conn.execute("DELETE FROM campaign_change_ids")
        conn.commit()
    finally:
        conn.close()
    with pytest.raises(state.StateInconsistent):
        _get(db)
    assert _rows(db) == []


def test_two_connections_first_get_insert_one_row_and_return_same_value(db: StateDatabase) -> None:
    barrier = threading.Barrier(2)

    def first_get(char: str) -> str:
        def generate() -> str:
            barrier.wait(timeout=10)
            return "I" + char * 40

        return _get(StateDatabase(db.path), generate)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(first_get, char) for char in ("c", "d")]
        values = [future.result(timeout=15) for future in futures]
    assert values[0] == values[1]
    assert len(_rows(db)) == 1
    assert _rows(db)[0]["change_id"] == values[0]


def test_derive_inserted_by_other_connection_during_generate_refuses(db: StateDatabase) -> None:
    def generate() -> str:
        _derive(StateDatabase(db.path))
        return CHANGE_ID

    with pytest.raises(state.StateInconsistent, match="DERIVE"):
        _get(db, generate)
    assert _rows(db) == []


def test_cache_race_winner_takes_precedence_over_new_derive(db: StateDatabase) -> None:
    def generate() -> str:
        _get(StateDatabase(db.path), lambda: CHANGE_ID)
        _derive(StateDatabase(db.path))
        return "I" + "d" * 40

    assert _get(db, generate) == CHANGE_ID
    assert len(_rows(db)) == 1


def test_change_id_collision_rolls_back_without_replacing_existing(db: StateDatabase) -> None:
    assert _get(db, lambda: CHANGE_ID) == CHANGE_ID
    before = _rows(db)
    with pytest.raises(state.StateInconsistent, match="UNIQUE"):
        _get(db, lambda: CHANGE_ID, submission_key="b" * 64)
    assert _rows(db) == before


def test_generation_failure_does_not_write(db: StateDatabase) -> None:
    def generate() -> str:
        raise RuntimeError("generation failed")

    with pytest.raises(RuntimeError, match="generation failed"):
        _get(db, generate)
    assert _rows(db) == []


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("submission_key", None),
        ("submission_key", ""),
        ("submission_key", "a" * 63),
        ("submission_key", "a" * 65),
        ("submission_key", "A" * 64),
        ("submission_key", "g" * 64),
        ("change_id", None),
        ("change_id", ""),
        ("change_id", "i" + "a" * 40),
        ("change_id", "I" + "A" * 40),
        ("change_id", "I" + "g" * 40),
        ("change_id", "I" + "a" * 39),
        ("change_id", "I" + "a" * 41),
        ("source", None),
        ("source", ""),
        ("source", "hash"),
        ("hook_sha256", None),
        ("hook_sha256", ""),
        ("hook_sha256", "b" * 63),
        ("hook_sha256", "b" * 65),
        ("hook_sha256", "B" * 64),
        ("hook_sha256", "g" * 64),
    ],
)
def test_new_table_rejects_invalid_values(db: StateDatabase, column: str, value: object) -> None:
    row = dict(
        submission_key=KEY,
        change_id=CHANGE_ID,
        source="commit_msg_hook",
        hook_sha256=HOOK_SHA,
        created_at="2026-10-08T00:00:00+00:00",
    )
    row[column] = value
    conn = db.connect()
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO campaign_change_ids VALUES (?, ?, ?, ?, ?)",
                tuple(row.values()),
            )
        conn.rollback()
    finally:
        conn.close()
    assert _rows(db) == []
