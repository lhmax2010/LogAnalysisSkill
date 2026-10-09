"""Apply the user-identity redaction policy to existing evidence without network access."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ef5_web_probe import PageInventory, PageRedactor


def encode_json(data: object) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()


def redact_archive(root: Path) -> dict[str, object]:
    records = json.loads((root / "requests.json").read_text())
    pending: dict[Path, bytes] = {}
    summary = []
    for record in records:
        response = root / record["response"]
        raw = response.read_bytes()
        old_sha = hashlib.sha256(raw).hexdigest()
        if old_sha != record["redacted_sha256"]:
            raise ValueError("Archive hash mismatch; nothing rewritten")
        redactor = PageRedactor("", "", "")
        safe = redactor.redact(raw.decode())
        if redactor.redact(safe) != safe or safe.count("\n") != raw.decode().count("\n"):
            raise ValueError("Redaction changed evidence line numbers or is not idempotent")
        parsed = PageInventory()
        parsed.feed(safe)
        links = [link for link in parsed.links if isinstance(link["href"], str) and link["href"]]
        page_path = response.with_name(response.name.removesuffix('.response.txt') + '.page.json')
        page = json.loads(page_path.read_text())
        if [link["href"] for link in page["links"]] != [link["href"] for link in links]:
            raise ValueError("Archive link layout differs; review before rewriting")
        page["visible_text"] = parsed.lines
        page["form_fields_metadata_only"] = parsed.inputs
        page["links"] = [
            {**old, **new} for old, new in zip(page["links"], links, strict=True)
        ]
        record["redacted_sha256"] = hashlib.sha256(safe.encode()).hexdigest()
        pending[response] = safe.encode()
        pending[page_path] = encode_json(page)
        summary.append({
            "response": response.name, "old_sha256": old_sha,
            "redacted_sha256": record["redacted_sha256"],
            "user_fields": sum(line.count("<USER>") for line in parsed.lines),
        })
    pending[root / "requests.json"] = encode_json(records)
    for path, payload in pending.items():
        path.write_bytes(payload)
    return {"policy": "WELCOME_TRIGGERED_BY_USER_V1", "network_requests": 0,
            "pages": summary, "line_numbers_preserved": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = redact_archive(args.archive)
    args.report.write_bytes(encode_json(report))
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
