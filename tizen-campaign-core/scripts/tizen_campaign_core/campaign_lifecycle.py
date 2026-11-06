"""Release recorded campaign copies without deleting source directories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tizen_ci_shared.state import StateDatabase
from tizen_ci_shared.workspace import is_protected, release_worktree_protection

from tizen_campaign_core import campaign_state as state

REJECTED_UNIT_ABANDONED = "REJECTED_UNIT_ABANDONED"
REJECTED_UNIT_NOT_TERMINAL = "REJECTED_UNIT_NOT_TERMINAL"
RELEASE_TERMINAL = frozenset(
    {"DENIED", "STALLED", "REGRESSED", "ROUNDS_EXHAUSTED", "REVIEW_PUSHED", "REVIEW_INELIGIBLE"}
)
RETAINED = frozenset({"HELD_FOR_INVESTIGATION", "WORKTREE_LOST", "SANDBOX_QB_FAILED"})
EMPTY_TERMINAL = frozenset({"NOT_REPRODUCED", "REJECTED_ARCH_NOT_ALLOWED"})
TERMINAL = RELEASE_TERMINAL | RETAINED | EMPTY_TERMINAL | {"REVIEW_MANUAL"}


class ReleaseNotAllowed(ValueError):
    """The current unit state does not authorize this release."""


def release_events(db: StateDatabase, key: str) -> list[dict[str, Any]]:
    conn = state._read_connection(db)
    try:
        return [
            json.loads(row[0])
            for row in conn.execute(
                "SELECT payload_json FROM campaign_gate_events WHERE campaign_unit_key=? "
                "AND event_type='WORKSPACE_RELEASE' ORDER BY event_id",
                (key,),
            )
        ]
    finally:
        conn.close()


def is_abandoned(db: StateDatabase, key: str) -> bool:
    return any(event["reason"] == "abandoned" for event in release_events(db, key))


def recorded_paths(db: StateDatabase, key: str) -> list[str]:
    conn = state._read_connection(db)
    try:
        state._require_unit(conn, key)
        paths = {
            str(row[0])
            for row in conn.execute(
                "SELECT vr.worktree_path FROM campaign_verifications cv "
                "JOIN verification_records vr "
                "ON vr.verification_id=cv.verification_id WHERE cv.campaign_unit_key=?",
                (key,),
            )
        }
        for row in conn.execute(
            "SELECT payload_json FROM campaign_gate_events WHERE campaign_unit_key=? "
            "AND event_type='ORPHAN_PASS'",
            (key,),
        ):
            paths.add(json.loads(row[0])["worktree_path"])
        return sorted(paths)
    finally:
        conn.close()


def _release(
    db: StateDatabase, key: str, reason: str, who: str | None = None, *, abandoned: bool = False
) -> list[str]:
    recorded = recorded_paths(db, key)
    done = {
        path
        for event in release_events(db, key)
        if event["reason"] == reason
        for path in event["paths"]
    }
    pending = [
        path for path in recorded if path not in done or (not abandoned and is_protected(path))
    ]
    for path in pending:
        try:
            if Path(path).exists() and is_protected(path):
                release_worktree_protection(path)
        except OSError as exc:
            raise state.StateInconsistent("worktree protection could not be released") from exc
    if pending:
        payload: dict[str, Any] = dict(paths=pending, reason=reason)
        if who is not None:
            payload["confirmed_by"] = who
        state.append_event(db, key, "WORKSPACE_RELEASE", payload)
    return pending


def release_terminal_worktrees(state_db: StateDatabase, campaign_unit_key: str) -> list[str]:
    if state.latest_status(state_db, campaign_unit_key) not in RELEASE_TERMINAL:
        raise ReleaseNotAllowed("unit is not in an automatic release state")
    return _release(state_db, campaign_unit_key, "terminal")


def release_held_worktrees(
    state_db: StateDatabase, campaign_unit_key: str, *, confirmed_by: str
) -> list[str]:
    if not confirmed_by.strip() or state.latest_status(state_db, campaign_unit_key) not in RETAINED:
        raise ReleaseNotAllowed("held release requires a retained state and confirmation")
    return _release(state_db, campaign_unit_key, "held", confirmed_by)


def release_abandoned_worktrees(
    state_db: StateDatabase, campaign_unit_key: str, *, confirmed_by: str
) -> list[str]:
    if not confirmed_by.strip() or (
        state.latest_status(state_db, campaign_unit_key) in TERMINAL
        and not is_abandoned(state_db, campaign_unit_key)
    ):
        raise ReleaseNotAllowed("abandon requires a nonterminal state and confirmation")
    return _release(state_db, campaign_unit_key, "abandoned_release", confirmed_by, abandoned=True)
