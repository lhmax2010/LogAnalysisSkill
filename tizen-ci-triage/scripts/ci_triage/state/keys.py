"""Deterministic keys for CI triage verification and submission units."""

from __future__ import annotations

import hashlib


def build_failure_key(
    *,
    ci_system: str,
    build_id: str,
    project: str,
    branch: str,
    arch: str,
    spec_name: str,
    base_commit: str,
) -> str:
    """Build the stable key for one CI failure.

    ``project`` is the full Gerrit project path, for example
    ``platform/core/multimedia/inference-engine-interface``. It already uniquely
    identifies the repository, so the key intentionally has no separate repo
    segment.
    """

    return "/".join(
        (
            ci_system,
            build_id,
            project,
            branch,
            arch,
            spec_name,
            base_commit,
        )
    )


def build_submission_key(*, failure_key: str, verified_tree_sha: str) -> str:
    """Build the stable private key for one verified tree submitted for a failure."""

    raw_key = f"{failure_key}:{verified_tree_sha}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def failure_key_sha12(failure_key: str) -> str:
    """Return a deterministic 12-character hash for compact Gerrit topics."""

    return hashlib.sha256(failure_key.encode("utf-8")).hexdigest()[:12]
