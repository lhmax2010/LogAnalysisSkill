#!/usr/bin/env python3
"""Compare frozen design attribution tables with the symbol-audit inventory."""

from __future__ import annotations

import re
import sys
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
MODULE_SCOPE_HEADING = "### 1.2a "
SYMBOL_COLUMNS = frozenset({"symbol", "类型", "符号"})
MODULE_COLUMNS = frozenset({"module"})
OWNER_COLUMNS = frozenset({"owner", "归属"})
DEFINITION_COLUMNS = frozenset({"definition"})

SpecKey = tuple[str, str]


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
        body = _merge_symbol_tables(
            body,
            skill_body,
            qb_discover_body,
            gerrit_fetch_body,
        )
        body_modules = parse_module_scope_table(design_path)
    except TableParseError as exc:
        print(f"PARSE_ERROR | {exc}")
        print(
            "SUMMARY | 0 OK | 0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | "
            "0 OWNER_MISMATCH | 1 PARSE_ERROR"
        )
        return 1

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
    if len(sys.argv) != 1:
        print(
            "usage: table_audit_bridge.py "
            "[--key-fixture twin-both-binary-key|"
            "--negative-fixture twin-both-name-only]"
        )
        return 2
    return run(Path(__file__).resolve().parents[3])


if __name__ == "__main__":
    sys.exit(main())
