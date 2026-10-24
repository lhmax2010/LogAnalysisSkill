"""Load the batch-one configuration; no network or browser initialization."""
from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess

from .errors import FlowError
from .files import confined, load_json


def check_filesystem(path):
    probe = Path(path).resolve()
    while not probe.exists():
        probe = probe.parent
    try:
        info = os.statvfs(probe)
        result = subprocess.run(["stat", "-f", "-c", "%T", str(probe)],
                                cwd=probe, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        raise FlowError(6, "filesystem_unverified") from None
    if result.returncode:
        raise FlowError(6, "filesystem_unverified")
    kind = result.stdout.strip().lower()
    if not kind or kind == "unknown" or kind.startswith(("nfs", "cifs", "smb")):
        raise FlowError(6, "unsupported_filesystem")
    return {"type": kind, "free_bytes": info.f_bavail * info.f_frsize}


@dataclass(frozen=True)
class Config:
    raw: dict
    data_root: Path
    source_dir: Path
    filesystem: dict

    def output(self, path):
        return confined(self.data_root, path)

    def source(self, path):
        path = Path(path).expanduser()
        return (path if path.is_absolute() else self.source_dir / path).resolve()


def load_config(path):
    path = Path(path).resolve()
    raw = load_json(path)
    try:
        if not isinstance(raw, dict) or not isinstance(raw["data_root"], str):
            raise ValueError()
        root = Path(raw["data_root"]).expanduser()
        root = (root if root.is_absolute() else path.parent / root).resolve()
        cosmos = raw["cosmos"]
        for key in ("archs", "regular_archs", "header_must_match"):
            value = cosmos[key]
            if not isinstance(value, list) or not value or len(set(value)) != len(value):
                raise ValueError()
            if not all(isinstance(x, str) and x.strip() for x in value):
                raise ValueError()
        if not set(cosmos["archs"]) <= set(cosmos["regular_archs"]):
            raise ValueError()
        if not {"profile", "build_conf", "base", "product"} <= set(cosmos["header_must_match"]):
            raise ValueError()
        for key in ("report", "summary", "expansion", "export"):
            if not isinstance(cosmos["report_markers"][key], str) or not cosmos["report_markers"][key].strip():
                raise ValueError()
        if not isinstance(cosmos["detail_table_title_prefix"], str) or not cosmos["detail_table_title_prefix"].strip():
            raise ValueError()
        status = cosmos["status_source"]
        if status is not None:
            if status["kind"] != "detail_page" or not status["complete_markers"]:
                raise ValueError()
            if not all(isinstance(s, str) and s.strip() for s in status["complete_markers"]):
                raise ValueError()
        if type(raw["poll"]["interval_s"]) not in (int, float) or raw["poll"]["interval_s"] <= 0:
            raise ValueError()
        if type(raw["poll"].get("stall_polls", 6)) is not int or raw["poll"].get("stall_polls", 6) < 2:
            raise ValueError()
        if type(raw["poll"].get("expected_hours", 24)) not in (int, float) or raw["poll"].get("expected_hours", 24) <= 0:
            raise ValueError()
        if type(raw["export"]["chunk_bytes"]) is not int or raw["export"]["chunk_bytes"] < 4:
            raise ValueError()
        allowed = {"report", "log", "results", "summary", "verification"}
        if not raw["export"]["allow_types"] or not set(raw["export"]["allow_types"]) <= allowed:
            raise ValueError()
        patterns = raw["prepush"]["credential_patterns"]
        if not isinstance(patterns, list) or not patterns:
            raise ValueError()
        for pattern in patterns:
            if not isinstance(pattern, str) or not pattern:
                raise ValueError()
            re.compile(pattern)
        if not isinstance(raw["p4"]["config_file"], str) or not raw["p4"]["config_file"]:
            raise ValueError()
        confined(root, raw["p4"]["config_file"])
        if raw.get("budget", {}).get("disk_warning_bytes", 0) < 0:
            raise ValueError()
    except (KeyError, TypeError, ValueError, re.error):
        raise FlowError(2, "invalid_config") from None
    # Check before creating data_root or any lock/database/artifact.
    filesystem = check_filesystem(root)
    return Config(raw, root, path.parent, filesystem)
