"""Append-only state database for CI triage verification records."""

from __future__ import annotations

from ci_triage.state.db import GERRIT_READY, StateDatabase
from ci_triage.state.keys import build_failure_key, build_submission_key, failure_key_sha12
from ci_triage.state.records import (
    LatestStatusRow,
    VerificationRecord,
    get_latest_status,
    get_latest_status_row,
    get_record,
    record_status,
    write_pass_record,
)

__all__ = [
    "GERRIT_READY",
    "LatestStatusRow",
    "StateDatabase",
    "VerificationRecord",
    "build_failure_key",
    "build_submission_key",
    "failure_key_sha12",
    "get_latest_status",
    "get_latest_status_row",
    "get_record",
    "record_status",
    "write_pass_record",
]
