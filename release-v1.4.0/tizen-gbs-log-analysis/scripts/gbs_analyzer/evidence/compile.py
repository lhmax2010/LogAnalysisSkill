"""Compile evidence collector."""

from __future__ import annotations

from typing import Any

from gbs_analyzer._utils.ctags_loader import extract_source_context
from gbs_analyzer.evidence._common import command_summary, quoted_symbol, search_header_declarations
from gbs_analyzer.evidence._common import source_path as resolve_source_path
from gbs_analyzer.evidence.base import (
    Evidence,
    EvidenceCollector,
    default_estimate,
    level_for_budget,
)


class CompileEvidenceCollector(EvidenceCollector):
    """Collect source snippets and command context for compiler diagnostics."""

    collector_name = "compile"

    def estimate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        del candidate
        return default_estimate()

    def collect(self, candidate: dict[str, Any], granted_budget: int) -> Evidence:
        event = self.event_for(candidate)
        command = self.command_for(event)
        level = level_for_budget(granted_budget)
        data: dict[str, Any] = {
            "primary_error": event,
            "command_summary": command_summary(command),
        }
        contains = {"primary_error", "command_summary"}
        methods: list[str] = []
        warnings: list[str] = []
        degraded = False

        if level >= 2:
            path = resolve_source_path(self.src_root, event)
            if path is not None and path.exists():
                context = extract_source_context(
                    path,
                    line=_int_or_none(event.get("line")),
                    symbol=quoted_symbol(str(event.get("message", ""))),
                    ctags_runner=self.ctags_runner,
                )
                data["source_snippet"] = context.as_dict()
                contains.add("source_snippet")
                methods.append(context.extraction_method)
                degraded = degraded or context.degraded
            else:
                warnings.append("source_file_unavailable")
                degraded = True

        if level >= 3:
            data["header_declarations"] = search_header_declarations(
                self.src_root,
                quoted_symbol(str(event.get("message", ""))),
            )
            contains.add("header_declarations")

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


def _int_or_none(value: Any) -> int | None:
    return value if isinstance(value, int) else None
