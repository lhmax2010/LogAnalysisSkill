from gbs_analyzer.error_clusters import build_error_clusters, extract_warning_option


def event(
    event_id: str,
    *,
    kind: str = "werror",
    message: str = "bad enum cast [-Werror,-Wimplicit-enum-enum-cast]",
    file: str = "src/foo.c",
    line: int = 1,
    column: int | None = 2,
    line_no: int | None = None,
) -> dict[str, object]:
    data: dict[str, object] = {
        "id": event_id,
        "kind": kind,
        "severity": "error",
        "message": message,
        "line_no": int(event_id[1:]) if line_no is None else line_no,
        "file": file,
        "line": line,
    }
    if column is not None:
        data["column"] = column
    return data


def packet(events: list[dict[str, object]]) -> dict[str, object]:
    return {"events": events}


def test_extract_warning_option_ignores_werror_promotion() -> None:
    assert extract_warning_option(event("E001")) == "-Wimplicit-enum-enum-cast"
    assert (
        extract_warning_option(
            event("E001", message="bad pointer [-Wpointer-bool-conversion]")
        )
        == "-Wpointer-bool-conversion"
    )
    assert (
        extract_warning_option(
            event("E001", message="bad cast [-Werror,-Wfoo,-Wbar]")
        )
        == "-Wfoo"
    )


def test_extract_warning_option_requires_concrete_source_warning_option() -> None:
    assert extract_warning_option(event("E001", message="bad cast [-Werror]")) is None
    assert extract_warning_option(event("E001", message="bad cast")) is None
    assert extract_warning_option(event("E001", kind="linker_undef")) is None


def test_cluster_emit_threshold_omits_small_repeated_diagnostics() -> None:
    result = build_error_clusters(
        packet(
            [
                event("E001", line=1),
                event("E002", line=2),
            ]
        )
    )

    assert result.summary is None
    assert result.sidecar is None


def test_cluster_emits_at_three_without_large_scale_for_one_file() -> None:
    result = build_error_clusters(
        packet(
            [
                event("E001", line=1),
                event("E002", line=2),
                event("E003", line=3),
            ]
        )
    )

    assert result.summary is not None
    cluster = result.summary["clusters"][0]
    assert cluster["count"] == 3
    assert cluster["file_count"] == 1
    assert cluster["large_scale"] is False
    assert cluster["locations_truncated"] is False
    assert result.sidecar is not None
    assert len(result.sidecar["clusters"][0]["locations"]) == 3


def test_cluster_marks_large_scale_by_count() -> None:
    result = build_error_clusters(
        packet([event(f"E{index:03d}", line=index) for index in range(1, 11)])
    )

    assert result.summary is not None
    cluster = result.summary["clusters"][0]
    assert cluster["count"] == 10
    assert cluster["file_count"] == 1
    assert cluster["large_scale"] is True
    assert cluster["locations_truncated"] is False


def test_cluster_marks_large_scale_by_file_count() -> None:
    result = build_error_clusters(
        packet(
            [
                event("E001", file="a/foo.c", line=1),
                event("E002", file="b/foo.c", line=2),
                event("E003", file="c/foo.c", line=3),
            ]
        )
    )

    assert result.summary is not None
    cluster = result.summary["clusters"][0]
    assert cluster["file_count"] == 3
    assert cluster["large_scale"] is True


def test_locations_sample_prefers_first_occurrence_per_file_then_log_order() -> None:
    events = [
        event("E001", file="a/foo.c", line=1),
        event("E002", file="a/foo.c", line=2),
        event("E003", file="b/foo.c", line=3),
        event("E004", file="c/foo.c", line=4),
        event("E005", file="d/foo.c", line=5),
        event("E006", file="e/foo.c", line=6),
        event("E007", file="f/foo.c", line=7),
        event("E008", file="g/foo.c", line=8),
        event("E009", file="h/foo.c", line=9),
        event("E010", file="i/foo.c", line=10),
        event("E011", file="j/foo.c", line=11),
        event("E012", file="k/foo.c", line=12),
    ]

    result = build_error_clusters(packet(events))

    assert result.summary is not None
    sample = result.summary["clusters"][0]["locations_sample"]
    assert [location["event_id"] for location in sample] == [
        "E001",
        "E003",
        "E004",
        "E005",
        "E006",
        "E007",
        "E008",
        "E009",
        "E010",
        "E011",
    ]
    assert result.summary["clusters"][0]["locations_truncated"] is True


def test_files_are_capped_at_twenty_but_sidecar_keeps_full_locations() -> None:
    events = [
        event(f"E{index:03d}", file=f"dir{index}/foo.c", line=index)
        for index in range(1, 22)
    ]

    result = build_error_clusters(packet(events))

    assert result.summary is not None
    cluster = result.summary["clusters"][0]
    assert len(cluster["files"]) == 20
    assert cluster["file_count"] == 21
    assert result.sidecar is not None
    assert len(result.sidecar["clusters"][0]["locations"]) == 21


def test_truncation_signal_without_cluster_emits_empty_cluster_summary() -> None:
    result = build_error_clusters(
        packet(
            [
                {
                    "id": "E001",
                    "kind": "raw_error",
                    "severity": "error",
                    "message": "fatal error: too many errors emitted, stopping now",
                    "line_no": 99,
                }
            ]
        )
    )

    assert result.summary == {
        "schema_version": "error_clusters/v1",
        "truncated": True,
        "truncation_signals": [
            {
                "line_no": 99,
                "message": "fatal error: too many errors emitted, stopping now",
            }
        ],
        "full_locations_path": None,
        "clusters": [],
    }
    assert result.sidecar is None


def test_truncation_signal_marks_large_cluster_actual_count_may_be_higher() -> None:
    result = build_error_clusters(
        packet(
            [
                event("E001", line=1),
                event("E002", line=2),
                event("E003", line=3),
                {
                    "id": "E004",
                    "kind": "raw_error",
                    "severity": "error",
                    "message": "fatal error: too many errors emitted, stopping now",
                    "line_no": 4,
                },
            ]
        )
    )

    assert result.summary is not None
    assert result.summary["truncated"] is True
    advisory = result.summary["clusters"][0]["advisory"]
    assert "actual occurrences may be higher" in advisory
