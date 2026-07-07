from __future__ import annotations

import pytest
from ci_triage.verify.failure_classify import classify_failure


def source_primary(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "kind": "werror",
        "file": "src/service_app_main.cc",
        "line": 82,
        "message": "error: no member named 'foo' in 'Bar' [-Werror]",
        "diagnostic_code": "-Werror",
        "type_fixability": "probably_fixable",
        "source_reachable": True,
        "source_owned": True,
    }
    data.update(overrides)
    return data


def test_1118258_mlgo_toolchain_flag_is_denylisted_and_not_raw_unparsed() -> None:
    result = classify_failure(
        {
            "primary_error": {
                "kind": "raw_error",
                "message": (
                    "clang: error: unknown argument: '-enable-ml-inliner=release'"
                ),
            }
        },
        build_log=(
            "armv7l-tizen-linux-gnueabi-clang -O2 -enable-ml-inliner=release "
            "-c source.cc"
        ),
        failure_stage="gbs_build_failed",
    )

    assert result.repair_allowed is False
    assert result.failure_class == "toolchain"
    assert result.confidence == 1.0
    assert result.matched_rule is not None
    assert result.matched_rule.startswith("denylist:")


def test_1095003_source_werror_is_repairable() -> None:
    result = classify_failure(
        {"primary_error": source_primary(file="src/foo.c", line=109)},
        build_log="src/foo.c:109:5: error: use of undeclared identifier 'bar' [-Werror]",
        failure_stage="gbs_build_failed",
    )

    assert result.repair_allowed is True
    assert result.failure_class == "source_repairable"
    assert result.confidence >= 0.8
    assert result.matched_rule == "heuristic:source_werror_or_compile_error"


def test_denylist_cannot_be_flipped_by_source_repairable_signals() -> None:
    result = classify_failure(
        {"primary_error": source_primary()},
        build_log="clang: error: unknown argument '-enable-ml-inliner=release'",
        failure_stage="gbs_build_failed",
    )

    assert result.repair_allowed is False
    assert result.failure_class == "toolchain"
    assert result.matched_rule == "denylist:toolchain_flag_enable_ml_inliner"


@pytest.mark.parametrize(
    ("stage", "expected_class"),
    [
        ("apply_failed", "apply_failed"),
        ("analyzer_failed", "analyzer_failed"),
        ("infrastructure_failed", "infrastructure_failed"),
        ("build_mutated_source", "build_mutated_source"),
    ],
)
def test_non_compile_stages_are_classified_but_not_repair_allowed(
    stage: str,
    expected_class: str,
) -> None:
    result = classify_failure(
        {"primary_error": source_primary()},
        build_log="",
        failure_stage=stage,
    )

    assert result.repair_allowed is False
    assert result.failure_class == expected_class
    assert result.matched_rule == f"failure_stage:{stage}"


def test_raw_unparsed_without_stronger_denylist_is_rejected() -> None:
    result = classify_failure(
        {"primary_error": {"kind": "raw_error", "message": "unparsed failure"}},
        failure_stage="gbs_build_failed",
    )

    assert result.repair_allowed is False
    assert result.failure_class == "raw_unparsed"
    assert result.matched_rule == "denylist:raw_unparsed"


def test_source_unreachable_is_not_repair_allowed() -> None:
    result = classify_failure(
        {
            "primary_error": source_primary(
                source_reachable=False,
                source_resolution_status="source_mapping_unavailable",
            )
        },
        failure_stage="gbs_build_failed",
    )

    assert result.repair_allowed is False
    assert result.failure_class == "source_unreachable"
    assert result.confidence < 0.8


def test_uncertain_default_rejects_source_located_unknown_fixability() -> None:
    result = classify_failure(
        {
            "primary_error": source_primary(
                type_fixability="unknown",
                diagnostic_code=None,
                message="error: something unusual happened",
            )
        },
        failure_stage="gbs_build_failed",
    )

    assert result.repair_allowed is False
    assert result.failure_class == "uncertain"
    assert result.confidence < 0.8


@pytest.mark.parametrize(
    ("message", "expected_class"),
    [
        ("ld: cannot find -lfoo", "dependency"),
        ("No space left on device", "build_env"),
        ("nothing provides pkgconfig(foo)", "dependency"),
        ("clang: error: unknown warning option '-Wno-stringop-overflow'", "toolchain"),
    ],
)
def test_denylist_patterns_reject_non_source_failures(
    message: str,
    expected_class: str,
) -> None:
    result = classify_failure(
        {"primary_error": source_primary(message=message)},
        build_log=message,
        failure_stage="gbs_build_failed",
    )

    assert result.repair_allowed is False
    assert result.failure_class == expected_class
    assert result.matched_rule is not None
    assert result.matched_rule.startswith("denylist:")
