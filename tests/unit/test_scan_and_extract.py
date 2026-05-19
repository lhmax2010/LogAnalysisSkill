import gzip
from pathlib import Path

import pytest

from gbs_analyzer.scan_and_extract import (
    BuildLogScanner,
    _iter_log_lines,
    _tool_from_command,
    scan_buildlog,
)
from gbs_analyzer.tracing import TraceLogger


def write_log(tmp_path: Path, text: str, name: str = "buildlog") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_scan_empty_log(tmp_path: Path) -> None:
    path = write_log(tmp_path, "")
    result = scan_buildlog(path)
    assert result.events == []
    assert result.commands == []
    assert result.failed_phase is None


def test_detects_phase_marker(tmp_path: Path) -> None:
    path = write_log(tmp_path, "+ %build\n")
    result = scan_buildlog(path)
    assert result.phases == [{"phase": "%build", "line_no": 1, "raw_offset": 0}]


def test_normalizes_gbs_timestamp_and_ansi(tmp_path: Path) -> None:
    raw_text = "[  213s] \x1b[31m+ gcc -c src/foo.c\x1b[0m"
    path = write_log(tmp_path, f"{raw_text}\n")

    line = next(_iter_log_lines(path))

    assert line.raw_text == raw_text
    assert line.text == "+ gcc -c src/foo.c"
    assert line.gbs_seconds == 213


@pytest.mark.parametrize("phase", ["%prep", "%build", "%install", "%check"])
def test_detects_rpm_executing_phase_marker(tmp_path: Path, phase: str) -> None:
    path = write_log(tmp_path, f"[  194s] Executing({phase}): /bin/sh -e /tmp/rpm\n")
    result = scan_buildlog(path)
    assert result.phases == [{"phase": phase, "line_no": 1, "raw_offset": 0}]


def test_does_not_generalize_rpm_executing_phase_marker(tmp_path: Path) -> None:
    path = write_log(tmp_path, "[  194s] Executing(%clean): /bin/sh -e /tmp/rpm\n")
    assert scan_buildlog(path).phases == []


def test_detects_command_boundary(tmp_path: Path) -> None:
    path = write_log(tmp_path, "+ %build\n+ gcc -c src/foo.c\n")
    result = scan_buildlog(path)
    assert len(result.commands) == 1
    assert result.commands[0].id == "C001"
    assert result.commands[0].phase == "%build"
    assert result.commands[0].argv_short == "gcc -c src/foo.c"


def test_joins_multiline_command(tmp_path: Path) -> None:
    path = write_log(tmp_path, "+ %build\n+ gcc \\\n  -Iinclude \\\n  src/foo.c\n")
    result = scan_buildlog(path)
    assert result.commands[0].argv_short == "gcc -Iinclude src/foo.c"


def test_expands_command_rsp(tmp_path: Path) -> None:
    (tmp_path / "args.rsp").write_text("-Iinc -DDEBUG foo.o", encoding="utf-8")
    path = write_log(tmp_path, "+ %build\n+ gcc @args.rsp -o app\n")
    result = scan_buildlog(path, cwd=tmp_path)
    assert result.commands[0].rsp_expanded["args.rsp"]["defines"] == ["-DDEBUG"]


def test_expands_rsp_inside_multiline_command(tmp_path: Path) -> None:
    (tmp_path / "args.rsp").write_text("-Iinc -DDEBUG foo.o", encoding="utf-8")
    path = write_log(tmp_path, "+ %build\n+ gcc \\\n  @args.rsp \\\n  -o app\n")
    result = scan_buildlog(path, cwd=tmp_path)
    command = result.commands[0]
    assert command.argv_short == "gcc @args.rsp -o app"
    assert command.rsp_expanded["args.rsp"]["include_paths"] == ["-Iinc"]


def test_missing_rsp_marks_scan_degraded(tmp_path: Path) -> None:
    path = write_log(tmp_path, "+ %build\n+ gcc @missing.rsp -o app\n")
    result = scan_buildlog(path, cwd=tmp_path)
    assert result.commands[0].command_degraded is True
    assert result.degraded_reasons == ["command_C001_rsp_unavailable"]


def test_detects_compiler_diagnostic(tmp_path: Path) -> None:
    path = write_log(tmp_path, "+ %build\n+ gcc -c src/foo.c\nsrc/foo.c:10:5: error: nope\n")
    result = scan_buildlog(path)
    event = result.events[0]
    assert event.kind == "compiler"
    assert event.file == "src/foo.c"
    assert event.line == 10
    assert event.column == 5
    assert event.message == "nope"
    assert event.command_id == "C001"
    assert event.details == {"is_assembler": False, "tool": "gcc"}


def test_detects_fatal_compiler_diagnostic_as_error(tmp_path: Path) -> None:
    path = write_log(tmp_path, "src/foo.cc:3: fatal error: missing.h: No such file\n")
    event = scan_buildlog(path).events[0]
    assert event.kind == "compiler"
    assert event.severity == "error"


def test_detects_assembler_diagnostic_as_compiler(tmp_path: Path) -> None:
    path = write_log(
        tmp_path,
        "\n".join(
            [
                "+ %build",
                "+ arm-linux-gnueabihf-as -o libavcodec/arm/h264cmc_neon.o",
                "libavcodec/arm/h264cmc_neon.S:43: Error: bad instruction `sasdd r1,r1,r3'",
                "",
            ]
        ),
    )

    event = scan_buildlog(path).events[0]

    assert event.kind == "compiler"
    assert event.severity == "error"
    assert event.file == "libavcodec/arm/h264cmc_neon.S"
    assert event.line == 43
    assert event.message == "bad instruction `sasdd r1,r1,r3'"
    assert event.details == {
        "is_assembler": True,
        "tool": "arm-linux-gnueabihf-as",
    }


def test_tool_from_command_handles_bad_or_empty_argv() -> None:
    assert _tool_from_command('"unterminated') == '"unterminated'
    assert _tool_from_command("") is None


def test_detects_linker_undefined_reference(tmp_path: Path) -> None:
    path = write_log(tmp_path, "foo.o: undefined reference to `bar'\n")
    event = scan_buildlog(path).events[0]
    assert event.kind == "linker_undef"
    assert event.details == {"symbol": "bar"}


def test_detects_linker_missing_lib(tmp_path: Path) -> None:
    path = write_log(tmp_path, "/usr/bin/ld: cannot find -lfoo\n")
    event = scan_buildlog(path).events[0]
    assert event.kind == "linker_missing"
    assert event.details == {"library": "foo"}


def test_detects_patch_failed(tmp_path: Path) -> None:
    path = write_log(tmp_path, "Patch #12 (fix.patch) failed\n")
    event = scan_buildlog(path).events[0]
    assert event.kind == "patch"
    assert event.details == {"num": "12"}


def test_detects_patch_hunk_failed(tmp_path: Path) -> None:
    path = write_log(tmp_path, "Hunk #2 FAILED at 144.\n")
    event = scan_buildlog(path).events[0]
    assert event.kind == "patch"
    assert event.details == {"num": "2"}


def test_detects_real_patch_context_failure_lines(tmp_path: Path) -> None:
    path = write_log(
        tmp_path,
        "can't find file to patch at input line 3\n"
        "1 out of 1 hunk ignored\n",
    )
    result = scan_buildlog(path)

    assert [event.kind for event in result.events] == ["patch", "patch"]
    assert result.events[0].message == (
        "error: patch failed: can't find file to patch at input line 3"
    )
    assert result.events[0].details == {"line": "3"}
    assert result.events[1].message == "Hunk #1 FAILED: 1 out of 1 hunk ignored"
    assert result.events[1].details == {"num": "1", "total": "1"}


def test_does_not_double_canonicalize_hunk_ignored_message(tmp_path: Path) -> None:
    path = write_log(tmp_path, "Hunk #1 FAILED: 1 out of 1 hunk ignored\n")
    event = scan_buildlog(path).events[0]

    assert event.kind == "patch"
    assert event.message == "Hunk #1 FAILED: 1 out of 1 hunk ignored"


def test_patch_failure_parents_prep_bad_exit_status(tmp_path: Path) -> None:
    path = write_log(
        tmp_path,
        "\n".join(
            [
                "Executing(%prep): /bin/sh -e /tmp/rpm",
                "+ /bin/patch --no-backup-if-mismatch -p1",
                "can't find file to patch at input line 3",
                "error: Bad exit status from /var/tmp/rpm-tmp.abc (%prep)",
                "",
            ]
        ),
    )

    result = scan_buildlog(path)

    assert [event.kind for event in result.events] == ["patch", "rpm_phase"]
    assert result.events[1].parent == result.events[0].id
    assert result.events[1].details == {
        "phase": "%prep",
        "derived_from": "patch_failed",
    }
    assert result.failed_phase == "%prep"


def test_detects_depsolve_failure(tmp_path: Path) -> None:
    path = write_log(tmp_path, "nothing provides pkgconfig(foo) needed by bar\n")
    assert scan_buildlog(path).events[0].kind == "depsolve"


def test_detects_install_missing(tmp_path: Path) -> None:
    path = write_log(tmp_path, "File not found: /home/abuild/rpmbuild/BUILDROOT/foo\n")
    assert scan_buildlog(path).events[0].kind == "install_missing"


def test_detects_werror(tmp_path: Path) -> None:
    path = write_log(tmp_path, "cc1: all warnings being treated as errors\n")
    assert scan_buildlog(path).events[0].kind == "werror"


def test_detects_rpm_phase_failure(tmp_path: Path) -> None:
    path = write_log(tmp_path, "error: Bad exit status from /var/tmp/rpm-tmp.abc (%build)\n")
    event = scan_buildlog(path).events[0]
    assert event.kind == "rpm_phase"
    assert event.details == {"phase": "%build"}


def test_real_gbs_prefix_recovers_command_and_failed_phase(tmp_path: Path) -> None:
    path = write_log(
        tmp_path,
        "\n".join(
            [
                "[  208s] Executing(%build): /bin/sh -e /var/tmp/rpm-tmp.abc",
                "[  209s] + /bin/make -j40",
                "[  213s] libavcodec/arm/h264cmc_neon.S:43: "
                "Error: bad instruction `sasdd r1,r1,r3'",
                "[  217s] error: Bad exit status from /var/tmp/rpm-tmp.abc (%build)",
                "",
            ]
        ),
    )

    result = scan_buildlog(path)

    assert len(result.commands) == 1
    assert result.commands[0].phase == "%build"
    assert result.failed_phase == "%build"


def test_detects_spec_script_error(tmp_path: Path) -> None:
    path = write_log(tmp_path, "spec file parse error: unexpected %endif\n")
    assert scan_buildlog(path).events[0].kind == "spec_script"


def test_detects_raw_error(tmp_path: Path) -> None:
    path = write_log(tmp_path, "error: something strange happened\n")
    assert scan_buildlog(path).events[0].kind == "raw_error"


def test_associates_make_cascade_with_compiler_event(tmp_path: Path) -> None:
    path = write_log(
        tmp_path,
        "\n".join(
            [
                "+ %build",
                "+ gcc -c src/foo.cc",
                "src/foo.cc:10:1: error: nope",
                "make[2]: *** [src/foo.o] Error 1",
                "",
            ]
        ),
    )
    result = scan_buildlog(path)
    assert result.events[1].kind == "make_cascade"
    assert result.events[1].parent == "E001"


def test_make_cascade_without_unique_parent_is_unlinked(tmp_path: Path) -> None:
    path = write_log(tmp_path, "make: *** [bar.o] Error 2\n")
    event = scan_buildlog(path).events[0]
    assert event.kind == "make_cascade"
    assert event.parent is None


def test_failed_phase_uses_current_phase(tmp_path: Path) -> None:
    path = write_log(tmp_path, "+ %install\nFile not found: /missing\n")
    assert scan_buildlog(path).failed_phase == "%install"


def test_scan_gzip_log(tmp_path: Path) -> None:
    path = tmp_path / "buildlog.gz"
    with gzip.open(path, "wt", encoding="utf-8") as file:
        file.write("+ %build\nsrc/foo.c:1:1: error: nope\n")
    result = scan_buildlog(path)
    assert result.is_gzip is True
    assert result.events[0].kind == "compiler"


def test_corrupt_gzip_raises(tmp_path: Path) -> None:
    path = tmp_path / "buildlog.gz"
    path.write_bytes(b"not actually gzip")

    with pytest.raises((gzip.BadGzipFile, EOFError, OSError)):
        scan_buildlog(path)


def test_result_as_dict_contains_commands_and_events(tmp_path: Path) -> None:
    path = write_log(tmp_path, "+ %build\n+ gcc -c src/foo.c\nsrc/foo.c:1:1: error: nope\n")
    data = scan_buildlog(path).as_dict()
    assert data["schema_version"] == "scan_result/v1"
    assert len(data["commands"]) == 1
    assert len(data["events"]) == 1


def test_scanner_emits_trace_events(tmp_path: Path) -> None:
    path = write_log(tmp_path, "+ %build\nsrc/foo.c:1:1: error: nope\n")
    with TraceLogger(tmp_path / "trace") as logger:
        BuildLogScanner(trace_logger=logger).scan(path)

    trace = (tmp_path / "trace" / "trace.jsonl").read_text(encoding="utf-8")
    assert "phase_marker_detected" in trace
    assert "diagnostic_detected" in trace
    assert "raw_text" in trace
    assert "text" in trace
    assert "scan_completed" in trace
