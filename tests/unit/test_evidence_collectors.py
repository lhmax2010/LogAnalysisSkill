import json
from pathlib import Path
from subprocess import CalledProcessError

import pytest

from gbs_analyzer.evidence.compile import CompileEvidenceCollector
from gbs_analyzer.evidence.deps import DepsEvidenceCollector
from gbs_analyzer.evidence.link import LinkEvidenceCollector
from gbs_analyzer.evidence.router import collector_for_candidate
from gbs_analyzer.evidence.spec import SpecEvidenceCollector


def write_source_tree(tmp_path: Path) -> Path:
    src = tmp_path / "srcroot"
    (src / "src").mkdir(parents=True)
    (src / "include").mkdir()
    (src / "src" / "foo.c").write_text(
        "int helper(void) {\n"
        "  return 0;\n"
        "}\n"
        "int main(void) {\n"
        "  return missing_symbol();\n"
        "}\n",
        encoding="utf-8",
    )
    (src / "include" / "foo.h").write_text("int missing_symbol(void);\n", encoding="utf-8")
    return src


def write_plain_source(tmp_path: Path) -> Path:
    src = tmp_path / "plain"
    (src / "src").mkdir(parents=True)
    (src / "src" / "foo.c").write_text(
        "\n".join(f"plain line {index}" for index in range(1, 80)),
        encoding="utf-8",
    )
    return src


def write_link_source_tree(tmp_path: Path) -> Path:
    src = tmp_path / "linksrc"
    (src / "src").mkdir(parents=True)
    (src / "src" / "foo.c").write_text(
        "int missing_symbol(void) {\n"
        "  return 2;\n"
        "}\n",
        encoding="utf-8",
    )
    return src


def write_spec(tmp_path: Path) -> Path:
    spec = tmp_path / "demo.spec"
    spec.write_text(
        "Name: demo\n"
        "BuildRequires: gcc, make\n"
        "Source0: demo.tar.gz\n"
        "Patch0: fix.patch\n"
        "%build\n"
        "make\n",
        encoding="utf-8",
    )
    return spec


def write_buildlog(tmp_path: Path) -> Path:
    buildlog = tmp_path / "buildlog"
    buildlog.write_text("+ %build\n+ make\nerror: spec failed\n", encoding="utf-8")
    return buildlog


def scan_data() -> dict[str, object]:
    return {
        "buildlog_path": "profile.tizen/buildlog",
        "failed_phase": "%build",
        "commands": [
            {"id": "C001", "phase": "%build", "argv_short": "gcc -c src/foo.c"},
            {"id": "C002", "phase": "%build", "argv_short": "gcc foo.o -lmissing"},
        ],
        "events": [
            {
                "id": "E001",
                "kind": "compiler",
                "message": "use of undeclared identifier 'missing_symbol'",
                "severity": "error",
                "file": "src/foo.c",
                "line": 5,
                "phase": "%build",
                "command_id": "C001",
            },
            {
                "id": "E002",
                "kind": "linker_undef",
                "message": "undefined reference to `missing_symbol'",
                "severity": "error",
                "phase": "%build",
                "command_id": "C002",
                "details": {"symbol": "missing_symbol"},
            },
            {
                "id": "E003",
                "kind": "linker_missing",
                "message": "/usr/bin/ld: cannot find -lmissing",
                "severity": "error",
                "phase": "%build",
                "command_id": "C002",
                "details": {"library": "missing"},
            },
            {
                "id": "E004",
                "kind": "spec_script",
                "message": "spec file error",
                "severity": "error",
                "phase": "%build",
                "command_id": "C001",
            },
            {
                "id": "E005",
                "kind": "depsolve",
                "message": "nothing provides libfoo needed by demo-1.0",
                "severity": "error",
                "phase": None,
                "command_id": None,
            },
            {"id": "E006", "kind": "patch", "message": "Patch failed"},
        ],
    }


def candidate(event_id: str, kind: str) -> dict[str, str]:
    return {"event_id": event_id, "kind": kind}


def ctags_runner(_: Path) -> str:
    return json.dumps({"name": "main", "line": 4}) + "\n"


def failing_ctags(_: Path) -> str:
    raise CalledProcessError(1, "ctags")


def missing_ctags(_: Path) -> str:
    raise OSError("ctags missing")


def test_compile_collector_level1_contains_error_and_command(tmp_path: Path) -> None:
    src = write_source_tree(tmp_path)
    evidence = CompileEvidenceCollector(scan_data(), src_root=src).collect(
        candidate("E001", "compiler"),
        300,
    )
    assert evidence.level == 1
    assert evidence.contains_all(["primary_error", "command_summary"])
    assert "source_snippet" not in evidence.data


def test_compile_collector_uses_ctags_when_available(tmp_path: Path) -> None:
    src = write_source_tree(tmp_path)
    evidence = CompileEvidenceCollector(
        scan_data(),
        src_root=src,
        ctags_runner=ctags_runner,
    ).collect(candidate("E001", "compiler"), 600)
    assert evidence.data["source_snippet"]["extraction_method"] == "ctags"
    assert evidence.degraded is False


def test_compile_collector_falls_back_to_regex_when_ctags_unavailable(
    tmp_path: Path,
) -> None:
    src = write_source_tree(tmp_path)
    evidence = CompileEvidenceCollector(
        scan_data(),
        src_root=src,
        ctags_runner=failing_ctags,
    ).collect(candidate("E001", "compiler"), 600)
    assert evidence.data["source_snippet"]["extraction_method"] == "regex_brace"


def test_compile_collector_falls_back_to_window_when_regex_cannot_match(
    tmp_path: Path,
) -> None:
    src = write_plain_source(tmp_path)
    evidence = CompileEvidenceCollector(
        scan_data(),
        src_root=src,
        ctags_runner=missing_ctags,
    ).collect(candidate("E001", "compiler"), 600)
    assert evidence.data["source_snippet"]["extraction_method"] == "line_window"
    assert evidence.degraded is True


def test_compile_collector_marks_missing_source_degraded(tmp_path: Path) -> None:
    evidence = CompileEvidenceCollector(scan_data(), src_root=tmp_path).collect(
        candidate("E001", "compiler"),
        600,
    )
    assert evidence.degraded is True
    assert evidence.warnings == ["source_file_unavailable"]


def test_compile_collector_level3_adds_header_declarations(tmp_path: Path) -> None:
    src = write_source_tree(tmp_path)
    evidence = CompileEvidenceCollector(scan_data(), src_root=src).collect(
        candidate("E001", "compiler"),
        900,
    )
    assert evidence.contains_all(["header_declarations"])
    assert evidence.data["header_declarations"][0]["text"] == "int missing_symbol(void);"


def test_link_collector_level1_captures_symbol_and_command() -> None:
    evidence = LinkEvidenceCollector(scan_data()).collect(candidate("E002", "linker_undef"), 300)
    assert evidence.data["symbol"] == "missing_symbol"
    assert evidence.contains_all(["link_command"])


def test_link_collector_captures_missing_library() -> None:
    evidence = LinkEvidenceCollector(scan_data()).collect(candidate("E003", "linker_missing"), 300)
    assert evidence.data["library"] == "missing"


def test_link_collector_level2_adds_spec_buildrequires(tmp_path: Path) -> None:
    spec = write_spec(tmp_path)
    evidence = LinkEvidenceCollector(scan_data(), spec_path=spec).collect(
        candidate("E002", "linker_undef"),
        600,
    )
    assert evidence.data["spec_buildrequires"] == ["gcc", "make"]


def test_link_collector_level3_symbol_context_uses_ctags(tmp_path: Path) -> None:
    src = write_source_tree(tmp_path)
    evidence = LinkEvidenceCollector(
        scan_data(),
        src_root=src,
        ctags_runner=ctags_runner,
    ).collect(candidate("E002", "linker_undef"), 900)
    assert evidence.data["symbol_context"]["extraction_method"] == "ctags"


def test_link_collector_falls_back_to_regex_when_ctags_unavailable(
    tmp_path: Path,
) -> None:
    src = write_link_source_tree(tmp_path)
    evidence = LinkEvidenceCollector(
        scan_data(),
        src_root=src,
        ctags_runner=failing_ctags,
    ).collect(candidate("E002", "linker_undef"), 900)
    assert evidence.data["symbol_context"]["extraction_method"] == "regex_brace"


def test_link_collector_marks_missing_symbol_context_degraded(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "foo.c").write_text("int other(void) { return 0; }\n", encoding="utf-8")
    evidence = LinkEvidenceCollector(scan_data(), src_root=src).collect(
        candidate("E002", "linker_undef"),
        900,
    )
    assert evidence.degraded is True
    assert "symbol_context_unavailable" in evidence.warnings


def test_spec_collector_marks_missing_spec_degraded() -> None:
    evidence = SpecEvidenceCollector(scan_data()).collect(candidate("E004", "spec_script"), 600)
    assert evidence.degraded is True
    assert evidence.warnings == ["spec_file_unavailable"]


def test_spec_collector_level1_includes_section(tmp_path: Path) -> None:
    spec = write_spec(tmp_path)
    evidence = SpecEvidenceCollector(scan_data(), spec_path=spec).collect(
        candidate("E004", "spec_script"),
        300,
    )
    assert evidence.data["spec_section_text"] == "make"
    assert "failure_context" not in evidence.data


def test_spec_collector_level2_adds_failure_context(tmp_path: Path) -> None:
    spec = write_spec(tmp_path)
    buildlog = write_buildlog(tmp_path)
    evidence = SpecEvidenceCollector(scan_data(), spec_path=spec, buildlog_path=buildlog).collect(
        candidate("E004", "spec_script"),
        600,
    )
    assert evidence.data["failure_context"]["last_command"] == "make"


def test_spec_collector_level3_adds_spec_metadata(tmp_path: Path) -> None:
    spec = write_spec(tmp_path)
    evidence = SpecEvidenceCollector(scan_data(), spec_path=spec).collect(
        candidate("E004", "spec_script"),
        900,
    )
    assert evidence.data["buildrequires"] == ["gcc", "make"]
    assert evidence.data["patches"][0]["value"] == "fix.patch"
    assert evidence.data["sources"][0]["value"] == "demo.tar.gz"


def test_spec_collector_does_not_depend_on_ctags_when_ctags_unavailable(
    tmp_path: Path,
) -> None:
    spec = write_spec(tmp_path)
    evidence = SpecEvidenceCollector(
        scan_data(),
        spec_path=spec,
        ctags_runner=failing_ctags,
    ).collect(candidate("E004", "spec_script"), 900)
    assert evidence.degraded is False
    assert evidence.data["spec_section_text"] == "make"


def test_deps_collector_level1_parses_missing_dependency() -> None:
    evidence = DepsEvidenceCollector(scan_data()).collect(candidate("E005", "depsolve"), 300)
    assert evidence.data["missing_dependency"] == {
        "dependency": "libfoo",
        "needed_by": "demo-1.0",
    }
    assert evidence.data["profile_hint"] == "buildlog"


def test_deps_collector_level2_adds_buildrequires(tmp_path: Path) -> None:
    spec = write_spec(tmp_path)
    evidence = DepsEvidenceCollector(scan_data(), spec_path=spec).collect(
        candidate("E005", "depsolve"),
        600,
    )
    assert evidence.data["spec_buildrequires"] == ["gcc", "make"]


def test_deps_collector_missing_spec_is_degraded(tmp_path: Path) -> None:
    evidence = DepsEvidenceCollector(scan_data(), spec_path=tmp_path / "missing.spec").collect(
        candidate("E005", "depsolve"),
        600,
    )
    assert evidence.degraded is True
    assert evidence.warnings == ["spec_file_unavailable"]


def test_deps_collector_does_not_depend_on_ctags_when_ctags_unavailable(
    tmp_path: Path,
) -> None:
    spec = write_spec(tmp_path)
    evidence = DepsEvidenceCollector(
        scan_data(),
        spec_path=spec,
        ctags_runner=failing_ctags,
    ).collect(candidate("E005", "depsolve"), 600)
    assert evidence.degraded is False
    assert evidence.data["spec_buildrequires"] == ["gcc", "make"]


@pytest.mark.parametrize(
    ("event_id", "kind", "collector_name"),
    [
        ("E001", "compiler", "compile"),
        ("E002", "linker_undef", "link"),
        ("E004", "spec_script", "spec"),
        ("E005", "depsolve", "deps"),
    ],
)
def test_router_returns_mvp_collectors(
    event_id: str,
    kind: str,
    collector_name: str,
) -> None:
    collector = collector_for_candidate(candidate(event_id, kind), scan_data())
    assert collector is not None
    assert collector.collector_name == collector_name


@pytest.mark.parametrize("kind", ["patch", "install_missing", "raw_error"])
def test_router_rejects_non_m5_collectors(kind: str) -> None:
    assert collector_for_candidate({"event_id": "E006", "kind": kind}, scan_data()) is None
