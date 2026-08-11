from __future__ import annotations

import pytest
from tizen_ci_shared.classify import (
    REPAIR_AUTO,
    REPAIR_DENIED,
    REPAIR_NEEDS_CONFIRMATION,
    classify_failure,
)


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

    assert result.repair_allowed == REPAIR_DENIED
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

    assert result.repair_allowed == REPAIR_AUTO
    assert result.failure_class == "source_repairable"
    assert result.confidence >= 0.8
    assert result.matched_rule == "heuristic:source_werror_or_compile_error"


def test_denylist_cannot_be_flipped_by_source_repairable_signals() -> None:
    result = classify_failure(
        {"primary_error": source_primary()},
        build_log="clang: error: unknown argument '-enable-ml-inliner=release'",
        failure_stage="gbs_build_failed",
    )

    assert result.repair_allowed == REPAIR_DENIED
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

    assert result.repair_allowed == REPAIR_DENIED
    assert result.failure_class == expected_class
    assert result.matched_rule == f"failure_stage:{stage}"


def test_raw_unparsed_without_stronger_denylist_is_rejected() -> None:
    result = classify_failure(
        {"primary_error": {"kind": "raw_error", "message": "unparsed failure"}},
        failure_stage="gbs_build_failed",
    )

    assert result.repair_allowed == REPAIR_DENIED
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

    assert result.repair_allowed == REPAIR_DENIED
    assert result.failure_class == "source_unreachable"
    assert result.confidence < 0.8


def test_source_owned_unknown_fixability_needs_confirmation() -> None:
    result = classify_failure(
        {
            "primary_error": source_primary(
                type_fixability="unknown",
                diagnostic_code=None,
                message="error: reference to 'LWE' is ambiguous",
            )
        },
        failure_stage="gbs_build_failed",
    )

    assert result.repair_allowed == REPAIR_NEEDS_CONFIRMATION
    assert result.failure_class == "source_repairable_unverified_type"
    assert result.confidence < 0.8
    assert result.matched_rule == "heuristic:type_unknown"
    assert "human confirmation" in result.reason


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

    assert result.repair_allowed == REPAIR_DENIED
    assert result.failure_class == expected_class
    assert result.matched_rule is not None
    assert result.matched_rule.startswith("denylist:")


def test_repair_allowed_constants_are_stable() -> None:
    assert REPAIR_AUTO == "auto"
    assert REPAIR_NEEDS_CONFIRMATION == "needs_confirmation"
    assert REPAIR_DENIED == "denied"


@pytest.mark.parametrize(
    ("primary", "expected_class", "expected_rule"),
    [
        (
            {"kind": "link_error", "message": "undefined reference to `foo_symbol`"},
            "uncertain",
            "heuristic:link_symbol",
        ),
        (
            {"kind": "rpm_phase", "message": "script failed"},
            "uncertain",
            "heuristic:unsupported_kind",
        ),
        (
            source_primary(file="", line=0),
            "source_unreachable",
            "heuristic:missing_source_location",
        ),
        (
            source_primary(
                source_reachable=False,
                source_resolution_status="source_mapping_unavailable",
            ),
            "source_unreachable",
            "heuristic:source_unreachable",
        ),
        (
            source_primary(
                source_owned=False,
                source_ownership_status="generated_or_vendor",
            ),
            "source_unreachable",
            "heuristic:source_not_owned",
        ),
    ],
)
def test_non_confirmable_boundaries_remain_denied(
    primary: dict[str, object],
    expected_class: str,
    expected_rule: str,
) -> None:
    result = classify_failure({"primary_error": primary}, failure_stage="gbs_build_failed")

    assert result.repair_allowed == REPAIR_DENIED
    assert result.failure_class == expected_class
    assert result.matched_rule == expected_rule


def test_low_confidence_uncertain_stays_denied_and_distinct_from_unverified_type() -> None:
    uncertain = classify_failure(
        {"primary_error": {"kind": "rpm_phase", "message": "script failed"}},
        failure_stage="gbs_build_failed",
    )
    unverified_type = classify_failure(
        {
            "primary_error": source_primary(
                type_fixability="unknown",
                diagnostic_code=None,
                message="error: reference to 'LWE' is ambiguous",
            )
        },
        failure_stage="gbs_build_failed",
    )

    assert uncertain.repair_allowed == REPAIR_DENIED
    assert uncertain.failure_class == "uncertain"
    assert unverified_type.repair_allowed == REPAIR_NEEDS_CONFIRMATION
    assert unverified_type.failure_class == "source_repairable_unverified_type"
    assert uncertain.failure_class != unverified_type.failure_class
