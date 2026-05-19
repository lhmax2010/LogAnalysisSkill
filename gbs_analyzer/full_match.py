"""Layer 4b full pattern matching and direct-answer verdicts."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from gbs_analyzer.evidence import Evidence
from gbs_analyzer.quick_filter import DEFAULT_PATTERN_PATH, PatternValidationError
from gbs_analyzer.scan_and_extract import ScanResult


class Verdict(Enum):
    DIRECT_TIER1 = "direct_tier1"
    DIRECT_TIER2 = "direct_tier2"
    NEEDS_LLM = "needs_llm"


@dataclass(frozen=True)
class DirectAnswer:
    enabled: bool
    fix_template: str | None = None
    evidence_required: tuple[str, ...] = ()


@dataclass(frozen=True)
class FullMatchPattern:
    id: str
    category: str
    tier: str
    event_kinds: tuple[str, ...]
    regex: tuple[re.Pattern[str], ...]
    required_context: dict[str, Any]
    negative_patterns: tuple[re.Pattern[str], ...]
    confidence: float
    terminal: bool
    direct_answer_tier1: DirectAnswer
    direct_answer_tier2: DirectAnswer


@dataclass(frozen=True)
class FullMatchResult:
    verdict: Verdict
    pattern_id: str | None = None
    matched_tier: str | None = None
    direct_answer: str | None = None
    captures: dict[str, str] | None = None
    reason: str | None = None
    confidence: float | None = None
    failure_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        packet_verdict = (
            "direct_answer"
            if self.verdict in {Verdict.DIRECT_TIER1, Verdict.DIRECT_TIER2}
            else "needs_llm"
        )
        data: dict[str, Any] = {
            "verdict": packet_verdict,
            "full_match_verdict": self.verdict.value,
            "pattern_id": self.pattern_id,
            "matched_tier": self.matched_tier,
            "direct_answer": self.direct_answer,
            "captures": self.captures or {},
            "reason": self.reason,
            "confidence": self.confidence,
            "failure_reason": self.failure_reason,
        }
        if self.verdict is Verdict.NEEDS_LLM and self.pattern_id:
            data["matched_patterns"] = [
                {
                    "pattern_id": self.pattern_id,
                    "confidence": self.confidence,
                    "captures": self.captures or {},
                    "failure_reason": self.failure_reason or self.reason,
                }
            ]
        return data


def load_full_match_patterns(
    path: str | Path = DEFAULT_PATTERN_PATH,
) -> list[FullMatchPattern]:
    """Load all tier1/tier2 patterns for Layer 4b matching."""

    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise PatternValidationError("pattern library must be a mapping")
    if raw.get("schema_version") != 2:
        raise PatternValidationError("pattern library schema_version must be 2")
    patterns = raw.get("patterns", [])
    if not isinstance(patterns, list):
        raise PatternValidationError("patterns must be a list")

    return [_compile_full_match_pattern(item) for item in patterns]


def determine_verdict(
    matched_rule: FullMatchPattern,
    event: dict[str, Any],
    evidence: Evidence,
    *,
    all_events: list[Any] | None = None,
    commands: dict[str, dict[str, Any]] | None = None,
    confidence: float | None = None,
) -> Verdict:
    """Return v0.5 §3.5 direct-answer verdict for a matched rule."""

    events = all_events or [event]
    command_map = commands or {}
    actual_confidence = matched_rule.confidence if confidence is None else confidence
    passes_required_context = _passes_required_context(
        matched_rule.required_context,
        event,
        events,
        command_map,
    )
    event_is_terminal = _is_terminal_event(event)

    if (
        matched_rule.direct_answer_tier1.enabled
        and actual_confidence >= 0.95
        and matched_rule.terminal
        and event_is_terminal
        and not evidence.degraded
        and passes_required_context
    ):
        return Verdict.DIRECT_TIER1

    tier2 = matched_rule.direct_answer_tier2
    if (
        tier2.enabled
        and actual_confidence >= 0.85
        and matched_rule.terminal
        and event_is_terminal
        and evidence.contains_all(list(tier2.evidence_required))
        and not evidence.degraded
    ):
        return Verdict.DIRECT_TIER2

    return Verdict.NEEDS_LLM


def full_match(
    scan_result: ScanResult | dict[str, Any],
    candidate: dict[str, Any],
    evidence: Evidence,
    *,
    patterns: list[FullMatchPattern] | None = None,
    pattern_path: str | Path = DEFAULT_PATTERN_PATH,
) -> FullMatchResult:
    """Evaluate a ranked candidate and its evidence against full patterns."""

    scan_data = _scan_as_dict(scan_result)
    event = _event_for_candidate(candidate, scan_data)
    if not event:
        return FullMatchResult(Verdict.NEEDS_LLM, reason="candidate_event_not_found")

    all_events = [item for item in scan_data.get("events", []) if isinstance(item, dict)]
    commands = {
        str(command["id"]): command
        for command in scan_data.get("commands", [])
        if isinstance(command, dict) and "id" in command
    }
    active_patterns = patterns if patterns is not None else load_full_match_patterns(pattern_path)

    first_needs_llm: FullMatchResult | None = None
    for pattern in active_patterns:
        captures = match_pattern(pattern, event, all_events, commands)
        if captures is None:
            continue
        confidence = _candidate_confidence(candidate, default=pattern.confidence)
        verdict = determine_verdict(
            pattern,
            event,
            evidence,
            all_events=all_events,
            commands=commands,
            confidence=confidence,
        )
        result = _result_from_verdict(
            verdict,
            pattern,
            captures,
            confidence=confidence,
            failure_reason=_failure_reason_for_needs_llm(
                pattern,
                event,
                evidence,
                all_events=all_events,
                commands=commands,
                confidence=confidence,
            )
            if verdict is Verdict.NEEDS_LLM
            else None,
        )
        if verdict in {Verdict.DIRECT_TIER1, Verdict.DIRECT_TIER2}:
            return result
        if first_needs_llm is None:
            first_needs_llm = result

    return first_needs_llm or FullMatchResult(Verdict.NEEDS_LLM, reason="no_pattern_match")


def match_pattern(
    pattern: FullMatchPattern,
    event: dict[str, Any],
    all_events: list[Any] | None = None,
    commands: dict[str, dict[str, Any]] | None = None,
) -> dict[str, str] | None:
    """Return regex captures when an event satisfies a full-match pattern."""

    if event.get("kind") not in pattern.event_kinds:
        return None
    events = all_events or [event]
    command_map = commands or {}
    if not _passes_required_context(pattern.required_context, event, events, command_map):
        return None

    message = str(event.get("message", ""))
    if any(negative.search(message) for negative in pattern.negative_patterns):
        return None

    for regex in pattern.regex:
        match = regex.search(message)
        if match:
            return {
                key: value
                for key, value in match.groupdict().items()
                if value is not None
            }
    return None


def _compile_full_match_pattern(item: Any) -> FullMatchPattern:
    if not isinstance(item, dict):
        raise PatternValidationError("each pattern must be a mapping")
    pattern_id = str(item.get("id", "<unknown>"))
    match = item.get("match")
    if not isinstance(match, dict):
        raise PatternValidationError(f"{pattern_id}: match must be a mapping")

    tier = str(item.get("tier", ""))
    if tier not in {"tier1", "tier2"}:
        raise PatternValidationError(f"{pattern_id}: tier must be tier1 or tier2")

    regexes = match.get("regex", [])
    if not isinstance(regexes, list) or not regexes:
        raise PatternValidationError(f"{pattern_id}: match.regex must be a non-empty list")

    direct_tier1 = _direct_answer_from_item(item, "direct_answer_tier1")
    if not direct_tier1.enabled and tier == "tier1" and item.get("fix_template"):
        direct_tier1 = DirectAnswer(
            enabled=True,
            fix_template=str(item["fix_template"]),
            evidence_required=(),
        )

    direct_tier2 = _direct_answer_from_item(item, "direct_answer_tier2")
    if not direct_tier1.enabled and not direct_tier2.enabled:
        raise PatternValidationError(
            f"{pattern_id}: at least one direct_answer tier must be enabled"
        )

    return FullMatchPattern(
        id=pattern_id,
        category=str(item["category"]),
        tier=tier,
        event_kinds=tuple(str(kind) for kind in item.get("event_kinds", [])),
        regex=tuple(re.compile(str(pattern), re.IGNORECASE) for pattern in regexes),
        required_context=dict(match.get("required_context", {})),
        negative_patterns=tuple(
            re.compile(str(pattern), re.IGNORECASE)
            for pattern in match.get("negative_patterns", [])
        ),
        confidence=float(item["confidence"]),
        terminal=bool(item["terminal"]),
        direct_answer_tier1=direct_tier1,
        direct_answer_tier2=direct_tier2,
    )


def _direct_answer_from_item(item: dict[str, Any], field: str) -> DirectAnswer:
    raw = item.get(field)
    if raw is None:
        return DirectAnswer(enabled=False)
    if not isinstance(raw, dict):
        raise PatternValidationError(f"{item.get('id', '<unknown>')}: {field} must be a mapping")

    enabled = bool(raw.get("enabled", False))
    evidence_required = raw.get("evidence_required", [])
    if evidence_required is None:
        evidence_required = []
    if not isinstance(evidence_required, list):
        raise PatternValidationError(
            f"{item.get('id', '<unknown>')}: {field}.evidence_required must be a list"
        )
    fix_template = raw.get("fix_template")
    if enabled and not fix_template:
        raise PatternValidationError(
            f"{item.get('id', '<unknown>')}: {field}.fix_template is required"
        )
    return DirectAnswer(
        enabled=enabled,
        fix_template=str(fix_template) if fix_template is not None else None,
        evidence_required=tuple(str(key) for key in evidence_required),
    )


def _result_from_verdict(
    verdict: Verdict,
    pattern: FullMatchPattern,
    captures: dict[str, str],
    *,
    confidence: float | None = None,
    failure_reason: str | None = None,
) -> FullMatchResult:
    actual_confidence = pattern.confidence if confidence is None else confidence
    if verdict == Verdict.DIRECT_TIER1:
        direct = _render_fix(pattern.direct_answer_tier1.fix_template, captures)
        return FullMatchResult(
            verdict,
            pattern_id=pattern.id,
            matched_tier="tier1",
            direct_answer=direct,
            captures=captures,
            confidence=actual_confidence,
        )
    if verdict == Verdict.DIRECT_TIER2:
        direct = _render_fix(pattern.direct_answer_tier2.fix_template, captures)
        return FullMatchResult(
            verdict,
            pattern_id=pattern.id,
            matched_tier="tier2",
            direct_answer=direct,
            captures=captures,
            confidence=actual_confidence,
        )
    return FullMatchResult(
        verdict,
        pattern_id=pattern.id,
        captures=captures,
        reason="matched_pattern_needs_llm",
        confidence=actual_confidence,
        failure_reason=failure_reason,
    )


def _candidate_confidence(candidate: dict[str, Any], *, default: float) -> float:
    try:
        return float(candidate.get("confidence", default))
    except (TypeError, ValueError):
        return default


def _failure_reason_for_needs_llm(
    pattern: FullMatchPattern,
    event: dict[str, Any],
    evidence: Evidence,
    *,
    all_events: list[Any],
    commands: dict[str, dict[str, Any]],
    confidence: float,
) -> str:
    if pattern.direct_answer_tier2.enabled and confidence < 0.85:
        return "confidence_below_tier2_threshold"
    if pattern.direct_answer_tier1.enabled and confidence < 0.95:
        return "confidence_below_tier1_threshold"
    if evidence.degraded:
        return "evidence_degraded"
    if not _is_terminal_event(event):
        return "event_not_terminal"
    if not pattern.terminal:
        return "pattern_not_terminal"
    tier2 = pattern.direct_answer_tier2
    if tier2.enabled and not evidence.contains_all(list(tier2.evidence_required)):
        return "missing_required_evidence"
    if not _passes_required_context(pattern.required_context, event, all_events, commands):
        return "required_context_not_met"
    return "direct_answer_requirements_not_met"


def _passes_required_context(
    context: dict[str, Any],
    event: dict[str, Any],
    all_events: list[Any],
    commands: dict[str, dict[str, Any]],
) -> bool:
    phases = context.get("phase")
    if phases is not None and event.get("phase") not in phases:
        return False

    severities = context.get("severity")
    if severities is not None and event.get("severity") not in severities:
        return False

    tools = context.get("tool_in")
    if tools is not None and _event_tool(event, commands) not in tools:
        return False

    if context.get("not_in_warning_block") and _is_in_warning_block(event, all_events):
        return False

    return True


def _event_tool(
    event: dict[str, Any],
    commands: dict[str, dict[str, Any]],
) -> str | None:
    command_id = event.get("command_id")
    if command_id is None:
        return None
    command = commands.get(str(command_id))
    if command is None:
        return None
    argv_short = str(command.get("argv_short", ""))
    try:
        parts = shlex.split(argv_short)
    except ValueError:
        parts = argv_short.split()
    if not parts:
        return None
    return Path(parts[0]).name


def _is_in_warning_block(event: dict[str, Any], all_events: list[Any], *, lines: int = 3) -> bool:
    line_no = event.get("line_no")
    if not isinstance(line_no, int):
        return False

    nearby = [
        candidate
        for candidate in all_events
        if isinstance(candidate, dict)
        and isinstance(candidate.get("line_no"), int)
        and abs(candidate["line_no"] - line_no) <= lines
    ]
    has_warning = any(
        candidate.get("severity") == "warning"
        or "warning:" in str(candidate.get("message", "")).lower()
        for candidate in nearby
    )
    has_other_error = any(
        candidate.get("id") != event.get("id")
        and (
            candidate.get("severity") == "error"
            or "error:" in str(candidate.get("message", "")).lower()
        )
        for candidate in nearby
    )
    return has_warning and not has_other_error


def _is_terminal_event(event: dict[str, Any]) -> bool:
    if "is_terminal" in event:
        return bool(event["is_terminal"])
    return not bool(event.get("parent"))


def _event_for_candidate(
    candidate: dict[str, Any],
    scan_data: dict[str, Any],
) -> dict[str, Any]:
    event_id = candidate.get("event_id") or candidate.get("id")
    for event in scan_data.get("events", []):
        if isinstance(event, dict) and event.get("id") == event_id:
            return event
    return candidate if candidate.get("kind") else {}


def _scan_as_dict(scan_result: ScanResult | dict[str, Any]) -> dict[str, Any]:
    if isinstance(scan_result, ScanResult):
        return scan_result.as_dict()
    return scan_result


def _render_fix(template: str | None, captures: dict[str, str]) -> str:
    if template is None:
        return ""
    return template.format_map(_SafeFormat(captures))


class _SafeFormat(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"
