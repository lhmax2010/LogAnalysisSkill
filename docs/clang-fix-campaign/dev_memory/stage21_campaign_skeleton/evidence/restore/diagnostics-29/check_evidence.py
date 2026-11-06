"""Read-only integrity and archive checks; never print historic identities."""

from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from tizen_qb_verify.qb_redact import SessionPageRedactor

HERE = Path(__file__).resolve().parent
CAPTURE = HERE.parent / "discovery-capture"
AGENT = "tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs"
STAGE = "PREFIX"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    global STAGE
    before = subprocess.check_output(["git", "show", f"b7a55d8:{AGENT}"])
    after = Path(AGENT).read_bytes()
    marker = b"export class Agent {"
    assert before.split(marker)[0] == after.split(marker)[0]
    # The original session identity is read from the already-existing local
    # history only into memory, never copied into a fixture or command output.
    STAGE = "HISTORY"
    archive = str(CAPTURE.relative_to(Path.cwd()) / "live-02/02.response.html")
    old = subprocess.check_output(["git", "show", f"57cac6e:{archive}"]).decode()
    spec = importlib.util.spec_from_file_location("archive_cells", CAPTURE / "sanitize_archives.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cells = module.Cells()
    cells.feed(old.split("</thea&lt;USER&gt;", 1)[1].split("</table>", 1)[0])
    assert len(cells.cells) == 7
    redactor = SessionPageRedactor()
    redactor.remember_session_identity(cells.cells[4].strip())
    assert redactor.identities
    pattern = re.compile(
        r"(?<![A-Za-z0-9_])(?:"
        + "|".join(re.escape(value) for value in redactor.identities)
        + r")(?![A-Za-z0-9_])"
    )
    STAGE = "ARCHIVES"
    files = [f"live-02/{n:02d}.response.html" for n in range(2, 7)] + ["live-04/02.response.html"]
    rows = []
    for name in files:
        raw = (CAPTURE / name).read_bytes()
        redactor.check_bytes(raw)
        rows.append({"file": name, "sha256": digest(raw), "identity_remaining": 0})
    result = {
        "agent_before_sha256": digest(before),
        "agent_after_sha256": digest(after),
        "prefix_before_sha256": digest(before.split(marker)[0] + marker),
        "prefix_after_sha256": digest(after.split(marker)[0] + marker),
        "prefix_equal": True,
        "archive_checks": rows,
        "historic_identities_written": False,
    }
    STAGE = "NODEIDS"
    baseline = HERE.parent / "batch3/r24/accepted/collect/stdout.log"

    def nodes(path):
        return {
            pattern.sub("[REDACTED_IDENTITY]", s.strip())
            for s in path.read_text().splitlines()
            if s.startswith("tests/") and "::" in s
        }

    old_nodes, new_nodes = nodes(baseline), nodes(HERE / "collect/stdout.txt")
    result["nodeids"] = {
        "before": len(old_nodes),
        "after": len(new_nodes),
        "removed": sorted(old_nodes - new_nodes),
        "added": sorted(new_nodes - old_nodes),
    }
    assert not old_nodes - new_nodes
    STAGE = "FULL_RESULT"
    suite = ET.parse(HERE / "full/pytest.xml").getroot().find("testsuite")
    result["full_pytest"] = dict(suite.attrib)
    result["full_failures"] = [
        {"classname": case.attrib["classname"], "name": case.attrib["name"]}
        for case in suite.findall("testcase")
        if case.find("failure") is not None or case.find("error") is not None
    ]
    STAGE = "SOURCE_HASHES"
    hashes = json.loads((HERE / "gate-inputs.json").read_text())
    changed = [
        path for path, expected in hashes.items() if digest(Path(path).read_bytes()) != expected
    ]
    result["gate_source_changes"] = changed
    assert not changed
    STAGE = "RETRIES"
    retries = []
    for number in range(1, 3):
        directory = HERE / f"retry-c5a-build-{number}"
        command = json.loads((directory / "command.json").read_text())
        retry_suite = ET.parse(directory / "pytest.xml").getroot().find("testsuite")
        retries.append(
            {
                "run": number,
                "exit": command["exit_code"],
                "suite": dict(retry_suite.attrib),
                "before_loadavg": command["before"]["loadavg"],
                "after_loadavg": command["after"]["loadavg"],
            }
        )
    result["timing_retries"] = retries
    result["third_retry"] = "NOT_RUN_STOP_AFTER_SECOND_FAILURE"
    result["gate_accepted"] = False
    STAGE = "PROFILES"
    profiles = [p.name for p in Path("/dev/shm").glob("p5q-browser-*")]
    result["remaining_profiles"] = profiles
    result["profiles_clean"] = not profiles
    result["profile_cleanup"] = "NOT_PERFORMED_STOPPED"
    processes = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            args = (entry / "cmdline").read_bytes().split(b"\0")
            if not any(b"--user-data-dir=/dev/shm/p5q-browser-" in arg for arg in args):
                continue
            processes.append({"pid": int(entry.name), "comm": (entry / "comm").read_text().strip()})
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    result["profile_processes"] = processes
    STAGE = "NEW_EVIDENCE_SCAN"
    scanned = 0
    identity_hits = []
    credential_check_rejections = []
    for path in HERE.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        raw = path.read_bytes()
        if pattern.search(html.unescape(raw.decode("utf-8"))):
            identity_hits.append(str(path.relative_to(HERE)))
        try:
            redactor.check_bytes(raw)
        except Exception:
            credential_check_rejections.append(str(path.relative_to(HERE)))
        scanned += 1
    result["evidence_files_scanned"] = scanned
    result["evidence_identity_hit_files"] = identity_hits
    result["page_checker_rejected_files"] = credential_check_rejections
    (HERE / "integrity-and-archive-scan.json").write_text(json.dumps(result, indent=2) + "\n")
    assert not identity_hits
    print(
        json.dumps(
            {
                "ok": True,
                "archives": len(rows),
                "identity_remaining": 0,
                "page_checker_rejected_files": credential_check_rejections,
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(
            json.dumps(
                {
                    "ok": False,
                    "code": "EVIDENCE_CHECK_FAILED",
                    "stage": STAGE,
                    "exception_class": type(error).__name__,
                }
            )
        )
        raise SystemExit(4) from None
