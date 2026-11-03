"""Sandbox submission command entry point."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import NoReturn, TextIO

from tizen_campaign_core.campaign_state import CampaignStateBusy

from tizen_sandbox_submit.sandbox_submit import (
    SandboxSubmitOptions,
    SandboxSubmitOutcome,
    empty_payload,
    invalid_outcome,
    sandbox_submit,
)


class _CampaignCliArgumentError(ValueError):
    """Raised instead of argparse's stderr+exit path for the JSON-only command."""


class _CampaignRepairStepParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise _CampaignCliArgumentError(message)


def _main_sandbox_submit(argv: list[str], *, stdout: TextIO, stderr: TextIO) -> int:
    parser = _CampaignRepairStepParser(prog="tizen_sandbox_submit sandbox-submit")
    parser.add_argument("--verification-ids", required=True)
    parser.add_argument("--state-db", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--sandbox-branch", required=True)
    parser.add_argument("--message-brief")
    parser.add_argument("--edit-source-kind", choices=("t1_cherry_pick", "generated", "suppress"))
    try:
        args = parser.parse_args(argv)
        result = sandbox_submit(SandboxSubmitOptions(**vars(args)))
    except _CampaignCliArgumentError as exc:
        result = invalid_outcome(str(exc))
    except Exception as exc:
        busy = isinstance(exc, CampaignStateBusy)
        payload = empty_payload()
        payload.update(
            action="busy" if busy else "rejected",
            error_code="CAMPAIGN_STATE_BUSY" if busy else "INTERNAL_ERROR",
            reason=f"{type(exc).__name__}: {exc}",
        )
        result = SandboxSubmitOutcome(4 if busy else 5, payload)
        traceback.print_exc(file=stderr)
    print(json.dumps(result.payload, sort_keys=True), file=stdout)
    return result.exit_code


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "sandbox-submit":
        return _main_sandbox_submit(argv[1:], stdout=sys.stdout, stderr=sys.stderr)
    parser = argparse.ArgumentParser(prog="tizen_sandbox_submit")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("sandbox-submit", add_help=False)
    parser.parse_args(argv)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
