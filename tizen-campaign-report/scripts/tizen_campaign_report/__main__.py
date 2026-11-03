"""Campaign reporting and explicit lifecycle command entry points."""

import argparse
import sys

from tizen_campaign_report.report import main as report_main


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    names = ("campaign-report", "campaign-finish-unit", "campaign-release-worktrees")
    if argv and argv[0] in names:
        return report_main(argv[0], argv[1:], stdout=sys.stdout)
    parser = argparse.ArgumentParser(prog="tizen_campaign_report")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in names:
        commands.add_parser(name, add_help=False)
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
