"""Resolve source-context availability for patch suggestion prompts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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


def resolve_context(
    evidence: CompileErrorEvidence,
    *,
    src_root: Path | None = None,
    window: int = DEFAULT_CONTEXT_WINDOW,
) -> ResolvedContext:
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
        path = resolve_source_path(evidence.file, src_root)
        if path is not None and path.is_file():
            return ResolvedContext(
                status="source_context_available",
                level="A",
                evidence=evidence,
                source_context=_context_from_file(path, evidence.line, window=window),
            )
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


def resolve_source_path(file_value: str, src_root: Path | None) -> Path | None:
    """Resolve an analyzer file value with the same simple policy as evidence collectors."""

    path = Path(file_value)
    if path.is_absolute():
        return path
    if src_root is None:
        return None
    return src_root / path


def _context_from_evidence(snippet: dict[str, Any]) -> SourceContext:
    return SourceContext(
        path=str(snippet.get("path", "")),
        start_line=_int_or_default(snippet.get("start_line"), 1),
        end_line=_int_or_default(snippet.get("end_line"), 1),
        text=str(snippet.get("text", "")),
        origin="evidence",
    )


def _context_from_file(path: Path, line: int, *, window: int) -> SourceContext:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = max(1, line - window)
    end = min(len(lines), line + window)
    return SourceContext(
        path=str(path),
        start_line=start,
        end_line=end,
        text="\n".join(lines[start - 1 : end]),
        origin="src_root",
    )


def _int_or_default(value: Any, default: int) -> int:
    return value if isinstance(value, int) else default
