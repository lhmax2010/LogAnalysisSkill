"""Gerrit query and source fetch helpers."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

# isort: off
from tizen_ci_shared.types import GerritChange  # P4.9 shim, removed at P4.9 end (§6.2)
from tizen_ci_shared.types import GerritPatchSet  # P4.9 shim, removed at P4.9 end (§6.2)
from tizen_ci_shared.types import SourceFetchResult  # P4.9 shim, removed at P4.9 end (§6.2)
# isort: on

GERRIT_HOST = "review.tizen.org"
GERRIT_PORT = "29418"

SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]


class GerritError(RuntimeError):
    """Gerrit/source failure with a stable error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def query_change_for_commit(
    commit_hash: str,
    *,
    subprocess_runner: SubprocessRunner = subprocess.run,
) -> GerritChange:
    """Query Gerrit for a commit and find the exact patch set revision."""

    command = [
        "ssh",
        "-p",
        GERRIT_PORT,
        GERRIT_HOST,
        "gerrit",
        "query",
        "--format=JSON",
        "--patch-sets",
        f"commit:{commit_hash}",
    ]
    try:
        completed = subprocess_runner(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise GerritError("GERRIT_QUERY_FAILED", f"gerrit query failed: {exc}") from exc

    changes = parse_gerrit_query_output(completed.stdout)
    if not changes:
        raise GerritError("GERRIT_CHANGE_NOT_FOUND", f"no Gerrit change found for {commit_hash}")
    if len(changes) > 1:
        raise GerritError(
            "GERRIT_CHANGE_AMBIGUOUS",
            f"multiple Gerrit changes matched commit {commit_hash}",
        )
    return change_from_query_obj(changes[0], commit_hash)


def parse_gerrit_query_output(output: str) -> list[dict[str, Any]]:
    """Parse JSON-lines output from Gerrit, excluding the stats row."""

    changes: list[dict[str, Any]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        if obj.get("type") == "stats":
            continue
        if isinstance(obj, dict):
            changes.append(obj)
    return changes


def change_from_query_obj(obj: dict[str, Any], commit_hash: str) -> GerritChange:
    patchset = find_patchset_by_revision(obj, commit_hash)
    return GerritChange(
        project=str(obj.get("project") or ""),
        branch=str(obj.get("branch") or ""),
        status=str(obj.get("status") or ""),
        number=_optional_int(obj.get("number")),
        subject=str(obj.get("subject") or ""),
        url=str(obj["url"]) if isinstance(obj.get("url"), str) else None,
        matching_patchset=patchset,
    )


def find_patchset_by_revision(obj: dict[str, Any], target_hash: str) -> GerritPatchSet | None:
    """Return the patch set whose revision equals the build commit."""

    patchsets = obj.get("patchSets")
    if not isinstance(patchsets, list):
        return None
    for item in patchsets:
        if not isinstance(item, dict):
            continue
        if item.get("revision") != target_hash:
            continue
        ref = item.get("ref")
        revision = item.get("revision")
        if isinstance(ref, str) and isinstance(revision, str):
            return GerritPatchSet(
                number=_optional_int(item.get("number")),
                revision=revision,
                ref=ref,
            )
    return None


def fetch_source_for_commit(
    project: str,
    commit_hash: str,
    destination: Path,
    *,
    subprocess_runner: SubprocessRunner = subprocess.run,
    git_ssh_command: str | None = None,
) -> SourceFetchResult:
    """Create a shallow checkout for the build commit."""

    change = query_change_for_commit(commit_hash, subprocess_runner=subprocess_runner)
    remote_url = f"ssh://{GERRIT_HOST}:{GERRIT_PORT}/{project}"
    _reset_generated_source_dir(destination)
    destination.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    if git_ssh_command:
        env["GIT_SSH_COMMAND"] = git_ssh_command

    try:
        _run_git(["git", "init", str(destination)], subprocess_runner, env=env)
        _run_git(
            ["git", "-C", str(destination), "remote", "add", "origin", remote_url],
            subprocess_runner,
            env=env,
        )
        if change.status == "NEW":
            if change.matching_patchset is None:
                raise GerritError(
                    "PATCHSET_REVISION_NOT_FOUND",
                    f"change {change.number} did not contain patch set revision {commit_hash}",
                )
            _run_git(
                [
                    "git",
                    "-C",
                    str(destination),
                    "fetch",
                    "--depth",
                    "1",
                    "origin",
                    change.matching_patchset.ref,
                ],
                subprocess_runner,
                env=env,
            )
            _run_git(
                ["git", "-C", str(destination), "checkout", "--detach", "FETCH_HEAD"],
                subprocess_runner,
                env=env,
            )
        else:
            try:
                _run_git(
                    ["git", "-C", str(destination), "fetch", "--depth", "1", "origin", commit_hash],
                    subprocess_runner,
                    env=env,
                )
            except subprocess.CalledProcessError:
                if not change.branch:
                    raise
                _run_git(
                    [
                        "git",
                        "-C",
                        str(destination),
                        "fetch",
                        "--depth",
                        "50",
                        "origin",
                        change.branch,
                    ],
                    subprocess_runner,
                    env=env,
                )
            _run_git(
                ["git", "-C", str(destination), "checkout", "--detach", commit_hash],
                subprocess_runner,
                env=env,
            )
    except subprocess.CalledProcessError as exc:
        return SourceFetchResult(
            status="FAILED_SOURCE",
            src_root=destination,
            remote_url=remote_url,
            change=change,
            error=f"git command failed: {exc}",
        )
    except GerritError as exc:
        return SourceFetchResult(
            status=exc.code,
            src_root=destination,
            remote_url=remote_url,
            change=change,
            error=str(exc),
        )

    return SourceFetchResult(
        status="source_available",
        src_root=destination,
        remote_url=remote_url,
        change=change,
    )


def _run_git(
    command: Sequence[str],
    subprocess_runner: SubprocessRunner,
    *,
    env: dict[str, str],
) -> None:
    subprocess_runner(command, check=True, text=True, env=env)


def _reset_generated_source_dir(path: Path) -> None:
    if path.exists() and path.is_symlink():
        raise GerritError("SOURCE_DIR_UNSAFE", f"source directory is a symlink: {path}")
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _optional_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None
