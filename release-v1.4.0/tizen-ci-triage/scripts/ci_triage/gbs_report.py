"""QuickBuild GBS report fetch and parse helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

from ci_triage.quickbuild import (
    DEFAULT_COOKIE_PATH,
    DEFAULT_QUICKBUILD_BASE_URL,
    HttpFetcher,
    QuickBuildError,
    _raise_if_login_page,
    _urllib_fetch,
    load_cookie_jar,
)

DEFAULT_ARCHES = (
    "standard-aarch64",
    "standard-armv7l",
    "standard-x86_64",
    "emulator-x86_64",
    "standard_gcov-armv7l",
)


@dataclass(frozen=True)
class GbsReportPackage:
    """One package row from QuickBuild's GBS Build Statis Details table."""

    build_id: str
    arch: str
    spec_name: str
    package_path: str
    status: str
    buildlog_url: str | None


@dataclass(frozen=True)
class GbsReport:
    """Parsed GBS report for one build and architecture."""

    build_id: str
    arch: str
    report_url: str
    iframe_url: str
    packages: tuple[GbsReportPackage, ...]

    @property
    def failed_packages(self) -> tuple[GbsReportPackage, ...]:
        return tuple(package for package in self.packages if package.status == "failed")


def fetch_gbs_report(
    build_id: str,
    arch: str,
    *,
    cookie_path: Path = DEFAULT_COOKIE_PATH,
    base_url: str = DEFAULT_QUICKBUILD_BASE_URL,
    fetcher: HttpFetcher | None = None,
) -> GbsReport:
    """Fetch and parse the static GBS Reports iframe for one architecture."""

    cookies = load_cookie_jar(cookie_path)
    fetch = fetcher or _urllib_fetch
    report_url = f"{base_url.rstrip('/')}/build/{build_id}/gbs_reports/{arch}"
    page = fetch(report_url, cookies)
    _raise_if_login_page(page, action="open GBS reports page")

    iframe_src = find_iframe_src(page.text)
    if iframe_src is None:
        raise QuickBuildError(
            "NO_GBS_REPORT",
            f"build {build_id}/{arch} has no GBS report iframe "
            "(non-package build: RBS/trigger/snapshot); nothing to triage",
        )
    iframe_url = urljoin(page.url, iframe_src)
    iframe = fetch(iframe_url, cookies)
    _raise_if_login_page(iframe, action="download GBS report iframe")
    if iframe.status != 200:
        raise QuickBuildError(
            "GBS_REPORT_DOWNLOAD_FAILED",
            f"failed to download GBS report {iframe_url}: HTTP {iframe.status}",
        )

    packages = parse_gbs_report_packages(
        iframe.text,
        build_id=build_id,
        arch=arch,
        iframe_url=iframe.url,
    )
    return GbsReport(
        build_id=build_id,
        arch=arch,
        report_url=report_url,
        iframe_url=iframe.url,
        packages=packages,
    )


def download_gbs_package_buildlog(
    package: GbsReportPackage,
    *,
    cookie_path: Path = DEFAULT_COOKIE_PATH,
    fetcher: HttpFetcher | None = None,
) -> str:
    """Download one per-package GBS build log from the GBS report link."""

    if not package.buildlog_url:
        raise QuickBuildError(
            "GBS_PACKAGE_LOG_MISSING",
            f"GBS report row has no failed buildlog URL for {package.spec_name}",
        )
    response = (fetcher or _urllib_fetch)(package.buildlog_url, load_cookie_jar(cookie_path))
    if response.status != 200:
        raise QuickBuildError(
            "GBS_PACKAGE_LOG_DOWNLOAD_FAILED",
            f"failed to download GBS package log {package.buildlog_url}: HTTP {response.status}",
        )
    return response.text


def find_iframe_src(html_text: str) -> str | None:
    """Return the iframe src from a QuickBuild GBS reports page."""

    parser = _IframeParser()
    parser.feed(html_text)
    return parser.src


def parse_gbs_report_packages(
    html_text: str,
    *,
    build_id: str,
    arch: str,
    iframe_url: str,
) -> tuple[GbsReportPackage, ...]:
    """Parse Build Statis Details rows from a static GBS Reports HTML page."""

    parser = _ReportTableParser()
    parser.feed(html_text)
    packages: list[GbsReportPackage] = []
    for table in parser.tables:
        if not _looks_like_build_status_table(table):
            continue
        for row in table.rows:
            package = _row_to_package(row, build_id=build_id, arch=arch, iframe_url=iframe_url)
            if package is not None:
                packages.append(package)
    return tuple(packages)


@dataclass(frozen=True)
class _Anchor:
    class_names: tuple[str, ...]
    href: str | None
    text: str


@dataclass(frozen=True)
class _Cell:
    text: str
    anchors: tuple[_Anchor, ...]


@dataclass(frozen=True)
class _Row:
    cells: tuple[_Cell, ...]


@dataclass(frozen=True)
class _Table:
    rows: tuple[_Row, ...]


@dataclass
class _CellBuilder:
    text_parts: list[str] = field(default_factory=list)
    anchors: list[_Anchor] = field(default_factory=list)


@dataclass
class _AnchorBuilder:
    class_names: tuple[str, ...]
    href: str | None
    text_parts: list[str] = field(default_factory=list)


class _IframeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.src: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "iframe" or self.src is not None:
            return
        attrs_map = _attrs_to_map(attrs)
        src = attrs_map.get("src")
        if src:
            self.src = src


class _ReportTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_table = False
        self._table_depth = 0
        self._current_rows: list[_Row] | None = None
        self._current_cells: list[_Cell] | None = None
        self._current_cell: _CellBuilder | None = None
        self._current_anchor: _AnchorBuilder | None = None
        self.tables: list[_Table] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = _attrs_to_map(attrs)
        if tag == "table":
            if self._in_table:
                self._table_depth += 1
            else:
                self._in_table = True
                self._table_depth = 1
                self._current_rows = []
            return
        if not self._in_table:
            return
        if tag == "tr":
            self._current_cells = []
            return
        if tag in {"td", "th"} and self._current_cells is not None:
            self._current_cell = _CellBuilder()
            return
        if tag == "a" and self._current_cell is not None:
            self._current_anchor = _AnchorBuilder(
                class_names=_class_names(attrs_map),
                href=attrs_map.get("href"),
            )

    def handle_endtag(self, tag: str) -> None:
        if not self._in_table:
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
        if (
            tag in {"td", "th"}
            and self._current_cell is not None
            and self._current_cells is not None
        ):
            self._current_cells.append(
                _Cell(
                    text=_normalize_text("".join(self._current_cell.text_parts)),
                    anchors=tuple(self._current_cell.anchors),
                )
            )
            self._current_cell = None
            return
        if tag == "tr" and self._current_cells is not None and self._current_rows is not None:
            if self._current_cells:
                self._current_rows.append(_Row(cells=tuple(self._current_cells)))
            self._current_cells = None
            return
        if tag == "table":
            self._table_depth -= 1
            if self._table_depth <= 0:
                if self._current_rows is not None:
                    self.tables.append(_Table(rows=tuple(self._current_rows)))
                self._in_table = False
                self._table_depth = 0
                self._current_rows = None

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.text_parts.append(data)
        if self._current_anchor is not None:
            self._current_anchor.text_parts.append(data)


def _looks_like_build_status_table(table: _Table) -> bool:
    has_status_anchor = any(
        len(row.cells) >= 3
        and any(
            "failed" in anchor.class_names or "succeeded" in anchor.class_names
            for anchor in row.cells[2].anchors
        )
        for row in table.rows
    )
    if has_status_anchor:
        return True
    header_text = " ".join(cell.text.lower() for row in table.rows[:2] for cell in row.cells)
    return (
        "package name" in header_text
        and "package path" in header_text
        and "build status" in header_text
    )


def _row_to_package(
    row: _Row,
    *,
    build_id: str,
    arch: str,
    iframe_url: str,
) -> GbsReportPackage | None:
    if len(row.cells) < 3:
        return None
    spec_name = row.cells[0].text.strip()
    package_path = row.cells[1].text.strip()
    if not spec_name or spec_name.lower() == "package name":
        return None
    status_anchor = row.cells[2].anchors[0] if row.cells[2].anchors else None
    if status_anchor is None:
        return None
    status = _status_from_anchor(status_anchor)
    if status is None:
        return None
    buildlog_url = urljoin(iframe_url, status_anchor.href) if status_anchor.href else None
    return GbsReportPackage(
        build_id=build_id,
        arch=arch,
        spec_name=spec_name,
        package_path=package_path,
        status=status,
        buildlog_url=buildlog_url,
    )


def _status_from_anchor(anchor: _Anchor) -> str | None:
    if "failed" in anchor.class_names:
        return "failed"
    if "succeeded" in anchor.class_names or "successful" in anchor.class_names:
        return "succeeded"
    text = anchor.text.lower()
    if text == "failed":
        return "failed"
    if text in {"succeeded", "successful"}:
        return "succeeded"
    return None


def _attrs_to_map(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
    return {key: value for key, value in attrs if value is not None}


def _class_names(attrs: dict[str, str]) -> tuple[str, ...]:
    return tuple(attrs.get("class", "").split())


def _normalize_text(text: str) -> str:
    return " ".join(text.split())
