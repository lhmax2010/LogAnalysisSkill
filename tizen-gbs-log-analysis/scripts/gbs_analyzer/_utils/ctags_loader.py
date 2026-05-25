"""ctags-backed source context extraction with deterministic fallbacks."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CtagsRunner = Callable[[Path], str]

FUNCTION_RE = re.compile(
    r"^\s*(?:[A-Za-z_][\w:<>,~*&\s]+\s+)+(?P<name>[A-Za-z_~]\w*)\s*\([^;]*\)\s*(?:const\s*)?\{?\s*$"
)


@dataclass(frozen=True)
class SourceContext:
    path: str
    start_line: int
    end_line: int
    text: str
    extraction_method: str
    degraded: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "text": self.text,
            "extraction_method": self.extraction_method,
            "degraded": self.degraded,
        }


def extract_source_context(
    path: str | Path,
    *,
    line: int | None = None,
    symbol: str | None = None,
    window: int = 30,
    ctags_runner: CtagsRunner | None = None,
) -> SourceContext:
    """Extract source context using ctags, regex brace pairing, then line window."""

    source_path = Path(path)
    lines = source_path.read_text(encoding="utf-8", errors="replace").splitlines()

    ctags_context = _context_from_ctags(
        source_path,
        lines,
        line=line,
        symbol=symbol,
        runner=ctags_runner,
    )
    if ctags_context is not None:
        return ctags_context

    regex_context = _context_from_regex(source_path, lines, line=line, symbol=symbol)
    if regex_context is not None:
        return regex_context

    return _context_from_window(source_path, lines, line=line, window=window)


def default_ctags_runner(path: Path) -> str:
    """Run universal-ctags for one source file."""

    completed = subprocess.run(
        ["ctags", "--output-format=json", "-f", "-", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _context_from_ctags(
    source_path: Path,
    lines: list[str],
    *,
    line: int | None,
    symbol: str | None,
    runner: CtagsRunner | None,
) -> SourceContext | None:
    active_runner = runner or default_ctags_runner
    try:
        tags = [_parse_tag(raw) for raw in active_runner(source_path).splitlines() if raw.strip()]
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
        return None

    candidates = [tag for tag in tags if tag is not None and tag.get("line")]
    if symbol:
        candidates = [tag for tag in candidates if tag.get("name") == symbol] or candidates
    if line is not None:
        before_line = [tag for tag in candidates if int(tag["line"]) <= line]
        if before_line:
            candidates = [max(before_line, key=lambda tag: int(tag["line"]))]
    if not candidates:
        return None

    start = max(1, int(candidates[0]["line"]))
    end = _brace_end(lines, start) or min(len(lines), start + 30)
    return _slice(source_path, lines, start, end, "ctags")


def _parse_tag(raw: str) -> dict[str, Any] | None:
    parsed = json.loads(raw)
    return parsed if isinstance(parsed, dict) else None


def _context_from_regex(
    source_path: Path,
    lines: list[str],
    *,
    line: int | None,
    symbol: str | None,
) -> SourceContext | None:
    functions: list[tuple[int, int, str]] = []
    for index, text in enumerate(lines, start=1):
        match = FUNCTION_RE.match(text)
        if not match:
            continue
        end = _brace_end(lines, index)
        if end is not None:
            functions.append((index, end, match.group("name")))

    for start, end, name in functions:
        if symbol and name == symbol:
            return _slice(source_path, lines, start, end, "regex_brace")
        if line is not None and start <= line <= end:
            return _slice(source_path, lines, start, end, "regex_brace")
    return None


def _brace_end(lines: list[str], start_line: int) -> int | None:
    depth = 0
    saw_open = False
    for index in range(start_line, len(lines) + 1):
        text = lines[index - 1]
        depth += text.count("{")
        if "{" in text:
            saw_open = True
        depth -= text.count("}")
        if saw_open and depth <= 0:
            return index
    return None


def _context_from_window(
    source_path: Path,
    lines: list[str],
    *,
    line: int | None,
    window: int,
) -> SourceContext:
    center = line if line is not None else 1
    start = max(1, center - window)
    end = min(len(lines), center + window)
    return _slice(source_path, lines, start, end, "line_window", degraded=True)


def _slice(
    source_path: Path,
    lines: list[str],
    start: int,
    end: int,
    method: str,
    *,
    degraded: bool = False,
) -> SourceContext:
    return SourceContext(
        path=str(source_path),
        start_line=start,
        end_line=end,
        text="\n".join(lines[start - 1 : end]),
        extraction_method=method,
        degraded=degraded,
    )
