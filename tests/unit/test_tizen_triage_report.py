from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from pathlib import Path

import pytest
from ci_triage.orchestrator import BatchTriageOptions
from tizen_ci_shared.quickbuild_http import HttpResponse, QuickBuildError
from tizen_ci_shared.types import (
    FailedPackage,
    GerritChange,
    GerritPatchSet,
    SourceFetchResult,
)
from tizen_triage_report.gbs_report import (
    DEFAULT_ARCHES,
    GbsReport,
    GbsReportPackage,
    _Anchor,
    _Cell,
    _looks_like_build_status_table,
    _Row,
    _row_to_package,
    _status_from_anchor,
    _Table,
    download_gbs_package_buildlog,
    fetch_gbs_report,
    find_iframe_src,
    parse_gbs_report_packages,
)
from tizen_triage_report.report import (
    TriageReportData,
    _primary_location,
    render_report,
)

# Test ownership boundary:
# - this file: tizen_triage_report skill behavior and package surface;
# - test_ci_triage.py: orchestration integration;
# - the final section here: compatibility-shim identity only.


GBS_REPORT_HTML = """
<html>
<body>
<table><tr><td>unrelated</td></tr></table>
<table>
  <tr>
    <th>Package Name</th><th>Package Path</th><th>Build Status</th>
  </tr>
  <tr>
    <td>lightweight-web-engine</td>
    <td>tizen_unified_toolchain_standard/lightweight-web-engine-1.3.31-1</td>
    <td>
      <a href="logs/fail/lightweight-web-engine-1.3.31-1/log.txt" class="failed">
        Failed
      </a>
    </td>
  </tr>
  <tr>
    <td>lwnode</td>
    <td>tizen_unified_toolchain_standard/lwnode-1.0.0-1</td>
    <td><a href="logs/succeeded/lwnode/log.txt" class="succeeded">Succeeded</a></td>
  </tr>
</table>
</body>
</html>
"""


def _cookie_file(tmp_path: Path) -> Path:
    path = tmp_path / "quickbuild_cookies.json"
    path.write_text(
        json.dumps(
            [
                {
                    "name": "JSESSIONID_8810",
                    "value": "session-value",
                    "domain": "quickbuild.tizen.org",
                    "path": "/",
                }
            ]
        ),
        encoding="utf-8",
    )
    return path


def _anchor(
    *,
    classes: tuple[str, ...] = ("failed",),
    href: str | None = "logs/fail/demo/log.txt",
    text: str = "Failed",
) -> _Anchor:
    return _Anchor(class_names=classes, href=href, text=text)


def _cell(text: str = "", *anchors: _Anchor) -> _Cell:
    return _Cell(text=text, anchors=anchors)


def _package_row(
    *,
    spec_name: str = "demo",
    package_path: str = "profile/demo-1.0.0-1",
    anchor: _Anchor | None = None,
) -> _Row:
    status_anchors = () if anchor is None else (anchor,)
    return _Row(
        cells=(
            _cell(spec_name),
            _cell(package_path),
            _Cell(text=anchor.text if anchor else "", anchors=status_anchors),
        )
    )


def _row_to_package_for(row: _Row) -> GbsReportPackage | None:
    return _row_to_package(
        row,
        build_id="111",
        arch="standard-armv7l",
        iframe_url="https://quickbuild.tizen.org/reports/index.html",
    )


# Skill behavior: GBS report fetching, parsing, and package-log download.


def test_gbs_report_parses_failed_rows_and_buildlog_url() -> None:
    packages = parse_gbs_report_packages(
        GBS_REPORT_HTML,
        build_id="111",
        arch="standard-armv7l",
        iframe_url=(
            "https://quickbuild.tizen.org/download/111/html/"
            "GBS%20Reports@%5E@standard-armv7l/index.html"
        ),
    )

    assert len(packages) == 2
    failed = [package for package in packages if package.status == "failed"]
    assert len(failed) == 1
    assert failed[0].spec_name == "lightweight-web-engine"
    assert failed[0].package_path == (
        "tizen_unified_toolchain_standard/lightweight-web-engine-1.3.31-1"
    )
    assert failed[0].buildlog_url == (
        "https://quickbuild.tizen.org/download/111/html/"
        "GBS%20Reports@%5E@standard-armv7l/logs/fail/"
        "lightweight-web-engine-1.3.31-1/log.txt"
    )


def test_gbs_report_fetch_uses_iframe_src_without_reencoding(tmp_path: Path) -> None:
    cookie_path = _cookie_file(tmp_path)
    calls: list[str] = []

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        calls.append(url)
        if url.endswith("/gbs_reports/standard-armv7l"):
            return HttpResponse(
                status=200,
                url=url,
                body=(
                    b'<iframe src="/download/111/html/'
                    b'GBS%20Reports@%5E@standard-armv7l/index.html"></iframe>'
                ),
            )
        return HttpResponse(status=200, url=url, body=GBS_REPORT_HTML.encode())

    report = fetch_gbs_report(
        "111",
        "standard-armv7l",
        cookie_path=cookie_path,
        fetcher=fetcher,
    )

    assert find_iframe_src('<iframe src="/x/index.html"></iframe>') == "/x/index.html"
    assert calls == [
        "https://quickbuild.tizen.org/build/111/gbs_reports/standard-armv7l",
        (
            "https://quickbuild.tizen.org/download/111/html/"
            "GBS%20Reports@%5E@standard-armv7l/index.html"
        ),
    ]
    assert report.failed_packages[0].spec_name == "lightweight-web-engine"


def test_fetch_gbs_report_rejects_report_page_login(tmp_path: Path) -> None:
    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        return HttpResponse(status=403, url=url, body=b"sign in")

    with pytest.raises(QuickBuildError) as exc:
        fetch_gbs_report(
            "111",
            "standard-armv7l",
            cookie_path=_cookie_file(tmp_path),
            fetcher=fetcher,
        )

    assert exc.value.code == "COOKIE_EXPIRED"


def test_gbs_report_without_iframe_reports_no_gbs_report(tmp_path: Path) -> None:
    cookie_path = _cookie_file(tmp_path)

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        return HttpResponse(
            status=200,
            url=url,
            body=(
                b'<html><a href="/download/111/snapshots/toolchain-manifest.txt">'
                b"Manifest</a></html>"
            ),
        )

    with pytest.raises(QuickBuildError) as exc:
        fetch_gbs_report(
            "111",
            "standard-x86_64",
            cookie_path=cookie_path,
            fetcher=fetcher,
        )

    assert exc.value.code == "NO_GBS_REPORT"


def test_fetch_gbs_report_rejects_iframe_page_login(tmp_path: Path) -> None:
    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        if "/gbs_reports/" in url:
            return HttpResponse(
                status=200,
                url=url,
                body=b'<iframe src="/download/111/report.html"></iframe>',
            )
        return HttpResponse(status=403, url=url, body=b"sign in")

    with pytest.raises(QuickBuildError) as exc:
        fetch_gbs_report(
            "111",
            "standard-armv7l",
            cookie_path=_cookie_file(tmp_path),
            fetcher=fetcher,
        )

    assert exc.value.code == "COOKIE_EXPIRED"


def test_parse_gbs_report_packages_ignores_non_status_tables() -> None:
    assert (
        parse_gbs_report_packages(
            "<table><tr><td>unrelated</td></tr></table>",
            build_id="111",
            arch="standard-armv7l",
            iframe_url="https://quickbuild.tizen.org/report.html",
        )
        == ()
    )


def test_download_gbs_package_buildlog_returns_text(tmp_path: Path) -> None:
    package = GbsReportPackage(
        build_id="111",
        arch="standard-armv7l",
        spec_name="demo",
        package_path="profile/demo-1.0.0-1",
        status="failed",
        buildlog_url="https://quickbuild.tizen.org/logs/demo.txt",
    )

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        assert url == package.buildlog_url
        return HttpResponse(status=200, url=url, body=b"compiler output\n")

    assert (
        download_gbs_package_buildlog(
            package,
            cookie_path=_cookie_file(tmp_path),
            fetcher=fetcher,
        )
        == "compiler output\n"
    )


def test_gbs_report_iframe_download_failure_remains_retryable(tmp_path: Path) -> None:
    cookie_path = _cookie_file(tmp_path)

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        if url.endswith("/gbs_reports/standard-x86_64"):
            return HttpResponse(
                status=200,
                url=url,
                body=(
                    b'<iframe src="/download/111/html/'
                    b'GBS Reports@^@standard-x86_64/index.html"></iframe>'
                ),
            )
        return HttpResponse(status=500, url=url, body=b"server error")

    with pytest.raises(QuickBuildError) as exc:
        fetch_gbs_report(
            "111",
            "standard-x86_64",
            cookie_path=cookie_path,
            fetcher=fetcher,
        )

    assert exc.value.code == "GBS_REPORT_DOWNLOAD_FAILED"


def test_fetch_gbs_report_preserves_raw_arch_in_url_and_packages(tmp_path: Path) -> None:
    arch = "standard-armv7l"
    calls: list[str] = []

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        calls.append(url)
        if url.endswith(f"/gbs_reports/{arch}"):
            return HttpResponse(
                status=200,
                url=url,
                body=b'<iframe src="/download/111/report.html"></iframe>',
            )
        return HttpResponse(status=200, url=url, body=GBS_REPORT_HTML.encode())

    report = fetch_gbs_report(
        "111",
        arch,
        cookie_path=_cookie_file(tmp_path),
        fetcher=fetcher,
    )

    assert calls[0] == f"https://quickbuild.tizen.org/build/111/gbs_reports/{arch}"
    assert report.arch == arch
    assert report.packages
    assert all(package.arch == arch for package in report.packages)


def test_fetch_gbs_report_no_iframe_error_preserves_raw_arch(tmp_path: Path) -> None:
    arch = "standard-armv7l"

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        return HttpResponse(status=200, url=url, body=b"<html></html>")

    with pytest.raises(QuickBuildError) as exc:
        fetch_gbs_report(
            "111",
            arch,
            cookie_path=_cookie_file(tmp_path),
            fetcher=fetcher,
        )

    assert exc.value.code == "NO_GBS_REPORT"
    assert arch in str(exc.value)


def test_download_gbs_package_buildlog_requires_url(tmp_path: Path) -> None:
    package = GbsReportPackage("111", "standard-armv7l", "demo", "profile/demo", "failed", None)

    with pytest.raises(QuickBuildError) as exc:
        download_gbs_package_buildlog(package, cookie_path=_cookie_file(tmp_path))

    assert exc.value.code == "GBS_PACKAGE_LOG_MISSING"


def test_download_gbs_package_buildlog_rejects_non_200(tmp_path: Path) -> None:
    package = GbsReportPackage(
        "111",
        "standard-armv7l",
        "demo",
        "profile/demo",
        "failed",
        "https://quickbuild.tizen.org/logs/demo.txt",
    )

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        return HttpResponse(status=500, url=url, body=b"server error")

    with pytest.raises(QuickBuildError) as exc:
        download_gbs_package_buildlog(
            package,
            cookie_path=_cookie_file(tmp_path),
            fetcher=fetcher,
        )

    assert exc.value.code == "GBS_PACKAGE_LOG_DOWNLOAD_FAILED"


def test_row_to_package_rejects_short_row() -> None:
    assert _row_to_package_for(_Row(cells=(_cell("demo"), _cell("profile/demo")))) is None


def test_row_to_package_rejects_empty_spec_name() -> None:
    assert _row_to_package_for(_package_row(spec_name="", anchor=_anchor())) is None


def test_row_to_package_rejects_header_row() -> None:
    assert _row_to_package_for(_package_row(spec_name="Package Name", anchor=_anchor())) is None


def test_row_to_package_rejects_missing_status_anchor() -> None:
    assert _row_to_package_for(_package_row()) is None


def test_row_to_package_rejects_unknown_status() -> None:
    assert _row_to_package_for(_package_row(anchor=_anchor(classes=(), text="Pending"))) is None


def test_status_from_anchor_prefers_status_classes() -> None:
    assert _status_from_anchor(_anchor(classes=("failed",), text="anything")) == "failed"
    assert _status_from_anchor(_anchor(classes=("succeeded",), text="anything")) == "succeeded"


def test_status_from_anchor_falls_back_to_text() -> None:
    assert _status_from_anchor(_anchor(classes=(), text="Failed")) == "failed"
    assert _status_from_anchor(_anchor(classes=(), text="Succeeded")) == "succeeded"


def test_status_from_anchor_class_wins_over_conflicting_text() -> None:
    assert _status_from_anchor(_anchor(classes=("failed",), text="Succeeded")) == "failed"


def test_status_from_anchor_accepts_successful_alias() -> None:
    assert _status_from_anchor(_anchor(classes=("successful",), text="anything")) == "succeeded"
    assert _status_from_anchor(_anchor(classes=(), text="Successful")) == "succeeded"


def test_looks_like_build_status_table_covers_three_detection_states() -> None:
    status_anchor_table = _Table(rows=(_package_row(anchor=_anchor()),))
    header_table = _Table(
        rows=(
            _Row(
                cells=(
                    _cell("Package Name"),
                    _cell("Package Path"),
                    _cell("Build Status"),
                )
            ),
        )
    )
    unrelated_table = _Table(rows=(_Row(cells=(_cell("unrelated"),)),))

    assert _looks_like_build_status_table(status_anchor_table) is True
    assert _looks_like_build_status_table(header_table) is True
    assert _looks_like_build_status_table(unrelated_table) is False


def test_row_to_package_builds_urls_with_and_without_href() -> None:
    with_href = _row_to_package_for(_package_row(anchor=_anchor(href="logs/demo.txt")))
    without_href = _row_to_package_for(_package_row(anchor=_anchor(href=None)))

    assert with_href is not None
    assert with_href.buildlog_url == "https://quickbuild.tizen.org/reports/logs/demo.txt"
    assert without_href is not None
    assert without_href.buildlog_url is None


def test_gbs_report_failed_packages_filters_mixed_statuses() -> None:
    failed = GbsReportPackage("111", "standard-armv7l", "bad", "profile/bad", "failed", None)
    succeeded = GbsReportPackage(
        "111", "standard-armv7l", "good", "profile/good", "succeeded", None
    )
    report = GbsReport("111", "standard-armv7l", "report-url", "iframe-url", (failed, succeeded))

    assert report.failed_packages == (failed,)


# Skill behavior: report rendering. A/B/C/D remain separate fixtures so nested
# branches cannot be hidden by an all-present/all-absent parameterization.


def test_render_report_fixture_a_all_optional_fields_present() -> None:
    change = GerritChange(
        project="platform/test/demo",
        branch="tizen",
        status="NEW",
        number=123,
        subject="Fix demo",
        url="https://review.tizen.org/123",
        matching_patchset=GerritPatchSet(2, "abc123", "refs/changes/23/123/2"),
    )
    data = TriageReportData(
        build_id="111",
        quickbuild_log_url="https://quickbuild.tizen.org/build/111",
        full_log_path=Path("/tmp/full.log"),
        analyzed_buildlog_path=Path("/tmp/package.log"),
        package_buildlog_url="https://quickbuild.tizen.org/package.log",
        selected_package=FailedPackage("demo-1.0-1", "demo", "/tmp/package.log"),
        project_key="platform/test/demo",
        commit_hash="abc123",
        source_fetch=SourceFetchResult(
            "fetched",
            Path("/tmp/src"),
            "ssh://review/platform/test/demo",
            change=change,
            error="source warning",
        ),
        analyzer_output_dir=Path("/tmp/analyzer"),
        evidence_packet_path=Path("/tmp/evidence.json"),
        patch_context_dir=Path("/tmp/patch"),
        patch_context_meta_path=Path("/tmp/patch/meta.json"),
        patch_context_status="ready",
        primary_error={"kind": "compiler", "file": "src/demo.c", "line": 7, "message": "bad"},
        warnings=["warning one"],
        errors=["error one"],
    )

    output = render_report(data)

    for expected in (
        "- Full log: `/tmp/full.log`",
        "- Analyzer input: `/tmp/package.log`",
        "- Package buildlog URL: https://quickbuild.tizen.org/package.log",
        "- buildlog path: `/tmp/package.log`",
        "- Gerrit project: `platform/test/demo`",
        "- Commit: `abc123`",
        "- Change: `123`",
        "- Patch set ref: `refs/changes/23/123/2`",
        "- Error: source warning",
        "- Evidence packet: `/tmp/evidence.json`",
        "- Analyzer output: `/tmp/analyzer`",
        "- Primary kind: `compiler`",
        "- Primary location: `src/demo.c:7`",
        "- Message: bad",
        "- Patch context: `/tmp/patch`",
        "- Status: `ready`",
        "- Meta: `/tmp/patch/meta.json`",
        "## Warnings\n- warning one",
        "## Errors\n- error one",
    ):
        assert expected in output


def test_render_report_fixture_b_all_optional_fields_absent() -> None:
    output = render_report(
        TriageReportData(
            build_id="111",
            quickbuild_log_url="https://quickbuild.tizen.org/build/111",
        )
    )

    assert "- Selected package: n/a" in output
    assert "- Source checkout: not attempted" in output
    for absent in (
        "- Full log:",
        "- Analyzer input:",
        "- Package buildlog URL:",
        "- Gerrit project:",
        "- Commit:",
        "- Evidence packet:",
        "- Analyzer output:",
        "- Primary kind:",
        "- Patch context:",
        "- Meta:",
        "## Warnings",
        "## Errors",
    ):
        assert absent not in output


def test_render_report_fixture_c_outer_present_inner_absent() -> None:
    output = render_report(
        TriageReportData(
            build_id="111",
            quickbuild_log_url="https://quickbuild.tizen.org/build/111",
            selected_package=FailedPackage("demo-1.0-1", "demo"),
            source_fetch=SourceFetchResult(
                "fetched",
                Path("/tmp/src"),
                "ssh://review/platform/test/demo",
                change=None,
                error=None,
            ),
        )
    )

    assert "- spec_name: `demo`" in output
    assert "- Status: `fetched`" in output
    assert "- buildlog path:" not in output
    assert "- Change status:" not in output
    assert "- Error:" not in output


def test_render_report_fixture_d_middle_present_leaf_absent() -> None:
    output = render_report(
        TriageReportData(
            build_id="111",
            quickbuild_log_url="https://quickbuild.tizen.org/build/111",
            source_fetch=SourceFetchResult(
                "fetched",
                Path("/tmp/src"),
                "ssh://review/platform/test/demo",
                change=GerritChange(
                    project="platform/test/demo",
                    branch="tizen",
                    status="NEW",
                    number=None,
                    subject="Fix demo",
                    url=None,
                    matching_patchset=None,
                ),
            ),
        )
    )

    assert "- Change status: `NEW`" in output
    assert "- Branch: `tizen`" in output
    assert "- Change:" not in output
    assert "- Patch set ref:" not in output


def test_primary_location_includes_file_and_line() -> None:
    assert _primary_location({"file": "src/demo.c", "line": 7}) == "src/demo.c:7"


def test_primary_location_returns_file_without_line() -> None:
    assert _primary_location({"file": "src/demo.c"}) == "src/demo.c"


def test_primary_location_returns_na_without_file() -> None:
    assert _primary_location({"line": 7}) == "n/a"


# Orchestration integration: the batch options consume the skill-owned default.


def test_default_gbs_report_arches_include_emulator_and_gcov() -> None:
    assert DEFAULT_ARCHES == (
        "standard-aarch64",
        "standard-armv7l",
        "standard-x86_64",
        "emulator-x86_64",
        "standard_gcov-armv7l",
    )
    assert BatchTriageOptions().arches == DEFAULT_ARCHES


# Package surface and legacy wiring.


def test_triage_report_package_root_exports_only_public_api() -> None:
    package = importlib.import_module("tizen_triage_report")
    gbs_module = importlib.import_module("tizen_triage_report.gbs_report")
    report_module = importlib.import_module("tizen_triage_report.report")
    public = {
        "DEFAULT_ARCHES": gbs_module.DEFAULT_ARCHES,
        "GbsReport": gbs_module.GbsReport,
        "GbsReportPackage": gbs_module.GbsReportPackage,
        "TriageReportData": report_module.TriageReportData,
        "download_gbs_package_buildlog": gbs_module.download_gbs_package_buildlog,
        "fetch_gbs_report": gbs_module.fetch_gbs_report,
        "find_iframe_src": gbs_module.find_iframe_src,
        "parse_gbs_report_packages": gbs_module.parse_gbs_report_packages,
        "render_report": report_module.render_report,
    }
    internal = {
        "_Anchor",
        "_AnchorBuilder",
        "_Cell",
        "_CellBuilder",
        "_IframeParser",
        "_ReportTableParser",
        "_Row",
        "_Table",
        "_attrs_to_map",
        "_class_names",
        "_looks_like_build_status_table",
        "_normalize_text",
        "_primary_location",
        "_row_to_package",
        "_status_from_anchor",
    }

    assert set(package.__all__) == set(public)
    assert all(getattr(package, name) is value for name, value in public.items())
    assert all(not hasattr(package, name) for name in internal)


def test_triage_report_legacy_shims_preserve_all_symbol_identities() -> None:
    legacy_gbs = importlib.import_module("ci_triage.gbs_report")
    skill_gbs = importlib.import_module("tizen_triage_report.gbs_report")
    legacy_report = importlib.import_module("ci_triage.report")
    skill_report = importlib.import_module("tizen_triage_report.report")
    gbs_symbols = {
        "DEFAULT_ARCHES",
        "GbsReport",
        "GbsReportPackage",
        "_Anchor",
        "_AnchorBuilder",
        "_Cell",
        "_CellBuilder",
        "_IframeParser",
        "_ReportTableParser",
        "_Row",
        "_Table",
        "_attrs_to_map",
        "_class_names",
        "_looks_like_build_status_table",
        "_normalize_text",
        "_row_to_package",
        "_status_from_anchor",
        "download_gbs_package_buildlog",
        "fetch_gbs_report",
        "find_iframe_src",
        "parse_gbs_report_packages",
    }
    report_symbols = {"TriageReportData", "_primary_location", "render_report"}

    assert all(getattr(legacy_gbs, name) is getattr(skill_gbs, name) for name in gbs_symbols)
    assert all(
        getattr(legacy_report, name) is getattr(skill_report, name) for name in report_symbols
    )
