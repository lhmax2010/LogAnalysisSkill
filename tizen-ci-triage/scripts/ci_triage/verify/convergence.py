"""Convergence decisions for repeated CI triage repair attempts.

Stage 1 intentionally uses approximate fingerprints built from existing
Evidence Packet fields. The bias is to allow one more repair attempt unless the
same diagnostic clearly remains unchanged, or a source-level error cluster newly
appears in files touched by the attempted patch.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DEFAULT_BUILD_PREFIXES = ("/home/abuild/rpmbuild/BUILD/",)
SOURCE_CLUSTER_KINDS = {"compiler", "compile_error", "source_warning_option", "werror"}
SOURCE_DIAGNOSTIC_KINDS = {"compiler", "compile_error", "werror"}
ERROR_DIAGNOSTIC_KINDS = {"compile_error", "compiler", "error", "werror"}
_WARNING_OPTION_RE = re.compile(r"-W[A-Za-z0-9_+=.,-]+")
_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_BUILD_PACKAGE_RE = re.compile(r".+-\d[\w.+:~%-]*$")


@dataclass(frozen=True)
class ConvergenceResult:
    """Result written by ``check-convergence``."""

    verdict: str
    confidence: str
    reason: str
    current_fingerprint: dict[str, Any] | None
    previous_fingerprint: dict[str, Any] | None
    error_count: int
    previous_error_count: int
    regression_suspected: bool
    touched_files_available: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _Fingerprint:
    normalized_file: str
    diagnostic_code: str
    anchor: str
    kind: str
    message: str

    @property
    def identity(self) -> tuple[str, str, str]:
        return (self.normalized_file, self.diagnostic_code, self.anchor)

    @property
    def attributes(self) -> tuple[str, str]:
        return (self.kind, self.message)

    def to_dict(self) -> dict[str, str]:
        return {
            "normalized_file": self.normalized_file,
            "diagnostic_code": self.diagnostic_code,
            "anchor": self.anchor,
            "kind": self.kind,
            "message": self.message,
        }


@dataclass(frozen=True)
class _ClusterView:
    type_key: tuple[str, tuple[str, ...], str]
    occurrence_key: tuple[str, tuple[str, ...], str, tuple[str, ...]]
    files: frozenset[str]
    count: int
    source_level: bool


def check_convergence(
    current_evidence: dict[str, Any],
    previous_evidence: dict[str, Any] | None,
    *,
    touched_files: set[str] | None = None,
) -> ConvergenceResult:
    """Return whether another repair iteration should continue.

    ``touched_files=None`` means the caller could not provide patch coverage, so
    regression detection is disabled fail-safe.
    """

    current_fingerprint = _primary_fingerprint(current_evidence, touched_files=touched_files)
    previous_fingerprint = (
        _primary_fingerprint(previous_evidence, touched_files=touched_files)
        if previous_evidence is not None
        else None
    )
    current_error_count = _error_count(current_evidence)
    previous_error_count = _error_count(previous_evidence) if previous_evidence is not None else 0
    touched_available = bool(touched_files)
    regression_suspected = _regression_suspected(
        current_evidence,
        previous_error_count=previous_error_count,
        current_error_count=current_error_count,
        touched_files=touched_files,
    )

    if previous_evidence is None:
        return ConvergenceResult(
            verdict="advance",
            confidence="low",
            reason="previous_missing_one_round_advance",
            current_fingerprint=_fingerprint_dict(current_fingerprint),
            previous_fingerprint=None,
            error_count=current_error_count,
            previous_error_count=0,
            regression_suspected=regression_suspected,
            touched_files_available=touched_available,
        )

    regression_reason = _regression_reason(
        current_evidence,
        previous_evidence,
        touched_files=touched_files,
    )
    if regression_reason is not None:
        return ConvergenceResult(
            verdict="regressed",
            confidence="high",
            reason=regression_reason,
            current_fingerprint=_fingerprint_dict(current_fingerprint),
            previous_fingerprint=_fingerprint_dict(previous_fingerprint),
            error_count=current_error_count,
            previous_error_count=previous_error_count,
            regression_suspected=regression_suspected,
            touched_files_available=touched_available,
        )

    if (
        current_fingerprint is not None
        and previous_fingerprint is not None
        and current_fingerprint.identity == previous_fingerprint.identity
        and current_fingerprint.attributes == previous_fingerprint.attributes
        and current_error_count == previous_error_count
    ):
        return ConvergenceResult(
            verdict="stalled",
            confidence="high",
            reason="fingerprint_unchanged_error_count_unchanged",
            current_fingerprint=current_fingerprint.to_dict(),
            previous_fingerprint=previous_fingerprint.to_dict(),
            error_count=current_error_count,
            previous_error_count=previous_error_count,
            regression_suspected=regression_suspected,
            touched_files_available=touched_available,
        )

    reason = "fingerprint_changed_or_error_count_changed"
    if not touched_available:
        reason += ";touched_files_unavailable_no_regression_check"
    if regression_suspected:
        reason += ";regression_suspected_not_decisive"
    return ConvergenceResult(
        verdict="advance",
        confidence="medium",
        reason=reason,
        current_fingerprint=_fingerprint_dict(current_fingerprint),
        previous_fingerprint=_fingerprint_dict(previous_fingerprint),
        error_count=current_error_count,
        previous_error_count=previous_error_count,
        regression_suspected=regression_suspected,
        touched_files_available=touched_available,
    )


def write_convergence_result(result: ConvergenceResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def touched_files_from_json(path: Path) -> set[str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("touched-files JSON must be an object")
    files = raw.get("files")
    if not isinstance(files, list):
        raise ValueError("touched-files JSON must contain a files list")
    result: set[str] = set()
    for item in files:
        if not isinstance(item, str) or not item:
            raise ValueError("touched-files files entries must be non-empty strings")
        result.add(_normalize_file(item))
    return result


def _fingerprint_dict(fingerprint: _Fingerprint | None) -> dict[str, Any] | None:
    return fingerprint.to_dict() if fingerprint is not None else None


def _primary_fingerprint(
    evidence: dict[str, Any],
    *,
    touched_files: set[str] | None,
) -> _Fingerprint | None:
    primary = evidence.get("primary_error")
    if not isinstance(primary, dict):
        return None
    normalized_file = _normalize_file(
        _string(primary.get("normalized_file") or primary.get("file")),
        touched_files,
    )
    diagnostic_code = _diagnostic_code(primary)
    message = _normalize_message(_string(primary.get("message")))
    return _Fingerprint(
        normalized_file=normalized_file,
        diagnostic_code=diagnostic_code,
        anchor=_anchor(primary),
        kind=_string(primary.get("kind")),
        message=message,
    )


def _diagnostic_code(data: dict[str, Any]) -> str:
    for key in ("diagnostic_code", "warning_option", "semantic_class"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    message = _string(data.get("message"))
    for token in _WARNING_OPTION_RE.findall(message):
        if token != "-Werror":
            return str(token)
    return "<none>"


def _anchor(primary: dict[str, Any]) -> str:
    for key in ("source_anchor", "symbol"):
        value = primary.get(key)
        if isinstance(value, str) and value:
            return value
    snippet = primary.get("source_snippet")
    if isinstance(snippet, str) and snippet.strip():
        return _stable_hash(_normalize_message(snippet))
    message = _string(primary.get("message"))
    quoted = re.findall(r"[`']([A-Za-z_][A-Za-z0-9_]*)[`']", message)
    if quoted:
        return str(quoted[0])
    identifiers = [
        token
        for token in _IDENTIFIER_RE.findall(message)
        if token.lower() not in {"error", "warning", "werror", "deprecated"}
    ]
    if identifiers:
        return str(identifiers[0])
    return _stable_hash(_normalize_message(message))


def _regression_reason(
    current_evidence: dict[str, Any],
    previous_evidence: dict[str, Any],
    *,
    touched_files: set[str] | None,
) -> str | None:
    if not touched_files:
        return None
    previous_by_type: dict[tuple[str, tuple[str, ...], str], set[str]] = {}
    for cluster in _clusters(previous_evidence, touched_files=touched_files):
        previous_by_type.setdefault(cluster.type_key, set()).update(cluster.files)

    for cluster in _clusters(current_evidence, touched_files=touched_files):
        if not cluster.source_level:
            continue
        previous_files = previous_by_type.get(cluster.type_key)
        if previous_files is None:
            added_files = set(cluster.files)
            token = "new_source_cluster_in_touched"
        else:
            added_files = set(cluster.files) - previous_files
            token = "expanded_source_cluster_in_touched"
        touched_added = sorted(added_files & touched_files)
        if touched_added:
            return f"{token}:{','.join(touched_added)}"
    return None


def _regression_suspected(
    current_evidence: dict[str, Any],
    *,
    previous_error_count: int,
    current_error_count: int,
    touched_files: set[str] | None,
) -> bool:
    if not touched_files:
        return False
    if (
        current_error_count < previous_error_count * 2
        or current_error_count - previous_error_count < 20
    ):
        return False
    affected: set[str] = set()
    for cluster in _clusters(current_evidence, touched_files=touched_files):
        if cluster.source_level:
            affected.update(cluster.files)
    return bool(affected & touched_files)


def _clusters(evidence: dict[str, Any], *, touched_files: set[str] | None) -> list[_ClusterView]:
    raw = evidence.get("error_clusters")
    if not isinstance(raw, dict):
        return []
    raw_clusters = raw.get("clusters")
    if not isinstance(raw_clusters, list):
        return []
    result: list[_ClusterView] = []
    for item in raw_clusters:
        if not isinstance(item, dict):
            continue
        result.append(_cluster_view(item, touched_files=touched_files))
    return result


def _cluster_view(cluster: dict[str, Any], *, touched_files: set[str] | None) -> _ClusterView:
    kind = _string(cluster.get("kind"))
    diagnostic_kinds = tuple(sorted(_string_list(cluster.get("diagnostic_kinds"))))
    diagnostic_code = _cluster_diagnostic_code(cluster)
    files = frozenset(_cluster_files(cluster, touched_files=touched_files))
    type_key = (kind, diagnostic_kinds, diagnostic_code)
    return _ClusterView(
        type_key=type_key,
        occurrence_key=(*type_key, tuple(sorted(files))),
        files=files,
        count=_int(cluster.get("count")),
        source_level=_is_source_level_cluster(kind, diagnostic_kinds),
    )


def _cluster_diagnostic_code(cluster: dict[str, Any]) -> str:
    for key in ("warning_option", "diagnostic_code", "semantic_class"):
        value = cluster.get(key)
        if isinstance(value, str) and value:
            return value
    for location in _location_dicts(cluster):
        code = _diagnostic_code(location)
        if code != "<none>":
            return code
    return "<none>"


def _cluster_files(cluster: dict[str, Any], *, touched_files: set[str] | None) -> set[str]:
    files = set()
    raw_files = cluster.get("files")
    if isinstance(raw_files, list):
        for item in raw_files:
            if isinstance(item, str) and item:
                files.add(_normalize_file(item, touched_files))
    for location in _location_dicts(cluster):
        file_value = location.get("file")
        if isinstance(file_value, str) and file_value:
            files.add(_normalize_file(file_value, touched_files))
    return files


def _location_dicts(cluster: dict[str, Any]) -> list[dict[str, Any]]:
    locations: list[dict[str, Any]] = []
    for key in ("locations_sample", "locations"):
        value = cluster.get(key)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict):
                locations.append(item)
    return locations


def _is_source_level_cluster(kind: str, diagnostic_kinds: tuple[str, ...]) -> bool:
    if kind in SOURCE_CLUSTER_KINDS:
        return True
    return bool(set(diagnostic_kinds) & SOURCE_DIAGNOSTIC_KINDS)


def _error_count(evidence: dict[str, Any] | None) -> int:
    if evidence is None:
        return 0
    clusters = _clusters(evidence, touched_files=None)
    if clusters:
        return sum(cluster.count for cluster in clusters if _is_error_cluster(cluster))
    primary = evidence.get("primary_error")
    return 1 if isinstance(primary, dict) else 0


def _is_error_cluster(cluster: _ClusterView) -> bool:
    return bool(set(cluster.type_key[1]) & ERROR_DIAGNOSTIC_KINDS)


def _normalize_file(path: str, touched_files: set[str] | None = None) -> str:
    value = path.replace("\\", "/").strip()
    value = re.sub(r"(:\d+){1,2}$", "", value)
    for prefix in sorted(DEFAULT_BUILD_PREFIXES, key=len, reverse=True):
        normalized_prefix = prefix.replace("\\", "/")
        if value.startswith(normalized_prefix):
            value = value[len(normalized_prefix) :]
            parts = [part for part in value.split("/") if part]
            if len(parts) > 1 and _BUILD_PACKAGE_RE.match(parts[0]):
                value = "/".join(parts[1:])
            break
    value = value.lstrip("./")
    if touched_files:
        for touched in sorted(touched_files, key=len, reverse=True):
            if value == touched or value.endswith("/" + touched):
                return touched
    return value


def _normalize_message(message: str) -> str:
    value = message.lower()
    value = re.sub(r"(:\d+){1,2}", ":#", value)
    value = re.sub(r"\b\d+\b", "#", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:12]


def _string(value: object) -> str:
    return value if isinstance(value, str) else ""


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _int(value: object) -> int:
    return value if isinstance(value, int) else 0
