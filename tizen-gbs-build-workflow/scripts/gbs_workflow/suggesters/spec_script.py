"""Advisory suggestions for RPM spec script failures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gbs_workflow.suggesters._common import failed_phase, primary_message
from gbs_workflow.suggesters.base import SuggesterBase, Suggestion

SPEC_KINDS = {"spec_script", "rpm_phase"}


class SpecScriptSuggester(SuggesterBase):
    """Guide users through failed RPM phase/script commands."""

    name = "spec_script"

    def matches(self, packet: dict[str, Any]) -> bool:
        primary_error = packet.get("primary_error")
        return isinstance(primary_error, dict) and primary_error.get("kind") in SPEC_KINDS

    def generate(self, packet: dict[str, Any], src_root: Path) -> list[Suggestion]:
        del src_root
        phase = failed_phase(packet)
        message = primary_message(packet) or "spec script failed"
        return [
            Suggestion(
                suggester=self.name,
                title=f"Review failing spec phase {phase}",
                description=(
                    f"The RPM spec phase `{phase}` failed with: `{message}`. Inspect the "
                    "last shell command before the failure and compare it with the spec section."
                ),
                patch_content=None,
                target_files=[],
                confidence="advisory",
                risks=[
                    (
                        "Changing install/build commands may affect package file ownership "
                        "or manifests."
                    ),
                    "The failing command may depend on profile-specific macros or paths.",
                ],
                manual_steps=[
                    f"Open the `{phase}` section in the spec file.",
                    "Find the last command shown before the failure in evidence_packet.md.",
                    "Check whether referenced files/directories are produced in this profile.",
                    "Adjust the spec command manually and re-run the workflow.",
                ],
            )
        ]
