"""Layer 5 evidence packet assembly and token budgeting."""

from __future__ import annotations

import json
import math
import re
import socket
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tiktoken
except ImportError:  # pragma: no cover - exercised by fallback tests via constructor
    tiktoken = None  # type: ignore[assignment]

from gbs_analyzer.evidence import Evidence
from gbs_analyzer.evidence._common import command_summary
from gbs_analyzer.full_match import FullMatchResult, Verdict
from gbs_analyzer.rank_causes import RankResult
from gbs_analyzer.scan_and_extract import ScanResult
from gbs_analyzer.tracing import TraceLogger


@dataclass(frozen=True)
class HardReserve:
    """Hard budget reserve. Unused tokens are not reclaimed."""

    amount: int


@dataclass(frozen=True)
class SoftReserve:
    """Soft budget reserve. Unused tokens return to the evidence pool."""

    amount: int


Reserve = HardReserve | SoftReserve


@dataclass
class BudgetPool:
    """Token budget pool with v0.5 hard/soft reserve accounting."""

    total: int = 1400
    reserved: dict[str, Reserve] = field(init=False)
    evidence_pool: int = field(init=False)
    soft_used: dict[str, int] = field(default_factory=dict)
    grants: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.reserved = {
            "primary_error": HardReserve(200),
            "command_summary": HardReserve(120),
            "metadata": HardReserve(80),
            "cascade_summary": SoftReserve(50),
            "top_k_text_summaries": SoftReserve(200),
            "raw_excerpt": SoftReserve(100),
        }
        initial = self.total - self.hard_reserved - self.soft_reserved
        if initial < 0:
            raise ValueError("reserved budget exceeds total")
        self.evidence_pool = initial

    @property
    def hard_reserved(self) -> int:
        return sum(
            reserve.amount for reserve in self.reserved.values() if isinstance(reserve, HardReserve)
        )

    @property
    def soft_reserved(self) -> int:
        return sum(
            reserve.amount for reserve in self.reserved.values() if isinstance(reserve, SoftReserve)
        )

    @property
    def reclaimed(self) -> int:
        total = 0
        for name, actual in self.soft_used.items():
            reserve = self.reserved[name]
            if isinstance(reserve, SoftReserve):
                total += max(0, reserve.amount - actual)
        return total

    @property
    def granted_total(self) -> int:
        return sum(self.grants.values())

    def report_reserve_used(self, name: str, actual_used: int) -> int:
        """Report SoftReserve usage and return the reclaimed token count."""

        reserve = self.reserved.get(name)
        if reserve is None:
            raise KeyError(f"unknown reserve: {name}")
        if not isinstance(reserve, SoftReserve):
            raise ValueError(f"{name} is not a soft reserve")
        if name in self.soft_used:
            raise ValueError(f"{name} has already been reported")
        actual = min(max(actual_used, 0), reserve.amount)
        self.soft_used[name] = actual
        reclaimed = reserve.amount - actual
        self.evidence_pool += reclaimed
        return reclaimed

    def request(self, collector_name: str, requested: int) -> int:
        """Grant as much of ``requested`` as the current evidence pool allows."""

        if requested < 0:
            raise ValueError("requested budget must be non-negative")
        granted = min(requested, self.evidence_pool)
        self.evidence_pool -= granted
        self.grants[collector_name] = self.grants.get(collector_name, 0) + granted
        return granted

    def conservation_total(self) -> int:
        soft_used = sum(self.soft_used.values())
        soft_pending = sum(
            reserve.amount
            for name, reserve in self.reserved.items()
            if isinstance(reserve, SoftReserve) and name not in self.soft_used
        )
        return (
            self.hard_reserved + soft_used + soft_pending + self.evidence_pool + self.granted_total
        )

    def conservation_ok(self) -> bool:
        return self.conservation_total() == self.total

    def as_dict(self) -> dict[str, Any]:
        return {
            "limit": self.total,
            "hard_reserved": self.hard_reserved,
            "soft_reserved": self.soft_reserved,
            "evidence_pool_initial": self.total - self.hard_reserved - self.soft_reserved,
            "reclaimed": self.reclaimed,
            "evidence_pool_final": self.evidence_pool,
            "granted": dict(sorted(self.grants.items())),
            "soft_used": dict(sorted(self.soft_used.items())),
            "conservation_total": self.conservation_total(),
            "conservation_ok": self.conservation_ok(),
        }


class TokenEstimator:
    """Estimate token usage with tiktoken and a deterministic local fallback."""

    def __init__(self, *, use_tiktoken: bool = True) -> None:
        self.method = "fallback"
        self._encoder: Any | None = None
        if use_tiktoken and tiktoken is not None:
            self._encoder = tiktoken.get_encoding("cl100k_base")
            self.method = "tiktoken"

    def estimate_text(self, text: str) -> int:
        if self._encoder is not None:
            return len(self._encoder.encode(text))
        return fallback_token_estimate(text)

    def estimate_obj(self, obj: Any) -> int:
        return self.estimate_text(json.dumps(obj, ensure_ascii=False, sort_keys=True))

    def truncate_text(self, text: str, max_tokens: int) -> str:
        if max_tokens <= 0:
            return ""
        current = self.estimate_text(text)
        if current <= max_tokens:
            return text
        ratio = max_tokens / max(current, 1)
        keep = max(1, math.floor(len(text) * ratio))
        truncated = text[:keep].rstrip()
        while truncated and self.estimate_text(truncated) > max_tokens:
            next_length = max(0, len(truncated) - 16)
            if next_length == len(truncated):
                next_length -= 1
            truncated = truncated[:next_length].rstrip()
        return truncated + "\n[truncated]"


def fallback_token_estimate(text: str) -> int:
    chinese_chars = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    words = re.findall(r"[A-Za-z0-9_./+-]+", text)
    word_chars = sum(len(word) for word in words)
    other_chars = max(0, len(text) - chinese_chars - word_chars)
    estimate = chinese_chars / 1.5 + len(words) / 0.75 + other_chars / 3
    return max(1, math.ceil(estimate))


class MinimalRedactor:
    """Apply storage-vs-LLM redaction rules from v0.5 §3.6."""

    def __init__(
        self,
        *,
        workspace_root: str | Path | None = None,
        hostname: str | None = None,
    ) -> None:
        self.workspace_root = str(Path(workspace_root)) if workspace_root is not None else None
        self.hostname = hostname or socket.gethostname()

    def redact_for_llm(self, text: str) -> str:
        redacted = text
        if self.workspace_root:
            redacted = redacted.replace(self.workspace_root, "<WORKSPACE>")
        redacted = re.sub(r"/home/[^/\s]+/", "/home/<USER>/", redacted)
        if self.hostname:
            redacted = redacted.replace(self.hostname, "<HOST>")
        return redacted

    def redact_obj_for_llm(self, obj: Any) -> Any:
        if isinstance(obj, str):
            return self.redact_for_llm(obj)
        if isinstance(obj, list):
            return [self.redact_obj_for_llm(item) for item in obj]
        if isinstance(obj, dict):
            return {key: self.redact_obj_for_llm(value) for key, value in obj.items()}
        return obj

    def redact_for_storage(self, obj: dict[str, Any]) -> dict[str, Any]:
        return obj


def fallback_raw_context(
    top1_event: dict[str, Any],
    scan_result: ScanResult | dict[str, Any],
    *,
    budget: int = 600,
    estimator: TokenEstimator | None = None,
) -> dict[str, Any]:
    """Return the MVP raw fallback context for unknown or collector-missing cases."""

    scan_data = _scan_as_dict(scan_result)
    active_estimator = estimator or TokenEstimator()
    excerpt = _read_log_window(top1_event, scan_data)
    excerpt = active_estimator.truncate_text(excerpt, budget)
    context = {
        "primary_error_excerpt": excerpt,
        "current_phase": top1_event.get("phase"),
        "current_command_summary": command_summary(_command_for_event(top1_event, scan_data)),
        "cascade_summary": format_cascade_summary(scan_data),
    }
    context["token_estimate"] = active_estimator.estimate_obj(context)
    return context


def assemble_packet(
    scan_result: ScanResult | dict[str, Any],
    rank_result: RankResult | dict[str, Any] | list[dict[str, Any]],
    evidence: Evidence | dict[str, Any] | None,
    full_match_result: FullMatchResult | dict[str, Any] | None,
    *,
    package: str = "unknown",
    arch: str = "unknown",
    profile: str = "unknown",
    budget_pool: BudgetPool | None = None,
    estimator: TokenEstimator | None = None,
    redactor: MinimalRedactor | None = None,
    trace_logger: TraceLogger | None = None,
    max_tokens: int = 1800,
) -> dict[str, Any]:
    """Assemble the v0.5 Evidence Packet storage JSON."""

    scan_data = _scan_as_dict(scan_result)
    candidates = _rank_candidates(rank_result)
    top_event = _top_event(candidates, scan_data)
    pool = budget_pool or BudgetPool()
    active_estimator = estimator or TokenEstimator()
    active_redactor = redactor or MinimalRedactor()

    cascade_summary = format_cascade_summary(scan_data)
    pool.report_reserve_used(
        "cascade_summary",
        active_estimator.estimate_text(cascade_summary),
    )
    pool.report_reserve_used(
        "top_k_text_summaries",
        active_estimator.estimate_obj(candidates),
    )

    evidence_data = _evidence_as_dict(evidence)
    degraded_reasons = list(scan_data.get("degraded_reasons", []))
    fallback_context: dict[str, Any] | None = None
    if evidence_data is None:
        fallback_context = fallback_raw_context(top_event, scan_data, estimator=active_estimator)
        pool.report_reserve_used(
            "raw_excerpt",
            active_estimator.estimate_text(str(fallback_context.get("primary_error_excerpt", ""))),
        )
        degraded_reasons.append("fallback_raw_context_used")
    else:
        pool.report_reserve_used("raw_excerpt", 0)
        collector = str(evidence_data.get("collector", "evidence"))
        granted_budget = int(evidence_data.get("granted_budget", 0))
        granted = pool.request(collector, granted_budget)
        if granted < granted_budget:
            degraded_reasons.append("budget_pool_partial")

    match_data = _full_match_as_dict(full_match_result)
    is_direct = match_data.get("verdict") == "direct_answer"
    packet_verdict = "direct_answer" if is_direct else "needs_llm"
    direct_answer = match_data.get("direct_answer") if is_direct else None

    evidence_section = (
        {"fallback_context": fallback_context}
        if fallback_context is not None
        else evidence_data.get("data", {})
        if evidence_data is not None
        else {}
    )
    degraded = bool(
        degraded_reasons or (evidence_data is not None and evidence_data.get("degraded"))
    )
    if evidence_data is not None and evidence_data.get("warnings"):
        degraded_reasons.extend(str(item) for item in evidence_data["warnings"])

    packet: dict[str, Any] = {
        "schema_version": "evidence_packet/v1",
        "verdict": packet_verdict,
        "via": "full_path",
        "package": package,
        "arch": arch,
        "profile": profile,
        "failed_phase": scan_data.get("failed_phase"),
        "root_cause_candidates": candidates,
        "cascade_summary": cascade_summary,
        "primary_error": top_event,
        "evidence": evidence_section,
        "matched_patterns": [match_data["pattern_id"]] if match_data.get("pattern_id") else [],
        "direct_answer": direct_answer,
        "matched_tier": match_data.get("matched_tier"),
        "prompt": None,
        "token_budget": pool.as_dict(),
        "degraded": degraded,
        "degraded_reasons": degraded_reasons,
        "allowed_next_actions": ["expand"],
    }

    if packet_verdict == "needs_llm":
        packet["prompt"] = active_redactor.redact_for_llm(_render_prompt(packet))

    packet["token_budget"]["estimate_method"] = active_estimator.method
    packet["token_budget"]["limit_with_prompt"] = max_tokens
    packet["token_budget"]["storage_redaction"] = "raw_paths_preserved"
    _enforce_final_token_limit(
        packet,
        max_tokens=max_tokens,
        estimator=active_estimator,
        redactor=active_redactor,
    )

    if trace_logger is not None:
        trace_logger.info(
            "L5_assembler",
            "packet_assembled",
            verdict=packet["verdict"],
            tokens=packet["token_budget"]["used"],
            conservation_ok=packet["token_budget"]["conservation_ok"],
        )

    return active_redactor.redact_for_storage(packet)


def _enforce_final_token_limit(
    packet: dict[str, Any],
    *,
    max_tokens: int,
    estimator: TokenEstimator,
    redactor: MinimalRedactor,
) -> None:
    """Shrink soft packet sections until the final packet respects ``max_tokens``."""

    _refresh_prompt(packet, redactor)
    used = estimator.estimate_obj(packet)
    if used <= max_tokens:
        packet["token_budget"]["used"] = used
        return

    _mark_packet_truncated(packet)
    shrink_steps: tuple[Callable[[], bool], ...] = (
        lambda: _limit_fallback_lines(packet, "extra_log_window", max_lines=30),
        lambda: _clear_fallback_field(packet, "extra_log_window"),
        lambda: _limit_fallback_lines(packet, "primary_error_excerpt", max_lines=30),
        lambda: _clear_cascade_summary(packet, estimator),
        lambda: _truncate_snippet_texts(packet, estimator, max_tokens=120),
        lambda: _truncate_fallback_text(packet, estimator, max_tokens=120),
        lambda: _keep_top_candidate(packet),
        lambda: _truncate_snippet_texts(packet, estimator, max_tokens=40),
        lambda: _truncate_fallback_text(packet, estimator, max_tokens=40),
    )

    for shrink in shrink_steps:
        changed = shrink()
        if not changed:
            continue
        _refresh_prompt(packet, redactor)
        used = estimator.estimate_obj(packet)
        if used <= max_tokens:
            packet["token_budget"]["used"] = used
            return

    packet["token_budget"]["used"] = estimator.estimate_obj(packet)


def _refresh_prompt(packet: dict[str, Any], redactor: MinimalRedactor) -> None:
    if packet.get("verdict") == "needs_llm":
        packet["prompt"] = redactor.redact_for_llm(_render_prompt(packet))


def _mark_packet_truncated(packet: dict[str, Any]) -> None:
    reasons = packet.setdefault("degraded_reasons", [])
    if isinstance(reasons, list) and "packet_truncated_to_token_budget" not in reasons:
        reasons.append("packet_truncated_to_token_budget")
    packet["degraded"] = True


def _fallback_context(packet: dict[str, Any]) -> dict[str, Any] | None:
    evidence = packet.get("evidence")
    if not isinstance(evidence, dict):
        return None
    fallback = evidence.get("fallback_context")
    return fallback if isinstance(fallback, dict) else None


def _limit_fallback_lines(packet: dict[str, Any], field: str, *, max_lines: int) -> bool:
    fallback = _fallback_context(packet)
    if fallback is None:
        return False
    value = fallback.get(field)
    if not isinstance(value, str):
        return False
    lines = value.splitlines()
    if len(lines) <= max_lines:
        return False
    fallback[field] = "\n".join(lines[-max_lines:]) + "\n[truncated]"
    return True


def _clear_fallback_field(packet: dict[str, Any], field: str) -> bool:
    fallback = _fallback_context(packet)
    if fallback is None:
        return False
    value = fallback.get(field)
    if not isinstance(value, str) or not value:
        return False
    fallback[field] = ""
    return True


def _clear_cascade_summary(packet: dict[str, Any], estimator: TokenEstimator) -> bool:
    summary = str(packet.get("cascade_summary") or "")
    fallback = _fallback_context(packet)
    fallback_summary = str(fallback.get("cascade_summary") or "") if fallback is not None else ""
    if estimator.estimate_text(summary + fallback_summary) <= 50:
        return False

    changed = False
    if summary:
        packet["cascade_summary"] = ""
        changed = True
    if fallback is not None and fallback_summary:
        fallback["cascade_summary"] = ""
        changed = True
    return changed


def _truncate_snippet_texts(
    packet: dict[str, Any],
    estimator: TokenEstimator,
    *,
    max_tokens: int,
) -> bool:
    evidence = packet.get("evidence")
    if not isinstance(evidence, dict):
        return False
    return _truncate_text_fields(evidence, estimator, max_tokens=max_tokens)


def _truncate_fallback_text(
    packet: dict[str, Any],
    estimator: TokenEstimator,
    *,
    max_tokens: int,
) -> bool:
    fallback = _fallback_context(packet)
    if fallback is None:
        return False
    changed = False
    for field_name in ("primary_error_excerpt", "extra_log_window"):
        value = fallback.get(field_name)
        if not isinstance(value, str) or not value:
            continue
        truncated = estimator.truncate_text(value, max_tokens)
        if truncated != value:
            fallback[field_name] = truncated
            changed = True
    return changed


def _truncate_text_fields(
    value: Any,
    estimator: TokenEstimator,
    *,
    max_tokens: int,
) -> bool:
    changed = False
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "text" and isinstance(child, str):
                truncated = estimator.truncate_text(child, max_tokens)
                if truncated != child:
                    value[key] = truncated
                    changed = True
            else:
                changed = (
                    _truncate_text_fields(
                        child,
                        estimator,
                        max_tokens=max_tokens,
                    )
                    or changed
                )
    elif isinstance(value, list):
        for child in value:
            changed = (
                _truncate_text_fields(
                    child,
                    estimator,
                    max_tokens=max_tokens,
                )
                or changed
            )
    return changed


def _keep_top_candidate(packet: dict[str, Any]) -> bool:
    candidates = packet.get("root_cause_candidates")
    if not isinstance(candidates, list) or len(candidates) <= 1:
        return False
    packet["root_cause_candidates"] = candidates[:1]
    return True


def render_packet_markdown(
    packet: dict[str, Any],
    *,
    redactor: MinimalRedactor | None = None,
) -> str:
    """Render a compact, LLM-redacted markdown view of a packet."""

    active_redactor = redactor or MinimalRedactor()
    public_packet = active_redactor.redact_obj_for_llm(packet)
    lines = [
        "# GBS Build Failure Analysis",
        f"- Verdict: {public_packet.get('verdict')}",
        f"- Failed phase: {public_packet.get('failed_phase')}",
        f"- Matched tier: {public_packet.get('matched_tier')}",
        "",
        "## Primary Error",
        json.dumps(public_packet.get("primary_error", {}), ensure_ascii=False, indent=2),
        "",
        "## Evidence",
        json.dumps(public_packet.get("evidence", {}), ensure_ascii=False, indent=2),
    ]
    if public_packet.get("prompt"):
        lines.extend(["", "## Prompt", str(public_packet["prompt"])])
    return "\n".join(lines)


def format_cascade_summary(scan_result: ScanResult | dict[str, Any]) -> str:
    scan_data = _scan_as_dict(scan_result)
    cascades = [
        event
        for event in scan_data.get("events", [])
        if isinstance(event, dict) and event.get("kind") == "make_cascade"
    ]
    if not cascades:
        return ""
    parts = []
    for event in cascades:
        target = event.get("target") or "<unknown>"
        parent = event.get("parent") or "unlinked"
        parts.append(f"{target} -> {parent}")
    return "make cascade: " + "; ".join(parts)


def _read_log_window(
    event: dict[str, Any],
    scan_data: dict[str, Any],
    *,
    before: int = 30,
    after: int = 20,
) -> str:
    path = Path(str(scan_data.get("buildlog_path", "")))
    if not path.exists():
        return str(event.get("message", ""))
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    line_no = event.get("line_no")
    if not isinstance(line_no, int):
        line_no = 1
    start = max(1, line_no - before)
    end = min(len(lines), line_no + after)
    return "\n".join(lines[start - 1 : end])


def _render_prompt(packet: dict[str, Any]) -> str:
    candidates = json.dumps(
        packet.get("root_cause_candidates", []),
        ensure_ascii=False,
        indent=2,
    )
    evidence = json.dumps(packet.get("evidence", {}), ensure_ascii=False, indent=2)
    return (
        "请根据以下 GBS 构建失败证据定位根因并给出最小修复建议。\n\n"
        f"Failed phase: {packet.get('failed_phase')}\n"
        f"Primary error: {json.dumps(packet.get('primary_error', {}), ensure_ascii=False)}\n\n"
        f"Candidates:\n{candidates}\n\n"
        f"Evidence:\n{evidence}\n"
    )


def _top_event(candidates: list[dict[str, Any]], scan_data: dict[str, Any]) -> dict[str, Any]:
    if candidates:
        event = _event_for_id(candidates[0].get("event_id"), scan_data)
        if event:
            return event
    events = [event for event in scan_data.get("events", []) if isinstance(event, dict)]
    return events[0] if events else {}


def _event_for_id(event_id: Any, scan_data: dict[str, Any]) -> dict[str, Any] | None:
    for event in scan_data.get("events", []):
        if isinstance(event, dict) and event.get("id") == event_id:
            return event
    return None


def _command_for_event(
    event: dict[str, Any],
    scan_data: dict[str, Any],
) -> dict[str, Any] | None:
    command_id = event.get("command_id")
    for command in scan_data.get("commands", []):
        if isinstance(command, dict) and command.get("id") == command_id:
            return command
    return None


def _rank_candidates(
    rank_result: RankResult | dict[str, Any] | list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if isinstance(rank_result, RankResult):
        candidates = rank_result.as_dict()["root_cause_candidates"]
        return [item for item in candidates if isinstance(item, dict)]
    if isinstance(rank_result, dict):
        candidates = rank_result.get("root_cause_candidates", [])
        return [item for item in candidates if isinstance(item, dict)]
    return [item for item in rank_result if isinstance(item, dict)]


def _evidence_as_dict(evidence: Evidence | dict[str, Any] | None) -> dict[str, Any] | None:
    if evidence is None:
        return None
    if isinstance(evidence, Evidence):
        return evidence.as_dict()
    return evidence


def _full_match_as_dict(
    full_match_result: FullMatchResult | dict[str, Any] | None,
) -> dict[str, Any]:
    if full_match_result is None:
        return {"verdict": "needs_llm"}
    if isinstance(full_match_result, FullMatchResult):
        return full_match_result.as_dict()
    if "verdict" in full_match_result:
        return full_match_result
    verdict = full_match_result.get("full_match_verdict")
    if verdict in {Verdict.DIRECT_TIER1.value, Verdict.DIRECT_TIER2.value}:
        return {**full_match_result, "verdict": "direct_answer"}
    return {**full_match_result, "verdict": "needs_llm"}


def _scan_as_dict(scan_result: ScanResult | dict[str, Any]) -> dict[str, Any]:
    if isinstance(scan_result, ScanResult):
        return scan_result.as_dict()
    return scan_result
