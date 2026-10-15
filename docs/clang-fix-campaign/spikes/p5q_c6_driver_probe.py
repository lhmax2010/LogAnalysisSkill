"""One browser-driver diagnostic run, with no campaign database access."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from ci_triage.qb_browser import QbBrowser, QbBrowserError
from ci_triage.qb_config import parse_qb_config
from ci_triage.qb_redact import PageRedactor

DEFAULT_CONFIG = Path("/home/linhao/Toolchain/p5q-live-validation/p5q-c6/config.yaml")
TARGET = "platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0"


def checked_result(path: Path, result: dict[str, Any]) -> None:
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    redactor = PageRedactor()
    redactor.check_bytes(raw)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    redactor.check_written(path)


def run_probe(config: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=False)
    result: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "ok": False,
        "commands": [],
        "trace": [],
        "release_state": "unknown",
        "form_action_releases": None,
        "state_db_access": False,
    }
    browser: QbBrowser | None = None
    stage = "login"
    started = time.monotonic()

    def record(ok: bool, error: BaseException | None = None) -> None:
        facts: dict[str, Any] = {
            "command": stage,
            "ok": ok,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "error_code": None,
            "agent_error_code": None,
            "failure_category": None,
            "agent_exited": None,
            "agent_exit_code": None,
        }
        if isinstance(error, QbBrowserError):
            facts.update(error.failure_facts())
            facts["command"] = stage
            facts["error_code"] = error.code
        elif error is not None:
            facts["error_code"] = type(error).__name__
        if browser is not None and browser.process is not None:
            facts["agent_exit_code"] = browser.process.poll()
            facts["agent_exited"] = facts["agent_exit_code"] is not None
        result["commands"].append(facts)

    try:
        raw = yaml.safe_load(config.read_text(encoding="utf-8"))
        qb = parse_qb_config(raw["qb"])
        project = qb["projects"]["tizen_base"]
        fields = copy.deepcopy(project["form"])
        fields.update(
            {
                "Build Package List": TARGET,
                "BUILD NOTES": "clang-fix-campaign request=probe-" + uuid.uuid4().hex,
            }
        )
        result["requested_fields"] = fields
        browser = QbBrowser(qb)
        browser.__enter__()
        browser.login()
        record(True)
        stage, started = "open_form", time.monotonic()
        browser.command("open_form", overview_id=project["overview_id"])
        record(True)
        stage, started = "fill", time.monotonic()
        reply = browser.command("fill", fields=fields)
        actual = reply.get("readback")
        expected = {
            key
            + ("/selection" if key in {"CHILD_CONFIGURATIONS", "TARGET_IMAGE"} else "/value"): value
            for key, value in fields.items()
        }
        if fields["SNAPSHOT_NUM"] == "@freeze":
            current = actual.get("SNAPSHOT_NUM/value") if isinstance(actual, dict) else None
            if not isinstance(current, str) or not current:
                raise QbBrowserError("QB_FORM_READBACK_MISMATCH")
            expected["SNAPSHOT_NUM/value"] = current
        expected_hash = hashlib.sha256(
            json.dumps(expected, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
                "utf-8"
            )
        ).hexdigest()
        if (
            actual != expected
            or reply.get("fingerprint") != expected_hash
            or reply.get("released") is not False
        ):
            raise QbBrowserError("QB_FORM_READBACK_MISMATCH")
        result.update(
            readback=actual,
            fingerprint=reply["fingerprint"],
            release_state="not_released",
            form_action_releases=0,
        )
        record(True)
        result["ok"] = True
    except Exception as error:
        record(False, error)
    finally:
        stage, started = "close", time.monotonic()
        process = browser.process if browser is not None else None
        try:
            if browser is not None:
                try:
                    browser.command("close")
                finally:
                    browser.close()
                if process is not None and process.poll() != 0:
                    raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
            record(True)
        except Exception as error:
            result["ok"] = False
            record(False, error)
        if process is not None:
            result["commands"][-1].update(
                agent_exit_code=process.poll(),
                agent_exited=process.poll() is not None,
            )
        result["trace"] = browser.trace if browser is not None else []
        result["ended_at"] = datetime.now(timezone.utc).isoformat()
        checked_result(output / "result.json", result)
    return 0 if result["ok"] else 5


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        return run_probe(args.config, args.output)
    except Exception:
        print("P5Q_PROBE_EVIDENCE_WRITE_FAILED", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
