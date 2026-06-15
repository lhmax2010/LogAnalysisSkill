"""Command-line dispatch for `python -m gbs_workflow`."""

from __future__ import annotations

from gbs_workflow.workflow import main

if __name__ == "__main__":
    raise SystemExit(main())
