"""Summarize completed tests and check evidence without exposing historical identities."""

import hashlib
import html
import importlib.util
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAPTURE = HERE.parent / "discovery-capture"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def suite(path):
    root = ET.parse(path).getroot()
    suites = list(root.iter("testsuite"))
    result = {
        key: sum(int(item.get(key, "0")) for item in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }
    result["passed"] = result["tests"] - result["failures"] - result["errors"] - result["skipped"]
    result["failures_list"] = [
        {"classname": case.get("classname"), "name": case.get("name")}
        for case in root.iter("testcase")
        if case.find("failure") is not None or case.find("error") is not None
    ]
    return result


def main():
    from tizen_qb_verify.qb_redact import SessionPageRedactor

    archive = str(CAPTURE.relative_to(Path.cwd()) / "live-02/02.response.html")
    old = subprocess.check_output(["git", "show", f"57cac6e:{archive}"]).decode()
    spec = importlib.util.spec_from_file_location("archive_cells", CAPTURE / "sanitize_archives.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cells = module.Cells()
    cells.feed(old.split("</thea&lt;USER&gt;", 1)[1].split("</table>", 1)[0])
    assert len(cells.cells) == 7
    redactor = SessionPageRedactor()
    redactor.remember_session_identity(cells.cells[4].strip())
    pattern = re.compile(
        r"(?<![A-Za-z0-9_])(?:"
        + "|".join(re.escape(value) for value in redactor.identities)
        + r")(?![A-Za-z0-9_])"
    )
    audit = []
    xml = HERE / "full/pytest.xml"
    raw = xml.read_bytes()
    root = ET.fromstring(raw)
    for tag in ("failure", "error"):
        for failure in root.iter(tag):
            assert not pattern.search(ET.tostring(failure, encoding="unicode"))
    cleaned, count = pattern.subn("[REDACTED_IDENTITY]", raw.decode())
    if count:
        xml.write_text(cleaned)
        audit.append(
            {
                "file": "full/pytest.xml",
                "count": count,
                "before_sha256": digest(raw),
                "after_sha256": digest(xml.read_bytes()),
                "failure_messages_changed": False,
            }
        )
    audit_path = HERE / "identifier-redaction.json"
    if audit:
        assert not audit_path.exists()
        audit_path.write_text(json.dumps(audit, indent=2) + "\n")
    snapshot = json.loads((HERE / "source-before.json").read_text())
    changed = [
        path for path, expected in snapshot.items() if digest(Path(path).read_bytes()) != expected
    ]
    cases = []
    for name in ("retry-1", "retry-2", "retry-3", "full"):
        folder = HERE / name
        command = json.loads((folder / "command.json").read_text())
        result = {
            "name": name,
            "exit": command["exit_code"],
            "suite": suite(folder / "pytest.xml"),
            "wait_seconds": command["wait_seconds"],
            "elapsed_seconds": command["elapsed_seconds"],
            "before": command["before"],
            "after": command["after"],
        }
        commands = folder / "c5a/build/commands.json"
        if commands.exists():
            result["close_seconds"] = [
                item.get("close_to_cli_exit_seconds") for item in json.loads(commands.read_text())
            ]
        cases.append(result)
    hit_files = []
    scanned = 0
    for path in HERE.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if pattern.search(html.unescape(path.read_text())):
            hit_files.append(str(path.relative_to(HERE)))
        scanned += 1
    result = {
        "cases": cases,
        "changed_sources": changed,
        "scanned_files": scanned,
        "identity_hit_files": hit_files,
        "profiles_remaining": [path.name for path in Path("/dev/shm").glob("p5q-browser-*")],
        "historic_identity_written": False,
    }
    (HERE / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    assert not changed and not hit_files
    print(
        json.dumps(
            {
                "source_changes": len(changed),
                "identity_hit_files": len(hit_files),
                "cases": [{"name": case["name"], "suite": case["suite"]} for case in cases],
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("EVIDENCE_FINALIZE_FAILED")
        raise SystemExit(4) from None
