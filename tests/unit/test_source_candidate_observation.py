from pathlib import Path

from gbs_analyzer.source_candidate_observation import build_source_candidate_observation
from gbs_analyzer.source_candidates import build_source_candidates


def event(
    event_id: str,
    *,
    kind: str = "werror",
    severity: str = "error",
    message: str = "private field 'metadata' is not used [-Werror,-Wunused-private-field]",
    file: str | None = "src/OutputMetadata.h",
    line: int | None = 10,
    column: int | None = 5,
) -> dict[str, object]:
    data: dict[str, object] = {
        "id": event_id,
        "kind": kind,
        "severity": severity,
        "message": message,
        "line_no": int(event_id[1:]),
    }
    if file is not None:
        data["file"] = file
    if line is not None:
        data["line"] = line
    if column is not None:
        data["column"] = column
    return data


def packet(events: list[dict[str, object]]) -> dict[str, object]:
    return {"schema_version": "scan_result/v1", "events": events}


def inference_engine_events() -> list[dict[str, object]]:
    deprecated = "warning: function is deprecated [-Werror,-Wdeprecated-declarations]"
    return [
        event(
            "E011",
            file="/home/abuild/rpmbuild/BUILD/inference-engine-1.0/src/OutputMetadata.h",
        ),
        event(
            "E012",
            message=deprecated,
            file="/home/abuild/rpmbuild/BUILD/inference-engine-1.0/src/profiler.cpp",
            line=20,
        ),
        event(
            "E013",
            message=deprecated,
            file="/home/abuild/rpmbuild/BUILD/inference-engine-1.0/src/profiler.cpp",
            line=30,
        ),
        event(
            "E014",
            message=deprecated,
            file="/home/abuild/rpmbuild/BUILD/inference-engine-1.0/src/profiler.cpp",
            line=40,
        ),
        event(
            "E015",
            message=deprecated,
            file="/home/abuild/rpmbuild/BUILD/inference-engine-1.0/src/tc.cpp",
            line=50,
        ),
        event(
            "E016",
            message=deprecated,
            file="/home/abuild/rpmbuild/BUILD/inference-engine-1.0/src/tc.cpp",
            line=60,
        ),
        event(
            "E017",
            message=deprecated,
            file="/home/abuild/rpmbuild/BUILD/inference-engine-1.0/src/tc.cpp",
            line=70,
        ),
        event(
            "E019",
            message=deprecated,
            file="/home/abuild/rpmbuild/BUILD/inference-engine-1.0/src/tc.cpp",
            line=80,
        ),
    ]


def write_buildlog(path: Path, events: list[dict[str, object]]) -> None:
    lines = [
        (
            f"{item['file']}:{item['line']}:{item['column']}: error: "
            f"{item['message']}"
        )
        for item in events
        if item.get("file") and item.get("line") and item.get("column")
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def inference_engine_packet() -> dict[str, object]:
    return {
        "primary_error": inference_engine_events()[0],
        "root_cause_candidates": [
            {
                "event_id": "E011",
                "kind": "werror",
                "is_terminal": True,
                "file": "/home/abuild/rpmbuild/BUILD/inference-engine-1.0/src/OutputMetadata.h",
                "line": 10,
                "message": "private field 'metadata' is not used [-Werror,-Wunused-private-field]",
            }
        ],
        "error_clusters": {
            "schema_version": "error_clusters/v1",
            "truncated": False,
            "full_locations_path": "error_clusters.json",
            "clusters": [
                {
                    "id": "CL001",
                    "kind": "source_warning_option",
                    "diagnostic_kinds": ["werror"],
                    "warning_option": "-Wdeprecated-declarations",
                    "count": 7,
                    "file_count": 2,
                    "large_scale": False,
                }
            ],
        },
    }


def inference_engine_cluster_sidecar() -> dict[str, object]:
    return {
        "schema_version": "error_clusters_locations/v1",
        "clusters": [
            {
                "id": "CL001",
                "warning_option": "-Wdeprecated-declarations",
                "locations": inference_engine_events()[1:],
            }
        ],
    }


def test_observation_reports_inference_engine_old_path_gap(tmp_path: Path) -> None:
    events = inference_engine_events()
    source_candidates = build_source_candidates(packet(events), src_root=Path("/missing"))
    buildlog = tmp_path / "build.log"
    write_buildlog(buildlog, events)

    observation = build_source_candidate_observation(
        packet=inference_engine_packet(),
        scan_result=packet(events),
        buildlog_path=buildlog,
        source_candidate_sidecar=source_candidates.sidecar,
        error_cluster_sidecar=inference_engine_cluster_sidecar(),
    )

    coverage = observation["coverage_diff"]
    assert coverage["old_path_decision"]["selected_branch"] == "single"
    assert coverage["old_path_decision"]["fallback_reasons"] == {
        "cluster": "large_scale_false",
        "multi": "candidates_lt_2",
    }
    assert coverage["old_path_decision"]["sidecar_readable"] is None
    assert coverage["counts"] == {
        "sidecar_diagnostics": 8,
        "old_path_covered": 1,
        "missed_by_old": 7,
        "extra_by_old": 0,
    }
    assert {item["event_id"] for item in coverage["missed_by_old"]} == {
        "E012",
        "E013",
        "E014",
        "E015",
        "E016",
        "E017",
        "E019",
    }
    stats = observation["type_source_stats"]
    assert stats["type_unknown_by_reason"] == {}
    assert stats["source_unreachable_by_status"] == {"source_mapping_unavailable": 8}


def test_observation_selects_cluster_when_large_scale_sidecar_is_usable(
    tmp_path: Path,
) -> None:
    events = [
        event(f"E{index:03d}", file=f"src/file{index}.c", line=index)
        for index in range(1, 11)
    ]
    source_candidates = build_source_candidates(packet(events), src_root=Path("/missing"))
    buildlog = tmp_path / "build.log"
    write_buildlog(buildlog, events)

    observation = build_source_candidate_observation(
        packet={
            "primary_error": events[0],
            "error_clusters": {
                "schema_version": "error_clusters/v1",
                "full_locations_path": "error_clusters.json",
                "clusters": [
                    {
                        "id": "CL001",
                        "kind": "source_warning_option",
                        "diagnostic_kinds": ["werror"],
                        "warning_option": "-Wunused-private-field",
                        "large_scale": True,
                    }
                ],
            },
        },
        scan_result=packet(events),
        buildlog_path=buildlog,
        source_candidate_sidecar=source_candidates.sidecar,
        error_cluster_sidecar={
            "schema_version": "error_clusters_locations/v1",
            "clusters": [
                {
                    "id": "CL001",
                    "warning_option": "-Wunused-private-field",
                    "locations": events,
                }
            ],
        },
    )

    coverage = observation["coverage_diff"]
    assert coverage["old_path_decision"]["selected_branch"] == "cluster"
    assert coverage["old_path_decision"]["sidecar_readable"] is True
    assert coverage["counts"]["old_path_covered"] == 10
    assert coverage["counts"]["missed_by_old"] == 0


def test_observation_selects_multi_when_two_terminal_candidates_exist(
    tmp_path: Path,
) -> None:
    events = [
        event("E001", file="src/a.c", line=1),
        event("E002", file="src/b.c", line=2),
    ]
    source_candidates = build_source_candidates(packet(events), src_root=Path("/missing"))
    buildlog = tmp_path / "build.log"
    write_buildlog(buildlog, events)

    observation = build_source_candidate_observation(
        packet={
            "primary_error": events[0],
            "root_cause_candidates": [
                {
                    "event_id": item["id"],
                    "kind": item["kind"],
                    "is_terminal": True,
                    "file": item["file"],
                    "line": item["line"],
                    "message": item["message"],
                }
                for item in events
            ],
        },
        scan_result=packet(events),
        buildlog_path=buildlog,
        source_candidate_sidecar=source_candidates.sidecar,
        error_cluster_sidecar=None,
    )

    coverage = observation["coverage_diff"]
    assert coverage["old_path_decision"]["selected_branch"] == "multi"
    assert coverage["old_path_decision"]["fallback_reasons"] == {
        "cluster": "no_error_clusters"
    }
    assert coverage["counts"]["old_path_covered"] == 2
    assert coverage["counts"]["missed_by_old"] == 0


def test_extra_by_old_marks_excluded_diagnostic_destination(tmp_path: Path) -> None:
    missing_line = event("E001", file="src/foo.c", line=None)
    source_candidates = build_source_candidates(packet([missing_line]), src_root=None)
    buildlog = tmp_path / "build.log"
    buildlog.write_text("src/foo.c:10:5: error: nope\n", encoding="utf-8")

    observation = build_source_candidate_observation(
        packet={
            "primary_error": {
                "id": "E001",
                "kind": "werror",
                "file": "src/foo.c",
                "message": "missing line [-Werror,-Wunused-private-field]",
            },
        },
        scan_result=packet([missing_line]),
        buildlog_path=buildlog,
        source_candidate_sidecar=source_candidates.sidecar,
        error_cluster_sidecar=None,
    )

    extra = observation["coverage_diff"]["extra_by_old"]
    assert len(extra) == 1
    assert extra[0]["new_sidecar_location"] == "excluded_source_diagnostics"
    assert extra[0]["exclusion_reason"] == "missing_line"


def test_extra_by_old_marks_nonfatal_warning_gate_reason(tmp_path: Path) -> None:
    warning = event(
        "E018",
        kind="compiler",
        severity="warning",
        message="unused variable 'ret' [-Wunused-variable]",
        file="libavcodec/h264_parse.c",
        line=175,
        column=9,
    )
    source_candidates = build_source_candidates(packet([warning]), src_root=Path("/missing"))
    buildlog = tmp_path / "build.log"
    write_buildlog(buildlog, [warning])

    observation = build_source_candidate_observation(
        packet={
            "primary_error": warning,
            "root_cause_candidates": [
                {
                    "event_id": "E001",
                    "kind": "compiler",
                    "is_terminal": True,
                    "file": "src/other.c",
                    "line": 1,
                    "message": "other error",
                },
                {
                    "event_id": "E018",
                    "kind": "compiler",
                    "is_terminal": True,
                    "file": "libavcodec/h264_parse.c",
                    "line": 175,
                    "message": "unused variable 'ret' [-Wunused-variable]",
                },
            ],
        },
        scan_result=packet([warning]),
        buildlog_path=buildlog,
        source_candidate_sidecar=source_candidates.sidecar,
        error_cluster_sidecar=None,
    )

    extra = observation["coverage_diff"]["extra_by_old"]
    assert len(extra) == 2
    by_event = {item["diagnostic"]["event_id"]: item for item in extra}
    assert by_event["E018"]["new_sidecar_location"] == "not_source_candidate_eligible"
    assert by_event["E018"]["exclusion_reason"] == "not_fatal_or_werror"


def test_scanner_gap_counts_only_source_located_fatal_like_lines(tmp_path: Path) -> None:
    structured = event(
        "E001",
        file="src/seen.c",
        line=1,
        column=2,
        message="seen [-Werror,-Wdeprecated-declarations]",
    )
    buildlog = tmp_path / "build.log"
    buildlog.write_text(
        "\n".join(
            [
                "src/seen.c:1:2: error: seen [-Werror,-Wdeprecated-declarations]",
                "src/missed.c:2:3: warning: missed [-Werror,-Wdeprecated-declarations]",
                "error: wrapper summary without source location",
                "ld: error: linker problem",
                "",
            ]
        ),
        encoding="utf-8",
    )

    observation = build_source_candidate_observation(
        packet={"primary_error": structured},
        scan_result=packet([structured]),
        buildlog_path=buildlog,
        source_candidate_sidecar={
            "schema_version": "source_candidate_sidecar/v1",
            "candidates": [],
        },
        error_cluster_sidecar=None,
    )

    gap = observation["scanner_coverage_gap"]
    assert gap["raw_diagnostic_like_line_count"] == 2
    assert gap["structured_event_count"] == 1
    assert gap["unmatched_diagnostic_like_line_count"] == 1
    assert gap["unmatched_categories"] == {"werror_promoted": 1}
