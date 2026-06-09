"""Render per-candidate patch context outputs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gbs_patch_suggest.formatter import EDIT_SPEC_SCHEMA
from gbs_patch_suggest.multi_candidate_ingest import (
    MultiCandidateDiagnostic,
    SkippedCandidate,
)
from gbs_patch_suggest.render import MANDATORY_INSTRUCTIONS
from gbs_patch_suggest.resolver import ResolvedContext

FILL_REPLACEMENT_LINE = "<FILL_REPLACEMENT_LINE>"


@dataclass(frozen=True)
class ResolvedCandidateContext:
    """Resolved source context for one independent candidate."""

    diagnostic: MultiCandidateDiagnostic
    resolved: ResolvedContext
    missing_line_text: bool = False


def write_multi_candidate_outputs(
    candidates: tuple[ResolvedCandidateContext, ...],
    skipped: tuple[SkippedCandidate, ...],
    output_dir: Path,
    *,
    evidence_path: Path | None = None,
    buildlog_path: Path | None = None,
) -> dict[str, Path]:
    """Write overview, per-candidate contexts, skeletons, and metadata."""

    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_context_dir = output_dir / "candidate_context"
    candidate_context_dir.mkdir(parents=True, exist_ok=True)

    candidate_outputs: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_dir = candidate_context_dir / candidate.diagnostic.candidate_id
        edit_specs_dir = candidate_dir / "edit_specs"
        edit_specs_dir.mkdir(parents=True, exist_ok=True)
        edit_spec_path = _write_edit_spec_skeleton(candidate, edit_specs_dir=edit_specs_dir)
        context_path = candidate_dir / "context.md"
        context_path.write_text(
            render_candidate_context(candidate, edit_spec_path=edit_spec_path),
            encoding="utf-8",
        )
        candidate_outputs.append(
            {
                "candidate": candidate,
                "path": candidate_dir,
                "context_path": context_path,
                "edit_spec_path": edit_spec_path,
            }
        )

    readme_path = output_dir / "README.md"
    context_path = output_dir / "context.md"
    meta_path = output_dir / "meta.json"
    readme_path.write_text(render_multi_candidate_readme(candidate_outputs), encoding="utf-8")
    context_path.write_text(
        render_multi_candidate_overview(candidate_outputs, skipped=skipped),
        encoding="utf-8",
    )
    meta_path.write_text(
        json.dumps(
            render_multi_candidate_meta(
                candidate_outputs,
                skipped=skipped,
                readme_path=readme_path,
                context_path=context_path,
                meta_path=meta_path,
                evidence_path=evidence_path,
                buildlog_path=buildlog_path,
                candidate_context_dir=candidate_context_dir,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "readme_md": readme_path,
        "context_md": context_path,
        "meta_json": meta_path,
        "candidate_context_dir": candidate_context_dir,
    }


def render_multi_candidate_readme(candidate_outputs: list[dict[str, Any]]) -> str:
    """Render README for multi-candidate mode."""

    return "\n".join(
        [
            "# Patch Suggestion Output",
            "",
            "This directory contains patch-generation context for multiple independent "
            "terminal source diagnostics.",
            "",
            "## Summary",
            "",
            f"- Candidate context count: `{len(candidate_outputs)}`",
            "- Mode: `multi_candidate`",
            "",
            "## Files",
            "",
            "- `context.md`: overview and processing order.",
            "- `meta.json`: machine-readable metadata for this run.",
            "- `candidate_context/`: per-candidate contexts and edit specs.",
            "",
            "## Guidance",
            "",
            "Read `context.md` first, then process one candidate context at a time. "
            "Do not load every candidate context at once, and do not read the raw buildlog.",
            "",
            "This skill did not generate a patch, did not apply a patch, and did not modify "
            "the source tree.",
            "",
        ]
    )


def render_multi_candidate_overview(
    candidate_outputs: list[dict[str, Any]],
    *,
    skipped: tuple[SkippedCandidate, ...],
) -> str:
    """Render top-level overview for multi-candidate mode."""

    lines = [
        "# Multi-candidate Patch Suggestion Context",
        "",
        "This file is an overview for multiple independent terminal source diagnostics "
        "exposed by analyzer `root_cause_candidates`. The skill did not read the raw "
        "buildlog, did not call an LLM, did not apply a patch, and did not modify the "
        "source tree.",
        "",
        "## Processing Rules",
        "",
        "- Process one candidate at a time.",
        "- Do not load every candidate context at once.",
        "- Do not read the raw buildlog; this mode only covers candidate diagnostics "
        "visible in `root_cause_candidates`.",
        "- For each candidate, fill the edit spec skeleton when available, then run "
        "`format-patch` to create one candidate patch.",
        "- Cascade and non-source candidates are skipped; do not patch them here.",
        "",
        "## Candidate Contexts",
        "",
    ]
    for output in candidate_outputs:
        candidate: ResolvedCandidateContext = output["candidate"]
        evidence = candidate.resolved.evidence
        lines.append(
            f"- `{_relative(output['context_path'], output['context_path'].parents[1])}` "
            f"for `{candidate.diagnostic.event_id}` ({evidence.file}:{evidence.line}, "
            f"status `{candidate.resolved.status}`)"
        )
    if skipped:
        lines.extend(["", "## Skipped Candidates", ""])
        for item in skipped:
            lines.append(
                f"- `{item.event_id or 'unknown'}` kind `{item.kind or 'unknown'}`: "
                f"`{item.reason}`"
            )
    lines.extend(["", MANDATORY_INSTRUCTIONS.rstrip(), ""])
    return "\n".join(lines)


def render_candidate_context(
    candidate: ResolvedCandidateContext,
    *,
    edit_spec_path: Path | None,
) -> str:
    """Render one independent candidate context."""

    diagnostic = candidate.diagnostic
    resolved = candidate.resolved
    evidence = resolved.evidence
    patch_name = _patch_name(diagnostic)
    edit_spec_name = _edit_spec_name(diagnostic)
    edit_spec_command_path = (
        f".gbs_patch_suggest/{_relative(edit_spec_path, edit_spec_path.parents[2])}"
        if edit_spec_path is not None
        else (
            ".gbs_patch_suggest/candidate_context/"
            f"{diagnostic.candidate_id}/edit_specs/{edit_spec_name}"
        )
    )
    lines = [
        f"# Candidate Patch Context: `{diagnostic.event_id}`",
        "",
        "Use this file by itself. Do not load every candidate context at once.",
        "",
        "## Candidate",
        "",
        f"- Candidate id: `{diagnostic.candidate_id}`",
        f"- Event id: `{diagnostic.event_id}`",
        f"- Rank: `{diagnostic.rank if diagnostic.rank is not None else 'n/a'}`",
        f"- Fault class: `{evidence.kind}`",
        f"- Semantic class: `{evidence.semantic_class}`",
        f"- Location: `{_location(evidence.file, evidence.line, evidence.column)}`",
        f"- Message: `{evidence.message}`",
        f"- Context level: `{resolved.level}`",
        f"- Status: `{resolved.status}`",
        "",
    ]
    if edit_spec_path is not None:
        lines.extend(
            [
                "## Generated Edit Spec Skeleton",
                "",
                f"- Skeleton: `{_relative(edit_spec_path, edit_spec_path.parents[1])}`",
                "- Keep `file`, `line`, and `old` unchanged unless the formatter reports a "
                "specific mismatch.",
                f"- Fill `{FILL_REPLACEMENT_LINE}` with the corrected full source line.",
                "- The skeleton is not repeated here to avoid duplicating source text and token "
                "usage; open the JSON file when you are ready to fill `new`.",
                "",
            ]
        )
    if candidate.missing_line_text:
        lines.extend(
            [
                "## Missing Line Text",
                "",
                "The reported line was outside the readable source context, so no skeleton "
                "edit was generated. Verify the file and line before writing an edit spec.",
                "",
            ]
        )

    if resolved.source_context is not None:
        source = resolved.source_context
        lines.extend(
            [
                "## Source Context",
                "",
                f"- Source path: `{source.path}`",
                f"- Lines: `{source.start_line}-{source.end_line}`",
                f"- Origin: `{source.origin}`",
                "",
                "```",
                source.text,
                "```",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Source Context Advisory",
                "",
                resolved.advisory or "Source context is unavailable.",
                "",
            ]
        )
        if resolved.candidates:
            lines.extend(["Candidate source matches:", ""])
            lines.extend(f"- `{path}`" for path in resolved.candidates)
            lines.append("")

    lines.extend(["## How to generate the patch for this candidate", ""])
    if edit_spec_path is not None:
        lines.extend(
            [
                "1. Work only on this candidate context before moving to the next candidate.",
                f"2. Open the generated edit spec skeleton: "
                f"`{_relative(edit_spec_path, edit_spec_path.parents[1])}`.",
                "3. Preserve `file`, `line`, and `old` unless the formatter reports a specific "
                "mismatch. The `old` value is an exact whole source line copied by the skill, "
                "including tabs and spaces.",
                f"4. Replace `{FILL_REPLACEMENT_LINE}` with the corrected full source line.",
                "5. Run the deterministic formatter; do not hand-write unified diff text and "
                "do not edit the source file directly.",
            ]
        )
    else:
        lines.extend(
            [
                "1. Work only on this candidate context before moving to the next candidate.",
                "2. Source context is unavailable or ambiguous, so no skeleton was generated.",
                "3. First open the correct file around the listed line and inspect the source.",
                "4. Write an edit spec only after you have verified the real source text.",
                "5. Run the deterministic formatter; do not hand-write unified diff text and "
                "do not edit the source file directly.",
            ]
        )
    lines.extend(
        [
            "",
            "Recommended names:",
            "",
            "```bash",
            edit_spec_name,
            patch_name,
            "```",
            "",
            "Formatter command:",
            "",
            "```bash",
            "python3 -m gbs_patch_suggest format-patch \\",
            "    --src-root /path/to/source \\",
            f"    --edit-spec {edit_spec_command_path} \\",
            f"    --output .gbs_patch_suggest/{patch_name} \\",
            "    --check",
            "```",
            "",
            "If the formatter fails, fix the edit spec and rerun the formatter. Do not fall "
            "back to hand-writing a unified diff, and do not edit the source file directly.",
            "",
            MANDATORY_INSTRUCTIONS.rstrip(),
            "",
        ]
    )
    return "\n".join(lines)


def render_multi_candidate_meta(
    candidate_outputs: list[dict[str, Any]],
    *,
    skipped: tuple[SkippedCandidate, ...],
    readme_path: Path,
    context_path: Path,
    meta_path: Path,
    evidence_path: Path | None,
    buildlog_path: Path | None,
    candidate_context_dir: Path,
) -> dict[str, Any]:
    """Render machine-readable metadata for multi-candidate mode."""

    return {
        "schema_version": "gbs_patch_suggest/meta/v1",
        "mode": "multi_candidate",
        "status": "multi_candidate_context_available",
        "outputs": {
            "readme_md": str(readme_path),
            "context_md": str(context_path),
            "meta_json": str(meta_path),
            "candidate_context_dir": str(candidate_context_dir),
        },
        "inputs": {
            "evidence_json": None if evidence_path is None else str(evidence_path),
            "buildlog": None if buildlog_path is None else str(buildlog_path),
        },
        "candidates": [
            {
                "candidate_id": output["candidate"].diagnostic.candidate_id,
                "event_id": output["candidate"].diagnostic.event_id,
                "rank": output["candidate"].diagnostic.rank,
                "status": output["candidate"].resolved.status,
                "level": output["candidate"].resolved.level,
                "context_md": str(output["context_path"]),
                "edit_spec_json": None
                if output["edit_spec_path"] is None
                else str(output["edit_spec_path"]),
                "file": output["candidate"].resolved.evidence.file,
                "line": output["candidate"].resolved.evidence.line,
                "message": output["candidate"].resolved.evidence.message,
                "missing_line_text": output["candidate"].missing_line_text,
            }
            for output in candidate_outputs
        ],
        "skipped_candidates": [
            {
                "event_id": item.event_id,
                "kind": item.kind,
                "rank": item.rank,
                "reason": item.reason,
                "summary": item.summary,
            }
            for item in skipped
        ],
    }


def _write_edit_spec_skeleton(
    candidate: ResolvedCandidateContext,
    *,
    edit_specs_dir: Path,
) -> Path | None:
    source = candidate.resolved.source_context
    evidence = candidate.resolved.evidence
    if source is None or evidence.file is None or evidence.line is None:
        return None
    line_text = _line_text(source.text, source.start_line, evidence.line)
    if line_text is None:
        return None
    path = edit_specs_dir / _edit_spec_name(candidate.diagnostic)
    data = {
        "schema_version": EDIT_SPEC_SCHEMA,
        "patch_name": _patch_name(candidate.diagnostic),
        "description": "Fill new for this independent source diagnostic.",
        "edits": [
            {
                "file": evidence.file,
                "line": evidence.line,
                "old": line_text,
                "new": FILL_REPLACEMENT_LINE,
            }
        ],
    }
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _line_text(text: str, start_line: int, target_line: int) -> str | None:
    index = target_line - start_line
    if index < 0:
        return None
    lines = text.splitlines()
    if index >= len(lines):
        return None
    return lines[index]


def _edit_spec_name(candidate: MultiCandidateDiagnostic) -> str:
    return f"edit_spec_{candidate.candidate_id}_{_file_slug(candidate.evidence.file)}.json"


def _patch_name(candidate: MultiCandidateDiagnostic) -> str:
    return f"candidate_{candidate.candidate_id}_{_file_slug(candidate.evidence.file)}.patch"


def _file_slug(file_value: str | None) -> str:
    if not file_value:
        return "unknown"
    return _slug(Path(file_value).name)


def _slug(value: str, *, max_length: int = 80) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip("/"))
    slug = slug.strip("_") or "item"
    return slug[:max_length].rstrip("_") or "item"


def _location(file: str | None, line: int | None, column: int | None) -> str:
    if not file:
        return "n/a"
    if line is None:
        return file
    if column is None:
        return f"{file}:{line}"
    return f"{file}:{line}:{column}"


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
