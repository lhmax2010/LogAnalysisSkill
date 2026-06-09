from pathlib import Path

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
    command_id: str | None = "C001",
    parent: str | None = None,
) -> dict[str, object]:
    data: dict[str, object] = {
        "id": event_id,
        "kind": kind,
        "severity": severity,
        "message": message,
        "line_no": int(event_id[1:]),
        "phase": "%build",
    }
    if file is not None:
        data["file"] = file
    if line is not None:
        data["line"] = line
    if column is not None:
        data["column"] = column
    if command_id is not None:
        data["command_id"] = command_id
    if parent is not None:
        data["parent"] = parent
    return data


def packet(events: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": "scan_result/v1",
        "failed_phase": "%build",
        "events": events,
    }


def write_source(src_root: Path, relative: str) -> None:
    path = src_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("int placeholder;\n", encoding="utf-8")


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


def test_unused_field_werror_singleton_becomes_type_probably_fixable(
    tmp_path: Path,
) -> None:
    write_source(tmp_path, "src/OutputMetadata.h")
    result = build_source_candidates(
        packet(
            [
                event(
                    "E011",
                    file="/home/abuild/rpmbuild/BUILD/inference-engine-1.0/src/OutputMetadata.h",
                )
            ]
        ),
        src_root=tmp_path,
    )

    assert result.summary is not None
    assert result.summary["candidate_count"] == 1
    assert result.summary["structured_source_candidate_count"] == 1
    assert result.summary["type_probably_fixable_count"] == 1
    assert result.summary["source_reachable_count"] == 1
    assert result.summary["source_owned_count"] == 1
    assert result.summary["patch_ready_count"] == 1
    assert result.sidecar is not None
    candidate = result.sidecar["candidates"][0]
    assert candidate["event_id"] == "E011"
    assert candidate["warning_option"] == "-Wunused-private-field"
    assert candidate["warning_option_source"] == "message_regex"
    assert candidate["normalized_file"] == "src/OutputMetadata.h"
    assert candidate["type_fixability"] == "probably_fixable"
    assert candidate["type_fixability_reason"] == (
        "whitelisted_warning_option:-Wunused-private-field"
    )
    assert candidate["source_reachable"] is True
    assert candidate["source_resolution_status"] == "mapped_to_source_root"
    assert candidate["source_owned"] is True
    assert candidate["source_ownership_status"] == "project_owned"


def test_type_fixability_is_independent_from_local_source_mapping() -> None:
    result = build_source_candidates(packet(inference_engine_events()), src_root=Path("/missing"))

    assert result.summary is not None
    assert result.summary["structured_source_candidate_count"] == 8
    assert result.summary["candidate_count"] == 8
    assert result.summary["type_probably_fixable_count"] == 8
    assert result.summary["source_reachable_count"] == 0
    assert result.summary["source_owned_count"] == 0
    assert result.summary["patch_ready_count"] == 0
    assert result.sidecar is not None
    candidates = result.sidecar["candidates"]
    assert {candidate["warning_option"] for candidate in candidates} == {
        "-Wunused-private-field",
        "-Wdeprecated-declarations",
    }
    assert {candidate["type_fixability"] for candidate in candidates} == {
        "probably_fixable"
    }
    assert {candidate["source_reachable"] for candidate in candidates} == {False}
    assert {candidate["source_owned"] for candidate in candidates} == {False}
    assert {candidate["source_resolution_status"] for candidate in candidates} == {
        "source_mapping_unavailable"
    }
    assert {candidate["source_ownership_status"] for candidate in candidates} == {
        "unknown"
    }


def test_type_and_source_both_succeed_with_mock_inference_engine_source(
    tmp_path: Path,
) -> None:
    write_source(tmp_path, "src/OutputMetadata.h")
    write_source(tmp_path, "src/profiler.cpp")
    write_source(tmp_path, "src/tc.cpp")

    result = build_source_candidates(packet(inference_engine_events()), src_root=tmp_path)

    assert result.summary is not None
    assert result.summary["type_probably_fixable_count"] == 8
    assert result.summary["source_reachable_count"] == 8
    assert result.summary["source_owned_count"] == 8
    assert result.summary["patch_ready_count"] == 8
    assert result.sidecar is not None
    normalized_files = {candidate["normalized_file"] for candidate in result.sidecar["candidates"]}
    assert normalized_files == {"src/OutputMetadata.h", "src/profiler.cpp", "src/tc.cpp"}


def test_missing_file_or_line_stays_out_of_main_candidates() -> None:
    result = build_source_candidates(
        packet(
            [
                event("E001", file=None, line=1),
                event("E002", file="src/foo.c", line=None),
            ]
        ),
        src_root=None,
    )

    assert result.summary is not None
    assert result.summary["candidate_count"] == 0
    assert result.summary["structured_source_candidate_count"] == 0
    assert result.summary["type_probably_fixable_count"] == 0
    assert result.summary["excluded_summary"] == {
        "missing_file_count": 1,
        "missing_line_count": 1,
        "explicit_parent_count": 0,
    }
    assert result.sidecar is not None
    assert result.sidecar["candidates"] == []
    assert result.sidecar["excluded_source_diagnostics"] == [
        {
            "event_id": "E001",
            "line": 1,
            "exclusion_reason": "missing_file",
        },
        {
            "event_id": "E002",
            "file": "src/foo.c",
            "exclusion_reason": "missing_line",
        },
    ]


def test_excluded_diagnostics_do_not_pollute_candidate_counts() -> None:
    excluded = [
        event(f"E{index:03d}", file=None, line=None)
        for index in range(101, 110)
    ]
    result = build_source_candidates(
        packet([*inference_engine_events(), *excluded]),
        src_root=Path("/missing"),
    )

    assert result.summary is not None
    assert result.summary["structured_source_candidate_count"] == 8
    assert result.summary["candidate_count"] == 8
    assert result.summary["type_probably_fixable_count"] == 8
    assert result.summary["source_reachable_count"] == 0
    assert result.summary["excluded_summary"] == {
        "missing_file_count": 9,
        "missing_line_count": 9,
        "explicit_parent_count": 0,
    }
    assert result.sidecar is not None
    assert len(result.sidecar["candidates"]) == 8
    assert len(result.sidecar["excluded_source_diagnostics"]) == 9


def test_explicit_parent_is_excluded_not_candidate(tmp_path: Path) -> None:
    write_source(tmp_path, "src/foo.c")
    result = build_source_candidates(
        packet([event("E002", file="src/foo.c", parent="E001")]),
        src_root=tmp_path,
    )

    assert result.summary is not None
    assert result.summary["candidate_count"] == 0
    assert result.summary["structured_source_candidate_count"] == 0
    assert result.summary["type_probably_fixable_count"] == 0
    assert result.summary["excluded_summary"]["explicit_parent_count"] == 1
    assert result.sidecar is not None
    assert result.sidecar["candidates"] == []
    assert result.sidecar["excluded_source_diagnostics"] == [
        {
            "event_id": "E002",
            "file": "src/foo.c",
            "line": 10,
            "parent": "E001",
            "exclusion_reason": "explicit_parent",
        }
    ]


def test_plain_warning_does_not_enter_sidecar(tmp_path: Path) -> None:
    write_source(tmp_path, "src/foo.c")
    result = build_source_candidates(
        packet(
            [
                event(
                    "E001",
                    kind="compiler",
                    severity="warning",
                    message="variable 'unused' set but not used [-Wunused-but-set-variable]",
                    file="src/foo.c",
                )
            ]
        ),
        src_root=tmp_path,
    )

    assert result.summary is None
    assert result.sidecar is None


def test_fatal_detection_source_records_fallback() -> None:
    result = build_source_candidates(
        packet(
            [
                event(
                    "E001",
                    kind="compiler",
                    severity="warning",
                    message="address issue [-Werror,-Wpointer-bool-conversion]",
                    file="src/foo.c",
                )
            ]
        ),
        src_root=None,
    )

    assert result.sidecar is not None
    assert result.sidecar["candidates"][0]["fatal_detection_source"] == (
        "werror_message_fallback"
    )


def test_dedupe_key_uses_sentinels_and_degraded_flag(tmp_path: Path) -> None:
    write_source(tmp_path, "src/foo.c")
    result = build_source_candidates(
        packet(
            [
                event(
                    "E001",
                    kind="compiler",
                    message="use of undeclared identifier 'foo'",
                    file="src/foo.c",
                    column=None,
                    command_id=None,
                )
            ]
        ),
        src_root=tmp_path,
    )

    assert result.sidecar is not None
    candidate = result.sidecar["candidates"][0]
    assert candidate["degraded_key"] is True
    assert "column=<unknown>" in candidate["dedupe_key"]
    assert "warning_option=<none>" in candidate["dedupe_key"]
    assert "command_id=<unknown>" in candidate["dedupe_key"]


def test_system_header_is_visible_but_not_owned() -> None:
    result = build_source_candidates(
        packet([event("E001", file="/usr/include/foo.h")]),
        src_root=None,
    )

    assert result.sidecar is not None
    candidate = result.sidecar["candidates"][0]
    assert candidate["type_fixability"] == "probably_fixable"
    assert candidate["source_reachable"] is False
    assert candidate["source_owned"] is False
    assert candidate["source_resolution_status"] == "source_root_unavailable"
    assert candidate["source_ownership_status"] == "system_or_toolchain_path"


def test_generated_or_vendor_source_can_be_reachable_but_not_owned(tmp_path: Path) -> None:
    write_source(tmp_path, "third_party/foo.cpp")
    result = build_source_candidates(
        packet([event("E001", file="third_party/foo.cpp")]),
        src_root=tmp_path,
    )

    assert result.summary is not None
    assert result.summary["type_probably_fixable_count"] == 1
    assert result.summary["source_reachable_count"] == 1
    assert result.summary["source_owned_count"] == 0
    assert result.summary["patch_ready_count"] == 0
    assert result.sidecar is not None
    candidate = result.sidecar["candidates"][0]
    assert candidate["source_reachable"] is True
    assert candidate["source_resolution_status"] == "mapped_to_source_root"
    assert candidate["source_owned"] is False
    assert candidate["source_ownership_status"] == "generated_or_vendor"
