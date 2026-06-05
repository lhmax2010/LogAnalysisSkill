"""Resolve per-file source context for large-scale diagnostic clusters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from gbs_patch_suggest.cluster_ingest import ClusterLocation, LargeScaleCluster
from gbs_patch_suggest.resolver import resolve_candidate_paths

CLUSTER_CONTEXT_WINDOW = 8
MERGE_GAP_LINES = 2
MAX_SOURCE_WINDOW_LINES = 400


@dataclass(frozen=True)
class SourceWindow:
    """Merged source window for one or more cluster locations."""

    start_line: int
    end_line: int
    text: str
    diagnostic_lines: tuple[int, ...]


@dataclass(frozen=True)
class SkeletonEdit:
    """Pre-filled edit-spec skeleton edit for one source line."""

    file: str
    line: int
    old: str
    covered_locations: tuple[ClusterLocation, ...]


@dataclass(frozen=True)
class ClusterFileContext:
    """Resolved context for one file in a repeated diagnostic cluster."""

    index: int
    file: str
    status: str
    level: str
    locations: tuple[ClusterLocation, ...]
    source_path: str | None = None
    source_windows: tuple[SourceWindow, ...] = ()
    source_windows_truncated: bool = False
    advisory: str | None = None
    candidates: tuple[str, ...] = ()
    skeleton_edits: tuple[SkeletonEdit, ...] = ()
    missing_line_text_locations: tuple[ClusterLocation, ...] = ()

    @property
    def has_source_context(self) -> bool:
        return bool(self.source_windows)


@dataclass(frozen=True)
class ResolvedCluster:
    """Resolved per-file context for one large-scale analyzer cluster."""

    id: str
    warning_option: str
    diagnostic_kinds: tuple[str, ...]
    truncated: bool
    file_contexts: tuple[ClusterFileContext, ...]


def resolve_clusters(
    clusters: tuple[LargeScaleCluster, ...],
    *,
    src_root: Path | None,
    window: int = CLUSTER_CONTEXT_WINDOW,
    max_source_lines: int = MAX_SOURCE_WINDOW_LINES,
) -> tuple[ResolvedCluster, ...]:
    """Resolve source windows for all cluster files without failing on misses."""

    return tuple(
        _resolve_cluster(
            cluster,
            src_root=src_root,
            window=window,
            max_source_lines=max_source_lines,
        )
        for cluster in clusters
    )


def _resolve_cluster(
    cluster: LargeScaleCluster,
    *,
    src_root: Path | None,
    window: int,
    max_source_lines: int,
) -> ResolvedCluster:
    grouped = _group_locations_by_file(cluster.locations)
    contexts = tuple(
        _resolve_file_context(
            index,
            file,
            locations,
            src_root=src_root,
            window=window,
            max_source_lines=max_source_lines,
        )
        for index, (file, locations) in enumerate(grouped.items(), start=1)
    )
    return ResolvedCluster(
        id=cluster.id,
        warning_option=cluster.warning_option,
        diagnostic_kinds=cluster.diagnostic_kinds,
        truncated=cluster.truncated,
        file_contexts=contexts,
    )


def _group_locations_by_file(
    locations: tuple[ClusterLocation, ...],
) -> dict[str, tuple[ClusterLocation, ...]]:
    grouped: dict[str, list[ClusterLocation]] = {}
    for location in locations:
        grouped.setdefault(location.file, []).append(location)
    return {file: tuple(file_locations) for file, file_locations in grouped.items()}


def _resolve_file_context(
    index: int,
    file: str,
    locations: tuple[ClusterLocation, ...],
    *,
    src_root: Path | None,
    window: int,
    max_source_lines: int,
) -> ClusterFileContext:
    candidates = resolve_candidate_paths(file, src_root)
    if len(candidates) == 1:
        source_path = candidates[0]
        try:
            lines = source_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            return ClusterFileContext(
                index=index,
                file=file,
                status="source_context_unavailable",
                level="B",
                locations=locations,
                advisory=f"Source file matched but could not be read: {exc}",
            )
        windows, truncated = _source_windows(
            lines,
            locations,
            window=window,
            max_source_lines=max_source_lines,
        )
        skeleton_edits, missing_line_text_locations = _skeleton_edits(
            file,
            lines,
            locations,
        )
        return ClusterFileContext(
            index=index,
            file=file,
            status="source_context_available",
            level="A",
            locations=locations,
            source_path=str(source_path),
            source_windows=windows,
            source_windows_truncated=truncated,
            skeleton_edits=skeleton_edits,
            missing_line_text_locations=missing_line_text_locations,
        )
    if len(candidates) > 1:
        return ClusterFileContext(
            index=index,
            file=file,
            status="source_context_ambiguous",
            level="B",
            locations=locations,
            advisory=(
                f"Multiple source files match `{file}` under the provided source root. "
                "Choose the correct file before preparing edits."
            ),
            candidates=tuple(str(path) for path in candidates[:10]),
        )
    return ClusterFileContext(
        index=index,
        file=file,
        status="source_context_unavailable",
        level="B",
        locations=locations,
        advisory=(
            f"Source context for `{file}` is unavailable. Open this file around the "
            "listed lines before preparing an edit spec."
        ),
    )


def _source_windows(
    lines: list[str],
    locations: tuple[ClusterLocation, ...],
    *,
    window: int,
    max_source_lines: int,
) -> tuple[tuple[SourceWindow, ...], bool]:
    raw = sorted(
        (
            max(1, location.line - window),
            min(len(lines), location.line + window),
            location.line,
        )
        for location in locations
        if 1 <= location.line <= max(len(lines), 1)
    )
    if not raw:
        return (), False

    merged: list[tuple[int, int, list[int]]] = []
    for start, end, diagnostic_line in raw:
        if not merged:
            merged.append((start, end, [diagnostic_line]))
            continue
        previous_start, previous_end, previous_lines = merged[-1]
        gap = start - previous_end - 1
        if gap <= MERGE_GAP_LINES:
            previous_lines.append(diagnostic_line)
            merged[-1] = (
                previous_start,
                max(previous_end, end),
                previous_lines,
            )
        else:
            merged.append((start, end, [diagnostic_line]))

    windows: list[SourceWindow] = []
    used_lines = 0
    truncated = False
    for start, end, diagnostic_lines in merged:
        line_count = end - start + 1
        if used_lines + line_count > max_source_lines:
            remaining = max_source_lines - used_lines
            if remaining <= 0:
                truncated = True
                break
            end = start + remaining - 1
            truncated = True
        windows.append(
            SourceWindow(
                start_line=start,
                end_line=end,
                text="\n".join(lines[start - 1 : end]),
                diagnostic_lines=tuple(sorted(set(diagnostic_lines))),
            )
        )
        used_lines += end - start + 1
        if truncated:
            break
    return tuple(windows), truncated


def _skeleton_edits(
    file: str,
    lines: list[str],
    locations: tuple[ClusterLocation, ...],
) -> tuple[tuple[SkeletonEdit, ...], tuple[ClusterLocation, ...]]:
    grouped: dict[int, list[ClusterLocation]] = {}
    missing: list[ClusterLocation] = []
    for location in locations:
        if 1 <= location.line <= len(lines):
            grouped.setdefault(location.line, []).append(location)
        else:
            missing.append(location)

    edits = tuple(
        SkeletonEdit(
            file=file,
            line=line,
            old=lines[line - 1],
            covered_locations=tuple(line_locations),
        )
        for line, line_locations in sorted(grouped.items())
    )
    return edits, tuple(missing)
