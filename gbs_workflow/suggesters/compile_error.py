"""Advisory suggestions for compiler diagnostics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gbs_workflow.suggesters._common import primary_error, primary_file_line, primary_message
from gbs_workflow.suggesters.base import SuggesterBase, Suggestion


class CompileErrorSuggester(SuggesterBase):
    """Guide users through compile-error investigation."""

    name = "compile_error"

    def matches(self, packet: dict[str, Any]) -> bool:
        error = primary_error(packet)
        return error.get("kind") == "compiler"

    def generate(self, packet: dict[str, Any], src_root: Path) -> list[Suggestion]:
        del src_root
        error = primary_error(packet)
        location = primary_file_line(packet)
        semantic_class = error.get("semantic_class") or error.get("category") or "unknown"
        message = primary_message(packet) or "compiler diagnostic"
        return [
            Suggestion(
                suggester=self.name,
                title=f"Inspect compiler error at {location}",
                description=(
                    f"The compiler reported `{message}` at `{location}`. Analyzer semantic "
                    f"class: `{semantic_class}`. This advisory does not edit source code."
                ),
                patch_content=None,
                target_files=[] if location == "n/a" else [location],
                confidence="advisory",
                risks=[
                    (
                        "Compiler errors often need source-level intent that workflow cannot "
                        "infer safely."
                    ),
                    "Fixing the first diagnostic may reveal later diagnostics.",
                ],
                manual_steps=[
                    f"Open `{location}` and inspect the reported line and nearby declarations.",
                    "Read evidence_packet.md for the compile command and include context.",
                    "Apply the source fix manually, then re-run the workflow.",
                ],
            )
        ]
