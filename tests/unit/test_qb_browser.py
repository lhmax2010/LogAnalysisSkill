from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from ci_triage.qb_browser import QbBrowser, QbBrowserError, decode_response
from ci_triage.qb_redact import EvidenceRedactionError

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "error,field,expected",
    [
        ("QB_FORM_CHANGED", None, "REJECTED_QB_FORM_CHANGED"),
        ("QB_FORM_VALUE_UNAVAILABLE", "SNAPSHOT_NUM", "REJECTED_QB_SNAPSHOT_UNAVAILABLE"),
        ("QB_FORM_VALUE_UNAVAILABLE", "BUILD_TYPE", "REJECTED_QB_FORM_MISMATCH"),
        ("QB_FORM_READBACK_MISMATCH", None, "REJECTED_QB_FORM_MISMATCH"),
        ("QB_LOGIN_TIMEOUT", None, "QB_LOGIN_TIMEOUT"),
        ("QB_LOGIN_ABORTED", None, "QB_LOGIN_ABORTED"),
        ("AGENT_PHASE", None, "QB_BROWSER_UNAVAILABLE"),
        ("UNKNOWN", None, "INTERNAL_ERROR"),
        ("QB_READ_ID_MISMATCH", None, "INTERNAL_ERROR"),
        ("QB_READ_REDIRECTED", None, "INTERNAL_ERROR"),
    ],
)
def test_frozen_error_mapping(error, field, expected):
    with pytest.raises(QbBrowserError) as caught:
        decode_response(
            json.dumps({"ok": False, "error": error, "field": field}), submit_sent=False
        )
    assert caught.value.code == expected


@pytest.mark.parametrize("raw", ["", "not json", '{"ok":false,"error":"AGENT_PHASE"}'])
def test_sent_submit_ambiguous_reply_is_unknown(raw):
    assert decode_response(raw, submit_sent=True) == {
        "ok": True,
        "landed": "unknown",
        "released": True,
        "observed": "<other>",
        "messages": [],
    }


@pytest.mark.parametrize("key", ["cookie", "Cookie", "set-cookie", "Authorization"])
@pytest.mark.parametrize("sent", [False, True])
def test_sensitive_key_is_always_rejected(key, sent):
    with pytest.raises(QbBrowserError) as caught:
        decode_response(
            json.dumps({"ok": True, "nested": [{key: "fixture-secret"}]}), submit_sent=sent
        )
    assert caught.value.code == "QB_BROWSER_UNAVAILABLE"
    assert "fixture-secret" not in str(caught.value)


@pytest.mark.parametrize(
    "html",
    [
        "JSESSIONID_8810=fixture-secret",
        '<input type="hidden" name="token" value="fixture-secret">',
        "<span>Welcome! fixture-user</span>",
    ],
)
def test_html_independent_redaction_check(html):
    with pytest.raises(EvidenceRedactionError):
        decode_response(json.dumps({"ok": True, "html_redacted": html}), submit_sent=False)


def test_redacted_html_and_palette_recorder_preserved():
    html = (
        '<span>Welcome! &lt;USER&gt;</span>'
        '<input type="hidden" name="a:palette:recorder" value="6162">'
    )
    assert (
        decode_response(json.dumps({"ok": True, "html_redacted": html}), submit_sent=False)[
            "html_redacted"
        ]
        == html
    )


@pytest.fixture
def fake(tmp_path, monkeypatch):
    config = {
        "browser": {
            "node": "node",
            "playwright_module": "/fixture/playwright",
            "chromium": "/fixture/chromium",
            "login_timeout_seconds": 600,
        },
        "projects": {
            "tizen": {
                "enabled": True,
                "overview_id": 42,
                "configuration_path": "root/RBS/TRIGGER",
                "project_name": "synthetic",
            }
        },
    }
    script = tmp_path / "responses.json"
    transcript = tmp_path / "commands.jsonl"
    actual = subprocess.Popen
    launches = []

    def launch(args, **kwargs):
        launches.append((args, kwargs))
        assert args == [
            "node",
            str(ROOT / "tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs"),
            "/fixture/playwright",
            "/fixture/chromium",
        ]
        assert not kwargs.get("shell", False)
        return actual(
            [
                sys.executable,
                str(ROOT / "tests/fixtures/qb_fake_agent.py"),
                str(script),
                str(transcript),
            ],
            **kwargs,
        )

    monkeypatch.setattr(subprocess, "Popen", launch)
    monkeypatch.setenv("QB_COOKIE", "fixture-cookie")
    monkeypatch.setenv("QB_PASSWORD", "fixture-password")
    monkeypatch.setenv("DEBUG", "pw:protocol")
    return config, script, transcript, launches


def test_driver_fake_protocol_roundtrip(fake):
    config, script, transcript, launches = fake
    script.write_text(
        json.dumps(
            [
                {"ok": True},
                {"ok": True, "status": 200, "html_redacted": "<p>safe</p>"},
                {"ok": True},
                {"ok": True, "fingerprint": "fixture"},
                {"ok": True, "landed": "build", "build_id": "12", "released": True},
                {"ok": True, "status": 200, "html_redacted": "<p>variables</p>"},
            ]
        )
    )
    with QbBrowser(config) as browser:
        assert browser.login()["ok"]
        assert browser.command("read", path="/build/12")["status"] == 200
        browser.command("open_form", overview_id=42)
        browser.command("fill", fields={})
        assert browser.command("submit", fingerprint="fixture")["build_id"] == "12"
        assert browser.command("read", path="/build/12/variables")["status"] == 200
    commands = [json.loads(line) for line in transcript.read_text().splitlines()]
    assert [command["command"] for command in commands] == [
        "login",
        "read",
        "open_form",
        "fill",
        "submit",
        "read",
        "close",
    ]
    assert not {"DEBUG", "QB_COOKIE", "QB_PASSWORD"} & set(launches[0][1]["env"])


@pytest.mark.parametrize("response", ["EXIT", "INVALID_JSON"])
def test_driver_bad_agent_reply_before_submit(fake, response):
    config, script, _, _ = fake
    script.write_text(json.dumps([response]))
    with QbBrowser(config) as browser, pytest.raises(QbBrowserError) as caught:
        browser.login()
    assert caught.value.code == "QB_BROWSER_UNAVAILABLE"


@pytest.mark.parametrize("response", ["EXIT", "INVALID_JSON"])
def test_driver_bad_agent_reply_after_submit(fake, response):
    config, script, _, _ = fake
    script.write_text(json.dumps([{"ok": True}] * 3 + [response]))
    with QbBrowser(config) as browser:
        browser.login()
        browser.command("open_form", overview_id=42)
        browser.command("fill", fields={})
        assert browser.command("submit", fingerprint="fixture")["landed"] == "unknown"


def test_python_production_launcher_never_passes_probe_switches():
    source = (ROOT / "tizen-ci-triage/scripts/ci_triage/qb_browser.py").read_text()
    for forbidden in (
        "diagnostic",
        "useBrowserFetch",
        "host-resolver-rules",
        "ignore-certificate-errors",
        "testOptions",
    ):
        assert forbidden not in source
    cli = (ROOT / "tizen-ci-triage/scripts/ci_triage/cli.py").read_text()
    for forbidden in (
        "diagnostic",
        "useBrowserFetch",
        "host-resolver-rules",
        "ignore-certificate-errors",
    ):
        assert forbidden not in cli
