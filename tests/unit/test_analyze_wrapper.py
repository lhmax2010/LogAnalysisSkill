from pathlib import Path

from gbs_analyzer.analyze import (
    EXIT_BUILDLOG_UNREADABLE,
    EXIT_SUCCESS,
    AnalyzeOptions,
    analyze_buildlog,
    main,
)

FIXTURES = Path("tests/fixtures")


def test_analyze_buildlog_fast_path_writes_outputs(tmp_path: Path) -> None:
    fixture = FIXTURES / "fast_path_missing_lib"
    result = analyze_buildlog(
        AnalyzeOptions(
            buildlog_path=fixture / "buildlog",
            src_root=fixture,
            output_dir=tmp_path,
            output_format="both",
            use_tiktoken=False,
            package="demo",
        )
    )

    assert result.exit_code == EXIT_SUCCESS
    assert result.packet is not None
    assert result.packet["via"] == "fast_path"
    assert result.packet["package"] == "demo"
    assert (tmp_path / "evidence_packet.json").is_file()
    assert (tmp_path / "evidence_packet.md").is_file()
    assert (tmp_path / "perf_report.json").is_file()
    assert result.perf_report is not None
    assert result.perf_report["schema_version"] == "perf_report/v1"
    assert result.perf_report["execution"]["fast_path_hit"] is True


def test_analyze_buildlog_full_path_tier2(tmp_path: Path) -> None:
    fixture = FIXTURES / "evidence_compile_no_member"
    result = analyze_buildlog(
        AnalyzeOptions(
            buildlog_path=fixture / "buildlog",
            src_root=fixture / "src",
            output_dir=tmp_path,
            output_format="json",
            use_tiktoken=False,
        )
    )

    assert result.exit_code == EXIT_SUCCESS
    assert result.packet is not None
    assert result.packet["via"] == "full_path"
    assert result.packet["verdict"] == "direct_answer"
    assert result.packet["matched_tier"] == "tier2"
    assert result.packet["degraded"] is False
    assert result.packet["token_budget"]["conservation_ok"] is True
    assert not (tmp_path / "evidence_packet.md").exists()
    assert result.perf_report is not None
    assert result.perf_report["decisions"]["evidence_collector"] == "compile"
    assert result.perf_report["decisions"]["level_achieved"] == 2


def test_analyze_buildlog_returns_unreadable_exit(tmp_path: Path) -> None:
    result = analyze_buildlog(
        AnalyzeOptions(
            buildlog_path=tmp_path / "missing.log",
            src_root=tmp_path,
            output_dir=tmp_path / "out",
            use_tiktoken=False,
        )
    )

    assert result.exit_code == EXIT_BUILDLOG_UNREADABLE
    assert result.packet is None
    assert result.error is not None


def test_main_keeps_stdout_quiet_for_success(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    fixture = FIXTURES / "fast_path_patch_failed"
    code = main(
        [
            "analyze",
            str(fixture / "buildlog"),
            "--src-root",
            str(fixture),
            "--output-dir",
            str(tmp_path),
            "--output-format",
            "json",
            "--no-tiktoken",
        ]
    )

    captured = capsys.readouterr()
    assert code == EXIT_SUCCESS
    assert captured.out == ""
    assert captured.err == ""


def test_main_reports_unreadable_buildlog_on_stderr(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(["analyze", str(tmp_path / "missing.log"), "--output-dir", str(tmp_path / "out")])

    captured = capsys.readouterr()
    assert code == EXIT_BUILDLOG_UNREADABLE
    assert captured.out == ""
    assert "buildlog is not readable" in captured.err
