"""Shared orchestration identity checks; repair-step behavior is unchanged."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from ci_triage.campaign_state import Unit

SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]
REJECTED_IDENTITY_MISMATCH = "REJECTED_IDENTITY_MISMATCH"
EXIT_REJECTED = 4


class _StepError(RuntimeError):
    def __init__(self, code: str, reason: str, exit_code: int) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason
        self.exit_code = exit_code


def _unit_hash(unit_key: str) -> str:
    return hashlib.sha256(unit_key.encode("utf-8")).hexdigest()[:12]


def _validate_source_identity(
    src_clean: Path,
    unit: Unit,
    *,
    subprocess_runner: SubprocessRunner,
) -> None:
    try:
        head = _git_stdout(src_clean, ["rev-parse", "HEAD"], subprocess_runner)
        origin = _git_stdout(src_clean, ["remote", "get-url", "origin"], subprocess_runner)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            f"source identity could not be read: {exc}",
            EXIT_REJECTED,
        ) from exc
    if head != unit.base_commit or _normalize_project(origin) != unit.project:
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            "source HEAD or origin does not match campaign unit",
            EXIT_REJECTED,
        )
    marker = src_clean / ".campaign_clone"
    try:
        marker_value: Any = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            f"campaign clone marker is unreadable: {exc}",
            EXIT_REJECTED,
        ) from exc
    expected = {
        "unit_key": unit.campaign_unit_key,
        "project": unit.project,
        "base_commit": unit.base_commit,
    }
    if marker_value != expected:
        raise _StepError(
            REJECTED_IDENTITY_MISMATCH,
            "campaign clone marker does not match campaign unit",
            EXIT_REJECTED,
        )


def _git_stdout(
    cwd: Path,
    args: list[str],
    subprocess_runner: SubprocessRunner,
) -> str:
    completed = subprocess_runner(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return (completed.stdout or "").strip()


def _normalize_project(remote: str) -> str:
    value = remote.strip()
    if "://" in value:
        path = urlsplit(value).path
    elif ":" in value and "@" in value.split(":", 1)[0]:
        path = value.split(":", 1)[1]
    else:
        path = value
    normalized = path.strip("/")
    if normalized.startswith("git/"):
        normalized = normalized[4:]
    return normalized.removesuffix(".git")
