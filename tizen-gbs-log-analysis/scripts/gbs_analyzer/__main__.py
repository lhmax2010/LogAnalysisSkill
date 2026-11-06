"""Command-line dispatch for `python -m gbs_analyzer`."""

from __future__ import annotations

from gbs_analyzer.analyze import main

if __name__ == "__main__":
    raise SystemExit(main())
