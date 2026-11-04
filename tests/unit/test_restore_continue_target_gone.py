"""RESTORE-10: only real, confirmed Chromium cancellation permits the new exception."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from test_qb_browser_node import ROOT, browser_paths, node_command


@pytest.mark.integration
def test_cancelled_static_continue_and_missing_main_document(tmp_path: Path) -> None:
    command, env = node_command()
    playwright, chromium = browser_paths()
    output = tmp_path / "result.json"
    result = subprocess.run(
        [*command, str(ROOT / "tests/node/p5q_continue_target_gone_browser.mjs"),
         playwright, chromium, str(output), "after"],
        env=env, capture_output=True, text=True, timeout=180,
    )
    print(result.stdout)
    print(result.stderr)
    facts = json.loads(output.read_text())
    print(json.dumps(facts, indent=2))
    assert result.returncode == 0, result.stdout + result.stderr
    assert facts["ok"]
    assert len(facts["samples"]) == 3
    for row in facts["samples"]:
        assert row["ok"] and row["profile_removed"] and row["next_read_ok"]
        assert all(op["cancelled_before_call"] for op in row["operations"])
        assert all(op["category"] == "REQUEST_ID_INVALID" for op in row["operations"])
    assert facts["main_document"]["read"]["has_body"] is False
