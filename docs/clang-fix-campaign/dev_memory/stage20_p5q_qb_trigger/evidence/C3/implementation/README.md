# C3-02 Protocol and C3-03 Stop Evidence

Baseline: `16b914843318d88be672565bdf2ea9365b25fdbc`.
Authority sha256: `f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`.
No real QuickBuild, browser login, Gerrit connection, Accept or build submission.

## Delivered Scope

- `qb_browser_agent.mjs`: safe snapshot_state on SNAPSHOT_NUM unavailable only.
- `qb_browser.py`: closed-shape validation and QbBrowserError.snapshot_state.
- Python: 17 new cases; Node: 7 new cases. Node cases are not added to pytest totals.
- `agent-diff.log`: only error response construction and fill snapshot capture changed.
  Policy and installGuards are unchanged; authority/design.md are unchanged.
- C3 CLI, its message templates and integrated DoD are **not delivered**.

## Stop P5Q-C3-03

`first-freeze-single-selected.json` is the production fill/command response to
`@freeze` with two equal-text options, different HTML values and one selected.
The unique selected option passes the first check; the later text lookup finds
two matches and returns QB_FORM_VALUE_UNAVAILABLE. selected therefore has exactly
one entry even though no frozen value exists. The approved single-selection
message does not contain the substring targeted by the first-freeze replacement
rule. See progress section 30.3 for candidate wording; none has been adopted.

The former C3-01 probes now pass the C3-02 protocol expectation:
`snapshot-response.json` and `driver-response.json` distinguish two current values.
Earlier `../snapshot-response-probe.json` and `../snapshot-driver-probe.json` are
unchanged historical observations. Script history at 16b9148 explains those files.

## Commands

Run from repository root. Node prefix is:

```sh
env -u DEBUG -u PWDEBUG -u NODE_OPTIONS ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code
```

| Command suffix / command | Output | Exit |
|---|---|---|
| Node `docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C3/snapshot-response-probe.mjs` | snapshot-response.json | 0 |
| Same plus `--duplicate-first-freeze` | first-freeze-single-selected.json | 0 (reproduces stop) |
| `.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C3/implementation/driver-response-probe.py` | driver-response.json | 0 |
| `.venv/bin/python -m pytest -v tests/unit/test_qb_browser.py` | driver-tests.log | 0 |
| Node `--test tests/node/test_qb_browser_agent.mjs` | node-unit.log | 0 |
| Node `--test tests/node/test_qb_agent_source_guards.mjs` | static-guards.log | 0 |
| `.venv/bin/mypy` | mypy.log | 0 |
| `.venv/bin/lint-imports` | lint-imports.log | 0 |
| `.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md` | design-check.log | 0 |

| Command | Output | Exit / result |
|---|---|---|
| `.venv/bin/python -m pytest -v` | pytest.log | 0; 2299 passed, 1 skipped, 0 failed; 258.23s |
| `.venv/bin/ruff check .` in staged-tree export | ruff.log | 0; all checks passed |
| Node `tests/node/p5q_c2b_safety.mjs /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome` | safety.log | 0; 4/4, loopback-only |

Driver tests: 160/160. Node unit tests: 159/159. Static guards/mutations: 183/183.
Mypy: 113 files. Import contracts: 6 kept / 0 broken. Design checker: 0 problem.
The export used `git archive 49d7784f43ea4522f4c4b7f3ff8c59e95520f3a4` into
`/tmp/p5q-c3-lint-muAoYR`; unrelated untracked drafts and pre-existing deletions
were not staged. Subsequent changes are documentation/logs only.

`guard-identity.log` compares exact text from `export class Policy` up to
`export class FrameOwnership`, and `export async function installGuards` up to
`export function pathShape`, against `git show 16b9148:<agent path>`.
Both equalities pass; their SHA256 values are recorded. No new allow rules.

The safety suite's QuickBuild hostname is mapped to a loopback HTTPS fixture;
synthetic login output is not evidence of an external login or external request.
The safety suite was additionally rerun despite unchanged interception code.

## Unaccepted Work

`implementation-wip.patch` is an unfinished, unaccepted implementation draft,
removed from the active production/test tree at the stop. It is not a delivery,
not a passed test suite, and must not be blindly applied. In particular its
first-freeze message branch is not consistent with the new edge case. Resume
from the authority and ruling, not from inferred behavior in this patch.
