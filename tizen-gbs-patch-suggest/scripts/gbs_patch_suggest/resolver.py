"""Resolve source-context availability for patch suggestion prompts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gbs_patch_suggest.ingest import CompileErrorEvidence

DEFAULT_CONTEXT_WINDOW = 30
SKIPPED_DIR_NAMES = {
    ".git",
    ".gbs_patch_suggest",
    ".gbs_workflow",
    "build",
    "node_modules",
}


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
    candidates: tuple[str, ...] = ()

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
        candidate_paths = resolve_candidate_paths(evidence.file, src_root)
        if len(candidate_paths) == 1:
            return ResolvedContext(
                status="source_context_available",
                level="A",
                evidence=evidence,
                source_context=_context_from_file(
                    candidate_paths[0],
                    evidence.line,
                    window=window,
                ),
            )
        if len(candidate_paths) > 1:
            return ResolvedContext(
                status="source_context_ambiguous",
                level="B",
                evidence=evidence,
                advisory=(
                    f"Multiple source files match `{evidence.file}` under the provided "
                    "source root. Ask the outer assistant or user to disambiguate before "
                    "generating a patch."
                ),
                candidates=tuple(str(path) for path in candidate_paths[:10]),
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


def resolve_candidate_paths(file_value: str, src_root: Path | None) -> list[Path]:
    """Return source candidates inside src_root using path-segment suffix matching."""

    if src_root is None or not src_root.is_dir():
        return []
    root = src_root.resolve()
    requested = Path(file_value)
    if requested.is_absolute():
        return _absolute_candidate(requested, root)

    requested_parts = requested.parts
    if not requested_parts:
        return []
    basename = requested.name
    candidates: list[Path] = []
    for path in _iter_files_by_basename(root, basename):
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if len(relative_parts) >= len(requested_parts) and (
            relative_parts[-len(requested_parts) :] == requested_parts
        ):
            candidates.append(path)
    return sorted(candidates)


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
        origin="src_root_suffix_search",
    )


def _absolute_candidate(path: Path, root: Path) -> list[Path]:
    candidate = path.resolve()
    if not candidate.is_file():
        return []
    try:
        candidate.relative_to(root)
    except ValueError:
        return []
    return [candidate]


def _iter_files_by_basename(root: Path, basename: str) -> list[Path]:
    matches: list[Path] = []
    pending = [root]
    while pending:
        current = pending.pop()
        try:
            children = sorted(current.iterdir(), key=lambda item: item.name)
        except OSError:
            continue
        for child in children:
            if child.is_dir():
                if _should_skip_dir(child):
                    continue
                pending.append(child)
            elif child.is_file() and child.name == basename:
                matches.append(child)
    return matches


def _should_skip_dir(path: Path) -> bool:
    return path.name in SKIPPED_DIR_NAMES or path.name.startswith("GBS-ROOT")


def _int_or_default(value: Any, default: int) -> int:
    return value if isinstance(value, int) else default
