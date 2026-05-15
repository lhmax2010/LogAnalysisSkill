import time
from pathlib import Path

from gbs_analyzer.rank_causes import rank_causes
from gbs_analyzer.scan_and_extract import scan_buildlog

FIXTURES = Path(__file__).parents[1] / "fixtures"


EXPECTED_TOP1 = {
    "rank_syntax_error": "syntax_error",
    "rank_no_member": "no_member",
    "rank_missing_lib": "missing_lib",
    "rank_undefined_ref": "undefined_reference",
    "rank_generic_gated": "generic_error",
}


def test_rank_fixtures_top1_accuracy() -> None:
    correct = 0
    for name, expected in EXPECTED_TOP1.items():
        scan = scan_buildlog(FIXTURES / name / "buildlog")
        top1 = rank_causes(scan).root_cause_candidates[0]
        correct += int(top1.semantic_class == expected)

    assert correct / len(EXPECTED_TOP1) >= 0.80


def test_rank_fixtures_exact_top1_classes() -> None:
    for name, expected in EXPECTED_TOP1.items():
        scan = scan_buildlog(FIXTURES / name / "buildlog")
        top1 = rank_causes(scan).root_cause_candidates[0]
        assert top1.semantic_class == expected


def test_rank_runtime_under_50ms() -> None:
    scans = [scan_buildlog(FIXTURES / name / "buildlog") for name in EXPECTED_TOP1]
    started = time.perf_counter()
    for scan in scans:
        rank_causes(scan)
    elapsed_ms = (time.perf_counter() - started) * 1000

    assert elapsed_ms < 50.0
