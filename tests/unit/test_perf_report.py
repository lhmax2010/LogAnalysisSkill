from pathlib import Path

from gbs_analyzer.packet_assembler import TokenEstimator
from gbs_analyzer.tracing.perf_report import (
    PERF_LAYER_KEYS,
    build_perf_report,
    estimate_buildlog_tokens,
    token_sections,
)


def packet() -> dict[str, object]:
    return {
        "verdict": "needs_llm",
        "via": "full_path",
        "matched_tier": None,
        "root_cause_candidates": [{"rank": 1, "summary": "compiler error"}],
        "primary_error": {"message": "boom"},
        "evidence": {
            "source_snippet": {"text": "int main(void) { boom(); }"},
            "command_summary": {"argv_short": "gcc -c foo.c"},
            "header_declarations": [{"path": "foo.h"}],
        },
        "prompt": "Please analyze",
        "token_budget": {
            "limit_with_prompt": 1800,
            "estimate_method": "fallback",
            "used": 320,
            "evidence_pool_initial": 650,
            "reclaimed": 120,
            "evidence_pool_final": 170,
        },
        "degraded": True,
        "degraded_reasons": ["budget_pool_partial"],
    }


def test_estimate_buildlog_tokens_uses_size_heuristic() -> None:
    assert estimate_buildlog_tokens(0) == 1
    assert estimate_buildlog_tokens(4000) == 1000


def test_token_sections_returns_stable_keys() -> None:
    sections = token_sections(packet(), TokenEstimator(use_tiktoken=False), packet_tokens=320)

    assert set(sections) == {
        "primary_error",
        "source_snippets",
        "command_summary",
        "header_declarations",
        "top_k_summaries",
        "prompt_template",
        "structure_overhead",
    }
    assert sections["structure_overhead"] >= 0


def test_build_perf_report_contains_execution_tokens_and_decisions(tmp_path: Path) -> None:
    buildlog = tmp_path / "buildlog"
    buildlog.write_text("error: boom\n", encoding="utf-8")
    timings = {key: float(index + 1) for index, key in enumerate(PERF_LAYER_KEYS)}

    report = build_perf_report(
        buildlog_path=buildlog,
        packet=packet(),
        timings_ms=timings,
        estimator=TokenEstimator(use_tiktoken=False),
        evidence_collector="compile",
        level_preferred=3,
        level_achieved=2,
        warnings=["source_file_unavailable"],
    )

    assert report["schema_version"] == "perf_report/v1"
    assert report["buildlog_size_bytes"] == buildlog.stat().st_size
    assert report["execution"]["by_layer"]["L0_scan"] == 1.0
    assert report["execution"]["total_ms"] == sum(float(index + 1) for index in range(6))
    assert report["tokens"]["packet_tokens"] == 320
    assert report["decisions"]["evidence_collector"] == "compile"
    assert report["decisions"]["downgrade_reason"] == "budget_pool_partial"
    assert report["warnings"] == ["source_file_unavailable"]
