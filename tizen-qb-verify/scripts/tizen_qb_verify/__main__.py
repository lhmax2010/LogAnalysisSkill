"""QuickBuild verification command entry points."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn, TextIO


class _CampaignCliArgumentError(ValueError):
    """Raised instead of argparse's stderr+exit path for the JSON-only command."""


class _CampaignRepairStepParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise _CampaignCliArgumentError(message)


def _main_qb_trigger(argv: list[str], *, stdout: TextIO, stderr: TextIO) -> int:
    from tizen_qb_verify.qb_trigger import QbTriggerOptions, empty_result, qb_trigger

    parser = _CampaignRepairStepParser(prog="tizen_qb_verify qb-trigger")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--verification-ids")
    selection.add_argument("--units-file", type=Path)
    parser.add_argument("--state-db", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--retrigger", action="store_true")
    try:
        args = parser.parse_args(argv)
        code, results = qb_trigger(QbTriggerOptions(**vars(args)), stderr=stderr)
    except _CampaignCliArgumentError:
        code, results = 2, [dict(empty_result(), error_code="INVALID_ARGS")]
    print(json.dumps(results, ensure_ascii=False, sort_keys=True), file=stdout)
    return code


def _main_qb_result_fetch(argv: list[str], *, stdout: TextIO, stderr: TextIO) -> int:
    from tizen_qb_verify.qb_result_fetch import QbResultFetchOptions, empty_result, qb_result_fetch

    parser = _CampaignRepairStepParser(prog="tizen_qb_verify qb-result-fetch")
    parser.add_argument("--request-id")
    parser.add_argument("--qb-build-id")
    parser.add_argument("--requests-file", type=Path)
    parser.add_argument("--accept-snapshot-drift", action="store_true")
    parser.add_argument("--state-db", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    try:
        args = parser.parse_args(argv)
        code, results = qb_result_fetch(QbResultFetchOptions(**vars(args)), stderr=stderr)
    except _CampaignCliArgumentError:
        code, results = 2, [dict(empty_result(), error_code="INVALID_ARGS")]
    print(json.dumps(results, ensure_ascii=False, sort_keys=True), file=stdout)
    return code


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "qb-trigger":
        return _main_qb_trigger(argv[1:], stdout=sys.stdout, stderr=sys.stderr)
    if argv and argv[0] == "qb-result-fetch":
        return _main_qb_result_fetch(argv[1:], stdout=sys.stdout, stderr=sys.stderr)
    parser = argparse.ArgumentParser(prog="tizen_qb_verify")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("qb-trigger", add_help=False)
    commands.add_parser("qb-result-fetch", add_help=False)
    parser.parse_args(argv)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
