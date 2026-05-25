"""Shared helpers for evidence collectors."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def command_summary(command: dict[str, Any] | None) -> dict[str, Any] | None:
    if command is None:
        return None
    return {
        "id": command.get("id"),
        "phase": command.get("phase"),
        "argv_short": command.get("argv_short"),
        "argv_full": command.get("argv_full"),
        "rsp_expanded": command.get("rsp_expanded"),
        "command_degraded": command.get("command_degraded", False),
    }


def source_path(src_root: Path | None, event: dict[str, Any]) -> Path | None:
    file_value = event.get("file")
    if not isinstance(file_value, str) or not file_value:
        return None
    path = Path(file_value)
    if path.is_absolute():
        return path
    if src_root is None:
        return None
    return src_root / path


def quoted_symbol(message: str) -> str | None:
    match = re.search(r"[`'\"](?P<symbol>[A-Za-z_]\w*)[`'\"]", message)
    return match.group("symbol") if match else None


def search_header_declarations(src_root: Path | None, symbol: str | None) -> list[dict[str, Any]]:
    if src_root is None or not symbol:
        return []
    declarations: list[dict[str, Any]] = []
    pattern = re.compile(rf"\b{re.escape(symbol)}\b")
    for path in sorted(src_root.rglob("*")):
        if path.suffix not in {".h", ".hh", ".hpp", ".hxx"}:
            continue
        for line_no, text in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(),
            start=1,
        ):
            if pattern.search(text):
                declarations.append(
                    {"path": str(path), "line": line_no, "text": text.strip()}
                )
                break
        if len(declarations) >= 5:
            break
    return declarations


def parse_missing_dependency(message: str) -> dict[str, str | None]:
    match = re.search(r"nothing provides\s+(?P<dep>.+?)(?:\s+needed by\s+(?P<pkg>\S+))?$", message)
    if not match:
        return {"dependency": message.strip(), "needed_by": None}
    return {
        "dependency": match.group("dep").strip(),
        "needed_by": match.group("pkg"),
    }


def profile_hint(scan_result: dict[str, Any]) -> str | None:
    buildlog_path = scan_result.get("buildlog_path")
    if isinstance(buildlog_path, str) and "profile" in buildlog_path.lower():
        return Path(buildlog_path).stem
    return None
