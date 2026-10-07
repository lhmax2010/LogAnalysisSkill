"""E8-6 fixed-tree Python participant preflight, not the full consumer scanner.

No observed module is imported or executed. All Python entries are visited even
after a blocker. Name resolution retains lexical imports, local shadowing and
simple alias bindings; ambiguous bindings are recorded instead of selected.
This does not certify name-backstop, non-Python, candidate or OBS coverage.
"""

from __future__ import annotations

import argparse
import ast
import doctest
import importlib.machinery
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from terminal_scan import (
    HEAD,
    RULES,
    RULES_SHA,
    TREE,
    ModuleIndex,
    ScanError,
    contexts,
    fixed_inputs,
    sha256,
    write_atomic,
)

PROCESS = frozenset(
    "subprocess.run subprocess.call subprocess.check_call subprocess.check_output "
    "subprocess.getoutput subprocess.getstatusoutput subprocess.Popen os.system os.popen "
    "os.execl os.execle os.execlp os.execlpe os.execv os.execve os.execvp os.execvpe "
    "os.spawnl os.spawnle os.spawnlp os.spawnlpe os.spawnv os.spawnve os.spawnvp os.spawnvpe "
    "os.posix_spawn os.posix_spawnp pty.spawn asyncio.create_subprocess_exec "
    "asyncio.create_subprocess_shell".split()
)
PATCH = frozenset(
    "unittest.mock.patch unittest.mock.patch.object unittest.mock.patch.dict "
    "unittest.mock.patch.multiple monkeypatch.setattr monkeypatch.delattr".split()
)
UTIL = frozenset(
    "importlib.util.find_spec importlib.util.spec_from_file_location "
    "importlib.util.spec_from_loader importlib.util.module_from_spec "
    "importlib.util.resolve_name".split()
)
BUILTINS = frozenset(
    {"__import__", "exec", "eval", "compile", "getattr", "hasattr", "setattr", "delattr"}
)


def monitored(name: str, modules: set[str]) -> bool:
    if name in modules:
        return False
    return (
        name in {"builtins.__import__", "builtins.exec", "builtins.eval"}
        or name.startswith(("importlib.", "runpy.", "pkgutil.", "imp.", "zipimport."))
        or name in PATCH | PROCESS
        or any(
            name.startswith("os." + prefix)
            for prefix in ("system", "popen", "exec", "spawn", "posix_spawn")
        )
    )


@dataclass
class Scope:
    parent: Scope | None
    kind: str
    definitions: dict[str, list[ast.AST | str | None]] = field(default_factory=dict)
    globals: set[str] = field(default_factory=set)
    nonlocals: set[str] = field(default_factory=set)

    def bind(self, name: str, value: ast.AST | str | None) -> None:
        self.definitions.setdefault(name, []).append(value)

    def owner(self, name: str) -> Scope | None:
        if name in self.globals and self.parent:
            scope = self
            while scope.parent:
                scope = scope.parent
            return scope
        if name in self.definitions and name not in self.nonlocals:
            return self
        parent = self.parent
        while parent and parent.kind == "class" and self.kind != "class":
            parent = parent.parent
        return parent.owner(name) if parent else None


class Bindings(ast.NodeVisitor):
    def __init__(self, tree: ast.Module, module_name: str, package: bool) -> None:
        self.scope = Scope(None, "module")
        self.module = module_name
        self.package = package
        self.scopes: dict[ast.AST, Scope] = {}
        self.function_scopes: dict[ast.AST, Scope] = {}
        self.modules = {
            "builtins",
            "importlib",
            "importlib.util",
            "runpy",
            "pkgutil",
            "imp",
            "zipimport",
            "sys",
            "os",
            "subprocess",
            "unittest",
            "unittest.mock",
            "pytest",
            "asyncio",
            "pty",
        }
        self.visit(tree)

    def visit(self, node: ast.AST) -> None:
        self.scopes[node] = self.scope
        super().visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.scopes[alias] = self.scope
            local = alias.asname or alias.name.split(".")[0]
            self.scope.bind(local, alias.name if alias.asname else local)
            self.modules.update(
                ".".join(alias.name.split(".")[:i])
                for i in range(1, len(alias.name.split(".")) + 1)
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        source = node.module or ""
        if node.level:
            parts = self.module.split(".") if self.package else self.module.split(".")[:-1]
            prefix = parts[: len(parts) - node.level + 1]
            source = ".".join([*prefix, *([source] if source else [])])
        for alias in node.names:
            self.scopes[alias] = self.scope
            self.scope.bind(alias.asname or alias.name, source + "." + alias.name)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.scope.bind(node.id, None)

    def visit_Global(self, node: ast.Global) -> None:
        self.scope.globals.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.scope.nonlocals.update(node.names)

    def target(self, node: ast.expr, value: ast.expr | None) -> None:
        self.scopes[node] = self.scope
        if isinstance(node, ast.Name):
            self.scope.bind(node.id, value)
        else:
            self.visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        for target in node.targets:
            self.target(target, node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.visit(node.annotation)
        if node.value:
            self.visit(node.value)
        self.target(node.target, node.value)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self.visit(node.value)
        self.target(node.target, node.value)

    def visit_With(self, node: ast.With | ast.AsyncWith) -> None:
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars:
                self.target(item.optional_vars, item.context_expr)
        for statement in node.body:
            self.visit(statement)

    visit_AsyncWith = visit_With

    def function(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda) -> None:
        if not isinstance(node, ast.Lambda):
            self.scope.bind(node.name, node)
            for decorator in node.decorator_list:
                self.visit(decorator)
            if node.returns:
                self.visit(node.returns)
        args = node.args
        params = [*args.posonlyargs, *args.args, *args.kwonlyargs]
        params += [p for p in (args.vararg, args.kwarg) if p]
        for param in params:
            if param.annotation:
                self.visit(param.annotation)
        for default in [*args.defaults, *args.kw_defaults]:
            if default:
                self.visit(default)
        outer = self.scope
        self.scope = Scope(outer, "function")
        self.function_scopes[node] = self.scope
        for param in params:
            self.scope.bind(param.arg, "monkeypatch" if param.arg == "monkeypatch" else None)
        body = [node.body] if isinstance(node, ast.Lambda) else node.body
        for statement in body:
            self.visit(statement)
        self.scope = outer

    visit_FunctionDef = function
    visit_AsyncFunctionDef = function
    visit_Lambda = function

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.bind(node.name, None)
        for expr in [*node.bases, *node.decorator_list, *node.keywords]:
            self.visit(expr)
        outer = self.scope
        self.scope = Scope(outer, "class")
        for statement in node.body:
            self.visit(statement)
        self.scope = outer

    def comprehension_scope(
        self, node: ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp
    ) -> None:
        outer = self.scope
        self.visit(node.generators[0].iter)
        self.scope = Scope(outer, "function")
        for index, generator in enumerate(node.generators):
            if index:
                self.visit(generator.iter)
            self.visit(generator.target)
            for condition in generator.ifs:
                self.visit(condition)
        if isinstance(node, ast.DictComp):
            self.visit(node.key)
            self.visit(node.value)
        else:
            self.visit(node.elt)
        self.scope = outer

    visit_ListComp = comprehension_scope
    visit_SetComp = comprehension_scope
    visit_GeneratorExp = comprehension_scope
    visit_DictComp = comprehension_scope

    def resolve(self, node: ast.AST, seen: frozenset[tuple[int, str]] = frozenset()) -> set[str]:
        if isinstance(node, ast.Name):
            owner = self.scopes[node].owner(node.id)
            if owner is None:
                return {"builtins." + node.id} if node.id in BUILTINS else set()
            key = (id(owner), node.id)
            if key in seen:
                return set()
            result = set()
            for definition in owner.definitions.get(node.id, []):
                if isinstance(definition, str):
                    result.add(definition)
                elif isinstance(definition, ast.AST):
                    result.update(self.resolve(definition, seen | {key}))
            return result
        if isinstance(node, ast.Attribute):
            result = set()
            for base in self.resolve(node.value, seen):
                if base == "@source-spec" and node.attr == "loader":
                    result.add("@source-loader")
                elif base == "@source-loader":
                    # Stdlib metadata only; never instantiate/execute an observed loader.
                    if callable(getattr(importlib.machinery.SourceFileLoader, node.attr, None)):
                        result.add("importlib.machinery.SourceFileLoader." + node.attr)
                elif not base.startswith("@"):
                    result.add(base + "." + node.attr)
            return result
        if isinstance(node, ast.Call):
            names = self.resolve(node.func, seen)
            if "pytest.MonkeyPatch" in names or "pytest.MonkeyPatch.context" in names:
                return {"monkeypatch"}
            if "importlib.util.spec_from_file_location" in names:
                location = argument(node, 1, "location")
                loader = next((kw for kw in node.keywords if kw.arg == "loader"), None)
                if loader is None and self.source_location(location, seen):
                    return {"@source-spec"}
            if (
                "importlib.import_module" in names
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                name = node.args[0].value
                self.modules.add(name)
                return {name}
        return set()

    def source_location(self, node: ast.AST | None, seen: frozenset[tuple[int, str]]) -> bool:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value.endswith(tuple(importlib.machinery.SOURCE_SUFFIXES))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return self.source_location(node.right, seen)
        if isinstance(node, ast.Call) and self.resolve(node.func, seen) == {"pathlib.Path"}:
            return bool(node.args) and self.source_location(node.args[0], seen)
        if isinstance(node, ast.Name):
            owner = self.scopes[node].owner(node.id)
            if owner and (id(owner), node.id) not in seen:
                definitions = owner.definitions[node.id]
                return bool(definitions) and all(
                    isinstance(value, ast.AST)
                    and self.source_location(value, seen | {(id(owner), node.id)})
                    for value in definitions
                )
        return False


def literal(node: ast.AST | None) -> Any:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


def argument(call: ast.Call, position: int, *keys: str) -> ast.expr | None:
    if len(call.args) > position and not isinstance(call.args[position], ast.Starred):
        return call.args[position]
    return next((kw.value for kw in call.keywords if kw.arg in keys), None)


def python_mode(argv: Any) -> tuple[str | None, str | None]:
    """E7 preflight only needs static interpreter mode; unknown stays C8b unresolved."""
    if not isinstance(argv, (list, tuple)) or not argv or not isinstance(argv[0], str):
        return None, None
    if not re.fullmatch(r"python[0-9.]*", Path(argv[0]).name):
        return None, None
    words = iter(argv[1:])
    for word in words:
        if not isinstance(word, str):
            return None, None
        if word == "-":
            return "stdin", None
        if word == "--":
            return "script", next(words, None)
        if not word.startswith("-"):
            return "script", word
        if word.startswith("--"):
            option, _, value = word.partition("=")
            if option == "--check-hash-based-pycs":
                if not value and next(words, None) is None:
                    return None, None
            elif option not in {"--help", "--version"}:
                return None, None
            continue
        for index, char in enumerate(word[1:], 1):
            if char in "bBdEh iIOPqRsSuvVx?".replace(" ", ""):
                continue
            if char in "WXcm":
                operand = word[index + 1 :] or next(words, None)
                if not isinstance(operand, str):
                    return None, None
                if char in "cm":
                    return char, operand
                break
            return None, None
    return "stdin", None


def call_forms(name: str, node: ast.Call, bindings: Bindings) -> list[str]:
    first = argument(node, 0, "name", "target", "source", "object")
    is_string = isinstance(first, ast.Constant) and isinstance(first.value, str)
    forms = []
    if name == "importlib.import_module":
        forms.append("C2a" if is_string else "C2b")
    if name in {"monkeypatch.setattr", "monkeypatch.delattr"}:
        forms.append("C3" if is_string else "C6a")
    if name in {"unittest.mock.patch", "unittest.mock.patch.dict", "unittest.mock.patch.multiple"}:
        forms.append("C3")
    if name == "unittest.mock.patch.object":
        forms.append("C6b")
    if name == "builtins.__import__":
        forms.append("C5b")
    if name == "runpy.run_module":
        forms.append("C5c")
    if name in UTIL:
        forms.append("C5d")
    if name in {"builtins.exec", "builtins.eval"}:
        forms.append("C9")
    if name in PROCESS:
        mode, _ = python_mode(literal(argument(node, 0, "args", "cmd", "command", "argv")))
        forms.append("C8a" if mode == "m" else "C8b")
    if name in {"builtins.setattr", "builtins.delattr", "builtins.getattr", "builtins.hasattr"}:
        if first is not None and bindings.resolve(first) & bindings.modules:
            forms.append("C6c" if name in {"builtins.setattr", "builtins.delattr"} else "C6d")
    return forms


def inspect_source(
    source: str,
    path: str,
    context: str,
    module: str = "",
    package: bool = False,
    origin: str = "file",
    offset: int = 0,
    prepared: Any = None,
    alias_result: Any = None,
) -> dict[str, Any]:
    from terminal_alias_preflight import AliasWorld, Unit, annotation_nodes

    try:
        unit = prepared or Unit(source, path, context, module, package)
        tree = unit.tree
    except SyntaxError as exc:
        return {
            "participants": [],
            "excluded_compile": [],
            "alias_bindings": [],
            "dynamic_unresolved": [],
            "excluded_annotations": [],
            "parse_errors": [
                {
                    "path": path,
                    "context": context,
                    "origin": origin,
                    "line": (exc.lineno or 1) + offset,
                    "error": str(exc),
                }
            ],
        }
    if alias_result is None:
        world = AliasWorld([unit])
        world.run()
        alias_result = world.result(path)
    bindings = unit.bindings
    annotations = annotation_nodes(tree)
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    result: dict[str, Any] = {
        "participants": [],
        "excluded_compile": [],
        "parse_errors": [],
        "alias_bindings": alias_result["alias_bindings"],
        "dynamic_unresolved": alias_result["dynamic_unresolved"],
        "excluded_annotations": [],
    }
    handled: set[ast.AST] = set()

    def add(node: ast.AST, kind: str, name: str, forms: list[str], reason: str) -> None:
        result["participants"].append(
            {
                "path": path,
                "context": context,
                "origin": origin,
                "line": getattr(node, "lineno", 1) + offset,
                "column": getattr(node, "col_offset", 0),
                "qualified_name": name,
                "kind": kind,
                "forms": forms,
                "match_count": len(forms),
                "reason": reason if len(forms) != 1 else "exactly one form",
                "source": ast.get_source_segment(source, node),
            }
        )

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                form = "C5a" if isinstance(node, ast.ImportFrom) and node.level else "C1"
                if isinstance(node, ast.Import) and alias.asname:
                    form = "C4"
                add(alias, "IMPORT_ALIAS", alias.name, [form], "")
        if isinstance(node, ast.Call):
            for name in sorted(bindings.resolve(node.func)):
                if name == "builtins.compile":
                    result["excluded_compile"].append(
                        {
                            "path": path,
                            "line": node.lineno + offset,
                            "kind": "CALL",
                            "context": context,
                        }
                    )
                forms = call_forms(name, node, bindings)
                if monitored(name, bindings.modules) or forms:
                    add(node, "CALL", name, forms, "monitored callable outside closed callee sets")
                if name.startswith("sys.modules."):
                    forms = (
                        ["C5e"]
                        if name in {"sys.modules.get", "sys.modules.pop", "sys.modules.setdefault"}
                        else []
                    )
                    add(
                        node,
                        "SYS_MODULES_CALL",
                        name,
                        forms,
                        "sys.modules method outside C5e closed set",
                    )
                    handled.add(node.func)
            handled.add(node.func)
        if isinstance(node, ast.Subscript) and "sys.modules" in bindings.resolve(node.value):
            add(node, "SYS_MODULES_SUBSCRIPT", "sys.modules", ["C5e"], "")
            handled.add(node.value)
        if isinstance(node, ast.Compare):
            for operator, operand in zip(node.ops, node.comparators, strict=True):
                if isinstance(operator, (ast.In, ast.NotIn)) and "sys.modules" in bindings.resolve(
                    operand
                ):
                    add(node, "SYS_MODULES_COMPARE", "sys.modules", ["C5e"], "")
                    handled.add(operand)

    for node in ast.walk(tree):
        if (
            not isinstance(node, (ast.Name, ast.Attribute))
            or not isinstance(node.ctx, ast.Load)
            or node in handled
        ):
            continue
        parent = parents.get(node)
        if isinstance(parent, ast.Attribute) and parent.value is node:
            continue
        for name in sorted(bindings.resolve(node)):
            if node in annotations and monitored(name, bindings.modules):
                result["excluded_annotations"].append(
                    {
                        "path": path,
                        "context": context,
                        "line": node.lineno + offset,
                        "column": node.col_offset,
                        "name": name,
                        "rule": "E8-1",
                    }
                )
                continue
            if name == "builtins.compile":
                result["excluded_compile"].append(
                    {"path": path, "line": node.lineno + offset, "kind": "READ", "context": context}
                )
            if monitored(name, bindings.modules):
                add(
                    node,
                    "NON_CALL_READ",
                    name,
                    [],
                    "section 1.1 participant 2-prime: no form accepts monitored non-call read",
                )
            elif name.startswith("sys.modules."):
                add(
                    node,
                    "SYS_MODULES_ATTRIBUTE",
                    name,
                    [],
                    "attribute access outside C5e callable/subscript/comparison forms",
                )

    # E8 replaces the old read/call classification at exactly the measured AST site.
    for row in alias_result["participants"]:
        kind = "CALL" if row["kind"] == "ALIAS_CALL" else row["kind"]
        result["participants"] = [
            p
            for p in result["participants"]
            if not (
                p["line"] == row["line"] + offset
                and p["column"] == row["column"]
                and p["kind"] == kind
            )
        ]
        result["participants"].append({**row, "line": row["line"] + offset, "origin": origin})

    # Only executable string sources, not arbitrary code-looking fixture strings.
    embedded: list[tuple[str, str, int]] = []
    for row in alias_result["participants"]:
        payload = row.get("payload", {})
        if payload.get("code_source") in {"c", "stdin"} and isinstance(payload.get("payload"), str):
            embedded.append(
                (payload["payload"], f"{origin}:alias-code@{row['line']}", row["line"] - 1)
            )
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                expr = node.body[0]
                try:
                    examples = doctest.DocTestParser().get_examples(doc)
                    if examples:
                        lines: list[str] = []
                        for example in examples:
                            lines.extend([""] * (example.lineno - len(lines)))
                            lines.extend(example.source.splitlines())
                        embedded.append(
                            (
                                "\n".join(lines),
                                f"{origin}:doctest@{expr.lineno}",
                                expr.lineno - 1,
                            )
                        )
                except ValueError as exc:
                    result["parse_errors"].append(
                        {
                            "path": path,
                            "context": context,
                            "origin": origin,
                            "line": expr.lineno + offset,
                            "error": str(exc),
                        }
                    )
        if isinstance(node, ast.Call):
            if any(
                row["kind"] == "ALIAS_CALL"
                and (row["line"], row["column"]) == (node.lineno, node.col_offset)
                for row in alias_result["participants"]
            ):
                continue
            names = bindings.resolve(node.func)
            payload = literal(argument(node, 0, "source"))
            if names & {"builtins.exec", "builtins.eval"} and isinstance(payload, str):
                embedded.append((payload, f"{origin}:C9@{node.lineno}", node.lineno - 1))
            if names & PROCESS:
                mode, payload = python_mode(
                    literal(argument(node, 0, "args", "cmd", "command", "argv"))
                )
                if mode == "c" and payload is not None:
                    embedded.append((payload, f"{origin}:-c@{node.lineno}", node.lineno - 1))
                stdin = literal(next((kw.value for kw in node.keywords if kw.arg == "input"), None))
                if isinstance(stdin, str):
                    embedded.append((stdin, f"{origin}:input@{node.lineno}", node.lineno - 1))
    for payload, label, line in embedded:
        nested = inspect_source(payload, path, context, module, package, label, offset + line)
        for key in result:
            result[key].extend(nested[key])
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for point in result["participants"]:
        point_key = (point["origin"], point["line"], point["column"], point["kind"])
        grouped.setdefault(point_key, []).append(point)
    result["participants"] = []
    for group in grouped.values():
        point = dict(group[0])
        point["qualified_names"] = sorted({p["qualified_name"] for p in group})
        point["qualified_name"] = " | ".join(point["qualified_names"])
        if any(not p["forms"] for p in group):
            point["forms"] = []
            point["reason"] = next(p["reason"] for p in group if not p["forms"])
        else:
            point["forms"] = sorted({form for p in group for form in p["forms"]})
        point["match_count"] = len(point["forms"])
        if point["match_count"] > 1:
            point["reason"] = (
                "multiple forms across unresolved lexical bindings; no binding selected"
            )
        result["participants"].append(point)
    return result


def main() -> int:
    from terminal_alias_preflight import AliasWorld, Unit

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--rules-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest, files = fixed_inputs(args.root, args.rules_root)
    rules = (args.rules_root / RULES).read_text()
    forms = re.findall(r"^(?:> )?\| `(C[0-9]+[a-z]?)` \|", rules, re.MULTILINE)
    if len(forms) != 24 or len(set(forms)) != 24 or not {"C9", "C8c", "C5f", "C7e"} <= set(forms):
        raise ScanError("E8_ATOMIC_TABLE_PARSE")
    index = ModuleIndex(files, contexts(files))
    all_results: dict[str, list[Any]] = {
        "participants": [],
        "excluded_compile": [],
        "parse_errors": [],
        "alias_bindings": [],
        "dynamic_unresolved": [],
        "excluded_annotations": [],
    }
    units = []
    for entry in manifest["entries"]:
        if entry["entry_kind"] != "PY_SOURCE":
            continue
        path = entry["path"]
        names = index.by_path.get(path, [])
        module = names[0][1] if len(names) == 1 else ""
        try:
            units.append(
                Unit(
                    files[path].decode(),
                    path,
                    entry["context"],
                    module,
                    path.endswith("/__init__.py"),
                )
            )
        except SyntaxError:
            pass  # inspect_source records every parse error below, without aborting other files.
    world = AliasWorld(units, index)
    world.run()
    entries = []
    for entry in manifest["entries"]:
        if entry["entry_kind"] != "PY_SOURCE":
            continue
        path = entry["path"]
        names = index.by_path.get(path, [])
        module = names[0][1] if len(names) == 1 else ""
        measured = inspect_source(
            files[path].decode(),
            path,
            entry["context"],
            module,
            path.endswith("/__init__.py"),
            prepared=world.units.get(path),
            alias_result=world.result(path) if path in world.units else None,
        )
        entries.append(
            {
                **entry,
                "participants": len(measured["participants"]),
                "parse_errors": len(measured["parse_errors"]),
            }
        )
        for key in all_results:
            all_results[key].extend(measured[key])
    points = sorted(
        all_results["participants"],
        key=lambda p: (p["path"], p["line"], p["column"], p["origin"], p["kind"]),
    )
    zero = [p for p in points if p["match_count"] == 0]
    multi = [p for p in points if p["match_count"] > 1]
    summary = {
        "tracked_entries": len(manifest["entries"]),
        "contexts": dict(Counter(e["context"] for e in manifest["entries"])),
        "python_entries": len(entries),
        "python_contexts": dict(Counter(e["context"] for e in entries)),
        "participants": len(points),
        "zero_matches": len(zero),
        "multiple_matches": len(multi),
        "parse_errors": len(all_results["parse_errors"]),
        "excluded_compile": len(all_results["excluded_compile"]),
        "excluded_annotations": len(all_results["excluded_annotations"]),
        "alias_bindings": len(all_results["alias_bindings"]),
        "alias_calls": sum(p["kind"] == "ALIAS_CALL" for p in points),
        "fixed_point_rounds": world.fixed_point_rounds,
        "dynamic_unresolved": {
            category: sum(r["category"] == category for r in all_results["dynamic_unresolved"])
            for category in ("C8c_ESCAPE", "ALIAS_PAYLOAD", "C5f")
        },
    }
    result = {
        "head": HEAD,
        "tree": TREE,
        "rules_sha256": RULES_SHA,
        "tool_sha256": sha256(Path(__file__).read_bytes()),
        "scope": "E8-6 Python preflight only; no full scan completion or OBS",
        "summary": summary,
        "entries": entries,
        "participants": points,
        "zero_matches": zero,
        "multiple_matches": multi,
        "parse_errors": all_results["parse_errors"],
        "excluded_compile": all_results["excluded_compile"],
        "alias_bindings": all_results["alias_bindings"],
        "dynamic_unresolved": all_results["dynamic_unresolved"],
        "excluded_annotations": all_results["excluded_annotations"],
        "module_resolution_events": index.events,
        "module_identity_ambiguities": [
            e for e in index.events if e["kind"] == "MODULE_IDENTITY_AMBIGUOUS"
        ],
    }
    write_atomic(args.output, result)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    for point in zero + multi:
        print(
            f"{point['path']}:{point['line']}:{point['column']} | {point['context']} | "
            f"{point['qualified_name']} | matches={point['match_count']} | {point['reason']}"
        )
    for error in all_results["parse_errors"]:
        print("PARSE_ERROR " + json.dumps(error, ensure_ascii=False))
    print(
        "PREFLIGHT="
        + (
            "BLOCKED"
            if zero or multi or all_results["parse_errors"] or result["module_identity_ambiguities"]
            else "ZERO_BLOCKERS"
        )
    )
    return int(
        bool(zero or multi or all_results["parse_errors"] or result["module_identity_ambiguities"])
    )


if __name__ == "__main__":
    raise SystemExit(main())
