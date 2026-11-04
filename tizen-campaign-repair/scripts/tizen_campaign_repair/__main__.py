"""Campaign repair command entry point."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import NoReturn, TextIO, cast

from tizen_campaign_core.suppress_policy import PolicyInputError, SourceKind, evaluate
from tizen_ci_shared.env import discover_sibling_pythonpath
from tizen_ci_shared.state import StateDatabase

from tizen_campaign_repair.campaign_repair_step import (
    CampaignRepairStepOptions,
    campaign_repair_step,
)
from tizen_campaign_repair.diff_cli import main as _main_diff_to_edit_spec


class _CampaignCliArgumentError(ValueError):
    """Raised instead of argparse's stderr+exit path for the JSON-only command."""


class _CampaignRepairStepParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise _CampaignCliArgumentError(message)


def campaign_repair_step_parser() -> argparse.ArgumentParser:
    parser = _CampaignRepairStepParser(
        prog="tizen_campaign_repair campaign-repair-step",
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


def _main_campaign_repair_step(
    argv: list[str],
    *,
    stdout: TextIO,
    extra_pythonpath: tuple[Path, ...],
) -> int:
    try:
        args = campaign_repair_step_parser().parse_args(argv)
    except _CampaignCliArgumentError as exc:
        print(json.dumps(_campaign_cli_error_payload(str(exc)), sort_keys=True), file=stdout)
        return 5
    paths = extra_pythonpath or discover_sibling_pythonpath(
        launcher_path=Path(__file__).resolve().parents[1] / "run_campaign_repair.py"
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


def _campaign_cli_error_payload(reason: str) -> dict[str, object]:
    return {
        "result": "FAIL",
        "verdict": "n_a",
        "repair_allowed": "denied",
        "failure_class": None,
        "failure_stage": None,
        "adopted": False,
        "convergence_reason": reason,
        "previous_basis": "none",
        "round_index": 0,
        "arch_norm": "",
        "verification_id": None,
        "evidence_path": None,
        "reconciliation": {
            "other_round_relinks": [],
            "non_campaign_verification_ids": [],
        },
        "warnings": [],
        "invocations_used": 0,
        "error_code": "INVALID_ARGS",
    }


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "campaign-repair-step":
        return _main_campaign_repair_step(argv[1:], stdout=sys.stdout, extra_pythonpath=())
    if argv and argv[0] == "suppress-policy":
        return _main_suppress_policy(argv[1:], stdout=sys.stdout, stderr=sys.stderr)
    if argv and argv[0] == "diff-to-edit-spec":
        return _main_diff_to_edit_spec(argv[1:], stdout=sys.stdout)
    if argv and argv[0] == "propose-fix":
        from tizen_campaign_repair.propose_fix import main as propose_main

        return propose_main(argv[1:], stdout=sys.stdout)
    parser = argparse.ArgumentParser(prog="tizen_campaign_repair")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("campaign-repair-step", add_help=False)
    commands.add_parser("suppress-policy", add_help=False)
    commands.add_parser("diff-to-edit-spec", add_help=False)
    commands.add_parser("propose-fix", add_help=False)
    parser.parse_args(argv)
    return 2


def _main_suppress_policy(argv: list[str], *, stdout: TextIO, stderr: TextIO) -> int:
    parser = _CampaignRepairStepParser(prog="ci_triage suppress-policy")
    parser.add_argument("action", choices=("check",))
    parser.add_argument("--edit-spec", type=Path, required=True)
    parser.add_argument("--src-root", type=Path, required=True)
    parser.add_argument("--source-kind", choices=("t1_cherry_pick", "generated", "suppress"),
                        default="generated")
    try:
        args = parser.parse_args(argv)
        raw = json.loads(args.edit_spec.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"{args.edit_spec} must contain a JSON object")
        result = evaluate(raw, args.src_root, cast(SourceKind, args.source_kind))
    except (ValueError, OSError, PolicyInputError) as exc:
        print(json.dumps({"error_code": "INVALID_ARGS", "reason": str(exc)}, sort_keys=True),
              file=stdout)
        return 2
    print(json.dumps(asdict(result), sort_keys=True), file=stdout)
    if result.verdict == "forbidden":
        print("REJECTED_SUPPRESS_POLICY", file=stderr)
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
