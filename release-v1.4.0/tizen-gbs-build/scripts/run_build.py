"""Launcher for the local tizen-gbs-build skill."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path


def _load_main() -> Callable[[list[str] | None], int]:
    try:
        from gbs_build_skill.runner import main

        return main
    except ModuleNotFoundError as exc:
        if exc.name != "gbs_build_skill":
            raise

    scripts_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(scripts_dir))
    from gbs_build_skill.runner import main

    return main


if __name__ == "__main__":
    raise SystemExit(_load_main()(None))
