"""Offline controls for the Cookie-only webpage spike."""

import contextlib
import io
import json
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch

from ef5_probe import HttpResponse
from ef5_web_probe import PageRedactor, WebProbe, check_page_url

BASE = "https://quickbuild.tizen.org"


class WebSafetyTests(unittest.TestCase):
    def test_whitelist_rejects_actions_queries_other_ids_and_origins(self) -> None:
        for path in ("/build/123", "/build/123/variables", "/build/123/dependencies"):
            check_page_url(BASE + path, BASE, {"123"})
        for path in (
            "/build/123/rerun", "/build/123/cancel", "/rest/trigger", "/signin",
            "/build/123?0-1.ILinkListener-run", "/build/123/variables?", "/build/124",
            "/build/123/../trigger", "/build/123/%2e%2e/trigger", "/build/123#run",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                check_page_url(BASE + path, BASE, {"123"})
        with self.assertRaises(ValueError):
            check_page_url("https://evil.invalid/build/123", BASE, {"123"})

    def test_hidden_fields_session_ids_and_scripts_redacted(self) -> None:
        raw = ('<input TYPE="HIDDEN" value="hidden-123456">'
               '<meta name="csrf-token" content="meta-123456">'
               '<script>var sessionId = "server-123456";</script>'
               '<a href="/build/123;jsessionid=url-123456">SBS_TARGET repo@abcd</a>')
        safe = PageRedactor("", "", "SID=cookie-123456").redact(raw)
        for value in ("hidden-123456", "meta-123456", "server-123456", "url-123456"):
            self.assertNotIn(value, safe)
        self.assertIn("SBS_TARGET repo@abcd", safe)

    def test_cookie_cannot_enter_url_before_send(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = WebProbe(BASE, Path(d) / "out", "SID=123456", {"123456"})
            with patch.object(p.opener, "open") as send, self.assertRaises(ValueError):
                p.get("page", "/build/123456", "cookie")
            send.assert_not_called()
            self.assertEqual(list(p.output.iterdir()), [])

    def test_set_cookie_removed_before_evidence_and_no_auth_headers_archived(self) -> None:
        class Response(io.BytesIO):
            code = 200
            headers = Message()
            headers.add_header("Set-Cookie", "SID=response-123456; HttpOnly")
            headers.add_header("Content-Type", "text/html")

            def geturl(self):
                return BASE + "/build/123"

        with tempfile.TemporaryDirectory() as d:
            p = WebProbe(BASE, Path(d) / "out", "SID=request-123456", {"123"})
            stream = Response(
                b'<html>response-123456<input type="hidden" value="hidden-6789"></html>'
            )
            with patch.object(p.opener, "open", return_value=stream) as send:
                p.get("page", "/build/123", "cookie")
            request = send.call_args.args[0]
            self.assertEqual(request.get_method(), "GET")
            self.assertEqual(request.get_header("Cookie"), "SID=request-123456")
            self.assertIsNone(request.get_header("Authorization"))
            evidence = "".join(f.read_text() for f in p.output.iterdir())
            for secret in ("response-123456", "request-123456", "hidden-6789", "Set-Cookie"):
                self.assertNotIn(secret, evidence)

    def test_blocked_pages_stop_before_tabs(self) -> None:
        for status, body in ((302, b""), (403, b"denied"), (200, b"AccessDeniedException"),
                             (200, b'<input type="password" name="password">')):
            with self.subTest(status=status, body=body), tempfile.TemporaryDirectory() as d:
                p = WebProbe(BASE, Path(d) / "out", "SID=fixture-cookie", {"123"})
                (p.output / "build-123-01.response.txt").write_bytes(body)
                with patch.object(p, "get", return_value=HttpResponse(status, BASE, body)) as get:
                    self.assertTrue(p.inspect_build("123").startswith("BLOCKED_"))
                self.assertEqual(get.call_count, 1)
                self.assertFalse(list(p.output.glob("*.page.json")))

    def test_only_literal_read_tabs_followed_no_parent_guesses(self) -> None:
        raw = ('<html>SBS succeeded<a href="/build/123/variables">Variables</a>'
               '<a href="/build/456">TRIGGER</a><a href="/build/123/rerun">Run</a>'
               '<a href="/build/123?0-run">Run action</a></html>')
        with tempfile.TemporaryDirectory() as d:
            p = WebProbe(BASE, Path(d) / "out", "SID=fixture-cookie", {"123"})

            def get(name, path, auth):
                text = raw if path == "/build/123" else "<html>SBS_TARGET repo@abc</html>"
                (p.output / (name + ".response.txt")).write_text(text)
                return HttpResponse(200, BASE + path, text.encode())

            with patch.object(p, "get", side_effect=get) as fetch:
                self.assertEqual(p.inspect_build("123"), "READ_PAGES_COLLECTED")
            self.assertEqual([c.args[1] for c in fetch.call_args_list],
                             ["/build/123", "/build/123/variables"])
            data = json.loads((p.output / "build-123-01.page.json").read_text())
            self.assertEqual([x["decision"] for x in data["links"]],
                             ["ALLOW_READ", "NOT_FOLLOWED", "NOT_FOLLOWED", "NOT_FOLLOWED"])
            self.assertEqual(data["forms_submitted"], 0)


if __name__ == "__main__":
    with contextlib.redirect_stdout(io.StringIO()):
        unittest.main()
