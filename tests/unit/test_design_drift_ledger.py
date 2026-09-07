from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_ledger_module() -> ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "docs/clang-fix-campaign/tools/design_drift_ledger.py"
    spec = importlib.util.spec_from_file_location("design_drift_ledger_for_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


LEDGER = _load_ledger_module()


def test_version_key_accepts_optional_v_and_patch() -> None:
    assert LEDGER._version_key("1.3") == (1, 3, 0)
    assert LEDGER._version_key("v1.3.1") == (1, 3, 1)


@pytest.mark.parametrize(
    "versions",
    [
        ("1.3", "1.3.2"),
        ("1.3.1", "1.4.1"),
        ("1.3", "1.4.1"),
        ("1.3.1", "1.3.3"),
        ("1.3.1", "1.5"),
    ],
)
def test_version_sequence_rejects_minor_and_patch_skips(
    versions: tuple[str, str],
) -> None:
    with pytest.raises(LEDGER.LedgerError, match="version sequence is not continuous"):
        LEDGER._validate_version_sequence(versions)


def test_version_sequence_accepts_patch_then_next_minor() -> None:
    LEDGER._validate_version_sequence(("1.3", "1.3.1", "1.4"))
