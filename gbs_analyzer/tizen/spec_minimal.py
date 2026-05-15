"""Minimal RPM spec parser for M4."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

TAG_RE = re.compile(r"^\s*(?P<tag>BuildRequires|Patch\d*|Source\d*)\s*:\s*(?P<value>.*?)\s*$")
SECTION_RE = re.compile(r"^\s*%(?P<name>[A-Za-z][A-Za-z0-9_]*)\b(?P<args>.*)$")
PHASE_MARKER_RE = re.compile(r"^\+\s+%(?P<phase>[A-Za-z][A-Za-z0-9_]*)\b")
SHELL_COMMAND_RE = re.compile(r"^\+\s+(?P<command>.+?)\s*$")


class SpecMinimalParser:
    """Parse the v0.5 minimal subset of a Tizen RPM spec file.

    The parser deliberately does not expand macros, evaluate conditional blocks,
    resolve subpackage ownership, or interpret version constraints.
    """

    def __init__(
        self,
        spec_path: str | Path,
        *,
        buildlog_path: str | Path | None = None,
        buildlog_text: str | None = None,
    ) -> None:
        self.spec_path = Path(spec_path)
        self.spec_text = self.spec_path.read_text(encoding="utf-8")
        self._logical_lines = _join_continuations(self.spec_text.splitlines())
        if buildlog_text is not None:
            self.buildlog_text = buildlog_text
        elif buildlog_path is not None:
            self.buildlog_text = Path(buildlog_path).read_text(encoding="utf-8")
        else:
            self.buildlog_text = ""

    @staticmethod
    def find_spec_file(package: str, src_root: str | Path) -> Path:
        """Return the package spec path from a source root.

        Exact `<package>.spec` matches win. If there is only one spec file in the
        tree, it is accepted as a fallback. Ambiguous source roots raise a
        `ValueError` rather than guessing.
        """

        root = Path(src_root)
        if not root.exists():
            raise FileNotFoundError(f"src_root does not exist: {root}")

        specs = sorted(root.rglob("*.spec"))
        exact = [path for path in specs if path.name == f"{package}.spec"]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            raise ValueError(f"ambiguous spec files for package {package}: {exact}")
        if len(specs) == 1:
            return specs[0]
        if not specs:
            raise FileNotFoundError(f"no spec file found under {root}")
        raise ValueError(f"ambiguous spec files under {root}: {specs}")

    def extract_buildrequires(self) -> list[str]:
        """Return raw BuildRequires entries without version semantic parsing."""

        entries: list[str] = []
        for tag, value in self._iter_tags("BuildRequires"):
            del tag
            entries.extend(_split_tag_values(value))
        return entries

    def extract_patches(self) -> list[dict[str, Any]]:
        """Return Patch tags as raw spec declarations."""

        patches: list[dict[str, Any]] = []
        for tag, value in self._iter_tags("Patch"):
            patches.append(_tag_dict(tag, value))
        return patches

    def extract_sources(self) -> list[dict[str, Any]]:
        """Return Source tags as raw spec declarations."""

        sources: list[dict[str, Any]] = []
        for tag, value in self._iter_tags("Source"):
            sources.append(_tag_dict(tag, value))
        return sources

    def extract_section(self, name: str) -> str:
        """Return the body of the first matching spec section."""

        target = _normalize_section_name(name)
        lines = self.spec_text.splitlines()
        start: int | None = None
        for index, line in enumerate(lines):
            match = SECTION_RE.match(line)
            if match and match.group("name").lower() == target:
                start = index + 1
                break
        if start is None:
            return ""

        end = len(lines)
        for index in range(start, len(lines)):
            match = SECTION_RE.match(lines[index])
            if match and _is_top_level_section(match.group("name")):
                end = index
                break
        return "\n".join(lines[start:end]).strip("\n")

    def extract_section_failure_context(self, phase: str) -> dict[str, str]:
        """Locate the last shell command and its output within a failed phase."""

        section_text = self.extract_section(phase)
        if not self.buildlog_text:
            return {
                "last_command": "",
                "last_command_output": "",
                "spec_section_text": section_text,
            }

        phase_lines = _phase_window(self.buildlog_text.splitlines(), _normalize_section_name(phase))
        command_index: int | None = None
        last_command = ""
        for index, line in enumerate(phase_lines):
            command_match = SHELL_COMMAND_RE.match(line)
            if not command_match or PHASE_MARKER_RE.match(line):
                continue
            command_index = index
            last_command = command_match.group("command")

        if command_index is None:
            output_lines: list[str] = []
        else:
            output_lines = []
            for line in phase_lines[command_index + 1 :]:
                if SHELL_COMMAND_RE.match(line):
                    break
                output_lines.append(line)

        return {
            "last_command": last_command,
            "last_command_output": "\n".join(output_lines).strip("\n"),
            "spec_section_text": section_text,
        }

    def get_parse_status(self) -> dict[str, Any]:
        """Return v0.5 uncertainty markers for the minimal spec parser."""

        return {
            "macro_expanded": False,
            "condition_evaluated": False,
            "subpackage_resolved": False,
            "confidence": "partial",
            "warnings": self._collect_warnings(),
        }

    def _iter_tags(self, prefix: str) -> list[tuple[str, str]]:
        matches: list[tuple[str, str]] = []
        for line in self._logical_lines:
            cleaned = _strip_comment(line)
            if not cleaned:
                continue
            match = TAG_RE.match(cleaned)
            if match and match.group("tag").lower().startswith(prefix.lower()):
                matches.append((match.group("tag"), match.group("value").strip()))
        return matches

    def _collect_warnings(self) -> list[str]:
        warnings: list[str] = []
        if "%{" in self.spec_text:
            warnings.append("macros_present_not_expanded")
        if any(re.match(r"^\s*%if", line) for line in self.spec_text.splitlines()):
            warnings.append("conditionals_present_not_evaluated")
        if any(re.match(r"^\s*%package\b", line) for line in self.spec_text.splitlines()):
            warnings.append("subpackages_present_not_resolved")
        return warnings


def _join_continuations(lines: list[str]) -> list[str]:
    logical: list[str] = []
    current = ""
    for line in lines:
        stripped = line.rstrip()
        if stripped.endswith("\\"):
            current += stripped[:-1].rstrip() + " "
            continue
        logical.append((current + stripped).strip())
        current = ""
    if current:
        logical.append(current.strip())
    return logical


def _strip_comment(line: str) -> str:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return ""
    return re.sub(r"\s+#.*$", "", stripped).strip()


def _split_tag_values(value: str) -> list[str]:
    return [entry.strip() for entry in value.split(",") if entry.strip()]


def _tag_dict(tag: str, value: str) -> dict[str, Any]:
    suffix = tag.removeprefix("Patch").removeprefix("Source")
    index = int(suffix) if suffix.isdigit() else None
    return {"tag": tag, "index": index, "value": value}


def _normalize_section_name(name: str) -> str:
    return name.strip().removeprefix("%").lower()


def _is_top_level_section(name: str) -> bool:
    return name.lower() in {
        "prep",
        "build",
        "install",
        "check",
        "clean",
        "files",
        "package",
        "description",
        "changelog",
        "pre",
        "post",
        "preun",
        "postun",
        "pretrans",
        "posttrans",
    }


def _phase_window(lines: list[str], phase: str) -> list[str]:
    start = 0
    for index, line in enumerate(lines):
        match = PHASE_MARKER_RE.match(line)
        if match and match.group("phase").lower() == phase:
            start = index + 1
            break
    else:
        return lines

    end = len(lines)
    for index in range(start, len(lines)):
        if PHASE_MARKER_RE.match(lines[index]):
            end = index
            break
    return lines[start:end]
