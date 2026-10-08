"""Offline controls; fixture values are synthetic, never browser credentials."""

import unittest
from http.cookies import SimpleCookie

from ef5_browser_receiver import cookie_header
from ef5_web_probe import PageRedactor


class BrowserReceiverTests(unittest.TestCase):
    def test_structured_cookie_roundtrip_and_redaction(self) -> None:
        rows = [
            {"domain": "quickbuild.tizen.org", "name": "SID", "value": "fake-session-123"},
            {"domain": ".tizen.org", "name": "OTHER", "value": "fake=value!"},
        ]
        header = cookie_header(rows)
        parsed = SimpleCookie()
        parsed.load(header)
        self.assertEqual({key: val.value for key, val in parsed.items()},
                         {"SID": "fake-session-123", "OTHER": "fake=value!"})
        safe = PageRedactor("", "", header).redact(
            '<html>fake-session-123 fake=value!<input type="hidden" value="fake-hidden"/>'
        )
        for value in ("fake-session-123", "fake=value!", "fake-hidden"):
            self.assertNotIn(value, safe)

    def test_foreign_cookie_empty_and_header_injection_rejected(self) -> None:
        for rows in (
            [],
            [{"domain": "evil.invalid", "name": "SID", "value": "fake"}],
            [{"domain": "quickbuild.tizen.org", "name": "SID", "value": "fake\r\nX: y"}],
            [{"domain": "quickbuild.tizen.org", "name": "SID\n", "value": "fake"}],
        ):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                cookie_header(rows)


if __name__ == "__main__":
    unittest.main()
