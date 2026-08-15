"""Batch orchestration for QuickBuild CI triage."""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from tizen_ci_shared.env import discover_sibling_pythonpath
from tizen_ci_shared.quickbuild_http import DEFAULT_COOKIE_PATH, QuickBuildError, download_full_log
from tizen_ci_shared.types import FailedPackage

from ci_triage.gbs_report import (
    DEFAULT_ARCHES,
    GbsReportPackage,
    download_gbs_package_buildlog,
    fetch_gbs_report,
)
from ci_triage.quickbuild_log import (
    QuickBuildLogError,
    match_pkg_key,
    parse_build_pkg_list,
)
from ci_triage.runner import TriageOptions, TriageResult, run_triage
from ci_triage.sources import FailedBuild, FailedBuildSource, QuickBuildSource

STATE_DISCOVERED = "DISCOVERED"
STATE_LOG_FETCHED = "LOG_FETCHED"
STATE_ANALYZED = "ANALYZED"
STATE_SOURCE_FETCHED = "SOURCE_FETCHED"
STATE_PATCH_SUGGESTED = "PATCH_SUGGESTED"
STATE_REPORTED = "REPORTED"
STATE_REPORTED_NO_REPORT = "REPORTED_NO_REPORT"
STATE_SKIPPED_PROCESSED = "SKIPPED_PROCESSED"
STATE_NEEDS_INPUT = "NEEDS_INPUT"
STATE_FAILED_LOG = "FAILED_LOG"
STATE_FAILED_ANALYZE = "FAILED_ANALYZE"
STATE_FAILED_SOURCE = "FAILED_SOURCE"
STATE_FAILED_PATCH = "FAILED_PATCH"
STATE_FAILED_REPORT = "FAILED_REPORT"
STATE_FAILED_PERMANENT = "FAILED_PERMANENT"

UNKNOWN_SPEC_NAME = "<unknown>"
NO_GBS_REPORT_SPEC_NAME = "__NO_GBS_REPORT__"
PROCESSED_FILENAME = "processed.json"
BATCH_MANIFEST_SCHEMA = "ci_triage/batch_manifest/v1"


TriageRunner = Callable[[TriageOptions], TriageResult]
FullLogDownloader = Callable[[str, Path], str]
GbsReportDiscoverer = Callable[[str, str, Path], tuple[GbsReportPackage, ...]]
GbsPackageLogDownloader = Callable[[GbsReportPackage, Path], str]
Clock = Callable[[], datetime]


@dataclass(frozen=True)
class BatchTriageOptions:
    """Options for one batch orchestration run."""

    state_root: Path = Path(".ci_triage")
    cookie_path: Path = DEFAULT_COOKIE_PATH
    retry_limit: int = 3
    python_executable: str = sys.executable
    extra_pythonpath: tuple[Path, ...] = ()
    git_ssh_command: str | None = None
    run_date: str | None = None
    arches: tuple[str, ...] = DEFAULT_ARCHES


@dataclass(frozen=True)
class BatchTriageResult:
    """Top-level result for one batch orchestration run."""

    daily_report_path: Path
    discovered_builds: int
    package_units: int
    warnings: tuple[str, ...] = ()


@dataclass
class PackageState:
    """Persistent state for one ``(build_id, spec_name)`` processing unit."""

    arch: str | None = None
    spec_name: str | None = None
    state: str = STATE_DISCOVERED
    project: str | None = None
    branch: str | None = "tizen"
    commit: str | None = None
    gerrit_status: str | None = None
    patchset_ref: str | None = None
    patch_status: str | None = None
    retries: int = 0
    error: str | None = None
    report_path: str | None = None
    transitions: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: object) -> PackageState:
        if not isinstance(raw, dict):
            return cls()
        transitions = raw.get("transitions")
        return cls(
            arch=_optional_string(raw.get("arch")),
            spec_name=_optional_string(raw.get("spec_name")),
            state=_string(raw.get("state"), STATE_DISCOVERED),
            project=_optional_string(raw.get("project")),
            branch=_optional_string(raw.get("branch")) or "tizen",
            commit=_optional_string(raw.get("commit")),
            gerrit_status=_optional_string(raw.get("gerrit_status")),
            patchset_ref=_optional_string(raw.get("patchset_ref")),
            patch_status=_optional_string(raw.get("patch_status")),
            retries=_int(raw.get("retries"), 0),
            error=_optional_string(raw.get("error")),
            report_path=_optional_string(raw.get("report_path")),
            transitions=transitions if isinstance(transitions, list) else [],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "arch": self.arch,
            "spec_name": self.spec_name,
            "project": self.project,
            "branch": self.branch,
            "commit": self.commit,
            "gerrit_status": self.gerrit_status,
            "patchset_ref": self.patchset_ref,
            "patch_status": self.patch_status,
            "retries": self.retries,
            "error": self.error,
            "report_path": self.report_path,
            "transitions": self.transitions,
        }


@dataclass
class BuildState:
    """Persistent state for one QuickBuild build."""

    build_id: str
    discovered_at: str
    begin_date: str
    state: str = STATE_DISCOVERED
    error: str | None = None
    transitions: list[dict[str, Any]] = field(default_factory=list)
    packages: dict[str, PackageState] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: Path, *, build: FailedBuild, now: str) -> BuildState:
        if not path.is_file():
            return cls(
                build_id=build.build_id,
                discovered_at=now,
                begin_date=build.begin_date.isoformat(sep=" ", timespec="seconds"),
            )
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls(
                build_id=build.build_id,
                discovered_at=now,
                begin_date=build.begin_date.isoformat(sep=" ", timespec="seconds"),
            )
        if not isinstance(raw, dict):
            return cls(
                build_id=build.build_id,
                discovered_at=now,
                begin_date=build.begin_date.isoformat(sep=" ", timespec="seconds"),
            )
        raw_packages = raw.get("packages")
        packages: dict[str, PackageState] = {}
        if isinstance(raw_packages, dict):
            for spec_name, value in raw_packages.items():
                if isinstance(spec_name, str):
                    packages[spec_name] = PackageState.from_dict(value)
        transitions = raw.get("transitions")
        return cls(
            build_id=_string(raw.get("build_id"), build.build_id),
            discovered_at=_string(raw.get("discovered_at"), now),
            begin_date=_string(
                raw.get("begin_date"),
                build.begin_date.isoformat(sep=" ", timespec="seconds"),
            ),
            state=_string(raw.get("state"), STATE_DISCOVERED),
            error=_optional_string(raw.get("error")),
            transitions=transitions if isinstance(transitions, list) else [],
            packages=packages,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "build_id": self.build_id,
            "discovered_at": self.discovered_at,
            "begin_date": self.begin_date,
            "state": self.state,
            "error": self.error,
            "transitions": self.transitions,
            "packages": {
                spec_name: package.to_dict()
                for spec_name, package in sorted(self.packages.items())
            },
        }


@dataclass
class BatchRunRecord:
    """One package row included in the daily report."""

    build_id: str
    arch: str
    spec_name: str
    project: str | None
    branch: str | None
    commit: str | None
    gerrit_status: str | None
    patch_status: str | None
    state: str
    report_path: str | None
    error: str | None
    retries: int


class CiTriageOrchestrator:
    """Batch runner that connects failed-build discovery to one-build triage."""

    def __init__(
        self,
        *,
        source: FailedBuildSource | None = None,
        options: BatchTriageOptions | None = None,
        triage_runner: TriageRunner = run_triage,
        full_log_downloader: FullLogDownloader | None = None,
        gbs_report_discoverer: GbsReportDiscoverer | None = None,
        package_log_downloader: GbsPackageLogDownloader | None = None,
        clock: Clock = datetime.now,
    ) -> None:
        self.options = options or BatchTriageOptions()
        self.source = source or QuickBuildSource(cookie_path=self.options.cookie_path)
        self.triage_runner = triage_runner
        self.full_log_downloader = full_log_downloader or self._download_full_log_text
        self.gbs_report_discoverer = gbs_report_discoverer or self._discover_failed_gbs_packages
        self.package_log_downloader = package_log_downloader or self._download_gbs_package_log
        self.clock = clock

    def run(self, since: datetime) -> BatchTriageResult:
        """Discover recent failed builds and process each failed package independently."""

        now = self.clock()
        paths = _BatchPaths.from_options(self.options, now)
        paths.ensure()
        processed = _load_processed(paths.processed_path)
        rows: list[BatchRunRecord] = []
        warnings: list[str] = []

        builds = self.source.discover(since)
        source_warnings = getattr(self.source, "warnings", None)
        if isinstance(source_warnings, list):
            warnings.extend(str(item) for item in source_warnings)

        for build in builds:
            build_state = BuildState.from_file(
                paths.state_dir / f"{build.build_id}.json",
                build=build,
                now=_timestamp(now),
            )
            try:
                self._process_build(build, build_state, paths, processed, rows, now)
            except QuickBuildError as exc:
                _transition_build(
                    build_state,
                    STATE_FAILED_LOG,
                    ok=False,
                    error=f"{exc.code}: {exc}",
                    now=now,
                )
            finally:
                _save_build_state(paths.state_dir / f"{build.build_id}.json", build_state)
                _save_processed(paths.processed_path, processed)

        daily_report_path = paths.runs_dir / "daily_report.md"
        daily_report_path.write_text(
            _render_daily_report(builds, rows, warnings, arch_order=self.options.arches),
            encoding="utf-8",
        )
        manifest_path = paths.runs_dir / "batch_manifest.json"
        manifest_path.write_text(
            _render_batch_manifest(paths, rows, now),
            encoding="utf-8",
        )
        return BatchTriageResult(
            daily_report_path=daily_report_path,
            discovered_builds=len(builds),
            package_units=len(rows),
            warnings=tuple(warnings),
        )

    def _process_build(
        self,
        build: FailedBuild,
        build_state: BuildState,
        paths: _BatchPaths,
        processed: dict[str, dict[str, set[str]]],
        rows: list[BatchRunRecord],
        now: datetime,
    ) -> None:
        full_log = self.full_log_downloader(build.build_id, self.options.cookie_path)
        _transition_build(build_state, STATE_LOG_FETCHED, ok=True, error=None, now=now)

        pkg_to_commit_error: str | None
        try:
            pkg_to_commit = parse_build_pkg_list(full_log)
        except QuickBuildLogError as exc:
            pkg_to_commit_error = f"{exc.code}: {exc}"
            pkg_to_commit = {}
        else:
            pkg_to_commit_error = None

        discovered_any = False
        no_gbs_report_any = False
        for arch in self.options.arches:
            if _is_processed(processed, build.build_id, arch, NO_GBS_REPORT_SPEC_NAME):
                no_gbs_report_any = True
                package = _package_for(build_state, arch, NO_GBS_REPORT_SPEC_NAME)
                _transition_package(
                    package,
                    STATE_SKIPPED_PROCESSED,
                    ok=True,
                    error=None,
                    now=now,
                )
                rows.append(
                    _row_from_package(build.build_id, arch, NO_GBS_REPORT_SPEC_NAME, package)
                )
                continue
            try:
                failed_packages = self.gbs_report_discoverer(
                    build.build_id,
                    arch,
                    self.options.cookie_path,
                )
            except QuickBuildError as exc:
                if exc.code == "NO_GBS_REPORT":
                    no_gbs_report_any = True
                    package = _package_for(build_state, arch, NO_GBS_REPORT_SPEC_NAME)
                    _transition_package(
                        package,
                        STATE_REPORTED_NO_REPORT,
                        ok=True,
                        error=str(exc),
                        now=now,
                    )
                    _mark_processed(processed, build.build_id, arch, NO_GBS_REPORT_SPEC_NAME)
                    rows.append(
                        _row_from_package(build.build_id, arch, NO_GBS_REPORT_SPEC_NAME, package)
                    )
                    continue
                package = _package_for(build_state, arch, UNKNOWN_SPEC_NAME)
                package.retries += 1
                _transition_package(
                    package,
                    STATE_FAILED_LOG,
                    ok=False,
                    error=f"{exc.code}: {exc}",
                    now=now,
                )
                rows.append(_row_from_package(build.build_id, arch, UNKNOWN_SPEC_NAME, package))
                continue

            if failed_packages:
                discovered_any = True
            for failed_package in failed_packages:
                self._process_package(
                    build,
                    failed_package,
                    pkg_to_commit,
                    pkg_to_commit_error,
                    build_state,
                    paths,
                    processed,
                    rows,
                    now,
                )

        if not discovered_any and not no_gbs_report_any:
            package = _package_for(build_state, "unknown-arch", UNKNOWN_SPEC_NAME)
            _transition_package(
                package,
                STATE_NEEDS_INPUT,
                ok=False,
                error=(
                    "GBS Reports contained no failed package rows "
                    f"(scanned arches: {', '.join(self.options.arches)})"
                ),
                now=now,
            )
            rows.append(
                _row_from_package(build.build_id, "unknown-arch", UNKNOWN_SPEC_NAME, package)
            )

    def _process_package(
        self,
        build: FailedBuild,
        failed_package: GbsReportPackage,
        pkg_to_commit: dict[str, str],
        pkg_to_commit_error: str | None,
        build_state: BuildState,
        paths: _BatchPaths,
        processed: dict[str, dict[str, set[str]]],
        rows: list[BatchRunRecord],
        now: datetime,
    ) -> None:
        arch = failed_package.arch
        spec_name = failed_package.spec_name
        package = _package_for(build_state, arch, spec_name)
        if _is_processed(processed, build.build_id, arch, spec_name):
            _transition_package(
                package,
                STATE_SKIPPED_PROCESSED,
                ok=True,
                error=None,
                now=now,
            )
            rows.append(_row_from_package(build.build_id, arch, spec_name, package))
            return

        if package.state.startswith("FAILED_") and package.retries >= self.options.retry_limit:
            _transition_package(
                package,
                STATE_FAILED_PERMANENT,
                ok=False,
                error=package.error or "retry limit reached",
                now=now,
            )
            rows.append(_row_from_package(build.build_id, arch, spec_name, package))
            return

        _transition_package(package, STATE_LOG_FETCHED, ok=True, error=None, now=now)
        if pkg_to_commit_error is not None:
            _transition_package(
                package,
                STATE_NEEDS_INPUT,
                ok=False,
                error=pkg_to_commit_error,
                now=now,
            )
            rows.append(_row_from_package(build.build_id, arch, spec_name, package))
            return

        try:
            project_key, commit_hash = match_pkg_key(spec_name, pkg_to_commit)
        except QuickBuildLogError as exc:
            _transition_package(
                package,
                STATE_NEEDS_INPUT,
                ok=False,
                error=f"{exc.code}: {exc}",
                now=now,
            )
            rows.append(_row_from_package(build.build_id, arch, spec_name, package))
            return
        package.project = project_key
        package.commit = commit_hash

        try:
            buildlog_text = self.package_log_downloader(failed_package, self.options.cookie_path)
        except QuickBuildError as exc:
            package.retries += 1
            _transition_package(
                package,
                STATE_FAILED_LOG,
                ok=False,
                error=f"{exc.code}: {exc}",
                now=now,
            )
            rows.append(_row_from_package(build.build_id, arch, spec_name, package))
            return

        result = self.triage_runner(
            TriageOptions(
                build_id=build.build_id,
                output_root=paths.runs_dir,
                output_dir=paths.package_dir(build.build_id, arch, spec_name),
                cookie_path=self.options.cookie_path,
                spec_name=spec_name,
                python_executable=self.options.python_executable,
                extra_pythonpath=self.options.extra_pythonpath or discover_sibling_pythonpath(),
                git_ssh_command=self.options.git_ssh_command,
                selected_package=FailedPackage(
                    fail_pkg=failed_package.package_path,
                    spec_name=spec_name,
                ),
                package_buildlog_text=buildlog_text,
                package_buildlog_url=failed_package.buildlog_url,
                project_key=project_key,
                commit_hash=commit_hash,
            )
        )
        _apply_triage_result(package, result, now=now)
        _read_report_metadata(package, result.report_path)
        package.report_path = str(result.report_path)
        if package.state == STATE_REPORTED:
            _mark_processed(processed, build.build_id, arch, spec_name)
        rows.append(_row_from_package(build.build_id, arch, spec_name, package))

    @staticmethod
    def _download_full_log_text(build_id: str, cookie_path: Path) -> str:
        return download_full_log(build_id, cookie_path=cookie_path).full_log

    @staticmethod
    def _discover_failed_gbs_packages(
        build_id: str,
        arch: str,
        cookie_path: Path,
    ) -> tuple[GbsReportPackage, ...]:
        return fetch_gbs_report(build_id, arch, cookie_path=cookie_path).failed_packages

    @staticmethod
    def _download_gbs_package_log(package: GbsReportPackage, cookie_path: Path) -> str:
        return download_gbs_package_buildlog(package, cookie_path=cookie_path)


@dataclass(frozen=True)
class _BatchPaths:
    state_root: Path
    state_dir: Path
    runs_dir: Path
    logs_dir: Path
    processed_path: Path
    run_date: str

    @classmethod
    def from_options(cls, options: BatchTriageOptions, now: datetime) -> _BatchPaths:
        run_date = options.run_date or now.date().isoformat()
        state_root = options.state_root
        return cls(
            state_root=state_root,
            state_dir=state_root / "state",
            runs_dir=state_root / "runs" / run_date,
            logs_dir=state_root / "logs",
            processed_path=state_root / PROCESSED_FILENAME,
            run_date=run_date,
        )

    def ensure(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def package_dir(self, build_id: str, arch: str, spec_name: str) -> Path:
        return self.runs_dir / build_id / _safe_path_name(arch) / _safe_path_name(spec_name)


def _apply_triage_result(package: PackageState, result: TriageResult, *, now: datetime) -> None:
    if result.exit_code == 0:
        _transition_package(package, STATE_ANALYZED, ok=True, error=None, now=now)
        _transition_package(package, STATE_SOURCE_FETCHED, ok=True, error=None, now=now)
        _transition_package(package, STATE_PATCH_SUGGESTED, ok=True, error=None, now=now)
        package.patch_status = _read_patch_status(result.output_dir / "patch_context" / "meta.json")
        _transition_package(package, STATE_REPORTED, ok=True, error=None, now=now)
        return

    failed_state = _map_triage_failure(result.status)
    package.retries += 1
    _transition_package(package, failed_state, ok=False, error=result.error, now=now)


def _map_triage_failure(status: str) -> str:
    if status in {
        "COOKIE_MISSING",
        "COOKIE_UNREADABLE",
        "COOKIE_EXPIRED",
        "QUICKBUILD_DOWNLOAD_FAILED",
        "DOWNLOAD_LINK_NOT_FOUND",
        "PACKAGE_BUILDLOG_DOWNLOAD_FAILED",
    }:
        return STATE_FAILED_LOG
    if status == "ANALYZER_FAILED":
        return STATE_FAILED_ANALYZE
    if status in {
        "FAILED_SOURCE",
        "SOURCE_DIR_UNSAFE",
        "GERRIT_QUERY_FAILED",
        "GERRIT_CHANGE_NOT_FOUND",
        "GERRIT_CHANGE_AMBIGUOUS",
        "PATCHSET_REVISION_NOT_FOUND",
    }:
        return STATE_FAILED_SOURCE
    if status == "PATCH_SUGGEST_FAILED":
        return STATE_FAILED_PATCH
    if status in {
        "NEEDS_PACKAGE_SELECTION",
        "FAILED_PACKAGE_NOT_FOUND",
        "FAILED_PACKAGE_AMBIGUOUS",
        "PROJECT_COMMIT_NOT_FOUND",
        "PROJECT_COMMIT_AMBIGUOUS",
    }:
        return STATE_NEEDS_INPUT
    return STATE_FAILED_REPORT


def _render_daily_report(
    builds: list[FailedBuild],
    rows: list[BatchRunRecord],
    warnings: list[str],
    *,
    arch_order: tuple[str, ...] = (),
) -> str:
    patch_count = sum(
        1
        for row in rows
        if row.state == STATE_REPORTED
        and row.patch_status is not None
        and row.patch_status.endswith("_context_available")
    )
    not_applicable_count = sum(
        1 for row in rows if row.state == STATE_REPORTED and row.patch_status == "not_applicable"
    )
    failure_count = sum(1 for row in rows if row.state.startswith("FAILED_"))
    needs_input = [row for row in rows if row.state == STATE_NEEDS_INPUT]
    no_gbs_report = [row for row in rows if row.state == STATE_REPORTED_NO_REPORT]
    no_gbs_report_groups = _group_no_gbs_report_rows(rows)
    failures = [row for row in rows if row.state.startswith("FAILED_")]
    build_urls = {build.build_id: build.quickbuild_url for build in builds if build.quickbuild_url}

    lines = [
        "# CI Triage Daily Report",
        "",
        "## Overview",
        f"- Failed builds discovered: {len(builds)}",
        f"- Failed package units: {len(rows)}",
        f"- Patch contexts available: {patch_count}",
        f"- Not applicable: {not_applicable_count}",
        f"- Failed units: {failure_count}",
        f"- Needs input: {len(needs_input)}",
        (
            f"- No GBS report: {_count_label(len(no_gbs_report), 'unit')} across "
            f"{_count_label(len(no_gbs_report_groups), 'build')}"
        ),
        "",
        "## Failed Package Index",
        "| build_id | arch | spec_name | commit | gerrit | patch_status | state | report |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    rendered_no_report_builds: set[str] = set()
    for row in rows:
        if row.state == STATE_REPORTED_NO_REPORT:
            if row.build_id in rendered_no_report_builds:
                continue
            rendered_no_report_builds.add(row.build_id)
            folded_rows = no_gbs_report_groups[row.build_id]
            first_row = folded_rows[0]
            lines.append(
                "| "
                f"{first_row.build_id} | {_arch_summary(folded_rows, arch_order)} | "
                f"{first_row.spec_name} | {_cell(first_row.commit)} | "
                f"{_cell(first_row.gerrit_status)} | {_cell(first_row.patch_status)} | "
                f"{first_row.state} | {_report_link(first_row.report_path)} |"
            )
            continue
        lines.append(
            "| "
            f"{row.build_id} | {row.arch} | {row.spec_name} | {_cell(row.commit)} | "
            f"{_cell(row.gerrit_status)} | {_cell(row.patch_status)} | {row.state} | "
            f"{_report_link(row.report_path)} |"
        )

    lines.extend(
        [
            "",
            "## Processing Failures",
            "| build_id | arch | spec_name | state | reason | retries |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    if failures:
        for row in failures:
            lines.append(
                f"| {row.build_id} | {row.arch} | {row.spec_name} | {row.state} | "
                f"{_cell(row.error)} | {row.retries} |"
            )
    else:
        lines.append("| n/a | n/a | n/a | n/a | n/a | 0 |")

    lines.extend(
        [
            "",
            "## Needs Input",
            "| build_id | arch | spec_name | reason |",
            "| --- | --- | --- | --- |",
        ]
    )
    if needs_input:
        for row in needs_input:
            lines.append(
                f"| {row.build_id} | {row.arch} | {row.spec_name} | {_cell(row.error)} |"
            )
    else:
        lines.append("| n/a | n/a | n/a | n/a |")

    lines.extend(
        [
            "",
            "## No GBS Report (non-package builds)",
            (
                "These builds failed but do not expose per-package GBS reports "
                "(RBS/trigger/snapshot style). Automatic package triage is not available; "
                "review the QuickBuild page manually."
            ),
            "",
            "| build_id | arch | build_url |",
            "| --- | --- | --- |",
        ]
    )
    if no_gbs_report_groups:
        for build_id, folded_rows in no_gbs_report_groups.items():
            build_url = build_urls.get(build_id, "")
            lines.append(
                f"| {build_id} | {_arch_summary(folded_rows, arch_order)} | {build_url} |"
            )
    else:
        lines.append("| n/a | n/a | n/a |")

    if warnings:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- {warning}" for warning in warnings)

    return "\n".join(lines) + "\n"


def _group_no_gbs_report_rows(rows: list[BatchRunRecord]) -> dict[str, list[BatchRunRecord]]:
    groups: dict[str, list[BatchRunRecord]] = {}
    for row in rows:
        if row.state == STATE_REPORTED_NO_REPORT:
            groups.setdefault(row.build_id, []).append(row)
    return groups


def _arch_summary(rows: list[BatchRunRecord], arch_order: tuple[str, ...]) -> str:
    ordered_arches = _ordered_arches(rows, arch_order)
    if len(ordered_arches) == 1:
        return ordered_arches[0]
    return f"{len(ordered_arches)} arches ({', '.join(ordered_arches)})"


def _ordered_arches(rows: list[BatchRunRecord], arch_order: tuple[str, ...]) -> list[str]:
    row_arches: list[str] = []
    for row in rows:
        if row.arch not in row_arches:
            row_arches.append(row.arch)

    ordered: list[str] = []
    row_arch_set = set(row_arches)
    for arch in arch_order:
        if arch in row_arch_set:
            ordered.append(arch)
    for arch in row_arches:
        if arch not in ordered:
            ordered.append(arch)
    return ordered


def _count_label(count: int, singular: str) -> str:
    suffix = "" if count == 1 else "s"
    return f"{count} {singular}{suffix}"


def _render_batch_manifest(paths: _BatchPaths, rows: list[BatchRunRecord], now: datetime) -> str:
    manifest = {
        "schema_version": BATCH_MANIFEST_SCHEMA,
        "generated_at": _timestamp(now),
        "run_date": paths.run_date,
        "packages": [_manifest_package(paths, row) for row in rows],
    }
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def _manifest_package(paths: _BatchPaths, row: BatchRunRecord) -> dict[str, Any]:
    package_dir = paths.package_dir(row.build_id, row.arch, row.spec_name)
    return {
        "unit_key": _manifest_unit_key(row.build_id, row.arch, row.spec_name),
        "build_id": row.build_id,
        "arch": row.arch,
        "spec_name": row.spec_name,
        "state": row.state,
        "patch_status": row.patch_status,
        "project": row.project,
        "base_commit": row.commit,
        "branch": row.branch or "tizen",
        "src_clean": _existing_dir(package_dir / "src" / row.spec_name),
        "evidence_packet": _existing_file(package_dir / "evidence_packet.json"),
        "patch_context": _existing_file(package_dir / "patch_context" / "context.md"),
        "patch_context_meta": _existing_file(package_dir / "patch_context" / "meta.json"),
        "report": _existing_file(Path(row.report_path)) if row.report_path else None,
        "package_buildlog": _existing_file(package_dir / f"{row.spec_name}.buildlog.txt"),
        "error": _manifest_error(row),
    }


def _manifest_unit_key(build_id: str, arch: str, spec_name: str) -> str:
    return f"{build_id}:{arch}:{spec_name}"


def _existing_file(path: Path) -> str | None:
    return str(path.resolve()) if path.is_file() else None


def _existing_dir(path: Path) -> str | None:
    return str(path.resolve()) if path.is_dir() else None


def _manifest_error(row: BatchRunRecord) -> dict[str, str] | None:
    if row.error:
        code, _, message = row.error.partition(":")
        if message and _looks_like_error_code(code):
            return {"code": code.strip() or row.state, "message": message.strip()}
        return {"code": row.state, "message": row.error}
    if row.state in {STATE_REPORTED, STATE_SKIPPED_PROCESSED}:
        return None
    if row.state.startswith("FAILED_") or row.state in {
        STATE_NEEDS_INPUT,
        STATE_REPORTED_NO_REPORT,
        STATE_FAILED_PERMANENT,
    }:
        return {"code": row.state, "message": row.state}
    # In-progress states such as LOG_FETCHED/ANALYZED are visible in the
    # manifest during partial runs, but they are not errors by themselves.
    return None


def _looks_like_error_code(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Z0-9_]*", value.strip()))


def _load_processed(path: Path) -> dict[str, dict[str, set[str]]]:
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    processed: dict[str, dict[str, set[str]]] = {}
    for build_id, arches in raw.items():
        if not isinstance(build_id, str):
            continue
        if isinstance(arches, dict):
            processed[build_id] = {}
            for arch, spec_names in arches.items():
                if isinstance(arch, str) and isinstance(spec_names, list):
                    processed[build_id][arch] = {
                        item for item in spec_names if isinstance(item, str)
                    }
        elif isinstance(arches, list):
            processed[build_id] = {
                "unknown-arch": {item for item in arches if isinstance(item, str)}
            }
    return processed


def _save_processed(path: Path, processed: dict[str, dict[str, set[str]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serializable = {
        build_id: {
            arch: sorted(spec_names) for arch, spec_names in sorted(arches.items())
        }
        for build_id, arches in sorted(processed.items())
    }
    path.write_text(json.dumps(serializable, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_processed(
    processed: dict[str, dict[str, set[str]]],
    build_id: str,
    arch: str,
    spec_name: str,
) -> bool:
    return spec_name in processed.get(build_id, {}).get(arch, set())


def _mark_processed(
    processed: dict[str, dict[str, set[str]]],
    build_id: str,
    arch: str,
    spec_name: str,
) -> None:
    processed.setdefault(build_id, {}).setdefault(arch, set()).add(spec_name)


def _save_build_state(path: Path, state: BuildState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _package_for(build_state: BuildState, arch: str, spec_name: str) -> PackageState:
    key = _unit_key(arch, spec_name)
    package = build_state.packages.get(key)
    if package is None:
        package = PackageState(arch=arch, spec_name=spec_name)
        build_state.packages[key] = package
    return package


def _transition_build(
    build_state: BuildState,
    to_state: str,
    *,
    ok: bool,
    error: str | None,
    now: datetime,
) -> None:
    previous = build_state.state
    build_state.state = to_state
    build_state.error = error
    build_state.transitions.append(_transition(previous, to_state, ok=ok, error=error, now=now))


def _transition_package(
    package: PackageState,
    to_state: str,
    *,
    ok: bool,
    error: str | None,
    now: datetime,
) -> None:
    previous = package.state
    package.state = to_state
    package.error = error
    package.transitions.append(_transition(previous, to_state, ok=ok, error=error, now=now))


def _transition(
    from_state: str,
    to_state: str,
    *,
    ok: bool,
    error: str | None,
    now: datetime,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "from": from_state,
        "to": to_state,
        "at": _timestamp(now),
        "ok": ok,
    }
    if error:
        item["error"] = error
    return item


def _row_from_package(
    build_id: str,
    arch: str,
    spec_name: str,
    package: PackageState,
) -> BatchRunRecord:
    return BatchRunRecord(
        build_id=build_id,
        arch=arch,
        spec_name=spec_name,
        project=package.project,
        branch=package.branch,
        commit=package.commit,
        gerrit_status=package.gerrit_status,
        patch_status=package.patch_status,
        state=package.state,
        report_path=package.report_path,
        error=package.error,
        retries=package.retries,
    )


def _unit_key(arch: str, spec_name: str) -> str:
    return f"{arch}/{spec_name}"


def _read_patch_status(meta_path: Path) -> str | None:
    try:
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    status = raw.get("status")
    return status if isinstance(status, str) else None


def _read_report_metadata(package: PackageState, report_path: Path) -> None:
    try:
        text = report_path.read_text(encoding="utf-8")
    except OSError:
        return
    status_match = re.search(r"^- Change status: `([^`]+)`", text, flags=re.MULTILINE)
    if status_match is not None:
        package.gerrit_status = status_match.group(1)
    patchset_match = re.search(r"^- Patch set ref: `([^`]+)`", text, flags=re.MULTILINE)
    if patchset_match is not None:
        package.patchset_ref = patchset_match.group(1)
    branch_match = re.search(r"^- Branch: `([^`]+)`", text, flags=re.MULTILINE)
    if branch_match is not None:
        package.branch = branch_match.group(1)


def _safe_path_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "unknown"


def _timestamp(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _cell(value: str | None) -> str:
    if value is None or value == "":
        return "n/a"
    return value.replace("|", "\\|")


def _report_link(report_path: str | None) -> str:
    if not report_path:
        return "n/a"
    return f"[report]({report_path})"


def _string(value: object, default: str) -> str:
    return value if isinstance(value, str) else default


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _int(value: object, default: int) -> int:
    return value if isinstance(value, int) else default
