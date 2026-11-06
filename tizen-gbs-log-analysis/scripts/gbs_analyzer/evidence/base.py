"""Evidence collector base types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gbs_analyzer.scan_and_extract import ScanResult


@dataclass(frozen=True)
class Evidence:
    collector: str
    level: int
    granted_budget: int
    data: dict[str, Any]
    contains: set[str] = field(default_factory=set)
    degraded: bool = False
    extraction_methods: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def contains_all(self, required: list[str]) -> bool:
        return set(required).issubset(self.contains)

    def as_dict(self) -> dict[str, Any]:
        return {
            "collector": self.collector,
            "level": self.level,
            "granted_budget": self.granted_budget,
            "data": self.data,
            "contains": sorted(self.contains),
            "degraded": self.degraded,
            "extraction_methods": self.extraction_methods,
            "warnings": self.warnings,
        }


class EvidenceCollector(ABC):
    """Base interface for M5 evidence collectors."""

    collector_name: str

    def __init__(
        self,
        scan_result: ScanResult | dict[str, Any],
        *,
        src_root: str | Path | None = None,
        spec_path: str | Path | None = None,
        buildlog_path: str | Path | None = None,
        ctags_runner: Any | None = None,
    ) -> None:
        self.scan_result = (
            scan_result.as_dict() if isinstance(scan_result, ScanResult) else scan_result
        )
        self.src_root = Path(src_root) if src_root is not None else None
        self.spec_path = Path(spec_path) if spec_path is not None else None
        self.buildlog_path = Path(buildlog_path) if buildlog_path is not None else None
        self.ctags_runner = ctags_runner

    @abstractmethod
    def estimate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        """Return preferred/minimum budgets and level thresholds."""

    @abstractmethod
    def collect(self, candidate: dict[str, Any], granted_budget: int) -> Evidence:
        """Collect evidence for a candidate within the granted budget."""

    def event_for(self, candidate: dict[str, Any]) -> dict[str, Any]:
        event_id = candidate.get("event_id") or candidate.get("id")
        for event in self.scan_result.get("events", []):
            if isinstance(event, dict) and event.get("id") == event_id:
                return event
        if candidate.get("kind"):
            return candidate
        return {}

    def command_for(self, event: dict[str, Any]) -> dict[str, Any] | None:
        command_id = event.get("command_id")
        for command in self.scan_result.get("commands", []):
            if isinstance(command, dict) and command.get("id") == command_id:
                return command
        return None


def level_for_budget(granted_budget: int) -> int:
    if granted_budget >= 900:
        return 3
    if granted_budget >= 600:
        return 2
    return 1


def default_estimate() -> dict[str, Any]:
    return {"preferred": 900, "minimum": 300, "levels": {1: 300, 2: 600, 3: 900}}
