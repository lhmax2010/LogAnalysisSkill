"""Offline-only controls for fixed-order, cookie-file EF-5 observation."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from ef5_web_probe import (
    COOKIE_READ_PATHS,
    CookieFileProbe,
    PageRedactor,
    _CookieStop,
    select_read_link,
)

BASE = "https://quickbuild.tizen.org"
SECRET = "fixture-cookie-keep-private-987654"
HTML = "<html><title>QuickBuild build</title><p>Successful</p></html>"


class Response(io.BytesIO):
    def __init__(self, text=HTML, status=200, location=""):
        super().__init__(text.encode())
        self.code = status
        self.headers = Message()
        self.headers.add_header("Content-Type", "text/html")
        self.headers.add_header("Set-Cookie", "SID=server-session-private-987654; HttpOnly")
        if location:
            self.headers.add_header("Location", location)


class CookieProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cookie_file = self.root / "cookie.json"
        self.cookie_file.write_text(json.dumps([
            {"name": "SID", "value": SECRET, "domain": "quickbuild.tizen.org"},
        ]))
        self.cookie_file.chmod(0o644)
        self.archive = self.root / "archive/page.response.txt"
        self.archive.parent.mkdir()
        self.write_archive('<a href="../overview/1921">Configuration Overview</a>')
        self.probe = CookieFileProbe(self.root / "out")
        self.stdout = io.StringIO()

    def write_archive(self, text):
        self.archive.write_text(text)
        (self.archive.parent / "requests.json").write_text(json.dumps([{
            "response": self.archive.name,
            "redacted_sha256": hashlib.sha256(self.archive.read_bytes()).hexdigest(),
        }]))

    def run_probe(self):
        with contextlib.redirect_stdout(self.stdout), contextlib.redirect_stderr(self.stdout):
            code = self.probe.run(self.cookie_file, self.archive)
        self.assert_private()
        return code, json.loads((self.probe.output / "run.json").read_text())

    def assert_private(self):
        evidence = self.stdout.getvalue() + "".join(
            p.read_text() for p in self.probe.output.glob("*") if p.is_file()
        )
        for secret in (SECRET, "server-session-private-987654", "hidden-private-987654",
                       "script-session-private-987654", "Alice Private", "alice-private"):
            self.assertNotIn(secret, evidence)
        self.assertNotIn("Set-Cookie", evidence)

    def test_file_loader_privacy_order_permissions_and_conditional_pages(self):
        before = self.cookie_file.read_bytes()
        body = (
            '<html><div>Welcome! Alice Private</div>'
            '<table><tr><td>Triggered By</td><td>alice-private</td></tr></table>'
            f'<p>{SECRET} server-session-private-987654</p>'
            '<input type="hidden" value="hidden-private-987654">'
            '<script>var sessionId = "script-session-private-987654";</script>'
            '<a href="/log">Log</a><a href="/run">Run the configuration</a></html>'
        )
        responses = [Response(body) for _ in COOKIE_READ_PATHS] + [
            Response('<a href="../variables/1921">Variables</a>'), Response(),
        ]
        from tizen_ci_shared.quickbuild_http import load_cookie_jar

        with patch("ef5_web_probe.load_cookie_jar", wraps=load_cookie_jar) as load, \
                patch.object(self.probe.opener, "open", side_effect=responses) as send:
            code, run = self.run_probe()
        load.assert_called_once_with(self.cookie_file)
        self.assertEqual(code, 0)
        self.assertEqual(run["cookie_file_mode"], "0644")
        self.assertEqual(run["requests"], 8)
        self.assertEqual(run["post_requests"], 0)
        self.assertEqual(run["redaction_self_check"], "PASS")
        expected = [BASE + path for path in COOKIE_READ_PATHS]
        expected += [BASE + "/overview/1921", BASE + "/variables/1921"]
        self.assertEqual([call.args[0].full_url for call in send.call_args_list], expected)
        for call in send.call_args_list:
            request = call.args[0]
            self.assertEqual(request.get_method(), "GET")
            self.assertEqual(request.get_header("Cookie"), f"SID={SECRET}")
            self.assertIsNone(request.get_header("Authorization"))
        self.assertEqual(self.cookie_file.read_bytes(), before)
        self.assertIn("&lt;USER&gt;", (self.probe.output / "01.response.txt").read_text())

    def test_outside_allowlist_or_wicket_never_calls_network(self):
        paths = (
            "/build/1069532", "/build/1069541", "/build/1069540/log", "/rest/version",
            "/build/1069540?0-1.ILinkListener-run", "/build/1069540?",
            "/build/1069540#x", "/wicket/page", "/overview/1921",
            "/build/1069540/../run", "/build/1069540%3Frun",
        )
        with patch.object(self.probe.opener, "open") as send:
            for path in paths:
                with self.subTest(path=path), self.assertRaises((_CookieStop, ValueError)):
                    self.probe.read_page(BASE + path)
            for method in ("POST", "PUT", "DELETE", "HEAD"):
                with self.subTest(method=method), self.assertRaises((_CookieStop, ValueError)):
                    self.probe.check_url(BASE + COOKIE_READ_PATHS[0], method)
            send.assert_not_called()

    def test_crlf_response_is_verified_as_bytes_without_normalizing_newlines(self):
        body = "<html>\r\n<p>Successful</p>\r\n</html>\r\n"
        self.write_archive("<span>TRIGGER</span>")
        responses = [Response(body) for _ in COOKIE_READ_PATHS]
        with patch.object(self.probe.opener, "open", side_effect=responses):
            code, run = self.run_probe()
        self.assertEqual(code, 0)
        self.assertEqual(run["requests"], 6)
        saved = (self.probe.output / "01.response.txt").read_bytes()
        self.assertEqual(saved, body.encode())
        self.assertEqual(self.probe.records[0]["redacted_sha256"],
                         hashlib.sha256(saved).hexdigest())

    def test_credential_in_url_rejected_before_send(self):
        self.probe._load_cookie(self.cookie_file)
        url = BASE + "/overview/" + SECRET
        self.probe.allowed.add(url)
        with patch.object(self.probe.opener, "open") as send, self.assertRaises(_CookieStop):
            self.probe.read_page(url)
        send.assert_not_called()

    def test_configuration_unsafe_links_not_followed(self):
        for href in ("../wicket/page?1.ILinkListener-variables", "../overview/1921?",
                     "../IBehaviorListener/1921", "/run/1921", "/accept/1921",
                     "/log", "/rest/version", "https://other.invalid/overview/1921",
                     "../overview/1921%3frun", "javascript:alert(1)"):
            with self.subTest(href=href):
                item = select_read_link(
                    f'<a href="{href}">Configuration Overview</a>',
                    BASE + "/build/1069532", "configuration overview",
                )
                self.assertEqual(item["decision"], "NOT_FOLLOWED")
        self.write_archive('<a href="../wicket/page?1-run">Configuration Overview</a>')
        with patch.object(self.probe.opener, "open",
                          side_effect=[Response() for _ in COOKIE_READ_PATHS]) \
                as send:
            code, run = self.run_probe()
        self.assertEqual((code, send.call_count), (0, 6))
        self.assertEqual(run["configuration_links"][0]["decision"], "NOT_FOLLOWED")

    def test_variables_action_not_followed_and_no_path_guessed(self):
        responses = [Response() for _ in COOKIE_READ_PATHS]
        responses.append(Response('<a href="../wicket/page?1-variables">Variables</a>'))
        with patch.object(self.probe.opener, "open", side_effect=responses) as send:
            code, run = self.run_probe()
        self.assertEqual((code, send.call_count), (0, 7))
        self.assertEqual(run["configuration_links"][1]["decision"], "NOT_FOLLOWED")

    def test_missing_or_ambiguous_configuration_link_not_guessed(self):
        for html in (
            '<title>root/SBS/TRIGGER</title><span>TRIGGER</span>',
            '<a href="/overview/1">Configuration Overview</a>'
            '<a href="/overview/2">Configuration Overview</a>',
        ):
            self.assertEqual(select_read_link(html, BASE, "configuration overview")["decision"],
                             "NOT_FOLLOWED")

    def test_cookie_load_failure_has_no_requests_or_exception_text(self):
        self.cookie_file.write_text(SECRET)
        with patch.object(self.probe.opener, "open") as send:
            code, run = self.run_probe()
        send.assert_not_called()
        self.assertEqual(code, 4)
        self.assertEqual(run["diagnostic"], {
            "stage": "cookie_load", "page_index": None,
            "error_category": "COOKIE_UNREADABLE", "http_status": None,
        })

    def test_missing_cookie_is_diagnostic(self):
        self.cookie_file.unlink()
        code, run = self.run_probe()
        self.assertEqual(code, 4)
        self.assertEqual(run["diagnostic"]["error_category"], "COOKIE_MISSING")
        self.assertEqual(run["requests"], 0)

    def test_network_failure_reports_page_index_without_raw_error(self):
        with patch.object(self.probe.opener, "open", side_effect=[Response(), URLError(SECRET)]):
            code, run = self.run_probe()
        self.assertEqual(code, 4)
        self.assertEqual(run["diagnostic"], {
            "stage": "fetch", "page_index": 2,
            "error_category": "TRANSPORT_ERROR", "http_status": None,
        })
        self.assertEqual(run["requests"], 2)

    def test_login_page_stops_all_followup_and_is_not_archived(self):
        login = Response(f'<html><input type="password">{SECRET}</html>')
        with patch.object(self.probe.opener, "open", side_effect=[Response(), login]) as send:
            code, run = self.run_probe()
        self.assertEqual((code, send.call_count), (4, 2))
        self.assertEqual(run["diagnostic"], {
            "stage": "login_check", "page_index": 2,
            "error_category": "COOKIE_EXPIRED", "http_status": 200,
        })
        self.assertFalse((self.probe.output / "02.response.txt").exists())

    def test_http_error_body_not_archived(self):
        with patch.object(self.probe.opener, "open", return_value=Response(SECRET, 500)):
            code, run = self.run_probe()
        self.assertEqual(code, 4)
        self.assertEqual(run["diagnostic"]["stage"], "fetch")
        self.assertEqual(run["diagnostic"]["http_status"], 500)
        self.assertFalse(list(self.probe.output.glob("*.response.txt")))

    def test_permission_denial_stops(self):
        response = Response("AccessDeniedException")
        with patch.object(self.probe.opener, "open", return_value=response):
            code, run = self.run_probe()
        self.assertEqual(code, 4)
        self.assertEqual(run["diagnostic"]["error_category"], "ACCESS_DENIED")
        self.assertEqual(run["requests"], 1)

    def test_redirect_to_login_never_followed(self):
        response = Response("", 302, "/signin")
        error = HTTPError(BASE, 302, "private error " + SECRET, response.headers, response)
        with patch.object(self.probe.opener, "open", side_effect=error) as send:
            code, run = self.run_probe()
        self.assertEqual((code, send.call_count), (4, 1))
        self.assertEqual(run["diagnostic"]["error_category"], "COOKIE_EXPIRED")
        self.assertEqual(run["redirects_followed"], 0)
        handler = next(h for h in self.probe.opener.handlers if hasattr(h, "redirect_request"))
        self.assertIsNone(handler.redirect_request(None, None, 302, "", {}, BASE))

    def test_redact_failure_sanitizes_diagnostic(self):
        with patch.object(self.probe.opener, "open", return_value=Response()), \
                patch.object(PageRedactor, "redact", side_effect=ValueError(SECRET)):
            code, run = self.run_probe()
        self.assertEqual(code, 4)
        self.assertEqual(run["diagnostic"]["stage"], "redact")
        self.assertEqual(run["diagnostic"]["error_category"], "REDACTION_FAILED")
        self.assertFalse(list(self.probe.output.glob("*.response.txt")))

    def test_write_failure_sanitizes_diagnostic(self):
        write = self.probe._write

        def fail_page(path, text):
            if path.name.endswith(".response.txt"):
                raise OSError(SECRET)
            write(path, text)

        with patch.object(self.probe.opener, "open", return_value=Response()), \
                patch.object(self.probe, "_write", side_effect=fail_page):
            code, run = self.run_probe()
        self.assertEqual(code, 4)
        self.assertEqual(run["diagnostic"]["stage"], "write")
        self.assertEqual(run["diagnostic"]["error_category"], "WRITE_FAILED")

    def test_archival_provenance_must_match(self):
        self.archive.write_text("tampered")
        with patch.object(self.probe.opener, "open",
                          side_effect=[Response() for _ in COOKIE_READ_PATHS]):
            code, run = self.run_probe()
        self.assertEqual(code, 4)
        self.assertEqual(run["diagnostic"]["error_category"], "ARCHIVE_HASH_MISMATCH")

    def test_second_run_exact_allowlist_and_iframe_external_links_never_followed(self):
        self.assertEqual(COOKIE_READ_PATHS, (
            "/build/1069540", "/build/1069540/overview", "/build/1069540/variables",
            "/build/1069540/step_status", "/build/1069540/html_report",
            "/build/1069532/step_status",
        ))
        body = (
            f'<iframe src="https://download.tizen.org/report?session={SECRET}"></iframe>'
            '<iframe src="/log"></iframe>'
            '<a href="https://download.tizen.org/report">External report</a>'
            '<a href="/build/1069540?2.ILinkListener-run">Run the configuration</a>'
        )
        self.write_archive("<span>TRIGGER</span>")
        responses = [Response(body) for _ in COOKIE_READ_PATHS]
        with patch.object(self.probe.opener, "open", side_effect=responses) as send:
            code, run = self.run_probe()
        self.assertEqual((code, send.call_count, run["post_requests"]), (0, 6, 0))
        page = json.loads((self.probe.output / "05.page.json").read_text())
        self.assertEqual(len(page["iframes"]), 2)
        self.assertTrue(all(row["decision"] == "NOT_FOLLOWED" for row in page["iframes"]))
        self.assertTrue(all(row["decision"] == "NOT_FOLLOWED" for row in page["links"]))

    def test_other_configuration_is_not_authorized_by_an_ordinary_link(self):
        self.write_archive('<a href="../overview/1922">Configuration Overview</a>')
        with patch.object(self.probe.opener, "open",
                          side_effect=[Response() for _ in COOKIE_READ_PATHS]) as send:
            code, run = self.run_probe()
        self.assertEqual((code, send.call_count), (0, 6))
        self.assertEqual(run["configuration_links"][0]["decision"], "NOT_FOLLOWED")
        self.assertEqual(run["configuration_links"][0]["reason"],
                         "CONFIGURATION_NOT_APPROVED")


if __name__ == "__main__":
    unittest.main()
