"""Campaign identity keys and isolated commit-msg hook generation."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path

from tizen_ci_shared.state.keys import build_submission_key

_HOOK_TIMEOUT = 30
_LOG = logging.getLogger(__name__)


class ChangeIdHookError(RuntimeError):
    """The isolated hook could not produce an unambiguous Change-Id."""

    code = "CHANGE_ID_HOOK_FAILED"


def build_campaign_unit_key(
    *,
    ci_system: str,
    source_build_id: str,
    project: str,
    branch: str,
    spec_name: str,
    base_commit: str,
) -> str:
    return json.dumps(
        [ci_system, source_build_id, project, branch, spec_name, base_commit],
        separators=(",", ":"),
        ensure_ascii=False,
    )


def build_submission_identity_key(
    *,
    ci_system: str,
    project: str,
    branch: str,
    spec_name: str,
    base_commit: str,
) -> str:
    return json.dumps(
        [ci_system, project, branch, spec_name, base_commit],
        separators=(",", ":"),
        ensure_ascii=False,
    )


def compute_submission_key(submission_identity_key: str, verified_tree_sha: str) -> str:
    return build_submission_key(
        failure_key=submission_identity_key,
        verified_tree_sha=verified_tree_sha,
    )


def _run_isolated(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    with subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as process:
        try:
            _, stderr = process.communicate(timeout=_HOOK_TIMEOUT)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
            raise
        if process.returncode != 0:
            raise ChangeIdHookError(
                f"command failed (exit {process.returncode}): "
                f"{stderr.decode('utf-8', errors='replace').strip()}"
            )


def generate_change_id_via_hook(
    *,
    hook_path: Path,
    hook_sha256: str,
    submission_key: str,
    message: str,
) -> str:
    """Return only the hook-generated identity; never access business state/repos."""
    if re.fullmatch(r"[0-9a-f]{64}", submission_key) is None:
        raise ChangeIdHookError("submission_key must be 64 lowercase hexadecimal characters")
    if re.match(r"^[a-z]+! ", message):
        raise ChangeIdHookError(
            "message first line matches ^[a-z]+! ; Gerrit hook skips Change-Id "
            "for fixup!/squash!-style commits"
        )
    if re.search(r"(?im)^\s*change-id\s*:", message) or re.search(
        r"(?im)^\s*link\s*:\s*\S+/id/I[0-9a-f]{40}\s*$",
        message,
    ):
        raise ChangeIdHookError("message already contains a Gerrit identity")
    temporary: Path | None = None
    try:
        hook_bytes = hook_path.read_bytes()
        if hashlib.sha256(hook_bytes).hexdigest() != hook_sha256:
            raise ChangeIdHookError("hook sha256 mismatch")
        # Do not honor a caller's TMPDIR pointing into a business worktree.
        temporary = Path(tempfile.mkdtemp(prefix="campaign-change-id-", dir="/tmp"))
        repo, home = temporary / "repo", temporary / "home"
        repo.mkdir()
        home.mkdir()
        env = {
            "PATH": os.environ.get("PATH", os.defpath),
            "LANG": os.environ.get("LANG", "C"),
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
        }
        for args in (
            ["init", "-q"],
            ["config", "--local", "user.name", "campaign"],
            ["config", "--local", "user.email", "campaign@invalid"],
            ["config", "--local", "gerrit.createChangeId", "true"],
            ["commit", "--allow-empty", "-q", "-m", "init"],
        ):
            _run_isolated(["git", *args], cwd=repo, env=env)
        hook_copy = temporary / "commit-msg"
        hook_copy.write_bytes(hook_bytes)
        message_file = temporary / "message"
        message_file.write_text(
            f"{message}\nX-Campaign-Submission-Key: {submission_key}\n",
            encoding="utf-8",
        )
        _run_isolated(["sh", str(hook_copy), str(message_file)], cwd=repo, env=env)
        matches = [
            match.group(1)
            for line in message_file.read_text(encoding="utf-8").splitlines()
            if (match := re.fullmatch(r"Change-Id: (I[0-9a-f]{40})\s*", line))
        ]
        if len(matches) != 1:
            raise ChangeIdHookError("hook must produce exactly one valid Change-Id line")
        return matches[0]
    except (OSError, UnicodeError, subprocess.SubprocessError) as exc:
        raise ChangeIdHookError(str(exc)) from exc
    finally:
        if temporary is not None:
            try:
                shutil.rmtree(temporary)
            except OSError as exc:
                _LOG.warning("cannot remove hook temporary directory %s: %s", temporary, exc)
