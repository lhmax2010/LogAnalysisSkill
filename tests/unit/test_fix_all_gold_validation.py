import json
from pathlib import Path
from typing import Any

import pytest
from gbs_patch_suggest.cli import PatchSuggestOptions, run_patch_suggest

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / "tests" / "fixtures" / "inference_engine_fix_all"
EXPECTED_GOLD_IDS = {"E011", "E012", "E013", "E015", "E016", "E017", "E018", "E019"}
EXPECTED_GOLD_MISSED_IDS = {"E015", "E016", "E017", "E018", "E019"}


def _load_fixture(name: str) -> dict[str, Any]:
    data = json.loads((GOLD / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _read_meta(output_dir: Path) -> dict[str, Any]:
    data = json.loads((output_dir / "meta.json").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _write_packet(tmp_path: Path, packet: dict[str, Any]) -> Path:
    evidence_path = tmp_path / "evidence_packet.json"
    evidence_path.write_text(json.dumps(packet), encoding="utf-8")
    return evidence_path


def _write_source(root: Path, relative: str, *, lines: int) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(f"{relative} line {line}" for line in range(1, lines + 1)),
        encoding="utf-8",
    )


def _source_candidate(
    event_id: str,
    *,
    file: str,
    normalized_file: str | None = None,
    line: int,
    kind: str = "werror",
    message: str = "fixable source diagnostic [-Werror,-Wdeprecated-declarations]",
    warning_option: str | None = "-Wdeprecated-declarations",
    type_fixability: str = "probably_fixable",
    source_reachable: bool = True,
    source_owned: bool = True,
) -> dict[str, Any]:
    normalized = normalized_file or file
    return {
        "column": 1,
        "dedupe_key": f"{normalized}:{line}:{event_id}",
        "degraded_key": False,
        "event_id": event_id,
        "file": file,
        "kind": kind,
        "line": line,
        "message": message,
        "normalized_file": normalized,
        "semantic_class": "generic_error",
        "source_located": True,
        "source_ownership_status": "project_owned" if source_owned else "unknown",
        "source_owned": source_owned,
        "source_reachable": source_reachable,
        "source_resolution_status": (
            "mapped_to_source_root" if source_reachable else "source_mapping_unavailable"
        ),
        "type_fixability": type_fixability,
        "type_fixability_reason": (
            f"whitelisted_warning_option:{warning_option}"
            if warning_option
            else "no_matching_type_rule"
        ),
        "warning_option": warning_option,
    }


def _write_source_candidate_packet(
    tmp_path: Path,
    candidates: list[dict[str, Any]],
) -> Path:
    patch_ready_count = sum(
        1
        for candidate in candidates
        if candidate["type_fixability"] == "probably_fixable"
        and candidate["source_reachable"] is True
        and candidate["source_owned"] is True
    )
    evidence = {
        "primary_error": {
            "kind": candidates[0]["kind"],
            "file": candidates[0]["file"],
            "line": candidates[0]["line"],
            "message": candidates[0]["message"],
        },
        "source_candidates": {
            "schema_version": "source_candidates/v1",
            "full_candidates_path": "source_candidates.json",
            "candidate_count": len(candidates),
            "structured_source_candidate_count": len(candidates),
            "type_probably_fixable_count": sum(
                1 for candidate in candidates if candidate["type_fixability"] == "probably_fixable"
            ),
            "source_reachable_count": sum(
                1 for candidate in candidates if candidate["source_reachable"] is True
            ),
            "source_owned_count": sum(
                1 for candidate in candidates if candidate["source_owned"] is True
            ),
            "patch_ready_count": patch_ready_count,
        },
    }
    (tmp_path / "source_candidates.json").write_text(
        json.dumps(
            {
                "schema_version": "source_candidate_sidecar/v1",
                "candidates": candidates,
                "excluded_source_diagnostics": [],
                "excluded_summary": {
                    "explicit_parent_count": 0,
                    "missing_file_count": 0,
                    "missing_line_count": 0,
                },
            }
        ),
        encoding="utf-8",
    )
    return _write_packet(tmp_path, evidence)


def _run_fix_all(
    tmp_path: Path,
    evidence_path: Path,
    *,
    src_root: Path | None,
) -> dict[str, Any]:
    output_dir = tmp_path / "out"
    result = run_patch_suggest(
        PatchSuggestOptions(
            evidence_path=evidence_path,
            output_dir=output_dir,
            src_root=src_root,
            experimental_fix_all=True,
        )
    )
    assert result.exit_code == 0
    assert result.status == "fix_all_context_available"
    return _read_meta(output_dir)


def test_inference_engine_gold_fixture_counts_and_current_main_gap() -> None:
    packet = _load_fixture("evidence_packet.json")
    sidecar = _load_fixture("source_candidates.json")
    observation = _load_fixture("source_candidate_observation.json")

    summary = packet["source_candidates"]
    assert summary["structured_source_candidate_count"] == 8
    assert summary["type_probably_fixable_count"] == 8
    assert summary["source_reachable_count"] == 8
    assert summary["patch_ready_count"] == 8

    candidates = sidecar["candidates"]
    assert {candidate["event_id"] for candidate in candidates} == EXPECTED_GOLD_IDS
    assert [candidate["event_id"] for candidate in candidates] == [
        "E011",
        "E012",
        "E013",
        "E015",
        "E016",
        "E017",
        "E018",
        "E019",
    ]
    assert {candidate["type_fixability"] for candidate in candidates} == {"probably_fixable"}
    assert {candidate["source_reachable"] for candidate in candidates} == {True}
    assert {candidate["source_owned"] for candidate in candidates} == {True}

    cluster = packet["error_clusters"]["clusters"][0]
    assert cluster["id"] == "CL001"
    assert cluster["large_scale"] is False
    assert {item["event_id"] for item in cluster["locations_sample"]} == {
        "E012",
        "E013",
        "E015",
        "E016",
        "E017",
        "E018",
        "E019",
    }

    coverage = observation["coverage_diff"]
    assert coverage["old_path_decision"]["selected_branch"] == "multi"
    assert coverage["old_path_decision"]["fallback_reasons"] == {
        "cluster": "large_scale_false"
    }
    assert coverage["counts"] == {
        "extra_by_old": 0,
        "missed_by_old": 5,
        "old_path_covered": 3,
        "sidecar_diagnostics": 8,
    }
    assert {item["event_id"] for item in coverage["old_path_covered"]} == {
        "E011",
        "E012",
        "E013",
    }
    assert {item["event_id"] for item in coverage["missed_by_old"]} == (
        EXPECTED_GOLD_MISSED_IDS
    )


def test_inference_engine_gold_default_off_keeps_current_multi_path(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"

    result = run_patch_suggest(
        PatchSuggestOptions(
            evidence_path=GOLD / "evidence_packet.json",
            output_dir=output_dir,
            src_root=GOLD / "src",
        )
    )

    assert result.exit_code == 0
    assert result.status == "multi_candidate_context_available"
    assert _read_meta(output_dir)["mode"] == "multi_candidate"
    assert not (output_dir / "fix_all_context").exists()


def test_inference_engine_gold_fix_all_by_file_with_mock_source(tmp_path: Path) -> None:
    meta = _run_fix_all(
        tmp_path,
        GOLD / "evidence_packet.json",
        src_root=GOLD / "src",
    )

    assert meta["mode"] == "fix_all_by_file"
    assert meta["counts"] == {
        "patch_ready_candidates": 8,
        "patch_ready_file_groups": 3,
        "source_candidates": 8,
        "visible_not_patch_ready": 0,
    }
    assert [Path(item["context_md"]).name for item in meta["files"]] == [
        "001_OutputMetadata.h.md",
        "002_inference_engine_profiler.cpp.md",
        "003_inference_engine_tc.cpp.md",
    ]
    assert [item["file"] for item in meta["files"]] == [
        "tools/include/OutputMetadata.h",
        "test/src/inference_engine_profiler.cpp",
        "test/src/inference_engine_tc.cpp",
    ]
    assert [item["location_count"] for item in meta["files"]] == [1, 1, 6]

    edit_specs = sorted((tmp_path / "out" / "fix_all_context" / "edit_specs").glob("*.json"))
    assert [path.name for path in edit_specs] == [
        "edit_spec_FIXALL_001_OutputMetadata.h.json",
    ]
    first = json.loads(edit_specs[0].read_text(encoding="utf-8"))
    assert first["edits"] == [
        {
            "file": "tools/include/OutputMetadata.h",
            "line": 124,
            "old": "  int decodingType;",
            "new": "<FILL_REPLACEMENT_LINE>",
        }
    ]
    assert meta["files"][0]["edit_spec_json"] is not None
    assert meta["files"][1]["edit_spec_json"] is None
    assert meta["files"][1]["suppressed_skeleton"] == [
        {
            "column": 1,
            "line": 295,
            "message": (
                "'InstantiateTestCase_P_IsDeprecated' is deprecated: "
                "INSTANTIATE_TEST_CASE_P is deprecated, please use "
                "INSTANTIATE_TEST_SUITE_P [-Werror,-Wdeprecated-declarations]"
            ),
            "reason": "structural_closing_line",
        }
    ]
    assert meta["files"][2]["edit_spec_json"] is None
    assert [item["line"] for item in meta["files"][2]["suppressed_skeleton"]] == [
        635,
        642,
        649,
        661,
        672,
        690,
    ]
    assert {
        item["reason"] for item in meta["files"][2]["suppressed_skeleton"]
    } == {"structural_closing_line"}


@pytest.mark.parametrize(
    ("case_name", "candidates", "source_files", "expected_counts", "expected_groups"),
    [
        (
            "515_525_werror",
            [
                _source_candidate(
                    "E515",
                    file="/home/abuild/rpmbuild/BUILD/pkg/src/tdm_meson_hwc.c",
                    normalized_file="src/tdm_meson_hwc.c",
                    line=515,
                    warning_option="-Wpointer-bool-conversion",
                ),
                _source_candidate(
                    "E525",
                    file="/home/abuild/rpmbuild/BUILD/pkg/src/tdm_meson_hwc.c",
                    normalized_file="src/tdm_meson_hwc.c",
                    line=525,
                    warning_option="-Wpointer-bool-conversion",
                ),
            ],
            {"src/tdm_meson_hwc.c": 530},
            {
                "patch_ready_candidates": 2,
                "patch_ready_file_groups": 1,
                "source_candidates": 2,
                "visible_not_patch_ready": 0,
            },
            {"src/tdm_meson_hwc.c": [515, 525]},
        ),
        (
            "bluetooth_enum_cast",
            [
                _source_candidate(
                    "BT001",
                    file="/home/abuild/rpmbuild/BUILD/capi-network-bluetooth/src/bluetooth-device.c",
                    normalized_file="src/bluetooth-device.c",
                    line=110,
                    warning_option="-Wimplicit-enum-enum-cast",
                ),
                _source_candidate(
                    "BT002",
                    file="/home/abuild/rpmbuild/BUILD/capi-network-bluetooth/src/bluetooth-device.c",
                    normalized_file="src/bluetooth-device.c",
                    line=140,
                    warning_option="-Wimplicit-enum-enum-cast",
                ),
                _source_candidate(
                    "BT003",
                    file="/home/abuild/rpmbuild/BUILD/capi-network-bluetooth/src/bluetooth-common.c",
                    normalized_file="src/bluetooth-common.c",
                    line=80,
                    warning_option="-Wimplicit-enum-enum-cast",
                ),
            ],
            {"src/bluetooth-device.c": 150, "src/bluetooth-common.c": 90},
            {
                "patch_ready_candidates": 3,
                "patch_ready_file_groups": 2,
                "source_candidates": 3,
                "visible_not_patch_ready": 0,
            },
            {"src/bluetooth-common.c": [80], "src/bluetooth-device.c": [110, 140]},
        ),
        (
            "libscl_ui_override",
            [
                _source_candidate(
                    "L001",
                    file="/home/abuild/rpmbuild/BUILD/libscl-ui/src/libscl-ui.cpp",
                    normalized_file="src/libscl-ui.cpp",
                    line=77,
                    warning_option="-Winconsistent-missing-override",
                ),
                _source_candidate(
                    "L002",
                    file="/home/abuild/rpmbuild/BUILD/libscl-ui/src/libscl-ui.cpp",
                    normalized_file="src/libscl-ui.cpp",
                    line=91,
                    warning_option="-Winconsistent-missing-override",
                ),
            ],
            {"src/libscl-ui.cpp": 100},
            {
                "patch_ready_candidates": 2,
                "patch_ready_file_groups": 1,
                "source_candidates": 2,
                "visible_not_patch_ready": 0,
            },
            {"src/libscl-ui.cpp": [77, 91]},
        ),
    ],
)
def test_historical_with_source_cases_are_patch_ready_by_file(
    tmp_path: Path,
    case_name: str,
    candidates: list[dict[str, Any]],
    source_files: dict[str, int],
    expected_counts: dict[str, int],
    expected_groups: dict[str, list[int]],
) -> None:
    evidence_path = _write_source_candidate_packet(tmp_path, candidates)
    src_root = tmp_path / f"{case_name}_src"
    for relative, line_count in source_files.items():
        _write_source(src_root, relative, lines=line_count)

    meta = _run_fix_all(tmp_path, evidence_path, src_root=src_root)

    assert meta["counts"] == expected_counts
    actual_groups: dict[str, list[int]] = {}
    for path in sorted((tmp_path / "out" / "fix_all_context" / "edit_specs").glob("*.json")):
        spec = json.loads(path.read_text(encoding="utf-8"))
        assert spec["schema_version"] == "gbs_patch_suggest/edit-spec/v1"
        file_name = spec["edits"][0]["file"]
        actual_groups[file_name] = [edit["line"] for edit in spec["edits"]]
    assert actual_groups == expected_groups


@pytest.mark.parametrize(
    ("case_name", "candidates", "expected_visible", "expected_type_probably"),
    [
        (
            "ffmpeg_no_source",
            [
                _source_candidate(
                    "FF001",
                    file="/home/abuild/rpmbuild/BUILD/ffmpeg/libavcodec/utils.c",
                    normalized_file="libavcodec/utils.c",
                    line=3765,
                    kind="compiler",
                    message="implicit declaration of function 'av_temp_lss'",
                    warning_option=None,
                    type_fixability="unknown",
                    source_reachable=False,
                    source_owned=False,
                )
            ],
            1,
            0,
        ),
        (
            "appcore_agent_no_source",
            [
                _source_candidate(
                    "E009",
                    file="/home/abuild/rpmbuild/BUILD/appcore-agent/ecore_event_loop.hh",
                    normalized_file="ecore_event_loop.hh",
                    line=50,
                    kind="compiler",
                    message="first independent type mismatch",
                    warning_option=None,
                    type_fixability="unknown",
                    source_reachable=False,
                    source_owned=False,
                ),
                _source_candidate(
                    "E015",
                    file="/home/abuild/rpmbuild/BUILD/appcore-agent/exception.cc",
                    normalized_file="exception.cc",
                    line=25,
                    kind="compiler",
                    message="second independent type mismatch",
                    warning_option=None,
                    type_fixability="unknown",
                    source_reachable=False,
                    source_owned=False,
                ),
                _source_candidate(
                    "E020",
                    file="/home/abuild/rpmbuild/BUILD/appcore-agent/service_app_main.cc",
                    normalized_file="service_app_main.cc",
                    line=82,
                    kind="compiler",
                    message="third independent type mismatch",
                    warning_option=None,
                    type_fixability="unknown",
                    source_reachable=False,
                    source_owned=False,
                ),
            ],
            3,
            0,
        ),
    ],
)
def test_historical_without_source_cases_remain_visible_without_false_patch_ready(
    tmp_path: Path,
    case_name: str,
    candidates: list[dict[str, Any]],
    expected_visible: int,
    expected_type_probably: int,
) -> None:
    evidence_path = _write_source_candidate_packet(tmp_path, candidates)

    meta = _run_fix_all(tmp_path, evidence_path, src_root=None)

    assert case_name
    assert meta["counts"] == {
        "patch_ready_candidates": 0,
        "patch_ready_file_groups": 0,
        "source_candidates": expected_visible,
        "visible_not_patch_ready": expected_visible,
    }
    assert sum(
        1
        for candidate in meta["candidates"]
        if candidate["type_fixability"] == "probably_fixable"
    ) == expected_type_probably
    assert {candidate["patch_ready"] for candidate in meta["candidates"]} == {False}
