"""E8 lexical fixed point. Reads AST only; never executes observed modules.

Bindings retain all process origins, without control-flow or fake-runner pruning.
This is participant preflight, not consumer-set closure or an OBS producer.
"""

from __future__ import annotations

import ast
import shlex
from dataclasses import dataclass, field
from typing import Any

from terminal_monitored_preflight import PROCESS, Bindings, Scope, argument, literal, python_mode
from terminal_scan import ModuleIndex


def annotation_nodes(tree: ast.AST) -> set[ast.AST]:
    result: set[ast.AST] = set()
    for node in ast.walk(tree):
        value = None
        if isinstance(node, (ast.arg, ast.AnnAssign)):
            value = node.annotation
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            value = node.returns
        if value is not None:
            result.update(ast.walk(value))
    return result


@dataclass
class Unit:
    source: str
    path: str
    context: str
    module: str = ""
    package: bool = False
    tree: ast.Module = field(init=False)
    bindings: Bindings = field(init=False)
    parents: dict[ast.AST, ast.AST] = field(init=False)
    annotations: set[ast.AST] = field(init=False)

    def __post_init__(self) -> None:
        self.tree = ast.parse(self.source, filename=self.path)
        self.bindings = Bindings(self.tree, self.module, self.package)
        self.parents = {c: p for p in ast.walk(self.tree) for c in ast.iter_child_nodes(p)}
        self.annotations = annotation_nodes(self.tree)

    def point(self, node: ast.AST) -> dict[str, Any]:
        return {
            "path": self.path,
            "context": self.context,
            "line": getattr(node, "lineno", 1),
            "column": getattr(node, "col_offset", 0),
            "source": ast.get_source_segment(self.source, node),
        }


def payload_family(name: str) -> tuple[str, int, tuple[str, ...]]:
    if name in {
        "subprocess.getoutput",
        "subprocess.getstatusoutput",
        "os.system",
        "os.popen",
        "asyncio.create_subprocess_shell",
    }:
        return "string", 0, ("cmd", "command")
    if name.startswith("os.execl"):
        return "varargs-env" if name.endswith("e") else "varargs", 1, ()
    if name.startswith("os.spawnl"):
        return "varargs-env" if name.endswith("e") else "varargs", 2, ()
    if name.startswith("os.execv"):
        return "vector", 1, ("args",)
    if name.startswith("os.spawnv"):
        return "vector", 2, ("args",)
    if name.startswith("os.posix_spawn"):
        return "vector", 1, ("argv",)
    if name == "pty.spawn":
        return "vector", 0, ("argv",)
    if name == "asyncio.create_subprocess_exec":
        return "varargs", 0, ()
    return "vector", 0, ("args",)


def static_value(unit: Unit, node: ast.AST | None, seen: frozenset[int] = frozenset()) -> Any:
    if node is None or id(node) in seen:
        return None
    if unit.bindings.resolve(node) == {"sys.executable"}:
        return "python"
    if isinstance(node, (ast.List, ast.Tuple)):
        values = [static_value(unit, n, seen) for n in node.elts]
        return values if all(isinstance(v, str) for v in values) else None
    if isinstance(node, ast.Name):
        owner = unit.bindings.scopes[node].owner(node.id)
        definitions = owner.definitions[node.id] if owner else []
        if len(definitions) == 1 and isinstance(definitions[0], ast.AST):
            return static_value(unit, definitions[0], seen | {id(node)})
    return literal(node)


def process_payload(unit: Unit, call: ast.Call, names: set[str]) -> dict[str, Any]:
    families = {payload_family(n) for n in names}
    if len(families) != 1:
        return {"form": "C8b", "reason": "aliases have different command payload signatures"}
    kind, pos, keys = families.pop()
    if any(k.arg is None for k in call.keywords) or any(
        isinstance(a, ast.Starred) for a in call.args
    ):
        return {"form": "C8b", "reason": "command binding contains unpacking"}
    if kind.startswith("varargs"):
        nodes = call.args[pos : -1 if kind == "varargs-env" else None]
        argv = [static_value(unit, n) for n in nodes]
    else:
        argv = static_value(unit, argument(call, pos, *keys))
    if kind == "string" or any(
        k.arg == "shell" and literal(k.value) is True for k in call.keywords
    ):
        if not isinstance(argv, str) or any(token in argv for token in ("$", "`", "%{")):
            return {"form": "C8b", "reason": "command string is not statically normalizable"}
        try:
            argv = shlex.split(argv)
        except ValueError:
            return {"form": "C8b", "reason": "command string cannot be tokenized"}
    if not isinstance(argv, (list, tuple)) or not argv or not all(isinstance(v, str) for v in argv):
        return {"form": "C8b", "reason": "argv is not statically normalizable"}
    mode, payload = python_mode(argv)
    result: dict[str, Any] = {
        "form": "C8a" if mode == "m" else "C8b",
        "argv": argv,
        "code_source": mode,
        "payload": payload,
    }
    if mode == "stdin":
        stdin = next((k.value for k in call.keywords if k.arg == "input"), None)
        if not isinstance(stdin, ast.Constant) or not isinstance(stdin.value, str):
            result["reason"] = "interpreter stdin payload is not a literal input string"
        else:
            result.update(code_source="stdin", payload=stdin.value)
    elif mode is None and argv[0].rsplit("/", 1)[-1].startswith("python"):
        result["reason"] = "interpreter options cannot be normalized"
    return result


class AliasWorld:
    def __init__(self, units: list[Unit], index: ModuleIndex | None = None):
        self.units = {u.path: u for u in units}
        self.index = index
        self.aliases: dict[tuple[str, int, str], set[tuple[str, int, int, str]]] = {}
        self.scope_by_key: dict[tuple[str, int, str], Scope] = {}
        self.origin_points: dict[tuple[str, int, int, str], dict[str, Any]] = {}
        self.reads: dict[tuple[str, int, int], dict[str, Any]] = {}
        self.rows: dict[str, list[dict[str, Any]]] = {u.path: [] for u in units}
        self.dynamic: list[dict[str, Any]] = []
        self.excluded: list[dict[str, Any]] = []
        self.fixed_point_rounds = 0

    def key(self, unit: Unit, scope: Scope, name: str) -> tuple[str, int, str]:
        key = unit.path, id(scope), name
        self.scope_by_key[key] = scope
        return key

    def resolve_def(
        self, unit: Unit, node: ast.AST, seen: frozenset[tuple[str, int, str]] = frozenset()
    ) -> list[tuple[Unit, ast.AST]]:
        values: list[tuple[Unit, ast.AST]] = []
        if isinstance(node, ast.Name):
            scope = unit.bindings.scopes[node].owner(node.id)
            if scope:
                key = (unit.path, id(scope), node.id)
                if key in seen:
                    return []
                for value in scope.definitions[node.id]:
                    if isinstance(value, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        values.append((unit, value))
                    elif isinstance(value, ast.AST):
                        values.extend(self.resolve_def(unit, value, seen | {key}))
                    elif isinstance(value, str):
                        values.extend(self.qualified_def(unit, value, seen | {key}))
        else:
            for name in unit.bindings.resolve(node):
                values.extend(self.qualified_def(unit, name, seen))
        return list({(u.path, id(n)): (u, n) for u, n in values}.values())

    def qualified_def(
        self, unit: Unit, name: str, seen: frozenset[tuple[str, int, str]]
    ) -> list[tuple[Unit, ast.AST]]:
        module, _, attr = name.rpartition(".")
        if not module:
            return []
        if self.index:
            event = self.index.resolve(unit.context, module, unit.path)
            if event["kind"] in {"MODULE_IDENTITY_AMBIGUOUS", "NON_CANDIDATE_NAME"}:
                return []
            matches = [self.units[t["path"]] for t in event["targets"] if t["path"] in self.units]
        else:
            matches = [
                u for u in self.units.values() if (u.context, u.module) == (unit.context, module)
            ]
        if len(matches) != 1:
            return []
        target = matches[0]
        scope = target.bindings.scopes[target.tree]
        key = (target.path, id(scope), attr)
        if key in seen:
            return []
        result: list[tuple[Unit, ast.AST]] = []
        for value in scope.definitions.get(attr, []):
            if isinstance(value, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result.append((target, value))
            elif isinstance(value, str):
                result.extend(self.qualified_def(target, value, seen | {key}))
            elif isinstance(value, ast.AST):
                result.extend(self.resolve_def(target, value, seen | {key}))
        return result

    def destination(self, unit: Unit, node: ast.AST) -> tuple[list[tuple[str, int, str]], str]:
        parent = unit.parents.get(node)
        if isinstance(parent, (ast.Assign, ast.AnnAssign, ast.NamedExpr)) and parent.value is node:
            targets = parent.targets if isinstance(parent, ast.Assign) else [parent.target]
            if len(targets) == 1 and isinstance(targets[0], ast.Name):
                target = targets[0]
                scope = unit.bindings.scopes[target].owner(target.id)
                if scope:
                    return [self.key(unit, scope, target.id)], "assignment"
            return [], "assignment is not to one plain name"
        for func, scope in unit.bindings.function_scopes.items():
            if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            args = func.args
            positional = [*args.posonlyargs, *args.args]
            defaults: list[tuple[ast.arg, ast.expr | None]] = list(
                zip(positional[len(positional) - len(args.defaults) :], args.defaults, strict=True)
            )
            defaults += list(zip(args.kwonlyargs, args.kw_defaults, strict=True))
            for parameter, value in defaults:
                if value is node:
                    return [self.key(unit, scope, parameter.arg)], "parameter default"
        call = unit.parents.get(parent) if isinstance(parent, ast.keyword) else parent
        if not isinstance(call, ast.Call) or (
            not isinstance(parent, ast.keyword) and node not in call.args
        ):
            return (
                [],
                "value escapes closed destinations (attribute/container/return/unpacking/lambda)",
            )
        definitions = self.resolve_def(unit, call.func)
        if len(definitions) != 1:
            return [], "callee does not resolve uniquely to a scanned def"
        target_unit, definition = definitions[0]
        assert isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef))
        args = definition.args
        if isinstance(parent, ast.keyword):
            params = [p for p in [*args.args, *args.kwonlyargs] if p.arg == parent.arg]
        else:
            assert isinstance(node, ast.expr)
            position = call.args.index(node)
            if any(isinstance(n, ast.Starred) for n in call.args[: position + 1]):
                return [], "positional binding contains unpacking"
            params = [*args.posonlyargs, *args.args][position : position + 1]
        if len(params) != 1:
            return [], "argument binds to variadic or unknown parameter"
        return [
            self.key(target_unit, target_unit.bindings.function_scopes[definition], params[0].arg)
        ], "call argument"

    def sources(self, unit: Unit, node: ast.AST) -> set[tuple[str, int, int, str]]:
        result = set()
        if isinstance(node, ast.Name):
            scope = unit.bindings.scopes[node].owner(node.id)
            if scope:
                result.update(self.aliases.get(self.key(unit, scope, node.id), set()))
        return result

    def run(self) -> None:
        # Roots are actual monitored reads; later rounds propagate only recorded bindings.
        roots: list[tuple[Unit, ast.expr, set[tuple[str, int, int, str]]]] = []
        for unit in self.units.values():
            for node in ast.walk(unit.tree):
                if not isinstance(node, (ast.Name, ast.Attribute)) or not isinstance(
                    node.ctx, ast.Load
                ):
                    continue
                parent = unit.parents.get(node)
                if isinstance(parent, ast.Call) and parent.func is node:
                    continue
                if isinstance(parent, ast.Attribute) and parent.value is node:
                    continue
                names = unit.bindings.resolve(node) & PROCESS
                if not names:
                    continue
                if node in unit.annotations:
                    self.excluded.append(
                        {**unit.point(node), "names": sorted(names), "rule": "E8-1"}
                    )
                    continue
                # Simple aliases are propagated from their original read, not invented anew.
                scope = (
                    unit.bindings.scopes[node].owner(node.id)
                    if isinstance(node, ast.Name)
                    else None
                )
                if (
                    scope
                    and isinstance(node, ast.Name)
                    and any(isinstance(v, ast.AST) for v in scope.definitions[node.id])
                ):
                    continue
                origins = {(unit.path, node.lineno, node.col_offset, n) for n in names}
                for origin in origins:
                    self.origin_points[origin] = {**unit.point(node), "qualified_name": origin[-1]}
                roots.append((unit, node, origins))
        changed = True
        while changed:
            before = sum(len(v) for v in self.aliases.values())
            pending = list(roots)
            for unit in self.units.values():
                for node in ast.walk(unit.tree):
                    if (
                        isinstance(node, ast.Name)
                        and isinstance(node.ctx, ast.Load)
                        and node not in unit.annotations
                    ):
                        parent = unit.parents.get(node)
                        if isinstance(parent, ast.Call) and parent.func is node:
                            continue
                        origins = self.sources(unit, node)
                        if origins:
                            pending.append((unit, node, origins))
            for unit, node, origins in pending:
                destinations, reason = self.destination(unit, node)
                key = unit.path, node.lineno, node.col_offset
                row = self.reads.setdefault(
                    key,
                    {
                        "unit": unit,
                        "node": node,
                        "origins": set(),
                        "destinations": destinations,
                        "reason": reason,
                    },
                )
                row["origins"].update(origins)
                for destination in destinations:
                    self.aliases.setdefault(destination, set()).update(origins)
            changed = sum(len(v) for v in self.aliases.values()) != before
            self.fixed_point_rounds += 1
        self.finish()

    def participant(
        self, unit: Unit, node: ast.AST, kind: str, names: list[str], form: str, **extra: Any
    ) -> dict[str, Any]:
        return {
            **unit.point(node),
            "origin": "file",
            "kind": kind,
            "qualified_names": names,
            "qualified_name": " | ".join(names),
            "forms": [form],
            "match_count": 1,
            "reason": "exactly one form",
            **extra,
        }

    def finish(self) -> None:
        for read in self.reads.values():
            unit, node, origins = read["unit"], read["node"], read["origins"]
            row = self.participant(
                unit,
                node,
                "NON_CALL_READ",
                sorted({o[-1] for o in origins}),
                "C8c",
                source_reads=[self.origin_points[o] for o in sorted(origins)],
                destination_reason=read["reason"],
            )
            self.rows[unit.path].append(row)
            if not read["destinations"]:
                self.dynamic.append(
                    {
                        **row,
                        "category": "C8c_ESCAPE",
                        "detail": read["reason"],
                        "status": "DYNAMIC_UNRESOLVED",
                    }
                )
        self.binding_evidence: list[dict[str, Any]] = []
        for key, origins in self.aliases.items():
            path, _, name = key
            unit = self.units[path]
            scope = self.scope_by_key[key]
            enclosing = next(
                (n for n, s in unit.bindings.function_scopes.items() if s is scope), unit.tree
            )
            calls = []
            for node in ast.walk(unit.tree):
                if (
                    not isinstance(node, ast.Call)
                    or not isinstance(node.func, ast.Name)
                    or node.func.id != name
                ):
                    continue
                if unit.bindings.scopes[node.func].owner(name) is not scope:
                    continue
                names = {o[-1] for o in origins}
                payload = process_payload(unit, node, names)
                row = self.participant(
                    unit,
                    node,
                    "ALIAS_CALL",
                    sorted(names),
                    payload["form"],
                    source_reads=[self.origin_points[o] for o in sorted(origins)],
                    payload=payload,
                )
                self.rows[path].append(row)
                calls.append(unit.point(node))
                if "reason" in payload:
                    self.dynamic.append(
                        {
                            **row,
                            "category": "ALIAS_PAYLOAD",
                            "detail": payload["reason"],
                            "status": "DYNAMIC_UNRESOLVED",
                        }
                    )
            self.binding_evidence.append(
                {
                    "binding": {
                        "path": path,
                        "context": unit.context,
                        "scope": getattr(enclosing, "name", "<module>"),
                        "scope_line": getattr(enclosing, "lineno", 1),
                        "name": name,
                    },
                    "source_reads": [self.origin_points[o] for o in sorted(origins)],
                    "calls": calls,
                }
            )
        for unit in self.units.values():
            for node in ast.walk(unit.tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                if node.func.attr not in {"exec_module", "load_module"}:
                    continue
                receiver = node.func.value
                link = None
                if (
                    isinstance(receiver, ast.Attribute)
                    and receiver.attr == "loader"
                    and isinstance(receiver.value, ast.Name)
                ):
                    scope = unit.bindings.scopes[node]
                    owner = scope.owner(receiver.value.id)
                    values = owner.definitions[receiver.value.id] if owner else []
                    if owner is scope and len(values) == 1 and isinstance(values[0], ast.Call):
                        value = values[0]
                        if unit.bindings.resolve(value.func) & {
                            "importlib.util.spec_from_file_location",
                            "importlib.util.spec_from_loader",
                            "importlib.util.find_spec",
                        }:
                            link = unit.point(value)
                row = self.participant(
                    unit, node, "CALL", [ast.unparse(node.func)], "C5f", c5d_link=link
                )
                self.rows[unit.path].append(row)
                if link is None:
                    self.dynamic.append(
                        {
                            **row,
                            "category": "C5f",
                            "status": "DYNAMIC_UNRESOLVED",
                            "detail": "loader receiver lacks a unique same-scope C5d assignment",
                        }
                    )

    def result(self, path: str) -> dict[str, Any]:
        return {
            "participants": self.rows[path],
            "alias_bindings": [r for r in self.binding_evidence if r["binding"]["path"] == path],
            "dynamic_unresolved": [r for r in self.dynamic if r["path"] == path],
            "excluded_annotations": [r for r in self.excluded if r["path"] == path],
        }
