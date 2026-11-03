# SKEL-R-01: Read Failure Investigation

Base: `a58494b`, `clang-fix-campaign`. Offline observation only. No production,
test assertion, frozen design, safety core or live state DB is changed. Local
fake HTTPS and private virtual displays only; no live QuickBuild, Gerrit or gbs.

## Evidence Index

- `sampling-results.md`, `summary.json`: sample counts, load ranges, exact failures.
- `regular-late/run-*/`: unchanged late-build test, 50 independent runs.
- `regular-c8/run-*/`: unchanged complete C8 investigation, 20 runs.
- Each run: `command.json` contains argv, UTC, exit, load samples, JUnit failures,
  AGENT_STOPPED and harness_failure. Raw stdout/stderr/JUnit are retained.
- `failure-facts.json`: failed executions' command replies, close times and server
  request order, excluding payloads in this derived view.
- `environment-disturbance.json`: read-only host observation during the slower runs.
- `integrity-before.json`: all tracked skill/test/frozen files equal `a58494b`.
- `sample.py.txt`, `summarize.py.txt`, `failure_facts.py.txt`, `audit.py.txt`:
  evidence-only orchestration/aggregation, not production or test replacements.

The initial evidence wrapper did not create pytest's basetemp parent. Its 27
setup errors and interrupted 28th startup are preserved under `setup-errors-late/`;
none entered the browser fixture. Only the wrapper was corrected, then a new
temporary root and new output directories were used. These are excluded from
read-failure rates, not hidden or overwritten.

## Formal Sampling Result

| Group | Runs | Pass / fail / skip | Failure rate | FETCH_CONTINUE_FAILED | 1-minute load range |
|---|---:|---|---|---:|---|
| Regular late-build | 50 | 47 / 3 / 0 | 6% | 0 | 1.17–40.77 |
| Regular C8 full investigation | 20 | 19 / 1 / 0 | 5% | 1 | 0.47–14.14 |
| Conditional half-core CPU stress | 0 | Not started | N/A | N/A | N/A |

The stress condition is literally "50 runs without failure"; regular late-build
had three failures, so that condition was not met. No CPU load process was created.
The observed resource disturbance is part of the regular sample, not relabeled
as the requested controlled CPU-stress group. This bounds what can be concluded.

Formal total: **66 passed / 4 failed / 0 skipped**, 70 independent invocations.
The C8 test completed 215 scenario executions: 19 full sets of 11, and run-15
stopped in its sixth scenario; its final five scenarios were not executed.
Its injected UNKNOWN responses are expected diagnostic outcomes, not extra pytest
failures. `summary.json` lists every scenario's response/error-category distribution.
Both groups retain the original assertions, including the 5-second close threshold.

## Failure Positions

| Sample | Command / stage | Established event sequence | Limit |
|---|---|---|---|
| Batch 2 late-build | First lookup `read /overview/1917` | Submit replies released/unknown; DENIED submit `/wicket/page`; AGENT_STOPPED FETCH_CONTINUE_FAILED; first lookup replies unavailable; expected 10 reads, got 1; server has only baseline/open_form's two configuration GETs and no lookup GET | Read refusal follows earlier stop, not server processing of a lookup GET; no CDP method/error category recorded |
| Batch 1 flaky-pre/run-02 racing-meta-refresh | Between submit reply and first read | Server received form POST 302 and landing GET 200; owned-frame GET `/wicket/page` denied in submit; FETCH_CONTINUE_FAILED; submit returns unknown; harness `Page.getFrameTree` throws TargetClosedError | `reads=[]`, root_after_submit absent; this is not evidence that the meta-refresh interrupted a read |
| P5Q C8 live-01 | First lookup `read /overview/1917`, 579 ms | QB_BROWSER_UNAVAILABLE / UNKNOWN; agent not observed to exit | Distinct signature; neither frame loss nor a canceled Fetch operation was captured |
| regular-late/run-40 | Trigger closure after lookup | All 10 lookup reads succeed; server receives one synthetic submission; close succeeds; agent close 4.224 s, close-to-CLI 5.487124443 s; assertion `< 5` fails | Not a read failure; no AGENT_STOPPED |
| regular-late/run-41 | Submit before release, then closure | Login/baseline/open_form/fill succeed; server receives all 12 field callbacks but zero form submissions; submit returns unavailable/UNKNOWN/released=false; close succeeds in 12.587 s; close-to-CLI 13.619728327 s fails `< 5` | No post-submit read; underlying framework exception class not retained |
| regular-late/run-42 | CLI before any server request | Original test's 150 s subprocess timeout; server receives zero requests, no agent transcript or close timestamps | Cannot distinguish startup/probe/session establishment waits with existing evidence |
| regular-c8/run-15, injected-missing-root-membership | After submit, before injection and before read | Server receives form POST 302 and landing GET 200; final owned-frame GET `/wicket/page` is denied in submit; FETCH_CONTINUE_FAILED; submit still returns released/unknown; harness's following Page.getFrameTree throws TargetClosedError | `injected_fault` absent, `reads=[]`, root_after_submit absent. The named ownership fault has not been injected; this is a natural failure during shared setup, not evidence that the injection caused it |

Historical sources:

- `../batch2/implementation/full/c5a/late-build/agent-0.json`,
  `commands.json`, `server-requests.json` and full pytest output.
- `../batch1/baseline/flaky-pre/run-02/node/racing-meta-refresh.json`.
- `../../../stage20_p5q_qb_trigger/evidence/C8/live-01/stop-report.md` and
  `../../../stage20_p5q_qb_trigger/evidence/C8/investigation/README.md`.

The current run-15 reproduces the historical Batch 1 event shape before the
scenario-specific action. Thus neither meta-refresh nor deliberately detached
ownership is necessary for this observed failure. The precise rejecting CDP
method and underlying exception remain absent from the unchanged agent's trace.

Regular-late failures coincide with a load rise (run-42 reaches 40.77 on 20
logical CPUs). The host observation records D-state tasks and nearly full swap.
This is correlation, not proof of a single resource cause. No artificial load
was started and no unrelated process was terminated. Existing browser close
thresholds and CLI timeouts were not changed.

## Mechanism And Confidence

**Certain from source:** `installGuards` at `qb_browser_agent.mjs:193-242` funnels
rejected `Fetch.failRequest`, `Fetch.continueRequest` and `Fetch.continueResponse`
promises into the same FETCH_CONTINUE_FAILED category. Its pending set is not
drained at a navigation/phase boundary. The runtime callback at :956-958 sets
failure and closes the browser. Consequently a read/harness operation may only
observe the resulting TargetClosedError, not the initiating protocol rejection.
No conclusion that the HTTP allowlist was too narrow follows from that sequence.

**Candidate, not yet established:** an old document's periodic refresh is canceled
during form navigation, and an in-flight reject/continue operation then addresses
an expired interception ID. The historical last denied request is `/wicket/page`,
while the fixture periodically requests `ajaxRefresh` on that path. Historical
path-shape evidence loses the query and request ID, so it does not prove this.

**Separate candidate family:** framework navigation rejection maps to UNKNOWN in
`Agent.command` (:617 onward) without necessarily setting runtime.failure. The
existing C8 test explicitly injects concurrent navigation, missing frame ownership,
connection abort and redirected/forbidden responses. Their matching UNKNOWN
signatures demonstrate non-uniqueness, not the actual cause of live-01.

**Not supported by observed natural frame events:** spontaneous main-frame ID
loss after submit. Injecting a missing ownership entry demonstrates the refusal
path only. Unknown frames must remain rejected.

## Candidate Changes, Not Implemented

The following diffs are proposals for design review, not patches applied this
round. Any semantic change needs a separate ruling. No unconditional swallowing
of CDP errors, request retry, broader allowlist or fallback to the main world is
proposed.

### A. First Preserve The Initiating Operation

Location: `qb_browser_agent.mjs:193` guarded catch and :239 Fetch operation;
`Agent.command` catch for read/submit. Pass only fixed metadata and fixed error
categories to trace, never raw error messages, headers, body or query values.

```diff
- const guarded = (promise, category = 'FETCH_CONTINUE_FAILED') => {
+ const guarded = (promise, category = 'FETCH_CONTINUE_FAILED', operation = null) => {
    pending.add(promise);
-   promise.catch(() => onStop(category)).finally(() => pending.delete(promise));
+   promise.catch(error => {
+     trace.push({ action: 'CDP_OPERATION_FAILED', operation,
+       phase: operation?.phase ?? null, category: classifyFixedProtocolError(error) });
+     onStop(category);
+   }).finally(() => pending.delete(promise));
  };
```

`operation` must be an enumerated method/request-or-response stage and sanitized
path kind captured when scheduling, not whatever navigation happens to be current
when the promise rejects. `classifyFixedProtocolError` must return only a closed
enum (expired request ID, target/session closed, other); it must never serialize
the exception. Add equivalent fixed read-step/submit-step markers in their catches.

Safety impact: observation only; same rejection and fail-closed conditions. It
touches installGuards and requires explicit authorization despite unchanged policy.
Tests: reject each of the three Fetch methods, simultaneous navigation cancellation,
two rejects (first cause retained), no secret/query/error-message leakage, unchanged
allow/deny matrix and all four interception safety groups.

### B. Conditional Cancellation Handling, Only After Proof

Location: same Fetch operation completion and a request lifecycle registry. This
is an intentionally narrow semantic candidate, **not justified by historical
logs alone**. Design must define a trustworthy cancellation-completion signal and
its request ID/target/navigation generation relation before implementation.

```diff
- promise.catch(() => onStop(category))
+ promise.catch(error => {
+   if (operation.method === 'Fetch.failRequest'
+       && fixedCategory(error) === 'REQUEST_ID_INVALID'
+       && lifecycle.provesCanceled(operation.requestId, operation.generation)) {
+     trace.push({ action: 'CANCELED_REJECTION_COMPLETED' });
+     return;
+   }
+   onStop(category);
+ })
```

Never apply this to allowed continue operations or infer cancellation from an
invalid-ID message alone. If a reliable signal cannot be obtained, keep fail-closed
and only take A. Safety impact: changes a stop condition, therefore a design/security
decision; no new permitted traffic. Tests must prove zero server requests for
canceled forbidden refreshes and retain shutdown for invalid IDs without matched
cancellation, cross-target IDs, Worker/popup traffic, unknown frames, forbidden
actions and every 307/308. Rerun all four safety groups and snapshot/response-byte
binding tests.

### C. Make Read Navigation Failures Distinguishable

Location: `Agent.read:708` around page.goto and `Agent.command` catch. Preserve
current return codes and no-retry behavior; add a fixed stage/category trace entry.

```diff
- const response = await this.page.goto(expected, { timeout: 30000 });
+ let response;
+ try {
+   response = await this.page.goto(expected, { timeout: 30000 });
+ } catch (error) {
+   this.runtime.trace.push({ action: 'READ_FAILED', stage: 'navigation',
+     category: classifyFixedNavigationError(error), path: pathShape(path) });
+   throw error;
+ }
```

Safety impact: no allowlist, ownership or error-code change. The fixed classifier
must cover navigation interrupted, blocked-by-client, connection failure, timeout,
target closed and other, without raw text. Tests: the existing C8 injected cases,
plus failure before/after response capture, original-byte identity, fixed trace
schema and sensitive-value scan. Agent touched: rerun all four safety groups.
Do not add retries/phase waits as a purported cure before the cause is identified.

### D. Separate Environment/Closure Diagnosis

Location: driver close around `qb_browser.py:489` and local test fixture logging,
not a timeout relaxation. Keep original thresholds/behavior.

```diff
  process.stdin.close()
+ close_started = time.monotonic()
  try:
      process.wait(timeout=35)
  except (OSError, subprocess.TimeoutExpired):
      self._terminate()
+ finally:
+     self.close_observation = {
+         'elapsed_ms': round((time.monotonic() - close_started) * 1000),
+         'returncode': process.poll(),
+     }
```

Illustrative placement only: preserve the existing close method's actual branch
structure and never let diagnostic writes alter results. Tests: normal EOF,
terminate path, close-time exception, missing agent close response, process group
cleanup after outer CLI timeout; trace writes cannot raise. Python-only observation
does not change Policy/installGuards. This is not a fix for FETCH_CONTINUE_FAILED.

## Outside-Copy Observations And Cleanup

Created `/tmp/skel-read-observe-Z6JSX8` with mktemp, then copied the agent, Python
driver and C8 investigation entry there. The driver copy stayed byte-identical
and was not executed; only the agent copy acquired metadata logging, and the
entry's imports were pointed to that copy and the original local fixture.
The repository files were never overwritten. No copied source is committed.
`observation-copy.json` records source paths, copy sizes and hashes.

The added observation wrapped browser-session CDP send and added passive frame,
page-close and disconnected listeners. It recorded monotonic timestamps, method,
request ID, owned-frame status, request/response stage, sanitized path, fixed
refresh/field/action classification and fixed exception class/category. It did
not record request headers/bodies or raw errors; Policy.allow was still called
exactly once per event with its original result, and rejection handling was unchanged.
An async logging wrapper can perturb timing; this is not a statistically comparable
extension of the unchanged-source sample.

`observe.py.txt` ran 10 independent sets of control, racing-meta-refresh and
configuration-redirect-307 on the same local fake HTTPS fixture. **10/10 completed,
30 scenario records, zero CDP send rejections captured**. Each 307 case still
gave the expected read UNKNOWN / BLOCKED_BY_CLIENT, while its Fetch.failRequest
completed successfully. This distinguishes normal deny-induced navigation error
from FETCH_CONTINUE_FAILED, but does not identify the historical failing method.
Full event ordering is in `instrumented/run-*/<case>.json`; command details and
load bounds are recorded separately from the formal samples.

`cleanup.json` records removal at 2026-11-03 10:08:54 UTC of both owned pytest
temporary roots and the observation-copy directory (three copied files, hashes
recorded before deletion). No process referenced these paths at deletion; all
three paths are absent afterward. No CPU stress process was started, so there is
none to terminate. `/dev/shm/p5q-browser-*` was empty afterward; a process-name/path
check found no P5Q agent/test entry or profile-based Chromium remaining. Unrelated
processes and user worktree changes were left alone.

## Final Conclusion And Checks

**The underlying CDP rejection cause is not uniquely determined.** A natural
FETCH_CONTINUE_FAILED was reproduced in the original C8 fixture, and it occurs
during shared submit-navigation handling, before both the first read and the
scenario's ownership fault injection. The subsequent read/TargetClosed symptom
is downstream of fail-closed. This is a firmer location than the original label
"post-submit read failed", not proof of an expired interception ID.

Expired/canceled refresh interception remains a plausible candidate with limited
evidence. Spontaneous ownership loss is not supported by the captured owned-frame
events. Live-01's UNKNOWN remains separately unresolved. Prefer candidate A/C
diagnostic improvement for a separately authorized round; B is conditional and
must not be implemented from this report alone. No candidate fix was applied.

`integrity-before.json` and `integrity-after.json`: all tracked skill/test/frozen
files byte-equal to `a58494b`; production agent SHA256 remains
`7e315a8d5176308429f2ee67ea31bc1cc17769a1d8da53d3c6d73160306c068c`,
prefix remains `40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16`.
Design checker: **0 problem**. Curated documentation diff check passes;
the full evidence diff check exits 2 for original pytest/fixture HTML whitespace
and verbatim excerpts, preserved rather than normalized (`final-checks.json`).
No full-repository gate was requested or substituted for these targeted samples.
No deviation from the ruling or need to change repository code for observation;
the wrapper setup errors and lack of a unique root cause are explicitly disclosed.
Stop here; neither Batch 3.5 nor Batch 4 is started.
