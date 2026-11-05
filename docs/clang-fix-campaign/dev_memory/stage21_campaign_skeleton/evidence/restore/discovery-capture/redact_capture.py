"""Evidence-only redaction worker. Private context stays in this process's memory."""

from __future__ import annotations

import hashlib
import html
import json
import sys
from pathlib import Path

from tizen_qb_verify.qb_redact import PageRedactor, SessionPageRedactor


def main() -> None:
    redactor = SessionPageRedactor()
    for line in sys.stdin:
        path: Path | None = None
        created = False
        try:
            item = json.loads(line)
            mode = item["mode"]
            source = item["text"]
            if mode not in {"html", "text", "json"}:
                raise ValueError
            # Metadata has fixed keys, not page identity-bearing text. Never replace its keys.
            checker: PageRedactor = redactor
            if mode == "json":
                checker = PageRedactor()
                checker.secrets = redactor.secrets
            # Escape text before the HTML-aware checker; preserve compiler angle brackets.
            safe = checker.redact(html.escape(source) if mode == "text" else source)
            if mode != "json" and not redactor.session_identity_complete:
                raise ValueError("SESSION_IDENTITY_INCOMPLETE")
            count = redactor.identity_replacement_count if mode != "json" else 0
            if mode == "text":
                safe = html.unescape(safe)
            raw = safe.encode("utf-8")
            checker.check_bytes(html.escape(safe).encode() if mode == "text" else raw)
            path = Path(item["path"])
            with path.open("xb") as stream:
                created = True
                stream.write(raw)
                stream.flush()
            written = path.read_bytes()
            checker.check_bytes(
                html.escape(written.decode("utf-8")).encode() if mode == "text" else written
            )
            if written != raw:
                raise ValueError
            print(json.dumps({"ok": True, "sha256": hashlib.sha256(raw).hexdigest(),
                              "bytes": len(raw), "identity_replacement_count": count,
                              "identity_remaining_count": 0}), flush=True)
        except Exception:
            if created and path is not None:
                path.unlink(missing_ok=True)
            print('{"ok":false,"error":"QB_EVIDENCE_REDACTION_FAILED"}', flush=True)


if __name__ == "__main__":
    main()
