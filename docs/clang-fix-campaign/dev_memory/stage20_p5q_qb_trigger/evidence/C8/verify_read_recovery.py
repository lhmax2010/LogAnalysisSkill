"""Offline checks of the single C8-03 read; never launch a browser or write state."""

import hashlib
import json
import sqlite3
from pathlib import Path

from ci_triage import qb_binding, qb_result_html
from ci_triage.qb_browser import _check_diagnostic_strings
from ci_triage.qb_redact import PageRedactor
from run_live import HERE, PREP, REPO, ROOT, write


def main():
    dest = HERE / "live-02/fetch"
    execution = json.loads((dest / "execution.json").read_text())
    output = json.loads((dest / "stdout.json").read_text())[0]
    trace = [json.loads(line) for line in (dest / "trace-new.jsonl").read_text().splitlines()]
    request = output["request_id"]
    assert execution["exit_code"] == 0 and output["status"] == "PASS" and output["terminal"]
    assert execution["after"]["sha256"] == PREP.digest(ROOT / "state.db")
    before = sqlite3.connect(":memory:")
    before.executescript((dest / "state-before.sql").read_text())
    profile = json.loads(
        before.execute("SELECT profile_json FROM campaign_qb_profiles").fetchone()[0]
    )
    bound_before = {
        row[0]
        for row in before.execute(
            "SELECT qb_build_id FROM campaign_qb_events WHERE event_type='BUILD_BOUND'"
        )
    }
    before.close()
    root = dest / "state/qb_evidence" / request
    configuration = (root / "01.overview-1917.html").read_text()
    recent = qb_result_html.recent_builds(configuration, profile)
    discovery = trace[0]
    assert discovery["mode"] == "read" and discovery["W"] == 0
    assert len(discovery["rounds"]) == 1 and discovery["final_category"] == "已绑定"
    round_ = discovery["rounds"][0]
    candidates = round_["candidates"]
    assert [row["build_id"] for row in candidates] == sorted(set(recent) - bound_before, key=int)
    assert sum(row["category"] == "匹配" for row in candidates) == 1
    result_file = dest / "state" / output["qb_result_path"]
    result = json.loads(result_file.read_text())
    parent, child = output["qb_build_id"], output["child_build_id"]
    target = "platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0"
    parent_html = (root / f"03.{parent}-overview.html").read_text()
    parent_vars = (root / f"02.{parent}-variables.html").read_text()
    child_html = (root / f"04.{child}-overview.html").read_text()
    child_vars = (root / f"05.{child}-variables.html").read_text()
    facts = qb_binding.parent_facts(
        parent_html, parent_vars, parent, profile, dict(request_id=request, sbs_target=target)
    )
    facts.update(
        qb_result_html.child_overview(child_html, profile, facts["child_build_result_text"])
    )
    facts.update(qb_result_html.child_variables(child_vars, parent, child, target))
    assert facts.pop("each_status") == ""
    for key, value in facts.items():
        assert result[key] == value, key
    snapshot = qb_result_html.snapshot_kind(
        facts["child_params_echo"]["SNAPSHOT_NUM_URL"], profile["form"]["SNAPSHOT_NUM"]
    )
    assert snapshot == ("same", result["snapshot_used"])
    assert not result["snapshot_drift_accepted"]
    expected_pages = {
        "01.overview-1917.html",
        f"02.{parent}-variables.html",
        f"03.{parent}-overview.html",
        f"04.{child}-overview.html",
        f"05.{child}-variables.html",
    }
    assert {p.name for p in root.iterdir()} == expected_pages
    assert not any("qb_diagnostics/" in name for name in execution["changed_state_files"])
    assert not list(Path("/dev/shm").glob("p5q-browser-*"))
    assert not list(ROOT.rglob(".transport"))
    source = (REPO / "tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs").read_bytes()
    prefix = hashlib.sha256(source.split(b"export class Agent {")[0]).hexdigest()
    assert prefix == "40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16"
    checker = PageRedactor()
    files = []
    for path in sorted((HERE / "live-02").rglob("*")):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        checker.check_bytes(raw)
        if path.suffix == ".json":
            _check_diagnostic_strings(json.loads(raw), checker)
        elif path.suffix == ".jsonl":
            for line in raw.splitlines():
                _check_diagnostic_strings(json.loads(line), checker)
        files.append(dict(path=str(path.relative_to(HERE)), sha256=PREP.digest(path)))
    report = dict(
        at=PREP.stamp(),
        immutable=PREP.immutable(),
        agent_prefix=prefix,
        execution_exit=execution["exit_code"],
        db_sha256=execution["after"]["sha256"],
        recent_builds=recent,
        bound_before=sorted(bound_before),
        candidates=candidates,
        candidate_set_equal=True,
        lookup_rounds=1,
        discovery_read_duration_sum_ms=sum(row["elapsed_ms"] for row in round_["reads"]),
        other_candidates_all_readable=all(
            row["category"] == "标记不同" for row in candidates if row["build_id"] != parent
        ),
        outside_identity_counts=[
            {key: row[key] for key in ("path", "outside_identity_count")}
            for row in [*round_["reads"], *trace[1:]]
        ],
        archived_pages=sorted(expected_pages),
        other_users_pages=0,
        diagnostics_added=0,
        terminal=dict(
            parent=parent,
            child=child,
            status=result["status"],
            parent_status=result["parent_status_text"],
            child_status=result["child_status_text"],
            child_result=result["child_build_result_text"],
            each_status="",
            request_marker=result["request_marker_echo"],
            target=result["sbs_target_echo"],
            frozen_snapshot=profile["form"]["SNAPSHOT_NUM"],
            parent_snapshot=result["params_echo"]["SNAPSHOT_NUM"],
            child_snapshot=result["child_params_echo"]["SNAPSHOT_NUM_URL"],
            snapshot_kind=snapshot[0],
            snapshot_drift_accepted=False,
            result_sha256=PREP.digest(result_file),
            accepted=result["accepted"],
        ),
        redaction_failures=0,
        files=files,
        acceptance="STOPPED: two unreadable candidates and one nonzero identity count",
        human_build_confirmation="PENDING",
    )
    write(dest / "archive-validation.json", report)
    print(
        json.dumps(dict(offline_checks="PASS", files=len(files), acceptance=report["acceptance"]))
    )


if __name__ == "__main__":
    main()
