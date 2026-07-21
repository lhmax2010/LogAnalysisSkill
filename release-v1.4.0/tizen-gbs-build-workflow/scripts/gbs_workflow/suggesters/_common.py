"""Shared helpers for workflow Suggesters."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def primary_error(packet: dict[str, Any]) -> dict[str, Any]:
    """Return the primary error object when present."""

    value = packet.get("primary_error")
    return value if isinstance(value, dict) else {}


def primary_kind(packet: dict[str, Any]) -> str:
    """Return the primary error kind."""

    return str(primary_error(packet).get("kind") or "")


def primary_message(packet: dict[str, Any]) -> str:
    """Return the primary error message."""

    return str(primary_error(packet).get("message") or "")


def primary_file_line(packet: dict[str, Any]) -> str:
    """Return a compact file:line location when available."""

    error = primary_error(packet)
    file_name = error.get("file")
    line = error.get("line")
    if file_name and line:
        return f"{file_name}:{line}"
    if file_name:
        return str(file_name)
    return "n/a"


def failed_phase(packet: dict[str, Any]) -> str:
    """Return the failed phase when available."""

    return str(packet.get("failed_phase") or "n/a")


def relative_path(path: Path, src_root: Path) -> str:
    """Return a user-facing path relative to src_root when possible."""

    try:
        return path.relative_to(src_root).as_posix()
    except ValueError:
        return path.as_posix()


def first_regex_group(patterns: list[str], text: str) -> str | None:
    """Return the first captured regex group from text."""

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return str(match.group(1)).strip()
    return None
