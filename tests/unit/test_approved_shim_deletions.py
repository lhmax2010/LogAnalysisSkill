"""PR-02 permits only individually approved, actually absent legacy modules."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("fixture", "reason"),
    [
        ("unapproved-deleted-shim", "not an approved deletion"),
        ("legacy-shim-residual-implementation", "non-re-export FunctionDef"),
    ],
)
def test_approved_deletion_guard_rejects_invalid_legacy_state(fixture: str, reason: str) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "docs/clang-fix-campaign/tools/symbol_audit.py"),
            "--negative-fixture",
            fixture,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert reason in result.stdout
