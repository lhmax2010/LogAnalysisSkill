"""Baseline reproduction command entry point."""

import argparse
import sys

from tizen_baseline_reproduce.baseline import main as baseline_main


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "baseline-reproduce":
        return baseline_main(argv[1:], stdout=sys.stdout)
    parser = argparse.ArgumentParser(prog="tizen_baseline_reproduce")
    parser.add_subparsers(dest="command", required=True).add_parser(
        "baseline-reproduce", add_help=False
    )
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
