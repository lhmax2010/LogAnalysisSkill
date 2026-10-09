from __future__ import annotations

import json
from dataclasses import asdict

import pytest
from ci_triage import campaign_state as state
from tizen_ci_shared.state import StateDatabase


@pytest.fixture
def db(tmp_path):
    database = StateDatabase(tmp_path / "state.sqlite3")
    state.create_unit(
        database, campaign_unit_key="unit", submission_identity_key="identity",
        primary_arch="standard-aarch64",
        failed_arches=("standard-aarch64", "standard-armv7l", "standard-x86_64"),
        toolchain_profile="standard", ci_evidence_ref="evidence.json",
        ci_evidence_sha256="c" * 64, max_rounds=3, max_build_invocations=9,
        ci_system="quickbuild", source_build_id="123", project="project", branch="tizen",
        spec_name="pkg", base_commit="a" * 40,
    )
    return database


def _event(db, kind, payload, *, at="2026-10-09T00:00:00Z", unit="unit"):
    conn = db.connect()
    try:
        with conn:
            conn.execute(
                "INSERT INTO campaign_gate_events "
                "(campaign_unit_key, event_type, round_index, arch_norm, payload_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (unit, kind, payload.get("round_index"), payload.get("arch_norm"),
                 json.dumps(payload), at),
            )
    finally:
        conn.close()


def _reproduce(db, arch, outcome):
    payload = {
        "arch_norm": arch, "outcome": outcome, "evidence_local": f"{arch}.json",
        "evidence_sha256": "e" * 64, "synthetic_zero_error": outcome == "baseline_pass",
        "gbs_conf_sha256": "b" * 64, "ci_evidence_sha256_used": "c" * 64,
        "build_log": "build.log", "basis": {},
    }
    state.append_event(db, "unit", "REPRODUCE", payload)


def _derive():
    return {
        "message_brief": "fix build", "author_identity": "Author <a@example.test>",
        "committer_identity": "Committer <c@example.test>",
        "author_date": "2026-10-09T00:00:00Z", "committer_date": "2026-10-09T00:00:00Z",
        "derived_commit_sha": "d" * 40, "verified_tree_sha": "e" * 40,
    }


@pytest.mark.parametrize(
    "primary,secondary,missing,expected",
    [
        ("matched", "baseline_pass", None, True),
        ("different_failure", "matched", None, False),
        ("baseline_pass", "matched", None, False),
        ("matched", "matched", "aarch64", False),
        ("matched", "matched", "armv7l", False),
        ("matched", "matched", "x86_64", False),
    ],
)
def test_reproduced_depends_on_primary_and_all_three_arches(
    db, primary, secondary, missing, expected,
):
    for arch in ("aarch64", "armv7l", "x86_64"):
        if arch != missing:
            _reproduce(db, arch, primary if arch == "aarch64" else secondary)
    view = state.gate_view(db, "unit")
    assert view.reproduced is expected
    assert set(view.reproduce_by_arch) == state.ARCH_NORMS - {missing}
    for arch, value in view.reproduce_by_arch.items():
        assert value == {
            "outcome": primary if arch == "aarch64" else secondary,
            "evidence_local": f"{arch}.json", "evidence_sha256": "e" * 64,
        }


def test_primary_latest_reproduce_overrides_old_matched(db):
    for arch in state.ARCH_NORMS:
        _reproduce(db, arch, "matched")
    assert state.gate_view(db, "unit").reproduced
    _reproduce(db, "aarch64", "different_failure")
    _reproduce(db, "x86_64", "matched")
    assert not state.gate_view(db, "unit").reproduced


@pytest.mark.parametrize("kind,field", [("POLICY", "policy"), ("KB", "kb"), ("REVIEW", "review")])
def test_latest_payload_uses_event_id_not_timestamp(db, kind, field):
    _event(db, kind, {"value": "old"}, at="2030-01-01T00:00:00Z")
    _event(db, kind, {"value": "new"}, at="2020-01-01T00:00:00Z")
    assert getattr(state.gate_view(db, "unit"), field) == {"value": "new"}


def test_latest_derive_allows_changed_commit_but_not_changed_identity(db):
    before = _derive()
    after = dict(before, derived_commit_sha="f" * 40)
    _event(db, "DERIVE", before, at="2030-01-01T00:00:00Z")
    _event(db, "DERIVE", after, at="2020-01-01T00:00:00Z")
    assert state.gate_view(db, "unit").derive == after


def test_push_classes_have_independent_latest_event(db):
    for ref_class in ("sandbox", "review"):
        _event(db, "PUSH", {"ref_class": ref_class, "value": "old"}, at="2030")
    _event(db, "PUSH", {"ref_class": "sandbox", "value": "new"}, at="2020")
    view = state.gate_view(db, "unit")
    assert view.sandbox_push == {"ref_class": "sandbox", "value": "new"}
    assert view.review_push == {"ref_class": "review", "value": "old"}


def _qb_result(db, request, status):
    state.append_qb_event(
        db, request_seq=request, event_type="RESULT", qb_build_id="123",
        status=status, accepted=True, sbs_target_echo="repo@sha",
        qb_result_sha256="f" * 64,
    )


def test_qb_two_level_latest_does_not_fall_back_to_old_request(db):
    old = state.create_qb_request(db, "unit", request_id="old", sbs_target="repo@sha")
    state.append_qb_event(db, request_seq=old, event_type="BUILD_BOUND", qb_build_id="123")
    _qb_result(db, old, "Successful")
    assert state.gate_view(db, "unit").qb_result == state.latest_qb_result(db, "unit")
    new = state.create_qb_request(db, "unit", request_id="new", sbs_target="repo@sha")
    assert state.gate_view(db, "unit").qb_result is None
    state.append_qb_event(db, request_seq=new, event_type="BUILD_BOUND", qb_build_id="123")
    _qb_result(db, new, "Failed")
    _qb_result(db, new, "Successful")
    _qb_result(db, old, "Obsolete")
    view = state.gate_view(db, "unit")
    assert view.qb_result["request_seq"] == new
    assert view.qb_result["status"] == "Successful"
    assert view.qb_result == state.latest_qb_result(db, "unit")


@pytest.mark.parametrize("field", [
    "message_brief", "author_identity", "committer_identity", "author_date", "committer_date",
])
def test_gate_view_detects_each_immutable_derive_field_across_all_rows(db, field):
    first = _derive()
    _event(db, "DERIVE", first)
    _event(db, "DERIVE", dict(first, **{field: "changed"}))
    _event(db, "DERIVE", first)
    with pytest.raises(state.StateInconsistent, match="identity fields changed"):
        state.gate_view(db, "unit")


def test_derive_write_side_rejects_committer_change(db):
    first = _derive()
    state.append_event(db, "unit", "DERIVE", first)
    with pytest.raises(state.StateInconsistent, match="identity fields changed"):
        state.append_event(db, "unit", "DERIVE", dict(first, committer_identity="Other <o@x>"))
    assert state.gate_view(db, "unit").derive == first


def test_gate_view_uses_one_snapshot_across_queries(db, monkeypatch):
    _event(db, "POLICY", {"value": "before"})
    real_query = state._gate_rows_on_connection
    calls = []

    def concurrent_write(conn, unit):
        assert conn.in_transaction
        calls.append(unit)
        _event(db, "POLICY", {"value": "after"})
        request = state.create_qb_request(db, "unit", request_id="new", sbs_target="repo@sha")
        state.append_qb_event(db, request_seq=request, event_type="BUILD_BOUND", qb_build_id="123")
        _qb_result(db, request, "Successful")
        return real_query(conn, unit)

    def no_public_read(*args, **kwargs):
        pytest.fail("gate_view opened another connection through a public read")

    monkeypatch.setattr(state, "_gate_rows_on_connection", concurrent_write)
    monkeypatch.setattr(state, "latest_event", no_public_read)
    monkeypatch.setattr(state, "latest_qb_result", no_public_read)
    view = state.gate_view(db, "unit")
    assert calls == ["unit"]
    assert view.policy == {"value": "before"}
    assert view.qb_result is None
    monkeypatch.setattr(state, "_gate_rows_on_connection", real_query)
    later = state.gate_view(db, "unit")
    assert later.policy == {"value": "after"}
    assert later.qb_result["status"] == "Successful"


def test_empty_unit_and_missing_unit(db):
    assert asdict(state.gate_view(db, "unit")) == {
        "reproduced": False, "reproduce_by_arch": {}, "policy": None, "derive": None,
        "sandbox_push": None, "review_push": None, "kb": None, "review": None, "qb_result": None,
    }
    with pytest.raises(state.StateInconsistent):
        state.gate_view(db, "missing")


def test_latest_policy_is_round_specific_and_read_only(db):
    _event(db, "POLICY", {"round_index": 1, "value": "old"}, at="2030")
    _event(db, "POLICY", {"round_index": 1, "value": "new"}, at="2020")
    _event(db, "POLICY", {"round_index": 2, "value": "other"})
    before = db.path.read_bytes()
    assert state.latest_policy_for_round(db, "unit", 1) == {"round_index": 1, "value": "new"}
    assert state.latest_policy_for_round(db, "unit", 2) == {"round_index": 2, "value": "other"}
    assert state.latest_policy_for_round(db, "unit", 3) is None
    assert db.path.read_bytes() == before


def test_lookup_change_id_hit_and_miss_never_generate_or_write(db, monkeypatch):
    key = "a" * 64
    value = state.get_or_create_change_id(
        db, campaign_unit_key="unit", submission_key=key, hook_sha256="b" * 64,
        generate=lambda: "I" + "c" * 40,
    )
    before = db.path.read_bytes()
    monkeypatch.setattr(state, "get_or_create_change_id", lambda *a, **k: pytest.fail("write"))
    assert state.lookup_change_id(db, key) == value
    assert state.lookup_change_id(db, "d" * 64) is None
    assert db.path.read_bytes() == before
