"""Failed-build discovery sources for CI triage."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Protocol

from ci_triage.quickbuild import (
    DEFAULT_COOKIE_PATH,
    DEFAULT_QUICKBUILD_BASE_URL,
    HttpFetcher,
    QuickBuildError,
    _raise_if_login_page,
    _urllib_fetch,
    load_cookie_jar,
)

QUICKBUILD_OVERVIEW_CONFIG_ID = "1930"
_STATUS_CLASSES = frozenset({"failed", "successful", "cancelled"})


@dataclass(frozen=True)
class FailedBuild:
    """One failed build discovered from an upstream CI source."""

    source: str
    build_id: str
    version: str
    begin_date: datetime
    status: str
    quickbuild_url: str


class FailedBuildSource(Protocol):
    """Source abstraction for discovering recent failed builds."""

    def discover(self, since: datetime) -> list[FailedBuild]:
        """Return failed builds with begin_date at or after since."""
        ...


@dataclass
class QuickBuildSource:
    """Discover failed builds from QuickBuild's static overview table."""

    cookie_path: Path = DEFAULT_COOKIE_PATH
    base_url: str = DEFAULT_QUICKBUILD_BASE_URL
    fetcher: HttpFetcher | None = None
    warnings: list[str] = field(default_factory=list, init=False)

    def discover(self, since: datetime) -> list[FailedBuild]:
        """Scrape overview/1930 and return failed builds newer than since."""

        self.warnings.clear()
        cookies = load_cookie_jar(self.cookie_path)
        fetch = self.fetcher or _urllib_fetch
        overview_url = f"{self.base_url.rstrip('/')}/overview/{QUICKBUILD_OVERVIEW_CONFIG_ID}"
        response = fetch(overview_url, cookies)
        _raise_if_login_page(response, action="open QuickBuild overview")

        table = _parse_builds_table(response.text)
        if table is None:
            raise QuickBuildError(
                "COOKIE_EXPIRED",
                "QuickBuild overview did not contain the Recent Builds table. "
                "The cookie may have expired; please log in and export cookies to "
                f"{self.cookie_path}.",
            )

        builds = [_row_to_build(row, base_url=self.base_url) for row in table.rows]
        parsed_builds = [build for build in builds if build is not None]
        if len(parsed_builds) >= 10 and parsed_builds[-1].begin_date >= since:
            self.warnings.append(
                "QuickBuild overview lists at least 10 builds and the oldest listed build "
                "is still in the requested window; history may contain more builds."
            )

        return [
            build
            for build in parsed_builds
            if build.status == "failed" and build.begin_date >= since
        ]


@dataclass(frozen=True)
class _Anchor:
    class_names: tuple[str, ...]
    href: str | None
    text: str


@dataclass(frozen=True)
class _Cell:
    class_names: tuple[str, ...]
    text: str
    anchors: tuple[_Anchor, ...]


@dataclass(frozen=True)
class _Row:
    cells: tuple[_Cell, ...]


@dataclass(frozen=True)
class _BuildsTable:
    rows: tuple[_Row, ...]


@dataclass
class _CellBuilder:
    class_names: tuple[str, ...]
    text_parts: list[str] = field(default_factory=list)
    anchors: list[_Anchor] = field(default_factory=list)


@dataclass
class _AnchorBuilder:
    class_names: tuple[str, ...]
    href: str | None
    text_parts: list[str] = field(default_factory=list)


class _BuildsTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.saw_builds_table = False
        self._in_builds_table = False
        self._table_depth = 0
        self._current_cells: list[_Cell] | None = None
        self._current_cell: _CellBuilder | None = None
        self._current_anchor: _AnchorBuilder | None = None
        self.rows: list[_Row] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = _attrs_to_map(attrs)
        if tag == "table":
            class_names = _class_names(attrs_map)
            if self._in_builds_table:
                self._table_depth += 1
            elif "builds" in class_names:
                self.saw_builds_table = True
                self._in_builds_table = True
                self._table_depth = 1
            return

        if not self._in_builds_table:
            return

        if tag == "tr":
            self._current_cells = []
            return
        if tag == "td" and self._current_cells is not None:
            self._current_cell = _CellBuilder(class_names=_class_names(attrs_map))
            return
        if tag == "a" and self._current_cell is not None:
            self._current_anchor = _AnchorBuilder(
                class_names=_class_names(attrs_map),
                href=attrs_map.get("href"),
            )

    def handle_endtag(self, tag: str) -> None:
        if not self._in_builds_table:
            return

        if tag == "a" and self._current_anchor is not None and self._current_cell is not None:
            self._current_cell.anchors.append(
                _Anchor(
                    class_names=self._current_anchor.class_names,
                    href=self._current_anchor.href,
                    text=_normalize_text("".join(self._current_anchor.text_parts)),
                )
            )
            self._current_anchor = None
            return

        if tag == "td" and self._current_cell is not None and self._current_cells is not None:
            self._current_cells.append(
                _Cell(
                    class_names=self._current_cell.class_names,
                    text=_normalize_text("".join(self._current_cell.text_parts)),
                    anchors=tuple(self._current_cell.anchors),
                )
            )
            self._current_cell = None
            return

        if tag == "tr" and self._current_cells is not None:
            if self._current_cells:
                self.rows.append(_Row(cells=tuple(self._current_cells)))
            self._current_cells = None
            return

        if tag == "table":
            self._table_depth -= 1
            if self._table_depth <= 0:
                self._in_builds_table = False
                self._table_depth = 0

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.text_parts.append(data)
        if self._current_anchor is not None:
            self._current_anchor.text_parts.append(data)


def _parse_builds_table(html_text: str) -> _BuildsTable | None:
    parser = _BuildsTableParser()
    parser.feed(html_text)
    if not parser.saw_builds_table:
        return None
    return _BuildsTable(rows=tuple(parser.rows))


def _row_to_build(row: _Row, *, base_url: str) -> FailedBuild | None:
    if len(row.cells) < 4:
        return None
    id_cell = next((cell for cell in row.cells if "id" in cell.class_names), row.cells[0])
    build_id = id_cell.text.strip()
    if not build_id.isdigit():
        return None

    status_anchor = next(
        (
            anchor
            for cell in row.cells
            for anchor in cell.anchors
            if "build-status" in anchor.class_names
        ),
        None,
    )
    if status_anchor is None:
        return None
    status = _status_from_classes(status_anchor.class_names)
    if status is None:
        return None

    try:
        begin_date = datetime.strptime(row.cells[3].text, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

    return FailedBuild(
        source="quickbuild",
        build_id=build_id,
        version=_strip_snapshot_prefix(status_anchor.text),
        begin_date=begin_date,
        status=status,
        quickbuild_url=f"{base_url.rstrip('/')}/build/{build_id}",
    )


def _status_from_classes(class_names: tuple[str, ...]) -> str | None:
    statuses = [name for name in class_names if name in _STATUS_CLASSES]
    return statuses[0] if len(statuses) == 1 else None


def _strip_snapshot_prefix(version: str) -> str:
    text = version.strip()
    prefix = "[Snapshot]"
    if text.startswith(prefix):
        return text[len(prefix) :].strip()
    return text


def _attrs_to_map(attrs: list[tuple[str, str | None]]) -> Mapping[str, str]:
    return {key: value for key, value in attrs if value is not None}


def _class_names(attrs: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(attrs.get("class", "").split())


def _normalize_text(text: str) -> str:
    return " ".join(text.split())
