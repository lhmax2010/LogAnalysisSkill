"""Load the batch-one configuration; no network or browser initialization."""
from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

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
            required = {"kind", "url_template", "status_title_regex",
                        "terminal_words", "running_words", "queued_words"}
            if not isinstance(status, dict) or set(status) != required or status["kind"] != "detail_page":
                raise ValueError()
            if not isinstance(status["url_template"], str) or not status["url_template"].strip():
                raise ValueError()
            url = urlsplit(status["url_template"])
            if url.scheme not in {"http", "https"} or not url.netloc or url.username or url.password:
                raise ValueError()
            if not isinstance(status["status_title_regex"], str) or re.compile(status["status_title_regex"]).groups != 1:
                raise ValueError()
            seen = set()
            for key in ("terminal_words", "running_words", "queued_words"):
                words = status[key]
                if not isinstance(words, list) or not words or not all(isinstance(w, str) and w.strip() for w in words):
                    raise ValueError()
                normalized = {" ".join(w.split()).casefold() for w in words}
                if len(normalized) != len(words) or normalized & seen:
                    raise ValueError()
                seen.update(normalized)
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
