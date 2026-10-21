# C8-02 Offline Investigation

Outcome: **live-01 root cause not uniquely determined; multiple matching local signatures reproduced**.
No production source, frozen design, interception rule or dedicated state DB was changed.
No real QuickBuild operation occurred: [live-02 preflight stopped](../live-02/stop-report.md).

## Method And Evidence

Production Agent/createRuntime/installGuards/FrameOwnership are imported unchanged.
The test fixture `tests/node/p5q_fake_quickbuild.mjs` serves synthetic HTML over
loopback HTTPS with test-only DNS and certificate overrides. No archived HTML is
served verbatim. The script `tests/node/p5q_c8_investigation.mjs` observes production
runtime.trace and the protocol adapter's metadata, and wraps Agent.read only to
classify exceptions before rethrowing the same object. It never invokes Policy.allow
a second time. Server evidence records method/path/status, not request headers or bodies.
Error records contain class and a fixed category only, never raw message or stack.
Each scenario performs one synthetic form submission, not a real build.

All browser tests use `tests/run_quiet.py` and a private virtual display. The unrelated
Chromium process tree that blocked live-02 was not terminated or reused.

The live signature under investigation is: read fails quickly with
QB_BROWSER_UNAVAILABLE / UNKNOWN, while the agent has not been observed to exit.
Local `signature=true` additionally verifies the browser is still connected and
Agent.command returned to the still-running Node process within 3 seconds.
It does not claim to reproduce the original 579 ms duration exactly.

## Candidate Results

Full metadata, frame events, raw failure shape and DENIED phase/path observations
are in the named JSON files under [navigation-02](navigation-02/summary.json) and
[navigation-03](navigation-03/summary.json). All cases kept the same main frame ID;
runtime.failure remained null, including the generic UNKNOWN cases.

| Candidate / control | Read result | Time | Live signature? | Interpretation |
|---|---|---:|---|---|
| Ordinary unknown landing, then read | ok / HTTP 200 | 38 ms | No | Baseline works |
| a: script navigation to build during idle | ok / HTTP 200 | 36 ms | No | DENIED idle /build/<id> is recorded; subsequent read succeeds |
| a: script navigation to build while overview response delayed | AgentError / QB_TRUSTED_CONTEXT_UNAVAILABLE | 1828 ms | No | Distinct typed error, not UNKNOWN |
| a: meta refresh while overview response delayed | AgentError / QB_TRUSTED_CONTEXT_UNAVAILABLE | 1826 ms | No | Distinct typed error |
| a: script navigation to Wicket while overview response delayed | AgentError / QB_TRUSTED_CONTEXT_UNAVAILABLE | 1824 ms | No | Distinct typed error |
| Delayed overview response alone | ok / HTTP 200 | 1857 ms | No | Delay alone does not explain the three typed failures |
| a: test-forced concurrent CDP Page.navigate to build | Error / NAVIGATION_INTERRUPTED; QB_BROWSER_UNAVAILABLE / UNKNOWN | 252 ms | Yes | Competing navigation can reproduce it; this is an injected second navigation, not proof the live page did it |
| b: injected missing main-frame ownership membership | Error / BLOCKED_BY_CLIENT; QB_BROWSER_UNAVAILABLE / UNKNOWN | 6 ms | Yes | Intended overview request denied with frame_owned=false; fault injection, not a naturally observed lost event |
| c: server closes configuration response connection | Error / NETWORK_RESPONSE_FAILED; QB_BROWSER_UNAVAILABLE / UNKNOWN | 9 ms | Yes | No ownership loss or policy denial required |
| c: configuration response 302 to signin | Error / BLOCKED_BY_CLIENT; QB_BROWSER_UNAVAILABLE / UNKNOWN | 10 ms | Yes | Policy denies signin while in read; redirect check is never reached |
| c: configuration response 307 | Error / BLOCKED_BY_CLIENT; QB_BROWSER_UNAVAILABLE / UNKNOWN | 8 ms | Yes | Response-stage denial, as designed |

Thus b's natural premise, a changed or lost main-frame identity after submit, was
**not observed**. The injected map loss only proves the error-mapping consequence.
Likewise the injected concurrent navigation is not evidence that live-01 executed a
script redirect. There is no basis to pick one of these causes from live-01's trace.

Source basis (production unchanged):
- Agent.submit at qb_browser_agent.mjs:853 returns unknown after an intermediate
  loaded URL; it does not establish that all subsequent page navigation is finished.
- Agent.command at :617 maps any non-AgentError to QB_BROWSER_UNAVAILABLE.
  failureReply/recordFailure at :21/:35 can emit UNKNOWN without setting runtime.failure
  or exiting. The literal AGENT_STOPPED line alone does not establish process exit.
- Agent.read at :708 awaits page.goto before explicit redirect/trusted-body checks.
  A framework navigation rejection can bypass those typed checks.
- FrameOwnership and installGuards at :160/:182 use page-session frame events and
  browser-session Fetch events. A missing frame is denied before Policy.allow.
- qb_discovery.py:120 assigns configuration_status only after the whole read reply
  succeeds. A null status does not prove that the server sent no HTTP response.

## Residual Directory Attribution

[history.json](history.json) reconstructs C7 full-01's completed JUnit prefix against
the archived collection: 680 named completed cases match exactly. The next case is
`test_real_cli_browser_submit_bind_pending_pass[build]`; its archived parameter name
is hashed. full-01 ended at 07:24:16.005053 UTC with exit 2/KeyboardInterrupt;
the old orphan's mtime was 07:24:16.761415 UTC, 0.756362 seconds later.
The C7 coverage notes explicitly document intentional SIGINT interruption.
This strongly associates the orphan with that interrupted integration test, but
there is no historical creator PID or signal-recipient trace. mtime is not claimed
to be a creation timestamp.

Current local reproductions use the unchanged `qb_browser_lifecycle.mjs` test entry:

| Termination | Exit | Time after signal/readiness | Outer profile left? |
|---|---:|---:|---|
| normal close | 0 | 0.044915 s | No |
| SIGTERM after readiness | 0 | 0.024555 s | No |
| SIGINT after readiness | 130 | 0.019112 s | Yes |

Evidence: navigation-02/cleanup-normal.json, cleanup-SIGTERM.json and
[cleanup-SIGINT.json](navigation-02/cleanup-SIGINT.json). The SIGINT remnant contains
the same directory/socket/symlink types as the old orphan. No symlink value was read.
After recording it, lsof showed no references; only this test's announced profile
was removed. No pre-existing directory or unrelated process was touched.

Mechanism supported by source and reproduction: launchRuntime at :896 registers
its own asynchronous SIGINT/SIGTERM cleanup. Local Playwright 1.58.2's
`lib/server/utils/processLauncher.js:60` independently handles SIGINT and calls
process.exit(130) after its own cleanup. SIGTERM does not do that exit. The early
SIGINT exit can preempt removal of the agent-created enclosing TMPDIR. This explains
the reproduced remnant. Exact signal routing of the historical interrupted Python
CLI still cannot be proven; parent KeyboardInterrupt may also kill an immediate
child without orderly descendant cleanup. Do not equate plausible attribution
with a historical PID-level proof.

## Candidate Changes, Not Implemented

| Candidate | Agent / interception impact | Required tests and risks |
|---|---|---|
| Add fixed read-step/error-class facts, navigation generation, and owned/not-owned vs policy-denied attribution | Agent change; guard trace points may change, conditions need not change | Redaction/protocol-key checks; every current allow/deny control; four safety groups. No raw framework messages, query values or headers |
| If concurrent navigation is confirmed, serialize the transition to a new read against a stable document generation within existing hard budgets | Agent sequencing; may require design clarification of extra waits, not automatic permission for requests or retries | Intermediate Wicket landing, client navigation during read, no duplicate submission, deadlines, exact original-response binding |
| If ownership loss is confirmed, reconcile frame events without ever accepting unknown frames | Agent plus installGuards; security-sensitive, requires explicit approval | Target/frame replacement, detached frames, popups/workers, request/response-stage ownership; never broaden host/path rules |
| Give the agent sole SIGINT cleanup ownership, e.g. disable Playwright's SIGINT handler while preserving explicit runtime.close | Agent launch/lifecycle change; no HTTP allow/deny changes intended | Normal/SIGINT/SIGTERM, signals during probe launch and working launch, parent interruption, concurrent signals, no surviving descendants or owned profiles |
| Record candidate variable-name set and table-shape facts without candidate values/pages | Python discovery instrumentation; no agent/Policy change needed in principle | Exactly all read candidates, no other users' values persisted, shapes fail closed, redaction, human review workflow |

The last candidate addresses a separate e3b evidence gap: current production trace
does not output variable-name sets, and other users' pages are intentionally not
archived. No instrumentation was injected into a live production invocation.
None of the listed changes was made; all need design disposition first.

## Runs And Limits

`navigation-01` preserves the initial hypothesis assertion failure (1 failed,
57.90 seconds): the probe incorrectly required the script-race case to reproduce
UNKNOWN but observed QB_TRUSTED_CONTEXT_UNAVAILABLE. This is not a production
regression or a successful reproduction. The assertion was removed so that the
investigation records hypotheses that do not reproduce, instead of discarding them.

`navigation-02`: 4 passed / 0 failed / 0 skipped, 154.41 seconds: one wrapper for
nine navigation cases plus normal/SIGTERM/SIGINT cleanup observations.
`navigation-03`: 2 passed / 0 failed / 0 skipped, 59.61 seconds: delay-only and forced
concurrent-navigation observations plus the existing real-CLI fake-server [build]
regression. These are targeted offline tests, not a full repository regression.
Production files and frozen inputs remain byte-identical; final checks are in audit.json.

Reproduction commands (all output paths are dedicated, no live config or DB):

```bash
env P5Q_C8_INVESTIGATION="$PWD/docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C8/investigation/navigation-02" .venv/bin/python tests/run_quiet.py tests/unit/test_p5q_c8_investigation.py -q
env P5Q_C8_CASES=delay-only-control,injected-competing-navigation P5Q_C8_INVESTIGATION="$PWD/docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C8/investigation/navigation-03" .venv/bin/python tests/run_quiet.py tests/unit/test_p5q_c8_investigation.py::test_post_submit_read_signatures 'tests/unit/test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass[build]' -q
```

For a later reproduction choose a fresh evidence directory; do not overwrite these
archived runs. The default navigation test now includes both additional controls.
