"""Offline knowledge-base entry point."""

import sys

from tizen_campaign_kb.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:], stdout=sys.stdout))
