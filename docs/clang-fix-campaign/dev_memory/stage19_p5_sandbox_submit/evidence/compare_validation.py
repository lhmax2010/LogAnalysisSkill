"""Compare P5 validation with its fixed baseline, without resetting expectations."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


def outcomes(path: Path) -> dict[str, str]:
    result = {}
    for case in ET.parse(path).iter("testcase"):
        name = case.attrib["classname"] + "::" + case.attrib["name"]
        assert name not in result, name
        result[name] = next(
            (tag for tag in ("failure", "error", "skipped") if case.find(tag) is not None),
            "passed",
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("current", type=Path)
    parser.add_argument("clean_tree", type=Path)
    args = parser.parse_args()
    baseline = args.current.parent / "baseline"
    before = json.loads((baseline / "commands.json").read_text())["results"]
    after = json.loads((args.current / "commands.json").read_text())["results"]
    before_exits = {item["name"]: item["exit"] for item in before}
    after_exits = {item["name"]: item["exit"] for item in after}
    assert before_exits.keys() == after_exits.keys()
    exit_changes = {
        name: [code, after_exits[name]]
        for name, code in before_exits.items() if after_exits[name] != code
    }
    old = outcomes(baseline / "pytest.xml")
    new = outcomes(args.current / "pytest.xml")
    missing = sorted(old.keys() - new.keys())
    changed = {name: [value, new[name]] for name, value in old.items()
               if name in new and new[name] != value}
    added = sorted(new.keys() - old.keys())
    source_hashes = {}
    paths = subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD", "--", "tests/", ":(glob)tizen-*/scripts/**"],
        text=True,
    ).splitlines()
    for name in paths:
        raw = Path(name).read_bytes()
        assert raw == (args.clean_tree / name).read_bytes(), name
        source_hashes[name] = hashlib.sha256(raw).hexdigest()
    result = {
        "baseline_commit": "cd7f8dd", "command_count": len(after),
        "exit_changes": exit_changes, "baseline_tests": dict(Counter(old.values())),
        "current_tests": dict(Counter(new.values())), "missing_nodeids": missing,
        "changed_outcomes": changed, "added_nodeids": added,
        "tested_source_sha256": source_hashes,
    }
    output = args.current.with_name(args.current.name + "-comparison.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items()
                      if key not in {"added_nodeids", "tested_source_sha256"}}, indent=2))
    print(f"added_nodeids={len(added)}; identical_tested_sources={len(source_hashes)}")
    assert not exit_changes and not missing and not changed
    assert all(new[name] == "passed" for name in added)
    print("baseline_comparison=PASS")


if __name__ == "__main__":
    main()
