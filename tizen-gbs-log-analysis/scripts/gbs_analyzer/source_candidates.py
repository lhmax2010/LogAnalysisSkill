"""Build additive source diagnostic candidate sidecars."""

from __future__ import annotations

import hashlib
import posixpath
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gbs_analyzer._utils.semantic_classifier import SemanticClassifier
from gbs_analyzer.error_clusters import extract_warning_option
from gbs_analyzer.scan_and_extract import ScanResult

SOURCE_CANDIDATES_SCHEMA = "source_candidates/v1"
SOURCE_CANDIDATES_SIDECAR_SCHEMA = "source_candidate_sidecar/v1"
SIDECAR_NAME = "source_candidates.json"
SOURCE_DIAGNOSTIC_KINDS = {"compiler", "werror"}
PROBABLY_FIXABLE_WARNING_OPTIONS = {
    "-Wdeprecated-declarations",
    "-Wimplicit-enum-enum-cast",
    "-Wpointer-bool-conversion",
    "-Winconsistent-missing-override",
    "-Wunused-private-field",
    "-Wunused-field",
}
SYSTEM_PREFIXES = (
    "/usr/include",
    "/usr/lib",
    "/opt/toolchain",
)
SUSPECT_PATH_PARTS = {
    "generated",
    "gen",
    "third_party",
    "external",
    "vendor",
}
SKIPPED_DIR_NAMES = {
    ".git",
    ".gbs_patch_suggest",
    ".gbs_workflow",
    "build",
    "node_modules",
}
MESSAGE_FINGERPRINT_LEN = 12
UNKNOWN = "<unknown>"
NONE = "<none>"


@dataclass(frozen=True)
class SourceCandidateResult:
    """Packet summary and sidecar payload for source diagnostic candidates."""

    summary: dict[str, Any] | None
    sidecar: dict[str, Any] | None


@dataclass(frozen=True)
class _SourcePathInfo:
    normalized_file: str
    source_reachable: bool
    source_resolution_status: str
    source_owned: bool
    source_ownership_status: str


def build_source_candidates(
    scan_result: ScanResult | dict[str, Any],
    *,
    src_root: str | Path | None,
    classifier: SemanticClassifier | None = None,
) -> SourceCandidateResult:
    """Return additive source candidates without changing ranking behavior."""

    scan_data = _scan_as_dict(scan_result)
    active_classifier = classifier or SemanticClassifier.from_file()
    candidates: list[dict[str, Any]] = []
    excluded_source_diagnostics: list[dict[str, Any]] = []
    excluded_summary = {
        "missing_file_count": 0,
        "missing_line_count": 0,
        "explicit_parent_count": 0,
    }

    for event in _events(scan_data):
        if event.get("kind") not in SOURCE_DIAGNOSTIC_KINDS:
            continue
        fatal_detection_source = _fatal_detection_source(event)
        if fatal_detection_source is None:
            continue
        file_value = event.get("file")
        line_value = event.get("line")
        missing_file = not isinstance(file_value, str) or not file_value
        missing_line = not isinstance(line_value, int) or line_value <= 0
        if missing_file or missing_line:
            if missing_file:
                excluded_summary["missing_file_count"] += 1
            if missing_line:
                excluded_summary["missing_line_count"] += 1
            excluded_source_diagnostics.append(
                _excluded_missing_location(
                    event,
                    missing_file=missing_file,
                    missing_line=missing_line,
                )
            )
            continue
        assert isinstance(line_value, int)
        line_int = line_value
        if event.get("parent"):
            excluded_summary["explicit_parent_count"] += 1
            excluded_source_diagnostics.append(_excluded_parent(event, str(file_value)))
            continue

        semantic_class = active_classifier.classify(event, scan_data).name
        warning_option = extract_warning_option(event)
        path_info = _source_path_info(str(file_value), src_root)
        candidate = _candidate(
            event,
            file_value=str(file_value),
            line_value=line_int,
            semantic_class=semantic_class,
            warning_option=warning_option,
            fatal_detection_source=fatal_detection_source,
            warning_option_source="message_regex" if warning_option is not None else "none",
            path_info=path_info,
        )
        candidates.append(candidate)

    if not candidates and not any(excluded_summary.values()):
        return SourceCandidateResult(summary=None, sidecar=None)

    counts = _candidate_counts(candidates)
    summary = {
        "schema_version": SOURCE_CANDIDATES_SCHEMA,
        "full_candidates_path": SIDECAR_NAME,
        "candidate_count": len(candidates),
        "structured_source_candidate_count": len(candidates),
        "type_probably_fixable_count": counts["type_probably_fixable"],
        "type_unknown_count": counts["type_unknown"],
        "type_not_fixable_count": counts["type_not_fixable"],
        "source_reachable_count": counts["source_reachable"],
        "source_owned_count": counts["source_owned"],
        "patch_ready_count": counts["patch_ready"],
        "excluded_summary": excluded_summary,
    }
    sidecar = {
        "schema_version": SOURCE_CANDIDATES_SIDECAR_SCHEMA,
        "candidates": candidates,
        "excluded_source_diagnostics": excluded_source_diagnostics,
        "excluded_summary": excluded_summary,
    }
    return SourceCandidateResult(summary=summary, sidecar=sidecar)


def _candidate(
    event: dict[str, Any],
    *,
    file_value: str,
    line_value: int,
    semantic_class: str,
    warning_option: str | None,
    fatal_detection_source: str,
    warning_option_source: str,
    path_info: _SourcePathInfo,
) -> dict[str, Any]:
    message = str(event.get("message") or "")
    type_fixability, type_fixability_reason = _type_fixability(
        warning_option=warning_option,
        semantic_class=semantic_class,
        message=message,
    )
    key, degraded_key = _dedupe_key(
        normalized_file=path_info.normalized_file,
        line=line_value,
        column=event.get("column"),
        warning_option=warning_option,
        semantic_class=semantic_class,
        message=message,
        command_id=event.get("command_id"),
        kind=event.get("kind"),
    )
    data = {
        "event_id": event.get("id"),
        "kind": event.get("kind"),
        "file": file_value,
        "normalized_file": path_info.normalized_file,
        "line": line_value,
        "column": event.get("column"),
        "message": message,
        "warning_option": warning_option,
        "warning_option_source": warning_option_source,
        "semantic_class": semantic_class,
        "command_id": event.get("command_id"),
        "line_no": event.get("line_no"),
        "source_located": True,
        "parent": event.get("parent"),
        "cascade_status": "none",
        "fatal_detection_source": fatal_detection_source,
        "type_fixability": type_fixability,
        "type_fixability_reason": type_fixability_reason,
        "source_reachable": path_info.source_reachable,
        "source_resolution_status": path_info.source_resolution_status,
        "source_owned": path_info.source_owned,
        "source_ownership_status": path_info.source_ownership_status,
        "exclusion_reason": None,
        "dedupe_key": key,
        "degraded_key": degraded_key,
    }
    return data


def _excluded_parent(event: dict[str, Any], file_value: str) -> dict[str, Any]:
    data = {
        "event_id": event.get("id"),
        "file": file_value,
        "line": event.get("line"),
        "parent": event.get("parent"),
        "exclusion_reason": "explicit_parent",
    }
    return {key: value for key, value in data.items() if value is not None}


def _excluded_missing_location(
    event: dict[str, Any],
    *,
    missing_file: bool,
    missing_line: bool,
) -> dict[str, Any]:
    if missing_file and missing_line:
        reason = "missing_file_and_line"
    elif missing_file:
        reason = "missing_file"
    else:
        reason = "missing_line"
    data = {
        "event_id": event.get("id"),
        "file": event.get("file"),
        "line": event.get("line"),
        "exclusion_reason": reason,
    }
    return {key: value for key, value in data.items() if value is not None}


def _fatal_detection_source(event: dict[str, Any]) -> str | None:
    if str(event.get("severity") or "").strip().lower() == "error":
        return "severity"
    if event.get("kind") == "werror":
        return "kind"
    if "-Werror" in str(event.get("message") or ""):
        return "werror_message_fallback"
    return None


def _type_fixability(
    *,
    warning_option: str | None,
    semantic_class: str,
    message: str,
) -> tuple[str, str]:
    if warning_option in PROBABLY_FIXABLE_WARNING_OPTIONS:
        return "probably_fixable", f"whitelisted_warning_option:{warning_option}"
    if _is_unused_field(semantic_class=semantic_class, message=message):
        return "probably_fixable", "unused_field_message_rule"
    return "unknown", "no_matching_fixability_rule"


def _is_unused_field(*, semantic_class: str, message: str) -> bool:
    lowered = message.lower()
    if semantic_class in {"unused_field", "unused_private_field"}:
        return True
    return (
        "unused" in lowered and "field" in lowered
    ) or "private field" in lowered and "not used" in lowered


def _source_path_info(file_value: str, src_root: str | Path | None) -> _SourcePathInfo:
    raw_normalized = _normalize_raw_file(file_value)
    if _is_system_path(raw_normalized):
        return _SourcePathInfo(
            normalized_file=raw_normalized,
            source_reachable=False,
            source_resolution_status=_unreachable_status(src_root),
            source_owned=False,
            source_ownership_status="system_or_toolchain_path",
        )

    mapped = _mapped_source_path(file_value, src_root)
    if mapped is not None:
        assert src_root is not None
        normalized = _relative_posix(mapped, Path(src_root).resolve())
        if _has_suspect_part(normalized):
            return _SourcePathInfo(
                normalized_file=normalized,
                source_reachable=True,
                source_resolution_status="mapped_to_source_root",
                source_owned=False,
                source_ownership_status="generated_or_vendor",
            )
        return _SourcePathInfo(
            normalized_file=normalized,
            source_reachable=True,
            source_resolution_status="mapped_to_source_root",
            source_owned=True,
            source_ownership_status="project_owned",
        )

    if _has_suspect_part(raw_normalized):
        return _SourcePathInfo(
            normalized_file=raw_normalized,
            source_reachable=False,
            source_resolution_status=_unreachable_status(src_root),
            source_owned=False,
            source_ownership_status="generated_or_vendor",
        )
    if src_root is None:
        return _SourcePathInfo(
            normalized_file=raw_normalized,
            source_reachable=False,
            source_resolution_status="source_root_unavailable",
            source_owned=False,
            source_ownership_status="unknown",
        )
    return _SourcePathInfo(
        normalized_file=raw_normalized,
        source_reachable=False,
        source_resolution_status="source_mapping_unavailable",
        source_owned=False,
        source_ownership_status="unknown",
    )


def _unreachable_status(src_root: str | Path | None) -> str:
    return "source_root_unavailable" if src_root is None else "source_mapping_unavailable"


def _mapped_source_path(file_value: str, src_root: str | Path | None) -> Path | None:
    if src_root is None:
        return None
    root = Path(src_root)
    if not root.is_dir():
        return None
    candidates = _resolve_candidate_paths(file_value, root)
    return candidates[0] if len(candidates) == 1 else None


def _resolve_candidate_paths(file_value: str, src_root: Path) -> list[Path]:
    root = src_root.resolve()
    requested = Path(file_value)
    if requested.is_absolute():
        candidate = requested.resolve()
        if candidate.is_file():
            try:
                candidate.relative_to(root)
            except ValueError:
                pass
            else:
                return [candidate]
        parts = requested.parts
        for start in range(1, len(parts)):
            candidates = _suffix_candidates(root, parts[start:])
            if candidates:
                return candidates
        return []
    return _suffix_candidates(root, requested.parts)


def _suffix_candidates(root: Path, requested_parts: tuple[str, ...]) -> list[Path]:
    if not requested_parts:
        return []
    basename = requested_parts[-1]
    candidates: list[Path] = []
    for path in _iter_files_by_basename(root, basename):
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if len(relative_parts) >= len(requested_parts) and (
            relative_parts[-len(requested_parts) :] == requested_parts
        ):
            candidates.append(path)
    return sorted(candidates)


def _iter_files_by_basename(root: Path, basename: str) -> list[Path]:
    matches: list[Path] = []
    pending = [root]
    while pending:
        current = pending.pop()
        try:
            children = sorted(current.iterdir(), key=lambda item: item.name)
        except OSError:
            continue
        for child in children:
            if child.is_dir():
                if _should_skip_dir(child):
                    continue
                pending.append(child)
            elif child.is_file() and child.name == basename:
                matches.append(child)
    return matches


def _should_skip_dir(path: Path) -> bool:
    return path.name in SKIPPED_DIR_NAMES or path.name.startswith("GBS-ROOT")


def _relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _normalize_raw_file(file_value: str) -> str:
    return posixpath.normpath(file_value.replace("\\", "/"))


def _is_system_path(normalized_file: str) -> bool:
    return any(
        normalized_file == prefix or normalized_file.startswith(prefix + "/")
        for prefix in SYSTEM_PREFIXES
    )


def _has_suspect_part(normalized_file: str) -> bool:
    parts = [part.lower() for part in normalized_file.split("/") if part]
    return any(part in SUSPECT_PATH_PARTS for part in parts)


def _dedupe_key(
    *,
    normalized_file: str,
    line: int,
    column: Any,
    warning_option: str | None,
    semantic_class: str,
    message: str,
    command_id: Any,
    kind: Any,
) -> tuple[str, bool]:
    degraded = False
    column_part: str
    if isinstance(column, int):
        column_part = str(column)
    else:
        column_part = UNKNOWN
        degraded = True
    warning_part = warning_option or NONE
    if warning_option is None:
        degraded = True
    semantic_part = semantic_class or UNKNOWN
    if not semantic_class:
        degraded = True
    command_part = str(command_id) if isinstance(command_id, str) and command_id else UNKNOWN
    if command_part == UNKNOWN:
        degraded = True
    parts = [
        f"file={normalized_file}",
        f"line={line}",
        f"column={column_part}",
        f"warning_option={warning_part}",
        f"semantic_class={semantic_part}",
        f"message={_message_fingerprint(message)}",
        f"command_id={command_part}",
        f"kind={kind or UNKNOWN}",
    ]
    return "|".join(parts), degraded


def _message_fingerprint(message: str) -> str:
    normalized = re.sub(r"\s+", " ", message.strip().lower())
    return hashlib.sha1(normalized.encode("utf-8", errors="replace")).hexdigest()[
        :MESSAGE_FINGERPRINT_LEN
    ]


def _candidate_counts(candidates: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "type_probably_fixable": 0,
        "type_unknown": 0,
        "type_not_fixable": 0,
        "source_reachable": 0,
        "source_owned": 0,
        "patch_ready": 0,
    }
    for candidate in candidates:
        value = candidate.get("type_fixability")
        if value == "probably_fixable":
            counts["type_probably_fixable"] += 1
        elif value == "not_fixable":
            counts["type_not_fixable"] += 1
        else:
            counts["type_unknown"] += 1
        if candidate.get("source_reachable") is True:
            counts["source_reachable"] += 1
        if candidate.get("source_owned") is True:
            counts["source_owned"] += 1
        if (
            value == "probably_fixable"
            and candidate.get("source_reachable") is True
            and candidate.get("source_owned") is True
        ):
            counts["patch_ready"] += 1
    return counts


def _events(scan_data: dict[str, Any]) -> list[dict[str, Any]]:
    return [event for event in scan_data.get("events", []) if isinstance(event, dict)]


def _scan_as_dict(scan_result: ScanResult | dict[str, Any]) -> dict[str, Any]:
    if isinstance(scan_result, ScanResult):
        return scan_result.as_dict()
    return scan_result
