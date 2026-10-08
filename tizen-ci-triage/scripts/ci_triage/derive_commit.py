"""Create a detached commit object from an already verified tree, never from the index."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


def _identity(value: str) -> tuple[str, str]:
    match = re.fullmatch(r"([^<>\r\n]+) <([^<>\r\n]+)>", value)
    if match is None or not match[1].strip() or not match[2].strip():
        raise ValueError("identity must be Name <email> on one line")
    return match[1], match[2]


def derive(
    worktree: Path,
    tree_sha: str,
    parent_sha: str,
    message: str,
    author_identity: str,
    committer_identity: str,
    author_date: str,
    committer_date: str,
) -> str:
    """Write a commit object only; callers own message construction and state recording."""
    author_name, author_email = _identity(author_identity)
    committer_name, committer_email = _identity(committer_identity)
    for label, value in (("tree_sha", tree_sha), ("parent_sha", parent_sha)):
        if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value) is None:
            raise ValueError(f"{label} must be a full lowercase Git object ID")
    if not author_date or not committer_date:
        raise ValueError("author_date and committer_date must be explicit")

    # Ambient Git routing/configuration must not redirect writes to another repository.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_AUTHOR_NAME": author_name, "GIT_AUTHOR_EMAIL": author_email,
        "GIT_COMMITTER_NAME": committer_name, "GIT_COMMITTER_EMAIL": committer_email,
        "GIT_AUTHOR_DATE": author_date, "GIT_COMMITTER_DATE": committer_date,
        "GIT_NO_REPLACE_OBJECTS": "1", "GIT_NO_LAZY_FETCH": "1",
    })
    command = ["git", "-C", str(worktree), "-c", "commit.gpgsign=false",
               "-c", "i18n.commitEncoding=UTF-8"]
    commit = subprocess.run(
        [*command, "commit-tree", tree_sha, "-p", parent_sha],
        input=message.encode("utf-8"), capture_output=True,
        env=env, check=True,
    ).stdout.decode("ascii").strip()
    actual_tree = subprocess.run(
        [*command, "rev-parse", "--verify", f"{commit}^{{tree}}"],
        capture_output=True, env=env, check=True,
    ).stdout.decode("ascii").strip()
    if actual_tree != tree_sha:
        raise RuntimeError(f"derived tree mismatch: expected={tree_sha} actual={actual_tree}")
    return commit
