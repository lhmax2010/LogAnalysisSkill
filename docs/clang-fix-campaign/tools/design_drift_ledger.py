#!/usr/bin/env python3
"""Gate stale design text and definition-to-reference drift for skill-4."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "clang-fix-campaign/design-drift-ledger/v1"
VERSION_RE = re.compile(r"^1\.(0|[1-9]|1[0-2])$")
HUNK_RE = re.compile(
    r"^@@ -(?P<old_start>[0-9]+)(?:,(?P<old_count>[0-9]+))? "
    r"\+(?P<new_start>[0-9]+)(?:,(?P<new_count>[0-9]+))? @@"
)
HEADING_RE = re.compile(r"^(?P<marks>#{2,6})\s+(?:§)?(?P<id>[0-9]+(?:\.[0-9]+)*)\b")
SECTION_REF_RE = re.compile(r"§[0-9]+(?:\.[0-9]+)*")
NUMBER_RE = re.compile(r"(\d+|[一二三四五六七八九十]+)(项|条|个|对)")
MARKDOWN_MARKERS = ("**", "`")
IGNORED_CATEGORIES = frozenset({"FORMAT_ONLY", "SUBSUMED", "OUT_OF_SCOPE"})


class LedgerError(RuntimeError):
    """The ledger or the checked design violates its frozen contract."""


@dataclass(frozen=True)
class VersionDoc:
    version: str
    path: Path
    lines: tuple[str, ...]


@dataclass(frozen=True)
class DiffCandidate:
    candidate_id: str
    old_version: str
    new_version: str
    old_path: str
    new_path: str
    old_start: int
    old_end: int
    new_start: int
    new_end: int
    old_lines: tuple[str, ...]
    new_lines: tuple[str, ...]
    pattern: str

    @property
    def old_line_numbers(self) -> frozenset[int]:
        return frozenset(range(self.old_start, self.old_end + 1))

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "old_version": self.old_version,
            "new_version": self.new_version,
            "old_path": self.old_path,
            "new_path": self.new_path,
            "old_start": self.old_start,
            "old_end": self.old_end,
            "new_start": self.new_start,
            "new_end": self.new_end,
            "old_lines": list(self.old_lines),
            "new_lines": list(self.new_lines),
            "pattern": self.pattern,
        }


@dataclass(frozen=True)
class DodItem:
    item_id: str
    text: str
    line_start: int
    line_end: int


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_data_path() -> Path:
    return Path(__file__).with_name("design_drift_ledger.json")


def normalize(text: str) -> str:
    """Normalize only the forms admitted by section 5.4."""

    normalized = unicodedata.normalize("NFKC", text)
    for marker in MARKDOWN_MARKERS:
        normalized = normalized.replace(marker, "")
    return " ".join(normalized.split())


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LedgerError(f"cannot read ledger data {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LedgerError("ledger data root must be an object")
    return value


def _version_key(version: str) -> int:
    match = VERSION_RE.fullmatch(version)
    if match is None:
        raise LedgerError(f"unsupported version: {version!r}")
    return int(match.group(1))


def _load_versions(data: dict[str, Any], repo_root: Path) -> tuple[VersionDoc, ...]:
    raw_versions = data.get("version_corpus")
    if not isinstance(raw_versions, list):
        raise LedgerError("version_corpus must be a list")

    documents: list[VersionDoc] = []
    for raw in raw_versions:
        if not isinstance(raw, dict):
            raise LedgerError("version_corpus entries must be objects")
        version = raw.get("version")
        raw_path = raw.get("path")
        expected_sha = raw.get("sha256")
        if not isinstance(version, str) or not isinstance(raw_path, str):
            raise LedgerError("version corpus entry lacks version/path")
        path = repo_root / raw_path
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise LedgerError(f"missing version corpus file {path}: {exc}") from exc
        actual_sha = _sha256_bytes(content)
        if expected_sha != actual_sha:
            raise LedgerError(
                f"version corpus SHA mismatch for {version}: expected {expected_sha}, "
                f"actual {actual_sha}"
            )
        documents.append(VersionDoc(version, path, tuple(content.decode("utf-8").splitlines())))

    documents.sort(key=lambda item: _version_key(item.version))
    actual = [_version_key(item.version) for item in documents]
    if actual != list(range(13)):
        raise LedgerError(f"version sequence is not continuous v1.0..v1.12: {actual}")
    return tuple(documents)


def _raw_diff(old: VersionDoc, new: VersionDoc) -> str:
    completed = subprocess.run(
        [
            "git",
            "diff",
            "--no-index",
            "--unified=0",
            "--",
            str(old.path),
            str(new.path),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode not in {0, 1}:
        raise LedgerError(
            f"git diff failed for v{old.version}->v{new.version}: {completed.stderr.strip()}"
        )
    return completed.stdout


def _candidate_id(
    old_version: str,
    old_start: int,
    old_end: int,
    new_start: int,
    new_end: int,
    old_text: str,
) -> str:
    digest = _sha256_bytes(normalize(old_text).encode("utf-8"))
    return f"v{old_version}|old:{old_start}-{old_end},new:{new_start}-{new_end}|{digest}"


def _diff_candidates(
    old: VersionDoc, new: VersionDoc, repo_root: Path
) -> tuple[DiffCandidate, ...]:
    candidates: list[DiffCandidate] = []
    current: dict[str, Any] | None = None
    excluded = _excluded_lines(old)
    line_scopes: dict[int, str] = {}
    current_section = "frontmatter"
    for line_number, line in enumerate(old.lines, 1):
        if line_number in excluded:
            line_scopes[line_number] = "excluded"
            continue
        section_match = re.match(r"^##\s+§(?P<id>[0-9]+)\b", line)
        if section_match is not None:
            current_section = f"§{section_match.group('id')}"
        line_scopes[line_number] = current_section

    def finish() -> None:
        nonlocal current
        if current is None or not current["old_lines"]:
            current = None
            return
        hunk_old_start = current["old_start"]
        new_start = current["new_start"]
        old_lines = tuple(current["old_lines"])
        new_lines = tuple(current["new_lines"])
        new_end = new_start + len(new_lines) - 1

        # A zero-context hunk may straddle the revision/body boundary. Split its
        # deleted side whenever scope membership changes so an exempt line cannot
        # poison a checked-scope replay. Each subspan keeps the raw new-side span
        # as provenance; raw deletion coverage is checked independently.
        groups: list[tuple[int, list[str]]] = []
        previous_scope: str | None = None
        for offset, old_line in enumerate(old_lines):
            line_number = hunk_old_start + offset
            scope = line_scopes[line_number]
            if previous_scope is None or scope != previous_scope:
                groups.append((line_number, []))
            groups[-1][1].append(old_line)
            previous_scope = scope

        for old_start, group_lines in groups:
            group = tuple(group_lines)
            old_end = old_start + len(group) - 1
            old_text = "\n".join(group)
            normalized_old = normalize(old_text)
            pattern = re.escape(normalized_old) if normalized_old else ""
            candidates.append(
                DiffCandidate(
                    candidate_id=_candidate_id(
                        old.version, old_start, old_end, new_start, new_end, old_text
                    ),
                    old_version=old.version,
                    new_version=new.version,
                    old_path=_relative(old.path, repo_root),
                    new_path=_relative(new.path, repo_root),
                    old_start=old_start,
                    old_end=old_end,
                    new_start=new_start,
                    new_end=new_end,
                    old_lines=group,
                    new_lines=new_lines,
                    pattern=pattern,
                )
            )
        current = None

    for line in _raw_diff(old, new).splitlines():
        match = HUNK_RE.match(line)
        if match is not None:
            finish()
            current = {
                "old_start": int(match.group("old_start")),
                "new_start": int(match.group("new_start")),
                "old_lines": [],
                "new_lines": [],
            }
            continue
        if current is None:
            continue
        if line.startswith("-"):
            current["old_lines"].append(line[1:])
        elif line.startswith("+"):
            current["new_lines"].append(line[1:])
    finish()
    return tuple(candidates)


def _raw_deleted_lines(
    documents: tuple[VersionDoc, ...],
) -> frozenset[tuple[str, int]]:
    """Read deleted line coordinates directly from raw diffs as the coverage anchor."""

    deleted: set[tuple[str, int]] = set()
    for old, new in zip(documents, documents[1:], strict=False):
        old_line_number: int | None = None
        for line in _raw_diff(old, new).splitlines():
            match = HUNK_RE.match(line)
            if match is not None:
                old_line_number = int(match.group("old_start"))
                continue
            if old_line_number is None:
                continue
            if line.startswith("-"):
                deleted.add((old.version, old_line_number))
                old_line_number += 1
            elif line.startswith(" "):
                old_line_number += 1
    return frozenset(deleted)


def _section_spans(lines: tuple[str, ...]) -> dict[str, tuple[int, int]]:
    headings: list[tuple[str, int, int]] = []
    for index, line in enumerate(lines, 1):
        match = HEADING_RE.match(line)
        if match is not None:
            headings.append((f"§{match.group('id')}", len(match.group("marks")), index))

    spans: dict[str, tuple[int, int]] = {}
    for position, (section_id, level, start) in enumerate(headings):
        end = len(lines)
        for _, next_level, next_start in headings[position + 1 :]:
            if next_level <= level:
                end = next_start - 1
                break
        if section_id in spans:
            raise LedgerError(f"duplicate section heading: {section_id}")
        spans[section_id] = (start, end)
    return spans


def _revision_span(lines: tuple[str, ...]) -> tuple[int, int] | None:
    starts = [
        index
        for index, line in enumerate(lines, 1)
        if line.startswith("> **v1.") or line.startswith("> **v2.")
    ]
    if not starts:
        return None
    start = starts[0]
    for index in range(start + 1, len(lines) + 1):
        if lines[index - 1] == "---":
            return start, index - 1
    raise LedgerError("revision block has no closing horizontal rule")


def _excluded_lines(doc: VersionDoc) -> frozenset[int]:
    excluded: set[int] = set()
    revision = _revision_span(doc.lines)
    if revision is not None:
        excluded.update(range(revision[0], revision[1] + 1))
    spans = _section_spans(doc.lines)
    for section_id in ("§5.4", "§5.5"):
        span = spans.get(section_id)
        if span is not None:
            excluded.update(range(span[0], span[1] + 1))
    return frozenset(excluded)


def _primary_sections(doc: VersionDoc) -> dict[str, str]:
    excluded = _excluded_lines(doc)
    result: dict[str, list[str]] = {"frontmatter": []}
    current = "frontmatter"
    for index, line in enumerate(doc.lines, 1):
        if index in excluded:
            continue
        match = re.match(r"^##\s+§(?P<id>[0-9]+)\b", line)
        if match is not None:
            current = f"§{match.group('id')}"
            result.setdefault(current, [])
        result[current].append(line)
    return {key: normalize("\n".join(value)) for key, value in result.items()}


def _section_text(doc: VersionDoc, section_id: str) -> str:
    span = _section_spans(doc.lines).get(section_id)
    if span is None:
        raise LedgerError(f"section {section_id} not found in v{doc.version}")
    return "\n".join(doc.lines[span[0] - 1 : span[1]])


def _dod_items(doc: VersionDoc) -> tuple[DodItem, ...]:
    span = _section_spans(doc.lines).get("§7")
    if span is None:
        raise LedgerError(f"section 7 not found in v{doc.version}")
    items: list[DodItem] = []
    current_lines: list[str] = []
    current_start = 0
    current_end = 0

    def finish() -> None:
        nonlocal current_lines, current_start, current_end
        if not current_lines:
            return
        items.append(
            DodItem(
                item_id=f"DOD-{len(items) + 1:02d}",
                text="\n".join(current_lines),
                line_start=current_start,
                line_end=current_end,
            )
        )
        current_lines = []

    for line_number in range(span[0] + 1, span[1] + 1):
        line = doc.lines[line_number - 1]
        if line == "---" or line.startswith("## "):
            break
        if line.startswith("- [ ] "):
            finish()
            current_start = line_number
            current_end = line_number
            current_lines = [line[6:]]
        elif current_lines:
            current_lines.append(line.strip())
            current_end = line_number
    finish()
    return tuple(items)


def _matches_by_section(pattern: str, doc: VersionDoc) -> dict[str, int]:
    if not pattern:
        return {}
    counts: dict[str, int] = {}
    for section_id, text in _primary_sections(doc).items():
        count = len(tuple(re.finditer(pattern, text)))
        if count:
            counts[section_id] = count
    return counts


def _candidate_map(documents: tuple[VersionDoc, ...], repo_root: Path) -> dict[str, DiffCandidate]:
    candidates: dict[str, DiffCandidate] = {}
    for old, new in zip(documents, documents[1:], strict=False):
        for candidate in _diff_candidates(old, new, repo_root):
            if candidate.candidate_id in candidates:
                raise LedgerError(f"duplicate candidate ID: {candidate.candidate_id}")
            candidates[candidate.candidate_id] = candidate
    return candidates


def _changed_sections(documents: tuple[VersionDoc, ...]) -> dict[str, str]:
    first_transition: dict[str, str] = {}
    for old, new in zip(documents, documents[1:], strict=False):
        old_spans = _section_spans(old.lines)
        new_spans = _section_spans(new.lines)
        for section_id in sorted(set(old_spans) | set(new_spans)):
            old_text = _section_text(old, section_id) if section_id in old_spans else ""
            new_text = _section_text(new, section_id) if section_id in new_spans else ""
            if normalize(old_text) != normalize(new_text):
                first_transition.setdefault(section_id, f"v{old.version}->v{new.version}")
    return first_transition


def _binding_candidate_id(definition_section: str, reference: str) -> str:
    return f"{definition_section}->{reference}"


def _export_binding_candidates(
    documents: tuple[VersionDoc, ...], target: VersionDoc
) -> tuple[tuple[str, ...], dict[str, str]]:
    changed = _changed_sections(documents)
    dod_items = _dod_items(target)
    exported = {
        _binding_candidate_id(section_id, f"dod:{item.item_id}")
        for section_id in changed
        for item in dod_items
    }
    # This deliberate superset includes every possible normative section reference,
    # therefore every normalized snippet occurrence, without trusting a hand-written
    # snippet list to define its own completeness boundary.
    for definition_section in changed:
        for reference_id in _section_spans(target.lines):
            exported.add(_binding_candidate_id(definition_section, f"section:{reference_id}"))
    return tuple(sorted(exported)), changed


def _extract_reference_text(
    binding: dict[str, Any], doc: VersionDoc, dod_by_id: dict[str, DodItem]
) -> str:
    reference = binding.get("reference")
    if not isinstance(reference, dict):
        raise LedgerError(f"binding {binding.get('id')} lacks reference")
    kind = reference.get("kind")
    reference_id = reference.get("id")
    if not isinstance(reference_id, str):
        raise LedgerError(f"binding {binding.get('id')} has invalid reference id")
    if kind == "dod":
        item = dod_by_id.get(reference_id)
        if item is None:
            raise LedgerError(f"DoD item {reference_id} not found in v{doc.version}")
        text = item.text
    elif kind == "section":
        text = _section_text(doc, reference_id)
    else:
        raise LedgerError(f"binding {binding.get('id')} has unknown reference kind {kind}")
    selector = reference.get("selector")
    if selector is None:
        return text
    if not isinstance(selector, str):
        raise LedgerError(f"binding {binding.get('id')} reference selector is not a string")
    match = re.search(selector, text, flags=re.MULTILINE | re.DOTALL)
    if match is None:
        raise LedgerError(
            f"binding {binding.get('id')} reference selector did not match v{doc.version}"
        )
    return match.group(0)


def _chinese_number(value: str) -> int:
    if value.isdigit():
        return int(value)
    digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if value == "十":
        return 10
    if "十" in value:
        left, right = value.split("十", 1)
        return (digits.get(left, 1) * 10) + digits.get(right, 0)
    if value not in digits:
        raise LedgerError(f"unsupported Chinese numeral: {value}")
    return digits[value]


def _evaluate_binding_text(
    binding: dict[str, Any], definition_text: str, reference_text: str
) -> tuple[bool, str]:
    binding_id = binding.get("id")
    predicate = binding.get("predicate")
    snippets = binding.get("canonical_snippets", [])
    if not isinstance(snippets, list) or not all(isinstance(item, str) for item in snippets):
        raise LedgerError(f"binding {binding_id} canonical_snippets must be strings")

    if predicate == "TEXT_CONTAINS":
        if not snippets:
            raise LedgerError(f"TEXT_CONTAINS binding {binding_id} has no snippets")
        normalized_definition = normalize(definition_text)
        normalized_reference = normalize(reference_text)
        missing_definition = [
            item for item in snippets if normalize(item) not in normalized_definition
        ]
        missing_reference = [
            item for item in snippets if normalize(item) not in normalized_reference
        ]
        if missing_definition or missing_reference:
            return False, (
                f"missing_definition={missing_definition}, missing_reference={missing_reference}"
            )
        return True, f"snippets={len(snippets)}"

    if predicate == "COUNT_EQUAL":
        selector = binding.get("definition_selector")
        if not isinstance(selector, str):
            raise LedgerError(f"COUNT_EQUAL binding {binding_id} lacks definition_selector")
        definition_count = len(re.findall(selector, definition_text, flags=re.MULTILINE))
        compact_reference = re.sub(r"\s+", "", normalize(reference_text))
        number_matches = NUMBER_RE.findall(compact_reference)
        if len(number_matches) != 1:
            return False, f"reference_number_matches={number_matches}"
        reference_count = _chinese_number(number_matches[0][0])
        return (
            definition_count == reference_count,
            f"definition_count={definition_count}, reference_count={reference_count}",
        )

    if predicate == "REF_ONLY":
        if not snippets:
            raise LedgerError(f"REF_ONLY binding {binding_id} has no carrying snippets")
        normalized_definition = normalize(definition_text)
        normalized_reference = normalize(reference_text)
        missing_definition = [
            item for item in snippets if normalize(item) not in normalized_definition
        ]
        leaked = [item for item in snippets if normalize(item) in normalized_reference]
        refs = SECTION_REF_RE.findall(normalized_reference)
        target = binding.get("definition_section")
        passed = not missing_definition and not leaked and refs == [target]
        return passed, (
            f"missing_definition={missing_definition}, leaked_snippets={leaked}, "
            f"parsed_targets={refs}, expected={target}"
        )

    raise LedgerError(f"binding {binding_id} has unknown predicate: {predicate}")


def _evaluate_binding(binding: dict[str, Any], doc: VersionDoc) -> tuple[bool, str]:
    definition_section = binding.get("definition_section")
    if not isinstance(definition_section, str):
        raise LedgerError(f"binding {binding.get('id')} lacks definition_section")
    dod_by_id = {item.item_id: item for item in _dod_items(doc)}
    try:
        definition_text = _section_text(doc, definition_section)
        reference_text = _extract_reference_text(binding, doc, dod_by_id)
    except LedgerError as exc:
        return False, str(exc)
    return _evaluate_binding_text(binding, definition_text, reference_text)


def _binding_reference_key(binding: dict[str, Any]) -> str:
    reference = binding.get("reference")
    if not isinstance(reference, dict):
        raise LedgerError(f"binding {binding.get('id')} lacks reference")
    kind = reference.get("kind")
    reference_id = reference.get("id")
    if not isinstance(kind, str) or not isinstance(reference_id, str):
        raise LedgerError(f"binding {binding.get('id')} has malformed reference")
    return _binding_candidate_id(str(binding.get("definition_section")), f"{kind}:{reference_id}")


def _check_binding_inventory(
    data: dict[str, Any], documents: tuple[VersionDoc, ...]
) -> tuple[dict[str, dict[str, Any]], tuple[str, ...]]:
    target = documents[-1]
    exported, changed = _export_binding_candidates(documents, target)
    bindings_raw = data.get("bindings")
    ignored_raw = data.get("ignored_binding_candidates")
    process_raw = data.get("process_only")
    if not isinstance(bindings_raw, list) or not isinstance(ignored_raw, list):
        raise LedgerError("bindings and ignored_binding_candidates must be lists")
    if not isinstance(process_raw, list):
        raise LedgerError("process_only must be a list")

    bindings: dict[str, dict[str, Any]] = {}
    retained_keys: set[str] = set()
    for binding in bindings_raw:
        if not isinstance(binding, dict) or not isinstance(binding.get("id"), str):
            raise LedgerError("binding entries must be objects with string IDs")
        binding_id = binding["id"]
        if binding_id in bindings:
            raise LedgerError(f"duplicate binding id: {binding_id}")
        definition_section = binding.get("definition_section")
        if definition_section not in changed:
            raise LedgerError(
                f"binding {binding_id} definition section was not changed in corpus: "
                f"{definition_section}"
            )
        expected_transition = changed[str(definition_section)]
        if binding.get("source_transition") != expected_transition:
            raise LedgerError(
                f"binding {binding_id} source transition mismatch: "
                f"{binding.get('source_transition')} != {expected_transition}"
            )
        bindings[binding_id] = binding
        retained_keys.add(_binding_reference_key(binding))

    ignored = set(ignored_raw)
    if not all(isinstance(item, str) for item in ignored_raw):
        raise LedgerError("ignored binding candidate IDs must be strings")
    if len(ignored) != len(ignored_raw):
        raise LedgerError("ignored binding candidate IDs contain duplicates")
    stored_exported = data.get("binding_candidates")
    if not isinstance(stored_exported, list) or not all(
        isinstance(item, str) for item in stored_exported
    ):
        raise LedgerError("binding_candidates must be a list of strings")
    if stored_exported != list(exported):
        raise LedgerError("stored binding candidate export differs from generated export")
    if retained_keys & ignored:
        raise LedgerError("binding candidate retained/ignored sets overlap")
    if set(exported) != retained_keys | ignored:
        missing = sorted(set(exported) - retained_keys - ignored)
        added = sorted((retained_keys | ignored) - set(exported))
        raise LedgerError(
            f"binding candidate partition mismatch: missing={missing}, not_exported={added}"
        )

    dod_ids = {item.item_id for item in _dod_items(target)}
    bound_dod = {
        str(binding["reference"]["id"])
        for binding in bindings.values()
        if binding["reference"].get("kind") == "dod"
    }
    process_ids: set[str] = set()
    for entry in process_raw:
        if not isinstance(entry, dict) or not isinstance(entry.get("dod_id"), str):
            raise LedgerError("PROCESS_ONLY entries require dod_id")
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            raise LedgerError(f"PROCESS_ONLY {entry.get('dod_id')} lacks a reason")
        process_ids.add(entry["dod_id"])
    if bound_dod & process_ids:
        raise LedgerError(
            f"DoD entries cannot be both bound and PROCESS_ONLY: {bound_dod & process_ids}"
        )
    if dod_ids != bound_dod | process_ids:
        raise LedgerError(
            f"DoD external-anchor mismatch: missing={sorted(dod_ids - bound_dod - process_ids)}, "
            f"unknown={sorted((bound_dod | process_ids) - dod_ids)}"
        )
    return bindings, exported


def _candidate_from_data(raw: dict[str, Any]) -> DiffCandidate:
    required_strings = (
        "candidate_id",
        "old_version",
        "new_version",
        "old_path",
        "new_path",
        "pattern",
    )
    if not all(isinstance(raw.get(key), str) for key in required_strings):
        raise LedgerError("candidate entry has malformed string fields")
    required_ints = ("old_start", "old_end", "new_start", "new_end")
    if not all(isinstance(raw.get(key), int) for key in required_ints):
        raise LedgerError(f"candidate {raw.get('candidate_id')} has malformed spans")
    old_lines = raw.get("old_lines")
    new_lines = raw.get("new_lines")
    if not isinstance(old_lines, list) or not all(isinstance(item, str) for item in old_lines):
        raise LedgerError(f"candidate {raw.get('candidate_id')} has malformed old_lines")
    if not isinstance(new_lines, list) or not all(isinstance(item, str) for item in new_lines):
        raise LedgerError(f"candidate {raw.get('candidate_id')} has malformed new_lines")
    return DiffCandidate(
        candidate_id=raw["candidate_id"],
        old_version=raw["old_version"],
        new_version=raw["new_version"],
        old_path=raw["old_path"],
        new_path=raw["new_path"],
        old_start=raw["old_start"],
        old_end=raw["old_end"],
        new_start=raw["new_start"],
        new_end=raw["new_end"],
        old_lines=tuple(old_lines),
        new_lines=tuple(new_lines),
        pattern=raw["pattern"],
    )


def _check_candidate_ledger(
    data: dict[str, Any], documents: tuple[VersionDoc, ...], repo_root: Path
) -> tuple[int, int, int]:
    generated = _candidate_map(documents, repo_root)
    ledger = data.get("candidate_ledger")
    if not isinstance(ledger, dict):
        raise LedgerError("candidate_ledger must be an object")
    retained_raw = ledger.get("retained")
    ignored_raw = ledger.get("ignored")
    if not isinstance(retained_raw, list) or not isinstance(ignored_raw, list):
        raise LedgerError("candidate retained/ignored entries must be lists")

    retained: dict[str, dict[str, Any]] = {}
    ignored: dict[str, dict[str, Any]] = {}
    for raw, target in ((item, retained) for item in retained_raw):
        if not isinstance(raw, dict):
            raise LedgerError("retained candidate entries must be objects")
        candidate = _candidate_from_data(raw)
        if candidate.candidate_id in target:
            raise LedgerError(f"duplicate retained candidate ID: {candidate.candidate_id}")
        target[candidate.candidate_id] = raw
    for raw, target in ((item, ignored) for item in ignored_raw):
        if not isinstance(raw, dict):
            raise LedgerError("ignored candidate entries must be objects")
        candidate = _candidate_from_data(raw)
        if candidate.candidate_id in target:
            raise LedgerError(f"duplicate ignored candidate ID: {candidate.candidate_id}")
        target[candidate.candidate_id] = raw

    retained_ids = set(retained)
    ignored_ids = set(ignored)
    if retained_ids & ignored_ids:
        raise LedgerError("candidate retained/ignored sets overlap")
    if set(generated) != retained_ids | ignored_ids:
        raise LedgerError(
            "candidate partition mismatch: "
            f"missing={sorted(set(generated) - retained_ids - ignored_ids)}, "
            f"not_exported={sorted((retained_ids | ignored_ids) - set(generated))}"
        )

    docs_by_version = {item.version: item for item in documents}
    raw_deleted = _raw_deleted_lines(documents)
    covered: set[tuple[str, int]] = set()
    for candidate in generated.values():
        stored = retained.get(candidate.candidate_id) or ignored.get(candidate.candidate_id)
        if stored is None:
            raise LedgerError(f"candidate omitted from partition: {candidate.candidate_id}")
        stored_candidate = _candidate_from_data(stored)
        if stored_candidate != candidate:
            raise LedgerError(f"candidate data drift: {candidate.candidate_id}")
        covered.update(
            (candidate.old_version, line_number)
            for line_number in stored_candidate.old_line_numbers
        )

    if raw_deleted != covered:
        raise LedgerError(f"raw deletion coverage mismatch: {sorted(raw_deleted - covered)}")

    for candidate_id, raw in ignored.items():
        candidate = generated[candidate_id]
        category = raw.get("category")
        if category not in IGNORED_CATEGORIES:
            raise LedgerError(f"ignored candidate {candidate_id} has invalid category {category}")
        old_doc = docs_by_version[candidate.old_version]
        excluded = _excluded_lines(old_doc)
        if category == "OUT_OF_SCOPE":
            if not candidate.old_line_numbers or not candidate.old_line_numbers <= excluded:
                raise LedgerError(f"OUT_OF_SCOPE span escapes exemption: {candidate_id}")
        elif category == "FORMAT_ONLY":
            if normalize("\n".join(candidate.old_lines)) != normalize(
                "\n".join(candidate.new_lines)
            ):
                raise LedgerError(f"FORMAT_ONLY normalization differs: {candidate_id}")
        elif category == "SUBSUMED":
            retained_id = raw.get("subsumed_by")
            if not isinstance(retained_id, str) or retained_id not in retained:
                raise LedgerError(f"SUBSUMED candidate has no retained source: {candidate_id}")
            retained_pattern = str(retained[retained_id]["pattern"])
            if re.search(retained_pattern, normalize("\n".join(candidate.old_lines))) is None:
                raise LedgerError(f"SUBSUMED predicate failed: {candidate_id}")
        print(
            f"DIFF_CANDIDATE | {candidate_id} | IGNORED:{category} | "
            f"span={candidate.old_start}-{candidate.old_end}"
        )

    expected_matches = data.get("expected_matches")
    if not isinstance(expected_matches, dict):
        raise LedgerError("expected_matches must be an object")
    target_doc = documents[-1]
    for candidate_id, raw in retained.items():
        candidate = generated[candidate_id]
        old_doc = docs_by_version[candidate.old_version]
        replay = _matches_by_section(candidate.pattern, old_doc)
        replay_count = sum(replay.values())
        if replay_count < 1:
            raise LedgerError(f"retained candidate has no checked-scope replay hit: {candidate_id}")
        if raw.get("replay_count") != replay_count:
            recorded_count = raw.get("replay_count")
            raise LedgerError(
                f"replay count drift for {candidate_id}: {recorded_count} != {replay_count}"
            )
        if raw.get("replay_sections") != replay:
            raise LedgerError(
                f"replay section drift for {candidate_id}: {raw.get('replay_sections')} != {replay}"
            )
        actual = _matches_by_section(candidate.pattern, target_doc)
        expected = expected_matches.get(candidate_id)
        if expected != actual:
            raise LedgerError(
                f"RESIDUAL_DRIFT({candidate_id}): expected={expected}, actual={actual}"
            )
        print(f"DRIFT_PATTERN | {candidate_id} | OK | replay={replay} | expected={actual}")
    if set(expected_matches) != retained_ids:
        raise LedgerError("expected match IDs do not equal retained candidate IDs")
    return len(generated), len(retained), len(ignored)


def _target_doc(data: dict[str, Any], repo_root: Path) -> VersionDoc:
    raw_path = data.get("target_design")
    version = data.get("target_version")
    expected_sha = data.get("target_sha256")
    if not isinstance(raw_path, str) or not isinstance(version, str):
        raise LedgerError("target_design/target_version missing")
    path = repo_root / raw_path
    content = path.read_bytes()
    actual_sha = _sha256_bytes(content)
    if actual_sha != expected_sha:
        raise LedgerError(
            f"target design SHA mismatch: expected {expected_sha}, actual {actual_sha}; "
            "rerun bootstrap and review the baseline"
        )
    return VersionDoc(version, path, tuple(content.decode("utf-8").splitlines()))


def _check_bindings(
    data: dict[str, Any], documents: tuple[VersionDoc, ...], target: VersionDoc
) -> tuple[int, tuple[str, ...]]:
    bindings, exported = _check_binding_inventory(data, documents)
    drifts: list[str] = []
    for binding_id, binding in sorted(bindings.items()):
        passed, detail = _evaluate_binding(binding, target)
        print(f"BINDING | {binding_id} | {'OK' if passed else 'DRIFT'} | {detail}")
        if not passed:
            drifts.append(binding_id)
    if drifts:
        raise LedgerError(f"BINDING_DRIFT={drifts}")
    return len(bindings), exported


def _bootstrap(data_path: Path, repo_root: Path) -> int:
    data = _load_json(data_path)
    if data.get("schema_version") != SCHEMA_VERSION:
        raise LedgerError(f"unexpected schema version: {data.get('schema_version')}")

    history = repo_root / "docs/clang-fix-campaign/history/skill4"
    corpus: list[dict[str, str]] = []
    for index in range(13):
        version = f"1.{index}"
        suffix = "-FROZEN.md" if index == 12 else "-draft.md"
        path = history / f"p49-skill4-build-verify-design-v{version}{suffix}"
        content = path.read_bytes()
        corpus.append(
            {
                "version": version,
                "path": _relative(path, repo_root),
                "sha256": _sha256_bytes(content),
            }
        )
    data["version_corpus"] = corpus
    documents = _load_versions(data, repo_root)
    generated = _candidate_map(documents, repo_root)
    docs_by_version = {item.version: item for item in documents}
    retained: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []
    expected: dict[str, dict[str, int]] = {}
    for candidate in sorted(
        generated.values(), key=lambda item: (_version_key(item.old_version), item.old_start)
    ):
        raw = candidate.as_dict()
        old_doc = docs_by_version[candidate.old_version]
        if candidate.old_line_numbers <= _excluded_lines(old_doc):
            raw["category"] = "OUT_OF_SCOPE"
            ignored.append(raw)
            continue
        if normalize("\n".join(candidate.old_lines)) == normalize("\n".join(candidate.new_lines)):
            raw["category"] = "FORMAT_ONLY"
            ignored.append(raw)
            continue
        replay = _matches_by_section(candidate.pattern, old_doc)
        replay_count = sum(replay.values())
        if replay_count < 1:
            raise LedgerError(
                "cannot classify in-scope candidate with zero replay hits: "
                f"{candidate.candidate_id}"
            )
        raw["replay_kind"] = "regression"
        raw["replay_count"] = replay_count
        raw["replay_sections"] = replay
        retained.append(raw)
        expected[candidate.candidate_id] = _matches_by_section(candidate.pattern, documents[-1])
    data["candidate_ledger"] = {"retained": retained, "ignored": ignored}
    data["expected_matches"] = expected

    exported, changed = _export_binding_candidates(documents, documents[-1])
    bindings = data.get("bindings")
    if not isinstance(bindings, list):
        raise LedgerError("bootstrap requires a manually reviewed bindings list")
    retained_binding_keys: set[str] = set()
    for binding in bindings:
        if not isinstance(binding, dict):
            raise LedgerError("binding entries must be objects")
        section = binding.get("definition_section")
        if not isinstance(section, str) or section not in changed:
            raise LedgerError(f"binding definition section is not diff-derived: {section}")
        binding["source_transition"] = changed[section]
        retained_binding_keys.add(_binding_reference_key(binding))
    if not retained_binding_keys <= set(exported):
        raise LedgerError(
            f"bindings not proposed by exporter: {sorted(retained_binding_keys - set(exported))}"
        )
    data["binding_candidates"] = list(exported)
    data["ignored_binding_candidates"] = sorted(set(exported) - retained_binding_keys)

    target_path = repo_root / str(data["target_design"])
    target_content = target_path.read_bytes()
    corpus_target = documents[-1].path.read_bytes()
    if target_content != corpus_target:
        raise LedgerError("target candidate and v1.12 history corpus are not byte-identical")
    data["target_sha256"] = _sha256_bytes(target_content)
    data["generated_from"] = str(data["target_design"])
    data_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"BOOTSTRAP | candidates={len(generated)} retained={len(retained)} "
        f"ignored={len(ignored)} binding_candidates={len(exported)} "
        f"bindings={len(bindings)}"
    )
    return 0


def _run_check(data_path: Path, repo_root: Path) -> int:
    data = _load_json(data_path)
    if data.get("schema_version") != SCHEMA_VERSION:
        raise LedgerError(f"unexpected schema version: {data.get('schema_version')}")
    documents = _load_versions(data, repo_root)
    target = _target_doc(data, repo_root)
    if target.path.read_bytes() != documents[-1].path.read_bytes():
        raise LedgerError("target candidate differs from Git-anchored v1.12 corpus")
    exported_count, retained_count, ignored_count = _check_candidate_ledger(
        data, documents, repo_root
    )
    binding_count, binding_candidates = _check_bindings(data, documents, target)
    print(
        "SUMMARY | "
        f"RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | exported={exported_count} | "
        f"retained={retained_count} | ignored={ignored_count} | "
        f"bindings={binding_count} | binding_candidates={len(binding_candidates)}"
    )
    return 0


def _admission_v19(data_path: Path, repo_root: Path) -> int:
    data = _load_json(data_path)
    documents = _load_versions(data, repo_root)
    bindings, _ = _check_binding_inventory(data, documents)
    v19 = next(item for item in documents if item.version == "1.9")
    drifts: list[str] = []
    for binding_id, binding in sorted(bindings.items()):
        passed, detail = _evaluate_binding(binding, v19)
        if not passed:
            drifts.append(binding_id)
            print(f"BINDING_DRIFT | {binding_id} | {detail}")
    admission = data.get("admission_v19")
    if not isinstance(admission, dict) or not isinstance(admission.get("required"), list):
        raise LedgerError("admission_v19.required must be a list")
    required = set(admission["required"])
    if not drifts or not required <= set(drifts):
        raise LedgerError(
            f"admission falsification incomplete: required={sorted(required)}, actual={drifts}"
        )
    print(f"ADMISSION_V19 | BINDING_DRIFT={len(drifts)} | required_known=2 | RED_AS_EXPECTED")
    return 1


def _negative_out_of_scope(data_path: Path, repo_root: Path) -> int:
    data = _load_json(data_path)
    documents = _load_versions(data, repo_root)
    ledger = data.get("candidate_ledger")
    if not isinstance(ledger, dict) or not isinstance(ledger.get("ignored"), list):
        raise LedgerError("ignored ledger missing")
    out_items = [
        item
        for item in ledger["ignored"]
        if isinstance(item, dict) and item.get("category") == "OUT_OF_SCOPE"
    ]
    if not out_items:
        raise LedgerError("no OUT_OF_SCOPE item available for negative fixture")
    unexpected_green: list[str] = []
    for item in out_items:
        raw = dict(item)
        old_version = str(raw["old_version"])
        doc = next(value for value in documents if value.version == old_version)
        first_in_scope = next(
            index for index in range(1, len(doc.lines) + 1) if index not in _excluded_lines(doc)
        )
        raw["old_start"] = first_in_scope
        raw["old_end"] = first_in_scope
        candidate = _candidate_from_data(raw)
        passed = candidate.old_line_numbers <= _excluded_lines(doc)
        candidate_id = str(item["candidate_id"])
        print(
            f"OUT_OF_SCOPE_MISUSE | {candidate_id} | old_version=v{old_version} | "
            f"in_scope_line={first_in_scope} | gate_exit={0 if passed else 1}"
        )
        if passed:
            unexpected_green.append(candidate_id)
    if unexpected_green:
        print(f"OUT_OF_SCOPE_FIXTURE_INVALID | unexpected_green={unexpected_green}")
        return 2
    print(f"OUT_OF_SCOPE_SUMMARY | items={len(out_items)} | RED_AS_EXPECTED")
    return 1


def _negative_binding(data_path: Path, repo_root: Path, binding_id: str) -> int:
    data = _load_json(data_path)
    documents = _load_versions(data, repo_root)
    bindings, _ = _check_binding_inventory(data, documents)
    binding = bindings.get(binding_id)
    if binding is None:
        raise LedgerError(f"unknown binding: {binding_id}")
    target = _target_doc(data, repo_root)
    dod_by_id = {item.item_id: item for item in _dod_items(target)}
    definition_text = _section_text(target, str(binding["definition_section"]))
    reference_text = _extract_reference_text(binding, target, dod_by_id)
    passed, detail = _evaluate_binding_text(binding, definition_text, reference_text)
    if not passed:
        raise LedgerError(f"baseline binding is not green: {binding_id}: {detail}")

    predicate = binding.get("predicate")
    outcomes: list[tuple[str, bool]] = []
    if predicate == "TEXT_CONTAINS":
        for index, snippet in enumerate(binding["canonical_snippets"], 1):
            normalized_reference = normalize(reference_text)
            mutant = normalized_reference.replace(normalize(snippet), "")
            mutant_passed, _ = _evaluate_binding_text(binding, definition_text, mutant)
            outcomes.append((f"delete_snippet_{index}", mutant_passed))
    elif predicate == "COUNT_EQUAL":
        compact = re.sub(r"\s+", "", normalize(reference_text))
        match = NUMBER_RE.search(compact)
        if match is None:
            raise LedgerError(f"COUNT_EQUAL fixture cannot find numeral: {binding_id}")
        deleted = compact[: match.start(1)] + compact[match.end(1) :]
        changed = compact[: match.start(1)] + "99" + compact[match.end(1) :]
        outcomes.append(
            ("delete_numeral", _evaluate_binding_text(binding, definition_text, deleted)[0])
        )
        outcomes.append(
            ("change_count", _evaluate_binding_text(binding, definition_text, changed)[0])
        )
        covered = binding.get("covered_mutation")
        outside = binding.get("outside_mutation")
        if not isinstance(covered, str) or not isinstance(outside, str):
            raise LedgerError(f"COUNT_EQUAL binding {binding_id} lacks selector mutations")
        outcomes.append(
            (
                "definition_covered_add",
                _evaluate_binding_text(binding, definition_text + "\n" + covered, reference_text)[
                    0
                ],
            )
        )
        outside_passed = _evaluate_binding_text(
            binding, definition_text + "\n" + outside, reference_text
        )[0]
        print(
            f"NEGATIVE_BINDING | {binding_id} | "
            f"selector_outside_interference_exit={0 if outside_passed else 1}"
        )
        if not outside_passed:
            return 2
    elif predicate == "REF_ONLY":
        snippet = str(binding["canonical_snippets"][0])
        outcomes.append(
            (
                "inject_restated_snippet",
                _evaluate_binding_text(binding, definition_text, reference_text + "\n" + snippet)[
                    0
                ],
            )
        )
        target_ref = str(binding["definition_section"])
        wrong_target = "§5.4.3" if target_ref != "§5.4.3" else "§5.4.4"
        wrong = reference_text.replace(target_ref, wrong_target)
        outcomes.append(
            (
                "point_to_existing_wrong_section",
                _evaluate_binding_text(binding, definition_text, wrong)[0],
            )
        )
    else:
        raise LedgerError(f"unsupported negative fixture predicate: {predicate}")

    unexpected_green = [name for name, mutant_passed in outcomes if mutant_passed]
    for name, mutant_passed in outcomes:
        print(f"NEGATIVE_BINDING | {binding_id} | {name} | gate_exit={0 if mutant_passed else 1}")
    if unexpected_green:
        print(f"NEGATIVE_BINDING_INVALID | {binding_id} | unexpected_green={unexpected_green}")
        return 2
    return 1


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("bootstrap", "check", "admission-v19", "negative-binding", "negative-fixture"),
    )
    parser.add_argument("value", nargs="?")
    parser.add_argument("--data", type=Path, default=_default_data_path())
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = _repo_root()
    data_path = args.data.resolve()
    try:
        if args.action == "bootstrap":
            return _bootstrap(data_path, repo_root)
        if args.action == "check":
            return _run_check(data_path, repo_root)
        if args.action == "admission-v19":
            return _admission_v19(data_path, repo_root)
        if args.action == "negative-binding":
            if args.value is None:
                raise LedgerError("negative-binding requires a binding ID")
            return _negative_binding(data_path, repo_root, args.value)
        if args.action == "negative-fixture":
            if args.value != "out-of-scope-misuse":
                raise LedgerError("negative-fixture requires out-of-scope-misuse")
            return _negative_out_of_scope(data_path, repo_root)
    except (LedgerError, OSError) as exc:
        print(f"DESIGN_DRIFT_LEDGER_ERROR: {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"unhandled action: {args.action}")


if __name__ == "__main__":
    raise SystemExit(main())
