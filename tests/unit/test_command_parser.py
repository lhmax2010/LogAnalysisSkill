from pathlib import Path

from gbs_analyzer._utils.command_parser import (
    RSP_PATTERN,
    extract_relevant_flags,
    join_backslash_continuations,
    parse_command,
    read_rsp,
    shorten_argv,
)


def test_rsp_pattern_matches_plain_rsp() -> None:
    assert RSP_PATTERN.findall("gcc @objects.rsp -o app") == ["objects.rsp"]


def test_rsp_pattern_matches_linker_rsp() -> None:
    assert RSP_PATTERN.findall("gcc -Wl,@link.rsp -o app") == ["link.rsp"]


def test_join_backslash_continuations() -> None:
    command = "gcc -Iinclude \\\n    -DDEBUG \\\n    src/foo.c"
    assert join_backslash_continuations(command) == "gcc -Iinclude -DDEBUG src/foo.c"


def test_extract_relevant_flags_preserves_priority_flags() -> None:
    flags = extract_relevant_flags("-L/lib -lfoo -Werror -fPIC -shared -Iinc -DDEBUG foo.o")
    assert flags["libraries"] == ["-lfoo"]
    assert flags["library_paths"] == ["-L/lib"]
    assert flags["other_significant"] == ["-Werror", "-fPIC", "-shared"]
    assert flags["include_paths"] == ["-Iinc"]
    assert flags["defines"] == ["-DDEBUG"]
    assert flags["objects"] == ["foo.o"]


def test_extract_relevant_flags_truncates_include_and_defines() -> None:
    rsp = " ".join([f"-Iinc{i}" for i in range(12)] + [f"-DKEY{i}" for i in range(25)])
    flags = extract_relevant_flags(rsp)
    assert len(flags["include_paths"]) == 10
    assert len(flags["defines"]) == 20


def test_read_rsp_caps_raw_tokens(tmp_path: Path) -> None:
    rsp = tmp_path / "args.rsp"
    rsp.write_text(" ".join(f"token{i}" for i in range(300)), encoding="utf-8")
    assert len(read_rsp(rsp, max_rsp_tokens=50).split()) == 50


def test_shorten_argv_keeps_short_command() -> None:
    assert shorten_argv("gcc foo.c") == "gcc foo.c"


def test_shorten_argv_truncates_long_command() -> None:
    command = "gcc " + " ".join(f"file{i}.o" for i in range(80))
    shortened = shorten_argv(command, limit=80)
    assert len(shortened) <= 85
    assert "..." in shortened
    assert shortened.startswith("gcc")


def test_parse_command_expands_relative_rsp(tmp_path: Path) -> None:
    rsp = tmp_path / "link.rsp"
    rsp.write_text("-L/lib -lfoo main.o", encoding="utf-8")
    parsed = parse_command("gcc @link.rsp -o app", tmp_path)
    assert parsed["rsp_expanded"] == {
        "link.rsp": {
            "defines": [],
            "include_paths": [],
            "libraries": ["-lfoo"],
            "library_paths": ["-L/lib"],
            "objects": ["main.o"],
            "other_significant": [],
        }
    }
    assert parsed["command_degraded"] is False


def test_parse_command_expands_absolute_rsp(tmp_path: Path) -> None:
    rsp = tmp_path / "abs.rsp"
    rsp.write_text("-DDEBUG abs.o", encoding="utf-8")
    parsed = parse_command(f"gcc @{rsp}", tmp_path)
    assert parsed["rsp_expanded"][str(rsp)]["defines"] == ["-DDEBUG"]  # type: ignore[index]


def test_parse_command_marks_missing_rsp_degraded(tmp_path: Path) -> None:
    parsed = parse_command("gcc @missing.rsp -o app", tmp_path)
    assert parsed["rsp_expanded"] == {"missing.rsp": None}
    assert parsed["command_degraded"] is True


def test_parse_command_omits_large_argv_full(tmp_path: Path) -> None:
    parsed = parse_command("gcc " + "x" * 600, tmp_path)
    assert parsed["argv_full"] is None
    assert parsed["argv_short"].startswith("gcc")
