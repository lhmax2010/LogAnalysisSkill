"""Artificial data only: no OBS producers, repository scans, or real injections."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "docs/clang-fix-campaign/tools/terminal_predicates.py"
SPEC = importlib.util.spec_from_file_location("terminal_predicates_for_test", TOOL)
assert SPEC is not None and SPEC.loader is not None
P = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = P
SPEC.loader.exec_module(P)
DATA = ROOT / "docs/clang-fix-campaign/tools/p49_terminal_data"
REGISTRY = P.load_json(DATA / "predicates.json")
FIXTURE = P.load_json(ROOT / "tests/fixtures/p49_terminal_predicates/synthetic.json")
HASH = P.canonical_hash(REGISTRY)
RENDERED = P.render(REGISTRY)
BY_ID = {claim["claim_id"]: claim for claim in REGISTRY}


def n(op: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    return {"op": op, "args": list(args), "source": "SYNTHETIC-CONTROL", **kwargs}


def check(
    registry: Any = None,
    outputs: Any = None,
    generated: str = RENDERED,
) -> list[dict[str, Any]]:
    return cast(
        list[dict[str, Any]],
        P.verify(
            REGISTRY if registry is None else registry,
            FIXTURE["outputs"] if outputs is None else outputs,
            context=FIXTURE["context"],
            files=FIXTURE["files"],
            expected_hash=HASH,
            generated=generated,
        ),
    )


def evaluate(node: dict[str, Any], output: Any = None, schema: Any = None) -> bool:
    P.validate_node(node)
    engine = P.Evaluator(
        {"x": 1, "y": 2, "xs": [1, 2], "text": "abc", "obj": {"a": 1, "b": 2}}
        if output is None
        else output,
        "int" if schema is None else schema,
        {"tree": "synthetic-tree", "head": "synthetic-head", "run_id": "synthetic-run"},
        claims={"synthetic": {"x": 1}},
        files={"synthetic.json": {"x": 1}},
    )
    return cast(bool, engine.evaluate(node))


NODE_PAIRS = [
    ("all", n("all", n("eq", "/x", 1)), n("all", n("eq", "/x", 0))),
    ("any", n("any", n("eq", "/x", 1)), n("any", n("eq", "/x", 0))),
    ("not", n("not", n("eq", "/x", 0)), n("not", n("eq", "/x", 1))),
    ("present", n("present", "/x"), n("present", "/missing")),
    ("eq", n("eq", "/x", 1), n("eq", "/x", 2)),
    ("ne", n("ne", "/x", 2), n("ne", "/x", 1)),
    ("eq_path", n("eq_path", "/x", "/x"), n("eq_path", "/x", "/y")),
    ("in", n("in", "/x", [1, 2]), n("in", "/x", [2])),
    ("matches", n("matches", "/text", "bc$"), n("matches", "/text", "^bc$")),
    ("nonempty", n("nonempty", "/xs"), n("nonempty", "/empty")),
    ("count", n("count", "/xs", 2, cmp="=="), n("count", "/xs", 1, cmp="==")),
    ("count_eq", n("count_eq", "/xs", "/obj"), n("count_eq", "/xs", "/text")),
    ("set_eq", n("set_eq", "/xs", [2, 1, 1]), n("set_eq", "/xs", [1])),
    ("subset", n("subset", [1], "/xs"), n("subset", [3], "/xs")),
    ("seq_eq", n("seq_eq", "/xs", [1, 2]), n("seq_eq", "/xs", [2, 1])),
    ("keys_eq", n("keys_eq", "/obj", ["b", "a"]), n("keys_eq", "/obj", ["a"])),
    ("forall", n("forall", "/xs", n("in", "@", [1, 2])), n("forall", "/xs", n("eq", "@", 1))),
    ("exists", n("exists", "/xs", n("eq", "@", 2)), n("exists", "/xs", n("eq", "@", 3))),
    (
        "implies",
        n("implies", n("eq", "/x", 0), n("eq", "/missing", 0)),
        n("implies", n("eq", "/x", 1), n("eq", "/y", 0)),
    ),
    ("sum_eq", n("sum_eq", "/obj", "/total"), n("sum_eq", "/obj", "/y")),
    ("in_path", n("in_path", "/x", "/xs"), n("in_path", "/text", "/xs")),
    ("union", n("set_eq", n("union", [1], [2]), "/xs"), n("set_eq", n("union", [1], [3]), "/xs")),
    ("keys", n("set_eq", n("keys", "/obj"), ["a", "b"]), n("set_eq", n("keys", "/obj"), ["a"])),
    ("values", n("set_eq", n("values", "/obj"), [1, 2]), n("set_eq", n("values", "/obj"), [1])),
    ("$value", n("eq", "/x", n("$value", "/x")), n("eq", "/x", n("$value", "/y"))),
    (
        "$ref",
        n("eq_path", "/x", n("$ref", "synthetic", "/x")),
        n("eq_path", "/y", n("$ref", "synthetic", "/x")),
    ),
    (
        "$file",
        n("eq_path", "/x", n("$file", "synthetic.json", "/x")),
        n("eq_path", "/y", n("$file", "synthetic.json", "/x")),
    ),
    ("schema_closed", n("schema_closed"), n("schema_closed")),
]


@pytest.mark.parametrize("name,positive,negative", NODE_PAIRS, ids=[x[0] for x in NODE_PAIRS])
def test_each_node_positive_negative(name: str, positive: Any, negative: Any) -> None:
    output = {
        "x": 1,
        "y": 2,
        "xs": [1, 2],
        "text": "abc",
        "obj": {"a": 1, "b": 2},
        "empty": [],
        "total": 3,
    }
    if name == "schema_closed":
        assert evaluate(positive, 1, "int")
        assert not evaluate(negative, True, "int")
    else:
        assert evaluate(positive, output)
        assert not evaluate(negative, output)


def test_node_catalog_covers_closed_language() -> None:
    assert {x[0] for x in NODE_PAIRS} == set(P.ARITIES) | {"all", "any"} | P.EXPRESSIONS


def test_registry_source_condition_coverage() -> None:
    source = (ROOT / "docs/clang-fix-campaign/p49-terminal-obs-predicates-v1.2.md").read_text()
    blocks = re.split(r"(?=^### B-\d)", source, flags=re.M)[1:]
    assert len(blocks) == len(REGISTRY)
    for block, claim in zip(blocks, REGISTRY, strict=True):
        block = block.split("\n---")[0]
        match = re.search(r"`(OBS-[^`]+)`", block)
        assert match is not None
        cid = match[1]
        assert claim["claim_id"] == cid
        numbers = re.findall(r"^  (\d+)\. ", block, re.M)
        expected = ["G1", "G2", "G3", "G4"] + [f"{cid}#{i}" for i in numbers]
        conditions = claim["predicate"]["args"]
        assert [node["source"] for node in conditions] == expected
        for node in conditions:
            assert {child["source"] for child in P.nodes(node)} == {node["source"]}
    assert P.load_json(DATA / "measurement_exemptions.json") == []


def test_all_artificial_claims_positive() -> None:
    assert all(row["verdict"] == "PASS" for row in check())


@pytest.mark.parametrize("claim_id", list(BY_ID))
def test_claim_fact_mutation_red(claim_id: str) -> None:
    outputs = copy.deepcopy(FIXTURE["outputs"])
    mutation = FIXTURE["mutations"][claim_id]
    parent = outputs[claim_id]
    parts = mutation["path"][1:].split("/")
    for part in parts[:-1]:
        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
    key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
    parent[key] = mutation["value"]
    assert (
        next(row for row in check(outputs=outputs) if row["claim_id"] == claim_id)["verdict"]
        != "PASS"
    )


@pytest.mark.parametrize("control", ["flip", "subject", "snapshot", "roundtrip"])
def test_assertion_four_controls(control: str) -> None:
    registry = copy.deepcopy(REGISTRY)
    if control == "flip":
        registry[0]["predicate"] = n("not", registry[0]["predicate"])
    elif control == "subject":
        registry[0]["subject"], registry[1]["subject"] = (
            registry[1]["subject"],
            registry[0]["subject"],
        )
    elif control == "snapshot":
        outputs = copy.deepcopy(FIXTURE["outputs"])
        outputs[REGISTRY[0]["claim_id"]]["snapshot"] = "old-tree"
        assert check(outputs=outputs)[0]["verdict"] == "FAIL"
        return
    with pytest.raises(P.PredicateError, match="canonical hash|round-trip"):
        check(registry, generated=RENDERED + "tampered" if control == "roundtrip" else RENDERED)


@pytest.mark.parametrize("control", ["empty", "parse", "unreasoned-exemption"])
def test_type_three_controls(control: str) -> None:
    registry = copy.deepcopy(REGISTRY)
    if control == "unreasoned-exemption":
        with pytest.raises(P.PredicateError, match="requires reason"):
            P.check_exemptions(
                registry,
                [{"claim_id": registry[0]["claim_id"]}],
                defined_keys=set(BY_ID),
                decision_refs=set(),
                references=[],
            )
        return
    registry[0]["predicate"] = {} if control == "empty" else n("unknown-node")
    with pytest.raises(P.PredicateError):
        P.validate_registry(registry)


@pytest.mark.parametrize("control", ["wildcard", "decision", "gate", "predicate"])
def test_exemption_four_controls(control: str) -> None:
    cid = "OBS-SYNTHETIC.measurement"
    claim: dict[str, Any] = {"claim_id": cid, "type": "MEASUREMENT"}
    exemption = {"claim_id": cid, "reason": "synthetic manual input"}
    refs, decisions = [], set()
    if control == "wildcard":
        exemption["claim_id"] = "OBS-*"
    elif control == "decision":
        decisions.add(cid)
    elif control == "gate":
        refs.append({"claim_id": cid, "use": "GATE"})
    else:
        claim["predicate"] = n("schema_closed")
    expected = {
        "wildcard": "literal",
        "decision": "decision",
        "gate": "GATE",
        "predicate": "contains predicate",
    }[control]
    with pytest.raises(P.PredicateError, match=expected):
        P.check_exemptions(
            [claim], [exemption], defined_keys={cid}, decision_refs=decisions, references=refs
        )


@pytest.mark.parametrize("case", ["required", "extra", "error", "short-circuit", "empty"])
def test_evaluation_five_controls(case: str) -> None:
    schema = {"kind": "record", "required": {"x": "int"}, "optional": {"maybe": "int"}}
    if case == "required":
        assert not evaluate(n("schema_closed"), {}, schema)
    elif case == "extra":
        assert not evaluate(n("schema_closed"), {"x": 1, "extra": 0}, schema)
    elif case == "error":
        missing = n("eq", "/maybe", 1)
        for node in [
            n("not", missing),
            n("any", missing, n("eq", "/x", 1)),
            n("implies", n("eq", "/x", 1), missing),
        ]:
            with pytest.raises(P.EvaluationError, match="MISSING") as exc:
                evaluate(node, {"x": 1}, schema)
            assert exc.value.path == "'/maybe'"
            assert exc.value.node == missing
    elif case == "short-circuit":
        for node in [
            n("any", n("eq", "/x", 1), n("eq", "/maybe", 1)),
            n("implies", n("eq", "/x", 0), n("eq", "/maybe", 1)),
        ]:
            assert evaluate(node, {"x": 1}, schema)
        assert not evaluate(n("all", n("eq", "/x", 0), n("eq", "/maybe", 1)))
    else:
        assert evaluate(n("forall", "/xs", n("eq", "@", 1)), {"xs": []})
        assert not evaluate(n("exists", "/xs", n("eq", "@", 1)), {"xs": []})


ITEM3_INPUTS = [
    ("dangling-absent", 0, {"state": "ABSENT"}, True),
    ("dangling-source", 0, {"state": "VALUE", "value": "SOURCE_DIR_UNSAFE"}, False),
    ("dangling-missing-value", 0, {"state": "VALUE"}, False),
    ("dangling-other", 0, {"state": "VALUE", "value": "OTHER"}, True),
    ("live-old-counterexample", 1, {"state": "ABSENT", "value": "SOURCE_DIR_UNSAFE"}, False),
    ("live-value", 1, {"state": "VALUE", "value": "SOURCE_DIR_UNSAFE"}, True),
    ("live-absent", 1, {"state": "ABSENT"}, False),
]


@pytest.mark.parametrize("name,index,code,green", ITEM3_INPUTS, ids=[x[0] for x in ITEM3_INPUTS])
def test_item3_all_inputs(name: str, index: int, code: Any, green: bool) -> None:
    cid = "OBS-1.item3-predicate"
    outputs = copy.deepcopy(FIXTURE["outputs"])
    outputs[cid]["scenarios"][index]["exception_code"] = code
    result = next(row for row in check(outputs=outputs) if row["claim_id"] == cid)
    assert (result["verdict"] == "PASS") is green


@pytest.mark.parametrize("group", ["evidence", "map", "optional", "nested"])
def test_schema_four_groups(group: str) -> None:
    if group == "evidence":
        schema = REGISTRY[0]["output_schema"]["required"]["evidence"]
        good = FIXTURE["outputs"][REGISTRY[0]["claim_id"]]["evidence"]
        for element in good:
            assert P.schema_matches(schema, [element])
        third = {"kind": "OTHER"}
        no_exit = {key: value for key, value in good[0].items() if key != "exit_code"}
        extra = {**good[1], "command": "not-permitted"}
        for element in [third, no_exit, extra]:
            assert not P.schema_matches(schema, [element])
    elif group == "map":
        schema = {"kind": "map", "values": "int"}
        assert P.schema_matches(schema, {})
        assert P.schema_matches(schema, {"arbitrary-key": 1})
        assert not P.schema_matches(schema, {"a": "1"})
    elif group == "optional":
        schema = {"kind": "record", "required": {"x": "int"}, "optional": {"a": "bool"}}
        assert P.schema_matches(schema, {"x": 1})
        assert not P.schema_matches(schema, {"x": 1, "a": 0})
    else:
        cid = "OBS-1.item1-basis"
        output = copy.deepcopy(FIXTURE["outputs"][cid])
        output["entries"][0]["extra"] = "not-permitted"
        assert not P.schema_matches(BY_ID[cid]["output_schema"], output)


def test_missing_option_is_red_for_entire_claim_not_just_low_level() -> None:
    registry = copy.deepcopy(REGISTRY)
    c = registry[2]
    c["predicate"] = n("not", n("eq", "/scenarios/2/exception_type", "none"))
    result = P.verify(
        registry,
        FIXTURE["outputs"],
        context=FIXTURE["context"],
        files=FIXTURE["files"],
        expected_hash=P.canonical_hash(registry),
        generated=P.render(registry),
    )
    assert result[2]["verdict"] == "EVALUATION_ERROR"
    assert result[2]["path"] == "'/scenarios/2/exception_type'"


def test_json_pointer_arrays_missing_elements_and_scope_restoration() -> None:
    assert evaluate(n("eq", "/a~1b/~0", 2), {"a/b": {"~": 2}})
    assert evaluate(
        n("seq_eq", "/xs/*/ys/*", [1, 2, 3]), {"xs": [{"ys": [1, 2]}, {"ys": []}, {"ys": [3]}]}
    )
    with pytest.raises(P.EvaluationError, match="MISSING"):
        evaluate(n("set_eq", "/xs/*/x", [1]), {"xs": [{"x": 1}, {}]})
    assert evaluate(
        n("forall", "/xs", n("all", n("exists", "@/ys", n("eq", "@", 2)), n("eq", "@/x", 1))),
        {"xs": [{"x": 1, "ys": [2]}]},
    )


@pytest.mark.parametrize(
    "node",
    [
        n("all"),
        n("unknown"),
        n("not"),
        n("eq", "/x", 1, additional=True),
        n("eq", "/x", n("union", [1], [2])),
        n("ne", "/x", n("$value", "/y")),
        n("count", "/x", 1, cmp="!="),
        n("matches", "/x", "["),
        n("present", "bad-pointer"),
        n("present", "/bad~2escape"),
        n("seq_eq", "/xs", 1),
    ],
)
def test_malformed_ast_fails_closed_even_in_skipped_branch(node: Any) -> None:
    with pytest.raises(P.PredicateError):
        P.validate_node(n("any", n("eq", "/x", 1), node))


def test_canonical_and_renderer_are_deterministic_and_separate() -> None:
    assert P.canonical({"b": "中", "a": 1}) == '{"a":1,"b":"中"}'.encode()
    assert P.canonical_hash({"a": 1, "b": 2}) == P.canonical_hash({"b": 2, "a": 1})
    assert P.canonical_hash([1, 2]) != P.canonical_hash([2, 1])
    assert P.render(REGISTRY) == RENDERED
    assert f"renderer_version={P.RENDERER_VERSION}" in RENDERED
    assert "renderer_version" not in P.canonical(REGISTRY).decode()
    assert len([line for line in RENDERED.splitlines() if line.startswith("- [")]) == sum(
        len(list(P.nodes(claim["predicate"]))) for claim in REGISTRY
    )


def test_json_loader_rejects_duplicate_keys_and_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "fixture.json"
    path.write_text('{"x":1,"x":2}')
    with pytest.raises(P.PredicateError, match="duplicate"):
        P.load_json(path)
    path.write_text('{"x":')
    with pytest.raises(json.JSONDecodeError):
        P.load_json(path)


def test_file_operands_are_read_only_and_confined(tmp_path: Path) -> None:
    path = tmp_path / "artifact.json"
    path.write_text('{"value":1}')
    before = path.read_bytes()
    engine = P.Evaluator({"x": 1}, "int", {}, root=tmp_path)
    assert engine.evaluate(n("eq_path", "/x", n("$file", "artifact.json", "/value")))
    assert path.read_bytes() == before
    for name in ("../outside.json", "missing.json"):
        with pytest.raises(P.EvaluationError):
            engine.evaluate(n("eq_path", "/x", n("$file", name, "/value")))


def test_unregistered_output_and_unknown_schema_fail_closed() -> None:
    with pytest.raises(P.PredicateError, match="coverage"):
        check(outputs={})
    with pytest.raises(P.PredicateError):
        P.validate_schema({"kind": "open-record"})
    registry = copy.deepcopy(REGISTRY)
    registry[0]["output_schema"]["additionalProperties"] = True
    with pytest.raises(P.PredicateError):
        P.validate_registry(registry)


def test_union_requires_records_and_unique_discriminator() -> None:
    for variants in [{"a": "str"}, {"a": {"kind": "record", "required": {}, "optional": {}}}]:
        with pytest.raises(P.PredicateError):
            P.validate_schema({"kind": "union", "tag": "state", "variants": variants})


def test_renderer_upgrade_does_not_change_predicate_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(P, "RENDERER_VERSION", "synthetic-upgrade")
    assert P.canonical_hash(REGISTRY) == HASH
    assert P.render(REGISTRY) != RENDERED
    with pytest.raises(P.PredicateError, match="round-trip"):
        check()


def test_count_comparators_and_value_rhs() -> None:
    assert evaluate(n("count", "/xs", 2, cmp=">="))
    assert not evaluate(n("count", "/xs", 3, cmp=">="))
    assert evaluate(n("count", "/xs", 2, cmp="<="))
    assert not evaluate(n("count", "/xs", 1, cmp="<="))
    assert evaluate(n("count", "/xs", n("$value", "/y"), cmp="=="))
    assert not evaluate(n("count", "/xs", n("$value", "/x"), cmp="=="))


def test_empty_exemption_list_is_enforced_at_batch_boundary() -> None:
    with pytest.raises(P.PredicateError, match="freezes measurement_exemptions"):
        P.verify(
            REGISTRY,
            FIXTURE["outputs"],
            context=FIXTURE["context"],
            files=FIXTURE["files"],
            expected_hash=HASH,
            generated=RENDERED,
            measurement_exemptions=[{"claim_id": REGISTRY[0]["claim_id"]}],
        )
    P.check_exemptions(REGISTRY, [], defined_keys=set(BY_ID), decision_refs=set(), references=[])


def test_missing_reference_cannot_be_negated_to_green() -> None:
    for expr in [n("$ref", "unregistered", "/x"), n("$file", "missing.json", "/x")]:
        with pytest.raises(P.EvaluationError, match="MISSING"):
            evaluate(n("not", n("eq_path", "/x", expr)))


def test_approved_frozen_hashes() -> None:
    P.check_frozen_hashes(REGISTRY, [])
    assert HASH == P.FROZEN_PREDICATES_HASH
    assert P.canonical_hash([]) == P.FROZEN_EXEMPTIONS_HASH


@pytest.mark.parametrize("target", ["registry", "exemptions"])
def test_frozen_file_tampering_is_rejected(target: str) -> None:
    registry, exemptions = copy.deepcopy(REGISTRY), []
    if target == "registry":
        registry[0]["subject"] += " changed"
    else:
        exemptions.append({"claim_id": REGISTRY[0]["claim_id"]})
    with pytest.raises(P.PredicateError, match="FROZEN_HASH_MISMATCH"):
        P.check_frozen_hashes(registry, exemptions)


def test_cli_cannot_override_freeze_pin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    registry = copy.deepcopy(REGISTRY)
    registry[0]["subject"] += " changed"
    path = tmp_path / "predicates.json"
    path.write_bytes(P.canonical(registry))
    path.with_name("measurement_exemptions.json").write_text("[]")
    monkeypatch.setattr(
        sys, "argv", [str(TOOL), str(path), "--expected-hash", P.canonical_hash(registry)]
    )
    assert P.main() == 1
