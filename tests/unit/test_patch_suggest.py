import json
import os
import subprocess
from pathlib import Path
from typing import cast

import pytest
from gbs_patch_suggest.analyzer_runner import (
    ANALYZER_SKILL_ENV,
    AnalyzerRunResult,
    build_analyzer_subprocess_env,
    discover_analyzer_pythonpath,
    run_analyzer_for_buildlog,
)
from gbs_patch_suggest.cli import (
    EXIT_EVIDENCE_UNREADABLE,
    EXIT_FATAL,
    PatchSuggestOptions,
    main,
    run_patch_suggest,
)
from gbs_patch_suggest.cluster_ingest import ClusterLocation, LargeScaleCluster
from gbs_patch_suggest.cluster_resolver import resolve_clusters
from gbs_patch_suggest.formatter import EDIT_SPEC_SCHEMA, FormatPatchOptions, format_patch
from gbs_patch_suggest.ingest import extract_first_diagnostic
from gbs_patch_suggest.render import MANDATORY_INSTRUCTIONS


def compiler_packet(
    *,
    kind: str = "compiler",
    message: str = "implicit declaration of function 'av_temp_lss'",
    file: str | None = "src/demo.c",
    line: int | None = 12,
    source_snippet: dict[str, object] | None = None,
) -> dict[str, object]:
    primary_error: dict[str, object] = {
        "kind": kind,
        "message": message,
    }
    if file is not None:
        primary_error["file"] = file
    if line is not None:
        primary_error["line"] = line
    packet: dict[str, object] = {
        "primary_error": primary_error,
        "root_cause_candidates": [
            {
                "kind": kind,
                "semantic_class": "undeclared_identifier",
                "confidence": 0.8,
            }
        ],
        "evidence": {},
    }
    if source_snippet is not None:
        packet["evidence"] = {"source_snippet": source_snippet}
    return packet


def write_packet(tmp_path: Path, packet: dict[str, object]) -> Path:
    path = tmp_path / "evidence_packet.json"
    path.write_text(json.dumps(packet), encoding="utf-8")
    return path


def add_error_cluster(
    packet: dict[str, object],
    tmp_path: Path,
    *,
    cluster_id: str = "CL001",
    warning_option: str = "-Wimplicit-enum-enum-cast",
    large_scale: bool = True,
    locations: list[dict[str, object]] | None = None,
) -> None:
    locations = locations or [
        {
            "event_id": "E001",
            "kind": "werror",
            "file": "src/device.c",
            "line": 10,
            "column": 5,
            "line_no": 100,
            "message": "enum cast [-Werror,-Wimplicit-enum-enum-cast]",
        }
    ]
    files = []
    for location in locations:
        file = location.get("file")
        if isinstance(file, str) and file not in files:
            files.append(file)
    packet["error_clusters"] = {
        "schema_version": "error_clusters/v1",
        "truncated": False,
        "truncation_signals": [],
        "full_locations_path": "error_clusters.json",
        "clusters": [
            {
                "id": cluster_id,
                "kind": "source_warning_option",
                "diagnostic_kinds": ["werror"],
                "warning_option": warning_option,
                "count": len(locations),
                "file_count": len(files),
                "files": files,
                "locations_sample": locations[:10],
                "locations_truncated": False,
                "advisory": "Large repeated source diagnostic cluster.",
                "large_scale": large_scale,
            }
        ],
    }
    (tmp_path / "error_clusters.json").write_text(
        json.dumps(
            {
                "schema_version": "error_clusters_locations/v1",
                "clusters": [
                    {
                        "id": cluster_id,
                        "warning_option": warning_option,
                        "locations": locations,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def read_meta(output_dir: Path) -> dict[str, object]:
    data = json.loads((output_dir / "meta.json").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


def read_context(output_dir: Path) -> str:
    return (output_dir / "context.md").read_text(encoding="utf-8")


def read_readme(output_dir: Path) -> str:
    return (output_dir / "README.md").read_text(encoding="utf-8")


def write_source(root: Path, relative: str, *, lines: int = 20) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{relative} line {index}" for index in range(1, lines + 1)))
    return path


def test_extract_first_diagnostic_uses_primary_error_and_top_candidate() -> None:
    diagnostic = extract_first_diagnostic(compiler_packet())

    assert diagnostic.kind == "compiler"
    assert diagnostic.semantic_class == "undeclared_identifier"
    assert diagnostic.file == "src/demo.c"
    assert diagnostic.line == 12
    assert diagnostic.message == "implicit declaration of function 'av_temp_lss'"


def test_level_a_uses_evidence_source_snippet(tmp_path: Path) -> None:
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(
            source_snippet={
                "path": "src/demo.c",
                "start_line": 10,
                "end_line": 13,
                "text": "int value = av_temp_lss();",
            }
        ),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(PatchSuggestOptions(evidence_path, output_dir=output_dir))

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_available"
    assert meta["level"] == "A"
    assert meta["has_source_context"] is True
    context = read_context(output_dir)
    assert "int value = av_temp_lss();" in context
    assert "Decide 1-3 candidate fixes and write each one as an edit spec" in context
    assert "approach, explicit assumption, and confidence" in context
    assert "Treat the semantic class as a hint, not as proof" in context
    assert "reported error may be a symptom, not the root cause" in context
    assert "verify that functions or symbols referenced near the error actually exist" in context
    assert "Do not silently keep an unverified symbol" in context
    assert "edit_spec_N.json" in context
    assert "candidate_N.patch" in context
    assert "python3 -m gbs_patch_suggest format-patch" in context
    assert "git diff --no-index" in context
    assert '"schema_version": "gbs_patch_suggest/edit-spec/v1"' in context
    assert "If the same `old` text appears in multiple places" in context
    assert "one edit per occurrence with its own `line` value" in context
    assert "`old_not_unique` or `context_not_unique`" in context
    assert "Do NOT read the formatter source code" in context
    assert "do NOT make `old` a giant multi-line block" in context
    assert "never modifies the source tree" in context
    assert "Do NOT fall back to hand-writing a unified diff" in context
    assert "Writing the `.patch` file only saves the suggestion to disk for review" in context
    assert MANDATORY_INSTRUCTIONS.strip() in context
    assert context.rstrip().endswith(MANDATORY_INSTRUCTIONS.strip())
    assert not list(output_dir.glob("*.patch"))


def test_werror_uses_same_source_diagnostic_flow(tmp_path: Path) -> None:
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(
            kind="werror",
            message=(
                "error: address of array will always evaluate to true "
                "[-Werror,-Wpointer-bool-conversion]"
            ),
            source_snippet={
                "path": "src/demo.c",
                "start_line": 7,
                "end_line": 9,
                "text": "if (array_field) {\n    return 1;\n}",
            },
        ),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(PatchSuggestOptions(evidence_path, output_dir=output_dir))

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_available"
    assert meta["level"] == "A"
    assert meta["applicable"] is True
    assert meta["fault_class"] == "werror"
    context = read_context(output_dir)
    assert "Fault class: `werror`" in context
    assert "address of array" in context
    assert "if (array_field)" in context


def test_outputs_include_readme_and_meta_paths(tmp_path: Path) -> None:
    evidence_path = write_packet(tmp_path, compiler_packet())
    output_dir = tmp_path / "out"

    result = run_patch_suggest(PatchSuggestOptions(evidence_path, output_dir=output_dir))

    assert result.exit_code == 0
    readme = read_readme(output_dir)
    assert "Patch Suggestion Output" in readme
    assert "Read `context.md` first" in readme
    assert "did not generate a patch" in readme
    assert "did not modify the source tree" in readme
    meta = read_meta(output_dir)
    assert meta["outputs"] == {
        "readme_md": str(output_dir / "README.md"),
        "context_md": str(output_dir / "context.md"),
        "meta_json": str(output_dir / "meta.json"),
    }
    assert meta["inputs"]["evidence_json"] == str(evidence_path)  # type: ignore[index]
    assert meta["inputs"]["buildlog"] is None  # type: ignore[index]


def test_buildlog_mode_runs_analyzer_then_generates_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    buildlog = tmp_path / "build.log"
    buildlog.write_text("compiler error", encoding="utf-8")
    output_dir = tmp_path / "out"
    expected_src_root = tmp_path / "src"
    expected_src_root.mkdir()
    extra_path = tmp_path / "analyzer_scripts"

    def fake_run_analyzer(
        buildlog_path: Path,
        *,
        output_dir: Path,
        src_root: Path | None = None,
        extra_pythonpath: tuple[Path, ...] = (),
        **_: object,
    ) -> AnalyzerRunResult:
        assert buildlog_path == buildlog
        assert src_root == expected_src_root
        assert extra_pythonpath == (extra_path,)
        output_dir.mkdir(parents=True, exist_ok=True)
        evidence_path = output_dir / "evidence_packet.json"
        evidence_path.write_text(json.dumps(compiler_packet()), encoding="utf-8")
        return AnalyzerRunResult(exit_code=0, output_dir=output_dir, evidence_path=evidence_path)

    monkeypatch.setattr("gbs_patch_suggest.cli.run_analyzer_for_buildlog", fake_run_analyzer)

    result = run_patch_suggest(
        PatchSuggestOptions(
            buildlog_path=buildlog,
            output_dir=output_dir,
            src_root=expected_src_root,
            analyzer_extra_pythonpath=(extra_path,),
        )
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["inputs"]["buildlog"] == str(buildlog)  # type: ignore[index]
    assert meta["inputs"]["evidence_json"] == str(  # type: ignore[index]
        output_dir / "analyzer_output" / "evidence_packet.json"
    )


def test_buildlog_mode_reports_analyzer_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    buildlog = tmp_path / "build.log"
    buildlog.write_text("compiler error", encoding="utf-8")

    def fake_run_analyzer(*_: object, **__: object) -> AnalyzerRunResult:
        return AnalyzerRunResult(
            exit_code=EXIT_FATAL,
            output_dir=tmp_path / "out" / "analyzer_output",
            evidence_path=tmp_path / "out" / "analyzer_output" / "evidence_packet.json",
            error="gbs_analyzer exited with 7",
        )

    monkeypatch.setattr("gbs_patch_suggest.cli.run_analyzer_for_buildlog", fake_run_analyzer)

    result = run_patch_suggest(
        PatchSuggestOptions(buildlog_path=buildlog, output_dir=tmp_path / "out")
    )

    assert result.exit_code == EXIT_FATAL
    assert result.error == "gbs_analyzer exited with 7"


def test_large_scale_cluster_writes_overview_and_per_file_contexts(tmp_path: Path) -> None:
    packet = compiler_packet(kind="werror", message="enum cast [-Werror,-Wimplicit-enum-enum-cast]")
    add_error_cluster(
        packet,
        tmp_path,
        locations=[
            {
                "event_id": "E001",
                "kind": "werror",
                "file": "src/device.c",
                "line": 10,
                "column": 5,
                "line_no": 100,
                "message": "device enum cast [-Werror,-Wimplicit-enum-enum-cast]",
            },
            {
                "event_id": "E002",
                "kind": "werror",
                "file": "src/device.c",
                "line": 13,
                "column": 5,
                "line_no": 103,
                "message": "device enum cast 2 [-Werror,-Wimplicit-enum-enum-cast]",
            },
            {
                "event_id": "E003",
                "kind": "werror",
                "file": "src/adapter.c",
                "line": 20,
                "column": 7,
                "line_no": 120,
                "message": "adapter enum cast [-Werror,-Wimplicit-enum-enum-cast]",
            },
        ],
    )
    evidence_path = write_packet(tmp_path, packet)
    src_root = tmp_path / "srcroot"
    write_source(src_root, "src/device.c", lines=40)
    write_source(src_root, "src/adapter.c", lines=40)
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    assert result.status == "cluster_context_available"
    meta = read_meta(output_dir)
    assert meta["mode"] == "cluster"
    assert meta["status"] == "cluster_context_available"
    assert (output_dir / "cluster_context").is_dir()
    overview = read_context(output_dir)
    assert "Do not load every per-file context at once" in overview
    assert "Do not read the raw buildlog" in overview
    assert "not visible in evidence" in overview
    file_contexts = sorted((output_dir / "cluster_context").glob("CL001_*/files/*.md"))
    assert len(file_contexts) == 2
    device_context = next(path for path in file_contexts if "device" in path.name)
    text = device_context.read_text(encoding="utf-8")
    assert "line `10:5`" in text
    assert "line `13:5`" in text
    assert "src/device.c line 10" in text
    assert "Generated Edit Spec Skeleton" in text
    assert "Fill every `<FILL_REPLACEMENT_LINE>` value" in text
    assert "candidate_CL001_001" in text
    edit_specs = sorted((device_context.parents[1] / "edit_specs").glob("*.json"))
    assert edit_specs
    skeleton = json.loads(edit_specs[0].read_text(encoding="utf-8"))
    assert skeleton["schema_version"] == EDIT_SPEC_SCHEMA
    assert skeleton["edits"][0]["file"] == "src/device.c"
    assert skeleton["edits"][0]["line"] == 10
    assert skeleton["edits"][0]["old"] == "src/device.c line 10"
    assert skeleton["edits"][0]["new"] == "<FILL_REPLACEMENT_LINE>"


def test_cluster_edit_spec_skeleton_preserves_tabs_and_formats_patch(
    tmp_path: Path,
) -> None:
    packet = compiler_packet(kind="werror", message="enum cast [-Werror,-Wenum-conversion]")
    add_error_cluster(
        packet,
        tmp_path,
        warning_option="-Wenum-conversion",
        locations=[
            {
                "event_id": "E001",
                "kind": "werror",
                "file": "src/device.c",
                "line": 3,
                "column": 12,
                "line_no": 100,
                "message": "enum cast [-Werror,-Wenum-conversion]",
            }
        ],
    )
    evidence_path = write_packet(tmp_path, packet)
    src_root = tmp_path / "srcroot"
    source = src_root / "src" / "device.c"
    source.parent.mkdir(parents=True)
    source.write_text(
        "\n".join(
            [
                "int demo(void)",
                "{",
                "\t\terror_code = old_status;",
                "\t\treturn error_code;",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    skeleton_path = next(output_dir.glob("cluster_context/*/edit_specs/*.json"))
    skeleton = json.loads(skeleton_path.read_text(encoding="utf-8"))
    assert skeleton["edits"] == [
        {
            "file": "src/device.c",
            "line": 3,
            "old": "\t\terror_code = old_status;",
            "new": "<FILL_REPLACEMENT_LINE>",
        }
    ]

    skeleton["edits"][0]["new"] = "\t\terror_code = new_status;"
    filled_spec = tmp_path / "filled_edit_spec.json"
    filled_spec.write_text(json.dumps(skeleton), encoding="utf-8")
    patch_path = tmp_path / "candidate.patch"

    formatted = format_patch(
        FormatPatchOptions(
            src_root=src_root,
            edit_spec=filled_spec,
            output=patch_path,
            check=True,
        )
    )

    assert formatted.exit_code == 0
    assert formatted.check_passed is True
    patch_text = patch_path.read_text(encoding="utf-8")
    assert "-\t\terror_code = old_status;" in patch_text
    assert "+\t\terror_code = new_status;" in patch_text


def test_cluster_edit_spec_skeleton_deduplicates_same_line_locations(
    tmp_path: Path,
) -> None:
    packet = compiler_packet(kind="werror")
    add_error_cluster(
        packet,
        tmp_path,
        locations=[
            {
                "event_id": "E001",
                "kind": "werror",
                "file": "src/device.c",
                "line": 10,
                "column": 5,
                "line_no": 100,
                "message": "first enum cast",
            },
            {
                "event_id": "E002",
                "kind": "werror",
                "file": "src/device.c",
                "line": 10,
                "column": 25,
                "line_no": 100,
                "message": "second enum cast on same line",
            },
        ],
    )
    evidence_path = write_packet(tmp_path, packet)
    src_root = tmp_path / "srcroot"
    write_source(src_root, "src/device.c", lines=20)
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    skeleton_path = next(output_dir.glob("cluster_context/*/edit_specs/*.json"))
    skeleton = json.loads(skeleton_path.read_text(encoding="utf-8"))
    assert len(skeleton["edits"]) == 1
    assert skeleton["edits"][0]["line"] == 10
    file_context = next(output_dir.glob("cluster_context/*/files/*.md"))
    text = file_context.read_text(encoding="utf-8")
    assert "first enum cast" in text
    assert "second enum cast on same line" in text
    assert text.count("line `10` covers:") == 1


def test_cluster_edit_spec_skeleton_skips_missing_line_text(tmp_path: Path) -> None:
    packet = compiler_packet(kind="werror")
    add_error_cluster(
        packet,
        tmp_path,
        locations=[
            {
                "event_id": "E001",
                "kind": "werror",
                "file": "src/device.c",
                "line": 99,
                "column": 5,
                "line_no": 100,
                "message": "line is beyond source file",
            }
        ],
    )
    evidence_path = write_packet(tmp_path, packet)
    src_root = tmp_path / "srcroot"
    write_source(src_root, "src/device.c", lines=5)
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    assert not list(output_dir.glob("cluster_context/*/edit_specs/*.json"))
    meta = read_meta(output_dir)
    file_meta = meta["clusters"][0]["files"][0]  # type: ignore[index]
    assert file_meta["edit_spec_json"] is None
    assert file_meta["missing_line_text"] == [
        {"column": 5, "line": 99, "message": "line is beyond source file"}
    ]
    file_context = next(output_dir.glob("cluster_context/*/files/*.md"))
    text = file_context.read_text(encoding="utf-8")
    assert "Missing Line Text" in text
    assert "no skeleton edit was generated" in text


def test_large_scale_cluster_sidecar_missing_falls_back_to_single_with_advisory(
    tmp_path: Path,
) -> None:
    packet = compiler_packet()
    packet["error_clusters"] = {
        "schema_version": "error_clusters/v1",
        "truncated": False,
        "truncation_signals": [],
        "full_locations_path": "missing_error_clusters.json",
        "clusters": [
            {
                "id": "CL001",
                "kind": "source_warning_option",
                "diagnostic_kinds": ["werror"],
                "warning_option": "-Wimplicit-enum-enum-cast",
                "count": 55,
                "file_count": 11,
                "large_scale": True,
            }
        ],
    }
    evidence_path = write_packet(tmp_path, packet)
    output_dir = tmp_path / "out"

    result = run_patch_suggest(PatchSuggestOptions(evidence_path, output_dir=output_dir))

    assert result.exit_code == 0
    assert result.status == "source_context_unavailable"
    assert not (output_dir / "cluster_context").exists()
    meta = read_meta(output_dir)
    assert "cluster_sidecar_unavailable" in str(meta["cluster_advisory"])
    assert "cluster_sidecar_unavailable" in read_readme(output_dir)


def test_non_large_scale_cluster_uses_single_diagnostic_flow(tmp_path: Path) -> None:
    packet = compiler_packet(
        source_snippet={
            "path": "src/demo.c",
            "start_line": 1,
            "end_line": 1,
            "text": "int x;",
        }
    )
    add_error_cluster(packet, tmp_path, large_scale=False)
    evidence_path = write_packet(tmp_path, packet)
    output_dir = tmp_path / "out"

    result = run_patch_suggest(PatchSuggestOptions(evidence_path, output_dir=output_dir))

    assert result.exit_code == 0
    assert result.status == "source_context_available"
    assert not (output_dir / "cluster_context").exists()
    assert "mode" not in read_meta(output_dir)


def test_cluster_context_marks_ambiguous_source_candidates(tmp_path: Path) -> None:
    packet = compiler_packet(kind="werror")
    add_error_cluster(packet, tmp_path)
    evidence_path = write_packet(tmp_path, packet)
    src_root = tmp_path / "src"
    write_source(src_root, "a/src/device.c", lines=20)
    write_source(src_root, "b/src/device.c", lines=20)
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    file_meta = meta["clusters"][0]["files"][0]  # type: ignore[index]
    assert file_meta["status"] == "source_context_ambiguous"
    file_context = next((output_dir / "cluster_context").glob("CL001_*/files/*.md"))
    text = file_context.read_text(encoding="utf-8")
    assert "Candidate source matches" in text
    assert "Choose the correct file" in text


def test_cluster_window_merges_close_ranges_and_truncates_large_context(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    write_source(src_root, "src/dpm.c", lines=1000)
    cluster = LargeScaleCluster(
        id="CL001",
        warning_option="-Wimplicit-enum-enum-cast",
        diagnostic_kinds=("werror",),
        truncated=True,
        locations=tuple(
            ClusterLocation(
                event_id=f"E{index:03d}",
                kind="werror",
                file="src/dpm.c",
                line=line,
                column=None,
                line_no=None,
                message="enum cast",
            )
            for index, line in enumerate([20, 25, *range(100, 700, 20)], start=1)
        ),
    )

    resolved = resolve_clusters((cluster,), src_root=src_root)

    file_context = resolved[0].file_contexts[0]
    assert file_context.source_windows[0].diagnostic_lines == (20, 25)
    assert file_context.source_windows_truncated is True
    total_lines = sum(
        window.end_line - window.start_line + 1 for window in file_context.source_windows
    )
    assert total_lines <= 400


def test_multiple_large_scale_clusters_get_independent_directories(tmp_path: Path) -> None:
    packet = compiler_packet(kind="werror")
    packet["error_clusters"] = {
        "schema_version": "error_clusters/v1",
        "truncated": False,
        "truncation_signals": [],
        "full_locations_path": "error_clusters.json",
        "clusters": [
            {
                "id": "CL001",
                "kind": "source_warning_option",
                "diagnostic_kinds": ["werror"],
                "warning_option": "-Wone",
                "count": 10,
                "file_count": 1,
                "large_scale": True,
            },
            {
                "id": "CL002",
                "kind": "source_warning_option",
                "diagnostic_kinds": ["compiler"],
                "warning_option": "-Wtwo",
                "count": 10,
                "file_count": 1,
                "large_scale": True,
            },
        ],
    }
    (tmp_path / "error_clusters.json").write_text(
        json.dumps(
            {
                "schema_version": "error_clusters_locations/v1",
                "clusters": [
                    {
                        "id": "CL001",
                        "warning_option": "-Wone",
                        "locations": [
                            {
                                "kind": "werror",
                                "file": "src/one.c",
                                "line": 5,
                                "message": "one",
                            }
                        ],
                    },
                    {
                        "id": "CL002",
                        "warning_option": "-Wtwo",
                        "locations": [
                            {
                                "kind": "compiler",
                                "file": "src/two.c",
                                "line": 6,
                                "message": "two",
                            }
                        ],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    evidence_path = write_packet(tmp_path, packet)
    src_root = tmp_path / "srcroot"
    write_source(src_root, "src/one.c")
    write_source(src_root, "src/two.c")

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=tmp_path / "out", src_root=src_root)
    )

    assert result.exit_code == 0
    dirs = sorted(path.name for path in (tmp_path / "out" / "cluster_context").iterdir())
    assert dirs == ["CL001_-Wone", "CL002_-Wtwo"]


def test_level_b_reports_file_line_without_source_context(tmp_path: Path) -> None:
    evidence_path = write_packet(tmp_path, compiler_packet())
    output_dir = tmp_path / "out"

    result = run_patch_suggest(PatchSuggestOptions(evidence_path, output_dir=output_dir))

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_unavailable"
    assert meta["level"] == "B"
    assert meta["has_source_context"] is False
    context = read_context(output_dir)
    assert "Source context for `src/demo.c:12` is unavailable" in context
    assert "First open the reported file and inspect the source around the reported line" in context
    assert "write each one as an edit spec" in context
    assert "reported error may be a symptom, not the root cause" in context
    assert "Search the source tree" in context
    assert "edit_spec_N.json" in context
    assert "candidate_N.patch" in context
    assert "format-patch" in context
    assert "Do NOT fall back to hand-writing a unified diff" in context
    assert "Writing the file and applying are completely separate actions" in context
    assert "Do NOT run `git apply` / `patch`" in context
    assert not list(output_dir.glob("*.patch"))


def test_suffix_search_unique_match_upgrades_to_level_a(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    write_source(src_root, "gst-libs/ext/ffmpeg/libavcodec/utils.c")
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file="libavcodec/utils.c", line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_available"
    assert meta["level"] == "A"
    assert meta["source_context"]["origin"] == "src_root_suffix_search"  # type: ignore[index]
    context = read_context(output_dir)
    assert "gst-libs/ext/ffmpeg/libavcodec/utils.c line 12" in context


def test_suffix_search_zero_match_stays_level_b(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    write_source(src_root, "other/utils.c")
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file="libavcodec/utils.c", line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_unavailable"
    assert meta["level"] == "B"
    assert meta["candidate_paths"] == []


def test_suffix_search_multiple_matches_stays_level_b_with_candidates(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    first = write_source(src_root, "a/libavcodec/utils.c")
    second = write_source(src_root, "b/libavcodec/utils.c")
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file="libavcodec/utils.c", line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_ambiguous"
    assert meta["level"] == "B"
    candidate_paths = cast(list[str], meta["candidate_paths"])
    assert set(candidate_paths) == {str(first), str(second)}
    context = read_context(output_dir)
    assert "Candidate matches found" in context
    assert "Do not choose a source file blindly" in context
    assert "decide which file matches the diagnostic" in context
    assert "Do not silently keep an unverified symbol" in context


def test_suffix_search_uses_path_segment_alignment(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    write_source(src_root, "mylibavcodec/utils.c")
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file="libavcodec/utils.c", line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_unavailable"
    assert meta["candidate_paths"] == []


def test_suffix_search_skips_heavy_directories(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    write_source(src_root, ".git/libavcodec/utils.c")
    write_source(src_root, "GBS-ROOT-LOCAL/libavcodec/utils.c")
    write_source(src_root, "build/libavcodec/utils.c")
    write_source(src_root, ".gbs_workflow/libavcodec/utils.c")
    write_source(src_root, ".gbs_patch_suggest/libavcodec/utils.c")
    write_source(src_root, "node_modules/libavcodec/utils.c")
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file="libavcodec/utils.c", line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_unavailable"
    assert meta["candidate_paths"] == []


def test_absolute_path_inside_src_root_upgrades_to_level_a(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    source = write_source(src_root, "libavcodec/utils.c")
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file=str(source), line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_available"
    assert meta["level"] == "A"


def test_absolute_path_outside_src_root_stays_level_b(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    outside = write_source(tmp_path / "outside", "libavcodec/utils.c")
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file=str(outside), line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_unavailable"
    assert meta["candidate_paths"] == []


def test_absolute_path_missing_stays_level_b(tmp_path: Path) -> None:
    src_root = tmp_path / "src"
    src_root.mkdir()
    evidence_path = write_packet(
        tmp_path,
        compiler_packet(file=str(src_root / "libavcodec" / "missing.c"), line=12),
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(evidence_path, output_dir=output_dir, src_root=src_root)
    )

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "source_context_unavailable"


def test_level_c_reports_diagnostic_only_without_file_line(tmp_path: Path) -> None:
    evidence_path = write_packet(tmp_path, compiler_packet(file=None, line=None))
    output_dir = tmp_path / "out"

    result = run_patch_suggest(PatchSuggestOptions(evidence_path, output_dir=output_dir))

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "diagnostic_only"
    assert meta["level"] == "C"
    context = read_context(output_dir)
    assert "has no usable file and line number" in context
    assert "Do not generate a patch from this diagnostic alone" in context
    assert MANDATORY_INSTRUCTIONS.strip() in context
    assert not list(output_dir.glob("*.patch"))


@pytest.mark.parametrize("kind", ["depsolve", "linker_undef", "patch", "rpm_phase"])
def test_non_source_diagnostic_packet_is_not_applicable(tmp_path: Path, kind: str) -> None:
    evidence_path = write_packet(
        tmp_path,
        {
            "primary_error": {"kind": kind, "message": "not source-fixable here"},
            "root_cause_candidates": [],
            "evidence": {},
        },
    )
    output_dir = tmp_path / "out"

    result = run_patch_suggest(PatchSuggestOptions(evidence_path, output_dir=output_dir))

    assert result.exit_code == 0
    meta = read_meta(output_dir)
    assert meta["status"] == "not_applicable"
    assert meta["applicable"] is False
    context = read_context(output_dir)
    assert "this skill is not applicable" in context
    assert "compiler and Werror source diagnostics" in context
    assert "Use the workflow suggester for this fault class" in context
    assert not list(output_dir.glob("*.patch"))


def test_cli_rejects_missing_evidence(tmp_path: Path) -> None:
    code = main(["--evidence", str(tmp_path / "missing.json"), "--output-dir", str(tmp_path)])

    assert code == EXIT_EVIDENCE_UNREADABLE


def test_cli_requires_exactly_one_input(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence_packet.json"
    buildlog = tmp_path / "build.log"
    with pytest.raises(SystemExit) as missing:
        main(["--output-dir", str(tmp_path)])
    assert missing.value.code == 2

    with pytest.raises(SystemExit) as both:
        main(["--evidence", str(evidence), "--buildlog", str(buildlog)])
    assert both.value.code == 2


def test_run_analyzer_for_buildlog_command_and_output(tmp_path: Path) -> None:
    buildlog = tmp_path / "build.log"
    buildlog.write_text("compiler error", encoding="utf-8")
    output_dir = tmp_path / "analyzer"
    commands: list[list[str]] = []

    def fake_runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        assert kwargs["check"] is True
        assert kwargs["text"] is True
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "evidence_packet.json").write_text(
            json.dumps(compiler_packet()),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0)

    result = run_analyzer_for_buildlog(
        buildlog,
        output_dir=output_dir,
        python_executable="python-test",
        subprocess_runner=fake_runner,
    )

    assert result.exit_code == 0
    assert result.evidence_path == output_dir / "evidence_packet.json"
    assert commands == [
        [
            "python-test",
            "-m",
            "gbs_analyzer",
            "analyze",
            str(buildlog),
            "--output-dir",
            str(output_dir),
        ]
    ]


def test_run_analyzer_for_buildlog_passes_src_root_and_extra_pythonpath(tmp_path: Path) -> None:
    buildlog = tmp_path / "build.log"
    buildlog.write_text("compiler error", encoding="utf-8")
    output_dir = tmp_path / "analyzer"
    src_root = tmp_path / "src"
    src_root.mkdir()
    extra = tmp_path / "scripts"

    def fake_runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert command[-2:] == ["--src-root", str(src_root)]
        env = kwargs["env"]
        assert isinstance(env, dict)
        assert env["PYTHONPATH"].split(os.pathsep)[0] == str(extra)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "evidence_packet.json").write_text(
            json.dumps(compiler_packet()),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0)

    result = run_analyzer_for_buildlog(
        buildlog,
        output_dir=output_dir,
        src_root=src_root,
        subprocess_runner=fake_runner,
        extra_pythonpath=(extra,),
    )

    assert result.exit_code == 0


def test_run_analyzer_for_buildlog_reports_failure_and_missing_evidence(tmp_path: Path) -> None:
    buildlog = tmp_path / "build.log"
    buildlog.write_text("compiler error", encoding="utf-8")
    output_dir = tmp_path / "analyzer"

    def failing_runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(9, command)

    failed = run_analyzer_for_buildlog(
        buildlog,
        output_dir=output_dir,
        subprocess_runner=failing_runner,
    )
    assert failed.exit_code == EXIT_FATAL
    assert failed.error == "gbs_analyzer exited with 9"

    def missing_evidence_runner(
        command: list[str],
        **_: object,
    ) -> subprocess.CompletedProcess[str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        return subprocess.CompletedProcess(command, 0)

    missing = run_analyzer_for_buildlog(
        buildlog,
        output_dir=output_dir,
        subprocess_runner=missing_evidence_runner,
    )
    assert missing.exit_code == EXIT_EVIDENCE_UNREADABLE
    assert "did not write evidence_packet.json" in (missing.error or "")


def test_analyzer_subprocess_env_prepends_without_polluting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extra = tmp_path / "extra"
    monkeypatch.setenv("PYTHONPATH", "existing")

    env = build_analyzer_subprocess_env((extra,))

    assert env is not None
    assert env["PYTHONPATH"] == f"{extra}{os.pathsep}existing"
    assert os.environ["PYTHONPATH"] == "existing"


def test_discover_analyzer_pythonpath_from_env_and_sibling(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analyzer_root = tmp_path / "custom-analyzer"
    analyzer_scripts = analyzer_root / "scripts"
    (analyzer_scripts / "gbs_analyzer").mkdir(parents=True)
    monkeypatch.setenv(ANALYZER_SKILL_ENV, str(analyzer_root))

    assert discover_analyzer_pythonpath() == (analyzer_scripts.resolve(),)

    monkeypatch.delenv(ANALYZER_SKILL_ENV)
    patch_scripts = tmp_path / "tizen-gbs-patch-suggest" / "scripts"
    patch_scripts.mkdir(parents=True)
    launcher = patch_scripts / "run_patch_suggest.py"
    launcher.write_text("", encoding="utf-8")
    sibling_scripts = tmp_path / "tizen-gbs-log-analysis" / "scripts"
    (sibling_scripts / "gbs_analyzer").mkdir(parents=True)

    assert discover_analyzer_pythonpath(launcher_path=launcher) == (sibling_scripts,)
