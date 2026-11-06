"""Mask session-identity collisions in test identifiers, retaining audit hashes."""

import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

from tizen_qb_verify.qb_redact import SessionPageRedactor

HERE = Path(__file__).resolve().parent
CAPTURE = HERE.parent / "discovery-capture"


def main():
    archive = str(CAPTURE.relative_to(Path.cwd()) / "live-02/02.response.html")
    original = subprocess.check_output(["git", "show", f"57cac6e:{archive}"]).decode()
    spec = importlib.util.spec_from_file_location("archive_cells", CAPTURE / "sanitize_archives.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cells = module.Cells()
    cells.feed(original.split("</thea&lt;USER&gt;", 1)[1].split("</table>", 1)[0])
    assert len(cells.cells) == 7
    redactor = SessionPageRedactor()
    redactor.remember_session_identity(cells.cells[4].strip())
    pattern = re.compile(
        r"(?<![A-Za-z0-9_])(?:"
        + "|".join(re.escape(value) for value in redactor.identities)
        + r")(?![A-Za-z0-9_])"
    )
    audit = []
    for relative in ("collect/stdout.txt", "full/pytest.xml"):
        path = HERE / relative
        raw = path.read_bytes()
        # The matches are in collected test identifiers, not a failure message.
        text = raw.decode()
        if relative.endswith(".xml"):
            import xml.etree.ElementTree as ET

            root = ET.fromstring(text)
            for failure in root.iter("failure"):
                assert not pattern.search(ET.tostring(failure, encoding="unicode"))
        else:
            assert all(
                line.startswith("tests/") and "::" in line
                for line in text.splitlines()
                if pattern.search(line)
            )
        cleaned, count = pattern.subn("[REDACTED_IDENTITY]", text)
        assert count > 0
        path.write_text(cleaned)
        audit.append(
            {
                "file": relative,
                "replacement_count": count,
                "before_sha256": hashlib.sha256(raw).hexdigest(),
                "after_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "failure_messages_changed": False,
            }
        )
    (HERE / "test-identifier-redaction.json").write_text(json.dumps(audit, indent=2) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("TEST_IDENTIFIER_REDACTION_FAILED")
        raise SystemExit(4) from None
