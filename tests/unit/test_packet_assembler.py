from pathlib import Path

import pytest

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


def test_budget_pool_rejects_bad_usage() -> None:
    pool = BudgetPool()

    with pytest.raises(KeyError):
        pool.report_reserve_used("missing", 1)
    with pytest.raises(ValueError):
        pool.report_reserve_used("primary_error", 1)
    with pytest.raises(ValueError):
        pool.request("compile", -1)


def test_budget_pool_rejects_duplicate_soft_report() -> None:
    pool = BudgetPool()
    pool.report_reserve_used("raw_excerpt", 1)

    with pytest.raises(ValueError, match="already"):
        pool.report_reserve_used("raw_excerpt", 1)


def test_fallback_token_estimate_handles_mixed_text() -> None:
    assert fallback_token_estimate("中文 text /tmp/foo.c") > 1


def test_token_estimator_fallback_truncates_text() -> None:
    estimator = TokenEstimator(use_tiktoken=False)
    text = "word " * 200

    truncated = estimator.truncate_text(text, 20)

    assert "[truncated]" in truncated
    assert len(truncated) < len(text)


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


def test_fallback_raw_context_reads_buildlog_window(tmp_path: Path) -> None:
    scan = scan_data(tmp_path)
    event = scan["events"][0]

    context = fallback_raw_context(event, scan, estimator=TokenEstimator(use_tiktoken=False))

    assert "undeclared identifier" in context["primary_error_excerpt"]
    assert context["current_phase"] == "%build"
    assert context["current_command_summary"]["argv_short"].startswith("gcc")
    assert context["cascade_summary"] == "make cascade: foo.o -> E001"
    assert context["token_estimate"] >= 1


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


def test_assemble_packet_marks_budget_partial(tmp_path: Path) -> None:
    packet = assemble_packet(
        scan_data(tmp_path),
        candidates(),
        Evidence(
            collector="compile",
            level=3,
            granted_budget=2000,
            data={},
            contains=set(),
        ),
        {"verdict": "needs_llm"},
        estimator=TokenEstimator(use_tiktoken=False),
    )

    assert "budget_pool_partial" in packet["degraded_reasons"]


def test_assemble_packet_uses_first_scan_event_without_candidates(tmp_path: Path) -> None:
    packet = assemble_packet(
        scan_data(tmp_path),
        [],
        None,
        None,
        estimator=TokenEstimator(use_tiktoken=False),
    )

    assert packet["primary_error"]["id"] == "E001"


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
