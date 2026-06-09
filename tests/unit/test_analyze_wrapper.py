import json
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
    downstream = result.perf_report["tokens"]["downstream_outputs"]
    assert downstream["evidence_packet_md_tokens"] >= 1
    assert downstream["evidence_packet_json_tokens"] >= 1
    assert downstream["total_claude_facing_tokens"] == downstream["evidence_packet_md_tokens"]
    assert "Actual Claude consumption" in downstream["scope"]


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
    downstream = result.perf_report["tokens"]["downstream_outputs"]
    assert downstream["evidence_packet_md_tokens"] is None
    assert downstream["evidence_packet_json_tokens"] >= 1
    assert downstream["total_claude_facing_tokens"] == 0


def test_analyze_buildlog_writes_error_clusters_sidecar_without_changing_primary(
    tmp_path: Path,
) -> None:
    buildlog = tmp_path / "build.log"
    buildlog.write_text(
        "\n".join(
            [
                "+ %build",
                "+ clang -Werror -c src/a.c",
                "src/a.c:10:5: error: enum cast [-Werror,-Wimplicit-enum-enum-cast]",
                "src/b.c:11:5: error: enum cast [-Werror,-Wimplicit-enum-enum-cast]",
                "src/c.c:12:5: error: enum cast [-Werror,-Wimplicit-enum-enum-cast]",
                "fatal error: too many errors emitted, stopping now",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = analyze_buildlog(
        AnalyzeOptions(
            buildlog_path=buildlog,
            src_root=tmp_path,
            output_dir=tmp_path / "out",
            output_format="both",
            use_tiktoken=False,
        )
    )

    assert result.exit_code == EXIT_SUCCESS
    assert result.packet is not None
    assert result.packet["primary_error"]["file"] == "src/a.c"
    assert result.packet["root_cause_candidates"][0]["event_id"] == "E001"
    clusters = result.packet["error_clusters"]
    assert clusters["truncated"] is True
    assert clusters["full_locations_path"] == "error_clusters.json"
    cluster = clusters["clusters"][0]
    assert cluster["warning_option"] == "-Wimplicit-enum-enum-cast"
    assert cluster["count"] == 3
    assert cluster["file_count"] == 3
    assert cluster["large_scale"] is True
    assert [location["event_id"] for location in cluster["locations_sample"]] == [
        "E001",
        "E002",
        "E003",
    ]
    sidecar_path = tmp_path / "out" / "error_clusters.json"
    assert sidecar_path.is_file()
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert sidecar["schema_version"] == "error_clusters_locations/v1"
    assert len(sidecar["clusters"][0]["locations"]) == 3
    assert result.output_paths["error_clusters_json"] == str(sidecar_path)
    markdown = (tmp_path / "out" / "evidence_packet.md").read_text(encoding="utf-8")
    assert "## Error Clusters" in markdown
    assert "-Wimplicit-enum-enum-cast" in markdown


def test_analyze_buildlog_writes_source_candidates_sidecar_additively(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    (src / "src").mkdir(parents=True)
    (src / "src" / "OutputMetadata.h").write_text("int metadata;\n", encoding="utf-8")
    buildlog = tmp_path / "build.log"
    buildlog.write_text(
        "\n".join(
            [
                "+ %build",
                "+ clang++ -Werror -c src/OutputMetadata.cc",
                (
                    "/home/abuild/rpmbuild/BUILD/inference-engine-1.0/src/OutputMetadata.h:"
                    "42:9: error: private field 'metadata' is not used "
                    "[-Werror,-Wunused-private-field]"
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = analyze_buildlog(
        AnalyzeOptions(
            buildlog_path=buildlog,
            src_root=src,
            output_dir=tmp_path / "out",
            output_format="both",
            use_tiktoken=False,
        )
    )

    assert result.exit_code == EXIT_SUCCESS
    assert result.packet is not None
    assert result.packet["primary_error"]["file"].endswith("OutputMetadata.h")
    assert result.packet["root_cause_candidates"][0]["event_id"] == "E001"
    summary = result.packet["source_candidates"]
    assert summary["full_candidates_path"] == "source_candidates.json"
    assert summary["candidate_count"] == 1
    assert summary["probably_fixable_count"] == 1
    sidecar_path = tmp_path / "out" / "source_candidates.json"
    assert sidecar_path.is_file()
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    candidate = sidecar["candidates"][0]
    assert candidate["event_id"] == "E001"
    assert candidate["normalized_file"] == "src/OutputMetadata.h"
    assert candidate["warning_option"] == "-Wunused-private-field"
    assert candidate["provisional_fixability"] == "probably_fixable"
    assert result.output_paths["source_candidates_json"] == str(sidecar_path)
    markdown = (tmp_path / "out" / "evidence_packet.md").read_text(encoding="utf-8")
    assert "## Source Candidates" in markdown


def test_main_auto_src_root_with_bare_buildlog_keeps_markdown_punctuation(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    buildlog = tmp_path / "log.txt"
    buildlog.write_text(
        "\n".join(
            [
                "+ %build",
                "+ clang -Werror -c src/a.c",
                "src/a.c:10:5: error: enum cast [-Werror,-Wimplicit-enum-enum-cast]",
                "src/b.c:11:5: error: enum cast [-Werror,-Wimplicit-enum-enum-cast]",
                "src/c.c:12:5: error: enum cast [-Werror,-Wimplicit-enum-enum-cast]",
                "fatal error: too many errors emitted, stopping now",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    code = main(
        [
            "analyze",
            "log.txt",
            "--output-dir",
            "out",
            "--output-format",
            "both",
            "--no-tiktoken",
        ]
    )

    assert code == EXIT_SUCCESS
    markdown = (tmp_path / "out" / "evidence_packet.md").read_text(encoding="utf-8")
    assert "error_clusters.json" in markdown
    assert "error_clusters<WORKSPACE>json" not in markdown
    assert "fix strategy. Compiler output" in markdown


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
