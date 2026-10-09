"""Bind exactly one PASS record per supported campaign architecture."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from tizen_ci_shared.state import StateDatabase, VerificationRecord, get_record

from ci_triage.campaign_state import ARCH_NORMS, ARCH_RAW_TO_NORM, REJECTED_ARCH_NOT_ALLOWED

_MISMATCH = "REJECTED_ARCH_AGGREGATE_MISMATCH"
_BINDING_FIELDS = (
    "verified_tree_sha", "base_commit", "spec_name", "project", "branch",
    "edit_spec_sha256", "gbs_conf_sha256",
)


@dataclass(frozen=True)
class AggregateResult:
    ok: bool
    verified_tree_sha: str | None
    base_commit: str | None
    spec_name: str | None
    project: str | None
    branch: str | None
    edit_spec_sha256: str | None
    gbs_conf_sha256: str | None
    records: tuple[VerificationRecord, ...]
    reasons: tuple[str, ...]


def aggregate_verifications(ids: Sequence[str], state_db: StateDatabase) -> AggregateResult:
    """Read the nominated records without choosing rounds or changing campaign state."""
    reasons: list[str] = []
    records: list[VerificationRecord] = []
    if len(ids) != len(ARCH_NORMS):
        reasons.append(f"{_MISMATCH}: record_count={len(ids)} expected={len(ARCH_NORMS)}")
    for verification_id in ids:
        record = get_record(state_db, verification_id)
        if record is None:
            reasons.append(f"{_MISMATCH}: verification_id={verification_id!r} record not found")
        else:
            records.append(record)

    normalized: set[str] = set()
    for record in records:
        label = f"verification_id={record.verification_id!r} arch={record.arch!r}"
        if record.result != "PASS":
            reasons.append(f"{_MISMATCH}: {label} result={record.result!r} expected='PASS'")
        arch = ARCH_RAW_TO_NORM.get(record.arch)
        if arch is None:
            reasons.append(f"{REJECTED_ARCH_NOT_ALLOWED}: {label}")
        else:
            normalized.add(arch)
    if normalized != ARCH_NORMS:
        details = [(record.verification_id, record.arch) for record in records]
        reasons.append(
            f"{_MISMATCH}: arch_norm={sorted(normalized)!r} expected={sorted(ARCH_NORMS)!r}; "
            f"records={details!r}"
        )

    for field in _BINDING_FIELDS:
        for record in records:
            if not getattr(record, field).strip():
                reasons.append(
                    f"{_MISMATCH}: verification_id={record.verification_id!r} "
                    f"{field}={getattr(record, field)!r} must be nonempty after strip"
                )
        if len({getattr(record, field) for record in records}) > 1:
            details_text = "; ".join(
                f"verification_id={record.verification_id!r} arch={record.arch!r} "
                f"{field}={getattr(record, field)!r}" for record in records
            )
            reasons.append(f"{_MISMATCH}: {details_text}")

    # Do not expose a usable binding from an incomplete or inconsistent aggregate.
    first = records[0] if records and not reasons else None
    return AggregateResult(
        ok=not reasons,
        verified_tree_sha=first.verified_tree_sha if first else None,
        base_commit=first.base_commit if first else None,
        spec_name=first.spec_name if first else None,
        project=first.project if first else None,
        branch=first.branch if first else None,
        edit_spec_sha256=first.edit_spec_sha256 if first else None,
        gbs_conf_sha256=first.gbs_conf_sha256 if first else None,
        records=tuple(records), reasons=tuple(reasons),
    )
