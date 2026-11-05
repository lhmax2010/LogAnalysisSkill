"""Capture protocol and offline replay; responses never contain raw exceptions."""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

from capture_archive import Archive


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    archive: Archive | None = None
    try:
        if args.replay:
            if args.output is None:
                raise ValueError
            args.output.mkdir()
            archive = Archive(args.output, replay=args.replay)
            record = json.loads((archive.private / "record.json").read_text())
            reply = archive.finish(record, replay=True)
            print(json.dumps(reply), flush=True)
            raise SystemExit(0 if reply["ok"] else 4)
        for line in sys.stdin:
            item = json.loads(line)
            if item["command"] == "start":
                if archive is not None:
                    raise ValueError
                archive = Archive(Path(item["output"]))
                reply = {"ok": True}
            elif item["command"] == "store" and archive is not None:
                reply = archive.store(item["name"], item["mode"],
                                      base64.b64decode(item["raw"], validate=True), item["text"])
            elif item["command"] == "finish" and archive is not None:
                reply = archive.finish(item["record"])
            else:
                raise ValueError
            print(json.dumps(reply), flush=True)
    except Exception:
        print(json.dumps({"ok": False, "error": "QB_EVIDENCE_REDACTION_FAILED", "stage": "WRITE",
                          **(archive.counts() if archive else {"welcome_regions": 0,
                             "registered_identities": 0, "identity_replacement_count": 0})}),
              flush=True)


if __name__ == "__main__":
    main()
