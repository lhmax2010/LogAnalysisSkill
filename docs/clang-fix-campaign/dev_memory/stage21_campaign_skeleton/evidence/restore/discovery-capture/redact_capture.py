"""Evidence-only redaction worker. Private context stays in this process's memory."""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from pathlib import Path

from tizen_qb_verify.qb_redact import PageRedactor


def main() -> None:
    redactor = PageRedactor()
    for line in sys.stdin:
        path: Path | None = None
        created = False
        try:
            item = json.loads(line)
            mode = item["mode"]
            source = item["text"]
            if mode not in {"html", "text", "json"}:
                raise ValueError
            # Escape text before the HTML-aware checker; preserve compiler angle brackets.
            safe = redactor.redact(html.escape(source) if mode == "text" else source)
            count = redactor.identity_outside_registered_count
            if mode == "text":
                safe = html.unescape(safe)
                for identity in sorted(redactor.identities, key=len, reverse=True):
                    safe = re.sub(
                        r"(?<![A-Za-z0-9_])" + re.escape(identity) + r"(?![A-Za-z0-9_])",
                        "<USER>", safe,
                    )
            raw = safe.encode("utf-8")
            redactor.check_bytes(html.escape(safe).encode() if mode == "text" else raw)
            path = Path(item["path"])
            with path.open("xb") as stream:
                created = True
                stream.write(raw)
                stream.flush()
            written = path.read_bytes()
            redactor.check_bytes(
                html.escape(written.decode("utf-8")).encode() if mode == "text" else written
            )
            if written != raw:
                raise ValueError
            print(json.dumps({"ok": True, "sha256": hashlib.sha256(raw).hexdigest(),
                              "bytes": len(raw), "outside_identity_count": count}), flush=True)
        except Exception:
            if created and path is not None:
                path.unlink(missing_ok=True)
            print('{"ok":false,"error":"QB_EVIDENCE_REDACTION_FAILED"}', flush=True)


if __name__ == "__main__":
    main()
