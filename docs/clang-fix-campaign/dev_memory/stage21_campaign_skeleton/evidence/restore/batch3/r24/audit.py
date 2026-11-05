"""Read-only source, collection and artifact audit for the offline restoration."""

from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".git").exists())
OLD = HERE.parents[1] / "redaction-16"
AGENT = "tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs"
RUN = HERE / "accepted"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    old = json.loads((OLD / "protected-final.json").read_text())
    protected = {}
    for path, record in old.items():
        if isinstance(record, dict):
            raw = (ROOT / path).read_bytes()
            protected[path] = {"sha256": digest(raw), "before": record["sha256"],
                               "unchanged": digest(raw) == record["sha256"]}
    for path in (".importlinter", "tizen-campaign-intake/scripts/tizen_campaign_intake/intake.py"):
        before = subprocess.check_output(["git", "show", f"4936377:{path}"], cwd=ROOT)
        protected[path] = {"sha256": digest((ROOT / path).read_bytes()),
                           "unchanged": (ROOT / path).read_bytes() == before}
    agent = (ROOT / AGENT).read_bytes()
    token = b"export class Agent {"
    protected["agent_prefix_sha256"] = digest(agent[:agent.index(token) + len(token)])
    protected["agent_prefix_before"] = old["agent_prefix_sha256"]
    protected["agent_mtime"] = (ROOT / AGENT).stat().st_mtime
    (HERE / "protected-final.json").write_text(json.dumps(protected, indent=2) + "\n")
    baseline = ET.parse(OLD / "full/pytest.xml").getroot()
    before = {test.attrib["classname"].replace(".", "/") + ".py::" + test.attrib["name"]
              for test in baseline.iter("testcase")}
    after = {line for line in (RUN / "collect/stdout.log").read_text().splitlines()
             if line.startswith("tests/") and "::" in line}
    comparison = dict(before=len(before), after=len(after), removed=sorted(before - after),
                      added=sorted(after - before))
    (HERE / "nodeids.json").write_text(json.dumps(comparison, indent=2) + "\n")
    assert not comparison["removed"]
    expected = {AGENT, "tizen-qb-verify/scripts/tizen_qb_verify/qb_browser.py"}
    assert all(row["unchanged"] for path, row in protected.items()
               if isinstance(row, dict) and path not in expected)
    full = json.loads((RUN / "full/command.json").read_text())
    inputs = json.loads((RUN / "inputs.json").read_text())
    changes = {p: {"before_focused": h, "full_tree": digest((ROOT / p).read_bytes()),
                   "mtime": (ROOT / p).stat().st_mtime}
               for p, h in inputs.items() if digest((ROOT / p).read_bytes()) != h}
    started = datetime.datetime.fromisoformat(full["started_utc"]).timestamp()
    assert not changes
    assert all(row["mtime"] < started for row in changes.values())
    (RUN / "source-proof.json").write_text(json.dumps({
        "full_started_utc": full["started_utc"], "pre_full_changes": changes,
        "note": "Accepted tree is unchanged from focused through full gates.",
        "all_other_source_hashes_unchanged": True,
    }, indent=2) + "\n")
    print(json.dumps({"protected": "PASS", "nodeids": comparison}))


if __name__ == "__main__":
    main()
