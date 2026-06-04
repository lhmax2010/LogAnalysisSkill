"""Ingest analyzer large-scale error cluster sidecars."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SOURCE_DIAGNOSTIC_KINDS = frozenset({"compiler", "werror"})
ERROR_CLUSTER_LOCATIONS_SCHEMA = "error_clusters_locations/v1"


@dataclass(frozen=True)
class ClusterLocation:
    """One source diagnostic location from analyzer error_clusters sidecar."""

    event_id: str | None
    kind: str | None
    file: str
    line: int
    column: int | None
    line_no: int | None
    message: str


@dataclass(frozen=True)
class LargeScaleCluster:
    """Large-scale source diagnostic cluster selected for per-file context."""

    id: str
    warning_option: str
    diagnostic_kinds: tuple[str, ...]
    truncated: bool
    locations: tuple[ClusterLocation, ...]


@dataclass(frozen=True)
class ClusterIngestResult:
    """Selected large-scale clusters or advisory describing fallback."""

    clusters: tuple[LargeScaleCluster, ...] = ()
    advisory: str | None = None

    @property
    def has_clusters(self) -> bool:
        return bool(self.clusters)


def ingest_large_scale_clusters(
    packet: dict[str, Any],
    *,
    evidence_path: Path,
) -> ClusterIngestResult:
    """Return large-scale source diagnostic clusters exposed by analyzer evidence."""

    summary = packet.get("error_clusters")
    if not isinstance(summary, dict):
        return ClusterIngestResult()

    selected_summaries = [
        cluster
        for cluster in _cluster_summaries(summary)
        if _is_large_scale_source_cluster(cluster)
    ]
    if not selected_summaries:
        return ClusterIngestResult()

    sidecar_ref = summary.get("full_locations_path")
    if not isinstance(sidecar_ref, str) or not sidecar_ref:
        return ClusterIngestResult(advisory="cluster_sidecar_unavailable: missing path")

    sidecar_path = evidence_path.parent / sidecar_ref
    try:
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return ClusterIngestResult(advisory=f"cluster_sidecar_unavailable: {exc}")

    if (
        not isinstance(sidecar, dict)
        or sidecar.get("schema_version") != ERROR_CLUSTER_LOCATIONS_SCHEMA
    ):
        return ClusterIngestResult(advisory="cluster_sidecar_unavailable: schema mismatch")

    sidecar_by_id = {
        str(cluster.get("id")): cluster
        for cluster in sidecar.get("clusters", [])
        if isinstance(cluster, dict) and cluster.get("id") is not None
    }
    clusters: list[LargeScaleCluster] = []
    for summary_cluster in selected_summaries:
        cluster_id = str(summary_cluster.get("id"))
        sidecar_cluster = sidecar_by_id.get(cluster_id)
        if not isinstance(sidecar_cluster, dict):
            continue
        locations = tuple(_parse_locations(sidecar_cluster.get("locations", [])))
        if not locations:
            continue
        clusters.append(
            LargeScaleCluster(
                id=cluster_id,
                warning_option=str(summary_cluster.get("warning_option") or ""),
                diagnostic_kinds=tuple(
                    str(kind)
                    for kind in summary_cluster.get("diagnostic_kinds", [])
                    if isinstance(kind, str)
                ),
                truncated=bool(summary.get("truncated")),
                locations=locations,
            )
        )

    if not clusters:
        return ClusterIngestResult(advisory="cluster_sidecar_unavailable: no usable locations")
    return ClusterIngestResult(clusters=tuple(clusters))


def _cluster_summaries(summary: dict[str, Any]) -> list[dict[str, Any]]:
    clusters = summary.get("clusters")
    if not isinstance(clusters, list):
        return []
    return [cluster for cluster in clusters if isinstance(cluster, dict)]


def _is_large_scale_source_cluster(cluster: dict[str, Any]) -> bool:
    if not cluster.get("large_scale"):
        return False
    if cluster.get("kind") != "source_warning_option":
        return False
    diagnostic_kinds = cluster.get("diagnostic_kinds")
    if not isinstance(diagnostic_kinds, list) or not diagnostic_kinds:
        return False
    kinds = {kind for kind in diagnostic_kinds if isinstance(kind, str)}
    return bool(kinds) and kinds.issubset(SOURCE_DIAGNOSTIC_KINDS)


def _parse_locations(raw_locations: object) -> list[ClusterLocation]:
    if not isinstance(raw_locations, list):
        return []
    locations: list[ClusterLocation] = []
    for raw in raw_locations:
        if not isinstance(raw, dict):
            continue
        file = raw.get("file")
        line = raw.get("line")
        if not isinstance(file, str) or not file or not isinstance(line, int) or line <= 0:
            continue
        locations.append(
            ClusterLocation(
                event_id=_optional_str(raw.get("event_id")),
                kind=_optional_str(raw.get("kind")),
                file=file,
                line=line,
                column=raw.get("column") if isinstance(raw.get("column"), int) else None,
                line_no=raw.get("line_no") if isinstance(raw.get("line_no"), int) else None,
                message=str(raw.get("message") or ""),
            )
        )
    return locations


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
