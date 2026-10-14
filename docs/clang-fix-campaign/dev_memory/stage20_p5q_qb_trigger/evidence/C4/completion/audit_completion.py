"""Check immutable boundaries and derive C4 test counts from actual JUnit results."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
BASE = "ec3be749ab7681c9ff45631c6ab58a25c336c070"


def baseline(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"])


def main() -> None:
    checks = {}
    for path in (
        "docs/clang-fix-campaign/p5q-qb-trigger-design-v1.5-FROZEN.md",
        "docs/clang-fix-campaign/design.md",
        "tizen-ci-triage/scripts/ci_triage/qb_trigger.py",
        "tizen-ci-triage/scripts/ci_triage/qb_redact.py",
        "tizen-ci-triage/scripts/ci_triage/campaign_state.py",
    ):
        raw = (ROOT / path).read_bytes()
        assert raw == baseline(path), path
        checks[path] = dict(unchanged=True, sha256=hashlib.sha256(raw).hexdigest())
    agent = "tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs"
    old, new = baseline(agent).decode(), (ROOT / agent).read_text()
    for name, start, end in (
        ("Policy", "export class Policy", "export class FrameOwnership"),
        ("installGuards", "export async function installGuards", "export function pathShape"),
    ):
        previous, current = (
            old[old.index(start) : old.index(end)],
            new[new.index(start) : new.index(end)],
        )
        assert previous == current, name
        checks[name] = dict(unchanged=True, sha256=hashlib.sha256(current.encode()).hexdigest())

    privacy = {
        "test_redacted_identity_keeps_business_fields",
        "test_write_after_check_failure_removes_evidence",
        "test_read_diagnostic_is_archived",
        "test_agent_sensitive_keys_never_archived",
        "test_registered_user_residue_rejected",
        "test_diagnostic_io_preserves_original_but_redaction_stops",
    }
    transactions = {
        "test_lock_held_network_outside_transaction",
        "test_write_point_rollback",
        "test_transaction_rechecks_and_removes_file",
        "test_result_publication_fsync_order",
        "test_publication_failure_removes_temp_and_final",
        "test_manual_binding_transaction_recheck",
    }
    cases = []
    counts: Counter[str] = Counter()
    for case in ET.parse(HERE / "focused.xml").iter("testcase"):
        assert not any(case.find(tag) is not None for tag in ("failure", "error", "skipped"))
        module = case.attrib["classname"].split(".")[-1]
        name = case.attrib["name"]
        function = name.split("[")[0]
        if module == "test_qb_result_fetch":
            group = (
                "凭据与脱敏"
                if function in privacy
                else "事务与原语"
                if function in transactions
                else "读取与落库"
            )
        elif module == "test_qb_trigger":
            group = "sha256远端残余"
        else:
            group = "Python驱动(含既有回归)"
        path = f"tests/unit/{module}.py"
        definitions = {
            n.name: n.lineno
            for n in ast.parse((ROOT / path).read_text()).body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        counts[group] += 1
        cases.append(
            dict(group=group, nodeid=path + "::" + name, location=f"{path}:{definitions[function]}")
        )
    checks["groups"] = dict(counts)
    checks["cases"] = cases
    previous_log = (HERE.parents[1] / "C3/completion/pytest.log").read_text()
    current_log = (HERE / "pytest.log").read_text()
    pattern = r"^(tests/.+?) (?:PASSED|SKIPPED|FAILED)(?:\s|$)"
    before, after = (set(re.findall(pattern, text, re.M)) for text in (previous_log, current_log))
    assert before and before <= after
    checks["collection"] = dict(
        before=len(before),
        after=len(after),
        removed=sorted(before - after),
        added=sorted(after - before),
    )
    checks["full_suite"] = ET.parse(HERE / "pytest.xml").find("testsuite").attrib
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
