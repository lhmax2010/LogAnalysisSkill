# live-10: Form Failure Diagnostics

2026-10-13; baseline284c5c0. FatTank sent a new chat start. PTY stayed open;
ping/pong preceded browser startup. One manual login, no retry. Frozen hash:
`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`.

## Invocation And Command Sequence

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-10 \
  .venv/bin/python full
```

Protocol commands, one after each response:

```jsonl
{"command":"ping"}
{"command":"read","path":"/build/1193467/overview"}
{"command":"read","path":"/build/1193467/variables"}
{"command":"read","path":"/build/1193469/overview"}
{"command":"read","path":"/build/1193469/variables"}
{"command":"read","path":"/build/1193469/step_status"}
{"command":"register_config","source_path":"/build/1193467/overview"}
{"command":"read","path":"/overview/1917"}
{"command":"form_evidence"}
```

Login is sent automatically only after pong. Configuration1917 is returned by
this session's verified parent source, not guessed. The process stops/cleans up
after form_evidence, so no later close/field command was sent.

## Outcome

Exit1, STOPPED/QB_FORM_CHANGED at open_form. Five build pages HTTP200/VERIFIED,
configuration source five checks and configuration-page two checks all PASS.
Form page HTTP200 at /wicket/page?10 is archived as form_unverified before stop.
No BUILD_TYPE change, no Ok/submit, form_action_releases0/released=false.
Browser and temporary profile removed; runtime_failure=null; no Worker/new page.

First failure: project_name,row0. controls0/viewer1, but viewer value has trailing
whitespace, unlike configured Tizen-Base-Toolchain. See integrity.log for escaped
exact strings; run.json:2780/:3212 and form-unverified.response.html:727/:732.
Production formDOM already uses trim(); why the page-context result retains
whitespace was not probed in this run. No new normalization rule is assumed.

Labels extra/missing/duplicates all empty. Later replayed checks are green but
reached=false; they are diagnostics, not successful production validation.
BUILD NOTES is one visible textarea; cke elements0. Initial BUILD_TYPE Full,
BUILD_REFERENCE Ref. Snapshot, SNAPSHOT_NUM tizen-base-toolchain_20260924.094908.
No transition version/options/refresh evidence was obtained.

Request-stage observations GET114/POST1 (manual login), allowed75/denied40;
response-stage200x61/302x2. Denials: ckeditor10, bootstrap fonts9+9, Wicket XHR12.
Trace/wrapper40/40, frame ownership0. Not server-receipt counts. No resources
were newly allowed. stop.path_shape is the last pre-open_form current value;
actual current form address is in form_diagnostics and form_network.

run.json SHA256: `9b384c1671f2825e17b0e3fd40443c0ed9a9b40b3b18402cf297a0d63672cbb9`.
Form HTML SHA256: `8f8b50258cf0db849b557428cc54479fe764888fa45b64096d9b4c2edefee12e`.
All seven original production-redacted HTML files are preserved byte-for-byte.
integrity.log repeats hashes/PageRedactor checks, verifies stop/cleanup/release
and source checks, and records exact failure values without storing identities.
Runtime pre/post checks used in-memory identities. Prior live directories unchanged.

Detailed field table, source lines and remaining NOT_COLLECTED items: ../appendix-c.md,
C2B-08 live-10 section. One observed form stop awaits designer ruling; no C3.

## Post-collection Gates

Commands run from repo root; raw outputs alongside this file. All exit0; results
also in progress24.7. No further QuickBuild request.

| Command group | Result | Log |
|---|---|---|
| Full pytest | 2165 passed,1 skipped,158.66s (unchanged count) | pytest.log |
| mypy | 113 files,clean | mypy.log |
| Ruff | All checks passed! | ruff.log |
| lint-imports | 6 kept,0 broken | lint-imports.log |
| Design checker | 0 problem | design-check.log |
| Node three pytest entrypoints | 3 passed,27.10s;120/120,41/41,safety4/4 | node-gates.log |
| Form diagnostic self-test | 26/26,no network/release | form-self-test.log |
| Existing self-tests | 22/22 and14/14,no network | self-test.log,id-self-test.log |

Safety Worker branch b:browser_fail_closed; shared_worker closeTarget success,
worker exception categoryError; attackHTTP0/WS0; browser/profile cleaned.
All four safety groups passed on local synthetic traffic only.

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
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs --form-self-test \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome .venv/bin/python
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs --self-test .venv/bin/python
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs --id-self-test \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome .venv/bin/python
git archive 26280747be55b9b18b32d91efb09ceb043a378bf | tar -x -C /tmp/p5q-live10-lint-NI7isH
# cwd=/tmp/p5q-live10-lint-NI7isH
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/ruff check .
```

Ruff checks the complete staged tree exported to a temporary directory, excluding
unrelated dirty user files/drafts; exact tree/path recorded above. Only docs/logs
followed this lint run. hashes.log confirms frozen/live-09 hashes unchanged. This
commit changes documentation/evidence only, no production/frozen/spike/test code.
