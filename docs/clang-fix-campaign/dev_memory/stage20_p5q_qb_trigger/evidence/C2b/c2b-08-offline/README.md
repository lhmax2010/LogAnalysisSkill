# C2B-08 Offline Form Failure Evidence

Baseline81e90f5; 2026-10-13. Spikes-only code and offline self-tests.
Production agent, Python driver, frozen design, design.md, tests/ and archived
live sessions are unchanged. No QuickBuild request and no live-10 session yet.
The ruling is recorded verbatim in progress24.1.

## Diagnostic Contract

withFormFailureEvidence wraps open_form and the subsequent BUILD_TYPE sequence.
An open_form QB_FORM_CHANGED, or a later field failure, may collect only from
the current same-origin /wicket/page document. Runtime failure, HTTP failure,
redirect or redaction failure retains immediate-stop priority. No navigation,
click, input, new registration, retry or extra field operation is performed by
the collector. Document status uses existing form_network metadata; non200 or
unknown status prevents diagnostics. Original failure is rethrown after capture.

The production formDOM snapshot stays in memory. Diagnostic JSON records input
and textarea lengths, not values; select option text and selection, not option
values; callback booleans/counts/fixed error codes, not source; row buttons and
classes; PROJECT_NAME viewer; redacted action; label differences/duplicates;
ckeditor elements and hidden textareas. A null snapshot records all form actions
and count. The explicit frozen label list contains13 entries including
PROJECT_NAME, matching12 exported FIELDS plus that viewer; no invented14th label.
For a null snapshot, observed labels and differences are null (unknown), not
fabricated observations of every field being absent.

The ordered replay names map to validateForm's actual conditions:
shape, label_set, unique_rows, then project_name or palette_controls/single_control
and callback per row, then action. After first failure, reached=false; subsequent
ok values are diagnostic recomputation, not a claim that production executed
those checks. Production validateForm is called on the same snapshot to assert
verdict agreement. The private ACTION and PALETTES copies are source-pinned by
the self-test. Callback shape evaluation calls production callbackURL directly.

The failure HTML uses production redactDOM and existing pre/post-write checks,
with form_unverified=true. Redacted HTML can contain business values; the
length-only rule describes the diagnostic JSON, not a change to HTML redaction.

## Self-test

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs --form-self-test \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome .venv/bin/python
```

Exit0,26/26,network_requests0,released=false, in form-self-test.log.
All DOM fixtures run on about:blank; fake current URL is used only by the
self-test, not by the live entry. Temporary redacted fixture archives are
checked before/after writing and removed after the test.

Five required fixtures: extra field -> label_set; missing field -> label_set;
rich-text BUILD NOTES with an extra hidden control -> single_control;
changed onchange -> callback; invalid action -> action. All preserve the original
QB_FORM_CHANGED and do not retry. The log prints field differences and first
failure; these are synthetic observations, not an inferred live failure cause.

Additional controls cover values/selection/privacy, null snapshot, duplicates,
project/roles, callback absent/double/foreign, later field errors, immediate-stop
priority, outside-form location, diagnostic redaction/navigation failure,
non200/missing document status and buttons outside td.value. No production
fix or extra allowlist entry follows from this test.

## Remaining Gates

All exit0. pytest2165 passed/1 skipped in130.89s (unchanged count); mypy113;
Ruff clean; import contracts6 kept/0 broken; design checker0 problem.
Existing self-tests22/22 and14/14 are separate from the new26 controls.
Node gate entrypoints3 passed in19.30s: unit120/120, runtime41/41, safety4/4.
All browser safety traffic is local synthetic traffic, not QuickBuild.

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
git archive 5ccb1f803b3df61365da34d486ea00c9fa1a0a9e | tar -x -C /tmp/p5q-c2b-08-final-lint-xkDdMI
# cwd=/tmp/p5q-c2b-08-final-lint-xkDdMI
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/ruff check .
```

Only documentation/logs followed the final lint tree; unrelated dirty files
were not staged. Frozen hash remains0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950.
live-09/run.json hash remains9cb7a31f1afd8e2241dc32b2e848d8b71076532f501c2b39bceae4fd062152e3.
No live-10 directory is created before the next explicit chat start.
