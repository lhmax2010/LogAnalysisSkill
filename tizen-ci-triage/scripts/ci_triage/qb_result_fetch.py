"""Fetch and bind campaign QB results through the read-only browser protocol."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
import traceback
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Any, TextIO

import yaml
from tizen_ci_shared.state import StateDatabase

from ci_triage import campaign_state as state
from ci_triage import qb_binding as binding
from ci_triage import qb_discovery as discovery
from ci_triage import qb_result_html as pages
from ci_triage import qb_trigger as trigger
from ci_triage import sandbox_submit as sandbox
from ci_triage._campaign_workspace import _unit_hash
from ci_triage.qb_browser import QbBrowser, QbBrowserError, _check_diagnostic_strings
from ci_triage.qb_config import parse_qb_config
from ci_triage.qb_evidence import archive
from ci_triage.qb_redact import EvidenceRedactionError, PageRedactor

RESULT_KEYS = frozenset(
    {
        "qb_build_id",
        "child_build_id",
        "status",
        "sbs_target_echo",
        "per_arch_status",
        "accepted",
        "configuration_path",
        "child_configuration_path",
        "parent_status_text",
        "child_status_text",
        "child_build_result_text",
        "child_failed_step",
        "child_error_message",
        "request_marker_echo",
        "params_echo",
        "child_params_echo",
        "snapshot_used",
        "snapshot_drift_accepted",
        "pkg_list_echo",
        "evidence",
        "fetched_at",
    }
)
DRIFT_GUIDANCE = (
    "该 unit 的复验基准已漂移(参考快照可能在构建期间滚动),须由人裁定:确认构建内容仍可比,"
    "则对该 request 加 `--accept-snapshot-drift` 重跑 fetch;否则在新 campaign 中重做"
)
SNAPSHOT_GUIDANCE = (
    "子构建快照地址的主机、路径根或形态与登记不符,须人工核对后按 R1 修订附录 C 第 6 项的登记"
)
EACH_GUIDANCE = (
    "EACH_GBS_BUILD_STATUS 非空且格式尚未取证;不得人工降级或 --retrigger。"
    "须用本次样本按 R1 定义解析规则、升设计版本后重跑 fetch"
)


@dataclass(frozen=True)
class QbResultFetchOptions:
    state_db: Path
    state_root: Path
    config: Path
    request_id: str | None = None
    qb_build_id: str | None = None
    requests_file: Path | None = None
    accept_snapshot_drift: bool = False


@dataclass(frozen=True)
class RequestView:
    request: dict[str, Any]
    build: str
    profile: dict[str, Any]
    bound: dict[str, Any] | None
    result: dict[str, Any] | None

    @property
    def key(self) -> str:
        return str(self.request["campaign_unit_key"])


def empty_result() -> dict[str, Any]:
    return dict(
        request_id=None,
        qb_build_id=None,
        child_build_id=None,
        status=None,
        terminal=False,
        result_event_id=None,
        qb_result_path=None,
        error_code=None,
        diagnostic_dir=None,
        message=None,
    )


def _selections(options: QbResultFetchOptions) -> list[dict[str, str]]:
    if options.accept_snapshot_drift and (not options.request_id or options.requests_file):
        raise ValueError("accept drift requires a single request-id")
    if options.requests_file and (
        options.request_id is not None or options.qb_build_id is not None
    ):
        raise ValueError("exclusive selection")
    rows = (
        json.loads(options.requests_file.read_bytes())
        if options.requests_file
        else [
            {
                k: v
                for k, v in {
                    "request_id": options.request_id,
                    "qb_build_id": options.qb_build_id,
                }.items()
                if v is not None
            }
        ]
    )
    if not isinstance(rows, list) or not rows:
        raise ValueError("nonempty requests required")
    for row in rows:
        if not isinstance(row, dict) or not row or not set(row) <= {"request_id", "qb_build_id"}:
            raise ValueError("invalid reference")
        for key, value in row.items():
            pattern = r"[0-9a-f]{32}" if key == "request_id" else r"[1-9][0-9]*"
            if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
                raise ValueError("invalid reference value")
    return rows


def _request(conn: sqlite3.Connection, selection: dict[str, str]) -> dict[str, Any]:
    if "request_id" in selection:
        row = trigger._row(
            conn, "SELECT * FROM campaign_qb_requests WHERE request_id=?", selection["request_id"]
        )
        pages.require(row is not None, "missing_request")
        assert row is not None
        return row
    rows = conn.execute(
        "SELECT DISTINCT r.* FROM campaign_qb_requests r JOIN campaign_qb_events e "
        "ON r.request_seq=e.request_seq WHERE e.event_type='BUILD_BOUND' AND e.qb_build_id=?",
        (selection["qb_build_id"],),
    ).fetchall()
    if len({r["campaign_unit_key"] for r in rows}) > 1:
        raise pages.ResultCheckError("AmbiguousQbReference", "ambiguous_build")
    pages.require(len(rows) == 1, "unbound_build")
    return dict(rows[0])


def _event(conn: sqlite3.Connection, seq: int, kind: str) -> dict[str, Any] | None:
    return trigger._row(
        conn,
        "SELECT * FROM campaign_qb_events WHERE request_seq=? "
        "AND event_type=? ORDER BY event_id DESC LIMIT 1",
        seq,
        kind,
    )


def _latest(conn: sqlite3.Connection, request: dict[str, Any]) -> None:
    latest = trigger._latest_request(conn, request["campaign_unit_key"])
    pages.require(
        latest is not None and latest["request_seq"] == request["request_seq"],
        "superseded",
        "REJECTED_QB_SUPERSEDED",
    )


def _binding_allowed(conn: sqlite3.Connection, request: dict[str, Any], build: str) -> None:
    _latest(conn, request)
    bound = _event(conn, request["request_seq"], "BUILD_BOUND")
    pages.require(bound is None or bound["qb_build_id"] == build, "different_binding")
    pages.require(
        sandbox._status(conn, request["campaign_unit_key"]) != "QB_SUBMIT_FAILED", "not_released"
    )
    other = conn.execute(
        "SELECT 1 FROM campaign_qb_events WHERE event_type='BUILD_BOUND' "
        "AND qb_build_id=? AND request_seq<>?",
        (build, request["request_seq"]),
    ).fetchone()
    pages.require(other is None, "other_binding")


def _view(db: StateDatabase, selection: dict[str, str], key: str) -> RequestView:
    conn = state._read_connection(db)
    try:
        conn.execute("BEGIN")
        request = _request(conn, selection)
        pages.require(
            request["campaign_unit_key"] == key, "unit_changed", "REJECTED_STATE_INCONSISTENT"
        )
        _latest(conn, request)
        bound = _event(conn, request["request_seq"], "BUILD_BOUND")
        build = selection.get("qb_build_id", bound["qb_build_id"] if bound else "")
        if build:
            _binding_allowed(conn, request, build)
        else:
            binding.automatic_allowed(conn, request)
        unit = state._require_unit(conn, key)
        stored = trigger._profile(conn, unit.branch)
        pages.require(stored is not None, "missing_profile", "REJECTED_STATE_INCONSISTENT")
        assert stored is not None
        raw = stored["profile_json"]
        pages.require(
            hashlib.sha256(raw.encode()).hexdigest() == stored["profile_sha256"],
            "profile_hash",
            "REJECTED_STATE_INCONSISTENT",
        )
        return RequestView(
            request, build, json.loads(raw), bound, _event(conn, request["request_seq"], "RESULT")
        )
    finally:
        conn.close()


def _manual_bind(db: StateDatabase, view: RequestView) -> None:
    if view.bound is not None:
        return
    binding.bind(db, view.request, view.build)


def _diagnostic(root: Path, key: str, diagnostic: dict[str, Any]) -> str | None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = root / "qb_diagnostics" / f"{stamp}-{_unit_hash(key)}"
    redactor = PageRedactor()
    html = diagnostic["html_redacted"].encode("utf-8")
    facts = {name: value for name, value in diagnostic.items() if name != "html_redacted"}
    try:
        redactor.check_bytes(html)
        _check_diagnostic_strings(facts, redactor)
        directory.mkdir(parents=True)
        (directory / "page.html").write_bytes(html)
        (directory / "structure.json").write_text(
            json.dumps(facts, ensure_ascii=False), encoding="utf-8"
        )
        redactor.check_bytes((directory / "page.html").read_bytes())
        _check_diagnostic_strings(json.loads((directory / "structure.json").read_bytes()), redactor)
        return str(directory)
    except OSError:
        shutil.rmtree(directory, ignore_errors=True)
        return None
    except (ValueError, EvidenceRedactionError):
        shutil.rmtree(directory, ignore_errors=True)
        raise EvidenceRedactionError("diagnostic redaction failed") from None


def _read_page(
    browser: QbBrowser,
    root: Path,
    view: RequestView,
    path: str,
    evidence: list[str],
    result: dict[str, Any],
    *,
    optional: bool = False,
) -> str | None:
    try:
        reply = browser.command("read", path=path)
    except QbBrowserError as exc:
        trigger._browser_failure_trace(root, view.key, exc)
        if exc.diagnostic is not None:
            result["diagnostic_dir"] = _diagnostic(root, view.key, exc.diagnostic)
        if optional and exc.agent_code in {"QB_READ_REDIRECTED", "QB_READ_ID_MISMATCH"}:
            return None
        raise
    html, status = reply.get("html_redacted"), reply.get("status")
    count = reply.get("outside_identity_count")
    if not isinstance(html, str) or type(status) is not int or type(count) is not int or count < 0:
        raise QbBrowserError("QB_BROWSER_UNAVAILABLE")
    evidence.append(archive(root, view.request["request_id"], path, html))
    trigger._trace(
        root,
        view.key,
        dict(request_id=view.request["request_id"], path=path, outside_identity_count=count),
    )
    if status != 200:
        if optional:
            return None
        raise QbBrowserError("QB_FETCH_FAILED")
    return html


def _previous_drift(root: Path, view: RequestView, actual: str) -> bool:
    if view.result is None:
        return False
    ref = view.result["qb_result_ref"]
    if not isinstance(ref, str):
        raise state.StateInconsistent("missing previous result")
    path = (root / ref).resolve()
    if not path.is_relative_to(root.resolve()):
        raise state.StateInconsistent("invalid result path")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != view.result["qb_result_sha256"]:
        raise state.StateInconsistent("result hash mismatch")
    previous = json.loads(raw)
    return (
        previous.get("snapshot_drift_accepted") is True and previous.get("snapshot_used") == actual
    )


def _guidance(
    root: Path, view: RequestView, output: dict[str, Any], message: str, evidence: list[str]
) -> None:
    message += ";证据:" + ",".join(evidence)
    _check_diagnostic_strings(message, PageRedactor())
    output["message"] = message
    trigger._trace(
        root,
        view.key,
        dict(request_id=view.request["request_id"], message=message, evidence=evidence),
    )


def _collect(
    browser: QbBrowser,
    db: StateDatabase,
    root: Path,
    view: RequestView,
    output: dict[str, Any],
    accept: bool,
    discovered: discovery.Discovery | None = None,
) -> dict[str, Any]:
    evidence: list[str] = list(discovered.evidence) if discovered else []
    parent = view.build

    def read(path: str) -> str | None:
        return _read_page(browser, root, view, path, evidence, output)

    if discovered is not None:
        assert discovered.facts is not None
        facts = dict(discovered.facts)
    else:
        overview = read(f"/build/{parent}/overview")
        variables = read(f"/build/{parent}/variables")
        assert overview is not None and variables is not None
        facts = binding.parent_facts(overview, variables, parent, view.profile, view.request)
        _manual_bind(db, view)
    child = facts["child_build_id"]
    if child is None:
        return dict(status="QUEUED", child_build_id=None)
    output["child_build_id"] = child
    overview = read(f"/build/{child}/overview")
    variables = read(f"/build/{child}/variables")
    assert overview is not None and variables is not None
    facts.update(pages.child_overview(overview, view.profile, facts["child_build_result_text"]))
    facts.update(pages.child_variables(variables, parent, child, view.request["sbs_target"]))
    frozen = view.profile["form"]["SNAPSHOT_NUM"]
    kind, actual = pages.snapshot_kind(facts["child_params_echo"]["SNAPSHOT_NUM_URL"], frozen)
    accepted = kind == "drift" and (accept or _previous_drift(root, view, actual))
    if kind == "unsupported" or kind == "drift" and not accepted:
        _guidance(
            root,
            view,
            output,
            f"冻结值:{frozen};实际值:{actual};"
            + (DRIFT_GUIDANCE if kind == "drift" else SNAPSHOT_GUIDANCE),
            evidence,
        )
        raise pages.ResultCheckError(pages.UNRECOGNIZED, "snapshot")
    if accepted:
        trigger._trace(
            root,
            view.key,
            dict(
                request_id=view.request["request_id"],
                frozen_snapshot=frozen,
                actual_snapshot=actual,
            ),
        )
    facts.update(snapshot_used=actual, snapshot_drift_accepted=bool(accepted))
    if facts.pop("each_status"):
        _guidance(root, view, output, EACH_GUIDANCE, evidence)
        raise pages.ResultCheckError(pages.UNRECOGNIZED, "each_status")
    facts["child_failed_step"] = None
    if facts["status"] in pages.TERMINAL - {"PASS"}:
        steps = _read_page(
            browser, root, view, f"/build/{child}/step_status", evidence, output, optional=True
        )
        if steps is not None:
            facts["child_failed_step"] = pages.failed_steps(steps)
    if facts["child_failed_step"] is None:
        facts["child_error_message"] = None
    facts.update(
        qb_build_id=parent,
        configuration_path=view.profile["configuration_path"],
        evidence=evidence,
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )
    return facts


def _publish(root: Path, request: str, facts: dict[str, Any]) -> tuple[Path, str]:
    pages.require(set(facts) == RESULT_KEYS, "result_schema", "REJECTED_STATE_INCONSISTENT")
    pages.require(
        set(facts["child_params_echo"]) == {"BUILD_REFERENCE", "SNAPSHOT_NUM_URL"},
        "child_schema",
        "REJECTED_STATE_INCONSISTENT",
    )
    _check_diagnostic_strings(facts, PageRedactor())
    directory = root / "qb_results" / request
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    raw = json.dumps(facts, ensure_ascii=False, sort_keys=True).encode("utf-8")
    temp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, delete=False) as stream:
            temp = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, destination)
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except BaseException:
        if temp is not None:
            temp.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise
    return destination, hashlib.sha256(raw).hexdigest()


def _persist(
    db: StateDatabase, root: Path, view: RequestView, facts: dict[str, Any]
) -> dict[str, Any] | None:
    terminal = facts["status"] in pages.TERMINAL
    output, digest = _publish(root, view.request["request_id"], facts) if terminal else (None, None)
    keep = False
    try:
        with trigger._write(db) as conn:
            _latest(conn, view.request)
            current = trigger._row(
                conn,
                "SELECT * FROM campaign_qb_requests WHERE request_seq=?",
                view.request["request_seq"],
            )
            bound = _event(conn, view.request["request_seq"], "BUILD_BOUND")
            pages.require(
                bound is not None
                and bound["qb_build_id"] == view.build
                and current is not None
                and current["sbs_target"] == view.request["sbs_target"],
                "binding_changed",
                "REJECTED_STATE_INCONSISTENT",
            )
            assert current is not None
            previous = _event(conn, view.request["request_seq"], "RESULT")
            if previous is not None:
                pages.require(
                    previous["status"] == facts["status"],
                    "terminal_changed",
                    "REJECTED_STATE_INCONSISTENT",
                )
                if (
                    previous["accepted"] == facts["accepted"]
                    and previous["sbs_target_echo"] == facts["sbs_target_echo"]
                    and previous["per_arch_status_json"] is None
                ):
                    return previous
            else:
                pages.require(
                    sandbox._status(conn, view.key) in {"QB_TRIGGERED", "SANDBOX_QB_PENDING"},
                    "result_state",
                    "REJECTED_STATE_INCONSISTENT",
                )
            if not terminal:
                if sandbox._status(conn, view.key) != "SANDBOX_QB_PENDING":
                    state._append_status_on_connection(conn, view.key, "SANDBOX_QB_PENDING")
                return None
            assert output is not None
            pages.require(
                facts["sbs_target_echo"] == current["sbs_target"],
                "target_changed",
                "REJECTED_STATE_INCONSISTENT",
            )
            event_id = state._append_qb_event_on_connection(
                conn,
                request_seq=view.request["request_seq"],
                event_type="RESULT",
                qb_build_id=view.build,
                status=facts["status"],
                accepted=facts["accepted"],
                sbs_target_echo=facts["sbs_target_echo"],
                per_arch_status_json=None,
                qb_result_sha256=digest,
                qb_result_ref=str(output.relative_to(root)),
            )
            if previous is None:
                state._append_status_on_connection(
                    conn,
                    view.key,
                    "SANDBOX_QB_PASS" if facts["status"] == "PASS" else "SANDBOX_QB_FAILED",
                )
            event = trigger._row(
                conn, "SELECT * FROM campaign_qb_events WHERE event_id=?", event_id
            )
        keep = True
        return event
    finally:
        if output is not None and not keep:
            output.unlink(missing_ok=True)


def qb_result_fetch(
    options: QbResultFetchOptions, *, stderr: TextIO
) -> tuple[int, list[dict[str, Any]]]:
    try:
        selections = _selections(options)
        config = yaml.safe_load(options.config.read_text(encoding="utf-8"))
        qb = parse_qb_config(config.get("qb") if isinstance(config, dict) else None)
        workspace = Path(config["campaign_workspace"])
    except (ValueError, TypeError, KeyError, OSError, yaml.YAMLError):
        return 2, [dict(empty_result(), error_code="INVALID_ARGS")]
    db = StateDatabase(options.state_db)
    browser: QbBrowser | None = None
    results = []
    exit_code = 0
    login_failed = False
    key = "unselected"
    try:
        for selection in selections:
            result = {**empty_result(), **selection}
            results.append(result)
            key = "unselected"
            try:
                conn = state._read_connection(db)
                try:
                    key = _request(conn, selection)["campaign_unit_key"]
                finally:
                    conn.close()
                with trigger._lock(workspace / _unit_hash(key)):
                    view = _view(db, selection, key)
                    result.update(
                        request_id=view.request["request_id"], qb_build_id=view.build or None
                    )
                    if login_failed:
                        raise QbBrowserError("QB_FETCH_FAILED")
                    if browser is None:
                        browser = QbBrowser(qb)
                        browser.__enter__()
                        try:
                            browser.login()
                        except QbBrowserError:
                            login_failed = True
                            raise
                    found = None
                    if not view.build:
                        found = discovery.discover(
                            browser,
                            db,
                            options.state_root,
                            view.request,
                            view.profile,
                            baseline_w=0,
                            submitted_at=None,
                            trace=partial(trigger._trace, options.state_root, key),
                        )
                        if found.category != "已绑定":
                            result["message"] = (
                                f"自动查找:{found.category},已核对 {len(found.checked)} 个候选,"
                                f"{len(found.unreadable)} 个暂不可读,"
                                f"构建号:{','.join(found.builds)};"
                                "可稍后重试,或人工查到构建号后同时给 --qb-build-id 绑定"
                            )
                            code = {
                                "配置页不可识别": pages.UNRECOGNIZED,
                                "配置页读取失败": "QB_FETCH_FAILED",
                                "读取失败": "QB_FETCH_FAILED",
                                "证据脱敏自检失败": "QB_EVIDENCE_REDACTION_FAILED",
                            }.get(found.category, pages.BINDING)
                            raise pages.ResultCheckError(code, "discovery")
                        view = replace(view, build=found.builds[0])
                        result["qb_build_id"] = view.build
                    facts = _collect(
                        browser,
                        db,
                        options.state_root,
                        view,
                        result,
                        options.accept_snapshot_drift,
                        found,
                    )
                    event = _persist(db, options.state_root, view, facts)
                    result.update(
                        status=facts["status"],
                        terminal=facts["status"] in pages.TERMINAL,
                        result_event_id=event["event_id"] if event else None,
                        qb_result_path=event["qb_result_ref"] if event else None,
                    )
            except pages.ResultCheckError as exc:
                result["error_code"] = exc.code
                exit_code = max(
                    exit_code,
                    5
                    if exc.code
                    in {pages.UNRECOGNIZED, "QB_FETCH_FAILED", "QB_EVIDENCE_REDACTION_FAILED"}
                    else 4,
                )
            except QbBrowserError as exc:
                trigger._browser_failure_trace(options.state_root, key, exc)
                result["error_code"] = (
                    "QB_EVIDENCE_REDACTION_FAILED"
                    if exc.code == "QB_EVIDENCE_REDACTION_FAILED"
                    else "QB_FETCH_FAILED"
                )
                exit_code = 5
            except EvidenceRedactionError:
                result["error_code"] = "QB_EVIDENCE_REDACTION_FAILED"
                exit_code = 5
            except state.CampaignStateBusy:
                result["error_code"] = "CAMPAIGN_STATE_BUSY"
                exit_code = max(exit_code, 4)
            except state.StateInconsistent:
                result["error_code"] = "REJECTED_STATE_INCONSISTENT"
                exit_code = max(exit_code, 4)
            except Exception:
                result["error_code"] = "INTERNAL_ERROR"
                exit_code = 5
                traceback.print_exc(file=stderr)
    finally:
        if browser is not None:
            trigger._close_browser(browser, options.state_root, key)
    return exit_code, results
