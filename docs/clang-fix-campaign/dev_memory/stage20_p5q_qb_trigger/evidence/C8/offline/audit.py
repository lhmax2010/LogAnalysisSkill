"""Check C8 gate archives; hash synthetic parametrizations before publication."""

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from ci_triage.qb_browser import _check_diagnostic_strings
from ci_triage.qb_redact import PageRedactor
from run_checks import ROOT, audit

HERE = Path(__file__).resolve().parent


def safe_name(name):
    if "[" in name and not name.split("[", 1)[1].startswith("sha256="):
        plain, parameters = name.split("[", 1)
        return plain + "[sha256=" + hashlib.sha256(parameters.encode()).hexdigest() + "]"
    return name


def main():
    for path in HERE.glob("*/junit.xml"):
        tree = ET.parse(path)
        for case in tree.findall(".//testcase"):
            name = case.attrib.get("name", "")
            case.set("name", safe_name(name))
        tree.write(path, encoding="utf-8", xml_declaration=True)
    collected = set()
    collection = HERE / "collection/output.log"
    lines = collection.read_text().splitlines()
    for i, line in enumerate(lines):
        if line.startswith("tests/") and "::" in line:
            file, *parts = line.split("::")
            parts[-1] = safe_name(parts[-1])
            lines[i] = "::".join([file, *parts])
            classname = ".".join([file.removesuffix(".py").replace("/", "."), *parts[:-1]])
            collected.add((classname, parts[-1]))
    collection.write_text("\n".join(lines) + "\n")
    redactor = PageRedactor()
    files = []
    for path in sorted(HERE.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.name == "audit.json":
            continue
        raw = path.read_bytes()
        redactor.check_bytes(raw)
        if path.suffix == ".json":
            _check_diagnostic_strings(json.loads(raw), redactor)
        files.append(dict(file=str(path.relative_to(HERE)), sha256=hashlib.sha256(raw).hexdigest()))
    tree = ET.parse(HERE / "full/junit.xml")
    cases = tree.findall(".//testcase")
    assert collected == {(case.attrib["classname"], case.attrib["name"]) for case in cases}
    failed = sum(
        case.find("failure") is not None or case.find("error") is not None for case in cases
    )
    skipped = sum(case.find("skipped") is not None for case in cases)
    assert failed == 0
    modes = {}
    for path in sorted((HERE / "full/cli-artifacts").glob("*/commands.json")):
        rows = json.loads(path.read_text())
        modes[path.parent.name] = dict(
            exits=[row["exit"] for row in rows],
            close_seconds=[row["close_to_cli_exit_seconds"] for row in rows],
            source=str(path.relative_to(HERE)),
        )
    assert len(modes) == 6
    whitespace = subprocess.run(
        ["git", "diff", "--cached", "--check"], cwd=ROOT, capture_output=True, text=True
    )
    issues = [line for line in whitespace.stdout.splitlines() if ": trailing whitespace." in line]
    assert whitespace.returncode in {0, 2}
    assert len(whitespace.stdout.splitlines()) == 2 * len(issues)
    assert all(
        "/C8/offline/" in line and "/qb_evidence/" in line and ".html:" in line for line in issues
    )
    summary = dict(
        inputs=audit(),
        total=len(cases),
        passed=len(cases) - failed - skipped,
        failed=failed,
        skipped=skipped,
        groups=dict(Counter(case.attrib["classname"] for case in cases)),
        integrations=modes,
        raw_html_whitespace=dict(exit=whitespace.returncode, locations=issues),
        files=files,
        redaction_checked=len(files),
    )
    (HERE / "audit.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps({key: value for key, value in summary.items() if key not in {"files", "groups"}})
    )


if __name__ == "__main__":
    main()
