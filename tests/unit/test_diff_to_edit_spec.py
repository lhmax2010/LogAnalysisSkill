from __future__ import annotations

import copy
import io
import json

import pytest
from ci_triage.cli import main as legacy_main
from tizen_build_verify.edit_spec_guard import EditSpecViolation, validate_edit_spec
from tizen_campaign_core import diff_to_edit_spec as converter
from tizen_campaign_repair.diff_cli import main


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "src"
    root.mkdir()
    (root / "file.c").write_text("one\nold\nthree\nfour\nfive\nold\nseven\n")
    return root


def diff(path="file.c", hunk="@@ -2 +2 @@\n-old\n+new\n"):
    return f"--- {path}\n+++ {path}\n" + hunk


@pytest.mark.parametrize("header", ["plain", "git", "p4", "obs", "timestamp"])
def test_headers_and_real_guard(source, header):
    hunk = "@@ -1,3 +1,3 @@\n one\n-old\n+new\n three\n"
    text = diff(hunk=hunk)
    if header == "git":
        text = "diff --git a/file.c b/file.c\nindex 1234567..abcdef0 100644\n"
        text += "--- a/file.c\n+++ b/file.c\n" + hunk
    elif header == "p4":
        text = "Change 123 by synthetic\n\nAffected files ...\n"
        text += "==== //depot/component/file.c#7 (text) ====\n" + hunk
    elif header == "obs":
        text = "Subject: fix\nIndex: component/file.c\n===================\n"
        text += diff("component/file.c", hunk)
    elif header == "timestamp":
        text = "--- file.c\t2026-11-04 00:00:00\n+++ file.c\t2026-11-04 01:00:00\n" + hunk
    before = (source / "file.c").read_bytes()
    spec = converter.convert(text, source, "fix")
    assert spec == {
        "schema_version": "gbs_patch_suggest/edit-spec/v1", "patch_name": "fix",
        "edits": [{"file": "file.c", "old": "one\nold\nthree\n", "new": "one\nnew\nthree\n"}],
    }
    validate_edit_spec(spec, str(source))
    assert (source / "file.c").read_bytes() == before


def test_unique_strip_level_and_ambiguity(source):
    assert converter.convert(diff("release/component/file.c"), source, "fix")["edits"][0][
        "file"
    ] == "file.c"
    (source / "component").mkdir()
    (source / "component/file.c").write_text((source / "file.c").read_text())
    with pytest.raises(converter.DiffUnsupported, match="ambiguous"):
        converter.convert(diff("release/component/file.c"), source, "fix")


def test_multiple_hunks_and_duplicate_old_anchor(source):
    text = diff(hunk="@@ -2 +2 @@\n-old\n+first\n@@ -6 +6 @@\n-old\n+second\n")
    spec = converter.convert(text, source, "fix")
    assert [edit["line"] for edit in spec["edits"]] == [2, 6]
    validate_edit_spec(spec, str(source))


def test_multifile(source):
    (source / "other.c").write_text("old\n")
    spec = converter.convert(diff() + diff("other.c", "@@ -1 +1 @@\n-old\n+new\n"), source, "f")
    assert len(spec["edits"]) == 2
    assert spec["edits"][0]["line"] == 2
    assert "line" not in spec["edits"][1]


def test_no_final_newline(source):
    (source / "file.c").write_text("old")
    text = diff(hunk="@@ -1 +1 @@\n-old\n\\ No newline at end of file\n"
                "+new\n\\ No newline at end of file\n")
    spec = converter.convert(text, source, "f")
    assert spec["edits"] == [{"file": "file.c", "old": "old", "new": "new"}]


@pytest.mark.parametrize("header,reason", [
    ("==== //depot/file.c#1 - //depot/other.c#2 ====", "rename"),
    ("==== //depot/file.c#1 (binary) ====", "binary"),
])
def test_p4_metadata_not_discarded(source, header, reason):
    with pytest.raises(converter.DiffUnsupported, match=reason):
        converter.convert(header + "\n@@ -2 +2 @@\n-old\n+new\n", source, "f")


def test_p4_same_path_revision_pair(source):
    spec = converter.convert(
        "==== //depot/file.c#1 - //depot/file.c#2 ====\n@@ -2 +2 @@\n-old\n+new\n",
        source, "f",
    )
    validate_edit_spec(spec, str(source))


@pytest.mark.parametrize("prefix,reason", [
    ("rename from old.c\nrename to file.c\n", "rename"),
    ("copy from old.c\ncopy to file.c\n", "copy"),
    ("GIT binary patch\n", "binary"),
    ("Binary files a/file.c and b/file.c differ\n", "binary"),
    ("old mode 100644\nnew mode 100755\n", "mode_change"),
    ("new file mode 100644\n", "new_file"),
    ("deleted file mode 100644\n", "deleted_file"),
])
def test_unsupported_git_shapes(source, prefix, reason):
    with pytest.raises(converter.DiffUnsupported, match=reason):
        converter.convert("diff --git a/file.c b/file.c\n" + prefix + diff(), source, "f")


@pytest.mark.parametrize("text", [
    "--- /dev/null\n+++ file.c\n@@ -0,0 +1 @@\n+new\n",
    "--- file.c\n+++ /dev/null\n@@ -1 +0,0 @@\n-old\n",
    "--- file.c\n+++ other.c\n@@ -2 +2 @@\n-old\n+new\n",
    diff(hunk="@@ -2 +2 @@\n-missing\n+new\n"),
    diff(hunk="@@ -1,2 +1,2 @@\n-old\n-three\n+new\n+three\n"),
    diff(hunk="@@ -2,3 +2,3 @@\n old\n three\n-WRONG\n+new\n"),
    diff(hunk="@@ -0,0 +1 @@\n+new\n"),
    diff(hunk="@@ -2,2 +2,2 @@\n-old\n+new\n"),
    diff(hunk="@@ -2 +2 @@\n-old\n+new\n@@ -2 +2 @@\n-old\n+again\n"),
    diff(hunk="@@ -2 +2 @@\n old\n"),
    "diff --git a/file.c b/file.c\n",
    "@@ -2 +2 @@\n-old\n+new\n",
    "",
])
def test_no_guessing_unsupported_shapes(source, text):
    with pytest.raises(converter.DiffUnsupported):
        converter.convert(text, source, "f")


@pytest.mark.parametrize("path", ["/file.c", "../file.c", "x/../../file.c", ".git/file.c",
                                      "x/.git/file.c", "missing.c", ".", "dir"])
def test_unsafe_paths_and_nonfiles(source, path):
    (source / "dir").mkdir()
    with pytest.raises(converter.DiffUnsupported):
        converter.convert(diff(path), source, "f")


def test_symlinks_inside_allowed_outside_rejected(source, tmp_path):
    (source / "alias.c").symlink_to(source / "file.c")
    spec = converter.convert(diff("alias.c"), source, "f")
    validate_edit_spec(spec, str(source))
    outside = tmp_path / "outside.c"
    outside.write_text((source / "file.c").read_text())
    (source / "escape.c").symlink_to(outside)
    with pytest.raises(converter.DiffUnsupported, match="guard_rejected"):
        converter.convert(diff("escape.c"), source, "f")


@pytest.mark.parametrize("mutation", [
    "schema", "name", "no_edits", "file", "old", "new", "line_zero", "line_far",
    "absolute", "parent", "git", "symlink", "missing", "directory", "nonregular",
    "nonunique", "single_line_anchor", "overlap",
])
def test_real_guard_rejection_matrix(source, tmp_path, mutation):
    import os

    spec = converter.convert(diff(), source, "f")
    edit = spec["edits"][0]
    if mutation == "schema":
        spec["schema_version"] = "invalid"
    elif mutation == "name":
        spec["patch_name"] = ""
    elif mutation == "no_edits":
        spec["edits"] = []
    elif mutation in {"file", "old", "new"}:
        del edit[mutation]
    elif mutation == "line_zero":
        edit["line"] = 0
    elif mutation == "line_far":
        edit["line"] = 900
    elif mutation == "absolute":
        edit["file"] = str(source / "file.c")
    elif mutation == "parent":
        edit["file"] = "../file.c"
    elif mutation == "git":
        edit["file"] = ".git/file.c"
    elif mutation == "symlink":
        (source / "escape").symlink_to(tmp_path)
        edit["file"] = "escape/out.c"
    elif mutation == "missing":
        edit["file"] = "missing.c"
    elif mutation == "directory":
        (source / "directory").mkdir()
        edit["file"] = "directory"
    elif mutation == "nonregular":
        os.mkfifo(source / "fifo")
        edit["file"] = "fifo"
    elif mutation == "nonunique":
        del edit["line"]
    elif mutation == "single_line_anchor":
        edit.update(old="old", line=1)
    elif mutation == "overlap":
        spec["edits"].append(copy.deepcopy(edit))
    with pytest.raises(EditSpecViolation):
        validate_edit_spec(spec, str(source))


def test_cli_publication_and_shared_entry(source, tmp_path, monkeypatch):
    patch = tmp_path / "input.diff"
    patch.write_text(diff())
    output = tmp_path / "edit.json"
    args = ["--diff", str(patch), "--src-root", str(source), "--output", str(output),
            "--patch-name", "fix"]
    out = io.StringIO()
    assert main(args, stdout=out) == 0
    validate_edit_spec(json.loads(output.read_text()), str(source))
    before = output.read_bytes()
    patch.write_text(diff(hunk="@@ -1 +1 @@\n-not-there\n+new\n"))
    out = io.StringIO()
    assert legacy_main(["diff-to-edit-spec", *args], stdout=out) == 4
    assert json.loads(out.getvalue())["error_code"] == "DIFF_CONVERT_UNSUPPORTED"
    assert output.read_bytes() == before
    patch.write_text(diff())

    def reject(*args):
        raise EditSpecViolation("injected guard refusal")

    monkeypatch.setattr(converter, "validate_edit_spec", reject)
    assert main(args, stdout=io.StringIO()) == 4
    assert output.read_bytes() == before
    assert not list(tmp_path.glob(".edit-spec-*"))


@pytest.mark.parametrize("args", [[], ["--patch-name", "fix"], ["--unknown"]])
def test_invalid_args_same_json_and_exit(args):
    new, old = io.StringIO(), io.StringIO()
    assert main(args, stdout=new) == 2
    assert legacy_main(["diff-to-edit-spec", *args], stdout=old) == 2
    assert json.loads(new.getvalue()) == json.loads(old.getvalue())


def test_input_hashes_unchanged_and_empty_patch_name(source, tmp_path):
    patch = tmp_path / "patch.diff"
    patch.write_text(diff())
    before = patch.read_bytes()
    args = ["--diff", str(patch), "--src-root", str(source), "--output", str(patch),
            "--patch-name", "fix"]
    assert main(args, stdout=io.StringIO()) == 2
    assert patch.read_bytes() == before
    args[-1] = ""
    assert main(args, stdout=io.StringIO()) == 2
