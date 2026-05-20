"""Suggestions for missing link libraries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gbs_analyzer.tizen.spec_minimal import SpecMinimalParser
from gbs_workflow.suggesters._common import first_regex_group, primary_message, relative_path
from gbs_workflow.suggesters.base import SuggesterBase, Suggestion
from gbs_workflow.suggesters.depsolve import add_buildrequires_line, make_git_diff


class LinkerMissingSuggester(SuggesterBase):
    """Generate low-confidence BuildRequires guidance for missing `-l` failures."""

    name = "linker_missing"

    def matches(self, packet: dict[str, Any]) -> bool:
        primary_error = packet.get("primary_error")
        return isinstance(primary_error, dict) and primary_error.get("kind") == "linker_missing"

    def generate(self, packet: dict[str, Any], src_root: Path) -> list[Suggestion]:
        library = parse_missing_library(packet)
        if library is None:
            return [manual_linker_missing_suggestion(packet)]

        candidate = candidate_devel_package(library)
        package = str(packet.get("package") or "unknown")
        try:
            spec_path = SpecMinimalParser.find_spec_file(package, src_root)
        except FileNotFoundError:
            return [manual_linker_missing_suggestion(packet, library=library, candidate=candidate)]

        relative_spec = relative_path(spec_path, src_root)
        original_text = spec_path.read_text(encoding="utf-8")
        updated_text = add_buildrequires_line(original_text, candidate)
        patch = make_git_diff(Path(relative_spec), original_text, updated_text)
        return [
            Suggestion(
                suggester=self.name,
                title=f"Try BuildRequires candidate {candidate}",
                description=(
                    f"The linker reports a missing library `{library}`. This patch adds "
                    f"`BuildRequires: {candidate}` as a low-confidence candidate. Also check "
                    "whether the link command needs a `-L` search path or a different Tizen "
                    "provider package."
                ),
                patch_content=patch,
                target_files=[relative_spec],
                confidence="low",
                risks=[
                    "The guessed -devel package name may not exist in the enabled repositories.",
                    "The true fix may be adding a library search path rather than a BuildRequires.",
                ],
                manual_steps=[
                    "Review the generated candidate patch before applying it.",
                    "Check the link command for missing or incorrect -L paths.",
                    (
                        "Search the Tizen repository metadata for the package that provides "
                        "the library."
                    ),
                ],
            )
        ]


def parse_missing_library(packet: dict[str, Any]) -> str | None:
    """Extract a missing library token from the primary error message."""

    return first_regex_group(
        [
            r"cannot find\s+-l([A-Za-z0-9_+.-]+)",
            r"cannot find\s+(lib[A-Za-z0-9_+-]+)(?:\.so)?",
            r"library not found for\s+-l([A-Za-z0-9_+.-]+)",
        ],
        primary_message(packet),
    )


def candidate_devel_package(library: str) -> str:
    """Return a conservative -devel package guess for a library token."""

    clean = library
    if clean.startswith("lib"):
        clean = clean[3:]
    clean = clean.removesuffix(".so")
    return f"lib{clean}-devel"


def manual_linker_missing_suggestion(
    packet: dict[str, Any],
    *,
    library: str | None = None,
    candidate: str | None = None,
) -> Suggestion:
    """Return advisory guidance when no safe candidate patch can be generated."""

    details = f" for `{library}`" if library else ""
    candidate_step = (
        f"Check whether `{candidate}` or a profile-specific package provides the library."
        if candidate
        else "Identify the package that provides the missing library."
    )
    return Suggestion(
        suggester=LinkerMissingSuggester.name,
        title=f"Review missing linker library{details}",
        description=(
            f"The linker reports a missing library{details}. No safe patch was generated, "
            "so review the link command and repository provider manually."
        ),
        patch_content=None,
        target_files=[],
        confidence="low",
        risks=[
            "The missing library may come from a package with a profile-specific name.",
            "Adding the wrong BuildRequires may hide the real link command issue.",
        ],
        manual_steps=[
            candidate_step,
            "Check the failing link command for missing -L paths.",
            "Review analyzer_output/evidence_packet.md for the full link evidence.",
        ],
    )
