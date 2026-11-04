from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

import pytest
from test_campaign_batch3_review import case as case
from test_campaign_batch3_review import rejected
from test_campaign_batch3_review import transport as transport
from test_sandbox_submit import git
from tizen_campaign_core import campaign_state as state
from tizen_campaign_core.suppress_policy import evaluate
from tizen_review_submit import review_submit as review


def record_policy(c, source="t1_cherry_pick"):
    verdict = evaluate(json.loads(c.spec.read_text()), c.src, source)
    policy = dict(state.latest_policy_for_round(c.db, c.key, 1))
    policy.update(
        edit_source_kind=source,
        fix_strategy_initial="cherry_pick" if source == "t1_cherry_pick" else "code",
        fix_strategy_final=verdict.fix_strategy_final,
        verdict=verdict.verdict,
        hits=[asdict(hit) for hit in verdict.hits],
    )
    state.append_event(c.db, c.key, "POLICY", policy)
    return verdict


def bind_policy_rejection_edit(c, new):
    # Rebind the synthetic evidence hashes to reach the real policy gate, not the
    # earlier edit-byte gate. These rejection cases must never reach publication.
    edit = json.loads(c.spec.read_text())
    edit["edits"][0]["new"] = new
    c.spec.write_text(json.dumps(edit))
    digest = hashlib.sha256(c.spec.read_bytes()).hexdigest()
    conn = c.db.connect()
    try:
        with conn:
            conn.execute("BEGIN")
            conn.execute("PRAGMA defer_foreign_keys=ON")
            for table in ("campaign_rounds", "campaign_verifications", "verification_records"):
                conn.execute(f"UPDATE {table} SET edit_spec_sha256=?", (digest,))
    finally:
        conn.close()


def assert_rejected(c, code):
    c.calls.clear()
    rejected(c, review.run(c.review_options), code)
    assert c.pushes() == []


def test_non_suppressing_t1_qb_pass_reproduced_pushes(case):
    verdict = record_policy(case)
    assert (verdict.verdict, verdict.fix_strategy_final) == ("allowed", "cherry_pick")
    assert state.gate_view(case.db, case.key).reproduced
    assert review.validate_qb_gate(case.db, case.key, case.result_path).ok
    case.calls.clear()
    outcome = review.run(case.review_options)
    assert outcome.exit_code == 0, outcome.payload
    assert git(case.remote, "rev-parse", "refs/for/tizen") == case.derived
    assert len(case.pushes()) == 1
    assert len(case.sql("SELECT 1 FROM campaign_gate_events WHERE event_type='REVIEW'")) == 1
    assert state.latest_status(case.db, case.key) == "REVIEW_PUSHED"


def test_t1_suppressing_content_fails_a2(case):
    bind_policy_rejection_edit(
        case, '#pragma GCC diagnostic ignored "-Wunused-variable"\nint value = 2;'
    )
    verdict = record_policy(case)
    assert (verdict.verdict, verdict.fix_strategy_final) == ("allowed", "suppress")
    assert_rejected(case, "REJECTED_REVIEW_GATE")


def test_t1_forbidden_content_still_rejected(case):
    bind_policy_rejection_edit(
        case, '#pragma GCC diagnostic ignored "-Weverything"\nint value = 2;'
    )
    verdict = record_policy(case)
    assert verdict.verdict == "forbidden" and verdict.fix_strategy_final is None
    assert_rejected(case, "REJECTED_SUPPRESS_POLICY")


def test_t1_without_reproduction_still_rejected(case):
    record_policy(case)
    case.sql("DELETE FROM campaign_gate_events WHERE event_type='REPRODUCE'")
    assert not state.gate_view(case.db, case.key).reproduced
    assert_rejected(case, "REJECTED_REVIEW_GATE")


def test_unknown_source_still_state_inconsistent(case):
    record_policy(case)
    policy = dict(state.latest_policy_for_round(case.db, case.key, 1))
    policy["edit_source_kind"] = "unknown"
    # The public event API rejects this source; simulate a corrupt stored event.
    case.sql(
        "UPDATE campaign_gate_events SET payload_json=? WHERE event_id="
        "(SELECT MAX(event_id) FROM campaign_gate_events WHERE event_type='POLICY')",
        (json.dumps(policy),),
    )
    assert_rejected(case, "REJECTED_STATE_INCONSISTENT")


@pytest.mark.parametrize(
    ("source", "recomputed", "stored"),
    [("generated", "code", "cherry_pick"), ("t1_cherry_pick", "cherry_pick", "code")],
)
def test_stored_and_recomputed_strategy_mismatch_still_rejected(case, source, recomputed, stored):
    assert record_policy(case, source).fix_strategy_final == recomputed
    policy = dict(state.latest_policy_for_round(case.db, case.key, 1))
    policy["fix_strategy_final"] = stored
    state.append_event(case.db, case.key, "POLICY", policy)
    assert_rejected(case, "REJECTED_STATE_INCONSISTENT")
