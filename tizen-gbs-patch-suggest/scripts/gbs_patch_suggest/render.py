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
    """Write PS-M1 context and metadata outputs."""

    output_dir.mkdir(parents=True, exist_ok=True)
    context_path = output_dir / "context.md"
    meta_path = output_dir / "meta.json"
    context_path.write_text(render_context(resolved), encoding="utf-8")
    meta_path.write_text(
        json.dumps(render_meta(resolved, context_path=context_path), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return {"context_md": context_path, "meta_json": meta_path}


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
            ]
        )
    else:
        parts.extend(
            [
                "## Source Context Advisory",
                "",
                resolved.advisory or "Source context is unavailable.",
                "",
                "Do not invent source content. If a patch is needed, inspect the referenced "
                "file first or explain why the available diagnostic is insufficient.",
                "",
            ]
        )

    parts.extend([MANDATORY_INSTRUCTIONS.rstrip(), ""])
    return "\n".join(parts)


def render_meta(resolved: ResolvedContext, *, context_path: Path) -> dict[str, Any]:
    """Render machine-readable PS-M1 metadata."""

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
        "advisory": resolved.advisory,
        "outputs": {"context_md": str(context_path)},
    }


def _location(file: str | None, line: int | None, column: int | None) -> str:
    if not file:
        return "n/a"
    if line is None:
        return file
    if column is None:
        return f"{file}:{line}"
    return f"{file}:{line}:{column}"
