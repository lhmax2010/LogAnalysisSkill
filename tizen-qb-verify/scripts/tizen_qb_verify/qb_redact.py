"""QuickBuild evidence redaction, ported from the offline EF-5 page/form probes."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

MASK = "&lt;REDACTED&gt;"
SECRET_NAME = re.compile(
    r"password|passwd|secret|token|credential|authorization|cookie|session|csrf|xsrf",
    re.I,
)
SECRET_VALUE = re.compile(
    r"""(?ix)[\w-]*(?:token|csrf|xsrf|session)[\w-]*["']?\s*[:=]\s*
    (?:"([^"]*)"|'([^']*)'|([^?&;\s<>"'`)\]}]+))"""
)
VALUE_ATTR = re.compile(r"""(?is)(\svalue\s*=\s*)(?:"[^"]*"|'[^']*'|[^\s>]+)""")
HEADERS = re.compile(r"(?im)^\s*(?:set-cookie|cookie|authorization)\s*:[^\r\n]*")


def _identity_pattern(value: str) -> re.Pattern[str]:
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(value) + r"(?![A-Za-z0-9_])")


class EvidenceRedactionError(ValueError):
    code = "QB_EVIDENCE_REDACTION_FAILED"


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
    user_columns: set[int] = field(default_factory=set)


class _UserFields(HTMLParser):
    """Locate identity-bearing HTML spans without replacing names in business fields."""

    def __init__(self, source: str) -> None:
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
        if tag not in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }:
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
                labels = ["".join(cell.text).strip() for cell in table.cells]
                if any(cell.tag == "th" for cell in table.cells):
                    table.user_columns = {
                        index for index, cell in enumerate(table.cells)
                        if cell.tag == "th" and labels[index] in {"Triggered By", "Requested By"}
                    }
                for index, cell in enumerate(table.cells):
                    if cell.tag == "th" and labels[index] in {"Triggered By", "Requested By"}:
                        table.user_columns.add(index)
                    elif cell.tag == "td" and index in table.user_columns:
                        self.spans.append((cell.start, cell.end))
                    elif labels[index] == "Triggered By" and index + 1 < len(table.cells):
                        cell = table.cells[index + 1]
                        self.spans.append((cell.start, cell.end))
            if tag == "table":
                self.tables.pop()
        if tag in self.tags:
            del self.tags[len(self.tags) - 1 - self.tags[::-1].index(tag) :]


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


class _Fields(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__()
        self.offsets = [0]
        for line in source.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.hidden: list[tuple[int, str]] = []
        self.secrets: set[str] = set()
        self.invalid_hidden = False
        self.feed(source)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        name = a.get("name") or ""
        recorder = name.split(":")[-2:] == ["palette", "recorder"]
        sensitive = bool(SECRET_NAME.search(name + (a.get("id") or "")))
        if tag == "input":
            hidden = (a.get("type") or "").lower() in {"hidden", "password"}
            if hidden and not recorder:
                line, col = self.getpos()
                self.hidden.append((self.offsets[line - 1] + col, self.get_starttag_text() or ""))
                self.secrets.add(a.get("value") or "")
                if "value" in a and a["value"] != "<REDACTED>":
                    self.invalid_hidden = True
            if sensitive or (a.get("type") or "").lower() == "password":
                self.secrets.add(a.get("value") or "")
        if tag == "meta" and sensitive:
            self.secrets.add(a.get("content") or "")
        for key, value in attrs:
            if key not in {"name", "id"} and SECRET_NAME.search(key):
                self.secrets.add(value or "")


class _Text(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.feed(source)

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


class PageRedactor:
    def __init__(self) -> None:
        self.secrets: set[str] = set()
        self.identities: set[str] = set()
        # Per checked document, not cumulative; callers can record this number in trace.
        self.identity_outside_registered_count = 0

    def _remember(self, value: str) -> None:
        if value and unescape(value) not in {"<REDACTED>", "<USER>"}:
            self.secrets.update(
                {
                    value,
                    escape(value),
                    quote(value, safe=""),
                    json.dumps(value, ensure_ascii=False)[1:-1],
                }
            )

    def redact(self, text: str) -> str:
        users = _UserFields(text)
        users.feed(text)
        for start, end in users.spans:
            identity = "".join(_Text(text[start:end]).parts).strip()
            if identity and identity != "<USER>":
                self.identities.add(identity)
        text = redact_user_fields(text)
        text = HEADERS.sub(MASK, text)
        fields = _Fields(text)
        for value in fields.secrets:
            self._remember(value)
        for match in SECRET_VALUE.finditer(unescape(text)):
            self._remember(next(value for value in match.groups() if value is not None))
        # Mask hidden attributes first, including empty values; scrub their copies globally below.
        for start, raw_tag in reversed(fields.hidden):
            tag = VALUE_ATTR.sub(lambda m: m[1] + '"' + MASK + '"', raw_tag)
            text = text[:start] + tag + text[start + len(raw_tag) :]
        for value in sorted(self.secrets, key=len, reverse=True):
            text = text.replace(value, MASK)
        # The post-write contract excludes the cookie assignment itself, not just its value.
        text = re.sub(r"(?i)JSESSIONID_8810\s*=", "redacted_session:", text)
        self.check_bytes(text.encode("utf-8"))
        return text

    def check_bytes(self, raw: bytes) -> None:
        text = raw.decode("utf-8")
        decoded = unescape(text)
        visible = text.replace(MASK, "").replace("<REDACTED>", "")
        fields = _Fields(text)
        users = _UserFields(text)
        users.feed(text)
        if (
            b"jsessionid_8810=" in raw.lower()
            or any(value in visible for value in self.secrets)
            or HEADERS.search(text)
            or fields.invalid_hidden
            or any(value not in {"", "<REDACTED>"} for value in fields.secrets)
            or any(
                "".join(_Text(text[start:end]).parts).strip() not in {"", "<USER>"}
                for start, end in users.spans
            )
        ):
            raise EvidenceRedactionError("evidence redaction self-check failed")
        for match in SECRET_VALUE.finditer(decoded):
            value = next(value for value in match.groups() if value is not None)
            if value not in {"<REDACTED>", ""}:
                raise EvidenceRedactionError("evidence redaction self-check failed")
        outside = text
        for start, end in sorted(set(users.spans), reverse=True):
            outside = outside[:start] + "\0" + outside[end:]
        outside = unescape(outside)
        self.identity_outside_registered_count = sum(
            len(_identity_pattern(identity).findall(outside)) for identity in self.identities
        )

    def check_written(self, path: Path) -> None:
        """Inspect raw bytes, deleting the evidence on failure without echoing its contents."""
        try:
            self.check_bytes(path.read_bytes())
        except (ValueError, OSError):
            path.unlink(missing_ok=True)
            raise EvidenceRedactionError("evidence redaction self-check failed") from None
