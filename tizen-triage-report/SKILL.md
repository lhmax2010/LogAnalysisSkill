---
name: tizen-triage-report
description: Fetch and parse one QuickBuild GBS report, download package build logs, and render a human-readable triage report. Use only for GBS report acquisition, parsing, and report rendering; do not use it for build discovery, source fetch, repair decisions, compilation, or submission.
---

# Tizen Triage Report

Use this skill after QuickBuild discovery has selected a build and architecture.
The package root exposes only the nine symbols documented by `__all__`.
Fetching and parsing remain one integrated operation in `fetch_gbs_report`;
this skill deliberately does not split a raw-fetch layer from report parsing.
It requires Python 3.10 or newer and authenticated QuickBuild cookie data for
live fetches.

## Inputs

- A QuickBuild build id and raw architecture name.
- A cookie JSON path and QuickBuild base URL for authenticated fetches.
- An optional HTTP fetcher for controlled or offline execution.
- `render_report` accepts a populated `TriageReportData` value.

The raw architecture string is passed into the GBS report URL, returned
`GbsReport.arch`, and every parsed `GbsReportPackage.arch` without
normalization.

## Outputs

`fetch_gbs_report` returns a `GbsReport` containing the iframe URL and ordered
package rows. Its `failed_packages` property preserves package order while
filtering failed rows. `download_gbs_package_buildlog` returns the exact log
text for one package. `render_report` returns deterministic Markdown for a
fixed `TriageReportData` input.

## Errors

- Cookie, login-page, HTTP, missing-iframe, and package-log failures raise
  `QuickBuildError` with their documented stable codes.
- Malformed or non-status table rows are ignored according to the parser
  contract; they are not promoted into package records.
- The default urllib adapter supplies its existing HTTP timeout and converts
  URL failures through `QuickBuildError`. Unlike `tizen-gerrit-fetch`, this
  skill has no subprocess timeout to propagate; unlike `tizen-build-verify`,
  it has no build wall-time result; unlike `tizen-gerrit-submit`, it has no
  local-git versus `ls-remote` timeout split.

## Side effects

Live fetch operations read cookie data and perform authenticated HTTP GETs.
Package-log download returns text without writing it. Parsing and Markdown
rendering are in-memory operations and do not mutate QuickBuild, repositories,
or campaign state.

## Idempotency

For identical fetched bytes and inputs, parsing and rendering are
deterministic. Live fetch results can change with QuickBuild state, cookie
validity, and server responses; the skill performs no retry or remote mutation.
