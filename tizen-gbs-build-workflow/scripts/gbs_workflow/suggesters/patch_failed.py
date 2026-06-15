"""Advisory suggestions for failed source patches."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gbs_workflow.suggesters._common import primary_message
from gbs_workflow.suggesters.base import SuggesterBase, Suggestion


class PatchFailedSuggester(SuggesterBase):
    """Guide users through patch failure recovery."""

    name = "patch_failed"

    def matches(self, packet: dict[str, Any]) -> bool:
        primary_error = packet.get("primary_error")
        return isinstance(primary_error, dict) and primary_error.get("kind") == "patch"

    def generate(self, packet: dict[str, Any], src_root: Path) -> list[Suggestion]:
        del src_root
        message = primary_message(packet) or "patch failed"
        return [
            Suggestion(
                suggester=self.name,
                title="Refresh or fix the failing patch",
                description=(
                    f"The patch step failed with: `{message}`. Review the rejected hunks "
                    "against the current source tree before regenerating the patch."
                ),
                patch_content=None,
                target_files=[],
                confidence="advisory",
                risks=[
                    (
                        "Regenerating a patch without checking the upstream source may drop "
                        "intended changes."
                    ),
                    "Applying a patch with fuzz can hide semantic conflicts.",
                ],
                manual_steps=[
                    "Check the build directory for `.rej` files and failed hunk context.",
                    "Open the patch referenced by the spec `%patch` line.",
                    "Rebase or regenerate the patch against the current source tree.",
                    "Re-run the workflow after updating the patch file.",
                ],
            )
        ]
