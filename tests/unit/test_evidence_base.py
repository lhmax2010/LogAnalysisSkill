from gbs_analyzer.evidence.base import Evidence, default_estimate, level_for_budget


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
