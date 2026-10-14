# C3 Completion Evidence

Baseline: `7f3c60e68a4dc8868a7e00ad2d2d9bc3328ff982`.
Authority: immutable P5Q v1.5, SHA256
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`.
Ruling: progress section 31, P5Q-C3-04. No real QuickBuild/Gerrit requests,
no human login, no build submission, no Accept/Ready to Accept. Test remote
queries use local bare repositories; the fixture rejects every git push command.
This does not claim C4, C5/C6 live evidence, or P5Q closeout.

## Implementation Map

Paths below are repository-relative; line numbers refer to this delivery.

| Requirement | Implementation | Verification |
|---|---|---|
| C3-04 ordinary SELECT duplicate text | `qb_browser_agent.mjs:433` validateForm; `:461` duplicateOptionText; `:524` formFacts | Node unit four command/path cases plus palette exclusion; real-browser fields four cases; `duplicate-first-freeze.json` |
| C3-04 two message templates | `qb_trigger.py:272` snapshot_message; exception handling in qb_trigger | `test_snapshot_templates_and_other_unit_unchanged`, 10 combinations; first concrete config with no stored freeze also tested |
| CLI interface / stdout / exit | `cli.py:414` _main_qb_trigger; `qb_trigger.py:58/:87/:102/:517` | invalid args/files, three units, exact action/error outcomes |
| Selection, lock, profile, coherent gates | `qb_trigger.py:129/:188` | six precondition failures, P5 selection and unit binding, lock, profile conflicts before agent |
| First-match idempotency | `qb_trigger.py:260` | twelve cells below; submit and new request counts; old request/events unchanged |
| Login/open/fill/readback | `qb_trigger.py:313/:517` | single login, middle-unit failure isolation, each readback field, snapshot errors and trace |
| Isolated ref check | `qb_trigger.py:355` | transport isolation, hostile main config, wrong repository SHA, post-fill ref change; eight override mutations |
| Atomic intent and race recheck | `qb_trigger.py:140/:379` | status/request/PUSH races, same/different concurrent profile, rollback injection |
| Release, landing, binding | `qb_trigger.py:433/:451/:470` | false release retry, unknown/exit/invalid JSON, two echo checks, global build uniqueness, binding races |
| Crash windows | intent/submit/bind boundaries | `test_crash_windows`, four cases plus retry assertions; three transaction rollback injections |
| Diagnostics | `qb_trigger.py:291` | structural error directory, pre/post checks, failed write preserves original error, post-check removes files |
| C2c review carryovers | `qb_config.py` rule7; `qb_redact.py` repeated header reset, delivered at 16b9148 | existing config/redaction suites rerun unchanged |

Module paths: agent under `tizen-ci-triage/scripts/ci_triage/`; CLI/trigger same directory.
CLI tests: `tests/unit/test_qb_trigger.py`. Binding page fixture derives rows from
`C2b/live-12/02.response.html`, replacing values, not inventing the variable table.
Browser field tests use the existing synthetic loopback form server for events.

## Idempotency Table

Every cell below is a separate pytest node at `tests/unit/test_qb_trigger.py:363`.
Prefix: `test_idempotency_every_cell`.

| Frozen section 4.2 row | Without retrigger | With retrigger |
|---|---|---|
| No request | `[False-none]`: submit | `[True-none]`: submit |
| SUBMITTED only, QB_SUBMIT_FAILED | `[False-failed-submit]`: new request | `[True-failed-submit]`: new request |
| SUBMITTED only, other state | `[False-uncertain]`: already_requested | `[True-uncertain]`: new request |
| BUILD_BOUND, no RESULT | `[False-bound]`: already_requested | `[True-bound]`: REJECTED_QB_REQUEST_PENDING |
| RESULT PASS | `[False-pass]`: already_passed | `[True-pass]`: REJECTED_QB_REQUEST_PENDING |
| RESULT terminal failure | `[False-fail]`: already_requested | `[True-fail]`: new request |

All cells assert submit count and request delta, not just action. Both old requests
and their events are compared field-by-field. Crash windows also rerun the CLI
after restoring the injected crash, asserting normal retry or already_requested.

## Group Coverage

`audit_completion.py` consumes `focused.xml` to produce `audit.json` with every
nodeid and its group. C3's new 139 pytest cases are partitioned (no double count):

| Frozen 9.1 group | New CLI cases |
|---|---|
| Trigger preconditions/idempotency | 38 |
| Fill/submit, including diagnostics and crash windows | 70 |
| Parameter freeze/config | 27 |
| Credential/redaction failures | 4 |

Diagnostics/privacy overlap is listed under fill/submit, not counted twice.
The focused run also reruns C1 profile primitives, exact schema/CHECK, concurrent
freeze, all config keys, all 160 driver cases and shared redaction vectors:
488 passed, 0 failed, 0 skipped. C4 RESULT tests are out of scope.

Key extra cases: twelve fields at `test_each_field_readback_mismatch`, extra target
line and palette selection at `test_readback_extra_payloads`, recorder mismatch at
`test_palette_recorder_mismatch_from_agent`; first freeze zero/one/many/null state
and existing freeze state are all covered by the template matrix. Existing
`tests/unit/test_qb_state.py` owns primitive hash/date/CHECK/no-op/concurrency tests.

## Commands

All commands run at the repo root unless stated otherwise. Node prefix:

```sh
env -u DEBUG -u PWDEBUG -u NODE_OPTIONS -u QB_COOKIE -u QB_PASSWORD ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code
```

`PW=/home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs`;
`CHROMIUM=/home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome`.

| Command | Log | Exit / result |
|---|---|---|
| `.venv/bin/python -m pytest -v` | pytest.log | 0; 2438 passed / 0 failed / 1 skipped, 279.06s |
| `.venv/bin/python -m pytest tests/unit/test_qb_trigger.py -v --junitxml=<this-dir>/trigger-tests.xml` | trigger-tests.log | 0; 139/0/0 |
| `.venv/bin/python -m pytest tests/unit/test_qb_trigger.py tests/unit/test_qb_config.py tests/unit/test_qb_state.py tests/unit/test_qb_browser.py tests/unit/test_qb_redact.py -v --junitxml=<this-dir>/focused.xml` | focused.log | 0; 488/0/0 |
| Node `--test tests/node/test_qb_browser_agent.mjs` | node-unit.log | 0; 163/0/0 |
| Node `--test tests/node/test_qb_agent_source_guards.mjs` | static-guards.log | 0; 183/0/0, including every forbidden-name negative |
| Node `tests/node/test_qb_browser_fields.mjs PW CHROMIUM` | node-fields.log | 0; 16/0/0 |
| Node `tests/node/p5q_c2b_safety.mjs PW CHROMIUM` | safety.log | 0; four groups passed, HTTP/WS attacks blocked |
| `.venv/bin/mypy` | mypy.log | 0; 114 source files |
| `.venv/bin/ruff check .` in complete staged-tree export | ruff.log | 0; tree/export path recorded there |
| `.venv/bin/lint-imports` | lint-imports.log | 0; 6 kept / 0 broken |
| `.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md` | design-check.log | 0; 0 problem |
| Node `.../evidence/C3/snapshot-response-probe.mjs --duplicate-first-freeze` | duplicate-first-freeze.json | 0; now FORM_CHANGED, duplicate_option_text, no snapshot_state |
| Same without flag | snapshot-response.json | 0; two distinct safe selected values retained |
| `.venv/bin/python <this-dir>/transport_mutations.py` | transport-mutations.json and eight logs | runner 0; each mutated pytest exit 1 |
| `.venv/bin/python <this-dir>/audit_completion.py` | audit.json | 0; immutable authority, Policy/installGuards, driver and design checks |

Raw failure logs preserve pytest's trailing whitespace as emitted; code and
documentation pass diff whitespace checks independently. Unrelated user edits,
deletions and untracked design drafts were not staged or modified.

No source files are edited during transport mutation: each fresh process removes
one OVERRIDES entry in memory and runs the actual isolation test. The test's literal
expected override list is independent of the mutated source list. Eight actual
failures, not an asserted count substituted for execution.

Policy/installGuards are byte-identical to 7f3c60e. The four safety groups are an
additional regression run, not required by a changed allow rule. The QuickBuild
hostname in those logs resolves only to the local synthetic HTTPS server.
Worker group used branch b (browser fail-closed), with zero attack HTTP requests,
zero WebSocket handshakes and temporary-directory cleanup confirmed. Full pytest
also reruns the Node wrappers; internal Node counts are not added to pytest totals.
The baseline 2299 passed/1 skipped becomes 2438 passed/1 skipped; the unchanged
skip is `test_case_insensitive_bypass_is_platform_specific`. C3 is complete;
there is no new design contradiction, and C4 has not started.
`collection-comparison.json` compares nodeids in the baseline
`../implementation/pytest.log` and final `pytest.log`: 2300 to 2439, zero removed,
139 added, all in `tests/unit/test_qb_trigger.py`.

## Development Failures

`fixture-setup-failures.log` records invalid test fixture setup (UNIQUE constraints).
The initial old-round fixture also reused the edit hash and was rejected by the
append-only round API. A subsequent round-change fixture omitted the composite
foreign-key edit hash. Fixed by creating a distinct round/hash and respecting its
composite key; the different-unit fixture frees the destination test binding first.
No production constraint was changed or disabled. A long Chinese assertion line
was split for Ruff. These are test-construction errors, not design deviations.

`pytest-before-final-template-case.log` is preliminary: 2437 passed/1 skipped.
It predates collection of the last first-freeze/concrete-config test. Final
acceptance uses `pytest.log`, not this earlier run.
