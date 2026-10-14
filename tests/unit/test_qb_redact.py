from __future__ import annotations

import json
from html import unescape
from pathlib import Path

import pytest
from ci_triage.qb_redact import EvidenceRedactionError, PageRedactor

PAGE = """<html><div>Welcome! Fixture Person</div>
<table><tr><td>Triggered By</td><td><a href="user">Fixture Account</a></td></tr></table>
<input type="hidden" name="csrf_token" value="csrf-private">
<input type="hidden" name="ordinary" value="ordinary-private"><option value="1">business</option>
<input type="hidden" name="prop:palette:recorder" value="61,62">
<a href="/x;jsessionid=url-private?token=token-private&amp;csrf=csrf-private">link</a>
<script>sessionKey="session-private";</script><p>JSESSIONID_8810=cookie-private</p>
</html>"""
SECRETS = [
    "Fixture Person",
    "Fixture Account",
    "csrf-private",
    "ordinary-private",
    "url-private",
    "token-private",
    "session-private",
    "cookie-private",
    "JSESSIONID_8810=",
]
VECTORS = json.loads(
    (Path(__file__).parents[1] / "fixtures/qb_redaction_vectors.json").read_text()
)


@pytest.mark.parametrize("vector", VECTORS, ids=lambda vector: vector["name"])
def test_shared_positional_identities_and_global_credentials(vector, tmp_path):
    redactor = PageRedactor()
    safe = redactor.redact(vector["html"])
    visible = unescape(safe)
    for value in vector["preserved"] + vector["masked"]:
        assert value in visible
    for value in vector["secrets"]:
        assert value not in visible
    assert visible.count("<USER>") == vector["user_mask_count"]
    assert redactor.identities == set(vector["identities"])
    assert redactor.identity_outside_registered_count == vector["identity_outside_registered_count"]
    assert safe == redactor.redact(safe)
    path = tmp_path / "safe.html"
    path.write_bytes(safe.encode())
    redactor.check_bytes(path.read_bytes())
    redactor.check_written(path)
    PageRedactor().check_written(path)
    assert path.read_bytes() == safe.encode()
    for identity in vector["identities"]:
        redactor.check_bytes((safe + " " + identity + "-PAM").encode())
        assert (
            redactor.identity_outside_registered_count
            == vector["identity_outside_registered_count"] + 1
        )
        path.write_bytes((safe + " " + identity).encode())
        redactor.check_written(path)
        assert path.exists()
    redactor.check_bytes(safe.encode())
    assert redactor.identity_outside_registered_count == vector["identity_outside_registered_count"]
    for secret in vector["secrets"]:
        injected = (safe + f"<label>x{secret}x</label>").encode()
        with pytest.raises(EvidenceRedactionError):
            redactor.check_bytes(injected)
        path.write_bytes(injected)
        with pytest.raises(EvidenceRedactionError):
            redactor.check_written(path)
        assert not path.exists()


@pytest.mark.parametrize("secret", ["CookieFixture", "TokenFixture", "SessionFixture"])
def test_secret_residual_self_check_remains_substring(secret, tmp_path):
    redactor = PageRedactor()
    redactor.secrets.add(secret)
    path = tmp_path / "unsafe.html"
    path.write_bytes(f"<p>x{secret}x</p>".encode())
    with pytest.raises(EvidenceRedactionError):
        redactor.check_bytes(path.read_bytes())
    with pytest.raises(EvidenceRedactionError):
        redactor.check_written(path)
    assert not path.exists()


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
        "<span>Welcome! Fixture Person</span>",
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


REGISTERED_FIELDS = [
    "<div>Welcome! {identity}</div>",
    "<table><tr><td>Triggered By</td><td>{identity}</td></tr></table>",
    "<table><tr><th>Status</th><th>Triggered By</th></tr>"
    "<tr><td>Successful</td><td>{identity}</td></tr></table>",
    "<table><thead><tr><th><span>Requested By</span></th><th>Process Status</th>"
    "</tr></thead><tbody><tr><td><span>{identity}</span></td>"
    "<td>RUNNING_BUILD</td></tr></tbody></table>",
]


@pytest.mark.parametrize("identity", ["Successful", "Failed", "Full", "root", "Lin"])
@pytest.mark.parametrize("template", REGISTERED_FIELDS)
def test_registered_field_restored_after_redaction_is_rejected(template, identity, tmp_path):
    source = template.format(identity=identity) + f"<p>{identity}</p>"
    redactor = PageRedactor()
    safe = redactor.redact(source)
    path = tmp_path / "evidence.html"
    path.write_bytes(safe.encode())
    redactor.check_written(path)
    assert f"<p>{identity}</p>" in path.read_text()

    restored = safe.replace("&lt;USER&gt;", identity, 1).encode()
    for checker in (redactor, PageRedactor()):
        with pytest.raises(EvidenceRedactionError):
            checker.check_bytes(restored)
        path.write_bytes(restored)
        with pytest.raises(EvidenceRedactionError):
            checker.check_written(path)
        assert not path.exists()


@pytest.mark.parametrize("template", REGISTERED_FIELDS)
@pytest.mark.parametrize("identity", ["", " \n ", "&lt;USER&gt;", "<span>&lt;USER&gt;</span>"])
def test_registered_fields_accept_only_empty_or_masked_values(template, identity):
    PageRedactor().check_bytes(template.format(identity=identity).encode())


def test_identity_count_is_per_document_and_context_survives_between_pages(capsys):
    redactor = PageRedactor()
    assert redactor.identity_outside_registered_count == 0
    redactor.redact("<span>Welcome! Lin</span><p>Lin Lin-PAM</p>")
    assert redactor.identity_outside_registered_count == 2
    second = "<table><tr><th>Owner</th></tr><tr><td>Lin</td></tr></table>"
    assert redactor.redact(second) == second
    assert redactor.identity_outside_registered_count == 1
    redactor.check_bytes(b"<span>Welcome! &lt;USER&gt;</span><p>Linux-PAM</p>")
    assert redactor.identity_outside_registered_count == 0
    assert capsys.readouterr() == ("", "")


def test_identity_count_excludes_registered_masks_even_when_mask_text_is_an_identity():
    redactor = PageRedactor()
    safe = redactor.redact("<span>Welcome! USER</span><p>USER</p>")
    assert safe == "<span>Welcome! &lt;USER&gt;</span><p>USER</p>"
    assert redactor.identity_outside_registered_count == 1
    redactor.check_bytes(safe.encode())
    assert redactor.identity_outside_registered_count == 1


def test_credentials_remain_global_when_the_value_is_also_an_identity():
    safe = PageRedactor().redact(
        '<span>Welcome! Lin</span><input type="hidden" name="token" value="Lin">'
        "<p>Lin xLinx</p>"
    )
    assert "Lin" not in safe
    assert "<p>&lt;REDACTED&gt; x&lt;REDACTED&gt;x</p>" in safe


def test_registered_columns_do_not_leak_between_tables():
    source = (
        "<table><tr><th>Requested By</th><th>Status</th></tr>"
        "<tr><td>Lin</td><td>Successful</td></tr></table>"
        "<table><tr><th>Owner</th><th>Status</th></tr>"
        "<tr><td>Lin</td><td>Successful</td></tr></table>"
    )
    redactor = PageRedactor()
    safe = redactor.redact(source)
    assert safe.count("&lt;USER&gt;") == 1
    assert safe.endswith("<tr><td>Lin</td><td>Successful</td></tr></table>")
    assert redactor.identity_outside_registered_count == 1


def test_ordinary_recorder_named_input_is_not_palette_exception():
    safe = PageRedactor().redact('<input type="hidden" name="recorder" value="private">')
    assert "private" not in safe


@pytest.mark.parametrize(
    "attributes",
    [
        'type="hidden" name="opaque"',
        'type="HIDDEN"',
        'type="hidden" name="recorder"',
        'type="password" name="opaque"',
    ],
)
def test_hidden_values_remain_global_in_later_strings_and_checks(attributes, tmp_path):
    redactor = PageRedactor()
    safe = redactor.redact(f'<input {attributes} value="OpaqueFixture">')
    assert "OpaqueFixture" not in safe
    assert redactor.redact("<label>xOpaqueFixturex</label>") == (
        "<label>x&lt;REDACTED&gt;x</label>"
    )
    path = tmp_path / "unsafe.html"
    path.write_bytes(b"<label>xOpaqueFixturex</label>")
    with pytest.raises(EvidenceRedactionError):
        redactor.check_written(path)
    assert not path.exists()


def test_short_hidden_values_are_global_even_in_business_options():
    safe = PageRedactor().redact(
        '<input type="hidden" name="opaque" value="1"><option value="1">1</option>'
    )
    assert "1" not in safe
    assert '<option value="&lt;REDACTED&gt;">&lt;REDACTED&gt;</option>' in safe


def test_palette_recorder_does_not_register_a_global_secret():
    redactor = PageRedactor()
    source = '<input type="hidden" name="x:palette:recorder" value="616263"><p>616263</p>'
    assert redactor.redact(source) == source
    assert redactor.secrets == set()
    redactor.check_bytes(source.encode())


@pytest.mark.parametrize("header", ["Triggered By", "Requested By"])
def test_trimmed_registered_headers_still_reject_unmasked_values(header, tmp_path):
    source = (
        f"<table><tr><th> \t{header}\n </th></tr>"
        "<tr><td>Unknown Account</td></tr></table>"
    )
    path = tmp_path / "unsafe.html"
    path.write_bytes(source.encode())
    with pytest.raises(EvidenceRedactionError):
        PageRedactor().check_written(path)
    assert not path.exists()


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
