"""Artificial gate objects only; no production collector or OBS producer runs."""

from __future__ import annotations

import copy
import importlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "docs/clang-fix-campaign/tools"
saved = sys.path[:]
sys.path.insert(0, str(TOOLS))
try:
    G = importlib.import_module("terminal_expected_diff")
    C = importlib.import_module("terminal_diff_controls")
    B = importlib.import_module("build_terminal_diff_data")
finally:
    sys.path[:] = saved


@pytest.fixture
def gate() -> Any:
    return G.load_gate(ROOT)


def test_data_generation_is_reproducible_and_closed(gate: Any) -> None:
    manifest, schema, expected = B.derive(ROOT)
    assert (manifest, schema, expected) == (gate.manifest, gate.schema, gate.expected)
    assert len(manifest["scenarios"]) == 4 + 6 * 4 + 2
    assert len(gate.validate()) == len(manifest["scenarios"])
    assert B.source_report(manifest, expected) == (G.DATA / "expected_diff_sources.md").read_text()


@pytest.mark.parametrize("control", C.CONTROLS)
def test_artificial_admission_control(gate: Any, control: str) -> None:
    if control == "normal":
        C.run_control(gate, control)
    else:
        with pytest.raises(G.GateError):
            C.run_control(gate, control)


def test_no_diff_positive_and_negative_do_not_need_fake_registered_scenario() -> None:
    entry = {"mode": "NO_DIFF", "reason": "人工不经过新签名的无变化对照"}
    G.compare_one({"field": {"deep": [1, True]}}, {"field": {"deep": [1, True]}}, entry, {})
    with pytest.raises(G.GateError, match="DIFF_PATHS"):
        G.compare_one({"field": 1}, {"field": True}, entry, {})
    with pytest.raises(G.GateError, match="EMPTY_REASON"):
        G.check_mode({"mode": "NO_DIFF", "reason": ""})


def test_registered_but_impossible_difference_cannot_pass_exact_set_comparison() -> None:
    entry = {
        "mode": "DIFF_SET",
        "differences": {"/field": {"old": {}, "new": {}, "reason": "人工登记一项不会发生的变化"}},
    }
    with pytest.raises(G.GateError, match="missing=.*field"):
        G.compare_one(
            {"field": 1}, {"field": 1}, entry, {"/field": {"old": G.value(1), "new": G.value(2)}}
        )


@pytest.mark.parametrize(
    "field",
    [
        "return_value",
        "exception_type",
        "exception_code",
        "exception_message",
        "warnings",
        "action",
        "calls",
        "destination",
        "worktree",
        "workdir_marker",
        "protected_marker",
        "exclude_completed",
        "exit_code",
    ],
)
def test_every_result_field_is_required(gate: Any, field: str) -> None:
    before, after = C.artificial_pair(gate)
    del before["REAL_DIR"][field]
    with pytest.raises(G.GateError, match="CLOSED_FIELDS"):
        gate.compare(before, after, C.ARTIFICIAL_READERS)


@pytest.mark.parametrize("path", ["extra", "calls", "marker", "reader"])
def test_undeclared_fields_are_rejected(gate: Any, path: str) -> None:
    before, after = C.artificial_pair(gate)
    obj = after["REAL_DIR"]
    target = {
        "extra": obj,
        "calls": obj["calls"][0]["kwargs"],
        "marker": obj["protected_marker"],
        "reader": obj["protected_marker"]["readers"][0],
    }[path]
    target["not_in_schema"] = True
    with pytest.raises(G.GateError, match="CLOSED_FIELDS"):
        gate.compare(before, after, C.ARTIFICIAL_READERS)


@pytest.mark.parametrize("replacement", [[], None, ["wrong-reader"], C.ARTIFICIAL_READERS * 2])
def test_runtime_readers_must_be_nonempty_unique_and_exact(gate: Any, replacement: Any) -> None:
    before, after = C.artificial_pair(gate)
    with pytest.raises(G.GateError):
        gate.compare(before, after, replacement)


def test_reader_results_may_not_be_omitted_or_changed(gate: Any) -> None:
    before, after = C.artificial_pair(gate)
    after["REAL_DIR"]["protected_marker"]["readers"] = []
    with pytest.raises(G.GateError, match="READERS_EMPTY_OR_MISSING"):
        gate.compare(before, after, C.ARTIFICIAL_READERS)
    before, after = C.artificial_pair(gate)
    after["REAL_DIR"]["protected_marker"]["readers"][0]["return_value"] = G.value(True)
    with pytest.raises(G.GateError, match="DIFF_PATHS"):
        gate.compare(before, after, C.ARTIFICIAL_READERS)


def test_partial_marker_hashes_and_reader_exceptions_are_compared(gate: Any) -> None:
    before, after = C.artificial_pair(gate)
    sid = "MARKER_WRITE_INTERRUPTED"
    for frame in (before, after):
        marker = frame[sid]["protected_marker"]
        marker.update(exists=True, sha256=G.value("a" * 64))
        marker["readers"][0].update(
            return_value=G.ABSENT,
            exception_type=G.value("JSONDecodeError"),
            exception_message=G.value("partial bytes"),
        )
    gate.compare(before, after, C.ARTIFICIAL_READERS)
    after[sid]["protected_marker"]["sha256"] = G.value("b" * 64)
    with pytest.raises(G.GateError, match="DIFF_PATHS"):
        gate.compare(before, after, C.ARTIFICIAL_READERS)


@pytest.mark.parametrize("sid", ["DANGLING_SYMLINK", "surface1-timeout", "surface5-timeout"])
def test_all_derived_message_rules_compare_full_strings(gate: Any, sid: str) -> None:
    before, after = C.artificial_pair(gate)
    original = after[sid]["exception_message"]["value"]
    after[sid]["exception_message"]["value"] = original + " WRONG_SUFFIX"
    with pytest.raises(G.GateError, match="DIFF_(PATHS|VALUE)"):
        gate.compare(before, after, C.ARTIFICIAL_READERS)
    after[sid]["exception_message"]["value"] = original[: len(original) // 2]
    with pytest.raises(G.GateError, match="DIFF_(PATHS|VALUE)"):
        gate.compare(before, after, C.ARTIFICIAL_READERS)


def test_no_path_or_nested_payload_mask(gate: Any) -> None:
    before, after = C.artificial_pair(gate)
    after["REAL_DIR"]["return_value"]["value"]["src_root"] = "/different/destination"
    with pytest.raises(G.GateError, match="DIFF_PATHS"):
        gate.compare(before, after, C.ARTIFICIAL_READERS)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-scenario",
        "unknown-scenario",
        "source-hash",
        "empty-source",
        "missing-kwarg",
        "wrong-call-source",
    ],
)
def test_registration_fail_closed(gate: Any, mutation: str) -> None:
    entries = gate.expected["scenarios"]
    change = entries["REAL_DIR"]["differences"]["/calls/0/kwargs/timeout"]
    if mutation == "missing-scenario":
        del entries["REAL_DIR"]
    elif mutation == "unknown-scenario":
        entries["UNKNOWN"] = copy.deepcopy(entries["REAL_DIR"])
    elif mutation == "source-hash":
        change["old"]["ref"]["sha256"] = "0" * 64
    elif mutation == "empty-source":
        change["new"]["source"]["quote"] = ""
    elif mutation == "missing-kwarg":
        del entries["REAL_DIR"]["differences"]["/calls/0/kwargs/timeout"]
    else:
        change["old"]["ref"]["pointer"] = "/observations/0/trace/0/kwargs"
    with pytest.raises(G.GateError):
        gate.validate()


def test_item5_membership_extraction_not_reader_result_inference() -> None:
    output: dict[str, Any] = {
        "OBS-1.item5-order": {
            "scenarios": [
                {"scenario_id": sid, "readers": [{"reader": "is_protected"}, {"reader": "other"}]}
                for sid in ("EXCLUDE_INTERRUPTED", "MARKER_WRITE_INTERRUPTED")
            ]
        }
    }
    assert G.readers_from_item5(output) == ["is_protected", "other"]
    output["OBS-1.item5-order"]["scenarios"][1]["readers"].pop()
    with pytest.raises(G.GateError, match="UNIVERSES_DIFFER"):
        G.readers_from_item5(output)


def test_injected_two_run_framework_runs_both_and_rejects_empty_readers_before_callbacks(
    gate: Any,
) -> None:
    before, after = C.artificial_pair(gate)
    seen = []

    def runner(frame: Any, label: str) -> Any:
        def collect(scenario: Any, readers: list[str]) -> Any:
            assert readers == C.ARTIFICIAL_READERS
            seen.append((label, scenario["id"]))
            return copy.deepcopy(frame[scenario["id"]])

        return collect

    old, new = gate.dual_run(runner(before, "before"), runner(after, "after"), C.ARTIFICIAL_READERS)
    assert old == before and new == after
    assert len(seen) == 2 * len(gate.manifest["scenarios"])
    seen.clear()
    with pytest.raises(G.GateError, match="READERS_EMPTY_OR_MISSING"):
        gate.dual_run(runner(before, "before"), runner(after, "after"), [])
    assert not seen


def test_absence_is_not_json_null_and_boolean_is_not_integer() -> None:
    assert G.changes({"x": G.ABSENT}, {"x": G.value(None)})
    assert G.changes({"x": False}, {"x": 0})
    with pytest.raises(G.GateError):
        G.validate_value(None, B.state("str"))
    with pytest.raises(G.GateError):
        G.validate_value(True, "int")


def test_snapshot_sources_remain_hash_identical(gate: Any) -> None:
    for file, sha in G.OBS_HASHES.items():
        assert json.loads(gate.sources.read(file, sha))


@pytest.mark.parametrize(
    "sid",
    [
        "EXCLUDE_INTERRUPTED",
        "MARKER_WRITE_INTERRUPTED",
        "surface1-SIGINT",
        "surface6-SIGTERM",
        "LIVE_SYMLINK_TO_DIR",
    ],
)
def test_e2_2_kwarg_registration_is_not_limited_to_default_surface_scenarios(
    gate: Any, sid: str
) -> None:
    before, after = C.artificial_pair(gate)
    assert all("timeout" not in c["kwargs"] for c in before[sid]["calls"])
    assert all(c["kwargs"]["timeout"] is None for c in after[sid]["calls"])
    resolved = gate.validate()[sid]
    assert all(f"/calls/{i}/kwargs/timeout" in resolved for i in range(len(before[sid]["calls"])))


@pytest.mark.parametrize("mutation", ["wrong-rule", "wrong-field-literal", "wrong-observation"])
def test_timeout_result_sources_bind_to_field_and_fixture(gate: Any, mutation: str) -> None:
    differences = gate.expected["scenarios"]["surface5-timeout"]["differences"]
    if mutation == "wrong-rule":
        differences["/exception_message"]["new"]["rule"] = "TIMEOUT_MESSAGE_FROM_EXC"
    elif mutation == "wrong-field-literal":
        differences["/exception_type"]["new"]["value"] = "FETCH_TIMEOUT"
    else:
        differences["/exception_message"]["new"]["inputs"]["injection"]["pointer"] = (
            "/observations/5/injection"
        )
    with pytest.raises(G.GateError):
        gate.validate()


def test_wrong_live_message_stops_existing_branch_derivation(gate: Any) -> None:
    row = gate.manifest["scenarios"][0]
    recipe = gate.expected["scenarios"]["DANGLING_SYMLINK"]["differences"]["/exception_message"][
        "new"
    ]
    original_fact = gate.sources.fact

    def fact(ref: Any) -> Any:
        result = original_fact(ref)
        if ref == recipe["inputs"]["adjacent"]:
            result["outcome"]["exception"]["value"]["message"] += " WRONG"
        return result

    gate.sources.fact = fact
    with pytest.raises(G.GateError, match="E2-1_LIVE_MESSAGE_MISMATCH"):
        G.resolve_new(recipe, row, gate.sources)


def test_citation_must_be_the_correct_surface_cell_even_if_same_exception_type(gate: Any) -> None:
    source = gate.expected["scenarios"]["surface1-timeout"]["differences"]["/exception_type"][
        "new"
    ]["source"]
    source["quote"] = gate.sources.timeout_cells()[1]
    with pytest.raises(G.GateError, match="MAPPING_SURFACE_BINDING"):
        gate.validate()


@pytest.mark.parametrize("number", range(1, 7))
def test_e3_timeout_fields_and_old_values_match_same_observation(gate: Any, number: int) -> None:
    sid = f"surface{number}-timeout"
    row = next(r for r in gate.manifest["scenarios"] if r["id"] == sid)
    deltas = gate.expected["scenarios"][sid]["differences"]
    fields = (
        {"/exception_type", "/exception_code"}
        if number <= 3
        else {"/return_value", "/warnings"}
        if number == 4
        else {"/exception_type", "/exception_message"}
    )
    assert set(deltas) == fields | {"/calls/0/kwargs/timeout"}
    plan = row["before_run"]
    assert plan["pass_timeout"] is False
    assert plan["source"]["section"] == "附录C/E3-1"
    assert plan["injection_ref"]["pointer"] == row["obs_ref"]["pointer"] + "/injection"
    assert all(deltas[p]["old"]["ref"]["file"] == G.OBS + "e1-item4/raw.json" for p in fields)
    assert all(
        deltas[p]["old"]["ref"]["pointer"].startswith(row["obs_ref"]["pointer"] + "/outcome/")
        for p in fields
    )
    before, after = C.artificial_pair(gate)
    observed = gate.sources.fact(row["obs_ref"])["outcome"]
    assert before[sid]["return_value"] == observed["return_value"]
    if number != 4:
        assert before[sid]["exception_type"] == G.value("TimeoutExpired")
        assert before[sid]["exception_message"] == G.value(
            observed["exception"]["value"]["message"]
        )
    if number <= 3:
        assert before[sid]["exception_message"] == after[sid]["exception_message"]
    gate.compare(before, after, C.ARTIFICIAL_READERS)


@pytest.mark.parametrize("number", range(1, 7))
def test_e3_old_source_cannot_borrow_another_timeout_scene(gate: Any, number: int) -> None:
    sid = f"surface{number}-timeout"
    field = "/return_value" if number == 4 else "/exception_type"
    ref = gate.expected["scenarios"][sid]["differences"][field]["old"]["ref"]
    other_index = 5 if number == 1 else 1
    ref["pointer"] = ref["pointer"].replace(
        f"/observations/{(number - 1) * 4 + 1}/", f"/observations/{other_index}/"
    )
    with pytest.raises(G.GateError, match="TIMEOUT_RESULT_OLD_SOURCE_BINDING"):
        gate.validate()


@pytest.mark.parametrize("number", range(1, 7))
def test_e3_obsolete_absence_source_is_rejected(gate: Any, number: int) -> None:
    sid = f"surface{number}-timeout"
    field = "/return_value" if number == 4 else "/exception_type"
    gate.expected["scenarios"][sid]["differences"][field]["old"] = {
        "kind": "ABSENT_SECTION4",
        "source": {},
    }
    with pytest.raises(G.GateError):
        gate.validate()


@pytest.mark.parametrize("number", [1, 2, 3])
def test_e3_same_wrong_message_on_both_sides_cannot_hide_bad_before_input(
    gate: Any, number: int
) -> None:
    before, after = C.artificial_pair(gate)
    sid = f"surface{number}-timeout"
    for frame in (before, after):
        frame[sid]["exception_message"] = G.value("not the archived TimeoutExpired text")
    with pytest.raises(G.GateError, match="TIMEOUT_BEFORE_OUTCOME"):
        gate.compare(before, after, C.ARTIFICIAL_READERS)


@pytest.mark.parametrize("mutation", ["missing", "pass-timeout", "different-injection"])
def test_e3_before_run_plan_is_required_and_exact(gate: Any, mutation: str) -> None:
    row = next(r for r in gate.manifest["scenarios"] if r["id"] == "surface1-timeout")
    if mutation == "missing":
        del row["before_run"]
    elif mutation == "pass-timeout":
        row["before_run"]["pass_timeout"] = True
    else:
        row["before_run"]["injection_ref"]["pointer"] = "/observations/5/injection"
    with pytest.raises(G.GateError, match="CLOSED_FIELDS|TIMEOUT_BEFORE_PLAN"):
        gate.validate()
