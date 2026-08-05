"""CLI for the one-build QuickBuild triage vertical slice."""

from __future__ import annotations

import argparse
import json
import sys
from json import JSONDecodeError
from pathlib import Path
from typing import TextIO

from ci_triage.campaign_repair_step import (
    CampaignRepairStepOptions,
    campaign_repair_step,
)
from ci_triage.quickbuild import DEFAULT_COOKIE_PATH
from ci_triage.runner import TriageOptions, discover_sibling_pythonpath, run_triage
from ci_triage.state import StateDatabase
from ci_triage.verify.build_verify import (
    BuildVerifyOptions,
    build_verify,
    build_verify_to_json,
)
from ci_triage.verify.convergence import (
    check_convergence,
    touched_files_from_json,
    write_convergence_result,
)
from ci_triage.verify.gerrit_submit import (
    GerritSubmitOptions,
    exit_code_for_release,
    exit_code_for_submit,
    gerrit_submit,
    release_verified_worktree,
    write_gerrit_submit_result,
    write_release_result,
)

EXIT_SUCCESS = 0
EXIT_FAILED = 1
EXIT_FILE_MISSING = 2
EXIT_JSON_INVALID = 3


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


def check_convergence_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ci_triage check-convergence",
        description="Decide whether another build-repair iteration should continue.",
    )
    parser.add_argument("--current-evidence", type=Path, required=True)
    parser.add_argument("--previous-evidence", type=Path)
    parser.add_argument("--touched-files", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def gerrit_submit_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ci_triage gerrit-submit",
        description="Validate a GERRIT_READY verification record and emit a dry-run Gerrit push.",
    )
    parser.add_argument("--verification-id", required=True)
    parser.add_argument("--state-db", type=Path, required=True)
    parser.add_argument("--gerrit-host", required=True)
    parser.add_argument("--gerrit-port", required=True)
    parser.add_argument("--gerrit-user", required=True)
    parser.add_argument("--submit-target", required=True)
    parser.add_argument("--submit-mode", choices=("dry-run", "submit"), default="dry-run")
    parser.add_argument("--git-ssh-command")
    parser.add_argument("--output", type=Path, required=True)
    return parser


def release_worktree_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ci_triage release-worktree",
        description="Release the protected worktree marker for a verification record.",
    )
    parser.add_argument("--verification-id", required=True)
    parser.add_argument("--state-db", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser


def campaign_repair_step_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ci_triage campaign-repair-step",
        description="Run one locked, budgeted, and reconciled campaign repair build.",
    )
    parser.add_argument("--campaign-unit-key", required=True)
    parser.add_argument("--state-db", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--round-index", type=int, required=True)
    parser.add_argument("--edit-spec", type=Path, required=True)
    parser.add_argument("--arch", required=True)
    parser.add_argument("--wall-timeout", type=int)
    return parser


def main(
    argv: list[str] | None = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
    extra_pythonpath: tuple[Path, ...] = (),
) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "build-verify":
        return _main_build_verify(argv[1:], stderr=stderr, extra_pythonpath=extra_pythonpath)
    if argv and argv[0] == "check-convergence":
        return _main_check_convergence(argv[1:], stderr=stderr)
    if argv and argv[0] == "gerrit-submit":
        return _main_gerrit_submit(argv[1:], stderr=stderr)
    if argv and argv[0] == "release-worktree":
        return _main_release_worktree(argv[1:], stderr=stderr)
    if argv and argv[0] == "campaign-repair-step":
        return _main_campaign_repair_step(
            argv[1:],
            stdout=stdout,
            extra_pythonpath=extra_pythonpath,
        )

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


def _main_check_convergence(argv: list[str], *, stderr: TextIO) -> int:
    parser = check_convergence_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code == 0:
            raise
        return EXIT_FAILED

    paths = [args.current_evidence]
    if args.previous_evidence is not None:
        paths.append(args.previous_evidence)
    if args.touched_files is not None:
        paths.append(args.touched_files)
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        print("ci_triage check-convergence: missing file(s): " + ", ".join(missing), file=stderr)
        return EXIT_FILE_MISSING

    try:
        current = _read_json(args.current_evidence)
        previous = (
            _read_json(args.previous_evidence) if args.previous_evidence is not None else None
        )
        touched = (
            touched_files_from_json(args.touched_files) if args.touched_files is not None else None
        )
    except (JSONDecodeError, ValueError) as exc:
        print(f"ci_triage check-convergence: invalid JSON: {exc}", file=stderr)
        return EXIT_JSON_INVALID

    result = check_convergence(current, previous, touched_files=touched)
    write_convergence_result(result, args.output)
    print(json.dumps(result.to_dict(), sort_keys=True), file=stderr)
    print(f"ci_triage check-convergence: result written to {args.output}", file=stderr)
    return EXIT_SUCCESS


def _main_gerrit_submit(argv: list[str], *, stderr: TextIO) -> int:
    parser = gerrit_submit_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code == 0:
            raise
        return EXIT_FAILED
    result = gerrit_submit(
        GerritSubmitOptions(
            verification_id=args.verification_id,
            state_db=StateDatabase(args.state_db),
            gerrit_host=args.gerrit_host,
            gerrit_port=args.gerrit_port,
            gerrit_user=args.gerrit_user,
            submit_target=args.submit_target,
            submit_mode=args.submit_mode,
            git_ssh_command=args.git_ssh_command,
        )
    )
    write_gerrit_submit_result(result, args.output)
    print(json.dumps(result.to_dict(), sort_keys=True), file=stderr)
    print(f"ci_triage gerrit-submit: result written to {args.output}", file=stderr)
    return exit_code_for_submit(result)


def _main_release_worktree(argv: list[str], *, stderr: TextIO) -> int:
    parser = release_worktree_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code == 0:
            raise
        return EXIT_FAILED
    result = release_verified_worktree(StateDatabase(args.state_db), args.verification_id)
    if args.output is not None:
        write_release_result(result, args.output)
        print(f"ci_triage release-worktree: result written to {args.output}", file=stderr)
    print(json.dumps(result.to_dict(), sort_keys=True), file=stderr)
    return exit_code_for_release(result)


def _main_campaign_repair_step(
    argv: list[str],
    *,
    stdout: TextIO,
    extra_pythonpath: tuple[Path, ...],
) -> int:
    args = campaign_repair_step_parser().parse_args(argv)
    paths = extra_pythonpath or discover_sibling_pythonpath(
        launcher_path=Path(__file__).resolve().parents[1] / "run_ci_triage.py"
    )
    outcome = campaign_repair_step(
        CampaignRepairStepOptions(
            campaign_unit_key=args.campaign_unit_key,
            state_db=StateDatabase(args.state_db),
            config_path=args.config,
            round_index=args.round_index,
            edit_spec_path=args.edit_spec,
            arch_raw=args.arch,
            wall_timeout=args.wall_timeout,
            extra_pythonpath=paths,
        )
    )
    print(json.dumps(outcome.result.to_dict(), sort_keys=True), file=stdout)
    return outcome.exit_code


def _read_json(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return raw


if __name__ == "__main__":
    raise SystemExit(main())
