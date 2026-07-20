"""CLI for batch QuickBuild CI triage orchestration."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import TextIO

from ci_triage.orchestrator import BatchTriageOptions, CiTriageOrchestrator
from ci_triage.quickbuild import DEFAULT_COOKIE_PATH
from ci_triage.runner import discover_sibling_pythonpath
from ci_triage.sources import QUICKBUILD_OVERVIEW_CONFIG_ID, QuickBuildSource

EXIT_SUCCESS = 0
EXIT_FAILED = 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ci_triage_batch",
        description=(
            "Discover recent QuickBuild failures and run CI triage for each failed package."
        ),
    )
    parser.add_argument(
        "--since",
        help=(
            "Naive QuickBuild begin-date lower bound, for example 2026-07-02T00:00:00. "
            "Defaults to now minus --hours."
        ),
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Look back this many hours when --since is omitted. Defaults to 24.",
    )
    parser.add_argument(
        "--state-root",
        type=Path,
        default=Path(".ci_triage"),
        help="Persistent state root. Defaults to .ci_triage.",
    )
    parser.add_argument(
        "--cookie",
        type=Path,
        default=DEFAULT_COOKIE_PATH,
        help=f"Browser-exported QuickBuild cookie JSON. Defaults to {DEFAULT_COOKIE_PATH}.",
    )
    parser.add_argument(
        "--overview-id",
        default=QUICKBUILD_OVERVIEW_CONFIG_ID,
        help=(
            "QuickBuild overview config id to scrape. "
            f"Defaults to {QUICKBUILD_OVERVIEW_CONFIG_ID}."
        ),
    )
    parser.add_argument(
        "--retry-limit",
        type=int,
        default=3,
        help="FAILED_* retry limit before FAILED_PERMANENT. Defaults to 3.",
    )
    parser.add_argument(
        "--arch",
        action="append",
        help=(
            "QuickBuild GBS report arch to scan, for example standard-armv7l. "
            "May be repeated. Defaults to all supported arches."
        ),
    )
    parser.add_argument(
        "--git-ssh-command",
        help=(
            "Optional GIT_SSH_COMMAND for Gerrit fetches; also read by the single-build "
            "runner from CI_TRIAGE_GIT_SSH_COMMAND."
        ),
    )
    return parser


def main(
    argv: list[str] | None = None,
    *,
    stderr: TextIO = sys.stderr,
    extra_pythonpath: tuple[Path, ...] = (),
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        since = _parse_since(args.since, hours=args.hours)
    except ValueError as exc:
        parser.error(str(exc))

    paths = extra_pythonpath or discover_sibling_pythonpath(
        launcher_path=Path(__file__).resolve().parents[1] / "run_ci_triage_batch.py"
    )
    source = QuickBuildSource(cookie_path=args.cookie, overview_config_id=args.overview_id)
    orchestrator = CiTriageOrchestrator(
        source=source,
        options=BatchTriageOptions(
            state_root=args.state_root,
            cookie_path=args.cookie,
            retry_limit=args.retry_limit,
            arches=tuple(args.arch) if args.arch else BatchTriageOptions().arches,
            extra_pythonpath=paths,
            git_ssh_command=args.git_ssh_command,
        ),
    )
    result = orchestrator.run(since)
    print(f"ci_triage_batch: discovered {result.discovered_builds} failed builds", file=stderr)
    print(f"ci_triage_batch: package units {result.package_units}", file=stderr)
    print(f"ci_triage_batch: report written to {result.daily_report_path}", file=stderr)
    for warning in result.warnings:
        print(f"ci_triage_batch: warning: {warning}", file=stderr)
    return EXIT_SUCCESS


def _parse_since(value: str | None, *, hours: int) -> datetime:
    if value:
        return datetime.fromisoformat(value)
    if hours <= 0:
        raise ValueError("--hours must be positive")
    return datetime.now() - timedelta(hours=hours)


if __name__ == "__main__":
    raise SystemExit(main())
