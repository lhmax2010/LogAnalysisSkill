"""Safety checks for patch-suggest edit specs before build verification."""

from __future__ import annotations

import os
import posixpath
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EDIT_SPEC_SCHEMA = "gbs_patch_suggest/edit-spec/v1"


class EditSpecViolation(ValueError):
    """Raised when an edit spec is unsafe or malformed."""


@dataclass(frozen=True)
class _LocatedEdit:
    file_path: Path
    start: int
    end: int


def validate_edit_spec(edit_spec: dict[str, Any], worktree_root: str) -> None:
    """Validate schema, nofollow path boundaries, and overlapping edits."""

    edits = _validate_schema(edit_spec)
    root = Path(worktree_root).resolve()
    located_by_file: dict[Path, list[_LocatedEdit]] = defaultdict(list)

    for edit in edits:
        target = _validate_target_path(str(edit["file"]), root)
        old = str(edit["old"])
        located_by_file[target].append(_locate_edit(target, old, edit.get("line")))

    for file_path, located_edits in located_by_file.items():
        _check_no_overlaps(file_path, located_edits)


def _validate_schema(edit_spec: dict[str, Any]) -> list[dict[str, Any]]:
    if edit_spec.get("schema_version") != EDIT_SPEC_SCHEMA:
        raise EditSpecViolation("unsupported edit_spec schema_version")
    patch_name = edit_spec.get("patch_name")
    if not isinstance(patch_name, str) or not patch_name:
        raise EditSpecViolation("edit_spec patch_name must be a non-empty string")
    edits = edit_spec.get("edits")
    if not isinstance(edits, list) or not edits:
        raise EditSpecViolation("edit_spec edits must be a non-empty list")
    validated: list[dict[str, Any]] = []
    for index, raw_edit in enumerate(edits):
        if not isinstance(raw_edit, dict):
            raise EditSpecViolation(f"edit {index} must be an object")
        for required in ("file", "old", "new"):
            if required not in raw_edit:
                raise EditSpecViolation(f"edit {index} missing required field: {required}")
        if not isinstance(raw_edit["file"], str) or not raw_edit["file"]:
            raise EditSpecViolation(f"edit {index} file must be a non-empty string")
        if not isinstance(raw_edit["old"], str) or raw_edit["old"] == "":
            raise EditSpecViolation(f"edit {index} old must be a non-empty string")
        if not isinstance(raw_edit["new"], str):
            raise EditSpecViolation(f"edit {index} new must be a string")
        line = raw_edit.get("line")
        if line is not None and (not isinstance(line, int) or line <= 0):
            raise EditSpecViolation(f"edit {index} line must be a positive integer")
        validated.append(raw_edit)
    return validated


def _validate_target_path(file_value: str, root: Path) -> Path:
    normalized = unicodedata.normalize("NFC", file_value)
    if normalized == "":
        raise EditSpecViolation("edit file path is empty")
    if normalized.startswith("/") or os.path.isabs(normalized):
        raise EditSpecViolation("absolute edit file paths are not allowed")

    norm = posixpath.normpath(normalized.replace("\\", "/"))
    if norm in ("", "."):
        raise EditSpecViolation("edit file path is empty")
    if norm == ".." or norm.startswith("../"):
        raise EditSpecViolation("edit file path escapes the worktree")
    parts = tuple(part for part in norm.split("/") if part and part != ".")
    if any(part == ".." for part in parts):
        raise EditSpecViolation("edit file path contains parent traversal")
    if ".git" in parts:
        raise EditSpecViolation("edit file path targets .git internals")

    current = root
    root_real = root.resolve()
    for part in parts:
        current = current / part
        if current.is_symlink():
            real = current.resolve()
            if not _is_relative_to(real, root_real):
                raise EditSpecViolation(f"edit file path symlink escapes worktree: {file_value}")

    if not _is_relative_to(current.resolve(), root_real):
        raise EditSpecViolation("edit file path escapes the worktree")
    if not current.exists():
        raise EditSpecViolation(f"edit target does not exist: {file_value}")
    if current.is_dir():
        raise EditSpecViolation(f"edit target is a directory: {file_value}")
    if not current.is_file():
        raise EditSpecViolation(f"edit target is not a regular file: {file_value}")
    return current


def _locate_edit(file_path: Path, old: str, line: object) -> _LocatedEdit:
    text = file_path.read_text(encoding="utf-8", errors="surrogateescape")
    if isinstance(line, int):
        start = _find_old_from_line(text, old, line)
    else:
        start = _find_unique_old(text, old)
    return _LocatedEdit(file_path=file_path, start=start, end=start + len(old))


def _find_old_from_line(text: str, old: str, line: int) -> int:
    line_starts = _line_starts(text)
    if line > len(line_starts):
        raise EditSpecViolation(f"edit line {line} is outside the target file")
    line_start = line_starts[line - 1]
    next_line_start = line_starts[line] if line < len(line_starts) else len(text)
    found = text.find(old, line_start)
    if found < 0:
        raise EditSpecViolation("edit old text was not found at or after the requested line")
    if "\n" not in old and found >= next_line_start:
        raise EditSpecViolation("edit old text was not found on the requested line")
    return found


def _find_unique_old(text: str, old: str) -> int:
    first = text.find(old)
    if first < 0:
        raise EditSpecViolation("edit old text was not found")
    second = text.find(old, first + 1)
    if second >= 0:
        raise EditSpecViolation("edit old text is not unique without a line anchor")
    return first


def _line_starts(text: str) -> list[int]:
    starts = [0]
    for index, char in enumerate(text):
        if char == "\n" and index + 1 < len(text):
            starts.append(index + 1)
    return starts


def _check_no_overlaps(file_path: Path, edits: list[_LocatedEdit]) -> None:
    sorted_edits = sorted(edits, key=lambda edit: edit.start)
    previous: _LocatedEdit | None = None
    for edit in sorted_edits:
        if previous is not None and edit.start < previous.end:
            raise EditSpecViolation(f"overlapping edits for {file_path}")
        previous = edit


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
