"""Load configuration and local storage prerequisites, without network I/O."""
from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
from string import Formatter
from urllib.parse import urlsplit

from .errors import FlowError
from .files import confined, load_json

FETCH_DEFAULTS = {"timeout_s": 60, "max_page_bytes": 20 * 1024 * 1024,
                  "max_log_bytes": 200 * 1024 * 1024, "log_concurrency": 4,
                  "user_agent": "VD-Cosmos-LogAnalyzer/0.5.3"}


def validate_template(value, allowed):
    if not isinstance(value, str) or not value:
        raise ValueError()
    for _, field, spec, conversion in Formatter().parse(value):
        if field is not None and (field not in allowed or spec or conversion):
            raise ValueError()


def validate_url(value):
    if not isinstance(value, str):
        raise ValueError()
    url = urlsplit(value)
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.fragment:
        raise ValueError()
    if any(char.isspace() for char in value):
        raise ValueError()
    _ = url.port  # Reject malformed ports while validating configuration.
    return url


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
            validate_url(status["url_template"])
            validate_template(status["url_template"], {"build_id"})
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
        if "report_root" in cosmos:
            validate_url(cosmos["report_root"])
            validate_template(cosmos["report_path_template"], {"last3", "build_id", "arch"})
        validate_template(cosmos.get("bucket_path_template", "b{last3}/"), {"last3", "build_id"})
        raw["fetch"] = FETCH_DEFAULTS | raw.get("fetch", {})
        fetch = raw["fetch"]
        if type(fetch["timeout_s"]) not in (int, float) or fetch["timeout_s"] <= 0:
            raise ValueError()
        for key in ("max_page_bytes", "max_log_bytes", "log_concurrency"):
            if type(fetch[key]) is not int or fetch[key] <= 0:
                raise ValueError()
        if not isinstance(fetch["user_agent"], str) or not fetch["user_agent"].strip() or any(c in fetch["user_agent"] for c in "\r\n"):
            raise ValueError()
        network = raw.setdefault("network", {})
        if not isinstance(network, dict):
            raise ValueError()
        if network.get("proxy"):
            validate_url(network["proxy"])
        if not isinstance(network.get("no_proxy_hosts", []), list) or not all(isinstance(h, str) and h.strip() for h in network.get("no_proxy_hosts", [])):
            raise ValueError()
        if network.get("ca_file") is not None and not isinstance(network["ca_file"], str):
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
