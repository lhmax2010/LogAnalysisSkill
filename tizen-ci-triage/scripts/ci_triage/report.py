"""Markdown report rendering for a single QuickBuild triage run."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tizen_ci_shared.types import FailedPackage, SourceFetchResult


@dataclass
class TriageReportData:
    """Report data accumulated during triage."""

    build_id: str
    quickbuild_log_url: str
    full_log_path: Path | None = None
    analyzed_buildlog_path: Path | None = None
    package_buildlog_url: str | None = None
    selected_package: FailedPackage | None = None
    project_key: str | None = None
    commit_hash: str | None = None
    source_fetch: SourceFetchResult | None = None
    analyzer_output_dir: Path | None = None
    evidence_packet_path: Path | None = None
    patch_context_dir: Path | None = None
    patch_context_meta_path: Path | None = None
    patch_context_status: str | None = None
    primary_error: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def render_report(data: TriageReportData) -> str:
    """Render a human-readable single-build report."""

    lines = [
        f"# CI Triage Report: QuickBuild {data.build_id}",
        "",
        "## QuickBuild",
        f"- Build id: `{data.build_id}`",
        f"- Log page: {data.quickbuild_log_url}",
    ]
    if data.full_log_path is not None:
        lines.append(f"- Full log: `{data.full_log_path}`")
    if data.analyzed_buildlog_path is not None:
        lines.append(f"- Analyzer input: `{data.analyzed_buildlog_path}`")
    if data.package_buildlog_url is not None:
        lines.append(f"- Package buildlog URL: {data.package_buildlog_url}")

    lines.extend(["", "## Failed Package"])
    if data.selected_package is None:
        lines.append("- Selected package: n/a")
    else:
        lines.extend(
            [
                f"- spec_name: `{data.selected_package.spec_name}`",
                f"- fail_pkg: `{data.selected_package.fail_pkg}`",
            ]
        )
        if data.selected_package.dest_file:
            lines.append(f"- buildlog path: `{data.selected_package.dest_file}`")
    if data.project_key is not None:
        lines.append(f"- Gerrit project: `{data.project_key}`")
    if data.commit_hash is not None:
        lines.append(f"- Commit: `{data.commit_hash}`")

    lines.extend(["", "## Gerrit Source"])
    if data.source_fetch is None:
        lines.append("- Source checkout: not attempted")
    else:
        source = data.source_fetch
        lines.append(f"- Status: `{source.status}`")
        lines.append(f"- Remote: `{source.remote_url}`")
        lines.append(f"- Source root: `{source.src_root}`")
        if source.change is not None:
            change = source.change
            lines.append(f"- Change status: `{change.status}`")
            lines.append(f"- Branch: `{change.branch}`")
            if change.number is not None:
                lines.append(f"- Change: `{change.number}`")
            if change.matching_patchset is not None:
                lines.append(f"- Patch set ref: `{change.matching_patchset.ref}`")
        if source.error:
            lines.append(f"- Error: {source.error}")

    lines.extend(["", "## Analyzer"])
    if data.evidence_packet_path is not None:
        lines.append(f"- Evidence packet: `{data.evidence_packet_path}`")
    if data.analyzer_output_dir is not None:
        lines.append(f"- Analyzer output: `{data.analyzer_output_dir}`")
    if data.primary_error:
        lines.append(f"- Primary kind: `{data.primary_error.get('kind', 'unknown')}`")
        location = _primary_location(data.primary_error)
        lines.append(f"- Primary location: `{location}`")
        lines.append(f"- Message: {data.primary_error.get('message', 'n/a')}")

    lines.extend(["", "## Patch Suggest"])
    if data.patch_context_dir is not None:
        lines.append(f"- Patch context: `{data.patch_context_dir}`")
    if data.patch_context_status is not None:
        lines.append(f"- Status: `{data.patch_context_status}`")
    if data.patch_context_meta_path is not None:
        lines.append(f"- Meta: `{data.patch_context_meta_path}`")
    lines.append("- Gerrit duplicate lookup: not implemented in this MVP")

    if data.warnings:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- {warning}" for warning in data.warnings)
    if data.errors:
        lines.extend(["", "## Errors"])
        lines.extend(f"- {error}" for error in data.errors)
    return "\n".join(lines) + "\n"


def _primary_location(error: dict[str, Any]) -> str:
    file_value = error.get("file")
    line = error.get("line")
    if isinstance(file_value, str) and line is not None:
        return f"{file_value}:{line}"
    if isinstance(file_value, str):
        return file_value
    return "n/a"
