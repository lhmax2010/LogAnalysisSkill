"""Layer 0+1 buildlog scanner and diagnostic extractor."""

from __future__ import annotations

import gzip
import mmap
import re
import shlex
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gbs_analyzer._utils.command_parser import parse_command
from gbs_analyzer._utils.source_to_object import (
    build_suffix_index,
    is_supported_source,
    match_make_target,
)
from gbs_analyzer.tracing import TraceLogger

PHASE_PATTERN = re.compile(r"^\+\s+(?P<phase>%(?:prep|build|install|check|clean|files|setup)\b.*)")
EXECUTING_PHASE_PATTERN = re.compile(r"^Executing\((?P<phase>%(?:prep|build|install|check))\):")
COMMAND_PATTERN = re.compile(r"^\+\s+(?P<command>.+)")
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
GBS_TIMESTAMP_PATTERN = re.compile(r"^\[\s*(?P<seconds>\d+)s\]\s*")
COMPILER_PATTERN = re.compile(
    r"(?P<file>[^\s:][^:]*\.(?:c|cc|cpp|cxx|S|s|cu|h|hh|hpp|hxx)):"
    r"(?P<line>\d+)(?::(?P<column>\d+))?:\s*"
    r"(?P<severity>fatal error|error|warning):\s*(?P<message>.*)",
    re.IGNORECASE,
)
LINKER_UNDEF_PATTERN = re.compile(r"undefined reference to [`'\"](?P<symbol>.+?)[`'\"]")
LINKER_MISSING_PATTERN = re.compile(r"cannot find -l(?P<library>[A-Za-z0-9_.+-]+)")
PATCH_PATTERNS = [
    re.compile(r"Patch\s*#?(?P<num>\d+)\s*(?:\(.*\))?\s*failed", re.IGNORECASE),
    re.compile(r"Hunk\s*#?(?P<num>\d+)\s*FAILED", re.IGNORECASE),
    re.compile(r"can't find file to patch(?: at input line (?P<line>\d+))?", re.IGNORECASE),
    re.compile(
        r"(?P<num>\d+)\s+out of\s+(?P<total>\d+)\s+hunks?\s+ignored",
        re.IGNORECASE,
    ),
    re.compile(r"patch:?\s*\*{4}\s*malformed patch at line (?P<line>\d+)", re.IGNORECASE),
    re.compile(r"patch failed:\s*(?P<file>[^\s]+):(?P<line>\d+)", re.IGNORECASE),
    re.compile(r"error:\s*patch(?:[\d:]+)?\s*failed", re.IGNORECASE),
]
MAKE_CASCADE_PATTERN = re.compile(
    r"make(?:\[\d+\])?: \*\*\* (?:\[[^\]]+:)?\s*\[(?P<target>[^\]]+)\] Error \d+"
)
RPM_PHASE_PATTERN = re.compile(r"error: Bad exit status from .*\((?P<phase>%\w+)\)")
DIAGNOSTIC_MARKERS = (
    "error",
    "fatal",
    "warning:",
    "undefined reference",
    "cannot find -l",
    "nothing provides",
    "patch",
    "hunk",
    "file not found",
    "unpackaged",
    "werror",
    "make",
    "spec file",
)


@dataclass(frozen=True)
class LogLine:
    line_no: int
    raw_offset: int
    text: str
    raw_text: str
    gbs_seconds: int | None = None


@dataclass
class CommandRecord:
    id: str
    line_no: int
    raw_offset: int
    phase: str | None
    argv_short: str
    argv_full: str | None
    rsp_expanded: dict[str, Any]
    command_degraded: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "line_no": self.line_no,
            "raw_offset": self.raw_offset,
            "phase": self.phase,
            "argv_short": self.argv_short,
            "argv_full": self.argv_full,
            "rsp_expanded": self.rsp_expanded,
            "command_degraded": self.command_degraded,
        }


@dataclass
class DiagnosticEvent:
    id: str
    kind: str
    severity: str
    message: str
    line_no: int
    raw_offset: int
    phase: str | None
    command_id: str | None
    file: str | None = None
    line: int | None = None
    column: int | None = None
    target: str | None = None
    parent: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "kind": self.kind,
            "severity": self.severity,
            "message": self.message,
            "line_no": self.line_no,
            "raw_offset": self.raw_offset,
            "phase": self.phase,
            "command_id": self.command_id,
            "details": self.details,
        }
        optional = {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "target": self.target,
            "parent": self.parent,
        }
        data.update({key: value for key, value in optional.items() if value is not None})
        return data


@dataclass
class ScanResult:
    schema_version: str
    buildlog_path: str
    buildlog_size_bytes: int
    is_gzip: bool
    failed_phase: str | None
    phases: list[dict[str, Any]]
    commands: list[CommandRecord]
    events: list[DiagnosticEvent]
    degraded_reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "buildlog_path": self.buildlog_path,
            "buildlog_size_bytes": self.buildlog_size_bytes,
            "is_gzip": self.is_gzip,
            "failed_phase": self.failed_phase,
            "phases": self.phases,
            "commands": [command.as_dict() for command in self.commands],
            "events": [event.as_dict() for event in self.events],
            "degraded_reasons": self.degraded_reasons,
        }


class BuildLogScanner:
    """Single-pass scanner for Tizen gbs build logs."""

    def __init__(
        self,
        *,
        cwd: str | Path | None = None,
        trace_logger: TraceLogger | None = None,
    ) -> None:
        self.cwd = Path(cwd) if cwd is not None else Path.cwd()
        self.trace_logger = trace_logger

    def scan(self, buildlog_path: str | Path) -> ScanResult:
        path = Path(buildlog_path)
        state = _ScanState(cwd=self.cwd, trace_logger=self.trace_logger)
        state.trace("INFO", "scan_started", path=str(path))
        for line in _iter_log_lines(path):
            state.process(line)
        state.finish_pending_command()
        result = ScanResult(
            schema_version="scan_result/v1",
            buildlog_path=str(path),
            buildlog_size_bytes=path.stat().st_size,
            is_gzip=path.suffix == ".gz",
            failed_phase=state.failed_phase,
            phases=state.phases,
            commands=state.commands,
            events=state.events,
            degraded_reasons=state.degraded_reasons,
        )
        state.trace(
            "INFO",
            "scan_completed",
            commands=len(result.commands),
            events=len(result.events),
            failed_phase=result.failed_phase,
        )
        return result


@dataclass
class _PendingCommand:
    line_no: int
    raw_offset: int
    lines: list[str]
    raw_lines: list[str]
    gbs_seconds: int | None


class _ScanState:
    def __init__(self, *, cwd: Path, trace_logger: TraceLogger | None) -> None:
        self.cwd = cwd
        self.trace_logger = trace_logger
        self.current_phase: str | None = None
        self.current_command_id: str | None = None
        self.commands: list[CommandRecord] = []
        self.events: list[DiagnosticEvent] = []
        self.phases: list[dict[str, Any]] = []
        self.failed_phase: str | None = None
        self.degraded_reasons: list[str] = []
        self._pending_command: _PendingCommand | None = None
        self._source_to_event: dict[str, str] = {}
        self._last_patch_event_by_phase: dict[str, str] = {}

    def trace(self, level: str, event: str, **fields: Any) -> None:
        if self.trace_logger is not None:
            self.trace_logger.emit(level, "L0_scan", event, **fields)

    def process(self, line: LogLine) -> None:
        phase = _match_phase_marker(line.text)
        if phase is not None:
            self.finish_pending_command()
            self.current_phase = phase
            self.phases.append(
                {
                    "phase": self.current_phase,
                    "line_no": line.line_no,
                    "raw_offset": line.raw_offset,
                }
            )
            self.trace(
                "INFO",
                "phase_marker_detected",
                phase=self.current_phase,
                line_no=line.line_no,
                offset=line.raw_offset,
                text=line.text,
                raw_text=line.raw_text,
                gbs_seconds=line.gbs_seconds,
            )
            return

        command_match = COMMAND_PATTERN.match(line.text)
        if command_match:
            self.finish_pending_command()
            self._pending_command = _PendingCommand(
                line_no=line.line_no,
                raw_offset=line.raw_offset,
                lines=[command_match.group("command")],
                raw_lines=[line.raw_text],
                gbs_seconds=line.gbs_seconds,
            )
            if not _continues(command_match.group("command")):
                self.finish_pending_command()
            return

        if self._pending_command is not None:
            self._pending_command.lines.append(line.text)
            self._pending_command.raw_lines.append(line.raw_text)
            if not _continues(line.text):
                self.finish_pending_command()
            return

        event = self._extract_event(line)
        if event is not None:
            self._add_event(event, line)

    def finish_pending_command(self) -> None:
        if self._pending_command is None:
            return
        command_id = f"C{len(self.commands) + 1:03d}"
        argv_line = "\n".join(self._pending_command.lines)
        parsed = parse_command(argv_line, self.cwd)
        command = CommandRecord(
            id=command_id,
            line_no=self._pending_command.line_no,
            raw_offset=self._pending_command.raw_offset,
            phase=self.current_phase,
            argv_short=str(parsed["argv_short"]),
            argv_full=parsed["argv_full"] if isinstance(parsed["argv_full"], str) else None,
            rsp_expanded=parsed["rsp_expanded"],
            command_degraded=bool(parsed["command_degraded"]),
        )
        self.commands.append(command)
        self.current_command_id = command_id
        self.trace(
            "INFO",
            "command_boundary_detected",
            command_id=command_id,
            phase=self.current_phase,
            line_no=command.line_no,
            offset=command.raw_offset,
            text=argv_line,
            raw_text="\n".join(self._pending_command.raw_lines),
            gbs_seconds=self._pending_command.gbs_seconds,
        )
        if command.command_degraded:
            self.degraded_reasons.append(f"command_{command_id}_rsp_unavailable")
        self._pending_command = None

    def _add_event(self, event: DiagnosticEvent, line: LogLine | None = None) -> None:
        if event.kind == "rpm_phase":
            phase = str(event.details.get("phase") or event.phase or "")
            patch_parent = self._last_patch_event_by_phase.get(phase)
            if phase == "%prep" and patch_parent is not None:
                event.parent = patch_parent
                event.details["derived_from"] = "patch_failed"

        if event.kind == "make_cascade" and event.target is not None:
            suffix_index = build_suffix_index(self._source_to_event)
            event.parent = match_make_target(event.target, suffix_index)
            if event.parent is not None:
                self.trace(
                    "INFO",
                    "cascade_associated",
                    event_id=event.id,
                    parent=event.parent,
                    target=event.target,
                )

        self.events.append(event)
        if event.kind == "patch" and event.phase is not None:
            self._last_patch_event_by_phase[event.phase] = event.id
        if event.file is not None and is_supported_source(event.file):
            self._source_to_event[event.file] = event.id
        if event.kind != "make_cascade":
            self.failed_phase = event.phase or self.failed_phase
        trace_fields: dict[str, Any] = {
            "event_id": event.id,
            "kind": event.kind,
            "phase": event.phase,
            "line_no": event.line_no,
            "offset": event.raw_offset,
        }
        if line is not None:
            trace_fields.update(
                {
                    "text": line.text,
                    "raw_text": line.raw_text,
                    "gbs_seconds": line.gbs_seconds,
                }
            )
        self.trace("INFO", "diagnostic_detected", **trace_fields)

    def _extract_event(self, line: LogLine) -> DiagnosticEvent | None:
        event_id = f"E{len(self.events) + 1:03d}"
        text = line.text
        lowered = text.lower()
        if not _may_contain_diagnostic(lowered):
            return None

        if "nothing provides" in lowered:
            return self._event(event_id, "depsolve", "error", text, line)

        patch_details = _match_patch(text)
        if patch_details is not None:
            message = str(patch_details.pop("_message", text))
            return self._event(event_id, "patch", "error", message, line, details=patch_details)

        if "file not found:" in lowered or "installed (but unpackaged) file(s) found" in lowered:
            return self._event(event_id, "install_missing", "error", text, line)

        if "-werror" in lowered or "all warnings being treated as errors" in lowered:
            compiler_match = COMPILER_PATTERN.search(text)
            if compiler_match:
                return self._werror_event(event_id, line, compiler_match)
            return self._event(event_id, "werror", "error", text, line)

        linker_missing = LINKER_MISSING_PATTERN.search(text)
        if linker_missing:
            return self._event(
                event_id,
                "linker_missing",
                "error",
                text,
                line,
                details={"library": linker_missing.group("library")},
            )

        linker_undef = LINKER_UNDEF_PATTERN.search(text)
        if linker_undef:
            return self._event(
                event_id,
                "linker_undef",
                "error",
                text,
                line,
                details={"symbol": linker_undef.group("symbol")},
            )

        compiler_match = COMPILER_PATTERN.search(text)
        if compiler_match:
            return self._compiler_event(event_id, line, compiler_match)

        rpm_phase = RPM_PHASE_PATTERN.search(text)
        if rpm_phase:
            return self._event(
                event_id,
                "rpm_phase",
                "error",
                text,
                line,
                details={"phase": rpm_phase.group("phase")},
            )

        make_cascade = MAKE_CASCADE_PATTERN.search(text)
        if make_cascade:
            return self._event(
                event_id,
                "make_cascade",
                "error",
                text,
                line,
                target=make_cascade.group("target"),
            )

        if "spec file" in lowered and "error" in lowered:
            return self._event(event_id, "spec_script", "error", text, line)

        if _looks_like_raw_error(lowered):
            return self._event(event_id, "raw_error", "error", text, line)

        return None

    def _compiler_event(
        self, event_id: str, line: LogLine, match: re.Match[str]
    ) -> DiagnosticEvent:
        column = match.group("column")
        file_path = match.group("file")
        details: dict[str, Any] = {"is_assembler": _is_assembler_source(file_path)}
        tool = self._current_command_tool()
        if tool is not None:
            details["tool"] = tool
        return self._event(
            event_id,
            "compiler",
            _normalize_severity(match.group("severity")),
            match.group("message"),
            line,
            file=file_path,
            diagnostic_line=int(match.group("line")),
            column=int(column) if column is not None else None,
            details=details,
        )

    def _werror_event(self, event_id: str, line: LogLine, match: re.Match[str]) -> DiagnosticEvent:
        column = match.group("column")
        file_path = match.group("file")
        details: dict[str, Any] = {"is_assembler": _is_assembler_source(file_path)}
        tool = self._current_command_tool()
        if tool is not None:
            details["tool"] = tool
        return self._event(
            event_id,
            "werror",
            _normalize_severity(match.group("severity")),
            match.group("message"),
            line,
            file=file_path,
            diagnostic_line=int(match.group("line")),
            column=int(column) if column is not None else None,
            details=details,
        )

    def _current_command_tool(self) -> str | None:
        if self.current_command_id is None:
            return None
        for command in reversed(self.commands):
            if command.id == self.current_command_id:
                return _tool_from_command(command.argv_short)
        return None

    def _event(
        self,
        event_id: str,
        kind: str,
        severity: str,
        message: str,
        line: LogLine,
        *,
        file: str | None = None,
        diagnostic_line: int | None = None,
        column: int | None = None,
        target: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> DiagnosticEvent:
        return DiagnosticEvent(
            id=event_id,
            kind=kind,
            severity=severity,
            message=message,
            line_no=line.line_no,
            raw_offset=line.raw_offset,
            phase=self.current_phase,
            command_id=self.current_command_id,
            file=file,
            line=diagnostic_line,
            column=column,
            target=target,
            details=details or {},
        )


def scan_buildlog(
    buildlog_path: str | Path,
    *,
    cwd: str | Path | None = None,
    trace_logger: TraceLogger | None = None,
) -> ScanResult:
    """Scan a buildlog using the M1 Layer 0+1 scanner."""

    return BuildLogScanner(cwd=cwd, trace_logger=trace_logger).scan(buildlog_path)


def _iter_log_lines(path: Path) -> Iterator[LogLine]:
    if path.suffix == ".gz":
        yield from _iter_gzip_lines(path)
        return
    yield from _iter_mmap_lines(path)


def _iter_mmap_lines(path: Path) -> Iterator[LogLine]:
    if path.stat().st_size == 0:
        return
    with path.open("rb") as file:
        with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mapped:
            line_no = 0
            while True:
                offset = mapped.tell()
                raw_line = mapped.readline()
                if not raw_line:
                    break
                line_no += 1
                raw_text = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                text, gbs_seconds = _normalize_log_text(raw_text)
                yield LogLine(
                    line_no=line_no,
                    raw_offset=offset,
                    text=text,
                    raw_text=raw_text,
                    gbs_seconds=gbs_seconds,
                )


def _iter_gzip_lines(path: Path) -> Iterator[LogLine]:
    raw_offset = 0
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as file:
        for line_no, text in enumerate(file, start=1):
            raw_text = text.rstrip("\r\n")
            normalized, gbs_seconds = _normalize_log_text(raw_text)
            yield LogLine(
                line_no=line_no,
                raw_offset=raw_offset,
                text=normalized,
                raw_text=raw_text,
                gbs_seconds=gbs_seconds,
            )
            raw_offset += len(text.encode("utf-8", errors="replace"))


def _continues(command_line: str) -> bool:
    return command_line.rstrip().endswith("\\")


def _normalize_log_text(raw_text: str) -> tuple[str, int | None]:
    text = ANSI_ESCAPE_PATTERN.sub("", raw_text)
    timestamp = GBS_TIMESTAMP_PATTERN.match(text)
    if timestamp is None:
        return text, None
    return text[timestamp.end() :], int(timestamp.group("seconds"))


def _match_phase_marker(text: str) -> str | None:
    phase_match = PHASE_PATTERN.match(text)
    if phase_match:
        return phase_match.group("phase").split()[0]
    executing_match = EXECUTING_PHASE_PATTERN.match(text)
    if executing_match:
        return executing_match.group("phase")
    return None


def _match_patch(text: str) -> dict[str, str] | None:
    for pattern in PATCH_PATTERNS:
        match = pattern.search(text)
        if match:
            details = {
                key: value
                for key, value in match.groupdict().items()
                if value is not None
            }
            if "can't find file to patch" in text.lower():
                details["_message"] = f"error: patch failed: {text}"
            elif (
                "hunk" in text.lower()
                and "ignored" in text.lower()
                and not text.lower().startswith("hunk")
            ):
                details["_message"] = f"Hunk #{details.get('num', '1')} FAILED: {text}"
            return details
    return None


def _normalize_severity(severity: str) -> str:
    normalized = severity.lower()
    return "error" if normalized == "fatal error" else normalized


def _is_assembler_source(path: str) -> bool:
    return Path(path).suffix.lower() == ".s"


def _tool_from_command(command_line: str) -> str | None:
    try:
        parts = shlex.split(command_line)
    except ValueError:
        parts = command_line.split()
    if not parts:
        return None
    return Path(parts[0]).name


def _may_contain_diagnostic(lowered_text: str) -> bool:
    return any(marker in lowered_text for marker in DIAGNOSTIC_MARKERS)


def _looks_like_raw_error(lowered_text: str) -> bool:
    return "error:" in lowered_text or "fatal:" in lowered_text
