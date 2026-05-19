import tempfile
from pathlib import Path

from gbs_analyzer.rank_causes import clamp, confidence_band, rank_causes, rank_score
from gbs_analyzer.scan_and_extract import scan_buildlog


def scan(text: str):
    path = Path(tempfile.mkdtemp()) / "buildlog"
    path.write_text(text, encoding="utf-8")
    return scan_buildlog(path)


def test_rank_prefers_missing_library_over_raw_error() -> None:
    result = rank_causes(scan("+ %build\n+ gcc main.o -lfoo\n/usr/bin/ld: cannot find -lfoo\n"))
    top = result.root_cause_candidates[0]
    assert top.semantic_class == "missing_lib"
    assert top.confidence_band == "high"


def test_rank_folds_parented_make_cascade_low() -> None:
    result = rank_causes(
        scan(
            "+ %build\n+ gcc -c src/foo.c\n"
            "src/foo.c:1:1: error: nope\n"
            "make: *** [src/foo.o] Error 1\n"
        )
    )
    assert result.root_cause_candidates[-1].kind == "make_cascade"
    assert result.root_cause_candidates[-1].confidence == 0.1


def test_rank_outputs_top_k_only() -> None:
    result = rank_causes(
        {
            "failed_phase": "%build",
            "events": [
                {"id": "E001", "kind": "raw_error", "message": "error: one", "line_no": 1},
                {"id": "E002", "kind": "raw_error", "message": "error: two", "line_no": 2},
                {"id": "E003", "kind": "raw_error", "message": "error: three", "line_no": 3},
            ],
        },
        top_k=2,
    )
    assert [candidate.rank for candidate in result.root_cause_candidates] == [1, 2]


def test_rank_result_as_dict() -> None:
    data = rank_causes(scan("src/foo.c:1:1: error: syntax error\n")).as_dict()
    assert data["root_cause_candidates"][0]["rank"] == 1
    assert data["root_cause_candidates"][0]["semantic_class"] == "syntax_error"


def test_rank_score_adds_command_and_location_bonus() -> None:
    event = {
        "id": "E001",
        "kind": "compiler",
        "message": "use of undeclared identifier 'foo'",
        "command_id": "C001",
        "file": "src/foo.c",
        "line": 10,
    }
    score, reasons = rank_score(event, [event])
    assert score > 0.75
    assert {"factor": "has_command", "delta": "+0.05"} in reasons
    assert {"factor": "has_location", "delta": "+0.05"} in reasons


def test_rank_score_applies_warning_block_penalty() -> None:
    warning = {"id": "E001", "severity": "warning", "message": "warning: note", "line_no": 1}
    event = {
        "id": "E002",
        "kind": "compiler",
        "message": "error: generic",
        "severity": "error",
        "line_no": 2,
    }
    score, reasons = rank_score(event, [warning, event])
    assert score < 0.45
    assert {"factor": "warning_block", "delta": "-0.30"} in reasons


def test_rank_score_applies_parent_penalty() -> None:
    event = {"id": "E001", "kind": "raw_error", "message": "error: cascade", "parent": "E000"}
    score, reasons = rank_score(event, [event])
    assert score < 0.45
    assert {"factor": "parent_cascade", "delta": "-0.40"} in reasons


def test_rank_boosts_patch_failure_in_failed_phase() -> None:
    event = {
        "id": "E001",
        "kind": "patch",
        "message": "Hunk #1 FAILED: 1 out of 1 hunk ignored",
        "phase": "%prep",
        "command_id": "C001",
    }
    score, reasons = rank_score(event, [event], failed_phase="%prep")

    assert score > 0.45
    assert {"factor": "patch_failed_phase", "delta": "+0.10"} in reasons


def test_rank_prefers_patch_over_derived_rpm_phase() -> None:
    result = rank_causes(
        scan(
            "Executing(%prep): /bin/sh -e /tmp/rpm\n"
            "+ /bin/patch --no-backup-if-mismatch -p1\n"
            "1 out of 1 hunk ignored\n"
            "error: Bad exit status from /var/tmp/rpm-tmp.abc (%prep)\n"
        )
    )

    assert result.root_cause_candidates[0].kind == "patch"
    assert result.root_cause_candidates[1].kind == "rpm_phase"


def test_generic_gating_reason_is_recorded() -> None:
    result = rank_causes(
        scan("+ %build\n+ ./configure\nerror: configure failed\n")
    ).root_cause_candidates[0]
    assert result.semantic_class == "generic_error"
    assert {"factor": "generic_context_satisfied", "value": True} in result.confidence_reason


def test_confidence_band_boundaries() -> None:
    assert confidence_band(0.90) == "high"
    assert confidence_band(0.70) == "medium_high"
    assert confidence_band(0.50) == "medium"
    assert confidence_band(0.49) == "low"


def test_clamp_bounds_values() -> None:
    assert clamp(2.0, 0.0, 1.0) == 1.0
    assert clamp(-1.0, 0.0, 1.0) == 0.0
