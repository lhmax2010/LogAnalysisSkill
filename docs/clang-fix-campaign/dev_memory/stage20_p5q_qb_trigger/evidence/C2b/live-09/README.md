# C2B-07 live-09

2026-10-13. Baseline b9b4d71. Status STOPPED / QB_FORM_CHANGED.
New chat start preceded this session. Only evidence and documentation change;
no production/script/frozen-design change, no C3. live-08 is untouched.

## Invocation

Repository root, maintained PTY:

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-09 \
  .venv/bin/python full
```

Send ping, receive pong before browser opens, then one human browser login.
Read1193467 overview/variables,1193469 overview/variables/step_status;
register_config from the fresh verified parent; read returned overview1917;
form_evidence. The last command stops with exit1, so no further command/retry.
The browser and temporary profile are confirmed removed. run.json is the
unaltered script output; six response HTML files are the original redacted bytes.

## Result

All five build pages HTTP200/VERIFIED; parent source five checks and configuration
page two checks pass. Run GET ?9-1.ILinkListener-run returns302, then GET
/wicket/page?10 returns200. open_form returns QB_FORM_CHANGED before the evidence
script can record a form snapshot; no BUILD_TYPE operation. Specific failed
form condition, action, callbacks, options and transitions are NOT_COLLECTED.
Do not infer these from archived earlier forms. stop.path_shape retains the
overview path because current is updated only on successful open_form.

form_action_releases=0, released=false, runtime_failure=null,
WORKER_BLOCKED/NEW_PAGE=0. Request-stage GET110/POST1 (human login only),
allowed75/denied36; response-stage HTTP200x60/302x2. No submit or Accept.
Detailed source line anchors and variable observations: ../appendix-c.md,
latest live-09 section, and progress23.5.

run.json SHA256:
`9cb7a31f1afd8e2241dc32b2e848d8b71076532f501c2b39bceae4fd062152e3`.
integrity.log: six hashes match run.json, PageRedactor.check_written passes
on six pages and run.json; release/configuration/stop/cleanup invariants pass.
The offline check does not retain original identities; runtime pre/post checks
used in-memory identities. variables-check.log is a local HTMLParser extraction
of selected rows (with source lines), preserving empty values and testing the
four parent target lines' containment in the child's245-line list.

## Validation

All commands below exit0 after live collection stopped. Regression2165 passed,
1 skipped (125.61s); mypy113 files; import contracts6 kept/0 broken; design0 problem.
Node entrypoints3 passed (19.45s), comprising units120/120, runtime41/41, safety4/4.
Safety Worker/WebSocket took b:browser_fail_closed: attackHTTP0/handshakes0,
shared_worker closeTarget success, worker exception Error, browser/profile removed.
The local safety fail-closed outcome is separate from live runtime_failure=null.
Self-tests22/22 and ID self-tests14/14 pass, network_requests=0 for each.

```bash
.venv/bin/python -m pytest -q
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
.venv/bin/python -m pytest -v -s \
  tests/unit/test_qb_browser_node.py::test_node_agent_unit_matrix \
  tests/unit/test_qb_browser_node.py::test_node_browser_redaction_and_response_interception \
  tests/unit/test_qb_browser_node.py::test_node_c2b_local_https_safety
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs --self-test .venv/bin/python
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs --id-self-test \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome .venv/bin/python
git archive 8f5a45213fe05fbfee55ec06f764aa54e4c05578 | tar -x -C /tmp/p5q-live-09-lint-4KgVAM
# cwd=/tmp/p5q-live-09-lint-4KgVAM
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/ruff check .
```

Ruff output: All checks passed! Only documentation/logs added after this tree.
Unrelated dirty user files were not staged. Source tests and production remain
unchanged; the67 configuration-source Node controls run within full pytest.
The live stop is not resolved by these green gates. No form result inferred,
no retry and no C3.
