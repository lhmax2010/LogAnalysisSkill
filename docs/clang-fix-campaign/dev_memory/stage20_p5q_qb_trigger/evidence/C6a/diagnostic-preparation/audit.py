"""Check diagnostic-only production diff and summarize this run's gate evidence."""

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from ci_triage.qb_redact import PageRedactor

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[7]
AGENT = "tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs"


def section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


def main():
    previous = subprocess.check_output(["git", "show", "66485ca:" + AGENT], cwd=ROOT, text=True)
    current = (ROOT / AGENT).read_text()
    policy_same = section(
        previous, "export class Policy", "export class FrameOwnership"
    ) == section(current, "export class Policy", "export class FrameOwnership")
    before = section(previous, "export async function installGuards", "export function pathShape")
    after = section(current, "export async function installGuards", "export function pathShape")
    # Reverse only the approved diagnostic annotations; all decisions must match.
    annotations = {
        "(promise, category = 'FETCH_CONTINUE_FAILED')": "(promise)",
        "promise.catch(() => onStop(category))": "promise.catch(onStop)",
        "onStop('ADAPT_FAILED')": "onStop()",
        "onStop('NEW_PAGE')": "onStop()",
        "onStop('WORKER_NOT_PAUSED')": "onStop()",
        "onStop('CLOSE_TARGET_FAILED')": "onStop()",
        "}), 'CLOSE_TARGET_FAILED');": "}));",
    }
    for added, old in annotations.items():
        assert added in after
        after = after.replace(added, old)
    assert policy_same and before == after
    suite = ET.parse(HERE / "full-02/pytest.xml").getroot().find("testsuite")
    assert suite is not None
    assert suite.attrib["failures"] == suite.attrib["errors"] == "0"
    report = dict(
        baseline="66485ca",
        policy_byte_identical=policy_same,
        installGuards_identical_except_category_annotations=before == after,
        pytest=suite.attrib,
        production_files=subprocess.check_output(
            ["git", "diff", "66485ca", "--name-only", "--", "tizen-ci-triage/scripts/ci_triage"],
            cwd=ROOT,
            text=True,
        ).splitlines(),
        gates={},
    )
    for group in ("full-02", "tools-01", "safety-01", "ruff-01"):
        report["gates"][group] = json.loads((HERE / group / "commands.json").read_text())
        assert all(row["exit"] == 0 for row in report["gates"][group])
    for name, path in {
        "frozen_design": ROOT / "docs/clang-fix-campaign/p5q-qb-trigger-design-v1.5-FROZEN.md",
        "dedicated_db": Path("/home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db"),
    }.items():
        report[name + "_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    raw = (json.dumps(report, indent=2) + "\n").encode()
    checker = PageRedactor()
    checker.check_bytes(raw)
    (HERE / "audit.json").write_bytes(raw)
    checker.check_written(HERE / "audit.json")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
