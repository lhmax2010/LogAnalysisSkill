"""Read-only EF-5 probes; credentials stay in memory and evidence is redacted first."""

from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from tizen_ci_shared.quickbuild_http import (
    DEFAULT_QUICKBUILD_BASE_URL,
    HttpResponse,
    _raise_if_login_page,
    normalize_quickbuild_url,
)

SENSITIVE = re.compile(r"password|passwd|secret|token|credential|authorization|cookie", re.I)
READ_PATH = re.compile(
    r"/rest/(?:version|info|ids|builds/[0-9]+"
    r"(?:/(?:status|variables|steps|dependencies|request_id))?)|/build/[0-9]+/?"
)
MASK = "[REDACTED]"
MAX_BODY = 8 * 1024 * 1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


class SensitiveHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: list[str] = []
        self.cells: list[str] = []
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "input" and (
            attributes.get("type", "") in {"password", "hidden"}
            or SENSITIVE.search(attributes.get("name") or "")
        ):
            self.values.append(attributes.get("value") or "")
        if tag == "tr":
            self.cells = []
        if tag in {"th", "td"}:
            self.cell = []

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"th", "td"} and self.cell is not None:
            self.cells.append("".join(self.cell).strip())
            self.cell = None
        if tag == "tr" and self.cells and SENSITIVE.search(self.cells[0]):
            self.values.extend(self.cells[1:])


def cookie_values(value: str) -> list[str]:
    cookies = SimpleCookie()
    cookies.load(value)
    if value and not cookies:
        raise ValueError("QB_COOKIE must be a Cookie header: name=value; name2=value2")
    return [morsel.value for morsel in cookies.values()]


class Redactor:
    def __init__(self, username: str, password: str, cookie: str) -> None:
        self.secrets: set[str] = set()
        for value in (password, cookie, *cookie_values(cookie)):
            self.remember(value)
        if password:
            self.remember(base64.b64encode(f"{username}:{password}".encode()).decode())

    def remember(self, value: str) -> None:
        if not value or value == MASK:
            return
        self.secrets.update((value, html.escape(value), quote(value, safe="")))
        self.secrets.add(json.dumps(value, ensure_ascii=False)[1:-1])

    def collect_xml(self, text: str) -> None:
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            return
        for element in root.iter():
            if SENSITIVE.search(element.tag):
                for child in element.iter():
                    self.remember((child.text or "").strip())
            children = list(element)
            if len(children) >= 2 and SENSITIVE.search(children[0].text or ""):
                for child in children[1:]:
                    for descendant in child.iter():
                        self.remember((descendant.text or "").strip())
            for name, value in element.attrib.items():
                if SENSITIVE.search(name):
                    self.remember(value)

    def redact(self, text: str) -> str:
        self.collect_xml(text)
        parser = SensitiveHTML()
        parser.feed(text)
        for value in parser.values:
            self.remember(value)
        # Learn values before replacing them, including cookies supplied by the response.
        for match in re.finditer(
            r"(?i)(?:password|passwd|secret|token|credential|authorization|cookie)"
            r'[\w-]*["\s]*[:=]\s*["\']([^"\'<>\r\n]+)',
            text,
        ):
            self.remember(match.group(1))
        for match in re.finditer(
            r"(?i)(?:;jsessionid=|[?&](?:token|password|session)=)([^&#\s\"'<>]+)", text
        ):
            self.remember(match.group(1))
        for value in sorted(self.secrets, key=len, reverse=True):
            text = text.replace(value, MASK)
        self.check(text)
        return text

    def check(self, text: str) -> None:
        # Remove the marker itself so short credentials cannot falsely match its letters.
        visible = text.replace(MASK, "")
        if any(value in visible for value in self.secrets):
            raise ValueError("credential self-check failed; evidence not written")


def check_url(url: str, base_url: str) -> None:
    parts, base = urlsplit(url), urlsplit(base_url)
    if parts.scheme != "https" or parts.netloc != base.netloc or parts.username or parts.fragment:
        raise ValueError("probe permits only same-origin HTTPS URLs without userinfo or fragments")
    if READ_PATH.fullmatch(parts.path) is None:
        raise ValueError("URL is outside the read-only allowlist")
    if parts.query and parts.path != "/rest/ids":
        raise ValueError("query parameters are allowed only for configuration lookup")
    if parts.query and [key for key, _ in parse_qsl(parts.query)] != ["configuration_path"]:
        raise ValueError("configuration lookup requires configuration_path")


def response_shape(response: HttpResponse) -> str:
    if not response.body:
        return "empty"
    try:
        json.loads(response.text)
        return "json"
    except ValueError:
        pass
    try:
        root = ET.fromstring(response.text)
        return "xml:" + root.tag
    except ET.ParseError:
        return "html" if "<html" in response.text.lower() else "text"


def xml_fields(text: str) -> list[dict[str, str]]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    fields: list[dict[str, str]] = []

    def visit(element: ET.Element, path: str) -> None:
        for key, value in element.attrib.items():
            fields.append({"path": f"{path}/@{key}", "value": value})
        if not list(element):
            fields.append({"path": path, "value": element.text or ""})
        for index, child in enumerate(element):
            visit(child, f"{path}/{child.tag}[{index}]")

    visit(root, "/" + root.tag)
    return fields


class Probe:
    def __init__(self, base_url: str, output: Path, username: str, password: str, cookie: str):
        self.base_url = base_url.rstrip("/")
        self.output = output
        self.password, self.cookie, self.username = password, cookie, username
        self.redactor = Redactor(username, password, cookie)
        self.opener = build_opener(NoRedirect())
        self.records: list[dict[str, object]] = []
        output.mkdir(parents=True, exist_ok=False, mode=0o700)

    def save_json(self, path: Path, data: object) -> None:
        text = self.redactor.redact(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        path.write_text(text)
        path.chmod(0o600)

    def get(self, name: str, path: str, auth: str) -> HttpResponse | None:
        url = normalize_quickbuild_url(self.base_url + path)
        check_url(url, self.base_url)
        # Never put a known credential in a URL, even if entered as a non-secret field.
        self.redactor.check(url)
        headers = {"User-Agent": "LogAnalysisSkill-EF5-read-only/1", "Accept": "*/*"}
        if auth == "basic":
            if not self.password or not self.username:
                raise ValueError("Basic Auth requires a username and password")
            encoded = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            headers["Authorization"] = "Basic " + encoded
        elif auth == "cookie":
            if not self.cookie:
                raise ValueError("Cookie authentication was not supplied")
            headers["Cookie"] = self.cookie
        elif auth != "anonymous":
            raise ValueError("unsupported authentication mode")
        record: dict[str, object] = {"method": "GET", "url": url, "auth_mode": auth}
        try:
            try:
                stream = self.opener.open(Request(url, headers=headers, method="GET"), timeout=30)
            except HTTPError as error:
                stream = error
            with stream:
                for cookie_header in stream.headers.get_all("Set-Cookie", []):
                    self.redactor.remember(cookie_header)
                    for value in cookie_values(cookie_header):
                        self.redactor.remember(value)
                body = stream.read(MAX_BODY + 1)
                if len(body) > MAX_BODY:
                    raise ValueError("response exceeds evidence size limit; no partial evidence")
                response = HttpResponse(
                    status=stream.code,
                    url=stream.geturl(),
                    body=body,
                    content_type=stream.headers.get("Content-Type"),
                )
                # Never archive response headers en masse: Set-Cookie is a credential.
                record["location"] = stream.headers.get("Location")
                record["www_authenticate"] = stream.headers.get("WWW-Authenticate")
        except (OSError, URLError, ValueError) as error:
            record.update({"error_type": type(error).__name__, "error": str(error)})
            self.records.append(record)
            self.save_json(self.output / "requests.json", self.records)
            print(f"{name}: transport/error; see redacted requests.json", flush=True)
            return None
        redacted = self.redactor.redact(response.text)
        evidence = self.output / (name + ".response.txt")
        evidence.write_text(redacted)
        evidence.chmod(0o600)
        record.update(
            {
                "status": response.status,
                "content_type": response.content_type,
                "shape": self.redactor.redact(response_shape(response)),
                "response": evidence.name,
                "redacted_sha256": hashlib.sha256(redacted.encode()).hexdigest(),
                "redaction_self_check": "PASS",
            }
        )
        self.records.append(record)
        self.save_json(self.output / "requests.json", self.records)
        fields = xml_fields(redacted)
        if fields:
            self.save_json(self.output / (name + ".fields.json"), fields)
        print(
            f"{name}: HTTP {response.status}; {record['shape']}; evidence={evidence.name}",
            flush=True,
        )
        return response

    def build(self, build_id: str, label: str) -> None:
        if not re.fullmatch(r"[0-9]+", build_id):
            raise ValueError("build id must be numeric")
        if self.password:
            for suffix in ("", "/status", "/variables", "/steps", "/dependencies", "/request_id"):
                name = label + "-rest" + (suffix.replace("/", "-") if suffix else "")
                self.get(name, f"/rest/builds/{build_id}{suffix}", "basic")
        page = self.get(
            label + "-page", f"/build/{build_id}", "cookie" if self.cookie else "anonymous"
        )
        if page is not None:
            try:
                _raise_if_login_page(page, action="EF-5 read-only build inspection")
            except Exception:
                print(
                    f"{label}: shared login-page check failed; page is NOT build evidence",
                    flush=True,
                )

    def finish(self, inputs: Mapping[str, object]) -> None:
        self.save_json(
            self.output / "run.json",
            {
                "inputs": dict(inputs),
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "requests": len(self.records),
                "post_requests": 0,
                "trigger_authorized": False,
                "redaction_self_check": "PASS",
            },
        )
        for path in self.output.iterdir():
            if path.is_file():
                self.redactor.check(path.read_text())
        print("Evidence credential self-check: PASS. POST/trigger requests: 0.", flush=True)


def read_secret(name: str) -> str:
    value = os.environ.get(name, "")
    if value:
        return value
    if not sys.stdin.isatty():
        raise ValueError(
            f"{name} is unset: run in FatTank's terminal for getpass; do not paste in chat"
        )
    return getpass.getpass(f"{name} (hidden; Enter to leave unavailable): ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username")
    parser.add_argument("--configuration-path")
    parser.add_argument("--build-id")
    parser.add_argument("--trigger-id")
    parser.add_argument("--base-url", default=DEFAULT_QUICKBUILD_BASE_URL)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--anonymous-only", action="store_true")
    args = parser.parse_args()
    username = args.username or ""
    if not args.anonymous_only and not username:
        if not sys.stdin.isatty():
            raise ValueError("provide --username or run in an interactive terminal")
        username = input("QuickBuild username (not password): ").strip()
    password = "" if args.anonymous_only else read_secret("QB_PASSWORD")
    cookie = "" if args.anonymous_only else read_secret("QB_COOKIE")
    if not args.anonymous_only and sys.stdin.isatty():
        if not args.configuration_path:
            args.configuration_path = (
                input("Configuration path (Enter if unknown): ").strip() or None
            )
        if not args.build_id:
            args.build_id = input("Existing SBS build id (Enter if unknown): ").strip() or None
        if not args.trigger_id:
            args.trigger_id = (
                input("Its parent TRIGGER build id (Enter if unknown): ").strip() or None
            )
    probe = Probe(args.base_url, args.output, username, password, cookie)
    print("READ-ONLY: no build submission, trigger, cancellation or state mutation.", flush=True)
    probe.get("version-anonymous", "/rest/version", "anonymous")
    if password:
        version = probe.get("version-basic", "/rest/version", "basic")
        if version is None or version.status != 200:
            probe.finish({"rest_probe": "BLOCKED", "reason": "Basic Auth probe did not return 200"})
            print("REST probe blocked; no subsequent authenticated requests attempted.", flush=True)
            return 4
    if args.configuration_path:
        probe.get(
            "configuration-id",
            "/rest/ids?" + urlencode({"configuration_path": args.configuration_path}),
            "basic" if password else "cookie" if cookie else "anonymous",
        )
    if args.build_id:
        probe.build(args.build_id, "sbs")
    if args.trigger_id:
        probe.build(args.trigger_id, "trigger")
    probe.finish(
        {
            "base_url": args.base_url,
            "configuration_path": args.configuration_path,
            "build_id": args.build_id,
            "trigger_id": args.trigger_id,
            "password_available": bool(password),
            "cookie_available": bool(cookie),
        }
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, EOFError, KeyboardInterrupt):
        # No traceback or exception text: it could contain sensitive server input.
        print("Probe stopped; no submission was sent. Check terminal inputs or sanitized evidence.")
        raise SystemExit(2) from None
