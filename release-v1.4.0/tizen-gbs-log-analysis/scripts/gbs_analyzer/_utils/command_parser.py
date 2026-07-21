"""Command-line parsing helpers for scanner command records."""

from __future__ import annotations

import os
import re
import shlex
from pathlib import Path
from typing import Any

RSP_PATTERN = re.compile(r"(?:^|\s)(?:-Wl,)?@([^\s]+\.rsp)(?:\s|$)")


def join_backslash_continuations(argv_line: str) -> str:
    """Join shell-style backslash continuations into one command line."""

    lines = argv_line.splitlines()
    if not lines:
        return ""

    parts: list[str] = []
    for line in lines:
        stripped = line.rstrip()
        if stripped.endswith("\\"):
            parts.append(stripped[:-1].strip())
        else:
            parts.append(stripped.strip())
    return " ".join(part for part in parts if part)


def read_rsp(path: str | Path, max_rsp_tokens: int = 200) -> str:
    """Read an rsp file and cap the raw token count used by downstream extraction."""

    content = Path(path).read_text(encoding="utf-8", errors="replace")
    return " ".join(content.split()[:max_rsp_tokens])


def extract_relevant_flags(rsp_content: str) -> dict[str, list[str]]:
    """Extract the flag classes required by v0.5 §3.1."""

    flags = shlex.split(rsp_content, posix=True)
    return {
        "libraries": [flag for flag in flags if flag.startswith("-l")],
        "library_paths": [flag for flag in flags if flag.startswith("-L")],
        "other_significant": [
            flag for flag in flags if flag in ("-Werror", "-fPIC", "-shared")
        ],
        "include_paths": [flag for flag in flags if flag.startswith("-I")][:10],
        "defines": [flag for flag in flags if flag.startswith("-D")][:20],
        "objects": [flag for flag in flags if flag.endswith((".o", ".a"))][:30],
    }


def shorten_argv(argv_line: str, limit: int = 200) -> str:
    """Keep commands readable while preserving the start and end."""

    normalized = " ".join(argv_line.split())
    if len(normalized) <= limit:
        return normalized
    head_limit = max(20, limit // 2)
    tail_limit = max(20, limit - head_limit - 5)
    return f"{normalized[:head_limit].rstrip()} ... {normalized[-tail_limit:].lstrip()}"


def parse_command(argv_line: str, cwd: str | Path, max_rsp_tokens: int = 200) -> dict[str, Any]:
    """Parse a scanner command line and expand relevant rsp flags when available."""

    joined = join_backslash_continuations(argv_line)
    rsp_files = RSP_PATTERN.findall(joined)
    rsp_content: dict[str, dict[str, list[str]] | None] = {}
    cwd_path = Path(cwd)

    for rsp_path in rsp_files:
        full_path = Path(rsp_path) if os.path.isabs(rsp_path) else cwd_path / rsp_path
        if full_path.exists():
            rsp_content[rsp_path] = extract_relevant_flags(read_rsp(full_path, max_rsp_tokens))
        else:
            rsp_content[rsp_path] = None

    return {
        "argv_short": shorten_argv(joined),
        "argv_full": joined if len(joined) < 500 else None,
        "rsp_expanded": rsp_content,
        "command_degraded": any(value is None for value in rsp_content.values()),
    }
