"""Launcher for the local tizen-gbs-patch-suggest skill."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path


def _load_main() -> Callable[..., int]:
    try:
        from gbs_patch_suggest.cli import main

        return main
    except ModuleNotFoundError as exc:
        if exc.name != "gbs_patch_suggest":
            raise

    scripts_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(scripts_dir))
    from gbs_patch_suggest.cli import main

    return main


if __name__ == "__main__":
    from gbs_patch_suggest.analyzer_runner import discover_analyzer_pythonpath

    needs_analyzer = any(
        arg == "--buildlog" or arg.startswith("--buildlog=") for arg in sys.argv[1:]
    )
    try:
        analyzer_pythonpath = (
            discover_analyzer_pythonpath(launcher_path=Path(__file__)) if needs_analyzer else ()
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    raise SystemExit(
        _load_main()(
            None,
            analyzer_extra_pythonpath=analyzer_pythonpath,
        )
    )
