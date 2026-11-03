from __future__ import annotations

import io
import json
import multiprocessing
from dataclasses import replace

import pytest
from ci_triage import cli
from test_campaign_repair_step import ARCH_NORM, UNIT_KEY, _fixture, _pass_builder
from tizen_campaign_core import campaign_state as state
from tizen_campaign_repair import __main__ as entry
from tizen_campaign_repair import campaign_repair_step as repair


@pytest.fixture
def first(tmp_path):
    f = _fixture(tmp_path)
    primary = state.latest_reproduce(f.db, UNIT_KEY, arch_norm=ARCH_NORM)["payload"]
    for arch in state.ARCH_NORMS - {ARCH_NORM}:
        state.append_event(f.db, UNIT_KEY, "REPRODUCE", dict(primary, arch_norm=arch))
    state.append_status(f.db, UNIT_KEY, "BASELINE_REPRODUCED")
    return f


def status_count(f):
    conn = state._read_connection(f.db)
    try:
        return conn.execute(
            "SELECT count(*) FROM campaign_status_log WHERE status='REPAIR_ROUND_RUNNING'"
        ).fetchone()[0]
    finally:
        conn.close()


def test_complete_baseline_enters_first_round(first):
    before = status_count(first)
    result = repair.campaign_repair_step(first.options, build_verify_fn=_pass_builder(first))
    assert result.exit_code == 0 and result.result.result == "PASS"
    assert status_count(first) == before + 1
    assert state.latest_status(first.db, UNIT_KEY) == "REPAIR_ROUND_RUNNING"
    assert state.invocations_used(first.db, UNIT_KEY) == 1


@pytest.mark.parametrize(
    "fault",
    ["missing_arch", "primary_not_matched", "round_two", "existing_round", "held", "terminal"],
)
def test_first_round_preconditions_leave_database_unchanged(first, fault):
    options = first.options
    if fault == "missing_arch":
        conn = first.db.connect()
        with conn:
            conn.execute(
                "DELETE FROM campaign_gate_events "
                "WHERE event_type='REPRODUCE' AND arch_norm='x86_64'"
            )
        conn.close()
    elif fault == "primary_not_matched":
        old = state.latest_reproduce(first.db, UNIT_KEY, arch_norm=ARCH_NORM)["payload"]
        state.append_event(first.db, UNIT_KEY, "REPRODUCE", dict(old, outcome="different_failure"))
    elif fault == "round_two":
        options = replace(options, round_index=2)
    elif fault == "existing_round":
        state.create_round(
            first.db, UNIT_KEY, round_index=1, edit_spec_ref="existing", edit_spec_sha256="a" * 64
        )
    else:
        state.append_status(
            first.db,
            UNIT_KEY,
            "HELD_FOR_INVESTIGATION" if fault == "held" else "STALLED",
            "state_inconsistent" if fault == "held" else "stalled",
            ARCH_NORM if fault == "held" else None,
        )
    before = first.db.path.read_bytes()
    outcome = repair.campaign_repair_step(
        options, build_verify_fn=lambda _: pytest.fail("must not build")
    )
    assert outcome.exit_code == 4 and outcome.result.error_code == "REJECTED_STATE_INCONSISTENT"
    assert first.db.path.read_bytes() == before
    assert state.invocations_used(first.db, UNIT_KEY) == 0
    assert (state.latest_round(first.db, UNIT_KEY) is not None) == (fault == "existing_round")


def test_crash_after_transition_before_create_round_resumes(first, monkeypatch):
    class Crash(BaseException):
        pass

    original = repair.create_round

    def fail(*a, **k):
        raise Crash()

    monkeypatch.setattr(repair, "create_round", fail)
    with pytest.raises(Crash):
        repair.campaign_repair_step(first.options)
    assert state.latest_status(first.db, UNIT_KEY) == "REPAIR_ROUND_RUNNING"
    assert state.latest_round(first.db, UNIT_KEY) is None
    assert state.invocations_used(first.db, UNIT_KEY) == 0
    count = status_count(first)
    monkeypatch.setattr(repair, "create_round", original)
    result = repair.campaign_repair_step(first.options, build_verify_fn=_pass_builder(first))
    assert result.exit_code == 0 and status_count(first) == count


def test_two_processes_first_round_lock_advances_once(first):
    ctx = multiprocessing.get_context("fork")
    reached, release = ctx.Event(), ctx.Event()
    queue = ctx.Queue()
    before = status_count(first)

    def worker():
        original = repair.create_round

        def pause(*a, **kw):
            reached.set()
            assert release.wait(15)
            return original(*a, **kw)

        repair.create_round = pause
        result = repair.campaign_repair_step(first.options, build_verify_fn=_pass_builder(first))
        queue.put((result.exit_code, result.result.error_code))

    process = ctx.Process(target=worker)
    process.start()
    try:
        assert reached.wait(15)
        second = repair.campaign_repair_step(first.options)
        assert second.result.error_code == "CAMPAIGN_STATE_BUSY"
    finally:
        release.set()
        process.join(20)
        if process.is_alive():
            process.terminate()
            process.join()
    assert process.exitcode == 0 and queue.get(timeout=2) == (0, None)
    assert status_count(first) == before + 1


@pytest.mark.parametrize("args", [[], ["check"], ["wrong"], ["check", "--source-kind", "unknown"]])
def test_suppress_policy_shared_parser_invalid(args):
    old, new = io.StringIO(), io.StringIO()
    assert cli._main_suppress_policy is entry._main_suppress_policy
    a = cli.main(["suppress-policy", *args], stdout=old, stderr=io.StringIO())
    b = entry._main_suppress_policy(args, stdout=new, stderr=io.StringIO())
    assert a == b == 2 and json.loads(old.getvalue()) == json.loads(new.getvalue())
