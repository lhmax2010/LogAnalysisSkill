"""Whole-file suppression policy for P5, without applying edits or writing state."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from tizen_build_verify.edit_spec_guard import (
    EditSpecViolation,
    _locate_edit,
    _validate_target_path,
    validate_edit_spec,
)

SourceKind = Literal["t1_cherry_pick", "generated", "suppress"]
POLICY_RULES_VERSION = "p5-policy/v1"
WHOLESALE_NAMES = frozenset({"everything", "all", "extra", "pedantic"})
_OPTION = re.compile(r"(?<![A-Za-z0-9_\-])-(?:W[A-Za-z0-9_+.=#\-]*|w)(?![A-Za-z0-9_+.=#\-])")
_BRACKET = re.compile(r"\[(=*)\[")
_RAW_STRING = re.compile(r'R"([^ ()\\\t\r\n]{0,16})\(')
_GLOBAL = "global_or_ambiguous"
_SUPPRESS = {"wno_flag", "wno_error_flag", "pragma_suppress"}
_WHOLESALE = {"wno_error_all", "wno_wholesale", "w_all_off", "pragma_wholesale", "pragma_unparsed"}
_ALLOWED_SCOPES = {"target_private", "target_property", "target_variable", "source_local"}


@dataclass(frozen=True)
class PolicyHit:
    edit_index: int
    file: str
    kind: str
    token: str | None
    scope: str
    rule: str
    count: int


@dataclass(frozen=True)
class PolicyVerdict:
    verdict: Literal["allowed", "forbidden"]
    fix_strategy_final: Literal["code", "cherry_pick", "suppress"] | None
    hits: tuple[PolicyHit, ...]
    rules_version: str


class PolicyInputError(ValueError):
    """The edit specification or source kind cannot be evaluated."""


@dataclass(frozen=True)
class _Instance:
    kind: str
    token: str
    scope: str
    start: int
    end: int

    @property
    def key(self) -> tuple[str, str, str]:
        return self.kind, self.token, self.scope


@dataclass(frozen=True)
class _Argument:
    value: str
    start: int
    end: int
    punctuation: bool = False


@dataclass(frozen=True)
class _Command:
    name: str
    arguments: tuple[_Argument, ...]
    start: int
    end: int


@dataclass(frozen=True)
class _Edit:
    index: int
    file: str
    start: int
    end: int
    new: str


def _category(file: str) -> str:
    path = Path(file.replace("\\", "/"))
    name, extension = path.name, path.suffix.lower()
    if extension == ".spec" or "packaging" in path.parts[:-1]:
        return "spec"
    if name == "CMakeLists.txt" or extension == ".cmake":
        return "cmake"
    if name == "Makefile.am":
        return "automake"
    if (
        name.startswith("Makefile")
        or extension in {".mk", ".in", ".ac", ".m4"}
        or name in {"meson.build", "configure"}
    ):
        return "build_other"
    if extension in {
        ".c",
        ".cc",
        ".cpp",
        ".cxx",
        ".c++",
        ".h",
        ".hh",
        ".hpp",
        ".hxx",
        ".inl",
        ".ipp",
        ".m",
        ".mm",
    }:
        return "source"
    if (
        extension in {".md", ".rst", ".adoc"}
        or name.startswith(("README", "ChangeLog", "NEWS", "AUTHORS"))
        or {"doc", "docs"}.intersection(path.parts[:-1])
    ):
        return "doc"
    return "other"


def _blank(chars: list[str], start: int, end: int) -> None:
    chars[start:end] = ["\n" if char == "\n" else " " for char in chars[start:end]]


def _quoted_end(text: str, start: int) -> int:
    quote, index = text[start], start + 1
    while index < len(text):
        if text[index] == "\\":
            index += 2
        elif text[index] == quote:
            return index + 1
        else:
            index += 1
    return len(text)


def _bracket_end(text: str, start: int) -> tuple[int, str] | None:
    match = _BRACKET.match(text, start)
    if match is None:
        return None
    close = "]" + match[1] + "]"
    stop = text.find(close, match.end())
    end = stop + len(close) if stop >= 0 else len(text)
    return end, text[match.end() : stop if stop >= 0 else len(text)]


def _cmake(text: str) -> tuple[str, list[_Command]]:
    active = list(text)
    tokens: list[_Argument] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char == "#":
            bracket = _bracket_end(text, index + 1)
            end = bracket[0] if bracket else text.find("\n", index)
            end = len(text) if end < 0 else end
            _blank(active, index, end)
            index = end
            continue
        if char in "()":
            tokens.append(_Argument(char, index, index + 1, True))
            index += 1
            continue
        start, value = index, ""
        bracket = _bracket_end(text, index)
        if bracket:
            index, value = bracket
        else:
            while index < len(text) and not text[index].isspace() and text[index] not in "()":
                if text[index] == '"':
                    end = _quoted_end(text, index)
                    raw = (
                        text[index + 1 : end - 1] if text[end - 1] == '"' else text[index + 1 : end]
                    )
                    raw = re.sub(r"\\\r?\n", "", raw)
                    value += re.sub(
                        r"\\(.)",
                        lambda m: {"n": "\n", "r": "\r", "t": "\t"}.get(m[1], m[1]),
                        raw,
                        flags=re.S,
                    )
                    index = end
                elif text[index] == "\\" and index + 1 < len(text):
                    value += text[index : index + 2]
                    index += 2
                else:
                    value += text[index]
                    index += 1
        tokens.append(_Argument(value, start, index))

    commands = []
    index = 0
    while index + 1 < len(tokens):
        name, opening = tokens[index : index + 2]
        if (
            name.punctuation
            or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name.value) is None
            or not opening.punctuation
            or opening.value != "("
        ):
            index += 1
            continue
        depth, stop = 1, index + 2
        while stop < len(tokens):
            token = tokens[stop]
            if token.punctuation:
                depth += 1 if token.value == "(" else -1
            if depth == 0:
                break
            stop += 1
        if depth != 0:
            index += 1
            continue
        commands.append(
            _Command(
                name.value.lower(), tuple(tokens[index + 2 : stop]), opening.start, tokens[stop].end
            )
        )
        index = stop + 1
    return "".join(active), commands


def _cmake_scope(command: _Command | None, position: int) -> str:
    if command is None:
        return _GLOBAL
    args = command.arguments
    current = next(
        (index for index, arg in enumerate(args) if arg.start <= position < arg.end), None
    )
    if current is None:
        return _GLOBAL
    if command.name == "target_compile_options":
        relevant = args[1 : current + 1]
        if any(re.search(r"\$\{|\$ENV\{|\$CACHE\{", arg.value) for arg in relevant):
            return _GLOBAL
        section = next(
            (
                arg.value
                for arg in reversed(relevant)
                if arg.value in {"PRIVATE", "PUBLIC", "INTERFACE"}
            ),
            None,
        )
        return "target_private" if section == "PRIVATE" else _GLOBAL
    if command.name in {"set_source_files_properties", "set_target_properties", "set_property"}:
        if command.name == "set_property" and (
            not args or args[0].value not in {"TARGET", "SOURCE"}
        ):
            return _GLOBAL
        prop = next(
            (
                arg.value
                for arg in reversed(args[: current + 1])
                if arg.value in {"PROPERTY", "PROPERTIES", "COMPILE_OPTIONS", "COMPILE_FLAGS"}
            ),
            None,
        )
        if prop in {"COMPILE_OPTIONS", "COMPILE_FLAGS"}:
            return "target_property"
    return _GLOBAL


def _splice(text: str) -> tuple[str, list[int]]:
    removed = {
        index
        for match in re.finditer(r"\\\r?\n", text)
        for index in range(match.start(), match.end())
    }
    positions = [index for index in range(len(text)) if index not in removed]
    return "".join(text[index] for index in positions), positions


def _source_masks(text: str) -> tuple[str, str]:
    comments, code = list(text), list(text)
    index = 0
    while index < len(text):
        raw_string = _RAW_STRING.match(text, index)
        if raw_string:
            close = ")" + raw_string[1] + '"'
            stop = text.find(close, raw_string.end())
            end = len(text) if stop < 0 else stop + len(close)
            _blank(code, index, end)
        elif text.startswith("//", index):
            end = text.find("\n", index)
            end = len(text) if end < 0 else end
            _blank(comments, index, end)
            _blank(code, index, end)
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            end = len(text) if end < 0 else end + 2
            _blank(comments, index, end)
            _blank(code, index, end)
        elif text[index] in "\"'":
            end = _quoted_end(text, index)
            _blank(code, index, end)
        else:
            end = index + 1
        index = end
    return "".join(comments), "".join(code)


def _pragma(body: str, raw: str, start: int, end: int) -> _Instance | None:
    suppress = re.fullmatch(
        r'(?:clang|GCC)\s+diagnostic\s+(?:ignored|warning)\s+"(-W[^"\s]+)"', body
    )
    if suppress:
        token = suppress[1]
        kind = "pragma_wholesale" if token[2:] in WHOLESALE_NAMES else "pragma_suppress"
        return _Instance(kind, token, "source_local", start, end)
    if re.fullmatch(r"(?:clang|GCC)\s+system_header", body):
        return _Instance("pragma_wholesale", "system_header", "source_local", start, end)
    diagnostic = re.fullmatch(r"(?:clang|GCC)\s+diagnostic\s+([A-Za-z_]+)(?:\s+.*)?", body)
    if diagnostic and diagnostic[1] not in {"ignored", "warning"}:
        return (
            _Instance("pragma_pop", "pop", "source_local", start, end)
            if diagnostic[1] == "pop"
            else None
        )
    if "diagnostic" in body or "system_header" in body:
        return _Instance("pragma_unparsed", raw, "source_local", start, end)
    return None


def _source_instances(text: str) -> list[_Instance]:
    comments, code = _source_masks(text)
    instances = []
    for match in re.finditer(r"^[ \t]*#[ \t]*pragma\b[^\n]*", code, re.M):
        raw = comments[match.start() : match.end()]
        body = re.sub(r"^[ \t]*#[ \t]*pragma\b", "", raw).strip()
        instance = _pragma(body, raw, match.start(), match.end())
        if instance:
            instances.append(instance)
    for match in re.finditer(r"\b(?:_Pragma|__pragma)\b", code):
        index = match.end()
        while index < len(code) and code[index].isspace():
            index += 1
        opening = index
        if index < len(code) and code[index] == "(":
            depth = 1
            index += 1
            while index < len(code) and depth:
                depth += (code[index] == "(") - (code[index] == ")")
                index += 1
            argument = comments[opening + 1 : index - 1] if depth == 0 else ""
        else:
            index, argument = match.end(), ""
        raw = comments[match.start() : index]
        literal = re.fullmatch(r'\s*"((?:[^"\\]|\\.)*)"\s*', argument, re.S)
        if match[0] == "__pragma" or literal is None:
            instances.append(
                _Instance("pragma_unparsed", raw, "source_local", match.start(), index)
            )
            continue
        body = re.sub(r'\\(["\\])', r"\1", literal[1])
        if "\\" in body:
            instances.append(
                _Instance("pragma_unparsed", raw, "source_local", match.start(), index)
            )
            continue
        instance = _pragma(body.strip(), raw, match.start(), index)
        if instance:
            instances.append(instance)
    return instances


def _option_kind(token: str) -> str | None:
    if token == "-w":
        return "w_all_off"
    if token == "-Wno-error":
        return "wno_error_all"
    if token.startswith("-Wno-error="):
        return "wno_wholesale" if token[11:] in WHOLESALE_NAMES else "wno_error_flag"
    if token.startswith("-Wno-"):
        return "wno_wholesale" if token[5:] in WHOLESALE_NAMES else "wno_flag"
    if token == "-Werror" or token.startswith("-Werror="):
        return "werror"
    return None


def _instances(text: str, category: str) -> list[_Instance]:
    if category == "doc":
        return []
    positions = list(range(len(text)))
    if category in {"source", "automake", "build_other", "spec"}:
        text, positions = _splice(text)
    commands: list[_Command] = []
    if category == "source":
        result = _source_instances(text)
    else:
        active = text
        if category == "cmake":
            active, commands = _cmake(text)
        elif category in {"automake", "build_other", "spec"}:
            chars = list(text)
            for comment in re.finditer(r"(?<!\S)#[^\n]*", text):
                _blank(chars, comment.start(), comment.end())
            active = "".join(chars)
        result = []
        for token in _OPTION.finditer(active):
            kind = _option_kind(token[0])
            if kind is None:
                continue
            start, end = token.span()
            scope = _GLOBAL
            if category == "cmake":
                command = next((cmd for cmd in commands if cmd.start <= start < cmd.end), None)
                scope = _cmake_scope(command, start)
                if command:
                    start, end = command.start, command.end
            elif category == "automake":
                line = active[active.rfind("\n", 0, start) + 1 : start]
                assignment = re.match(
                    r"\s*([^\s=:+?]+)_(?:CFLAGS|CXXFLAGS|CPPFLAGS)\s*[:+?]?=", line
                )
                if assignment and assignment[1] != "AM":
                    scope = "target_variable"
            if kind in {"wno_error_all", "wno_wholesale", "w_all_off"}:
                scope = "n/a"
            result.append(_Instance(kind, token[0], scope, start, end))
        for command in commands:
            if command.name not in {"add_executable", "add_library", "add_test"}:
                continue
            args = command.arguments
            offset = 1 if command.name == "add_test" and args and args[0].value == "NAME" else 0
            if len(args) > offset:
                result.append(
                    _Instance(
                        "target_decl",
                        command.name + " " + args[offset].value,
                        "n/a",
                        command.start,
                        command.end,
                    )
                )
    return [
        _Instance(
            item.kind, item.token, item.scope, positions[item.start], positions[item.end - 1] + 1
        )
        for item in result
    ]


def _hit_index(instances: Sequence[_Instance], spans: Sequence[tuple[int, int, int]]) -> int:
    return min(
        (
            index
            for start, end, index in spans
            for item in instances
            if start < item.end and item.start < end
        ),
        default=-1,
    )


def _file_hits(before: str, edits: list[_Edit]) -> list[PolicyHit]:
    after = before
    for edit in sorted(edits, key=lambda item: item.start, reverse=True):
        after = after[: edit.start] + edit.new + after[edit.end :]
    old_spans = [(edit.start, edit.end, edit.index) for edit in edits]
    new_spans = []
    delta = 0
    for edit in sorted(edits, key=lambda item: item.start):
        new_spans.append((edit.start + delta, edit.start + delta + len(edit.new), edit.index))
        delta += len(edit.new) - (edit.end - edit.start)
    file = min(edit.file for edit in edits)
    category = _category(file)
    old, new = _instances(before, category), _instances(after, category)
    old_count, new_count = Counter(item.key for item in old), Counter(item.key for item in new)
    hits = []

    def hit(
        kind: str,
        token: str,
        scope: str,
        rule: str,
        count: int,
        located: Sequence[_Instance],
        spans: Sequence[tuple[int, int, int]],
    ) -> None:
        index = _hit_index(located, spans)
        original_file = next((edit.file for edit in edits if edit.index == index), file)
        hits.append(PolicyHit(index, original_file, kind, token, scope, rule, count))

    for key, count in new_count.items():
        kind, token, scope = key
        increase = count - old_count[key]
        if increase > 0 and kind in _SUPPRESS | _WHOLESALE:
            rule = "suppress" if kind in _SUPPRESS and scope in _ALLOWED_SCOPES else "forbidden"
            hit(
                kind,
                token,
                scope,
                rule,
                increase,
                [item for item in new if item.key == key],
                new_spans,
            )
    for token in {item.token for item in old + new if item.kind == "werror"}:
        global_key = ("werror", token, _GLOBAL)
        g = new_count[global_key] - old_count[global_key]
        n = sum(
            count
            for (kind, name, scope), count in old_count.items()
            if kind == "werror" and name == token and scope != _GLOBAL
        ) - sum(
            count
            for (kind, name, scope), count in new_count.items()
            if kind == "werror" and name == token and scope != _GLOBAL
        )
        count = max(0, -g) + max(0, n - max(g, 0))
        if count:
            hit(
                "werror_removed",
                token,
                "n/a",
                "forbidden",
                count,
                [item for item in old if item.kind == "werror" and item.token == token],
                old_spans,
            )
    pop_removed = sum(1 for item in old if item.kind == "pragma_pop") - sum(
        1 for item in new if item.kind == "pragma_pop"
    )
    suppress_removed = sum(
        max(0, count - new_count[key])
        for key, count in old_count.items()
        if key[0] == "pragma_suppress"
    )
    if pop_removed > suppress_removed:
        hit(
            "pragma_pop_removed",
            "pop",
            "n/a",
            "forbidden",
            pop_removed - suppress_removed,
            [item for item in old if item.kind == "pragma_pop"],
            old_spans,
        )
    for key, count in old_count.items():
        if key[0] == "target_decl" and count > new_count[key]:
            hit(
                "target_removed",
                key[1],
                "n/a",
                "forbidden",
                count - new_count[key],
                [item for item in old if item.key == key],
                old_spans,
            )
    for edit in edits:
        if not edit.new.strip():
            hits.append(
                PolicyHit(edit.index, edit.file, "pure_deletion", None, "n/a", "forbidden", 1)
            )
    return hits


def evaluate(
    edit_spec: Mapping[str, object], src_root: Path, source_kind: SourceKind
) -> PolicyVerdict:
    try:
        validate_edit_spec(dict(edit_spec), str(src_root))
        if source_kind not in {"t1_cherry_pick", "generated", "suppress"}:
            raise PolicyInputError("unsupported source_kind")
        by_file: dict[Path, list[_Edit]] = defaultdict(list)
        for index, edit in enumerate(cast(list[dict[str, Any]], edit_spec["edits"])):
            path = _validate_target_path(edit["file"], src_root.resolve())
            located = _locate_edit(path, edit["old"], edit.get("line"))
            by_file[path].append(
                _Edit(index, edit["file"], located.start, located.end, edit["new"])
            )
        hits = [
            hit
            for path, edits in by_file.items()
            for hit in _file_hits(path.read_text(encoding="utf-8", errors="surrogateescape"), edits)
        ]
    except EditSpecViolation as exc:
        raise PolicyInputError(str(exc)) from exc
    ordered = tuple(
        sorted(
            hits,
            key=lambda item: (
                item.rule,
                item.kind,
                item.file,
                item.token or "",
                item.scope,
                item.edit_index,
            ),
        )
    )
    if any(item.rule == "forbidden" for item in ordered):
        return PolicyVerdict("forbidden", None, ordered, POLICY_RULES_VERSION)
    final: Literal["code", "cherry_pick", "suppress"] = "code"
    if any(item.rule == "suppress" for item in ordered) or source_kind == "suppress":
        final = "suppress"
    elif source_kind == "t1_cherry_pick":
        final = "cherry_pick"
    return PolicyVerdict("allowed", final, ordered, POLICY_RULES_VERSION)
