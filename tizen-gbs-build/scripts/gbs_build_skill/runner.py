"""Subprocess runner for Tizen gbs builds."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

DEFAULT_TIMEOUT_SECONDS = 1800
EXIT_TIMEOUT = 124
EXIT_COMMAND_NOT_FOUND = 127
EXIT_ARGS = 2
GBS_FAILURE_LOG_PATTERN = re.compile(
    r"Leaving the logs in (?P<path>/\S+/logs/fail/(?P<pkg>[^/]+)/log\.txt)"
)


@dataclass(frozen=True)
class BuildOptions:
    """Options used to invoke a single gbs build."""

    conf: Path
    arch: str
    output_log: Path
    include_all: bool = False
    timeout: int = DEFAULT_TIMEOUT_SECONDS
    gbs_binary: str = "gbs"
    cwd: Path | None = None


@dataclass(frozen=True)
class BuildResult:
    """Result of a gbs build invocation."""

    exit_code: int
    log_path: Path
    command: tuple[str, ...]
    duration_seconds: float
    timed_out: bool = False
    failure_log_path: Path | None = None
    analysis_log_path: Path | None = None
    package_name: str | None = None


def build_command(options: BuildOptions) -> list[str]:
    """Build the argv list for `gbs build` from runner options."""

    command = [
        options.gbs_binary,
        "-c",
        str(options.conf),
        "build",
        "-A",
        options.arch,
    ]
    if options.include_all:
        command.append("--include-all")
    return command


def _extract_failure_log_path(compiler_log: Path) -> tuple[Path | None, str | None]:
    """Return GBS's structured failure log path and package name, when present."""

    try:
        text = compiler_log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, None

    matches = list(GBS_FAILURE_LOG_PATTERN.finditer(text))
    if not matches:
        return None, None

    last = matches[-1]
    candidate = Path(last.group("path"))
    if not candidate.is_file():
        return None, None
    return candidate, last.group("pkg")


def _build_result(
    *,
    exit_code: int,
    log_path: Path,
    command: tuple[str, ...],
    duration_seconds: float,
    timed_out: bool = False,
) -> BuildResult:
    failure_log_path: Path | None = None
    package_name: str | None = None
    analysis_log_path = log_path
    if exit_code != 0:
        failure_log_path, package_name = _extract_failure_log_path(log_path)
        if failure_log_path is not None:
            analysis_log_path = failure_log_path

    return BuildResult(
        exit_code=exit_code,
        log_path=log_path,
        command=command,
        duration_seconds=duration_seconds,
        timed_out=timed_out,
        failure_log_path=failure_log_path,
        analysis_log_path=analysis_log_path,
        package_name=package_name,
    )


def run_gbs_build(options: BuildOptions) -> BuildResult:
    """Run `gbs build`, streaming stdout and stderr into `options.output_log`.

    The returned exit code is the gbs process exit code, except timeout returns 124 and a
    missing executable returns 127.
    """

    command = build_command(options)
    options.output_log.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()

    with options.output_log.open("w", encoding="utf-8", errors="replace") as log_file:
        try:
            process = subprocess.Popen(
                command,
                cwd=options.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except FileNotFoundError:
            log_file.write(f"{options.gbs_binary}: command not found\n")
            log_file.flush()
            return _build_result(
                exit_code=EXIT_COMMAND_NOT_FOUND,
                log_path=options.output_log,
                command=tuple(command),
                duration_seconds=time.monotonic() - start,
            )

        reader = threading.Thread(
            target=_stream_process_output,
            args=(process, log_file),
            daemon=True,
        )
        reader.start()

        timed_out = False
        try:
            exit_code = process.wait(timeout=options.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            exit_code = EXIT_TIMEOUT
            log_file.write(f"\n[gbs_build_skill] timeout after {options.timeout}s\n")
            log_file.flush()
            process.wait()
        finally:
            reader.join(timeout=5)

    return _build_result(
        exit_code=exit_code,
        log_path=options.output_log,
        command=tuple(command),
        duration_seconds=time.monotonic() - start,
        timed_out=timed_out,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for `python -m gbs_build_skill`."""

    args = _parse_args(argv)
    src_dir = _resolve_src_dir(args.src_dir)
    if args.src_dir is not None and src_dir is None:
        print(f"gbs_build_skill: source directory not found: {args.src_dir}", file=sys.stderr)
        return EXIT_ARGS

    result = run_gbs_build(
        BuildOptions(
            conf=args.conf,
            arch=args.arch,
            include_all=args.include_all,
            output_log=args.output_log,
            timeout=args.timeout,
            cwd=src_dir,
        )
    )
    _print_summary(result, args.timeout)
    return result.exit_code


def _print_summary(result: BuildResult, timeout: int) -> None:
    status = "succeeded" if result.exit_code == 0 else "failed"
    print(f"gbs_build_skill: build {status} (exit {result.exit_code})", file=sys.stderr)
    print(f"gbs_build_skill: compiler log written to {result.log_path}", file=sys.stderr)
    if result.timed_out:
        print(f"gbs_build_skill: timed out after {timeout}s", file=sys.stderr)
    if result.exit_code == 0:
        return
    if result.failure_log_path is None:
        print("gbs_build_skill: failure log: not found in compiler log", file=sys.stderr)
        print(
            f"gbs_build_skill: recommended for analysis: {result.log_path} (compiler log only)",
            file=sys.stderr,
        )
        return
    print(f"gbs_build_skill: failure log: {result.failure_log_path}", file=sys.stderr)
    print(
        f"gbs_build_skill: recommended for analysis: {result.analysis_log_path}",
        file=sys.stderr,
    )
    if result.package_name is not None:
        print(f"gbs_build_skill: package: {result.package_name}", file=sys.stderr)


def _resolve_src_dir(src_dir: Path | None) -> Path | None:
    if src_dir is None:
        return None
    resolved = src_dir.resolve()
    if not resolved.is_dir():
        return None
    return resolved


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m gbs_build_skill",
        description="Run gbs build and stream stdout/stderr into a buildlog.",
    )
    parser.add_argument("--conf", required=True, type=Path, help="Path to gbs.conf")
    parser.add_argument("--arch", required=True, help="Target architecture, e.g. armv7l")
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Pass --include-all to gbs build.",
    )
    parser.add_argument(
        "--output-log",
        required=True,
        type=Path,
        help="Path to write combined gbs stdout/stderr.",
    )
    parser.add_argument(
        "--timeout",
        default=DEFAULT_TIMEOUT_SECONDS,
        type=int,
        help="Build timeout in seconds (default: 1800).",
    )
    parser.add_argument(
        "--src-dir",
        default=None,
        type=Path,
        help="Source directory to run gbs in. Defaults to current working directory.",
    )
    return parser.parse_args(argv)


def _stream_process_output(process: subprocess.Popen[str], log_file: TextIO) -> None:
    if process.stdout is None:
        return
    for chunk in process.stdout:
        log_file.write(chunk)
        log_file.flush()
