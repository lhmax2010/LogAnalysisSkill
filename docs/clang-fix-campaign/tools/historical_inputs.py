"""Read pinned historical bytes by repository path and SHA-256, never by HEAD."""

from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath


class HistoricalInputError(ValueError):
    """A pinned historical input cannot be established from complete history."""


@dataclass(frozen=True)
class HistoricalInput:
    path: str
    sha256: str
    commit: str
    blob: str
    content: bytes


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)
    if result.returncode:
        raise HistoricalInputError("HISTORY_GIT: " + result.stderr.decode())
    return result.stdout


@lru_cache(maxsize=256)
def locate(root: Path, path: str, sha256: str) -> HistoricalInput:
    relative = PurePosixPath(path)
    if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != path:
        raise HistoricalInputError(f"HISTORY_PATH: {path}")
    if re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        raise HistoricalInputError(f"HISTORY_SHA256: {sha256}")
    if _git(root, "rev-parse", "--is-shallow-repository").strip() != b"false":
        raise HistoricalInputError("HISTORY_INCOMPLETE: fetch full Git history first")
    commits = _git(
        root, "log", "--all", "--full-history", "--format=%H", "--", path
    ).decode().splitlines()
    seen: set[str] = set()
    for commit in commits:
        entries = _git(root, "ls-tree", "-z", commit, "--", path).split(b"\0")
        for entry in filter(None, entries):
            metadata, filename = entry.split(b"\t", 1)
            _, kind, oid = metadata.decode().split()
            if filename.decode() != path or kind != "blob" or oid in seen:
                continue
            seen.add(oid)
            content = _git(root, "cat-file", "blob", oid)
            if hashlib.sha256(content).hexdigest() == sha256:
                return HistoricalInput(path, sha256, commit, oid, content)
    raise HistoricalInputError(f"HISTORY_NOT_FOUND: path={path} sha256={sha256}")


def read_pinned(root: Path, path: str, sha256: str) -> bytes:
    return locate(root.resolve(), path, sha256).content
