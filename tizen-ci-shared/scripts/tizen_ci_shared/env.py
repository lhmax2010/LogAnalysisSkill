"""Shared environment discovery helpers."""

from __future__ import annotations

from pathlib import Path


def discover_sibling_pythonpath(*, launcher_path: Path | None = None) -> tuple[Path, ...]:
    """Return sibling analyzer/patch-suggest scripts paths for direct-folder usage."""

    if launcher_path is None:
        return ()
    triage_root = launcher_path.resolve().parents[1]
    root = triage_root.parent
    candidates = (
        root / "tizen-gbs-log-analysis" / "scripts",
        root / "tizen-gbs-patch-suggest" / "scripts",
    )
    return tuple(path for path in candidates if path.is_dir())
