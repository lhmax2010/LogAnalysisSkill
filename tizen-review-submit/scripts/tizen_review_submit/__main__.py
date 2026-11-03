"""Review publication entry point."""

import argparse
import sys

from tizen_review_submit.review_submit import main as review_main


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "review-submit":
        return review_main(argv[1:], stdout=sys.stdout)
    parser = argparse.ArgumentParser(prog="tizen_review_submit")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("review-submit", add_help=False)
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
