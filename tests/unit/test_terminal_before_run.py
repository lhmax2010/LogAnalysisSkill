"""Artificial before-collector controls, without running an OBS producer."""

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

saved = sys.path[:]
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "docs/clang-fix-campaign/tools"))
try:
    B = importlib.import_module("terminal_before_run")
finally:
    sys.path[:] = saved


def test_copy_absent_and_dangling_are_distinct(tmp_path: Path) -> None:
    B.copy_scene(tmp_path / "absent", tmp_path / "copy-absent")
    assert not (tmp_path / "copy-absent").exists()
    source = tmp_path / "dangling"
    source.symlink_to(tmp_path / "missing")
    B.copy_scene(source, tmp_path / "copy-link")
    assert (tmp_path / "copy-link").is_symlink()
    assert B.file_state(source)["value"]["kind"] == "SYMLINK"
    assert B.file_state(tmp_path / "absent")["value"]["kind"] == "ABSENT"


def test_gate_reader_copies_isolated_and_exception_fields_exact(tmp_path: Path) -> None:
    source = tmp_path / "original"
    source.mkdir()
    (source / "marker").write_bytes(b"partial")

    def remove(*, worktree_path: Path) -> None:
        (worktree_path / "marker").unlink()

    def read(*, worktree_path: Path) -> bytes:
        assert (worktree_path / "marker").read_bytes() == b"partial"
        raise ValueError("exact message")

    rows = B.reader_results(
        SimpleNamespace(remove=remove, read=read), source, tmp_path / "copies", ["remove", "read"]
    )
    assert rows[0]["return_value"] == {"state": "VALUE", "value": None}
    assert rows[1]["exception_type"] == {"state": "VALUE", "value": "builtins.ValueError"}
    assert rows[1]["exception_message"] == {"state": "VALUE", "value": "exact message"}
    assert (source / "marker").read_bytes() == b"partial"
