"""Launcher for the local tizen-ci-triage vertical-slice tool."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path


def _load_main() -> Callable[[list[str] | None], int]:
    try:
        from ci_triage.cli import main

        return main
    except ModuleNotFoundError as exc:
        if exc.name != "ci_triage":
            raise

    scripts_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(scripts_dir))
    from ci_triage.cli import main

    return main


if __name__ == "__main__":
    raise SystemExit(_load_main()(sys.argv[1:]))
