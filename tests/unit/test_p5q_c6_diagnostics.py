"""Fixed diagnostic propagation and a non-mutating real-driver local probe."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from ci_triage.qb_browser import FAILURE_CATEGORIES
from test_p5q_c5a_integration import line
from test_qb_browser_node import ROOT, browser_paths, node_command
from test_qb_result_fetch import FetchCampaign
from test_qb_trigger import Campaign

PROBE = ROOT / "docs/clang-fix-campaign/spikes/p5q_c6_driver_probe.py"


@pytest.mark.parametrize("category", sorted(FAILURE_CATEGORIES))
@pytest.mark.parametrize("operation", ["trigger", "fetch"])
def test_cli_failure_trace_preserves_category(tmp_path, monkeypatch, category, operation):
    error = dict(ok=False, error="QB_BROWSER_UNAVAILABLE", failure_category=category)
    if operation == "trigger":
        campaign = Campaign(tmp_path, monkeypatch)
        before = campaign.snapshot()
        code, rows = campaign.run([error])
        assert rows[0]["error_code"] == "QB_BROWSER_UNAVAILABLE"
        assert campaign.snapshot() == before
        root, command = tmp_path / "evidence", "open_form"
    else:
        campaign = FetchCampaign(tmp_path, monkeypatch)
        before = campaign.snapshot()
        code, row, _ = campaign.run(replies=[error])
        assert row["error_code"] == "QB_FETCH_FAILED"
        assert campaign.snapshot() == before
        root, command = tmp_path, "read"
    assert code == 5
    traces = [
        json.loads(line)
        for path in (root / "qb_traces").glob("*.jsonl")
        for line in path.read_text().splitlines()
    ]
    failures = [row for row in traces if row.get("action") == "BROWSER_COMMAND_FAILED"]
    assert len(failures) == 1
    assert failures[0] == dict(
        action="BROWSER_COMMAND_FAILED",
        command=command,
        agent_error_code="QB_BROWSER_UNAVAILABLE",
        failure_category=category,
        agent_exited=False,
        agent_exit_code=None,
    )


def test_probe_source_is_non_mutating():
    source = PROBE.read_text()
    for forbidden in (
        "submit",
        "campaign_state",
        "sqlite",
        "input(",
        "getpass",
        "--host-resolver-rules",
    ):
        assert forbidden not in source
    assert 'browser.command("open_form"' in source
    assert 'browser.command("fill"' in source
    assert 'browser.command("close"' in source


@pytest.mark.integration
@pytest.mark.parametrize("category", [None, "NEW_PAGE", "BROWSER_DISCONNECTED", "PAGE_CLOSED"])
def test_probe_local_real_driver(tmp_path, monkeypatch, category):
    command, env = node_command()
    playwright, chromium = browser_paths()
    # Only use the fixture to write configuration, not to replace the real driver.
    with pytest.MonkeyPatch.context() as patch:
        campaign = Campaign(tmp_path, patch)
    campaign.project["configuration_path"] = (
        "root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER"
    )
    campaign.data["qb"]["browser"].update(
        node=str(ROOT / "tests/fixtures/p5q_node_entry.py"),
        playwright_module=playwright,
        chromium=chromium,
    )
    campaign.save()
    before = campaign.db.path.read_bytes()
    evidence = Path(os.environ.get("P5Q_C6_DIAG_EVIDENCE", str(tmp_path / "evidence"))) / (
        category or "normal"
    )
    evidence.mkdir(parents=True, exist_ok=False)
    config, received = tmp_path / "server.json", evidence / "server-requests.json"
    env.update(
        P5Q_TEST_SERVER=str(config),
        P5Q_TEST_NODE=json.dumps(command),
        P5Q_TEST_AGENT_LOG=str(evidence / "agent.json"),
        P5Q_TEST_C6_FAILURE=category or "",
    )
    server = subprocess.Popen(
        [*command, str(ROOT / "tests/node/p5q_fake_quickbuild.mjs"), str(config), str(received)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        assert line(server) == {"ready": True}
        argv = [
            sys.executable,
            str(PROBE),
            "--config",
            str(campaign.config),
            "--output",
            str(evidence / "probe"),
        ]
        run = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=150)
        (evidence / "command.json").write_text(
            json.dumps(
                dict(
                    argv=argv,
                    exit=run.returncode,
                    stdout=run.stdout,
                    stderr=run.stderr,
                ),
                indent=2,
            )
        )
        result = json.loads((evidence / "probe/result.json").read_text())
        assert campaign.db.path.read_bytes() == before
        if category is None:
            assert run.returncode == 0, result
            assert result["ok"] is True
            assert [r["command"] for r in result["commands"]] == [
                "login",
                "open_form",
                "fill",
                "close",
            ]
            assert all(r["ok"] for r in result["commands"])
            assert result["release_state"] == "not_released"
            assert result["form_action_releases"] == 0
            assert result["commands"][-1]["agent_exit_code"] == 0
            assert "QB_AGENT_STOPPED" not in run.stderr
        else:
            assert run.returncode == 5, result
            assert result["ok"] is False
            failure = next(r for r in result["commands"] if not r["ok"])
            assert failure["command"] == "open_form"
            assert failure["failure_category"] == category, result
            assert f"QB_AGENT_STOPPED category={category}\n" in run.stderr
            assert result["commands"][-1]["agent_exit_code"] == 0
        agent = json.loads((evidence / "agent.json").read_text())
        assert all(
            r["input"]["command"] in {"login", "open_form", "fill", "close"}
            for r in agent["transcript"]
        )
        assert "synthetic-password" not in (evidence / "probe/result.json").read_text()
    finally:
        if server.poll() is None:
            server.stdin.write('{"close":true}\n')
            server.stdin.flush()
            assert line(server) == {"ok": True}
        server.communicate(timeout=30)
        assert server.returncode == 0
        requests = json.loads(received.read_text())
        assert requests["submissions"] == [] and requests["builds"] == 0
