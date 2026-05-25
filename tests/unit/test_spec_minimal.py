from pathlib import Path

import pytest
from gbs_analyzer.tizen.spec_minimal import SpecMinimalParser


def write_spec(tmp_path: Path, text: str, name: str = "demo.spec") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def parser(tmp_path: Path, text: str, *, buildlog_text: str | None = None) -> SpecMinimalParser:
    return SpecMinimalParser(write_spec(tmp_path, text), buildlog_text=buildlog_text)


def test_find_spec_file_prefers_exact_package_match(tmp_path: Path) -> None:
    write_spec(tmp_path, "Name: other\n", "other.spec")
    exact = write_spec(tmp_path, "Name: demo\n", "demo.spec")
    assert SpecMinimalParser.find_spec_file("demo", tmp_path) == exact


def test_find_spec_file_accepts_single_fallback(tmp_path: Path) -> None:
    only = write_spec(tmp_path, "Name: renamed\n", "renamed.spec")
    assert SpecMinimalParser.find_spec_file("demo", tmp_path) == only


def test_find_spec_file_rejects_missing_root(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="src_root"):
        SpecMinimalParser.find_spec_file("demo", tmp_path / "missing")


def test_find_spec_file_rejects_ambiguous_specs(tmp_path: Path) -> None:
    write_spec(tmp_path, "Name: one\n", "one.spec")
    write_spec(tmp_path, "Name: two\n", "two.spec")
    with pytest.raises(ValueError, match="ambiguous"):
        SpecMinimalParser.find_spec_file("demo", tmp_path)


def test_extract_buildrequires_multiple_lines_and_commas(tmp_path: Path) -> None:
    spec = parser(
        tmp_path,
        """
Name: demo
BuildRequires: gcc, make
BuildRequires: pkgconfig(foo) >= 1.0
""",
    )
    assert spec.extract_buildrequires() == ["gcc", "make", "pkgconfig(foo) >= 1.0"]


def test_extract_buildrequires_joins_continuations(tmp_path: Path) -> None:
    spec = parser(
        tmp_path,
        """
Name: demo
BuildRequires: gcc, \\
  make
""",
    )
    assert spec.extract_buildrequires() == ["gcc", "make"]


def test_extract_buildrequires_ignores_comments(tmp_path: Path) -> None:
    spec = parser(
        tmp_path,
        """
# BuildRequires: ignored
BuildRequires: gcc # host compiler
""",
    )
    assert spec.extract_buildrequires() == ["gcc"]


def test_extract_patches_preserves_raw_tags(tmp_path: Path) -> None:
    spec = parser(
        tmp_path,
        """
Patch0: fix-build.patch
Patch12: backport.patch
Patch: unnumbered.patch
""",
    )
    assert spec.extract_patches() == [
        {"tag": "Patch0", "index": 0, "value": "fix-build.patch"},
        {"tag": "Patch12", "index": 12, "value": "backport.patch"},
        {"tag": "Patch", "index": None, "value": "unnumbered.patch"},
    ]


def test_extract_sources_preserves_raw_tags(tmp_path: Path) -> None:
    spec = parser(
        tmp_path,
        """
Source0: demo.tar.gz
Source10: config.ini
""",
    )
    assert spec.extract_sources() == [
        {"tag": "Source0", "index": 0, "value": "demo.tar.gz"},
        {"tag": "Source10", "index": 10, "value": "config.ini"},
    ]


def test_extract_section_accepts_name_with_or_without_percent(tmp_path: Path) -> None:
    spec = parser(
        tmp_path,
        """
%prep
%setup -q

%build
make all
""",
    )
    assert spec.extract_section("prep") == "%setup -q"
    assert spec.extract_section("%build") == "make all"


def test_extract_section_returns_empty_for_missing_section(tmp_path: Path) -> None:
    assert parser(tmp_path, "Name: demo\n").extract_section("%build") == ""


def test_extract_section_stops_at_next_top_level_section(tmp_path: Path) -> None:
    spec = parser(
        tmp_path,
        """
%build
make
%install
make install
""",
    )
    assert spec.extract_section("%build") == "make"


def test_failure_context_finds_last_command_output_in_phase(tmp_path: Path) -> None:
    spec = parser(
        tmp_path,
        """
%build
cmake .
make
""",
        buildlog_text=(
            "+ %build\n"
            "+ cmake .\n"
            "-- configured\n"
            "+ make\n"
            "src/foo.c:1: error: nope\n"
            "make: *** [all] Error 2\n"
            "+ %install\n"
        ),
    )
    context = spec.extract_section_failure_context("%build")
    assert context["last_command"] == "make"
    assert context["last_command_output"] == "src/foo.c:1: error: nope\nmake: *** [all] Error 2"
    assert context["spec_section_text"] == "cmake .\nmake"


def test_failure_context_stops_output_at_next_command(tmp_path: Path) -> None:
    spec = parser(
        tmp_path,
        "%build\nmake\n",
        buildlog_text="+ %build\n+ make prep\nok\n+ make all\nfailed\n",
    )
    context = spec.extract_section_failure_context("%build")
    assert context["last_command"] == "make all"
    assert context["last_command_output"] == "failed"


def test_failure_context_without_buildlog_keeps_spec_section(tmp_path: Path) -> None:
    context = parser(tmp_path, "%build\nmake\n").extract_section_failure_context("%build")
    assert context == {
        "last_command": "",
        "last_command_output": "",
        "spec_section_text": "make",
    }


def test_parse_status_is_partial_without_warnings(tmp_path: Path) -> None:
    status = parser(tmp_path, "Name: demo\n").get_parse_status()
    assert status == {
        "macro_expanded": False,
        "condition_evaluated": False,
        "subpackage_resolved": False,
        "confidence": "partial",
        "warnings": [],
    }


def test_parse_status_reports_uncertainty_warnings(tmp_path: Path) -> None:
    status = parser(
        tmp_path,
        """
Name: %{name}
%if 0%{?tizen}
BuildRequires: gcc
%endif
%package devel
""",
    ).get_parse_status()
    assert status["warnings"] == [
        "macros_present_not_expanded",
        "conditionals_present_not_evaluated",
        "subpackages_present_not_resolved",
    ]
