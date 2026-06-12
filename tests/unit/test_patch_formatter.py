import json
import shutil
import subprocess
from pathlib import Path

from gbs_patch_suggest.cli import main
from gbs_patch_suggest.formatter import FormatPatchOptions, format_patch


def write_spec(tmp_path: Path, edits: list[dict[str, object]]) -> Path:
    path = tmp_path / "edit_spec.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "gbs_patch_suggest/edit-spec/v1",
                "patch_name": "candidate_1.patch",
                "description": "test patch",
                "edits": edits,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_format_patch_generates_git_apply_compatible_patch_without_touching_source(
    tmp_path: Path,
) -> None:
    src_root = tmp_path / "src"
    source = src_root / "src" / "demo.c"
    source.parent.mkdir(parents=True)
    original = "int main(void) {\n\tint value = 1;\n\treturn value;\n}\n"
    source.write_text(original, encoding="utf-8")
    spec = write_spec(
        tmp_path,
        [
            {
                "file": "src/demo.c",
                "line": 2,
                "old": "value = 1",
                "new": "value = 2",
            }
        ],
    )
    output = tmp_path / "candidate_1.patch"

    result = format_patch(FormatPatchOptions(src_root, spec, output, check=True))

    assert result.exit_code == 0
    assert result.check_passed is True
    assert source.read_text(encoding="utf-8") == original
    patch = output.read_text(encoding="utf-8")
    assert "diff --git a/src/demo.c b/src/demo.c" in patch
    assert "--- a/src/demo.c" in patch
    assert "+++ b/src/demo.c" in patch
    assert "-\tint value = 1;" in patch
    assert "+\tint value = 2;" in patch
    subprocess.run(
        ["git", "-C", str(src_root), "apply", "--check", str(output)],
        check=True,
    )


def test_format_patch_applies_same_file_multi_edits_from_later_offsets(
    tmp_path: Path,
) -> None:
    src_root = tmp_path / "src"
    source = src_root / "src" / "tdm_meson_hwc.c"
    source.parent.mkdir(parents=True)
    source.write_text(
        "\n".join(
            [
                "void f(void) {",
                "\tfirst = hwc_window_data->name ? true : false;",
                "\tkeep();",
                "\tsecond = hwc_window_data->name ? true : false;",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec = write_spec(
        tmp_path,
        [
            {
                "file": "src/tdm_meson_hwc.c",
                "line": 2,
                "old": "hwc_window_data->name ? true : false",
                "new": "hwc_window_data->name != NULL",
            },
            {
                "file": "src/tdm_meson_hwc.c",
                "line": 4,
                "old": "hwc_window_data->name ? true : false",
                "new": "hwc_window_data->name != NULL",
            },
        ],
    )
    output = tmp_path / "candidate_1.patch"

    result = format_patch(FormatPatchOptions(src_root, spec, output, check=True))

    assert result.exit_code == 0
    patch = output.read_text(encoding="utf-8")
    assert patch.count("+\t") == 2
    apply_root = tmp_path / "apply"
    shutil.copytree(src_root, apply_root)
    subprocess.run(["git", "-C", str(apply_root), "apply", str(output)], check=True)
    applied = (apply_root / "src" / "tdm_meson_hwc.c").read_text(encoding="utf-8")
    assert applied.count("hwc_window_data->name != NULL") == 2
    assert "hwc_window_data->name ? true : false" not in applied


def test_format_patch_uses_before_after_to_disambiguate_duplicate_old(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    source = src_root / "src" / "demo.c"
    source.parent.mkdir(parents=True)
    source.write_text(
        "before_a\nsame_old\nafter_a\nbefore_b\nsame_old\nafter_b\n",
        encoding="utf-8",
    )
    spec = write_spec(
        tmp_path,
        [
            {
                "file": "src/demo.c",
                "old": "same_old",
                "new": "new_value",
                "before": "before_b\n",
                "after": "\nafter_b",
            }
        ],
    )

    result = format_patch(FormatPatchOptions(src_root, spec, tmp_path / "candidate.patch"))

    assert result.exit_code == 0
    patch = (tmp_path / "candidate.patch").read_text(encoding="utf-8")
    assert "-same_old" in patch
    assert "+new_value" in patch
    assert "before_b" in patch


def test_format_patch_reports_duplicate_old_without_disambiguation(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    source = src_root / "src" / "demo.c"
    source.parent.mkdir(parents=True)
    source.write_text("same_old\nmiddle\nsame_old\n", encoding="utf-8")
    spec = write_spec(
        tmp_path,
        [{"file": "src/demo.c", "old": "same_old", "new": "new_value"}],
    )
    output = tmp_path / "candidate.patch"

    result = format_patch(FormatPatchOptions(src_root, spec, output))

    assert result.exit_code == 1
    assert result.error_code == "old_not_unique"
    assert result.error is not None
    assert "1, 3" in result.error
    assert not output.exists()


def test_format_patch_reports_missing_old_and_cleans_temp_dir(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    source = src_root / "src" / "demo.c"
    source.parent.mkdir(parents=True)
    source.write_text("actual\n", encoding="utf-8")
    spec = write_spec(
        tmp_path,
        [{"file": "src/demo.c", "old": "missing", "new": "new_value"}],
    )
    temp_parent = tmp_path / "temps"
    temp_parent.mkdir()

    result = format_patch(
        FormatPatchOptions(src_root, spec, tmp_path / "candidate.patch", temp_parent=temp_parent)
    )

    assert result.exit_code == 1
    assert result.error_code == "old_not_found"
    assert list(temp_parent.iterdir()) == []


def test_format_patch_rejects_file_outside_src_root(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    src_root.mkdir()
    outside = tmp_path / "outside.c"
    outside.write_text("old\n", encoding="utf-8")
    spec = write_spec(
        tmp_path,
        [{"file": "../outside.c", "old": "old", "new": "new"}],
    )

    result = format_patch(FormatPatchOptions(src_root, spec, tmp_path / "candidate.patch"))

    assert result.exit_code == 1
    assert result.error_code == "file_outside_src_root"


def test_format_patch_rejects_symlink_escape(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    src_root.mkdir()
    outside = tmp_path / "outside.c"
    outside.write_text("old\n", encoding="utf-8")
    (src_root / "link.c").symlink_to(outside)
    spec = write_spec(
        tmp_path,
        [{"file": "link.c", "old": "old", "new": "new"}],
    )

    result = format_patch(FormatPatchOptions(src_root, spec, tmp_path / "candidate.patch"))

    assert result.exit_code == 1
    assert result.error_code == "file_outside_src_root"


def test_format_patch_rebuilds_headers_for_multiple_files(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    first = src_root / "src" / "one.c"
    second = src_root / "nested" / "two.c"
    first.parent.mkdir(parents=True)
    second.parent.mkdir(parents=True)
    first.write_text("one_old\n", encoding="utf-8")
    second.write_text("two_old\n", encoding="utf-8")
    spec = write_spec(
        tmp_path,
        [
            {"file": "src/one.c", "old": "one_old", "new": "one_new"},
            {"file": "nested/two.c", "old": "two_old", "new": "two_new"},
        ],
    )

    result = format_patch(FormatPatchOptions(src_root, spec, tmp_path / "candidate.patch"))

    assert result.exit_code == 0
    patch = (tmp_path / "candidate.patch").read_text(encoding="utf-8")
    assert "diff --git a/src/one.c b/src/one.c" in patch
    assert "--- a/src/one.c" in patch
    assert "+++ b/src/one.c" in patch
    assert "diff --git a/nested/two.c b/nested/two.c" in patch
    assert "--- a/nested/two.c" in patch
    assert "+++ b/nested/two.c" in patch


def test_format_patch_insert_after_generates_git_apply_compatible_patch(
    tmp_path: Path,
) -> None:
    src_root = tmp_path / "src"
    spec_file = src_root / "packaging" / "demo.spec"
    spec_file.parent.mkdir(parents=True)
    original = "\n".join(
        [
            "%build",
            "export CFLAGS=\"$CFLAGS -Wno-stringop-overflow\"",
            "%cmake .",
            "",
        ]
    )
    spec_file.write_text(original, encoding="utf-8")
    insert = "\n".join(
        [
            "%{?_toolchain:",
            "%if %{toolchain_is clang}",
            "CFLAGS=${CFLAGS/-Wno-stringop-overflow/}",
            "%endif",
            "}",
        ]
    )
    spec = write_spec(
        tmp_path,
        [
            {
                "operation": "insert_after",
                "file": "packaging/demo.spec",
                "line": 2,
                "anchor": "export CFLAGS=\"$CFLAGS -Wno-stringop-overflow\"",
                "insert": insert,
            }
        ],
    )
    output = tmp_path / "candidate.patch"

    result = format_patch(FormatPatchOptions(src_root, spec, output, check=True))

    assert result.exit_code == 0
    assert spec_file.read_text(encoding="utf-8") == original
    patch = output.read_text(encoding="utf-8")
    assert "diff --git a/packaging/demo.spec b/packaging/demo.spec" in patch
    assert " export CFLAGS=\"$CFLAGS -Wno-stringop-overflow\"" in patch
    assert "+%{?_toolchain:" in patch
    assert "+CFLAGS=${CFLAGS/-Wno-stringop-overflow/}" in patch
    subprocess.run(["git", "-C", str(src_root), "apply", "--check", str(output)], check=True)


def test_format_patch_insert_after_rejects_anchor_mismatch(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    spec_file = src_root / "packaging" / "demo.spec"
    spec_file.parent.mkdir(parents=True)
    spec_file.write_text("%build\n%cmake .\n", encoding="utf-8")
    spec = write_spec(
        tmp_path,
        [
            {
                "operation": "insert_after",
                "file": "packaging/demo.spec",
                "line": 2,
                "anchor": "export CFLAGS=\"$CFLAGS\"",
                "insert": "inserted\n",
            }
        ],
    )

    result = format_patch(FormatPatchOptions(src_root, spec, tmp_path / "candidate.patch"))

    assert result.exit_code == 1
    assert result.error_code == "anchor_not_found"


def test_format_patch_insert_after_rejects_out_of_range_line(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    spec_file = src_root / "packaging" / "demo.spec"
    spec_file.parent.mkdir(parents=True)
    spec_file.write_text("%build\n", encoding="utf-8")
    spec = write_spec(
        tmp_path,
        [
            {
                "operation": "insert_after",
                "file": "packaging/demo.spec",
                "line": 5,
                "anchor": "%build",
                "insert": "inserted\n",
            }
        ],
    )

    result = format_patch(FormatPatchOptions(src_root, spec, tmp_path / "candidate.patch"))

    assert result.exit_code == 1
    assert result.error_code == "insert_out_of_range"


def test_format_patch_cli_subcommand_does_not_break_context_cli(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    source = src_root / "src" / "demo.c"
    source.parent.mkdir(parents=True)
    source.write_text("old\n", encoding="utf-8")
    spec = write_spec(
        tmp_path,
        [{"file": "src/demo.c", "old": "old", "new": "new"}],
    )
    output = tmp_path / "candidate.patch"

    code = main(
        [
            "format-patch",
            "--src-root",
            str(src_root),
            "--edit-spec",
            str(spec),
            "--output",
            str(output),
            "--check",
        ]
    )

    assert code == 0
    assert output.exists()

    missing_evidence_code = main(
        ["--evidence", str(tmp_path / "missing.json"), "--output-dir", str(tmp_path / "out")]
    )
    assert missing_evidence_code == 3
