import json
import subprocess
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from ci_triage.gbs_report import (
    DEFAULT_ARCHES,
    GbsReportPackage,
    fetch_gbs_report,
    find_iframe_src,
    parse_gbs_report_packages,
)
from ci_triage.gerrit import (
    GerritChange,
    fetch_source_for_commit,
    find_patchset_by_revision,
)
from ci_triage.orchestrator import (
    STATE_FAILED_ANALYZE,
    STATE_FAILED_LOG,
    STATE_FAILED_PERMANENT,
    STATE_NEEDS_INPUT,
    STATE_REPORTED,
    STATE_REPORTED_NO_REPORT,
    STATE_SKIPPED_PROCESSED,
    BatchRunRecord,
    BatchTriageOptions,
    CiTriageOrchestrator,
    _manifest_error,
)
from ci_triage.quickbuild import (
    HttpResponse,
    PackageBuildLog,
    QuickBuildError,
    derive_package_buildlog_url,
    download_full_log,
    normalize_quickbuild_url,
)
from ci_triage.quickbuild_log import (
    QuickBuildLogError,
    match_pkg_key,
    parse_build_pkg_list,
    parse_failed_packages,
    select_failed_package,
)
from ci_triage.runner import TriageOptions, TriageResult, _safe_pkg_dir, run_triage
from tizen_ci_shared.types import SourceFetchResult
from tizen_qb_discover.sources import FailedBuild, QuickBuildSource

OVERVIEW_HTML = """
<html>
<body>
<table class="table table-sm table-striped-even builds">
  <tr class="even">
    <td class="id"><span>1118258</span></td>
    <td><a class=" build-status failed maskable" href="/build/1118258">
      [Snapshot] 20260701.034300
    </a></td>
    <td>master01</td>
    <td><span>2026-07-01 03:43:00</span></td>
    <td><span>00:31:00</span></td>
    <td><span>scheduler</span></td>
  </tr>
  <tr class="odd">
    <td class="id"><span>1118000</span></td>
    <td><a class=" build-status successful maskable" href="/build/1118000">20260630.210000</a></td>
    <td>master01</td>
    <td><span>2026-06-30 21:00:00</span></td>
    <td><span>00:26:00</span></td>
    <td><span>scheduler</span></td>
  </tr>
  <tr class="even">
    <td class="id"><span>1117858</span></td>
    <td><a class=" build-status failed maskable" href="/build/1117858">
      [Snapshot] 20260630.010101
    </a></td>
    <td>master01</td>
    <td><span>2026-06-30 01:01:01</span></td>
    <td><span>00:32:00</span></td>
    <td><span>scheduler</span></td>
  </tr>
  <tr class="odd">
    <td class="id"><span>1117000</span></td>
    <td><a class=" build-status successful maskable" href="/build/1117000">20260628.120000</a></td>
    <td>master01</td>
    <td><span>2026-06-28 12:00:00</span></td>
    <td><span>00:30:00</span></td>
    <td><span>scheduler</span></td>
  </tr>
  <tr class="even">
    <td class="id"><span>1115346</span></td>
    <td><a class=" build-status failed maskable" href="/build/1115346">
      [Snapshot] 20260624.040404
    </a></td>
    <td>master01</td>
    <td><span>2026-06-24 04:04:04</span></td>
    <td><span>00:34:00</span></td>
    <td><span>scheduler</span></td>
  </tr>
  <tr class="odd">
    <td class="id"><span>1115000</span></td>
    <td><a class=" build-status successful maskable" href="/build/1115000">20260623.130000</a></td>
    <td>master01</td>
    <td><span>2026-06-23 13:00:00</span></td>
    <td><span>00:29:00</span></td>
    <td><span>scheduler</span></td>
  </tr>
  <tr class="even">
    <td class="id"><span>1114933</span></td>
    <td><a class=" build-status failed maskable" href="/build/1114933">
      [Snapshot] 20260622.080808
    </a></td>
    <td>master01</td>
    <td><span>2026-06-22 08:08:08</span></td>
    <td><span>00:37:00</span></td>
    <td><span>scheduler</span></td>
  </tr>
  <tr class="odd">
    <td class="id"><span>1114932</span></td>
    <td><a class=" build-status cancelled maskable" href="/build/1114932">
      [Snapshot] 20260622.070707
    </a></td>
    <td>master01</td>
    <td><span>2026-06-22 07:07:07</span></td>
    <td><span>00:05:00</span></td>
    <td><span>scheduler</span></td>
  </tr>
  <tr class="even">
    <td class="id"><span>1114600</span></td>
    <td><a class=" build-status successful maskable" href="/build/1114600">20260620.120000</a></td>
    <td>master01</td>
    <td><span>2026-06-20 12:00:00</span></td>
    <td><span>00:27:00</span></td>
    <td><span>scheduler</span></td>
  </tr>
  <tr class="odd">
    <td class="id"><span>1114499</span></td>
    <td><a class=" build-status failed maskable" href="/build/1114499">
      [Snapshot] 20260619.060606
    </a></td>
    <td>master01</td>
    <td><span>2026-06-19 06:06:06</span></td>
    <td><span>00:33:00</span></td>
    <td><span>scheduler</span></td>
  </tr>
</table>
</body>
</html>
"""

EXPECTED_MANIFEST_UNIT_KEYS = {
    "unit_key",
    "build_id",
    "arch",
    "spec_name",
    "state",
    "patch_status",
    "project",
    "base_commit",
    "branch",
    "src_clean",
    "evidence_packet",
    "patch_context",
    "patch_context_meta",
    "report",
    "package_buildlog",
    "error",
}


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


def _failed_build(build_id: str = "111") -> FailedBuild:
    return FailedBuild(
        source="quickbuild",
        build_id=build_id,
        version="20260701.034300",
        begin_date=datetime(2026, 7, 1, 3, 43, 0),
        status="failed",
        quickbuild_url=f"https://quickbuild.tizen.org/build/{build_id}",
    )


class _FakeSource:
    def __init__(self, builds: list[FailedBuild]) -> None:
        self.builds = builds
        self.warnings: list[str] = []

    def discover(self, since: datetime) -> list[FailedBuild]:
        return self.builds


def _full_log_for(*spec_names: str) -> str:
    mapping_items = ", ".join(
        f"'platform/test/{spec_name}': '{spec_name}-commit'" for spec_name in spec_names
    )
    package_lines = [
        f"fail_pkg: {spec_name}-1.0.0-1, spec_name: {spec_name}" for spec_name in spec_names
    ]
    return "\n".join([f"build_pkg_list_dic: {{{mapping_items}}}", *package_lines])


def _gbs_package(
    spec_name: str,
    *,
    arch: str = "standard-armv7l",
) -> GbsReportPackage:
    return GbsReportPackage(
        build_id="111",
        arch=arch,
        spec_name=spec_name,
        package_path=f"tizen_unified_toolchain_standard/{spec_name}-1.0.0-1",
        status="failed",
        buildlog_url=f"https://quickbuild.tizen.org/download/111/html/report/logs/fail/{spec_name}/log.txt",
    )


def _gbs_discoverer(
    *packages: GbsReportPackage,
) -> Callable[[str, str, Path], tuple[GbsReportPackage, ...]]:
    def discover(build_id: str, arch: str, cookie_path: Path) -> tuple[GbsReportPackage, ...]:
        return tuple(package for package in packages if package.arch == arch)

    return discover


def _successful_triage(status: str) -> Callable[[TriageOptions], TriageResult]:
    def runner(options: TriageOptions) -> TriageResult:
        assert options.output_dir is not None
        output_dir = options.output_dir
        output_dir.mkdir(parents=True)
        report_path = output_dir / "report.md"
        report_path.write_text(
            "\n".join(
                [
                    "# report",
                    "- Change status: `NEW`",
                    "- Patch set ref: `refs/changes/01/1/1`",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        meta_dir = output_dir / "patch_context"
        meta_dir.mkdir()
        (meta_dir / "meta.json").write_text(json.dumps({"status": status}), encoding="utf-8")
        return TriageResult(
            exit_code=0,
            status="success",
            output_dir=output_dir,
            report_path=report_path,
        )

    return runner


def _manifest_success_triage(
    status: str,
    *,
    wrong_context_type: bool = False,
) -> Callable[[TriageOptions], TriageResult]:
    def runner(options: TriageOptions) -> TriageResult:
        assert options.output_dir is not None
        assert options.spec_name is not None
        output_dir = options.output_dir
        output_dir.mkdir(parents=True)
        report_path = output_dir / "report.md"
        report_path.write_text(
            "\n".join(
                [
                    "# report",
                    "- Change status: `NEW`",
                    "- Branch: `tizen`",
                    "- Patch set ref: `refs/changes/01/1/1`",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (output_dir / "src" / options.spec_name).mkdir(parents=True)
        (output_dir / "evidence_packet.json").write_text("{}", encoding="utf-8")
        (output_dir / f"{options.spec_name}.buildlog.txt").write_text(
            "PACKAGE LOG",
            encoding="utf-8",
        )
        patch_context = output_dir / "patch_context"
        patch_context.mkdir()
        if wrong_context_type:
            (patch_context / "context.md").mkdir()
        else:
            (patch_context / "context.md").write_text("# context\n", encoding="utf-8")
        (patch_context / "meta.json").write_text(
            json.dumps({"status": status}),
            encoding="utf-8",
        )
        return TriageResult(
            exit_code=0,
            status="success",
            output_dir=output_dir,
            report_path=report_path,
        )

    return runner


def _read_batch_manifest(result_path: Path) -> dict[str, Any]:
    return json.loads((result_path.parent / "batch_manifest.json").read_text(encoding="utf-8"))


def _manifest_package(manifest: dict[str, Any], spec_name: str) -> dict[str, Any]:
    packages = manifest["packages"]
    assert isinstance(packages, list)
    for item in packages:
        if item["spec_name"] == spec_name:
            return item
    raise AssertionError(f"manifest package {spec_name!r} not found")


def _manifest_error_row(error: str | None, state: str = STATE_NEEDS_INPUT) -> BatchRunRecord:
    return BatchRunRecord(
        build_id="111",
        arch="standard-armv7l",
        spec_name="demo",
        project=None,
        branch="tizen",
        commit=None,
        gerrit_status=None,
        patch_status=None,
        state=state,
        report_path=None,
        error=error,
        retries=0,
    )


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
        fetch_gbs_report("111", "standard-x86_64", cookie_path=cookie_path, fetcher=fetcher)

    assert exc.value.code == "NO_GBS_REPORT"


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
        fetch_gbs_report("111", "standard-x86_64", cookie_path=cookie_path, fetcher=fetcher)

    assert exc.value.code == "GBS_REPORT_DOWNLOAD_FAILED"


def test_default_gbs_report_arches_include_emulator_and_gcov() -> None:
    assert DEFAULT_ARCHES == (
        "standard-aarch64",
        "standard-armv7l",
        "standard-x86_64",
        "emulator-x86_64",
        "standard_gcov-armv7l",
    )
    assert BatchTriageOptions().arches == DEFAULT_ARCHES


def test_quickbuild_url_normalization_quotes_raw_spaces_idempotently() -> None:
    raw = (
        "https://quickbuild.tizen.org/download/111/html/"
        "GBS Reports@^@standard-aarch64/index.html"
    )
    encoded = (
        "https://quickbuild.tizen.org/download/111/html/"
        "GBS%20Reports@%5E@standard-aarch64/index.html"
    )

    assert normalize_quickbuild_url(raw) == encoded
    assert normalize_quickbuild_url(encoded) == encoded


def test_batch_orchestrator_reports_success_and_marks_processed(tmp_path: Path) -> None:
    orchestrator = CiTriageOrchestrator(
        source=_FakeSource([_failed_build("111")]),
        options=BatchTriageOptions(
            state_root=tmp_path / ".ci_triage",
            cookie_path=tmp_path / "cookies.json",
            run_date="2026-07-03",
            arches=("standard-armv7l",),
        ),
        full_log_downloader=lambda build_id, cookie_path: _full_log_for("foo"),
        gbs_report_discoverer=_gbs_discoverer(_gbs_package("foo")),
        package_log_downloader=lambda package, cookie_path: "PACKAGE LOG",
        triage_runner=_successful_triage("not_applicable"),
        clock=lambda: datetime(2026, 7, 3, 9, 0, 0),
    )

    result = orchestrator.run(datetime(2026, 7, 2, 0, 0, 0))

    assert result.package_units == 1
    state = json.loads((tmp_path / ".ci_triage/state/111.json").read_text(encoding="utf-8"))
    package = state["packages"]["standard-armv7l/foo"]
    assert package["state"] == STATE_REPORTED
    assert package["arch"] == "standard-armv7l"
    assert package["commit"] == "foo-commit"
    assert package["patch_status"] == "not_applicable"
    assert package["gerrit_status"] == "NEW"
    assert package["patchset_ref"] == "refs/changes/01/1/1"
    processed = json.loads((tmp_path / ".ci_triage/processed.json").read_text(encoding="utf-8"))
    assert processed == {"111": {"standard-armv7l": ["foo"]}}
    report = result.daily_report_path.read_text(encoding="utf-8")
    assert "- Not applicable: 1" in report
    assert (
        "| 111 | standard-armv7l | foo | foo-commit | NEW | not_applicable | REPORTED |"
        in report
    )


def test_batch_manifest_includes_success_and_failure_units_with_stable_schema(
    tmp_path: Path,
) -> None:
    orchestrator = CiTriageOrchestrator(
        source=_FakeSource([_failed_build("111")]),
        options=BatchTriageOptions(
            state_root=tmp_path / ".ci_triage",
            cookie_path=tmp_path / "cookies.json",
            run_date="2026-07-03",
            arches=("standard-armv7l",),
        ),
        full_log_downloader=lambda build_id, cookie_path: _full_log_for("good"),
        gbs_report_discoverer=_gbs_discoverer(
            _gbs_package("good"),
            _gbs_package("missing"),
        ),
        package_log_downloader=lambda package, cookie_path: "PACKAGE LOG",
        triage_runner=_manifest_success_triage("source_context_available"),
        clock=lambda: datetime(2026, 7, 3, 9, 0, 0),
    )

    result = orchestrator.run(datetime(2026, 7, 2, 0, 0, 0))
    report_text = result.daily_report_path.read_text(encoding="utf-8")
    manifest = _read_batch_manifest(result.daily_report_path)

    assert "batch_manifest.json" not in report_text
    assert manifest["schema_version"] == "ci_triage/batch_manifest/v1"
    assert manifest["generated_at"] == "2026-07-03T09:00:00"
    assert manifest["run_date"] == "2026-07-03"
    assert len(manifest["packages"]) == 2
    keys = {item["unit_key"] for item in manifest["packages"]}
    assert keys == {
        "111:standard-armv7l:good",
        "111:standard-armv7l:missing",
    }
    assert len(keys) == len(manifest["packages"])

    for item in manifest["packages"]:
        assert set(item) == EXPECTED_MANIFEST_UNIT_KEYS, f"schema drift: {item['unit_key']}"

    success = _manifest_package(manifest, "good")
    assert success["state"] == STATE_REPORTED
    assert success["patch_status"] == "source_context_available"
    assert success["project"] == "platform/test/good"
    assert success["base_commit"] == "good-commit"
    assert success["branch"] == "tizen"
    assert success["error"] is None
    assert success["src_clean"] is not None
    assert success["evidence_packet"] is not None
    assert success["patch_context"] is not None
    assert Path(success["src_clean"]).is_absolute()
    assert Path(success["src_clean"]).is_dir()
    for key in [
        "evidence_packet",
        "patch_context",
        "patch_context_meta",
        "report",
        "package_buildlog",
    ]:
        assert Path(success[key]).is_absolute()
        assert Path(success[key]).is_file()

    failed = _manifest_package(manifest, "missing")
    assert failed["unit_key"] == "111:standard-armv7l:missing"
    assert failed["state"] == STATE_NEEDS_INPUT
    assert failed["patch_status"] is None
    assert failed["project"] is None
    assert failed["base_commit"] is None
    assert failed["branch"] == "tizen"
    assert failed["error"] is not None
    assert set(failed["error"]) == {"code", "message"}
    assert failed["error"]["code"] == "PROJECT_COMMIT_NOT_FOUND"
    assert "missing" in failed["error"]["message"]
    for key in [
        "src_clean",
        "evidence_packet",
        "patch_context",
        "patch_context_meta",
        "report",
        "package_buildlog",
    ]:
        assert failed[key] is None


def test_batch_manifest_nulls_paths_when_existing_path_has_wrong_type(
    tmp_path: Path,
) -> None:
    orchestrator = CiTriageOrchestrator(
        source=_FakeSource([_failed_build("111")]),
        options=BatchTriageOptions(
            state_root=tmp_path / ".ci_triage",
            run_date="2026-07-03",
            arches=("standard-armv7l",),
        ),
        full_log_downloader=lambda build_id, cookie_path: _full_log_for("foo"),
        gbs_report_discoverer=_gbs_discoverer(_gbs_package("foo")),
        package_log_downloader=lambda package, cookie_path: "PACKAGE LOG",
        triage_runner=_manifest_success_triage(
            "source_context_available",
            wrong_context_type=True,
        ),
        clock=lambda: datetime(2026, 7, 3, 9, 0, 0),
    )

    result = orchestrator.run(datetime(2026, 7, 2, 0, 0, 0))
    manifest = _read_batch_manifest(result.daily_report_path)
    package = _manifest_package(manifest, "foo")

    assert set(package) == EXPECTED_MANIFEST_UNIT_KEYS
    assert (Path(package["patch_context_meta"])).is_file()
    assert package["patch_context"] is None


@pytest.mark.parametrize(
    ("text", "expected_code", "expected_message"),
    [
        (
            "PROJECT_COMMIT_NOT_FOUND: no matching project",
            "PROJECT_COMMIT_NOT_FOUND",
            "no matching project",
        ),
        (
            "GBS_REPORT_DOWNLOAD_FAILED: HTTP 500",
            "GBS_REPORT_DOWNLOAD_FAILED",
            "HTTP 500",
        ),
        ("ERROR2: something", "ERROR2", "something"),
    ],
)
def test_manifest_error_splits_uppercase_error_code_prefixes(
    text: str,
    expected_code: str,
    expected_message: str,
) -> None:
    error = _manifest_error(_manifest_error_row(text))

    assert error == {"code": expected_code, "message": expected_message}


@pytest.mark.parametrize(
    "text",
    [
        (
            "GBS Reports contained no failed package rows "
            "(scanned arches: standard-aarch64, standard-armv7l)"
        ),
        "scanned arches: a, b",
        "Some Error: detail",
        "failed to fetch https://example.com/x: HTTP 404",
        "plain error text",
    ],
)
def test_manifest_error_does_not_split_non_error_code_colons(text: str) -> None:
    error = _manifest_error(_manifest_error_row(text))

    assert error == {"code": STATE_NEEDS_INPUT, "message": text}


@pytest.mark.parametrize("state", [STATE_REPORTED, STATE_SKIPPED_PROCESSED])
def test_manifest_error_returns_none_for_success_or_skipped_without_error(state: str) -> None:
    assert _manifest_error(_manifest_error_row(None, state=state)) is None


def test_batch_orchestrator_skips_processed_package(tmp_path: Path) -> None:
    state_root = tmp_path / ".ci_triage"
    state_root.mkdir()
    (state_root / "processed.json").write_text(
        json.dumps({"111": {"standard-armv7l": ["foo"]}}),
        encoding="utf-8",
    )
    calls: list[TriageOptions] = []

    orchestrator = CiTriageOrchestrator(
        source=_FakeSource([_failed_build("111")]),
        options=BatchTriageOptions(
            state_root=state_root,
            run_date="2026-07-03",
            arches=("standard-armv7l",),
        ),
        full_log_downloader=lambda build_id, cookie_path: _full_log_for("foo"),
        gbs_report_discoverer=_gbs_discoverer(_gbs_package("foo")),
        package_log_downloader=lambda package, cookie_path: "PACKAGE LOG",
        triage_runner=lambda options: calls.append(options) or _successful_triage("x")(options),
        clock=lambda: datetime(2026, 7, 3, 9, 0, 0),
    )

    orchestrator.run(datetime(2026, 7, 2, 0, 0, 0))

    assert calls == []
    state = json.loads((state_root / "state/111.json").read_text(encoding="utf-8"))
    assert state["packages"]["standard-armv7l/foo"]["state"] == STATE_SKIPPED_PROCESSED


def test_batch_orchestrator_isolates_package_failures(tmp_path: Path) -> None:
    def triage_runner(options: TriageOptions) -> TriageResult:
        assert options.output_dir is not None
        options.output_dir.mkdir(parents=True)
        report_path = options.output_dir / "report.md"
        report_path.write_text("# report\n", encoding="utf-8")
        if options.spec_name == "bad":
            return TriageResult(
                exit_code=1,
                status="ANALYZER_FAILED",
                output_dir=options.output_dir,
                report_path=report_path,
                error="analyzer crashed",
            )
        (options.output_dir / "patch_context").mkdir()
        (options.output_dir / "patch_context/meta.json").write_text(
            json.dumps({"status": "fix_all_context_available"}),
            encoding="utf-8",
        )
        return TriageResult(
            exit_code=0,
            status="success",
            output_dir=options.output_dir,
            report_path=report_path,
        )

    state_root = tmp_path / ".ci_triage"
    orchestrator = CiTriageOrchestrator(
        source=_FakeSource([_failed_build("111")]),
        options=BatchTriageOptions(
            state_root=state_root,
            run_date="2026-07-03",
            arches=("standard-armv7l",),
        ),
        full_log_downloader=lambda build_id, cookie_path: _full_log_for("good", "bad"),
        gbs_report_discoverer=_gbs_discoverer(_gbs_package("good"), _gbs_package("bad")),
        package_log_downloader=lambda package, cookie_path: "PACKAGE LOG",
        triage_runner=triage_runner,
        clock=lambda: datetime(2026, 7, 3, 9, 0, 0),
    )

    orchestrator.run(datetime(2026, 7, 2, 0, 0, 0))

    state = json.loads((state_root / "state/111.json").read_text(encoding="utf-8"))
    assert state["packages"]["standard-armv7l/good"]["state"] == STATE_REPORTED
    assert state["packages"]["standard-armv7l/bad"]["state"] == STATE_FAILED_ANALYZE
    assert state["packages"]["standard-armv7l/bad"]["retries"] == 1
    processed = json.loads((state_root / "processed.json").read_text(encoding="utf-8"))
    assert processed == {"111": {"standard-armv7l": ["good"]}}


def test_batch_orchestrator_isolates_build_log_failure(tmp_path: Path) -> None:
    def downloader(build_id: str, cookie_path: Path) -> str:
        if build_id == "111":
            raise QuickBuildError("COOKIE_EXPIRED", "please log in")
        return _full_log_for("foo")

    orchestrator = CiTriageOrchestrator(
        source=_FakeSource([_failed_build("111"), _failed_build("222")]),
        options=BatchTriageOptions(
            state_root=tmp_path / ".ci_triage",
            run_date="2026-07-03",
            arches=("standard-armv7l",),
        ),
        full_log_downloader=downloader,
        gbs_report_discoverer=_gbs_discoverer(_gbs_package("foo")),
        package_log_downloader=lambda package, cookie_path: "PACKAGE LOG",
        triage_runner=_successful_triage("fix_all_context_available"),
        clock=lambda: datetime(2026, 7, 3, 9, 0, 0),
    )

    orchestrator.run(datetime(2026, 7, 2, 0, 0, 0))

    failed_state = json.loads(
        (tmp_path / ".ci_triage/state/111.json").read_text(encoding="utf-8")
    )
    success_state = json.loads(
        (tmp_path / ".ci_triage/state/222.json").read_text(encoding="utf-8")
    )
    assert failed_state["state"] == STATE_FAILED_LOG
    assert success_state["packages"]["standard-armv7l/foo"]["state"] == STATE_REPORTED


def test_batch_orchestrator_marks_no_gbs_report_as_reported_no_report(
    tmp_path: Path,
) -> None:
    def discover(build_id: str, arch: str, cookie_path: Path) -> tuple[GbsReportPackage, ...]:
        raise QuickBuildError(
            "NO_GBS_REPORT",
            f"build {build_id}/{arch} has no GBS report iframe",
        )

    state_root = tmp_path / ".ci_triage"
    orchestrator = CiTriageOrchestrator(
        source=_FakeSource([_failed_build("111")]),
        options=BatchTriageOptions(
            state_root=state_root,
            run_date="2026-07-03",
            arches=("standard-armv7l",),
        ),
        full_log_downloader=lambda build_id, cookie_path: _full_log_for("foo"),
        gbs_report_discoverer=discover,
        triage_runner=_successful_triage("fix_all_context_available"),
        clock=lambda: datetime(2026, 7, 3, 9, 0, 0),
    )

    result = orchestrator.run(datetime(2026, 7, 2, 0, 0, 0))

    state = json.loads((state_root / "state/111.json").read_text(encoding="utf-8"))
    package = state["packages"]["standard-armv7l/__NO_GBS_REPORT__"]
    assert package["state"] == STATE_REPORTED_NO_REPORT
    assert package["retries"] == 0
    assert "unknown-arch/<unknown>" not in state["packages"]
    processed = json.loads((state_root / "processed.json").read_text(encoding="utf-8"))
    assert processed == {"111": {"standard-armv7l": ["__NO_GBS_REPORT__"]}}
    report = result.daily_report_path.read_text(encoding="utf-8")
    assert "- No GBS report: 1 unit across 1 build" in report
    assert "## No GBS Report (non-package builds)" in report
    assert "| 111 | standard-armv7l | __NO_GBS_REPORT__ |" in report
    assert "| 111 | standard-armv7l | https://quickbuild.tizen.org/build/111 |" in report
    assert "1 arches" not in report
    assert "https://quickbuild.tizen.org/build/111" in report


def test_daily_report_folds_no_gbs_report_rows_but_manifest_keeps_units(
    tmp_path: Path,
) -> None:
    def discover(build_id: str, arch: str, cookie_path: Path) -> tuple[GbsReportPackage, ...]:
        raise QuickBuildError(
            "NO_GBS_REPORT",
            f"build {build_id}/{arch} has no GBS report iframe",
        )

    state_root = tmp_path / ".ci_triage"
    orchestrator = CiTriageOrchestrator(
        source=_FakeSource([_failed_build("111")]),
        options=BatchTriageOptions(
            state_root=state_root,
            run_date="2026-07-03",
        ),
        full_log_downloader=lambda build_id, cookie_path: _full_log_for("foo"),
        gbs_report_discoverer=discover,
        triage_runner=_successful_triage("x"),
        clock=lambda: datetime(2026, 7, 3, 9, 0, 0),
    )

    result = orchestrator.run(datetime(2026, 7, 2, 0, 0, 0))

    arch_cell = f"{len(DEFAULT_ARCHES)} arches ({', '.join(DEFAULT_ARCHES)})"
    report = result.daily_report_path.read_text(encoding="utf-8")
    assert "- No GBS report: 5 units across 1 build" in report
    assert report.count(f"| 111 | {arch_cell} |") == 2
    assert report.count("__NO_GBS_REPORT__") == 1

    manifest = _read_batch_manifest(result.daily_report_path)
    packages = manifest["packages"]
    assert len(packages) == len(DEFAULT_ARCHES)
    by_arch = {item["arch"]: item for item in packages}
    assert tuple(by_arch) == DEFAULT_ARCHES
    for arch in DEFAULT_ARCHES:
        item = by_arch[arch]
        assert item["unit_key"] == f"111:{arch}:__NO_GBS_REPORT__"
        assert item["arch"] == arch
        assert item["state"] == STATE_REPORTED_NO_REPORT
        assert item["patch_status"] is None
        assert item["error"]["code"] == STATE_REPORTED_NO_REPORT
        for key in [
            "src_clean",
            "evidence_packet",
            "patch_context",
            "patch_context_meta",
            "report",
            "package_buildlog",
        ]:
            assert item[key] is None


def test_daily_report_folds_no_gbs_report_once_per_build(tmp_path: Path) -> None:
    def discover(build_id: str, arch: str, cookie_path: Path) -> tuple[GbsReportPackage, ...]:
        raise QuickBuildError(
            "NO_GBS_REPORT",
            f"build {build_id}/{arch} has no GBS report iframe",
        )

    orchestrator = CiTriageOrchestrator(
        source=_FakeSource([_failed_build("111"), _failed_build("222")]),
        options=BatchTriageOptions(
            state_root=tmp_path / ".ci_triage",
            run_date="2026-07-03",
            arches=("standard-armv7l",),
        ),
        full_log_downloader=lambda build_id, cookie_path: _full_log_for("foo"),
        gbs_report_discoverer=discover,
        triage_runner=_successful_triage("x"),
        clock=lambda: datetime(2026, 7, 3, 9, 0, 0),
    )

    result = orchestrator.run(datetime(2026, 7, 2, 0, 0, 0))

    report = result.daily_report_path.read_text(encoding="utf-8")
    assert "- No GBS report: 2 units across 2 builds" in report
    assert report.count("__NO_GBS_REPORT__") == 2
    assert "| 111 | standard-armv7l | https://quickbuild.tizen.org/build/111 |" in report
    assert "| 222 | standard-armv7l | https://quickbuild.tizen.org/build/222 |" in report


def test_daily_report_preserves_row_order_when_folding_no_gbs_report(
    tmp_path: Path,
) -> None:
    def discover(build_id: str, arch: str, cookie_path: Path) -> tuple[GbsReportPackage, ...]:
        if arch == "standard-armv7l":
            return (_gbs_package("good", arch=arch),)
        raise QuickBuildError(
            "NO_GBS_REPORT",
            f"build {build_id}/{arch} has no GBS report iframe",
        )

    orchestrator = CiTriageOrchestrator(
        source=_FakeSource([_failed_build("111")]),
        options=BatchTriageOptions(
            state_root=tmp_path / ".ci_triage",
            run_date="2026-07-03",
            arches=("standard-armv7l", "standard-x86_64", "emulator-x86_64"),
        ),
        full_log_downloader=lambda build_id, cookie_path: _full_log_for("good"),
        gbs_report_discoverer=discover,
        package_log_downloader=lambda package, cookie_path: "PACKAGE LOG",
        triage_runner=_successful_triage("not_applicable"),
        clock=lambda: datetime(2026, 7, 3, 9, 0, 0),
    )

    result = orchestrator.run(datetime(2026, 7, 2, 0, 0, 0))

    report = result.daily_report_path.read_text(encoding="utf-8")
    reported_row = (
        "| 111 | standard-armv7l | good | good-commit | NEW | not_applicable | REPORTED |"
    )
    folded_row = (
        "| 111 | 2 arches (standard-x86_64, emulator-x86_64) | "
        "__NO_GBS_REPORT__ |"
    )
    assert reported_row in report
    assert folded_row in report
    assert report.index(reported_row) < report.index(folded_row)
    assert report.count("__NO_GBS_REPORT__") == 1


def test_batch_orchestrator_maps_gbs_report_download_failure_to_failed_log(
    tmp_path: Path,
) -> None:
    def discover(build_id: str, arch: str, cookie_path: Path) -> tuple[GbsReportPackage, ...]:
        raise QuickBuildError(
            "GBS_REPORT_DOWNLOAD_FAILED",
            f"failed to download GBS report for {build_id}/{arch}",
        )

    state_root = tmp_path / ".ci_triage"
    orchestrator = CiTriageOrchestrator(
        source=_FakeSource([_failed_build("111")]),
        options=BatchTriageOptions(
            state_root=state_root,
            run_date="2026-07-03",
            arches=("standard-armv7l",),
        ),
        full_log_downloader=lambda build_id, cookie_path: _full_log_for("foo"),
        gbs_report_discoverer=discover,
        triage_runner=_successful_triage("x"),
        clock=lambda: datetime(2026, 7, 3, 9, 0, 0),
    )

    orchestrator.run(datetime(2026, 7, 2, 0, 0, 0))

    state = json.loads((state_root / "state/111.json").read_text(encoding="utf-8"))
    package = state["packages"]["standard-armv7l/<unknown>"]
    assert package["state"] == STATE_FAILED_LOG
    assert package["retries"] == 1
    processed_path = state_root / "processed.json"
    if processed_path.exists():
        assert json.loads(processed_path.read_text(encoding="utf-8")) == {}


def test_batch_orchestrator_skips_processed_no_gbs_report_without_fetching(
    tmp_path: Path,
) -> None:
    state_root = tmp_path / ".ci_triage"
    state_root.mkdir()
    (state_root / "processed.json").write_text(
        json.dumps({"111": {"standard-armv7l": ["__NO_GBS_REPORT__"]}}),
        encoding="utf-8",
    )
    calls = 0

    def discover(build_id: str, arch: str, cookie_path: Path) -> tuple[GbsReportPackage, ...]:
        nonlocal calls
        calls += 1
        return ()

    orchestrator = CiTriageOrchestrator(
        source=_FakeSource([_failed_build("111")]),
        options=BatchTriageOptions(
            state_root=state_root,
            run_date="2026-07-03",
            arches=("standard-armv7l",),
        ),
        full_log_downloader=lambda build_id, cookie_path: _full_log_for("foo"),
        gbs_report_discoverer=discover,
        triage_runner=_successful_triage("x"),
        clock=lambda: datetime(2026, 7, 3, 9, 0, 0),
    )

    orchestrator.run(datetime(2026, 7, 2, 0, 0, 0))

    assert calls == 0
    state = json.loads((state_root / "state/111.json").read_text(encoding="utf-8"))
    assert state["packages"]["standard-armv7l/__NO_GBS_REPORT__"]["state"] == (
        STATE_SKIPPED_PROCESSED
    )
    assert "unknown-arch/<unknown>" not in state["packages"]


def test_batch_orchestrator_marks_failed_package_permanent_at_retry_limit(
    tmp_path: Path,
) -> None:
    state_root = tmp_path / ".ci_triage"
    (state_root / "state").mkdir(parents=True)
    (state_root / "state/111.json").write_text(
        json.dumps(
            {
                "build_id": "111",
                "discovered_at": "2026-07-03T09:00:00",
                "begin_date": "2026-07-01 03:43:00",
                "state": "LOG_FETCHED",
                "packages": {
                    "standard-armv7l/foo": {
                        "arch": "standard-armv7l",
                        "spec_name": "foo",
                        "state": "FAILED_ANALYZE",
                        "retries": 3,
                        "error": "old failure",
                        "transitions": [],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    calls: list[TriageOptions] = []
    orchestrator = CiTriageOrchestrator(
        source=_FakeSource([_failed_build("111")]),
        options=BatchTriageOptions(
            state_root=state_root,
            run_date="2026-07-03",
            arches=("standard-armv7l",),
        ),
        full_log_downloader=lambda build_id, cookie_path: _full_log_for("foo"),
        gbs_report_discoverer=_gbs_discoverer(_gbs_package("foo")),
        package_log_downloader=lambda package, cookie_path: "PACKAGE LOG",
        triage_runner=lambda options: calls.append(options) or _successful_triage("x")(options),
        clock=lambda: datetime(2026, 7, 3, 9, 0, 0),
    )

    orchestrator.run(datetime(2026, 7, 2, 0, 0, 0))

    assert calls == []
    state = json.loads((state_root / "state/111.json").read_text(encoding="utf-8"))
    assert state["packages"]["standard-armv7l/foo"]["state"] == STATE_FAILED_PERMANENT
    assert state["packages"]["standard-armv7l/foo"]["retries"] == 3


def test_batch_orchestrator_marks_missing_failed_package_rows_as_needs_input(
    tmp_path: Path,
) -> None:
    orchestrator = CiTriageOrchestrator(
        source=_FakeSource([_failed_build("111")]),
        options=BatchTriageOptions(
            state_root=tmp_path / ".ci_triage",
            run_date="2026-07-03",
            arches=("standard-armv7l",),
        ),
        full_log_downloader=lambda build_id, cookie_path: (
            "build_pkg_list_dic: {'platform/test/foo': 'foo-commit'}"
        ),
        gbs_report_discoverer=lambda build_id, arch, cookie_path: (),
        package_log_downloader=lambda package, cookie_path: "PACKAGE LOG",
        triage_runner=_successful_triage("x"),
        clock=lambda: datetime(2026, 7, 3, 9, 0, 0),
    )

    result = orchestrator.run(datetime(2026, 7, 2, 0, 0, 0))

    state = json.loads((tmp_path / ".ci_triage/state/111.json").read_text(encoding="utf-8"))
    package = state["packages"]["unknown-arch/<unknown>"]
    assert package["state"] == STATE_NEEDS_INPUT
    assert package["retries"] == 0
    assert "no failed package rows" in package["error"]
    assert package["error"] == (
        "GBS Reports contained no failed package rows "
        "(scanned arches: standard-armv7l)"
    )
    manifest = _read_batch_manifest(result.daily_report_path)
    missing = _manifest_package(manifest, "<unknown>")
    assert missing["unit_key"] == "111:unknown-arch:<unknown>"
    assert missing["arch"] == "unknown-arch"
    assert missing["spec_name"] == "<unknown>"
    assert missing["error"]["message"] == package["error"]


def test_quickbuild_source_discovers_failed_builds_from_overview(tmp_path: Path) -> None:
    cookie_path = _cookie_file(tmp_path)
    calls: list[str] = []

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        calls.append(url)
        assert cookies == {"JSESSIONID_8810": "session-value"}
        return HttpResponse(status=200, url=url, body=OVERVIEW_HTML.encode())

    source = QuickBuildSource(cookie_path=cookie_path, fetcher=fetcher)
    builds = source.discover(datetime(2026, 6, 1, 0, 0, 0))

    assert calls == ["https://quickbuild.tizen.org/overview/1930"]
    assert [build.build_id for build in builds] == [
        "1118258",
        "1117858",
        "1115346",
        "1114933",
        "1114499",
    ]
    assert builds[0].source == "quickbuild"
    assert builds[0].status == "failed"
    assert builds[0].version == "20260701.034300"
    assert builds[0].begin_date == datetime(2026, 7, 1, 3, 43, 0)
    assert builds[0].quickbuild_url == "https://quickbuild.tizen.org/build/1118258"
    assert source.warnings == [
        "QuickBuild overview lists at least 10 builds and the oldest listed build "
        "is still in the requested window; history may contain more builds."
    ]


def test_quickbuild_source_uses_configured_overview_id(tmp_path: Path) -> None:
    cookie_path = _cookie_file(tmp_path)
    calls: list[str] = []

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        calls.append(url)
        return HttpResponse(status=200, url=url, body=OVERVIEW_HTML.encode())

    source = QuickBuildSource(
        cookie_path=cookie_path,
        fetcher=fetcher,
        overview_config_id="2042",
    )
    source.discover(datetime(2026, 7, 1, 3, 0, 0))

    assert calls == ["https://quickbuild.tizen.org/overview/2042"]


@pytest.mark.parametrize(
    "overview_config_id",
    [
        "abc",
        "https://quickbuild.tizen.org/overview/1934",
        "",
    ],
)
def test_quickbuild_source_rejects_invalid_overview_id_before_io(
    tmp_path: Path,
    overview_config_id: str,
) -> None:
    cookie_path = tmp_path / "missing-cookies.json"
    calls: list[str] = []

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        calls.append(url)
        return HttpResponse(status=200, url=url, body=OVERVIEW_HTML.encode())

    source = QuickBuildSource(
        cookie_path=cookie_path,
        fetcher=fetcher,
        overview_config_id=overview_config_id,
    )

    with pytest.raises(QuickBuildError) as exc:
        source.discover(datetime(2026, 7, 1, 3, 0, 0))

    assert exc.value.code == "INVALID_OVERVIEW_ID"
    assert repr(overview_config_id) in str(exc.value)
    assert "numeric configuration id" in str(exc.value)
    assert calls == []


def test_quickbuild_source_filters_since_lower_bound(tmp_path: Path) -> None:
    cookie_path = _cookie_file(tmp_path)

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        return HttpResponse(status=200, url=url, body=OVERVIEW_HTML.encode())

    source = QuickBuildSource(cookie_path=cookie_path, fetcher=fetcher)
    builds = source.discover(datetime(2026, 7, 1, 3, 0, 0))

    assert [build.build_id for build in builds] == ["1118258"]
    assert source.warnings == []


def test_quickbuild_source_keeps_non_snapshot_version_text(tmp_path: Path) -> None:
    cookie_path = _cookie_file(tmp_path)
    html = OVERVIEW_HTML.replace("build-status successful", "build-status failed", 1)

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        return HttpResponse(status=200, url=url, body=html.encode())

    builds = QuickBuildSource(cookie_path=cookie_path, fetcher=fetcher).discover(
        datetime(2026, 6, 30, 20, 0, 0)
    )

    assert [build.version for build in builds[:2]] == [
        "20260701.034300",
        "20260630.210000",
    ]


def test_quickbuild_source_reports_expired_cookie_when_overview_has_no_builds_table(
    tmp_path: Path,
) -> None:
    cookie_path = _cookie_file(tmp_path)

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        return HttpResponse(status=200, url=url, body=b"<html><body>signin</body></html>")

    source = QuickBuildSource(cookie_path=cookie_path, fetcher=fetcher)
    with pytest.raises(QuickBuildError, match="cookie may have expired") as exc:
        source.discover(datetime(2026, 7, 1, 0, 0, 0))

    message = str(exc.value)
    assert exc.value.code == "COOKIE_EXPIRED"
    assert "https://quickbuild.tizen.org/overview/1930" in message
    assert str(cookie_path) in message
    assert "overview id may not exist" in message
    assert "check --overview-id" in message


def test_download_full_log_resolves_wicket_download_link(tmp_path: Path) -> None:
    cookie_path = _cookie_file(tmp_path)
    calls: list[str] = []

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        calls.append(url)
        assert cookies == {"JSESSIONID_8810": "session-value"}
        if url.endswith("/build/1118282/log"):
            return HttpResponse(
                status=200,
                url=url,
                body=(
                    b'<a href="../wicket/page?21-1.ILinkListener-content-buildTab-panel-'
                    b'download">Save</a>'
                ),
            )
        return HttpResponse(status=200, url=url, body=b"FULL LOG")

    result = download_full_log("1118282", cookie_path=cookie_path, fetcher=fetcher)

    assert result.full_log == "FULL LOG"
    assert calls == [
        "https://quickbuild.tizen.org/build/1118282/log",
        "https://quickbuild.tizen.org/build/wicket/page?21-1.ILinkListener-content-buildTab-panel-download",
    ]


def test_download_full_log_reports_expired_cookie(tmp_path: Path) -> None:
    cookie_path = _cookie_file(tmp_path)

    def fetcher(url: str, cookies: Mapping[str, str]) -> HttpResponse:
        return HttpResponse(
            status=200,
            url="https://quickbuild.tizen.org/signin?redirect-url-after-sign-in=x",
            body=b"<html>signin</html>",
        )

    with pytest.raises(QuickBuildError, match="cookie expired"):
        download_full_log("1118282", cookie_path=cookie_path, fetcher=fetcher)


def test_parse_full_log_package_mapping_and_failed_package() -> None:
    full_log = "\n".join(
        [
            "04:04 INFO - build_pkg_list_dic: "
            "{'platform/upstream/lightweight-web-engine': 'abc123', "
            "'platform/framework/web/lwnode': 'def456'}",
            "09:07 INFO - fail_pkg: lightweight-web-engine-1.3.31-1, "
            "spec_name: lightweight-web-engine, "
            "dest_file: /failed/lightweight-web-engine.buildlog.txt",
        ]
    )

    mapping = parse_build_pkg_list(full_log)
    failed = parse_failed_packages(full_log)
    selected = select_failed_package(failed, spec_name=None)
    project, commit = match_pkg_key(selected.spec_name, mapping)

    assert mapping["platform/upstream/lightweight-web-engine"] == "abc123"
    assert selected.spec_name == "lightweight-web-engine"
    assert selected.fail_pkg == "lightweight-web-engine-1.3.31-1"
    assert project == "platform/upstream/lightweight-web-engine"
    assert commit == "abc123"


def test_match_pkg_key_supports_tizen_hal_and_capi_prefix_mapping() -> None:
    mapping = {
        "platform/hal/api/drm": "drm-commit",
        "platform/hal/api/hdcp": "hdcp-commit",
        "platform/core/api/inputmethod": "inputmethod-commit",
        "platform/core/appfw/united-service": "united-commit",
        "platform/core/system/sessiond": "sessiond-commit",
        "profile/common/apps/native/enlightenment": "enlightenment-commit",
        "platform/adaptation/libtdm-drm": "tdm-commit",
        "platform/hal/backend/drm-generic": "backend-commit",
    }

    assert match_pkg_key("hal-api-drm", mapping) == ("platform/hal/api/drm", "drm-commit")
    assert match_pkg_key("hal-api-hdcp", mapping) == ("platform/hal/api/hdcp", "hdcp-commit")
    assert match_pkg_key("capi-ui-inputmethod", mapping) == (
        "platform/core/api/inputmethod",
        "inputmethod-commit",
    )
    assert match_pkg_key("united-service", mapping) == (
        "platform/core/appfw/united-service",
        "united-commit",
    )
    assert match_pkg_key("sessiond", mapping) == (
        "platform/core/system/sessiond",
        "sessiond-commit",
    )
    assert match_pkg_key("enlightenment", mapping) == (
        "profile/common/apps/native/enlightenment",
        "enlightenment-commit",
    )


def test_match_pkg_key_uses_exact_match_before_prefix_fallback() -> None:
    mapping = {
        "platform/core/api/inputmethod": "fallback-commit",
        "platform/core/api/capi-ui-inputmethod": "exact-commit",
    }

    assert match_pkg_key("capi-ui-inputmethod", mapping) == (
        "platform/core/api/capi-ui-inputmethod",
        "exact-commit",
    )


def test_match_pkg_key_reports_ambiguous_prefix_fallback() -> None:
    mapping = {
        "platform/core/api/inputmethod": "first",
        "platform/extra/api/inputmethod": "second",
    }

    with pytest.raises(QuickBuildLogError) as exc:
        match_pkg_key("capi-ui-inputmethod", mapping)

    assert exc.value.code == "PROJECT_COMMIT_AMBIGUOUS"
    assert "platform/core/api/inputmethod" in str(exc.value)
    assert "platform/extra/api/inputmethod" in str(exc.value)


def test_match_pkg_key_keeps_not_found_when_prefix_fallback_has_no_safe_match() -> None:
    mapping = {
        "platform/adaptation/libtdm-drm": "tdm-commit",
        "platform/hal/backend/drm-generic": "backend-commit",
        "platform/core/uifw/inputmethod": "uifw-commit",
    }

    with pytest.raises(QuickBuildLogError) as exc:
        match_pkg_key("hal-api-drm", mapping)
    assert exc.value.code == "PROJECT_COMMIT_NOT_FOUND"

    with pytest.raises(QuickBuildLogError) as exc:
        match_pkg_key("capi-ui-inputmethod", mapping)
    assert exc.value.code == "PROJECT_COMMIT_NOT_FOUND"


def test_derive_package_buildlog_url_from_quickbuild_dest_file() -> None:
    url = derive_package_buildlog_url(
        "/data/workspace/gbsbuild-ROOT/live/"
        "TIZEN_Tizen_Tizen-Unified-Toolchain_RBS_TRIGGER_20260701.034300/"
        "buildlogs/standard/armv7l/failed/lwnode.buildlog.txt"
    )

    assert url == (
        "http://download.tizen.org/RBS/TIZEN/Tizen/Tizen-Unified-Toolchain/"
        "tizen-unified-toolchain_20260701.034300/builddata/buildlogs/standard/"
        "armv7l/failed/lwnode.buildlog.txt"
    )


def test_multiple_failed_packages_require_explicit_spec_name() -> None:
    failed = parse_failed_packages(
        """
fail_pkg: lightweight-web-engine-1.3.31-1, spec_name: lightweight-web-engine
fail_pkg: lwnode-1.0.0-1, spec_name: lwnode
"""
    )

    with pytest.raises(QuickBuildLogError, match="multiple failed packages"):
        select_failed_package(failed, spec_name=None)

    assert select_failed_package(failed, spec_name="lwnode").spec_name == "lwnode"


def test_run_triage_continues_with_explicit_spec_name_when_failed_rows_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    full_log = "\n".join(
        [
            "04:04 INFO - build_pkg_list_dic: "
            "{'platform/core/appfw/united-service': "
            "'9e3ffb3ba9aedcc7244478539835d6916a479c66'}",
        ]
    )
    commands: list[list[str]] = []

    def fake_download(build_id: str, *, cookie_path: Path) -> SimpleNamespace:
        return SimpleNamespace(
            log_page_url=f"https://quickbuild.tizen.org/build/{build_id}/log",
            download_url="https://quickbuild.tizen.org/wicket/page?x-download",
            full_log=full_log,
        )

    def fake_fetch_source(
        project: str,
        commit_hash: str,
        destination: Path,
        *,
        subprocess_runner: Any,
        git_ssh_command: str | None,
    ) -> SourceFetchResult:
        assert project == "platform/core/appfw/united-service"
        assert destination == tmp_path / "out" / "1095511" / "src" / "united-service"
        destination.mkdir(parents=True)
        return SourceFetchResult(
            status="source_available",
            src_root=destination,
            remote_url=f"ssh://review.tizen.org:29418/{project}",
            change=None,
        )

    def fake_subprocess(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if "gbs_analyzer" in command:
            output_dir = Path(command[command.index("--output-dir") + 1])
            output_dir.mkdir(parents=True)
            (output_dir / "evidence_packet.json").write_text(
                json.dumps({"primary_error": {"kind": "raw_error", "message": "x"}}),
                encoding="utf-8",
            )
        if "gbs_patch_suggest" in command:
            output_dir = Path(command[command.index("--output-dir") + 1])
            output_dir.mkdir(parents=True)
            (output_dir / "meta.json").write_text(
                json.dumps({"status": "not_applicable"}),
                encoding="utf-8",
            )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("ci_triage.runner.download_full_log", fake_download)
    monkeypatch.setattr("ci_triage.runner.fetch_source_for_commit", fake_fetch_source)

    result = run_triage(
        TriageOptions(
            build_id="1095511",
            output_root=tmp_path / "out",
            cookie_path=tmp_path / "cookies.json",
            spec_name="united-service",
        ),
        subprocess_runner=fake_subprocess,
    )

    assert result.status == "success"
    report = result.report_path.read_text(encoding="utf-8")
    assert "using explicit `--spec-name`" not in report
    assert "using explicit --spec-name" in report
    analyzer_command = next(command for command in commands if "gbs_analyzer" in command)
    assert analyzer_command[analyzer_command.index("--package") + 1] == "united-service"


def test_run_triage_requires_arch_or_spec_name_for_auto_package_discovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_download(build_id: str, *, cookie_path: Path) -> SimpleNamespace:
        return SimpleNamespace(
            log_page_url=f"https://quickbuild.tizen.org/build/{build_id}/log",
            download_url="https://quickbuild.tizen.org/wicket/page?x-download",
            full_log="build_pkg_list_dic: {'platform/test/foo': 'foo-commit'}",
        )

    monkeypatch.setattr("ci_triage.runner.download_full_log", fake_download)

    result = run_triage(
        TriageOptions(
            build_id="111",
            output_root=tmp_path / "out",
            cookie_path=tmp_path / "cookies.json",
        )
    )

    assert result.status == "ARCH_REQUIRED"
    assert "requires --arch" in (result.error or "")


def test_run_triage_uses_gbs_report_package_log_when_arch_is_provided(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    full_log = "build_pkg_list_dic: {'platform/test/foo': 'foo-commit'}"
    commands: list[list[str]] = []

    def fake_download(build_id: str, *, cookie_path: Path) -> SimpleNamespace:
        return SimpleNamespace(
            log_page_url=f"https://quickbuild.tizen.org/build/{build_id}/log",
            download_url="https://quickbuild.tizen.org/wicket/page?x-download",
            full_log=full_log,
        )

    def fake_fetch_gbs_report(build_id: str, arch: str, *, cookie_path: Path) -> SimpleNamespace:
        assert arch == "standard-armv7l"
        return SimpleNamespace(failed_packages=(_gbs_package("foo", arch=arch),))

    def fake_download_gbs_log(package: GbsReportPackage, *, cookie_path: Path) -> str:
        assert package.spec_name == "foo"
        return "GBS PACKAGE LOG"

    def fake_fetch_source(
        project: str,
        commit_hash: str,
        destination: Path,
        *,
        subprocess_runner: Any,
        git_ssh_command: str | None,
    ) -> SourceFetchResult:
        assert project == "platform/test/foo"
        assert commit_hash == "foo-commit"
        assert destination == tmp_path / "out" / "111" / "src" / "foo"
        destination.mkdir(parents=True)
        return SourceFetchResult(
            status="source_available",
            src_root=destination,
            remote_url=f"ssh://review.tizen.org:29418/{project}",
            change=None,
        )

    def fake_subprocess(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if "gbs_analyzer" in command:
            buildlog = Path(command[command.index("analyze") + 1])
            assert buildlog.read_text(encoding="utf-8") == "GBS PACKAGE LOG"
            output_dir = Path(command[command.index("--output-dir") + 1])
            output_dir.mkdir(parents=True)
            (output_dir / "evidence_packet.json").write_text(
                json.dumps({"primary_error": {"kind": "raw_error", "message": "x"}}),
                encoding="utf-8",
            )
        if "gbs_patch_suggest" in command:
            output_dir = Path(command[command.index("--output-dir") + 1])
            output_dir.mkdir(parents=True)
            (output_dir / "meta.json").write_text(
                json.dumps({"status": "not_applicable"}),
                encoding="utf-8",
            )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("ci_triage.runner.download_full_log", fake_download)
    monkeypatch.setattr("ci_triage.runner.fetch_gbs_report", fake_fetch_gbs_report)
    monkeypatch.setattr("ci_triage.runner.download_gbs_package_buildlog", fake_download_gbs_log)
    monkeypatch.setattr("ci_triage.runner.fetch_source_for_commit", fake_fetch_source)

    result = run_triage(
        TriageOptions(
            build_id="111",
            output_root=tmp_path / "out",
            cookie_path=tmp_path / "cookies.json",
            arch="standard-armv7l",
        ),
        subprocess_runner=fake_subprocess,
    )

    assert result.status == "success"
    assert any("gbs_analyzer" in command for command in commands)


def test_find_patchset_by_revision_uses_matching_revision_not_current() -> None:
    change = {
        "patchSets": [
            {
                "number": 6,
                "revision": "ba0d7cc0f960da15cbd1134d213a3708dddde59f",
                "ref": "refs/changes/15/338415/6",
            },
            {
                "number": 7,
                "revision": "d4ce79de7e83e323aef427249eb4d0d2924d9263",
                "ref": "refs/changes/15/338415/7",
            },
        ]
    }

    patchset = find_patchset_by_revision(
        change,
        "ba0d7cc0f960da15cbd1134d213a3708dddde59f",
    )

    assert patchset is not None
    assert patchset.ref == "refs/changes/15/338415/6"


def test_fetch_source_for_new_change_fetches_matching_patchset_ref(tmp_path: Path) -> None:
    commands: list[list[str]] = []
    commit = "ba0d7cc0f960da15cbd1134d213a3708dddde59f"
    gerrit_output = "\n".join(
        [
            json.dumps(
                {
                    "project": "platform/upstream/lightweight-web-engine",
                    "branch": "tizen",
                    "status": "NEW",
                    "number": 338415,
                    "subject": "test",
                    "patchSets": [
                        {
                            "number": 6,
                            "revision": commit,
                            "ref": "refs/changes/15/338415/6",
                        },
                        {
                            "number": 7,
                            "revision": "d4ce79de7e83e323aef427249eb4d0d2924d9263",
                            "ref": "refs/changes/15/338415/7",
                        },
                    ],
                }
            ),
            json.dumps({"type": "stats", "rowCount": 1}),
        ]
    )

    def runner(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if command[:3] == ["ssh", "-p", "29418"]:
            return subprocess.CompletedProcess(command, 0, stdout=gerrit_output, stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = fetch_source_for_commit(
        "platform/upstream/lightweight-web-engine",
        commit,
        tmp_path / "src",
        subprocess_runner=runner,
    )

    assert result.status == "source_available"
    assert result.remote_url == "ssh://review.tizen.org:29418/platform/upstream/lightweight-web-engine"
    assert any("refs/changes/15/338415/6" in command for command in commands)
    assert not any("refs/changes/15/338415/7" in command for command in commands)


def test_run_triage_passes_cloned_src_root_to_analyzer_and_patch_suggest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    full_log = "\n".join(
        [
            "04:04 INFO - build_pkg_list_dic: "
            "{'platform/core/uifw/multi-assistant': "
            "'6341961cb6c81f938de60d86bf374685708867d2'}",
            "09:07 INFO - fail_pkg: multi-assistant-0.3.22-1, "
            "spec_name: multi-assistant, "
            "dest_file: /data/workspace/gbsbuild-ROOT/live/"
            "TIZEN_Tizen_Tizen-Unified-Toolchain_RBS_TRIGGER_20260701.034300/"
            "buildlogs/standard/armv7l/failed/multi-assistant.buildlog.txt",
        ]
    )
    src_root = tmp_path / "out" / "111" / "src" / "multi-assistant"
    commands: list[list[str]] = []

    def fake_download(build_id: str, *, cookie_path: Path) -> SimpleNamespace:
        assert build_id == "111"
        return SimpleNamespace(
            log_page_url="https://quickbuild.tizen.org/build/111/log",
            download_url="https://quickbuild.tizen.org/wicket/page?x-download",
            full_log=full_log,
        )

    def fake_fetch_source(
        project: str,
        commit_hash: str,
        destination: Path,
        *,
        subprocess_runner: Any,
        git_ssh_command: str | None,
    ) -> SourceFetchResult:
        assert project == "platform/core/uifw/multi-assistant"
        assert commit_hash == "6341961cb6c81f938de60d86bf374685708867d2"
        destination.mkdir(parents=True)
        change = GerritChange(
            project=project,
            branch="tizen",
            status="MERGED",
            number=344807,
            subject="test",
            url=None,
            matching_patchset=None,
        )
        return SourceFetchResult(
            status="source_available",
            src_root=destination,
            remote_url=f"ssh://review.tizen.org:29418/{project}",
            change=change,
        )

    def fake_download_package_buildlog(dest_file: str) -> PackageBuildLog:
        assert dest_file.endswith("/failed/multi-assistant.buildlog.txt")
        return PackageBuildLog(
            url="http://download.tizen.org/.../multi-assistant.buildlog.txt",
            text="PACKAGE BUILDLOG",
        )

    def fake_subprocess(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if "gbs_analyzer" in command:
            assert Path(command[command.index("analyze") + 1]).read_text(
                encoding="utf-8"
            ) == "PACKAGE BUILDLOG"
        if "gbs_analyzer" in command:
            output_dir = Path(command[command.index("--output-dir") + 1])
            output_dir.mkdir(parents=True)
            (output_dir / "evidence_packet.json").write_text(
                json.dumps(
                    {
                        "primary_error": {
                            "kind": "werror",
                            "message": "unknown warning option",
                        }
                    }
                ),
                encoding="utf-8",
            )
        if "gbs_patch_suggest" in command:
            output_dir = Path(command[command.index("--output-dir") + 1])
            output_dir.mkdir(parents=True)
            (output_dir / "meta.json").write_text(
                json.dumps({"status": "spec_toolchain_flag_context_available"}),
                encoding="utf-8",
            )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("ci_triage.runner.download_full_log", fake_download)
    monkeypatch.setattr("ci_triage.runner.fetch_source_for_commit", fake_fetch_source)
    monkeypatch.setattr(
        "ci_triage.runner.download_package_buildlog",
        fake_download_package_buildlog,
    )

    result = run_triage(
        TriageOptions(
            build_id="111",
            output_root=tmp_path / "out",
            cookie_path=tmp_path / "cookies.json",
            spec_name="multi-assistant",
        ),
        subprocess_runner=fake_subprocess,
    )

    assert result.status == "success"
    assert result.exit_code == 0
    analyzer_command = next(command for command in commands if "gbs_analyzer" in command)
    patch_command = next(command for command in commands if "gbs_patch_suggest" in command)
    assert analyzer_command[analyzer_command.index("--src-root") + 1] == str(src_root)
    assert patch_command[patch_command.index("--src-root") + 1] == str(src_root)
    report = result.report_path.read_text(encoding="utf-8")
    assert "spec_toolchain_flag_context_available" in report
    assert "platform/core/uifw/multi-assistant" in report


@pytest.mark.parametrize(
    ("spec_name", "expected"),
    [
        ("inference-engine-interface", "inference-engine-interface"),
        ("libfoo.bar", "libfoo.bar"),
    ],
)
def test_safe_pkg_dir_accepts_single_segment_package_names(
    spec_name: str,
    expected: str,
) -> None:
    assert _safe_pkg_dir(spec_name) == expected


@pytest.mark.parametrize(
    "spec_name",
    [
        "",
        ".",
        "..",
        "foo/bar",
        "foo\\bar",
        "bad\x00name",
    ],
)
def test_safe_pkg_dir_rejects_path_escape_inputs(spec_name: str) -> None:
    with pytest.raises(ValueError, match="unsafe spec_name"):
        _safe_pkg_dir(spec_name)
