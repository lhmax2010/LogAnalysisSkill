import importlib.util
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
from gbs_build_skill.runner import BuildOptions, BuildResult
from gbs_workflow.workflow import (
    WorkflowOptions,
    WorkflowResult,
    build_analyzer_subprocess_env,
    collect_suggestions,
    main,
    run_workflow,
    slugify,
    write_suggestions,
)


def load_workflow_launcher() -> Any:
    path = Path("tizen-gbs-build-workflow/scripts/run_workflow.py")
    spec = importlib.util.spec_from_file_location("workflow_launcher_for_test", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
        (output_dir / "perf_report.json").write_text(
            json.dumps({"tokens": {"by_section": {"source_snippets": 17}}}),
            encoding="utf-8",
        )
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


def compiler_packet() -> dict[str, object]:
    return {
        "package": "ffmpeg",
        "failed_phase": "%build",
        "primary_error": {
            "kind": "compiler",
            "file": "libavcodec/utils.c",
            "line": 109,
            "message": "implicit declaration of function 'av_temp_lss'",
        },
    }


def werror_packet() -> dict[str, object]:
    return {
        "package": "ffmpeg",
        "failed_phase": "%build",
        "primary_error": {
            "kind": "werror",
            "file": "libavcodec/utils.c",
            "line": 109,
            "message": (
                "error: address of array will always evaluate to true "
                "[-Werror,-Wpointer-bool-conversion]"
            ),
        },
    }


def subprocess_module(command: list[str]) -> str:
    return command[command.index("-m") + 1]


def write_fake_patch_context(output_dir: Path, *, status: str | None = None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "context.md").write_text("# Patch Context\n", encoding="utf-8")
    (output_dir / "README.md").write_text("# README\n", encoding="utf-8")
    meta = {"status": status} if status is not None else {}
    (output_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")


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
    assert result.patch_context_path is None
    assert result.patch_context_error is None
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
    assert "Downstream Token Estimate" in summary
    assert "Actual Claude consumption" in summary
    assert "Source snippets subset from analyzer perf_report: 17 tokens" in summary
    assert result.downstream_token_estimate is not None
    assert result.downstream_token_estimate["total_claude_facing_tokens"] >= 1
    roles = {file["role"] for file in result.downstream_token_estimate["files"]}
    assert roles == {"workflow_summary", "evidence_packet_md", "suggestion_md"}


def test_workflow_passes_extra_pythonpath_to_analyzer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTHONPATH", "/existing/path")
    captured_env: dict[str, str] = {}

    def analyzer(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        env = kwargs.get("env")
        assert isinstance(env, dict)
        captured_env.update(env)
        return fake_analyzer(depsolve_packet())(command, **kwargs)

    extra_paths = (tmp_path / "workflow_scripts", tmp_path / "analyzer_scripts")
    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build(1),
        subprocess_runner=analyzer,
        python_executable="/test/python",
        analyzer_extra_pythonpath=extra_paths,
    )

    assert result.exit_code == 1
    assert captured_env is not os.environ
    assert captured_env["PYTHONPATH"].split(os.pathsep)[:3] == [
        str(extra_paths[0]),
        str(extra_paths[1]),
        "/existing/path",
    ]


def test_analyzer_subprocess_env_returns_none_without_extra_pythonpath() -> None:
    assert build_analyzer_subprocess_env(()) is None


def test_workflow_launcher_discovers_patch_suggest_from_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launcher = load_workflow_launcher()
    skill_root = tmp_path / "tizen-gbs-patch-suggest"
    scripts = skill_root / "scripts"
    (scripts / "gbs_patch_suggest").mkdir(parents=True)

    monkeypatch.setenv("TIZEN_GBS_PATCH_SUGGEST_SKILL_DIR", str(skill_root))

    assert launcher._optional_dependency_scripts(
        env_name="TIZEN_GBS_PATCH_SUGGEST_SKILL_DIR",
        skill_name="tizen-gbs-patch-suggest",
        package_dir="gbs_patch_suggest",
    ) == scripts.resolve()


def test_workflow_launcher_discovers_patch_suggest_sibling_without_blocking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    launcher = load_workflow_launcher()
    workflow_script = tmp_path / "tizen-gbs-build-workflow" / "scripts" / "run_workflow.py"
    patch_scripts = tmp_path / "tizen-gbs-patch-suggest" / "scripts"
    workflow_script.parent.mkdir(parents=True)
    (patch_scripts / "gbs_patch_suggest").mkdir(parents=True)

    monkeypatch.setattr(launcher, "__file__", str(workflow_script))
    monkeypatch.setenv("TIZEN_GBS_PATCH_SUGGEST_SKILL_DIR", str(tmp_path / "missing"))

    assert launcher._optional_dependency_scripts(
        env_name="TIZEN_GBS_PATCH_SUGGEST_SKILL_DIR",
        skill_name="tizen-gbs-patch-suggest",
        package_dir="gbs_patch_suggest",
    ) == patch_scripts


def test_workflow_compile_failure_writes_optional_patch_context(tmp_path: Path) -> None:
    patch_commands: list[list[str]] = []

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        module = subprocess_module(command)
        if module == "gbs_analyzer":
            return fake_analyzer(compiler_packet())(command, **kwargs)
        if module == "gbs_patch_suggest":
            patch_commands.append(command)
            evidence_path = Path(command[command.index("--evidence") + 1])
            output_dir = Path(command[command.index("--output-dir") + 1])
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "context.md").write_text("# Patch Context\n", encoding="utf-8")
            (output_dir / "README.md").write_text("# README\n", encoding="utf-8")
            (output_dir / "meta.json").write_text("{}", encoding="utf-8")
            assert evidence_path == tmp_path / ".gbs_workflow/analyzer_output/evidence_packet.json"
            assert command[command.index("--src-root") + 1] == str(tmp_path / "src")
            return subprocess.CompletedProcess(command, 0)
        raise AssertionError(f"unexpected subprocess module: {module}")

    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build(1),
        subprocess_runner=runner,
        python_executable="/test/python",
    )

    assert result.exit_code == 1
    assert result.patch_context_path == result.output_dir / "patch_context" / "context.md"
    assert result.patch_context_error is None
    assert len(patch_commands) == 1
    summary = result.summary_path.read_text(encoding="utf-8")
    assert "## Patch Context" in summary
    assert "did not generate a final patch" in summary
    assert "patch_context/context.md" in summary
    assert result.downstream_token_estimate is not None
    roles = {file["role"] for file in result.downstream_token_estimate["files"]}
    assert "patch_context_md" in roles


def test_workflow_werror_patch_ready_context_suppresses_generic_fallback(
    tmp_path: Path,
) -> None:
    patch_commands: list[list[str]] = []

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        module = subprocess_module(command)
        if module == "gbs_analyzer":
            return fake_analyzer(werror_packet())(command, **kwargs)
        if module == "gbs_patch_suggest":
            patch_commands.append(command)
            output_dir = Path(command[command.index("--output-dir") + 1])
            write_fake_patch_context(
                output_dir,
                status="spec_toolchain_flag_context_available",
            )
            return subprocess.CompletedProcess(command, 0)
        raise AssertionError(f"unexpected subprocess module: {module}")

    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build(1),
        subprocess_runner=runner,
        python_executable="/test/python",
    )

    assert result.exit_code == 1
    assert result.patch_context_path == result.output_dir / "patch_context" / "context.md"
    assert result.patch_context_error is None
    assert len(patch_commands) == 1
    assert result.suggestion_paths == []
    summary = result.summary_path.read_text(encoding="utf-8")
    assert "## Patch Context" in summary
    assert "Patch-suggest status**: `spec_toolchain_flag_context_available`" in summary
    assert "Patch-suggest produced patch-ready context" in summary
    assert "Manually review unsupported error kind werror" not in summary
    assert "fallback" not in summary


def test_workflow_werror_patch_advisory_keeps_generic_fallback(tmp_path: Path) -> None:
    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        module = subprocess_module(command)
        if module == "gbs_analyzer":
            return fake_analyzer(werror_packet())(command, **kwargs)
        if module == "gbs_patch_suggest":
            output_dir = Path(command[command.index("--output-dir") + 1])
            write_fake_patch_context(output_dir, status="spec_toolchain_flag_advisory")
            return subprocess.CompletedProcess(command, 0)
        raise AssertionError(f"unexpected subprocess module: {module}")

    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build(1),
        subprocess_runner=runner,
        python_executable="/test/python",
    )

    summary = result.summary_path.read_text(encoding="utf-8")
    assert "Patch-suggest status**: `spec_toolchain_flag_advisory`" in summary
    assert "Patch-suggest produced patch-ready context" not in summary
    assert "Manually review unsupported error kind werror" in summary
    assert "| 001 | fallback |" in summary


def test_workflow_non_source_diagnostic_failure_does_not_run_patch_suggest(
    tmp_path: Path,
) -> None:
    modules: list[str] = []

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        module = subprocess_module(command)
        modules.append(module)
        assert module == "gbs_analyzer"
        return fake_analyzer(depsolve_packet())(command, **kwargs)

    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build(1),
        subprocess_runner=runner,
        python_executable="/test/python",
    )

    assert result.exit_code == 1
    assert modules == ["gbs_analyzer"]
    assert result.patch_context_path is None
    assert result.patch_context_error is None
    assert "## Patch Context" not in result.summary_path.read_text(encoding="utf-8")


def test_workflow_patch_context_failure_is_non_fatal(tmp_path: Path) -> None:
    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        module = subprocess_module(command)
        if module == "gbs_analyzer":
            return fake_analyzer(compiler_packet())(command, **kwargs)
        if module == "gbs_patch_suggest":
            raise subprocess.CalledProcessError(9, command)
        raise AssertionError(f"unexpected subprocess module: {module}")

    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build(1),
        subprocess_runner=runner,
        python_executable="/test/python",
    )

    assert result.exit_code == 1
    assert result.patch_context_path is None
    assert result.patch_context_error == "gbs_patch_suggest exited with 9"
    summary = result.summary_path.read_text(encoding="utf-8")
    assert "Patch context generation was skipped or unavailable" in summary
    assert "This is non-fatal" in summary


def test_workflow_werror_patch_context_failure_keeps_generic_fallback(tmp_path: Path) -> None:
    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        module = subprocess_module(command)
        if module == "gbs_analyzer":
            return fake_analyzer(werror_packet())(command, **kwargs)
        if module == "gbs_patch_suggest":
            raise subprocess.CalledProcessError(9, command)
        raise AssertionError(f"unexpected subprocess module: {module}")

    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build(1),
        subprocess_runner=runner,
        python_executable="/test/python",
    )

    assert result.patch_context_error == "gbs_patch_suggest exited with 9"
    summary = result.summary_path.read_text(encoding="utf-8")
    assert "Patch context generation was skipped or unavailable" in summary
    assert "Manually review unsupported error kind werror" in summary
    assert "| 001 | fallback |" in summary


def test_workflow_passes_extra_pythonpath_to_patch_suggest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTHONPATH", "/existing/path")
    captured_env: dict[str, str] = {}
    patch_scripts = tmp_path / "patch_scripts"

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        module = subprocess_module(command)
        if module == "gbs_analyzer":
            return fake_analyzer(compiler_packet())(command, **kwargs)
        if module == "gbs_patch_suggest":
            env = kwargs.get("env")
            assert isinstance(env, dict)
            captured_env.update(env)
            output_dir = Path(command[command.index("--output-dir") + 1])
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "context.md").write_text("# Patch Context\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)
        raise AssertionError(f"unexpected subprocess module: {module}")

    result = run_workflow(
        workflow_options(tmp_path),
        build_runner=fake_build(1),
        subprocess_runner=runner,
        python_executable="/test/python",
        patch_suggest_extra_pythonpath=(patch_scripts,),
    )

    assert result.exit_code == 1
    assert captured_env is not os.environ
    assert captured_env["PYTHONPATH"].split(os.pathsep)[:2] == [
        str(patch_scripts),
        "/existing/path",
    ]
    assert os.environ["PYTHONPATH"] == "/existing/path"


def test_workflow_prefers_structured_gbs_failure_log(tmp_path: Path) -> None:
    options = workflow_options(tmp_path)
    structured_log = tmp_path / "gbs" / "logs" / "fail" / "ffmpeg" / "log.txt"
    structured_log.parent.mkdir(parents=True)
    structured_log.write_text("inner rpm log\n", encoding="utf-8")
    analyzer_input: list[str] = []

    def build_runner(build_options: BuildOptions) -> BuildResult:
        build_options.output_log.parent.mkdir(parents=True, exist_ok=True)
        build_options.output_log.write_text("wrapper output\n", encoding="utf-8")
        return BuildResult(
            exit_code=1,
            log_path=build_options.output_log,
            command=("gbs", "build"),
            duration_seconds=0.1,
            failure_log_path=structured_log,
            analysis_log_path=structured_log,
            package_name="ffmpeg",
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


def test_workflow_falls_back_to_build_log_when_analysis_log_is_missing(tmp_path: Path) -> None:
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

    assert result.analysis_log_path == result.compiler_log_path
    assert analyzer_input == [str(result.compiler_log_path)]


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
    options = workflow_options(tmp_path)
    analysis_log = tmp_path / "gbs" / "logs" / "fail" / "ffmpeg" / "log.txt"
    analysis_log.parent.mkdir(parents=True)
    analysis_log.write_text("inner rpm log\n", encoding="utf-8")

    def build_runner(build_options: BuildOptions) -> BuildResult:
        build_options.output_log.parent.mkdir(parents=True, exist_ok=True)
        build_options.output_log.write_text("wrapper output\n", encoding="utf-8")
        return BuildResult(
            exit_code=1,
            log_path=build_options.output_log,
            command=("gbs", "build"),
            duration_seconds=0.1,
            analysis_log_path=analysis_log,
        )

    def failing_analyzer(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        assert command[command.index("analyze") + 1] == str(analysis_log)
        raise subprocess.CalledProcessError(9, command)

    result = run_workflow(
        options,
        build_runner=build_runner,
        subprocess_runner=failing_analyzer,
    )

    assert result.exit_code == 1
    assert result.analysis_log_path == analysis_log
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


def test_cli_main_returns_workflow_exit_code(
    tmp_path: Path,
    monkeypatch: object,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run(options: WorkflowOptions, **kwargs: object) -> WorkflowResult:
        del kwargs
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
            downstream_token_estimate={"total_claude_facing_tokens": 123},
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
    captured = capsys.readouterr()
    assert "workflow downstream tokens: 123 estimated" in captured.err
