"""Structured tracing utilities for analyzer layers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

TRACE_LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}


@dataclass(frozen=True)
class TraceRecord:
    """One structured trace event."""

    ts: str
    level: str
    layer: str
    event: str
    fields: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "level": self.level,
            "layer": self.layer,
            "event": self.event,
            **self.fields,
        }


class TraceLogger:
    """Write human-readable and JSONL trace logs."""

    def __init__(self, output_dir: Path | str, *, debug: bool = False) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.min_level = TRACE_LEVELS["DEBUG" if debug else "INFO"]
        self._text_file = self._open("trace.log")
        self._jsonl_file = self._open("trace.jsonl")
        self._closed = False

    def _open(self, name: str) -> TextIO:
        return (self.output_dir / name).open("a", encoding="utf-8")

    def close(self) -> None:
        if self._closed:
            return
        self._text_file.close()
        self._jsonl_file.close()
        self._closed = True

    def __enter__(self) -> TraceLogger:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    def debug(self, layer: str, event: str, **fields: Any) -> None:
        self.emit("DEBUG", layer, event, **fields)

    def info(self, layer: str, event: str, **fields: Any) -> None:
        self.emit("INFO", layer, event, **fields)

    def warning(self, layer: str, event: str, **fields: Any) -> None:
        self.emit("WARNING", layer, event, **fields)

    def error(self, layer: str, event: str, **fields: Any) -> None:
        self.emit("ERROR", layer, event, **fields)

    def emit(self, level: str, layer: str, event: str, **fields: Any) -> None:
        normalized = level.upper()
        if normalized not in TRACE_LEVELS:
            raise ValueError(f"unknown trace level: {level}")
        if TRACE_LEVELS[normalized] < self.min_level:
            return
        if self._closed:
            raise ValueError("trace logger is closed")

        record = TraceRecord(
            ts=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            level=normalized,
            layer=layer,
            event=event,
            fields=fields,
        )
        payload = record.as_dict()
        self._jsonl_file.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        self._text_file.write(_format_text_record(payload) + "\n")
        self._jsonl_file.flush()
        self._text_file.flush()


def _format_text_record(record: dict[str, Any]) -> str:
    base = f"{record['ts']} {record['level']} {record['layer']} {record['event']}"
    details = {
        key: value
        for key, value in record.items()
        if key not in {"ts", "level", "layer", "event"}
    }
    if not details:
        return base
    return f"{base} {json.dumps(details, ensure_ascii=False, sort_keys=True)}"


def setup_tracing(output_dir: Path | str, *, trace: bool = False) -> TraceLogger:
    """Create a trace logger using DEBUG level when ``trace`` is enabled."""

    return TraceLogger(output_dir, debug=trace)
