import json
from pathlib import Path
from subprocess import CalledProcessError

import pytest

from gbs_analyzer.evidence.router import collector_for_candidate
from gbs_analyzer.full_match import Verdict, full_match
from gbs_analyzer.scan_and_extract import scan_buildlog

FIXTURES = Path(__file__).parents[1] / "fixtures"


def failing_ctags(_: Path) -> str:
    raise CalledProcessError(1, "ctags")


def happy_ctags(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    name = "missing_symbol" if "missing_symbol" in text else "main"
    line_no = 1
    for index, line in enumerate(text.splitlines(), start=1):
        if name in line:
            line_no = index
            break
    return json.dumps({"name": name, "line": line_no}) + "\n"


@pytest.mark.parametrize(
    ("fixture_name", "buildlog_name", "src_subdir", "spec_name", "pattern_id"),
    [
        (
            "evidence_compile_no_member",
            "buildlog",
            "src",
            None,
            "compile_undeclared_identifier_tier2",
        ),
        (
            "evidence_link_undef",
            "buildlog",
            "src",
            "demo.spec",
            "linker_undefined_reference_tier2",
        ),
        (
            "evidence_spec_install",
            "buildlog",
            None,
            "demo.spec",
            "rpm_phase_failure_tier2",
        ),
    ],
)
def test_tier2_full_match_fixtures_hit(
    fixture_name: str,
    buildlog_name: str,
    src_subdir: str | None,
    spec_name: str | None,
    pattern_id: str,
) -> None:
    fixture = FIXTURES / fixture_name
    scan = scan_buildlog(fixture / buildlog_name)
    scan_data = scan.as_dict()
    event = scan_data["events"][0]
    candidate = {"event_id": event["id"], "kind": event["kind"]}
    collector = collector_for_candidate(
        candidate,
        scan,
        src_root=fixture / src_subdir if src_subdir else None,
        spec_path=fixture / spec_name if spec_name else None,
        buildlog_path=fixture / buildlog_name,
        ctags_runner=failing_ctags,
    )
    assert collector is not None

    evidence = collector.collect(candidate, 900)
    result = full_match(scan, candidate, evidence)

    assert result.verdict is Verdict.DIRECT_TIER2
    assert result.pattern_id == pattern_id
    assert result.matched_tier == "tier2"
    assert result.direct_answer


@pytest.mark.parametrize(
    ("fixture_name", "buildlog_name", "src_subdir", "spec_name", "pattern_id"),
    [
        (
            "evidence_compile_no_member",
            "buildlog",
            "src",
            None,
            "compile_undeclared_identifier_tier2",
        ),
        (
            "evidence_link_undef",
            "buildlog",
            "src",
            "demo.spec",
            "linker_undefined_reference_tier2",
        ),
        (
            "evidence_spec_install",
            "buildlog",
            None,
            "demo.spec",
            "rpm_phase_failure_tier2",
        ),
    ],
)
def test_tier2_full_match_fixtures_hit_with_happy_ctags(
    fixture_name: str,
    buildlog_name: str,
    src_subdir: str | None,
    spec_name: str | None,
    pattern_id: str,
) -> None:
    fixture = FIXTURES / fixture_name
    scan = scan_buildlog(fixture / buildlog_name)
    event = scan.as_dict()["events"][0]
    candidate = {"event_id": event["id"], "kind": event["kind"]}
    collector = collector_for_candidate(
        candidate,
        scan,
        src_root=fixture / src_subdir if src_subdir else None,
        spec_path=fixture / spec_name if spec_name else None,
        buildlog_path=fixture / buildlog_name,
        ctags_runner=happy_ctags,
    )
    assert collector is not None

    evidence = collector.collect(candidate, 900)
    result = full_match(scan, candidate, evidence)

    assert result.verdict is Verdict.DIRECT_TIER2
    assert result.pattern_id == pattern_id
    assert result.matched_tier == "tier2"
    if src_subdir is not None:
        assert evidence.extraction_methods == ["ctags"]
