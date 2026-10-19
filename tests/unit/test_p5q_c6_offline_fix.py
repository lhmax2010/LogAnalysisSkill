"""Production-entry lifecycle regressions; no real QuickBuild navigation."""

import json
import os
import select
import subprocess
import time
from pathlib import Path

import pytest
from ci_triage.qb_browser import QbBrowser, QbBrowserError
from test_qb_browser_node import ROOT, browser_paths, node_command


@pytest.mark.integration
def test_local_login_facts():
    command, env = node_command()
    paths = browser_paths()
    result = subprocess.run(
        [*command, str(ROOT / "tests/node/test_qb_login_facts.mjs"), *paths],
        env=env, capture_output=True, text=True, timeout=180,
    )
    print(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.integration
def test_production_entry_close_exits_with_input_held_open(tmp_path):
    command, env = node_command()
    paths = browser_paths()
    argv = [*command, str(ROOT / "tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs"), *paths]
    process = subprocess.Popen(
        argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, env=env,
    )
    record = {"argv": argv, "stdin_held_open": True}
    try:
        process.stdin.write('{"command":"close"}\n')
        process.stdin.flush()
        assert select.select([process.stdout], [], [], 30)[0]
        record["response"] = json.loads(process.stdout.readline())
        assert record["response"] == {"ok": True}
        started = time.monotonic()
        try:
            assert process.wait(timeout=5) == 0
        finally:
            record.update(seconds=round(time.monotonic() - started, 3), exit=process.poll())
        assert not process.stdin.closed
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        process.stdin.close()
        record["stderr"] = process.stderr.read()
        process.stdout.close()
        process.stderr.close()
        output = Path(os.environ.get("P5Q_C6_FIX_EVIDENCE", str(tmp_path)))
        output.mkdir(parents=True, exist_ok=True)
        (output / "production-close.json").write_text(json.dumps(record, indent=2) + "\n")


@pytest.mark.integration
def test_driver_close_does_not_terminate_production_entry(monkeypatch, tmp_path):
    command, _ = node_command()
    playwright, chromium = browser_paths()
    if len(command) != 1:
        pytest.skip("Production argv requires a standalone Node executable")
    browser = QbBrowser({"browser": {
        "node": command[0], "playwright_module": playwright, "chromium": chromium,
    }})
    browser.__enter__()
    process = browser.process
    # A protocol round trip waits for Chromium startup before measuring shutdown.
    with pytest.raises(QbBrowserError, match="QB_BROWSER_UNAVAILABLE"):
        browser.command("invalid")
    wait = process.wait

    def wait_after_eof(*args, **kwargs):
        assert process.stdin.closed
        return wait(*args, **kwargs)

    monkeypatch.setattr(process, "wait", wait_after_eof)
    monkeypatch.setattr(process, "terminate", lambda: pytest.fail("unexpected terminate"))
    started = time.monotonic()
    browser.close()
    seconds = time.monotonic() - started
    assert seconds < 5
    assert process.returncode == 0
    assert process.stdin.closed
    output = Path(os.environ.get("P5Q_C6_FIX_EVIDENCE", str(tmp_path)))
    output.mkdir(parents=True, exist_ok=True)
    (output / "driver-close.json").write_text(
        json.dumps({"seconds": seconds, "exit": process.returncode, "terminate_calls": 0})
    )
