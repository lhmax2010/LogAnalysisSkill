"""Mechanical boundary checks and test-group counts for this delivery."""

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

root = Path.cwd()
directory = Path(__file__).resolve().parent
agent_path = "tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs"
old = subprocess.check_output(["git", "show", "7f3c60e:" + agent_path], text=True)
new = (root / agent_path).read_text()
checks = {}
for name, start, end in (
    ("Policy", "export class Policy", "export class FrameOwnership"),
    ("installGuards", "export async function installGuards", "export function pathShape"),
):
    previous = old[old.index(start) : old.index(end)]
    current = new[new.index(start) : new.index(end)]
    assert previous == current, name
    checks[name] = dict(unchanged=True, sha256=hashlib.sha256(current.encode()).hexdigest())
frozen = root / "docs/clang-fix-campaign/p5q-qb-trigger-design-v1.5-FROZEN.md"
digest = hashlib.sha256(frozen.read_bytes()).hexdigest()
assert digest == "f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c"
checks["frozen_sha256"] = digest
for path in (
    "tizen-ci-triage/scripts/ci_triage/qb_browser.py",
    "docs/clang-fix-campaign/design.md",
):
    assert (root / path).read_bytes() == subprocess.check_output(["git", "show", "7f3c60e:" + path])
checks["driver_and_design_unchanged"] = True

preconditions = {
    "test_idempotency_every_cell",
    "test_precondition_rejections",
    "test_three_units_middle_fill_failure",
    "test_transport_isolation",
    "test_wrong_remote_sha_after_fill",
    "test_sandbox_lock_rejects_before_agent",
    "test_selection_matches_unit_without_held",
    "test_invalid_units_file_before_agent",
    "test_cli_missing_arguments",
    "test_correct_sha_only_in_other_repository_rejected",
}
configuration = {
    "test_changed_config_rejected_before_agent",
    "test_invalid_config_never_starts_agent",
    "test_project_not_ready",
    "test_two_branches_freeze_separately_and_reuse",
    "test_new_campaign_changed_config",
}
counts = Counter()
cases = []
for case in ET.parse(directory / "focused.xml").iter("testcase"):
    assert not list(case), case.attrib
    if case.attrib["classname"].endswith("test_qb_trigger"):
        name = case.attrib["name"]
        function = name.split("[")[0]
        group = (
            "触发前置与幂等"
            if function in preconditions
            else "参数冻结与配置"
            if function in configuration
            else "凭据与脱敏"
            if function == "test_sensitive_agent_page_never_written"
            else "填表与提交"
        )
        counts[group] += 1
        cases.append(dict(group=group, nodeid="tests/unit/test_qb_trigger.py::" + name))
checks["c3_group_counts"] = dict(counts)
checks["c3_total"] = len(cases)
checks["focused_total"] = sum(1 for _ in ET.parse(directory / "focused.xml").iter("testcase"))
checks["cases"] = cases
print(json.dumps(checks, ensure_ascii=False, indent=2))
