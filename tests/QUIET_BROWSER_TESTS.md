# Quiet Browser Tests

Run offline tests from the repository root without opening windows on the desktop:

```bash
.venv/bin/python tests/run_quiet.py tests/ -q
.venv/bin/python tests/run_quiet.py tests/unit/test_qb_browser_node.py -q
```

Arguments are passed directly to pytest. Chromium remains headed, using the same
production agent and interception rules, but runs on Xvfb's private X display.
One display serves the entire test invocation. `xvfb-run` chooses an unused display,
uses an Xauthority file, disables TCP listening, and cleans up on exit. The parent
terminal's display environment is unchanged.

The launcher needs `Xvfb`, `xvfb-run`, and `xauth`. It also recognizes an unpacked
Ubuntu Xvfb package in `~/.local/share/p5q-test-display/`; no root installation is
required. Missing prerequisites fail before starting browsers. There is no fallback
to the user's desktop. Without local Node/Playwright/Chromium, the existing explicit
pytest skip behavior remains unchanged.

Browser-bearing pytest tests reject a direct desktop invocation. Do not set
`P5Q_TEST_DISPLAY=virtual` manually; the launcher sets it for its child process.
Do not run Node browser tests directly on the desktop. For a targeted run, select
their pytest wrapper with `-k` or a full nodeid.

This launcher is for offline tests only. Never use it for a real QuickBuild login:
human login must still use the visible production window. No cookies are persisted,
no login is automated, and real submission still requires the explicit confirmation
gate. Batch focused tests during editing, then run the required complete gates once
on the final tree; rerun affected gates after any further relevant change.
