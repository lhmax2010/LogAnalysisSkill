"""Submit one durable campaign request at a time through the isolated QB agent."""

from __future__ import annotations

import copy
import fcntl
import json
import re
import shutil
import sqlite3
import subprocess
import traceback
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, TextIO

import yaml
from tizen_ci_shared.state import StateDatabase

from ci_triage import campaign_state as state
from ci_triage import sandbox_submit as sandbox
from ci_triage._campaign_workspace import _unit_hash
from ci_triage.aggregate import aggregate_verifications
from ci_triage.qb_browser import QbBrowser, QbBrowserError, _check_diagnostic_strings
from ci_triage.qb_config import (
    FORM_KEYS,
    QbConfigError,
    QbProjectNotReady,
    canonical_profile_json,
    parse_qb_config,
    project_for_branch,
)
from ci_triage.qb_redact import EvidenceRedactionError, PageRedactor

_STATUSES = {
    "SANDBOX_PUSHED",
    "KB_APPENDED",
    "QB_REQUESTED",
    "QB_TRIGGERED",
    "SANDBOX_QB_PENDING",
    "SANDBOX_QB_PASS",
    "SANDBOX_QB_FAILED",
    "QB_SUBMIT_FAILED",
}
_PALETTES = {"CHILD_CONFIGURATIONS", "TARGET_IMAGE"}
_UNKNOWN_MESSAGE = (
    "请到 QuickBuild 按请求标记找到构建后用 qb-result-fetch --request-id 与 --qb-build-id 绑定;"
    "确认没有构建后用 --retrigger 重提"
)


@dataclass(frozen=True)
class QbTriggerOptions:
    state_db: Path
    state_root: Path
    config: Path
    verification_ids: str | None = None
    units_file: Path | None = None
    retrigger: bool = False


@dataclass(frozen=True)
class TriggerSnapshot:
    unit: state.Unit
    status: str
    derived: str
    push: dict[str, Any]
    push_event: int
    request: dict[str, Any] | None
    bound: dict[str, Any] | None
    result: dict[str, Any] | None
    profile: dict[str, Any] | None
    project: dict[str, Any]


class _Rejected(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def empty_result() -> dict[str, Any]:
    return dict(
        campaign_unit_key=None,
        sbs_target=None,
        request_id=None,
        request_seq=None,
        qb_build_id=None,
        action="rejected",
        status=None,
        error_code=None,
        diagnostic_dir=None,
        message=None,
    )


def _groups(options: QbTriggerOptions) -> list[tuple[str, ...]]:
    if (options.verification_ids is None) == (options.units_file is None):
        raise QbConfigError("select verification-ids or units-file")
    rows = (
        json.loads(options.units_file.read_text(encoding="utf-8"))
        if options.units_file
        else [{"verification_ids": (options.verification_ids or "").split(",")}]
    )
    if not isinstance(rows, list) or not rows:
        raise QbConfigError("units-file must be a nonempty array")
    groups = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"verification_ids"}:
            raise QbConfigError("invalid unit selection")
        ids = row["verification_ids"]
        if (
            not isinstance(ids, list)
            or len(ids) != 3
            or any(not isinstance(item, str) or not item.strip() for item in ids)
            or len(set(ids)) != 3
        ):
            raise QbConfigError("three distinct verification ids required")
        groups.append(tuple(ids))
    return groups


@contextmanager
def _lock(root: Path) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".sandbox_submit.lock").open("a+", encoding="utf-8") as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise state.CampaignStateBusy("sandbox lock held") from None
        yield


@contextmanager
def _write(db: StateDatabase) -> Iterator[sqlite3.Connection]:
    # Trigger only operates on an existing campaign; never initialize schema here.
    conn = sqlite3.connect(db.path.resolve().as_uri() + "?mode=rw", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        with state._immediate_transaction(conn):
            yield conn
    finally:
        conn.close()


def _row(conn: sqlite3.Connection, sql: str, *args: Any) -> dict[str, Any] | None:
    row = conn.execute(sql, args).fetchone()
    return dict(row) if row is not None else None


def _latest_request(conn: sqlite3.Connection, key: str) -> dict[str, Any] | None:
    return _row(
        conn,
        "SELECT * FROM campaign_qb_requests WHERE campaign_unit_key=? "
        "ORDER BY request_seq DESC LIMIT 1",
        key,
    )


def _profile(conn: sqlite3.Connection, branch: str) -> dict[str, Any] | None:
    return _row(conn, "SELECT * FROM campaign_qb_profiles WHERE branch=?", branch)


def _push_event(conn: sqlite3.Connection, key: str) -> int:
    rows = conn.execute(
        "SELECT event_id,payload_json FROM campaign_gate_events "
        "WHERE campaign_unit_key=? AND event_type='PUSH' "
        "ORDER BY event_id DESC",
        (key,),
    ).fetchall()
    return next(
        (
            int(row["event_id"])
            for row in rows
            if json.loads(row["payload_json"])["ref_class"] == "sandbox"
        ),
        0,
    )


def _snapshot(
    db: StateDatabase, ids: tuple[str, ...], key: str, qb: dict[str, Any]
) -> TriggerSnapshot:
    conn = state._read_connection(db)
    try:
        conn.execute("BEGIN")
        links = sandbox._links(conn, ids)
        if links[0]["campaign_unit_key"] != key:
            raise state.CampaignStateBusy("unit changed during locking")
        round_ = sandbox._round(conn, key)
        if round_ is None or links[0]["round_index"] != round_.round_index:
            raise _Rejected("REJECTED_ROUND_SUPERSEDED")
        unit = state._require_unit(conn, key)
        aggregate = aggregate_verifications(ids, db)
        if not aggregate.ok or any(
            getattr(aggregate, field) != getattr(unit, field)
            for field in ("base_commit", "project", "spec_name", "branch")
        ):
            raise _Rejected("REJECTED_ARCH_AGGREGATE_MISMATCH")
        project = project_for_branch(qb, unit.branch)
        profile = _profile(conn, unit.branch)
        if profile is not None:
            frozen = json.loads(profile["profile_json"])
            if (
                canonical_profile_json(project, frozen_snapshot=frozen["form"]["SNAPSHOT_NUM"])
                != profile["profile_json"]
            ):
                raise _Rejected("REJECTED_QB_PARAMS_CHANGED")
        gate = state._gate_view_on_connection(conn, key)
        status = sandbox._status(conn, key)
        if status not in _STATUSES or not gate.derive or not gate.sandbox_push:
            raise _Rejected("REJECTED_SANDBOX_NOT_BOUND")
        derived, push = str(gate.derive["derived_commit_sha"]), dict(gate.sandbox_push)
        if (
            push["result"] != "ok"
            or push["pushed_sha"] != derived
            or not isinstance(push["ref"], str)
            or not push["ref"].startswith("refs/heads/")
            or sandbox._BRANCH.fullmatch(push["ref"].removeprefix("refs/heads/")) is None
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/+-]*", unit.project) is None
            or ".." in unit.project
            or unit.project.endswith("/")
        ):
            raise _Rejected("REJECTED_SANDBOX_NOT_BOUND")
        request = _latest_request(conn, key)
        seq = request["request_seq"] if request else None
        events = [
            _row(
                conn,
                "SELECT * FROM campaign_qb_events WHERE request_seq=? "
                "AND event_type=? ORDER BY event_id DESC LIMIT 1",
                seq,
                kind,
            )
            for kind in ("BUILD_BOUND", "RESULT")
        ]
        return TriggerSnapshot(
            unit,
            str(status),
            derived,
            push,
            _push_event(conn, key),
            request,
            events[0],
            events[1],
            profile,
            project,
        )
    finally:
        conn.close()


def _idempotency(snapshot: TriggerSnapshot, retrigger: bool) -> str | None:
    if snapshot.request is None:
        return None
    if snapshot.bound is None:
        return None if snapshot.status == "QB_SUBMIT_FAILED" or retrigger else "already_requested"
    if snapshot.result is None or snapshot.result["status"] == "PASS":
        if retrigger:
            raise _Rejected("REJECTED_QB_REQUEST_PENDING")
        return "already_passed" if snapshot.result else "already_requested"
    return None if retrigger else "already_requested"


def snapshot_message(frozen: str | None, selected: list[str] | None, option_count: int) -> str:
    if frozen is not None and selected is not None and len(selected) == 1:
        return f"参考快照已从 {frozen} 变为 {selected[0]},需在新 campaign 中处理"
    value = "尚无" if frozen is None else frozen
    current = "形态不在登记范围" if selected is None else ",".join(selected) if selected else "无"
    followup = (
        "请人工核对 SNAPSHOT_NUM 下拉框后重跑" if frozen is None else "需在新 campaign 中处理"
    )
    return f"参考快照不可用:冻结值 {value},当前选中项 {current},共 {option_count} 个选项;{followup}"


def _trace(root: Path, key: str, facts: dict[str, Any]) -> None:
    _check_diagnostic_strings(facts, PageRedactor())
    path = root / "qb_traces" / (_unit_hash(key) + ".jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(facts, ensure_ascii=False, sort_keys=True) + "\n")


def _browser_failure_trace(root: Path, key: str, error: QbBrowserError) -> None:
    if error.trace_written:
        return
    try:
        _trace(root, key, {"action": "BROWSER_COMMAND_FAILED", **error.failure_facts()})
        error.trace_written = True
    except (OSError, EvidenceRedactionError):
        # Diagnostic storage must not replace the original command outcome.
        pass


def _diagnostic(root: Path, key: str, diagnostic: dict[str, Any]) -> str | None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = root / "qb_diagnostics" / f"{stamp}-{_unit_hash(key)}"
    try:
        directory.mkdir(parents=True)
        redactor = PageRedactor()
        html = diagnostic["html_redacted"].encode("utf-8")
        facts = {key: value for key, value in diagnostic.items() if key != "html_redacted"}
        redactor.check_bytes(html)
        _check_diagnostic_strings(facts, redactor)
        (directory / "page.html").write_bytes(html)
        (directory / "structure.json").write_text(
            json.dumps(facts, ensure_ascii=False, sort_keys=True), encoding="utf-8"
        )
        redactor.check_bytes((directory / "page.html").read_bytes())
        _check_diagnostic_strings(json.loads((directory / "structure.json").read_bytes()), redactor)
        return str(directory)
    except (OSError, ValueError, EvidenceRedactionError):
        shutil.rmtree(directory, ignore_errors=True)
        return None


def _readback_profile(
    project: dict[str, Any], fields: dict[str, Any], filled: dict[str, Any], frozen: bool
) -> str:
    actual = filled.get("readback")
    keys = {f"{key}/{'selection' if key in _PALETTES else 'value'}" for key in fields}
    if not isinstance(actual, dict) or set(actual) != keys:
        raise _Rejected("REJECTED_QB_FORM_MISMATCH")
    values = {}
    for key, wanted in fields.items():
        value = actual[f"{key}/{'selection' if key in _PALETTES else 'value'}"]
        values[key] = value
        if key == "SNAPSHOT_NUM" and wanted == "@freeze":
            if not isinstance(value, str) or not value or value == "@freeze":
                raise _Rejected("REJECTED_QB_FORM_MISMATCH")
            continue
        if type(value) is type(wanted) and value == wanted:
            continue
        if key == "SNAPSHOT_NUM":
            selected = (
                [value]
                if isinstance(value, str)
                and len(value) <= 200
                and re.fullmatch(r"[A-Za-z0-9._:+-]+", value)
                else None
            )
            raise QbBrowserError(
                "REJECTED_QB_SNAPSHOT_UNAVAILABLE",
                snapshot_state={
                    "selected": selected,
                    "option_count": filled["snapshot_option_count"],
                },
            )
        raise _Rejected(
            "REJECTED_QB_PARAMS_CHANGED"
            if frozen and key in FORM_KEYS
            else "REJECTED_QB_FORM_MISMATCH"
        )
    candidate = copy.deepcopy(project)
    candidate["form"] = {key: values[key] for key in FORM_KEYS}
    return canonical_profile_json(candidate)


def _remote_check(config: sandbox._Config, snapshot: TriggerSnapshot, root: Path) -> None:
    path = root / ".transport"
    try:
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.exists():
            shutil.rmtree(path)
        # A fresh bare transport needs no source objects for ls-remote.
        config.git.run(None, "init", "--bare", str(path))
        remote = config.remote_base.rstrip("/") + "/" + snapshot.unit.project
        sandbox._remote_check(config.git, path, remote)
        if (
            sandbox._classify_ref(snapshot.push["ref"], config.git) != sandbox.RefClass.SANDBOX
            or sandbox._remote_sha(config.git, path, remote, snapshot.push["ref"])
            != snapshot.derived
        ):
            raise _Rejected("REJECTED_SANDBOX_NOT_BOUND")
    except (sandbox._Reject, sandbox._TransportFailure, OSError, subprocess.SubprocessError):
        raise _Rejected("REJECTED_SANDBOX_NOT_BOUND") from None
    finally:
        if path.exists():
            shutil.rmtree(path)


def _intent(
    db: StateDatabase, snapshot: TriggerSnapshot, profile: str, request_id: str, target: str
) -> int:
    key = snapshot.unit.campaign_unit_key
    with _write(db) as conn:
        latest = _latest_request(conn, key)
        if (
            sandbox._status(conn, key) != snapshot.status
            or (latest["request_seq"] if latest else None)
            != (snapshot.request["request_seq"] if snapshot.request else None)
            or _push_event(conn, key) != snapshot.push_event
        ):
            raise _Rejected("REJECTED_STATE_INCONSISTENT")
        current = _profile(conn, snapshot.unit.branch)
        if current is not None and current["profile_json"] != profile:
            raise _Rejected("REJECTED_QB_PARAMS_CHANGED")
        state._insert_qb_profile_on_connection(conn, snapshot.unit.branch, profile_json=profile)
        seq = state._create_qb_request_on_connection(
            conn, key, request_id=request_id, sbs_target=target
        )
        state._append_status_on_connection(conn, key, "QB_REQUESTED")
        return seq


class _VariableRows(HTMLParser):
    """Variable table cells; preserve br boundaries for exact target-line comparison."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self.cells: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.cells = []
        elif tag in {"td", "th"} and self.cells is not None:
            self.cell = []
        elif tag == "br" and self.cell is not None:
            self.cell.append("\n")

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.cell is not None and self.cells is not None:
            self.cells.append("".join(self.cell).strip())
            self.cell = None
        elif tag == "tr" and self.cells is not None:
            self.rows.append(self.cells)
            self.cells = None


def _binding_echo(response: dict[str, Any], target: str, marker: str) -> bool:
    if response.get("status") != 200 or not isinstance(response.get("html_redacted"), str):
        return False
    parser = _VariableRows()
    parser.feed(response["html_redacted"])

    def value(name: str, label: str) -> str | None:
        rows = [row for row in parser.rows if len(row) == 3 and row[0] == name]
        return rows[0][2] if len(rows) == 1 and rows[0][1] == label else None

    packages = value("BUILD_PKG_LIST_MODIFY", "Build Package List")
    return (
        packages is not None
        and [line.strip() for line in packages.splitlines() if line.strip()] == [target]
        and value("BUILD_NOTES", "BUILD NOTES") == marker
    )


def _bind(db: StateDatabase, key: str, seq: int, build: str) -> None:
    with _write(db) as conn:
        latest = _latest_request(conn, key)
        if (
            latest is None
            or latest["request_seq"] != seq
            or conn.execute(
                "SELECT 1 FROM campaign_qb_events WHERE event_type='BUILD_BOUND' "
                "AND (request_seq=? OR qb_build_id=?)",
                (seq, build),
            ).fetchone()
        ):
            raise _Rejected("REJECTED_QB_BINDING_MISMATCH")
        state._append_qb_event_on_connection(
            conn, request_seq=seq, event_type="BUILD_BOUND", qb_build_id=build
        )
        state._append_status_on_connection(conn, key, "QB_TRIGGERED")


def _submit(
    db: StateDatabase, browser: QbBrowser, result: dict[str, Any], fingerprint: str, root: Path
) -> None:
    key, seq = result["campaign_unit_key"], result["request_seq"]
    try:
        reply = browser.command("submit", fingerprint=fingerprint)
    except QbBrowserError as exc:
        _browser_failure_trace(root, key, exc)
        if exc.released is not False:
            raise
        with _write(db) as conn:
            state._append_status_on_connection(conn, key, "QB_SUBMIT_FAILED")
        result.update(
            action="submit_failed", status="QB_SUBMIT_FAILED", error_code="REJECTED_QB_FORM_CHANGED"
        )
        if exc.diagnostic is not None:
            result["diagnostic_dir"] = _diagnostic(root, key, exc.diagnostic)
        return
    if reply["landed"] == "unknown":
        message = f"观察到的落点:{reply['observed']};{_UNKNOWN_MESSAGE}"
        _trace(
            root,
            key,
            dict(
                request_id=result["request_id"],
                message=message,
                observed=reply["observed"],
                messages=reply["messages"],
            ),
        )
        result.update(action="submit_uncertain", error_code="QB_SUBMIT_UNCERTAIN", message=message)
        return
    build = reply["build_id"]
    try:
        echo = browser.command("read", path=f"/build/{build}/variables")
        if not _binding_echo(
            echo, result["sbs_target"], f"clang-fix-campaign request={result['request_id']}"
        ):
            raise _Rejected("REJECTED_QB_BINDING_MISMATCH")
        _bind(db, key, seq, build)
    except (_Rejected, QbBrowserError) as exc:
        if isinstance(exc, QbBrowserError):
            _browser_failure_trace(root, key, exc)
        result.update(action="submit_uncertain", error_code="REJECTED_QB_BINDING_MISMATCH")
        if isinstance(exc, QbBrowserError) and exc.diagnostic is not None:
            result["diagnostic_dir"] = _diagnostic(root, key, exc.diagnostic)
        return
    result.update(action="submitted_bound", status="QB_TRIGGERED", qb_build_id=build)


def qb_trigger(options: QbTriggerOptions, *, stderr: TextIO) -> tuple[int, list[dict[str, Any]]]:
    try:
        groups = _groups(options)
        raw = yaml.safe_load(options.config.read_text(encoding="utf-8"))
        qb = parse_qb_config(raw.get("qb") if isinstance(raw, dict) else None)
        config = sandbox._config(options.config)
    except (ValueError, OSError, yaml.YAMLError, sandbox._Reject):
        return 2, [dict(empty_result(), error_code="INVALID_ARGS")]
    db = StateDatabase(options.state_db)
    results: list[dict[str, Any]] = []
    exit_code = 0
    browser: QbBrowser | None = None
    login_failure: str | None = None
    try:
        for ids in groups:
            result = empty_result()
            results.append(result)
            fields: dict[str, Any] = {}
            frozen_snapshot: str | None = None
            key = "unselected"
            try:
                conn = state._read_connection(db)
                try:
                    key = str(sandbox._links(conn, ids)[0]["campaign_unit_key"])
                finally:
                    conn.close()
                result["campaign_unit_key"] = key
                if login_failure:
                    result.update(action="submit_failed", error_code=login_failure)
                    continue
                with _lock(config.workspace / _unit_hash(key)):
                    snapshot = _snapshot(db, ids, key, qb)
                    if snapshot.profile is not None:
                        frozen_snapshot = json.loads(snapshot.profile["profile_json"])["form"][
                            "SNAPSHOT_NUM"
                        ]
                    result.update(
                        status=snapshot.status,
                        sbs_target=f"{snapshot.unit.project}@{snapshot.derived}",
                    )
                    action = _idempotency(snapshot, options.retrigger)
                    if action:
                        assert snapshot.request is not None
                        result.update(
                            action=action,
                            request_id=snapshot.request["request_id"],
                            request_seq=snapshot.request["request_seq"],
                            qb_build_id=snapshot.bound["qb_build_id"] if snapshot.bound else None,
                        )
                        continue
                    if browser is None:
                        browser = QbBrowser(qb)
                        browser.__enter__()
                        try:
                            browser.login()
                        except QbBrowserError as exc:
                            _browser_failure_trace(options.state_root, key, exc)
                            login_failure = exc.code
                            result.update(action="submit_failed", error_code=exc.code)
                            exit_code = 5
                            continue
                    request_id = uuid.uuid4().hex
                    result["request_id"] = request_id
                    browser.command("open_form", overview_id=snapshot.project["overview_id"])
                    frozen = (
                        json.loads(snapshot.profile["profile_json"]) if snapshot.profile else None
                    )
                    fields = copy.deepcopy(frozen["form"] if frozen else snapshot.project["form"])
                    fields.update(
                        {
                            "Build Package List": result["sbs_target"],
                            "BUILD NOTES": f"clang-fix-campaign request={request_id}",
                        }
                    )
                    filled = browser.command("fill", fields=fields)
                    profile = _readback_profile(
                        snapshot.project, fields, filled, frozen is not None
                    )
                    if snapshot.profile is not None and profile != snapshot.profile["profile_json"]:
                        raise _Rejected("REJECTED_QB_PARAMS_CHANGED")
                    _remote_check(config, snapshot, config.workspace / _unit_hash(key))
                    _trace(
                        options.state_root,
                        key,
                        dict(
                            sbs_target=result["sbs_target"],
                            request_id=request_id,
                            fingerprint=filled["fingerprint"],
                            first_freeze=frozen is None,
                            snapshot_option_count=filled["snapshot_option_count"],
                        ),
                    )
                    seq = _intent(db, snapshot, profile, request_id, result["sbs_target"])
                    # Durable intent exists now; an unexpected failure cannot prove non-release.
                    result.update(request_seq=seq, status="QB_REQUESTED", action="submit_uncertain")
                    _submit(db, browser, result, filled["fingerprint"], options.state_root)
                    if result["action"] in {"submit_failed", "submit_uncertain"}:
                        exit_code = 5
            except (QbBrowserError, _Rejected, QbProjectNotReady, sandbox._Reject) as exc:
                result["error_code"] = exc.code
                exit_code = max(exit_code, 4 if exc.code.startswith("REJECTED_") else 5)
                if isinstance(exc, QbBrowserError):
                    _browser_failure_trace(options.state_root, key, exc)
                    if exc.snapshot_state is not None:
                        result["message"] = snapshot_message(
                            frozen_snapshot,
                            exc.snapshot_state["selected"],
                            exc.snapshot_state["option_count"],
                        )
                        try:
                            _trace(
                                options.state_root,
                                key,
                                dict(
                                    message=result["message"], skip_reason="qb_snapshot_unavailable"
                                ),
                            )
                        except (OSError, EvidenceRedactionError):
                            result["error_code"] = "QB_EVIDENCE_REDACTION_FAILED"
                            exit_code = 5
                    if exc.diagnostic is not None:
                        result["diagnostic_dir"] = _diagnostic(
                            options.state_root, key, exc.diagnostic
                        )
            except state.CampaignStateBusy:
                result["error_code"] = "CAMPAIGN_STATE_BUSY"
                exit_code = max(exit_code, 4)
            except state.StateInconsistent:
                result["error_code"] = "REJECTED_STATE_INCONSISTENT"
                exit_code = max(exit_code, 4)
            except EvidenceRedactionError:
                result["error_code"] = "QB_EVIDENCE_REDACTION_FAILED"
                exit_code = 5
            except Exception:
                result["error_code"] = "INTERNAL_ERROR"
                exit_code = 5
                traceback.print_exc(file=stderr)
    finally:
        if browser is not None:
            browser.close()
    return exit_code, results
