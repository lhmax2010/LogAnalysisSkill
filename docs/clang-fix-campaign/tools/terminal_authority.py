"""Immutable rule inputs with byte-exact containment in the current authority."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

DOC = "docs/clang-fix-campaign/p49-terminal-batch-design-v1.31-FROZEN.md"
E1_COMMIT = "27fb46077d2c3c91197bcedb534995f6987c9ef5"
E10_COMMIT = "8e72c345afc18efd118dd5880cd8ebd6b96e7bb1"
E11_COMMIT = "ab4779ef1cd4ab1613e7e894d1512264d5a6268c"


def assert_contained(old: bytes, current: bytes) -> None:
    # Errata are inserted at the top and appended at EOF. Compare complete
    # lines in order, without whitespace/Unicode normalization or masking.
    remaining = iter(current.splitlines(keepends=True))
    for line in old.splitlines(keepends=True):
        if not any(candidate == line for candidate in remaining):
            raise ValueError("CURRENT_AUTHORITY_MISSING_SOURCE: " + repr(line))


def read_authority(root: Path, commit: str, expected_sha256: str, path: str = DOC) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=root, capture_output=True, check=False
    )
    if result.returncode:
        raise ValueError("AUTHORITY_GIT_BLOB: " + result.stderr.decode())
    if hashlib.sha256(result.stdout).hexdigest() != expected_sha256:
        raise ValueError("AUTHORITY_BLOB_HASH")
    assert_contained(result.stdout, (root / path).read_bytes())
    return result.stdout
