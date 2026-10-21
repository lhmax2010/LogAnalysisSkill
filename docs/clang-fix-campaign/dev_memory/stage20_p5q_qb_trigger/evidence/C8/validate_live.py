"""Offline audit of C8 live-01; never invokes a browser or modifies a live DB."""

import hashlib
import json
import os
import sqlite3
import subprocess
from pathlib import Path

from ci_triage.qb_browser import _check_diagnostic_strings
from ci_triage.qb_redact import PageRedactor
from run_live import HERE, PREP, REPO, ROOT, write


def main():
    live = HERE / "live-01"
    execution = json.loads((live / "trigger/execution.json").read_text())
    assert PREP.digest(ROOT / "state.db") == execution["after"]["sha256"]
    conn = sqlite3.connect((ROOT / "state.db").as_uri() + "?mode=ro", uri=True)
    try:
        assert "\n".join(conn.iterdump()) + "\n" == (live / "trigger/state-after.sql").read_text()
        assert conn.execute("SELECT event_type FROM campaign_qb_events").fetchall() == [
            ("SUBMITTED",)
        ]
        assert conn.execute("SELECT COUNT(*) FROM campaign_units").fetchone() == (1,)
        status = conn.execute(
            "SELECT status FROM campaign_status_log ORDER BY log_id DESC LIMIT 1"
        ).fetchone()[0]
        assert status == "QB_REQUESTED"
    finally:
        conn.close()
    cleanup = dict(
        profiles=[str(p) for p in Path("/dev/shm").glob("p5q-browser-*")],
        transports=[str(p) for p in ROOT.rglob(".transport")],
        processes=[],
        scan_errors=[],
    )
    for path in Path("/proc").glob("[0-9]*"):
        if int(path.name) == os.getpid():
            continue
        try:
            args = (path / "cmdline").read_bytes().split(b"\0")
            kinds = [
                kind
                for kind, needle in (
                    ("agent", b"qb_browser_agent.mjs"),
                    ("test_agent", b"p5q_cli_agent.mjs"),
                    ("chromium", b"ms-playwright/chromium"),
                    ("profile", b"p5q-browser-"),
                )
                if any(needle in arg for arg in args)
            ]
            if kinds:
                cleanup["processes"].append(dict(pid=int(path.name), kinds=kinds))
        except (FileNotFoundError, ProcessLookupError):
            pass
        except PermissionError:
            cleanup["scan_errors"].append(int(path.name))
    assert all(not values for values in cleanup.values())
    source = (REPO / "tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs").read_bytes()
    prefix = hashlib.sha256(source.split(b"export class Agent {")[0]).hexdigest()
    assert prefix == "40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16"
    gates = []
    for argv in [
        [".venv/bin/ruff", "check", str(HERE / "run_live.py"), str(Path(__file__))],
        [
            ".venv/bin/python",
            "docs/clang-fix-campaign/tools/check_design_doc.py",
            "docs/clang-fix-campaign/design.md",
        ],
        ["git", "diff", "--check", "--", str(HERE), str(HERE.parent.parent / "progress.md")],
        ["git", "diff", "--cached", "--check"],
        ["git", "diff", "--exit-code", "1b718c8", "--", "tizen-ci-triage/scripts/ci_triage"],
    ]:
        started = PREP.stamp()
        result = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
        gates.append(
            dict(
                argv=argv,
                started=started,
                ended=PREP.stamp(),
                exit=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        )
        assert result.returncode == 0, result.stdout
    files = []
    checker = PageRedactor()
    for path in sorted(live.rglob("*")):
        if not path.is_file() or path.name == "validation.json":
            continue
        raw = path.read_bytes()
        checker.check_bytes(raw)
        if path.suffix == ".json":
            _check_diagnostic_strings(json.loads(raw), checker)
        if path.suffix == ".jsonl":
            for line in raw.splitlines():
                _check_diagnostic_strings(json.loads(line), checker)
        files.append(dict(path=str(path.relative_to(live)), sha256=PREP.digest(path)))
    write(
        live / "validation.json",
        dict(
            at=PREP.stamp(),
            immutable=PREP.immutable(),
            c6_tree_unchanged=True,
            db_sha256=PREP.digest(ROOT / "state.db"),
            status=status,
            protected_prefix_sha256=prefix,
            cleanup=cleanup,
            gates=gates,
            files=files,
            redaction_failed=0,
            live_outcome="STOPPED_READ_FAILURE",
            new_live_operations=0,
        ),
    )
    print(json.dumps(dict(audit="PASS", files=len(files), gates=len(gates))))


if __name__ == "__main__":
    main()
