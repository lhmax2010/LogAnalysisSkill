"""Record an authorized C8 production invocation; never retry a command."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

from ci_triage._campaign_workspace import _unit_hash
from ci_triage.qb_redact import PageRedactor

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("c8_preparation", HERE / "preparation/prepare_c8.py")
assert SPEC is not None and SPEC.loader is not None
PREP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREP)
ROOT, REPO = PREP.ROOT, PREP.REPO
INITIAL = "dd43219d2964e23d711e904ab640a73eb3c328e6685940dc7711beb4f7563ff2"


def checked(path, raw):
    checker = PageRedactor()
    checker.check_bytes(raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    checker.check_written(path)


def write(path, value):
    checked(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def database(out, label):
    conn = sqlite3.connect((ROOT / "state.db").as_uri() + "?mode=ro", uri=True)
    try:
        checked(out / f"state-{label}.sql", ("\n".join(conn.iterdump()) + "\n").encode())
        counts = {
            name: conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            for name in ("campaign_qb_requests", "campaign_qb_profiles", "campaign_qb_events")
        }
    finally:
        conn.close()
    return dict(sha256=PREP.digest(ROOT / "state.db"), counts=counts)


def processes():
    rows = []
    for entry in Path("/proc").glob("[0-9]*"):
        try:
            args = (entry / "cmdline").read_bytes().split(b"\0")
            kinds = [
                kind
                for kind, needle in (
                    ("chromium", b"ms-playwright/chromium"),
                    ("agent", b"qb_browser_agent.mjs"),
                )
                if any(needle in arg for arg in args)
            ]
            if kinds:
                rows.append(dict(pid=int(entry.name), kinds=kinds))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            pass
    return rows


def preflight():
    out = HERE / "live-01"
    out.mkdir(exist_ok=False)
    assert PREP.digest(ROOT / "state.db") == INITIAL
    assert (ROOT / "config.yaml").read_bytes() == (HERE / "preparation/config.yaml").read_bytes()
    assert os.environ.get("DISPLAY") and os.environ.get("P5Q_TEST_DISPLAY") != "virtual"
    original_write = PREP.write
    try:
        PREP.write = lambda name, value: write(out / name, value)
        PREP.preflight()
    finally:
        PREP.write = original_write
    report = json.loads((out / "preflight.json").read_text())
    assert not report["persistent_d_pids"], "PERSISTENT_D_STATE"
    assert report["db_sha256_after"] == INITIAL
    write(
        out / "authorization.json",
        dict(
            at=PREP.stamp(),
            user_reply="确认提交",
            unit=PREP.KEY,
            target=PREP.TARGET,
            maximum_real_trigger_invocations=1,
            retrigger=False,
        ),
    )
    print(
        json.dumps(dict(preflight="PASS", d_samples=[len(s["rows"]) for s in report["d_samples"]]))
    )


def invoke(step, request_id, name):
    PREP.immutable()
    assert (ROOT / "config.yaml").read_bytes() == (HERE / "preparation/config.yaml").read_bytes()
    assert os.environ.get("DISPLAY") and os.environ.get("P5Q_TEST_DISPLAY") != "virtual"
    out = HERE / "live-01" / name
    out.mkdir(exist_ok=False)
    args = [
        sys.executable,
        "-m",
        "ci_triage",
        "qb-trigger" if step == "trigger" else "qb-result-fetch",
    ]
    if step == "trigger":
        assert name == "trigger" and request_id is None
        assert PREP.digest(ROOT / "state.db") == INITIAL
        auth = json.loads((out.parent / "authorization.json").read_text())
        assert auth["user_reply"] == "确认提交"
        args += ["--verification-ids", ",".join(PREP.IDS)]
    else:
        assert request_id and name.startswith("fetch-")
        args += ["--request-id", request_id]
    args += [
        "--state-db",
        str(ROOT / "state.db"),
        "--state-root",
        str(ROOT / "state"),
        "--config",
        str(ROOT / "config.yaml"),
    ]
    before = database(out, "before")
    files_before = {
        str(p.relative_to(ROOT / "state")): PREP.digest(p)
        for p in (ROOT / "state").rglob("*")
        if p.is_file()
    }
    trace = ROOT / "state/qb_traces" / (_unit_hash(PREP.KEY) + ".jsonl")
    trace_before = trace.read_bytes() if trace.exists() else b""
    checked(out / "trace-before.jsonl", trace_before)
    facts = dict(argv=args, started_at=PREP.stamp(), before=before, attempt=1, production=True)
    write(out / "command.json", facts)
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
    start = time.monotonic()
    process = subprocess.Popen(
        args,
        cwd=REPO,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    observations, previous, last_chromium = [], None, None
    print(f"C8_{step.upper()}_STARTED", flush=True)
    while True:
        rows = processes()
        now = time.monotonic()
        if any("chromium" in row["kinds"] for row in rows):
            last_chromium = now
        if rows != previous:
            observations.append(dict(at=PREP.stamp(), elapsed_seconds=now - start, processes=rows))
            previous = rows
        try:
            stdout, stderr = process.communicate(timeout=0.2)
            break
        except subprocess.TimeoutExpired:
            continue
    ended = time.monotonic()
    facts.update(
        ended_at=PREP.stamp(),
        exit_code=process.returncode,
        elapsed_seconds=ended - start,
        last_chromium_to_cli_exit_seconds=(
            ended - last_chromium if last_chromium is not None else None
        ),
        agent_exit_code="NOT_COLLECTED",
    )
    checked(out / "stdout.json", stdout)
    checked(out / "stderr.txt", stderr)
    facts["after"] = database(out, "after")
    trace_after = trace.read_bytes() if trace.exists() else b""
    assert trace_after.startswith(trace_before)
    checked(out / "trace-after.jsonl", trace_after)
    checked(out / "trace-new.jsonl", trace_after[len(trace_before) :])
    changed = []
    for path in sorted((ROOT / "state").rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(ROOT / "state"))
        if files_before.get(rel) == PREP.digest(path):
            continue
        changed.append(rel)
        checked(out / "state" / rel, path.read_bytes())
    facts.update(changed_state_files=changed, immutable=PREP.immutable())
    write(out / "process-observations.json", observations)
    write(out / "execution.json", facts)
    print(
        json.dumps(
            dict(
                exit=process.returncode,
                stdout=json.loads(stdout),
                tail_seconds=facts["last_chromium_to_cli_exit_seconds"],
            ),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("preflight", "trigger", "fetch"))
    parser.add_argument("--request-id")
    parser.add_argument("--name")
    options = parser.parse_args()
    if options.step == "preflight":
        preflight()
    else:
        invoke(options.step, options.request_id, options.name or options.step)
