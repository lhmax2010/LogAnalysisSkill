from __future__ import annotations

import hashlib
import io
import json
from dataclasses import replace

import pytest
import yaml
from test_campaign_fake_ssh import transport as transport
from test_sandbox_submit import Campaign, git
from tizen_campaign_core import campaign_state as state
from tizen_campaign_report import report
from tizen_review_submit import review_submit as review
from tizen_sandbox_submit import sandbox_submit as sandbox


@pytest.fixture
def case(tmp_path, monkeypatch, transport):
    c = Campaign(tmp_path / "case", monkeypatch)
    monkeypatch.setenv("SKEL_FAKE_SSH_ROOT", str(c.remote_base))
    settings = yaml.safe_load(c.config.read_text())
    settings["gerrit_ssh_base"] = "ssh://gerrit.invalid:29418"
    c.config.write_text(yaml.safe_dump(settings))
    git(c.src, "remote", "set-url", "origin", "ssh://gerrit.invalid:29418/project")
    outcome = sandbox.sandbox_submit(c.options)
    assert outcome.exit_code == 0, outcome.payload
    c.derived = outcome.payload["derived_commit_sha"]
    for arch in sandbox.ARCH_ORDER:
        state.append_event(
            c.db,
            c.key,
            "REPRODUCE",
            dict(
                arch_norm=arch,
                outcome="matched",
                evidence_local=f"{arch}.json",
                evidence_sha256="e" * 64,
                synthetic_zero_error=False,
                gbs_conf_sha256="f" * 64,
                ci_evidence_sha256_used="e" * 64,
                build_log="local.log",
                basis={},
            ),
        )
    conn = c.db.connect()
    try:
        with conn:
            state._insert_qb_profile_on_connection(
                conn, "tizen", profile_json='{"qb_pass_requires_accept":false}'
            )
    finally:
        conn.close()
    c.seq = state.create_qb_request(
        c.db, c.key, request_id="request-one", sbs_target="project@" + c.derived
    )
    state.append_qb_event(c.db, request_seq=c.seq, event_type="BUILD_BOUND", qb_build_id="101")
    c.result = {key: "" for key in review.RESULT_KEYS}
    c.result.update(
        qb_build_id="101",
        child_build_id="102",
        status="PASS",
        sbs_target_echo="project@" + c.derived,
        accepted=None,
        per_arch_status=None,
        child_failed_step=None,
        child_error_message=None,
        request_marker_echo="clang-fix-campaign request=request-one",
        snapshot_drift_accepted=False,
        snapshot_used="snapshot",
        params_echo={
            k: ""
            for k in (
                "BUILD_TYPE",
                "BUILD_REFERENCE",
                "SNAPSHOT_NUM",
                "PROJECT_BRANCH",
                "FAIL_FAST",
            )
        },
        child_params_echo=dict(BUILD_REFERENCE="Ref. Snapshot", SNAPSHOT_NUM_URL="test"),
        pkg_list_echo={},
        evidence=[],
        fetched_at="2026-11-03T00:00:00Z",
    )
    c.result_path = c.root / "result.json"
    publish_result(c)
    state.append_status(c.db, c.key, "SANDBOX_QB_PASS")
    c.review_options = review.ReviewOptions(
        "v0,v1,v2", c.db.path, c.config, c.result_path, "refs/for/tizen"
    )
    c.before_refs = git(c.remote, "show-ref")
    c.before_ids = [tuple(r) for r in c.sql("SELECT * FROM campaign_change_ids")]
    return c


def publish_result(c):
    c.result_path.write_text(json.dumps(c.result))
    state.append_qb_event(
        c.db,
        request_seq=c.seq,
        event_type="RESULT",
        qb_build_id=c.result["qb_build_id"],
        status=c.result["status"],
        sbs_target_echo="project@" + c.derived,
        accepted=c.result["accepted"],
        per_arch_status_json=json.dumps(c.result["per_arch_status"])
        if c.result["per_arch_status"] is not None
        else None,
        qb_result_sha256=hashlib.sha256(c.result_path.read_bytes()).hexdigest(),
        qb_result_ref="qb_results/request-one/result.json",
    )


def rejected(c, outcome, code):
    assert outcome.exit_code == 4 and outcome.payload["error_code"] == code, outcome.payload
    assert git(c.remote, "show-ref") == c.before_refs
    assert not c.sql("SELECT 1 FROM campaign_gate_events WHERE event_type='REVIEW'")


def test_success_cached_change_id_and_retry(case):
    gate = review.validate_qb_gate(case.db, case.key, case.result_path)
    assert gate.ok and gate.source == "first_party" and not gate.degraded
    result = review.run(case.review_options)
    assert result.exit_code == 0, result.payload
    assert git(case.remote, "rev-parse", "refs/for/tizen") == case.derived
    assert result.payload["review_url"] is None
    assert [tuple(r) for r in case.sql("SELECT * FROM campaign_change_ids")] == case.before_ids
    before = case.db.path.read_bytes()
    assert review.run(case.review_options).payload["action"] == "already_pushed"
    assert case.db.path.read_bytes() == before
    assert "no_change_url_in_push_output" in (case.unit_root / "review-trace.jsonl").read_text()


@pytest.mark.parametrize("new_request", [False, True])
def test_two_level_latest_result_supersedes_old_file(case, new_request):
    old = case.result_path.read_bytes()
    if new_request:
        case.seq = state.create_qb_request(
            case.db, case.key, request_id="request-two", sbs_target="project@" + case.derived
        )
        case.result["request_marker_echo"] = "clang-fix-campaign request=request-two"
        case.result["qb_build_id"] = "201"
        state.append_qb_event(
            case.db, request_seq=case.seq, event_type="BUILD_BOUND", qb_build_id="201"
        )
    case.result["fetched_at"] = "2026-11-03T01:00:00Z"
    publish_result(case)
    case.result_path.write_bytes(old)
    rejected(case, review.run(case.review_options), "REJECTED_QB_SUPERSEDED")


@pytest.mark.parametrize("gate", ["aggregate", "qb_bytes", "edit_bytes", "policy", "a2", "toctou"])
def test_six_revalidation_refusals(case, monkeypatch, gate):
    code = "REJECTED_STATE_INCONSISTENT"
    if gate == "aggregate":
        state.create_round(
            case.db, case.key, round_index=2, edit_spec_ref="next", edit_spec_sha256="9" * 64
        )
        case.sql(
            "UPDATE campaign_verifications SET round_index=2 WHERE verification_id='v0'",
            foreign_keys=False,
        )
        code = "REJECTED_ARCH_AGGREGATE_MISMATCH"
    elif gate == "qb_bytes":
        case.result_path.write_text(case.result_path.read_text() + " ")
        code = "REJECTED_QB_BINDING_MISMATCH"
    elif gate == "edit_bytes":
        case.spec.write_text(case.spec.read_text() + " ")
        code = "REJECTED_EDIT_SPEC_REBIND_MISMATCH"
    elif gate == "policy":
        policy = dict(state.latest_policy_for_round(case.db, case.key, 1))
        policy["fix_strategy_final"] = "suppress"
        state.append_event(case.db, case.key, "POLICY", policy)
    elif gate == "a2":
        case.sql("DELETE FROM campaign_gate_events WHERE event_type='REPRODUCE'")
        code = "REJECTED_REVIEW_GATE"
    else:
        original = sandbox.toctou_recheck

        def tamper(*a, **k):
            (case.copies[0] / "file.c").write_text("tampered\n")
            return original(*a, **k)

        monkeypatch.setattr(sandbox, "toctou_recheck", tamper)
        code = "REJECTED_WORKTREE_DIRTY"
    rejected(case, review.run(case.review_options), code)


def test_pending_exact_request_message_no_manual_fallback(case):
    state.create_qb_request(
        case.db, case.key, request_id="latest-request", sbs_target="project@" + case.derived
    )
    outcome = review.run(case.review_options)
    rejected(case, outcome, "REJECTED_QB_REQUEST_PENDING")
    assert outcome.payload["message"] == (
        "该 unit 最新的验证请求(request_id=latest-request)还没有结果。"
        "若 qb-result-fetch 曾报告结果无法识别"
        "(QB_RESULT_UNRECOGNIZED,例如各架构状态非空或快照漂移;"
        "可在运行 qb-result-fetch 时所用的 state_root "
        "下查看该 request 的 trace 确认),重读不会改变结果,请按其输出的指引处置,或用 "
        "campaign-release-worktrees --abandon 放弃该 unit;否则稍后重跑 qb-result-fetch。"
    )
    gate = review.validate_qb_gate(case.db, case.key, case.result_path, allow_manual=True)
    assert not gate.ok and not gate.degraded and gate.source == "first_party"


@pytest.mark.parametrize("at", ["after_barrier", "during_push"])
def test_abandon_cannot_interleave_with_review(case, monkeypatch, at):
    seen = []

    def abandon():
        with pytest.raises(sandbox._Reject) as error:
            report.release(case.db, case.key, {"campaign_workspace": str(case.ws)}, "Tester", True)
        seen.append(error.value.code)

    if at == "after_barrier":
        original = review.is_abandoned

        def wrapped(*a):
            result = original(*a)
            abandon()
            return result

        monkeypatch.setattr(review, "is_abandoned", wrapped)
    else:
        original_push = review._push

        def wrapped_push(*a):
            abandon()
            return original_push(*a)

        monkeypatch.setattr(review, "_push", wrapped_push)
    assert review.run(case.review_options).exit_code == 0
    assert seen == ["CAMPAIGN_STATE_BUSY"]
    assert (
        not review.is_abandoned(case.db, case.key)
        if at != "after_barrier"
        else not original(case.db, case.key)
    )


def test_abandon_lock_blocks_review(case):
    with sandbox._locks(case.unit_root):
        rejected(case, review.run(case.review_options), "CAMPAIGN_STATE_BUSY")


@pytest.mark.parametrize(
    "fault",
    [
        "missing_file",
        "extra_key",
        "missing_key",
        "wrong_type",
        "wrong_marker",
        "wrong_target",
        "fail_status",
        "arch_fail",
        "accept_required",
        "missing_cache",
        "wrong_branch",
    ],
)
def test_gate_and_identity_hard_failures(case, fault):
    code = "REJECTED_QB_BINDING_MISMATCH"
    if fault == "missing_file":
        case.result_path.unlink()
    elif fault == "missing_cache":
        case.sql("DELETE FROM campaign_change_ids")
        code = "REJECTED_STATE_INCONSISTENT"
    elif fault == "wrong_branch":
        case.review_options = replace(case.review_options, review_target="refs/for/other")
        code = "REJECTED_REVIEW_TARGET_MISMATCH"
    elif fault == "accept_required":
        text = '{"qb_pass_requires_accept":true}'
        case.sql(
            "UPDATE campaign_qb_profiles SET profile_json=?,profile_sha256=?",
            (text, hashlib.sha256(text.encode()).hexdigest()),
        )
        code = "REJECTED_QB_NOT_VERIFIED"
    else:
        if fault == "extra_key":
            case.result["extra"] = "bad"
        elif fault == "missing_key":
            del case.result["snapshot_used"]
        elif fault == "wrong_type":
            case.result["snapshot_used"] = 17
        elif fault == "wrong_marker":
            case.result["request_marker_echo"] = "another request"
        elif fault == "wrong_target":
            case.result["sbs_target_echo"] = "other@" + case.derived
        elif fault == "fail_status":
            case.result["status"] = "FAIL"
            code = "REJECTED_QB_NOT_VERIFIED"
        else:
            case.result["per_arch_status"] = dict(aarch64="PASS", armv7l="FAIL", x86_64="PASS")
            code = "REJECTED_QB_NOT_VERIFIED"
        publish_result(case)
    rejected(case, review.run(case.review_options), code)


def test_push_failure_has_no_review(case, monkeypatch):
    def fail(*a, **k):
        raise sandbox._TransportFailure("offline failure")

    monkeypatch.setattr(sandbox, "_transport", fail)
    result = review.run(case.review_options)
    assert result.exit_code == 5 and result.payload["error_code"] == "PUSH_FAILED"
    assert state.latest_status(case.db, case.key) == "REVIEW_PUSH_FAILED"
    assert git(case.remote, "show-ref") == case.before_refs
    assert not case.sql("SELECT 1 FROM campaign_gate_events WHERE event_type='REVIEW'")


def test_cli_invalid_arguments_no_manual_option():
    output = io.StringIO()
    assert review.main(["--print-manual-command"], stdout=output) == 2
    assert json.loads(output.getvalue())["error_code"] == "INVALID_ARGS"
