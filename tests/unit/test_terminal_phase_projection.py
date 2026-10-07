"""PHASE1-03 source-derived projection, with full-phase behavior unchanged."""

import copy
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
saved = sys.path[:]
sys.path.insert(0, str(ROOT / "docs/clang-fix-campaign/tools"))
try:
    G = importlib.import_module("terminal_expected_diff")
    C = importlib.import_module("terminal_phase_controls")
finally:
    sys.path[:] = saved


@pytest.mark.parametrize("control", C.CONTROLS)
def test_phase_a_controls(control: str) -> None:
    gate = G.load_gate(ROOT)
    if control == "normal":
        C.run(gate, control)
    else:
        with pytest.raises(G.GateError, match="DIFF_PATHS"):
            C.run(gate, control)


def test_projection_uses_document_source_not_section_prefix_or_result() -> None:
    gate = G.load_gate(ROOT)
    frozen = copy.deepcopy(gate.expected)
    projection = gate.item3_projection()
    assert {(r["scenario"], r["path"]) for r in projection} == {
        ("DANGLING_SYMLINK", "/exception_type"),
        ("DANGLING_SYMLINK", "/exception_code"),
        ("DANGLING_SYMLINK", "/exception_message"),
    }
    assert all(row["source"]["file"] == G.DOC for row in projection)
    assert gate.expected == frozen


def test_full_phase_still_requires_item3_and_rejects_unknown_phase() -> None:
    gate = G.load_gate(ROOT)
    before, after = C.phase_a_pair(gate)
    for kwargs in ({}, {"phase": "FULL"}):
        with pytest.raises(G.GateError, match="DIFF_PATHS"):
            gate.compare(before, after, C.ARTIFICIAL_READERS, **kwargs)
    with pytest.raises(G.GateError, match="UNKNOWN_PHASE"):
        gate.compare(before, after, C.ARTIFICIAL_READERS, phase="B-partial")


def test_unregistered_change_in_a_is_still_red() -> None:
    gate = G.load_gate(ROOT)
    before, after = C.phase_a_pair(gate)
    after["REAL_DIR"]["action"] = G.value("unexpected")
    with pytest.raises(G.GateError, match="DIFF_PATHS"):
        gate.compare(before, after, C.ARTIFICIAL_READERS, phase="A")
