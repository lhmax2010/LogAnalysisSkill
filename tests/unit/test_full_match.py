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


def linker_pattern(**overrides: object) -> FullMatchPattern:
    rule = next(
        item
        for item in load_full_match_patterns()
        if item.id == "linker_undefined_reference_tier2"
    )
    data = {
        "id": rule.id,
        "category": rule.category,
        "tier": rule.tier,
        "event_kinds": rule.event_kinds,
        "regex": rule.regex,
        "required_context": {"severity": ["error"], "tool_in": ["ld"]},
        "negative_patterns": rule.negative_patterns,
        "confidence": rule.confidence,
        "terminal": rule.terminal,
        "direct_answer_tier1": rule.direct_answer_tier1,
        "direct_answer_tier2": rule.direct_answer_tier2,
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


def test_determine_verdict_allows_tier2_when_evidence_degraded_but_complete() -> None:
    verdict = determine_verdict(
        pattern(),
        event(),
        evidence({"primary_error", "source_snippet", "command_summary"}, degraded=True),
    )

    assert verdict is Verdict.DIRECT_TIER2


def test_determine_verdict_needs_llm_when_degraded_tier2_evidence_missing() -> None:
    verdict = determine_verdict(
        pattern(),
        event(),
        evidence({"primary_error"}, degraded=True),
    )

    assert verdict is Verdict.NEEDS_LLM


def test_determine_verdict_keeps_tier1_blocked_when_evidence_degraded() -> None:
    verdict = determine_verdict(
        replace(
            pattern(),
            confidence=0.96,
            direct_answer_tier1=DirectAnswer(
                enabled=True,
                fix_template="tier1",
            ),
            direct_answer_tier2=DirectAnswer(enabled=False),
        ),
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


def test_full_match_renders_tier1_shorthand_direct_answer() -> None:
    scan = {
        "events": [
            {
                "id": "E001",
                "kind": "depsolve",
                "severity": "error",
                "message": "nothing provides libfoo",
                "line_no": 1,
            }
        ],
        "commands": [],
    }

    result = full_match(scan, {"event_id": "E001"}, evidence())

    assert result.verdict is Verdict.DIRECT_TIER1
    assert result.matched_tier == "tier1"
    assert result.direct_answer is not None


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


def test_full_match_records_near_match_below_tier2_threshold() -> None:
    result = full_match(
        {"events": [event()], "commands": [{"id": "C001", "argv_short": "gcc -c foo.c"}]},
        {"event_id": "E001", "confidence": 0.84},
        evidence({"primary_error", "source_snippet", "command_summary"}),
        patterns=[replace(pattern(), confidence=0.84)],
    )

    assert result.verdict is Verdict.NEEDS_LLM
    assert result.pattern_id == "compile_undeclared_identifier_tier2"
    assert result.confidence == 0.84
    packet = result.as_dict()
    assert packet["matched_tier"] is None
    assert packet["matched_patterns"] == [
        {
            "id": "compile_undeclared_identifier_tier2",
            "pattern_id": "compile_undeclared_identifier_tier2",
            "confidence": 0.84,
            "captures": {"identifier": "missing_symbol"},
            "failure_reason": "confidence_below_tier2_threshold",
        }
    ]


def test_full_match_records_near_match_when_context_blocks_direct_match() -> None:
    result = full_match(
        {"events": [event()], "commands": [{"id": "C001", "argv_short": "make -j40"}]},
        {"event_id": "E001", "confidence": 0.84},
        evidence({"primary_error", "source_snippet", "command_summary"}),
        patterns=[
            replace(
                pattern(),
                confidence=0.87,
                required_context={"severity": ["error"], "tool_in": ["gcc"]},
            )
        ],
    )

    assert result.verdict is Verdict.NEEDS_LLM
    packet = result.as_dict()
    assert packet["matched_patterns"][0]["id"] == "compile_undeclared_identifier_tier2"
    assert packet["matched_patterns"][0]["pattern_id"] == "compile_undeclared_identifier_tier2"
    assert packet["matched_patterns"][0]["confidence"] == 0.84
    assert (
        packet["matched_patterns"][0]["failure_reason"]
        == "confidence_below_tier2_threshold"
    )


@pytest.mark.parametrize(
    ("rule", "event_data", "evidence_data", "expected_reason"),
    [
        (
            pattern(),
            event(),
            evidence({"primary_error"}, degraded=True),
            "missing_required_evidence",
        ),
        (
            pattern(),
            event(parent="E000"),
            evidence({"primary_error", "source_snippet", "command_summary"}),
            "event_not_terminal",
        ),
        (
            replace(pattern(), terminal=False),
            event(),
            evidence({"primary_error", "source_snippet", "command_summary"}),
            "pattern_not_terminal",
        ),
        (pattern(), event(), evidence({"primary_error"}), "missing_required_evidence"),
    ],
)
def test_full_match_records_needs_llm_failure_reasons(
    rule: FullMatchPattern,
    event_data: dict[str, object],
    evidence_data: Evidence,
    expected_reason: str,
) -> None:
    result = full_match(
        {"events": [event_data], "commands": [{"id": "C001", "argv_short": "gcc -c foo.c"}]},
        {"event_id": "E001", "confidence": 0.90},
        evidence_data,
        patterns=[replace(rule, confidence=0.87)],
    )

    assert result.verdict is Verdict.NEEDS_LLM
    assert result.as_dict()["matched_patterns"][0]["failure_reason"] == expected_reason


def test_full_match_records_required_context_near_match_with_high_confidence() -> None:
    result = full_match(
        {"events": [event()], "commands": [{"id": "C001", "argv_short": "make -j40"}]},
        {"event_id": "E001", "confidence": 0.90},
        evidence({"primary_error", "source_snippet", "command_summary"}),
        patterns=[
            replace(
                pattern(),
                confidence=0.87,
                required_context={"severity": ["error"], "tool_in": ["gcc"]},
            )
        ],
    )

    assert result.verdict is Verdict.NEEDS_LLM
    assert result.as_dict()["matched_patterns"][0]["failure_reason"] == "required_context_not_met"


def test_full_match_allows_linker_undef_tool_context_mismatch() -> None:
    linker_event = event(
        kind="linker_undef",
        message="undefined reference to `nonexistent_helper_xxxyzz'",
    )

    result = full_match(
        {"events": [linker_event], "commands": [{"id": "C001", "argv_short": "make -j40"}]},
        {"event_id": "E001", "confidence": 0.90},
        evidence({"primary_error", "link_command", "symbol_context"}),
        patterns=[linker_pattern()],
    )

    assert result.verdict is Verdict.DIRECT_TIER2
    assert result.pattern_id == "linker_undefined_reference_tier2"
    assert result.matched_tier == "tier2"


def test_full_match_keeps_compile_tool_context_mismatch_blocking() -> None:
    result = full_match(
        {"events": [event()], "commands": [{"id": "C001", "argv_short": "make -j40"}]},
        {"event_id": "E001", "confidence": 0.90},
        evidence({"primary_error", "source_snippet", "command_summary"}),
        patterns=[
            replace(
                pattern(),
                confidence=0.87,
                required_context={"severity": ["error"], "tool_in": ["gcc"]},
            )
        ],
    )

    assert result.verdict is Verdict.NEEDS_LLM
    assert result.as_dict()["matched_patterns"][0]["failure_reason"] == "required_context_not_met"


def test_full_match_keeps_linker_undef_non_tool_context_blocking() -> None:
    linker_event = event(
        kind="linker_undef",
        severity="warning",
        message="undefined reference to `nonexistent_helper_xxxyzz'",
    )

    result = full_match(
        {"events": [linker_event], "commands": [{"id": "C001", "argv_short": "make -j40"}]},
        {"event_id": "E001", "confidence": 0.90},
        evidence({"primary_error", "link_command", "symbol_context"}),
        patterns=[linker_pattern()],
    )

    assert result.verdict is Verdict.NEEDS_LLM
    assert result.as_dict()["matched_patterns"][0]["failure_reason"] == "required_context_not_met"


def test_full_match_uses_pattern_confidence_when_candidate_confidence_is_invalid() -> None:
    result = full_match(
        {"events": [event()], "commands": [{"id": "C001", "argv_short": "gcc -c foo.c"}]},
        {"event_id": "E001", "confidence": "bad"},
        evidence({"primary_error", "source_snippet", "command_summary"}),
        patterns=[replace(pattern(), confidence=0.84)],
    )

    assert result.verdict is Verdict.NEEDS_LLM
    assert result.confidence == 0.84


def test_full_match_keeps_first_needs_llm_match() -> None:
    result = full_match(
        {"events": [event()], "commands": []},
        {"event_id": "E001"},
        evidence({"primary_error"}),
        patterns=[pattern(), replace(pattern(), event_kinds=("linker_undef",))],
    )

    assert result.verdict is Verdict.NEEDS_LLM
    assert result.pattern_id == "compile_undeclared_identifier_tier2"
    assert result.reason == "matched_pattern_needs_llm"


def test_full_match_returns_needs_llm_for_unmatched_patterns() -> None:
    result = full_match(
        {"events": [event(message="different error")], "commands": []},
        {"event_id": "E001"},
        evidence({"primary_error", "source_snippet", "command_summary"}),
        patterns=[pattern()],
    )

    assert result.verdict is Verdict.NEEDS_LLM
    assert result.reason == "no_pattern_match"


def test_context_checks_phase_tool_and_warning_block() -> None:
    rule = replace(
        pattern(),
        required_context={
            "phase": ["%build"],
            "severity": ["error"],
            "tool_in": ["gcc"],
            "not_in_warning_block": True,
        },
    )
    commands = {"C001": {"id": "C001", "argv_short": "gcc -c foo.c"}}
    warning_events = [
        {"id": "E000", "severity": "warning", "message": "warning: earlier", "line_no": 9},
        event(phase="%build"),
    ]

    assert match_pattern(rule, event(phase="%install"), commands=commands) is None
    assert match_pattern(rule, event(phase="%build"), commands={}) is None
    assert match_pattern(rule, event(phase="%build"), warning_events, commands) is None

    captures = match_pattern(rule, event(phase="%build"), [event(phase="%build")], commands)
    assert captures == {"identifier": "missing_symbol"}


def test_context_tool_handles_bad_or_empty_argv() -> None:
    rule = replace(pattern(), required_context={"tool_in": ["gcc"]})

    assert match_pattern(rule, event(command_id=None), commands={}) is None
    assert match_pattern(rule, event(), commands={"C001": {"argv_short": "'unterminated"}}) is None
    assert match_pattern(rule, event(), commands={"C001": {"argv_short": ""}}) is None


def test_explicit_is_terminal_false_blocks_direct_answer() -> None:
    verdict = determine_verdict(
        pattern(),
        event(is_terminal=False),
        evidence({"primary_error", "source_snippet", "command_summary"}),
    )

    assert verdict is Verdict.NEEDS_LLM


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


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ([], "must be a mapping"),
        ({"schema_version": 1, "patterns": []}, "schema_version"),
        ({"schema_version": 2, "patterns": {}}, "patterns must be a list"),
        ({"schema_version": 2, "patterns": ["bad"]}, "each pattern"),
    ],
)
def test_loader_rejects_invalid_library_shapes(
    tmp_path: Path,
    data: object,
    message: str,
) -> None:
    path = tmp_path / "patterns.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(PatternValidationError, match=message):
        load_full_match_patterns(path)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda item: item.update({"match": []}), "match must be a mapping"),
        (lambda item: item.update({"tier": "tier3"}), "tier must be"),
        (lambda item: item["match"].update({"regex": []}), "match.regex"),
        (lambda item: item.update({"direct_answer_tier2": "bad"}), "must be a mapping"),
        (
            lambda item: item.update(
                {"direct_answer_tier2": {"enabled": True, "evidence_required": "bad"}}
            ),
            "evidence_required",
        ),
        (
            lambda item: item.update({"direct_answer_tier2": {"enabled": True}}),
            "fix_template",
        ),
    ],
)
def test_loader_rejects_invalid_pattern_shapes(
    tmp_path: Path,
    mutate: object,
    message: str,
) -> None:
    item = {
        "id": "bad",
        "category": "compile_error",
        "tier": "tier2",
        "event_kinds": ["compiler"],
        "match": {"regex": ["error"]},
        "confidence": 0.86,
        "terminal": True,
        "direct_answer_tier2": {
            "enabled": True,
            "evidence_required": [],
            "fix_template": "fix",
        },
    }
    mutate(item)  # type: ignore[operator]
    path = tmp_path / "patterns.yaml"
    path.write_text(yaml.safe_dump({"schema_version": 2, "patterns": [item]}), encoding="utf-8")

    with pytest.raises(PatternValidationError, match=message):
        load_full_match_patterns(path)
