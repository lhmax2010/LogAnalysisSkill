from __future__ import annotations

import io
import json
from dataclasses import replace
from pathlib import Path

import pytest
from test_campaign_state import EDIT_SHA, UNIT_KEY, _create_round, _create_unit, _record
from tizen_campaign_core import campaign_lifecycle as life
from tizen_campaign_core import campaign_state as state
from tizen_campaign_core._campaign_io import lock
from tizen_campaign_core._campaign_workspace import _unit_hash
from tizen_campaign_report import report as commands
from tizen_ci_shared.state import StateDatabase, write_pass_record
from tizen_ci_shared.workspace import PROTECTED_FILENAME


@pytest.fixture
def copies(tmp_path):
    db = StateDatabase(tmp_path / "state.db")
    _create_unit(db)
    _create_round(db)
    paths = [tmp_path / name for name in ("linked", "orphan", "other")]
    for path in paths:
        path.mkdir()
        (path / PROTECTED_FILENAME).write_text("{}")
    record = replace(_record("v1"), worktree_path=str(paths[0]))
    write_pass_record(db, record)
    conn = db.connect()
    with conn:
        conn.execute(
            "INSERT INTO campaign_verifications (campaign_unit_key,arch_raw,arch_norm,"
            "verification_id,round_index,edit_spec_sha256,campaign_schema_version,created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                UNIT_KEY,
                "standard-aarch64",
                "aarch64",
                "v1",
                1,
                EDIT_SHA,
                state.CAMPAIGN_SCHEMA_VERSION,
                "now",
            ),
        )
    conn.close()
    state.append_event(
        db,
        UNIT_KEY,
        "ORPHAN_PASS",
        dict(
            round_index=1,
            arch_norm="armv7l",
            verification_id="v2",
            worktree_path=str(paths[1]),
            reason="link_failed",
            detected_at="now",
        ),
    )
    state.append_status(db, UNIT_KEY, "QB_TRIGGERED")
    return db, paths, dict(campaign_workspace=str(tmp_path / "ws"))


@pytest.mark.parametrize("status", sorted(life.RELEASE_TERMINAL))
def test_finish_terminal_releases_both_sources_idempotently(copies, status):
    db, paths, _ = copies
    state.append_status(db, UNIT_KEY, status)
    assert commands.finish(db, UNIT_KEY) == (
        0,
        dict(released=sorted(map(str, paths[:2])), error_code=None),
    )
    assert all(p.is_dir() and not (p / PROTECTED_FILENAME).exists() for p in paths[:2])
    assert (paths[2] / PROTECTED_FILENAME).exists()
    assert commands.finish(db, UNIT_KEY)[1]["released"] == []
    assert len(life.release_events(db, UNIT_KEY)) == 1


@pytest.mark.parametrize("status", sorted(life.EMPTY_TERMINAL))
def test_finish_empty_terminal_does_not_call_release(copies, status, monkeypatch):
    db, _, _ = copies
    state.append_status(db, UNIT_KEY, status)
    monkeypatch.setattr(
        life, "release_terminal_worktrees", lambda *a: pytest.fail("must not release")
    )
    assert commands.finish(db, UNIT_KEY) == (0, dict(released=[], error_code=None))


@pytest.mark.parametrize("status", sorted(life.RETAINED))
def test_finish_retained_and_explicit_release(copies, status):
    db, paths, settings = copies
    state.append_status(
        db,
        UNIT_KEY,
        status,
        reason="aggregate_mismatch" if status == "HELD_FOR_INVESTIGATION" else None,
    )
    assert commands.finish(db, UNIT_KEY)[1]["retained"] is True
    assert len(commands.release(db, UNIT_KEY, settings, "Operator", False)) == 2
    assert life.release_events(db, UNIT_KEY)[-1]["confirmed_by"] == "Operator"
    assert commands.release(db, UNIT_KEY, settings, "Operator", False) == []
    assert paths[0].is_dir()


@pytest.mark.parametrize("status", ["QB_TRIGGERED", "LOCAL_3ARCH_PASS", "BASELINE_REPRODUCED"])
def test_nonterminal_finish_and_manual_release_rejected(copies, status):
    db, _, settings = copies
    state.append_status(db, UNIT_KEY, status)
    assert commands.finish(db, UNIT_KEY)[0] == 4
    with pytest.raises(life.ReleaseNotAllowed):
        commands.release(db, UNIT_KEY, settings, "Operator", False)
    with pytest.raises(life.ReleaseNotAllowed):
        life.release_terminal_worktrees(db, UNIT_KEY)


@pytest.mark.parametrize("status", sorted(life.TERMINAL))
def test_abandon_terminal_without_barrier_rejected(copies, status):
    db, _, settings = copies
    state.append_status(
        db,
        UNIT_KEY,
        status,
        reason="aggregate_mismatch" if status == "HELD_FOR_INVESTIGATION" else None,
    )
    with pytest.raises(life.ReleaseNotAllowed):
        commands.release(db, UNIT_KEY, settings, "Operator", True)
    assert not life.release_events(db, UNIT_KEY)


def test_abandon_enumerates_and_report_wins_over_later_pass(copies):
    db, paths, settings = copies
    assert commands.release(db, UNIT_KEY, settings, "Operator", True) == sorted(map(str, paths[:2]))
    assert life.release_events(db, UNIT_KEY)[0] == dict(
        paths=[], reason="abandoned", confirmed_by="Operator"
    )
    assert state.latest_status(db, UNIT_KEY) == "QB_TRIGGERED"
    state.append_status(db, UNIT_KEY, "SANDBOX_QB_PASS")
    assert commands.report(db)[0]["workspace_status"] == "已放弃"
    assert commands.report(db)[0]["status"] == "SANDBOX_QB_PASS"
    assert commands.release(db, UNIT_KEY, settings, "Operator", True) == []
    assert (paths[2] / PROTECTED_FILENAME).exists()


@pytest.mark.parametrize("point", ["barrier", "last_marker"])
def test_abandon_crash_reconciliation(copies, monkeypatch, point):
    db, paths, settings = copies
    if point == "barrier":
        original = life.release_abandoned_worktrees

        def crash(*a, **kw):
            raise RuntimeError("crash")

        monkeypatch.setattr(life, "release_abandoned_worktrees", crash)
    else:
        original = state.append_event

        def crash(*a, **kw):
            if a[3]["reason"] == "abandoned_release":
                raise RuntimeError("crash")
            return original(*a, **kw)

        monkeypatch.setattr(state, "append_event", crash)
    with pytest.raises(RuntimeError, match="crash"):
        commands.release(db, UNIT_KEY, settings, "Operator", True)
    assert life.is_abandoned(db, UNIT_KEY)
    if point == "barrier":
        monkeypatch.setattr(life, "release_abandoned_worktrees", original)
    else:
        monkeypatch.setattr(state, "append_event", original)
        assert all(not (p / PROTECTED_FILENAME).exists() for p in paths[:2])
    assert len(commands.release(db, UNIT_KEY, settings, "Operator", True)) == 2
    before = db.path.read_bytes()
    assert commands.release(db, UNIT_KEY, settings, "Operator", True) == []
    assert before == db.path.read_bytes()


def test_abandoned_release_is_not_barrier(copies):
    db, _, settings = copies
    state.append_event(
        db,
        UNIT_KEY,
        "WORKSPACE_RELEASE",
        dict(paths=[], reason="abandoned_release", confirmed_by="Operator"),
    )
    assert not life.is_abandoned(db, UNIT_KEY)
    commands.release(db, UNIT_KEY, settings, "Operator", True)
    assert sum(e["reason"] == "abandoned" for e in life.release_events(db, UNIT_KEY)) == 1


@pytest.mark.parametrize(
    "held_lock",
    [
        ".sandbox_submit.lock",
        "aarch64/.repair_step.lock",
        "armv7l/.repair_step.lock",
        "x86_64/.repair_step.lock",
    ],
)
def test_abandon_busy_has_no_barrier(copies, held_lock):
    db, _, settings = copies
    root = Path(settings["campaign_workspace"]) / _unit_hash(UNIT_KEY)
    with lock(root / held_lock):
        with pytest.raises(commands._Reject) as error:
            commands.release(db, UNIT_KEY, settings, "Operator", True)
        assert error.value.code == "CAMPAIGN_STATE_BUSY"
    assert not life.release_events(db, UNIT_KEY)


def test_terminal_release_reconciles_reappeared_marker(copies):
    db, paths, _ = copies
    state.append_status(db, UNIT_KEY, "STALLED")
    life.release_terminal_worktrees(db, UNIT_KEY)
    (paths[0] / PROTECTED_FILENAME).write_text("{}")
    assert life.release_terminal_worktrees(db, UNIT_KEY) == [str(paths[0])]
    assert len(life.release_events(db, UNIT_KEY)) == 2


def test_report_latest_request_latest_result_pure_database(copies, monkeypatch, tmp_path):
    db, _, _ = copies
    one = state.create_qb_request(db, UNIT_KEY, request_id="r1", sbs_target="repo@sha")
    state.append_qb_event(db, request_seq=one, event_type="BUILD_BOUND", qb_build_id="101")

    def result(seq, parent, ref):
        state.append_qb_event(
            db,
            request_seq=seq,
            event_type="RESULT",
            qb_build_id=parent,
            status="PASS",
            accepted=False,
            sbs_target_echo="repo@sha",
            qb_result_sha256="a" * 64,
            qb_result_ref=ref,
        )

    result(one, "101", "qb_results/r1/old.json")
    two = state.create_qb_request(db, UNIT_KEY, request_id="r2", sbs_target="repo@sha")
    row = commands.report(db)[0]
    assert row["qb_build_id"] is row["qb_result_ref"] is None
    state.append_qb_event(db, request_seq=two, event_type="BUILD_BOUND", qb_build_id="102")
    row = commands.report(db)[0]
    assert row["qb_build_id"] == "102" and row["qb_result_ref"] is None
    result(two, "102", "qb_results/r2/first.json")
    result(two, "102", "qb_results/r2/latest.json")
    before = db.path.read_bytes()
    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", lambda *a, **kw: pytest.fail("report opened a file"))
        rows = commands.report(db)
    assert (
        rows[0]["qb_build_id"] == "102" and rows[0]["qb_result_ref"] == "qb_results/r2/latest.json"
    )
    assert db.path.read_bytes() == before
    out, destination = io.StringIO(), tmp_path / "report.md"
    assert (
        commands.main(
            "campaign-report",
            ["--state-db", str(db.path), "--output", str(destination)],
            stdout=out,
        )
        == 0
    )
    assert json.loads(out.getvalue()) == rows
    assert destination.read_text() == commands.markdown(rows)
    assert before == db.path.read_bytes()


@pytest.mark.parametrize("who", ["", "   "])
def test_empty_confirmation_rejected(copies, who):
    db, _, settings = copies
    with pytest.raises(life.ReleaseNotAllowed):
        commands.release(db, UNIT_KEY, settings, who, True)
    assert not life.release_events(db, UNIT_KEY)


@pytest.mark.parametrize("mode", ["terminal", "held"])
def test_release_crash_reconciliation_and_failed_correction(copies, monkeypatch, mode):
    db, paths, _ = copies
    state.append_status(db, UNIT_KEY, "STALLED" if mode == "terminal" else "WORKTREE_LOST")

    def release():
        if mode == "terminal":
            return life.release_terminal_worktrees(db, UNIT_KEY)
        return life.release_held_worktrees(db, UNIT_KEY, confirmed_by="Operator")

    with monkeypatch.context() as patch:

        def crash(*a, **kw):
            raise RuntimeError("injected crash")

        patch.setattr(state, "append_event", crash)
        with pytest.raises(RuntimeError):
            release()
    assert not any((p / PROTECTED_FILENAME).exists() for p in paths[:2])
    assert release() == sorted(map(str, paths[:2]))
    assert release() == []
    (paths[0] / PROTECTED_FILENAME).write_text("{}")
    with monkeypatch.context() as patch:

        def refuse(*a):
            raise OSError("denied")

        patch.setattr(life, "release_worktree_protection", refuse)
        with pytest.raises(state.StateInconsistent):
            release()
    assert len(life.release_events(db, UNIT_KEY)) == 1
    assert release() == [str(paths[0])]


def test_abandon_accounts_missing_copy_and_new_copy_after_pass(copies, tmp_path):
    db, paths, settings = copies
    (paths[0] / PROTECTED_FILENAME).unlink()
    paths[0].rmdir()
    assert commands.release(db, UNIT_KEY, settings, "Operator", True) == sorted(map(str, paths[:2]))
    state.append_status(db, UNIT_KEY, "SANDBOX_QB_PASS")
    added = tmp_path / "late-orphan"
    added.mkdir()
    (added / PROTECTED_FILENAME).write_text("{}")
    state.append_event(
        db,
        UNIT_KEY,
        "ORPHAN_PASS",
        dict(
            round_index=1,
            arch_norm="x86_64",
            verification_id="late",
            worktree_path=str(added),
            reason="link_failed",
            detected_at="now",
        ),
    )
    assert commands.release(db, UNIT_KEY, settings, "Operator", True) == [str(added)]
    assert not (added / PROTECTED_FILENAME).exists()
    assert (paths[2] / PROTECTED_FILENAME).exists()
    assert sum(e["reason"] == "abandoned" for e in life.release_events(db, UNIT_KEY)) == 1
