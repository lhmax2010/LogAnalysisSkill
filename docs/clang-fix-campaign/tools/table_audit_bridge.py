#!/usr/bin/env python3
"""Compare frozen design attribution tables with the symbol-audit inventory."""

from __future__ import annotations

import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from symbol_audit import SPECS, ModuleScopeSpec, SymbolSpec

SECTION_HEADINGS = (
    "## §2 ",
    "### 3.2 ",
    "### 3.3 ",
    "### 4.1 ",
)
CONVERGENCE_SECTION_HEADINGS = ("### 1.2 ",)
QB_DISCOVER_SECTION_HEADINGS = ("### 2.2 ",)
GERRIT_FETCH_SECTION_HEADINGS = ("## §0 ",)
BUILD_VERIFY_SECTION_HEADINGS = ("## §0 ",)
MODULE_SCOPE_HEADING = "### 1.2a "
SYMBOL_COLUMNS = frozenset({"symbol", "类型", "符号"})
MODULE_COLUMNS = frozenset({"module"})
OWNER_COLUMNS = frozenset({"owner", "归属"})
DEFINITION_COLUMNS = frozenset({"definition"})

SpecKey = tuple[str, str]
RelocationTriplet = tuple[str, str, str]

BUILD_VERIFY_RELOCATIONS: dict[RelocationTriplet, RelocationTriplet] = {
    (
        "ci_triage/verify/workspace.py",
        "create_worktree",
        "build-verify",
    ): (
        "tizen_build_verify/workspace.py",
        "create_worktree",
        "skill/tizen_build_verify",
    ),
    (
        "ci_triage/verify/workspace.py",
        "check_disk_and_maybe_cleanup",
        "build-verify",
    ): (
        "tizen_build_verify/workspace.py",
        "check_disk_and_maybe_cleanup",
        "skill/tizen_build_verify",
    ),
    (
        "ci_triage/verify/workspace.py",
        "_copy_repository",
        "build-verify",
    ): (
        "tizen_build_verify/workspace.py",
        "_copy_repository",
        "skill/tizen_build_verify",
    ),
}


class TableParseError(ValueError):
    """Frozen attribution table could not be parsed without guessing."""


@dataclass(frozen=True)
class BodyEntry:
    symbol: str
    definition: str
    owner: str
    line_number: int


@dataclass(frozen=True)
class BodyModuleEntry:
    module: str
    owner: str
    line_number: int


@dataclass(frozen=True)
class RelocationResult:
    entries: dict[SpecKey, BodyEntry]
    consumed_sources: frozenset[RelocationTriplet]
    produced_destinations: frozenset[RelocationTriplet]
    verdicts: tuple[str, ...]


def _triplet(entry: BodyEntry) -> RelocationTriplet:
    return (entry.definition, entry.symbol, entry.owner)


def _mapping_contract_reasons(
    mapping: Mapping[RelocationTriplet, RelocationTriplet],
    *,
    expected: Mapping[RelocationTriplet, RelocationTriplet] | None = None,
) -> tuple[str, ...]:
    destinations = tuple(mapping.values())
    reasons: list[str] = []
    if len(set(destinations)) != len(destinations):
        reasons.append("RELOCATION_NOT_BIJECTIVE: duplicate destination")
    if expected is not None and dict(mapping) != dict(expected):
        missing_sources = sorted(
            source for source in expected if source not in mapping
        )
        for source in missing_sources:
            reasons.append(f"UNMAPPED_SOURCE: production mapping omits {source}")
        reasons.append(
            "RELOCATION_MAPPING_NOT_EXACT: production mapping must contain "
            f"exactly {len(expected)} frozen pairs"
        )
    return tuple(reasons)


def _relocation_output_reasons(
    entries: dict[SpecKey, BodyEntry],
    consumed_sources: frozenset[RelocationTriplet],
    produced_destinations: frozenset[RelocationTriplet],
    mapping: Mapping[RelocationTriplet, RelocationTriplet],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for source_triplet, destination_triplet in mapping.items():
        if source_triplet in consumed_sources and source_triplet[:2] in entries:
            reasons.append(f"SOURCE_REMAINS: {source_triplet}")
        if (
            destination_triplet in produced_destinations
            and destination_triplet[:2] not in entries
        ):
            reasons.append(f"DESTINATION_NOT_PRODUCED: {destination_triplet}")
    return tuple(reasons)


def apply_relocations(
    source_entries: dict[SpecKey, BodyEntry],
    destination_entries: dict[SpecKey, BodyEntry],
    mapping: Mapping[RelocationTriplet, RelocationTriplet],
) -> RelocationResult:
    """Apply an injected relocation mapping without consulting global state."""

    output = dict(source_entries)
    consumed: set[RelocationTriplet] = set()
    produced: set[RelocationTriplet] = set()
    verdicts = list(_mapping_contract_reasons(mapping))

    for source_triplet, destination_triplet in mapping.items():
        source_key = source_triplet[:2]
        destination_key = destination_triplet[:2]
        source_entry = source_entries.get(source_key)
        if source_entry is None or _triplet(source_entry) != source_triplet:
            verdicts.append(f"UNMAPPED_SOURCE: {source_triplet}")
            continue

        destination_entry = destination_entries.get(destination_key)
        if destination_entry is None:
            same_symbol = tuple(
                entry
                for entry in destination_entries.values()
                if entry.symbol == destination_triplet[1]
            )
            if same_symbol:
                verdicts.append(
                    "DESTINATION_DEFINITION_MISMATCH: expected "
                    f"{destination_triplet[0]}, measured "
                    + ",".join(sorted(entry.definition for entry in same_symbol))
                )
            else:
                verdicts.append(f"MISSING_DESTINATION: {destination_triplet}")
            continue
        if _triplet(destination_entry) != destination_triplet:
            verdicts.append(
                "DESTINATION_MISMATCH: expected "
                f"{destination_triplet}, measured {_triplet(destination_entry)}"
            )
            continue

        output.pop(source_key, None)
        output[destination_key] = destination_entry
        consumed.add(source_triplet)
        produced.add(destination_triplet)

    verdicts.extend(
        _relocation_output_reasons(
            output,
            frozenset(consumed),
            frozenset(produced),
            mapping,
        )
    )

    return RelocationResult(
        entries=output,
        consumed_sources=frozenset(consumed),
        produced_destinations=frozenset(produced),
        verdicts=tuple(verdicts),
    )


def _cells(raw_line: str) -> list[str]:
    stripped = raw_line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        raise TableParseError(f"not a Markdown table row: {raw_line}")
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _symbol_names(cell: str, raw_line: str) -> tuple[str, ...]:
    code_spans = re.findall(r"`([^`]+)`", cell)
    candidates = code_spans or [cell.strip()]
    names: list[str] = []
    for candidate in candidates:
        match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)", candidate)
        if match is None:
            raise TableParseError(f"cannot parse symbol cell: {raw_line}")
        names.append(match.group(1))
    if not names:
        raise TableParseError(f"empty symbol cell: {raw_line}")
    return tuple(names)


def _owner(cell: str, raw_line: str) -> str:
    normalized = cell.replace("**", "").replace("`", "").strip()
    normalized = normalized.split("(", 1)[0].strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_/-]*", normalized):
        raise TableParseError(f"cannot parse owner cell: {raw_line}")
    return normalized


def _module(cell: str, raw_line: str) -> str:
    code_spans = re.findall(r"`([^`]+)`", cell)
    candidate = code_spans[0] if len(code_spans) == 1 else cell.strip()
    if not re.fullmatch(r"[A-Za-z0-9_./-]+\.py", candidate):
        raise TableParseError(f"cannot parse module cell: {raw_line}")
    return candidate


def _first_table(lines: list[str], heading_index: int) -> tuple[int, int]:
    start: int | None = None
    for index in range(heading_index + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("#"):
            break
        if stripped.startswith("|"):
            start = index
            break
    if start is None:
        raise TableParseError(f"no attribution table after: {lines[heading_index]}")

    end = start
    while end < len(lines) and lines[end].strip().startswith("|"):
        end += 1
    return start, end


def parse_design_tables(
    design_path: Path,
    *,
    section_headings: tuple[str, ...] = SECTION_HEADINGS,
) -> dict[SpecKey, BodyEntry]:
    """Parse selected frozen attribution tables, rejecting ambiguous rows."""

    lines = design_path.read_text(encoding="utf-8").splitlines()
    heading_indexes: dict[str, int] = {}
    for heading in section_headings:
        matches = [index for index, line in enumerate(lines) if line.startswith(heading)]
        if len(matches) != 1:
            raise TableParseError(
                f"expected one heading starting {heading!r}, found {len(matches)}"
            )
        heading_indexes[heading] = matches[0]

    entries: dict[SpecKey, BodyEntry] = {}
    for heading, heading_index in heading_indexes.items():
        start, end = _first_table(lines, heading_index)
        header = _cells(lines[start])
        if start + 1 >= end or not _is_separator(_cells(lines[start + 1])):
            raise TableParseError(f"missing table separator: {lines[start]}")
        try:
            symbol_index = next(
                index for index, name in enumerate(header) if name in SYMBOL_COLUMNS
            )
            owner_index = next(
                index for index, name in enumerate(header) if name in OWNER_COLUMNS
            )
            definition_index = next(
                index for index, name in enumerate(header)
                if name in DEFINITION_COLUMNS
            )
        except StopIteration as exc:
            raise TableParseError(
                "table lacks symbol/definition/owner columns after "
                f"{heading!r}: {lines[start]}"
            ) from exc

        for index in range(start + 2, end):
            raw_line = lines[index]
            cells = _cells(raw_line)
            if len(cells) != len(header):
                raise TableParseError(f"column count mismatch: {raw_line}")
            owner = _owner(cells[owner_index], raw_line)
            definition = _module(cells[definition_index], raw_line)
            for symbol in _symbol_names(cells[symbol_index], raw_line):
                entry = BodyEntry(symbol, definition, owner, index + 1)
                key = (definition, symbol)
                previous = entries.get(key)
                if previous is not None and previous.owner != owner:
                    raise TableParseError(
                        f"conflicting owners for {definition}:{symbol}: "
                        f"line {previous.line_number} has {previous.owner}, "
                        f"line {entry.line_number} has {entry.owner}"
                    )
                entries[key] = entry
    return entries


def _merge_symbol_tables(
    *tables: dict[SpecKey, BodyEntry],
) -> dict[SpecKey, BodyEntry]:
    merged: dict[SpecKey, BodyEntry] = {}
    for table in tables:
        duplicates = sorted(merged.keys() & table.keys())
        if duplicates:
            rendered = ",".join(f"{definition}:{symbol}" for definition, symbol in duplicates)
            raise TableParseError(
                "symbol definitions appear in multiple attribution tables: " + rendered
            )
        merged.update(table)
    return merged


def parse_module_scope_table(design_path: Path) -> dict[str, BodyModuleEntry]:
    """Parse the frozen module-scope attribution table without inference."""

    lines = design_path.read_text(encoding="utf-8").splitlines()
    matches = [
        index for index, line in enumerate(lines) if line.startswith(MODULE_SCOPE_HEADING)
    ]
    if len(matches) != 1:
        raise TableParseError(
            f"expected one heading starting {MODULE_SCOPE_HEADING!r}, found {len(matches)}"
        )
    start, end = _first_table(lines, matches[0])
    header = _cells(lines[start])
    if start + 1 >= end or not _is_separator(_cells(lines[start + 1])):
        raise TableParseError(f"missing table separator: {lines[start]}")
    try:
        module_index = next(
            index for index, name in enumerate(header) if name in MODULE_COLUMNS
        )
        owner_index = next(
            index for index, name in enumerate(header) if name in OWNER_COLUMNS
        )
    except StopIteration as exc:
        raise TableParseError(
            f"module-scope table lacks module/owner columns: {lines[start]}"
        ) from exc

    entries: dict[str, BodyModuleEntry] = {}
    for index in range(start + 2, end):
        raw_line = lines[index]
        cells = _cells(raw_line)
        if len(cells) != len(header):
            raise TableParseError(f"column count mismatch: {raw_line}")
        module = _module(cells[module_index], raw_line)
        entry = BodyModuleEntry(module, _owner(cells[owner_index], raw_line), index + 1)
        if module in entries:
            raise TableParseError(f"duplicate module-scope row for {module}: {raw_line}")
        entries[module] = entry
    return entries


def run(repo_root: Path) -> int:
    design_path = (
        repo_root / "docs/clang-fix-campaign/p49-step0-design-v2.1-FROZEN.md"
    )
    skill_design_path = repo_root / (
        "docs/clang-fix-campaign/"
        "p49-skill1-convergence-judge-design-v1.4-FROZEN.md"
    )
    qb_discover_design_path = repo_root / (
        "docs/clang-fix-campaign/"
        "p49-skill2-qb-discover-design-v1.3-FROZEN.md"
    )
    gerrit_fetch_design_path = repo_root / (
        "docs/clang-fix-campaign/"
        "p49-skill3-gerrit-fetch-design-v1.3.1-FROZEN.md"
    )
    build_verify_design_path = repo_root / (
        "docs/clang-fix-campaign/"
        "p49-skill4-build-verify-design-v1.12.1-FROZEN.md"
    )
    try:
        body = parse_design_tables(design_path)
        skill_body = parse_design_tables(
            skill_design_path,
            section_headings=CONVERGENCE_SECTION_HEADINGS,
        )
        qb_discover_body = parse_design_tables(
            qb_discover_design_path,
            section_headings=QB_DISCOVER_SECTION_HEADINGS,
        )
        gerrit_fetch_body = parse_design_tables(
            gerrit_fetch_design_path,
            section_headings=GERRIT_FETCH_SECTION_HEADINGS,
        )
        build_verify_body = parse_design_tables(
            build_verify_design_path,
            section_headings=BUILD_VERIFY_SECTION_HEADINGS,
        )
        mapping_reasons = _mapping_contract_reasons(
            BUILD_VERIFY_RELOCATIONS,
            expected=BUILD_VERIFY_RELOCATIONS,
        )
        relocation = apply_relocations(
            body,
            build_verify_body,
            BUILD_VERIFY_RELOCATIONS,
        )
        relocation_destinations = {
            destination[:2] for destination in BUILD_VERIFY_RELOCATIONS.values()
        }
        build_verify_new_body = {
            key: entry
            for key, entry in build_verify_body.items()
            if key not in relocation_destinations
        }
        body = _merge_symbol_tables(
            relocation.entries,
            skill_body,
            qb_discover_body,
            gerrit_fetch_body,
            build_verify_new_body,
        )
        body_modules = parse_module_scope_table(design_path)
    except TableParseError as exc:
        print(f"PARSE_ERROR | {exc}")
        print(
            "SUMMARY | 0 OK | 0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | "
            "0 OWNER_MISMATCH | 1 PARSE_ERROR"
        )
        return 1

    relocation_verdicts = (*mapping_reasons, *relocation.verdicts)
    if relocation_verdicts:
        for verdict in relocation_verdicts:
            print(f"RELOCATION | {verdict}")
        print(
            "SUMMARY | 0 OK | 0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | "
            "0 OWNER_MISMATCH | 1 RELOCATION_ERROR | 0 PARSE_ERROR"
        )
        return 1
    print(
        "RELOCATION | "
        f"consumed={len(relocation.consumed_sources)}/"
        f"{len(BUILD_VERIFY_RELOCATIONS)} | "
        f"produced={len(relocation.produced_destinations)}/"
        f"{len(BUILD_VERIFY_RELOCATIONS)} | OK"
    )

    symbol_specs = tuple(spec for spec in SPECS if isinstance(spec, SymbolSpec))
    module_specs = tuple(spec for spec in SPECS if isinstance(spec, ModuleScopeSpec))
    inventory = {
        (spec.definition, spec.name): spec.owner for spec in symbol_specs
    }
    module_inventory = {spec.module: spec.owner for spec in module_specs}
    if len(inventory) != len(symbol_specs):
        print("PARSE_ERROR | duplicate (definition, symbol) keys in symbol_audit.SPECS")
        print(
            "SUMMARY | 0 OK | 0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | "
            "0 OWNER_MISMATCH | 1 PARSE_ERROR"
        )
        return 1
    if len(module_inventory) != len(module_specs):
        print("PARSE_ERROR | duplicate module names in symbol_audit.SPECS")
        print(
            "SUMMARY | 0 SYMBOL OK | 0 MODULE-SCOPE OK | "
            "0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | "
            "0 OWNER_MISMATCH | 1 PARSE_ERROR"
        )
        return 1

    all_symbols = sorted(body.keys() | inventory.keys())
    missing_inventory = 0
    missing_body = 0
    owner_mismatch = 0
    ok = 0
    print("definition | symbol | body_owner | inventory_owner | verdict")
    for key in all_symbols:
        definition, symbol = key
        body_entry = body.get(key)
        body_owner = body_entry.owner if body_entry is not None else "-"
        inventory_owner = inventory.get(key, "-")
        if body_entry is None:
            verdict = "MISSING_FROM_BODY"
            missing_body += 1
        elif key not in inventory:
            verdict = "MISSING_FROM_INVENTORY"
            missing_inventory += 1
        elif body_owner != inventory_owner:
            verdict = "OWNER_MISMATCH"
            owner_mismatch += 1
        else:
            verdict = "OK"
            ok += 1
        print(
            f"{definition} | {symbol} | {body_owner} | "
            f"{inventory_owner} | {verdict}"
        )

    module_ok = 0
    print("module | body_owner | inventory_owner | verdict")
    for module in sorted(body_modules.keys() | module_inventory.keys()):
        body_module_entry = body_modules.get(module)
        body_owner = body_module_entry.owner if body_module_entry is not None else "-"
        inventory_owner = module_inventory.get(module, "-")
        if body_module_entry is None:
            verdict = "MISSING_FROM_BODY"
            missing_body += 1
        elif module not in module_inventory:
            verdict = "MISSING_FROM_INVENTORY"
            missing_inventory += 1
        elif body_owner != inventory_owner:
            verdict = "OWNER_MISMATCH"
            owner_mismatch += 1
        else:
            verdict = "OK"
            module_ok += 1
        print(f"{module} | {body_owner} | {inventory_owner} | {verdict}")

    print(
        f"SUMMARY | {ok} SYMBOL OK | {module_ok} MODULE-SCOPE OK | "
        f"{missing_inventory} MISSING_FROM_INVENTORY | "
        f"{missing_body} MISSING_FROM_BODY | {owner_mismatch} OWNER_MISMATCH | "
        "0 PARSE_ERROR"
    )
    return 1 if missing_inventory or missing_body or owner_mismatch else 0


def _body_entry(triplet: RelocationTriplet, line_number: int = 1) -> BodyEntry:
    definition, symbol, owner = triplet
    return BodyEntry(symbol, definition, owner, line_number)


def _run_relocation_negative_fixture(name: str) -> int:
    source = ("legacy.py", "S", "legacy-owner")
    destination = ("skill.py", "S", "skill-owner")
    mapping = {source: destination}
    source_entries = {source[:2]: _body_entry(source)}
    destination_entries = {destination[:2]: _body_entry(destination)}

    if name == "missing-destination":
        result = apply_relocations(source_entries, {}, mapping)
        reasons = result.verdicts
        expected = "MISSING_DESTINATION"
    elif name == "wrong-definition":
        wrong = ("wrong.py", "S", "skill-owner")
        result = apply_relocations(
            source_entries,
            {wrong[:2]: _body_entry(wrong)},
            mapping,
        )
        reasons = result.verdicts
        expected = "DESTINATION_DEFINITION_MISMATCH"
    elif name == "wrong-owner":
        wrong = ("skill.py", "S", "wrong-owner")
        result = apply_relocations(
            source_entries,
            {wrong[:2]: _body_entry(wrong)},
            mapping,
        )
        reasons = result.verdicts
        expected = "DESTINATION_MISMATCH"
    elif name == "source-remains":
        result = apply_relocations(source_entries, destination_entries, mapping)
        tampered = dict(result.entries)
        tampered[source[:2]] = _body_entry(source)
        reasons = _relocation_output_reasons(
            tampered,
            result.consumed_sources,
            result.produced_destinations,
            mapping,
        )
        expected = "SOURCE_REMAINS"
    elif name == "mapping-contract":
        production_items = tuple(BUILD_VERIFY_RELOCATIONS.items())
        missing = dict(production_items[:-1])
        extra = {
            **BUILD_VERIFY_RELOCATIONS,
            ("extra.py", "E", "old"): ("new.py", "E", "new"),
        }
        duplicate_destination = dict(BUILD_VERIFY_RELOCATIONS)
        duplicate_destination[production_items[1][0]] = production_items[0][1]
        cases = {
            "missing": _mapping_contract_reasons(
                missing,
                expected=BUILD_VERIFY_RELOCATIONS,
            ),
            "non-exact": _mapping_contract_reasons(
                extra,
                expected=BUILD_VERIFY_RELOCATIONS,
            ),
            "non-bijective": _mapping_contract_reasons(
                duplicate_destination,
                expected=BUILD_VERIFY_RELOCATIONS,
            ),
        }
        for case, case_reasons in cases.items():
            print(
                f"RELOCATION_NEGATIVE | {name}/{case} | "
                + "; ".join(case_reasons)
            )
        passed = (
            any("UNMAPPED_SOURCE" in item for item in cases["missing"])
            and any("RELOCATION_MAPPING_NOT_EXACT" in item for item in cases["non-exact"])
            and any("RELOCATION_NOT_BIJECTIVE" in item for item in cases["non-bijective"])
        )
        return 1 if passed else 0
    elif name == "source-table-mismatch":
        wrong_source = ("legacy.py", "S", "wrong-owner")
        result = apply_relocations(
            {wrong_source[:2]: _body_entry(wrong_source)},
            destination_entries,
            mapping,
        )
        reasons = result.verdicts
        expected = "UNMAPPED_SOURCE"
    else:
        print(f"unknown relocation negative fixture: {name}")
        return 2

    rendered = "; ".join(reasons) or "OK"
    print(f"RELOCATION_NEGATIVE | {name} | {rendered}")
    return 1 if any(expected in reason for reason in reasons) else 0


def _run_relocation_synthetic(name: str) -> int:
    a = ("old.py", "A", "old-owner")
    b = ("new.py", "B", "new-owner")
    c = ("old.py", "C", "old-owner")
    d = ("new.py", "D", "new-owner")
    x = ("other.py", "X", "other-owner")

    if name == "one":
        mapping = {a: b}
        result = apply_relocations(
            {a[:2]: _body_entry(a)},
            {b[:2]: _body_entry(b)},
            mapping,
        )
        passed = (
            result.consumed_sources == frozenset({a})
            and result.produced_destinations == frozenset({b})
            and set(result.entries) == {b[:2]}
            and not result.verdicts
        )
    elif name == "two":
        mapping = {a: b}
        result = apply_relocations(
            {x[:2]: _body_entry(x)},
            {b[:2]: _body_entry(b)},
            mapping,
        )
        passed = (
            result.consumed_sources == frozenset()
            and set(result.entries) == {x[:2]}
            and any("UNMAPPED_SOURCE" in verdict for verdict in result.verdicts)
        )
    elif name == "three":
        mapping = {a: b, c: d}
        result = apply_relocations(
            {a[:2]: _body_entry(a), x[:2]: _body_entry(x)},
            {b[:2]: _body_entry(b), d[:2]: _body_entry(d)},
            mapping,
        )
        passed = (
            result.consumed_sources == frozenset({a})
            and result.produced_destinations == frozenset({b})
            and set(result.entries) == {b[:2], x[:2]}
            and a[:2] not in result.entries
            and c[:2] not in result.entries
            and d[:2] not in result.entries
            and any("UNMAPPED_SOURCE" in verdict for verdict in result.verdicts)
        )
    else:
        print(f"unknown relocation synthetic fixture: {name}")
        return 2

    print(
        f"RELOCATION_SYNTHETIC | {name} | "
        f"consumed={sorted(result.consumed_sources)} | "
        f"produced={sorted(result.produced_destinations)} | "
        f"output={sorted(result.entries)} | verdicts={result.verdicts} | "
        f"{'OK' if passed else 'MISMATCH'}"
    )
    return 0 if passed else 1


def _run_key_fixture(name: str) -> int:
    sources = BodyEntry(
        "_attrs_to_map",
        "tizen_qb_discover/sources.py",
        "skill/tizen_qb_discover",
        1,
    )
    report = BodyEntry(
        "_attrs_to_map",
        "ci_triage/gbs_report.py",
        "triage-report",
        2,
    )
    if name == "twin-both-binary-key":
        merged = _merge_symbol_tables(
            {(sources.definition, sources.symbol): sources},
            {(report.definition, report.symbol): report},
        )
        print(
            "KEY_FIXTURE | twin-both-binary-key | "
            f"{len(merged)} distinct definitions | OK"
        )
        return 0
    if name == "twin-both-name-only":
        by_name = {entry.symbol: entry for entry in (sources, report)}
        if len(by_name) != 2:
            print(
                "NEGATIVE_FIXTURE | twin-both-name-only | MISMATCH: "
                "name-only key overwrote one definition"
            )
            return 1
        print("NEGATIVE_FIXTURE | twin-both-name-only | OK")
        return 0
    print(f"unknown key fixture: {name}")
    return 2


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] in {"--key-fixture", "--negative-fixture"}:
        return _run_key_fixture(sys.argv[2])
    if len(sys.argv) == 3 and sys.argv[1] == "--relocation-negative":
        return _run_relocation_negative_fixture(sys.argv[2])
    if len(sys.argv) == 3 and sys.argv[1] == "--relocation-synthetic":
        return _run_relocation_synthetic(sys.argv[2])
    if len(sys.argv) != 1:
        print(
            "usage: table_audit_bridge.py "
            "[--key-fixture twin-both-binary-key|"
            "--negative-fixture twin-both-name-only|"
            "--relocation-negative missing-destination|wrong-definition|"
            "wrong-owner|source-remains|mapping-contract|source-table-mismatch|"
            "--relocation-synthetic one|two|three]"
        )
        return 2
    return run(Path(__file__).resolve().parents[3])


if __name__ == "__main__":
    sys.exit(main())
