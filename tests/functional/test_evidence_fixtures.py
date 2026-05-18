from pathlib import Path
from subprocess import CalledProcessError

import pytest

from gbs_analyzer.evidence.router import collector_for_candidate
from gbs_analyzer.scan_and_extract import scan_buildlog

FIXTURES = Path(__file__).parents[1] / "fixtures"


CASES = {
    "compile": [
        ("evidence_compile_no_member", "buildlog", "source_snippet"),
        ("evidence_compile_window", "buildlog", "source_snippet"),
    ],
    "link": [
        ("evidence_link_undef", "buildlog", "link_command"),
        ("evidence_link_missing", "buildlog", "spec_buildrequires"),
    ],
    "spec": [
        ("evidence_spec_build", "buildlog", "failure_context"),
        ("evidence_spec_install", "buildlog", "failure_context"),
    ],
    "deps": [
        ("evidence_deps_nothing", "buildlog", "missing_dependency"),
        ("evidence_deps_profile", "profile.mobile.buildlog", "missing_dependency"),
    ],
}


def failing_ctags(_: Path) -> str:
    raise CalledProcessError(1, "ctags")


@pytest.mark.parametrize("collector_name", ["compile", "link", "spec", "deps"])
def test_each_m5_collector_has_two_fixtures(collector_name: str) -> None:
    for fixture_name, buildlog_name, required_key in CASES[collector_name]:
        fixture = FIXTURES / fixture_name
        scan = scan_buildlog(fixture / buildlog_name)
        event = scan.as_dict()["events"][0]
        collector = collector_for_candidate(
            {"event_id": event["id"], "kind": event["kind"]},
            scan,
            src_root=fixture / "src",
            spec_path=fixture / "demo.spec",
            buildlog_path=fixture / buildlog_name,
            ctags_runner=failing_ctags,
        )
        assert collector is not None
        assert collector.collector_name == collector_name

        evidence = collector.collect({"event_id": event["id"], "kind": event["kind"]}, 900)
        assert required_key in evidence.data
        assert evidence.collector == collector_name


def test_compile_fixture_triggers_ctags_window_fallback() -> None:
    fixture = FIXTURES / "evidence_compile_window"
    scan = scan_buildlog(fixture / "buildlog")
    event = scan.as_dict()["events"][0]
    collector = collector_for_candidate(
        {"event_id": event["id"], "kind": event["kind"]},
        scan,
        src_root=fixture / "src",
        ctags_runner=failing_ctags,
    )
    assert collector is not None
    evidence = collector.collect({"event_id": event["id"], "kind": event["kind"]}, 900)
    assert evidence.data["source_snippet"]["extraction_method"] == "line_window"
    assert evidence.degraded is True
