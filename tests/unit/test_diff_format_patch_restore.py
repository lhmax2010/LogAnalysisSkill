from __future__ import annotations

import io
import json
import os
import subprocess

import pytest
from tizen_build_verify.edit_spec_guard import validate_edit_spec
from tizen_campaign_core.diff_to_edit_spec import DiffUnsupported, convert
from tizen_campaign_repair.diff_cli import main


@pytest.fixture
def format_patch(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home), GIT_CONFIG_NOSYSTEM="1",
               GIT_CONFIG_GLOBAL=os.devnull, GIT_AUTHOR_NAME="Offline Test",
               GIT_AUTHOR_EMAIL="offline@example.invalid", GIT_COMMITTER_NAME="Offline Test",
               GIT_COMMITTER_EMAIL="offline@example.invalid")

    def git(*args):
        return subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgSign=false",
             "-C", str(repo), *args], env=env, check=True, capture_output=True,
        ).stdout

    git("init", "--quiet")
    originals = {"one.c": "before\nold\nafter\n", "two.c": "first\nold\nlast\n"}
    for name, text in originals.items():
        (repo / name).write_text(text, encoding="utf-8")
    git("add", ".")
    git("commit", "--quiet", "-m", "Base")

    def generate(count):
        names = list(originals)[:count]
        for name in names:
            (repo / name).write_text(originals[name].replace("old", "new"), encoding="utf-8")
        git("add", ".")
        git("commit", "--quiet", "--signoff", "-m", "Fix offline fixture")
        patch = git("format-patch", "--stdout", "-1").decode("utf-8")
        for name, text in originals.items():
            (repo / name).write_text(text, encoding="utf-8")
        return repo, patch, names, originals

    return generate


@pytest.mark.parametrize("count", [1, 2])
@pytest.mark.parametrize("ending", ["original", "no_blank", "extra_blanks", "version_at_eof"])
def test_actual_format_patch_and_real_guard(format_patch, tmp_path, count, ending):
    root, patch, names, originals = format_patch(count)
    assert patch.startswith("From ")
    assert "Subject: [PATCH] Fix offline fixture\n" in patch
    assert "Signed-off-by: Offline Test <offline@example.invalid>\n" in patch
    assert "\n-- \n" in patch
    if ending == "no_blank":
        patch = patch.rstrip("\n") + "\n"
    elif ending == "extra_blanks":
        patch += "\n\n"
    elif ending == "version_at_eof":
        patch = patch.rstrip("\n")
    spec = convert(patch, root, "offline-fix")
    validate_edit_spec(spec, str(root))
    assert [edit["file"] for edit in spec["edits"]] == names
    for edit in spec["edits"]:
        assert edit["old"] == originals[edit["file"]]
        assert edit["new"] == originals[edit["file"]].replace("old", "new")
    path, output = tmp_path / "input.patch", tmp_path / "edit.json"
    path.write_bytes(patch.encode("utf-8"))
    stdout = io.StringIO()
    assert main(["--diff", str(path), "--src-root", str(root), "--output", str(output),
                 "--patch-name", "offline-fix"], stdout=stdout) == 0
    assert json.loads(output.read_text()) == spec
    validate_edit_spec(json.loads(output.read_text()), str(root))
    assert {name: (root / name).read_text() for name in originals} == originals


@pytest.mark.parametrize("version", ["2.39.2", "2.39.2.windows.1", "2.39.2-rc1"])
def test_git_version_tokens_accepted(format_patch, version):
    root, patch, _, _ = format_patch(1)
    body, _ = patch.rsplit("-- \n", 1)
    spec = convert(body + "-- \n" + version + "\n\n", root, "offline-fix")
    validate_edit_spec(spec, str(root))


@pytest.mark.parametrize("version", [
    "2 arbitrary payload", "2.39.2 arbitrary payload", "2.39.2 ",
    "2.39.2\tpayload", "2.39.2\rpayload", "2.39.2\x1bpayload",
    "2.39.2\x7fpayload", "2.39.2\vpayload", "2.39.2+payload",
    "2", "2windows.1",
])
def test_invalid_version_tokens_rejected(format_patch, version):
    root, patch, _, _ = format_patch(1)
    body, _ = patch.rsplit("-- \n", 1)
    with pytest.raises(DiffUnsupported, match="^unparsed_patch_content$"):
        convert(body + "-- \n" + version + "\n", root, "offline-fix")


@pytest.mark.parametrize("placement", [
    "after_signature", "between_files", "before_hunk", "before_headers",
    "between_hunks", "missing_version", "empty_version", "non_version",
    "extra_version", "separator_crlf", "blank_before_signature",
])
def test_signature_outside_terminal_position_rejected(format_patch, placement):
    root, patch, _, _ = format_patch(2)
    body, signature = patch.rsplit("-- \n", 1)
    footer = "-- \n" + signature
    if placement == "after_signature":
        patch += "extra content\n"
    elif placement == "between_files":
        position = body.index("diff --git ", body.index("diff --git ") + 1)
        patch = body[:position] + footer + body[position:]
    elif placement == "before_hunk":
        position = body.index("@@ ")
        patch = body[:position] + footer + body[position:]
    elif placement == "before_headers":
        patch = footer + body
    elif placement == "between_hunks":
        patch += "@@ -2 +2 @@\n-old\n+new\n"
    elif placement == "missing_version":
        patch = body + "-- \n"
    elif placement == "empty_version":
        patch = body + "-- \n\n"
    elif placement == "non_version":
        patch = body + "-- \nextra content\n"
    elif placement == "extra_version":
        patch += "2.39.2\n"
    elif placement == "separator_crlf":
        patch = body + "-- \r\n" + signature
    else:
        patch = body + "\n" + footer
    with pytest.raises(DiffUnsupported, match="^unparsed_patch_content$"):
        convert(patch, root, "offline-fix")


@pytest.mark.parametrize("existing_output", [False, True])
def test_latin1_diff_is_unsupported_encoding(format_patch, tmp_path, existing_output):
    root, patch, _, originals = format_patch(1)
    path, output = tmp_path / "latin1.patch", tmp_path / "edit.json"
    path.write_bytes(patch.replace("Fix offline fixture", "Fix caf\u00e9").encode("latin-1"))
    if existing_output:
        output.write_bytes(b"existing output\n")
    stdout = io.StringIO()
    assert main(["--diff", str(path), "--src-root", str(root), "--output", str(output),
                 "--patch-name", "offline-fix"], stdout=stdout) == 4
    assert json.loads(stdout.getvalue()) == {
        "error_code": "DIFF_CONVERT_UNSUPPORTED", "reason": "unsupported_encoding",
    }
    if existing_output:
        assert output.read_bytes() == b"existing output\n"
    else:
        assert not output.exists()
    assert not list(tmp_path.glob(".edit-spec-*"))
    assert {name: (root / name).read_text() for name in originals} == originals
