"""Observation-only coverage report for source candidate sidecars."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gbs_analyzer.error_clusters import extract_warning_option
from gbs_analyzer.scan_and_extract import ScanResult

OBSERVATION_SCHEMA = "source_candidate_observation/v1"
SOURCE_DIAGNOSTIC_KINDS = {"compiler", "werror"}
MESSAGE_FINGERPRINT_LEN = 12
RAW_DIAGNOSTIC_PATTERN = re.compile(
    r"(?P<file>(?:/[^:\n]+|[A-Za-z0-9_./+-][^:\n]*?)):"
    r"(?P<line>\d+):"
    r"(?:(?P<column>\d+):)?\s*"
    r"(?P<level>fatal error|error|warning):\s*"
    r"(?P<message>.*)"
)
WARNING_BLOCK_PATTERN = re.compile(r"\[([^\]]+)\]")
TRUNCATION_MARKER = "too many errors emitted"


@dataclass(frozen=True)
class _CoverageItem:
    identity: str
    diagnostic: dict[str, Any]
    source: str


def build_source_candidate_observation(
    *,
    packet: dict[str, Any],
    scan_result: ScanResult | dict[str, Any],
    buildlog_path: Path,
    source_candidate_sidecar: dict[str, Any] | None,
    error_cluster_sidecar: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return an observation report without changing analyzer or patch outputs."""

    scan_data = _scan_as_dict(scan_result)
    main_candidates = _source_candidates(source_candidate_sidecar)
    excluded = _excluded_source_diagnostics(source_candidate_sidecar)
    sidecar_items = [
        _coverage_item(candidate, source="source_candidates")
        for candidate in main_candidates
    ]
    sidecar_by_identity = {item.identity: item for item in sidecar_items}
    excluded_by_identity = {
        _identity(excluded_item): excluded_item
        for excluded_item in excluded
        if _identity(excluded_item) is not None
    }
    scan_events_by_identity = {
        _identity(event): event
        for event in _events(scan_data)
        if _identity(event) is not None
    }

    old_coverage, old_decision = _old_path_coverage(
        packet=packet,
        error_cluster_sidecar=error_cluster_sidecar,
    )
    old_by_identity = {item.identity: item for item in old_coverage}

    missed = [
        item
        for item in sidecar_items
        if item.identity not in old_by_identity
    ]
    extra = [
        _extra_item(
            item,
            excluded_by_identity.get(item.identity),
            scan_events_by_identity.get(item.identity),
        )
        for item in old_coverage
        if item.identity not in sidecar_by_identity
    ]

    scanner_gap = _scanner_coverage_gap(
        buildlog_path=buildlog_path,
        scan_data=scan_data,
    )
    type_source_stats = _type_source_stats(main_candidates)

    return {
        "schema_version": OBSERVATION_SCHEMA,
        "scope": (
            "Observation-only report. It does not alter Evidence Packet ranking, "
            "patch-suggest output, or source_candidate sidecar contents."
        ),
        "coverage_diff": {
            "sidecar_diagnostics": [_summarize(item.diagnostic) for item in sidecar_items],
            "old_path_covered": [_summarize(item.diagnostic) for item in old_coverage],
            "missed_by_old": [_summarize(item.diagnostic) for item in missed],
            "extra_by_old": extra,
            "counts": {
                "sidecar_diagnostics": len(sidecar_items),
                "old_path_covered": len(old_coverage),
                "missed_by_old": len(missed),
                "extra_by_old": len(extra),
            },
            "old_path_decision": old_decision,
        },
        "scanner_coverage_gap": scanner_gap,
        "type_source_stats": type_source_stats,
    }


def _old_path_coverage(
    *,
    packet: dict[str, Any],
    error_cluster_sidecar: dict[str, Any] | None,
) -> tuple[list[_CoverageItem], dict[str, Any]]:
    fallback_reasons: dict[str, str] = {}
    sidecar_readable: bool | None = None

    cluster_items, cluster_reason, sidecar_readable = _cluster_old_coverage(
        packet,
        error_cluster_sidecar,
    )
    if cluster_items is not None:
        return cluster_items, {
            "selected_branch": "cluster",
            "fallback_reasons": fallback_reasons,
            "sidecar_readable": sidecar_readable,
        }
    fallback_reasons["cluster"] = cluster_reason

    multi_items, multi_reason = _multi_old_coverage(packet)
    if multi_items is not None:
        return multi_items, {
            "selected_branch": "multi",
            "fallback_reasons": fallback_reasons,
            "sidecar_readable": sidecar_readable,
        }
    fallback_reasons["multi"] = multi_reason

    single_items, single_reason = _single_old_coverage(packet)
    if single_items is not None:
        return single_items, {
            "selected_branch": "single",
            "fallback_reasons": fallback_reasons,
            "sidecar_readable": sidecar_readable,
        }
    fallback_reasons["single"] = single_reason
    return [], {
        "selected_branch": "none",
        "fallback_reasons": fallback_reasons,
        "sidecar_readable": sidecar_readable,
    }


def _cluster_old_coverage(
    packet: dict[str, Any],
    error_cluster_sidecar: dict[str, Any] | None,
) -> tuple[list[_CoverageItem] | None, str, bool | None]:
    summary = packet.get("error_clusters")
    if not isinstance(summary, dict):
        return None, "no_error_clusters", None
    clusters = [cluster for cluster in summary.get("clusters", []) if isinstance(cluster, dict)]
    if not clusters:
        return None, "no_clusters", None
    selected = [cluster for cluster in clusters if _is_large_scale_source_cluster(cluster)]
    if not selected:
        if any(cluster.get("large_scale") is False for cluster in clusters):
            return None, "large_scale_false", None
        return None, "no_large_scale_source_cluster", None
    if (
        not isinstance(error_cluster_sidecar, dict)
        or error_cluster_sidecar.get("schema_version") != "error_clusters_locations/v1"
    ):
        return None, "sidecar_unreadable", False
    sidecar_by_id = {
        str(cluster.get("id")): cluster
        for cluster in error_cluster_sidecar.get("clusters", [])
        if isinstance(cluster, dict) and cluster.get("id") is not None
    }
    items: list[_CoverageItem] = []
    for summary_cluster in selected:
        cluster_id = str(summary_cluster.get("id"))
        warning_option = str(summary_cluster.get("warning_option") or "")
        sidecar_cluster = sidecar_by_id.get(cluster_id)
        if not isinstance(sidecar_cluster, dict):
            continue
        for raw_location in sidecar_cluster.get("locations", []):
            if not isinstance(raw_location, dict):
                continue
            file_value = raw_location.get("file")
            line_value = raw_location.get("line")
            if not isinstance(file_value, str) or not isinstance(line_value, int):
                continue
            location = dict(raw_location)
            location.setdefault("warning_option", warning_option)
            location.setdefault("source_cluster_id", cluster_id)
            item = _coverage_item(location, source="old_cluster")
            items.append(item)
    if not items:
        return None, "sidecar_no_usable_locations", True
    return items, "", True


def _multi_old_coverage(packet: dict[str, Any]) -> tuple[list[_CoverageItem] | None, str]:
    raw_candidates = packet.get("root_cause_candidates")
    if not isinstance(raw_candidates, list):
        return None, "no_root_cause_candidates"
    eligible = [
        candidate
        for candidate in raw_candidates
        if isinstance(candidate, dict) and _is_multi_eligible(candidate)
    ]
    if len(eligible) < 2:
        return None, "candidates_lt_2"
    return [
        _coverage_item(candidate, source="old_multi")
        for candidate in eligible
    ], ""


def _single_old_coverage(packet: dict[str, Any]) -> tuple[list[_CoverageItem] | None, str]:
    primary = packet.get("primary_error")
    if not isinstance(primary, dict) or not primary:
        return None, "no_primary_error"
    return [_coverage_item(primary, source="old_single")], ""


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


def _is_multi_eligible(candidate: dict[str, Any]) -> bool:
    if candidate.get("is_terminal") is not True:
        return False
    if candidate.get("kind") not in SOURCE_DIAGNOSTIC_KINDS:
        return False
    if not isinstance(candidate.get("file"), str) or not candidate.get("file"):
        return False
    line_value = candidate.get("line")
    if not isinstance(line_value, int) or line_value <= 0:
        return False
    return isinstance(candidate.get("message"), str) and bool(candidate.get("message"))


def _coverage_item(diagnostic: dict[str, Any], *, source: str) -> _CoverageItem:
    identity = _identity(diagnostic)
    if identity is None:
        identity = f"fallback:{_fallback_identity(diagnostic)}"
    data = dict(diagnostic)
    data["coverage_source"] = source
    data["identity"] = identity
    return _CoverageItem(identity=identity, diagnostic=data, source=source)


def _identity(diagnostic: dict[str, Any]) -> str | None:
    event_id = diagnostic.get("event_id") or diagnostic.get("id")
    if isinstance(event_id, str) and event_id:
        return f"event_id:{event_id}"
    dedupe_key = diagnostic.get("dedupe_key")
    if isinstance(dedupe_key, str) and dedupe_key:
        return f"dedupe:{dedupe_key}"
    return None


def _fallback_identity(diagnostic: dict[str, Any]) -> str:
    warning_option = diagnostic.get("warning_option")
    if not isinstance(warning_option, str) or not warning_option:
        warning_option = extract_warning_option(diagnostic) or "<none>"
    parts = [
        f"file={diagnostic.get('normalized_file') or diagnostic.get('file') or '<unknown>'}",
        (
            f"line={diagnostic.get('line')}"
            if isinstance(diagnostic.get("line"), int)
            else "line=<unknown>"
        ),
        (
            f"column={diagnostic.get('column')}"
            if isinstance(diagnostic.get("column"), int)
            else "column=<unknown>"
        ),
        f"warning_option={warning_option}",
        f"semantic_class={diagnostic.get('semantic_class') or '<unknown>'}",
        f"message={_message_fingerprint(str(diagnostic.get('message') or ''))}",
        f"command_id={diagnostic.get('command_id') or '<unknown>'}",
        f"kind={diagnostic.get('kind') or '<unknown>'}",
    ]
    return "|".join(parts)


def _extra_item(
    item: _CoverageItem,
    excluded: dict[str, Any] | None,
    scan_event: dict[str, Any] | None,
) -> dict[str, Any]:
    data = {
        "diagnostic": _summarize(item.diagnostic),
        "new_sidecar_location": "not_present",
        "exclusion_reason": None,
    }
    if excluded is not None:
        data["new_sidecar_location"] = "excluded_source_diagnostics"
        data["exclusion_reason"] = excluded.get("exclusion_reason")
        data["excluded_diagnostic"] = _summarize(excluded)
    elif scan_event is not None:
        data["new_sidecar_location"] = "not_source_candidate_eligible"
        data["exclusion_reason"] = _source_candidate_gate_exclusion_reason(scan_event)
        data["scan_event"] = _summarize(scan_event)
    return data


def _source_candidate_gate_exclusion_reason(event: dict[str, Any]) -> str:
    if event.get("kind") not in SOURCE_DIAGNOSTIC_KINDS:
        return "non_source_kind"
    if not isinstance(event.get("file"), str) or not event.get("file"):
        return "missing_file"
    line_value = event.get("line")
    if not isinstance(line_value, int) or line_value <= 0:
        return "missing_line"
    if event.get("parent") is not None:
        return "explicit_parent"
    if not _is_structured_source_diagnostic(event):
        return "not_fatal_or_werror"
    return "not_present_in_source_candidate_sidecar"


def _scanner_coverage_gap(
    *,
    buildlog_path: Path,
    scan_data: dict[str, Any],
) -> dict[str, Any]:
    raw = _raw_source_diagnostics(buildlog_path)
    structured = [
        event
        for event in _events(scan_data)
        if _is_structured_source_diagnostic(event)
    ]
    structured_keys = {_raw_match_key(event) for event in structured}
    unmatched = [
        item
        for item in raw
        if _raw_match_key(item) not in structured_keys
    ]
    return {
        "scope": (
            "Heuristic observation only. Raw diagnostic-like lines are not converted "
            "into source_candidates."
        ),
        "raw_diagnostic_like_line_count": len(raw),
        "structured_event_count": len(structured),
        "unmatched_diagnostic_like_line_count": len(unmatched),
        "unmatched_diagnostic_like_line_samples": [
            _summarize(item) for item in unmatched[:10]
        ],
        "unmatched_categories": _unmatched_categories(unmatched),
    }


def _raw_source_diagnostics(buildlog_path: Path) -> list[dict[str, Any]]:
    try:
        lines = buildlog_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    diagnostics: list[dict[str, Any]] = []
    for line_no, line in enumerate(lines, start=1):
        match = RAW_DIAGNOSTIC_PATTERN.search(_strip_gbs_prefix(line))
        if match is None:
            continue
        level = match.group("level").lower()
        message = match.group("message").strip()
        if level == "warning" and "-Werror" not in message:
            continue
        diagnostics.append(
            {
                "line_no": line_no,
                "file": match.group("file"),
                "line": int(match.group("line")),
                "column": _optional_int(match.group("column")),
                "severity": "error" if level in {"error", "fatal error"} else "warning",
                "message": message,
                "warning_option": _warning_option_from_message(message),
            }
        )
    return diagnostics


def _strip_gbs_prefix(line: str) -> str:
    return re.sub(r"^\[\s*\d+s\]\s*", "", line)


def _is_structured_source_diagnostic(event: dict[str, Any]) -> bool:
    if event.get("kind") not in SOURCE_DIAGNOSTIC_KINDS:
        return False
    if not isinstance(event.get("file"), str) or not isinstance(event.get("line"), int):
        return False
    if str(event.get("severity") or "").lower() == "error":
        return True
    if event.get("kind") == "werror":
        return True
    return "-Werror" in str(event.get("message") or "")


def _raw_match_key(diagnostic: dict[str, Any]) -> tuple[Any, ...]:
    return (
        diagnostic.get("file"),
        diagnostic.get("line"),
        diagnostic.get("column"),
        diagnostic.get("warning_option") or _warning_option_from_message(
            str(diagnostic.get("message") or "")
        ),
    )


def _warning_option_from_message(message: str) -> str | None:
    for block in WARNING_BLOCK_PATTERN.findall(message):
        for raw_token in block.split(","):
            token = raw_token.strip()
            if token.startswith("-W") and token != "-Werror":
                return str(token)
    return None


def _unmatched_categories(unmatched: list[dict[str, Any]]) -> dict[str, int]:
    categories = {
        "werror_promoted": 0,
        "source_error": 0,
        "truncation_signal": 0,
    }
    for item in unmatched:
        message = str(item.get("message") or "")
        if "-Werror" in message:
            categories["werror_promoted"] += 1
        else:
            categories["source_error"] += 1
        if TRUNCATION_MARKER in message.lower():
            categories["truncation_signal"] += 1
    return {key: value for key, value in categories.items() if value}


def _type_source_stats(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    type_unknown_by_reason: dict[str, int] = {}
    source_unreachable_by_status: dict[str, int] = {}
    source_not_owned_by_status: dict[str, int] = {}
    for candidate in candidates:
        if candidate.get("type_fixability") == "unknown":
            _increment(type_unknown_by_reason, candidate.get("type_fixability_reason"))
        if candidate.get("source_reachable") is not True:
            _increment(source_unreachable_by_status, candidate.get("source_resolution_status"))
        if candidate.get("source_owned") is not True:
            _increment(source_not_owned_by_status, candidate.get("source_ownership_status"))
    return {
        "type_unknown_by_reason": type_unknown_by_reason,
        "source_unreachable_by_status": source_unreachable_by_status,
        "source_not_owned_by_status": source_not_owned_by_status,
    }


def _increment(counter: dict[str, int], key: object) -> None:
    label = str(key) if key else "<unknown>"
    counter[label] = counter.get(label, 0) + 1


def _source_candidates(sidecar: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(sidecar, dict):
        return []
    candidates = sidecar.get("candidates")
    if not isinstance(candidates, list):
        return []
    return [candidate for candidate in candidates if isinstance(candidate, dict)]


def _excluded_source_diagnostics(sidecar: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(sidecar, dict):
        return []
    diagnostics = sidecar.get("excluded_source_diagnostics")
    if not isinstance(diagnostics, list):
        return []
    return [diagnostic for diagnostic in diagnostics if isinstance(diagnostic, dict)]


def _summarize(diagnostic: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "identity",
        "event_id",
        "id",
        "kind",
        "file",
        "normalized_file",
        "line",
        "column",
        "warning_option",
        "semantic_class",
        "type_fixability",
        "source_reachable",
        "source_resolution_status",
        "source_owned",
        "source_ownership_status",
        "exclusion_reason",
        "coverage_source",
    )
    summary = {
        key: diagnostic[key]
        for key in keys
        if key in diagnostic and diagnostic[key] is not None
    }
    message = diagnostic.get("message")
    if isinstance(message, str) and message:
        summary["message"] = _truncate(message)
    return summary


def _truncate(text: str, *, limit: int = 240) -> str:
    return text if len(text) <= limit else text[: limit - 15].rstrip() + "... [truncated]"


def _message_fingerprint(message: str) -> str:
    normalized = re.sub(r"\s+", " ", message.strip().lower())
    return hashlib.sha1(normalized.encode("utf-8", errors="replace")).hexdigest()[
        :MESSAGE_FINGERPRINT_LEN
    ]


def _optional_int(value: str | None) -> int | None:
    return int(value) if value is not None else None


def _events(scan_data: dict[str, Any]) -> list[dict[str, Any]]:
    return [event for event in scan_data.get("events", []) if isinstance(event, dict)]


def _scan_as_dict(scan_result: ScanResult | dict[str, Any]) -> dict[str, Any]:
    if isinstance(scan_result, ScanResult):
        return scan_result.as_dict()
    return scan_result
