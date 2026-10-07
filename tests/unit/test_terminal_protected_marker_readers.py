"""E11-2 reader selector controls; only artificial source is parsed."""

import importlib
import sys
from pathlib import Path

saved = sys.path[:]
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs/clang-fix-campaign/tools"))
try:
    R = importlib.import_module("protected_marker_readers")
finally:
    sys.path[:] = saved


def test_e11_new_name_and_attribute_reader_listed() -> None:
    source = (
        "def new_reader(path):\n return path / PROTECTED_FILENAME\n"
        "def other(path):\n return path / workspace.PROTECTED_FILENAME\n"
    )
    assert [r["reader"] for r in R.functions(source, "test.py")] == ["new_reader", "other"]


def test_e11_comment_string_and_signature_near_miss() -> None:
    source = (
        "# PROTECTED_FILENAME\n"
        "def f(x=PROTECTED_FILENAME):\n return 'PROTECTED_FILENAME'\n"
        "def mark_worktree_protected(p):\n return p / PROTECTED_FILENAME\n"
    )
    assert R.functions(source, "test.py") == []


def test_e11_tests_and_writers_not_silently_excluded() -> None:
    source = (
        "def test_marker(tmp_path):\n (tmp_path / PROTECTED_FILENAME).write_text('x')\n"
    )
    result = R.functions(source, "tests/test_marker.py")
    assert [r["reader"] for r in result] == ["test_marker"]
    assert result[0]["arguments"] == "tmp_path"


def test_e11_nested_function_body_and_async_are_scanned() -> None:
    source = (
        "def outer():\n def inner():\n  return PROTECTED_FILENAME\n return inner\n"
        "class C:\n async def f(self):\n  return w.PROTECTED_FILENAME\n"
    )
    assert [r["qualname"] for r in R.functions(source, "test.py")] == [
        "outer", "outer.inner", "C.f"
    ]
