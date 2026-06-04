"""Render large-scale cluster patch context outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from gbs_patch_suggest.cluster_resolver import ClusterFileContext, ResolvedCluster
from gbs_patch_suggest.render import MANDATORY_INSTRUCTIONS


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
        files_dir.mkdir(parents=True, exist_ok=True)
        file_outputs = []
        for file_context in cluster.file_contexts:
            file_path = files_dir / _file_context_name(file_context)
            file_path.write_text(
                render_file_context(cluster, file_context),
                encoding="utf-8",
            )
            file_outputs.append({"context": file_context, "path": file_path})
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


def render_file_context(cluster: ResolvedCluster, file_context: ClusterFileContext) -> str:
    """Render one per-file context."""

    file_slug = _slug(file_context.file)
    edit_spec_name = f"edit_spec_{cluster.id}_{file_context.index:03d}_{file_slug}.json"
    patch_name = f"candidate_{cluster.id}_{file_context.index:03d}_{file_slug}.patch"
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

    lines.extend(
        [
            "## How to generate the patch for this file",
            "",
            "1. Work only on this file context before moving to the next file.",
            "2. Decide the class-wide edit strategy for this file.",
            "3. Write one edit spec containing edits for every listed location in this file "
            "that should be changed.",
            "4. Use `line`, `before`, or `after` to disambiguate repeated old text.",
            "5. Run the deterministic formatter; do not hand-write unified diff text.",
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
            f"    --edit-spec .gbs_patch_suggest/{edit_spec_name} \\",
            f"    --output .gbs_patch_suggest/{patch_name} \\",
            "    --check",
            "```",
            "",
            "If source context is unavailable or ambiguous, first open the correct file around "
            "the listed lines. Do not guess, and do not generate a patch until the source "
            "has been inspected.",
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
                        "source_windows_truncated": file_output[
                            "context"
                        ].source_windows_truncated,
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
    return f"{file_context.index:03d}_{_slug(file_context.file)}.md"


def _slug(value: str, *, max_length: int = 80) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip("/"))
    slug = slug.strip("_") or "item"
    return slug[:max_length].rstrip("_") or "item"


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
