"""Command-line dispatch for ``python -m ci_triage``."""

from __future__ import annotations

from ci_triage.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
