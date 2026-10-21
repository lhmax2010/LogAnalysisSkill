"""Real Python CLIs, real guarded browser, synthetic local HTTPS and bare git."""

import json
import os
import select
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest
from test_qb_browser_node import ROOT, browser_paths, node_command
from test_qb_trigger import Campaign


def line(process):
    assert select.select([process.stdout], [], [], 30)[0], "local server did not reply"
    return json.loads(process.stdout.readline())


@pytest.mark.integration
@pytest.mark.parametrize(
    "mode",
    ["build", "error-created", "error-no-build", "no-navigation", "delayed-build", "late-build"],
)
def test_real_cli_browser_submit_bind_pending_pass(tmp_path, mode):
    command, env = node_command()
    playwright, chromium = browser_paths()
    # Reuse state fixture only, not its fake-agent monkeypatch or CLI shortcuts.
    with pytest.MonkeyPatch.context() as mp:
        campaign = Campaign(tmp_path, mp)
    campaign.project["configuration_path"] = (
        "root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER"
    )
    campaign.data["qb"]["browser"].update(
        node=str(ROOT / "tests/fixtures/p5q_node_entry.py"),
        playwright_module=playwright,
        chromium=chromium,
    )
    campaign.save()
    evidence = Path(os.environ.get("P5Q_C5A_EVIDENCE", str(tmp_path / "evidence"))) / mode
    evidence.mkdir(parents=True, exist_ok=True)
    config, received = tmp_path / "local-server.json", evidence / "server-requests.json"
    env.update(P5Q_TEST_SERVER=str(config), P5Q_TEST_NODE=json.dumps(command))
    server = subprocess.Popen(
        [*command, str(ROOT / "tests/node/p5q_fake_quickbuild.mjs"), str(config), str(received)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    commands = []

    def server_command(value):
        server.stdin.write(json.dumps(value) + "\n")
        server.stdin.flush()
        assert line(server) == {"ok": True}

    def cli(name, *args, expected_exit=0):
        env["P5Q_TEST_AGENT_LOG"] = str(evidence / f"agent-{len(commands)}.json")
        argv = [
            sys.executable,
            str(ROOT / "tests/fixtures/p5q_cli_clock.py"),
            name,
            *args,
            "--state-db",
            str(tmp_path / "state.db"),
            "--state-root",
            str(tmp_path / "state"),
            "--config",
            str(campaign.config),
        ]
        run = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=150)
        ended = time.time()
        agent_log = Path(env["P5Q_TEST_AGENT_LOG"])
        close_seconds = None
        if agent_log.exists():
            lifecycle = json.loads(agent_log.read_text())
            close_started = lifecycle["close_started_unix_ms"]
            if close_started is not None:
                close_seconds = ended - close_started / 1000
        commands.append(
            {
                "argv": argv,
                "exit": run.returncode,
                "stdout": run.stdout,
                "stderr": run.stderr,
                "close_to_cli_exit_seconds": close_seconds,
            }
        )
        (evidence / "commands.json").write_text(
            json.dumps(commands, ensure_ascii=False, indent=2) + "\n"
        )
        server_command({})
        if close_seconds is not None:
            assert 0 <= close_seconds < 5
        elif name == "qb-result-fetch" or not commands[:-1]:
            pytest.fail("missing close timing for browser invocation")
        assert run.returncode == expected_exit, run.stdout + run.stderr
        return json.loads(run.stdout)[0]

    try:
        assert line(server) == {"ready": True}
        server_command({"mode": mode})
        triggered = cli(
            "qb-trigger",
            "--verification-ids",
            "u1-v0,u1-v1,u1-v2",
            expected_exit=5 if mode in {"error-no-build", "late-build"} else 0,
        )
        transcript = json.loads((evidence / "agent-0.json").read_text())["transcript"]
        protocol = [row["input"] for row in transcript]
        submit_index = next(i for i, value in enumerate(protocol) if value["command"] == "submit")
        baseline_reads = [v for v in protocol[:submit_index] if v["command"] == "read"]
        lookup_reads = [
            v
            for v in protocol[submit_index + 1 :]
            if v["command"] == "read" and v.get("path") == "/overview/1917"
        ]
        assert baseline_reads == [{"command": "read", "path": "/overview/1917"}]
        assert len(lookup_reads) == (
            0
            if mode == "build"
            else 10
            if mode in {"error-no-build", "late-build"}
            else 2
            if mode == "delayed-build"
            else 1
        )
        requests = json.loads(received.read_text())["received"]
        assert sum(
            r["method"] == "GET" and r["path"] == "/overview/1917" for r in requests
        ) == 2 + len(lookup_reads)
        if mode == "error-no-build":
            assert triggered["action"] == "submit_uncertain", triggered
            again = cli("qb-trigger", "--verification-ids", "u1-v0,u1-v1,u1-v2")
            assert again["request_id"] == triggered["request_id"]
            payload = json.loads(received.read_text())
            assert len(payload["submissions"]) == 1
            assert payload["builds"] == (0 if mode == "error-no-build" else 1)
            assert again["action"] == "already_requested"
            assert not campaign.sql(
                "SELECT * FROM campaign_qb_events WHERE event_type='BUILD_BOUND'"
            )
            (evidence / "state-facts.json").write_text(json.dumps(campaign.snapshot(), indent=2))
            return
        assert triggered["action"] == (
            "submit_uncertain" if mode == "late-build" else "submitted_bound"
        ), triggered
        if mode == "late-build":
            assert not campaign.sql(
                "SELECT * FROM campaign_qb_events WHERE event_type='BUILD_BOUND'"
            )
            server_command({"publish": True})
        request = triggered["request_id"]
        pending = cli("qb-result-fetch", "--request-id", request)
        assert pending["status"] == "RUNNING", pending
        fetch_commands = json.loads((evidence / "agent-1.json").read_text())["transcript"]
        fetch_reads = [
            r["input"]["path"] for r in fetch_commands if r["input"]["command"] == "read"
        ]
        assert fetch_reads == (
            ["/overview/1917", "/build/1193467/variables", "/build/1193467/overview"]
            if mode == "late-build"
            else ["/build/1193467/overview", "/build/1193467/variables"]
        ) + ["/build/1193469/overview", "/build/1193469/variables"]
        assert (
            campaign.sql("SELECT status FROM campaign_status_log ORDER BY log_id DESC LIMIT 1")[0][
                "status"
            ]
            == "SANDBOX_QB_PENDING"
        )
        server_command({"status": "Successful"})
        passed = cli("qb-result-fetch", "--request-id", request)
        assert passed["status"] == "PASS", passed
        payload = json.loads(received.read_text())
        assert payload["errors"] == []
        assert len(payload["submissions"]) == 1
        body = payload["submissions"][0]
        assert body["form:field:7:input"] == "u1@" + campaign.units["u1"]["sha"]
        assert body["form:field:11:input"] == "clang-fix-campaign request=" + request
        assert body["form:field:6:palette:recorder"] == b"standard-armv7l:aarch64:x86_64".hex()
        assert not any(
            any(word in row["path"] for word in ("ajaxRefresh", "/rest/", "promote", "/log"))
            for row in payload["received"]
        )
        assert len(campaign.sql("SELECT * FROM campaign_qb_events WHERE event_type='RESULT'")) == 1
        result = json.loads((tmp_path / "state" / passed["qb_result_path"]).read_text())
        assert result["status"] == "PASS"
        (evidence / "result.json").write_text(json.dumps(result, indent=2))
        (evidence / "state-facts.json").write_text(json.dumps(campaign.snapshot(), indent=2))
        shutil.copytree(tmp_path / "state" / "qb_evidence", evidence / "qb_evidence")
        for file in (evidence / "qb_evidence").rglob("*.html"):
            assert "LocalTester" not in file.read_text()
        assert (
            campaign.sql("SELECT status FROM campaign_status_log ORDER BY log_id DESC LIMIT 1")[0][
                "status"
            ]
            == "SANDBOX_QB_PASS"
        )
    finally:
        if server.poll() is None:
            server_command({"close": True})
        server.communicate(timeout=30)
        assert server.returncode == 0
