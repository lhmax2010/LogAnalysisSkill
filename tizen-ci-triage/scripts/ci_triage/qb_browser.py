"""Serial JSON driver for the credential-isolated QuickBuild browser agent."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from ci_triage.qb_redact import PageRedactor


class QbBrowserError(RuntimeError):
    def __init__(
        self, code: str, *, released: bool | None = None,
        diagnostic: dict[str, Any] | None = None, diagnostic_failed: bool = False,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.released = released
        self.diagnostic = diagnostic
        self.diagnostic_failed = diagnostic_failed


def _sensitive_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).casefold() in {"cookie", "set-cookie", "authorization"} or _sensitive_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_sensitive_key(item) for item in value)
    return False


def _check_diagnostic_strings(value: object, redactor: PageRedactor) -> None:
    if isinstance(value, str):
        redactor.check_bytes(value.encode("utf-8"))
    elif isinstance(value, dict):
        for key, item in value.items():
            _check_diagnostic_strings(key, redactor)
            _check_diagnostic_strings(item, redactor)
    elif isinstance(value, list):
        for item in value:
            _check_diagnostic_strings(item, redactor)


def _unknown() -> dict[str, Any]:
    return {
        "ok": True,
        "landed": "unknown",
        "released": True,
        "observed": "<other>",
        "messages": [],
    }


def decode_response(raw: str, *, submit_sent: bool, command: str = "") -> dict[str, Any]:
    """Map only the frozen response table; never echo an agent payload in errors."""
    try:
        response = json.loads(raw)
    except (ValueError, TypeError):
        if submit_sent:
            return _unknown()
        raise QbBrowserError("QB_BROWSER_UNAVAILABLE") from None
    if _sensitive_key(response):
        if submit_sent:
            return _unknown()
        raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
    if not isinstance(response, dict) or type(response.get("ok")) is not bool:
        if submit_sent:
            return _unknown()
        raise QbBrowserError("INTERNAL_ERROR")
    if submit_sent:
        if response["ok"]:
            build_id = response.get("build_id")
            valid_build = (
                response.get("landed") == "build"
                and isinstance(build_id, str)
                and build_id.isascii()
                and build_id.isdecimal()
            )
            valid_unknown = (
                response.get("landed") == "unknown"
                and isinstance(response.get("observed"), str)
                and isinstance(response.get("messages"), list)
                and all(isinstance(message, str) for message in response["messages"])
            )
            if (
                response.get("released") is not True
                or not (valid_build or valid_unknown)
                or "html_redacted" in response
            ):
                return _unknown()
        elif response.get("released") is not False or not isinstance(response.get("error"), str):
            return _unknown()
    if response["ok"]:
        if "html_redacted" in response:
            html = response["html_redacted"]
            if not isinstance(html, str):
                raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
            PageRedactor().check_bytes(html.encode("utf-8"))
        return response
    code = response.get("error")
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
            "AGENT_PHASE": "QB_BROWSER_UNAVAILABLE",
            "QB_BROWSER_UNAVAILABLE": "QB_BROWSER_UNAVAILABLE",
            "QB_EVIDENCE_REDACTION_FAILED": "QB_EVIDENCE_REDACTION_FAILED",
        }.get(code if isinstance(code, str) else "", "INTERNAL_ERROR")
        if command == "read" and code in ("QB_READ_REDIRECTED", "QB_READ_ID_MISMATCH"):
            mapped = "QB_FETCH_FAILED"
        if code == "QB_TRUSTED_CONTEXT_UNAVAILABLE":
            mapped = (
                "QB_FETCH_FAILED" if command == "read" else
                "REJECTED_QB_FORM_CHANGED" if command in {"open_form", "fill", "submit"}
                else "INTERNAL_ERROR"
            )
    diagnostic = response.get("diagnostic")
    if diagnostic is not None:
        if not isinstance(diagnostic, dict) or not isinstance(diagnostic.get("html_redacted"), str):
            raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
        redactor = PageRedactor()
        redactor.check_bytes(diagnostic["html_redacted"].encode("utf-8"))
        # Validate decoded strings, never JSON escape sequences as HTML attributes.
        _check_diagnostic_strings(
            {key: value for key, value in diagnostic.items() if key != "html_redacted"}, redactor,
        )
    raise QbBrowserError(
        mapped, released=False if submit_sent else None, diagnostic=diagnostic,
        diagnostic_failed=response.get("diagnostic_failed") is True,
    )


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
            if command == "submit":
                return _unknown()
            raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
        if _sensitive_key(fields):
            raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
        try:
            process.stdin.write(
                json.dumps({"command": command, **fields}, ensure_ascii=False) + "\n"
            )
            process.stdin.flush()
            raw = process.stdout.readline()
        except (OSError, UnicodeError, ValueError):
            raw = ""
        return decode_response(raw, submit_sent=command == "submit", command=command)

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
