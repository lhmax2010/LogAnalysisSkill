"""End-to-end vertical slice orchestration for one QuickBuild failed build."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ci_triage.gbs_report import (
    GbsReportPackage,
    download_gbs_package_buildlog,
    fetch_gbs_report,
)
from ci_triage.gerrit import fetch_source_for_commit
from ci_triage.quickbuild import (
    DEFAULT_COOKIE_PATH,
    QuickBuildError,
    download_full_log,
    download_package_buildlog,
)
from ci_triage.quickbuild_log import (
    FailedPackage,
    QuickBuildLogError,
    match_pkg_key,
    parse_build_pkg_list,
    parse_failed_packages,
    select_failed_package,
)
from ci_triage.report import TriageReportData, render_report

SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class TriageOptions:
    """Options for one QuickBuild triage invocation."""

    build_id: str
    output_root: Path = Path("ci_triage_out")
    output_dir: Path | None = None
    cookie_path: Path = DEFAULT_COOKIE_PATH
    spec_name: str | None = None
    arch: str | None = None
    python_executable: str = sys.executable
    extra_pythonpath: tuple[Path, ...] = ()
    git_ssh_command: str | None = None
    selected_package: FailedPackage | None = None
    package_buildlog_text: str | None = None
    package_buildlog_url: str | None = None
    project_key: str | None = None
    commit_hash: str | None = None


@dataclass(frozen=True)
class TriageResult:
    """Result paths and status for one QuickBuild triage invocation."""

    exit_code: int
    status: str
    output_dir: Path
    report_path: Path
    error: str | None = None


def run_triage(
    options: TriageOptions,
    *,
    subprocess_runner: SubprocessRunner = subprocess.run,
) -> TriageResult:
    """Run one build_id through full-log download, source checkout, analyzer, patch-suggest."""

    output_dir = options.output_dir or options.output_root / options.build_id
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "report.md"
    report = TriageReportData(
        build_id=options.build_id,
        quickbuild_log_url=f"https://quickbuild.tizen.org/build/{options.build_id}/log",
    )

    try:
        package_buildlog_text = options.package_buildlog_text
        package_buildlog_url = options.package_buildlog_url
        download = download_full_log(options.build_id, cookie_path=options.cookie_path)
        full_log_path = output_dir / "full_log.txt"
        full_log_path.write_text(download.full_log, encoding="utf-8")
        report.full_log_path = full_log_path

        if options.selected_package is not None:
            selected = options.selected_package
        elif options.arch is not None:
            selected, gbs_package = _select_gbs_report_package(
                options.build_id,
                options.arch,
                options.spec_name,
                cookie_path=options.cookie_path,
            )
            if options.package_buildlog_text is None:
                package_buildlog_text = download_gbs_package_buildlog(
                    gbs_package,
                    cookie_path=options.cookie_path,
                )
                package_buildlog_url = gbs_package.buildlog_url
        else:
            if options.spec_name is None:
                raise QuickBuildError(
                    "ARCH_REQUIRED",
                    "QuickBuild single-build triage now requires --arch for automatic "
                    "GBS report failed-package discovery, or --spec-name for the "
                    "legacy full-log fallback.",
                )
            try:
                failed_packages = parse_failed_packages(download.full_log)
            except QuickBuildLogError as exc:
                if exc.code != "FAILED_PACKAGE_NOT_FOUND" or options.spec_name is None:
                    raise
                report.warnings.append(
                    "full log has no fail_pkg/spec_name entries; using explicit "
                    f"--spec-name {options.spec_name!r} and full-log analyzer fallback"
                )
                failed_packages = (
                    FailedPackage(fail_pkg=options.spec_name, spec_name=options.spec_name),
                )
            selected = select_failed_package(failed_packages, spec_name=options.spec_name)
        report.selected_package = selected

        analyzer_input = full_log_path
        if package_buildlog_text is not None:
            analyzer_input = output_dir / f"{selected.spec_name}.buildlog.txt"
            analyzer_input.write_text(package_buildlog_text, encoding="utf-8")
            report.package_buildlog_url = package_buildlog_url
        elif selected.dest_file:
            try:
                package_log = download_package_buildlog(selected.dest_file)
            except QuickBuildError as exc:
                report.warnings.append(
                    f"{exc.code}: {exc}; falling back to full QuickBuild log for analyzer"
                )
            else:
                if package_log is not None:
                    analyzer_input = output_dir / f"{selected.spec_name}.buildlog.txt"
                    analyzer_input.write_text(package_log.text, encoding="utf-8")
                    report.package_buildlog_url = package_log.url
                else:
                    report.warnings.append(
                        "Could not derive package buildlog URL from dest_file; "
                        "falling back to full QuickBuild log for analyzer"
                    )
        report.analyzed_buildlog_path = analyzer_input

        if options.project_key is not None and options.commit_hash is not None:
            project_key = options.project_key
            commit_hash = options.commit_hash
        else:
            pkg_to_commit = parse_build_pkg_list(download.full_log)
            project_key, commit_hash = match_pkg_key(selected.spec_name, pkg_to_commit)
        report.project_key = project_key
        report.commit_hash = commit_hash

        source_fetch = fetch_source_for_commit(
            project_key,
            commit_hash,
            output_dir / "src" / _safe_pkg_dir(selected.spec_name),
            subprocess_runner=subprocess_runner,
            git_ssh_command=options.git_ssh_command or os.environ.get("CI_TRIAGE_GIT_SSH_COMMAND"),
        )
        report.source_fetch = source_fetch
        if source_fetch.status != "source_available":
            return _finish(
                report,
                report_path,
                output_dir,
                status=source_fetch.status,
                error=source_fetch.error or "source checkout failed",
            )

        analyzer_dir = output_dir / "analyzer_output"
        analyzer_result = _run_analyzer(
            analyzer_input,
            src_root=source_fetch.src_root,
            output_dir=analyzer_dir,
            package=selected.spec_name,
            python_executable=options.python_executable,
            subprocess_runner=subprocess_runner,
            extra_pythonpath=options.extra_pythonpath,
        )
        if analyzer_result is not None:
            return _finish(
                report,
                report_path,
                output_dir,
                status="ANALYZER_FAILED",
                error=analyzer_result,
            )

        analyzer_evidence_path = analyzer_dir / "evidence_packet.json"
        evidence_path = output_dir / "evidence_packet.json"
        shutil.copyfile(analyzer_evidence_path, evidence_path)
        report.analyzer_output_dir = analyzer_dir
        report.evidence_packet_path = evidence_path
        packet = _read_packet(evidence_path)
        report.primary_error = _primary_error(packet)

        patch_context_dir = output_dir / "patch_context"
        patch_error = _run_patch_suggest(
            evidence_path,
            src_root=source_fetch.src_root,
            output_dir=patch_context_dir,
            python_executable=options.python_executable,
            subprocess_runner=subprocess_runner,
            extra_pythonpath=options.extra_pythonpath,
        )
        report.patch_context_dir = patch_context_dir
        meta_path = patch_context_dir / "meta.json"
        if meta_path.is_file():
            report.patch_context_meta_path = meta_path
            report.patch_context_status = _read_patch_status(meta_path)
        if patch_error is not None:
            return _finish(
                report,
                report_path,
                output_dir,
                status="PATCH_SUGGEST_FAILED",
                error=patch_error,
            )

        return _finish(report, report_path, output_dir, status="success", error=None, exit_code=0)
    except QuickBuildError as exc:
        return _finish(report, report_path, output_dir, status=exc.code, error=str(exc))
    except QuickBuildLogError as exc:
        return _finish(report, report_path, output_dir, status=exc.code, error=str(exc))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return _finish(report, report_path, output_dir, status="TRIAGE_FAILED", error=str(exc))


def discover_sibling_pythonpath(*, launcher_path: Path | None = None) -> tuple[Path, ...]:
    """Return sibling analyzer/patch-suggest scripts paths for direct-folder usage."""

    if launcher_path is None:
        return ()
    triage_root = launcher_path.resolve().parents[1]
    root = triage_root.parent
    candidates = (
        root / "tizen-gbs-log-analysis" / "scripts",
        root / "tizen-gbs-patch-suggest" / "scripts",
    )
    return tuple(path for path in candidates if path.is_dir())


def _safe_pkg_dir(spec_name: str) -> str:
    """Return a single safe package directory name for source checkout.

    ``spec_name`` should be the RPM spec Name: value. It comes from external
    QuickBuild/GBS report parsing, so reject path separators, parent-directory
    names, empty strings, and NUL bytes before using it as a directory segment.
    Package names may contain dots in the middle, e.g. ``libfoo.bar``.
    """

    if (
        not spec_name
        or "/" in spec_name
        or "\\" in spec_name
        or spec_name in (".", "..")
        or "\x00" in spec_name
    ):
        raise ValueError(f"unsafe spec_name for source dir: {spec_name!r}")
    return spec_name


def _select_gbs_report_package(
    build_id: str,
    arch: str,
    spec_name: str | None,
    *,
    cookie_path: Path,
) -> tuple[FailedPackage, GbsReportPackage]:
    report = fetch_gbs_report(build_id, arch, cookie_path=cookie_path)
    failed = report.failed_packages
    if spec_name is not None:
        matches = [package for package in failed if package.spec_name == spec_name]
        if len(matches) == 1:
            package = matches[0]
            return _failed_package_from_gbs(package), package
        if not matches:
            choices = ", ".join(package.spec_name for package in failed) or "none"
            raise QuickBuildLogError(
                "FAILED_PACKAGE_NOT_FOUND",
                f"requested spec_name {spec_name!r} was not in GBS failed packages: {choices}",
            )
        raise QuickBuildLogError(
            "FAILED_PACKAGE_AMBIGUOUS",
            f"requested spec_name {spec_name!r} matched multiple GBS failed package rows",
        )

    if len(failed) == 1:
        package = failed[0]
        return _failed_package_from_gbs(package), package

    choices = ", ".join(package.spec_name for package in failed) or "none"
    raise QuickBuildLogError(
        "NEEDS_PACKAGE_SELECTION",
        f"GBS report for {arch} has multiple failed packages; rerun with --spec-name. "
        f"Candidates: {choices}",
    )


def _failed_package_from_gbs(package: GbsReportPackage) -> FailedPackage:
    return FailedPackage(
        fail_pkg=package.package_path,
        spec_name=package.spec_name,
    )


def _run_analyzer(
    buildlog_path: Path,
    *,
    src_root: Path,
    output_dir: Path,
    package: str,
    python_executable: str,
    subprocess_runner: SubprocessRunner,
    extra_pythonpath: Sequence[Path],
) -> str | None:
    command = [
        python_executable,
        "-m",
        "gbs_analyzer",
        "analyze",
        str(buildlog_path),
        "--src-root",
        str(src_root),
        "--output-dir",
        str(output_dir),
        "--package",
        package,
    ]
    return _run_checked(command, subprocess_runner, extra_pythonpath)


def _run_patch_suggest(
    evidence_path: Path,
    *,
    src_root: Path,
    output_dir: Path,
    python_executable: str,
    subprocess_runner: SubprocessRunner,
    extra_pythonpath: Sequence[Path],
) -> str | None:
    command = [
        python_executable,
        "-m",
        "gbs_patch_suggest",
        "--evidence",
        str(evidence_path),
        "--src-root",
        str(src_root),
        "--output-dir",
        str(output_dir),
    ]
    return _run_checked(command, subprocess_runner, extra_pythonpath)


def _run_checked(
    command: list[str],
    subprocess_runner: SubprocessRunner,
    extra_pythonpath: Sequence[Path],
) -> str | None:
    env = _build_subprocess_env(extra_pythonpath)
    kwargs: dict[str, object] = {"check": True, "text": True}
    if env is not None:
        kwargs["env"] = env
    try:
        subprocess_runner(command, **kwargs)
    except subprocess.CalledProcessError as exc:
        return f"{command[0]} {' '.join(command[1:3])} exited with {exc.returncode}"
    return None


def _build_subprocess_env(extra_pythonpath: Sequence[Path]) -> dict[str, str] | None:
    if not extra_pythonpath:
        return None
    env = os.environ.copy()
    entries = [str(path) for path in extra_pythonpath]
    existing = env.get("PYTHONPATH")
    if existing:
        entries.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(entries)
    return env


def _read_packet(evidence_path: Path) -> dict[str, Any]:
    raw = json.loads(evidence_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"evidence packet is not an object: {evidence_path}")
    return raw


def _primary_error(packet: dict[str, Any]) -> dict[str, Any] | None:
    value = packet.get("primary_error")
    return value if isinstance(value, dict) else None


def _read_patch_status(meta_path: Path) -> str | None:
    try:
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(raw, dict):
        status = raw.get("status")
        return status if isinstance(status, str) else None
    return None


def _finish(
    report: TriageReportData,
    report_path: Path,
    output_dir: Path,
    *,
    status: str,
    error: str | None,
    exit_code: int = 1,
) -> TriageResult:
    if error:
        report.errors.append(f"{status}: {error}")
    report_path.write_text(render_report(report), encoding="utf-8")
    return TriageResult(
        exit_code=exit_code,
        status=status,
        output_dir=output_dir,
        report_path=report_path,
        error=error,
    )
