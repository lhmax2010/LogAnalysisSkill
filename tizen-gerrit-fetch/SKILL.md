---
name: tizen-gerrit-fetch
description: Query Gerrit for an exact build commit and create a disposable shallow source checkout. Use only for Tizen Gerrit source acquisition; do not use it for QuickBuild discovery, GBS report parsing, repair decisions, compilation, or submission.
---

# Tizen Gerrit Fetch

Use this skill when orchestration must resolve a build commit through Gerrit
and recreate a tool-owned source destination for analysis or verification.
The package root exposes exactly `fetch_source_for_commit`, `GerritError`,
`GERRIT_HOST`, and `GERRIT_PORT`.

## Inputs

- Gerrit project name and exact commit hash.
- A destructive `destination` path owned by this tool. Every successful query
  is followed by deletion and recreation of that path; never pass a directory
  containing user-managed data.
- An optional subprocess runner for controlled execution and an optional
  `git_ssh_command` propagated to every git subprocess.

The implementation sets no timeout or cancellation. A caller may enforce a
deadline through its subprocess runner.

## Outputs

`fetch_source_for_commit` returns `SourceFetchResult` with
`source_available` after checkout, `FAILED_SOURCE` for a git
`CalledProcessError`, or the code from a `GerritError` raised inside the git
phase, currently `PATCHSET_REVISION_NOT_FOUND`.

The operation performs one Gerrit SSH query. A NEW change fetches its matching
patch-set ref at depth 1. A non-NEW change first fetches the commit at depth 1
and, only when that fails and a branch is known, fetches that branch at depth
50 before checkout. No other retry or network path is present.

## Errors

- Query failure, no matching change, and ambiguous changes raise
  `GerritError` with stable query error codes before destination deletion.
- A live destination symlink raises `SOURCE_DIR_UNSAFE` without deleting the
  link or its target.
- A dangling destination symlink is not recognized by `Path.exists()`; the
  following `mkdir(..., exist_ok=True)` raises `FileExistsError`.
- JSON, change-conversion, filesystem, `subprocess.TimeoutExpired`, and other
  non-`CalledProcessError` runner exceptions propagate unchanged. A timeout is
  not converted to `GerritError` or `FAILED_SOURCE`.

## Side effects

After a successful query, the destination is synchronously removed and
recreated. Git initialization, remote setup, fetch, and checkout run serially.
Failures, timeouts, or external interruption can leave any completed subset of
that directory and its git state behind. Recursive removal cost grows with the
destination tree and filesystem performance; there is no progress callback or
fake-runner wall-clock guarantee.

## Idempotency

The operation is not idempotent: every invocation rebuilds the destination and
its result depends on current Gerrit state. Repeated calls are supported only
for a disposable path owned by the tool.
