# SKEL-R-04 / SKEL-R-06 Offline Verification

Status: **STOPPED_SKEL_R_07**, not accepted. See [stop report](../stop-report-SKEL-R-07.md).

Baseline: `8d60851`. This directory is separate from the preserved SKEL-R-05
stop report and its original-tree test results in the parent directory.

## Implementation Boundary

Production changes are confined to `installGuards` in
`tizen-qb-verify/scripts/tizen_qb_verify/qb_browser_agent.mjs`:

1. Classify every failure, even after the first OPERATION_FAILED was recorded.
2. Only `Fetch.failRequest` with category `REQUEST_ID_INVALID` produces
   `DENY_TARGET_GONE` and returns without the stop callback.
3. Every other operation/category retains the original stop callback.
4. Gone denials do not consume the first-cause slot. An actual subsequent
   failure (including read navigation cancellation) can therefore be the first
   OPERATION_FAILED, as explicitly required by SKEL-R-06(1c).
5. DENY_TARGET_GONE has exactly action, phase, stage, path, generation, using
   the same fixed/sanitized metadata as the accepted diagnostic implementation.
   Diagnostic writer errors do not change the selected stop outcome.

No allow/deny rule, frame ownership rule, grammar, response/error code, Python
driver, safety core, identity check, result writer, schema or frozen document
changed. `integrity.json`, `production.diff`, and `audit.py.txt` record this
boundary and the before/after full-agent and prefix hashes.

## Authorized Existing-Test Changes

All are in `tests/node/test_qb_read_failure_diagnostics.mjs`; see the exact
`authorized-test.diff`. No other existing test is modified.

| Case at baseline | Before | After |
|---|---|---|
| Parameterized three Fetch methods, line 40 | All stop, all OPERATION_FAILED | failRequest alone: no stop, one DENY_TARGET_GONE, no OPERATION_FAILED; both continue cases unchanged; sensitive scan retained |
| Two failures, line 60 | Two stops | Session closed stops once; later invalid ID produces one DENY_TARGET_GONE; first OPERATION_FAILED remains TARGET_OR_SESSION_CLOSED |
| Navigation cancellation, line 96 | Fetch stop; first cause Fetch.failRequest | No Fetch stop; one DENY_TARGET_GONE; read still QB_BROWSER_UNAVAILABLE and first cause page.goto/NAVIGATION_INTERRUPTED |

The last Node case was renamed from
`read navigation cancellation concurrent with a rejected Fetch keeps initiating failure`
to `read navigation cancellation after a gone deny records navigation as first failure`.
Its pytest wrapper/nodeid did not change. Other Node test titles are preserved.

## Added Tests

- `tests/node/test_qb_deny_target_gone.mjs`: 23 cases, including the full three
  operations by seven categories matrix, repeated gone denials before/after a
  real failure, first-cause retention, throwing trace sink and sensitive scans.
- `tests/node/p5q_deny_target_gone_browser.mjs`: real Chromium against local
  HTTPS with a test-only certificate and resolver rules. It cancels an actual
  paused navigation with Page.stopLoading, then invokes the original real
  Fetch.failRequest, twice. Both actual CDP rejections produce DENY_TARGET_GONE;
  the server receives zero canceled requests. The same session then checks
  ordinary denied requests, a forbidden listener, an injected unknown frame,
  307/308, and finally an allowed request. No fabricated CDP exception or
  response is used for the canceled-request check.
- `tests/unit/test_qb_deny_target_gone.py`: two pytest wrappers for these tests.
  Browser execution requires the existing private virtual-display runner.

## Evidence

- `focused/`: 223 pytest passes; revised 17-case diagnostic suite, added 23-case
  matrix and real cancellation fixture; unchanged agent matrix, stop-category
  and static-mutation suites. The fixture is `deny-gone/browser.json`.
- `safety/`: four unchanged local HTTPS interception safety groups.
- `c8-01` through `c8-04`: independent serial runs,
  original pytest stdout/stderr/JUnit, load and process-name/CPU observations,
  original fake-server requests and agent traces. Summary records distinguish
  expected injected read failures from failed pytest runs. Three passed; the
  fourth failed at fake login in racing-wicket-navigation (TargetClosedError,
  no login POST, no Fetch failure diagnostic). Remaining 16 C8 runs and all
  20 late-build runs were not started, per the new-failure stop rule.
- Full regression: **NOT_RUN_STOPPED**. No `-x`/`--maxfail` full run was used;
  focused test totals are not presented as complete regression results.
- `mypy/`, `imports/`, `design/`, `ruff-recheck/`, `collect/`: gates.
- `integrity.json`: all 3098 baseline pytest nodeids retained, two added.
- `run.py.txt`: runner; `audit.py.txt`: reproducible scope audit.

The first ruff invocation (`ruff/`) failed in the evidence wrapper because its
list of files included `tests/run_quiet.py`, mistakenly triggering addition of
pytest's JUnit argument. Only the runner's command detection was fixed; the
unchanged production/test tree passed `ruff-recheck/`. Original failed command
and output are retained, not counted as a source lint failure or hidden.

The first completed C8 run passed pytest, but its evidence wrapper treated
`summary.json` (a list) as a mapping during metadata aggregation and exited 1.
Its original files are retained under `wrapper-error-c8-01/`; end load and the
subprocess exit code were not durably collected and are marked null. Only the
wrapper type check was fixed. This preliminary run is outside the 20 formal
runs; formal runs started afresh with complete metadata. This is not a
rerun used to hide a test failure and does not change test assertions.

`sampling-results.md` and `results.json` contain the four completed attempts.
Two natural DENY_TARGET_GONE entries in c8-04/racing-meta-refresh did not stop
that session (runtime failure null, browser connected). They are separate from
the following scenario's login-stage failure. No FETCH_CONTINUE_FAILED was
observed in these four attempts; this does not make the failed attempt pass.
`final-checks.json` records final source/document whitespace checks, diagnostic
schema/sensitive scan and P5Q-specific process/profile leftovers.
No real QuickBuild, Gerrit or gbs is used; no CPU stress is started.
