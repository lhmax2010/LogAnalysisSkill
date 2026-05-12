"""Source-to-object suffix helpers for make cascade folding."""

from __future__ import annotations

from pathlib import Path

SOURCE_EXTENSIONS = {".c", ".cc", ".cpp", ".cxx", ".S", ".cu"}


def is_supported_source(path: str) -> bool:
    return Path(path).suffix in SOURCE_EXTENSIONS


def strip_ext(filename: str) -> str:
    path = Path(filename)
    return path.name[: -len(path.suffix)] if path.suffix else path.name


def candidates_for_source(src_path: str) -> set[str]:
    """Return object suffix candidates for a compiler diagnostic source path."""

    base = Path(src_path).name
    stem = strip_ext(base)
    return {f"{stem}.o", f"{base}.o"}


def build_suffix_index(source_to_event: dict[str, str]) -> dict[str, set[str]]:
    """Create a suffix -> event id map from source path -> event id."""

    index: dict[str, set[str]] = {}
    for src_path, event_id in source_to_event.items():
        if not is_supported_source(src_path):
            continue
        for suffix in candidates_for_source(src_path):
            index.setdefault(suffix, set()).add(event_id)
    return index


def match_make_target(target_in_log: str, suffix_index: dict[str, set[str]]) -> str | None:
    """Return a unique parent event id when the make target ends with one suffix."""

    matches: set[str] = set()
    for suffix, event_ids in suffix_index.items():
        if target_in_log.endswith(suffix):
            matches.update(event_ids)
    return next(iter(matches)) if len(matches) == 1 else None
