import time
from pathlib import Path

from gbs_analyzer.quick_filter import quick_filter
from gbs_analyzer.scan_and_extract import scan_buildlog

FIXTURES = Path(__file__).parents[1] / "fixtures"


def evaluate_fixture(name: str):
    return quick_filter(scan_buildlog(FIXTURES / name / "buildlog"))


def test_depsolve_fast_path_fixture_hits() -> None:
    result = evaluate_fixture("fast_path_depsolve")
    assert result.match is not None
    assert result.match.pattern_id == "depsolve_nothing_provides"
    assert result.match.category == "depsolve_failure"


def test_patch_failed_fast_path_fixture_hits() -> None:
    result = evaluate_fixture("fast_path_patch_failed")
    assert result.match is not None
    assert result.match.pattern_id == "patch_failed_standard"
    assert result.match.category == "patch_failed"


def test_missing_lib_fast_path_fixture_hits() -> None:
    result = evaluate_fixture("fast_path_missing_lib")
    assert result.match is not None
    assert result.match.pattern_id == "linker_missing_library"
    assert result.match.category == "linker_missing_lib"


def test_install_missing_fast_path_fixture_hits() -> None:
    result = evaluate_fixture("fast_path_install_missing")
    assert result.match is not None
    assert result.match.pattern_id == "install_file_not_found"
    assert result.match.category == "install_file_missing"


def test_quick_filter_fixtures_run_under_100ms() -> None:
    scans = [
        scan_buildlog(FIXTURES / name / "buildlog")
        for name in [
            "fast_path_depsolve",
            "fast_path_patch_failed",
            "fast_path_missing_lib",
            "fast_path_install_missing",
        ]
    ]

    started = time.perf_counter()
    results = [quick_filter(scan) for scan in scans]
    elapsed = time.perf_counter() - started

    assert all(result.hit for result in results)
    assert elapsed < 0.1
