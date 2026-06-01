"""Render patch suggestion context and metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gbs_patch_suggest.resolver import ResolvedContext

MANDATORY_INSTRUCTIONS = """## ⚠️ Instructions — MUST follow

1. Generate the patch strictly according to the rules in this document:
   provide candidate(s) as unified diff, each with its approach, explicit
   assumption, and confidence; do NOT fabricate functions/headers; if uncertain,
   say so rather than guessing.

2. This patch is a SUGGESTION DRAFT ONLY. Do NOT apply it to any file.
   Do NOT run `git apply` / `patch`. Do NOT modify the source tree.
   Present the patch to the user for review; the user decides whether to apply.
"""


def write_outputs(resolved: ResolvedContext, output_dir: Path) -> dict[str, Path]:
    """Write patch-suggest context, README, and metadata outputs."""

    output_dir.mkdir(parents=True, exist_ok=True)
    readme_path = output_dir / "README.md"
    context_path = output_dir / "context.md"
    meta_path = output_dir / "meta.json"
    readme_path.write_text(
        render_readme(resolved, context_path=context_path, meta_path=meta_path),
        encoding="utf-8",
    )
    context_path.write_text(render_context(resolved), encoding="utf-8")
    meta_path.write_text(
        json.dumps(
            render_meta(
                resolved,
                readme_path=readme_path,
                context_path=context_path,
                meta_path=meta_path,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"readme_md": readme_path, "context_md": context_path, "meta_json": meta_path}


def render_readme(resolved: ResolvedContext, *, context_path: Path, meta_path: Path) -> str:
    """Render a short README for the patch-suggest output directory."""

    evidence = resolved.evidence
    parts = [
        "# Patch Suggestion Output",
        "",
        "This directory contains patch-generation context prepared from one analyzer diagnostic.",
        "",
        "## Selected Diagnostic",
        "",
        f"- Fault class: `{evidence.kind}`",
        f"- Semantic class: `{evidence.semantic_class}`",
        f"- Location: `{_location(evidence.file, evidence.line, evidence.column)}`",
        f"- Message: `{evidence.message or 'n/a'}`",
        f"- Status: `{resolved.status}`",
        f"- Context level: `{resolved.level}`",
        "",
        "## Files",
        "",
        f"- `{context_path.name}`: primary file for the outer assistant to read.",
        f"- `{meta_path.name}`: machine-readable metadata for this run.",
        "",
        "## Guidance",
        "",
        "Read `context.md` first. It contains the diagnostic, available source context or "
        "advisory, and the patch-generation rules for the outer assistant.",
        "",
        "This skill did not generate a patch, did not apply a patch, and did not modify the "
        "source tree.",
        "",
    ]
    return "\n".join(parts)


def render_context(resolved: ResolvedContext) -> str:
    """Render the LLM-facing context file."""

    evidence = resolved.evidence
    parts = [
        "# Patch Suggestion Context",
        "",
        "This file prepares context for the outer assistant. The skill did not call an LLM, "
        "did not apply a patch, and did not modify the source tree.",
        "",
        "## Selected Diagnostic",
        "",
        f"- Fault class: `{evidence.kind}`",
        f"- Semantic class: `{evidence.semantic_class}`",
        f"- Location: `{_location(evidence.file, evidence.line, evidence.column)}`",
        f"- Message: `{evidence.message or 'n/a'}`",
        f"- Context level: `{resolved.level}`",
        f"- Status: `{resolved.status}`",
        "",
    ]

    if resolved.level == "not_applicable":
        parts.extend(
            [
                "## Not Applicable",
                "",
                resolved.advisory or "This diagnostic is not a compiler error.",
                "",
                _patch_guidance_not_applicable(),
                "",
            ]
        )
    elif resolved.source_context is not None:
        source = resolved.source_context
        parts.extend(
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
                _patch_guidance_level_a(evidence.semantic_class),
                "",
            ]
        )
    else:
        candidate_lines = []
        if resolved.candidates:
            candidate_lines = [
                "",
                "Candidate matches found under the source root:",
                *[f"- `{candidate}`" for candidate in resolved.candidates],
                "",
            ]
        parts.extend(
            [
                "## Source Context Advisory",
                "",
                resolved.advisory or "Source context is unavailable.",
                *candidate_lines,
                "",
                "Do not invent source content. If a patch is needed, inspect the referenced "
                "file first or explain why the available diagnostic is insufficient.",
                "",
                _patch_guidance_without_source(resolved),
                "",
            ]
        )

    parts.extend([MANDATORY_INSTRUCTIONS.rstrip(), ""])
    return "\n".join(parts)


def render_meta(
    resolved: ResolvedContext,
    *,
    readme_path: Path,
    context_path: Path,
    meta_path: Path,
) -> dict[str, Any]:
    """Render machine-readable patch-suggest metadata."""

    evidence = resolved.evidence
    source = resolved.source_context
    return {
        "schema_version": "gbs_patch_suggest/meta/v1",
        "status": resolved.status,
        "level": resolved.level,
        "applicable": evidence.is_compiler,
        "fault_class": evidence.kind,
        "semantic_class": evidence.semantic_class,
        "primary_error": {
            "kind": evidence.kind,
            "message": evidence.message,
            "file": evidence.file,
            "line": evidence.line,
            "column": evidence.column,
        },
        "has_source_context": source is not None,
        "source_context": None
        if source is None
        else {
            "path": source.path,
            "start_line": source.start_line,
            "end_line": source.end_line,
            "origin": source.origin,
        },
        "candidate_paths": list(resolved.candidates),
        "advisory": resolved.advisory,
        "outputs": {
            "readme_md": str(readme_path),
            "context_md": str(context_path),
            "meta_json": str(meta_path),
        },
    }


def _location(file: str | None, line: int | None, column: int | None) -> str:
    if not file:
        return "n/a"
    if line is None:
        return file
    if column is None:
        return f"{file}:{line}"
    return f"{file}:{line}:{column}"


def _patch_guidance_level_a(semantic_class: str) -> str:
    return "\n".join(
        [
            "## How to generate the patch",
            "",
            "Use the diagnostic and source context above to prepare patch suggestion(s) "
            "for the user:",
            "",
            "1. Generate 1-3 candidate fixes as unified diff blocks.",
            "2. For each candidate, include its approach, explicit assumption, and confidence.",
            "3. Prefer the smallest patch that addresses the root cause; avoid broad refactors.",
            "4. Treat the semantic class as a hint, not as proof.",
            f"   Current semantic class: `{semantic_class}`.",
            "5. If the source context is insufficient, say what is missing instead of guessing.",
        ]
    )


def _patch_guidance_without_source(resolved: ResolvedContext) -> str:
    if resolved.status == "source_context_ambiguous":
        return "\n".join(
            [
                "## How to generate the patch",
                "",
                "Do not choose a source file blindly. First inspect the candidate path list above, "
                "decide which file matches the diagnostic, and read that file around the reported "
                "line before writing any patch.",
                "",
                "After confirming the correct file and context, generate 1-3 candidate "
                "unified diffs. "
                "For each candidate, include its approach, explicit assumption, and confidence. "
                "Prefer a minimal patch and treat the semantic class as a hint, not as proof.",
            ]
        )
    if resolved.level == "C":
        return "\n".join(
            [
                "## How to generate the patch",
                "",
                "Do not generate a patch from this diagnostic alone. There is no usable file and "
                "line number, so first obtain source location or additional build context. If that "
                "is not possible, explain that the available diagnostic is insufficient.",
            ]
        )
    return "\n".join(
        [
            "## How to generate the patch",
            "",
            "First open the reported file and inspect the source around the reported line. Do not "
            "generate a patch until that source context has been checked.",
            "",
            "After reading the file, generate 1-3 candidate unified diffs. For each candidate, "
            "include its approach, explicit assumption, and confidence. Prefer a minimal patch "
            "and treat the semantic class as a hint, not as proof.",
        ]
    )


def _patch_guidance_not_applicable() -> str:
    return "\n".join(
        [
            "## How to proceed",
            "",
            "This skill only prepares patch context for compiler diagnostics. Use the workflow "
            "suggester for this fault class instead of generating a source patch here.",
        ]
    )
