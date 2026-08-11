"""Shared dependency-free data types for CI triage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GerritPatchSet:
    """Patch set matching a build commit."""

    number: int | None
    revision: str
    ref: str


@dataclass(frozen=True)
class GerritChange:
    """Relevant Gerrit change metadata for a build commit."""

    project: str
    branch: str
    status: str
    number: int | None
    subject: str
    url: str | None
    matching_patchset: GerritPatchSet | None


@dataclass(frozen=True)
class SourceFetchResult:
    """Source checkout result."""

    status: str
    src_root: Path
    remote_url: str
    change: GerritChange | None = None
    error: str | None = None


@dataclass(frozen=True)
class FailedPackage:
    """A failed package reported by QuickBuild publish logs."""

    fail_pkg: str
    spec_name: str
    dest_file: str | None = None
