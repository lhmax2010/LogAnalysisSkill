"""Spec script evidence collector."""

from __future__ import annotations

from typing import Any

from gbs_analyzer.evidence.base import (
    Evidence,
    EvidenceCollector,
    default_estimate,
    level_for_budget,
)
from gbs_analyzer.tizen.spec_minimal import SpecMinimalParser


class SpecEvidenceCollector(EvidenceCollector):
    """Collect spec section and failure context for spec script errors."""

    collector_name = "spec"

    def estimate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        del candidate
        return default_estimate()

    def collect(self, candidate: dict[str, Any], granted_budget: int) -> Evidence:
        event = self.event_for(candidate)
        level = level_for_budget(granted_budget)
        phase = str(event.get("phase") or event.get("details", {}).get("phase") or "%build")
        data: dict[str, Any] = {"primary_error": event, "phase": phase}
        contains = {"primary_error"}
        warnings: list[str] = []
        degraded = False

        if self.spec_path is None or not self.spec_path.exists():
            warnings.append("spec_file_unavailable")
            degraded = True
        else:
            parser = SpecMinimalParser(
                self.spec_path,
                buildlog_path=self.buildlog_path,
            )
            data["spec_section_text"] = parser.extract_section(phase)
            data["spec_parse_status"] = parser.get_parse_status()
            contains.update({"spec_section_text", "spec_parse_status"})
            if level >= 2:
                data["failure_context"] = parser.extract_section_failure_context(phase)
                contains.add("failure_context")
            if level >= 3:
                data["buildrequires"] = parser.extract_buildrequires()
                data["patches"] = parser.extract_patches()
                data["sources"] = parser.extract_sources()
                contains.update({"spec_buildrequires", "spec_patches", "spec_sources"})

        return Evidence(
            collector=self.collector_name,
            level=level,
            granted_budget=granted_budget,
            data=data,
            contains=contains,
            degraded=degraded,
            warnings=warnings,
        )
