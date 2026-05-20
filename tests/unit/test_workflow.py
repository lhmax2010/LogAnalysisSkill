import json
import subprocess
from pathlib import Path
from typing import Any

from gbs_build_skill.runner import BuildOptions, BuildResult
from gbs_workflow.workflow import (
    WorkflowOptions,
    WorkflowResult,
    collect_suggestions,
    main,
    run_workflow,
    select_analysis_log,
    slugify,
    write_suggestions,
)


def workflow_options(tmp_path: Path) -> WorkflowOptions:
    src_root = tmp_path / "src"
    src_root.mkdir()
    (src_root / "ffmpeg.spec").write_text(
        "Name: ffmpeg\nVersion: 1\nBuildRequires:  gcc\n%prep\n",
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


def fake_build(exit_code: int) -> Any:
    def _runner(options: BuildOptions) -> BuildResult:
        options.output_log.parent.mkdir(parents=True, exist_ok=True)
        options.output_log.write_text("build output\n", encoding="utf-8")
        return BuildResult(
            exit_code=exit_code,
            log_path=options.output_log,
            command=("gbs", "build"),
            duration_seconds=0.1,
        )

    return _runner


def fake_analyzer(packet: dict[str, object]) -> Any:
    def _runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        output_dir = Path(command[command.index("--output-dir") + 1])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "evidence_packet.json").write_text(
            json.dumps(packet),
            encoding="utf-8",
        )
        (output_dir / "evidence_packet.md").write_text("# Evidence\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    return _runner


def depsolve_packet() -> dict[str, object]:
    return {
        "package": "ffmpeg",
        "failed_phase": None,
        "primary_error": {
            "kind": "depsolve",
            "message": "nothing provides pkgconfig(nonexistent-pkg-xxxyzz)",
        },
    }


def test_workflow_success_short_circuits_without_analyzer(tmp_path: Path) -> None:
    called = False

    def analyzer_should_not_run(
        *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        nonlocal called
        called = True
        return subprocess.CompletedProcess(args, 0)

    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build(0),
        subprocess_runner=analyzer_should_not_run,
    )

    assert result.exit_code == 0
    assert result.build_succeeded is True
    assert called is False
    assert "Build status**: success" in result.summary_path.read_text(encoding="utf-8")
    assert not (result.output_dir / "analyzer_output").exists()


def test_workflow_failure_runs_analyzer_and_writes_depsolve_suggestion(tmp_path: Path) -> None:
    analyzer_input: list[str] = []

    def analyzer(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        analyzer_input.append(command[command.index("analyze") + 1])
        return fake_analyzer(depsolve_packet())(command, **kwargs)

    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build(1),
        subprocess_runner=analyzer,
        python_executable="/test/python",
    )

    assert result.exit_code == 1
    assert result.build_succeeded is False
    assert result.evidence_packet_path == (
        result.output_dir / "analyzer_output" / "evidence_packet.json"
    )
    patch_files = sorted((result.output_dir / "suggestions").glob("*.patch"))
    md_files = sorted((result.output_dir / "suggestions").glob("*.md"))
    assert len(patch_files) == 1
    assert len(md_files) == 1
    assert "BuildRequires:  pkgconfig(nonexistent-pkg-xxxyzz)" in patch_files[0].read_text(
        encoding="utf-8"
    )
    assert analyzer_input == [str(result.compiler_log_path)]
    summary = result.summary_path.read_text(encoding="utf-8")
    assert "depsolve" in summary
    assert "Yes" in summary


def test_workflow_prefers_structured_gbs_failure_log(tmp_path: Path) -> None:
    options = workflow_options(tmp_path)
    structured_log = tmp_path / "gbs" / "logs" / "fail" / "ffmpeg" / "log.txt"
    structured_log.parent.mkdir(parents=True)
    structured_log.write_text("inner rpm log\n", encoding="utf-8")
    analyzer_input: list[str] = []

    def build_runner(build_options: BuildOptions) -> BuildResult:
        build_options.output_log.parent.mkdir(parents=True, exist_ok=True)
        build_options.output_log.write_text(
            f"warning: build failed, Leaving the logs in {structured_log}\n",
            encoding="utf-8",
        )
        return BuildResult(
            exit_code=1,
            log_path=build_options.output_log,
            command=("gbs", "build"),
            duration_seconds=0.1,
        )

    def analyzer(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        analyzer_input.append(command[command.index("analyze") + 1])
        return fake_analyzer(depsolve_packet())(command, **kwargs)

    result = run_workflow(
        options,
        build_runner=build_runner,
        subprocess_runner=analyzer,
        python_executable="/test/python",
    )

    assert result.analysis_log_path == structured_log
    assert analyzer_input == [str(structured_log)]


def test_select_analysis_log_falls_back_when_referenced_log_missing(tmp_path: Path) -> None:
    compiler_log = tmp_path / "compiler.log"
    compiler_log.write_text(
        "warning: build failed, Leaving the logs in /tmp/missing/logs/fail/pkg/log.txt\n",
        encoding="utf-8",
    )

    assert select_analysis_log(compiler_log) == compiler_log


def test_select_analysis_log_falls_back_when_wrapper_log_missing(tmp_path: Path) -> None:
    missing_log = tmp_path / "missing.log"

    assert select_analysis_log(missing_log) == missing_log


def test_workflow_returns_error_when_packet_is_missing(tmp_path: Path) -> None:
    def analyzer_without_packet(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        del kwargs
        output_dir = Path(command[command.index("--output-dir") + 1])
        output_dir.mkdir(parents=True, exist_ok=True)
        return subprocess.CompletedProcess(command, 0)

    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build(1),
        subprocess_runner=analyzer_without_packet,
    )

    assert result.exit_code == 3
    assert result.error is not None
    assert "cannot read evidence_packet.json" in result.summary_path.read_text(encoding="utf-8")


def test_workflow_returns_error_when_analyzer_subprocess_fails(tmp_path: Path) -> None:
    def failing_analyzer(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        raise subprocess.CalledProcessError(9, command)

    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build(1),
        subprocess_runner=failing_analyzer,
    )

    assert result.exit_code == 1
    assert result.error == "gbs_analyzer exited with 9"
    assert "gbs_analyzer exited with 9" in result.summary_path.read_text(encoding="utf-8")


def test_collect_suggestions_skips_unmatched_suggesters(tmp_path: Path) -> None:
    suggestions = collect_suggestions(
        {"primary_error": {"kind": "compiler", "message": "boom"}},
        tmp_path,
        suggesters=[],
    )

    assert suggestions == []


def test_write_suggestions_writes_markdown_only_for_guidance(tmp_path: Path) -> None:
    from gbs_workflow.suggesters.base import Suggestion

    files = write_suggestions(
        [
            Suggestion(
                suggester="demo",
                title="Manual Review",
                description="Look at evidence",
                patch_content=None,
                target_files=[],
                confidence="advisory",
                risks=[],
                manual_steps=["Read evidence_packet.md"],
            )
        ],
        tmp_path,
    )

    assert [path.suffix for path in files] == [".md"]
    assert "Manual Review" in files[0].read_text(encoding="utf-8")


def test_slugify_keeps_short_safe_file_name() -> None:
    assert (
        slugify("Add BuildRequires for pkgconfig(libssl)")
        == "add_buildrequires_for_pkgconfig_libssl"
    )


def test_cli_main_returns_workflow_exit_code(tmp_path: Path, monkeypatch: object) -> None:
    def fake_run(options: WorkflowOptions) -> WorkflowResult:
        summary = options.output_dir / "workflow_summary.md"
        summary.parent.mkdir(parents=True)
        summary.write_text("# Summary\n", encoding="utf-8")
        return WorkflowResult(
            exit_code=7,
            build_exit_code=7,
            build_succeeded=False,
            output_dir=options.output_dir,
            summary_path=summary,
            compiler_log_path=options.output_dir / "compiler.log",
        )

    monkeypatch.setattr("gbs_workflow.workflow.run_workflow", fake_run)

    assert main(
        [
            "--conf",
            str(tmp_path / "gbs.conf"),
            "--arch",
            "armv7l",
            "--src-root",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / ".gbs_workflow"),
        ]
    ) == 7
