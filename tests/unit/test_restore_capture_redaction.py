"""RESTORE-12: byte-preserving session identity masking and HTMLParser positions."""

import json
import subprocess
import sys
from html import escape
from pathlib import Path

import pytest
from tizen_qb_verify.qb_redact import (
    EvidenceRedactionError,
    PageRedactor,
    SessionPageRedactor,
)


@pytest.mark.parametrize("separator", ["\r", "\r\n", "\v", "\f", "\x85", "\u2028"])
def test_registered_cell_offsets_follow_htmlparser(separator: str) -> None:
    prefix = f"<p>before{separator}after</p>\n"
    source = prefix + (
        "<table><thead><tr><th>Triggered By</th></tr></thead>\n"
        "<tbody><tr><td>SyntheticUser</td></tr></tbody></table>"
    )
    redactor = PageRedactor()
    result = redactor.redact(source)
    assert result == source.replace("SyntheticUser", "&lt;USER&gt;")
    redactor.check_bytes(result.encode())


@pytest.mark.parametrize("separator", ["\r", "\v", "\u2028"])
def test_credential_attribute_offsets_follow_htmlparser(separator: str) -> None:
    source = f'<p>before{separator}after</p>\n<input type="hidden" value="SyntheticSecret">'
    assert PageRedactor().redact(source) == source.replace("SyntheticSecret", "&lt;REDACTED&gt;")


def test_session_user_is_masked_in_all_values_without_serializing_tags() -> None:
    source = (
        '<span>Welcome! synthetic-account (Display Name)</span>\r\n'
        '<title>Display Name</title><table><thead synthetic-account="unchanged">'
        '<tr><td>synthetic-account</td><td><a title="Display Name" '
        "href='/users/synthetic-account'>Display Name</a></td></tr></thead></table>"
        '<script>const user="synthetic-account";</script><!-- Display Name -->'
        '<p>prefixsynthetic-accountSuffix</p>'
    )
    expected = (
        '<span>Welcome! &lt;USER&gt;</span>\r\n'
        '<title>&lt;USER&gt;</title><table><thead synthetic-account="unchanged">'
        '<tr><td>&lt;USER&gt;</td><td><a title="&lt;USER&gt;" '
        "href='/users/&lt;USER&gt;'>&lt;USER&gt;</a></td></tr></thead></table>"
        '<script>const user="&lt;USER&gt;";</script><!-- &lt;USER&gt; -->'
        '<p>prefixsynthetic-accountSuffix</p>'
    )
    redactor = SessionPageRedactor()
    assert redactor.redact(source) == expected
    assert redactor.identity_replacement_count == 8
    assert redactor.session_identity_complete
    redactor.check_bytes(expected.encode())
    assert redactor.identity_outside_registered_count == 0
    assert redactor.redact(expected) == expected
    assert redactor.identity_replacement_count == 0


@pytest.mark.parametrize("identity", ["d>", "thead", "<td>", "USER", "A&B", 'A"B'])
def test_identity_fragments_never_rewrite_html_names(identity: str) -> None:
    redactor = SessionPageRedactor()
    redactor.remember_session_identity(identity)
    prefix = '<table><thead thead="normal"><tr><td>'
    suffix = '</td></tr></thead></table>'
    source = prefix + escape(identity) + suffix
    result = redactor.redact(source)
    assert result == prefix + '&lt;USER&gt;' + suffix
    redactor.check_bytes(result.encode())
    assert redactor.identity_outside_registered_count == 0


def test_encoded_identity_attribute_and_text_keep_other_bytes() -> None:
    redactor = SessionPageRedactor()
    redactor.remember_session_identity("Lin")
    source = '<b title="L&#105;n">L&#x69;n</b><i>Linux-PAM ILinkListener</i>'
    assert redactor.redact(source) == (
        '<b title="&lt;USER&gt;">&lt;USER&gt;</b><i>Linux-PAM ILinkListener</i>'
    )
    assert redactor.identity_replacement_count == 2


def test_remaining_session_identity_is_a_redaction_failure() -> None:
    redactor = SessionPageRedactor()
    redactor.remember_session_identity("SessionUser")
    with pytest.raises(EvidenceRedactionError):
        redactor.check_bytes(b'<a title="SessionUser">safe</a>')


def test_partial_multi_character_entity_fails_instead_of_claiming_zero_remaining() -> None:
    redactor = SessionPageRedactor()
    redactor.remember_session_identity("\u2242")
    with pytest.raises(EvidenceRedactionError):
        redactor.redact('<p>&NotEqualTilde;</p>')
    with pytest.raises(EvidenceRedactionError):
        redactor.check_bytes(b'<p>&NotEqualTilde;</p>')


def test_session_mode_does_not_claim_to_repair_historical_damaged_tags() -> None:
    redactor = SessionPageRedactor()
    redactor.remember_session_identity("SessionUser")
    source = '</thea&lt;USER&gt;<td>SessionUser</td>'
    assert redactor.redact(source) == '</thea&lt;USER&gt;<td>&lt;USER&gt;</td>'


def test_session_credentials_are_still_scrubbed() -> None:
    redactor = SessionPageRedactor()
    source = '<span>Welcome! SessionUser</span><input type="hidden" value="PrivateToken">'
    result = redactor.redact(source)
    assert "SessionUser" not in result and "PrivateToken" not in result
    redactor.check_bytes(result.encode())


def test_session_identity_must_not_be_inferred_from_other_users() -> None:
    redactor = SessionPageRedactor()
    redactor.redact('<span>Welcome! AccountOnly</span><table><tr><th>Triggered By</th></tr>'
                    '<tr><td>OtherAccount (OtherName)</td></tr></table>')
    assert not redactor.session_identity_complete
    assert redactor.identities == {"AccountOnly"}


@pytest.mark.parametrize("complete", [True, False])
def test_capture_worker_checks_before_and_after_writing(tmp_path: Path, complete: bool) -> None:
    script = Path(__file__).resolve().parents[2] / (
        "docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/evidence/restore/"
        "discovery-capture/redact_capture.py"
    )
    identity = "SyntheticAccount (SyntheticIdentity)" if complete else "SyntheticAccount"
    path = tmp_path / "page.html"
    messages = [json.dumps({"path": str(path), "mode": "html",
                           "text": f'<span>Welcome! {identity}</span><a>SyntheticIdentity</a>'})]
    if complete:
        messages.append(json.dumps({
            "path": str(tmp_path / "log.txt"), "mode": "text",
            "text": "SyntheticAccount error: vector<T> SyntheticIdentity\n",
        }))
    process = subprocess.run([sys.executable, str(script)], input="\n".join(messages) + "\n",
                             capture_output=True, text=True, check=True)
    replies = [json.loads(line) for line in process.stdout.splitlines()]
    assert replies[0]["ok"] is complete
    assert path.exists() is complete
    if complete:
        for reply in replies:
            assert reply["identity_replacement_count"] == 2
            assert reply["identity_remaining_count"] == 0
            assert "outside_identity_count" not in reply
        assert (tmp_path / "log.txt").read_text() == "<USER> error: vector<T> <USER>\n"
        assert "Synthetic" not in path.read_text()
    else:
        assert replies == [{"ok": False, "error": "QB_EVIDENCE_REDACTION_FAILED"}]
