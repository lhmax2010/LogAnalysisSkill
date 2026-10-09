"""Cookie-only, GET-only EF-5 HTML observation; never execute page actions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from ef5_probe import MASK, Probe, Redactor, read_secret
from tizen_ci_shared.quickbuild_http import DEFAULT_QUICKBUILD_BASE_URL, _raise_if_login_page

READ_PAGE = re.compile(
    r"/build/([0-9]+)(?:/(?:overview|status|variables|steps|dependencies|changes))?/?"
)
EXTRA_READ_PATHS = frozenset({
    "/build/1069540", "/build/1069540/overview", "/build/1069540/variables",
    "/build/1069532/step_status", "/build/1069540/step_status",
})
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-id", default="1069532")
    parser.add_argument("--trigger-id")
    parser.add_argument("--base-url", default=DEFAULT_QUICKBUILD_BASE_URL)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ids = [args.build_id, *([args.trigger_id] if args.trigger_id else [])]
    if any(re.fullmatch(r"[0-9]+", value) is None for value in ids):
        raise ValueError("build IDs must be numeric")
    print("GET-only build pages; no redirects, REST, scripts, forms or build actions.", flush=True)
    cookie = read_secret("QB_COOKIE")
    probe = WebProbe(args.base_url, args.output, cookie, set(ids))
    results: dict[str, str] = {}
    for build_id in ids:
        results[build_id] = probe.inspect_build(build_id)
        if results[build_id] != "READ_PAGES_COLLECTED":
            break
    code = 0 if all(value == "READ_PAGES_COLLECTED" for value in results.values()) else 4
    probe.finish({"builds": results, "exit_code": code,
                  "trigger_confirmation": "NOT_GRANTED", "cookie_stored": False,
                  "auth_mode": "cookie", "automatic_parent_inference": False})
    print(json.dumps({"results": results, "exit_code": code}), flush=True)
    return code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Exception, KeyboardInterrupt):
        # Never print exceptions containing raw remote content or private input.
        print("Web probe stopped; no action submitted. Inspect sanitized evidence if present.")
        sys.exit(2)
