"""Depsolve failure suggestions for BuildRequires additions."""

from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Any

from gbs_analyzer.tizen.spec_minimal import SpecMinimalParser

from gbs_workflow.suggesters.base import SuggesterBase, Suggestion

MISSING_DEP_RE = re.compile(
    r"\bnothing provides\s+(?P<dependency>.+?)(?:\s+needed by\b|$)",
    re.IGNORECASE,
)


class DepsolveSuggester(SuggesterBase):
    """Generate a reversible BuildRequires patch for depsolve failures."""

    name = "depsolve"

    def matches(self, packet: dict[str, Any]) -> bool:
        """Return true for depsolve primary errors."""

        primary_error = packet.get("primary_error")
        return isinstance(primary_error, dict) and primary_error.get("kind") == "depsolve"

    def generate(self, packet: dict[str, Any], src_root: Path) -> list[Suggestion]:
        """Generate one BuildRequires patch when the missing dependency is parseable."""

        dependency = parse_missing_dependency(packet)
        if dependency is None:
            return []

        package = str(packet.get("package") or "unknown")
        spec_path = SpecMinimalParser.find_spec_file(package, src_root)
        relative_spec = spec_path.relative_to(src_root)
        original_text = spec_path.read_text(encoding="utf-8")
        if has_buildrequires_dependency(original_text, dependency):
            return [
                Suggestion(
                    suggester=self.name,
                    title=f"Verify repository provider for {dependency}",
                    description=(
                        f"The spec already declares `BuildRequires: {dependency}`, but the "
                        "depsolver still reports that nothing provides it. This usually means "
                        "the dependency name is wrong for the enabled repositories, or the "
                        "repository/profile that provides it is not enabled."
                    ),
                    patch_content=None,
                    target_files=[str(relative_spec)],
                    confidence="advisory",
                    risks=[
                        "Adding another identical BuildRequires line will not fix this failure.",
                        (
                            "The correct provider may use a different package name in this "
                            "Tizen profile."
                        ),
                    ],
                    manual_steps=[
                        "Check whether the package exists in the enabled Tizen repositories.",
                        "Verify the repository/profile configuration used by gbs.",
                        (
                            "If the provider name differs, replace the existing BuildRequires "
                            "entry manually."
                        ),
                    ],
                )
            ]

        updated_text = add_buildrequires_line(original_text, dependency)
        patch = make_git_diff(relative_spec, original_text, updated_text)

        title = f"Add BuildRequires for {dependency}"
        return [
            Suggestion(
                suggester=self.name,
                title=title,
                description=(
                    f"The depsolver reports that nothing provides `{dependency}`. "
                    "This patch adds a matching BuildRequires entry to the package spec."
                ),
                patch_content=patch,
                target_files=[str(relative_spec)],
                confidence="medium",
                risks=[
                    "The dependency name may differ in the enabled Tizen repositories.",
                    (
                        "Adding the BuildRequires is reversible, but the package may still "
                        "be unavailable."
                    ),
                ],
                manual_steps=[
                    "Review the generated patch.",
                    "If you accept it, run git apply on the patch file.",
                    "Re-run the workflow after applying the change.",
                ],
            )
        ]


def parse_missing_dependency(packet: dict[str, Any]) -> str | None:
    """Extract the missing dependency from a depsolve primary error message."""

    primary_error = packet.get("primary_error")
    if not isinstance(primary_error, dict):
        return None
    message = str(primary_error.get("message") or "")
    match = MISSING_DEP_RE.search(message)
    if match is None:
        return None
    dependency = match.group("dependency").strip().rstrip(".,;")
    return dependency or None


def add_buildrequires_line(spec_text: str, dependency: str) -> str:
    """Add a BuildRequires line after the existing BuildRequires block."""

    lines = spec_text.splitlines(keepends=True)
    newline = _detect_newline(spec_text)
    insert_at: int | None = None
    for index, line in enumerate(lines):
        if re.match(r"^\s*BuildRequires\s*:", line):
            insert_at = index + 1
            continue
        if insert_at is not None and line.startswith((" ", "\t")):
            insert_at = index + 1
            continue
        if insert_at is not None:
            break

    if insert_at is None:
        insert_at = _first_section_index(lines)

    new_line = f"BuildRequires:  {dependency}{newline}"
    updated = lines[:insert_at] + [new_line] + lines[insert_at:]
    return "".join(updated)


def has_buildrequires_dependency(spec_text: str, dependency: str) -> bool:
    """Return true when the spec already declares the dependency."""

    normalized_dependency = _normalize_dependency(dependency)
    for line in _buildrequires_lines(spec_text):
        value = line.split(":", 1)[1] if ":" in line else line
        if _normalize_dependency(value) == normalized_dependency:
            return True
    return False


def make_git_diff(relative_path: Path, original_text: str, updated_text: str) -> str:
    """Return a git-apply compatible unified diff for a spec change."""

    path = relative_path.as_posix()
    diff_lines = list(
        difflib.unified_diff(
            original_text.splitlines(keepends=True),
            updated_text.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )
    return f"diff --git a/{path} b/{path}\n" + "".join(diff_lines)


def _detect_newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def _first_section_index(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        if re.match(r"^\s*%[A-Za-z]", line):
            return index
    return len(lines)


def _buildrequires_lines(spec_text: str) -> list[str]:
    return [
        line
        for line in spec_text.splitlines()
        if re.match(r"^\s*BuildRequires\s*:", line, re.IGNORECASE)
    ]


def _normalize_dependency(value: str) -> str:
    return re.sub(r"\s+", "", value.strip()).lower()
