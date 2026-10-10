from __future__ import annotations

from html import unescape
from pathlib import Path

import pytest
from ci_triage.qb_redact import EvidenceRedactionError, PageRedactor

PAGE = """<html><div>Welcome! Fixture Person</div>
<table><tr><td>Triggered By</td><td><a href="user">Fixture Account</a></td></tr></table>
<input type="hidden" name="csrf_token" value="csrf-private">
<input type="hidden" name="ordinary" value="1"><option value="1">business</option>
<input type="hidden" name="prop:palette:recorder" value="61,62">
<a href="/x;jsessionid=url-private?token=token-private&amp;csrf=csrf-private">link</a>
<script>sessionKey="session-private";</script><p>JSESSIONID_8810=cookie-private</p>
</html>"""
SECRETS = [
    "Fixture Person",
    "Fixture Account",
    "csrf-private",
    "url-private",
    "token-private",
    "session-private",
    "cookie-private",
    "JSESSIONID_8810=",
]


def test_redact_roundtrip_and_raw_written_scan(tmp_path: Path, capsys):
    redactor = PageRedactor()
    safe = redactor.redact(PAGE)
    assert safe == redactor.redact(safe)
    assert '<input type="hidden" name="prop:palette:recorder" value="61,62">' in safe
    assert '<option value="1">business' in safe
    assert "<USER>" in unescape(safe)
    assert "<REDACTED>" in unescape(safe)
    assert PAGE.count("\n") == safe.count("\n")
    path = tmp_path / "evidence.html"
    path.write_bytes(safe.encode())
    redactor.check_written(path)
    for secret in SECRETS:
        assert secret.encode() not in path.read_bytes()
        assert secret not in capsys.readouterr().out
        assert secret not in capsys.readouterr().err


@pytest.mark.parametrize(
    "bad",
    [
        '<input type="hidden" value="private">',
        '<a href="/x;jsessionid=private">link</a>',
        "JSESSIONID_8810=private",
        "Fixture Person",
        "Authorization: Basic private",
        "Cookie: private",
        "Set-Cookie: private",
        "\xff",
    ],
)
def test_self_check_failure_deletes_evidence(tmp_path, bad):
    redactor = PageRedactor()
    redactor.redact(PAGE)
    path = tmp_path / "unsafe.html"
    path.write_bytes(bad.encode("latin1"))
    with pytest.raises(EvidenceRedactionError) as error:
        redactor.check_written(path)
    assert error.value.code == "QB_EVIDENCE_REDACTION_FAILED"
    assert str(error.value) == "evidence redaction self-check failed"
    assert not path.exists()


@pytest.mark.parametrize("header", ["Set-Cookie", "Cookie", "Authorization"])
def test_header_lines_never_returned(header):
    safe = PageRedactor().redact(header + ": sensitive-private\n<html>page</html>")
    assert header not in safe
    assert "sensitive-private" not in safe


def test_triggered_by_column_and_entities():
    source = (
        "<span>Welcome! Name &amp; Last</span><table><tr><th>Id</th>"
        "<th>Triggered By</th></tr><tr><td>123</td><td>other-user</td></tr></table>"
    )
    safe = PageRedactor().redact(source)
    assert "Name" not in safe and "other-user" not in safe
    assert "123" in safe


def test_ordinary_recorder_named_input_is_not_palette_exception():
    safe = PageRedactor().redact('<input type="hidden" name="recorder" value="private">')
    assert "private" not in safe


def test_encoded_and_quoted_secrets():
    safe = PageRedactor().redact(
        '<input type="hidden" name="token" value="private&amp;secret">'
        '<script>token="private&amp;secret"</script>'
    )
    assert "private" not in safe


@pytest.mark.parametrize(
    "source",
    [
        "<div>Welcome! Unknown User</div>",
        "<table><tr><td>Triggered By</td><td>Unknown Account</td></tr></table>",
        '<meta name="csrf-token" content="unseen-private">',
        '<input name="csrf-token" value="unseen-private">',
    ],
)
def test_fresh_redactor_self_check_does_not_need_prior_secrets(source, tmp_path):
    path = tmp_path / "injected.html"
    path.write_bytes(source.encode())
    with pytest.raises(EvidenceRedactionError):
        PageRedactor().check_written(path)
    assert not path.exists()
