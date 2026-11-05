"""RESTORE-12 one-time archive remediation; identity values stay in process memory."""

from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from tizen_qb_verify.qb_redact import SessionPageRedactor


class Cells(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cells: list[str] = []
        self.active = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "td":
            self.cells.append("")
            self.active = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "td":
            self.active = False

    def handle_data(self, data: str) -> None:
        if self.active:
            self.cells[-1] += data


def remediate(directory: Path) -> dict[str, object]:
    source = (directory / "live-02/02.response.html").read_bytes().decode("utf-8")
    damaged = "</thea&lt;USER&gt;"
    if source.count(damaged) != 1:
        raise ValueError("ARCHIVE_SOURCE_SHAPE")
    # The ruling identifies this exact historical Triggered By cell as the session user.
    tail = source.split(damaged, 1)[1].split("</table>", 1)[0]
    cells = Cells()
    cells.feed(tail)
    if len(cells.cells) != 7:
        raise ValueError("ARCHIVE_SOURCE_SHAPE")
    identity = cells.cells[4].strip()
    if not re.fullmatch(r"(.+?)\s+\(([^()]+)\)", identity):
        raise ValueError("ARCHIVE_ALREADY_PROCESSED_OR_UNRECOGNIZED")
    redactor = SessionPageRedactor()
    redactor.remember_session_identity(identity)
    rows: list[dict[str, object]] = []
    for run in ("live-01", "live-02"):
        for path in sorted((directory / run).glob("*.response.html")):
            before = path.read_bytes()
            after = redactor.redact(before.decode("utf-8")).encode("utf-8")
            count = redactor.identity_replacement_count
            redactor.check_bytes(after)
            assert before.count(damaged.encode()) == after.count(damaged.encode())
            temporary = path.with_suffix(".redaction-tmp")
            with temporary.open("xb") as stream:
                stream.write(after)
            temporary.replace(path)
            redactor.check_bytes(path.read_bytes())
            rows.append({"file": str(path.relative_to(directory)),
                         "before_sha256": hashlib.sha256(before).hexdigest(),
                         "after_sha256": hashlib.sha256(after).hexdigest(),
                         "identity_replacement_count": count, "identity_remaining_count": 0,
                         "damaged_tag_preserved": damaged.encode() in after})
    return {"ruling": "SKEL-RESTORE-12", "files": rows,
            "identity_values_recorded": False,
            "live_01_body_count": len(list((directory / "live-01").glob("*.response.html")))}


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    try:
        result = remediate(here)
        (here / "archive-redaction-12.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"ok": True, "files": len(result["files"])}))  # type: ignore[arg-type]
    except Exception:
        print('{"ok":false,"error":"ARCHIVE_REDACTION_FAILED"}')
        raise SystemExit(4) from None
