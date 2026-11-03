from __future__ import annotations

import copy
import hashlib
import io
import json
import subprocess
import sys
import uuid
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from qb_discovery_fixtures import configuration, reply
from test_campaign_batch2_intake import case as case
from test_campaign_batch3_start import execute
from test_campaign_batch3_start import ready as ready
from test_campaign_fake_ssh import transport as transport
from test_qb_result_fetch import CONFIG, FROZEN, mutate, summary_change, variable_page
from test_qb_trigger import ARCHIVE, variables
from tizen_baseline_reproduce import baseline
from tizen_campaign_core import campaign_state as state
from tizen_campaign_intake import intake
from tizen_campaign_repair.__main__ import _main_suppress_policy
from tizen_campaign_repair.campaign_repair_step import (
    CampaignRepairStepOptions,
    campaign_repair_step,
)
from tizen_campaign_report import report
from tizen_qb_verify import qb_result_fetch as fetch
from tizen_qb_verify import qb_trigger as trigger
from tizen_qb_verify.qb_config import ARCHITECTURES
from tizen_review_submit import review_submit as review
from tizen_sandbox_submit import sandbox_submit as sandbox


def sequence(c):
    conn = state._read_connection(c.db)
    try:
        return [
            row[0]
            for row in conn.execute(
                "SELECT status FROM campaign_status_log WHERE campaign_unit_key=? ORDER BY log_id",
                (c.key,),
            )
        ]
    finally:
        conn.close()


@pytest.fixture
def flow(ready, monkeypatch, tmp_path):
    c = ready
    assert execute(c)[0] == 0
    binary = c.transport[0].parent / "bin/gbs"
    binary.write_text(
        "#!/usr/bin/env python3\nimport os, pathlib, sys\n"
        "sys.stdout.write(pathlib.Path(os.environ['FAKE_BASELINE_LOG']).read_text())\n"
        "sys.exit(int(os.environ['FAKE_BASELINE_EXIT']))\n"
    )
    monkeypatch.setenv("FAKE_BASELINE_LOG", str(c.args.ci_log))
    monkeypatch.setenv("FAKE_BASELINE_EXIT", "1")
    for prefix in ("GIT_AUTHOR", "GIT_COMMITTER"):
        monkeypatch.setenv(prefix + "_NAME", "Offline Test")
        monkeypatch.setenv(prefix + "_EMAIL", "offline@example.invalid")
    created = intake.add_unit(c.args)
    for arch in ("aarch64", "armv7l", "x86_64"):
        args = SimpleNamespace(
            state_db=c.db.path,
            config=c.args.config,
            arch="standard-" + arch,
            campaign_unit_key=c.key,
            src_clean=Path(created["src_clean"]),
            base_commit=c.args.base_commit,
            package=c.args.spec_name,
            profile="clang",
            gbs_conf=Path(c.settings["clang_conf_path"]),
            evidence_ci=None,
            output_dir=tmp_path / ("baseline-" + arch),
            wall_timeout=10,
            keep_copy=False,
        )
        code, payload = baseline.run(args)
        assert code == 0, payload
    c.edit = tmp_path / "edit.json"
    c.edit.write_text(
        json.dumps(
            dict(
                schema_version="gbs_patch_suggest/edit-spec/v1",
                patch_name="repair",
                edits=[dict(file="src/clang_case.c", old="return missing", new="return 0")],
            )
        )
    )
    c.repair = CampaignRepairStepOptions(
        c.key, c.db, c.args.config, 1, c.edit, "standard-aarch64", 10
    )
    hook = tmp_path / "commit-msg"
    hook.write_text(
        '#!/bin/sh\nprintf "\\nChange-Id: I1111111111111111111111111111111111111111\\n" >> "$1"\n'
    )
    c.project = dict(
        enabled=True,
        overview_id=1917,
        configuration_path=CONFIG,
        project_name="Tizen-Base-Toolchain",
        qb_pass_requires_accept=False,
        form={
            "BUILD_TYPE": "Full",
            "REPO_TYPE": "ALL",
            "BUILD_REFERENCE": "Ref. Snapshot",
            "SNAPSHOT_NUM": "@freeze",
            "PROJECT_BRANCH": "tizen_base",
            "Immediate Stop With Error": True,
            "CHILD_CONFIGURATIONS": [ARCHITECTURES],
            "TARGET_IMAGE": [],
            "Add Package List": "",
            "Remove Package List": "",
        },
    )
    c.settings.update(
        gerrit_commit_msg_hook=str(hook),
        gerrit_commit_msg_hook_sha256=hashlib.sha256(hook.read_bytes()).hexdigest(),
        qb=dict(
            base_url="https://quickbuild.tizen.org",
            projects={"tizen_base": c.project},
            browser=dict(
                node=sys.executable,
                playwright_module=sys.executable,
                chromium=sys.executable,
                login_timeout_seconds=60,
            ),
        ),
    )
    c.args.config.write_text(yaml.safe_dump(c.settings))
    c.state_root = tmp_path / "qb-state"
    c.script, c.transcript = tmp_path / "replies.json", tmp_path / "commands.jsonl"
    original = subprocess.Popen

    def popen(argv, *a, **kw):
        if any(str(v).endswith("qb_browser_agent.mjs") for v in argv):
            argv = [
                sys.executable,
                str(Path(__file__).parents[1] / "fixtures/qb_fake_agent.py"),
                str(c.script),
                str(c.transcript),
            ]
        return original(argv, *a, **kw)

    monkeypatch.setattr(subprocess, "Popen", popen)
    return c


def repair_one(c, arch):
    assert (
        _main_suppress_policy(
            [
                "check",
                "--edit-spec",
                str(c.edit),
                "--src-root",
                str(c.root / "src"),
                "--source-kind",
                "generated",
            ],
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )
        == 0
    )
    return campaign_repair_step(replace(c.repair, arch_raw="standard-" + arch))


def push_and_request(c, monkeypatch):
    monkeypatch.setenv("FAKE_BASELINE_EXIT", "0")
    ids = []
    for arch in ("aarch64", "armv7l", "x86_64"):
        result = repair_one(c, arch)
        assert result.exit_code == 0 and result.result.result == "PASS", result.result.to_dict()
        ids.append(result.result.verification_id)
    assert state.latest_status(c.db, c.key) == "REPAIR_ROUND_RUNNING"
    c.ids = ",".join(ids)
    result = sandbox.sandbox_submit(
        sandbox.SandboxSubmitOptions(
            c.ids, c.db.path, c.args.config, "sandbox/offline", "repair", "generated"
        )
    )
    assert result.exit_code == 0, result.payload
    c.target = c.args.project + "@" + result.payload["derived_commit_sha"]
    c.request_id = uuid.UUID(int=1).hex
    monkeypatch.setattr(trigger.uuid, "uuid4", lambda: uuid.UUID(int=1))
    c.marker = "clang-fix-campaign request=" + c.request_id
    fields = copy.deepcopy(c.project["form"])
    fields.update({"SNAPSHOT_NUM": FROZEN, "Build Package List": c.target, "BUILD NOTES": c.marker})
    readback = {
        f"{k}/{'selection' if k in trigger._PALETTES else 'value'}": v for k, v in fields.items()
    }
    c.script.write_text(
        json.dumps(
            dict(
                configuration_pages={"/overview/1917": reply(configuration(c.project))},
                replies=[
                    dict(ok=True),
                    dict(ok=True, released=False),
                    dict(
                        ok=True,
                        released=False,
                        readback=readback,
                        fingerprint="a" * 64,
                        snapshot_option_count=1,
                    ),
                    dict(ok=True, released=True, landed="build", build_id="1193467"),
                    reply(variables(c.target, c.marker)),
                ],
            )
        )
    )
    code, results = trigger.qb_trigger(
        trigger.QbTriggerOptions(c.db.path, c.state_root, c.args.config, verification_ids=c.ids),
        stderr=io.StringIO(),
    )
    assert code == 0 and results[0]["action"] == "submitted_bound", results


def read_pass(c):
    parent = dict(
        QB_TRIGGER_ID=("", "1193467"),
        BUILD_PKG_LIST_MODIFY=("Build Package List", c.target),
        BUILD_NOTES=("BUILD NOTES", c.marker),
        BUILD_REFERENCE=("", "Ref. Snapshot"),
        BUILD_TYPE=("", "Full"),
        PROJECT_BRANCH=("", "tizen_base"),
        FAIL_FAST=("Immediate Stop With Error", "yes"),
        CHILD_CONFIGURATIONS=("", ARCHITECTURES),
        SNAPSHOT_NUM=("", FROZEN),
    )
    child = dict(
        TRIGGER_ID=("", "1193467"),
        QB_TRIGGER_ID=("", "1193469"),
        FAIL_FAST=("", "yes"),
        BUILD_PKG_LIST=("", c.target),
        REPO_ARCH=("", ARCHITECTURES),
        CHILD_CONFIGURATIONS=("", ARCHITECTURES),
        BUILD_REFERENCE=("", "Ref. Snapshot"),
        SNAPSHOT_NUM_URL=("", fetch.pages.SNAPSHOT_ROOT + FROZEN),
        EACH_GBS_BUILD_STATUS=("", ""),
    )
    c.script.write_text(
        json.dumps(
            [
                dict(ok=True),
                reply((ARCHIVE / "01.response.html").read_text()),
                reply(variable_page(2, parent)),
                reply(
                    mutate(
                        (ARCHIVE / "03.response.html").read_text(),
                        lambda d: summary_change(d, "Status", "Successful"),
                    )
                ),
                reply(variable_page(4, child)),
            ]
        )
    )
    code, results = fetch.qb_result_fetch(
        fetch.QbResultFetchOptions(c.db.path, c.state_root, c.args.config, request_id=c.request_id),
        stderr=io.StringIO(),
    )
    assert code == 0, results
    return state.latest_qb_result(c.db, c.key)


def test_success_full_offline_chain(flow, monkeypatch):
    c = flow
    push_and_request(c, monkeypatch)
    event = read_pass(c)
    result = review.run(
        review.ReviewOptions(
            c.ids,
            c.db.path,
            c.args.config,
            c.state_root / event["qb_result_ref"],
            "refs/for/tizen_base",
        )
    )
    assert result.exit_code == 0, result.payload
    assert report.finish(c.db, c.key)[0] == 0
    row = report.report(c.db)[0]
    assert row["status"] == "REVIEW_PUSHED" and row["workspace_status"] == "已释放"
    states = sequence(c)
    print("STATE_SEQUENCE=" + json.dumps(states))
    assert states[-1] == "REVIEW_PUSHED"
    assert all(
        s in states
        for s in (
            "CI_EVIDENCE_READY",
            "BASELINE_RUNNING",
            "BASELINE_REPRODUCED",
            "REPAIR_ROUND_RUNNING",
            "LOCAL_3ARCH_PASS",
            "SANDBOX_PUSHED",
            "QB_REQUESTED",
            "QB_TRIGGERED",
            "SANDBOX_QB_PASS",
            "REVIEW_PUSHING",
        )
    )


def test_stalled_finish_offline_chain(flow):
    outcome = repair_one(flow, "aarch64")
    assert outcome.result.verdict == "stalled", outcome.result.to_dict()
    assert state.latest_status(flow.db, flow.key) == "STALLED"
    assert report.finish(flow.db, flow.key)[0] == 0
    assert report.report(flow.db)[0]["status"] == "STALLED"
    print("STATE_SEQUENCE=" + json.dumps(sequence(flow)))


def test_triggered_abandon_then_late_pass_offline_chain(flow, monkeypatch):
    c = flow
    push_and_request(c, monkeypatch)
    assert report.finish(c.db, c.key)[0] == 4
    report.release(c.db, c.key, c.settings, "Offline Operator", True)
    assert report.report(c.db)[0]["workspace_status"] == "已放弃"
    event = read_pass(c)
    result = review.run(
        review.ReviewOptions(
            c.ids,
            c.db.path,
            c.args.config,
            c.state_root / event["qb_result_ref"],
            "refs/for/tizen_base",
        )
    )
    assert result.exit_code == 4 and result.payload["error_code"] == "REJECTED_UNIT_ABANDONED"
    assert state.latest_status(c.db, c.key) == "SANDBOX_QB_PASS"
    assert report.report(c.db)[0]["workspace_status"] == "已放弃"
    conn = state._read_connection(c.db)
    try:
        assert (
            conn.execute(
                "SELECT count(*) FROM campaign_gate_events WHERE event_type='REVIEW'"
            ).fetchone()[0]
            == 0
        )
    finally:
        conn.close()
    print("STATE_SEQUENCE=" + json.dumps(sequence(c)))


def test_suppress_edit_passes_sandbox_but_fails_review_a2(flow, monkeypatch):
    c = flow
    edit = json.loads(c.edit.read_text())
    edit["edits"] = [
        dict(
            file="src/clang_case.c",
            old="int main() { return missing; }",
            new=(
                '#pragma GCC diagnostic ignored "-Wunused-variable"\nint main() { return missing; }'
            ),
        )
    ]
    c.edit.write_text(json.dumps(edit))
    push_and_request(c, monkeypatch)
    event = read_pass(c)
    before = sandbox.SandboxGit().run(c.transport[1], "show-ref").stdout
    result = review.run(
        review.ReviewOptions(
            c.ids,
            c.db.path,
            c.args.config,
            c.state_root / event["qb_result_ref"],
            "refs/for/tizen_base",
        )
    )
    assert result.exit_code == 4 and result.payload["error_code"] == "REJECTED_REVIEW_GATE"
    assert state.latest_status(c.db, c.key) == "REVIEW_INELIGIBLE"
    assert sandbox.SandboxGit().run(c.transport[1], "show-ref").stdout == before
    assert state.latest_event(c.db, c.key, "REVIEW") is None
