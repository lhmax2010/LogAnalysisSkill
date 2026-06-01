"""Resolve source-context availability for patch suggestion prompts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gbs_patch_suggest.ingest import CompileErrorEvidence

DEFAULT_CONTEXT_WINDOW = 30


@dataclass(frozen=True)
class SourceContext:
    """Source snippet context for the selected compiler diagnostic."""

    path: str
    start_line: int
    end_line: int
    text: str
    origin: str


@dataclass(frozen=True)
class ResolvedContext:
    """Three-level source context resolution result."""

    status: str
    level: str
    evidence: CompileErrorEvidence
    source_context: SourceContext | None = None
    advisory: str | None = None

    @property
    def has_source_context(self) -> bool:
        return self.source_context is not None


def resolve_context(evidence: CompileErrorEvidence) -> ResolvedContext:
    """Resolve A/B/C source context levels without failing on missing source."""

    if not evidence.is_compiler:
        return ResolvedContext(
            status="not_applicable",
            level="not_applicable",
            evidence=evidence,
            advisory=(
                f"primary_error.kind is `{evidence.kind}`, so this skill is not applicable. "
                "Use the workflow suggester for this fault class."
            ),
        )

    if evidence.source_snippet is not None:
        return ResolvedContext(
            status="source_context_available",
            level="A",
            evidence=evidence,
            source_context=_context_from_evidence(evidence.source_snippet),
        )

    if evidence.file and evidence.line:
        return ResolvedContext(
            status="source_context_unavailable",
            level="B",
            evidence=evidence,
            advisory=(
                f"Source context for `{evidence.file}:{evidence.line}` is unavailable to "
                "this skill. Ask the outer assistant to open that file and inspect the "
                "reported line before generating a patch."
            ),
        )

    return ResolvedContext(
        status="diagnostic_only",
        level="C",
        evidence=evidence,
        advisory=(
            "The compiler diagnostic has no usable file and line number. Provide only "
            "diagnostic context; do not guess a source patch without inspecting the tree."
        ),
    )


def _context_from_evidence(snippet: dict[str, Any]) -> SourceContext:
    return SourceContext(
        path=str(snippet.get("path", "")),
        start_line=_int_or_default(snippet.get("start_line"), 1),
        end_line=_int_or_default(snippet.get("end_line"), 1),
        text=str(snippet.get("text", "")),
        origin="evidence",
    )


def _int_or_default(value: Any, default: int) -> int:
    return value if isinstance(value, int) else default
