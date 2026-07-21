"""Ingest multiple terminal source diagnostics from analyzer candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gbs_patch_suggest.ingest import (
    SOURCE_DIAGNOSTIC_KINDS,
    CompileErrorEvidence,
)


@dataclass(frozen=True)
class MultiCandidateDiagnostic:
    """One eligible independent source diagnostic candidate."""

    index: int
    candidate_id: str
    event_id: str
    rank: int | None
    evidence: CompileErrorEvidence
    raw_candidate: dict[str, Any]


@dataclass(frozen=True)
class SkippedCandidate:
    """Candidate visible in evidence but not handled by multi-candidate mode."""

    event_id: str | None
    kind: str | None
    rank: int | None
    reason: str
    summary: str | None = None


@dataclass(frozen=True)
class MultiCandidateIngestResult:
    """Eligible multi-candidate diagnostics and skipped candidates."""

    candidates: tuple[MultiCandidateDiagnostic, ...] = ()
    skipped: tuple[SkippedCandidate, ...] = ()

    @property
    def has_candidates(self) -> bool:
        return len(self.candidates) >= 2


def ingest_terminal_source_candidates(packet: dict[str, Any]) -> MultiCandidateIngestResult:
    """Select independent terminal compiler/Werror candidates from analyzer evidence."""

    raw_candidates = packet.get("root_cause_candidates")
    if not isinstance(raw_candidates, list):
        return MultiCandidateIngestResult()

    eligible: list[MultiCandidateDiagnostic] = []
    skipped: list[SkippedCandidate] = []
    for raw in raw_candidates:
        if not isinstance(raw, dict):
            continue
        reason = _skip_reason(raw)
        if reason is not None:
            skipped.append(_skipped(raw, reason))
            continue
        eligible.append(_diagnostic(len(eligible) + 1, raw, packet))

    if len(eligible) < 2:
        return MultiCandidateIngestResult(skipped=tuple(skipped))
    return MultiCandidateIngestResult(
        candidates=tuple(eligible),
        skipped=tuple(skipped),
    )


def _skip_reason(candidate: dict[str, Any]) -> str | None:
    if candidate.get("is_terminal") is not True:
        return "not_terminal_cascade"
    kind = candidate.get("kind")
    if kind not in SOURCE_DIAGNOSTIC_KINDS:
        return "not_source_diagnostic"
    file_value = candidate.get("file")
    message = candidate.get("message")
    line = candidate.get("line")
    if not isinstance(file_value, str) or not file_value:
        return "missing_file"
    if not isinstance(line, int) or line <= 0:
        return "missing_line"
    if not isinstance(message, str) or not message:
        return "missing_message"
    return None


def _diagnostic(
    index: int,
    candidate: dict[str, Any],
    packet: dict[str, Any],
) -> MultiCandidateDiagnostic:
    event_id = str(candidate.get("event_id"))
    return MultiCandidateDiagnostic(
        index=index,
        candidate_id=f"C{index:03d}_{event_id}",
        event_id=event_id,
        rank=_optional_int(candidate.get("rank")),
        evidence=CompileErrorEvidence(
            kind=str(candidate["kind"]),
            message=str(candidate["message"]),
            semantic_class=str(candidate.get("semantic_class") or "unknown"),
            file=str(candidate["file"]),
            line=int(candidate["line"]),
            column=_optional_int(candidate.get("column")),
            source_snippet=None,
            raw_primary_error=dict(candidate),
        ),
        raw_candidate=dict(candidate),
    )


def _skipped(candidate: dict[str, Any], reason: str) -> SkippedCandidate:
    return SkippedCandidate(
        event_id=str(candidate["event_id"]) if candidate.get("event_id") is not None else None,
        kind=str(candidate["kind"]) if candidate.get("kind") is not None else None,
        rank=_optional_int(candidate.get("rank")),
        reason=reason,
        summary=str(candidate["summary"]) if isinstance(candidate.get("summary"), str) else None,
    )


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) else None
