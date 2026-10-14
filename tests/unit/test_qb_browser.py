from __future__ import annotations

import ast
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
        ("QB_BROWSER_UNAVAILABLE", None, "QB_BROWSER_UNAVAILABLE"),
        ("QB_EVIDENCE_REDACTION_FAILED", None, "QB_EVIDENCE_REDACTION_FAILED"),
        ("UNKNOWN", None, "INTERNAL_ERROR"),
        ("QB_READ_ID_MISMATCH", None, "QB_FETCH_FAILED"),
        ("QB_READ_REDIRECTED", None, "QB_FETCH_FAILED"),
        ("QB_TRUSTED_CONTEXT_UNAVAILABLE", None, "QB_FETCH_FAILED"),
    ],
)
def test_frozen_error_mapping(error, field, expected):
    with pytest.raises(QbBrowserError) as caught:
        decode_response(
            json.dumps({"ok": False, "error": error, "field": field}),
            submit_sent=False,
            command="read",
        )
    assert caught.value.code == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "not json",
        "null",
        "[]",
        "true",
        '{"ok":0}',
        '{"ok":false,"error":"AGENT_PHASE"}',
        '{"ok":false,"error":[],"released":false}',
        '{"ok":false,"released":false}',
        '{"ok":true,"released":false,"landed":"build","build_id":"12"}',
        '{"ok":true,"released":true,"landed":"build","build_id":"wrong"}',
        '{"ok":true,"landed":"build","build_id":"12"}',
        '{"ok":true,"released":true}',
    ],
)
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
def test_sensitive_reply_is_always_discarded(key, sent):
    raw = json.dumps({"ok": True, "nested": [{key: "fixture-secret"}]})
    if sent:
        result = decode_response(raw, submit_sent=True)
        assert result["landed"] == "unknown"
        assert "fixture-secret" not in json.dumps(result)
        assert key not in result
        return
    with pytest.raises(QbBrowserError) as caught:
        decode_response(raw, submit_sent=False)
    assert caught.value.code == "QB_BROWSER_UNAVAILABLE"
    assert "fixture-secret" not in str(caught.value)


@pytest.mark.parametrize("error", ["QB_READ_REDIRECTED", "QB_READ_ID_MISMATCH"])
def test_read_error_mapping_is_scoped_to_read(error):
    with pytest.raises(QbBrowserError) as caught:
        decode_response(
            json.dumps({"ok": False, "error": error}), submit_sent=False, command="fill"
        )
    assert caught.value.code == "INTERNAL_ERROR"
    assert caught.value.released is None


@pytest.mark.parametrize("command", ["open_form", "fill", "submit"])
def test_trusted_context_form_error_mapping(command):
    with pytest.raises(QbBrowserError) as caught:
        decode_response(
            json.dumps({"ok": False, "error": "QB_TRUSTED_CONTEXT_UNAVAILABLE"}),
            submit_sent=False, command=command,
        )
    assert caught.value.code == "REJECTED_QB_FORM_CHANGED"


def test_structural_error_carries_checked_diagnostic_without_losing_error():
    diagnostic = {
        "html_redacted": "<span>Welcome! &lt;USER&gt;</span><p>Successful</p>",
        "facts": {"first_failed_check": "labels", "extra": ["&lt;REDACTED&gt;"]},
    }
    with pytest.raises(QbBrowserError) as caught:
        decode_response(json.dumps({"ok": False, "error": "QB_FORM_CHANGED",
                                    "diagnostic": diagnostic}), submit_sent=False, command="fill")
    assert caught.value.code == "REJECTED_QB_FORM_CHANGED"
    assert caught.value.diagnostic == diagnostic
    assert caught.value.diagnostic_failed is False


@pytest.mark.parametrize(
    "command,error,expected",
    [
        ("fill", "QB_FORM_CHANGED", "REJECTED_QB_FORM_CHANGED"),
        ("read", "QB_READ_ID_MISMATCH", "QB_FETCH_FAILED"),
        ("submit", "QB_FORM_READBACK_MISMATCH", "REJECTED_QB_FORM_MISMATCH"),
    ],
)
def test_redacted_hidden_input_diagnostic_preserves_original_error(command, error, expected):
    diagnostic = {
        "html_redacted": (
            '<input type="hidden" name="token" value="&lt;REDACTED&gt;">'
            '<input type="hidden" name="opaque" value="&lt;REDACTED&gt;">'
            '<input type="hidden" name="x:palette:recorder" value="616263">'
        ),
        "facts": {
            "first_failed_check": "labels",
            'quoted "label" \\ path': 'token="&lt;REDACTED&gt;"',
            "csrf_token": "<REDACTED>",
            "rows": [{"callback": "/x;jsessionid=&lt;REDACTED&gt;"}, None, 1, False],
        },
    }
    with pytest.raises(QbBrowserError) as caught:
        decode_response(
            json.dumps({"ok": False, "error": error, "released": False,
                        "diagnostic": diagnostic}),
            submit_sent=command == "submit", command=command,
        )
    assert caught.value.code == expected
    assert caught.value.diagnostic == diagnostic
    assert caught.value.diagnostic_failed is False
    assert caught.value.released is (False if command == "submit" else None)


def test_diagnostic_fact_strings_are_checked_without_json_escaping():
    diagnostic = {
        "html_redacted": "<p>safe</p>",
        "facts": {
            "label": '<input type="hidden" name="token" value="&lt;REDACTED&gt;">',
            '<span>Welcome! &lt;USER&gt;</span>': ['csrf="<REDACTED>"', 'sessionKey=""'],
        },
    }
    with pytest.raises(QbBrowserError) as caught:
        decode_response(
            json.dumps({"ok": False, "error": "QB_FORM_CHANGED", "diagnostic": diagnostic}),
            submit_sent=False, command="fill",
        )
    assert caught.value.code == "REJECTED_QB_FORM_CHANGED"
    assert caught.value.diagnostic == diagnostic


@pytest.mark.parametrize("location", ["key", "value", "list"])
@pytest.mark.parametrize(
    "leak",
    [
        "JSESSIONID_8810=synthetic-private",
        "/x;jsessionid=synthetic-private",
        'token="synthetic-private"',
        "callback?csrf=synthetic-private",
        "XSRF='synthetic-private'",
        "prefix\nAuthorization: Bearer synthetic-private",
        "Cookie: synthetic-private",
        "Set-Cookie: synthetic-private",
        "tok&#101;n=&quot;synthetic-private&quot;",
    ],
)
def test_nested_diagnostic_facts_reject_credentials_in_keys_and_values(location, leak):
    entry = {leak: "safe"} if location == "key" else {"label": leak}
    if location == "list":
        entry = {"labels": [leak]}
    diagnostic = {"html_redacted": "<p>safe</p>", "facts": {"rows": [{"nested": entry}]}}
    with pytest.raises(EvidenceRedactionError) as caught:
        decode_response(
            json.dumps({"ok": False, "error": "QB_FORM_CHANGED", "diagnostic": diagnostic}),
            submit_sent=False, command="fill",
        )
    assert "synthetic-private" not in str(caught.value)


@pytest.mark.parametrize("key", ["cookie", "Cookie", "set-cookie", "Authorization"])
@pytest.mark.parametrize("sent", [False, True])
def test_diagnostic_sensitive_keys_are_still_discarded(key, sent):
    raw = json.dumps({
        "ok": False, "error": "QB_FORM_CHANGED", "released": False,
        "diagnostic": {"html_redacted": "<p>safe</p>", "facts": {"rows": [{key: "safe"}]}},
    })
    if sent:
        response = decode_response(raw, submit_sent=True, command="submit")
        assert response["landed"] == "unknown"
        assert "diagnostic" not in response
        return
    with pytest.raises(QbBrowserError) as caught:
        decode_response(raw, submit_sent=False, command="fill")
    assert caught.value.code == "QB_BROWSER_UNAVAILABLE"
    assert caught.value.diagnostic is None


def test_diagnostic_failure_has_no_partial_snapshot():
    with pytest.raises(QbBrowserError) as caught:
        decode_response(json.dumps({"ok": False, "error": "QB_READ_ID_MISMATCH",
                                    "diagnostic_failed": True}), submit_sent=False, command="read")
    assert caught.value.code == "QB_FETCH_FAILED"
    assert caught.value.diagnostic is None
    assert caught.value.diagnostic_failed is True


@pytest.mark.parametrize("part", ["html_redacted", "facts"])
def test_diagnostic_raw_secret_rejected(part):
    diagnostic = {"html_redacted": "<p>safe</p>", "facts": {}}
    diagnostic[part] = "JSESSIONID_8810=synthetic-private"
    with pytest.raises(EvidenceRedactionError):
        decode_response(json.dumps({"ok": False, "error": "QB_FORM_CHANGED",
                                    "diagnostic": diagnostic}), submit_sent=False, command="fill")


@pytest.mark.parametrize(
    "error,expected",
    [
        ("QB_FORM_CHANGED", "REJECTED_QB_FORM_CHANGED"),
        ("AGENT_PHASE", "QB_BROWSER_UNAVAILABLE"),
        ("QB_BROWSER_UNAVAILABLE", "QB_BROWSER_UNAVAILABLE"),
        ("QB_EVIDENCE_REDACTION_FAILED", "QB_EVIDENCE_REDACTION_FAILED"),
        ("UNKNOWN", "INTERNAL_ERROR"),
    ],
)
@pytest.mark.parametrize("released", [False, True, None, 0, 1, "false", {}, []])
def test_submit_error_only_explicit_boolean_false_proves_not_released(error, expected, released):
    raw = json.dumps({"ok": False, "error": error, "released": released})
    if released is False:
        with pytest.raises(QbBrowserError) as caught:
            decode_response(raw, submit_sent=True, command="submit")
        assert caught.value.code == expected
        assert caught.value.released is False
    else:
        assert decode_response(raw, submit_sent=True, command="submit")["landed"] == "unknown"


def test_submit_verified_build_and_unknown_landing_preserved():
    for response in (
        {"ok": True, "released": True, "landed": "build", "build_id": "12"},
        {
            "ok": True,
            "released": True,
            "landed": "unknown",
            "observed": "/wicket/page",
            "messages": ["safe message"],
        },
    ):
        assert decode_response(json.dumps(response), submit_sent=True) == response


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
        "<span>Welcome! &lt;USER&gt;</span>"
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


@pytest.mark.parametrize("released", [False, True, None, 0, "false"])
def test_driver_preserves_submit_release_evidence(fake, released):
    config, script, _, _ = fake
    script.write_text(
        json.dumps(
            [{"ok": True}] * 3 + [{"ok": False, "error": "QB_FORM_CHANGED", "released": released}]
        )
    )
    with QbBrowser(config) as browser:
        browser.login()
        browser.command("open_form", overview_id=42)
        browser.command("fill", fields={})
        if released is False:
            with pytest.raises(QbBrowserError) as caught:
                browser.command("submit", fingerprint="fixture")
            assert caught.value.code == "REJECTED_QB_FORM_CHANGED"
            assert caught.value.released is False
        else:
            assert browser.command("submit", fingerprint="fixture")["landed"] == "unknown"


def test_driver_read_error_mapping(fake):
    config, script, _, _ = fake
    script.write_text(json.dumps([{"ok": True}, {"ok": False, "error": "QB_READ_ID_MISMATCH"}]))
    with QbBrowser(config) as browser, pytest.raises(QbBrowserError) as caught:
        browser.login()
        browser.command("read", path="/build/12")
    assert caught.value.code == "QB_FETCH_FAILED"


@pytest.mark.parametrize("failure", ["missing-process", "broken-pipe", "closed-pipe", "decode"])
def test_submit_process_failure_cannot_claim_not_released(fake, monkeypatch, failure):
    config, script, _, _ = fake
    browser = QbBrowser(config)
    if failure == "missing-process":
        assert browser.command("submit", fingerprint="fixture")["landed"] == "unknown"
        return
    script.write_text("[]")
    with browser:

        def fail(*_args):
            if failure == "closed-pipe":
                raise ValueError("closed pipe")
            if failure == "decode":
                raise UnicodeError("invalid bytes")
            raise BrokenPipeError("broken pipe")

        with monkeypatch.context() as patch:
            stream = browser.process.stdout if failure == "decode" else browser.process.stdin
            patch.setattr(stream, "readline" if failure == "decode" else "write", fail)
            assert browser.command("submit", fingerprint="fixture")["landed"] == "unknown"


def test_python_production_launcher_never_passes_probe_switches():
    source = (ROOT / "tizen-ci-triage/scripts/ci_triage/qb_browser.py").read_text()
    # Diagnostic responses are data, not permission to launch in probe mode.
    launches = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute) and node.func.attr == "Popen"]
    assert len(launches) == 1
    argv = launches[0].args[0]
    assert isinstance(argv, ast.List) and len(argv.elts) == 4
    assert ast.unparse(argv) == (
        "[browser['node'], str(Path(__file__).with_name('qb_browser_agent.mjs')), "
        "browser['playwright_module'], browser['chromium']]"
    )
    for forbidden in (
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
