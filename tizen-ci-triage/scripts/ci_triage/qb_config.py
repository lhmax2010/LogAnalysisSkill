"""Offline validation and canonical snapshots of P5Q configuration."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

BASE_URL = "https://quickbuild.tizen.org"
ARCHITECTURES = "standard-armv7l:aarch64:x86_64"
FORM_KEYS = frozenset(
    {
        "BUILD_TYPE",
        "REPO_TYPE",
        "BUILD_REFERENCE",
        "SNAPSHOT_NUM",
        "PROJECT_BRANCH",
        "Immediate Stop With Error",
        "CHILD_CONFIGURATIONS",
        "TARGET_IMAGE",
        "Add Package List",
        "Remove Package List",
    }
)


class QbConfigError(ValueError):
    code = "INVALID_ARGS"


class QbProjectNotReady(ValueError):
    code = "REJECTED_QB_PROJECT_NOT_READY"


def _mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise QbConfigError(f"{name} must be a mapping with string keys")
    return value


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise QbConfigError(f"{name} must be a nonempty string")
    return value


def parse_qb_config(value: object) -> dict[str, Any]:
    """Validate the campaign's qb section without opening a browser or connection."""
    qb = _mapping(value, "qb")
    if qb.get("base_url") != BASE_URL:
        raise QbConfigError("qb.base_url must be https://quickbuild.tizen.org")
    browser = _mapping(qb.get("browser"), "qb.browser")
    for key in ("node", "playwright_module", "chromium"):
        path = Path(_text(browser.get(key), f"qb.browser.{key}"))
        if not path.is_absolute() or not path.exists():
            raise QbConfigError(f"qb.browser.{key} must be an existing absolute path")
    projects = _mapping(qb.get("projects"), "qb.projects")
    for branch, value in projects.items():
        project = _mapping(value, "qb project")
        if type(project.get("enabled")) is not bool:
            raise QbConfigError("project.enabled must be a boolean")
        if not project["enabled"]:
            continue
        _text(project.get("configuration_path"), "configuration_path")
        _text(project.get("project_name"), "project_name")
        if type(project.get("overview_id")) is not int or project["overview_id"] <= 0:
            raise QbConfigError("overview_id must be a positive integer")
        form = _mapping(project.get("form"), "project.form")
        if set(form) != FORM_KEYS:
            raise QbConfigError("project.form must contain exactly the ten configured fields")
        for key in ("BUILD_TYPE", "REPO_TYPE", "BUILD_REFERENCE", "SNAPSHOT_NUM"):
            _text(form[key], key)
        if form["PROJECT_BRANCH"] != branch:
            raise QbConfigError("PROJECT_BRANCH must equal the project key")
        if (
            form["Immediate Stop With Error"] is not True
            or form["CHILD_CONFIGURATIONS"] != [ARCHITECTURES]
            or form["TARGET_IMAGE"] != []
            or form["Add Package List"] != ""
            or form["Remove Package List"] != ""
        ):
            raise QbConfigError("architecture, failure propagation and package overrides are fixed")
        if type(project.get("qb_pass_requires_accept")) is not bool:
            raise QbConfigError("qb_pass_requires_accept must be a boolean")
    return copy.deepcopy(qb)


def project_for_branch(qb: dict[str, Any], branch: str) -> dict[str, Any]:
    """Select an enabled project from an already validated configuration."""
    project = qb["projects"].get(branch)
    if project is None or not project["enabled"]:
        raise QbProjectNotReady("no enabled QuickBuild project for unit.branch")
    return copy.deepcopy(project)


def canonical_profile_json(
    project: dict[str, Any],
    *,
    frozen_snapshot: str | None = None,
) -> str:
    """Use the supplied selected/frozen snapshot; never consult mutable external state."""
    form = copy.deepcopy(project["form"])
    if form["SNAPSHOT_NUM"] == "@freeze":
        if frozen_snapshot == "@freeze":
            raise QbConfigError("SNAPSHOT_NUM requires an actual frozen value")
        form["SNAPSHOT_NUM"] = _text(frozen_snapshot, "frozen SNAPSHOT_NUM")
    profile = {
        key: project[key]
        for key in (
            "configuration_path",
            "overview_id",
            "project_name",
            "qb_pass_requires_accept",
        )
    }
    profile["form"] = form
    return json.dumps(profile, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
