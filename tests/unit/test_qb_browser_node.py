"""Offline Node tests. Runtime absence is explicit, never reported as a pass."""

from __future__ import annotations

import json
import os
import select
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def node_command() -> tuple[list[str], dict[str, str]]:
    env = os.environ.copy()
    for key in ("DEBUG", "PWDEBUG", "NODE_OPTIONS", "QB_COOKIE", "QB_PASSWORD"):
        env.pop(key, None)
    node = shutil.which("node")
    if node:
        return [node], env
    embedded = Path("/snap/code/current/usr/share/code/code")
    if embedded.exists():
        env["ELECTRON_RUN_AS_NODE"] = "1"
        return [str(embedded)], env
    pytest.skip("Node unavailable: run and archive C2a Node self-tests on the developer machine")


def browser_paths() -> tuple[str, str]:
    playwright = os.environ.get(
        "P5Q_TEST_PLAYWRIGHT",
        str(Path.home() / ".bun/install/cache/playwright-core/1.58.2@@@1/index.mjs"),
    )
    chromium = os.environ.get(
        "P5Q_TEST_CHROMIUM",
        str(Path.home() / ".cache/ms-playwright/chromium-1208/chrome-linux64/chrome"),
    )
    if (
        not Path(playwright).is_file()
        or not Path(chromium).is_file()
        or not os.environ.get("DISPLAY")
    ):
        pytest.skip("Local Playwright/Chromium/display unavailable; local C2a evidence required")
    return playwright, chromium


def test_node_agent_unit_matrix() -> None:
    command, env = node_command()
    result = subprocess.run(
        [*command, "--test", str(ROOT / "tests/node/test_qb_browser_agent.mjs")],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    print(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.integration
def test_node_browser_redaction_and_response_interception() -> None:
    command, env = node_command()
    paths = browser_paths()
    result = subprocess.run(
        [*command, str(ROOT / "tests/node/test_qb_browser_runtime.mjs"), *paths],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    print(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.integration
def test_node_h_diagnostic_normal_and_control() -> None:
    command, env = node_command()
    paths = browser_paths()
    if not shutil.which("openssl"):
        pytest.skip("openssl unavailable for synthetic local h-probe TLS certificate")
    result = subprocess.run(
        [*command, str(ROOT / "tests/node/p5q_h_interception_probe.mjs"), *paths],
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    rows = [json.loads(line) for line in result.stdout.splitlines()]
    summary = next(row for row in rows if "summary" in row)
    assert summary["passed"] == 3 and summary["failed"] == 0
    print(json.dumps(summary))


@pytest.mark.integration
@pytest.mark.parametrize("mode", ["normal", "exception", "signal"])
def test_node_profile_cleanup(mode: str) -> None:
    command, env = node_command()
    paths = browser_paths()
    process = subprocess.Popen(
        [*command, str(ROOT / "tests/node/qb_browser_lifecycle.mjs"), mode, *paths],
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdout is not None
        assert select.select([process.stdout], [], [], 30)[0], "runtime did not report readiness"
        ready = json.loads(process.stdout.readline())
        profile = Path(ready["profile"])
        assert ready["ready"] and profile.parent == Path("/dev/shm")
        if mode == "signal":
            process.terminate()
        stdout, stderr = process.communicate(timeout=30)
        assert process.returncode == (1 if mode == "exception" else 0), stdout + stderr
        if mode == "exception":
            assert '"error":"QB_BROWSER_UNAVAILABLE"' in stdout
            assert "synthetic exception" not in stdout + stderr
        assert not profile.exists()
        print(json.dumps({"mode": mode, "removed": not profile.exists()}))
    finally:
        if process.poll() is None:
            process.terminate()
            process.communicate(timeout=30)
