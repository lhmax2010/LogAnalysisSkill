"""Summarize measured C5a evidence; no production or network calls."""

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[6]
FINAL = HERE / "full-02"


def tests(path):
    cases = ET.parse(path).getroot().findall(".//testcase")
    counts = dict(passed=0, failed=0, skipped=0)
    for case in cases:
        outcome = (
            "skipped"
            if case.find("skipped") is not None
            else (
                "failed"
                if case.find("failure") is not None or case.find("error") is not None
                else "passed"
            )
        )
        counts[outcome] += 1
    return counts, {case.attrib["classname"] + "::" + case.attrib["name"] for case in cases}


def main():
    counts, current = tests(FINAL / "pytest.xml")
    _, previous = tests(HERE.parent / "C4/completion/pytest.xml")
    assert counts["failed"] == 0
    assert not previous - current
    digest = hashlib.sha256(
        (ROOT / "docs/clang-fix-campaign/p5q-qb-trigger-design-v1.5-FROZEN.md").read_bytes()
    ).hexdigest()
    assert digest == "f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c"
    changed = subprocess.check_output(
        [
            "git",
            "diff",
            "39e4bde",
            "--name-only",
            "--",
            "tizen-ci-triage/scripts/ci_triage",
            "docs/clang-fix-campaign/design.md",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    assert changed == []
    artifacts = FINAL / "artifacts"
    modes = {}
    for mode in ("build", "error-created", "error-no-build", "no-navigation"):
        received = json.loads((artifacts / mode / "server-requests.json").read_text())
        assert len(received["submissions"]) == 1
        assert not received["errors"]
        assert not any(
            any(word in row["path"] for word in ("ajaxRefresh", "/rest/", "promote", "/log"))
            for row in received["received"]
        )
        modes[mode] = dict(
            requests=len(received["received"]), submissions=1, builds=received["builds"]
        )
    rehearsal = json.loads((artifacts / "tools/rehearsal/run.json").read_text())
    assert rehearsal["release_state"] == "not_released"
    assert rehearsal["form_action_releases"] == 0
    assert len(rehearsal["registrations"]) == 12
    assert all(row["allowed"] == 1 and row["denied"] == 0 for row in rehearsal["registrations"])
    assert all(row["outside_identity_count"] == 0 for row in rehearsal["page_identity_counts"])
    log = (FINAL / "pytest.log").read_text()
    safety = [
        json.loads(line[line.index('{"group":') :])
        for line in log.splitlines()
        if '{"group":' in line
    ]
    assert len(safety) == 4 and all(row["ok"] for row in safety)
    (HERE / "safety.json").write_text(json.dumps(safety, indent=2) + "\n")
    result = dict(
        pytest=counts,
        previous_collection=len(previous),
        current_collection=len(current),
        added=sorted(current - previous),
        removed=sorted(previous - current),
        frozen_sha256=digest,
        production_and_design_changes=changed,
        full_chain=modes,
        rehearsal=dict(fields=12, action_releases=0),
        safety_passed=len(safety),
    )
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
