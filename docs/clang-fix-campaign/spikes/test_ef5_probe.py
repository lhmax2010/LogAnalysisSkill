"""Offline safety controls for the EF-5 spike, not production-package tests."""

import base64
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request

from ef5_probe import HttpResponse, NoRedirect, Probe, Redactor, check_url, main

BASE = "https://quickbuild.tizen.org"


class ProbeSafetyTests(unittest.TestCase):
    def test_supplied_credentials_and_encodings_are_removed(self) -> None:
        password = "a<&+secret-987"
        cookie = "SID=private-session-123"
        redactor = Redactor("sample-user", password, cookie)
        encoded = base64.b64encode(f"sample-user:{password}".encode()).decode()
        text = redactor.redact(f"{password} {cookie} {encoded} a%3C%26%2Bsecret-987")
        self.assertNotIn(password, text)
        self.assertNotIn("private-session-123", text)
        self.assertNotIn(encoded, text)
        self.assertNotIn("secret-987", text)
        redactor.check(text)

    def test_server_side_xml_secrets_redacted_without_losing_sbs_target(self) -> None:
        redactor = Redactor("", "", "")
        text = redactor.redact(
            "<map><entry><string>API_TOKEN</string><string>remote-token-123</string></entry>"
            "<password>remote-password-456</password>"
            "<entry><string>SBS_TARGET</string><string>repo@abc</string></entry></map>"
        )
        self.assertNotIn("remote-token-123", text)
        self.assertNotIn("remote-password-456", text)
        self.assertIn("repo@abc", text)

    def test_html_hidden_password_and_sensitive_table_cells_redacted(self) -> None:
        text = Redactor("", "", "").redact(
            '<html><input type="hidden" value="csrf-random-123">'
            '<input type="password" value="password-random-456">'
            "<table><tr><td>SECRET_KEY</td><td>key-random-789</td></tr></table></html>"
        )
        for secret in ("csrf-random-123", "password-random-456", "key-random-789"):
            self.assertNotIn(secret, text)

    def test_known_secret_check_rejects_unsanitized_text(self) -> None:
        with self.assertRaises(ValueError):
            Redactor("", "private-password-123", "").check("private-password-123")

    def test_safe_reads_allowed(self) -> None:
        for path in (
            "/rest/version",
            "/rest/builds/123/variables",
            "/build/123",
            "/rest/ids?configuration_path=root%2FSBS",
        ):
            check_url(BASE + path, BASE)

    def test_get_trigger_and_non_read_paths_are_blocked(self) -> None:
        for path in (
            "/rest/trigger?configuration_id=1",
            "/rest/build_requests",
            "/build/123?action=run",
            "/rest/builds/123/delete",
            "/rest/ids?path=root",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                check_url(BASE + path, BASE)

    def test_cross_origin_and_non_https_rejected(self) -> None:
        for url in (
            "https://example.org/rest/version",
            "http://quickbuild.tizen.org/rest/version",
            "https://user:password@quickbuild.tizen.org/rest/version",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                check_url(url, BASE)

    def test_redirects_never_followed(self) -> None:
        self.assertIsNone(
            NoRedirect().redirect_request(
                Request(BASE + "/rest/version"),
                None,
                302,
                "redirect",
                {},
                BASE + "/rest/trigger?configuration_id=1",
            )
        )

    def test_credential_in_configuration_path_rejected_before_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            probe = Probe(BASE, Path(directory) / "out", "sample", "not-a-config-path", "")
            with patch.object(probe.opener, "open") as send:
                with self.assertRaises(ValueError):
                    probe.get(
                        "configuration", "/rest/ids?configuration_path=not-a-config-path", "basic"
                    )
                send.assert_not_called()
            self.assertEqual(list(probe.output.iterdir()), [])

    def test_failed_basic_probe_stops_subsequent_reads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            argv = [
                "ef5_probe.py",
                "--username",
                "sample",
                "--build-id",
                "123",
                "--configuration-path",
                "root/SBS",
                "--output",
                str(Path(directory) / "out"),
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(sys.stdin, "isatty", return_value=False),
                patch("ef5_probe.read_secret", side_effect=["fixture-password", ""]),
                patch.object(Probe, "get", return_value=HttpResponse(500, BASE, b"denied")) as get,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(main(), 4)
            self.assertEqual(
                [call.args[0] for call in get.call_args_list],
                ["version-anonymous", "version-basic"],
            )


if __name__ == "__main__":
    unittest.main()
