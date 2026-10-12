# C2a Offline Completion

Date: 2026-10-12. Baseline: `d1f09cc`. Authority is the unchanged v1.2-FROZEN
plus approved C2A-01/02/03 rulings in progress sections 12-14.
No QuickBuild/Gerrit requests or human login. C2b is NOT_STARTED.

## h Acceptance

Final evidence: [h-final.log](h-final.log). Exit 0, 3/3 PASS.
The fixture calls the production `installGuards` implementation. Only its host
policy is loopback-specific. Diagnostic options are passed by the test entry,
never by the Python driver or production agent main.

| Mode | HTTP during h window (all paths) | WS handshake | Reference records | Console records | Outcome |
|---|---:|---:|---:|---:|---|
| Diagnostic | 0 | 0 | 20 | 221 | PASS; browser stays open for observation |
| Normal | 0 | 0 | 0 | 1 | PASS; browser closed, QB_BROWSER_UNAVAILABLE |
| Diagnostic without browser Fetch | 80 | 0 | 20 | 221 | PASS control; WS layer remains enabled |

Diagnostic and control each attempt fetch, fetch via eval, XHR, form, location,
ws and wss twenty times over a ten-second window. Console records are captured
live with `Runtime.consoleAPICalled`: `reference/obtained=true`,
`attempt/result=INVOKED`, then fetch `completion/REJECTED` in the protected case.
The attempt label describes invocation, not server receipt. The server's
request list is the verdict source. Reference acquisition is not a verdict.
Normal mode closes at the first new page, before the reference can be reported.
All temporary browser profiles and synthetic TLS certificates were removed.

The fixture navigation precedes the measurement window. Its icon is inline;
**no HTTP path is excluded from the final protected zero-request assertion**.
Earlier `h-production-guards.log` records a late main-page favicon separately;
that run is retained, but `h-final.log` is the final strict-window result.
`h-interception-probe.log` used timer-only rounds throttled by popup rules;
`h-interception-repeated.log` fixed the test scheduler. Neither supersedes the
final production-guard evidence. No protection was disabled to fix the fixture.

Command (bash pipefail; stdout captured verbatim):

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  tests/node/p5q_h_interception_probe.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome
```

Runtime: embedded Node 24.21.0, Playwright 1.58.2, Chromium 145.0.7632.6.
No standalone node was installed or downloaded. Production still uses the
configured Node executable; the Electron setting is a local test runner only.

Final h fixture SHA256:
`2525a39643f6796dc53dd8244d282e5f536dc30513d4fc7602451703e3f36581`.
Final h log SHA256:
`7b200010f9b83ea1a70ad597fe3ec421a3e5f3c01684071f439074cd1ed63b11`.
a-g remain the accepted results in `request-boundary-cached-frames.log` and
`request-boundary-report.md`; not rerun this round as instructed. Their runnable
probe remains `tests/node/p5q_request_boundary_probe.mjs`; h now has its own
test entry and is excluded from that script's default a-g suite.

## Implemented Boundaries

| Surface | Mechanism installed before navigation |
|---|---|
| HTTP | Browser.newBrowserCDPSession; Fetch.enable Request and Response patterns; Fetch.requestPaused; Fetch.failRequest / continueRequest / continueResponse. All targets, each hop; 307/308 fail at response stage. |
| WebSocket | BrowserContext.routeWebSocket("**/*") closes without connectToServer, before page creation. |
| New targets | --block-new-web-contents; BrowserContext.addInitScript with non-writable/non-configurable window.open returning null; Target.setDiscoverTargets makes any new page close the browser. Worker filters use Target.setAutoAttach and Target.autoAttachRelated with waitForDebuggerOnStart, then Target.closeTarget without resume. |

Frame membership is seeded by Page.getFrameTree on the working page. Only its
Page.frameAttached/frameDetached/frameNavigated events update the set. Detached
descendants are removed; foreign, missing, and unknown frameId are rejected.
Protocol metadata is copied only in adaptProtocol; credentials never enter the
policy object. Rejected-request traces store phase/path shape, not query values.
Diagnostics use only synthetic pages and may transcribe synthetic console data;
production never transcribes browser console events.

## Test Mapping

| Group | Test entry | Result |
|---|---|---|
| Permanent denies, phase allows, exact addresses, callbacks, response status, metadata, frame ownership, form/readback, command state, static rules | tests/node/test_qb_browser_agent.mjs | 53 PASS |
| Real DOM redaction and real browser Fetch 307/308 versus 302 | tests/node/test_qb_browser_runtime.mjs | 2 PASS |
| Real profile cleanup normal / exception / SIGTERM | tests/unit/test_qb_browser_node.py with qb_browser_lifecycle.mjs | 3 PASS |
| h diagnostic / normal / no-Fetch control | tests/node/p5q_h_interception_probe.mjs | 3 PASS |
| Python protocol/error mapping/credential-key rejection/fake process | tests/unit/test_qb_browser.py | 31 PASS |
| Config existing plus positive-integer timeout | tests/unit/test_qb_config.py | 59 PASS (9 new) |

Python Node wrappers are six pytest cases (including h); their internal Node tests are not
added again to the pytest total. When Node or the local Playwright/Chromium/display
is absent, wrappers explicitly skip with a reason. No such local wrapper skipped.

The real redirect test initially raced Chromium's asynchronous error-page commit
after rejecting a redirect. Its fixture now lets that error document settle before
starting the next case. No policy or expected outcome was relaxed.

## Commands And Gates

| Command | Exit | Raw evidence |
|---|---:|---|
| .venv/bin/pytest -q -s tests/unit/test_qb_browser_node.py tests/unit/test_qb_browser.py tests/unit/test_qb_config.py | 0 | offline-final.log; 96 passed |
| .venv/bin/python -m pytest -q | 0 | pytest-final.log; 2087 passed, 1 skipped |
| .venv/bin/mypy | 0 | mypy.log; 113 source files |
| .venv/bin/lint-imports | 0 | lint-imports.log; 6 kept, 0 broken |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | design-check.log; 0 problem |
| .venv/bin/ruff check . in clean staged-tree export | 0 | ruff-clean-tree.log |

Full regression retains baseline 2041 passed/1 skipped and adds 46 pytest cases.
The original working tree's `ruff check .` includes unrelated untracked historical
scripts (`audit_four_sigs.py`, `hashobj2.py`, `ident_check3.py`, `norm_diff5.py`)
and reports 53 errors. Those scripts are not edited, staged, or excluded via a
configuration change. Ruff acceptance runs on the entire clean staged-tree export,
including all delivered new files. The initial snapshot tree was
`fddaa77bad39dbf456e11e1c43cab7e647791c27`, exported with git archive to
`/tmp/p5q-c2a-lint-MY6NeQ`; final source revisions were checked again using tree
`4cb6f4377533776b617698c1a56860dc352c0da5` in the same clean export. The original
working-tree failure is preserved in `ruff-working-tree.log` (exit 1), not described
as a green run. Final full regression is `pytest-final.log` and the Node matrix
is `offline-final.log`. The exception-cleanup case raises a genuinely uncaught
synthetic exception through the production failure handler (child exit 1);
its pytest assertion passes only if the directory is gone and raw exception text
is absent. Read tests also reject a redirect chain ending back at the original URL.

## Delivery Limits

- No new Python dependency. Agent .mjs is included as ci_triage package data so
  installed packages retain the driver-adjacent executable.
- Login's protocol payload carries only the configured timeout and enabled
  project identifiers/path/name. Launch arguments remain exactly the frozen
  Node/agent/Playwright/Chromium list; no testing or diagnostic flags.
- Full-page fake QuickBuild workflow and remaining section 9.3 cases remain in
  the planned integration stage. Before C2b, the four section 9.3 security subsets
  must be fully checked with its specified local HTTPS fixture, not inferred from
  unit tests. This commit does not authorize C2b or any real submission.
- No new design stop item. The h stop is closed by C2A-03 and the final 3/3 run.
