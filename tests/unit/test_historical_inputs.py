"""Historical checks use pinned bytes, not mutable documents or chosen commits."""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "docs/clang-fix-campaign/tools"
saved_path = sys.path[:]
sys.path.insert(0, str(TOOLS))
try:
    HISTORY = importlib.import_module("historical_inputs")
    DIFF = importlib.import_module("terminal_expected_diff")
finally:
    sys.path[:] = saved_path


def test_history_reads_old_content_despite_worktree_change(tmp_path: Path) -> None:
    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init")
    git("config", "user.name", "History Test")
    git("config", "user.email", "history@example.invalid")
    path = tmp_path / "design.md"
    path.write_bytes(b"old bytes\n")
    git("add", "design.md")
    git("commit", "-m", "old")
    path.write_bytes(b"new bytes\n")
    git("commit", "-am", "new")
    old_sha = hashlib.sha256(b"old bytes\n").hexdigest()
    found = HISTORY.locate(tmp_path, "design.md", old_sha)
    assert found.content == b"old bytes\n"
    assert subprocess.check_output(
        ["git", "show", f"{found.commit}:design.md"], cwd=tmp_path
    ) == found.content


def test_skill4_restored_corpus_is_found_without_commit_exception() -> None:
    path = "docs/clang-fix-campaign/history/skill4/p49-skill4-build-verify-design-v1.12-FROZEN.md"
    sha = "c0f730ab378b97b1f0a5483e508c9003d864248c7225db2405c71e955f618408"
    assert hashlib.sha256(HISTORY.read_pinned(ROOT, path, sha)).hexdigest() == sha


@pytest.mark.parametrize("mutation", ["sha256", "path"])
@pytest.mark.parametrize("tool", ["ledger", "branch"])
def test_tool_rejects_unlocatable_pin(tmp_path: Path, mutation: str, tool: str) -> None:
    filename = (
        "design_drift_ledger.skill5.json" if tool == "ledger" else "branch_inventory.skill6.json"
    )
    data = json.loads((TOOLS / filename).read_text())
    if mutation == "sha256":
        sha = data["target_sha256"]
        data["target_sha256"] = ("0" if sha[0] != "0" else "1") + sha[1:]
    else:
        data["target_design"] = "docs/does-not-exist-in-history.md"
    data_path = tmp_path / filename
    data_path.write_text(json.dumps(data))
    script = "design_drift_ledger.py" if tool == "ledger" else "branch_inventory.py"
    argv = [sys.executable, str(TOOLS / script), "check", "--data", str(data_path)]
    if tool == "branch":
        argv += ["--design", data["target_design"]]
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "HISTORY_NOT_FOUND" in result.stdout + result.stderr


@pytest.mark.parametrize("mutation", ["sha256", "path"])
def test_expected_diff_historical_pin_control(
    monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    if mutation == "sha256":
        sha = DIFF.TABLE_HASH
        monkeypatch.setattr(DIFF, "TABLE_HASH", ("0" if sha[0] != "0" else "1") + sha[1:])
    else:
        monkeypatch.setattr(DIFF, "TABLE", "docs/does-not-exist-in-history.md")
    with pytest.raises(HISTORY.HistoricalInputError, match="HISTORY_NOT_FOUND"):
        DIFF.Sources(ROOT).read(DIFF.TABLE, DIFF.TABLE_HASH)
