# C2B-09 Evidence Collector Follow-up

Baseline: production normalization commit `4a4a727` (already pushed).
Only spikes code and evidence/docs change here. Frozen design, production, old
sessions and validateForm/network admission rules are unchanged.

Raw form/ID/configuration/child-heading observations normalize in Node. ID
diagnostics persist only the selected Id cell, not other table values. Form
failure diagnostics use the production normalizer and preserve the original
failure and immediate-stop conditions.

The read-only native probe emits nine boolean flags after login and page reads
(also the form page); it never emits source code. Individually wrapped functions
turn only their own flag false. Both archived configuration-source fixtures pass
with normal/broken trim. This is not the deferred isolated-world implementation.

## Commands And Logs

Run from repository root. All commands below must exit0. Browser tests use
about:blank/imported DOM or loopback-only servers, never live QuickBuild.

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  --intrinsics-self-test \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  .venv/bin/python
# Same arguments with --form-self-test or --id-self-test.
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs --self-test .venv/bin/python
.venv/bin/python -m pytest -v -s \
  tests/unit/test_qb_browser_node.py::test_node_c2b_configuration_source_checks \
  tests/unit/test_qb_browser_node.py::test_node_browser_redaction_and_response_interception \
  tests/unit/test_qb_browser_node.py::test_node_agent_unit_matrix \
  tests/unit/test_qb_browser_node.py::test_node_c2b_local_https_safety
.venv/bin/python -m pytest -q
.venv/bin/mypy
.venv/bin/lint-imports
.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
```

| Log | Result | Exit |
|---|---|---|
| intrinsics-self-test.log | 12/12; nine native flags, nine one-at-a-time wrappers, two configuration fixtures; no requests/release | 0 |
| form-self-test.log | 27/27 including broken trim; no requests/release | 0 |
| id-self-test.log | 15/15 including broken trim/child source; no requests | 0 |
| self-test.log | 22/22, existing channel/address controls | 0 |
| node-gates.log | 4 passed,20.64s; configuration67/67,unit120/120,DOM50/50,safety4/4 | 0 |

Worker safety took branch b:browser_fail_closed; shared_worker closeTarget
success, worker closeTarget Error, QB_BROWSER_UNAVAILABLE, browser/profile
removed, attack HTTP0/WS0. 307/308, per-hop and credential-isolation groups pass.
The synthetic fixture values in the logs are not live credentials or users.

Live-11 requires a new chat start plus ping/pong before browser creation.
No live-11 request, page, native flag, configuration check or form transition
has been collected in this commit. Existing live-10 observations are unchanged.

## Final Gates

All exit0: pytest2165 passed/1 skipped in109.10s (unchanged); mypy113 source
files; Ruff clean; lint-imports6 kept/0 broken; design checker0 problem.
Fourteen added standalone Node self-test controls do not add Python nodeids.
The nine production Node additions are already in `4a4a727` and pass here too.

```bash
git archive d0d06745f648af32d69e4397e816319451a39083 | tar -x -C /tmp/p5q-c2b09-spikes-lint-X8ohj2
# cwd=/tmp/p5q-c2b09-spikes-lint-X8ohj2
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/ruff check .
git diff --cached --check
```

Only evidence/docs appended after the exported-tree Ruff run. `hashes.log`
matches frozen0a3f5e0b...1950, live-10/run.json9b384c16...2cbb9 and
live-10/form-unverified.response.html8f8b5025...e12e. Production/design/frozen
diff relative to4a4a727 is empty. Unrelated user changes and drafts are excluded.
