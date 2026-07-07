"""Verification record API for the append-only triage state DB."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from ci_triage.state.db import GERRIT_READY, StateDatabase


@dataclass(frozen=True)
class VerificationRecord:
    """PASS record proving that one candidate patch has been build-verified."""

    verification_id: str
    result: str
    timestamp: str
    failure_key: str
    base_commit: str
    verified_commit_sha: str
    verified_tree_sha: str
    canonical_diff_sha256: str
    patch_sha256: str
    edit_spec_sha256: str
    project: str
    branch: str
    spec_name: str
    arch: str
    gbs_conf_sha256: str
    build_log_sha256: str
    worktree_path: str
    command_line: str


def write_pass_record(db: StateDatabase, record: VerificationRecord) -> str:
    """Write a PASS record and mark the failure GERRIT_READY.

    This is the only public API that may produce a GERRIT_READY state. It ties the
    ready state to a concrete verification record in the same transaction.
    """

    if record.result != "PASS":
        raise ValueError("verification records currently support only PASS results")
    return db.insert_pass_record(_record_to_values(record))


def get_record(db: StateDatabase, verification_id: str) -> VerificationRecord | None:
    """Fetch one PASS verification record."""

    values = db.get_verification_record(verification_id)
    if values is None:
        return None
    return VerificationRecord(**values)


def get_latest_status(db: StateDatabase, unit_key: str) -> str | None:
    """Return the latest append-only status for one unit."""

    return db.get_latest_status(unit_key)


def record_status(
    db: StateDatabase,
    unit_key: str,
    status: str,
    *,
    reason: str | None = None,
    verification_id: str | None = None,
) -> None:
    """Append a normal status transition.

    GERRIT_READY is intentionally blocked here. Use ``write_pass_record`` so the
    state cannot be recorded without the paired verification record.
    """

    if status == GERRIT_READY:
        raise ValueError("GERRIT_READY can only be written by write_pass_record")
    db.insert_status(
        unit_key,
        status,
        reason=reason,
        verification_id=verification_id,
        allow_gerrit_ready=False,
    )


def _record_to_values(record: VerificationRecord) -> dict[str, str]:
    values = asdict(record)
    return {key: value for key, value in values.items() if isinstance(value, str)}
