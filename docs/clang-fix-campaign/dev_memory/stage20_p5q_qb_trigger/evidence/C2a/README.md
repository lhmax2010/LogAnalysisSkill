# C2a: Execution-Before-Close Capability Probe

Current C2a implementation and C2A-03 acceptance are in
[completion.md](completion.md). The following is an unmodified historical
stopping-point narrative, not the current task status.

Historical record only. Superseded by the approved P5Q-C2A-01 ruling;
not rerun or used for current acceptance. See the
[new creation probe report](creation-probe-report.md).

Date: 2026-10-10. Baseline: `d1f09cc`. This is a stopping-point
reproducer, **not** the production browser agent or completed C2a acceptance.

## Authority

- Frozen design SHA256:
  `0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`.
- Frozen design lines 180, 216, 576 require new windows to be blocked before
  execution, not just closed after their creation notification.
- No frozen text, production source, or existing tests were modified.

## Environment And Commands

No standalone `node` was found on PATH. The local VS Code Electron executable
was used in its Node-only mode: Node `24.21.0`. This is a probe runner, not an
authorized substitution for the production agent launch contract.
Installed Playwright core: `1.58.2`; Chromium: `145.0.7632.6`.

Run the following command with the final argument `baseline`, `hold`, or `close`:

```bash
env -u LD_LIBRARY_PATH -u LD_PRELOAD -u GTK_PATH -u GIO_MODULE_DIR \
  -u DEBUG -u PWDEBUG -u QB_COOKIE -u QB_PASSWORD ELECTRON_RUN_AS_NODE=1 \
  /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2a/target_pause_probe.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome close
```

Raw stdout was captured with `tee` under `bash -o pipefail`; the table below
records the command exit codes. No protocol debug logging was enabled.

## Reproducer

The primary page is `about:blank`. Before executing the fixture, two separate
browser CDP sessions install:

- `Target.setAutoAttach(autoAttach=true, waitForDebuggerOnStart=true,
  flatten=true)` for browser-level page targets;
- `Target.autoAttachRelated(targetId=<primary>, waitForDebuggerOnStart=true)`
  for related targets, including the dedicated Worker.

Separate sessions matter: `autoAttachRelated` cancels `setAutoAttach` on the
same session. The final probe avoids that configuration error. Target filters
exclude `browser` and `tab`, permitting `page` and worker targets. The Chromium
protocol rejects filters simultaneously permitting both `tab` and `page`.

The opener executes this in-memory fixture:

```javascript
const popup = window.open('about:blank');
popup.document.write('<script>opener.probePopupRan = true;<\/script>');
```

A separate Worker created from a local Blob reports a second execution marker.
The probe never sends `Runtime.runIfWaitingForDebugger` for a new target.
In `close` mode, the `Target.attachedToTarget` handler immediately sends
`Target.closeTarget`, without resuming or awaiting another operation first.

## Actual Results

| Mode | Log | Worker ran | Popup ran | Popup waitingForDebugger | closeTarget result | Exit |
|---|---|---|---|---|---|---|
| baseline, no extra CDP pause | [target-pause-baseline.log](target-pause-baseline.log) | true | true | not intercepted | not called | 0 |
| hold, never resume | [target-pause-hold.log](target-pause-hold.log) | false | true | true | not called | 1 |
| close immediately on attachment | [target-pause-close.log](target-pause-close.log) | false | true | true | success=true | 1 |

All three runs report `PROFILE_REMOVED=true`. Page/context request events in
each run contain only `{"blob:":1}`: no HTTP, HTTPS, WS, or WSS requests.
No QuickBuild or Gerrit page, credential file, or user profile was used.
Host resolution was disabled and browser background networking disabled.

## Conclusion And Limits

`waitingForDebugger=true` did **not** prevent the same-origin opener from
synchronously injecting and executing a script in the popup's initial document.
Successful immediate target closure did not undo or prevent that execution.
This is a counterexample to the proposed execution-before-close guarantee on
the tested local stack, not a claim that every possible Chromium architecture
is incapable of enforcing it.

`BrowserContext.routeWebSocket` was installed as a deny-only route in the probe;
its safety acceptance is **not** established by this experiment. HTTP
`Fetch.enable` / `Fetch.requestPaused` policy and response interception were
not implemented or tested. SharedWorker, ServiceWorker, full cleanup signal
matrix, driver, fake agent, and the remaining section 9.2 tests were not run.

Production work stops at `P5Q-C2A-01`. A design ruling is needed for an additional
window-creation prevention mechanism and its anti-bypass acceptance. No
JavaScript override, weaker close-after-notification policy, or production
fallback was silently introduced.
