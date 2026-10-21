"""Verify archived outputs, immutable inputs and JUnit totals without live I/O."""

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from ci_triage.qb_browser import _check_diagnostic_strings
from ci_triage.qb_redact import EvidenceRedactionError, PageRedactor
from run_checks import ROOT, audit

HERE = Path(__file__).resolve().parent


def main():
    records = []
    redactor = PageRedactor()
    for path in sorted(HERE.rglob("*")):
        if not path.is_file() or path.name == "delivery-audit.json" or "__pycache__" in path.parts:
            continue
        raw = path.read_bytes()
        try:
            redactor.check_bytes(raw)
        except EvidenceRedactionError:
            raise RuntimeError(f"REDACTION_FAILED file={path.relative_to(HERE)}") from None
        if path.suffix == ".json":
            _check_diagnostic_strings(json.loads(raw), redactor)
        elif path.suffix == ".jsonl":
            for line in raw.decode().splitlines():
                _check_diagnostic_strings(json.loads(line), redactor)
        elif path.suffix == ".log":
            for line in raw.decode().splitlines():
                if line.startswith("{") and line.endswith("}"):
                    _check_diagnostic_strings(json.loads(line), redactor)
        records.append(
            dict(
                file=str(path.relative_to(HERE)),
                bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest(),
                check="PASS",
            )
        )
    suites = []
    indexed = {}
    for name in ("full-final", "wait-boundaries-final"):
        tree = ET.parse(HERE / name / "junit.xml")
        for suite in tree.findall("testsuite"):
            suites.append(dict(run=name, **suite.attrib))
        for case in tree.findall(".//testcase"):
            key = (case.attrib["classname"], case.attrib["name"])
            assert key not in indexed, key
            indexed[key] = case
    collected = set()
    for line in (HERE / "collection-final/output.log").read_text().splitlines():
        if not line.startswith("tests/") or "::" not in line:
            continue
        file, *parts = line.split("::")
        classname = ".".join([file.removesuffix(".py").replace("/", "."), *parts[:-1]])
        collected.add((classname, parts[-1]))
    assert collected == set(indexed), (collected - set(indexed), set(indexed) - collected)
    cases = list(indexed.values())
    counts = Counter(case.attrib["classname"] for case in cases)
    failed = sum(
        case.find("failure") is not None or case.find("error") is not None for case in cases
    )
    skipped = sum(case.find("skipped") is not None for case in cases)
    assert failed == 0
    whitespace = subprocess.run(
        ["git", "diff", "--cached", "--check"], cwd=ROOT, capture_output=True, text=True
    )
    issues = [line for line in whitespace.stdout.splitlines() if ": trailing whitespace." in line]
    assert whitespace.returncode in {0, 2}
    assert len(whitespace.stdout.splitlines()) == len(issues) * 2
    assert all(
        "/continuation/" in line and "/qb_evidence/" in line and ".html:" in line for line in issues
    )
    result = dict(
        immutable_inputs=audit(),
        suites=suites,
        total=len(cases),
        passed=len(cases) - skipped - failed,
        failed=failed,
        skipped=skipped,
        current_collection_exactly_covered=True,
        preserved_html_whitespace=dict(exit=whitespace.returncode, count=len(issues), files=issues),
        groups=dict(sorted(counts.items())),
        files=records,
        redaction_passed=len(records),
        redaction_failed=0,
    )
    (HERE / "delivery-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps({key: value for key, value in result.items() if key not in {"files", "groups"}})
    )


if __name__ == "__main__":
    main()
