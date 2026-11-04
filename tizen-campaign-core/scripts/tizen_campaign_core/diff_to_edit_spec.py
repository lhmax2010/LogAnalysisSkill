"""Strict unified-diff conversion; no patch application or fuzzy matching."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tizen_build_verify.edit_spec_guard import (
    EDIT_SPEC_SCHEMA,
    EditSpecViolation,
    validate_edit_spec,
)

_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:.*)\n?$")
_P4 = re.compile(r"^==== (//.+?)#\d+(?: - (//.+?)#\d+| \(([^\n]+)\))? ====$")
_UNSUPPORTED = (
    ("rename from ", "rename"), ("rename to ", "rename"),
    ("copy from ", "copy"), ("copy to ", "copy"),
    ("GIT binary patch", "binary"), ("Binary files ", "binary"),
    ("old mode ", "mode_change"), ("new mode ", "mode_change"),
    ("new file mode ", "new_file"), ("deleted file mode ", "deleted_file"),
)


class DiffUnsupported(ValueError):
    """A diff cannot be represented exactly by the existing edit-spec contract."""


@dataclass
class _Hunk:
    start: int
    old: str
    new: str


@dataclass
class _File:
    before: str
    after: str
    depot: bool = False
    hunks: list[_Hunk] = field(default_factory=list)


def _header(line: str) -> str:
    value = line[4:].rstrip("\n")
    # Unified headers use a tab before timestamps; accept the conventional space date too.
    return re.split(r"\t| +(?=\d{4}-\d\d-\d\d[ T])", value, maxsplit=1)[0]


def _hunk(lines: list[str], index: int) -> tuple[_Hunk, int]:
    match = _HUNK.fullmatch(lines[index])
    if match is None:
        raise DiffUnsupported("malformed_hunk_header")
    start, count, new_start, new_count = (
        int(match[1]), int(match[2] or 1), int(match[3]), int(match[4] or 1)
    )
    if count == 0:
        raise DiffUnsupported("empty_old_hunk")
    if start < 1 or (new_count and new_start < 1):
        raise DiffUnsupported("invalid_hunk_line")
    index += 1
    old: list[str] = []
    new: list[str] = []
    changed = False
    last = ""
    marked = False
    while index < len(lines):
        line = lines[index]
        if line == "\\ No newline at end of file\n" or line == "\\ No newline at end of file":
            if not last or marked:
                raise DiffUnsupported("malformed_no_newline_marker")
            if last in " -":
                old[-1] = old[-1].removesuffix("\n")
            if last in " +":
                new[-1] = new[-1].removesuffix("\n")
            marked = True
            index += 1
            continue
        if len(old) == count and len(new) == new_count:
            break
        if not line or line[0] not in " +-" or not line.endswith("\n"):
            raise DiffUnsupported("malformed_hunk_body")
        last, marked = line[0], False
        if last in " -":
            old.append(line[1:])
        if last in " +":
            new.append(line[1:])
        changed = changed or last in "+-"
        if len(old) > count or len(new) > new_count:
            raise DiffUnsupported("hunk_count_mismatch")
        index += 1
    if len(old) != count or len(new) != new_count or not changed:
        raise DiffUnsupported("hunk_count_mismatch_or_no_change")
    return _Hunk(start, "".join(old), "".join(new)), index


def _parse(diff: str) -> list[_File]:
    if "\x00" in diff:
        raise DiffUnsupported("binary")
    lines = diff.splitlines(keepends=True)
    files: list[_File] = []
    current: _File | None = None
    index = 0
    pending_git = False
    while index < len(lines):
        line = lines[index]
        for prefix, reason in _UNSUPPORTED:
            if line.startswith(prefix):
                raise DiffUnsupported(reason)
        if line.startswith("diff --git "):
            if pending_git:
                raise DiffUnsupported("file_without_hunks")
            pending_git, current = True, None
        elif line.startswith("==== "):
            match = _P4.fullmatch(line.rstrip("\n"))
            if match is None:
                raise DiffUnsupported("unsupported_p4_header")
            if match[2] is not None and match[2] != match[1]:
                raise DiffUnsupported("rename")
            if match[3] is not None and "binary" in match[3]:
                raise DiffUnsupported("binary")
            current = _File(match[1], match[1], depot=True)
            files.append(current)
        elif line.startswith("--- "):
            if index + 1 >= len(lines) or not lines[index + 1].startswith("+++ "):
                raise DiffUnsupported("missing_new_header")
            before, after = _header(line), _header(lines[index + 1])
            if before == "/dev/null":
                raise DiffUnsupported("new_file")
            if after == "/dev/null":
                raise DiffUnsupported("deleted_file")
            current = _File(before, after)
            files.append(current)
            pending_git = False
            index += 1
        elif line.startswith("@@"):
            if current is None:
                raise DiffUnsupported("hunk_without_file")
            hunk, index = _hunk(lines, index)
            current.hunks.append(hunk)
            continue
        elif line.startswith(("+++ ", "+", "-", " ")) and current and current.hunks:
            raise DiffUnsupported("unparsed_patch_content")
        elif line.strip() and not line.startswith(("index ", "Index: ", "===", "diff ")):
            # Mail/OBS descriptions are allowed only before the first file.
            if files or pending_git:
                raise DiffUnsupported("unparsed_patch_content")
        index += 1
    if pending_git or not files or any(not file.hunks for file in files):
        raise DiffUnsupported("empty_diff_or_file_without_hunks")
    return files


def _parts(path: str, depot: bool) -> list[str]:
    path = unicodedata.normalize("NFC", path).replace("\\", "/")
    if depot and path.startswith("//"):
        path = path[2:]
    if not path or path.startswith(("/", '"')) or re.match(r"^[A-Za-z]:", path):
        raise DiffUnsupported("unsafe_or_unsupported_path")
    parts = path.split("/")
    if any(part in {"", ".", "..", ".git"} for part in parts):
        raise DiffUnsupported("unsafe_path_component")
    return parts


def _paths(files: list[_File], root: Path) -> list[str]:
    pairs = [(_parts(file.before, file.depot), _parts(file.after, file.depot)) for file in files]
    # One strip level must identify every file. Never select by hunk contents.
    candidates: list[list[str]] = []
    limit = min(min(len(a), len(b)) for a, b in pairs)
    for strip in range(limit):
        paths = ["/".join(a[strip:]) for a, _ in pairs]
        if any(a[strip:] != b[strip:] for a, b in pairs):
            continue
        if all((root / path).is_file() for path in paths):
            candidates.append(paths)
    if len(candidates) != 1:
        raise DiffUnsupported("path_strip_ambiguous" if candidates else "path_strip_unresolved")
    return candidates[0]


def convert(diff: str, src_root: Path, patch_name: str) -> dict[str, Any]:
    """Return a validated edit-spec without modifying source or writing output."""
    if not patch_name or not src_root.is_dir():
        raise ValueError("patch_name must be non-empty and src_root must be a directory")
    files = _parse(diff)
    paths = _paths(files, src_root)
    edits: list[dict[str, Any]] = []
    for file, path in zip(files, paths, strict=True):
        for hunk in file.hunks:
            edits.append(dict(file=path, old=hunk.old, new=hunk.new, line=hunk.start))
    result = dict(schema_version=EDIT_SPEC_SCHEMA, patch_name=patch_name, edits=edits)
    try:
        # Guard checks boundaries before converter reads the source for exact hunk matching.
        validate_edit_spec(result, str(src_root))
        for edit in edits:
            text = (src_root / edit["file"]).read_text(encoding="utf-8", errors="surrogateescape")
            lines = text.splitlines(keepends=True)
            start = sum(len(line) for line in lines[:edit["line"] - 1])
            old = str(edit["old"])
            if text[start:start + len(old)] != old:
                raise DiffUnsupported("hunk_context_mismatch_no_fuzz")
            if text.find(old, text.find(old) + 1) < 0:
                del edit["line"]
        validate_edit_spec(result, str(src_root))
    except EditSpecViolation as exc:
        raise DiffUnsupported("guard_rejected: " + str(exc)) from exc
    return result
