"""C8-02 evidence wrapper: one production result read, no trigger or retry."""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

from run_live import HERE, PREP, REPO, ROOT, checked, database, processes, write

OUT = HERE / "live-02"
EXPECTED = "c346b6b8d065ad14a5dbab2bb9e9d66f370234e8ac73133426789002075b2c63"
REQUEST = "202711dfe6b34472b6b8dc23f3a74a6e"


def current():
    conn = sqlite3.connect((ROOT / "state.db").as_uri() + "?mode=ro", uri=True)
    try:
        return dict(
            sha256=PREP.digest(ROOT / "state.db"),
            counts={
                table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("campaign_qb_requests", "campaign_qb_profiles", "campaign_qb_events")
            },
            events=conn.execute(
                "SELECT event_type,qb_build_id FROM campaign_qb_events ORDER BY event_id"
            ).fetchall(),
            status=conn.execute(
                "SELECT status FROM campaign_status_log ORDER BY log_id DESC LIMIT 1"
            ).fetchone()[0],
            request=conn.execute("SELECT request_id FROM campaign_qb_requests").fetchall(),
        )
    finally:
        conn.close()


def preflight():
    OUT.mkdir(exist_ok=False)
    report = dict(
        at=PREP.stamp(),
        immutable=PREP.immutable(),
        database=current(),
        processes=processes(),
        profiles=[str(p) for p in Path("/dev/shm").glob("p5q-browser-*")],
        transports=[str(p) for p in ROOT.rglob(".transport")],
        d_samples=[],
        commands=[],
    )
    for argv in (["df", "-h", "/home", "/dev/shm"], ["free", "-h"]):
        report["commands"].append(PREP.command(argv))
    for index in range(3):
        if index:
            time.sleep(10)
        result = PREP.command(["ps", "-eo", "state,pid,comm"])
        report["d_samples"].append(
            dict(
                at=PREP.stamp(),
                rows=[row for row in result["stdout"].splitlines() if row.split()[:1] == ["D"]],
            )
        )
    write(OUT / "preflight.json", report)
    assert report["database"]["sha256"] == EXPECTED
    assert list(report["database"]["counts"].values()) == [1, 1, 1]
    assert report["database"]["events"] == [("SUBMITTED", None)]
    assert report["database"]["request"] == [(REQUEST,)]
    assert report["database"]["status"] == "QB_REQUESTED"
    assert not report["processes"] and not report["profiles"] and not report["transports"]
    assert not any(sample["rows"] for sample in report["d_samples"]), "D_STATE_REVIEW_REQUIRED"
    assert (ROOT / "config.yaml").read_bytes() == (HERE / "preparation/config.yaml").read_bytes()
    write(OUT / "preflight-passed.json", {"at": PREP.stamp(), "sha256": EXPECTED})
    print("PREFLIGHT_PASS")


def fetch():
    assert PREP.digest(ROOT / "state.db") == EXPECTED
    PREP.immutable()
    assert (OUT / "preflight-passed.json").exists()
    assert os.environ.get("DISPLAY") and os.environ.get("P5Q_TEST_DISPLAY") != "virtual"
    assert not processes() and not list(Path("/dev/shm").glob("p5q-browser-*"))
    dest = OUT / "fetch"
    dest.mkdir(exist_ok=False)
    argv = [
        sys.executable,
        "-m",
        "ci_triage",
        "qb-result-fetch",
        "--request-id",
        REQUEST,
        "--state-db",
        str(ROOT / "state.db"),
        "--state-root",
        str(ROOT / "state"),
        "--config",
        str(ROOT / "config.yaml"),
    ]
    before = database(dest, "before")
    trace = ROOT / "state/qb_traces/7383e5c48f62.jsonl"
    old_trace = trace.read_bytes()
    checked(dest / "trace-before.jsonl", old_trace)
    before_files = {
        str(p.relative_to(ROOT / "state")): PREP.digest(p)
        for p in (ROOT / "state").rglob("*")
        if p.is_file()
    }
    facts = dict(
        argv=argv,
        started_at=PREP.stamp(),
        before=before,
        request_id=REQUEST,
        production=True,
        authorization="P5Q-C8-02",
        attempt=1,
    )
    write(dest / "command.json", facts)
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("P5Q_TEST_") or key in {
            "QB_COOKIE",
            "QB_PASSWORD",
            "DEBUG",
            "PWDEBUG",
            "NODE_OPTIONS",
            "PYTHONPATH",
            "MYPYPATH",
        }:
            env.pop(key, None)
    started = time.monotonic()
    process = subprocess.Popen(
        argv,
        cwd=REPO,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    observations, previous, last_chromium = [], None, None
    print("READ_STARTED", flush=True)
    while True:
        rows = processes()
        now = time.monotonic()
        if any("chromium" in row["kinds"] for row in rows):
            last_chromium = now
        if rows != previous:
            observations.append(
                dict(at=PREP.stamp(), elapsed_seconds=now - started, processes=rows)
            )
            previous = rows
        try:
            stdout, stderr = process.communicate(timeout=0.2)
            break
        except subprocess.TimeoutExpired:
            continue
    ended = time.monotonic()
    checked(dest / "stdout.json", stdout)
    checked(dest / "stderr.txt", stderr)
    new_trace = trace.read_bytes()
    assert new_trace.startswith(old_trace)
    checked(dest / "trace-after.jsonl", new_trace)
    checked(dest / "trace-new.jsonl", new_trace[len(old_trace) :])
    changed = []
    for path in sorted((ROOT / "state").rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(ROOT / "state"))
        if before_files.get(rel) != PREP.digest(path):
            changed.append(rel)
            checked(dest / "state" / rel, path.read_bytes())
    facts.update(
        ended_at=PREP.stamp(),
        exit_code=process.returncode,
        elapsed_seconds=ended - started,
        last_chromium_to_cli_exit_seconds=(ended - last_chromium if last_chromium else None),
        agent_exit_code="NOT_COLLECTED",
        after=database(dest, "after"),
        changed_state_files=changed,
        state=current(),
        immutable=PREP.immutable(),
    )
    write(dest / "process-observations.json", observations)
    write(dest / "execution.json", facts)
    print(json.dumps(dict(exit=process.returncode, result=json.loads(stdout)), ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("preflight", "fetch"))
    args = parser.parse_args()
    preflight() if args.step == "preflight" else fetch()
