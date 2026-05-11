from pathlib import Path

from gbs_analyzer.scan_and_extract import scan_buildlog

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_compile_error_fixture_scans() -> None:
    result = scan_buildlog(FIXTURES / "scan_compile_error" / "buildlog")
    assert [event.kind for event in result.events] == ["compiler", "make_cascade"]
    assert result.events[1].parent == "E001"
    assert result.failed_phase == "%build"


def test_link_missing_fixture_scans() -> None:
    result = scan_buildlog(FIXTURES / "scan_link_missing" / "buildlog")
    assert result.events[0].kind == "linker_missing"
    assert result.events[0].details == {"library": "missing"}


def test_patch_failed_fixture_scans() -> None:
    result = scan_buildlog(FIXTURES / "scan_patch_failed" / "buildlog")
    assert result.events[0].kind == "patch"
    assert result.events[0].details == {"num": "3"}
    assert result.failed_phase == "%prep"


def test_depsolve_fixture_scans() -> None:
    result = scan_buildlog(FIXTURES / "scan_depsolve_failure" / "buildlog")
    assert len(result.events) == 1
    assert result.events[0].kind == "depsolve"


def test_make_cascade_fixture_scans() -> None:
    result = scan_buildlog(FIXTURES / "scan_make_cascade" / "buildlog")
    assert [event.kind for event in result.events] == [
        "compiler",
        "make_cascade",
        "make_cascade",
    ]
    assert result.events[1].parent == "E001"
    assert result.events[2].parent is None
