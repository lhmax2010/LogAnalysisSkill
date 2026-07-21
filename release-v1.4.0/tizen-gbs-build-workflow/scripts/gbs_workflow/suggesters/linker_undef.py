"""Advisory suggestions for undefined reference failures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gbs_workflow.suggesters._common import (
    first_regex_group,
    primary_file_line,
    primary_message,
)
from gbs_workflow.suggesters.base import SuggesterBase, Suggestion


class LinkerUndefSuggester(SuggesterBase):
    """Guide users through undefined-reference investigation."""

    name = "linker_undef"

    def matches(self, packet: dict[str, Any]) -> bool:
        primary_error = packet.get("primary_error")
        return isinstance(primary_error, dict) and primary_error.get("kind") == "linker_undef"

    def generate(self, packet: dict[str, Any], src_root: Path) -> list[Suggestion]:
        del src_root
        symbol = parse_undefined_symbol(packet) or "<symbol>"
        location = primary_file_line(packet)
        return [
            Suggestion(
                suggester=self.name,
                title=f"Resolve undefined reference to {symbol}",
                description=(
                    f"The link step cannot resolve `{symbol}`. This usually means the "
                    "object file that defines the symbol is not linked, the declaration and "
                    "definition differ, or a required library flag is missing."
                ),
                patch_content=None,
                target_files=[] if location == "n/a" else [location],
                confidence="advisory",
                risks=[
                    (
                        "Adding a library flag without checking object ownership can mask "
                        "build-system bugs."
                    ),
                    "The same symbol name may exist in multiple optional libraries.",
                ],
                manual_steps=[
                    f"Inspect the reference location: {location}.",
                    "Find where the symbol should be defined and confirm that object is built.",
                    "Check whether the final link command includes the object or required -l flag.",
                    "If the symbol is optional, verify the related feature macro/config option.",
                ],
            )
        ]


def parse_undefined_symbol(packet: dict[str, Any]) -> str | None:
    """Extract an undefined symbol from linker text."""

    return first_regex_group(
        [
            r"undefined reference to [`'\"]([^`'\"]+)[`'\"]",
            r"undefined reference to\s+([A-Za-z_][A-Za-z0-9_@.]*)",
        ],
        primary_message(packet),
    )
