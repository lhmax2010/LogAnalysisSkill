"""Only private-display, loopback-HTTPS capture tests; no production launch parameters."""

import subprocess

import pytest
from test_qb_browser_node import ROOT, node_command


@pytest.mark.integration
def test_capture_spaces_session_redaction_and_remaining_three_pages() -> None:
    command, env = node_command()
    script = ROOT / (
        "docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/evidence/restore/"
        "discovery-capture/offline.test.mjs"
    )
    result = subprocess.run([*command, "--test", str(script)], env=env,
                            capture_output=True, text=True, timeout=240)
    assert result.returncode == 0, result.stdout + result.stderr
