"""Reserved command entry point for a later campaign skeleton batch."""

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(prog="tizen_campaign_intake")
    parser.add_subparsers(dest="command", required=True)
    parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
