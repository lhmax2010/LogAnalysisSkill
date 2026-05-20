import subprocess
from pathlib import Path

import pytest

from gbs_workflow.suggesters.base import SuggesterBase
from gbs_workflow.suggesters.depsolve import (
    DepsolveSuggester,
    add_buildrequires_line,
    parse_missing_dependency,
)
from gbs_workflow.suggesters.registry import DEFAULT_SUGGESTERS


def packet(message: str, *, kind: str = "depsolve") -> dict[str, object]:
    return {
        "package": "ffmpeg",
        "primary_error": {
            "kind": kind,
            "message": message,
        },
    }


def write_spec(root: Path, text: str) -> Path:
    spec = root / "packaging" / "ffmpeg.spec"
    spec.parent.mkdir(parents=True)
    spec.write_text(text, encoding="utf-8")
    return spec


def test_suggester_base_contract_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        SuggesterBase()  # type: ignore[abstract]


def test_registry_only_registers_depsolve_in_bw_m2() -> None:
    assert [item.__class__.__name__ for item in DEFAULT_SUGGESTERS] == ["DepsolveSuggester"]


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("nothing provides pkgconfig(libssl)", "pkgconfig(libssl)"),
        ("nothing provides libssl-devel", "libssl-devel"),
        ("nothing provides pkgconfig(foo) needed by ffmpeg", "pkgconfig(foo)"),
    ],
)
def test_parse_missing_dependency_formats(message: str, expected: str) -> None:
    assert parse_missing_dependency(packet(message)) == expected


def test_depsolve_matches_primary_error_kind_only() -> None:
    suggester = DepsolveSuggester()

    assert suggester.matches(packet("not parseable")) is True
    assert suggester.matches(packet("nothing provides pkgconfig(foo)", kind="compiler")) is False


def test_generate_returns_empty_for_unparseable_message(tmp_path: Path) -> None:
    write_spec(tmp_path, "Name: ffmpeg\nBuildRequires:  gcc\n%prep\n")

    assert DepsolveSuggester().generate(packet("dependency solver failed"), tmp_path) == []


def test_add_buildrequires_line_after_existing_block() -> None:
    updated = add_buildrequires_line(
        "Name: ffmpeg\nBuildRequires:  gcc\nVersion: 1\n%prep\n",
        "pkgconfig(libssl)",
    )

    assert updated == (
        "Name: ffmpeg\n"
        "BuildRequires:  gcc\n"
        "BuildRequires:  pkgconfig(libssl)\n"
        "Version: 1\n"
        "%prep\n"
    )


def test_add_buildrequires_line_before_first_section_when_no_existing_block() -> None:
    updated = add_buildrequires_line("Name: ffmpeg\nVersion: 1\n%prep\n", "pkgconfig(foo)")

    assert updated == "Name: ffmpeg\nVersion: 1\nBuildRequires:  pkgconfig(foo)\n%prep\n"


def test_depsolve_generate_writes_git_apply_compatible_patch(tmp_path: Path) -> None:
    write_spec(
        tmp_path,
        "Name: ffmpeg\nVersion: 1\nBuildRequires:  gcc\n%prep\n%setup -q\n",
    )

    suggestions = DepsolveSuggester().generate(
        packet("nothing provides pkgconfig(nonexistent-pkg-xxxyzz)"),
        tmp_path,
    )

    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert suggestion.suggester == "depsolve"
    assert suggestion.confidence == "medium"
    assert suggestion.target_files == ["packaging/ffmpeg.spec"]
    assert suggestion.patch_content is not None
    assert "BuildRequires:  pkgconfig(nonexistent-pkg-xxxyzz)" in suggestion.patch_content

    patch_path = tmp_path / "suggestion.patch"
    patch_path.write_text(suggestion.patch_content, encoding="utf-8")
    subprocess.run(["git", "apply", "--check", patch_path], cwd=tmp_path, check=True)
