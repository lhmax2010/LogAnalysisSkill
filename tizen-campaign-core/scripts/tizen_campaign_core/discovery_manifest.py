"""Immutable, filesystem-only handoff between QB discovery and campaign intake."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from tizen_campaign_core import campaign_state as state
from tizen_campaign_core._campaign_io import fsync_parent

SCHEMA = "clang_discover_manifest/v1"
KEYS = {
    "schema_version",
    "qb_project",
    "build_id",
    "child_build_id",
    "captured_at",
    "report_dir",
    "packages",
}
PACKAGE_KEYS = {
    "spec_name",
    "failed_arches",
    "primary_arch",
    "project",
    "branch",
    "base_commit",
    "log_path",
    "log_sha256",
    "status",
    "reason",
}
STATUSES = {
    "ok",
    "DISCOVERY_SOURCE_UNRESOLVED",
    "DISCOVERY_LOG_UNREADABLE",
    "DISCOVERY_REPORT_AMBIGUOUS",
    "ARCH_NOT_ALLOWED",
}
REASONS = {
    "SOURCE_VARIABLES",
    "ARCH_NOT_ALLOWED",
    "REPORT_STRUCTURE",
    "HTTP_STATUS",
    "REDIRECT",
    "DOWNLOAD",
    "CONTENT_TYPE",
    "ENCODING",
    "TOO_LARGE",
    "NO_BODY",
    "NAVIGATION",
    "PATH_UNSUPPORTED",
}


def require(value: object) -> None:
    if not value:
        raise ValueError("INVALID_DISCOVERY_MANIFEST")


def project_valid(value: object) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/+-]*", value) is not None
        and ".." not in value
        and not value.endswith("/")
    )


def package_valid(value: object) -> bool:
    return (
        isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", value) is not None
    )


def validate(value: Any) -> dict[str, Any]:
    require(isinstance(value, dict) and set(value) == KEYS)
    require(value["schema_version"] == SCHEMA)
    require(package_valid(value["qb_project"]))
    for key in ("build_id", "child_build_id"):
        require(isinstance(value[key], str) and re.fullmatch(r"[1-9][0-9]*", value[key]))
    require(isinstance(value["captured_at"], str))
    timestamp = datetime.datetime.fromisoformat(value["captured_at"])
    require(timestamp.tzinfo is not None)
    require(
        isinstance(value["report_dir"], str)
        and value["report_dir"] != ""
        and not any(c in value["report_dir"] for c in "\\/\x00")
        and value["report_dir"] not in {".", ".."}
    )
    require(isinstance(value["packages"], list))
    seen = set()
    for row in value["packages"]:
        require(isinstance(row, dict) and set(row) == PACKAGE_KEYS)
        require(package_valid(row["spec_name"]) and row["spec_name"] not in seen)
        seen.add(row["spec_name"])
        arches = row["failed_arches"]
        require(
            isinstance(arches, list)
            and bool(arches)
            and all(isinstance(a, str) and bool(a) for a in arches)
        )
        require(list(state._canonical_failed_arches(arches)) == arches)
        allowed = all(a in state.ARCH_RAW_TO_NORM for a in arches)
        require(row["primary_arch"] == (arches[0] if allowed else None))
        require(row["status"] in STATUSES and (row["reason"] is None or row["reason"] in REASONS))
        require(allowed == (row["status"] != "ARCH_NOT_ALLOWED"))
        for key in ("project", "branch", "base_commit"):
            require(row[key] is None or isinstance(row[key], str))
        if row["project"] is not None:
            require(project_valid(row["project"]))
        if row["branch"] is not None:
            require(package_valid(row["branch"]))
        if row["base_commit"] is not None:
            require(re.fullmatch(r"[0-9a-f]{40}", row["base_commit"]))
        if row["status"] == "ok":
            require(all(row[k] for k in ("project", "branch", "base_commit")))
            require(row["reason"] is None and isinstance(row["log_path"], str))
            require(
                isinstance(row["log_sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", row["log_sha256"])
            )
        else:
            require(row["reason"] in REASONS)
        require((row["log_path"] is None) == (row["log_sha256"] is None))
        if row["log_path"] is not None:
            require(allowed)
            require(row["log_path"] == f"logs/{row['spec_name']}.{row['primary_arch']}.txt")
            require(
                isinstance(row["log_sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", row["log_sha256"])
            )
    return dict(value)


def atomic_write(path: Path, raw: bytes) -> None:
    """Caller owns a fresh per-run directory; never overwrite a published artifact."""
    require(not path.exists() and not path.is_symlink())
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".publish-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.rename(temporary, path)
        fsync_parent(path)
    finally:
        temporary.unlink(missing_ok=True)


def load(path: Path, state_root: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    root, resolved = state_root.resolve(strict=True), path.resolve(strict=True)
    relative = resolved.relative_to(root)
    require(
        len(relative.parts) == 4
        and relative.parts[0] == "discovery"
        and relative.parts[-1] == "discover-manifest.json"
    )
    value = validate(json.loads(resolved.read_text(encoding="utf-8")))
    require(relative.parts[1] == value["build_id"])
    logs = {}
    for row in value["packages"]:
        if row["log_path"] is not None:
            log = (resolved.parent / row["log_path"]).resolve(strict=True)
            require(log.is_relative_to(root) and log.is_relative_to(resolved.parent))
            require(
                log.is_file() and hashlib.sha256(log.read_bytes()).hexdigest() == row["log_sha256"]
            )
            logs[row["spec_name"]] = log
    return value, logs
