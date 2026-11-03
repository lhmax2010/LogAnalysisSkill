"""SKEL-R-04/06 narrow exception, including real canceled local requests."""

import os
import subprocess
from pathlib import Path

import pytest
from test_qb_browser_node import ROOT, browser_paths, node_command


def test_deny_target_gone_unit_matrix():
    command, env = node_command()
    result = subprocess.run(
        [*command, "--test", str(ROOT / "tests/node/test_qb_deny_target_gone.mjs")],
        env=env, capture_output=True, text=True, timeout=30,
    )
    print(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.integration
def test_deny_target_gone_server_receives_zero(tmp_path: Path):
    command, env = node_command()
    output = Path(os.environ.get("P5Q_DENY_GONE_EVIDENCE", str(tmp_path)))
    output.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [*command, str(ROOT / "tests/node/p5q_deny_target_gone_browser.mjs"),
         *browser_paths(), str(output / "browser.json")],
        env=env, capture_output=True, text=True, timeout=60,
    )
    print(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr
