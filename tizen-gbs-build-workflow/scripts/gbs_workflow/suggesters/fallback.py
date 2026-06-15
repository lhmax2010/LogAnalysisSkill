"""Fallback guidance for unsupported primary errors."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gbs_workflow.suggesters._common import primary_kind, primary_message
from gbs_workflow.suggesters.base import SuggesterBase, Suggestion

SUPPORTED_PRIMARY_KINDS = {
    "compiler",
    "depsolve",
    "linker_missing",
    "linker_undef",
    "patch",
    "rpm_phase",
    "spec_script",
}


class FallbackSuggester(SuggesterBase):
    """Generate generic review guidance for unsupported primary errors."""

    name = "fallback"

    def matches(self, packet: dict[str, Any]) -> bool:
        kind = primary_kind(packet)
        return kind not in SUPPORTED_PRIMARY_KINDS

    def generate(self, packet: dict[str, Any], src_root: Path) -> list[Suggestion]:
        del src_root
        kind = primary_kind(packet) or "unknown"
        message = primary_message(packet) or "no primary message"
        return [
            Suggestion(
                suggester=self.name,
                title=f"Manually review unsupported error kind {kind}",
                description=(
                    f"No v0.1 Suggester handles primary error kind `{kind}`. The primary "
                    f"message is: `{message}`."
                ),
                patch_content=None,
                target_files=[],
                confidence="advisory",
                risks=[
                    "The workflow has not classified this failure into a known fix category.",
                    "A generic suggestion may miss package-specific constraints.",
                ],
                manual_steps=[
                    "Open analyzer_output/evidence_packet.md and review the Top-1 evidence.",
                    "Check compiler.log around the primary error offset.",
                    (
                        "If this becomes common, archive the case for a future Suggester or "
                        "v0.2 design."
                    ),
                ],
            )
        ]
