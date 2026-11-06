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
- A destructive `destination` path owned by this tool. After a successful query
  and source-directory safety check, that path is deleted and recreated; never
  pass a directory containing user-managed data.
- An optional subprocess runner for controlled execution and an optional
  `git_ssh_command` propagated to every git subprocess.
- An optional keyword-only `timeout: float | None = None`, passed to the Gerrit
  query and each git subprocess. `None` imposes no subprocess timeout; a value
  applies separately to each call, not to the whole operation.

The implementation does not catch SIGINT or SIGTERM and does not automatically
roll back residual files after timeout or interruption.

## Outputs

`fetch_source_for_commit` returns `SourceFetchResult` with
`source_available` after checkout, `FAILED_SOURCE` for a git
`CalledProcessError`, or `PATCHSET_REVISION_NOT_FOUND` when a NEW change lacks
the requested patch-set revision. `FETCH_TIMEOUT` is raised, not returned as a
`SourceFetchResult`.

The operation performs one Gerrit SSH query. A NEW change fetches its matching
patch-set ref at depth 1. A non-NEW change first fetches the commit at depth 1
and, only when that fails and a branch is known, fetches that branch at depth
50 before checkout. No other retry or network path is present.

## Errors

- Query failure, no matching change, and ambiguous changes raise
  `GerritError` with stable query error codes before destination deletion.
- Both live and dangling destination symlinks raise
  `GerritError("SOURCE_DIR_UNSAFE", "source directory is a symlink: <path>")`.
  The link and its target remain untouched, and no git command runs.
- A query or git subprocess `TimeoutExpired` raises
  `GerritError("FETCH_TIMEOUT", str(exc))`, retaining the original exception as
  its cause. A query timeout occurs before destination reset; a git timeout
  leaves whatever state that stage has already produced.
- JSON, change-conversion, filesystem, and other runner exceptions retain their
  existing propagation behavior. External interruption is not caught or
  normalized.

## Side effects

After a successful query and safety check, the destination is synchronously
removed and recreated. Git initialization, remote setup, fetch, and checkout
run serially. Query failure, timeout, or interruption leaves the destination
unchanged. Git-stage failure, timeout, or interruption leaves the state already
produced by that stage, without automatic cleanup. Recursive removal cost grows with the
destination tree and filesystem performance; there is no progress callback or
fake-runner wall-clock guarantee.

## Idempotency

The operation is not idempotent: every invocation rebuilds the destination and
its result depends on current Gerrit state. Repeated calls are supported only
for a disposable path owned by the tool.
