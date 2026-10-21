from __future__ import annotations

import inspect
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from queue import Empty, Queue

import pytest
from ci_triage import qb_trigger as trigger
from ci_triage.qb_browser import QbBrowser, QbBrowserError, decode_response, driver_failed
from test_qb_discovery import config_reply, run_trigger, trigger_setup
from test_qb_result_fetch import FetchCampaign, P, R

ROOT = Path(__file__).resolve().parents[2]
NODE = shutil.which("node") or "/home/linhao/.local/bin/node"
HOLDS = [
    "newCDPSession",
    "Page.getFrameTree",
    "Page.createIsolatedWorld",
    "Runtime.evaluate",
    "detach",
]


@pytest.mark.parametrize("hold", HOLDS)
@pytest.mark.parametrize("command", ["read", "submit"])
def test_cdp_hang_driver_deadline(monkeypatch, tmp_path, hold, command):
    _hang(monkeypatch, tmp_path, hold, command, shortened=True)


def _hang(monkeypatch, tmp_path, hold, command, *, shortened):
    original = subprocess.Popen

    def start(_argv, **kwargs):
        return original([NODE, str(ROOT / "tests/node/p5q_hung_cdp_agent.mjs"), hold], **kwargs)

    monkeypatch.setattr(subprocess, "Popen", start)
    config = dict(browser=dict(node=NODE, playwright_module="unused", chromium="unused"))
    options = dict(read_timeout=0.4, submit_timeout=0.4) if shortened else {}
    with QbBrowser(config, **options) as browser:
        started = time.monotonic()
        if command == "read":
            with pytest.raises(QbBrowserError, match="QB_FETCH_FAILED"):
                browser.command(command, path="/build/1/variables")
        else:
            response = browser.command(command, fingerprint="a" * 64)
            assert driver_failed(response)
            assert response["landed"] == "unknown"
        elapsed = time.monotonic() - started
        assert (0.3 if shortened else 60) <= elapsed < (5 if shortened else 67)
        assert browser.process.poll() is not None
        assert len(browser.termination_records) == 1
        record = browser.termination_records[0]
        assert set(record) == {"event", "waited_seconds", "exit_code"}
        assert record["event"] == "agent_terminated" and record["exit_code"] == -15
        if not shortened:
            assert record["waited_seconds"] == 60
        trigger._close_browser(browser, tmp_path, "test-unit")
    trace = next((tmp_path / "qb_traces").glob("*.jsonl"))
    assert json.loads(trace.read_text()) == record
    print(json.dumps(dict(hold=hold, command=command, elapsed_seconds=elapsed, **record)))


def test_read_default_60_seconds_real_clock(monkeypatch, tmp_path):
    _hang(monkeypatch, tmp_path, "Runtime.evaluate", "read", shortened=False)


@pytest.mark.parametrize(
    "response",
    [
        None,
        [],
        {"ok": 1},
        {"ok": True, "cookie": "SYNTHETIC"},
        {"ok": False, "released": False, "error": 4},
        {"ok": False, "error": "QB_FORM_CHANGED"},
        {"ok": False, "released": "false", "error": "QB_FORM_CHANGED"},
        {"ok": True, "released": True, "landed": "build", "build_id": "invalid"},
        {"ok": True, "released": False, "landed": "build", "build_id": "1"},
        {"ok": True, "released": True, "landed": "build", "build_id": "1", "html_redacted": ""},
        {"ok": False, "released": False, "error": "QB_LOGIN_TIMEOUT", "login_facts": {}},
        {"ok": False, "released": False, "error": "QB_FORM_CHANGED", "snapshot_state": {}},
        {"ok": False, "released": False, "error": "QB_FORM_CHANGED", "failure_category": "bad"},
    ],
)
def test_driver_unknown_is_internal_and_not_serialized(response):
    result = decode_response(json.dumps(response), submit_sent=True, command="submit")
    assert driver_failed(result)
    assert set(json.loads(json.dumps(result))) == {
        "ok",
        "released",
        "landed",
        "observed",
        "messages",
    }


def test_agent_unknown_has_no_driver_marker():
    result = decode_response(
        json.dumps(
            dict(ok=True, released=True, landed="unknown", observed="/wicket/page", messages=[])
        ),
        submit_sent=True,
        command="submit",
    )
    assert not driver_failed(result)


@pytest.mark.parametrize("elapsed", [149, 150])
def test_submit_default_budget_boundary_with_virtual_wait(tmp_path, monkeypatch, elapsed):
    from ci_triage import qb_browser as driver

    c = FetchCampaign(tmp_path, monkeypatch)
    form = trigger_setup(c)
    observed = []

    class TimedReplies(Queue):
        def get(self, block=True, timeout=None):
            raw = super().get(block=block, timeout=5)
            if timeout == 150:
                observed.append(timeout)
                c.clock.advance(elapsed)
                if elapsed == 150:
                    raise Empty
            return raw

    monkeypatch.setattr(driver, "Queue", TimedReplies)
    monkeypatch.setattr(driver, "time", c.clock.time)
    code, rows = run_trigger(
        c,
        [
            config_reply(c),
            *form,
            dict(ok=True, released=True, landed="unknown", observed="/wicket/page", messages=[]),
            config_reply(c, [P]),
            c.replies()[1],
            c.replies()[0],
        ],
    )
    commands = [item["command"] for item in c.commands()]
    after = commands[commands.index("submit") + 1 :]
    traces = [
        json.loads(line)
        for path in (c.root / "qb_traces").glob("*.jsonl")
        for line in path.read_text().splitlines()
    ]
    terminated = [item for item in traces if item.get("event") == "agent_terminated"]
    assert observed == [150]
    if elapsed == 149:
        assert code == 0 and rows[0]["action"] == "submitted_bound"
        assert after == ["read", "read", "read", "close"]
        assert not terminated
    else:
        assert (code, rows[0]["error_code"]) == (5, "QB_SUBMIT_UNCERTAIN")
        assert not after and c.status() == "QB_REQUESTED"
        assert len(terminated) == 1 and terminated[0]["waited_seconds"] == 150
    print(json.dumps(dict(virtual_elapsed=elapsed, response_limit=150, action=rows[0]["action"])))


def test_close_waits_35_seconds_then_records_one_termination(tmp_path, monkeypatch):
    original = subprocess.Popen
    c = FetchCampaign(tmp_path, monkeypatch)
    fixture = (ROOT / "tests/fixtures/qb_fake_agent.py").read_text()
    old = "            print('{\"ok\":true}', flush=True)\n            return"
    assert fixture.count(old) == 1
    fixture = fixture.replace(
        old,
        old.replace(
            "            return", "            __import__('time').sleep(60)\n            return"
        ),
    )

    def start(argv, **kwargs):
        if any(str(arg).endswith("qb_browser_agent.mjs") for arg in argv):
            argv = [sys.executable, "-c", fixture, str(c.script), str(c.transcript)]
        return original(argv, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", start)
    form = trigger_setup(c)
    started = time.monotonic()
    code, rows = run_trigger(
        c,
        [
            config_reply(c),
            *form,
            dict(ok=True, released=True, landed="build", build_id=P),
            c.replies()[1],
        ],
    )
    elapsed = time.monotonic() - started
    assert code == 0 and rows[0]["action"] == "submitted_bound"
    traces = [
        json.loads(line)
        for path in (c.root / "qb_traces").glob("*.jsonl")
        for line in path.read_text().splitlines()
    ]
    records = [item for item in traces if item.get("event") == "agent_terminated"]
    assert len(records) == 1
    assert records[0]["waited_seconds"] >= 35 and records[0]["exit_code"] == -15
    assert 35 <= elapsed < 45
    print(json.dumps(dict(elapsed_seconds=elapsed, **records[0])))


@pytest.mark.parametrize("hold", HOLDS)
@pytest.mark.parametrize("mode", ["fetch", "lookup", "submit"])
def test_cdp_hangs_through_cli_mapping_and_termination_trace(tmp_path, monkeypatch, hold, mode):
    from ci_triage import qb_result_fetch as fetch

    c = FetchCampaign(tmp_path, monkeypatch)
    if mode == "fetch":
        c.bind()
        prelude = []
    elif mode == "lookup":
        prelude = [config_reply(c, ["1193467"])]
    else:
        prelude = [config_reply(c), *trigger_setup(c)]
    scenario = tmp_path / "cdp-scenario.json"
    scenario.write_text(json.dumps(dict(replies=prelude, log=str(c.transcript))))
    original = subprocess.Popen

    def start(argv, **kwargs):
        if any(str(arg).endswith("qb_browser_agent.mjs") for arg in argv):
            argv = [NODE, str(ROOT / "tests/node/p5q_hung_cdp_agent.mjs"), hold, str(scenario)]
        return original(argv, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", start)
    monkeypatch.setattr(
        trigger if mode == "submit" else fetch,
        "QbBrowser",
        lambda qb: QbBrowser(qb, read_timeout=0.4, submit_timeout=0.4),
    )
    if mode == "submit":
        import io

        code, rows = trigger.qb_trigger(
            trigger.QbTriggerOptions(
                c.db.path, c.root, c.config, verification_ids="u1-v0,u1-v1,u1-v2"
            ),
            stderr=io.StringIO(),
        )
        assert (code, rows[0]["error_code"]) == (5, "QB_SUBMIT_UNCERTAIN")
        assert [x["command"] for x in c.commands()] == [
            "login",
            "read",
            "open_form",
            "fill",
            "submit",
        ]
        assert c.status() == "QB_REQUESTED" and len(c.events("SUBMITTED")) == 1
    else:
        code, output, err = c.run(["--request-id", R])
        assert (code, output["error_code"], err) == (5, "QB_FETCH_FAILED", "")
        if mode == "lookup":
            assert "读取失败" in output["message"] and not c.events("BUILD_BOUND")
    traces = [
        json.loads(line)
        for file in (c.root / "qb_traces").glob("*.jsonl")
        for line in file.read_text().splitlines()
    ]
    assert sum(t.get("event") == "agent_terminated" for t in traces) == 1
    assert not c.events("RESULT")


@pytest.mark.parametrize("failure", ["missing", "pipe", "exited"])
def test_real_driver_process_or_pipe_failure_unknown(failure):
    from types import SimpleNamespace

    class BrokenPipe:
        def write(self, _):
            raise BrokenPipeError()

    browser = QbBrowser({})
    if failure != "missing":
        browser.process = SimpleNamespace(
            poll=lambda: 1 if failure == "exited" else None, stdin=BrokenPipe(), stdout=object()
        )
    response = browser.command("submit", fingerprint="a" * 64)
    assert driver_failed(response) and browser.unavailable


def test_budget_static_contract_and_mutations():
    source = (ROOT / "tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs").read_text()
    defaults = inspect.signature(QbBrowser).parameters

    def check(
        text, read=defaults["read_timeout"].default, submit=defaults["submit_timeout"].default
    ):
        assert "this.page.goto(expected, { timeout: 30000 })" in text
        assert 30000 / 1000 < read == 60
        body = text.split("async submit(expectedFingerprint)")[1].split(
            "export async function startupSelfTest"
        )[0]
        assert "timeout: 60000" in body
        assert "Date.now() + 10000" in body
        assert body.count("timeout: 60000") == 2
        assert (60000 + 10000 + 60000) / 1000 < submit == 150

    check(source)
    for name, text, read, submit in [
        ("navigation-missing", source.replace("expected, { timeout: 30000 }", "expected"), 60, 150),
        ("navigation-60000", source.replace("timeout: 30000", "timeout: 60000"), 60, 150),
        ("driver-read-short", source, 30, 150),
        ("submit-click-long", source.replace("timeout: 60000", "timeout: 150000", 1), 60, 150),
        (
            "submit-release-long",
            source.replace("Date.now() + 10000", "Date.now() + 150000"),
            60,
            150,
        ),
        ("driver-submit-short", source, 60, 130),
    ]:
        with pytest.raises(AssertionError):
            check(text, read, submit)
        print(name + ": RED")
