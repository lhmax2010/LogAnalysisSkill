"""CLI for the one-build QuickBuild triage vertical slice."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TextIO

from ci_triage.quickbuild import DEFAULT_COOKIE_PATH
from ci_triage.runner import TriageOptions, discover_sibling_pythonpath, run_triage

EXIT_SUCCESS = 0
EXIT_FAILED = 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ci_triage",
        description=(
            "Run one QuickBuild failed build through full-log download, Gerrit source "
            "checkout, gbs_analyzer, and gbs_patch_suggest."
        ),
    )
    parser.add_argument("build_id", help="QuickBuild build id, for example 1118282.")
    parser.add_argument(
        "--cookie",
        type=Path,
        default=DEFAULT_COOKIE_PATH,
        help=f"Browser-exported QuickBuild cookie JSON. Defaults to {DEFAULT_COOKIE_PATH}.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("ci_triage_out"),
        help="Output root. The build report is written below <output-root>/<build_id>/.",
    )
    parser.add_argument(
        "--spec-name",
        help="Failed package spec_name to process when a build has multiple failed packages.",
    )
    parser.add_argument(
        "--arch",
        help=(
            "QuickBuild GBS report arch, for example standard-armv7l. Required for "
            "automatic failed-package discovery when --spec-name is omitted."
        ),
    )
    parser.add_argument(
        "--git-ssh-command",
        help=(
            "Optional GIT_SSH_COMMAND for Gerrit fetches; also read from "
            "CI_TRIAGE_GIT_SSH_COMMAND."
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
    paths = extra_pythonpath or discover_sibling_pythonpath(
        launcher_path=Path(__file__).resolve().parents[1] / "run_ci_triage.py"
    )
    result = run_triage(
        TriageOptions(
            build_id=args.build_id,
            output_root=args.output_root,
            cookie_path=args.cookie,
            spec_name=args.spec_name,
            arch=args.arch,
            extra_pythonpath=paths,
            git_ssh_command=args.git_ssh_command,
        )
    )
    print(f"ci_triage: status {result.status}", file=stderr)
    print(f"ci_triage: report written to {result.report_path}", file=stderr)
    if result.error:
        print(f"ci_triage: {result.error}", file=stderr)
    return EXIT_SUCCESS if result.exit_code == 0 else EXIT_FAILED


if __name__ == "__main__":
    raise SystemExit(main())
