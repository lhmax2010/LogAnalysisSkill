"""Render patch suggestion context and metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gbs_patch_suggest.resolver import ResolvedContext

MANDATORY_INSTRUCTIONS = """## ⚠️ Instructions — MUST follow

1. Generate the patch strictly according to the rules in this document:
   decide candidate edit spec(s), each with its approach, explicit assumption,
   and confidence; use `format-patch` to produce unified diff patch files; do
   NOT fabricate functions/headers; if uncertain, say so rather than guessing.
   Do NOT hand-write unified diffs. If the formatter fails, revise the edit spec
   and rerun the formatter.

2. This patch is a SUGGESTION DRAFT ONLY. Do NOT apply it to any file.
   You may write candidate `.patch` files to disk as suggestion artifacts for
   review, but writing a `.patch` file is NOT applying it.
   Do NOT run `git apply` / `patch`. Do NOT modify the source tree.
   The user reviews the patch file and decides whether to run `git apply`.
"""


def write_outputs(
    resolved: ResolvedContext,
    output_dir: Path,
    *,
    evidence_path: Path | None = None,
    buildlog_path: Path | None = None,
) -> dict[str, Path]:
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
                evidence_path=evidence_path,
                buildlog_path=buildlog_path,
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
                resolved.advisory
                or "This diagnostic is not a compiler or Werror source diagnostic.",
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
    evidence_path: Path | None = None,
    buildlog_path: Path | None = None,
) -> dict[str, Any]:
    """Render machine-readable patch-suggest metadata."""

    evidence = resolved.evidence
    source = resolved.source_context
    return {
        "schema_version": "gbs_patch_suggest/meta/v1",
        "status": resolved.status,
        "level": resolved.level,
        "applicable": evidence.is_source_diagnostic,
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
        "inputs": {
            "evidence_json": None if evidence_path is None else str(evidence_path),
            "buildlog": None if buildlog_path is None else str(buildlog_path),
        },
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
            "1. Decide 1-3 candidate fixes and write each one as an edit spec.",
            "2. For each candidate, include its approach, explicit assumption, and confidence.",
            "3. Prefer the smallest patch that addresses the root cause; avoid broad refactors.",
            *_root_cause_verification_guidance(start_index=4),
            "6. Treat the semantic class as a hint, not as proof.",
            f"   Current semantic class: `{semantic_class}`.",
            "7. If the source context is insufficient, say what is missing instead of guessing.",
            "",
            *_patch_file_guidance(),
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
                "After confirming the correct file and context, decide 1-3 candidate fixes "
                "and write each one as an edit spec. "
                "For each candidate, include its approach, explicit assumption, and confidence. "
                "Prefer a minimal patch and treat the semantic class as a hint, not as proof.",
                "",
                *_root_cause_verification_guidance(),
                "",
                *_patch_file_guidance(),
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
            "After reading the file, decide 1-3 candidate fixes and write each one as an "
            "edit spec. For each candidate, "
            "include its approach, explicit assumption, and confidence. Prefer a minimal patch "
            "and treat the semantic class as a hint, not as proof.",
            "",
            *_root_cause_verification_guidance(),
            "",
            *_patch_file_guidance(),
        ]
    )


def _patch_guidance_not_applicable() -> str:
    return "\n".join(
        [
            "## How to proceed",
            "",
            "This skill only prepares patch context for compiler and Werror source "
            "diagnostics. Use the workflow suggester for this fault class instead of "
            "generating a source patch here.",
        ]
    )


def _root_cause_verification_guidance(*, start_index: int | None = None) -> list[str]:
    prefix_a = f"{start_index}. " if start_index is not None else "- "
    prefix_b = f"{start_index + 1}. " if start_index is not None else "- "
    return [
        (
            f"{prefix_a}The reported error may be a symptom, not the root cause. Before "
            "assuming a minimal syntactic fix, consider whether the offending line or symbol "
            "should exist at all, such as a call to an undefined function, a stray token, or "
            "leftover/incomplete code."
        ),
        (
            f"{prefix_b}Before finalizing the patch, verify that functions or symbols "
            "referenced near the error actually exist. Search the source tree, for example "
            "with grep, for their definition. If a referenced symbol is not defined anywhere "
            "and you cannot verify it should exist, flag it explicitly and consider whether "
            "the fix is to remove or correct the offending code rather than preserve it. "
            "Do not silently keep an unverified symbol."
        ),
    ]


def _patch_file_guidance() -> list[str]:
    return [
        "Patch formatter workflow:",
        "",
        "- For each semantic candidate, write an `edit_spec_N.json` file in the output "
        "directory. The edit spec contains explicit `file`, `old`, and `new` values; "
        "include `line`, `before`, or `after` when needed to disambiguate repeated old text.",
        "- If the same `old` text appears in multiple places, do NOT make `old` huge by "
        "copying many surrounding lines just to force uniqueness. Keep `old` to the "
        "smallest text that should change, and write one edit per occurrence with its "
        "own `line` value. If line is still not enough, add short `before` or `after` "
        "anchors.",
        "",
        "  Example for two identical old snippets at lines 515 and 525:",
        "",
        "  ```json",
        '  {',
        '    "schema_version": "gbs_patch_suggest/edit-spec/v1",',
        '    "patch_name": "candidate_1.patch",',
        '    "edits": [',
        '      {',
        '        "file": "src/tdm_meson_hwc.c",',
        '        "line": 515,',
        '        "old": "<smallest exact text to replace>",',
        '        "new": "<replacement text>"',
        '      },',
        '      {',
        '        "file": "src/tdm_meson_hwc.c",',
        '        "line": 525,',
        '        "old": "<smallest exact text to replace>",',
        '        "new": "<replacement text>"',
        '      }',
        '    ]',
        '  }',
        "  ```",
        "",
        "- Run the deterministic formatter to produce the patch file instead of "
        "hand-writing unified diff text:",
        "",
        "  ```bash",
        "  python3 -m gbs_patch_suggest format-patch \\",
        "      --src-root /path/to/source \\",
        "      --edit-spec .gbs_patch_suggest/edit_spec_N.json \\",
        "      --output .gbs_patch_suggest/candidate_N.patch \\",
        "      --check",
        "  ```",
        "",
        "- The formatter reads the real source file, applies the explicit edit only to a "
        "temporary copy, uses `git diff --no-index` to create a standard unified diff, "
        "and never modifies the source tree.",
        "- If the formatter fails because `old` is missing, ambiguous, or does not pass "
        "`git apply --check`, revise `edit_spec_N.json` and rerun the formatter. Do NOT "
        "fall back to hand-writing a unified diff.",
        "- If the formatter reports `old_not_unique` or `context_not_unique`, use the "
        "reported error code and candidate line numbers to add `line`, `before`, or "
        "`after`. Do NOT read the formatter source code to infer rules, and do NOT "
        "make `old` a giant multi-line block as a workaround.",
        "- Tell the user where each `candidate_N.patch` file was written.",
        "- Writing the `.patch` file only saves the suggestion to disk for review. It does "
        "NOT mean the patch should be applied. The user, not you, runs `git apply` after "
        "reviewing. Writing the file and applying are completely separate actions.",
    ]
