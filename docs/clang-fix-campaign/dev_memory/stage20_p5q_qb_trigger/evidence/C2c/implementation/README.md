# C2c Implementation Evidence

Baseline: `68b71aaaac62c3e1f4e7ba477033cf98ffe7132b`.
Authority: `p5q-qb-trigger-design-v1.5-FROZEN.md`, unchanged SHA256
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`.
The approved C2C-03 ruling is recorded verbatim in progress section 28.1.
The previous `../implementation-wip.patch` was not applied as a delivered patch.

## Scope And Boundaries

- Isolated CDP execution, response-byte reads, inert diagnostics, positional
  identity redaction, no refresh registrations, one-callback field windows,
  startup framework verification, and design.md v1.5.23 Appendix A sync.
- Browser tests use synthetic local HTTPS servers and certificate pinning.
  Real QuickBuild/Gerrit requests, manual login, Accept/Ready to Accept: **0**.
- No C3 work. C5/C6 obligations in progress 27.2 remain open: the real original
  response/activity comparison, successful sample and BUILD_NOTES sample.
- The startup synthetic page uses a disposable fully guarded browser, which is
  closed before launching the working browser. No exception is added to the
  unexpected-page/Worker/HTTP/WebSocket guards.

## Final Commands

All commands run at the repository root using the existing `.venv`.
Node launch helpers remove `DEBUG`, `PWDEBUG`, `NODE_OPTIONS`, `QB_COOKIE` and
`QB_PASSWORD`. Local runtime: Playwright 1.58.2, Chromium 145.0.7632.6.
No new Python or npm dependency is installed.

| Command | Result | Exit | Log |
|---|---|---|---|
| `.venv/bin/python -m pytest -v` | 2277 passed / 0 failed / 1 skipped; 257.03s; baseline 2165/1 (+112 passed) | 0 | pytest-final.log |
| `.venv/bin/python -m pytest -v tests/unit/test_qb_redact.py tests/unit/test_qb_browser.py` | 233 passed / 0 failed / 0 skipped | 0 | python-final.log |
| `.venv/bin/mypy` | 113 source files, no issues | 0 | mypy.log |
| `.venv/bin/lint-imports` | 6 kept / 0 broken | 0 | lint-imports.log |
| `.venv/bin/ruff check .` in complete staged-tree export | All checks passed | 0 | ruff-final.log |
| `.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md` | 0 problem | 0 | design-check.log |
| Node six-entry command below | 6 passed / 0 failed / 0 skipped | 0 | node-final.log |
| DOM entry rerun after final shared-vector addition | 63 Node tests passed / 0 failed / 0 skipped | 0 | dom-final.log |
| Trusted-read entry final isolated rerun | 37 Node tests passed / 0 failed / 0 skipped; 129 loopback requests | 0 | trusted-final.log |
| Static guard mutation command below | 183 passed / 0 failed / 0 skipped | 0 | static-mutations-final.log |

```bash
.venv/bin/python -m pytest -v -s \
  tests/unit/test_qb_browser_node.py::test_node_agent_unit_matrix \
  tests/unit/test_qb_browser_node.py::test_node_c2c_source_guard_mutations \
  tests/unit/test_qb_browser_node.py::test_node_browser_redaction_and_response_interception \
  tests/unit/test_qb_browser_node.py::test_node_c2b_local_https_safety \
  tests/unit/test_qb_browser_node.py::test_node_c2c_trusted_reads_and_fields

env -u DEBUG -u PWDEBUG -u NODE_OPTIONS -u QB_COOKIE -u QB_PASSWORD \
  ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code --test \
  tests/node/test_qb_agent_source_guards.mjs
```

Node runner totals are reported separately, not added to pytest's wrapper count:
policy/phase unit 152; final shared-vector DOM 63; source guards 183;
trusted/inert read 37; fields/startup 12; safety groups 4. All pass without skips.
The raw-capture suite also has its earlier direct log in `trusted-raw-capture.log`.
`trusted-final.log` reruns the exact staged source including stale/mismatched
navigation slots, same-URL subresources and non-byte capture controls.

Ruff uses a `git archive` export of the staged tree, so the user's unrelated
untracked drafts, `.gitignore` edit and four deleted documents are not changed
or included in this task. The tree hash and cleanup location are in the log.
After that code-tree check only evidence/documentation is staged.

## Mandatory Controls

`test_qb_agent_source_guards.mjs` injects one forbidden line into an in-memory
copy of the actual production source for every named API/option. It runs the
same AST guard as the positive source check, asserts a nonempty verdict and a
throw, and logs each case. Nothing dangerous is executed. The sole
`addInitScript` exception is checked structurally as the immutable window.open
guard; `setContent` is confined to startupSelfTest. Additional controls cover
aliases, computed members, protocol fields outside the adapter, refresh
registrations, active cloneNode, and test-only Python launch arguments.

C2C-03 layers in `tests/node/test_qb_browser_agent.mjs`:

| Layer | Test |
|---|---|
| Permanent denial only | `C2C-03 permanent deny distinguishes stop query values from listener components` |
| Final closed allowlist | `C2C-03 stop outside listener still fails the callback and read query grammar` |
| Removed refresh exception, all six phases | `refresh denied in <phase>, including C2C-03 value=stop regression` |

Safety was rerun from scratch after production changes. `node-final.log` records
server-observed requests for Worker/WebSocket, 307/308, credential isolation and
per-hop filtering: **4/4**, loopback only. Worker branch is
`b:browser_fail_closed`: shared_worker closes successfully; worker closeTarget
raises Error, browser/profile close; attack HTTP=0, WebSocket handshakes=0.

## Intermediate Failures And Resolution

These logs are retained, but are not the final acceptance result:

- `node-gates.log`: 1 failed / 4 passed; four leaf charset tests failed because
  Playwright response.body() had transcoded the navigation bytes. No permission
  was relaxed. `raw-bytes-probe.log` compares the two design-approved APIs:
  Fetch.getResponseBody, before continueResponse, preserves all four server
  bodies exactly (Latin-1, invalid UTF-8, valid UTF-8, literal U+FFFD). Production
  now uses only that byte-preserving route, bound to this navigation/frame/ID.
  Missing, non-base64, malformed or stale capture fails closed.
- `pytest-full.log`: 2236 passed / 1 failed / 1 skipped; the old read unit mock
  lacked the new request-bound capture. The mock now supplies capture metadata
  and asserts the transcoded Playwright body is never read. Final rerun is
  `pytest-final.log`.
- Internal implementation checking found JSON-escaped diagnostic HTML must not
  be reparsed as HTML. Python now checks decoded HTML separately and recursively
  checks decoded fact strings/keys; hidden-input and nested-leak tests cover it.
- The shared `USER` identity vector catches counting a generated registered mask
  as an outside identity. Both implementations exclude registered positions;
  outside count is exactly 1. Shared vectors now number 20.
- `python-focused.log`, `static-mutations.log`, `ruff-staged.log` are earlier
  successful intermediate checks, superseded by their final counterparts.

`p5q_c2c_raw_bytes_probe.mjs` under `tests/node/` reproduces the byte comparison
with the same two runtime path arguments as the browser tests. Its log includes
the invocation, runtime/source hashes, complete synthetic bytes and cleanup.
None of these synthetic observations establishes the real-site premise reserved
for C5; that obligation remains explicitly open.

Raw failing-run logs retain the test runners' trailing spaces on indented error
lines. Code, tests and Markdown pass diff whitespace checks; raw logs are not
rewritten to hide those whitespace warnings.
