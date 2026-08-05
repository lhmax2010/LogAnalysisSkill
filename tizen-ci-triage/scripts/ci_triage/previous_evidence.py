"""Resolve the trusted previous evidence for one campaign architecture."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ci_triage.campaign_state import latest_reproduce
from ci_triage.state import StateDatabase

_SKIP_NA_REASONS = {
    "orphan_invocation",
    "apply_failed",
    "analyzer_failed",
    "toolchain_failed",
}

_SYNTHETIC_ZERO_EVIDENCE: dict[str, Any] = {
    "schema_version": "evidence_packet/v1",
    "synthetic": True,
    "reason": "baseline_pass",
    "primary_error": None,
    "error_clusters": {
        "schema_version": "error_clusters/v1",
        "clusters": [],
        "truncated": False,
    },
    "cascade_summary": "",
    "root_cause_candidates": [],
}


@dataclass(frozen=True)
class ResolvedEvidence:
    """A hash-verified evidence object and the history basis that selected it."""

    evidence: dict[str, Any]
    basis: str
    evidence_path: str | None
    evidence_sha256: str | None


@dataclass(frozen=True)
class MissingEvidence:
    """A previous-evidence integrity failure that must fail closed."""

    reason: str


PreviousEvidence = ResolvedEvidence | MissingEvidence


def resolve(
    state_db: StateDatabase,
    campaign_unit_key: str,
    *,
    arch_norm: str,
) -> PreviousEvidence:
    """Resolve previous evidence using the frozen campaign history semantics.

    Both the pre-build check and the post-build TOCTOU check call this function.
    A substantive event whose bound file is missing or has a mismatched digest is
    never downgraded to an empty previous result.
    """

    reproduce = latest_reproduce(state_db, campaign_unit_key, arch_norm=arch_norm)
    if reproduce is None:
        return MissingEvidence("latest REPRODUCE event is missing")

    events = _convergence_payloads(state_db, campaign_unit_key, arch_norm)
    if events is None:
        return MissingEvidence("stored CONVERGENCE payload is invalid")
    if not events:
        return _from_reproduce(reproduce)

    latest = events[0]
    if latest.get("result") == "PASS":
        return ResolvedEvidence(
            evidence=_synthetic_zero_evidence(),
            basis="synthetic_zero",
            evidence_path=None,
            evidence_sha256=None,
        )

    if latest.get("verdict") == "n_a":
        reason = latest.get("reason")
        if reason == "rebaselined":
            return _from_reproduce(reproduce)
        if reason in _SKIP_NA_REASONS:
            substantive = next(
                (payload for payload in events[1:] if payload.get("verdict") != "n_a"),
                None,
            )
            return (
                _from_payload(substantive, basis="prev_build")
                if substantive
                else _from_reproduce(reproduce)
            )
        return MissingEvidence(f"latest n_a convergence has unsupported reason {reason!r}")

    return _from_payload(latest, basis="prev_build")


def _convergence_payloads(
    state_db: StateDatabase,
    campaign_unit_key: str,
    arch_norm: str,
) -> list[dict[str, object]] | None:
    conn = state_db.connect()
    try:
        rows = conn.execute(
            "SELECT payload_json FROM campaign_gate_events "
            "WHERE campaign_unit_key = ? AND event_type = 'CONVERGENCE' "
            "AND arch_norm = ? ORDER BY event_id DESC",
            (campaign_unit_key, arch_norm),
        ).fetchall()
    finally:
        conn.close()
    result: list[dict[str, object]] = []
    for row in rows:
        try:
            value: Any = json.loads(str(row["payload_json"]))
        except json.JSONDecodeError:
            return None
        if not isinstance(value, dict):
            return None
        result.append(value)
    return result


def _from_reproduce(event: dict[str, object]) -> PreviousEvidence:
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return MissingEvidence("latest REPRODUCE payload is invalid")
    return _from_payload(payload, basis="reproduce", path_key="evidence_local")


def _from_payload(
    payload: dict[str, object],
    *,
    basis: str,
    path_key: str = "evidence_path",
) -> PreviousEvidence:
    path_value = payload.get(path_key)
    digest_value = payload.get("evidence_sha256")
    if not isinstance(path_value, str) or not isinstance(digest_value, str):
        return MissingEvidence(f"{basis} evidence binding is incomplete")
    path = Path(path_value)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return MissingEvidence(f"{basis} evidence is unreadable: {exc}")
    if hashlib.sha256(raw).hexdigest() != digest_value:
        return MissingEvidence(f"{basis} evidence sha256 mismatch")
    try:
        value: Any = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return MissingEvidence(f"{basis} evidence is invalid JSON: {exc}")
    if not isinstance(value, dict):
        return MissingEvidence(f"{basis} evidence must be a JSON object")
    return ResolvedEvidence(
        evidence=value,
        basis=basis,
        evidence_path=str(path),
        evidence_sha256=digest_value,
    )


def _synthetic_zero_evidence() -> dict[str, Any]:
    # Return a fresh object so convergence callers cannot mutate shared state.
    return deepcopy(_SYNTHETIC_ZERO_EVIDENCE)
