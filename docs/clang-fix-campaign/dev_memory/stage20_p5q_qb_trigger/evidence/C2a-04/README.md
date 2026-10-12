# C2a-04 Correction Evidence

Baseline: ca43b5d. Date: 2026-10-12. Scope: stage20 progress section 15.
Frozen design, design.md and checkers unchanged. No C2b, no QuickBuild/Gerrit
requests. Browser fixtures use archived HTML and local synthetic data only.

The build identity fixture loads web-cookie-02/01,03,04.response.txt unchanged
using page.setContent; browser policy denies every request and DNS is disabled.
Navigation and Summary values are checked independently of the HTML title.

The first Python test run returned 94 passed / 2 failed: two newly added driver
fixtures issued read/submit while the fake agent was still in the new phase.
It correctly returned AGENT_PHASE. The fixtures now execute login and, for
submit, open_form/fill first. No production phase restriction was changed.

## Commands And Results

Every log is captured with bash pipefail and tee, preserving the command's exit.

| Command | Exit | Result / raw output |
|---|---:|---|
| `.venv/bin/pytest -q -s tests/unit/test_qb_browser.py tests/unit/test_qb_browser_node.py` | 0 | [offline.log](offline.log): 102 passed |
| `.venv/bin/python -m pytest -q` | 0 | [pytest.log](pytest.log): 2152 passed, 1 skipped |
| `.venv/bin/mypy` | 0 | [mypy.log](mypy.log): 113 source files |
| `.venv/bin/lint-imports` | 0 | [lint-imports.log](lint-imports.log): 6 kept, 0 broken |
| `.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md` | 0 | [design-check.log](design-check.log): 0 problem |
| `.venv/bin/ruff check .` in original worktree | 1 | [ruff-working-tree.log](ruff-working-tree.log): 53 pre-existing errors in unrelated untracked scripts |
| Absolute `.venv/bin/ruff check .` in complete staged-tree export | 0 | [ruff-clean-tree.log](ruff-clean-tree.log): All checks passed |

Ruff export tree: `a5ed032b6a643da378c2434738473092349c0d59`, produced by
`git write-tree` after staging only task files. Export command:

```bash
git archive a5ed032b6a643da378c2434738473092349c0d59 | tar -x -C /tmp/p5q-c2a04-lint-O3x8v4
```

Ruff ran after extraction finished, with the repository's unchanged configuration.
Only documentation and evidence were updated after this code snapshot. The four
untracked scripts are `audit_four_sigs.py`, `docs/clang-fix-campaign/hashobj2.py`,
`docs/clang-fix-campaign/ident_check3.py`, `docs/clang-fix-campaign/norm_diff5.py`.
They and the unrelated .gitignore/document deletions are untouched and unstaged.

## Test Accounting

- Full pytest: baseline 2087/1 -> 2152/1, 65 added, no additional skip.
- Driver: 31 -> 96, including the full mapping table, read-only mapping scope,
  exact Boolean false versus false-like values, missing or malformed replies,
  sensitive-key rejection, successful landing preservation and process failures.
- Node unit: 53 -> 57, four new cases: refresh POST denial, delayed request,
  real ten-second release deadline, released navigation timeout.
- Real browser: 2 -> 22, comprising the original two, nineteen archive-based
  identity subtests and their parent entry. All three original pages pass unchanged;
  both alternate Id/ID spellings, reordered Id column and negative mutations run.
- Existing h modes: 3/3; profile cleanup normal/exception/SIGTERM: 3/3.
- Six pytest Node wrappers are unchanged in count. Node-internal counts are not
  added again to pytest totals. No local Node/browser wrapper skipped.

The Node wrapper uses the existing local runtime (no download):
`ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code`, Playwright
`/home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs`, Chromium
`/home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome`.
Tests access no external service; synthetic browser servers bind loopback only.

## Behavior Boundaries

`released=False` is available on QbBrowserError only for an explicitly false
Boolean in a valid submit error response. Ambiguous or invalid submit responses
are discarded and become an unknown landing, including sensitive-key payloads.
A well-formed successful build landing is still returned per the existing
protocol; no retry permission is inferred from a malformed or failed exchange.

Submission no longer uses the old form's load state as navigation evidence:
after the actual Fetch release, waitForURL waits for a changed URL and load,
at most 60 seconds. A same-URL error page or navigation timeout is unknown.
The non-release deadline is 10 seconds, followed by action invalidation.

Frozen SHA256 (unchanged):
`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`.
No new design gap; original C2b/integration handoffs remain pending.
