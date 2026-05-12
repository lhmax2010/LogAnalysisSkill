from pathlib import Path

import pytest
import yaml

from gbs_analyzer.quick_filter import (
    PatternValidationError,
    QuickFilter,
    is_in_warning_block,
    load_pattern_library,
    quick_filter,
)
from gbs_analyzer.scan_and_extract import scan_buildlog


def write_log(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "buildlog"
    path.write_text(text, encoding="utf-8")
    return path


def write_library(tmp_path: Path, category: str, fix_template: str) -> Path:
    data = {
        "schema_version": 2,
        "tier1_allowed_categories": ["depsolve_failure", "patch_failed"],
        "tier1_forbidden_categories": ["compile_error"],
        "patterns": [
            {
                "id": "candidate",
                "category": category,
                "tier": "tier1",
                "event_kinds": ["depsolve"],
                "match": {"regex": ["nothing provides (?P<requirement>.+)"]},
                "confidence": 0.96,
                "terminal": True,
                "fix_template": fix_template,
            }
        ],
    }
    path = tmp_path / "patterns.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return path


def test_load_default_pattern_library() -> None:
    library = load_pattern_library()
    assert library["schema_version"] == 2
    assert len(library["patterns"]) == 7


def test_depsolve_fast_path_hits(tmp_path: Path) -> None:
    result = quick_filter(scan_buildlog(write_log(tmp_path, "nothing provides pkgconfig(foo)\n")))
    assert result.hit is True
    assert result.match is not None
    assert result.match.pattern_id == "depsolve_nothing_provides"
    assert result.match.category == "depsolve_failure"


def test_patch_standard_fast_path_hits(tmp_path: Path) -> None:
    scan = scan_buildlog(write_log(tmp_path, "Patch #7 (fix.patch) failed\n"))
    assert quick_filter(scan).match.pattern_id == "patch_failed_standard"  # type: ignore[union-attr]


def test_patch_hunk_fast_path_hits(tmp_path: Path) -> None:
    scan = scan_buildlog(write_log(tmp_path, "Hunk #2 FAILED at 20.\n"))
    assert quick_filter(scan).match.pattern_id == "patch_failed_hunk"  # type: ignore[union-attr]


def test_patch_at_line_fast_path_hits(tmp_path: Path) -> None:
    scan = scan_buildlog(write_log(tmp_path, "patch failed: src/foo.c:12\n"))
    assert quick_filter(scan).match.pattern_id == "patch_failed_at_line"  # type: ignore[union-attr]


def test_patch_rpm_fast_path_hits(tmp_path: Path) -> None:
    scan = scan_buildlog(write_log(tmp_path, "error: patch failed\n"))
    assert quick_filter(scan).match.pattern_id == "patch_failed_rpm"  # type: ignore[union-attr]


def test_linker_missing_fast_path_hits_with_allowed_tool(tmp_path: Path) -> None:
    scan = scan_buildlog(
        write_log(tmp_path, "+ %build\n+ gcc main.o -lfoo\n/usr/bin/ld: cannot find -lfoo\n")
    )
    match = quick_filter(scan).match
    assert match is not None
    assert match.pattern_id == "linker_missing_library"
    assert match.captures == {"library": "foo"}


def test_install_missing_fast_path_hits(tmp_path: Path) -> None:
    scan = scan_buildlog(write_log(tmp_path, "File not found: /tmp/BUILDROOT/missing\n"))
    assert quick_filter(scan).match.pattern_id == "install_file_not_found"  # type: ignore[union-attr]


def test_undefined_reference_does_not_hit(tmp_path: Path) -> None:
    scan = scan_buildlog(write_log(tmp_path, "foo.o: undefined reference to `bar'\n"))
    assert quick_filter(scan).hit is False


def test_compile_error_does_not_hit(tmp_path: Path) -> None:
    scan = scan_buildlog(write_log(tmp_path, "src/foo.c:1:1: error: nope\n"))
    assert quick_filter(scan).hit is False


def test_werror_does_not_hit(tmp_path: Path) -> None:
    scan = scan_buildlog(write_log(tmp_path, "cc1: all warnings being treated as errors\n"))
    assert quick_filter(scan).hit is False


def test_rpm_phase_failure_does_not_hit(tmp_path: Path) -> None:
    scan = scan_buildlog(write_log(tmp_path, "error: Bad exit status from /tmp/rpm (%build)\n"))
    assert quick_filter(scan).hit is False


def test_spec_script_error_does_not_hit(tmp_path: Path) -> None:
    scan = scan_buildlog(write_log(tmp_path, "spec file parse error: unexpected %endif\n"))
    assert quick_filter(scan).hit is False


def test_linker_missing_requires_allowed_tool(tmp_path: Path) -> None:
    scan = scan_buildlog(write_log(tmp_path, "/usr/bin/ld: cannot find -lfoo\n"))
    assert quick_filter(scan).hit is False


def test_warning_block_blocks_required_context() -> None:
    event = {"id": "E002", "severity": "error", "message": "cannot find -lfoo", "line_no": 10}
    events = [
        {"id": "E001", "severity": "warning", "message": "warning: note", "line_no": 8},
        event,
    ]
    assert is_in_warning_block(event, events)


def test_other_error_prevents_warning_block() -> None:
    event = {"id": "E002", "severity": "error", "message": "cannot find -lfoo", "line_no": 10}
    events = [
        {"id": "E001", "severity": "warning", "message": "warning: note", "line_no": 8},
        event,
        {"id": "E003", "severity": "error", "message": "error: real failure", "line_no": 11},
    ]
    assert not is_in_warning_block(event, events)


def test_minimal_packet_contains_direct_answer(tmp_path: Path) -> None:
    scan = scan_buildlog(write_log(tmp_path, "nothing provides libfoo needed by pkg\n"))
    match = quick_filter(scan).match
    assert match is not None
    packet = match.minimal_packet
    assert packet["verdict"] == "direct_answer"
    assert packet["via"] == "fast_path"
    assert packet["matched_tier"] == "tier1"
    assert packet["allowed_next_actions"] == ["expand"]


def test_degraded_scan_reasons_propagate(tmp_path: Path) -> None:
    scan = scan_buildlog(
        write_log(tmp_path, "+ gcc @missing.rsp\nnothing provides libfoo\n"),
        cwd=tmp_path,
    )
    match = quick_filter(scan).match
    assert match is not None
    assert match.minimal_packet["degraded"] is True
    assert match.minimal_packet["degraded_reasons"] == ["command_C001_rsp_unavailable"]


def test_evaluate_accepts_scan_result_dict(tmp_path: Path) -> None:
    scan = scan_buildlog(write_log(tmp_path, "nothing provides libfoo\n")).as_dict()
    assert QuickFilter.from_file().evaluate(scan).hit is True


def test_validation_rejects_forbidden_category(tmp_path: Path) -> None:
    path = write_library(
        tmp_path,
        "compile_error",
        "可能需要检查源码；需要更多上下文请运行 expand。",
    )
    with pytest.raises(PatternValidationError, match="not tier1-allowed"):
        load_pattern_library(path)


def test_validation_rejects_overlong_patch_fix(tmp_path: Path) -> None:
    fix = "可能" + ("补丁" * 100) + "；需要更多上下文请运行 expand。"
    path = write_library(tmp_path, "patch_failed", fix)
    with pytest.raises(PatternValidationError, match="exceeds 150"):
        load_pattern_library(path)


def test_validation_rejects_assertive_fix(tmp_path: Path) -> None:
    path = write_library(tmp_path, "depsolve_failure", "缺少依赖，运行 expand。")
    with pytest.raises(PatternValidationError, match="conservative"):
        load_pattern_library(path)


def test_validation_requires_expand_hint(tmp_path: Path) -> None:
    path = write_library(tmp_path, "depsolve_failure", "可能缺少依赖，建议检查 repo。")
    with pytest.raises(PatternValidationError, match="expand"):
        load_pattern_library(path)
