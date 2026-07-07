"""CLI for the one-build QuickBuild triage vertical slice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from ci_triage.quickbuild import DEFAULT_COOKIE_PATH
from ci_triage.runner import TriageOptions, discover_sibling_pythonpath, run_triage
from ci_triage.state import StateDatabase
from ci_triage.verify.build_verify import (
    BuildVerifyOptions,
    build_verify,
    build_verify_to_json,
)

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


def build_verify_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ci_triage build-verify",
        description="Apply an edit_spec in a disposable worktree and run one gbs build verify.",
    )
    parser.add_argument("--src-clean", type=Path, required=True)
    parser.add_argument("--base-commit", required=True)
    parser.add_argument("--edit-spec", type=Path, required=True)
    parser.add_argument("--gbs-conf", type=Path, required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--baseline-evidence", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--iter-index", type=int, required=True)
    parser.add_argument("--wall-timeout", type=int, default=3600)
    parser.add_argument("--state-db", type=Path, required=True)
    parser.add_argument("--ci-system", default="quickbuild")
    parser.add_argument("--build-id", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--arch", required=True)
    return parser


def main(
    argv: list[str] | None = None,
    *,
    stderr: TextIO = sys.stderr,
    extra_pythonpath: tuple[Path, ...] = (),
) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "build-verify":
        return _main_build_verify(argv[1:], stderr=stderr, extra_pythonpath=extra_pythonpath)

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


def _main_build_verify(
    argv: list[str],
    *,
    stderr: TextIO,
    extra_pythonpath: tuple[Path, ...],
) -> int:
    parser = build_verify_parser()
    args = parser.parse_args(argv)
    paths = extra_pythonpath or discover_sibling_pythonpath(
        launcher_path=Path(__file__).resolve().parents[1] / "run_ci_triage.py"
    )
    result = build_verify(
        BuildVerifyOptions(
            src_clean=args.src_clean,
            base_commit=args.base_commit,
            edit_spec_path=args.edit_spec,
            gbs_conf=args.gbs_conf,
            package=args.package,
            workspace_root=args.workspace_root,
            baseline_evidence=args.baseline_evidence,
            output_dir=args.output_dir,
            iter_index=args.iter_index,
            wall_timeout=args.wall_timeout,
            state_db=StateDatabase(args.state_db),
            ci_system=args.ci_system,
            build_id=args.build_id,
            project=args.project,
            branch=args.branch,
            arch=args.arch,
            extra_pythonpath=paths,
        )
    )
    output_path = args.output_dir / "build_verify_result.json"
    build_verify_to_json(result, output_path)
    print(json.dumps(result.to_dict(), sort_keys=True), file=stderr)
    print(f"ci_triage build-verify: result written to {output_path}", file=stderr)
    return EXIT_SUCCESS if result.result == "PASS" else EXIT_FAILED


if __name__ == "__main__":
    raise SystemExit(main())
