"""Parsing helpers for QuickBuild full logs."""

from __future__ import annotations

import ast
import re

from tizen_ci_shared.types import FailedPackage  # P4.9 shim, removed at P4.9 end (§6.2)


class QuickBuildLogError(RuntimeError):
    """QuickBuild log parse failure with a stable error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def parse_build_pkg_list(full_log: str) -> dict[str, str]:
    """Parse the Python-dict build_pkg_list_dic line into project -> commit."""

    for line in full_log.splitlines():
        if "build_pkg_list_dic:" not in line:
            continue
        raw = line.split("build_pkg_list_dic:", 1)[1].strip()
        try:
            parsed = ast.literal_eval(raw)
        except (SyntaxError, ValueError) as exc:
            raise QuickBuildLogError(
                "BUILD_PKG_LIST_UNREADABLE",
                "build_pkg_list_dic is not parseable as a Python literal dict",
            ) from exc
        if not isinstance(parsed, dict):
            raise QuickBuildLogError(
                "BUILD_PKG_LIST_UNREADABLE",
                "build_pkg_list_dic is not a dict",
            )
        result: dict[str, str] = {}
        for key, value in parsed.items():
            if isinstance(key, str) and isinstance(value, str):
                result[key] = value
        if not result:
            raise QuickBuildLogError("BUILD_PKG_LIST_UNREADABLE", "build_pkg_list_dic is empty")
        return result
    raise QuickBuildLogError("BUILD_PKG_LIST_MISSING", "full log has no build_pkg_list_dic line")


def parse_failed_packages(full_log: str) -> tuple[FailedPackage, ...]:
    """Return failed package entries using spec_name as the stable package key."""

    packages: list[FailedPackage] = []
    pattern = re.compile(
        r"fail_pkg:\s*(?P<fail_pkg>[^,]+),\s*"
        r"spec_name:\s*(?P<spec_name>[^,\s]+)"
        r"(?:,\s*dest_file:\s*(?P<dest_file>\S+))?"
    )
    seen: set[tuple[str, str]] = set()
    for match in pattern.finditer(full_log):
        fail_pkg = match.group("fail_pkg").strip()
        spec_name = match.group("spec_name").strip()
        key = (fail_pkg, spec_name)
        if key in seen:
            continue
        seen.add(key)
        packages.append(
            FailedPackage(
                fail_pkg=fail_pkg,
                spec_name=spec_name,
                dest_file=match.group("dest_file"),
            )
        )
    if not packages:
        raise QuickBuildLogError(
            "FAILED_PACKAGE_NOT_FOUND",
            "full log has no fail_pkg/spec_name entries",
        )
    return tuple(packages)


def select_failed_package(
    failed_packages: tuple[FailedPackage, ...],
    *,
    spec_name: str | None,
) -> FailedPackage:
    """Select one failed package for the vertical-slice MVP."""

    if spec_name is not None:
        matches = [package for package in failed_packages if package.spec_name == spec_name]
        if len(matches) == 1:
            return matches[0]
        if not matches:
            choices = ", ".join(package.spec_name for package in failed_packages)
            raise QuickBuildLogError(
                "FAILED_PACKAGE_NOT_FOUND",
                f"requested spec_name {spec_name!r} was not in failed packages: {choices}",
            )
        raise QuickBuildLogError(
            "FAILED_PACKAGE_AMBIGUOUS",
            f"requested spec_name {spec_name!r} matched multiple failed package rows",
        )

    if len(failed_packages) == 1:
        return failed_packages[0]

    choices = ", ".join(package.spec_name for package in failed_packages)
    raise QuickBuildLogError(
        "NEEDS_PACKAGE_SELECTION",
        f"build has multiple failed packages; rerun with --spec-name. Candidates: {choices}",
    )


def match_pkg_key(spec_name: str, pkg_to_commit: dict[str, str]) -> tuple[str, str]:
    """Map a spec_name like 'multi-assistant' to one project key and commit."""

    matches = _exact_project_matches(spec_name, pkg_to_commit)
    if len(matches) == 1:
        key = matches[0]
        return key, pkg_to_commit[key]

    if not matches:
        matches = _tizen_prefix_project_matches(spec_name, pkg_to_commit)

    if len(matches) == 1:
        key = matches[0]
        return key, pkg_to_commit[key]
    if not matches:
        raise QuickBuildLogError(
            "PROJECT_COMMIT_NOT_FOUND",
            f"no build_pkg_list_dic key matched spec_name {spec_name!r}",
        )
    raise QuickBuildLogError(
        "PROJECT_COMMIT_AMBIGUOUS",
        f"multiple build_pkg_list_dic keys matched {spec_name!r}: {', '.join(matches)}",
    )


def _exact_project_matches(spec_name: str, pkg_to_commit: dict[str, str]) -> list[str]:
    return [key for key in pkg_to_commit if _project_basename(key) == spec_name]


def _tizen_prefix_project_matches(spec_name: str, pkg_to_commit: dict[str, str]) -> list[str]:
    rules = (
        ("hal-api-", "/hal/api/"),
        ("capi-ui-", "/api/"),
        ("capi-", "/api/"),
    )
    for prefix, required_segment in rules:
        if not spec_name.startswith(prefix):
            continue
        project_name = spec_name.removeprefix(prefix)
        return [
            key
            for key in pkg_to_commit
            if required_segment in f"/{key}/" and _project_basename(key) == project_name
        ]
    return []


def _project_basename(project: str) -> str:
    return project.split("/")[-1]
