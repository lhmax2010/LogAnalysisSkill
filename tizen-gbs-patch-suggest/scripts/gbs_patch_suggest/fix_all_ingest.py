"""Ingest analyzer source candidate sidecars for experimental fix-all mode."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gbs_patch_suggest.cluster_ingest import ClusterLocation

SOURCE_CANDIDATE_SUMMARY_SCHEMA = "source_candidates/v1"
SOURCE_CANDIDATE_SIDECAR_SCHEMA = "source_candidate_sidecar/v1"


@dataclass(frozen=True)
class SourceCandidateDiagnostic:
    """One analyzer source candidate visible to experimental fix-all mode."""

    index: int
    event_id: str | None
    kind: str
    file: str
    normalized_file: str
    line: int
    column: int | None
    line_no: int | None
    message: str
    warning_option: str | None
    semantic_class: str | None
    type_fixability: str
    type_fixability_reason: str | None
    source_reachable: bool
    source_resolution_status: str
    source_owned: bool
    source_ownership_status: str
    raw_candidate: dict[str, Any]

    @property
    def patch_ready(self) -> bool:
        return (
            self.type_fixability == "probably_fixable"
            and self.source_reachable
            and self.source_owned
        )

    @property
    def group_file(self) -> str:
        return self.normalized_file or self.file

    @property
    def not_patch_ready_reason(self) -> str | None:
        if self.patch_ready:
            return None
        if self.type_fixability != "probably_fixable":
            return f"type_fixability:{self.type_fixability}"
        if not self.source_reachable:
            return f"source_reachable:{self.source_resolution_status}"
        if not self.source_owned:
            return f"source_owned:{self.source_ownership_status}"
        return "not_patch_ready"

    def as_location(self) -> ClusterLocation:
        """Return a resolver-compatible location using the source-root path."""

        return ClusterLocation(
            event_id=self.event_id,
            kind=self.kind,
            file=self.group_file,
            line=self.line,
            column=self.column,
            line_no=self.line_no,
            message=self.message,
        )


@dataclass(frozen=True)
class FixAllIngestResult:
    """Source candidates and advisory for experimental fix-all mode."""

    candidates: tuple[SourceCandidateDiagnostic, ...] = ()
    advisory: str | None = None

    @property
    def has_candidates(self) -> bool:
        return bool(self.candidates)

    @property
    def patch_ready_candidates(self) -> tuple[SourceCandidateDiagnostic, ...]:
        return tuple(candidate for candidate in self.candidates if candidate.patch_ready)


def ingest_source_candidates(
    packet: dict[str, Any],
    *,
    evidence_path: Path,
) -> FixAllIngestResult:
    """Load analyzer source_candidates sidecar if the packet exposes it."""

    summary = packet.get("source_candidates")
    if not isinstance(summary, dict):
        return FixAllIngestResult(advisory="source_candidates_unavailable: missing summary")
    if summary.get("schema_version") != SOURCE_CANDIDATE_SUMMARY_SCHEMA:
        return FixAllIngestResult(advisory="source_candidates_unavailable: summary schema mismatch")

    sidecar_ref = summary.get("full_candidates_path")
    if not isinstance(sidecar_ref, str) or not sidecar_ref:
        return FixAllIngestResult(advisory="source_candidates_unavailable: missing path")
    sidecar_path = evidence_path.parent / sidecar_ref
    try:
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return FixAllIngestResult(advisory=f"source_candidates_unavailable: {exc}")

    if (
        not isinstance(sidecar, dict)
        or sidecar.get("schema_version") != SOURCE_CANDIDATE_SIDECAR_SCHEMA
    ):
        return FixAllIngestResult(advisory="source_candidates_unavailable: sidecar schema mismatch")

    candidates = tuple(_parse_candidates(sidecar.get("candidates", [])))
    if not candidates:
        return FixAllIngestResult(advisory="source_candidates_unavailable: no main candidates")
    return FixAllIngestResult(candidates=candidates)


def _parse_candidates(raw_candidates: object) -> list[SourceCandidateDiagnostic]:
    if not isinstance(raw_candidates, list):
        return []
    candidates: list[SourceCandidateDiagnostic] = []
    for raw in raw_candidates:
        if not isinstance(raw, dict):
            continue
        parsed = _parse_candidate(len(candidates) + 1, raw)
        if parsed is not None:
            candidates.append(parsed)
    return candidates


def _parse_candidate(
    index: int,
    raw: dict[str, Any],
) -> SourceCandidateDiagnostic | None:
    file_value = raw.get("file")
    line = raw.get("line")
    message = raw.get("message")
    kind = raw.get("kind")
    if not isinstance(file_value, str) or not file_value:
        return None
    if not isinstance(line, int) or line <= 0:
        return None
    if not isinstance(message, str) or not message:
        return None
    if not isinstance(kind, str) or not kind:
        return None
    normalized = raw.get("normalized_file")
    if not isinstance(normalized, str) or not normalized:
        normalized = file_value
    return SourceCandidateDiagnostic(
        index=index,
        event_id=str(raw["event_id"]) if raw.get("event_id") is not None else None,
        kind=kind,
        file=file_value,
        normalized_file=normalized,
        line=line,
        column=_optional_int(raw.get("column")),
        line_no=_optional_int(raw.get("line_no")),
        message=message,
        warning_option=str(raw["warning_option"])
        if raw.get("warning_option") is not None
        else None,
        semantic_class=str(raw["semantic_class"])
        if raw.get("semantic_class") is not None
        else None,
        type_fixability=str(raw.get("type_fixability") or "unknown"),
        type_fixability_reason=str(raw["type_fixability_reason"])
        if raw.get("type_fixability_reason") is not None
        else None,
        source_reachable=raw.get("source_reachable") is True,
        source_resolution_status=str(raw.get("source_resolution_status") or "unknown"),
        source_owned=raw.get("source_owned") is True,
        source_ownership_status=str(raw.get("source_ownership_status") or "unknown"),
        raw_candidate=dict(raw),
    )


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) else None
