from __future__ import annotations

import os
import unicodedata
from pathlib import Path

import pytest
from tizen_build_verify.edit_spec_guard import EditSpecViolation, validate_edit_spec


def _write(root: Path, relative: str, text: str = "alpha\nbeta\ngamma\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _spec(file_value: str, *, old: str = "beta", line: int | None = 2) -> dict[str, object]:
    edit: dict[str, object] = {"file": file_value, "old": old, "new": "BETA"}
    if line is not None:
        edit["line"] = line
    return {
        "schema_version": "gbs_patch_suggest/edit-spec/v1",
        "patch_name": "candidate.patch",
        "edits": [edit],
    }


def test_normal_relative_path_passes(tmp_path: Path) -> None:
    _write(tmp_path, "tools/include/OutputMetadata.h")

    validate_edit_spec(_spec("tools/include/OutputMetadata.h"), str(tmp_path))


def test_absolute_path_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(EditSpecViolation, match="absolute"):
        validate_edit_spec(_spec("/etc/passwd"), str(tmp_path))


def test_parent_traversal_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(EditSpecViolation, match="escapes|parent"):
        validate_edit_spec(_spec("../../outside.c"), str(tmp_path))


def test_intermediate_symlink_to_outside_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "target.c").write_text("beta\n", encoding="utf-8")
    (root / "link").symlink_to(outside, target_is_directory=True)

    with pytest.raises(EditSpecViolation, match="symlink escapes"):
        validate_edit_spec(_spec("link/target.c", old="beta", line=1), str(root))


def test_final_symlink_to_outside_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.c"
    outside.write_text("beta\n", encoding="utf-8")
    src = root / "src"
    src.mkdir()
    (src / "link.c").symlink_to(outside)

    with pytest.raises(EditSpecViolation, match="symlink escapes"):
        validate_edit_spec(_spec("src/link.c", old="beta", line=1), str(root))


def test_git_internal_path_is_rejected(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("beta\n", encoding="utf-8")

    with pytest.raises(EditSpecViolation, match=".git"):
        validate_edit_spec(_spec(".git/config", old="beta", line=1), str(tmp_path))


def test_empty_and_directory_paths_are_rejected(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()

    with pytest.raises(EditSpecViolation, match="empty"):
        validate_edit_spec(_spec(""), str(tmp_path))
    with pytest.raises(EditSpecViolation, match="directory"):
        validate_edit_spec(_spec("src"), str(tmp_path))


def test_nfd_path_normalizes_to_existing_nfc_file(tmp_path: Path) -> None:
    nfc_name = unicodedata.normalize("NFC", "café.c")
    nfd_name = unicodedata.normalize("NFD", "café.c")
    _write(tmp_path, nfc_name, "beta\n")

    validate_edit_spec(_spec(nfd_name, old="beta", line=1), str(tmp_path))


def test_case_insensitive_bypass_is_platform_specific(tmp_path: Path) -> None:
    if os.path.normcase("A") == "A":
        pytest.skip("case-sensitive filesystem")
    _write(tmp_path, "Src/File.c", "beta\n")
    validate_edit_spec(_spec("src/file.c", old="beta", line=1), str(tmp_path))


def test_overlapping_edits_are_rejected(tmp_path: Path) -> None:
    _write(tmp_path, "src/file.c", "abcdef\n")
    spec = {
        "schema_version": "gbs_patch_suggest/edit-spec/v1",
        "patch_name": "candidate.patch",
        "edits": [
            {"file": "src/file.c", "line": 1, "old": "abc", "new": "ABC"},
            {"file": "src/file.c", "line": 1, "old": "bcd", "new": "BCD"},
        ],
    }

    with pytest.raises(EditSpecViolation, match="overlapping"):
        validate_edit_spec(spec, str(tmp_path))


@pytest.mark.parametrize(
    "bad_spec",
    [
        {"schema_version": "wrong", "patch_name": "x.patch", "edits": []},
        {
            "schema_version": "gbs_patch_suggest/edit-spec/v1",
            "patch_name": "x.patch",
            "edits": [],
        },
        {
            "schema_version": "gbs_patch_suggest/edit-spec/v1",
            "patch_name": "x.patch",
            "edits": [{"old": "x", "new": "y"}],
        },
        {
            "schema_version": "gbs_patch_suggest/edit-spec/v1",
            "patch_name": "x.patch",
            "edits": [{"file": "x.c", "new": "y"}],
        },
    ],
)
def test_invalid_schema_is_rejected(tmp_path: Path, bad_spec: dict[str, object]) -> None:
    with pytest.raises(EditSpecViolation):
        validate_edit_spec(bad_spec, str(tmp_path))
