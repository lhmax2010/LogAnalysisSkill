"""Minimal lifecycle commands and a database-only campaign report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TextIO

from tizen_campaign_core import campaign_lifecycle as life
from tizen_campaign_core import campaign_state as state
from tizen_campaign_core._campaign_io import JsonParser, config
from tizen_campaign_core._campaign_workspace import _unit_hash
from tizen_ci_shared.state import StateDatabase
from tizen_sandbox_submit.sandbox_submit import _locks, _Reject


def finish(db: StateDatabase, key: str) -> tuple[int, dict[str, Any]]:
    status = state.latest_status(db, key)
    if status in life.RELEASE_TERMINAL:
        return 0, dict(released=life.release_terminal_worktrees(db, key), error_code=None)
    if status in life.EMPTY_TERMINAL:
        return 0, dict(released=[], error_code=None)
    if status in life.RETAINED:
        return 0, dict(retained=True, reason=status, error_code=None)
    return 4, dict(
        error_code=life.REJECTED_UNIT_NOT_TERMINAL,
        message="如决定放弃该 unit,用 campaign-release-worktrees --abandon",
    )


def release(
    db: StateDatabase, key: str, settings: dict[str, Any], who: str, abandon: bool
) -> list[str]:
    if not abandon:
        return life.release_held_worktrees(db, key, confirmed_by=who)
    root = Path(settings["campaign_workspace"]).resolve() / _unit_hash(key)
    with _locks(root):
        if not who.strip():
            raise life.ReleaseNotAllowed("confirmed-by must not be empty")
        if state.get_unit(db, key) is None:
            raise life.ReleaseNotAllowed("unknown unit")
        if not life.is_abandoned(db, key):
            if state.latest_status(db, key) in life.TERMINAL:
                raise life.ReleaseNotAllowed("terminal unit cannot be abandoned")
            state.append_event(
                db, key, "WORKSPACE_RELEASE", dict(paths=[], reason="abandoned", confirmed_by=who)
            )
        return life.release_abandoned_worktrees(db, key, confirmed_by=who)


def report(db: StateDatabase) -> list[dict[str, Any]]:
    conn = state._read_connection(db)
    try:
        conn.execute("BEGIN")
        result = []
        for unit in conn.execute(
            "SELECT * FROM campaign_units ORDER BY campaign_unit_key"
        ).fetchall():
            key = unit["campaign_unit_key"]
            status = conn.execute(
                "SELECT status,reason FROM campaign_status_log WHERE campaign_unit_key=? "
                "ORDER BY log_id DESC LIMIT 1",
                (key,),
            ).fetchone()
            events = [
                (row["event_type"], json.loads(row["payload_json"]))
                for row in conn.execute(
                    "SELECT event_type,payload_json FROM campaign_gate_events "
                    "WHERE campaign_unit_key=? ORDER BY event_id",
                    (key,),
                )
            ]
            abandoned = any(
                kind == "WORKSPACE_RELEASE" and event["reason"] == "abandoned"
                for kind, event in events
            )
            request = conn.execute(
                "SELECT request_seq FROM campaign_qb_requests WHERE campaign_unit_key=? "
                "ORDER BY request_seq DESC LIMIT 1",
                (key,),
            ).fetchone()
            parent = reference = None
            if request is not None:
                bound = conn.execute(
                    "SELECT qb_build_id FROM campaign_qb_events WHERE request_seq=? "
                    "AND event_type IN ('BUILD_BOUND','RESULT') AND qb_build_id IS NOT NULL "
                    "ORDER BY event_id DESC LIMIT 1",
                    (request[0],),
                ).fetchone()
                last = conn.execute(
                    "SELECT qb_result_ref FROM campaign_qb_events WHERE request_seq=? "
                    "AND event_type='RESULT' ORDER BY event_id DESC LIMIT 1",
                    (request[0],),
                ).fetchone()
                parent = bound[0] if bound else None
                reference = last[0] if last else None
            paths = {
                r[0]
                for r in conn.execute(
                    "SELECT vr.worktree_path FROM campaign_verifications cv "
                    "JOIN verification_records vr ON vr.verification_id=cv.verification_id "
                    "WHERE cv.campaign_unit_key=?",
                    (key,),
                )
            }
            paths.update(e["worktree_path"] for kind, e in events if kind == "ORPHAN_PASS")
            released = {
                path
                for kind, event in events
                if kind == "WORKSPACE_RELEASE"
                for path in event["paths"]
            }
            current = status[0] if status else None
            copy_state = "保留待查" if current in life.RETAINED else "在用"
            if released and paths.issubset(released):
                copy_state = "已释放"
            if abandoned:
                copy_state = "已放弃"
            reviews = [e for kind, e in events if kind == "REVIEW"]
            result.append(
                dict(
                    campaign_unit_key=key,
                    spec_name=unit["spec_name"],
                    project=unit["project"],
                    status=current,
                    reason="abandoned(状态列为放弃时及之后的状态)"
                    if abandoned
                    else (status[1] if status else None),
                    rounds=conn.execute(
                        "SELECT count(*) FROM campaign_rounds WHERE campaign_unit_key=?", (key,)
                    ).fetchone()[0],
                    invocations_used=sum(kind == "BUILD_INVOCATION" for kind, _ in events),
                    qb_build_id=parent,
                    qb_result_ref=reference,
                    review_url=reviews[-1].get("review_url") if reviews else None,
                    workspace_status=copy_state,
                )
            )
        return result
    finally:
        conn.close()


def markdown(rows: list[dict[str, Any]]) -> str:
    columns = {
        "spec_name": "包名",
        "project": "项目",
        "status": "最新状态",
        "reason": "终止原因",
        "rounds": "修复轮数",
        "invocations_used": "已用编译次数",
        "qb_build_id": "QuickBuild 父构建号",
        "qb_result_ref": "结果文件引用",
        "review_url": "review URL",
        "workspace_status": "副本状态",
    }
    lines = [
        "| " + " | ".join(columns.values()) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        cells = [
            "" if row[key] is None else str(row[key]).replace("|", "\\|").replace("\n", "<br>")
            for key in columns
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main(command: str, argv: list[str], *, stdout: TextIO) -> int:
    parser = JsonParser(prog="tizen_campaign_report " + command)
    parser.add_argument("--state-db", type=Path, required=True)
    if command == "campaign-report":
        parser.add_argument("--output", type=Path)
    else:
        parser.add_argument("--config", type=Path, required=True)
        parser.add_argument("--campaign-unit-key", required=True)
        if command == "campaign-release-worktrees":
            parser.add_argument("--confirmed-by", required=True)
            parser.add_argument("--abandon", action="store_true")
    try:
        args = parser.parse_args(argv)
        db = StateDatabase(args.state_db)
        if command == "campaign-report":
            result: Any = report(db)
            if args.output:
                args.output.write_text(markdown(result), encoding="utf-8")
            code = 0
        else:
            settings = config(args.config)
            if command == "campaign-finish-unit":
                code, result = finish(db, args.campaign_unit_key)
            else:
                result = dict(
                    released=release(
                        db, args.campaign_unit_key, settings, args.confirmed_by, args.abandon
                    ),
                    error_code=None,
                )
                code = 0
    except life.ReleaseNotAllowed as exc:
        code, result = 4, dict(error_code="ReleaseNotAllowed", reason=str(exc))
    except _Reject as exc:
        code, result = exc.exit_code, dict(error_code=exc.code, reason=exc.detail)
    except state.StateInconsistent as exc:
        code, result = 4, dict(error_code="REJECTED_STATE_INCONSISTENT", reason=str(exc))
    except (ValueError, OSError) as exc:
        code, result = 2, dict(error_code="INVALID_ARGS", reason=str(exc))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), file=stdout)
    return code
