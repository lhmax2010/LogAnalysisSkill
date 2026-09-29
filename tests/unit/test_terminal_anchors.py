"""Artificial selector and filesystem controls; no live OBS producer invocation."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "docs/clang-fix-campaign/tools"
SPEC = importlib.util.spec_from_file_location("terminal_anchors_test", TOOLS / "verify_anchors.py")
assert SPEC is not None and SPEC.loader is not None
saved = sys.path[:]
sys.path.insert(0, str(TOOLS))
try:
    A = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(A)
finally:
    sys.path[:] = saved


@pytest.mark.parametrize("operator,count", [("and", 1), ("or", 0)])
def test_boolean_selector_counts_exact_shape(operator: str, count: int) -> None:
    source = (
        f"def guard(p):\n    if p.exists() {operator} p.is_symlink():\n        raise ValueError()\n"
    )
    assert A.item3_anchor(source)["matched_count"] == count


def test_duplicate_selector_is_not_silently_chosen() -> None:
    one = "def f(p):\n    return p.exists() and p.is_symlink()\n"
    found = A.item3_anchor(one + one.replace("f(p)", "g(p)"))
    assert found["matched_count"] == 2
    assert found["span_sha256"] == ""


def test_receiver_mismatch_is_reported_as_fact() -> None:
    found = A.item3_anchor("def f(p,q):\n    return p.exists() and q.is_symlink()\n")
    assert found["matched_count"] == 1
    assert found["same_receiver"] is False


def test_call_selector_not_line_number(tmp_path: Path) -> None:
    source = tmp_path / "module.py"
    source.write_text("\n\ndef f(x):\n    return x()\n\ndef other():\n    return x()\n")
    anchor, spans = A.call_anchor(tmp_path, 1, "module.py", "f", "x")
    assert anchor["matched_count"] == 1
    assert spans[0]["source"] == "x()"
    assert spans[0]["lineno"] == 4


def test_dangling_link_is_not_recorded_as_absent(tmp_path: Path) -> None:
    path = tmp_path / "link"
    path.symlink_to(tmp_path / "missing")
    assert A.path_state(path) == {
        "kind": "SYMLINK",
        "target": str(tmp_path / "missing"),
        "target_exists": False,
    }


def test_marker_hash_is_raw_byte_hash(tmp_path: Path) -> None:
    path = tmp_path / "marker"
    assert A.marker_state(path) == {"state": "ABSENT"}
    path.write_bytes(b'{"partial":')
    assert A.marker_state(path) == {"state": "PRESENT", "sha256": A.digest(path)}


def test_claim_allowlist_excludes_item5() -> None:
    assert set(A.CLAIMS.values()) == {"OBS-1.item3-predicate", "OBS-1.item4-anchors"}
