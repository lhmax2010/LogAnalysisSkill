"""Immutable authority inputs retain their original hashes and exact wording."""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
saved = sys.path[:]
sys.path.insert(0, str(ROOT / "docs/clang-fix-campaign/tools"))
try:
    A = importlib.import_module("terminal_authority")
    S = importlib.import_module("terminal_scan")
finally:
    sys.path[:] = saved


def test_immutable_e10_with_current_authority_containment() -> None:
    old = A.read_authority(ROOT, A.E10_COMMIT, S.RULES_SHA)
    assert b"E10-1" in old and b"E11-1" not in old


def test_additions_do_not_change_pinned_bytes() -> None:
    assert A.assert_contained(b"heading\nbody\n", b"heading\nnew\nbody\nappend\n") is None


@pytest.mark.parametrize("current", [b"heading\n", b"heading\n body\n", b"body\nheading\n"])
def test_removal_rewording_and_reordering_are_red(current: bytes) -> None:
    with pytest.raises(ValueError, match="CURRENT_AUTHORITY_MISSING_SOURCE"):
        A.assert_contained(b"heading\nbody\n", current)


def test_blob_hash_change_is_red() -> None:
    with pytest.raises(ValueError, match="AUTHORITY_BLOB_HASH"):
        A.read_authority(ROOT, A.E10_COMMIT, "0" * 64)
