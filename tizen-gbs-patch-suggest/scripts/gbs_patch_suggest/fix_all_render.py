"""Render experimental fix-all by file patch context outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from gbs_patch_suggest.cluster_resolver import ClusterFileContext
from gbs_patch_suggest.fix_all_ingest import SourceCandidateDiagnostic
from gbs_patch_suggest.fix_all_resolver import ResolvedFixAllContext
from gbs_patch_suggest.formatter import EDIT_SPEC_SCHEMA
from gbs_patch_suggest.render import MANDATORY_INSTRUCTIONS

FILL_REPLACEMENT_LINE = "<FILL_REPLACEMENT_LINE>"


def write_fix_all_outputs(
    resolved: ResolvedFixAllContext,
    output_dir: Path,
    *,
    evidence_path: Path | None = None,
    buildlog_path: Path | None = None,
) -> dict[str, Path]:
    """Write overview, per-file contexts, skeletons, and metadata."""

    output_dir.mkdir(parents=True, exist_ok=True)
    fix_all_dir = output_dir / "fix_all_context"
    files_dir = fix_all_dir / "files"
    edit_specs_dir = fix_all_dir / "edit_specs"
    files_dir.mkdir(parents=True, exist_ok=True)
    edit_specs_dir.mkdir(parents=True, exist_ok=True)

    file_outputs: list[dict[str, Any]] = []
    for file_context in resolved.file_contexts:
        context_path = files_dir / _file_context_name(file_context)
        edit_spec_path = _write_edit_spec_skeleton(file_context, edit_specs_dir=edit_specs_dir)
        context_path.write_text(
            render_file_context(file_context, edit_spec_path=edit_spec_path),
            encoding="utf-8",
        )
        file_outputs.append(
            {
                "context": file_context,
                "path": context_path,
                "edit_spec_path": edit_spec_path,
            }
        )

    readme_path = output_dir / "README.md"
    context_path = output_dir / "context.md"
    meta_path = output_dir / "meta.json"
    readme_path.write_text(render_readme(resolved, file_outputs=file_outputs), encoding="utf-8")
    context_path.write_text(
        render_overview(resolved, file_outputs=file_outputs),
        encoding="utf-8",
    )
    meta_path.write_text(
        json.dumps(
            render_meta(
                resolved,
                file_outputs=file_outputs,
                readme_path=readme_path,
                context_path=context_path,
                meta_path=meta_path,
                evidence_path=evidence_path,
                buildlog_path=buildlog_path,
                fix_all_dir=fix_all_dir,
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
        "fix_all_context_dir": fix_all_dir,
    }


def render_readme(
    resolved: ResolvedFixAllContext,
    *,
    file_outputs: list[dict[str, Any]],
) -> str:
    """Render README for experimental fix-all mode."""

    return "\n".join(
        [
            "# Patch Suggestion Output",
            "",
            "This directory contains experimental fix-all-by-file context prepared from "
            "analyzer `source_candidates` evidence.",
            "",
            "## Summary",
            "",
            f"- Source candidate count: `{len(resolved.candidates)}`",
            f"- Patch-ready candidate count: `{len(resolved.patch_ready_candidates)}`",
            f"- Patch-ready file count: `{len(file_outputs)}`",
            "- Mode: `fix_all_by_file`",
            "",
            "## Files",
            "",
            "- `context.md`: overview and processing order.",
            "- `meta.json`: machine-readable metadata for this run.",
            "- `fix_all_context/`: per-file contexts and edit specs for patch-ready files.",
            "",
            "## Guidance",
            "",
            "Read `context.md` first, then process one patch-ready file context at a time. "
            "Do not load every per-file context at once, and do not read the raw buildlog.",
            "",
            "This skill did not generate a patch, did not apply a patch, and did not modify "
            "the source tree.",
            "",
        ]
    )


def render_overview(
    resolved: ResolvedFixAllContext,
    *,
    file_outputs: list[dict[str, Any]],
) -> str:
    """Render top-level experimental fix-all overview."""

    not_ready = tuple(candidate for candidate in resolved.candidates if not candidate.patch_ready)
    lines = [
        "# Experimental Fix-all-by-file Patch Context",
        "",
        "This file is an overview for analyzer `source_candidates`. The skill did not "
        "read the raw buildlog, did not call an LLM, did not apply a patch, and did not "
        "modify the source tree.",
        "",
        "## Experimental Scope",
        "",
        "- This mode only covers diagnostics visible in `source_candidates.json`.",
        "- Excluded diagnostics are not part of this coverage universe.",
        "- `large_scale` does not control coverage in this mode.",
        "- Process one file at a time; do not load every per-file context at once.",
        "",
        "## Counts",
        "",
        f"- Source candidates: `{len(resolved.candidates)}`",
        f"- Patch-ready candidates: `{len(resolved.patch_ready_candidates)}`",
        f"- Patch-ready file groups: `{len(file_outputs)}`",
        f"- Visible but not patch-ready: `{len(not_ready)}`",
        "",
    ]

    if file_outputs:
        lines.extend(["## Patch-ready Files", ""])
        for file_output in file_outputs:
            file_context: ClusterFileContext = file_output["context"]
            lines.append(
                f"- `{_relative(file_output['path'], file_output['path'].parents[1])}` "
                f"for `{file_context.file}` ({len(file_context.locations)} candidates, "
                f"status `{file_context.status}`)"
            )
        lines.append("")
    else:
        lines.extend(
            [
                "## Patch-ready Files",
                "",
                "No edit-spec skeletons were generated. The visible diagnostics are either "
                "not type-fixable yet, source-unreachable on this machine, or not owned by "
                "the project source tree.",
                "",
            ]
        )

    if not_ready:
        lines.extend(["## Visible But Not Patch-ready", ""])
        for candidate in not_ready:
            lines.append(
                f"- `{candidate.event_id or 'unknown'}` `{candidate.group_file}:{candidate.line}` "
                f"kind `{candidate.kind}` type `{candidate.type_fixability}` "
                f"source `{candidate.source_resolution_status}` ownership "
                f"`{candidate.source_ownership_status}` reason "
                f"`{candidate.not_patch_ready_reason}`"
            )
        lines.append("")

    lines.extend([MANDATORY_INSTRUCTIONS.rstrip(), ""])
    return "\n".join(lines)


def render_file_context(
    file_context: ClusterFileContext,
    *,
    edit_spec_path: Path | None = None,
) -> str:
    """Render one per-file context for experimental fix-all mode."""

    edit_spec_name = _edit_spec_name(file_context)
    patch_name = _patch_name(file_context)
    edit_spec_command_path = (
        f".gbs_patch_suggest/{_relative(edit_spec_path, edit_spec_path.parents[2])}"
        if edit_spec_path is not None
        else f".gbs_patch_suggest/{edit_spec_name}"
    )
    lines = [
        f"# Fix-all File Patch Context: `{file_context.file}`",
        "",
        "Use this file by itself. Do not load every per-file context at once.",
        "",
        "## File Summary",
        "",
        f"- File status: `{file_context.status}`",
        f"- Context level: `{file_context.level}`",
        f"- Patch-ready candidates in this file: `{len(file_context.locations)}`",
        "",
        "## Candidate Locations In This File",
        "",
    ]
    for location in file_context.locations:
        column = "" if location.column is None else f":{location.column}"
        event = "" if location.event_id is None else f"`{location.event_id}` "
        lines.append(f"- {event}line `{location.line}{column}`: `{location.message}`")
    lines.append("")

    if file_context.skeleton_edits and edit_spec_path is not None:
        lines.extend(
            [
                "## Generated Edit Spec Skeleton",
                "",
                f"- Skeleton: `{_relative(edit_spec_path, edit_spec_path.parents[1])}`",
                "- Keep `file`, `line`, and `old` unchanged unless the formatter reports a "
                "specific mismatch.",
                f"- Fill every `{FILL_REPLACEMENT_LINE}` value with the corrected full "
                "source line.",
                "- The skeleton is not repeated here to avoid duplicating source text and token "
                "usage; open the JSON file when you are ready to fill `new`.",
                "",
                "Skeleton edit coverage:",
                "",
            ]
        )
        for edit in file_context.skeleton_edits:
            lines.append(f"- line `{edit.line}` covers:")
            for location in edit.covered_locations:
                column = "" if location.column is None else f":{location.column}"
                event = "" if location.event_id is None else f"`{location.event_id}` "
                lines.append(f"  - {event}`{location.line}{column}`: `{location.message}`")
        lines.append("")

    if file_context.missing_line_text_locations:
        lines.extend(
            [
                "## Missing Line Text",
                "",
                "The following locations were outside the readable source file range, so no "
                "skeleton edit was generated for them:",
                "",
            ]
        )
        for location in file_context.missing_line_text_locations:
            column = "" if location.column is None else f":{location.column}"
            event = "" if location.event_id is None else f"`{location.event_id}` "
            lines.append(f"- {event}line `{location.line}{column}`: `{location.message}`")
        lines.append("")

    if file_context.source_windows:
        lines.extend(
            [
                "## Source Windows",
                "",
                f"- Source path: `{file_context.source_path}`",
                "- Source windows truncated: "
                f"`{str(file_context.source_windows_truncated).lower()}`",
                "",
            ]
        )
        for window in file_context.source_windows:
            lines.extend(
                [
                    f"### Lines {window.start_line}-{window.end_line}",
                    "",
                    "Covers diagnostic lines: "
                    + ", ".join(f"`{line}`" for line in window.diagnostic_lines),
                    "",
                    "```",
                    window.text,
                    "```",
                    "",
                ]
            )
    else:
        lines.extend(
            [
                "## Source Context Advisory",
                "",
                file_context.advisory or "Source context is unavailable.",
                "",
            ]
        )
        if file_context.candidates:
            lines.extend(["Candidate source matches:", ""])
            lines.extend(f"- `{candidate}`" for candidate in file_context.candidates)
            lines.append("")

    lines.extend(
        [
            "## How to generate the patch for this file",
            "",
        ]
    )
    if edit_spec_path is not None:
        lines.extend(
            [
                "1. Work only on this file context before moving to the next file.",
                f"2. Open the generated edit spec skeleton: "
                f"`{_relative(edit_spec_path, edit_spec_path.parents[1])}`.",
                "3. Preserve every `file`, `line`, and `old` value unless the formatter "
                "reports a specific mismatch. The `old` values are exact whole source "
                "lines copied by the skill, including tabs and spaces.",
                f"4. Replace each `{FILL_REPLACEMENT_LINE}` placeholder with the corrected "
                "full source line.",
                "5. Run the deterministic formatter; do not hand-write unified diff text "
                "and do not edit the source file directly.",
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
                "If the formatter fails, fix the edit spec and rerun the formatter. Do not "
                "fall back to hand-writing a unified diff, and do not edit the source file "
                "directly.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "No edit spec skeleton was generated for this file. Inspect the listed "
                "locations and source status before deciding whether a manual edit spec is "
                "appropriate. Do not hand-write a unified diff and do not edit the source "
                "file directly.",
                "",
            ]
        )
    lines.extend([MANDATORY_INSTRUCTIONS.rstrip(), ""])
    return "\n".join(lines)


def render_meta(
    resolved: ResolvedFixAllContext,
    *,
    file_outputs: list[dict[str, Any]],
    readme_path: Path,
    context_path: Path,
    meta_path: Path,
    evidence_path: Path | None,
    buildlog_path: Path | None,
    fix_all_dir: Path,
) -> dict[str, Any]:
    """Render machine-readable metadata for experimental fix-all mode."""

    return {
        "schema_version": "gbs_patch_suggest/meta/v1",
        "mode": "fix_all_by_file",
        "status": "fix_all_context_available",
        "experimental": True,
        "outputs": {
            "readme_md": str(readme_path),
            "context_md": str(context_path),
            "meta_json": str(meta_path),
            "fix_all_context_dir": str(fix_all_dir),
        },
        "inputs": {
            "evidence_json": None if evidence_path is None else str(evidence_path),
            "buildlog": None if buildlog_path is None else str(buildlog_path),
        },
        "counts": {
            "source_candidates": len(resolved.candidates),
            "patch_ready_candidates": len(resolved.patch_ready_candidates),
            "patch_ready_file_groups": len(file_outputs),
            "visible_not_patch_ready": len(resolved.candidates)
            - len(resolved.patch_ready_candidates),
        },
        "candidates": [_candidate_meta(candidate) for candidate in resolved.candidates],
        "files": [
            {
                "file": file_output["context"].file,
                "status": file_output["context"].status,
                "location_count": len(file_output["context"].locations),
                "context_md": str(file_output["path"]),
                "edit_spec_json": None
                if file_output["edit_spec_path"] is None
                else str(file_output["edit_spec_path"]),
                "source_windows_truncated": file_output["context"].source_windows_truncated,
            }
            for file_output in file_outputs
        ],
    }


def _candidate_meta(candidate: SourceCandidateDiagnostic) -> dict[str, Any]:
    return {
        "event_id": candidate.event_id,
        "kind": candidate.kind,
        "file": candidate.file,
        "normalized_file": candidate.normalized_file,
        "line": candidate.line,
        "column": candidate.column,
        "warning_option": candidate.warning_option,
        "semantic_class": candidate.semantic_class,
        "type_fixability": candidate.type_fixability,
        "source_reachable": candidate.source_reachable,
        "source_resolution_status": candidate.source_resolution_status,
        "source_owned": candidate.source_owned,
        "source_ownership_status": candidate.source_ownership_status,
        "patch_ready": candidate.patch_ready,
        "not_patch_ready_reason": candidate.not_patch_ready_reason,
    }


def _write_edit_spec_skeleton(
    file_context: ClusterFileContext,
    *,
    edit_specs_dir: Path,
) -> Path | None:
    if not file_context.skeleton_edits:
        return None
    path = edit_specs_dir / _edit_spec_name(file_context)
    data = {
        "schema_version": EDIT_SPEC_SCHEMA,
        "patch_name": _patch_name(file_context),
        "description": "Fill new values for all patch-ready source candidates in this file.",
        "edits": [
            {
                "file": edit.file,
                "line": edit.line,
                "old": edit.old,
                "new": FILL_REPLACEMENT_LINE,
            }
            for edit in file_context.skeleton_edits
        ],
    }
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _file_context_name(file_context: ClusterFileContext) -> str:
    return f"{file_context.index:03d}_{_file_slug(file_context.file)}.md"


def _edit_spec_name(file_context: ClusterFileContext) -> str:
    return f"edit_spec_FIXALL_{file_context.index:03d}_{_file_slug(file_context.file)}.json"


def _patch_name(file_context: ClusterFileContext) -> str:
    return f"candidate_FIXALL_{file_context.index:03d}_{_file_slug(file_context.file)}.patch"


def _file_slug(file_value: str) -> str:
    return _slug(Path(file_value).name)


def _slug(value: str, *, max_length: int = 80) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip("/"))
    slug = slug.strip("_") or "item"
    return slug[:max_length].rstrip("_") or "item"


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
