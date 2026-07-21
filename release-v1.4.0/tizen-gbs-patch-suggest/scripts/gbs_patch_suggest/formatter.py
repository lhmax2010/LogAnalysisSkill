"""Deterministic patch formatter for explicit edit specs."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

EXIT_SUCCESS = 0
EXIT_FORMATTER_ERROR = 1
EDIT_SPEC_SCHEMA = "gbs_patch_suggest/edit-spec/v1"

SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class Edit:
    """One explicit source edit requested by the outer assistant."""

    file: str
    operation: str
    old: str | None = None
    new: str | None = None
    line: int | None = None
    anchor: str | None = None
    insert: str | None = None
    before: str | None = None
    after: str | None = None


@dataclass(frozen=True)
class EditSpec:
    """Machine-readable edit specification produced by the outer assistant."""

    schema_version: str
    patch_name: str | None
    description: str | None
    edits: tuple[Edit, ...]


@dataclass(frozen=True)
class FormatPatchOptions:
    """Options for formatting an edit spec into a unified diff patch."""

    src_root: Path
    edit_spec: Path
    output: Path
    check: bool = False
    git_binary: str = "git"
    temp_parent: Path | None = None


@dataclass(frozen=True)
class FormatPatchResult:
    """Result of deterministic patch formatting."""

    exit_code: int
    output_path: Path
    error: str | None = None
    error_code: str | None = None
    check_passed: bool = False


@dataclass(frozen=True)
class _ResolvedEdit:
    edit: Edit
    source_path: Path
    relative_path: Path
    start: int
    end: int


@dataclass(frozen=True)
class _Match:
    start: int
    end: int
    start_line: int
    end_line: int


class FormatterError(ValueError):
    """Actionable formatter failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def format_patch(
    options: FormatPatchOptions,
    *,
    subprocess_runner: SubprocessRunner = subprocess.run,
) -> FormatPatchResult:
    """Format an explicit edit spec into a git-apply-compatible patch."""

    try:
        spec = load_edit_spec(options.edit_spec)
        patch_text = build_patch_text(
            spec,
            src_root=options.src_root,
            git_binary=options.git_binary,
            temp_parent=options.temp_parent,
            subprocess_runner=subprocess_runner,
        )
        if options.check:
            _run_git_apply_check(
                patch_text,
                src_root=options.src_root,
                git_binary=options.git_binary,
                subprocess_runner=subprocess_runner,
            )
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(patch_text, encoding="utf-8")
    except FormatterError as exc:
        return FormatPatchResult(
            exit_code=EXIT_FORMATTER_ERROR,
            output_path=options.output,
            error=exc.message,
            error_code=exc.code,
        )
    except OSError as exc:
        return FormatPatchResult(
            exit_code=EXIT_FORMATTER_ERROR,
            output_path=options.output,
            error=str(exc),
            error_code="io_error",
        )

    return FormatPatchResult(
        exit_code=EXIT_SUCCESS,
        output_path=options.output,
        check_passed=options.check,
    )


def load_edit_spec(path: Path) -> EditSpec:
    """Load and validate an edit spec JSON file."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FormatterError("invalid_json", f"edit spec is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise FormatterError("invalid_schema", "edit spec root must be an object")

    schema_version = _required_str(data, "schema_version")
    if schema_version != EDIT_SPEC_SCHEMA:
        raise FormatterError(
            "unsupported_schema",
            f"unsupported edit spec schema: {schema_version}",
        )
    raw_edits = data.get("edits")
    if not isinstance(raw_edits, list) or not raw_edits:
        raise FormatterError("missing_edits", "edit spec must contain at least one edit")

    edits = tuple(_parse_edit(raw_edit, index) for index, raw_edit in enumerate(raw_edits, start=1))
    return EditSpec(
        schema_version=schema_version,
        patch_name=_optional_str(data, "patch_name"),
        description=_optional_str(data, "description"),
        edits=edits,
    )


def build_patch_text(
    spec: EditSpec,
    *,
    src_root: Path,
    git_binary: str = "git",
    temp_parent: Path | None = None,
    subprocess_runner: SubprocessRunner = subprocess.run,
) -> str:
    """Build patch text from a validated edit spec without touching source files."""

    src_root_resolved = _resolve_src_root(src_root)
    grouped = _resolve_edits(spec.edits, src_root_resolved)

    with tempfile.TemporaryDirectory(dir=temp_parent) as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        orig_dir = temp_dir / "orig"
        mod_dir = temp_dir / "mod"
        patch_parts: list[str] = []

        for relative_path, edits in grouped.items():
            source_path = edits[0].source_path
            original_text = _read_source_text(source_path)
            resolved_edits = _locate_file_edits(original_text, edits)
            modified_text = _apply_resolved_edits(original_text, resolved_edits)

            orig_file = orig_dir / relative_path
            mod_file = mod_dir / relative_path
            orig_file.parent.mkdir(parents=True, exist_ok=True)
            mod_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, orig_file)
            shutil.copy2(source_path, mod_file)
            _write_source_text(mod_file, modified_text)

            file_diff = _run_git_diff_no_index(
                orig_file,
                mod_file,
                relative_path=relative_path,
                git_binary=git_binary,
                subprocess_runner=subprocess_runner,
            )
            if file_diff:
                patch_parts.append(file_diff)

    if not patch_parts:
        raise FormatterError("no_changes", "edit spec produced no patch changes")
    return "\n".join(part.rstrip("\n") for part in patch_parts) + "\n"


def _parse_edit(raw: object, index: int) -> Edit:
    if not isinstance(raw, dict):
        raise FormatterError("invalid_edit", f"edit #{index} must be an object")
    file = _required_str(raw, "file")
    operation = _optional_str(raw, "operation") or "replace"
    line = raw.get("line")
    if line is not None and (not isinstance(line, int) or line <= 0):
        raise FormatterError("invalid_line", f"edit #{index} line must be a positive integer")
    if operation == "replace":
        old = _required_str(raw, "old")
        if old == "":
            raise FormatterError("empty_old", f"edit #{index} old text must not be empty")
        new = _required_str(raw, "new")
        return Edit(
            file=file,
            operation=operation,
            old=old,
            new=new,
            line=line,
            before=_optional_str(raw, "before"),
            after=_optional_str(raw, "after"),
        )
    if operation == "insert_after":
        if line is None:
            raise FormatterError(
                "missing_line",
                f"edit #{index} insert_after requires a positive line",
            )
        anchor = _required_str(raw, "anchor")
        if anchor == "":
            raise FormatterError("empty_anchor", f"edit #{index} anchor must not be empty")
        insert = _required_str(raw, "insert")
        if insert == "":
            raise FormatterError("empty_insert", f"edit #{index} insert must not be empty")
        return Edit(
            file=file,
            operation=operation,
            line=line,
            anchor=anchor,
            insert=insert,
        )
    raise FormatterError("unsupported_operation", f"unsupported edit operation: {operation}")


def _required_str(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise FormatterError("invalid_schema", f"{key} must be a string")
    return value


def _optional_str(data: dict[str, object], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise FormatterError("invalid_schema", f"{key} must be a string")
    return value


def _resolve_src_root(src_root: Path) -> Path:
    resolved = src_root.resolve()
    if not resolved.is_dir():
        raise FormatterError("src_root_not_found", f"src-root is not a directory: {src_root}")
    return resolved


def _resolve_edits(
    edits: tuple[Edit, ...],
    src_root: Path,
) -> dict[Path, tuple[_ResolvedEdit, ...]]:
    grouped: dict[Path, list[_ResolvedEdit]] = defaultdict(list)
    for edit in edits:
        source_path, relative_path = _resolve_source_path(edit.file, src_root)
        grouped[relative_path].append(
            _ResolvedEdit(
                edit=edit,
                source_path=source_path,
                relative_path=relative_path,
                start=-1,
                end=-1,
            )
        )
    return {path: tuple(path_edits) for path, path_edits in grouped.items()}


def _resolve_source_path(file_name: str, src_root: Path) -> tuple[Path, Path]:
    raw_path = Path(file_name)
    candidate = raw_path.resolve() if raw_path.is_absolute() else (src_root / raw_path).resolve()
    try:
        relative_path = candidate.relative_to(src_root)
    except ValueError as exc:
        raise FormatterError(
            "file_outside_src_root",
            f"edit file escapes src-root: {file_name}",
        ) from exc
    if not candidate.is_file():
        raise FormatterError("file_not_found", f"edit file is not readable: {file_name}")
    if not relative_path.parts:
        raise FormatterError("invalid_file", f"edit file is invalid: {file_name}")
    return candidate, relative_path


def _locate_file_edits(
    original_text: str,
    edits: tuple[_ResolvedEdit, ...],
) -> tuple[_ResolvedEdit, ...]:
    located: list[_ResolvedEdit] = []
    for resolved_edit in edits:
        match = _locate_edit(original_text, resolved_edit.edit)
        located.append(
            _ResolvedEdit(
                edit=resolved_edit.edit,
                source_path=resolved_edit.source_path,
                relative_path=resolved_edit.relative_path,
                start=match.start,
                end=match.end,
            )
        )
    _ensure_non_overlapping(located)
    return tuple(located)


def _locate_edit(text: str, edit: Edit) -> _Match:
    if edit.operation == "insert_after":
        return _locate_insert_after(text, edit)
    assert edit.old is not None
    if edit.before is not None or edit.after is not None:
        before = edit.before or ""
        after = edit.after or ""
        anchor = f"{before}{edit.old}{after}"
        matches = _find_matches(text, anchor, offset=len(before), old_length=len(edit.old))
        if not matches:
            raise FormatterError(
                "context_not_found",
                f"context anchor did not match for {edit.file}",
            )
        if len(matches) > 1:
            raise FormatterError(
                "context_not_unique",
                f"context anchor matched multiple locations for {edit.file}: "
                f"{_candidate_lines(matches)}",
            )
        return matches[0]

    matches = _find_matches(text, edit.old)
    if not matches:
        raise FormatterError("old_not_found", f"old text did not match for {edit.file}")
    if len(matches) == 1:
        return matches[0]
    if edit.line is None:
        raise FormatterError(
            "old_not_unique",
            f"old text matched multiple locations for {edit.file}: {_candidate_lines(matches)}",
        )
    return _disambiguate_by_line(edit, matches)


def _find_matches(
    text: str,
    needle: str,
    *,
    offset: int = 0,
    old_length: int | None = None,
) -> list[_Match]:
    if needle == "":
        return []
    matches: list[_Match] = []
    search_from = 0
    span_length = len(needle) if old_length is None else old_length
    while True:
        start = text.find(needle, search_from)
        if start == -1:
            return matches
        old_start = start + offset
        old_end = old_start + span_length
        matches.append(
            _Match(
                start=old_start,
                end=old_end,
                start_line=_line_for_offset(text, old_start),
                end_line=_line_for_offset(text, max(old_start, old_end - 1)),
            )
        )
        search_from = start + 1


def _disambiguate_by_line(edit: Edit, matches: list[_Match]) -> _Match:
    assert edit.line is not None
    covering = [
        match for match in matches if match.start_line <= edit.line <= match.end_line
    ]
    if len(covering) == 1:
        return covering[0]
    if len(covering) > 1:
        raise FormatterError(
            "old_not_unique",
            f"old text matched multiple locations covering line {edit.line} for {edit.file}: "
            f"{_candidate_lines(covering)}",
        )

    nearest_distance = min(abs(match.start_line - edit.line) for match in matches)
    nearest = [
        match for match in matches if abs(match.start_line - edit.line) == nearest_distance
    ]
    if len(nearest) == 1:
        return nearest[0]
    raise FormatterError(
        "old_not_unique",
        f"old text matched multiple equally near locations for {edit.file}: "
        f"{_candidate_lines(nearest)}",
    )


def _locate_insert_after(text: str, edit: Edit) -> _Match:
    assert edit.line is not None
    assert edit.anchor is not None
    lines = text.splitlines(keepends=True)
    if edit.line > len(lines):
        raise FormatterError(
            "insert_out_of_range",
            f"insert_after line {edit.line} is outside {edit.file}",
        )
    line_text = lines[edit.line - 1].removesuffix("\n").removesuffix("\r")
    if line_text != edit.anchor:
        raise FormatterError(
            "anchor_not_found",
            f"insert_after anchor did not match line {edit.line} for {edit.file}",
        )
    end = sum(len(line) for line in lines[: edit.line])
    return _Match(start=end, end=end, start_line=edit.line + 1, end_line=edit.line + 1)


def _line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _candidate_lines(matches: list[_Match]) -> str:
    return ", ".join(str(match.start_line) for match in matches[:10])


def _ensure_non_overlapping(edits: list[_ResolvedEdit]) -> None:
    sorted_edits = sorted(edits, key=lambda item: item.start)
    previous: _ResolvedEdit | None = None
    for current in sorted_edits:
        if previous is not None and previous.end > current.start:
            raise FormatterError(
                "overlapping_edits",
                f"edits overlap in {current.relative_path.as_posix()}",
            )
        previous = current


def _apply_resolved_edits(text: str, edits: tuple[_ResolvedEdit, ...]) -> str:
    modified = text
    for resolved_edit in sorted(edits, key=lambda item: item.start, reverse=True):
        replacement = _replacement_text(resolved_edit.edit)
        modified = (
            modified[: resolved_edit.start]
            + replacement
            + modified[resolved_edit.end :]
        )
    return modified


def _replacement_text(edit: Edit) -> str:
    if edit.operation == "insert_after":
        assert edit.insert is not None
        return edit.insert if edit.insert.endswith("\n") else edit.insert + "\n"
    assert edit.new is not None
    return edit.new


def _read_source_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="surrogateescape")


def _write_source_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", errors="surrogateescape")


def _run_git_diff_no_index(
    orig_file: Path,
    mod_file: Path,
    *,
    relative_path: Path,
    git_binary: str,
    subprocess_runner: SubprocessRunner,
) -> str:
    try:
        completed = subprocess_runner(
            [git_binary, "diff", "--no-index", "--", str(orig_file), str(mod_file)],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise FormatterError("git_not_found", f"git command not found: {git_binary}") from exc
    if completed.returncode not in (0, 1):
        raise FormatterError(
            "git_diff_failed",
            f"git diff --no-index failed: {completed.stderr.strip()}",
        )
    if completed.returncode == 0:
        return ""
    if not completed.stdout:
        raise FormatterError("git_diff_failed", "git diff --no-index produced no output")
    return _rewrite_diff_headers(completed.stdout, relative_path)


def _rewrite_diff_headers(diff_text: str, relative_path: Path) -> str:
    rel = relative_path.as_posix()
    rewritten: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            rewritten.append(f"diff --git a/{rel} b/{rel}")
        elif line.startswith("--- "):
            rewritten.append(f"--- a/{rel}")
        elif line.startswith("+++ "):
            rewritten.append(f"+++ b/{rel}")
        else:
            rewritten.append(line)
    return "\n".join(rewritten) + "\n"


def _run_git_apply_check(
    patch_text: str,
    *,
    src_root: Path,
    git_binary: str,
    subprocess_runner: SubprocessRunner,
) -> None:
    try:
        completed = subprocess_runner(
            [git_binary, "-C", str(src_root), "apply", "--check", "-"],
            input=patch_text,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise FormatterError("git_not_found", f"git command not found: {git_binary}") from exc
    if completed.returncode != 0:
        raise FormatterError(
            "git_apply_check_failed",
            f"git apply --check failed: {completed.stderr.strip()}",
        )
