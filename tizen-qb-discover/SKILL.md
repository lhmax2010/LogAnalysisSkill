---
name: tizen-qb-discover
description: Discover recent failed builds from a configured QuickBuild overview and return structured FailedBuild records. Use only for authenticated QuickBuild overview discovery; do not use it for GBS report parsing, package-log analysis, repair classification, patch generation, compilation, or submission.
---

# Tizen QuickBuild Discover

Use this skill when orchestration needs the failed builds visible in one
QuickBuild overview during a specified time window.

## Inputs

- A lower-bound `datetime` for build discovery.
- A QuickBuild cookie JSON path.
- An optional numeric overview configuration id and base URL.
- An optional HTTP fetcher for controlled or offline execution.

The skill does not fetch GBS package reports or build logs. Those are separate
capabilities invoked after discovery.

## Outputs

`QuickBuildSource.discover` returns deterministic `FailedBuild` records for
failed rows at or after the requested lower bound. The source also exposes
warnings when the overview may have truncated the requested history.

## Errors

- `INVALID_OVERVIEW_ID` rejects non-numeric configuration ids before cookie or
  network access.
- Cookie and authentication failures propagate as `QuickBuildError` with their
  stable error code.
- A missing Recent Builds table reports the overview URL and the possible
  cookie, id, or authorization causes.

## Idempotency

For identical overview HTML and time input, discovery returns the same ordered
records. The skill performs authenticated reads only and does not mutate
QuickBuild or repository state.
