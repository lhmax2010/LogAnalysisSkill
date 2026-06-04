"""Build compact summaries for repeated source diagnostic clusters."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from gbs_analyzer.scan_and_extract import ScanResult

ERROR_CLUSTERS_SCHEMA = "error_clusters/v1"
ERROR_CLUSTER_LOCATIONS_SCHEMA = "error_clusters_locations/v1"
SIDECAR_NAME = "error_clusters.json"
TRUNCATION_MARKER = "too many errors emitted"
_WARNING_BLOCK_PATTERN = re.compile(r"\[([^\]]+)\]")
_SOURCE_DIAGNOSTIC_KINDS = {"compiler", "werror"}


@dataclass(frozen=True)
class ErrorClusterResult:
    """Packet summary and optional sidecar payload for repeated diagnostics."""

    summary: dict[str, Any] | None
    sidecar: dict[str, Any] | None


def build_error_clusters(scan_result: ScanResult | dict[str, Any]) -> ErrorClusterResult:
    """Return additive error cluster metadata for an analyzer scan result."""

    scan_data = _scan_as_dict(scan_result)
    events = [event for event in scan_data.get("events", []) if isinstance(event, dict)]
    truncation_signals = _truncation_signals(events)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        warning_option = extract_warning_option(event)
        if warning_option is None:
            continue
        grouped.setdefault(warning_option, []).append(event)

    clusters: list[dict[str, Any]] = []
    sidecar_clusters: list[dict[str, Any]] = []
    for warning_option, cluster_events in grouped.items():
        if len(cluster_events) < 3:
            continue
        cluster_id = f"CL{len(clusters) + 1:03d}"
        cluster = _cluster_summary(
            cluster_id,
            warning_option,
            cluster_events,
            truncated=bool(truncation_signals),
        )
        clusters.append(cluster)
        sidecar_clusters.append(
            {
                "id": cluster_id,
                "warning_option": warning_option,
                "locations": [_sidecar_location(event) for event in cluster_events],
            }
        )

    if not clusters and not truncation_signals:
        return ErrorClusterResult(summary=None, sidecar=None)

    summary = {
        "schema_version": ERROR_CLUSTERS_SCHEMA,
        "truncated": bool(truncation_signals),
        "truncation_signals": truncation_signals,
        "full_locations_path": SIDECAR_NAME if clusters else None,
        "clusters": clusters,
    }
    sidecar = (
        {
            "schema_version": ERROR_CLUSTER_LOCATIONS_SCHEMA,
            "clusters": sidecar_clusters,
        }
        if clusters
        else None
    )
    return ErrorClusterResult(summary=summary, sidecar=sidecar)


def extract_warning_option(event: dict[str, Any]) -> str | None:
    """Return the concrete warning option key for a source diagnostic event."""

    if event.get("kind") not in _SOURCE_DIAGNOSTIC_KINDS:
        return None
    message = str(event.get("message") or "")
    for block in _WARNING_BLOCK_PATTERN.findall(message):
        for raw_token in block.split(","):
            token: str = raw_token.strip()
            if not token.startswith("-W"):
                continue
            if token == "-Werror":
                continue
            return token
    return None


def _cluster_summary(
    cluster_id: str,
    warning_option: str,
    events: list[dict[str, Any]],
    *,
    truncated: bool,
) -> dict[str, Any]:
    files = _ordered_files(events)
    sample = _locations_sample(events)
    large_scale = len(events) >= 10 or len(files) >= 3
    return {
        "id": cluster_id,
        "kind": "source_warning_option",
        "diagnostic_kinds": sorted({str(event.get("kind")) for event in events}),
        "warning_option": warning_option,
        "count": len(events),
        "file_count": len(files),
        "files": files[:20],
        "locations_sample": [_packet_location(event) for event in sample],
        "locations_truncated": len(events) > len(sample),
        "advisory": _advisory(large_scale=large_scale, truncated=truncated),
        "large_scale": large_scale,
    }


def _ordered_files(events: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    files: list[str] = []
    for event in events:
        file = event.get("file")
        if not isinstance(file, str) or not file or file in seen:
            continue
        seen.add(file)
        files.append(file)
    return files


def _locations_sample(events: list[dict[str, Any]], *, limit: int = 10) -> list[dict[str, Any]]:
    selected_indices: list[int] = []
    selected_set: set[int] = set()
    seen_files: set[str] = set()
    for index, event in enumerate(events):
        file = event.get("file")
        if not isinstance(file, str) or not file or file in seen_files:
            continue
        selected_indices.append(index)
        selected_set.add(index)
        seen_files.add(file)
        if len(selected_indices) >= limit:
            break
    if len(selected_indices) < limit:
        for index, _event in enumerate(events):
            if index in selected_set:
                continue
            selected_indices.append(index)
            if len(selected_indices) >= limit:
                break
    return [events[index] for index in selected_indices]


def _packet_location(event: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = {
        "event_id": event.get("id"),
        "file": event.get("file"),
        "line": event.get("line"),
        "column": event.get("column"),
    }
    return {key: value for key, value in data.items() if value is not None}


def _sidecar_location(event: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = {
        "event_id": event.get("id"),
        "kind": event.get("kind"),
        "file": event.get("file"),
        "line": event.get("line"),
        "column": event.get("column"),
        "line_no": event.get("line_no"),
        "message": event.get("message"),
    }
    return {key: value for key, value in data.items() if value is not None}


def _truncation_signals(events: list[dict[str, Any]], *, limit: int = 5) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for event in events:
        message = str(event.get("message") or "")
        if TRUNCATION_MARKER not in message.lower():
            continue
        signals.append(
            {
                "line_no": event.get("line_no"),
                "message": message,
            }
        )
        if len(signals) >= limit:
            break
    return signals


def _advisory(*, large_scale: bool, truncated: bool) -> str:
    if large_scale:
        advisory = (
            "Large repeated source diagnostic cluster. Patching only the primary error "
            "is likely incomplete; consider a class-wide fix strategy."
        )
    else:
        advisory = (
            "Repeated source diagnostic cluster. Review all listed locations before "
            "assuming a one-off patch is complete."
        )
    if truncated:
        advisory += " Compiler output was truncated; actual occurrences may be higher."
    return advisory


def _scan_as_dict(scan_result: ScanResult | dict[str, Any]) -> dict[str, Any]:
    if isinstance(scan_result, ScanResult):
        return scan_result.as_dict()
    return scan_result
