"""Mechanical scope, gate, timing and immutable-input checks for the offline repair."""

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    path = "tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs"
    old = subprocess.check_output(["git", "show", f"243df59:{path}"], cwd=ROOT)
    new = (ROOT / path).read_bytes()
    marker = b"export class Agent {"
    assert old.count(marker) == new.count(marker) == 1
    assert old.split(marker)[0] == new.split(marker)[0]
    untouched = {}
    for path in (
        "tizen-ci-triage/scripts/ci_triage/qb_trigger.py",
        "tizen-ci-triage/scripts/ci_triage/qb_result_fetch.py",
        "docs/clang-fix-campaign/p5q-qb-trigger-design-v1.5-FROZEN.md",
        "docs/clang-fix-campaign/design.md",
    ):
        before = subprocess.check_output(["git", "show", f"243df59:{path}"], cwd=ROOT)
        assert before == (ROOT / path).read_bytes()
        untouched[path] = digest(before)
    db = Path("/home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db")
    db_hash = digest(db.read_bytes())
    assert db_hash == "08ed202e69a73a480e7282a198565f32adae8157a332804df4df970238eacd30"
    gates = {}
    for name in ("focused-01", "full", "mypy", "ruff-final", "lint-imports", "node-unit",
                 "design", "safety"):
        row = json.loads((HERE / name / "command.json").read_text())
        assert row["exit"] == 0, name
        assert row["input_hashes_before"] == row["input_hashes_after"], name
        gates[name] = {key: row[key] for key in ("exit", "seconds")}
    suite = ET.parse(HERE / "full/pytest.xml").getroot().find("testsuite")
    counts = {key: int(suite.attrib[key]) for key in ("tests", "failures", "errors", "skipped")}
    counts["passed"] = counts["tests"] - sum(
        counts[key] for key in ("failures", "errors", "skipped")
    )
    timing = []
    for name in ("focused-01", "full"):
        rows = json.loads((HERE / name / "cli-artifacts/build/commands.json").read_text())
        timing.extend(
            {"run": name, "command": row["argv"][3],
             "close_to_cli_exit_seconds": row["close_to_cli_exit_seconds"]} for row in rows
        )
    secrets = (b"synthetic_private_account", b"synthetic_private_password",
               b"synthetic_private_session", b"synthetic_query_value")
    scanned = []
    for directory in (HERE / "focused-01/artifacts", HERE / "full/artifacts"):
        for file in directory.rglob("*.json"):
            assert not any(secret in file.read_bytes() for secret in secrets), file
            scanned.append(str(file.relative_to(HERE)))
    report = {
        "baseline": "243df59", "policy_and_install_guards_prefix_unchanged": True,
        "security_prefix_sha256": digest(new.split(marker)[0]), "untouched": untouched,
        "dedicated_state_db_sha256": db_hash, "gates": gates, "pytest": counts,
        "close_timings": timing, "login_evidence_no_synthetic_secrets": scanned,
    }
    (HERE / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
