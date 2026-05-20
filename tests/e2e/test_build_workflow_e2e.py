import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from gbs_build_skill.runner import BuildOptions, BuildResult
from gbs_workflow.workflow import WorkflowOptions, run_workflow


def packet(kind: str, message: str, **primary_extra: object) -> dict[str, object]:
    primary_error: dict[str, object] = {"kind": kind, "message": message}
    primary_error.update(primary_extra)
    return {
        "package": "ffmpeg",
        "failed_phase": "%build",
        "primary_error": primary_error,
    }


WORKFLOW_CASES: list[tuple[str, dict[str, object], str, bool]] = [
    (
        "A_linker_undef",
        packet(
            "linker_undef",
            "undefined reference to `nonexistent_helper_xxxyzz'",
            file="libavcodec/foo.c",
            line=42,
        ),
        "linker_undef",
        False,
    ),
    (
        "B_depsolve_existing_buildrequires",
        packet("depsolve", "nothing provides pkgconfig(nonexistent-pkg-xxxyzz)"),
        "depsolve",
        False,
    ),
    (
        "C_patch_failed",
        packet("patch", "Hunk #1 FAILED at 10"),
        "patch_failed",
        False,
    ),
    (
        "D_rpm_phase",
        packet("rpm_phase", "Bad exit status from /var/tmp/rpm-tmp.123 (%install)"),
        "spec_script",
        False,
    ),
    (
        "unknown_fallback",
        packet("raw_error", "unclassified build failure"),
        "fallback",
        False,
    ),
]


def workflow_options(tmp_path: Path) -> WorkflowOptions:
    src_root = tmp_path / "src"
    (src_root / "packaging").mkdir(parents=True)
    (src_root / "packaging" / "ffmpeg.spec").write_text(
        "Name: ffmpeg\n"
        "Version: 1\n"
        "BuildRequires:  pkgconfig(nonexistent-pkg-xxxyzz)\n"
        "%prep\n",
        encoding="utf-8",
    )
    return WorkflowOptions(
        conf=tmp_path / "gbs.conf",
        arch="armv7l",
        include_all=True,
        src_root=src_root,
        output_dir=tmp_path / ".gbs_workflow",
        timeout=1800,
    )


def fake_build(options: BuildOptions) -> BuildResult:
    options.output_log.parent.mkdir(parents=True, exist_ok=True)
    options.output_log.write_text("fake failing gbs build\n", encoding="utf-8")
    return BuildResult(
        exit_code=1,
        log_path=options.output_log,
        command=("gbs", "build"),
        duration_seconds=0.1,
    )


def fake_analyzer(packet_data: dict[str, object]) -> Any:
    def _runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        output_dir = Path(command[command.index("--output-dir") + 1])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "evidence_packet.json").write_text(
            json.dumps(packet_data),
            encoding="utf-8",
        )
        (output_dir / "evidence_packet.md").write_text("# Evidence\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    return _runner


@pytest.mark.parametrize(
    ("case_name", "packet_data", "expected_suggester", "expect_patch"),
    WORKFLOW_CASES,
    ids=[case[0] for case in WORKFLOW_CASES],
)
def test_build_workflow_routes_core_cases(
    tmp_path: Path,
    case_name: str,
    packet_data: dict[str, object],
    expected_suggester: str,
    expect_patch: bool,
) -> None:
    del case_name
    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build,
        subprocess_runner=fake_analyzer(packet_data),
        python_executable="/test/python",
    )

    assert result.exit_code == 1
    assert result.build_succeeded is False
    summary = result.summary_path.read_text(encoding="utf-8")
    assert expected_suggester in summary
    assert ("| Yes |" in summary) is expect_patch

    suggestion_dir = result.output_dir / "suggestions"
    md_files = sorted(suggestion_dir.glob("*.md"))
    patch_files = sorted(suggestion_dir.glob("*.patch"))
    assert len(md_files) == 1
    assert len(patch_files) == (1 if expect_patch else 0)
    assert expected_suggester in md_files[0].name


def test_compile_error_suggester_reads_candidate_semantic_class(tmp_path: Path) -> None:
    packet_data = packet(
        "compiler",
        "error: unknown type name",
        file="libavcodec/foo.c",
        line=7,
    )
    packet_data["root_cause_candidates"] = [{"semantic_class": "undeclared_identifier"}]

    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build,
        subprocess_runner=fake_analyzer(packet_data),
        python_executable="/test/python",
    )

    md_file = next((result.output_dir / "suggestions").glob("*.md"))
    assert "compile_error" in md_file.name
    assert "undeclared_identifier" in md_file.read_text(encoding="utf-8")


def test_compile_error_suggester_falls_back_to_unknown_semantic_class(tmp_path: Path) -> None:
    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build,
        subprocess_runner=fake_analyzer(
            packet("compiler", "error: syntax problem", file="libavcodec/foo.c", line=9)
        ),
        python_executable="/test/python",
    )

    md_file = next((result.output_dir / "suggestions").glob("*.md"))
    assert "compile_error" in md_file.name
    assert "Analyzer semantic class: `unknown`" in md_file.read_text(encoding="utf-8")
