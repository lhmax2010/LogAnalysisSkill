from typing import Any

from gbs_analyzer.evidence.base import (
    Evidence,
    EvidenceCollector,
    default_estimate,
    level_for_budget,
)
from gbs_analyzer.scan_and_extract import CommandRecord, DiagnosticEvent, ScanResult


class DummyCollector(EvidenceCollector):
    collector_name = "dummy"

    def estimate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        return default_estimate()

    def collect(self, candidate: dict[str, Any], granted_budget: int) -> Evidence:
        return Evidence(
            collector=self.collector_name,
            level=level_for_budget(granted_budget),
            granted_budget=granted_budget,
            data={"candidate": candidate},
        )


def test_evidence_contains_all_required_items() -> None:
    evidence = Evidence(
        collector="compile",
        level=2,
        granted_budget=600,
        data={},
        contains={"source_snippet", "command_summary"},
    )
    assert evidence.contains_all(["source_snippet"])
    assert not evidence.contains_all(["source_snippet", "missing"])


def test_evidence_as_dict_sorts_contains() -> None:
    evidence = Evidence(
        collector="compile",
        level=1,
        granted_budget=300,
        data={"x": 1},
        contains={"b", "a"},
        extraction_methods=["line_window"],
    )
    assert evidence.as_dict()["contains"] == ["a", "b"]


def test_level_for_budget() -> None:
    assert level_for_budget(299) == 1
    assert level_for_budget(600) == 2
    assert level_for_budget(900) == 3


def test_default_estimate_shape() -> None:
    estimate = default_estimate()
    assert estimate["preferred"] == 900
    assert estimate["minimum"] == 300
    assert estimate["levels"][2] == 600


def test_collector_normalizes_paths_and_scan_result_dataclass(tmp_path) -> None:
    scan_result = ScanResult(
        schema_version="scan_result/v1",
        buildlog_path="buildlog",
        buildlog_size_bytes=10,
        is_gzip=False,
        failed_phase="%build",
        phases=[],
        commands=[],
        events=[],
    )
    collector = DummyCollector(
        scan_result,
        src_root=tmp_path / "src",
        spec_path=tmp_path / "demo.spec",
        buildlog_path=tmp_path / "buildlog",
        ctags_runner=lambda *_args: "",
    )

    assert collector.scan_result["failed_phase"] == "%build"
    assert collector.src_root == tmp_path / "src"
    assert collector.spec_path == tmp_path / "demo.spec"
    assert collector.buildlog_path == tmp_path / "buildlog"
    assert collector.ctags_runner is not None


def test_event_for_finds_scan_event_by_event_id() -> None:
    collector = DummyCollector(
        {
            "events": [
                {"id": "evt-1", "kind": "compiler", "message": "first"},
                {"id": "evt-2", "kind": "depsolve", "message": "second"},
            ],
            "commands": [],
        }
    )

    assert collector.event_for({"event_id": "evt-2"})["message"] == "second"


def test_event_for_finds_scan_event_by_candidate_id() -> None:
    collector = DummyCollector(
        {
            "events": [{"id": "evt-1", "kind": "compiler", "message": "match"}],
            "commands": [],
        }
    )

    assert collector.event_for({"id": "evt-1"})["message"] == "match"


def test_event_for_falls_back_to_candidate_when_it_is_event_like() -> None:
    collector = DummyCollector({"events": [], "commands": []})
    candidate = {"id": "candidate-1", "kind": "linker_missing"}

    assert collector.event_for(candidate) is candidate


def test_event_for_returns_empty_mapping_for_unresolved_candidate() -> None:
    collector = DummyCollector({"events": [{"id": "evt-1"}], "commands": []})

    assert collector.event_for({"event_id": "missing"}) == {}


def test_command_for_finds_command_by_command_id() -> None:
    collector = DummyCollector(
        {
            "events": [],
            "commands": [
                {"id": "cmd-1", "argv_short": "gcc -c foo.c"},
                {"id": "cmd-2", "argv_short": "ld -lmissing"},
            ],
        }
    )

    assert collector.command_for({"command_id": "cmd-2"}) == {
        "id": "cmd-2",
        "argv_short": "ld -lmissing",
    }


def test_command_for_returns_none_when_unresolved() -> None:
    collector = DummyCollector(
        {
            "events": [],
            "commands": [{"id": "cmd-1", "argv_short": "gcc -c foo.c"}],
        }
    )

    assert collector.command_for({"command_id": "missing"}) is None
    assert collector.command_for({}) is None


def test_collector_accepts_scan_result_with_command_and_event_dataclasses() -> None:
    command = CommandRecord(
        id="cmd-1",
        line_no=1,
        raw_offset=0,
        phase="%build",
        argv_short="gcc -c foo.c",
        argv_full=None,
        rsp_expanded={},
        command_degraded=False,
    )
    event = DiagnosticEvent(
        id="evt-1",
        kind="compiler",
        severity="error",
        message="foo.c:1: error: boom",
        line_no=2,
        raw_offset=10,
        phase="%build",
        command_id="cmd-1",
        file="foo.c",
        line=1,
    )
    collector = DummyCollector(
        ScanResult(
            schema_version="scan_result/v1",
            buildlog_path="buildlog",
            buildlog_size_bytes=20,
            is_gzip=False,
            failed_phase="%build",
            phases=[],
            commands=[command],
            events=[event],
        )
    )

    found_event = collector.event_for({"event_id": "evt-1"})
    assert found_event["file"] == "foo.c"
    assert collector.command_for(found_event)["argv_short"] == "gcc -c foo.c"
