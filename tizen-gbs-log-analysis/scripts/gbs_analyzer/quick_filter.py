"""Layer 4a quick pattern filter for tier1 fast-path matches."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from gbs_analyzer.scan_and_extract import ScanResult

DEFAULT_PATTERN_PATH = Path(__file__).resolve().parent / "patterns" / "gbs_errors.yaml"
UNCERTAIN_WORDS = ("可能", "通常", "建议", "检查", "may", "usually", "check")


class PatternValidationError(ValueError):
    """Raised when the quick-filter pattern library violates tier1 constraints."""


@dataclass(frozen=True)
class QuickPattern:
    id: str
    category: str
    tier: str
    event_kinds: tuple[str, ...]
    regex: tuple[re.Pattern[str], ...]
    required_context: dict[str, Any]
    negative_patterns: tuple[re.Pattern[str], ...]
    confidence: float
    terminal: bool
    fix_template: str


@dataclass(frozen=True)
class QuickFilterMatch:
    pattern_id: str
    category: str
    event_id: str
    confidence: float
    captures: dict[str, str]
    direct_answer: str
    minimal_packet: dict[str, Any]


@dataclass(frozen=True)
class QuickFilterResult:
    hit: bool
    match: QuickFilterMatch | None = None
    evaluated_patterns: int = 0


class QuickFilter:
    """Evaluate tier1 patterns against scan results."""

    def __init__(self, patterns: list[QuickPattern]) -> None:
        self.patterns = patterns

    @classmethod
    def from_file(cls, path: str | Path = DEFAULT_PATTERN_PATH) -> QuickFilter:
        library = (
            _load_default_pattern_library()
            if Path(path) == DEFAULT_PATTERN_PATH
            else load_pattern_library(path)
        )
        return cls(library["patterns"])

    def evaluate(self, scan_result: ScanResult | dict[str, Any]) -> QuickFilterResult:
        scan_data = _scan_as_dict(scan_result)
        events = scan_data.get("events", [])
        commands = {
            command["id"]: command
            for command in scan_data.get("commands", [])
            if isinstance(command, dict) and "id" in command
        }
        evaluated = 0

        for event in events:
            if not isinstance(event, dict):
                continue
            for pattern in self.patterns:
                evaluated += 1
                captures = _match_pattern(pattern, event, events, commands)
                if captures is None:
                    continue
                direct_answer = _render_fix(pattern.fix_template, captures)
                match = QuickFilterMatch(
                    pattern_id=pattern.id,
                    category=pattern.category,
                    event_id=str(event["id"]),
                    confidence=pattern.confidence,
                    captures=captures,
                    direct_answer=direct_answer,
                    minimal_packet=_minimal_packet(scan_data, event, pattern, direct_answer),
                )
                return QuickFilterResult(hit=True, match=match, evaluated_patterns=evaluated)

        return QuickFilterResult(hit=False, evaluated_patterns=evaluated)


def load_pattern_library(path: str | Path = DEFAULT_PATTERN_PATH) -> dict[str, Any]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise PatternValidationError("pattern library must be a mapping")
    return {
        "schema_version": raw.get("schema_version"),
        "tier1_allowed_categories": tuple(raw.get("tier1_allowed_categories", [])),
        "tier1_forbidden_categories": tuple(raw.get("tier1_forbidden_categories", [])),
        "patterns": _compile_patterns(raw),
    }


@lru_cache(maxsize=1)
def _load_default_pattern_library() -> dict[str, Any]:
    return load_pattern_library(DEFAULT_PATTERN_PATH)


def _compile_patterns(raw: dict[str, Any]) -> list[QuickPattern]:
    if raw.get("schema_version") != 2:
        raise PatternValidationError("pattern library schema_version must be 2")

    allowed = set(raw.get("tier1_allowed_categories", []))
    forbidden = set(raw.get("tier1_forbidden_categories", []))
    patterns = raw.get("patterns", [])
    if not isinstance(patterns, list):
        raise PatternValidationError("patterns must be a list")

    compiled: list[QuickPattern] = []
    for item in patterns:
        if not isinstance(item, dict):
            raise PatternValidationError("each pattern must be a mapping")
        if item.get("tier") != "tier1":
            continue
        _validate_tier1_pattern(item, allowed, forbidden)
        match = item["match"]
        compiled.append(
            QuickPattern(
                id=str(item["id"]),
                category=str(item["category"]),
                tier=str(item["tier"]),
                event_kinds=tuple(str(kind) for kind in item["event_kinds"]),
                regex=tuple(
                    re.compile(str(pattern), re.IGNORECASE) for pattern in match["regex"]
                ),
                required_context=dict(match.get("required_context", {})),
                negative_patterns=tuple(
                    re.compile(str(pattern), re.IGNORECASE)
                    for pattern in match.get("negative_patterns", [])
                ),
                confidence=float(item["confidence"]),
                terminal=bool(item["terminal"]),
                fix_template=str(item["fix_template"]),
            )
        )
    return compiled


def _validate_tier1_pattern(
    item: dict[str, Any], allowed: set[str], forbidden: set[str]
) -> None:
    pattern_id = item.get("id", "<unknown>")
    category = item.get("category")
    tier = item.get("tier")
    fix_template = str(item.get("fix_template", ""))

    if tier != "tier1":
        raise PatternValidationError(f"{pattern_id}: only tier1 patterns are allowed in M2")
    if category not in allowed:
        raise PatternValidationError(f"{pattern_id}: category is not tier1-allowed")
    if category in forbidden:
        raise PatternValidationError(f"{pattern_id}: category is tier1-forbidden")
    if not item.get("terminal"):
        raise PatternValidationError(f"{pattern_id}: tier1 pattern must be terminal")
    if float(item.get("confidence", 0.0)) < 0.95:
        raise PatternValidationError(f"{pattern_id}: tier1 confidence must be >= 0.95")
    limit = 150 if category == "patch_failed" else 300
    if len(fix_template) > limit:
        raise PatternValidationError(f"{pattern_id}: fix_template exceeds {limit} chars")
    if not any(word in fix_template for word in UNCERTAIN_WORDS):
        raise PatternValidationError(f"{pattern_id}: fix_template must be conservative")
    if "expand" not in fix_template:
        raise PatternValidationError(f"{pattern_id}: fix_template must mention expand")


def _match_pattern(
    pattern: QuickPattern,
    event: dict[str, Any],
    all_events: list[Any],
    commands: dict[str, dict[str, Any]],
) -> dict[str, str] | None:
    if event.get("kind") not in pattern.event_kinds:
        return None
    if not _passes_required_context(pattern.required_context, event, all_events, commands):
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

    if context.get("not_in_warning_block") and is_in_warning_block(event, all_events):
        return False

    return True


def is_in_warning_block(event: dict[str, Any], all_events: list[Any], *, lines: int = 3) -> bool:
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


def _event_tool(event: dict[str, Any], commands: dict[str, dict[str, Any]]) -> str | None:
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


def _scan_as_dict(scan_result: ScanResult | dict[str, Any]) -> dict[str, Any]:
    if isinstance(scan_result, ScanResult):
        return scan_result.as_dict()
    return scan_result


def _render_fix(template: str, captures: dict[str, str]) -> str:
    return template.format_map(_SafeFormat(captures))


class _SafeFormat(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _minimal_packet(
    scan_data: dict[str, Any],
    event: dict[str, Any],
    pattern: QuickPattern,
    direct_answer: str,
) -> dict[str, Any]:
    return {
        "schema_version": "evidence_packet/v1",
        "verdict": "direct_answer",
        "via": "fast_path",
        "failed_phase": scan_data.get("failed_phase"),
        "root_cause_candidates": [
            {
                "rank": 1,
                "event_id": event.get("id"),
                "kind": event.get("kind"),
                "confidence": pattern.confidence,
                "summary": event.get("message"),
            }
        ],
        "cascade_summary": "",
        "primary_error": event,
        "evidence": {},
        "matched_patterns": [pattern.id],
        "direct_answer": direct_answer,
        "matched_tier": "tier1",
        "prompt": None,
        "token_budget": {
            "limit": 1800,
            "used": None,
            "note": "Quick filter minimal packet is assembled before BudgetPool.",
        },
        "degraded": bool(scan_data.get("degraded_reasons")),
        "degraded_reasons": scan_data.get("degraded_reasons", []),
        "allowed_next_actions": ["expand"],
    }


def quick_filter(scan_result: ScanResult | dict[str, Any]) -> QuickFilterResult:
    """Evaluate the default pattern library against a scan result."""

    return QuickFilter.from_file().evaluate(scan_result)
