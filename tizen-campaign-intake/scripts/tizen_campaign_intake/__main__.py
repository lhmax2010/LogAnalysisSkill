"""Manual intake entry point; startup checks remain reserved for batch 3."""

import argparse
import sys

from tizen_campaign_intake.intake import main as add_unit_main


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "campaign-add-unit":
        return add_unit_main(argv[1:], stdout=sys.stdout)
    parser = argparse.ArgumentParser(prog="tizen_campaign_intake")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("campaign-add-unit", add_help=False)
    commands.add_parser("campaign-start-check", help="reserved for batch 3")
    parser.parse_args(argv)
    parser.error("campaign-start-check is reserved for batch 3")


if __name__ == "__main__":
    raise SystemExit(main())
