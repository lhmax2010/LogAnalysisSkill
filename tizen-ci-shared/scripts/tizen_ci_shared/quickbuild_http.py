"""QuickBuild authenticated full-log download helpers."""

from __future__ import annotations

import html
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

DEFAULT_QUICKBUILD_BASE_URL = "https://quickbuild.tizen.org"
DEFAULT_COOKIE_PATH = Path("/tmp/quickbuild_cookies.json")
DOWNLOAD_LINK_MARKER = "ILinkListener-content-buildTab-panel-download"
DOWNLOAD_TIZEN_BASE_URL = "http://download.tizen.org/RBS/TIZEN/Tizen/Tizen-Unified-Toolchain"


@dataclass(frozen=True)
class HttpResponse:
    """Small response object used by the downloader and tests."""

    status: int
    url: str
    body: bytes
    content_type: str | None = None

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


HttpFetcher = Callable[[str, Mapping[str, str]], HttpResponse]


@dataclass(frozen=True)
class QuickBuildDownload:
    """Downloaded QuickBuild full-log content and provenance."""

    build_id: str
    log_page_url: str
    download_url: str
    full_log: str


@dataclass(frozen=True)
class PackageBuildLog:
    """Downloaded per-package GBS build log from download.tizen.org."""

    url: str
    text: str


class QuickBuildError(RuntimeError):
    """QuickBuild download failure with a stable error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def load_cookie_jar(cookie_path: Path = DEFAULT_COOKIE_PATH) -> dict[str, str]:
    """Load browser-exported QuickBuild cookies from a JSON file."""

    try:
        raw = json.loads(cookie_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise QuickBuildError(
            "COOKIE_MISSING",
            f"QuickBuild cookie file is missing: {cookie_path}",
        ) from exc
    except json.JSONDecodeError as exc:
        raise QuickBuildError(
            "COOKIE_UNREADABLE",
            f"QuickBuild cookie file is not valid JSON: {cookie_path}",
        ) from exc

    if not isinstance(raw, list):
        raise QuickBuildError("COOKIE_UNREADABLE", "QuickBuild cookie JSON must be a list")

    cookies: dict[str, str] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        value = item.get("value")
        domain = item.get("domain")
        if (
            isinstance(name, str)
            and isinstance(value, str)
            and (domain is None or "quickbuild.tizen.org" in str(domain))
        ):
            cookies[name] = value

    if not cookies:
        raise QuickBuildError(
            "COOKIE_EXPIRED",
            "QuickBuild cookie file has no quickbuild.tizen.org cookies; "
            "please log in and export cookies again.",
        )
    return cookies


def download_full_log(
    build_id: str,
    *,
    cookie_path: Path = DEFAULT_COOKIE_PATH,
    base_url: str = DEFAULT_QUICKBUILD_BASE_URL,
    fetcher: HttpFetcher | None = None,
) -> QuickBuildDownload:
    """Download a QuickBuild full log through the Wicket dynamic download link."""

    cookies = load_cookie_jar(cookie_path)
    fetch = fetcher or _urllib_fetch
    log_page_url = f"{base_url.rstrip('/')}/build/{build_id}/log"
    page = fetch(log_page_url, cookies)
    _raise_if_login_page(page, action="open build log page")

    href = find_download_href(page.text)
    if href is None:
        raise QuickBuildError(
            "DOWNLOAD_LINK_NOT_FOUND",
            "QuickBuild log page did not contain the full-log download link. "
            "The cookie may have expired; please log in and export cookies again.",
        )

    download_url = urljoin(page.url, href)
    full_log_response = fetch(download_url, cookies)
    _raise_if_login_page(full_log_response, action="download full log")
    return QuickBuildDownload(
        build_id=build_id,
        log_page_url=log_page_url,
        download_url=download_url,
        full_log=full_log_response.text,
    )


def find_download_href(html_text: str) -> str | None:
    """Return the Wicket full-log download href from a build-log HTML page."""

    for match in re.finditer(r"""href\s*=\s*["']([^"']+)["']""", html_text, re.IGNORECASE):
        href = html.unescape(match.group(1))
        if DOWNLOAD_LINK_MARKER in href:
            return href
    return None


def derive_package_buildlog_url(dest_file: str) -> str | None:
    """Derive the public per-package buildlog URL from a QuickBuild dest_file."""

    match = re.search(
        r"/live/TIZEN_Tizen_Tizen-Unified-Toolchain_RBS_TRIGGER_"
        r"(?P<snapshot>[^/]+)/buildlogs/"
        r"(?P<profile>[^/]+)/(?P<arch>[^/]+)/failed/(?P<filename>[^/\s]+)$",
        dest_file,
    )
    if match is None:
        return None
    snapshot = quote(match.group("snapshot"), safe=".")
    profile = quote(match.group("profile"), safe="")
    arch = quote(match.group("arch"), safe="")
    filename = quote(match.group("filename"), safe="")
    return (
        f"{DOWNLOAD_TIZEN_BASE_URL}/tizen-unified-toolchain_{snapshot}/"
        f"builddata/buildlogs/{profile}/{arch}/failed/{filename}"
    )


def download_package_buildlog(
    dest_file: str,
    *,
    fetcher: HttpFetcher | None = None,
) -> PackageBuildLog | None:
    """Download one failed package buildlog when QuickBuild exposes its dest_file."""

    url = derive_package_buildlog_url(dest_file)
    if url is None:
        return None
    response = (fetcher or _urllib_fetch)(url, {})
    if response.status != 200:
        raise QuickBuildError(
            "PACKAGE_BUILDLOG_DOWNLOAD_FAILED",
            f"failed to download package buildlog {url}: HTTP {response.status}",
        )
    return PackageBuildLog(url=url, text=response.text)


def _raise_if_login_page(response: HttpResponse, *, action: str) -> None:
    final_url = response.url.lower()
    text = response.text.lower()
    if (
        response.status in {401, 403}
        or "/signin" in final_url
        or "redirect-url-after-sign-in" in text
    ):
        raise QuickBuildError(
            "COOKIE_EXPIRED",
            f"QuickBuild cookie expired while trying to {action}; "
            f"please log in and export cookies to {DEFAULT_COOKIE_PATH}.",
        )


def _urllib_fetch(url: str, cookies: Mapping[str, str]) -> HttpResponse:
    url = normalize_quickbuild_url(url)
    cookie_header = "; ".join(f"{name}={value}" for name, value in cookies.items())
    request = Request(url, headers={"Cookie": cookie_header, "User-Agent": "ci-triage/0.1"})
    try:
        with urlopen(request, timeout=60) as response:
            return HttpResponse(
                status=response.status,
                url=response.geturl(),
                body=response.read(),
                content_type=response.headers.get("content-type"),
            )
    except HTTPError as exc:
        return HttpResponse(
            status=exc.code,
            url=exc.geturl(),
            body=exc.read(),
            content_type=exc.headers.get("content-type"),
        )
    except URLError as exc:
        raise QuickBuildError("QUICKBUILD_DOWNLOAD_FAILED", str(exc)) from exc


def normalize_quickbuild_url(url: str) -> str:
    """Idempotently quote QuickBuild URL paths that may contain raw spaces."""

    parts = urlsplit(url)
    path = quote(unquote(parts.path), safe="/@")
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))
