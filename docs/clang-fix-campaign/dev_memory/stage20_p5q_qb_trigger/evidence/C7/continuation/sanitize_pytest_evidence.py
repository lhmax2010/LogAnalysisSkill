"""Remove synthetic HTML parameter payloads from pytest artifact identifiers."""

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from ci_triage.qb_redact import PageRedactor

HERE = Path(__file__).resolve().parent


def safe_name(name):
    if "[" not in name or "[case-sha256-" in name:
        return name
    digest = hashlib.sha256(name.encode()).hexdigest()
    return name.split("[", 1)[0] + "[case-sha256-" + digest + "]"


def main():
    records = []
    for path in [
        HERE / "collection-final/output.log",
        *HERE.rglob("junit.xml"),
        HERE / "safety-01/output.log",
    ]:
        before = path.read_bytes()
        if path.suffix == ".xml":
            tree = ET.fromstring(before)
            for case in tree.findall(".//testcase"):
                if "name" in case.attrib:
                    case.set("name", safe_name(case.attrib["name"]))
            after = ET.tostring(tree, encoding="utf-8", xml_declaration=True)
        else:
            lines = []
            for line in before.decode().splitlines(keepends=True):
                if line.startswith("tests/") and "::" in line:
                    prefix, name = line.rstrip("\n").rsplit("::", 1)
                    line = prefix + "::" + safe_name(name) + "\n"
                elif line.startswith("{"):
                    # Keep HTML in JSON inert for raw-byte checks; decoded facts are unchanged.
                    line = (
                        json.dumps(json.loads(line), ensure_ascii=True)
                        .replace("<", "\\u003c")
                        .replace(">", "\\u003e")
                        + "\n"
                    )
                lines.append(line)
            after = "".join(lines).encode()
        PageRedactor().check_bytes(after)
        path.write_bytes(after)
        records.append(
            dict(
                file=str(path.relative_to(HERE)),
                original_sha256=hashlib.sha256(before).hexdigest(),
                redacted_sha256=hashlib.sha256(after).hexdigest(),
            )
        )
    (HERE / "pytest-artifact-redaction.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
