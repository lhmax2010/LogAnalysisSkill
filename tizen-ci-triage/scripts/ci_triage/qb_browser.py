"""Serial JSON driver for the credential-isolated QuickBuild browser agent."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from ci_triage.qb_redact import PageRedactor

FAILURE_CATEGORIES = frozenset(
    {
        "NEW_PAGE",
        "WORKER_BLOCKED",
        "WORKER_NOT_PAUSED",
        "CLOSE_TARGET_FAILED",
        "BROWSER_DISCONNECTED",
        "PAGE_CLOSED",
        "ADAPT_FAILED",
        "FETCH_CONTINUE_FAILED",
        "UNKNOWN",
    }
)
_COMMANDS = frozenset({"login", "open_form", "fill", "read", "submit", "close"})
_PATH_SHAPES = frozenset(
    {"/", "/dashboard", "/wicket/page", "/signin", "<other>", "/overview/<id>"}
    | {f"/build/<id>{suffix}" for suffix in ("", "/overview", "/variables", "/step_status")}
)
_AGENT_CODES = frozenset(
    {
        "QB_BROWSER_UNAVAILABLE",
        "AGENT_PHASE",
        "QB_LOGIN_TIMEOUT",
        "QB_LOGIN_ABORTED",
        "QB_FORM_CHANGED",
        "QB_FORM_VALUE_UNAVAILABLE",
        "QB_FORM_READBACK_MISMATCH",
        "QB_READ_REDIRECTED",
        "QB_READ_ID_MISMATCH",
        "QB_EVIDENCE_REDACTION_FAILED",
        "QB_TRUSTED_CONTEXT_UNAVAILABLE",
    }
)


class QbBrowserError(RuntimeError):
    def __init__(
        self,
        code: str,
        *,
        released: bool | None = None,
        diagnostic: dict[str, Any] | None = None,
        diagnostic_failed: bool = False,
        snapshot_state: dict[str, Any] | None = None,
        agent_code: str | None = None,
        failure_category: str | None = None,
        command: str | None = None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.released = released
        self.diagnostic = diagnostic
        self.diagnostic_failed = diagnostic_failed
        self.snapshot_state = snapshot_state
        self.login_facts: dict[str, Any] | None = None
        self.agent_code = agent_code
        self.failure_category = failure_category
        self.command = command
        self.agent_exited: bool | None = None
        self.agent_exit_code: int | None = None
        self.trace_written = False

    def failure_facts(self) -> dict[str, Any]:
        facts: dict[str, Any] = {
            "command": self.command if self.command in _COMMANDS else None,
            "agent_error_code": (
                self.agent_code
                if self.agent_code in _AGENT_CODES
                else "UNKNOWN"
                if self.agent_code is not None
                else None
            ),
            "failure_category": (
                self.failure_category if self.failure_category in FAILURE_CATEGORIES else None
            ),
            "agent_exited": self.agent_exited,
            "agent_exit_code": self.agent_exit_code,
        }
        if self.login_facts is not None:
            facts["login_facts"] = self.login_facts
        return facts


def validate_login_facts(value: object) -> dict[str, Any]:
    booleans = {"on_signin", "password_present", "sign_out_present", "login_channel_closed"}
    counts = {"checks", "login_posts_released"}
    if not isinstance(value, dict) or set(value) != booleans | counts | {
        "final_path_shape", "denied"
    }:
        raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
    path = value["final_path_shape"]
    denied = value["denied"]
    if (
        not isinstance(path, str)
        or path not in _PATH_SHAPES
        or any(type(value[key]) is not bool for key in booleans)
        or any(type(value[key]) is not int or value[key] < 0 for key in counts)
        or not isinstance(denied, dict)
        or any(
            key not in _PATH_SHAPES or type(count) is not int or count < 0
            for key, count in denied.items()
        )
    ):
        raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
    return value


def validate_snapshot_state(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"selected", "option_count"}:
        raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
    selected = value["selected"]
    if (
        type(value["option_count"]) is not int
        or value["option_count"] < 0
        or selected is not None
        and (
            not isinstance(selected, list)
            or any(
                not isinstance(item, str)
                or len(item) > 200
                or re.fullmatch(r"[A-Za-z0-9._:+-]+", item) is None
                for item in selected
            )
        )
    ):
        raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
    return value


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
    """Retain fixed diagnostic metadata without changing existing error mapping."""
    category = None
    login_facts = None
    try:
        response = json.loads(raw)
    except (ValueError, TypeError):
        response = None
    try:
        if isinstance(response, dict) and "login_facts" in response:
            if (
                command != "login" or response.get("ok") is not False
                or response.get("error") not in ("QB_LOGIN_TIMEOUT", "QB_LOGIN_ABORTED")
                or _sensitive_key(response)
            ):
                if submit_sent:
                    return _unknown()
                raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
            login_facts = validate_login_facts(response["login_facts"])
        if isinstance(response, dict) and "failure_category" in response:
            value = response["failure_category"]
            if not isinstance(value, str) or value not in FAILURE_CATEGORIES:
                if submit_sent:
                    return _unknown()
                raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
            category = value
        return _decode_response(raw, submit_sent=submit_sent, command=command)
    except QbBrowserError as exc:
        exc.command = command if command in _COMMANDS else None
        exc.failure_category = category
        exc.login_facts = login_facts
        if isinstance(response, dict) and not _sensitive_key(response):
            code = response.get("error")
            if isinstance(code, str) and code in _AGENT_CODES:
                exc.agent_code = code
        raise


def _decode_response(raw: str, *, submit_sent: bool, command: str = "") -> dict[str, Any]:
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
    snapshot_state = None
    snapshot_error = (
        command == "fill"
        and response.get("error") == "QB_FORM_VALUE_UNAVAILABLE"
        and response.get("field") == "SNAPSHOT_NUM"
        and response["ok"] is False
    )
    if snapshot_error:
        snapshot_state = validate_snapshot_state(response.get("snapshot_state"))
    elif "snapshot_state" in response:
        if submit_sent:
            return _unknown()
        raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
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
        if "outside_identity_count" in response and (
            type(response["outside_identity_count"]) is not int
            or response["outside_identity_count"] < 0
        ):
            raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
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
                "QB_FETCH_FAILED"
                if command == "read"
                else "REJECTED_QB_FORM_CHANGED"
                if command in {"open_form", "fill", "submit"}
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
            {key: value for key, value in diagnostic.items() if key != "html_redacted"},
            redactor,
        )
    raise QbBrowserError(
        mapped,
        released=False if submit_sent else None,
        diagnostic=diagnostic,
        diagnostic_failed=response.get("diagnostic_failed") is True,
        snapshot_state=snapshot_state,
        agent_code=code if isinstance(code, str) else None,
    )


class QbBrowser:
    """One agent and one login per CLI invocation; commands are synchronous."""

    def __init__(self, qb: dict[str, Any]) -> None:
        self.qb = qb
        self.process: subprocess.Popen[str] | None = None
        self.trace: list[dict[str, Any]] = []

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
        try:
            response = self._command(command, **fields)
        except QbBrowserError as exc:
            exc.command = command if command in _COMMANDS else None
            if self.process is not None:
                exc.agent_exit_code = self.process.poll()
                exc.agent_exited = exc.agent_exit_code is not None
            self.trace.append({"ok": False, **exc.failure_facts()})
            raise
        self.trace.append({"command": command if command in _COMMANDS else None, "ok": True})
        return response

    def _command(self, command: str, **fields: Any) -> dict[str, Any]:
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
            if process.poll() is None and process.stdin is not None and not process.stdin.closed:
                process.stdin.write('{"command":"close"}\n')
                process.stdin.flush()
            if process.stdin is not None:
                process.stdin.close()
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
