"""SKEL-R-02 diagnostic-only changes retain failure and close behavior."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from unittest.mock import Mock

import pytest
from test_qb_browser_node import ROOT, node_command
from tizen_qb_verify.qb_browser import QbBrowser


def test_node_read_failure_diagnostics():
    command, env = node_command()
    result = subprocess.run(
        [*command, "--test", str(ROOT / "tests/node/test_qb_read_failure_diagnostics.mjs")],
        env=env, capture_output=True, text=True, timeout=30,
    )
    print(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr


def browser_with(process):
    browser = QbBrowser.__new__(QbBrowser)
    browser.process = process
    browser.termination_records = []
    return browser


@pytest.mark.parametrize("reply", ["", '{"ok":true}\n'])
def test_close_real_process_with_or_without_reply(reply):
    process = subprocess.Popen(
        [sys.executable, "-c", f"import sys; sys.stdin.readline(); sys.stdout.write({reply!r})"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    )
    browser = browser_with(process)
    browser.close()
    assert browser.process is None
    assert process.returncode == 0
    assert set(browser.close_observation) == {"elapsed_ms", "returncode"}
    assert browser.close_observation["returncode"] == 0
    assert 0 <= browser.close_observation["elapsed_ms"] < 5000
    assert browser.termination_records == []


@pytest.mark.parametrize("mode", ["normal", "timeout", "write_error", "cleanup_error"])
def test_close_observation_preserves_existing_paths(mode):
    process = Mock()
    process.stdin = io.StringIO()
    process.stdout = io.StringIO()
    process.poll.side_effect = lambda: process.returncode
    process.returncode = None
    if mode == "timeout":
        process.wait.side_effect = [subprocess.TimeoutExpired("agent", 35), None]
        process.terminate.side_effect = lambda: setattr(process, "returncode", -15)
    else:
        process.wait.side_effect = lambda **_: setattr(process, "returncode", 0)
    if mode == "write_error":
        process.stdin = Mock(closed=False)
        process.stdin.write.side_effect = OSError("private-error cookie=private-cookie")
        process.terminate.side_effect = lambda: setattr(process, "returncode", -15)
    if mode == "cleanup_error":
        process.stdout = Mock()
        process.stdout.close.side_effect = ValueError("private-error")
    browser = browser_with(process)
    if mode == "cleanup_error":
        with pytest.raises(ValueError, match="private-error"):
            browser.close()
    else:
        browser.close()
        assert browser.process is None
    assert browser.close_observation["elapsed_ms"] >= 0
    assert isinstance(browser.close_observation["returncode"], int)
    assert "private" not in json.dumps(browser.close_observation)
    assert process.terminate.call_count == (mode in {"timeout", "write_error"})


@pytest.mark.parametrize("failure", ["poll", "sink"])
def test_close_diagnostic_failure_does_not_escape(failure):
    class Browser(QbBrowser):
        def __setattr__(self, name, value):
            if name == "close_observation" and failure == "sink":
                raise RuntimeError("private-error")
            super().__setattr__(name, value)

    process = Mock(stdin=io.StringIO(), stdout=io.StringIO())
    process.poll.side_effect = [0, RuntimeError("private-error")] if failure == "poll" else [0, 0]
    browser = Browser.__new__(Browser)
    browser.process = process
    browser.close()
    assert browser.process is None


def test_close_without_process_is_unchanged():
    browser = browser_with(None)
    browser.close()
    assert not hasattr(browser, "close_observation")
