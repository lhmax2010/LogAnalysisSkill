"""Compare recorded gate exits and JUnit outcomes without rerunning any producer."""

from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


def outcomes(path: Path) -> dict[str, str]:
    cases = list(ET.parse(path).iter("testcase"))
    result = {
        f"{case.attrib['classname']}::{case.attrib['name']}": next(
            (tag for tag in ("failure", "error", "skipped") if case.find(tag) is not None),
            "passed",
        ) for case in cases
    }
    assert len(result) == len(cases)
    return result


def main() -> None:
    baseline, current, tree = (Path(value) for value in sys.argv[1:4])
    exits = [
        {row["name"]: row["exit"]
         for row in json.loads((p / "commands.json").read_text())["results"]}
        for p in (baseline, current)
    ]
    assert exits[0].keys() == exits[1].keys()
    before, after = (outcomes(p / "pytest.xml") for p in (baseline, current))
    report = {
        "baseline_commit": "4a6873d", "command_count": len(exits[0]),
        "exit_changes": {name: [value, exits[1][name]] for name, value in exits[0].items()
                         if value != exits[1][name]},
        "baseline_tests": dict(Counter(before.values())),
        "current_tests": dict(Counter(after.values())),
        "missing_nodeids": sorted(before.keys() - after.keys()),
        "changed_outcomes": [key for key in before.keys() & after.keys()
                             if before[key] != after[key]],
        "added_nodeids": sorted(after.keys() - before.keys()),
        "tested_files": {
            name: hashlib.sha256((tree / name).read_bytes()).hexdigest() for name in sys.argv[4:]
        },
    }
    print(json.dumps(report, indent=2))
    assert not report["exit_changes"]
    assert not report["missing_nodeids"]
    assert not report["changed_outcomes"]
    assert set(after.values()) <= {"passed", "skipped"}


if __name__ == "__main__":
    main()
