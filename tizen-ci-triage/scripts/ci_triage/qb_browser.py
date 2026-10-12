"""Serial JSON driver for the credential-isolated QuickBuild browser agent."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from ci_triage.qb_redact import PageRedactor


class QbBrowserError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _sensitive_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).casefold() in {"cookie", "set-cookie", "authorization"} or _sensitive_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_sensitive_key(item) for item in value)
    return False


def _unknown() -> dict[str, Any]:
    return {
        "ok": True,
        "landed": "unknown",
        "released": True,
        "observed": "<other>",
        "messages": [],
    }


def decode_response(raw: str, *, submit_sent: bool) -> dict[str, Any]:
    """Map only the frozen response table; never echo an agent payload in errors."""
    try:
        response = json.loads(raw)
    except (ValueError, TypeError):
        if submit_sent:
            return _unknown()
        raise QbBrowserError("QB_BROWSER_UNAVAILABLE") from None
    if _sensitive_key(response):
        raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
    if not isinstance(response, dict) or type(response.get("ok")) is not bool:
        raise QbBrowserError("INTERNAL_ERROR")
    if response["ok"]:
        if "html_redacted" in response:
            html = response["html_redacted"]
            if not isinstance(html, str):
                raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
            PageRedactor().check_bytes(html.encode("utf-8"))
        return response
    code = response.get("error")
    if code == "AGENT_PHASE":
        if submit_sent:
            return _unknown()
        raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
    if code == "QB_FORM_VALUE_UNAVAILABLE":
        mapped = (
            "REJECTED_QB_SNAPSHOT_UNAVAILABLE"
            if response.get("field") == "SNAPSHOT_NUM"
            else "REJECTED_QB_FORM_MISMATCH"
        )
    else:
        mapped = {
            "QB_FORM_CHANGED": "REJECTED_QB_FORM_CHANGED",
            "QB_FORM_READBACK_MISMATCH": "REJECTED_QB_FORM_MISMATCH",
            "QB_LOGIN_TIMEOUT": "QB_LOGIN_TIMEOUT",
            "QB_LOGIN_ABORTED": "QB_LOGIN_ABORTED",
        }.get(code if isinstance(code, str) else "", "INTERNAL_ERROR")
    raise QbBrowserError(mapped)


class QbBrowser:
    """One agent and one login per CLI invocation; commands are synchronous."""

    def __init__(self, qb: dict[str, Any]) -> None:
        self.qb = qb
        self.process: subprocess.Popen[str] | None = None

    def __enter__(self) -> QbBrowser:
        browser = self.qb["browser"]
        env = os.environ.copy()
        for name in ("DEBUG", "PWDEBUG", "NODE_OPTIONS", "QB_COOKIE", "QB_PASSWORD"):
            env.pop(name, None)
        try:
            self.process = subprocess.Popen(
                [
                    browser["node"],
                    str(Path(__file__).with_name("qb_browser_agent.mjs")),
                    browser["playwright_module"],
                    browser["chromium"],
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                env=env,
            )
        except OSError:
            raise QbBrowserError("QB_BROWSER_UNAVAILABLE") from None
        return self

    def command(self, command: str, **fields: Any) -> dict[str, Any]:
        process = self.process
        if process is None or process.stdin is None or process.stdout is None:
            raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
        if _sensitive_key(fields):
            raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
        sent = False
        try:
            process.stdin.write(
                json.dumps({"command": command, **fields}, ensure_ascii=False) + "\n"
            )
            process.stdin.flush()
            sent = True
            raw = process.stdout.readline()
        except (OSError, UnicodeError):
            raw = ""
        return decode_response(raw, submit_sent=sent and command == "submit")

    def login(self) -> dict[str, Any]:
        return self.command(
            "login",
            login_timeout_seconds=self.qb["browser"]["login_timeout_seconds"],
            projects=[
                {key: value[key] for key in ("overview_id", "configuration_path", "project_name")}
                for value in self.qb["projects"].values()
                if value["enabled"]
            ],
        )

    def close(self) -> None:
        process = self.process
        if process is None:
            return
        try:
            if process.poll() is None and process.stdin is not None:
                process.stdin.write('{"command":"close"}\n')
                process.stdin.flush()
            process.wait(timeout=35)
        except (OSError, subprocess.TimeoutExpired):
            process.terminate()
            process.wait(timeout=35)
        finally:
            if process.stdin is not None:
                process.stdin.close()
            if process.stdout is not None:
                process.stdout.close()
            self.process = None

    def __exit__(self, *_args: object) -> None:
        self.close()
