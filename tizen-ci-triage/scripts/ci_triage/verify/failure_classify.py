"""Classify build verification failures before another repair attempt.

The classifier is intentionally conservative: it is better to miss an automatic
repair opportunity than to let Cline edit source for a toolchain, dependency, or
environment failure.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

CONFIDENCE_THRESHOLD = 0.8
SOURCE_KINDS = {"compiler", "werror"}
RAW_KINDS = {"raw_error", "raw_unparsed"}
NON_BUILD_STAGE_CLASSES = {
    "apply_failed": "apply_failed",
    "analyzer_failed": "analyzer_failed",
    "infrastructure_failed": "infrastructure_failed",
    "build_mutated_source": "build_mutated_source",
}
EXPLICIT_NON_REPAIR_CLASSES = {"source_unreachable"}
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


@dataclass(frozen=True)
class FailureClassification:
    """Decision returned by the failure classifier."""

    repair_allowed: bool
    failure_class: str
    confidence: float
    matched_rule: str | None
    reason: str


@dataclass(frozen=True)
class _DenyRule:
    rule_id: str
    failure_class: str
    pattern: re.Pattern[str]
    reason: str


DENYLIST_RULES: tuple[_DenyRule, ...] = (
    _DenyRule(
        rule_id="toolchain_flag_enable_ml_inliner",
        failure_class="toolchain",
        pattern=re.compile(r"-enable-ml-inliner(?:=|\b)", re.IGNORECASE),
        reason="LLVM MLGO/pass flag failure is a toolchain integration issue",
    ),
    _DenyRule(
        rule_id="toolchain_unknown_argument",
        failure_class="toolchain",
        pattern=re.compile(r"\b(?:unknown|unsupported)\s+(?:argument|option)\b", re.IGNORECASE),
        reason="compiler rejected a toolchain or command-line flag",
    ),
    _DenyRule(
        rule_id="toolchain_unrecognized_option",
        failure_class="toolchain",
        pattern=re.compile(r"\bunrecognized\b.*\boption\b", re.IGNORECASE),
        reason="compiler rejected a toolchain or command-line option",
    ),
    _DenyRule(
        rule_id="toolchain_unknown_warning_option",
        failure_class="toolchain",
        pattern=re.compile(r"\bunknown warning option\b", re.IGNORECASE),
        reason="compiler rejected a warning flag rather than source code",
    ),
    _DenyRule(
        rule_id="missing_link_library",
        failure_class="dependency",
        pattern=re.compile(r"\bcannot find -l[^\s:]+", re.IGNORECASE),
        reason="linker cannot find a required library",
    ),
    _DenyRule(
        rule_id="missing_library_path",
        failure_class="dependency",
        pattern=re.compile(r"(?:-l|-L)[^\n]*\bNo such file or directory\b", re.IGNORECASE),
        reason="library or library path is missing from the build environment",
    ),
    _DenyRule(
        rule_id="no_space_left",
        failure_class="build_env",
        pattern=re.compile(r"\bNo space left on device\b", re.IGNORECASE),
        reason="builder storage is exhausted",
    ),
    _DenyRule(
        rule_id="read_only_filesystem",
        failure_class="build_env",
        pattern=re.compile(r"\bRead-only file system\b", re.IGNORECASE),
        reason="builder filesystem is read-only",
    ),
    _DenyRule(
        rule_id="out_of_memory",
        failure_class="build_env",
        pattern=re.compile(r"\b(?:out of memory|oom-killer|killed process)\b", re.IGNORECASE),
        reason="builder appears to have run out of memory",
    ),
    _DenyRule(
        rule_id="depsolve_failure",
        failure_class="dependency",
        pattern=re.compile(
            r"\b(?:nothing provides|depsolve|cannot install|conflicting requests)\b",
            re.IGNORECASE,
        ),
        reason="dependency resolution failed before source repair can help",
    ),
)


def classify_failure(
    evidence: Mapping[str, Any],
    *,
    build_log: str = "",
    failure_stage: str = "gbs_build_failed",
) -> FailureClassification:
    """Classify a build verification failure.

    ``evidence`` may be a full Evidence Packet with ``primary_error`` or a primary
    diagnostic mapping directly. The result is deliberately biased toward
    ``repair_allowed=False`` unless the diagnostic is a high-confidence source
    repair candidate.
    """

    primary = _primary_error(evidence)

    stage_class = NON_BUILD_STAGE_CLASSES.get(failure_stage)
    if stage_class is not None:
        return FailureClassification(
            repair_allowed=False,
            failure_class=stage_class,
            confidence=1.0,
            matched_rule=f"failure_stage:{failure_stage}",
            reason=f"{failure_stage} is not a source-build failure classification path",
        )

    deny = _match_denylist(primary, build_log)
    if deny is not None:
        return deny

    if _kind(primary) in RAW_KINDS:
        return FailureClassification(
            repair_allowed=False,
            failure_class="raw_unparsed",
            confidence=1.0,
            matched_rule="denylist:raw_unparsed",
            reason="analyzer produced a raw/unparsed diagnostic",
        )

    heuristic = _heuristic_classification(primary)
    if (
        heuristic.confidence < CONFIDENCE_THRESHOLD
        and heuristic.failure_class not in EXPLICIT_NON_REPAIR_CLASSES
    ):
        return FailureClassification(
            repair_allowed=False,
            failure_class="uncertain",
            confidence=heuristic.confidence,
            matched_rule=heuristic.matched_rule,
            reason=heuristic.reason,
        )
    return heuristic


def _primary_error(evidence: Mapping[str, Any]) -> Mapping[str, Any]:
    primary = evidence.get("primary_error")
    if isinstance(primary, Mapping):
        return primary
    return evidence


def _match_denylist(
    primary: Mapping[str, Any],
    build_log: str,
) -> FailureClassification | None:
    haystack = "\n".join(
        (
            _string(primary.get("message")),
            _string(primary.get("details")),
            build_log,
        )
    )
    for rule in DENYLIST_RULES:
        if rule.pattern.search(haystack):
            return FailureClassification(
                repair_allowed=False,
                failure_class=rule.failure_class,
                confidence=1.0,
                matched_rule=f"denylist:{rule.rule_id}",
                reason=rule.reason,
            )
    return None


def _heuristic_classification(primary: Mapping[str, Any]) -> FailureClassification:
    kind = _kind(primary)
    if kind in SOURCE_KINDS:
        return _source_diagnostic_classification(primary)

    if kind.startswith("link") and _message_has_source_symbol(primary):
        return FailureClassification(
            repair_allowed=False,
            failure_class="uncertain",
            confidence=0.7,
            matched_rule="heuristic:link_symbol",
            reason=(
                "linker error may be source-related, but confidence is below "
                "automatic repair gate"
            ),
        )

    return FailureClassification(
        repair_allowed=False,
        failure_class="uncertain",
        confidence=0.2,
        matched_rule="heuristic:unsupported_kind",
        reason=f"unsupported or non-source analyzer kind: {kind or '<missing>'}",
    )


def _source_diagnostic_classification(primary: Mapping[str, Any]) -> FailureClassification:
    if not _has_source_location(primary):
        return FailureClassification(
            repair_allowed=False,
            failure_class="source_unreachable",
            confidence=0.4,
            matched_rule="heuristic:missing_source_location",
            reason="source diagnostic has no reliable file/line location",
        )

    if not _source_reachable(primary):
        return FailureClassification(
            repair_allowed=False,
            failure_class="source_unreachable",
            confidence=0.55,
            matched_rule="heuristic:source_unreachable",
            reason="source file could not be mapped to the local source root",
        )

    if not _source_owned(primary):
        return FailureClassification(
            repair_allowed=False,
            failure_class="source_unreachable",
            confidence=0.55,
            matched_rule="heuristic:source_not_owned",
            reason="diagnostic path is not project-owned source",
        )

    if not _probably_fixable(primary):
        return FailureClassification(
            repair_allowed=False,
            failure_class="uncertain",
            confidence=0.65,
            matched_rule="heuristic:type_unknown",
            reason="diagnostic is source-located but not known probably-fixable",
        )

    return FailureClassification(
        repair_allowed=True,
        failure_class="source_repairable",
        confidence=0.95,
        matched_rule="heuristic:source_werror_or_compile_error",
        reason="source-located, source-owned, probably-fixable compiler/werror diagnostic",
    )


def _has_source_location(primary: Mapping[str, Any]) -> bool:
    file_value = primary.get("file") or primary.get("normalized_file")
    line_value = primary.get("line")
    return (
        isinstance(file_value, str)
        and bool(file_value)
        and isinstance(line_value, int)
        and line_value > 0
    )


def _source_reachable(primary: Mapping[str, Any]) -> bool:
    value = primary.get("source_reachable")
    if isinstance(value, bool):
        return value
    status = primary.get("source_resolution_status")
    if isinstance(status, str):
        return status == "mapped_to_source_root"
    return _looks_project_source_path(_source_file(primary))


def _source_owned(primary: Mapping[str, Any]) -> bool:
    value = primary.get("source_owned")
    if isinstance(value, bool):
        return value
    status = primary.get("source_ownership_status")
    if isinstance(status, str):
        return status == "project_owned"
    return _looks_project_source_path(_source_file(primary))


def _probably_fixable(primary: Mapping[str, Any]) -> bool:
    for key in ("type_fixability", "provisional_fixability", "fixability"):
        value = primary.get(key)
        if isinstance(value, str):
            return value == "probably_fixable"
    diagnostic_code = primary.get("diagnostic_code") or primary.get("warning_option")
    if isinstance(diagnostic_code, str) and diagnostic_code.startswith("-W"):
        return True
    message = _string(primary.get("message")).lower()
    return any(
        marker in message
        for marker in (
            "use of undeclared",
            "no member named",
            "invalid conversion",
            "deprecated",
            "[-werror",
        )
    )


def _looks_project_source_path(path: str | None) -> bool:
    if not path:
        return False
    lowered = path.replace("\\", "/").lower()
    if lowered.startswith(SYSTEM_PREFIXES):
        return False
    parts = {part for part in lowered.split("/") if part}
    return not bool(parts & SUSPECT_PATH_PARTS)


def _source_file(primary: Mapping[str, Any]) -> str | None:
    file_value = primary.get("normalized_file") or primary.get("file")
    if isinstance(file_value, str) and file_value:
        return file_value
    return None


def _message_has_source_symbol(primary: Mapping[str, Any]) -> bool:
    message = _string(primary.get("message"))
    return bool(re.search(r"`?[A-Za-z_][A-Za-z0-9_]*`?", message))


def _kind(primary: Mapping[str, Any]) -> str:
    return _string(primary.get("kind")).lower()


def _string(value: object) -> str:
    return value if isinstance(value, str) else ""
