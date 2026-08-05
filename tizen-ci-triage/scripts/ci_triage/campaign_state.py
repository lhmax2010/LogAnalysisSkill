"""Append-only state primitives for clang fix campaigns.

The campaign schema is additive: it is initialized after ``StateDatabase.connect``
and never alters the existing verification, status, or submission tables.  The
database remains a strong workflow constraint, not physical isolation from another
process running as the same OS user.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ci_triage.state import StateDatabase
from ci_triage.verify.convergence import _error_count, _primary_fingerprint

CAMPAIGN_SCHEMA_VERSION = "campaign/v1"
HELD_FOR_INVESTIGATION = "HELD_FOR_INVESTIGATION"
REJECTED_ARCH_NOT_ALLOWED = "REJECTED_ARCH_NOT_ALLOWED"

ARCH_RAW_TO_NORM = {
    "standard-aarch64": "aarch64",
    "standard-armv7l": "armv7l",
    "standard-x86_64": "x86_64",
}
ARCH_NORMS = frozenset(ARCH_RAW_TO_NORM.values())
_FAILED_ARCH_ORDER = (
    "standard-aarch64",
    "standard-armv7l",
    "standard-x86_64",
    "emulator-x86_64",
    "standard_gcov-armv7l",
)

_KNOWN_EVENT_TYPES = frozenset(
    {
        "REPRODUCE",
        "BUILD_INVOCATION",
        "ORPHAN_PASS",
        "POLICY",
        "DERIVE",
        "PUSH",
        "KB",
        "REVIEW",
        "CONVERGENCE",
        "SECONDARY_TARGET_ADOPTED",
        "WORKSPACE_CLEANUP",
        "WORKSPACE_RELEASE",
    }
)
_CONVERGENCE_NA_REASONS = frozenset(
    {
        "orphan_invocation",
        "rebaselined",
        "apply_failed",
        "analyzer_failed",
        "toolchain_failed",
        "previous_evidence_missing",
    }
)
_ARCH_SCOPED_HELD_REASONS = frozenset(
    {
        "previous_evidence_missing",
        "orphan_pass",
        "link_mismatch",
        "verification_mismatch",
    }
)
_IDENTITY_FIELDS = (
    "ci_system",
    "source_build_id",
    "project",
    "branch",
    "spec_name",
    "base_commit",
)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS campaign_units (
  campaign_unit_key        TEXT PRIMARY KEY,
  ci_system                TEXT NOT NULL,
  source_build_id          TEXT NOT NULL,
  project                  TEXT NOT NULL,
  branch                   TEXT NOT NULL,
  spec_name                TEXT NOT NULL,
  base_commit              TEXT NOT NULL,
  submission_identity_key  TEXT NOT NULL,
  toolchain_profile        TEXT NOT NULL,
  ci_evidence_ref          TEXT,
  ci_evidence_sha256       TEXT,
  primary_arch             TEXT,
  max_rounds               INTEGER NOT NULL CHECK (max_rounds >= 1),
  max_build_invocations    INTEGER NOT NULL CHECK (max_build_invocations >= 1),
  failed_arches            TEXT NOT NULL,
  created_at               TEXT NOT NULL,
  schema_version           TEXT NOT NULL,
  CHECK (
    (primary_arch IS NULL AND ci_evidence_ref IS NULL
      AND ci_evidence_sha256 IS NULL)
    OR
    (primary_arch IS NOT NULL AND ci_evidence_ref IS NOT NULL
      AND ci_evidence_sha256 IS NOT NULL)
  )
);

CREATE TABLE IF NOT EXISTS campaign_gate_events (
  event_id            INTEGER PRIMARY KEY AUTOINCREMENT,
  campaign_unit_key   TEXT NOT NULL,
  round_index         INTEGER,
  arch_norm           TEXT,
  verdict             TEXT,
  invocation_event_id INTEGER,
  event_type          TEXT NOT NULL,
  payload_json        TEXT NOT NULL,
  created_at          TEXT NOT NULL,
  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key)
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_convergence_per_invocation
  ON campaign_gate_events (invocation_event_id)
  WHERE event_type = 'CONVERGENCE' AND invocation_event_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_gate_unit_type
  ON campaign_gate_events (campaign_unit_key, event_type, event_id);

CREATE TABLE IF NOT EXISTS campaign_status_log (
  log_id            INTEGER PRIMARY KEY AUTOINCREMENT,
  campaign_unit_key TEXT NOT NULL,
  status            TEXT NOT NULL,
  reason            TEXT,
  arch_norm         TEXT,
  created_at        TEXT NOT NULL,
  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key)
);
CREATE INDEX IF NOT EXISTS ix_status_unit
  ON campaign_status_log (campaign_unit_key, log_id);

CREATE TABLE IF NOT EXISTS campaign_rounds (
  campaign_unit_key TEXT NOT NULL,
  round_index       INTEGER NOT NULL CHECK (round_index >= 1),
  edit_spec_ref     TEXT NOT NULL,
  edit_spec_sha256  TEXT NOT NULL,
  created_at        TEXT NOT NULL,
  PRIMARY KEY (campaign_unit_key, round_index),
  UNIQUE (campaign_unit_key, edit_spec_sha256),
  UNIQUE (campaign_unit_key, round_index, edit_spec_sha256),
  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key)
);

CREATE TABLE IF NOT EXISTS campaign_verifications (
  link_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  campaign_unit_key       TEXT NOT NULL,
  arch_raw                TEXT NOT NULL,
  arch_norm               TEXT NOT NULL,
  verification_id         TEXT NOT NULL UNIQUE,
  round_index             INTEGER NOT NULL,
  edit_spec_sha256        TEXT NOT NULL,
  campaign_schema_version TEXT NOT NULL,
  created_at              TEXT NOT NULL,
  UNIQUE (campaign_unit_key, arch_norm, round_index),
  FOREIGN KEY (campaign_unit_key, round_index, edit_spec_sha256)
    REFERENCES campaign_rounds (campaign_unit_key, round_index, edit_spec_sha256),
  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key),
  FOREIGN KEY (verification_id) REFERENCES verification_records (verification_id)
);

CREATE TABLE IF NOT EXISTS campaign_qb_requests (
  request_seq       INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id        TEXT NOT NULL UNIQUE,
  campaign_unit_key TEXT NOT NULL,
  sbs_target        TEXT NOT NULL,
  created_at        TEXT NOT NULL,
  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key)
);
CREATE INDEX IF NOT EXISTS ix_qb_req_unit
  ON campaign_qb_requests (campaign_unit_key, request_seq);

CREATE TABLE IF NOT EXISTS campaign_qb_events (
  event_id              INTEGER PRIMARY KEY AUTOINCREMENT,
  request_seq           INTEGER NOT NULL,
  event_type            TEXT NOT NULL
                        CHECK (event_type IN ('SUBMITTED','BUILD_BOUND','RESULT')),
  qb_build_id           TEXT,
  status                TEXT,
  accepted              INTEGER,
  sbs_target_echo       TEXT,
  per_arch_status_json  TEXT,
  qb_result_sha256      TEXT,
  qb_result_ref         TEXT,
  degraded              INTEGER NOT NULL DEFAULT 0,
  created_at            TEXT NOT NULL,
  FOREIGN KEY (request_seq) REFERENCES campaign_qb_requests (request_seq)
);
CREATE INDEX IF NOT EXISTS ix_qb_ev_req
  ON campaign_qb_events (request_seq, event_id);
CREATE INDEX IF NOT EXISTS ix_qb_ev_build
  ON campaign_qb_events (qb_build_id);
"""


class CampaignStateError(RuntimeError):
    """Base class for campaign-state contract failures."""


class StateInconsistent(CampaignStateError):
    """Stored state conflicts with the requested append-only transition."""


class PayloadSchemaError(CampaignStateError, ValueError):
    """A gate event payload does not satisfy its frozen schema."""


class UnknownEventType(PayloadSchemaError):
    """A caller attempted to write an unregistered gate event type."""


class RoundsExhausted(CampaignStateError):
    """The unit has consumed its edit-spec round budget."""


class BudgetExhausted(CampaignStateError):
    """The unit has consumed its build invocation budget."""


class CampaignStateBusy(CampaignStateError):
    """SQLite could not acquire the required immediate write lock."""


@dataclass(frozen=True)
class Unit:
    campaign_unit_key: str
    ci_system: str
    source_build_id: str
    project: str
    branch: str
    spec_name: str
    base_commit: str
    submission_identity_key: str
    toolchain_profile: str
    ci_evidence_ref: str | None
    ci_evidence_sha256: str | None
    primary_arch: str | None
    max_rounds: int
    max_build_invocations: int
    failed_arches: tuple[str, ...]
    created_at: str
    schema_version: str


@dataclass(frozen=True)
class Round:
    campaign_unit_key: str
    round_index: int
    edit_spec_ref: str
    edit_spec_sha256: str
    created_at: str


@dataclass(frozen=True)
class InvocationReceipt:
    event_id: int
    invocations_used: int
    invocations_remaining: int


@dataclass(frozen=True)
class ReconcileResult:
    branch: str
    current_verification_id: str | None
    current_relinked_invocation_event_id: int | None
    other_round_relinks: tuple[tuple[int, str, int], ...]
    backfilled_invocation_event_ids: tuple[int, ...]
    orphan_pass_verification_ids: tuple[str, ...]
    held_rounds: tuple[int, ...]
    non_campaign_verification_ids: tuple[str, ...]


def ensure_schema(state_db: StateDatabase) -> None:
    """Create all seven additive campaign tables and their indexes."""

    conn = state_db.connect()
    try:
        _ensure_schema_on_connection(conn)
    finally:
        conn.close()


def create_unit(
    state_db: StateDatabase,
    *,
    campaign_unit_key: str,
    submission_identity_key: str,
    primary_arch: str,
    failed_arches: Sequence[str],
    toolchain_profile: str,
    ci_evidence_ref: str,
    ci_evidence_sha256: str,
    max_rounds: int,
    max_build_invocations: int,
    **identity_fields: str,
) -> None:
    """Insert one normal campaign unit, or no-op on an exact retry."""

    if not primary_arch or primary_arch not in ARCH_RAW_TO_NORM:
        raise ValueError("primary_arch must be one of the verified standard arches")
    if not ci_evidence_ref or not ci_evidence_sha256:
        raise ValueError("create_unit requires non-empty CI evidence fields")
    values = _unit_values(
        campaign_unit_key=campaign_unit_key,
        submission_identity_key=submission_identity_key,
        primary_arch=primary_arch,
        failed_arches=failed_arches,
        toolchain_profile=toolchain_profile,
        ci_evidence_ref=ci_evidence_ref,
        ci_evidence_sha256=ci_evidence_sha256,
        max_rounds=max_rounds,
        max_build_invocations=max_build_invocations,
        identity_fields=identity_fields,
    )
    conn = _connect(state_db)
    try:
        with _immediate_transaction(conn):
            _insert_or_compare_unit(conn, values)
    finally:
        conn.close()


def create_arch_rejected_unit(
    state_db: StateDatabase,
    *,
    campaign_unit_key: str,
    submission_identity_key: str,
    failed_arches: Sequence[str],
    reason: str,
    toolchain_profile: str,
    max_rounds: int,
    max_build_invocations: int,
    **identity_fields: str,
) -> None:
    """Atomically insert an arch-rejected unit and its terminal status."""

    if not reason:
        raise ValueError("arch rejection reason must be non-empty")
    values = _unit_values(
        campaign_unit_key=campaign_unit_key,
        submission_identity_key=submission_identity_key,
        primary_arch=None,
        failed_arches=failed_arches,
        toolchain_profile=toolchain_profile,
        ci_evidence_ref=None,
        ci_evidence_sha256=None,
        max_rounds=max_rounds,
        max_build_invocations=max_build_invocations,
        identity_fields=identity_fields,
    )
    conn = _connect(state_db)
    try:
        with _immediate_transaction(conn):
            inserted = _insert_or_compare_unit(conn, values)
            existing = conn.execute(
                "SELECT status, reason, arch_norm FROM campaign_status_log "
                "WHERE campaign_unit_key = ? ORDER BY log_id DESC LIMIT 1",
                (campaign_unit_key,),
            ).fetchone()
            if existing is None:
                _insert_status_row(
                    conn,
                    campaign_unit_key,
                    REJECTED_ARCH_NOT_ALLOWED,
                    reason,
                    None,
                )
            elif (
                _text(existing, "status") != REJECTED_ARCH_NOT_ALLOWED
                or _optional_text(existing, "reason") != reason
                or existing["arch_norm"] is not None
            ):
                raise StateInconsistent("arch-rejected unit has a conflicting latest status")
            elif inserted:
                raise StateInconsistent("new arch-rejected unit unexpectedly had a status row")
    finally:
        conn.close()


def get_unit(state_db: StateDatabase, campaign_unit_key: str) -> Unit | None:
    conn = _connect(state_db)
    try:
        row = conn.execute(
            "SELECT * FROM campaign_units WHERE campaign_unit_key = ?",
            (campaign_unit_key,),
        ).fetchone()
    finally:
        conn.close()
    return _unit_from_row(row) if row is not None else None


def append_event(
    state_db: StateDatabase,
    campaign_unit_key: str,
    event_type: str,
    payload: Mapping[str, object],
) -> int:
    """Validate and append one gate event.

    Budget events and secondary-target adoption have stronger transactional APIs
    and cannot be written through this general entry point.
    """

    if event_type == "BUILD_INVOCATION":
        raise PayloadSchemaError("BUILD_INVOCATION must be written by consume_build_invocation")
    if event_type == "SECONDARY_TARGET_ADOPTED":
        raise PayloadSchemaError(
            "SECONDARY_TARGET_ADOPTED must be written by the atomic adoption API"
        )
    conn = _connect(state_db)
    try:
        with _immediate_transaction(conn):
            return _append_event_on_connection(conn, campaign_unit_key, event_type, payload)
    finally:
        conn.close()


def latest_event(
    state_db: StateDatabase,
    campaign_unit_key: str,
    event_type: str,
) -> dict[str, object] | None:
    _require_known_event_type(event_type)
    conn = _connect(state_db)
    try:
        row = conn.execute(
            "SELECT * FROM campaign_gate_events "
            "WHERE campaign_unit_key = ? AND event_type = ? "
            "ORDER BY event_id DESC LIMIT 1",
            (campaign_unit_key, event_type),
        ).fetchone()
    finally:
        conn.close()
    return _event_from_row(row) if row is not None else None


def latest_reproduce(
    state_db: StateDatabase,
    campaign_unit_key: str,
    *,
    arch_norm: str,
) -> dict[str, object] | None:
    _require_arch_norm(arch_norm)
    conn = _connect(state_db)
    try:
        row = conn.execute(
            "SELECT * FROM campaign_gate_events "
            "WHERE campaign_unit_key = ? AND event_type = 'REPRODUCE' "
            "AND arch_norm = ? ORDER BY event_id DESC LIMIT 1",
            (campaign_unit_key, arch_norm),
        ).fetchone()
    finally:
        conn.close()
    return _event_from_row(row) if row is not None else None


def adopt_secondary_target_with_convergence(
    state_db: StateDatabase,
    campaign_unit_key: str,
    *,
    arch_norm: str,
    expected_reproduce_event_id: int,
    convergence_payload: Mapping[str, object],
) -> bool:
    """Atomically consume one secondary-target adoption and write convergence."""

    _require_arch_norm(arch_norm)
    _require_equal(convergence_payload, "arch_norm", arch_norm)
    _require_equal(convergence_payload, "result", "FAIL")
    _require_equal(convergence_payload, "verdict", "stalled")
    conn = _connect(state_db)
    try:
        with _immediate_transaction(conn):
            _require_unit(conn, campaign_unit_key)
            existing = conn.execute(
                "SELECT 1 FROM campaign_gate_events "
                "WHERE campaign_unit_key = ? AND event_type = 'SECONDARY_TARGET_ADOPTED' "
                "AND arch_norm = ? LIMIT 1",
                (campaign_unit_key, arch_norm),
            ).fetchone()
            if existing is not None:
                return False
            reproduce = conn.execute(
                "SELECT * FROM campaign_gate_events "
                "WHERE campaign_unit_key = ? AND event_type = 'REPRODUCE' "
                "AND arch_norm = ? ORDER BY event_id DESC LIMIT 1",
                (campaign_unit_key, arch_norm),
            ).fetchone()
            if reproduce is None or int(reproduce["event_id"]) != expected_reproduce_event_id:
                return False
            reproduce_payload = _payload_from_row(reproduce)
            if reproduce_payload.get("outcome") != "different_failure":
                return False

            current = _load_bound_evidence(
                convergence_payload.get("evidence_path"),
                convergence_payload.get("evidence_sha256"),
            )
            baseline = _load_bound_evidence(
                reproduce_payload.get("evidence_local"),
                reproduce_payload.get("evidence_sha256"),
            )
            if current is None or baseline is None:
                return False
            current_truncated = _evidence_truncated(current)
            baseline_truncated = _evidence_truncated(baseline)
            if current_truncated or baseline_truncated:
                return False
            current_fingerprint = _primary_fingerprint(current, touched_files=None)
            baseline_fingerprint = _primary_fingerprint(baseline, touched_files=None)
            if current_fingerprint is None or current_fingerprint != baseline_fingerprint:
                return False
            current_count = _error_count(current)
            baseline_count = _error_count(baseline)
            if current_count != baseline_count:
                return False

            revised_convergence = dict(convergence_payload)
            revised_convergence["verdict"] = "advance"
            _validate_event_payload(
                conn,
                campaign_unit_key,
                "CONVERGENCE",
                revised_convergence,
            )
            adoption_payload: dict[str, object] = {
                "arch_norm": arch_norm,
                "adopted_fingerprint": current_fingerprint.to_dict(),
                "baseline_error_count": baseline_count,
                "current_error_count": current_count,
                "baseline_truncated": False,
                "current_truncated": False,
                "expected_reproduce_event_id": expected_reproduce_event_id,
                "at": _now_iso8601(),
            }
            _validate_event_payload(
                conn,
                campaign_unit_key,
                "SECONDARY_TARGET_ADOPTED",
                adoption_payload,
            )
            _insert_event_row(
                conn,
                campaign_unit_key,
                "SECONDARY_TARGET_ADOPTED",
                adoption_payload,
            )
            _insert_event_row(
                conn,
                campaign_unit_key,
                "CONVERGENCE",
                revised_convergence,
            )
            return True
    finally:
        conn.close()


def find_unlinked_pass(
    state_db: StateDatabase,
    campaign_unit_key: str,
    *,
    arch_norm: str,
    failure_key: str,
) -> list[dict[str, str]]:
    """Return every matching unlinked PASS; callers must not choose ambiguities."""

    _require_arch_norm(arch_norm)
    conn = _connect(state_db)
    try:
        _require_unit(conn, campaign_unit_key)
        rows = conn.execute(
            "SELECT vr.* FROM verification_records AS vr "
            "LEFT JOIN campaign_verifications AS cv "
            "ON cv.verification_id = vr.verification_id "
            "WHERE vr.failure_key = ? AND cv.verification_id IS NULL "
            "ORDER BY vr.timestamp, vr.verification_id",
            (failure_key,),
        ).fetchall()
    finally:
        conn.close()
    return [
        {key: str(row[key]) for key in row.keys()}
        for row in rows
        if _normalize_arch_raw(str(row["arch"])) == arch_norm
    ]


def append_status(
    state_db: StateDatabase,
    campaign_unit_key: str,
    status: str,
    reason: str | None = None,
    arch_norm: str | None = None,
) -> None:
    if not status:
        raise PayloadSchemaError("status must be non-empty")
    if arch_norm is not None:
        _require_arch_norm(arch_norm)
    if (
        status == HELD_FOR_INVESTIGATION
        and reason in _ARCH_SCOPED_HELD_REASONS
        and arch_norm is None
    ):
        raise PayloadSchemaError(f"HELD reason {reason!r} requires arch_norm")
    conn = _connect(state_db)
    try:
        with _immediate_transaction(conn):
            _require_unit(conn, campaign_unit_key)
            _insert_status_row(conn, campaign_unit_key, status, reason, arch_norm)
    finally:
        conn.close()


def latest_status(state_db: StateDatabase, campaign_unit_key: str) -> str | None:
    conn = _connect(state_db)
    try:
        row = conn.execute(
            "SELECT status FROM campaign_status_log WHERE campaign_unit_key = ? "
            "ORDER BY log_id DESC LIMIT 1",
            (campaign_unit_key,),
        ).fetchone()
    finally:
        conn.close()
    return _text(row, "status") if row is not None else None


def create_round(
    state_db: StateDatabase,
    campaign_unit_key: str,
    *,
    round_index: int,
    edit_spec_ref: str,
    edit_spec_sha256: str,
) -> None:
    normalized_ref = os.path.realpath(edit_spec_ref)
    if round_index < 1 or not edit_spec_sha256 or not normalized_ref:
        raise ValueError("round_index, edit_spec_ref, and edit_spec_sha256 are required")
    conn = _connect(state_db)
    try:
        with _immediate_transaction(conn):
            unit = _require_unit(conn, campaign_unit_key)
            exact = conn.execute(
                "SELECT 1 FROM campaign_rounds WHERE campaign_unit_key = ? "
                "AND round_index = ? AND edit_spec_sha256 = ? AND edit_spec_ref = ?",
                (campaign_unit_key, round_index, edit_spec_sha256, normalized_ref),
            ).fetchone()
            if exact is not None:
                return
            conflict = conn.execute(
                "SELECT round_index, edit_spec_ref, edit_spec_sha256 "
                "FROM campaign_rounds WHERE campaign_unit_key = ? "
                "AND (round_index = ? OR edit_spec_sha256 = ?)",
                (campaign_unit_key, round_index, edit_spec_sha256),
            ).fetchone()
            if conflict is not None:
                raise StateInconsistent("round identity conflicts with append-only state")
            count_row = conn.execute(
                "SELECT COUNT(*) AS count, MAX(round_index) AS max_round "
                "FROM campaign_rounds WHERE campaign_unit_key = ?",
                (campaign_unit_key,),
            ).fetchone()
            if count_row is None:
                raise StateInconsistent("round count query returned no row")
            count = int(count_row["count"])
            if count >= unit.max_rounds:
                raise RoundsExhausted("campaign round budget exhausted")
            max_round = count_row["max_round"]
            expected = 1 if max_round is None else int(max_round) + 1
            if round_index != expected:
                raise StateInconsistent(
                    f"new round_index must be {expected}, got {round_index}"
                )
            conn.execute(
                "INSERT INTO campaign_rounds "
                "(campaign_unit_key, round_index, edit_spec_ref, edit_spec_sha256, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    campaign_unit_key,
                    round_index,
                    normalized_ref,
                    edit_spec_sha256,
                    _now_iso8601(),
                ),
            )
    finally:
        conn.close()


def get_round(
    state_db: StateDatabase,
    campaign_unit_key: str,
    round_index: int,
) -> Round | None:
    conn = _connect(state_db)
    try:
        row = conn.execute(
            "SELECT * FROM campaign_rounds WHERE campaign_unit_key = ? AND round_index = ?",
            (campaign_unit_key, round_index),
        ).fetchone()
    finally:
        conn.close()
    return _round_from_row(row) if row is not None else None


def latest_round(state_db: StateDatabase, campaign_unit_key: str) -> Round | None:
    conn = _connect(state_db)
    try:
        row = conn.execute(
            "SELECT * FROM campaign_rounds WHERE campaign_unit_key = ? "
            "ORDER BY round_index DESC LIMIT 1",
            (campaign_unit_key,),
        ).fetchone()
    finally:
        conn.close()
    return _round_from_row(row) if row is not None else None


def invocations_used(state_db: StateDatabase, campaign_unit_key: str) -> int:
    conn = _connect(state_db)
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM campaign_gate_events "
            "WHERE campaign_unit_key = ? AND event_type = 'BUILD_INVOCATION'",
            (campaign_unit_key,),
        ).fetchone()
    finally:
        conn.close()
    return int(row["count"]) if row is not None else 0


def consume_build_invocation(
    state_db: StateDatabase,
    campaign_unit_key: str,
    *,
    round_index: int,
    arch_norm: str,
) -> InvocationReceipt:
    _require_arch_norm(arch_norm)
    conn = _connect(state_db)
    try:
        with _immediate_transaction(conn):
            unit = _require_unit(conn, campaign_unit_key)
            if _round_on_connection(conn, campaign_unit_key, round_index) is None:
                raise StateInconsistent("build invocation references a missing round")
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM campaign_gate_events "
                "WHERE campaign_unit_key = ? AND event_type = 'BUILD_INVOCATION'",
                (campaign_unit_key,),
            ).fetchone()
            used = int(row["count"]) if row is not None else 0
            if used >= unit.max_build_invocations:
                raise BudgetExhausted("campaign build invocation budget exhausted")
            event_id = _insert_event_row(
                conn,
                campaign_unit_key,
                "BUILD_INVOCATION",
                {"round_index": round_index, "arch_norm": arch_norm},
            )
            used += 1
            return InvocationReceipt(
                event_id=event_id,
                invocations_used=used,
                invocations_remaining=unit.max_build_invocations - used,
            )
    finally:
        conn.close()


def link_verification_with_convergence(
    state_db: StateDatabase,
    campaign_unit_key: str,
    *,
    convergence_payload: Mapping[str, object],
    arch_raw: str,
    arch_norm: str,
    verification_id: str,
    round_index: int,
    edit_spec_sha256: str,
) -> None:
    """Atomically link one PASS record and its PASS convergence event."""

    _require_arch_norm(arch_norm)
    if _normalize_arch_raw(arch_raw) != arch_norm:
        raise StateInconsistent("arch_raw and arch_norm do not match")
    _require_equal(convergence_payload, "round_index", round_index)
    _require_equal(convergence_payload, "arch_norm", arch_norm)
    _require_equal(convergence_payload, "verification_id", verification_id)
    _require_equal(convergence_payload, "result", "PASS")
    _require_equal(convergence_payload, "verdict", "n_a")
    if convergence_payload.get("evidence_path") is not None:
        raise StateInconsistent("PASS convergence evidence_path must be null")
    if convergence_payload.get("evidence_sha256") is not None:
        raise StateInconsistent("PASS convergence evidence_sha256 must be null")

    conn = _connect(state_db)
    try:
        with _immediate_transaction(conn):
            _require_unit(conn, campaign_unit_key)
            round_row = _round_on_connection(conn, campaign_unit_key, round_index)
            if round_row is None or round_row.edit_spec_sha256 != edit_spec_sha256:
                raise StateInconsistent("verification link does not match the campaign round")
            record = conn.execute(
                "SELECT result, edit_spec_sha256, arch FROM verification_records "
                "WHERE verification_id = ?",
                (verification_id,),
            ).fetchone()
            if record is None:
                raise StateInconsistent("verification record not found")
            if _text(record, "result") != "PASS":
                raise StateInconsistent("verification record is not PASS")
            if _text(record, "edit_spec_sha256") != edit_spec_sha256:
                raise StateInconsistent("verification edit_spec hash mismatch")
            if _normalize_arch_raw(_text(record, "arch")) != arch_norm:
                raise StateInconsistent("verification arch mismatch")
            _validate_event_payload(
                conn,
                campaign_unit_key,
                "CONVERGENCE",
                convergence_payload,
            )
            conn.execute(
                "INSERT INTO campaign_verifications "
                "(campaign_unit_key, arch_raw, arch_norm, verification_id, round_index, "
                "edit_spec_sha256, campaign_schema_version, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    campaign_unit_key,
                    arch_raw,
                    arch_norm,
                    verification_id,
                    round_index,
                    edit_spec_sha256,
                    CAMPAIGN_SCHEMA_VERSION,
                    _now_iso8601(),
                ),
            )
            _insert_event_row(
                conn,
                campaign_unit_key,
                "CONVERGENCE",
                convergence_payload,
            )
    except sqlite3.IntegrityError as exc:
        raise StateInconsistent(f"verification link violated campaign constraints: {exc}") from exc
    finally:
        conn.close()


def create_qb_request(
    state_db: StateDatabase,
    campaign_unit_key: str,
    *,
    request_id: str,
    sbs_target: str,
) -> int:
    if not request_id or not sbs_target:
        raise ValueError("request_id and sbs_target are required")
    conn = _connect(state_db)
    try:
        with _immediate_transaction(conn):
            _require_unit(conn, campaign_unit_key)
            existing = conn.execute(
                "SELECT request_seq, campaign_unit_key, sbs_target "
                "FROM campaign_qb_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if existing is not None:
                if (
                    _text(existing, "campaign_unit_key") != campaign_unit_key
                    or _text(existing, "sbs_target") != sbs_target
                ):
                    raise StateInconsistent("request_id is already bound to different input")
                return int(existing["request_seq"])
            cursor = conn.execute(
                "INSERT INTO campaign_qb_requests "
                "(request_id, campaign_unit_key, sbs_target, created_at) VALUES (?, ?, ?, ?)",
                (request_id, campaign_unit_key, sbs_target, _now_iso8601()),
            )
            request_seq = _lastrowid(cursor)
            conn.execute(
                "INSERT INTO campaign_qb_events "
                "(request_seq, event_type, degraded, created_at) VALUES (?, 'SUBMITTED', 0, ?)",
                (request_seq, _now_iso8601()),
            )
            return request_seq
    finally:
        conn.close()


def append_qb_event(
    state_db: StateDatabase,
    *,
    request_seq: int,
    event_type: str,
    qb_build_id: str | None = None,
    status: str | None = None,
    accepted: bool | None = None,
    sbs_target_echo: str | None = None,
    per_arch_status_json: str | None = None,
    qb_result_sha256: str | None = None,
    qb_result_ref: str | None = None,
    degraded: bool = False,
) -> int:
    if event_type == "SUBMITTED":
        raise PayloadSchemaError("SUBMITTED can only be written by create_qb_request")
    if event_type not in {"BUILD_BOUND", "RESULT"}:
        raise PayloadSchemaError(f"unsupported QB event_type: {event_type!r}")
    conn = _connect(state_db)
    try:
        with _immediate_transaction(conn):
            request = conn.execute(
                "SELECT request_seq FROM campaign_qb_requests WHERE request_seq = ?",
                (request_seq,),
            ).fetchone()
            if request is None:
                raise StateInconsistent("QB event references a missing request")
            if event_type == "BUILD_BOUND":
                if not qb_build_id:
                    raise PayloadSchemaError("BUILD_BOUND requires qb_build_id")
                if any(
                    value is not None
                    for value in (
                        status,
                        accepted,
                        sbs_target_echo,
                        per_arch_status_json,
                        qb_result_sha256,
                        qb_result_ref,
                    )
                ):
                    raise PayloadSchemaError("BUILD_BOUND may not contain result fields")
                existing_ids = {
                    _text(row, "qb_build_id")
                    for row in conn.execute(
                        "SELECT qb_build_id FROM campaign_qb_events "
                        "WHERE request_seq = ? AND event_type = 'BUILD_BOUND'",
                        (request_seq,),
                    ).fetchall()
                }
                if existing_ids and existing_ids != {qb_build_id}:
                    raise StateInconsistent("QB request is already bound to another build")
            else:
                if not status or not sbs_target_echo or not qb_result_sha256:
                    raise PayloadSchemaError(
                        "RESULT requires status, sbs_target_echo, and qb_result_sha256"
                    )
                bound = conn.execute(
                    "SELECT 1 FROM campaign_qb_events WHERE request_seq = ? "
                    "AND event_type = 'BUILD_BOUND' AND (? IS NULL OR qb_build_id = ?) LIMIT 1",
                    (request_seq, qb_build_id, qb_build_id),
                ).fetchone()
                if bound is None:
                    raise StateInconsistent("RESULT requires an existing valid build binding")
            cursor = conn.execute(
                "INSERT INTO campaign_qb_events "
                "(request_seq, event_type, qb_build_id, status, accepted, "
                "sbs_target_echo, per_arch_status_json, qb_result_sha256, qb_result_ref, "
                "degraded, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    request_seq,
                    event_type,
                    qb_build_id,
                    status,
                    int(accepted) if accepted is not None else None,
                    sbs_target_echo,
                    per_arch_status_json,
                    qb_result_sha256,
                    qb_result_ref,
                    int(degraded),
                    _now_iso8601(),
                ),
            )
            return _lastrowid(cursor)
    finally:
        conn.close()


def find_unit_by_request_id(state_db: StateDatabase, request_id: str) -> str | None:
    conn = _connect(state_db)
    try:
        row = conn.execute(
            "SELECT campaign_unit_key FROM campaign_qb_requests WHERE request_id = ?",
            (request_id,),
        ).fetchone()
    finally:
        conn.close()
    return _text(row, "campaign_unit_key") if row is not None else None


def find_unit_by_qb_build_id(state_db: StateDatabase, qb_build_id: str) -> str | None:
    conn = _connect(state_db)
    try:
        rows = conn.execute(
            "SELECT DISTINCT req.campaign_unit_key "
            "FROM campaign_qb_events AS ev "
            "JOIN campaign_qb_requests AS req ON req.request_seq = ev.request_seq "
            "WHERE ev.qb_build_id = ?",
            (qb_build_id,),
        ).fetchall()
    finally:
        conn.close()
    units = sorted({_text(row, "campaign_unit_key") for row in rows})
    if len(units) > 1:
        raise StateInconsistent("QB build id is ambiguous across campaign units")
    return units[0] if units else None


def latest_qb_result(
    state_db: StateDatabase,
    campaign_unit_key: str,
) -> dict[str, object] | None:
    conn = _connect(state_db)
    try:
        row = conn.execute(
            "SELECT ev.* FROM campaign_qb_requests AS req "
            "JOIN campaign_qb_events AS ev ON ev.request_seq = req.request_seq "
            "WHERE req.campaign_unit_key = ? "
            "AND req.request_seq = (SELECT MAX(request_seq) FROM campaign_qb_requests "
            "WHERE campaign_unit_key = ?) AND ev.event_type = 'RESULT' "
            "ORDER BY ev.event_id DESC LIMIT 1",
            (campaign_unit_key, campaign_unit_key),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def _connect(state_db: StateDatabase) -> sqlite3.Connection:
    conn = state_db.connect()
    _ensure_schema_on_connection(conn)
    return conn


def _ensure_schema_on_connection(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA_SQL)


@contextmanager
def _immediate_transaction(conn: sqlite3.Connection) -> Iterator[None]:
    try:
        conn.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError as exc:
        if _is_busy_error(exc):
            raise CampaignStateBusy("CAMPAIGN_STATE_BUSY") from exc
        raise
    try:
        yield
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()


def _is_busy_error(exc: sqlite3.OperationalError) -> bool:
    message = str(exc).lower()
    return "locked" in message or "busy" in message


def _unit_values(
    *,
    campaign_unit_key: str,
    submission_identity_key: str,
    primary_arch: str | None,
    failed_arches: Sequence[str],
    toolchain_profile: str,
    ci_evidence_ref: str | None,
    ci_evidence_sha256: str | None,
    max_rounds: int,
    max_build_invocations: int,
    identity_fields: Mapping[str, str],
) -> dict[str, object]:
    if set(identity_fields) != set(_IDENTITY_FIELDS):
        missing = sorted(set(_IDENTITY_FIELDS) - set(identity_fields))
        extra = sorted(set(identity_fields) - set(_IDENTITY_FIELDS))
        raise ValueError(f"identity fields mismatch: missing={missing}, extra={extra}")
    required_strings = {
        "campaign_unit_key": campaign_unit_key,
        "submission_identity_key": submission_identity_key,
        "toolchain_profile": toolchain_profile,
        **identity_fields,
    }
    empty = sorted(key for key, value in required_strings.items() if not value)
    if empty:
        raise ValueError(f"campaign unit fields must be non-empty: {empty}")
    if max_rounds < 1 or max_build_invocations < 1:
        raise ValueError("campaign budgets must be positive")
    arches = _canonical_failed_arches(failed_arches)
    if not arches:
        raise ValueError("failed_arches must be non-empty")
    if primary_arch is not None and primary_arch not in arches:
        raise ValueError("primary_arch must be present in failed_arches")
    return {
        "campaign_unit_key": campaign_unit_key,
        **{key: identity_fields[key] for key in _IDENTITY_FIELDS},
        "submission_identity_key": submission_identity_key,
        "toolchain_profile": toolchain_profile,
        "ci_evidence_ref": ci_evidence_ref,
        "ci_evidence_sha256": ci_evidence_sha256,
        "primary_arch": primary_arch,
        "max_rounds": max_rounds,
        "max_build_invocations": max_build_invocations,
        "failed_arches": json.dumps(arches, separators=(",", ":")),
        "schema_version": CAMPAIGN_SCHEMA_VERSION,
    }


def _canonical_failed_arches(arches: Sequence[str]) -> tuple[str, ...]:
    if isinstance(arches, (str, bytes)):
        raise ValueError("failed_arches must be a sequence of arch names")
    values = set(arches)
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError("failed_arches entries must be non-empty strings")
    rank = {arch: index for index, arch in enumerate(_FAILED_ARCH_ORDER)}
    return tuple(sorted(values, key=lambda value: (rank.get(value, len(rank)), value)))


def _insert_or_compare_unit(conn: sqlite3.Connection, values: Mapping[str, object]) -> bool:
    key = str(values["campaign_unit_key"])
    existing = conn.execute(
        "SELECT * FROM campaign_units WHERE campaign_unit_key = ?", (key,)
    ).fetchone()
    compare_columns = tuple(values)
    if existing is not None:
        differences = [
            column for column in compare_columns if existing[column] != values[column]
        ]
        if differences:
            raise StateInconsistent(f"campaign unit differs in fields: {differences}")
        return False
    columns = (*compare_columns, "created_at")
    placeholders = ", ".join("?" for _ in columns)
    conn.execute(
        f"INSERT INTO campaign_units ({', '.join(columns)}) VALUES ({placeholders})",
        (*[values[column] for column in compare_columns], _now_iso8601()),
    )
    return True


def _require_unit(conn: sqlite3.Connection, campaign_unit_key: str) -> Unit:
    row = conn.execute(
        "SELECT * FROM campaign_units WHERE campaign_unit_key = ?", (campaign_unit_key,)
    ).fetchone()
    if row is None:
        raise StateInconsistent(f"campaign unit not found: {campaign_unit_key}")
    return _unit_from_row(row)


def _unit_from_row(row: sqlite3.Row) -> Unit:
    raw_arches: Any = json.loads(_text(row, "failed_arches"))
    if not isinstance(raw_arches, list) or not all(isinstance(item, str) for item in raw_arches):
        raise StateInconsistent("campaign unit failed_arches is not a string array")
    return Unit(
        campaign_unit_key=_text(row, "campaign_unit_key"),
        ci_system=_text(row, "ci_system"),
        source_build_id=_text(row, "source_build_id"),
        project=_text(row, "project"),
        branch=_text(row, "branch"),
        spec_name=_text(row, "spec_name"),
        base_commit=_text(row, "base_commit"),
        submission_identity_key=_text(row, "submission_identity_key"),
        toolchain_profile=_text(row, "toolchain_profile"),
        ci_evidence_ref=_optional_text(row, "ci_evidence_ref"),
        ci_evidence_sha256=_optional_text(row, "ci_evidence_sha256"),
        primary_arch=_optional_text(row, "primary_arch"),
        max_rounds=int(row["max_rounds"]),
        max_build_invocations=int(row["max_build_invocations"]),
        failed_arches=tuple(raw_arches),
        created_at=_text(row, "created_at"),
        schema_version=_text(row, "schema_version"),
    )


def _round_from_row(row: sqlite3.Row) -> Round:
    return Round(
        campaign_unit_key=_text(row, "campaign_unit_key"),
        round_index=int(row["round_index"]),
        edit_spec_ref=_text(row, "edit_spec_ref"),
        edit_spec_sha256=_text(row, "edit_spec_sha256"),
        created_at=_text(row, "created_at"),
    )


def _round_on_connection(
    conn: sqlite3.Connection,
    campaign_unit_key: str,
    round_index: int,
) -> Round | None:
    row = conn.execute(
        "SELECT * FROM campaign_rounds WHERE campaign_unit_key = ? AND round_index = ?",
        (campaign_unit_key, round_index),
    ).fetchone()
    return _round_from_row(row) if row is not None else None


def _insert_status_row(
    conn: sqlite3.Connection,
    campaign_unit_key: str,
    status: str,
    reason: str | None,
    arch_norm: str | None,
) -> None:
    conn.execute(
        "INSERT INTO campaign_status_log "
        "(campaign_unit_key, status, reason, arch_norm, created_at) VALUES (?, ?, ?, ?, ?)",
        (campaign_unit_key, status, reason, arch_norm, _now_iso8601()),
    )


def _append_event_on_connection(
    conn: sqlite3.Connection,
    campaign_unit_key: str,
    event_type: str,
    payload: Mapping[str, object],
) -> int:
    _require_unit(conn, campaign_unit_key)
    _validate_event_payload(conn, campaign_unit_key, event_type, payload)
    if event_type == "ORPHAN_PASS":
        verification_id = str(payload["verification_id"])
        rows = conn.execute(
            "SELECT payload_json FROM campaign_gate_events "
            "WHERE campaign_unit_key = ? AND event_type = 'ORPHAN_PASS'",
            (campaign_unit_key,),
        ).fetchall()
        for row in rows:
            existing = json.loads(_text(row, "payload_json"))
            if isinstance(existing, dict) and existing.get("verification_id") == verification_id:
                event = conn.execute(
                    "SELECT event_id FROM campaign_gate_events "
                    "WHERE campaign_unit_key = ? AND event_type = 'ORPHAN_PASS' "
                    "AND payload_json = ? ORDER BY event_id DESC LIMIT 1",
                    (campaign_unit_key, _canonical_json(existing)),
                ).fetchone()
                if event is not None:
                    return int(event["event_id"])
    _validate_immutable_derive_fields(conn, campaign_unit_key, event_type, payload)
    return _insert_event_row(conn, campaign_unit_key, event_type, payload)


def _insert_event_row(
    conn: sqlite3.Connection,
    campaign_unit_key: str,
    event_type: str,
    payload: Mapping[str, object],
) -> int:
    cursor = conn.execute(
        "INSERT INTO campaign_gate_events "
        "(campaign_unit_key, round_index, arch_norm, verdict, invocation_event_id, "
        "event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            campaign_unit_key,
            payload.get("round_index"),
            payload.get("arch_norm"),
            payload.get("verdict"),
            payload.get("invocation_event_id"),
            event_type,
            _canonical_json(payload),
            _now_iso8601(),
        ),
    )
    return _lastrowid(cursor)


def _validate_event_payload(
    conn: sqlite3.Connection,
    campaign_unit_key: str,
    event_type: str,
    payload: Mapping[str, object],
) -> None:
    _require_known_event_type(event_type)
    validators = {
        "REPRODUCE": _validate_reproduce,
        "BUILD_INVOCATION": _validate_build_invocation,
        "ORPHAN_PASS": _validate_orphan_pass,
        "POLICY": _validate_policy,
        "DERIVE": _validate_derive,
        "PUSH": _validate_push,
        "KB": _validate_kb,
        "REVIEW": _validate_review,
        "CONVERGENCE": _validate_convergence_shape,
        "SECONDARY_TARGET_ADOPTED": _validate_adoption,
        "WORKSPACE_CLEANUP": _validate_workspace_event,
        "WORKSPACE_RELEASE": _validate_workspace_event,
    }
    validators[event_type](payload)
    if event_type == "CONVERGENCE":
        _validate_invocation_binding(conn, campaign_unit_key, payload)


def _require_known_event_type(event_type: str) -> None:
    if event_type not in _KNOWN_EVENT_TYPES:
        raise UnknownEventType(f"unregistered campaign event type: {event_type!r}")


def _validate_reproduce(payload: Mapping[str, object]) -> None:
    _require_keys(
        payload,
        {
            "arch_norm",
            "outcome",
            "evidence_local",
            "evidence_sha256",
            "synthetic_zero_error",
            "gbs_conf_sha256",
            "ci_evidence_sha256_used",
            "build_log",
            "basis",
        },
    )
    _require_arch_norm(_payload_str(payload, "arch_norm"))
    outcome = _payload_str(payload, "outcome")
    if outcome not in {"matched", "different_failure", "baseline_pass"}:
        raise PayloadSchemaError("invalid REPRODUCE outcome")
    _require_nonempty_strings(
        payload,
        (
            "evidence_local",
            "evidence_sha256",
            "gbs_conf_sha256",
            "ci_evidence_sha256_used",
            "build_log",
        ),
    )
    if not isinstance(payload["synthetic_zero_error"], bool):
        raise PayloadSchemaError("synthetic_zero_error must be bool")
    if outcome == "baseline_pass" and payload["synthetic_zero_error"] is not True:
        raise PayloadSchemaError("baseline_pass requires synthetic_zero_error=true")


def _validate_build_invocation(payload: Mapping[str, object]) -> None:
    _require_keys(payload, {"round_index", "arch_norm"})
    _require_round_index(payload)
    _require_arch_norm(_payload_str(payload, "arch_norm"))


def _validate_orphan_pass(payload: Mapping[str, object]) -> None:
    _require_keys(
        payload,
        {
            "round_index",
            "arch_norm",
            "verification_id",
            "worktree_path",
            "reason",
            "detected_at",
        },
    )
    _require_round_index(payload)
    _require_arch_norm(_payload_str(payload, "arch_norm"))
    _require_nonempty_strings(payload, ("verification_id", "worktree_path", "detected_at"))
    if payload["reason"] not in {"link_failed", "hash_mismatch", "worktree_damaged", "ambiguous"}:
        raise PayloadSchemaError("invalid ORPHAN_PASS reason")


def _validate_policy(payload: Mapping[str, object]) -> None:
    _require_keys(
        payload,
        {
            "round_index",
            "verdict",
            "hits",
            "fix_strategy_initial",
            "fix_strategy_final",
            "edit_source_kind",
        },
    )
    _require_round_index(payload)
    if not isinstance(payload["hits"], list):
        raise PayloadSchemaError("POLICY hits must be a list")
    if payload["edit_source_kind"] not in {"t1_cherry_pick", "generated", "suppress"}:
        raise PayloadSchemaError("invalid POLICY edit_source_kind")


def _validate_derive(payload: Mapping[str, object]) -> None:
    keys = {
        "message_brief",
        "author_identity",
        "committer_identity",
        "author_date",
        "committer_date",
        "derived_commit_sha",
        "verified_tree_sha",
    }
    _require_keys(payload, keys)
    _require_nonempty_strings(payload, tuple(keys))


def _validate_push(payload: Mapping[str, object]) -> None:
    _require_keys(payload, {"ref", "ref_class", "pushed_sha", "result", "url", "at"})
    _require_nonempty_strings(payload, ("ref", "pushed_sha", "at"))
    if payload["ref_class"] not in {"sandbox", "review"}:
        raise PayloadSchemaError("invalid PUSH ref_class")
    if payload["result"] not in {"ok", "failed"}:
        raise PayloadSchemaError("invalid PUSH result")
    if payload["url"] is not None and not isinstance(payload["url"], str):
        raise PayloadSchemaError("PUSH url must be string or null")


def _validate_kb(payload: Mapping[str, object]) -> None:
    _require_keys(payload, {"kb_id", "dedupe_hit", "status", "at"})
    _require_nonempty_strings(payload, ("kb_id", "at"))
    if not isinstance(payload["dedupe_hit"], bool) or payload["status"] != "NEW":
        raise PayloadSchemaError("invalid KB payload")


def _validate_review(payload: Mapping[str, object]) -> None:
    _require_keys(payload, {"outcome", "review_url", "degraded", "qb_event_id", "at"})
    if payload["outcome"] not in {"pushed", "manual", "ineligible"}:
        raise PayloadSchemaError("invalid REVIEW outcome")
    if not isinstance(payload["degraded"], bool):
        raise PayloadSchemaError("REVIEW degraded must be bool")
    if payload["outcome"] == "manual" and payload["degraded"] is not True:
        raise PayloadSchemaError("manual REVIEW must be degraded")
    if payload["review_url"] is not None and not isinstance(payload["review_url"], str):
        raise PayloadSchemaError("REVIEW review_url must be string or null")
    if payload["qb_event_id"] is not None and not isinstance(payload["qb_event_id"], int):
        raise PayloadSchemaError("REVIEW qb_event_id must be int or null")
    _require_nonempty_strings(payload, ("at",))


def _validate_convergence_shape(payload: Mapping[str, object]) -> None:
    _require_keys(
        payload,
        {
            "round_index",
            "arch_norm",
            "invocation_event_id",
            "result",
            "verdict",
            "reason",
            "evidence_path",
            "evidence_sha256",
            "verification_id",
            "actual_changed_paths",
            "previous_basis",
            "at",
        },
    )
    _require_round_index(payload)
    _require_arch_norm(_payload_str(payload, "arch_norm"))
    reason = _payload_str(payload, "reason")
    result = _payload_str(payload, "result")
    verdict = _payload_str(payload, "verdict")
    invocation_id = payload["invocation_event_id"]
    if verdict not in {"advance", "stalled", "regressed", "denied", "n_a"}:
        raise PayloadSchemaError("invalid CONVERGENCE verdict")
    if payload["previous_basis"] not in {"reproduce", "prev_build", "synthetic_zero", "none"}:
        raise PayloadSchemaError("invalid CONVERGENCE previous_basis")
    if not isinstance(payload["actual_changed_paths"], list) or not all(
        isinstance(item, str) for item in payload["actual_changed_paths"]
    ):
        raise PayloadSchemaError("actual_changed_paths must be a string list")
    if invocation_id is None:
        if reason != "rebaselined" or result != "n_a" or verdict != "n_a":
            raise PayloadSchemaError(
                "only rebaselined n_a convergence may omit invocation_event_id"
            )
    elif not isinstance(invocation_id, int) or isinstance(invocation_id, bool):
        raise PayloadSchemaError("invocation_event_id must be int or null")
    if reason in _CONVERGENCE_NA_REASONS:
        if result != "n_a" or verdict != "n_a":
            raise PayloadSchemaError("non-build convergence reasons require result/verdict n_a")
    elif result not in {"PASS", "FAIL"}:
        raise PayloadSchemaError("build outcome convergence requires PASS or FAIL")
    if result == "PASS":
        if verdict != "n_a" or not isinstance(payload["verification_id"], str):
            raise PayloadSchemaError("PASS convergence requires n_a and verification_id")
        if payload["evidence_path"] is not None or payload["evidence_sha256"] is not None:
            raise PayloadSchemaError("PASS convergence evidence fields must be null")
    elif result == "FAIL":
        if verdict == "n_a":
            raise PayloadSchemaError("FAIL build outcome requires a substantive verdict")
        if not isinstance(payload["evidence_path"], str) or not isinstance(
            payload["evidence_sha256"], str
        ):
            raise PayloadSchemaError("FAIL convergence requires evidence path and hash")
        if payload["verification_id"] is not None:
            raise PayloadSchemaError("FAIL convergence verification_id must be null")
    else:
        if payload["evidence_path"] is not None or payload["evidence_sha256"] is not None:
            raise PayloadSchemaError("n_a convergence evidence fields must be null")
        if payload["verification_id"] is not None:
            raise PayloadSchemaError("n_a convergence verification_id must be null")
    _require_nonempty_strings(payload, ("reason", "at"))


def _validate_adoption(payload: Mapping[str, object]) -> None:
    _require_keys(
        payload,
        {
            "arch_norm",
            "adopted_fingerprint",
            "baseline_error_count",
            "current_error_count",
            "baseline_truncated",
            "current_truncated",
            "expected_reproduce_event_id",
            "at",
        },
    )
    _require_arch_norm(_payload_str(payload, "arch_norm"))
    if not isinstance(payload["adopted_fingerprint"], dict):
        raise PayloadSchemaError("adopted_fingerprint must be an object")
    for key in ("baseline_error_count", "current_error_count", "expected_reproduce_event_id"):
        if not isinstance(payload[key], int) or isinstance(payload[key], bool):
            raise PayloadSchemaError(f"{key} must be int")
    if payload["baseline_truncated"] is not False or payload["current_truncated"] is not False:
        raise PayloadSchemaError("adoption requires untruncated evidence")


def _validate_workspace_event(payload: Mapping[str, object]) -> None:
    _require_keys(payload, {"paths", "reason"})
    if not isinstance(payload["paths"], list) or not all(
        isinstance(item, str) for item in payload["paths"]
    ):
        raise PayloadSchemaError("workspace paths must be a string list")
    _require_nonempty_strings(payload, ("reason",))
    if "confirmed_by" in payload and not isinstance(payload["confirmed_by"], str):
        raise PayloadSchemaError("confirmed_by must be a string")


def _validate_invocation_binding(
    conn: sqlite3.Connection,
    campaign_unit_key: str,
    payload: Mapping[str, object],
) -> None:
    invocation_id = payload.get("invocation_event_id")
    if invocation_id is None:
        return
    row = conn.execute(
        "SELECT campaign_unit_key, event_type, round_index, arch_norm "
        "FROM campaign_gate_events WHERE event_id = ?",
        (invocation_id,),
    ).fetchone()
    if row is None:
        raise StateInconsistent("invocation_event_id does not exist")
    if _text(row, "event_type") != "BUILD_INVOCATION":
        raise StateInconsistent("invocation_event_id is not BUILD_INVOCATION")
    if _text(row, "campaign_unit_key") != campaign_unit_key:
        raise StateInconsistent("invocation_event_id belongs to another unit")
    if row["round_index"] != payload.get("round_index") or row["arch_norm"] != payload.get(
        "arch_norm"
    ):
        raise StateInconsistent("invocation_event_id round or arch mismatch")


def _validate_immutable_derive_fields(
    conn: sqlite3.Connection,
    campaign_unit_key: str,
    event_type: str,
    payload: Mapping[str, object],
) -> None:
    if event_type != "DERIVE":
        return
    rows = conn.execute(
        "SELECT payload_json FROM campaign_gate_events "
        "WHERE campaign_unit_key = ? AND event_type = 'DERIVE' ORDER BY event_id",
        (campaign_unit_key,),
    ).fetchall()
    immutable = ("message_brief", "author_identity", "author_date", "committer_date")
    for row in rows:
        existing = json.loads(_text(row, "payload_json"))
        if not isinstance(existing, dict):
            raise StateInconsistent("stored DERIVE payload is not an object")
        if any(existing.get(key) != payload.get(key) for key in immutable):
            raise StateInconsistent("DERIVE first-write identity fields changed")


def _require_keys(payload: Mapping[str, object], required: set[str]) -> None:
    missing = sorted(required - set(payload))
    if missing:
        raise PayloadSchemaError(f"payload missing required fields: {missing}")


def _require_nonempty_strings(
    payload: Mapping[str, object],
    keys: Sequence[str],
) -> None:
    for key in keys:
        if not isinstance(payload.get(key), str) or not payload[key]:
            raise PayloadSchemaError(f"payload field {key} must be a non-empty string")


def _require_round_index(payload: Mapping[str, object]) -> None:
    value = payload.get("round_index")
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise PayloadSchemaError("round_index must be a positive integer")


def _require_arch_norm(arch_norm: str) -> None:
    if arch_norm not in ARCH_NORMS:
        raise PayloadSchemaError(f"unsupported arch_norm: {arch_norm!r}")


def _normalize_arch_raw(arch_raw: str) -> str | None:
    return ARCH_RAW_TO_NORM.get(arch_raw)


def _require_equal(payload: Mapping[str, object], key: str, expected: object) -> None:
    if payload.get(key) != expected:
        raise StateInconsistent(f"convergence {key} does not match link input")


def _payload_str(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise PayloadSchemaError(f"payload field {key} must be a string")
    return value


def _canonical_json(payload: Mapping[str, object]) -> str:
    try:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise PayloadSchemaError(f"payload is not JSON serializable: {exc}") from exc


def _event_from_row(row: sqlite3.Row) -> dict[str, object]:
    payload = _payload_from_row(row)
    return {
        "event_id": int(row["event_id"]),
        "campaign_unit_key": _text(row, "campaign_unit_key"),
        "event_type": _text(row, "event_type"),
        "round_index": row["round_index"],
        "arch_norm": row["arch_norm"],
        "verdict": row["verdict"],
        "invocation_event_id": row["invocation_event_id"],
        "payload": payload,
        "created_at": _text(row, "created_at"),
    }


def _text(row: sqlite3.Row, key: str) -> str:
    value: Any = row[key]
    if not isinstance(value, str):
        raise StateInconsistent(f"expected text value for {key}")
    return value


def _optional_text(row: sqlite3.Row, key: str) -> str | None:
    value: Any = row[key]
    if value is None:
        return None
    if not isinstance(value, str):
        raise StateInconsistent(f"expected optional text value for {key}")
    return value


def _now_iso8601() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _payload_from_row(row: sqlite3.Row) -> dict[str, object]:
    payload: Any = json.loads(_text(row, "payload_json"))
    if not isinstance(payload, dict):
        raise StateInconsistent("stored event payload is not an object")
    return payload


def _load_bound_evidence(path_value: object, digest_value: object) -> dict[str, Any] | None:
    if not isinstance(path_value, str) or not isinstance(digest_value, str):
        return None
    path = Path(path_value)
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if hashlib.sha256(raw).hexdigest() != digest_value:
        return None
    try:
        value: Any = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _evidence_truncated(evidence: Mapping[str, object]) -> bool:
    if evidence.get("truncated") is True:
        return True
    clusters = evidence.get("error_clusters")
    if not isinstance(clusters, dict):
        return False
    raw_clusters = clusters.get("clusters")
    if not isinstance(raw_clusters, list):
        return False
    return any(
        isinstance(cluster, dict) and cluster.get("locations_truncated") is True
        for cluster in raw_clusters
    )


def _lastrowid(cursor: sqlite3.Cursor) -> int:
    if cursor.lastrowid is None:
        raise StateInconsistent("SQLite insert did not return a row id")
    return cursor.lastrowid
