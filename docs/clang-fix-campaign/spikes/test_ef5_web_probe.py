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
from ef5_web_probe import EXTRA_READ_PATHS, PageInventory, PageRedactor, WebProbe, check_page_url

BASE = "https://quickbuild.tizen.org"


class WebSafetyTests(unittest.TestCase):
    def test_five_exact_paths_only_and_no_post(self) -> None:
        ids = {"1069532", "1069540"}
        self.assertEqual(len(EXTRA_READ_PATHS), 5)
        for path in EXTRA_READ_PATHS:
            check_page_url(BASE + path, BASE, ids)
            for method in ("POST", "PUT", "DELETE", "HEAD"):
                with self.subTest(path=path, method=method), self.assertRaises(ValueError):
                    check_page_url(BASE + path, BASE, ids, method)
        for path in ("/build/1069540/steps", "/build/1069540/status",
                     "/build/1069540/dependencies", "/build/1069540/changes",
                     "/build/1069540/log", "/build/1069532/log",
                     "/build/1069540/step_status/", "/build/1069540/overview/",
                     "/build/1069541/step_status", "/build/1069540/rerun",
                     "/build/1069540/cancel", "/build/1069540?0-run",
                     "/wicket/page?0-1.ILinkListener-run", "/rest/builds/1069540"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                check_page_url(BASE + path, BASE, ids)

    def test_user_fields_redacted_without_changing_business_text(self) -> None:
        raw = ('<span><span>Welcome! <span>Alice &amp; Team</span></span></span>\n'
               '<table><tr><th>Status</th><th>Triggered By</th><th>SR_STATUS</th></tr>\n'
               '<tr><td>Successful</td><td><a href="/user/alice">alice (Alice)</a></td>'
               '<td>ACCEPTED</td></tr></table>\n<p>RepoAlice@abc</p>')
        safe = PageRedactor("", "", "SID=fixture-only").redact(raw)
        self.assertNotIn('Team', safe)
        self.assertNotIn('/user/alice', safe)
        self.assertNotIn('alice (Alice)', safe)
        self.assertEqual(safe.count('&lt;USER&gt;'), 2)
        for value in ('Successful', 'ACCEPTED', 'RepoAlice@abc', 'Triggered By'):
            self.assertIn(value, safe)
        self.assertEqual(safe.count('\n'), raw.count('\n'))
        self.assertEqual(PageRedactor("", "", "SID=fixture-only").redact(safe), safe)
        parsed = PageInventory()
        parsed.feed(safe)
        self.assertEqual(sum(line.count('<USER>') for line in parsed.lines), 2)

    def test_user_fields_key_value_and_missing_column(self) -> None:
        raw = ('<div>Welcome! Bob</div><table><tr><td>Triggered By</td><td>bob</td>'
               '</tr></table><table><tr><th>Status</th></tr><tr><td>BobRepo</td></tr>'
               '</table>')
        safe = PageRedactor("", "", "SID=fixture-only").redact(raw)
        self.assertEqual(safe.count('&lt;USER&gt;'), 2)
        self.assertIn('BobRepo', safe)

    def test_explicit_paths_do_not_expand_via_links(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = WebProbe(BASE, Path(d) / "out", "SID=fixture-only", {"1069532"})

            def get(name, path, auth):
                text = '<a href="/build/1069532/overview">Overview</a>'
                (p.output / (name + ".response.txt")).write_text(text)
                return HttpResponse(200, BASE + path, text.encode())

            with patch.object(p, "get", side_effect=get) as fetch:
                self.assertEqual(p.inspect_build("1069532", ("/build/1069532/step_status",),
                                                 follow_links=False), 'READ_PAGES_COLLECTED')
            self.assertEqual([call.args[1] for call in fetch.call_args_list],
                             ['/build/1069532/step_status'])

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
