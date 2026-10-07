"""E10 callable identity evidence. Compile/disassemble only, never execute code."""

from __future__ import annotations

import ast
import dis
import types
from collections import Counter, defaultdict
from pathlib import PurePosixPath
from typing import Any

from terminal_scan import ScanError

CALLABLES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


def source_span(node: ast.AST) -> tuple[int, int, int, int]:
    return (node.lineno, node.col_offset, node.end_lineno, node.end_col_offset)  # type: ignore[attr-defined]


def callable_ids(source: str, path: str, command: list[str]) -> dict[str, Any]:
    tree = ast.parse(source, filename=path)
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    nodes = [node for node in ast.walk(tree) if isinstance(node, CALLABLES)]
    by_span = {source_span(node): node for node in nodes}
    code_nodes: dict[int, ast.AST] = {}
    code_parents: dict[int, types.CodeType] = {}
    codes: list[types.CodeType] = []
    issues: list[dict[str, Any]] = []

    def visit(code: types.CodeType) -> None:
        children = [value for value in code.co_consts if isinstance(value, types.CodeType)]
        for instruction in dis.get_instructions(code):
            child = instruction.argval
            if not isinstance(child, types.CodeType):
                continue
            pos = instruction.positions
            if pos is None:
                continue
            span = (pos.lineno, pos.col_offset, pos.end_lineno, pos.end_col_offset)
            if span in by_span:
                code_nodes[id(child)] = by_span[span]
        for child in children:
            code_parents[id(child)] = code
            codes.append(child)
            visit(child)

    top = compile(source, path, "exec", dont_inherit=True, optimize=0)
    visit(top)
    matched = set(code_nodes.values())
    for code in codes:
        if id(code) in code_nodes:
            continue
        candidates = [
            node
            for node in nodes
            if node not in matched
            and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == code.co_name
            and min([node.lineno, *[d.lineno for d in node.decorator_list]]) == code.co_firstlineno
        ]
        if len(candidates) == 1:
            code_nodes[id(code)] = candidates[0]
            matched.add(candidates[0])
    for node in nodes:
        if node not in matched:
            issues.append(
                {
                    "reason": "CALLABLE_CODE_LOCATION_UNRESOLVED",
                    "path": path,
                    "span": source_span(node),
                    "source": ast.get_source_segment(source, node),
                }
            )

    # A compiler parent, not syntactic AST containment, owns a default-argument lambda.
    names: dict[int, str] = {id(top): ""}
    pending = codes[:]
    counts: Counter[str] = Counter()
    while pending:
        ready = [c for c in pending if id(code_parents[id(c)]) in names]
        ready.sort(
            key=lambda c: (
                source_span(code_nodes[id(c)])
                if id(c) in code_nodes
                else (c.co_firstlineno, -1, c.co_firstlineno, -1)
            )
        )
        if not ready:
            raise ScanError("CALLABLE_CODE_PARENT_CYCLE")
        for code in ready:
            parent = code_parents[id(code)]
            name = code.co_qualname
            if parent is not top and name.startswith(parent.co_qualname + "."):
                name = names[id(parent)] + name[len(parent.co_qualname) :]
            if code.co_name == "<lambda>":
                prefix = name.removesuffix("<lambda>")
                counts[prefix] += 1
                name = prefix + f"<lambda>#{counts[prefix]}"
            names[id(code)] = name
        ready_ids = {id(code) for code in ready}
        pending = [code for code in pending if id(code) not in ready_ids]

    rows = []
    for code in codes:
        matched_node = code_nodes.get(id(code))
        if matched_node is None:
            continue
        assert isinstance(matched_node, CALLABLES)
        node = matched_node
        qualname = names[id(code)]
        binding = None
        if isinstance(node, ast.Lambda):
            parent_node = parents[node]
            if isinstance(parent_node, ast.Assign) and len(parent_node.targets) == 1:
                target = parent_node.targets[0]
                scope = parents[parent_node]
                while not isinstance(scope, (ast.Module, ast.ClassDef, *CALLABLES)):
                    scope = parents[scope]
                if isinstance(target, ast.Name) and isinstance(scope, (ast.Module, ast.ClassDef)):
                    binding = target.id
        elif "<locals>" not in qualname.split("."):
            binding = qualname
        row: dict[str, Any] = {
            "candidate_id": path + "#PROXY#" + qualname,
            "path": path,
            "qualname": qualname,
            "co_qualname": code.co_qualname,
            "span": source_span(node),
            "anonymous": isinstance(node, ast.Lambda),
            "binding_name": binding,
            "source": ast.get_source_segment(source, node),
        }
        if "<locals>" in qualname.split("."):
            row["admission"] = {
                "status": "REJECTED_NOT_SHIM",
                "authority": "E10-2",
                "claim": "定义于函数体内不可按名字寻址",
                "predicate": "lexical qualname 含 <locals>",
                "command": command,
                "output": {"span": row["span"], "co_qualname": code.co_qualname},
            }
        rows.append(row)
    rows.sort(key=lambda row: row["span"])
    return {"callables": rows, "issues": issues}


def name_forms(row: dict[str, Any], module: str | None) -> list[dict[str, str]]:
    """E10-1 supplies n; E5 permits dotted forms only for packaged modules."""
    path = PurePosixPath(row["path"])
    forms = [
        {"kind": "source_path", "value": str(path)},
        {"kind": "package_path", "value": str(path.parent) + "/"},
    ]
    if module:
        forms.append({"kind": "dotted_module", "value": module})
        parent, dot, leaf = module.rpartition(".")
        if dot:
            forms.append({"kind": "split_import", "module": parent, "name": leaf})
        if row["binding_name"]:
            forms.append({"kind": "dotted_binding", "value": module + "." + row["binding_name"]})
            forms.append({"kind": "split_import", "module": module, "name": row["binding_name"]})
    return forms


def assert_unique(rows: list[dict[str, Any]]) -> None:
    ids: dict[str, list[Any]] = defaultdict(list)
    for row in rows:
        ids[row["candidate_id"]].append(row["span"])
    duplicates = {key: values for key, values in ids.items() if len(values) != 1}
    if duplicates:
        raise ScanError(f"SEAL-7: {duplicates}")
