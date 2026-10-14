# C2c Freeze Registration And Stop Evidence

Date: 2026-10-14. Baseline: `b6bec94f4336740d5fd6fb9b58607cd1af355128`.
Status: `STOPPED / P5Q-C2C-02 OPEN`. No real QuickBuild/Gerrit requests or login.
No production, test, or design.md changes are delivered in this commit.

## Authority

`docs/clang-fix-campaign/p5q-qb-trigger-design-v1.5-FROZEN.md`

SHA256: `f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`.
The file is registered byte-for-byte; v1.2 remains historical evidence.

## Stop Reproduction

Run from the repository root:

```bash
env -u DEBUG -u PWDEBUG -u NODE_OPTIONS -u QB_COOKIE -u QB_PASSWORD \
  ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2c/spec-gap-check.mjs
```

`spec-gap.log`: five assertion checks pass; deliberate exit **2** reports the
specification blocker. It imports only the immutable baseline Git blob, checks
the frozen document hash, and uses synthetic metadata. Network requests: **0**.

- v1.5 line 756 requires a legal callback containing `stop` in its query to be allowed.
- Lines 306/282 allow only the closed callback grammar and optional decimal random suffix.
- `&value=stop` fails registration; `stop` in the listener component is permanently denied.
- The inherited positive at `tests/node/test_qb_browser_agent.mjs:209` uses a registered
  refresh GET; line 280 now requires that entire class to be denied.

Proposed, NOT approved: test non-listener query values at the permanent-denial
predicate layer without treating that result as final allowlist authorization;
make the inherited refresh request a negative. Full facts and the request for
designer adjudication are in progress.md section 27.3.

## Feasibility Only

```bash
env -u DEBUG -u PWDEBUG -u NODE_OPTIONS -u QB_COOKIE -u QB_PASSWORD \
  ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2c/preflight.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome
```

`preflight-baseline.log`: exit **0**; isolated context available; change counts
`[1,1,1]` for selectOption/check/fill+blur; network requests **0**.
This was rerun after restoring production/tests to the baseline. It is not C2c
acceptance, nor proof of all navigation/response/field-window requirements.

`feasibility.log` is the earlier exploratory run while edits were in progress.
`implementation-wip.patch` preserves incomplete, unvalidated work, including an
unfinished test which exposed the contradiction. It is **not a delivered fix**
and must not be applied as validated code. Only our edits were reversed; unrelated
user work was left intact.

C2c static-guard mutation suite: **NOT_RUN**. Implementation steps 1-6 and
design.md v1.5.23 synchronization: **NOT_DELIVERED**, pending the above ruling.

## Baseline Regression For This Documentation Commit

All rerun on 2026-10-14 after restoring production/tests. These do not attest
to the unimplemented v1.5 requirements. All commands run from the repo root.

| Command | Result | Exit | Raw log |
|---|---|---|---|
| `.venv/bin/python -m pytest -q` | 2165 passed, 0 failed, 1 skipped; 123.74s | 0 | pytest-baseline.log |
| `.venv/bin/mypy` | 113 source files, no issues | 0 | mypy-baseline.log |
| `.venv/bin/lint-imports` | 6 kept, 0 broken | 0 | lint-imports-baseline.log |
| `.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md` | 0 problem; existing v1.5.22, not v1.5.23 | 0 | design-check-baseline.log |
| Node entrypoints below | 3 passed, 0 failed, 0 skipped; 20.14s | 0 | node-baseline.log |
| `.venv/bin/ruff check .` on complete staged-tree export | All checks passed | 0 | ruff-baseline.log |

```bash
.venv/bin/python -m pytest -v -s \
  tests/unit/test_qb_browser_node.py::test_node_agent_unit_matrix \
  tests/unit/test_qb_browser_node.py::test_node_browser_redaction_and_response_interception \
  tests/unit/test_qb_browser_node.py::test_node_c2b_local_https_safety
```

Node: unit **142/142**, DOM **51/51**, safety **4/4**, no skips. Safety groups
were rerun from scratch against loopback-only fake servers. Worker branch:
`b:browser_fail_closed`; shared_worker closeTarget succeeds, worker raises
`Error`; attack HTTP and WebSocket handshakes both zero; browser/profile cleaned.

Ruff ran on staged tree `4d86fe86dedb138db7cc7a7dc8a6da35a929ebdb` exported
with `git archive`, excluding unrelated user changes/untracked drafts.
`/tmp/p5q-c2c-lint-tp36xd` was removed after the run. Subsequent edits only add
this documentation and logs. The WIP patch SHA256 is
`1e3f87f72837ddf9c67016d6172bedfec2d2f82fe15986e5a9a0c73a22b5ef8a`.
