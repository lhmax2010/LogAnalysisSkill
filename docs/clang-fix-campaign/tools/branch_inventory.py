#!/usr/bin/env python3
"""Audit skill-6 symbol and branch inventories against the current source."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "clang-fix-campaign/branch-inventory/v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DESIGN = REPO_ROOT / (
    "docs/clang-fix-campaign/p49-skill6-triage-report-design-v1.8-FROZEN.md"
)
DEFAULT_DATA = Path(__file__).with_name("branch_inventory.skill6.json")
EXTERNAL_SOURCE = REPO_ROOT / "tizen-ci-shared/scripts/tizen_ci_shared/quickbuild_http.py"
EXCLUDED_QUALNAMES = frozenset({"_ReportTableParser", "_IframeParser"})
MODULES = (
    (
        "gbs_report",
        REPO_ROOT / "tizen-ci-triage/scripts/ci_triage/gbs_report.py",
        "tizen_triage_report/gbs_report.py",
    ),
    (
        "report",
        REPO_ROOT / "tizen-ci-triage/scripts/ci_triage/report.py",
        "tizen_triage_report/report.py",
    ),
)
OWNER = "skill/tizen_triage_report"
BRANCH_ID_RE = re.compile(
    r"(?P<qual>[A-Za-z_][A-Za-z0-9_.]*):(?P<line>[0-9]+):"
    r"(?P<kind>ifexp|compif|assert|case|raise|return|if)\b"
)
CALL_ID_RE = re.compile(r"(?P<qual>[A-Za-z_][A-Za-z0-9_.]*):(?P<line>[0-9]+):call")


class InventoryError(RuntimeError):
    """Raised when a design or source inventory is incomplete."""


@dataclass(frozen=True)
class BranchPoint:
    branch_id: str
    category: str


@dataclass(frozen=True)
class ModuleInventory:
    name: str
    source: Path
    definition: str
    symbols: tuple[str, ...]
    decision_ids: tuple[str, ...]
    terminal_ids: tuple[str, ...]

    @property
    def all_ids(self) -> tuple[str, ...]:
        return self.decision_ids + self.terminal_ids


@dataclass(frozen=True)
class BranchRow:
    contract: str
    anchor: str
    local_ids: tuple[str, ...]
    external: bool


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _qualname(stack: list[str]) -> str:
    return ".".join(stack)


class _BranchVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.stack: list[str] = []
        self.excluded_depth = 0
        self.points: list[BranchPoint] = []

    def _add(self, node: ast.AST, kind: str, category: str, *, line: int | None = None) -> None:
        if self.excluded_depth:
            return
        lineno = line if line is not None else getattr(node, "lineno", None)
        if not isinstance(lineno, int):
            raise InventoryError(f"branch node lacks a line number: {ast.dump(node)}")
        self.points.append(BranchPoint(f"{_qualname(self.stack)}:{lineno}:{kind}", category))

    def _visit_scope(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> None:
        self.stack.append(node.name)
        excluded = node.name in EXCLUDED_QUALNAMES
        if excluded:
            self.excluded_depth += 1
        self.generic_visit(node)
        if excluded:
            self.excluded_depth -= 1
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._visit_scope(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._visit_scope(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self._visit_scope(node)

    def visit_If(self, node: ast.If) -> None:  # noqa: N802
        self._add(node, "if", "decision")
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:  # noqa: N802
        self._add(node, "ifexp", "decision")
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:  # noqa: N802
        self._add(node, "assert", "decision")
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        for condition in node.ifs:
            self._add(condition, "compif", "decision")
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:  # noqa: N802
        if not self.excluded_depth:
            for case in node.cases:
                line = getattr(case.pattern, "lineno", node.lineno)
                self._add(case.pattern, "case", "decision", line=line)
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:  # noqa: N802
        self._add(node, "raise", "terminal")
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:  # noqa: N802
        self._add(node, "return", "terminal")
        self.generic_visit(node)


def _top_level_symbols(tree: ast.Module) -> tuple[str, ...]:
    symbols: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    symbols.append(target.id)
    return tuple(symbols)


def _scan_module(name: str, source: Path, definition: str) -> ModuleInventory:
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    visitor = _BranchVisitor()
    visitor.visit(tree)
    ids = [point.branch_id for point in visitor.points]
    duplicates = sorted({branch_id for branch_id in ids if ids.count(branch_id) > 1})
    if duplicates:
        raise InventoryError(f"duplicate branch IDs in {source}: {duplicates}")
    return ModuleInventory(
        name=name,
        source=source,
        definition=definition,
        symbols=_top_level_symbols(tree),
        decision_ids=tuple(
            point.branch_id for point in visitor.points if point.category == "decision"
        ),
        terminal_ids=tuple(
            point.branch_id for point in visitor.points if point.category == "terminal"
        ),
    )


def _scan_modules() -> tuple[ModuleInventory, ...]:
    return tuple(_scan_module(*module) for module in MODULES)


def _section(text: str, section: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(section)}\b.*?(?=^## (?:§|附:)|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if match is None:
        raise InventoryError(f"design section not found: {section}")
    return match.group(0)


def _markdown_table(section_text: str, header: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    collecting = False
    for line in section_text.splitlines():
        if not line.startswith("|"):
            if collecting:
                break
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not collecting:
            if cells == header:
                collecting = True
                rows.append(cells)
            continue
        if cells and all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        raise InventoryError(f"Markdown table not found: {' | '.join(header)}")
    return rows


def _parse_symbol_table(design: Path) -> dict[tuple[str, str], str]:
    rows = _markdown_table(
        _section(design.read_text(encoding="utf-8"), "§0"),
        ["symbol", "definition", "owner"],
    )
    if not rows or rows[0] != ["symbol", "definition", "owner"]:
        raise InventoryError("§0 table must have symbol | definition | owner columns")
    parsed: dict[tuple[str, str], str] = {}
    for cells in rows[1:]:
        if len(cells) != 3:
            raise InventoryError(f"malformed §0 row: {cells}")
        symbol = cells[0].strip("`")
        definition = cells[1].strip("`")
        owner = cells[2].strip("`")
        key = (definition, symbol)
        if key in parsed:
            raise InventoryError(f"duplicate §0 symbol row: {key}")
        parsed[key] = owner
    return parsed


def _expected_symbol_table(inventories: tuple[ModuleInventory, ...]) -> dict[tuple[str, str], str]:
    return {
        (inventory.definition, symbol): OWNER
        for inventory in inventories
        for symbol in inventory.symbols
    }


def _parser_only(design: Path, inventories: tuple[ModuleInventory, ...]) -> None:
    actual = _parse_symbol_table(design)
    expected = _expected_symbol_table(inventories)
    missing = sorted(expected.keys() - actual.keys())
    extra = sorted(actual.keys() - expected.keys())
    owner_mismatch = sorted(
        (definition, symbol, expected[(definition, symbol)], actual[(definition, symbol)])
        for definition, symbol in expected.keys() & actual.keys()
        if expected[(definition, symbol)] != actual[(definition, symbol)]
    )
    if missing or extra or owner_mismatch:
        raise InventoryError(
            f"parser-only mismatch: missing={missing}, extra={extra}, "
            f"owner_mismatch={owner_mismatch}"
        )
    print(
        f"PARSER_ONLY | {len(actual)}/{len(expected)} | missing=0 | extra=0 | OWNER_MISMATCH=0 | OK"
    )


def _branch_rows(design: Path) -> tuple[BranchRow, ...]:
    rows = _markdown_table(
        _section(design.read_text(encoding="utf-8"), "§5"),
        ["契约句", "分支(代码锚)", "用例"],
    )
    if not rows or rows[0] != ["契约句", "分支(代码锚)", "用例"]:
        raise InventoryError("§5 branch table header is missing or malformed")
    result: list[BranchRow] = []
    for cells in rows[1:]:
        if len(cells) != 3:
            raise InventoryError(f"malformed §5 branch row: {cells}")
        contract, anchor, _ = cells
        external = "EXTERNAL_BRANCH" in anchor
        local_ids = (
            () if external else tuple(match.group(0) for match in BRANCH_ID_RE.finditer(anchor))
        )
        if not external and not local_ids:
            raise InventoryError(f"branch row has no exact local branch ID: {contract}")
        if external:
            calls = tuple(match.group(0) for match in CALL_ID_RE.finditer(anchor))
            required = (
                len(calls) == 1
                and "tizen_ci_shared.quickbuild_http:193:if" in anchor
                and "tizen_ci_shared.quickbuild_http:198:raise" in anchor
                and "QuickBuildError" in anchor
                and "COOKIE_EXPIRED" in anchor
            )
            if not required:
                raise InventoryError(f"EXTERNAL_BRANCH binding is incomplete for row: {contract}")
        result.append(BranchRow(contract, anchor, local_ids, external))
    return tuple(result)


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _validate_external_bindings(rows: tuple[BranchRow, ...]) -> None:
    trees = {
        inventory.name: ast.parse(inventory.source.read_text(encoding="utf-8"))
        for inventory in _scan_modules()
    }
    calls: dict[str, str | None] = {}
    for tree in trees.values():

        class Visitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.stack: list[str] = []

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
                self.stack.append(node.name)
                self.generic_visit(node)
                self.stack.pop()

            def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
                self.stack.append(node.name)
                self.generic_visit(node)
                self.stack.pop()

            def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
                calls[f"{_qualname(self.stack)}:{node.lineno}:call"] = _call_name(node)
                self.generic_visit(node)

        Visitor().visit(tree)
    for row in rows:
        if not row.external:
            continue
        call_id = CALL_ID_RE.search(row.anchor)
        assert call_id is not None
        measured_call = calls.get(call_id.group(0))
        if measured_call != "_raise_if_login_page":
            raise InventoryError(
                "EXTERNAL_BRANCH local call mismatch: "
                f"{call_id.group(0)} -> {measured_call!r}, expected '_raise_if_login_page'"
            )

    external_tree = ast.parse(
        EXTERNAL_SOURCE.read_text(encoding="utf-8"), filename=str(EXTERNAL_SOURCE)
    )
    nodes_by_line: dict[int, list[ast.AST]] = {}
    for node in ast.walk(external_tree):
        line = getattr(node, "lineno", None)
        if isinstance(line, int):
            nodes_by_line.setdefault(line, []).append(node)
    if not any(isinstance(node, ast.If) for node in nodes_by_line.get(193, [])):
        raise InventoryError(
            "EXTERNAL_BRANCH target tizen_ci_shared.quickbuild_http:193 is not ast.If"
        )
    raises = [node for node in nodes_by_line.get(198, []) if isinstance(node, ast.Raise)]
    if len(raises) != 1:
        raise InventoryError(
            "EXTERNAL_BRANCH target tizen_ci_shared.quickbuild_http:198 is not one ast.Raise"
        )
    exc = raises[0].exc
    if not isinstance(exc, ast.Call) or _call_name(exc) != "QuickBuildError":
        raise InventoryError("EXTERNAL_BRANCH raise does not construct QuickBuildError")
    if (
        not exc.args
        or not isinstance(exc.args[0], ast.Constant)
        or exc.args[0].value != "COOKIE_EXPIRED"
    ):
        raise InventoryError("EXTERNAL_BRANCH QuickBuildError first argument is not COOKIE_EXPIRED")


def _load_data(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InventoryError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise InventoryError(f"unexpected data schema in {path}")
    return value


def _inventory_payload(inventories: tuple[ModuleInventory, ...]) -> dict[str, Any]:
    return {
        inventory.name: {
            "source": str(inventory.source.relative_to(REPO_ROOT)),
            "definition": inventory.definition,
            "decision_points": len(inventory.decision_ids),
            "terminal_outcomes": len(inventory.terminal_ids),
            "ids": list(inventory.all_ids),
        }
        for inventory in inventories
    }


def _check(design: Path, data_path: Path, inventories: tuple[ModuleInventory, ...]) -> None:
    data = _load_data(data_path)
    if data.get("target_design") != str(design.relative_to(REPO_ROOT)):
        raise InventoryError("data target_design does not match the checked design")
    if data.get("target_sha256") != _sha256(design):
        raise InventoryError("data target_sha256 does not match the checked design")
    expected_modules = _inventory_payload(inventories)
    if data.get("modules") != expected_modules:
        raise InventoryError("stored module inventory differs from the AST scan")

    rows = _branch_rows(design)
    _validate_external_bindings(rows)
    all_ids = {branch_id for inventory in inventories for branch_id in inventory.all_ids}
    referenced = {branch_id for row in rows for branch_id in row.local_ids}
    unknown = sorted(referenced - all_ids)
    if unknown:
        raise InventoryError(f"branch table references unknown IDs: {unknown}")
    reasons = data.get("unreferenced_reasons")
    if not isinstance(reasons, dict) or not all(
        isinstance(key, str) and isinstance(value, str) and value.strip()
        for key, value in reasons.items()
    ):
        raise InventoryError("unreferenced_reasons must be a non-empty string mapping")
    unreferenced = all_ids - referenced
    if set(reasons) != unreferenced:
        raise InventoryError(
            "unreferenced reason partition mismatch: "
            f"missing={sorted(unreferenced - set(reasons))}, "
            f"extra={sorted(set(reasons) - unreferenced)}"
        )
    external_count = sum(row.external for row in rows)
    print(
        f"BRANCH_TABLE | rows={len(rows)} | referenced_ids={len(referenced)} | "
        f"unreferenced_ids={len(unreferenced)} | external_rows={external_count} | OK"
    )
    for inventory in inventories:
        print(
            f"MODULE | {inventory.name} | decision_points={len(inventory.decision_ids)} | "
            f"terminal_outcomes={len(inventory.terminal_ids)} | "
            f"ids={len(inventory.all_ids)} | unique=YES"
        )
    print(
        f"SUMMARY | modules={len(inventories)} | ids={len(all_ids)} | "
        "collisions=0 | unknown_refs=0 | missing_reasons=0 | OK"
    )


def _admission_v17(snapshot: Path) -> int:
    text = snapshot.read_text(encoding="utf-8")
    defects = {
        "HANDWRITTEN_BOOL_COUNT": "实存 14 处" in text,
        "MISSING_V17_REVISION_BLOCK": "> **v1.7 修订" not in text,
    }
    for defect, present in defects.items():
        print(f"ADMISSION | {defect} | {'DRIFT' if present else 'NOT_FOUND'}")
    if not all(defects.values()):
        raise InventoryError(f"v1.7 admission fixture lacks required defects: {defects}")
    print("ADMISSION | snapshot=v1.7 | required=2/2 | RED_AS_EXPECTED")
    return 1


def _print_symbols(inventories: tuple[ModuleInventory, ...]) -> None:
    print("| symbol | definition | owner |")
    print("|---|---|---|")
    for inventory in inventories:
        for symbol in inventory.symbols:
            print(f"| `{symbol}` | `{inventory.definition}` | `{OWNER}` |")


def _print_inventory(inventories: tuple[ModuleInventory, ...]) -> None:
    print(json.dumps(_inventory_payload(inventories), indent=2, sort_keys=True))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("symbols", "inventory", "parser-only", "check", "admission-v17"),
    )
    parser.add_argument("--design", type=Path, default=DEFAULT_DESIGN)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=REPO_ROOT / "docs/clang-fix-campaign/history/skill6/"
        "p49-skill6-triage-report-design-v1.7-draft.md",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    try:
        design = args.design if args.design.is_absolute() else REPO_ROOT / args.design
        data = args.data if args.data.is_absolute() else REPO_ROOT / args.data
        snapshot = args.snapshot if args.snapshot.is_absolute() else REPO_ROOT / args.snapshot
        inventories = _scan_modules()
        if args.action == "symbols":
            _print_symbols(inventories)
        elif args.action == "inventory":
            _print_inventory(inventories)
        elif args.action == "parser-only":
            _parser_only(design, inventories)
        elif args.action == "check":
            _parser_only(design, inventories)
            _check(design, data, inventories)
        else:
            return _admission_v17(snapshot)
    except (InventoryError, OSError, SyntaxError) as exc:
        print(f"ERROR | {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
