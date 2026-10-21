"""Shared manual/automatic request binding transaction, without browser I/O."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from tizen_ci_shared.state import StateDatabase

from ci_triage import campaign_state as state
from ci_triage import qb_result_html as pages
from ci_triage import sandbox_submit as sandbox


@contextmanager
def write(db: StateDatabase) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db.path.resolve().as_uri() + "?mode=rw", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        with state._immediate_transaction(conn):
            yield conn
    finally:
        conn.close()


def row(conn: sqlite3.Connection, sql: str, *args: Any) -> dict[str, Any] | None:
    found = conn.execute(sql, args).fetchone()
    return dict(found) if found is not None else None


def latest_request(conn: sqlite3.Connection, key: str) -> dict[str, Any] | None:
    return row(
        conn,
        "SELECT * FROM campaign_qb_requests WHERE campaign_unit_key=? "
        "ORDER BY request_seq DESC LIMIT 1",
        key,
    )


def event(conn: sqlite3.Connection, seq: int, kind: str) -> dict[str, Any] | None:
    return row(
        conn,
        "SELECT * FROM campaign_qb_events WHERE request_seq=? "
        "AND event_type=? ORDER BY event_id DESC LIMIT 1",
        seq,
        kind,
    )


def latest(conn: sqlite3.Connection, request: dict[str, Any]) -> None:
    current = latest_request(conn, request["campaign_unit_key"])
    pages.require(
        current is not None and current["request_seq"] == request["request_seq"],
        "superseded",
        "REJECTED_QB_SUPERSEDED",
    )


def automatic_allowed(conn: sqlite3.Connection, request: dict[str, Any]) -> None:
    latest(conn, request)
    pages.require(event(conn, request["request_seq"], "BUILD_BOUND") is None, "already_bound")
    pages.require(
        sandbox._status(conn, request["campaign_unit_key"]) == "QB_REQUESTED",
        "automatic_binding_state",
    )


def allowed(conn: sqlite3.Connection, request: dict[str, Any], build: str) -> None:
    latest(conn, request)
    bound = event(conn, request["request_seq"], "BUILD_BOUND")
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


def bind(db: StateDatabase, request: dict[str, Any], build: str) -> None:
    with write(db) as conn:
        allowed(conn, request, build)
        pages.require(event(conn, request["request_seq"], "BUILD_BOUND") is None, "binding_changed")
        pages.require(
            sandbox._status(conn, request["campaign_unit_key"]) == "QB_REQUESTED",
            "binding_state",
            "REJECTED_STATE_INCONSISTENT",
        )
        state._append_qb_event_on_connection(
            conn,
            request_seq=request["request_seq"],
            event_type="BUILD_BOUND",
            qb_build_id=build,
        )
        state._append_status_on_connection(conn, request["campaign_unit_key"], "QB_TRIGGERED")


def parent_facts(
    overview: str, variables: str, build: str, profile: dict[str, Any], request: dict[str, Any]
) -> dict[str, Any]:
    facts = pages.parent_overview(overview, f"/build/{build}/overview", profile)
    facts.update(
        pages.parent_variables(
            variables,
            build,
            request["request_id"],
            request["sbs_target"],
            profile,
        )
    )
    return facts
