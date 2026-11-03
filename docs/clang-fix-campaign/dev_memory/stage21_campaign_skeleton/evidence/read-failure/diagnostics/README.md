# SKEL-R-02 Diagnostic-Only Verification

Baseline: `6c5f640`. Authority: stage21 progress section 20, SKEL-R-02.
Status: **STOPPED_SKEL_R_03, not accepted**. See
`stop-report-SKEL-R-03.md`: full regression stopped at a new C8 failure scenario
(901 passed, 1 failed, 2196 not run). The code is retained for design review.
This implements investigation candidates A/C/D, not candidate B. It does not
claim to fix or uniquely identify the intermittent CDP rejection.

## Scope And Observation Contract

Only `installGuards`, the navigation catch in `Agent.read`, the catch in
`Agent.command`, and `QbBrowser.close` changed in production. See
`production.diff` and `integrity.json`. Existing tests and their assertions,
Policy, frame ownership, trusted-page parsing, security cores, identity checks,
result writing, schema, frozen files and all other tracked skills are unchanged.

The illustrative A/C proposal entries are combined into one first-cause entry
`OPERATION_FAILED` per installed runtime. This prevents a later navigation
cancellation or command catch from overwriting the initiating Fetch failure.
All failed Fetch operations still invoke the original stop callback, including
the second and later failures. No error is ignored, retried or reclassified in
the protocol response. Error text is inspected only to select a fixed category;
it is never serialized. Diagnostic getters/sinks are guarded independently of
the original stop/error path. A failed first diagnostic write is not replaced
with a later, misleading cause.

| Field | Complete domain |
|---|---|
| action | `OPERATION_FAILED` |
| operation | `Fetch.failRequest`, `Fetch.continueRequest`, `Fetch.continueResponse`, `page.goto`, `Agent.command`, fallback `OTHER` |
| phase | `login`, `read`, `open_form`, `fill`, `submit`, `idle`, fallback `unknown` |
| stage | `request`, `response`, `navigation`, `command`, fallback `unknown` |
| path | Existing `pathShape`: `/`, `/signin`, `/dashboard`, `/wicket/page`, `/overview/<id>`, `/build/<id>` with optional `/overview`, `/variables`, `/step_status`, fallback `<other>` |
| generation | Nonnegative safe integer; committed main-frame navigation count since guard installation, captured when scheduling the operation, fallback 0 |
| category | `REQUEST_ID_INVALID`, `TARGET_OR_SESSION_CLOSED`, `NAVIGATION_INTERRUPTED`, `BLOCKED_BY_CLIENT`, `CONNECTION_FAILED`, `TIMEOUT`, `OTHER` |

The passive generation listener does not supply or change frame ownership.
The command catch observes only read/submit failures. Diagnostic properties on
Policy are not consulted by its allow/deny decisions.

Python `close_observation` has exactly `elapsed_ms` (nonnegative integer) and
`returncode` (integer or null). It is an internal observation attribute, not an
additional command response, stdout field, DB value or automatic CLI trace
entry. The elapsed time covers the existing close start through cleanup,
including the unchanged wait/termination path. No process means the existing
early return; there is then no new observation. Diagnostic errors cannot mask
an original cleanup exception or turn a successful close into failure.

## New Coverage

| Requirement | Test location | Cases |
|---|---|---:|
| Three rejected Fetch methods; original stop, fixed metadata and secret scan | `tests/node/test_qb_read_failure_diagnostics.mjs`, `rejected ... still stops` | 3 |
| Capture phase/generation at scheduling; two failures retain first | same file, `capture scheduling phase...` | 1 |
| Read navigation's complete category enum; unchanged response and cleanup | same file, `read navigation diagnostic ...` | 7 |
| Concurrent cancellation and refusal retain initiating Fetch failure | same file, `read navigation cancellation concurrent...` | 1 |
| read/submit command catch and unchanged released-submit response | same file, `command catch...`, `released submit response...` | 3 |
| Diagnostic getter/sink throws without changing original stop/rejection | same file, last two tests | 2 |
| Real child process close, with and without reply | `tests/unit/test_qb_read_failure_diagnostics.py::test_close_real_process_with_or_without_reply` | 2 |
| Normal, timeout/terminate, write exception, cleanup exception | same file, `test_close_observation_preserves_existing_paths` | 4 |
| Diagnostic poll/sink errors suppressed | same file, `test_close_diagnostic_failure_does_not_escape` | 2 |
| No-process close remains unchanged | same file, `test_close_without_process_is_unchanged` | 1 |

The 17 Node cases run under one additional pytest wrapper, giving 10 new pytest
nodeids, not 27. Synthetic secret strings are test inputs only; assertions scan
trace/observations for their absence. `focused/` archives the new cases and
unchanged driver, agent matrix, stop-category and static-mutation tests.

## Evidence Layout

- `run.py.txt`: reproducible offline gate runner, individual output directories.
- `audit.py.txt`, `integrity.json`, `production.diff`: before/after hashes,
  production scope, unchanged existing tests, retained 3088 nodeids plus 10 new.
- `focused/`: 221 pytest passes; Node cases and static negative controls in stdout.
- `safety/`: four local HTTPS safety groups, server counters and cleanup facts.
- `collect/`: complete 3098-nodeid list; no collection errors.
- `mypy/`, `ruff/`, `imports/`, `design/`: command, load, stdout and stderr.
- `full/`: full regression, JUnit and C5a/C8 synthetic evidence; results recorded
  separately in `results.json` after completion.

All browser runs use the local fake server and virtual display. No real
QuickBuild, Gerrit or gbs command was run. No temporary instrumented production
copy or CPU stress process is needed for this diagnostic implementation.

`final-checks.json` also records the natural failure's fixed-schema/secret scan,
C5a close tails and final design check. Scoped source/document whitespace checks
pass. The full staged evidence check returns 2 for original fixture HTML,
pytest failure output and the literal diff's whitespace; these raw artifacts
are preserved, not cleaned to make the evidence check green.
