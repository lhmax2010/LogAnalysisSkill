"""Record one explicitly authorized production C6a invocation without retries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from ci_triage.qb_redact import PageRedactor

ROOT = Path("/home/linhao/Toolchain/p5q-live-validation/p5q-c6")
REPO = Path("/home/linhao/Toolchain/development/LogAnalysisSkill")
EVIDENCE = Path(__file__).resolve().parent
KEY = "p5q-c6-libtirpc-20261015"
FROZEN_HASH = "f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c"


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def checked_write(path: Path, content: bytes) -> None:
    redactor = PageRedactor()
    redactor.check_bytes(content)
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    redactor.check_bytes(path.read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("trigger", "fetch"))
    parser.add_argument("--evidence-run", choices=("live-01", "live-02"), default="live-01")
    options = parser.parse_args()
    step, evidence_run = options.step, options.evidence_run
    frozen = REPO / "docs/clang-fix-campaign/p5q-qb-trigger-design-v1.5-FROZEN.md"
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == FROZEN_HASH
    assert (ROOT / "config.yaml").read_bytes() == (
        EVIDENCE / "preparation/config.yaml"
    ).read_bytes()
    assert os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    args = [
        sys.executable,
        "-m",
        "ci_triage",
        "qb-" + ("trigger" if step == "trigger" else "result-fetch"),
    ]
    if step == "trigger":
        prepared = json.loads((EVIDENCE / "preparation/state-prepared.json").read_text())
        assert hashlib.sha256((ROOT / "state.db").read_bytes()).hexdigest() == prepared["db_sha256"]
        args += ["--verification-ids", ",".join(f"{KEY}-v{i}" for i in range(3))]
    else:
        trigger = json.loads((EVIDENCE / evidence_run / "trigger/stdout.json").read_text())[0]
        assert trigger["action"] == "submitted_bound" and trigger["error_code"] is None
        args += ["--request-id", trigger["request_id"]]
    args += [
        "--state-db",
        str(ROOT / "state.db"),
        "--state-root",
        str(ROOT / "state"),
        "--config",
        str(ROOT / "config.yaml"),
    ]
    assert "--retrigger" not in args
    output = EVIDENCE / evidence_run / step
    output.mkdir(parents=True, exist_ok=False)
    facts = {
        "argv": args,
        "started_at": stamp(),
        "user_authorization": "确认提交",
        "production_path": True,
        "test_arguments": [],
        "attempt": 1,
        "evidence_run": evidence_run,
    }
    checked_write(
        output / "command.json", (json.dumps(facts, ensure_ascii=False, indent=2) + "\n").encode()
    )
    env = os.environ.copy()
    for name in (
        "QB_COOKIE",
        "QB_PASSWORD",
        "DEBUG",
        "PWDEBUG",
        "NODE_OPTIONS",
        "PYTHONPATH",
        "MYPYPATH",
    ):
        env.pop(name, None)
    print(f"C6A_{step.upper()}_STARTED", flush=True)
    process = subprocess.Popen(
        args,
        cwd=REPO,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    facts.update(ended_at=stamp(), exit_code=process.returncode)
    checked_write(output / "stdout.json", stdout)
    checked_write(output / "stderr.txt", stderr)
    conn = sqlite3.connect((ROOT / "state.db").as_uri() + "?mode=ro", uri=True)
    try:
        sql = "\n".join(conn.iterdump()) + "\n"
    finally:
        conn.close()
    checked_write(output / "state-after.sql", sql.encode())
    facts["state_db_sha256"] = hashlib.sha256((ROOT / "state.db").read_bytes()).hexdigest()
    checked_write(
        output / "execution.json", (json.dumps(facts, ensure_ascii=False, indent=2) + "\n").encode()
    )
    print(
        json.dumps(
            {"step": step, "exit_code": process.returncode, "stdout": json.loads(stdout)},
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
