"""Reconstruct C7 interruption attribution from archived, read-only evidence."""

import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from ci_triage.qb_redact import PageRedactor

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parents[1]
C7 = EVIDENCE / "C7/continuation"


def main():
    cases = ET.parse(C7 / "full-01/junit.xml").getroot().findall(".//testcase")
    names = [case.get("name") for case in cases if case.get("name")]
    collection = [
        line
        for line in (C7 / "collection-final/output.log").read_text().splitlines()
        if line.startswith("tests/") and "::" in line
    ]
    assert len(names) == 680
    assert names == [nodeid.split("::")[-1] for nodeid in collection[:680]]
    command = json.loads((C7 / "full-01/command.json").read_text())
    residue = json.loads((EVIDENCE / "C8/preparation/orphan-cleanup.json").read_text())
    result = {
        "completed_prefix": len(names),
        "collection_prefix_matches": True,
        "next_nodeid": collection[680],
        "full_run_exit": command["exit"],
        "full_run_end": command["ended"],
        "orphan_mtime": residue["mtime"],
        "mtime_after_end_seconds": (
            datetime.fromisoformat(residue["mtime"]) - datetime.fromisoformat(command["ended"])
        ).total_seconds(),
        "historical_signal_recipients": "NOT_COLLECTED",
        "historical_creator_pid": "NOT_COLLECTED",
        "source_attribution": "STRONG_TEMPORAL_AND_COLLECTION_MATCH_NOT_PID_PROOF",
        "sources": [],
    }
    for path in (
        C7 / "full-01/junit.xml",
        C7 / "full-01/command.json",
        C7 / "collection-final/output.log",
        C7 / "coverage.md",
        EVIDENCE / "C8/preparation/orphan-cleanup.json",
    ):
        result["sources"].append(
            {
                "path": str(path.relative_to(EVIDENCE)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    checker = PageRedactor()
    checker.check_bytes(raw)
    path = HERE / "history.json"
    with path.open("xb") as stream:
        stream.write(raw)
    checker.check_written(path)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
