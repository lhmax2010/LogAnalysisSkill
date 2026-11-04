from __future__ import annotations

import hashlib
import json
import multiprocessing
from pathlib import Path

import pytest
import yaml
from test_campaign_fake_ssh import transport as transport
from test_sandbox_submit import Campaign, git
from tizen_campaign_core import campaign_state as state
from tizen_campaign_core import kb
from tizen_campaign_core._campaign_io import analyze
from tizen_campaign_kb import sync
from tizen_campaign_report import report
from tizen_ci_shared.state import StateDatabase
from tizen_sandbox_submit import sandbox_submit as sandbox


@pytest.fixture(scope="module")
def ci_anchor(tmp_path_factory):
    return analyze(
        Path(__file__).parents[1] / "fixtures/e2e_clang_compile/buildlog",
        tmp_path_factory.mktemp("kb-sync-analyzer"),
    )


@pytest.fixture
def campaign(tmp_path, monkeypatch, transport, ci_anchor):
    c = Campaign(tmp_path / "case", monkeypatch)
    monkeypatch.setenv("SKEL_FAKE_SSH_ROOT", str(c.remote_base))
    c.settings = yaml.safe_load(c.config.read_text())
    c.settings.update(
        gerrit_ssh_base="ssh://gerrit.invalid:29418", kb_db=str(tmp_path / "kb/records.jsonl"),
    )
    c.config.write_text(yaml.safe_dump(c.settings))
    git(c.src, "remote", "set-url", "origin", "ssh://gerrit.invalid:29418/project")
    c.anchor = c.root / "ci-evidence.json"
    c.anchor.write_bytes(ci_anchor.read_bytes())
    c.sql(
        "UPDATE campaign_units SET ci_evidence_ref=?,ci_evidence_sha256=?",
        (str(c.anchor), hashlib.sha256(c.anchor.read_bytes()).hexdigest()),
    )
    c.kb_db = Path(c.settings["kb_db"])
    return c


def pushed(c, *, source="generated", precedent=None):
    if precedent is not None:
        spec = json.loads(c.spec.read_text())
        spec["kb_precedent_ref"] = precedent
        c.spec.write_text(json.dumps(spec))
        digest = hashlib.sha256(c.spec.read_bytes()).hexdigest()
        for table in ("campaign_rounds", "campaign_verifications", "verification_records"):
            c.sql(f"UPDATE {table} SET edit_spec_sha256=?", (digest,), foreign_keys=False)
    outcome = c.run(edit_source_kind=source)
    assert outcome.exit_code == 0, outcome.payload
    c.derived = outcome.payload["derived_commit_sha"]


def qb_result(c, status="PASS", *, new=True):
    if new:
        index = len(c.sql("SELECT * FROM campaign_qb_requests")) + 1
        c.seq = state.create_qb_request(
            c.db, c.key, request_id=f"request-{index}", sbs_target="project@" + c.derived,
        )
        state.append_qb_event(c.db, request_seq=c.seq, event_type="BUILD_BOUND", qb_build_id="101")
    if status is not None:
        state.append_qb_event(
            c.db, request_seq=c.seq, event_type="RESULT", status=status, qb_build_id="101",
            sbs_target_echo="project@" + c.derived, qb_result_sha256="a" * 64,
            qb_result_ref="qb_results/result.json",
        )


def audits(c):
    return c.sql("SELECT * FROM campaign_gate_events WHERE event_type='KB_SYNC'")


def test_append_new_complete_bound_provenance_and_byte_stable_repeat(campaign):
    c = campaign
    pushed(c)
    statuses = c.statuses()
    first = sync.run(c.db, c.key, c.settings)
    stored, = kb.records(c.kb_db)
    policy = state.latest_policy_for_round(c.db, c.key, 1)
    assert stored["status"] == "NEW"
    assert stored["baseline_commit"] == c.base and stored["verified_tree_sha"] == c.tree
    assert stored["verified_archs"] == sorted(state.ARCH_NORMS)
    assert stored["files"] == ["file.c"] and stored["fix_summary"] == "correct value"
    assert stored["sandbox_branch"] == "refs/heads/sandbox/test" and stored["quickbuild_id"] == 1
    assert stored["change_id"] == "I" + "1" * 40 and stored["reused_from"] is None
    assert stored["fix_strategy_initial"] == policy["fix_strategy_initial"]
    assert stored["fix_strategy_final"] == policy["fix_strategy_final"]
    assert stored["error_lines"]
    for name, value in kb.describe_evidence(json.loads(c.anchor.read_text())).items():
        assert stored[name] == value
    before = c.db.path.read_bytes(), c.kb_db.read_bytes()
    second = sync.run(c.db, c.key, c.settings)
    assert second["kb_id"] == first["kb_id"] and second["deduped"]
    assert second["event_id"] == first["event_id"]
    assert before == (c.db.path.read_bytes(), c.kb_db.read_bytes())
    assert c.statuses() == statuses and len(audits(c)) == 1


def test_only_latest_request_latest_result_pass_promotes(campaign):
    c = campaign
    pushed(c)
    first = sync.run(c.db, c.key, c.settings)
    qb_result(c)
    qb_result(c, None)
    assert sync.run(c.db, c.key, c.settings)["status"] == "NEW"
    qb_result(c, "FAIL", new=False)
    assert sync.run(c.db, c.key, c.settings)["status"] == "NEW"
    qb_result(c, "PASS", new=False)
    statuses = c.statuses()
    result = sync.run(c.db, c.key, c.settings)
    assert result["status"] == "CI_VERIFIED" and result["kb_id"] == first["kb_id"]
    assert len(kb.records(c.kb_db)) == 1 and len(audits(c)) == 2
    before = c.db.path.read_bytes(), c.kb_db.read_bytes()
    assert sync.run(c.db, c.key, c.settings)["event_id"] == result["event_id"]
    assert before == (c.db.path.read_bytes(), c.kb_db.read_bytes())
    assert c.statuses() == statuses


@pytest.mark.parametrize("fault", ["no_push", "failed_push", "push_sha", "derive_tree",
                                  "missing_link", "edit_bytes", "ci_bytes", "policy", "cache"])
def test_unverified_provenance_refused_without_kb_or_database_writes(campaign, fault):
    c = campaign
    pushed(c)
    if fault == "no_push":
        c.sql("DELETE FROM campaign_gate_events WHERE event_type='PUSH'")
    elif fault in {"failed_push", "push_sha"}:
        payload = dict(state.gate_view(c.db, c.key).sandbox_push)
        payload["result" if fault == "failed_push" else "pushed_sha"] = (
            "failed" if fault == "failed_push" else "f" * 40
        )
        state.append_event(c.db, c.key, "PUSH", payload)
    elif fault == "derive_tree":
        c.sql("UPDATE verification_records SET verified_tree_sha=?", ("f" * 40,))
    elif fault == "missing_link":
        c.sql("DELETE FROM campaign_verifications WHERE arch_norm='aarch64'")
    elif fault == "edit_bytes":
        c.spec.write_text(c.spec.read_text() + " ")
    elif fault == "ci_bytes":
        c.anchor.write_text(c.anchor.read_text() + " ")
    elif fault == "policy":
        c.sql("DELETE FROM campaign_gate_events WHERE event_type='POLICY'")
    else:
        c.sql("DELETE FROM campaign_change_ids")
    before = c.db.path.read_bytes()
    with pytest.raises(state.StateInconsistent):
        sync.run(c.db, c.key, c.settings)
    assert c.db.path.read_bytes() == before
    assert not c.kb_db.exists() and not audits(c)


@pytest.mark.parametrize("fault", ["request_target", "result_echo", "build_binding"])
def test_pass_binding_cannot_promote_other_result(campaign, fault):
    c = campaign
    pushed(c)
    qb_result(c)
    if fault == "request_target":
        c.sql("UPDATE campaign_qb_requests SET sbs_target='other@bad'")
    elif fault == "result_echo":
        c.sql("UPDATE campaign_qb_events SET sbs_target_echo='other@bad' WHERE event_type='RESULT'")
    else:
        c.sql("UPDATE campaign_qb_events SET qb_build_id='999' WHERE event_type='RESULT'")
    before = c.db.path.read_bytes()
    with pytest.raises(state.StateInconsistent):
        sync.run(c.db, c.key, c.settings)
    assert c.db.path.read_bytes() == before and not c.kb_db.exists()


@pytest.mark.parametrize("point", ["append", "promote", "audit"])
def test_cross_file_crash_retries_same_record_and_single_audit(campaign, monkeypatch, point):
    c = campaign
    pushed(c)
    qb_result(c)
    owner, name = (state, "_append_event_on_connection") if point == "audit" else (kb, point)
    original = getattr(owner, name)

    def crash(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("injected crash after publication")

    before = c.db.path.read_bytes()
    with monkeypatch.context() as patch:
        patch.setattr(owner, name, crash)
        with pytest.raises(RuntimeError, match="injected crash"):
            sync.run(c.db, c.key, c.settings)
    assert c.db.path.read_bytes() == before and not audits(c)
    stored, = kb.records(c.kb_db)
    retried = sync.run(c.db, c.key, c.settings)
    assert retried["kb_id"] == stored["id"] and retried["status"] == "CI_VERIFIED"
    assert len(kb.records(c.kb_db)) == len(audits(c)) == 1


def test_report_db_only_source_and_precedent_match_bound_round(campaign, monkeypatch):
    c = campaign
    pushed(c, source="t1_cherry_pick", precedent="prior-kb-instance")
    sync.run(c.db, c.key, c.settings)
    assert kb.records(c.kb_db)[0]["reused_from"] == "prior-kb-instance"
    before = c.db.path.read_bytes()

    def forbidden(*args, **kwargs):
        pytest.fail("report must not open provenance or KB files")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_bytes", forbidden)
        patch.setattr(Path, "read_text", forbidden)
        row, = report.report(c.db)
        assert row["source_kind"] == "t1_cherry_pick"
        assert row["kb_precedent_ref"] == "prior-kb-instance"
        assert "prior-kb-instance" in report.markdown([row])
        assert "t1_cherry_pick" in report.markdown([row])
    assert c.db.path.read_bytes() == before
    state.create_round(c.db, c.key, round_index=2, edit_spec_ref="later", edit_spec_sha256="8" * 64)
    row, = report.report(c.db)
    assert row["source_kind"] is None and row["kb_precedent_ref"] is None


def test_t1_without_bound_precedent_refused(campaign):
    c = campaign
    pushed(c, source="t1_cherry_pick")
    with pytest.raises(state.StateInconsistent, match="precedent"):
        sync.run(c.db, c.key, c.settings)
    assert not c.kb_db.exists()


def test_latest_result_fail_overrides_prior_pass_without_status_inference(campaign):
    c = campaign
    pushed(c)
    qb_result(c)
    qb_result(c, "FAIL", new=False)
    state.append_status(c.db, c.key, "SANDBOX_QB_PASS")
    assert sync.run(c.db, c.key, c.settings)["status"] == "NEW"
    row, = report.report(c.db)
    assert row["source_kind"] == "generated" and row["kb_precedent_ref"] is None


def test_existing_merged_record_not_demoted_by_sync(campaign):
    c = campaign
    pushed(c)
    qb_result(c)
    first = sync.run(c.db, c.key, c.settings)
    kb.promote(c.kb_db, first["kb_id"], "MERGED")
    assert sync.run(c.db, c.key, c.settings)["status"] == "MERGED"
    before = c.db.path.read_bytes(), c.kb_db.read_bytes()
    sync.run(c.db, c.key, c.settings)
    assert before == (c.db.path.read_bytes(), c.kb_db.read_bytes())


def test_corrupt_kb_is_not_replaced_and_writes_no_audit(campaign):
    c = campaign
    pushed(c)
    c.kb_db.parent.mkdir()
    c.kb_db.write_bytes(b"not JSON\n")
    before = c.db.path.read_bytes(), c.kb_db.read_bytes()
    with pytest.raises(ValueError):
        sync.run(c.db, c.key, c.settings)
    assert before == (c.db.path.read_bytes(), c.kb_db.read_bytes())


@pytest.mark.parametrize("name,value", [("kb_db", "relative"), ("kb_db", None),
                                      ("campaign_workspace", "relative")])
def test_invalid_configuration_does_not_touch_database(campaign, name, value):
    c = campaign
    before = c.db.path.read_bytes()
    settings = dict(c.settings, **{name: value})
    with pytest.raises(ValueError):
        sync.run(c.db, c.key, settings)
    assert before == c.db.path.read_bytes() and not c.kb_db.exists()


def test_previously_audited_kb_row_cannot_disappear_silently(campaign):
    c = campaign
    pushed(c)
    sync.run(c.db, c.key, c.settings)
    c.kb_db.unlink()
    before = c.db.path.read_bytes()
    with pytest.raises(state.StateInconsistent, match="missing or rebound"):
        sync.run(c.db, c.key, c.settings)
    assert c.db.path.read_bytes() == before and not c.kb_db.exists()


def _sync_child(db_path, key, settings, queue):
    try:
        queue.put(sync.run(StateDatabase(db_path), key, settings))
    except sandbox._Reject as exc:
        queue.put({"error_code": exc.code})


def test_concurrent_sync_locks_out_duplicate_audit(campaign, monkeypatch):
    c = campaign
    pushed(c)
    ctx = multiprocessing.get_context("fork")
    started, release, queue = ctx.Event(), ctx.Event(), ctx.Queue()
    original = kb.append

    def paused(*args, **kwargs):
        started.set()
        assert release.wait(15)
        return original(*args, **kwargs)

    monkeypatch.setattr(kb, "append", paused)
    process = ctx.Process(target=_sync_child, args=(c.db.path, c.key, c.settings, queue))
    process.start()
    try:
        assert started.wait(15)
        with pytest.raises(sandbox._Reject) as caught:
            sync.run(c.db, c.key, c.settings)
        assert caught.value.code == "CAMPAIGN_STATE_BUSY"
    finally:
        release.set()
        process.join(15)
        if process.is_alive():
            process.terminate()
            process.join()
    assert process.exitcode == 0
    first = queue.get(timeout=5)
    second = sync.run(c.db, c.key, c.settings)
    assert second["event_id"] == first["event_id"]
    assert len(kb.records(c.kb_db)) == len(audits(c)) == 1


@pytest.mark.parametrize("name,value", [
    ("status", "PASS"), ("source_kind", "unknown"), ("kb_id", ""),
    ("push_event_id", True), ("qb_event_id", -1), ("dedupe_key", "A" * 64),
    ("kb_precedent_ref", {}), ("round_index", 0),
])
def test_kb_sync_validator_refuses_invalid_payload_without_writes(campaign, name, value):
    c = campaign
    payload = dict(kb_id="id", dedupe_key="a" * 64, status="NEW", round_index=1,
                   source_kind="generated", kb_precedent_ref=None, push_event_id=1,
                   qb_event_id=None, at="2026-11-04T00:00:00+00:00")
    payload[name] = value
    before = c.db.path.read_bytes()
    with pytest.raises(state.PayloadSchemaError):
        state.append_event(c.db, c.key, "KB_SYNC", payload)
    assert c.db.path.read_bytes() == before
