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


def test_node_c2c_source_guard_mutations() -> None:
    command, env = node_command()
    result = subprocess.run(
        [*command, "--test", str(ROOT / "tests/node/test_qb_agent_source_guards.mjs")],
        env=env, capture_output=True, text=True, timeout=60,
    )
    print(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.integration
@pytest.mark.parametrize("script", ["test_qb_browser_trusted.mjs", "test_qb_browser_fields.mjs"])
def test_node_c2c_trusted_reads_and_fields(script: str) -> None:
    command, env = node_command()
    paths = browser_paths()
    if not shutil.which("openssl"):
        pytest.skip("openssl unavailable for synthetic local C2c TLS certificate")
    result = subprocess.run(
        [*command, str(ROOT / "tests/node" / script), *paths],
        env=env, capture_output=True, text=True, timeout=240,
    )
    print(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.integration
def test_node_c5a_evidence_tools() -> None:
    command, env = node_command()
    paths = browser_paths()
    if not shutil.which("openssl"):
        pytest.skip("openssl unavailable for synthetic local C5a TLS certificate")
    result = subprocess.run(
        [*command, str(ROOT / "tests/node/test_p5q_c5_tools.mjs"), *paths],
        env=env,
        capture_output=True,
        text=True,
        timeout=150,
    )
    print(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr


def test_c5a_tools_are_readonly_and_not_production_test_overrides() -> None:
    spikes = ROOT / "docs/clang-fix-campaign/spikes"
    for name in ("p5q_fill_rehearsal.mjs", "p5q_compare_raw_active.mjs", "p5q_c5_tools.mjs"):
        source = (spikes / name).read_text()
        assert "command: 'submit'" not in source
        assert "submitUrl" not in source
        assert "name: 'Ok'" not in source
        assert "--host-resolver-rules" not in source
        assert "--ignore-certificate-errors-spki-list" not in source
        assert "installGuards =" not in source and "policy.allow =" not in source
        assert "process.stdin" not in source
        assert "error.message" not in source
        assert "error.stack" not in source


@pytest.mark.integration
def test_node_c5b_failure_evidence() -> None:
    command, env = node_command()
    paths = browser_paths()
    if not shutil.which("openssl"):
        pytest.skip("openssl unavailable for synthetic local C5b TLS certificate")
    result = subprocess.run(
        [*command, str(ROOT / "tests/node/test_p5q_c5b_failure_evidence.mjs"), *paths],
        env=env, capture_output=True, text=True, timeout=180,
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
def test_node_c2b_configuration_source_checks() -> None:
    command, env = node_command()
    result = subprocess.run(
        [*command, str(ROOT / "tests/node/test_p5q_c2b_config_source.mjs"), *browser_paths()],
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
def test_node_c2b_local_https_safety() -> None:
    command, env = node_command()
    paths = browser_paths()
    if not shutil.which("openssl"):
        pytest.skip("openssl unavailable for synthetic local C2b TLS certificate")
    result = subprocess.run(
        [*command, str(ROOT / "tests/node/p5q_c2b_safety.mjs"), *paths],
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    rows = [json.loads(line) for line in result.stdout.splitlines()]
    summary = next(row for row in rows if "summary" in row)
    assert summary["passed"] == 4 and summary["failed"] == 0
    worker = next(row for row in rows if row.get("group") == "worker-websocket")
    assert worker["details"]["branch"] in {"a:targets_closed", "b:browser_fail_closed"}
    assert worker["details"]["attackHTTP"] == worker["details"]["websocketHandshakes"] == 0
    assert {row["type"] for row in worker["observations"]["closeTarget"]} == {
        "worker", "shared_worker"
    }
    print(result.stdout)


def test_c2b_evidence_entry_is_not_a_submit_or_launch_override_path() -> None:
    source = (ROOT / "docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs").read_text()
    assert "command: 'submit'" not in source
    assert "submitUrl" not in source
    assert "name: 'Ok'" not in source
    assert "createRuntime(playwright, chromium)" in source
    assert "launchArgs" not in source
    assert "WORKER_BLOCKED" in source and "NEW_PAGE" in source
    assert "if (runtime.failure) stop(runtime.failure)" in source
    assert "check_written" in source
    for relative in (
        "tizen-ci-triage/scripts/ci_triage/qb_browser.py",
        "tizen-ci-triage/scripts/ci_triage/cli.py",
    ):
        production = (ROOT / relative).read_text()
        assert "--host-resolver-rules" not in production
        assert "--ignore-certificate-errors-spki-list" not in production
        assert "p5q_c2b_evidence" not in production


@pytest.mark.integration
def test_node_login_retry_and_five_attempt_limit() -> None:
    command, env = node_command()
    paths = browser_paths()
    if not shutil.which("openssl"):
        pytest.skip("openssl unavailable for synthetic login-retry TLS certificate")
    result = subprocess.run(
        [*command, str(ROOT / "tests/node/p5q_login_retry.mjs"), *paths],
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    rows = [json.loads(line) for line in result.stdout.splitlines()]
    assert {row["scenario"] for row in rows if "scenario" in row} == {
        "retry-success", "five-failure-limit"
    }
    summary = next(row for row in rows if "summary" in row)
    assert summary["passed"] == summary["expected"] == 2
    print(result.stdout)


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
