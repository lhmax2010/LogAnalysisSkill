"""Dependency resolution evidence collector."""

from __future__ import annotations

from typing import Any

from gbs_analyzer.evidence._common import parse_missing_dependency, profile_hint
from gbs_analyzer.evidence.base import (
    Evidence,
    EvidenceCollector,
    default_estimate,
    level_for_budget,
)
from gbs_analyzer.tizen.spec_minimal import SpecMinimalParser


class DepsEvidenceCollector(EvidenceCollector):
    """Collect missing dependency and BuildRequires context."""

    collector_name = "deps"

    def estimate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        del candidate
        return default_estimate()

    def collect(self, candidate: dict[str, Any], granted_budget: int) -> Evidence:
        event = self.event_for(candidate)
        level = level_for_budget(granted_budget)
        data: dict[str, Any] = {
            "primary_error": event,
            "missing_dependency": parse_missing_dependency(str(event.get("message", ""))),
            "profile_hint": profile_hint(self.scan_result),
        }
        contains = {"primary_error", "missing_dependency"}
        warnings: list[str] = []
        degraded = False

        if level >= 2:
            if self.spec_path is not None and self.spec_path.exists():
                parser = SpecMinimalParser(self.spec_path)
                data["spec_buildrequires"] = parser.extract_buildrequires()
                data["spec_parse_status"] = parser.get_parse_status()
                contains.add("spec_buildrequires")
            else:
                warnings.append("spec_file_unavailable")
                degraded = True

        return Evidence(
            collector=self.collector_name,
            level=level,
            granted_budget=granted_budget,
            data=data,
            contains=contains,
            degraded=degraded,
            warnings=warnings,
        )
