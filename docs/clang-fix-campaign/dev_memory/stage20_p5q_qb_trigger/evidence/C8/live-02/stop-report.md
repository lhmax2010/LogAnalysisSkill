# C8-02 Read Recovery: Preflight Stopped

No production qb-result-fetch or other QuickBuild operation was started.
No new login window was opened. No submission or retry was made.

Command: `.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C8/run_read_recovery.py preflight`.
Exit: 1. Facts: [preflight.json](preflight.json).

The preflight found 11 Playwright Chromium processes. Root PID 1226014 was
started at local 2026-10-21 19:43:12; its parent PID was 1225999.
Read-only /proc/exe inspection identified:

- Browser: `/home/linhao/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome`.
- Parent: `/home/linhao/qb_fetch/.deps/playwright/driver/node`.

This differs from P5Q's configured Chromium 1208. Ownership was not inferred as
permission to terminate it or waive the no-leftovers check. These processes were
not killed. No files belonging to that other tool were read, except /proc process
metadata; no command-line secrets, environment or browser session were inspected.

All other preflight checks matched: DB SHA256
`c346b6b8d065ad14a5dbab2bb9e9d66f370234e8ac73133426789002075b2c63`,
QB requests/profiles/events 1/1/1, SUBMITTED only, status QB_REQUESTED;
zero P5Q profile or .transport directories, three D-state samples 0/0/0,
both frozen designs and the C6 files unchanged. No preflight success marker exists.

The single authorized read was not attempted. Binding, human build confirmation,
terminal result and C8-02 acceptance a-d remain NOT_RUN. The existing request may
already have a build; do not resubmit. This stop does not explain live-01's UNKNOWN.

The separately authorized offline investigation continues with a synthetic HTTPS
server and a private virtual display. Resuming live work requires resolution of
this preflight stop; it is not retried automatically.
