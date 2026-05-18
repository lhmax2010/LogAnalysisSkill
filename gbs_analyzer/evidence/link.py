"""Link evidence collector."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gbs_analyzer._utils.ctags_loader import extract_source_context
from gbs_analyzer.evidence._common import command_summary
from gbs_analyzer.evidence.base import (
    Evidence,
    EvidenceCollector,
    default_estimate,
    level_for_budget,
)
from gbs_analyzer.tizen.spec_minimal import SpecMinimalParser


class LinkEvidenceCollector(EvidenceCollector):
    """Collect link command, symbol/library, and BuildRequires evidence."""

    collector_name = "link"

    def estimate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        del candidate
        return default_estimate()

    def collect(self, candidate: dict[str, Any], granted_budget: int) -> Evidence:
        event = self.event_for(candidate)
        command = self.command_for(event)
        level = level_for_budget(granted_budget)
        details = event.get("details", {}) if isinstance(event.get("details"), dict) else {}
        data: dict[str, Any] = {
            "primary_error": event,
            "link_command": command_summary(command),
            "symbol": details.get("symbol"),
            "library": details.get("library"),
        }
        contains = {"primary_error", "link_command"}
        methods: list[str] = []
        warnings: list[str] = []
        degraded = False

        if level >= 2 and self.spec_path is not None and self.spec_path.exists():
            parser = SpecMinimalParser(self.spec_path)
            data["spec_buildrequires"] = parser.extract_buildrequires()
            data["spec_parse_status"] = parser.get_parse_status()
            contains.add("spec_buildrequires")

        if level >= 3 and details.get("symbol") and self.src_root is not None:
            context = _find_symbol_context(
                self.src_root,
                str(details["symbol"]),
                self.ctags_runner,
            )
            if context is not None:
                data["symbol_context"] = context.as_dict()
                contains.add("symbol_context")
                methods.append(context.extraction_method)
                degraded = degraded or context.degraded
            else:
                warnings.append("symbol_context_unavailable")
                degraded = True

        return Evidence(
            collector=self.collector_name,
            level=level,
            granted_budget=granted_budget,
            data=data,
            contains=contains,
            degraded=degraded,
            extraction_methods=methods,
            warnings=warnings,
        )


def _find_symbol_context(src_root: Path, symbol: str, ctags_runner: Any | None) -> Any | None:
    for path in sorted(src_root.rglob("*")):
        if path.suffix not in {".c", ".cc", ".cpp", ".cxx", ".S", ".cu", ".h", ".hpp"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if symbol not in text:
            continue
        return extract_source_context(path, symbol=symbol, ctags_runner=ctags_runner)
    return None
