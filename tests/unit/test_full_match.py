from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from gbs_analyzer.evidence import Evidence
from gbs_analyzer.full_match import (
    DirectAnswer,
    FullMatchPattern,
    Verdict,
    determine_verdict,
    full_match,
    load_full_match_patterns,
    match_pattern,
)
from gbs_analyzer.quick_filter import PatternValidationError


def evidence(
    contains: set[str] | None = None,
    *,
    degraded: bool = False,
) -> Evidence:
    return Evidence(
        collector="test",
        level=3,
        granted_budget=900,
        data={},
        contains=contains or set(),
        degraded=degraded,
    )


def event(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "E001",
        "kind": "compiler",
        "severity": "error",
        "message": "use of undeclared identifier 'missing_symbol'",
        "line_no": 10,
        "command_id": "C001",
    }
    data.update(overrides)
    return data


def pattern(**overrides: object) -> FullMatchPattern:
    data: dict[str, object] = {
        "id": "compile_undeclared_identifier_tier2",
        "category": "compile_error",
        "tier": "tier2",
        "event_kinds": ("compiler",),
        "regex": load_full_match_patterns()[8].regex,
        "required_context": {"severity": ["error"]},
        "negative_patterns": (),
        "confidence": 0.86,
        "terminal": True,
        "direct_answer_tier1": DirectAnswer(enabled=False),
        "direct_answer_tier2": DirectAnswer(
            enabled=True,
            fix_template="fix {identifier}",
            evidence_required=("primary_error", "source_snippet", "command_summary"),
        ),
    }
    data.update(overrides)
    return FullMatchPattern(**data)  # type: ignore[arg-type]


def test_load_default_patterns_keeps_flat_tier1_and_nested_tier2() -> None:
    patterns = load_full_match_patterns()
    by_id = {item.id: item for item in patterns}

    assert len(patterns) == 12
    assert by_id["depsolve_nothing_provides"].direct_answer_tier1.enabled
    assert by_id["depsolve_nothing_provides"].direct_answer_tier1.evidence_required == ()
    assert by_id["depsolve_nothing_provides"].direct_answer_tier2.enabled
    assert by_id["compile_undeclared_identifier_tier2"].direct_answer_tier1.enabled is False
    assert by_id["compile_undeclared_identifier_tier2"].direct_answer_tier2.evidence_required == (
        "primary_error",
        "command_summary",
        "source_snippet",
    )


def test_match_pattern_returns_named_captures() -> None:
    captures = match_pattern(pattern(), event())

    assert captures == {"identifier": "missing_symbol"}


def test_match_pattern_rejects_event_kind() -> None:
    assert match_pattern(pattern(), event(kind="depsolve")) is None


def test_match_pattern_rejects_required_context() -> None:
    assert match_pattern(pattern(), event(severity="warning")) is None


def test_match_pattern_rejects_negative_pattern() -> None:
    rule = replace(pattern(), negative_patterns=load_full_match_patterns()[8].negative_patterns)

    assert match_pattern(rule, event(message="warning: undeclared identifier 'missing'")) is None


def test_determine_verdict_returns_direct_tier1_for_flat_shorthand() -> None:
    rule = load_full_match_patterns()[0]
    verdict = determine_verdict(
        rule,
        event(kind="depsolve", message="nothing provides libfoo", severity="error"),
        evidence(),
    )

    assert verdict is Verdict.DIRECT_TIER1


def test_determine_verdict_returns_direct_tier2_when_evidence_complete() -> None:
    verdict = determine_verdict(
        pattern(),
        event(),
        evidence({"primary_error", "source_snippet", "command_summary"}),
    )

    assert verdict is Verdict.DIRECT_TIER2


def test_determine_verdict_needs_llm_when_tier2_evidence_missing() -> None:
    verdict = determine_verdict(pattern(), event(), evidence({"primary_error"}))

    assert verdict is Verdict.NEEDS_LLM


def test_determine_verdict_needs_llm_when_evidence_degraded() -> None:
    verdict = determine_verdict(
        pattern(),
        event(),
        evidence({"primary_error", "source_snippet", "command_summary"}, degraded=True),
    )

    assert verdict is Verdict.NEEDS_LLM


def test_determine_verdict_needs_llm_when_event_is_non_terminal() -> None:
    verdict = determine_verdict(
        pattern(),
        event(parent="E000"),
        evidence({"primary_error", "source_snippet", "command_summary"}),
    )

    assert verdict is Verdict.NEEDS_LLM


def test_determine_verdict_needs_llm_when_rule_confidence_too_low() -> None:
    verdict = determine_verdict(
        replace(pattern(), confidence=0.84),
        event(),
        evidence({"primary_error", "source_snippet", "command_summary"}),
    )

    assert verdict is Verdict.NEEDS_LLM


def test_full_match_returns_needs_llm_for_missing_candidate() -> None:
    result = full_match(
        {"events": [], "commands": []},
        {"event_id": "missing"},
        evidence(),
        patterns=[pattern()],
    )

    assert result.verdict is Verdict.NEEDS_LLM
    assert result.reason == "candidate_event_not_found"


def test_full_match_renders_direct_answer_and_packet_dict() -> None:
    result = full_match(
        {"events": [event()], "commands": [{"id": "C001", "argv_short": "gcc -c foo.c"}]},
        {"event_id": "E001"},
        evidence({"primary_error", "source_snippet", "command_summary"}),
        patterns=[pattern()],
    )

    assert result.verdict is Verdict.DIRECT_TIER2
    assert result.direct_answer == "fix missing_symbol"
    packet = result.as_dict()
    assert packet["verdict"] == "direct_answer"
    assert packet["matched_tier"] == "tier2"


def test_full_match_returns_needs_llm_for_unmatched_patterns() -> None:
    result = full_match(
        {"events": [event(message="different error")], "commands": []},
        {"event_id": "E001"},
        evidence({"primary_error", "source_snippet", "command_summary"}),
        patterns=[pattern()],
    )

    assert result.verdict is Verdict.NEEDS_LLM
    assert result.reason == "no_pattern_match"


def test_loader_rejects_tier2_without_direct_answer(tmp_path: Path) -> None:
    data = {
        "schema_version": 2,
        "patterns": [
            {
                "id": "bad",
                "category": "compile_error",
                "tier": "tier2",
                "event_kinds": ["compiler"],
                "match": {"regex": ["error"]},
                "confidence": 0.86,
                "terminal": True,
            }
        ],
    }
    path = tmp_path / "patterns.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(PatternValidationError, match="direct_answer"):
        load_full_match_patterns(path)
