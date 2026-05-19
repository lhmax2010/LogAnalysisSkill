from pathlib import Path

import pytest

import gbs_analyzer.packet_assembler as packet_assembler
from gbs_analyzer.evidence import Evidence
from gbs_analyzer.full_match import FullMatchResult, Verdict
from gbs_analyzer.packet_assembler import (
    BudgetPool,
    MinimalRedactor,
    TokenEstimator,
    assemble_packet,
    fallback_raw_context,
    fallback_token_estimate,
    format_cascade_summary,
    render_packet_markdown,
)
from gbs_analyzer.rank_causes import RankResult, RootCauseCandidate
from gbs_analyzer.scan_and_extract import (
    CommandRecord,
    DiagnosticEvent,
    ScanResult,
)
from gbs_analyzer.tracing import setup_tracing


def scan_data(tmp_path: Path) -> dict[str, object]:
    buildlog = tmp_path / "buildlog"
    buildlog.write_text(
        "\n".join(
            [
                "+ %build",
                "+ gcc -c /home/linhao/work/src/foo.c",
                "src/foo.c:5:3: error: use of undeclared identifier 'missing_symbol'",
                "make: *** [foo.o] Error 1",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "schema_version": "scan_result/v1",
        "buildlog_path": str(buildlog),
        "buildlog_size_bytes": buildlog.stat().st_size,
        "is_gzip": False,
        "failed_phase": "%build",
        "phases": [{"name": "%build", "line_no": 1}],
        "commands": [
            {
                "id": "C001",
                "phase": "%build",
                "argv_short": "gcc -c /home/linhao/work/src/foo.c",
            }
        ],
        "events": [
            {
                "id": "E001",
                "kind": "compiler",
                "severity": "error",
                "message": "use of undeclared identifier 'missing_symbol'",
                "line_no": 3,
                "raw_offset": 20,
                "phase": "%build",
                "command_id": "C001",
                "file": "/home/linhao/work/src/foo.c",
                "line": 5,
            },
            {
                "id": "E002",
                "kind": "make_cascade",
                "severity": "error",
                "message": "make: *** [foo.o] Error 1",
                "line_no": 4,
                "raw_offset": 80,
                "phase": "%build",
                "command_id": "C001",
                "target": "foo.o",
                "parent": "E001",
            },
        ],
        "degraded_reasons": [],
    }


def candidates() -> list[dict[str, object]]:
    return [
        {
            "rank": 1,
            "event_id": "E001",
            "kind": "compiler",
            "semantic_class": "undeclared_identifier",
            "confidence": 0.92,
            "confidence_band": "high",
            "summary": "compiler undeclared_identifier",
        }
    ]


def rank_result() -> RankResult:
    return RankResult(
        root_cause_candidates=[
            RootCauseCandidate(
                rank=1,
                event_id="E001",
                kind="compiler",
                semantic_class="undeclared_identifier",
                confidence=0.92,
                confidence_band="high",
                confidence_reason=[],
                is_terminal=True,
                summary="compiler undeclared_identifier",
            )
        ]
    )


def compile_evidence(*, degraded: bool = False) -> Evidence:
    return Evidence(
        collector="compile",
        level=3,
        granted_budget=600,
        data={
            "primary_error": {"id": "E001"},
            "command_summary": {"argv_short": "gcc -c /home/linhao/work/src/foo.c"},
            "source_snippet": {"path": "/home/linhao/work/src/foo.c", "text": "boom"},
        },
        contains={"primary_error", "command_summary", "source_snippet"},
        degraded=degraded,
        warnings=["source_file_unavailable"] if degraded else [],
    )


def tier2_result() -> FullMatchResult:
    return FullMatchResult(
        verdict=Verdict.DIRECT_TIER2,
        pattern_id="compile_undeclared_identifier_tier2",
        matched_tier="tier2",
        direct_answer="检查 missing_symbol 声明。",
        captures={"identifier": "missing_symbol"},
        confidence=0.86,
    )


def test_budget_pool_initial_state_conserves_total() -> None:
    pool = BudgetPool()

    assert pool.hard_reserved == 400
    assert pool.soft_reserved == 350
    assert pool.evidence_pool == 650
    assert pool.conservation_total() == 1400
    assert pool.conservation_ok()


def test_budget_pool_reclaims_soft_reserve() -> None:
    pool = BudgetPool()

    reclaimed = pool.report_reserve_used("top_k_text_summaries", 80)

    assert reclaimed == 120
    assert pool.evidence_pool == 770
    assert pool.reclaimed == 120
    assert pool.conservation_ok()


def test_budget_pool_clamps_soft_reserve_usage() -> None:
    pool = BudgetPool()

    assert pool.report_reserve_used("cascade_summary", 999) == 0
    assert pool.report_reserve_used("raw_excerpt", -10) == 100
    assert pool.conservation_ok()


def test_budget_pool_request_grants_available_budget() -> None:
    pool = BudgetPool()
    pool.report_reserve_used("raw_excerpt", 0)

    granted = pool.request("compile", 900)

    assert granted == 750
    assert pool.grants == {"compile": 750}
    assert pool.evidence_pool == 0
    assert pool.conservation_ok()


def test_budget_pool_clears_partial_after_cumulative_grants() -> None:
    pool = BudgetPool()

    first_grant = pool.request("link", 650, preferred=900)

    assert first_grant == 650
    assert pool.is_partial("link") is True

    pool.report_reserve_used("raw_excerpt", 0)
    pool.report_reserve_used("cascade_summary", 0)
    pool.report_reserve_used("top_k_text_summaries", 0)
    second_grant = pool.request("link", 250, preferred=900)

    assert second_grant == 250
    assert pool.grants["link"] == 900
    assert pool.is_partial("link") is False
    assert "link" not in pool.as_dict()["partial_grants"]
    assert pool.conservation_ok()


def test_budget_pool_rejects_bad_usage() -> None:
    pool = BudgetPool()

    with pytest.raises(KeyError):
        pool.report_reserve_used("missing", 1)
    with pytest.raises(ValueError):
        pool.report_reserve_used("primary_error", 1)
    with pytest.raises(ValueError):
        pool.request("compile", -1)
    with pytest.raises(ValueError):
        pool.request("compile", 1, preferred=-1)


def test_budget_pool_rejects_over_reserved_total() -> None:
    with pytest.raises(ValueError, match="reserved budget"):
        BudgetPool(total=100)


def test_budget_pool_rejects_duplicate_soft_report() -> None:
    pool = BudgetPool()
    pool.report_reserve_used("raw_excerpt", 1)

    with pytest.raises(ValueError, match="already"):
        pool.report_reserve_used("raw_excerpt", 1)


def test_budget_pool_reclaimed_ignores_non_soft_entries() -> None:
    pool = BudgetPool()
    pool.soft_used["primary_error"] = 10

    assert pool.reclaimed == 0


def test_fallback_token_estimate_handles_mixed_text() -> None:
    assert fallback_token_estimate("中文 text /tmp/foo.c") > 1


def test_token_estimator_uses_tiktoken_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeEncoder:
        def encode(self, text: str) -> list[str]:
            return text.split()

    class FakeTiktoken:
        @staticmethod
        def get_encoding(name: str) -> FakeEncoder:
            assert name == "cl100k_base"
            return FakeEncoder()

    monkeypatch.setattr(packet_assembler, "tiktoken", FakeTiktoken)

    estimator = TokenEstimator()

    assert estimator.method == "tiktoken"
    assert estimator.estimate_text("one two three") == 3


def test_token_estimator_falls_back_when_tiktoken_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(packet_assembler, "tiktoken", None)

    estimator = TokenEstimator()

    assert estimator.method == "fallback"
    assert estimator.estimate_text("one two") >= 1


def test_token_estimator_fallback_truncates_text() -> None:
    estimator = TokenEstimator(use_tiktoken=False)
    text = "word " * 200

    truncated = estimator.truncate_text(text, 20)

    assert "[truncated]" in truncated
    assert len(truncated) < len(text)


def test_token_estimator_truncate_handles_tiny_budgets() -> None:
    estimator = TokenEstimator(use_tiktoken=False)

    assert estimator.truncate_text("anything", 0) == ""
    assert "[truncated]" in estimator.truncate_text("word " * 200, 1)


def test_token_estimator_estimates_objects() -> None:
    estimator = TokenEstimator(use_tiktoken=False)

    assert estimator.estimate_obj({"hello": "world"}) >= 1
    assert estimator.method == "fallback"


def test_redactor_redacts_workspace_home_and_host() -> None:
    redactor = MinimalRedactor(workspace_root="/home/linhao/work", hostname="builder01")

    redacted = redactor.redact_for_llm("/home/linhao/work/src/foo.c on builder01")

    assert "<WORKSPACE>/src/foo.c" in redacted
    assert "<HOST>" in redacted


def test_redactor_storage_preserves_raw_paths() -> None:
    packet = {"path": "/home/linhao/work/src/foo.c"}
    redactor = MinimalRedactor(workspace_root="/home/linhao/work")

    assert redactor.redact_for_storage(packet) is packet


def test_redactor_recurses_for_llm_objects() -> None:
    redactor = MinimalRedactor(workspace_root="/home/linhao/work")
    obj = {"items": ["/home/linhao/work/src/foo.c"]}

    assert redactor.redact_obj_for_llm(obj) == {"items": ["<WORKSPACE>/src/foo.c"]}


def test_format_cascade_summary() -> None:
    assert format_cascade_summary(scan_data(Path("/tmp"))) == "make cascade: foo.o -> E001"


def test_format_cascade_summary_returns_empty_without_cascades(tmp_path: Path) -> None:
    scan = scan_data(tmp_path)
    scan["events"] = [scan["events"][0]]

    assert format_cascade_summary(scan) == ""


def test_fallback_raw_context_reads_buildlog_window(tmp_path: Path) -> None:
    scan = scan_data(tmp_path)
    event = scan["events"][0]

    context = fallback_raw_context(event, scan, estimator=TokenEstimator(use_tiktoken=False))

    assert "undeclared identifier" in context["primary_error_excerpt"]
    assert context["current_phase"] == "%build"
    assert context["current_command_summary"]["argv_short"].startswith("gcc")
    assert context["cascade_summary"] == "make cascade: foo.o -> E001"
    assert context["token_estimate"] >= 1


def test_fallback_raw_context_handles_missing_line_and_command(tmp_path: Path) -> None:
    scan = scan_data(tmp_path)
    event = dict(scan["events"][0])
    event["line_no"] = "unknown"
    event["command_id"] = "missing"

    context = fallback_raw_context(event, scan, estimator=TokenEstimator(use_tiktoken=False))

    assert "undeclared identifier" in context["primary_error_excerpt"]
    assert context["current_command_summary"] is None


def test_fallback_raw_context_uses_event_message_when_log_missing() -> None:
    scan = scan_data(Path("/tmp"))
    scan["buildlog_path"] = "/tmp/does-not-exist"
    event = scan["events"][0]

    context = fallback_raw_context(event, scan, estimator=TokenEstimator(use_tiktoken=False))

    assert context["primary_error_excerpt"] == event["message"]


def test_assemble_packet_direct_answer_preserves_storage_paths(tmp_path: Path) -> None:
    packet = assemble_packet(
        scan_data(tmp_path),
        rank_result(),
        compile_evidence(),
        tier2_result(),
        package="demo",
        arch="x86_64",
        profile="mobile",
        estimator=TokenEstimator(use_tiktoken=False),
        redactor=MinimalRedactor(workspace_root="/home/linhao/work"),
    )

    assert packet["verdict"] == "direct_answer"
    assert packet["via"] == "full_path"
    assert packet["direct_answer"] == "检查 missing_symbol 声明。"
    assert packet["matched_tier"] == "tier2"
    assert packet["prompt"] is None
    assert packet["package"] == "demo"
    assert packet["evidence"]["source_snippet"]["path"] == "/home/linhao/work/src/foo.c"
    assert packet["token_budget"]["conservation_ok"] is True


def test_assemble_packet_accepts_scan_rank_evidence_and_legacy_match_dicts(
    tmp_path: Path,
) -> None:
    scan = scan_data(tmp_path)
    scan_result = ScanResult(
        schema_version="scan_result/v1",
        buildlog_path=str(scan["buildlog_path"]),
        buildlog_size_bytes=int(scan["buildlog_size_bytes"]),
        is_gzip=False,
        failed_phase="%build",
        phases=[{"name": "%build", "line_no": 1}],
        commands=[
            CommandRecord(
                id="C001",
                line_no=2,
                raw_offset=10,
                phase="%build",
                argv_short="gcc -c /home/linhao/work/src/foo.c",
                argv_full=None,
                rsp_expanded={},
                command_degraded=False,
            )
        ],
        events=[
            DiagnosticEvent(
                id="E001",
                kind="compiler",
                severity="error",
                message="use of undeclared identifier 'missing_symbol'",
                line_no=3,
                raw_offset=20,
                phase="%build",
                command_id="C001",
                file="/home/linhao/work/src/foo.c",
                line=5,
            )
        ],
    )

    packet = assemble_packet(
        scan_result,
        {"root_cause_candidates": candidates()},
        compile_evidence().as_dict(),
        {
            "full_match_verdict": Verdict.DIRECT_TIER2.value,
            "pattern_id": "compile_undeclared_identifier_tier2",
            "matched_tier": "tier2",
            "direct_answer": "检查 missing_symbol 声明。",
        },
        estimator=TokenEstimator(use_tiktoken=False),
    )

    assert packet["verdict"] == "direct_answer"
    assert packet["matched_patterns"] == ["compile_undeclared_identifier_tier2"]


def test_assemble_packet_preserves_near_matched_pattern_details(tmp_path: Path) -> None:
    near_match = {
        "pattern_id": "linker_undefined_reference_tier2",
        "confidence": 0.84,
        "captures": {"symbol": "missing_helper"},
        "failure_reason": "confidence_below_tier2_threshold",
    }

    packet = assemble_packet(
        scan_data(tmp_path),
        candidates(),
        compile_evidence().as_dict(),
        {
            "verdict": "needs_llm",
            "matched_patterns": [near_match],
            "pattern_id": "linker_undefined_reference_tier2",
        },
        estimator=TokenEstimator(use_tiktoken=False),
    )

    assert packet["verdict"] == "needs_llm"
    assert packet["matched_patterns"] == [near_match]


def test_assemble_packet_needs_llm_prompt_is_redacted(tmp_path: Path) -> None:
    packet = assemble_packet(
        scan_data(tmp_path),
        candidates(),
        compile_evidence(),
        {"verdict": "needs_llm"},
        estimator=TokenEstimator(use_tiktoken=False),
        redactor=MinimalRedactor(workspace_root="/home/linhao/work"),
    )

    assert packet["verdict"] == "needs_llm"
    assert packet["prompt"] is not None
    assert "<WORKSPACE>" in packet["prompt"]
    assert "/home/linhao/work" not in packet["prompt"]


def test_assemble_packet_uses_fallback_when_evidence_missing(tmp_path: Path) -> None:
    packet = assemble_packet(
        scan_data(tmp_path),
        candidates(),
        None,
        None,
        estimator=TokenEstimator(use_tiktoken=False),
    )

    assert packet["verdict"] == "needs_llm"
    assert "fallback_context" in packet["evidence"]
    assert "fallback_raw_context_used" in packet["degraded_reasons"]
    assert packet["degraded"] is True
    assert packet["token_budget"]["conservation_ok"] is True


def test_assemble_packet_truncates_to_final_token_budget(tmp_path: Path) -> None:
    scan = scan_data(tmp_path)
    buildlog = Path(str(scan["buildlog_path"]))
    buildlog.write_text(
        "\n".join(f"log window line {index} " + ("word " * 80) for index in range(1, 90)),
        encoding="utf-8",
    )
    event = scan["events"][0]
    assert isinstance(event, dict)
    event["line_no"] = 45

    packet = assemble_packet(
        scan,
        candidates(),
        None,
        None,
        estimator=TokenEstimator(use_tiktoken=False),
        max_tokens=600,
    )

    assert packet["token_budget"]["used"] <= 600
    assert packet["token_budget"]["limit_with_prompt"] == 600
    assert packet["token_budget"]["conservation_ok"] is True
    assert packet["degraded"] is True
    assert "packet_truncated_to_token_budget" in packet["degraded_reasons"]


def test_assemble_packet_truncates_source_snippet_when_needed(tmp_path: Path) -> None:
    evidence = compile_evidence()
    evidence.data["source_snippet"]["text"] = "source line " + ("token " * 500)

    packet = assemble_packet(
        scan_data(tmp_path),
        candidates(),
        evidence,
        {"verdict": "needs_llm"},
        estimator=TokenEstimator(use_tiktoken=False),
        max_tokens=1200,
    )

    assert packet["token_budget"]["used"] <= 1200
    assert packet["token_budget"]["conservation_ok"] is True
    assert "packet_truncated_to_token_budget" in packet["degraded_reasons"]
    assert "[truncated]" in packet["evidence"]["source_snippet"]["text"]


def test_final_token_guard_helper_edges() -> None:
    estimator = TokenEstimator(use_tiktoken=False)
    packet = {
        "verdict": "needs_llm",
        "prompt": None,
        "evidence": {"fallback_context": {"primary_error_excerpt": "short"}},
        "root_cause_candidates": [{"rank": 1}, {"rank": 2}],
        "cascade_summary": "cascade " * 100,
        "token_budget": {},
        "degraded_reasons": ["packet_truncated_to_token_budget"],
    }

    assert packet_assembler._limit_fallback_lines(packet, "missing", max_lines=1) is False
    assert packet_assembler._clear_fallback_field(packet, "missing") is False
    assert (
        packet_assembler._truncate_fallback_text(
            {"evidence": {}},
            estimator,
            max_tokens=10,
        )
        is False
    )
    assert (
        packet_assembler._truncate_snippet_texts(
            {"evidence": "bad"},
            estimator,
            max_tokens=10,
        )
        is False
    )
    assert packet_assembler._clear_cascade_summary(packet, estimator) is True
    assert packet["cascade_summary"] == ""
    assert packet_assembler._keep_top_candidate(packet) is True
    assert packet["root_cause_candidates"] == [{"rank": 1}]


def test_final_token_guard_helper_mutation_edges() -> None:
    estimator = TokenEstimator(use_tiktoken=False)
    packet = {
        "evidence": {
            "fallback_context": {
                "extra_log_window": "extra",
                "cascade_summary": "cascade " * 100,
            }
        },
        "root_cause_candidates": [{"rank": 1}],
    }
    nested = [{"text": "snippet " * 200}]

    assert packet_assembler._clear_fallback_field(packet, "extra_log_window") is True
    assert packet["evidence"]["fallback_context"]["extra_log_window"] == ""
    assert packet_assembler._clear_cascade_summary(packet, estimator) is True
    assert packet["evidence"]["fallback_context"]["cascade_summary"] == ""
    assert packet_assembler._truncate_text_fields(
        nested,
        estimator,
        max_tokens=10,
    )
    assert "[truncated]" in nested[0]["text"]
    assert packet_assembler._keep_top_candidate(packet) is False


def test_final_token_guard_truncates_extra_log_window() -> None:
    packet = {
        "verdict": "needs_llm",
        "primary_error": {"message": "boom"},
        "root_cause_candidates": [{"rank": 1}],
        "evidence": {
            "fallback_context": {
                "primary_error_excerpt": "error",
                "extra_log_window": "\n".join(f"extra {index}" for index in range(60)),
            }
        },
        "cascade_summary": "",
        "token_budget": {},
        "degraded_reasons": [],
    }

    packet_assembler._enforce_final_token_limit(
        packet,
        max_tokens=250,
        estimator=TokenEstimator(use_tiktoken=False),
        redactor=MinimalRedactor(),
    )

    assert packet["token_budget"]["used"] <= 250
    assert "packet_truncated_to_token_budget" in packet["degraded_reasons"]
    assert "[truncated]" in packet["evidence"]["fallback_context"]["extra_log_window"]


def test_final_token_guard_uses_wrapper_limit_not_evidence_pool() -> None:
    estimator = TokenEstimator(use_tiktoken=False)
    packet = {
        "verdict": "direct_answer",
        "primary_error": {"message": "boom"},
        "root_cause_candidates": [{"rank": 1}],
        "evidence": {"source_snippets": [{"file": "foo.c", "text": ""}]},
        "cascade_summary": "",
        "token_budget": {},
        "degraded": False,
        "degraded_reasons": [],
    }
    while estimator.estimate_obj(packet) <= 1400:
        packet["evidence"]["source_snippets"][0]["text"] += "context token " * 20
    assert estimator.estimate_obj(packet) < 1800

    packet_assembler._enforce_final_token_limit(
        packet,
        max_tokens=1800,
        estimator=estimator,
        redactor=MinimalRedactor(),
    )

    assert packet["token_budget"]["used"] < 1800
    assert "packet_truncated_to_token_budget" not in packet["degraded_reasons"]
    assert packet["degraded"] is False


def test_final_token_guard_reestimates_until_under_max_tokens() -> None:
    estimator = TokenEstimator(use_tiktoken=False)
    packet = {
        "verdict": "direct_answer",
        "primary_error": {"message": "boom"},
        "root_cause_candidates": [{"rank": 1}],
        "evidence": {
            "source_snippets": [
                {"file": "foo.c", "line_start": 1, "line_end": 999, "text": "line\n" * 5000}
            ]
        },
        "cascade_summary": "make cascade: " + ("foo.o -> E001; " * 200),
        "token_budget": {"conservation_ok": True},
        "degraded": False,
        "degraded_reasons": [],
    }
    assert estimator.estimate_obj(packet) > 1800

    packet_assembler._enforce_final_token_limit(
        packet,
        max_tokens=1800,
        estimator=estimator,
        redactor=MinimalRedactor(),
    )

    assert packet["token_budget"]["used"] <= 1800
    assert packet["token_budget"]["conservation_ok"] is True
    assert "packet_truncated_to_token_budget" in packet["degraded_reasons"]
    assert "packet_could_not_truncate_to_budget" not in packet["degraded_reasons"]


def test_final_token_guard_marks_unable_when_safe_fields_exhausted() -> None:
    estimator = TokenEstimator(use_tiktoken=False)
    packet = {
        "verdict": "direct_answer",
        "primary_error": {"message": "root " * 2000},
        "root_cause_candidates": [{"rank": 1}],
        "evidence": {"metadata_only": {"path": "foo.c"}},
        "cascade_summary": "",
        "token_budget": {},
        "degraded": False,
        "degraded_reasons": [],
    }

    packet_assembler._enforce_final_token_limit(
        packet,
        max_tokens=50,
        estimator=estimator,
        redactor=MinimalRedactor(),
    )

    assert packet["token_budget"]["used"] > 50
    assert "packet_truncated_to_token_budget" in packet["degraded_reasons"]
    assert "packet_could_not_truncate_to_budget" in packet["degraded_reasons"]


def test_prompt_helpers_keep_prompt_compact_and_path_oriented() -> None:
    assert packet_assembler._first_prompt_candidate("bad") == {}
    assert packet_assembler._first_prompt_candidate(["bad"]) == {}
    assert packet_assembler._first_prompt_candidate(
        [{"rank": 1, "event_id": "E001", "summary": "long"}]
    ) == {"rank": 1, "event_id": "E001"}

    evidence = {
        "source_snippet": {"path": "/home/linhao/work/foo.c", "text": "boom"},
        "nested": [{"file": "/home/linhao/work/foo.c"}, {"file": "/tmp/bar.c"}],
    }
    assert packet_assembler._prompt_evidence_paths(evidence) == [
        "/home/linhao/work/foo.c",
        "/tmp/bar.c",
    ]
    assert packet_assembler._compact_prompt_mapping(
        {"message": "boom", "text": "long"},
        include_message=False,
    ) == {"text": "[omitted]"}
    assert packet_assembler._compact_prompt_mapping("raw") == "raw"


def test_truncate_prompt_to_fit_handles_empty_and_large_prompt() -> None:
    estimator = TokenEstimator(use_tiktoken=False)
    assert (
        packet_assembler._truncate_prompt_to_fit(
            {"prompt": None},
            estimator,
            max_tokens=50,
        )
        is False
    )
    packet = {
        "prompt": "prompt word " * 200,
        "primary_error": {"message": "boom"},
        "token_budget": {},
    }
    original = estimator.estimate_obj(packet)

    assert (
        packet_assembler._truncate_prompt_to_fit(
            packet,
            estimator,
            max_tokens=120,
        )
        is True
    )
    assert estimator.estimate_obj(packet) < original
    assert "[truncated]" in packet["prompt"]


def test_assemble_packet_marks_degraded_evidence_warning(tmp_path: Path) -> None:
    packet = assemble_packet(
        scan_data(tmp_path),
        candidates(),
        compile_evidence(degraded=True),
        {"verdict": "needs_llm"},
        estimator=TokenEstimator(use_tiktoken=False),
    )

    assert packet["degraded"] is True
    assert "source_file_unavailable" in packet["degraded_reasons"]


def test_assemble_packet_does_not_promote_reasonless_evidence_degraded(
    tmp_path: Path,
) -> None:
    evidence_data = compile_evidence(degraded=True).as_dict()
    evidence_data["warnings"] = []

    packet = assemble_packet(
        scan_data(tmp_path),
        candidates(),
        evidence_data,
        {"verdict": "needs_llm"},
        estimator=TokenEstimator(use_tiktoken=False),
    )

    assert packet["degraded"] is False
    assert packet["degraded_reasons"] == []


def test_assemble_packet_marks_budget_partial(tmp_path: Path) -> None:
    evidence_data = Evidence(
        collector="compile",
        level=2,
        granted_budget=600,
        data={},
        contains=set(),
    ).as_dict()
    evidence_data["level_preferred"] = 3

    packet = assemble_packet(
        scan_data(tmp_path),
        candidates(),
        evidence_data,
        {"verdict": "needs_llm"},
        estimator=TokenEstimator(use_tiktoken=False),
    )

    assert "budget_pool_partial" in packet["degraded_reasons"]


def test_assemble_packet_does_not_mark_partial_when_level_reaches_preferred(
    tmp_path: Path,
) -> None:
    evidence_data = Evidence(
        collector="compile",
        level=3,
        granted_budget=2000,
        data={},
        contains=set(),
    ).as_dict()
    evidence_data["level_preferred"] = 3

    packet = assemble_packet(
        scan_data(tmp_path),
        candidates(),
        evidence_data,
        {"verdict": "needs_llm"},
        estimator=TokenEstimator(use_tiktoken=False),
    )

    assert "budget_pool_partial" not in packet["degraded_reasons"]


def test_assemble_packet_uses_first_scan_event_without_candidates(tmp_path: Path) -> None:
    packet = assemble_packet(
        scan_data(tmp_path),
        [],
        None,
        None,
        estimator=TokenEstimator(use_tiktoken=False),
    )

    assert packet["primary_error"]["id"] == "E001"


def test_assemble_packet_uses_empty_primary_error_when_no_events(tmp_path: Path) -> None:
    scan = scan_data(tmp_path)
    scan["events"] = []

    packet = assemble_packet(
        scan,
        [{"event_id": "missing"}],
        None,
        {"full_match_verdict": "unknown"},
        estimator=TokenEstimator(use_tiktoken=False),
    )

    assert packet["primary_error"] == {}
    assert packet["verdict"] == "needs_llm"


def test_render_packet_markdown_redacts_llm_view(tmp_path: Path) -> None:
    packet = assemble_packet(
        scan_data(tmp_path),
        candidates(),
        compile_evidence(),
        {"verdict": "needs_llm"},
        estimator=TokenEstimator(use_tiktoken=False),
        redactor=MinimalRedactor(workspace_root="/home/linhao/work"),
    )

    markdown = render_packet_markdown(
        packet,
        redactor=MinimalRedactor(workspace_root="/home/linhao/work"),
    )

    assert "# GBS Build Failure Analysis" in markdown
    assert "<WORKSPACE>" in markdown
    assert "/home/linhao/work" not in markdown


def test_render_packet_markdown_includes_prompt_when_present(tmp_path: Path) -> None:
    packet = assemble_packet(
        scan_data(tmp_path),
        candidates(),
        compile_evidence(),
        {"verdict": "needs_llm"},
        estimator=TokenEstimator(use_tiktoken=False),
    )

    markdown = render_packet_markdown(packet)

    assert "## Prompt" in markdown


def test_assemble_packet_emits_trace(tmp_path: Path) -> None:
    with setup_tracing(tmp_path / "trace", trace=True) as trace_logger:
        assemble_packet(
            scan_data(tmp_path),
            candidates(),
            compile_evidence(),
            {"verdict": "needs_llm"},
            estimator=TokenEstimator(use_tiktoken=False),
            trace_logger=trace_logger,
        )

    trace_text = (tmp_path / "trace" / "trace.log").read_text(encoding="utf-8")
    assert "L5_assembler packet_assembled" in trace_text
