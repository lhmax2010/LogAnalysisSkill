"""Resolve .spec toolchain flag compatibility fixes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from gbs_patch_suggest.spec_toolchain_flag_ingest import SpecToolchainFlagDiagnostic

BUILD_SECTION_RE = re.compile(r"^\s*%build\b")
TOP_LEVEL_SECTION_RE = re.compile(
    r"^\s*%"
    r"(prep|build|install|check|clean|files|package|description|changelog|"
    r"pre|post|preun|postun|pretrans|posttrans)\b"
)
FLAG_ASSIGN_RE = re.compile(r"\b(?:export\s+)?(?:CFLAGS|CXXFLAGS)\b\s*(?:=|\+=)")
CONSUMER_RE = re.compile(
    r"^\s*(?:%(?:cmake|configure|make|meson)\b|(?:cmake|configure|make|meson|ninja)(?:\s|$))"
)
CLANG_IF_RE = re.compile(r"^\s*%if\s+%\{toolchain_is\s+clang\}\s*$")
ENDIF_RE = re.compile(r"^\s*%endif\b")


class UnsafeSpecLayout(ValueError):
    """Spec layout is too ambiguous to patch automatically."""


@dataclass(frozen=True)
class SpecToolchainFlagResolution:
    """Resolved .spec insertion plan or advisory."""

    status: str
    options: tuple[str, ...]
    spec_path: Path | None = None
    spec_relative_path: str | None = None
    insert_after_line: int | None = None
    anchor: str | None = None
    insert: str | None = None
    advisory: str | None = None

    @property
    def patch_ready(self) -> bool:
        return self.status == "spec_toolchain_flag_context_available"


def resolve_spec_toolchain_flags(
    diagnostic: SpecToolchainFlagDiagnostic,
    *,
    src_root: Path | None,
) -> SpecToolchainFlagResolution:
    """Find a safe .spec insertion point for Clang-only flag stripping."""

    if not diagnostic.options:
        return SpecToolchainFlagResolution(status="not_applicable", options=())
    if src_root is None:
        return _advisory(diagnostic.options, "source root unavailable; cannot inspect .spec")
    try:
        spec_path = _find_single_spec(src_root)
    except (FileNotFoundError, ValueError) as exc:
        return _advisory(diagnostic.options, str(exc))

    lines = spec_path.read_text(encoding="utf-8", errors="surrogateescape").splitlines()
    section = _build_section_bounds(lines)
    if section is None:
        return _advisory(diagnostic.options, "no %build section found in .spec")
    start, end = section
    source_lines = _flag_source_lines(lines, start, end, diagnostic.options)
    if not source_lines:
        return _advisory(
            diagnostic.options,
            "unknown options were not found in %build CFLAGS/CXXFLAGS lines",
        )
    consumer_line = _first_consumer_line(lines, start, end)
    if consumer_line is None:
        return _advisory(diagnostic.options, "no flag consumer found in %build section")
    last_source_line = max(source_lines)
    if last_source_line >= consumer_line:
        return _advisory(
            diagnostic.options,
            "CFLAGS/CXXFLAGS option source appears after the first flag consumer",
        )

    try:
        existing_block = _existing_safe_clang_block(lines, last_source_line, consumer_line)
    except UnsafeSpecLayout as exc:
        return _advisory(diagnostic.options, str(exc))
    if existing_block is not None:
        insert_after, existing_lines = existing_block
        insert = _render_strip_block(diagnostic.options, wrap=False, existing_lines=existing_lines)
        if not insert:
            return _advisory(
                diagnostic.options,
                "existing clang toolchain block already strips the unknown options",
            )
    else:
        insert_after = last_source_line
        insert = _render_strip_block(diagnostic.options, wrap=True)
    anchor = lines[insert_after - 1]
    spec_relative = spec_path.resolve().relative_to(src_root.resolve()).as_posix()
    return SpecToolchainFlagResolution(
        status="spec_toolchain_flag_context_available",
        options=diagnostic.options,
        spec_path=spec_path,
        spec_relative_path=spec_relative,
        insert_after_line=insert_after,
        anchor=anchor,
        insert=insert,
    )


def _advisory(options: tuple[str, ...], reason: str) -> SpecToolchainFlagResolution:
    return SpecToolchainFlagResolution(
        status="spec_toolchain_flag_advisory",
        options=options,
        advisory=reason,
    )


def _find_single_spec(src_root: Path) -> Path:
    root = src_root.resolve()
    specs = sorted(
        path
        for path in root.rglob("*.spec")
        if ".git" not in path.parts and not any(part.startswith("GBS-ROOT") for part in path.parts)
    )
    if not specs:
        raise FileNotFoundError(f"no spec file found under {src_root}")
    if len(specs) > 1:
        raise ValueError(f"ambiguous spec files under {src_root}: {specs}")
    return specs[0]


def _build_section_bounds(lines: list[str]) -> tuple[int, int] | None:
    start: int | None = None
    for index, line in enumerate(lines, start=1):
        if BUILD_SECTION_RE.match(line):
            start = index + 1
            break
    if start is None:
        return None
    end = len(lines) + 1
    for index in range(start, len(lines) + 1):
        if TOP_LEVEL_SECTION_RE.match(lines[index - 1]):
            end = index
            break
    return start, end


def _flag_source_lines(
    lines: list[str],
    start: int,
    end: int,
    options: tuple[str, ...],
) -> list[int]:
    matches: list[int] = []
    for index in range(start, end):
        line = lines[index - 1]
        if "${CFLAGS/" in line or "${CXXFLAGS/" in line:
            continue
        if not FLAG_ASSIGN_RE.search(line):
            continue
        if any(option in line for option in options):
            matches.append(index)
    return matches


def _first_consumer_line(lines: list[str], start: int, end: int) -> int | None:
    for index in range(start, end):
        if CONSUMER_RE.match(lines[index - 1]):
            return index
    return None


def _existing_safe_clang_block(
    lines: list[str],
    last_source_line: int,
    consumer_line: int,
) -> tuple[int, set[str]] | None:
    for index in range(last_source_line + 1, consumer_line):
        if not CLANG_IF_RE.match(lines[index - 1]):
            continue
        block_end = _matching_endif(lines, index, consumer_line)
        if block_end is None:
            raise UnsafeSpecLayout(
                "existing clang toolchain block is not safely closed before the flag consumer"
            )
        existing_lines = {line.strip() for line in lines[index:block_end - 1]}
        return block_end - 1, existing_lines
    return None


def _matching_endif(lines: list[str], clang_if_line: int, consumer_line: int) -> int | None:
    depth = 0
    for index in range(clang_if_line, consumer_line):
        line = lines[index - 1]
        if line.lstrip().startswith("%if"):
            depth += 1
        elif ENDIF_RE.match(line):
            depth -= 1
            if depth == 0:
                return index
    return None


def _render_strip_block(
    options: tuple[str, ...],
    *,
    wrap: bool,
    existing_lines: set[str] | None = None,
) -> str:
    lines: list[str] = []
    if wrap:
        lines.extend(["%{?_toolchain:", "%if %{toolchain_is clang}"])
    existing = existing_lines or set()
    for option in options:
        line = f"CFLAGS=${{CFLAGS/{option}/}}"
        if line not in existing:
            lines.append(line)
    for option in options:
        line = f"CXXFLAGS=${{CXXFLAGS/{option}/}}"
        if line not in existing:
            lines.append(line)
    if wrap:
        lines.extend(["%endif", "}"])
    return "\n".join(lines)
