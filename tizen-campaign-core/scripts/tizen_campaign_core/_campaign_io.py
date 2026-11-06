"""Small filesystem/process primitives shared by campaign intake and baseline."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, NoReturn

import yaml

from tizen_campaign_core._campaign_workspace import _StepError


class JsonParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise ValueError(message)


def config(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not value.get("campaign_workspace"):
        raise ValueError("config requires campaign_workspace")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@contextmanager
def lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise _StepError("CAMPAIGN_STATE_BUSY", str(path), 4) from exc
        yield


def fsync_parent(path: Path) -> None:
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def publish(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix="." + path.name + ".")
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != raw:
                raise _StepError("REJECTED_STATE_INCONSISTENT", "evidence differs", 4) from None
        except OSError as exc:
            raise _StepError("WORKSPACE_FS_UNSUPPORTED", "hard-link publication failed", 5) from exc
    finally:
        temporary.unlink(missing_ok=True)
    fsync_parent(path)


def analyze(log: Path, output: Path, *, src_root: Path | None = None) -> Path:
    argv = [
        sys.executable,
        "-m",
        "gbs_analyzer",
        "analyze",
        str(log),
        "--output-dir",
        str(output),
        "--output-format",
        "both",
    ]
    if src_root is not None:
        argv += ["--src-root", str(src_root)]
    subprocess.run(argv, check=True, capture_output=True, text=True)
    evidence = output / "evidence_packet.json"
    value = json.loads(evidence.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("analyzer evidence must be an object")
    return evidence
