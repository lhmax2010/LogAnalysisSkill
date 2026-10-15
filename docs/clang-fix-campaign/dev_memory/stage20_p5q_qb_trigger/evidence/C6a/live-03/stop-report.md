# C6a live-03 Stop Report

## Observed Result

New authorization was the literal reply `确认提交`, after the user requested another
window and was told that the production command automatically proceeds to submit
after login. One recorder invocation was made with the original production argv.
There was no `--retrigger`, alternate browser path, or follow-up result fetch.

The recorder completed successfully (exit 0); the production CLI returned **exit 5**:

- action: `rejected`
- error_code: `QB_BROWSER_UNAVAILABLE`
- status: `SANDBOX_PUSHED`
- request_id: `e724b5428a4a45a5a2d03a0a93e6eb25`
- request_seq, qb_build_id, diagnostic_dir, message: all null

Raw, checked production output is in `trigger/stdout.json`; argv and timestamps
are in `trigger/command.json` and `trigger/execution.json`. Stderr contains only
the fixed login prompt. Start/end UTC:
2026-10-15T08:03:41.724509+00:00 / 2026-10-15T08:08:04.355155+00:00.

## State and Evidence Boundary

`stop-audit.json` verifies an unchanged database SHA256 and byte-identical SQL
versus live-01. All three QB tables remain empty; the unit remains SANDBOX_PUSHED.
The request ID was generated only in memory/output and was never persisted.

Source inference, not an archived page observation: `qb_trigger.py:571` calls
login before the request ID is generated at line 577; login therefore returned
normally. The intent write at line 608 precedes submit. No intent was persisted,
so this execution did not reach the submit step.

The exact failed command and original agent error are **unknown**. The driver can
map several paths to QB_BROWSER_UNAVAILABLE; no trace or diagnostic was archived.
Do not infer a particular open-form, fill, transport, protocol or browser failure.
No new network call was made to diagnose it. HTTP request count is NOT_COLLECTED.

No parent build was obtained. BUILD_NOTES, BUILD_REFERENCE, SNAPSHOT_NUM, landed
state and build ID are NOT_COLLECTED. There is no persisted request for C6b.
All four known recorder/CLI/agent/Chromium PIDs have exited. The two remaining
browser-directory mtimes predate this run; only metadata was inspected, no content
was read, and no process references either path. No attribution is made.

## Candidate Follow-up (Not Implemented)

Ask the design owner to authorize fixed command-phase/error-category evidence
and safely filtered trace at the production driver boundary, then locate the
failure before considering another authorized invocation. Do not log original
protocol events, credentials or unredacted response bodies, and do not relax
Policy or installGuards. No production change or retry is part of this record.
