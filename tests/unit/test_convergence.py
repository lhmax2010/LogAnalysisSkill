from __future__ import annotations

import json
from pathlib import Path

from ci_triage.verify.convergence import check_convergence, touched_files_from_json


def primary(
    *,
    file: str = "src/foo.c",
    kind: str = "werror",
    code: str = "-Wdeprecated-declarations",
    message: str = "error: use of deprecated symbol 'OldApi' [-Werror,-Wdeprecated-declarations]",
) -> dict[str, object]:
    return {
        "primary_error": {
            "kind": kind,
            "file": file,
            "line": 42,
            "diagnostic_code": code,
            "message": message,
        }
    }


def packet(
    *,
    primary_data: dict[str, object] | None = None,
    clusters: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    data = primary_data or primary()
    if clusters is not None:
        data["error_clusters"] = {
            "schema_version": "error_clusters/v1",
            "clusters": clusters,
        }
    return data


def cluster(
    *,
    files: list[str],
    warning_option: str = "-Wdeprecated-declarations",
    diagnostic_kinds: list[str] | None = None,
    kind: str = "source_warning_option",
    count: int | None = None,
) -> dict[str, object]:
    return {
        "id": "CL001",
        "kind": kind,
        "diagnostic_kinds": diagnostic_kinds or ["werror"],
        "warning_option": warning_option,
        "count": count if count is not None else len(files),
        "files": files,
        "locations_sample": [{"file": file, "line": index + 1} for index, file in enumerate(files)],
    }


def test_same_primary_and_error_count_is_stalled() -> None:
    previous = packet()
    current = packet()

    result = check_convergence(current, previous, touched_files={"src/foo.c"})

    assert result.verdict == "stalled"
    assert result.confidence == "high"
    assert "fingerprint_unchanged" in result.reason


def test_primary_changes_advances() -> None:
    previous = packet()
    current = packet(primary_data=primary(message="error: use of 'NewApi' [-Werror,-Wfoo]"))

    result = check_convergence(current, previous, touched_files={"src/foo.c"})

    assert result.verdict == "advance"
    assert result.confidence == "medium"


def test_new_source_cluster_in_touched_file_regresses() -> None:
    previous = packet(clusters=[cluster(files=["src/old.c"])])
    current = packet(
        clusters=[
            cluster(files=["src/old.c"]),
            cluster(files=["src/foo.c"], warning_option="-Wimplicit-int"),
        ]
    )

    result = check_convergence(current, previous, touched_files={"src/foo.c"})

    assert result.verdict == "regressed"
    assert "new_source_cluster_in_touched" in result.reason


def test_new_source_cluster_outside_touched_file_does_not_regress() -> None:
    previous = packet(clusters=[cluster(files=["src/old.c"])])
    current = packet(
        primary_data=primary(message="error: moved on to 'NextApi' [-Werror,-Wnext]"),
        clusters=[
            cluster(files=["src/old.c"]),
            cluster(files=["src/other.c"], warning_option="-Wimplicit-int"),
        ],
    )

    result = check_convergence(current, previous, touched_files={"src/foo.c"})

    assert result.verdict == "advance"


def test_missing_touched_files_never_regresses_even_when_error_count_explodes() -> None:
    previous = packet(clusters=[cluster(files=["src/old.c"], count=1)])
    current = packet(
        primary_data=primary(message="error: moved on to 'NextApi' [-Werror,-Wnext]"),
        clusters=[cluster(files=["src/foo.c"], count=40)],
    )

    result = check_convergence(current, previous, touched_files=None)

    assert result.verdict == "advance"
    assert result.regression_suspected is False
    assert result.touched_files_available is False


def test_kind_wrapper_change_with_same_identity_advances_not_regresses() -> None:
    previous = packet()
    current = packet(primary_data=primary(kind="compile_error"))

    result = check_convergence(current, previous, touched_files={"src/foo.c"})

    assert result.verdict == "advance"
    assert result.current_fingerprint is not None
    assert result.previous_fingerprint is not None
    assert result.current_fingerprint["normalized_file"] == (
        result.previous_fingerprint["normalized_file"]
    )


def test_iter_one_baseline_unchanged_primary_is_stalled() -> None:
    baseline = packet()
    current = packet()

    result = check_convergence(current, baseline, touched_files={"src/foo.c"})

    assert result.verdict == "stalled"


def test_regressed_is_checked_before_stalled_when_primary_and_count_match() -> None:
    previous = packet(clusters=[cluster(files=["src/old.c"], count=3)])
    current = packet(
        clusters=[
            cluster(files=["src/old.c"], count=1),
            cluster(files=["src/foo.c"], warning_option="-Wimplicit-int", count=2),
        ]
    )

    result = check_convergence(current, previous, touched_files={"src/foo.c"})

    assert result.error_count == result.previous_error_count
    assert result.verdict == "regressed"
    assert "new_source_cluster_in_touched" in result.reason


def test_existing_cluster_expanding_to_touched_file_regresses() -> None:
    previous = packet(clusters=[cluster(files=["src/old.c"], count=1)])
    current = packet(clusters=[cluster(files=["src/old.c", "src/foo.c"], count=2)])

    result = check_convergence(current, previous, touched_files={"src/foo.c"})

    assert result.verdict == "regressed"
    assert "expanded_source_cluster_in_touched" in result.reason


def test_same_cluster_identity_in_previous_is_not_new() -> None:
    previous = packet(clusters=[cluster(files=["src/foo.c"], count=1)])
    current = packet(
        primary_data=primary(message="error: moved on to 'NextApi' [-Werror,-Wnext]"),
        clusters=[cluster(files=["src/foo.c"], count=1)],
    )

    result = check_convergence(current, previous, touched_files={"src/foo.c"})

    assert result.verdict == "advance"


def test_previous_null_advances_with_low_confidence() -> None:
    result = check_convergence(packet(), None, touched_files={"src/foo.c"})

    assert result.verdict == "advance"
    assert result.confidence == "low"
    assert result.previous_fingerprint is None


def test_cluster_count_increases_without_new_file_does_not_regress() -> None:
    previous = packet(clusters=[cluster(files=["src/foo.c"], count=1)])
    current = packet(
        primary_data=primary(message="error: moved on to 'NextApi' [-Werror,-Wnext]"),
        clusters=[cluster(files=["src/foo.c"], count=20)],
    )

    result = check_convergence(current, previous, touched_files={"src/foo.c"})

    assert result.verdict == "advance"
    assert result.regression_suspected is False


def test_non_source_cluster_in_touched_file_does_not_regress() -> None:
    previous = packet(clusters=[])
    current = packet(
        primary_data=primary(message="error: moved on to 'NextApi' [-Werror,-Wnext]"),
        clusters=[
            cluster(
                files=["src/foo.c"],
                kind="depsolve",
                diagnostic_kinds=["depsolve"],
                warning_option="<none>",
            )
        ],
    )

    result = check_convergence(current, previous, touched_files={"src/foo.c"})

    assert result.verdict == "advance"


def test_touched_files_json_normalizes_build_prefix(tmp_path: Path) -> None:
    path = tmp_path / "touched.json"
    path.write_text(
        json.dumps({"files": ["/home/abuild/rpmbuild/BUILD/pkg-1.0/src/foo.c"]}),
        encoding="utf-8",
    )

    assert touched_files_from_json(path) == {"src/foo.c"}
