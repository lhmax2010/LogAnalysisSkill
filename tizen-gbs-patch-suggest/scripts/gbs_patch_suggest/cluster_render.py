"""Render large-scale cluster patch context outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from gbs_patch_suggest.cluster_resolver import ClusterFileContext, ResolvedCluster
from gbs_patch_suggest.formatter import EDIT_SPEC_SCHEMA
from gbs_patch_suggest.render import MANDATORY_INSTRUCTIONS

FILL_REPLACEMENT_LINE = "<FILL_REPLACEMENT_LINE>"


def write_cluster_outputs(
    clusters: tuple[ResolvedCluster, ...],
    output_dir: Path,
    *,
    evidence_path: Path | None = None,
    buildlog_path: Path | None = None,
) -> dict[str, Path]:
    """Write overview, per-cluster index, per-file context, and metadata."""

    output_dir.mkdir(parents=True, exist_ok=True)
    cluster_context_dir = output_dir / "cluster_context"
    cluster_context_dir.mkdir(parents=True, exist_ok=True)

    cluster_outputs: list[dict[str, Any]] = []
    for cluster in clusters:
        cluster_dir = cluster_context_dir / _cluster_dir_name(cluster)
        files_dir = cluster_dir / "files"
        edit_specs_dir = cluster_dir / "edit_specs"
        files_dir.mkdir(parents=True, exist_ok=True)
        edit_specs_dir.mkdir(parents=True, exist_ok=True)
        file_outputs = []
        for file_context in cluster.file_contexts:
            file_path = files_dir / _file_context_name(file_context)
            edit_spec_path = _write_edit_spec_skeleton(
                cluster,
                file_context,
                edit_specs_dir=edit_specs_dir,
            )
            file_path.write_text(
                render_file_context(cluster, file_context, edit_spec_path=edit_spec_path),
                encoding="utf-8",
            )
            file_outputs.append(
                {"context": file_context, "path": file_path, "edit_spec_path": edit_spec_path}
            )
        index_path = cluster_dir / "index.md"
        index_path.write_text(
            render_cluster_index(cluster, file_outputs=file_outputs),
            encoding="utf-8",
        )
        cluster_outputs.append(
            {
                "cluster": cluster,
                "path": cluster_dir,
                "index_path": index_path,
                "file_outputs": file_outputs,
            }
        )

    readme_path = output_dir / "README.md"
    context_path = output_dir / "context.md"
    meta_path = output_dir / "meta.json"
    readme_path.write_text(render_cluster_readme(cluster_outputs), encoding="utf-8")
    context_path.write_text(render_cluster_overview(cluster_outputs), encoding="utf-8")
    meta_path.write_text(
        json.dumps(
            render_cluster_meta(
                cluster_outputs,
                readme_path=readme_path,
                context_path=context_path,
                meta_path=meta_path,
                evidence_path=evidence_path,
                buildlog_path=buildlog_path,
                cluster_context_dir=cluster_context_dir,
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
        "cluster_context_dir": cluster_context_dir,
    }


def render_cluster_readme(cluster_outputs: list[dict[str, Any]]) -> str:
    """Render README for cluster mode output."""

    cluster_count = len(cluster_outputs)
    file_count = sum(len(output["file_outputs"]) for output in cluster_outputs)
    return "\n".join(
        [
            "# Patch Suggestion Output",
            "",
            "This directory contains large-scale patch context prepared from analyzer "
            "`error_clusters` evidence.",
            "",
            "## Summary",
            "",
            f"- Cluster count: `{cluster_count}`",
            f"- File context count: `{file_count}`",
            "- Mode: `cluster`",
            "",
            "## Files",
            "",
            "- `context.md`: overview and processing order.",
            "- `meta.json`: machine-readable metadata for this run.",
            "- `cluster_context/`: per-cluster indexes and per-file contexts.",
            "",
            "## Guidance",
            "",
            "Read `context.md` first, then process one per-file context at a time. "
            "Do not load every per-file context at once, and do not read the raw buildlog.",
            "",
            "This skill did not generate a patch, did not apply a patch, and did not modify "
            "the source tree.",
            "",
        ]
    )


def render_cluster_overview(cluster_outputs: list[dict[str, Any]]) -> str:
    """Render top-level context.md for cluster mode."""

    lines = [
        "# Large-scale Patch Suggestion Context",
        "",
        "This file is an overview for repeated source diagnostics exposed by analyzer "
        "`error_clusters`. The skill did not read the raw buildlog, did not call an LLM, "
        "did not apply a patch, and did not modify the source tree.",
        "",
        "## Processing Rules",
        "",
        "- Process one file at a time.",
        "- Do not load every per-file context at once.",
        "- Do not read the raw buildlog; this mode only covers locations visible in "
        "`error_clusters.json`.",
        "- For each file, write one edit spec containing all listed locations for that file, "
        "then run `format-patch` to create one file-level patch.",
        "- Sidecar-visible locations are the full scope for this mode; other raw-log errors "
        "are not visible in evidence and are not handled here.",
        "",
        "## Clusters",
        "",
    ]
    for output in cluster_outputs:
        cluster: ResolvedCluster = output["cluster"]
        lines.extend(
            [
                f"### {cluster.id}: `{cluster.warning_option}`",
                "",
                f"- Diagnostic kinds: `{', '.join(cluster.diagnostic_kinds)}`",
                f"- Files: `{len(cluster.file_contexts)}`",
                f"- Analyzer truncation signal: `{str(cluster.truncated).lower()}`",
                f"- Index: `{_relative(output['index_path'], output['path'].parents[1])}`",
                "",
                "Per-file contexts:",
            ]
        )
        for file_output in output["file_outputs"]:
            file_context: ClusterFileContext = file_output["context"]
            lines.append(
                f"- `{_relative(file_output['path'], output['path'].parents[1])}` "
                f"for `{file_context.file}` ({len(file_context.locations)} locations, "
                f"status `{file_context.status}`)"
            )
        lines.append("")

    lines.extend([MANDATORY_INSTRUCTIONS.rstrip(), ""])
    return "\n".join(lines)


def render_cluster_index(
    cluster: ResolvedCluster,
    *,
    file_outputs: list[dict[str, Any]],
) -> str:
    """Render one cluster index."""

    lines = [
        f"# Cluster {cluster.id}: `{cluster.warning_option}`",
        "",
        f"- Diagnostic kinds: `{', '.join(cluster.diagnostic_kinds)}`",
        f"- File count: `{len(cluster.file_contexts)}`",
        f"- Analyzer truncation signal: `{str(cluster.truncated).lower()}`",
        "",
        "Process one file context at a time. Do not load every file context at once.",
        "",
        "## File Contexts",
        "",
    ]
    for file_output in file_outputs:
        file_context: ClusterFileContext = file_output["context"]
        lines.append(
            f"- `{_relative(file_output['path'], file_output['path'].parents[1])}`: "
            f"`{file_context.file}` ({len(file_context.locations)} locations, "
            f"status `{file_context.status}`)"
        )
    lines.append("")
    return "\n".join(lines)


def render_file_context(
    cluster: ResolvedCluster,
    file_context: ClusterFileContext,
    *,
    edit_spec_path: Path | None = None,
) -> str:
    """Render one per-file context."""

    file_slug = _slug(file_context.file)
    edit_spec_name = f"edit_spec_{cluster.id}_{file_context.index:03d}_{file_slug}.json"
    patch_name = _patch_name(cluster, file_context)
    edit_spec_command_path = (
        f".gbs_patch_suggest/{_relative(edit_spec_path, edit_spec_path.parents[3])}"
        if edit_spec_path is not None
        else f".gbs_patch_suggest/{edit_spec_name}"
    )
    lines = [
        f"# File Patch Context: `{file_context.file}`",
        "",
        "Use this file by itself. Do not load every per-file context at once.",
        "",
        "## Cluster",
        "",
        f"- Cluster id: `{cluster.id}`",
        f"- Warning option: `{cluster.warning_option}`",
        f"- Diagnostic kinds: `{', '.join(cluster.diagnostic_kinds)}`",
        f"- File status: `{file_context.status}`",
        f"- Context level: `{file_context.level}`",
        "",
        "## Locations In This File",
        "",
    ]
    for location in file_context.locations:
        column = "" if location.column is None else f":{location.column}"
        lines.append(f"- line `{location.line}{column}`: `{location.message}`")
    lines.append("")
    if file_context.skeleton_edits and edit_spec_path is not None:
        lines.extend(
            [
                "## Generated Edit Spec Skeleton",
                "",
                f"- Skeleton: `{_relative(edit_spec_path, edit_spec_path.parents[1])}`",
                "- Keep `file`, `line`, and `old` unchanged unless the formatter reports a "
                "specific mismatch.",
                f"- Fill every `{FILL_REPLACEMENT_LINE}` value with the corrected source line.",
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
                lines.append(f"  - `{location.line}{column}`: `{location.message}`")
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
            lines.append(f"- line `{location.line}{column}`: `{location.message}`")
        lines.extend(
            [
                "",
                "Confirm these locations manually before preparing edits. Do not guess `old` "
                "text and do not hand-write a diff.",
                "",
            ]
        )

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
        if file_context.source_windows_truncated:
            lines.extend(
                [
                    "Some source windows were truncated to keep this context bounded. "
                    "Open the remaining file:line locations directly if they are needed. "
                    "Do not read the raw buildlog.",
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

    lines.extend(["## How to generate the patch for this file", ""])
    if edit_spec_path is not None:
        lines.extend(
            [
                "1. Work only on this file context before moving to the next file.",
                f"2. Open the generated edit spec skeleton: "
                f"`{_relative(edit_spec_path, edit_spec_path.parents[1])}`.",
                "3. Preserve every `file`, `line`, and `old` value unless the formatter reports "
                "a specific mismatch. The `old` values are exact whole source lines copied by "
                "the skill, including tabs and spaces.",
                f"4. Replace each `{FILL_REPLACEMENT_LINE}` placeholder with the corrected full "
                "source line. Use the locations/messages above to decide the right replacement.",
                "5. Run the deterministic formatter; do not hand-write unified diff text and do "
                "not edit the source file directly.",
            ]
        )
    else:
        lines.extend(
            [
                "1. Work only on this file context before moving to the next file.",
                "2. Source context is unavailable or ambiguous, so no skeleton was generated.",
                "3. First open the correct file around the listed lines and inspect the source.",
                "4. Write an edit spec only after you have verified the real source text. Use "
                "`line`, `before`, or `after` to disambiguate repeated text.",
                "5. Run the deterministic formatter; do not hand-write unified diff text and do "
                "not edit the source file directly.",
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


def render_cluster_meta(
    cluster_outputs: list[dict[str, Any]],
    *,
    readme_path: Path,
    context_path: Path,
    meta_path: Path,
    evidence_path: Path | None,
    buildlog_path: Path | None,
    cluster_context_dir: Path,
) -> dict[str, Any]:
    """Render machine-readable metadata for cluster mode."""

    return {
        "schema_version": "gbs_patch_suggest/meta/v1",
        "mode": "cluster",
        "status": "cluster_context_available",
        "outputs": {
            "readme_md": str(readme_path),
            "context_md": str(context_path),
            "meta_json": str(meta_path),
            "cluster_context_dir": str(cluster_context_dir),
        },
        "inputs": {
            "evidence_json": None if evidence_path is None else str(evidence_path),
            "buildlog": None if buildlog_path is None else str(buildlog_path),
        },
        "clusters": [
            {
                "id": output["cluster"].id,
                "warning_option": output["cluster"].warning_option,
                "diagnostic_kinds": list(output["cluster"].diagnostic_kinds),
                "truncated": output["cluster"].truncated,
                "index_md": str(output["index_path"]),
                "files": [
                    {
                        "file": file_output["context"].file,
                        "status": file_output["context"].status,
                        "location_count": len(file_output["context"].locations),
                        "context_md": str(file_output["path"]),
                        "edit_spec_json": None
                        if file_output["edit_spec_path"] is None
                        else str(file_output["edit_spec_path"]),
                        "source_windows_truncated": file_output[
                            "context"
                        ].source_windows_truncated,
                        "missing_line_text": [
                            {
                                "line": location.line,
                                "column": location.column,
                                "message": location.message,
                            }
                            for location in file_output[
                                "context"
                            ].missing_line_text_locations
                        ],
                    }
                    for file_output in output["file_outputs"]
                ],
            }
            for output in cluster_outputs
        ],
    }


def _cluster_dir_name(cluster: ResolvedCluster) -> str:
    return f"{cluster.id}_{_slug(cluster.warning_option)}"


def _file_context_name(file_context: ClusterFileContext) -> str:
    return f"{file_context.index:03d}_{_file_slug(file_context.file)}.md"


def _write_edit_spec_skeleton(
    cluster: ResolvedCluster,
    file_context: ClusterFileContext,
    *,
    edit_specs_dir: Path,
) -> Path | None:
    if not file_context.skeleton_edits:
        return None
    path = edit_specs_dir / _edit_spec_name(cluster, file_context)
    data = {
        "schema_version": EDIT_SPEC_SCHEMA,
        "patch_name": _patch_name(cluster, file_context),
        "description": "Fill new values for all listed source diagnostics in this file.",
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


def _edit_spec_name(cluster: ResolvedCluster, file_context: ClusterFileContext) -> str:
    return f"edit_spec_{cluster.id}_{file_context.index:03d}_{_file_slug(file_context.file)}.json"


def _patch_name(cluster: ResolvedCluster, file_context: ClusterFileContext) -> str:
    return f"candidate_{cluster.id}_{file_context.index:03d}_{_file_slug(file_context.file)}.patch"


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
