"""Artificial invocation contract: each reader receives its own failure copy."""

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

saved = sys.path[:]
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs/clang-fix-campaign/tools"))
try:
    M = importlib.import_module("terminal_marker_observation")
finally:
    sys.path[:] = saved


def test_readers_do_not_share_or_mutate_failure_scene(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "marker").write_bytes(b"partial")
    seen = []

    def remove(*, worktree_path: Path) -> bool:
        seen.append(worktree_path)
        (worktree_path / "marker").unlink()
        return True

    def read(*, worktree_path: Path) -> str:
        seen.append(worktree_path)
        return (worktree_path / "marker").read_text()

    module = SimpleNamespace(PROTECTED_FILENAME="marker", remove=remove, read=read)
    rows = M.read_copies(module, source, tmp_path / "copies", ["remove", "read"])
    assert rows[0]["result_value_or_type"] == "True"
    assert rows[1]["result_value_or_type"] == "'partial'"
    assert seen[0] != seen[1] and all(path != source for path in seen)
    assert (source / "marker").read_bytes() == b"partial"
    assert rows[0]["marker_before"] == rows[1]["marker_before"]


def test_reader_exception_records_fully_qualified_type(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()

    def fail(**kwargs: Any) -> None:
        raise ValueError("fixture")

    rows = M.read_copies(
        SimpleNamespace(PROTECTED_FILENAME="marker", fail=fail),
        source,
        tmp_path / "copies",
        ["fail"],
    )
    assert rows[0]["result_kind"] == "EXCEPTION"
    assert rows[0]["result_value_or_type"] == "builtins.ValueError"
