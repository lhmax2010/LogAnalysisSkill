"""Build the analyzer performance report emitted by the M8 wrapper."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gbs_analyzer.packet_assembler import TokenEstimator

PERF_SCHEMA_VERSION = "perf_report/v1"
PERF_LAYER_KEYS = (
    "L0_scan",
    "L4a_quick",
    "L2_rank",
    "L3_evidence",
    "L4b_full",
    "L5_assembler",
)


def build_perf_report(
    *,
    buildlog_path: str | Path,
    packet: dict[str, Any],
    timings_ms: dict[str, float],
    estimator: TokenEstimator,
    exit_status: str = "success",
    evidence_collector: str | None = None,
    level_preferred: int | None = None,
    level_achieved: int | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Return the v0.5 §10.2 `perf_report.json` payload."""

    path = Path(buildlog_path)
    size = path.stat().st_size if path.exists() else 0
    by_layer = {key: round(float(timings_ms.get(key, 0.0)), 4) for key in PERF_LAYER_KEYS}
    total_ms = round(sum(by_layer.values()), 4)
    token_budget = packet.get("token_budget", {})
    packet_tokens = int(token_budget.get("used") or estimator.estimate_obj(packet))
    input_log_tokens = estimate_buildlog_tokens(size)
    section_tokens = token_sections(packet, estimator, packet_tokens)
    downgrade_reason = _downgrade_reason(packet)

    return {
        "schema_version": PERF_SCHEMA_VERSION,
        "analyzed_at": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "buildlog_size_bytes": size,
        "buildlog_token_estimate": input_log_tokens,
        "execution": {
            "total_ms": total_ms,
            "by_layer": by_layer,
            "fast_path_hit": packet.get("via") == "fast_path",
            "exit_status": exit_status,
        },
        "tokens": {
            "estimate_method": token_budget.get("estimate_method", estimator.method),
            "input_log_tokens": input_log_tokens,
            "packet_tokens": packet_tokens,
            "compression_ratio": round(input_log_tokens / max(packet_tokens, 1), 4),
            "budget": {
                "limit": token_budget.get(
                    "limit_with_prompt",
                    token_budget.get("limit", 1800),
                ),
                "evidence_pool_initial": token_budget.get("evidence_pool_initial"),
                "reclaimed": token_budget.get("reclaimed"),
                "evidence_pool_final": token_budget.get("evidence_pool_final"),
                "used": packet_tokens,
            },
            "by_section": section_tokens,
        },
        "decisions": {
            "verdict": packet.get("verdict"),
            "via": packet.get("via"),
            "matched_tier": packet.get("matched_tier"),
            "candidates_ranked": len(packet.get("root_cause_candidates", [])),
            "candidates_kept": len(packet.get("root_cause_candidates", [])),
            "evidence_collector": evidence_collector,
            "level_preferred": level_preferred,
            "level_achieved": level_achieved,
            "downgraded": bool(packet.get("degraded")),
            "downgrade_reason": downgrade_reason,
        },
        "degradations": list(packet.get("degraded_reasons", [])),
        "warnings": warnings or [],
    }


def estimate_buildlog_tokens(size_bytes: int) -> int:
    """Use a deterministic size heuristic for large logs."""

    return max(1, int(size_bytes / 4))


def token_sections(
    packet: dict[str, Any],
    estimator: TokenEstimator,
    packet_tokens: int | None = None,
) -> dict[str, int]:
    """Estimate token contribution by stable packet section names."""

    sections = {
        "primary_error": estimator.estimate_obj(packet.get("primary_error", {})),
        "source_snippets": _evidence_section_tokens(packet, estimator),
        "command_summary": _command_section_tokens(packet, estimator),
        "header_declarations": _header_section_tokens(packet, estimator),
        "top_k_summaries": estimator.estimate_obj(packet.get("root_cause_candidates", [])),
        "prompt_template": estimator.estimate_text(str(packet.get("prompt") or "")),
    }
    total = packet_tokens if packet_tokens is not None else estimator.estimate_obj(packet)
    sections["structure_overhead"] = max(0, int(total) - sum(sections.values()))
    return sections


def _evidence_section_tokens(packet: dict[str, Any], estimator: TokenEstimator) -> int:
    evidence = packet.get("evidence", {})
    if not isinstance(evidence, dict):
        return 1
    snippet_keys = {"source_snippet", "symbol_context", "failure_context", "fallback_context"}
    snippet_data = {
        key: value
        for key, value in evidence.items()
        if key in snippet_keys or key.endswith("_snippet")
    }
    return estimator.estimate_obj(snippet_data or evidence)


def _command_section_tokens(packet: dict[str, Any], estimator: TokenEstimator) -> int:
    evidence = packet.get("evidence", {})
    if not isinstance(evidence, dict):
        return 1
    command_data = {
        key: value
        for key, value in evidence.items()
        if key in {"command_summary", "link_command", "current_command_summary"}
    }
    return estimator.estimate_obj(command_data)


def _header_section_tokens(packet: dict[str, Any], estimator: TokenEstimator) -> int:
    evidence = packet.get("evidence", {})
    if not isinstance(evidence, dict):
        return 1
    return estimator.estimate_obj(evidence.get("header_declarations", []))


def _downgrade_reason(packet: dict[str, Any]) -> str | None:
    reasons = packet.get("degraded_reasons", [])
    if isinstance(reasons, list) and reasons:
        return str(reasons[0])
    return None
