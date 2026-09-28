"""Read-only OBS comparator. No scanners, subprocesses, or claim producers.

JSON AST: {op, args, source}; count also has cmp. Paths are strings; ref/file
and ctx are explicit operands. source is provenance, never an executable rule.
Only an independently supplied registry digest anchors subject/predicate integrity.
The candidate registry in this segment is NOT an approved frozen registry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

RENDERER_VERSION = "1"
EVIDENCE_PREFIX = "docs/clang-fix-campaign/dev_memory/stage14_p49_terminal_batch/a0-evidence/"
MISSING = object()
ARITIES = {
    "not": 1,
    "present": 1,
    "eq": 2,
    "ne": 2,
    "eq_path": 2,
    "in": 2,
    "matches": 2,
    "nonempty": 1,
    "count": 2,
    "count_eq": 2,
    "set_eq": 2,
    "subset": 2,
    "seq_eq": 2,
    "keys_eq": 2,
    "forall": 2,
    "exists": 2,
    "implies": 2,
    "sum_eq": 2,
    "in_path": 2,
    "schema_closed": 0,
}
EXPRESSIONS = {"union", "keys", "values", "$value", "$ref", "$file"}
LABELS = {
    "all": "所有条件成立",
    "any": "至少一项成立",
    "not": "条件取反",
    "present": "路径存在且非空值",
    "eq": "等于",
    "ne": "不等于",
    "eq_path": "两路径值相等",
    "in": "属于常量集合",
    "matches": "正则匹配",
    "nonempty": "集合或字符串非空",
    "count": "元素计数比较",
    "count_eq": "两处计数相等",
    "set_eq": "集合相等",
    "subset": "集合包含",
    "seq_eq": "序列相等",
    "keys_eq": "键集合相等",
    "forall": "逐元素全部满足",
    "exists": "存在满足的元素",
    "implies": "前件成立则后件成立",
    "sum_eq": "数值和相等",
    "in_path": "属于路径集合",
    "schema_closed": "按完整 schema 逐层封闭核对",
    "union": "集合并",
    "keys": "对象键数组",
    "values": "对象值数组",
    "$value": "读取标量",
    "$ref": "读取另一 claim 的事实",
    "$file": "读取独立产物的事实",
}


class PredicateError(ValueError):
    """Malformed registry or expression; never a false boolean operand."""


class EvaluationError(PredicateError):
    def __init__(self, node: dict[str, Any], path: str, message: str):
        self.node = node
        self.path = path
        super().__init__(f"{node.get('source')}: {path}: {message}")


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load_json(path: Path) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise PredicateError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def validate_schema(schema: Any) -> None:
    if isinstance(schema, str) and schema in {"str", "int", "bool"}:
        return
    if not isinstance(schema, dict):
        raise PredicateError("invalid schema")
    kind = schema.get("kind")
    keys = {
        "record": {"kind", "required", "optional"},
        "array": {"kind", "items"},
        "map": {"kind", "values"},
        "literal": {"kind", "value"},
        "union": {"kind", "tag", "variants"},
    }
    if kind not in keys or set(schema) != keys[kind]:
        raise PredicateError(f"invalid schema fields: {schema}")
    if kind == "record":
        required, optional = schema["required"], schema["optional"]
        if not isinstance(required, dict) or not isinstance(optional, dict):
            raise PredicateError("record fields must be objects")
        if required.keys() & optional.keys():
            raise PredicateError("required/optional overlap")
        for child in [*required.values(), *optional.values()]:
            validate_schema(child)
    elif kind in {"array", "map"}:
        validate_schema(schema["items" if kind == "array" else "values"])
    elif kind == "literal":
        if not isinstance(schema["value"], str):
            raise PredicateError("discriminator must be a string literal")
    else:
        tag, variants = schema["tag"], schema["variants"]
        if not isinstance(tag, str) or not isinstance(variants, dict) or not variants:
            raise PredicateError("union requires discriminator and variants")
        for value, branch in variants.items():
            validate_schema(branch)
            if not isinstance(branch, dict) or branch.get("kind") != "record":
                raise PredicateError("union branches must be records")
            if branch["required"].get(tag) != {
                "kind": "literal",
                "value": value,
            }:
                raise PredicateError("union branch discriminator mismatch")


def schema_matches(schema: Any, value: Any) -> bool:
    if isinstance(schema, str):
        return type(value) is {"str": str, "int": int, "bool": bool}[schema]
    kind = schema["kind"]
    if kind == "record":
        if not isinstance(value, dict):
            return False
        required, optional = schema["required"], schema["optional"]
        fields = {**required, **optional}
        return required.keys() <= value.keys() <= fields.keys() and all(
            schema_matches(fields[key], item) for key, item in value.items()
        )
    if kind == "array":
        return isinstance(value, list) and all(
            schema_matches(schema["items"], item) for item in value
        )
    if kind == "map":
        return isinstance(value, dict) and all(
            isinstance(key, str) and schema_matches(schema["values"], item)
            for key, item in value.items()
        )
    if kind == "literal":
        return bool(value == schema["value"])
    if not isinstance(value, dict):
        return False
    tag_value = value.get(schema["tag"])
    if not isinstance(tag_value, str) or tag_value not in schema["variants"]:
        return False
    return schema_matches(schema["variants"][tag_value], value)


def _path_syntax(path: Any) -> bool:
    return (
        isinstance(path, str)
        and (
            path == ""
            or path == "@"
            or path.startswith(("/", "@/"))
            or path in {"$ctx.tree", "$ctx.head", "$ctx.run_id"}
        )
        and not re.search(r"~(?![01])", path)
    )


def validate_node(node: Any, *, expression: bool = False) -> None:
    if not isinstance(node, dict) or not isinstance(node.get("source"), str):
        raise PredicateError("node requires source condition identifier")
    op, args = node.get("op"), node.get("args")
    expected = {"op", "args", "source"} | ({"cmp"} if op == "count" else set())
    if not node["source"] or set(node) != expected or not isinstance(args, list):
        raise PredicateError("invalid node fields")
    if expression:
        if op not in EXPRESSIONS:
            raise PredicateError("unknown argument expression")
        n = 2 if op in {"$ref", "$file"} else 1
        if (op == "union" and not args) or (op != "union" and len(args) != n):
            raise PredicateError("invalid expression arity")
    elif op in {"all", "any"}:
        if not args:
            raise PredicateError("empty predicate combination")
    elif op not in ARITIES or len(args) != ARITIES[op]:
        raise PredicateError("unknown node or invalid arity")
    if op == "count" and node["cmp"] not in {"==", ">=", "<="}:
        raise PredicateError("invalid count comparison")
    if op in {"all", "any", "not", "implies"}:
        for child in args:
            validate_node(child)
        return
    if op in {"forall", "exists"}:
        validate_node(args[1])
    literal_positions = {
        "eq": {1},
        "ne": {1},
        "in": {1},
        "matches": {1},
        "count": {1},
        "seq_eq": {1},
        "keys_eq": {1},
        "$ref": {0, 1},
        "$file": {0, 1},
    }.get(op, set())
    for index, arg in enumerate(args):
        if op in {"forall", "exists"} and index == 1:
            continue
        if isinstance(arg, dict):
            validate_node(arg, expression=True)
            if arg["op"] == "union" and op not in {"set_eq", "subset"}:
                raise PredicateError("union only allowed in set_eq/subset")
            if arg["op"] == "$value" and (op not in {"eq", "count"} or index != 1):
                raise PredicateError("$value only allowed on eq/count RHS")
            if index in literal_positions and arg["op"] != "$value":
                raise PredicateError("constant required")
        elif index in literal_positions:
            canonical(arg)
        elif isinstance(arg, list) and op in {"set_eq", "subset", "union"}:
            canonical(arg)
        elif not _path_syntax(arg):
            raise PredicateError(f"invalid operand: {arg!r}")
    if op in {"$ref", "$file"}:
        if not isinstance(args[0], str) or not args[0] or not _path_syntax(args[1]):
            raise PredicateError("invalid artifact reference")
    if op in {"in", "seq_eq", "keys_eq"} and not isinstance(args[1], list):
        raise PredicateError("constant array required")
    if op == "matches":
        if not isinstance(args[1], str):
            raise PredicateError("regex must be a string")
        try:
            re.compile(args[1])
        except re.error as exc:
            raise PredicateError("invalid regex") from exc
    if op == "count" and not isinstance(args[1], dict) and type(args[1]) is not int:
        raise PredicateError("count RHS must be integer")


def nodes(node: dict[str, Any]) -> Iterator[dict[str, Any]]:
    yield node
    for arg in node["args"]:
        if isinstance(arg, dict):
            yield from nodes(arg)


def validate_registry(registry: Any) -> None:
    if not isinstance(registry, list) or not registry:
        raise PredicateError("registry must be a nonempty list")
    seen: set[str] = set()
    for claim in registry:
        if not isinstance(claim, dict) or set(claim) != {
            "claim_id",
            "type",
            "subject",
            "quantifier",
            "output_schema",
            "predicate",
        }:
            raise PredicateError("invalid claim fields")
        for key in ("claim_id", "subject", "quantifier"):
            if not isinstance(claim[key], str) or not claim[key]:
                raise PredicateError(f"missing {key}")
        if claim["claim_id"] in seen or claim["type"] != "ASSERTION":
            raise PredicateError("duplicate claim or unapproved type")
        seen.add(claim["claim_id"])
        validate_schema(claim["output_schema"])
        validate_node(claim["predicate"])


def _pointer(value: Any, path: str) -> Any:
    if path == "":
        return value
    if not path.startswith("/") or re.search(r"~(?![01])", path):
        raise PredicateError(f"invalid JSON Pointer: {path}")
    parts = [part.replace("~1", "/").replace("~0", "~") for part in path[1:].split("/")]

    def walk(item: Any, rest: list[str]) -> Any:
        if not rest:
            return item
        key, tail = rest[0], rest[1:]
        if key == "*":
            if not isinstance(item, list):
                return MISSING
            result = []
            for element in item:
                child = walk(element, tail)
                if child is MISSING:
                    return MISSING
                if "*" in tail:
                    result.extend(child)
                else:
                    result.append(child)
            return result
        if isinstance(item, dict) and key in item:
            return walk(item[key], tail)
        if isinstance(item, list) and re.fullmatch(r"0|[1-9][0-9]*", key):
            index = int(key)
            if index < len(item):
                return walk(item[index], tail)
        return MISSING

    return walk(value, parts)


@dataclass
class Evaluator:
    output: Any
    schema: Any
    context: dict[str, str]
    claims: dict[str, Any] = field(default_factory=dict)
    files: dict[str, Any] = field(default_factory=dict)
    root: Path | None = None
    false_node: dict[str, Any] | None = None

    def _file(self, name: str) -> Any:
        expanded = EVIDENCE_PREFIX + name[2:] if name.startswith("E/") else name
        if expanded in self.files:
            return self.files[expanded]
        if name in self.files:
            return self.files[name]
        if self.root is None:
            return MISSING
        path = (self.root / expanded).resolve()
        if not path.is_relative_to(self.root.resolve()):
            raise PredicateError("artifact path escapes read-only root")
        if not path.is_file():
            return MISSING
        self.files[expanded] = load_json(path)
        return self.files[expanded]

    def value(
        self, expr: Any, current: Any, node: dict[str, Any], *, optional: bool = False
    ) -> Any:
        result: Any
        if isinstance(expr, dict):
            op, args = expr["op"], expr["args"]
            if op in {"$file", "$ref"}:
                source = self._file(args[0]) if op == "$file" else self.claims.get(args[0], MISSING)
                result = MISSING if source is MISSING else _pointer(source, args[1])
            elif op == "union":
                result = []
                for arg in args:
                    val = self.value(arg, current, expr)
                    if not isinstance(val, list):
                        raise EvaluationError(expr, repr(arg), "union requires arrays")
                    result.extend(val)
            else:
                val = self.value(args[0], current, expr)
                if op in {"keys", "values"}:
                    if not isinstance(val, dict):
                        raise EvaluationError(expr, repr(args[0]), "object required")
                    result = list(val.keys() if op == "keys" else val.values())
                elif op == "$value":
                    if isinstance(val, (dict, list)):
                        raise EvaluationError(expr, repr(args[0]), "scalar required")
                    result = val
                else:
                    raise PredicateError("unknown argument expression")
        elif isinstance(expr, list):
            result = expr
        elif expr.startswith("$ctx."):
            result = self.context.get(expr[5:], MISSING)
        elif expr.startswith("@"):
            result = _pointer(current, expr[1:])
        else:
            result = _pointer(self.output, expr)
        if result is MISSING and not optional:
            raise EvaluationError(node, repr(expr), "MISSING")
        return result

    def evaluate(self, node: dict[str, Any], current: Any = MISSING) -> bool:
        op, args = node["op"], node["args"]
        try:
            answer = self._evaluate(op, args, node, current)
        except EvaluationError:
            raise
        except (TypeError, ValueError, KeyError, OSError) as exc:
            raise EvaluationError(node, repr(args), str(exc)) from exc
        if not answer:
            self.false_node = node
        return answer

    def _evaluate(self, op: str, args: list[Any], node: dict[str, Any], current: Any) -> bool:
        if op == "all":
            return all(self.evaluate(child, current) for child in args)
        if op == "any":
            return any(self.evaluate(child, current) for child in args)
        if op == "not":
            return not self.evaluate(args[0], current)
        if op == "implies":
            return not self.evaluate(args[0], current) or self.evaluate(args[1], current)
        if op == "schema_closed":
            return schema_matches(self.schema, self.output)
        if op == "present":
            value = self.value(args[0], current, node, optional=True)
            return value is not MISSING and value is not None
        left = self.value(args[0], current, node)
        if op in {"forall", "exists"}:
            if not isinstance(left, list):
                raise PredicateError("quantifier requires array")
            checks = (self.evaluate(args[1], item) for item in left)
            return all(checks) if op == "forall" else any(checks)
        if op == "nonempty":
            if not isinstance(left, (str, list, dict)):
                raise PredicateError("nonempty requires array/object/string")
            return len(left) > 0
        right = args[1]
        if op in {"eq_path", "count_eq", "set_eq", "subset", "sum_eq", "in_path"} or (
            op in {"eq", "count"} and isinstance(right, dict)
        ):
            right = self.value(right, current, node)
        if op in {"eq", "eq_path", "ne"}:
            equal = canonical(left) == canonical(right)
            return not equal if op == "ne" else equal
        if op == "matches":
            if not isinstance(left, str):
                raise PredicateError("matches requires string")
            return re.search(right, left) is not None
        if op == "count":
            if not isinstance(left, (list, str, dict)) or type(right) is not int:
                raise PredicateError("count requires container and integer")
            return {"==": len(left) == right, ">=": len(left) >= right, "<=": len(left) <= right}[
                node["cmp"]
            ]
        if op == "count_eq":
            if not all(isinstance(val, (list, str, dict)) for val in (left, right)):
                raise PredicateError("count_eq requires containers")
            return len(left) == len(right)
        if op == "keys_eq":
            if not isinstance(left, dict):
                raise PredicateError("keys_eq requires object")
            left = list(left)
        if op in {"in", "in_path"}:
            if not isinstance(right, list):
                raise PredicateError("membership requires array")
            return canonical(left) in {canonical(item) for item in right}
        if op in {"set_eq", "subset", "keys_eq", "seq_eq"}:
            if not isinstance(left, list) or not isinstance(right, list):
                raise PredicateError("set/sequence operation requires arrays")
            if op == "seq_eq":
                return canonical(left) == canonical(right)
            a, b = {canonical(item) for item in left}, {canonical(item) for item in right}
            return a <= b if op == "subset" else a == b
        if op == "sum_eq":
            values = list(left.values()) if isinstance(left, dict) else left
            if not isinstance(values, list) or not all(
                type(val) in {int, float} for val in [*values, right]
            ):
                raise PredicateError("sum_eq requires numbers")
            return bool(sum(values) == right)
        raise PredicateError("unknown predicate")


def render(registry: list[dict[str, Any]]) -> str:
    validate_registry(registry)
    lines = [f"<!-- BEGIN GENERATED predicates renderer_version={RENDERER_VERSION} -->"]
    for claim in registry:
        lines.append(f"\n### {claim['claim_id']}\n")
        lines.append(f"对象: {claim['subject']};量词: {claim['quantifier']}。")
        for node in nodes(claim["predicate"]):
            args = [
                f"子节点({arg['op']})" if isinstance(arg, dict) else arg for arg in node["args"]
            ]
            detail = canonical(args).decode("utf-8")
            lines.append(
                f"- [{node['source']}] {LABELS[node['op']]}: {detail}"
                + (f";比较符 {node['cmp']}" if node["op"] == "count" else "")
            )
    lines.append("<!-- END GENERATED predicates -->\n")
    return "\n".join(lines)


def check_exemptions(
    claims: list[dict[str, Any]],
    exemptions: list[dict[str, Any]],
    *,
    defined_keys: set[str],
    decision_refs: set[str],
    references: list[dict[str, str]],
) -> None:
    """Compare supplied reference facts only; do not scan/produce reference facts."""
    by_id = {claim["claim_id"]: claim for claim in claims}
    seen: set[str] = set()
    for entry in exemptions:
        key = entry.get("claim_id")
        if not isinstance(key, str) or key not in defined_keys or re.search(r"[*?\[\]]", key):
            raise PredicateError("exemption requires literal defined key")
        if key in seen:
            raise PredicateError("duplicate exemption")
        seen.add(key)
        if not entry.get("reason") or not isinstance(entry["reason"], str):
            raise PredicateError("exemption requires reason")
        if key in decision_refs:
            raise PredicateError("exemption intersects decision references")
        if any(ref["claim_id"] == key and ref["use"] == "GATE" for ref in references):
            raise PredicateError("exemption has GATE reference")
        if key not in by_id or "predicate" in by_id[key]:
            raise PredicateError("exempt claim missing or contains predicate")
    for ref in references:
        if ref.get("use") not in {"GATE", "REPORT", "HUMAN"}:
            raise PredicateError("invalid reference use")
        if ref["claim_id"] not in by_id:
            raise PredicateError("undefined referenced claim")
    for claim in claims:
        kind = claim.get("type", "ASSERTION")
        if kind == "MEASUREMENT":
            if claim["claim_id"] not in seen:
                raise PredicateError("MEASUREMENT not exempted")
        elif kind == "ASSERTION":
            validate_node(claim.get("predicate"))
        else:
            raise PredicateError("unknown claim type")


def verify(
    registry: list[dict[str, Any]],
    outputs: dict[str, Any],
    *,
    context: dict[str, str],
    expected_hash: str,
    generated: str,
    files: dict[str, Any] | None = None,
    root: Path | None = None,
    measurement_exemptions: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    # This frozen batch permits no exemptions. Generic upper-bound comparisons
    # are tested separately, without synthesizing SEAL-16 reference facts.
    if measurement_exemptions:
        raise PredicateError("this batch freezes measurement_exemptions as []")
    validate_registry(registry)
    if canonical_hash(registry) != expected_hash:
        raise PredicateError("registry canonical hash differs from external anchor")
    if render(registry) != generated:
        raise PredicateError("renderer round-trip differs")
    if set(outputs) != {claim["claim_id"] for claim in registry}:
        raise PredicateError("claim output coverage differs")
    results = []
    for claim in registry:
        evaluator = Evaluator(
            outputs[claim["claim_id"]], claim["output_schema"], context, outputs, files or {}, root
        )
        result: dict[str, Any] = {"claim_id": claim["claim_id"]}
        try:
            ok = evaluator.evaluate(claim["predicate"])
            result.update(verdict="PASS" if ok else "FAIL")
            if not ok:
                result["node"] = evaluator.false_node
        except EvaluationError as exc:
            result.update(verdict="EVALUATION_ERROR", node=exc.node, path=exc.path, error=str(exc))
        results.append(result)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--outputs", type=Path)
    parser.add_argument("--context", type=Path)
    parser.add_argument("--expected-hash")
    parser.add_argument("--generated", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--exemptions", type=Path)
    args = parser.parse_args()
    try:
        registry = load_json(args.registry)
        validate_registry(registry)
        exemptions = load_json(
            args.exemptions or args.registry.with_name("measurement_exemptions.json")
        )
        if exemptions != []:
            raise PredicateError("this batch freezes measurement_exemptions as []")
        if args.render:
            print(render(registry), end="")
        elif args.outputs:
            if not args.context or not args.expected_hash or not args.generated:
                parser.error("verification requires context, external hash and generated block")
            results = verify(
                registry,
                load_json(args.outputs),
                context=load_json(args.context),
                expected_hash=args.expected_hash,
                generated=args.generated.read_text(encoding="utf-8"),
                root=args.root,
                measurement_exemptions=exemptions,
            )
            print(json.dumps(results, ensure_ascii=False, indent=2))
            return int(any(row["verdict"] != "PASS" for row in results))
        else:
            print(
                f"registry_valid claims={len(registry)} canonical_hash={canonical_hash(registry)}"
            )
        return 0
    except (PredicateError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
