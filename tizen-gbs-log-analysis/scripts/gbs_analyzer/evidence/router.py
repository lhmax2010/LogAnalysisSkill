"""Route ranked candidates to M5 evidence collectors."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gbs_analyzer.evidence.base import EvidenceCollector
from gbs_analyzer.evidence.compile import CompileEvidenceCollector
from gbs_analyzer.evidence.deps import DepsEvidenceCollector
from gbs_analyzer.evidence.link import LinkEvidenceCollector
from gbs_analyzer.evidence.spec import SpecEvidenceCollector
from gbs_analyzer.scan_and_extract import ScanResult


def collector_for_candidate(
    candidate: dict[str, Any],
    scan_result: ScanResult | dict[str, Any],
    *,
    src_root: str | Path | None = None,
    spec_path: str | Path | None = None,
    buildlog_path: str | Path | None = None,
    ctags_runner: Any | None = None,
) -> EvidenceCollector | None:
    """Return the MVP collector for a ranked candidate or scanner event."""

    scan_data = scan_result.as_dict() if isinstance(scan_result, ScanResult) else scan_result
    event = _event_for_candidate(candidate, scan_data)
    kind = event.get("kind") or candidate.get("kind")

    kwargs = {
        "src_root": src_root,
        "spec_path": spec_path,
        "buildlog_path": buildlog_path,
        "ctags_runner": ctags_runner,
    }
    if kind in {"compiler", "werror"}:
        return CompileEvidenceCollector(scan_data, **kwargs)
    if kind in {"linker_undef", "linker_missing"}:
        return LinkEvidenceCollector(scan_data, **kwargs)
    if kind in {"spec_script", "rpm_phase"}:
        return SpecEvidenceCollector(scan_data, **kwargs)
    if kind == "depsolve":
        return DepsEvidenceCollector(scan_data, **kwargs)
    return None


def _event_for_candidate(
    candidate: dict[str, Any],
    scan_result: dict[str, Any],
) -> dict[str, Any]:
    event_id = candidate.get("event_id") or candidate.get("id")
    for event in scan_result.get("events", []):
        if isinstance(event, dict) and event.get("id") == event_id:
            return event
    return candidate
