"""SQLite storage for triage state.

Security boundary:
This database is a strong workflow constraint, not physical isolation. Callers such
as gerrit-submit should trust only verification records written through this module's
API, and should not accept externally supplied "verified" results. However, if an
agent or user runs as the same OS account as the DB file, that actor can still edit
the SQLite file directly. Stage 1 does not claim to resist malicious or runaway
same-user tampering; it relies on code review and tests to prevent accidental
bypasses. Stronger isolation such as a daemon, service account, or record signatures
is left to Stage 2.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GERRIT_READY = "GERRIT_READY"

_VERIFICATION_COLUMNS = (
    "verification_id",
    "result",
    "timestamp",
    "failure_key",
    "base_commit",
    "verified_commit_sha",
    "verified_tree_sha",
    "canonical_diff_sha256",
    "patch_sha256",
    "edit_spec_sha256",
    "project",
    "branch",
    "spec_name",
    "arch",
    "gbs_conf_sha256",
    "build_log_sha256",
    "worktree_path",
    "command_line",
)


@dataclass(frozen=True)
class StateDatabase:
    """Path-backed SQLite state DB.

    All state changes are append-only inserts. There are intentionally no update
    helpers for status rows; callers derive current state from the latest log row.
    """

    path: Path

    def connect(self) -> sqlite3.Connection:
        """Open and initialize one configured SQLite connection."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        _configure_connection(conn)
        _initialize_schema(conn)
        return conn

    def insert_pass_record(self, record_values: Mapping[str, str]) -> str:
        """Insert a PASS verification record and the paired GERRIT_READY status."""

        verification_id = record_values["verification_id"]
        failure_key = record_values["failure_key"]
        conn = self.connect()
        try:
            with conn:
                _insert_verification_record(conn, record_values)
                _insert_status(
                    conn,
                    unit_key=failure_key,
                    status=GERRIT_READY,
                    reason="verification passed",
                    verification_id=verification_id,
                    allow_gerrit_ready=True,
                )
        finally:
            conn.close()
        return verification_id

    def get_verification_record(self, verification_id: str) -> dict[str, str] | None:
        """Fetch one verification record by ID."""

        conn = self.connect()
        try:
            row = conn.execute(
                f"SELECT {', '.join(_VERIFICATION_COLUMNS)} "
                "FROM verification_records WHERE verification_id = ?",
                (verification_id,),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        return {column: _row_string(row, column) for column in _VERIFICATION_COLUMNS}

    def insert_status(
        self,
        unit_key: str,
        status: str,
        *,
        reason: str | None = None,
        verification_id: str | None = None,
        allow_gerrit_ready: bool = False,
    ) -> None:
        """Append one status transition row."""

        conn = self.connect()
        try:
            with conn:
                _insert_status(
                    conn,
                    unit_key=unit_key,
                    status=status,
                    reason=reason,
                    verification_id=verification_id,
                    allow_gerrit_ready=allow_gerrit_ready,
                )
        finally:
            conn.close()

    def get_latest_status(self, unit_key: str) -> str | None:
        """Return the latest status for one unit key."""

        row = self.get_latest_status_row(unit_key)
        return row["status"] if row is not None else None

    def get_latest_status_row(self, unit_key: str) -> dict[str, str | None] | None:
        """Return the latest status row for one unit key."""

        conn = self.connect()
        try:
            row = conn.execute(
                "SELECT status, verification_id, timestamp FROM unit_status_log WHERE unit_key = ? "
                "ORDER BY timestamp DESC, log_id DESC LIMIT 1",
                (unit_key,),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        return {
            "status": _row_string(row, "status"),
            "verification_id": _row_optional_string(row, "verification_id"),
            "timestamp": _row_string(row, "timestamp"),
        }

    def get_submission(self, submission_key: str) -> dict[str, str | None] | None:
        """Fetch one submitted Gerrit record by submission key."""

        conn = self.connect()
        try:
            row = conn.execute(
                "SELECT submission_key, verification_id, submitted_at, action, gerrit_change_id "
                "FROM submissions WHERE submission_key = ?",
                (submission_key,),
            ).fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        return {
            "submission_key": _row_string(row, "submission_key"),
            "verification_id": _row_string(row, "verification_id"),
            "submitted_at": _row_string(row, "submitted_at"),
            "action": _row_string(row, "action"),
            "gerrit_change_id": _row_optional_string(row, "gerrit_change_id"),
        }

    def insert_submission(
        self,
        *,
        submission_key: str,
        verification_id: str,
        action: str,
        gerrit_change_id: str | None = None,
    ) -> None:
        """Insert one Gerrit submission audit row.

        Stage 1 dry-run paths must not call this; it is present for duplicate
        checks, tests, and the Stage 2 real-push path.
        """

        conn = self.connect()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO submissions "
                    "(submission_key, verification_id, submitted_at, action, gerrit_change_id) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        submission_key,
                        verification_id,
                        _now_iso8601(),
                        action,
                        gerrit_change_id,
                    ),
                )
        finally:
            conn.close()

    def get_status_log(self, unit_key: str) -> tuple[dict[str, str | None], ...]:
        """Read status rows for tests and audit views."""

        conn = self.connect()
        try:
            rows = conn.execute(
                "SELECT unit_key, status, timestamp, verification_id, reason "
                "FROM unit_status_log WHERE unit_key = ? ORDER BY timestamp ASC, log_id ASC",
                (unit_key,),
            ).fetchall()
        finally:
            conn.close()
        return tuple(
            {
                "unit_key": _row_string(row, "unit_key"),
                "status": _row_string(row, "status"),
                "timestamp": _row_string(row, "timestamp"),
                "verification_id": _row_optional_string(row, "verification_id"),
                "reason": _row_optional_string(row, "reason"),
            }
            for row in rows
        )


def _configure_connection(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")


def _initialize_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS verification_records (
            verification_id TEXT PRIMARY KEY,
            result TEXT NOT NULL CHECK (result = 'PASS'),
            timestamp TEXT NOT NULL,
            failure_key TEXT NOT NULL,
            base_commit TEXT NOT NULL,
            verified_commit_sha TEXT NOT NULL,
            verified_tree_sha TEXT NOT NULL,
            canonical_diff_sha256 TEXT NOT NULL,
            patch_sha256 TEXT NOT NULL,
            edit_spec_sha256 TEXT NOT NULL,
            project TEXT NOT NULL,
            branch TEXT NOT NULL,
            spec_name TEXT NOT NULL,
            arch TEXT NOT NULL,
            gbs_conf_sha256 TEXT NOT NULL,
            build_log_sha256 TEXT NOT NULL,
            worktree_path TEXT NOT NULL,
            command_line TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS unit_status_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_key TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            verification_id TEXT,
            reason TEXT,
            FOREIGN KEY (verification_id) REFERENCES verification_records (verification_id)
        );

        CREATE INDEX IF NOT EXISTS idx_unit_status_log_latest
            ON unit_status_log (unit_key, timestamp, log_id);

        CREATE TABLE IF NOT EXISTS submissions (
            submission_key TEXT PRIMARY KEY,
            verification_id TEXT NOT NULL,
            submitted_at TEXT NOT NULL,
            action TEXT NOT NULL,
            gerrit_change_id TEXT,
            FOREIGN KEY (verification_id) REFERENCES verification_records (verification_id)
        );
        """
    )


def _insert_verification_record(
    conn: sqlite3.Connection,
    record_values: Mapping[str, str],
) -> None:
    values = tuple(record_values[column] for column in _VERIFICATION_COLUMNS)
    placeholders = ", ".join("?" for _ in _VERIFICATION_COLUMNS)
    conn.execute(
        "INSERT INTO verification_records "
        f"({', '.join(_VERIFICATION_COLUMNS)}) VALUES ({placeholders})",
        values,
    )


def _insert_status(
    conn: sqlite3.Connection,
    *,
    unit_key: str,
    status: str,
    reason: str | None,
    verification_id: str | None,
    allow_gerrit_ready: bool,
) -> None:
    if status == GERRIT_READY and not allow_gerrit_ready:
        raise ValueError("GERRIT_READY can only be written by write_pass_record")
    conn.execute(
        "INSERT INTO unit_status_log "
        "(unit_key, status, timestamp, verification_id, reason) VALUES (?, ?, ?, ?, ?)",
        (unit_key, status, _now_iso8601(), verification_id, reason),
    )


def _now_iso8601() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _row_string(row: sqlite3.Row, key: str) -> str:
    value: Any = row[key]
    if not isinstance(value, str):
        raise TypeError(f"expected text value for {key}")
    return value


def _row_optional_string(row: sqlite3.Row, key: str) -> str | None:
    value: Any = row[key]
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"expected optional text value for {key}")
    return value
