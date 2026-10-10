"""Cookie-only, GET-only EF-5 HTML observation; never execute page actions."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, build_opener

from ef5_probe import MASK, MAX_BODY, NoRedirect, Probe, Redactor, cookie_values
from tizen_ci_shared.quickbuild_http import (
    DEFAULT_COOKIE_PATH,
    DEFAULT_QUICKBUILD_BASE_URL,
    HttpResponse,
    QuickBuildError,
    _raise_if_login_page,
    load_cookie_jar,
)

READ_PAGE = re.compile(
    r"/build/([0-9]+)(?:/(?:overview|status|variables|steps|dependencies|changes))?/?"
)
EXTRA_READ_PATHS = frozenset({
    "/build/1069540", "/build/1069540/overview", "/build/1069540/variables",
    "/build/1069532/step_status", "/build/1069540/step_status",
})
COOKIE_READ_PATHS = (
    "/build/1069540", "/build/1069540/overview", "/build/1069540/variables",
    "/build/1069540/step_status", "/build/1069540/html_report", "/build/1069532/step_status",
)
COOKIE_CONFIG_PATH = "/overview/1921"
CONFIG_ARCHIVE = (
    Path(__file__).resolve().parents[1]
    / "dev_memory/stage15_p1_ef_spike/evidence/web-browser-01"
    / "build-1069532-01.response.txt"
)
SECRET_NAME = re.compile(
    r"password|passwd|secret|token|credential|authorization|cookie|session|csrf|xsrf", re.I
)


def check_page_url(url: str, base_url: str, build_ids: set[str], method: str = "GET") -> None:
    parts, base = urlsplit(url), urlsplit(base_url)
    match = READ_PAGE.fullmatch(parts.path)
    extra = parts.path in EXTRA_READ_PATHS
    build_id = parts.path.split("/")[2] if extra else (match[1] if match else None)
    # The new child receives only its four explicitly authorized paths, not every old tab.
    allowed = extra or (match is not None and build_id != "1069540")
    if (
        method != "GET" or parts.scheme != "https" or parts.netloc != base.netloc
        or parts.username or parts.query or parts.fragment or not allowed
        or build_id not in build_ids
        or "?" in url or "#" in url
    ):
        raise ValueError("outside the explicit read-only build-page allowlist")


@dataclass
class _UserCell:
    tag: str
    start: int
    end: int = 0
    text: list[str] = field(default_factory=list)


@dataclass
class _UserTable:
    cells: list[_UserCell] = field(default_factory=list)
    active: _UserCell | None = None
    user_column: int | None = None


class _UserFields(HTMLParser):
    """Locate identity-bearing HTML spans without replacing names in business fields."""

    def __init__(self, source: str):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.offsets = [0]
        for line in source.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.tags: list[str] = []
        self.tables: list[_UserTable] = []
        self.spans: list[tuple[int, int]] = []
        self.welcome: tuple[int, int] | None = None

    def source_offset(self) -> int:
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.tables.append(_UserTable())
        if self.tables:
            table = self.tables[-1]
            if tag == "tr":
                table.cells = []
            if tag in {"th", "td"}:
                raw_tag = self.get_starttag_text()
                if raw_tag is None:
                    raise ValueError("Missing HTML source tag")
                table.active = _UserCell(tag, self.source_offset() + len(raw_tag))
                table.cells.append(table.active)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input",
                       "link", "meta", "param", "source", "track", "wbr"}:
            self.tags.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if self.tables and self.tables[-1].active is not None:
            self.tables[-1].active.text.append(data)
        greeting = re.match(r"\s*Welcome!\s*", data)
        if greeting and self.tags and self.tags[-1] in {"span", "div"}:
            self.welcome = (len(self.tags), self.source_offset() + greeting.end())

    def handle_entityref(self, name: str) -> None:
        self.handle_data(unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        self.handle_data(unescape(f"&#{name};"))

    def handle_endtag(self, tag: str) -> None:
        if self.welcome and len(self.tags) == self.welcome[0] and self.tags[-1] == tag:
            self.spans.append((self.welcome[1], self.source_offset()))
            self.welcome = None
        if self.tables:
            table = self.tables[-1]
            if tag in {"td", "th"} and table.active is not None:
                table.active.end = self.source_offset()
                table.active = None
            if tag == "tr":
                labels = [" ".join("".join(cell.text).split()) for cell in table.cells]
                if "Triggered By" in labels:
                    index = labels.index("Triggered By")
                    if table.cells[index].tag == "th":
                        table.user_column = index
                    elif index + 1 < len(table.cells):
                        cell = table.cells[index + 1]
                        self.spans.append((cell.start, cell.end))
                elif table.user_column is not None and table.user_column < len(table.cells):
                    cell = table.cells[table.user_column]
                    if cell.tag == "td":
                        self.spans.append((cell.start, cell.end))
            if tag == "table":
                self.tables.pop()
        if tag in self.tags:
            del self.tags[len(self.tags) - 1 - self.tags[::-1].index(tag):]


def redact_user_fields(text: str) -> str:
    parsed = _UserFields(text)
    parsed.feed(text)
    for start, end in sorted(set(parsed.spans), reverse=True):
        if end < start:
            raise ValueError("Invalid user field span")
        # Keep evidence source line numbers stable; HTML escapes render literally as <USER>.
        replacement = "&lt;USER&gt;" + "\n" * text[start:end].count("\n")
        text = text[:start] + replacement + text[end:]
    return text


class PageInventory(HTMLParser):
    """Extract evidence from sanitized HTML only; do not fetch or execute anything."""

    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []
        self.links: list[dict[str, object]] = []
        self.frames: list[dict[str, object]] = []
        self.inputs: list[dict[str, object]] = []
        self.secret_values: list[str] = []
        self.link: dict[str, object] | None = None
        self.skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {key.lower(): value or "" for key, value in attrs}
        if tag in {"script", "style"}:
            self.skip += 1
        if tag == "input":
            hidden = a.get("type", "").lower() in {"hidden", "password"}
            sensitive = SECRET_NAME.search(a.get("name", "") + a.get("id", ""))
            if hidden or sensitive:
                self.secret_values.append(a.get("value", ""))
            self.inputs.append({"line": self.getpos()[0], "name": a.get("name"),
                                "type": a.get("type"), "value": a.get("value")})
        if tag == "meta" and SECRET_NAME.search(a.get("name", "")):
            self.secret_values.append(a.get("content", ""))
        for key, value in a.items():
            if SECRET_NAME.search(key) and key not in {"name", "id"}:
                self.secret_values.append(value)
        if tag == "a":
            self.link = {"line": self.getpos()[0], "href": a.get("href"), "text": ""}
            self.links.append(self.link)
        if tag == "iframe":
            self.frames.append({"line": self.getpos()[0], "src": a.get("src"),
                                "decision": "NOT_FOLLOWED"})

    def handle_data(self, data: str) -> None:
        if self.skip:
            return
        value = " ".join(data.split())
        if value:
            self.lines.append(f"{self.getpos()[0]}: {value}")
            if self.link is not None:
                self.link["text"] = str(self.link["text"]) + value + " "

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.skip = max(0, self.skip - 1)
        if tag == "a":
            self.link = None


class PageRedactor(Redactor):
    def redact(self, text: str) -> str:
        text = redact_user_fields(text)
        parsed = PageInventory()
        parsed.feed(text)
        for value in parsed.secret_values:
            self.remember(value)
        # Session/CSRF values also occur in JavaScript and URLs, outside form inputs.
        for pattern in (
            r'''(?i)[\w-]*(?:session|csrf|xsrf)[\w-]*["'\s]*[:=]\s*["']([^"'<>\r\n]+)''',
            r'''(?i)(?:;jsessionid=|[?&](?:session[\w-]*|csrf[\w-]*|xsrf[\w-]*)=)([^&#\s"'<>]+)''',
        ):
            for match in re.finditer(pattern, text):
                self.remember(match[1])
        redacted = super().redact(text)
        checked = PageInventory()
        checked.feed(redacted)
        if any(value and value != MASK for value in checked.secret_values):
            raise ValueError("HTML sensitive-field self-check failed; no evidence written")
        return redacted


class WebProbe(Probe):
    def __init__(self, base_url: str, output: Path, cookie: str, build_ids: set[str]):
        if not cookie or "\r" in cookie or "\n" in cookie:
            raise ValueError("a nonempty single-line Cookie header is required")
        self.build_ids = build_ids
        super().__init__(base_url, output, "", "", cookie)
        self.redactor = PageRedactor("", "", cookie)

    def check_url(self, url: str) -> None:
        check_page_url(url, self.base_url, self.build_ids)

    def inspect_build(
        self, build_id: str, paths: tuple[str, ...] | None = None, *, follow_links: bool = True,
    ) -> str:
        pending = [self.base_url + path for path in (paths or (f"/build/{build_id}",))]
        visited: set[str] = set()
        while pending:
            url = pending.pop(0)
            if url in visited:
                continue
            visited.add(url)
            name = f"build-{build_id}-{len(visited):02d}"
            response = self.get(name, url.removeprefix(self.base_url), "cookie")
            if response is None or response.status != 200:
                return "BLOCKED_HTTP_OR_REDIRECT"
            try:
                _raise_if_login_page(response, action="EF-5 read-only HTML inspection")
            except Exception:
                return "BLOCKED_LOGIN_PAGE"
            safe = (self.output / (name + ".response.txt")).read_text()
            parsed = PageInventory()
            parsed.feed(safe)
            visible = "\n".join(parsed.lines)
            if re.search(
                r"AccessDeniedException|access denied|permission denied|not authorized|"
                r"not allowed to access|please (?:log|sign) in", visible, re.I
            ):
                return "BLOCKED_PERMISSION_OR_LOGIN"
            if any(str(row.get("type", "")).lower() == "password" for row in parsed.inputs):
                return "BLOCKED_LOGIN_FORM"
            decisions: list[dict[str, object]] = []
            for link in parsed.links:
                href = link["href"]
                if not isinstance(href, str) or not href:
                    continue
                target = urljoin(url, href)
                try:
                    check_page_url(target, self.base_url, {build_id})
                    self.redactor.check(target)
                except ValueError:
                    decision = "NOT_FOLLOWED"
                else:
                    decision = "ALLOW_READ" if follow_links else "ALLOW_READ_NOT_FOLLOWED"
                    if follow_links and target not in visited and target not in pending:
                        pending.append(target)
                decisions.append({**link, "resolved_url": target, "decision": decision})
            self.save_json(self.output / (name + ".page.json"), {
                "url": url, "visible_text": parsed.lines, "links": decisions,
                "form_fields_metadata_only": parsed.inputs,
                "forms_submitted": 0, "javascript_executed": False,
            })
        return "READ_PAGES_COLLECTED"


def ordinary_page_url(href: str, page_url: str) -> str:
    """Only literal, same-origin page links may extend the cookie-run allowlist."""
    url = urljoin(page_url, href)
    parts, base = urlsplit(url), urlsplit(DEFAULT_QUICKBUILD_BASE_URL)
    if (
        not href or any(char in href for char in "?#%\\")
        or any(ord(char) < 33 for char in href)
        or re.search(r"ilinklistener|ibehaviorlistener|wicket", href, re.I)
        or parts.scheme != "https" or parts.netloc != base.netloc or parts.username
        or parts.query or parts.fragment
        or not re.fullmatch(r"/[A-Za-z0-9_./-]+", parts.path)
        or re.search(
            r"/(?:rest|log|run|trigger|accept|cancel|rerun|restart|retry|stop|delete|edit)"
            r"(?:[/._-]|$)", parts.path, re.I,
        )
    ):
        raise ValueError("NOT_FOLLOWED")
    return url


def select_read_link(text: str, page_url: str, label: str) -> dict[str, object]:
    parsed = PageInventory()
    parsed.feed(text)
    links = [link for link in parsed.links if str(link["text"]).strip().casefold() == label]
    if not links:
        return {"decision": "NOT_FOLLOWED", "reason": "NO_LITERAL_LINK"}
    # Multiple matching links are not a license to choose or to guess a route.
    targets = {(str(link["href"]), str(link["text"]).strip()) for link in links}
    if len(targets) != 1:
        return {"decision": "NOT_FOLLOWED", "reason": "AMBIGUOUS_LINK"}
    link = links[0]
    try:
        url = ordinary_page_url(str(link["href"] or ""), page_url)
    except ValueError:
        return {"decision": "NOT_FOLLOWED", "reason": "UNSAFE_LINK", "line": link["line"]}
    return {"decision": "ALLOW_READ", "line": link["line"], "url": url}


class _CookieStop(Exception):
    """Carry only a fixed category, never private exception text."""


class CookieFileProbe:
    """Single explicit run; no browser, password, redirect, retries or action API."""

    def __init__(self, output: Path):
        self.output = output
        self.redactor = PageRedactor("", "", "")
        self.cookie = ""
        self.cookie_mode: str | None = None
        self.opener = build_opener(NoRedirect())
        self.allowed = {DEFAULT_QUICKBUILD_BASE_URL + path for path in COOKIE_READ_PATHS}
        self.records: list[dict[str, object]] = []
        self.configuration: list[dict[str, object]] = []
        self.phase = "cookie_load"
        self.page_index: int | None = None
        self.http_status: int | None = None

    def _load_cookie(self, path: Path) -> None:
        try:
            self.cookie_mode = f"{stat.S_IMODE(path.stat().st_mode):04o}"
            values = load_cookie_jar(path)
            pairs = []
            for name, value in values.items():
                if any(char in name + value for char in "\r\n"):
                    raise ValueError("invalid cookie")
                cookie = SimpleCookie()
                cookie[name] = value
                pairs.append(cookie[name].OutputString())
            self.cookie = "; ".join(pairs)
            self.redactor = PageRedactor("", "", self.cookie)
            for value in values.values():
                self.redactor.remember(value)
        except FileNotFoundError:
            raise _CookieStop("COOKIE_MISSING") from None
        except QuickBuildError as exc:
            code = exc.code if exc.code in {
                "COOKIE_MISSING", "COOKIE_UNREADABLE", "COOKIE_EXPIRED",
            } else "COOKIE_LOAD_FAILED"
            raise _CookieStop(code) from None
        except Exception:
            raise _CookieStop("COOKIE_LOAD_FAILED") from None

    def check_url(self, url: str, method: str = "GET") -> None:
        if method != "GET" or ordinary_page_url(url, DEFAULT_QUICKBUILD_BASE_URL) != url:
            raise _CookieStop("URL_NOT_ALLOWED")
        if url not in self.allowed:
            raise _CookieStop("URL_NOT_ALLOWED")
        try:
            self.redactor.check(url)
        except ValueError:
            raise _CookieStop("CREDENTIAL_IN_URL") from None

    def _write(self, path: Path, text: str) -> None:
        self.redactor.check(text)
        path.write_text(text, encoding="utf-8")
        path.chmod(0o600)
        written = path.read_bytes().decode("utf-8")
        self.redactor.check(written)
        if written != text:
            raise ValueError("evidence verification failed")

    def _json(self, name: str, data: object) -> None:
        self._write(self.output / name, json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def _fetch(self, url: str) -> HttpResponse:
        self.check_url(url)
        record: dict[str, object] = {"page_index": self.page_index, "url": url, "method": "GET"}
        self.records.append(record)
        try:
            try:
                stream = self.opener.open(Request(url, headers={
                    "Cookie": self.cookie, "User-Agent": "LogAnalysisSkill-EF5-read-only/2",
                    "Accept": "text/html",
                }, method="GET"), timeout=30)
            except HTTPError as error:
                stream = error
            with stream:
                self.http_status = int(stream.code)
                record["status"] = self.http_status
                location = stream.headers.get("Location", "")
                if self.http_status in {301, 302, 303, 307, 308}:
                    if re.search(r"signin|login", location, re.I):
                        self.phase = "login_check"
                        raise _CookieStop("COOKIE_EXPIRED")
                    raise _CookieStop("REDIRECT_REFUSED")
                for header in stream.headers.get_all("Set-Cookie", []):
                    self.redactor.remember(header)
                    for value in cookie_values(header):
                        self.redactor.remember(value)
                body = stream.read(MAX_BODY + 1)
                if len(body) > MAX_BODY:
                    raise _CookieStop("RESPONSE_TOO_LARGE")
                return HttpResponse(self.http_status, url, body, "text/html")
        except _CookieStop:
            raise
        except Exception:
            raise _CookieStop("TRANSPORT_ERROR") from None

    def _login_check(self, response: HttpResponse) -> None:
        try:
            _raise_if_login_page(response, action="read-only cookie probe")
        except QuickBuildError:
            raise _CookieStop("COOKIE_EXPIRED") from None
        parsed = PageInventory()
        parsed.feed(response.text)
        if any(str(item.get("type", "")).lower() == "password" for item in parsed.inputs):
            raise _CookieStop("COOKIE_EXPIRED")
        visible = "\n".join(parsed.lines)
        if re.search(
            r"please (?:log|sign) in|sign in to quickbuild|login to quickbuild", visible, re.I,
        ):
            raise _CookieStop("COOKIE_EXPIRED")
        if re.search(r"AccessDeniedException|access denied|permission denied|not authorized|"
                     r"not allowed to access", visible, re.I):
            raise _CookieStop("ACCESS_DENIED")
        if response.status != 200:
            self.phase = "fetch"
            raise _CookieStop("HTTP_ERROR")

    def read_page(self, url: str) -> str:
        self.page_index = len(self.records) + 1
        self.http_status = None
        self.phase = "fetch"
        response = self._fetch(url)
        self.phase = "login_check"
        self._login_check(response)
        self.phase = "redact"
        safe = self.redactor.redact(response.text)
        self.redactor.check(safe)
        parsed = PageInventory()
        parsed.feed(safe)
        page = {
            "url": url, "visible_text": parsed.lines,
            "links": [{**link, "decision": "NOT_FOLLOWED"} for link in parsed.links],
            "iframes": parsed.frames,
            "form_fields_metadata_only": parsed.inputs,
            "forms_submitted": 0, "javascript_executed": False,
        }
        page_text = json.dumps(page, ensure_ascii=False, indent=2) + "\n"
        self.redactor.check(page_text)
        name = f"{self.page_index:02d}"
        self.phase = "write"
        self._write(self.output / f"{name}.response.txt", safe)
        self._write(self.output / f"{name}.page.json", page_text)
        self.records[-1].update({
            "response": f"{name}.response.txt", "page": f"{name}.page.json",
            "redacted_sha256": hashlib.sha256(safe.encode()).hexdigest(),
            "redaction_self_check": "PASS",
        })
        return safe

    def _configuration_pages(self, archive: Path) -> None:
        self.page_index = None
        self.http_status = None
        self.phase = "redact"
        raw = archive.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        records = json.loads((archive.parent / "requests.json").read_text())
        if not any(row.get("response") == archive.name and row.get("redacted_sha256") == digest
                   for row in records):
            raise _CookieStop("ARCHIVE_HASH_MISMATCH")
        text = raw.decode("utf-8")
        self.redactor.check(text)
        source_url = DEFAULT_QUICKBUILD_BASE_URL + "/build/1069532"
        decision = select_read_link(text, source_url, "configuration overview")
        if (decision["decision"] == "ALLOW_READ"
                and decision["url"] != DEFAULT_QUICKBUILD_BASE_URL + COOKIE_CONFIG_PATH):
            decision.update(decision="NOT_FOLLOWED", reason="CONFIGURATION_NOT_APPROVED")
        decision.update({"source": archive.name, "source_sha256": digest,
                         "purpose": "configuration"})
        self.configuration.append(decision)
        if decision["decision"] != "ALLOW_READ":
            return
        url = str(decision["url"])
        self.allowed.add(url)
        page = self.read_page(url)
        variables = select_read_link(page, url, "variables")
        variables.update({"source": f"{self.page_index:02d}.response.txt",
                          "purpose": "configuration_variables"})
        self.configuration.append(variables)
        if variables["decision"] == "ALLOW_READ":
            variable_url = str(variables["url"])
            if variable_url not in {row["url"] for row in self.records}:
                self.allowed.add(variable_url)
                self.read_page(variable_url)
            else:
                variables.update(decision="NOT_FOLLOWED", reason="ALREADY_READ")

    def run(self, cookie_file: Path, archive: Path = CONFIG_ARCHIVE) -> int:
        error: str | None = None
        self.phase = "write"
        self.output.mkdir(parents=True, exist_ok=False, mode=0o700)
        try:
            self.phase = "cookie_load"
            self._load_cookie(cookie_file)
            for path in COOKIE_READ_PATHS:
                self.read_page(DEFAULT_QUICKBUILD_BASE_URL + path)
            self._configuration_pages(archive)
        except _CookieStop as exc:
            error = str(exc)
        except (Exception, KeyboardInterrupt):
            error = {
                "cookie_load": "COOKIE_LOAD_FAILED", "fetch": "TRANSPORT_ERROR",
                "login_check": "LOGIN_CHECK_FAILED", "redact": "REDACTION_FAILED",
                "write": "WRITE_FAILED",
            }[self.phase]
        diagnostic = None if error is None else {
            "stage": self.phase, "page_index": self.page_index,
            "error_category": error, "http_status": self.http_status,
        }
        run = {
            "conclusion": "WEB_READ_PARTIAL" if error is None else "BLOCKED",
            "diagnostic": diagnostic, "exit_code": 0 if error is None else 4,
            "cookie_file_mode": self.cookie_mode, "cookie_stored": False,
            "auth_mode": "cookie_file_in_memory", "requests": len(self.records),
            "http_statuses": [row.get("status") for row in self.records],
            "post_requests": 0, "trigger_authorized": False, "redirects_followed": 0,
            "configuration_links": self.configuration,
        }
        try:
            self._json("requests.json", self.records)
            run["redaction_self_check"] = "PASS"
            self._json("run.json", run)
            for evidence_path in self.output.iterdir():
                self.redactor.check(evidence_path.read_text())
        except Exception:
            # If evidence storage itself fails, never print remote content or secret errors.
            print('BLOCKED stage=write error_category=EVIDENCE_WRITE_FAILED', flush=True)
            return 4
        print(json.dumps({key: run[key] for key in (
            "conclusion", "diagnostic", "requests", "http_statuses", "post_requests",
        )}), flush=True)
        return 0 if error is None else 4


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cookie-file", type=Path, default=DEFAULT_COOKIE_PATH)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return CookieFileProbe(args.output).run(args.cookie_file)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Exception, KeyboardInterrupt):
        # Never print exceptions containing raw remote content or private input.
        print("Web probe stopped; no action submitted. Inspect sanitized evidence if present.")
        sys.exit(2)
