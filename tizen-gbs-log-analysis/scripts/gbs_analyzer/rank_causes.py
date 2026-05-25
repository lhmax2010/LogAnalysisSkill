"""Layer 2 root-cause ranking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gbs_analyzer._utils.semantic_classifier import SemanticClass, SemanticClassifier
from gbs_analyzer.quick_filter import is_in_warning_block
from gbs_analyzer.scan_and_extract import ScanResult


@dataclass(frozen=True)
class RootCauseCandidate:
    rank: int
    event_id: str
    kind: str
    semantic_class: str
    confidence: float
    confidence_band: str
    confidence_reason: list[dict[str, Any]]
    is_terminal: bool
    summary: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "event_id": self.event_id,
            "kind": self.kind,
            "semantic_class": self.semantic_class,
            "confidence": self.confidence,
            "confidence_band": self.confidence_band,
            "confidence_reason": self.confidence_reason,
            "is_terminal": self.is_terminal,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class RankResult:
    root_cause_candidates: list[RootCauseCandidate]

    def as_dict(self) -> dict[str, Any]:
        return {
            "root_cause_candidates": [
                candidate.as_dict() for candidate in self.root_cause_candidates
            ]
        }


def rank_causes(
    scan_result: ScanResult | dict[str, Any],
    *,
    top_k: int = 3,
    classifier: SemanticClassifier | None = None,
) -> RankResult:
    """Rank scanner events and keep Top-K root-cause candidates."""

    scan_data = _scan_as_dict(scan_result)
    events = [event for event in scan_data.get("events", []) if isinstance(event, dict)]
    active_classifier = classifier or SemanticClassifier.from_file()

    scored: list[tuple[float, dict[str, Any], SemanticClass, list[dict[str, Any]]]] = []
    for event in events:
        sem = active_classifier.classify(event, scan_data)
        score, reasons = rank_score(
            event,
            events,
            sem,
            failed_phase=scan_data.get("failed_phase"),
        )
        scored.append((score, event, sem, reasons))

    scored.sort(key=lambda item: (-item[0], int(item[1].get("line_no", 0))))
    candidates = [
        _candidate(rank=index + 1, score=score, event=event, sem=sem, reasons=reasons)
        for index, (score, event, sem, reasons) in enumerate(scored[:top_k])
    ]
    return RankResult(root_cause_candidates=candidates)


def rank_score(
    event: dict[str, Any],
    all_events: list[Any],
    semantic: SemanticClass | None = None,
    *,
    failed_phase: str | None = None,
) -> tuple[float, list[dict[str, Any]]]:
    """Return the v0.5 ranking score and structured confidence reasons."""

    if event.get("kind") == "make_cascade" and event.get("parent"):
        return 0.1, [
            {"factor": "make_cascade_parent", "value": event.get("parent"), "score": 0.1}
        ]

    sem = semantic or SemanticClassifier.from_file().classify(event, {"failed_phase": None})
    reasons: list[dict[str, Any]] = [
        {"factor": "semantic_class", "value": sem.name, "base": sem.base_confidence}
    ]
    score = sem.base_confidence

    if event.get("kind") == "linker_undef":
        reasons.append({"factor": "linker_undef_no_cascade_penalty", "delta": "+0.00"})
    else:
        cascade_delta = -(sem.cascade_probability * 0.3)
        score += cascade_delta
        reasons.append(
            {
                "factor": "cascade_probability",
                "probability": sem.cascade_probability,
                "delta": _format_delta(cascade_delta),
            }
        )

    if event.get("command_id"):
        score += 0.05
        reasons.append({"factor": "has_command", "delta": "+0.05"})

    if event.get("file") and event.get("line"):
        score += 0.05
        reasons.append({"factor": "has_location", "delta": "+0.05"})

    if event.get("kind") == "patch" and event.get("phase") == failed_phase:
        score += 0.1
        reasons.append({"factor": "patch_failed_phase", "delta": "+0.10"})

    if is_in_warning_block(event, all_events):
        score -= 0.3
        reasons.append({"factor": "warning_block", "delta": "-0.30"})

    if event.get("parent"):
        score -= 0.4
        reasons.append({"factor": "parent_cascade", "delta": "-0.40"})

    clamped = clamp(score, 0.0, 1.0)
    if clamped != score:
        reasons.append({"factor": "clamp", "from": round(score, 4), "to": clamped})
    if sem.name == "generic_error":
        reasons.append(
            {
                "factor": "generic_context_satisfied",
                "value": sem.context_satisfied,
            }
        )
    return clamped, reasons


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _candidate(
    *,
    rank: int,
    score: float,
    event: dict[str, Any],
    sem: SemanticClass,
    reasons: list[dict[str, Any]],
) -> RootCauseCandidate:
    return RootCauseCandidate(
        rank=rank,
        event_id=str(event.get("id")),
        kind=str(event.get("kind")),
        semantic_class=sem.name,
        confidence=round(score, 4),
        confidence_band=confidence_band(score),
        confidence_reason=reasons,
        is_terminal=not bool(event.get("parent")),
        summary=_summary(event, sem),
    )


def confidence_band(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.70:
        return "medium_high"
    if score >= 0.50:
        return "medium"
    return "low"


def _summary(event: dict[str, Any], sem: SemanticClass) -> str:
    location = ""
    if event.get("file") and event.get("line"):
        location = f" at {event['file']}:{event['line']}"
    message = str(event.get("message", "")).strip()
    return f"{event.get('kind')} {sem.name}{location} - {message}"


def _format_delta(value: float) -> str:
    return f"{value:+.2f}"


def _scan_as_dict(scan_result: ScanResult | dict[str, Any]) -> dict[str, Any]:
    if isinstance(scan_result, ScanResult):
        return scan_result.as_dict()
    return scan_result
