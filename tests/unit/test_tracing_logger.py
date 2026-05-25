import json
from pathlib import Path

import pytest
from gbs_analyzer.tracing import TraceLogger, setup_tracing


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_setup_tracing_writes_info_record(tmp_path: Path) -> None:
    with setup_tracing(tmp_path) as logger:
        logger.info("L0_scan", "phase_marker_detected", phase="%build", offset=42)

    records = read_jsonl(tmp_path / "trace.jsonl")
    assert records == [
        {
            "event": "phase_marker_detected",
            "layer": "L0_scan",
            "level": "INFO",
            "offset": 42,
            "phase": "%build",
            "ts": records[0]["ts"],
        }
    ]
    assert "L0_scan phase_marker_detected" in (tmp_path / "trace.log").read_text(
        encoding="utf-8"
    )


def test_default_logger_filters_debug_records(tmp_path: Path) -> None:
    with TraceLogger(tmp_path) as logger:
        logger.debug("L0_scan", "command_boundary_detected")
        logger.info("L0_scan", "scan_started")

    records = read_jsonl(tmp_path / "trace.jsonl")
    assert [record["event"] for record in records] == ["scan_started"]


def test_trace_mode_keeps_debug_records(tmp_path: Path) -> None:
    with setup_tracing(tmp_path, trace=True) as logger:
        logger.debug("L0_scan", "command_boundary_detected", command_id="C001")

    records = read_jsonl(tmp_path / "trace.jsonl")
    assert records[0]["level"] == "DEBUG"
    assert records[0]["command_id"] == "C001"


def test_logger_creates_output_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "nested" / "trace"
    with TraceLogger(output_dir) as logger:
        logger.warning("L0_scan", "scan_degraded", reason="fixture")

    assert (output_dir / "trace.log").is_file()
    assert (output_dir / "trace.jsonl").is_file()


def test_logger_rejects_unknown_level(tmp_path: Path) -> None:
    with TraceLogger(tmp_path) as logger:
        with pytest.raises(ValueError, match="unknown trace level"):
            logger.emit("NOTICE", "L0_scan", "event")


def test_logger_rejects_write_after_close(tmp_path: Path) -> None:
    logger = TraceLogger(tmp_path)
    logger.close()

    with pytest.raises(ValueError, match="closed"):
        logger.info("L0_scan", "after_close")


def test_close_is_idempotent(tmp_path: Path) -> None:
    logger = TraceLogger(tmp_path)
    logger.close()
    logger.close()

    assert (tmp_path / "trace.log").is_file()
