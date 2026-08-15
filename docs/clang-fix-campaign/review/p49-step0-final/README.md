# P4.9 Step-0 Final Review Package

Review request:

> step-0 implementation is complete against v2.0-FROZEN revisions 1 through
> 7a. The DoD account is in `../p49-step0-closeout.md`. Please confirm:
> (1) implementation matches the frozen contract; and (2) the named DEFERRED
> list is acceptable, then return a step-0 CLOSED confirmation.

## Inputs

- Frozen contract: `../../p49-step0-design-v2.1-FROZEN.md`.
- DoD account: `../p49-step0-closeout.md`.
- Mechanical audit: `../p49-step0-symbol-audit.md`.
- Stage result: `../../dev_memory/stage07_p49_step0/result.md`.

## Implementation Commits

```text
8dca6c1c0f286c60de172b46ddd1e41053955cc9 feat(tizen-ci-shared): establish shared package with state and types (P4.9 step-0 commit 1)
ab58bfdabe5f2845beb6d6d216b22d0847756bc5 feat(tizen-ci-shared): migrate workspace, classify, env with marker authority (P4.9 step-0 commit 2)
6def1edea087627a68e7343e458174d780401013 feat(tizen-ci-shared): sink QuickBuild HTTP surface, complete step-0 contracts (P4.9 step-0 commit 3)
```

## Reproduction Commands

Run from the repository root:

```bash
PYTHONPATH=tizen-ci-shared/scripts:tizen-gbs-build/scripts:tizen-gbs-log-analysis/scripts:tizen-gbs-build-workflow/scripts:tizen-gbs-patch-suggest/scripts:tizen-ci-triage/scripts \
  .venv/bin/pytest

PYTHONPATH=tizen-ci-shared/scripts:tizen-ci-triage/scripts \
  .venv/bin/lint-imports

.venv/bin/mypy
.venv/bin/mypy --strict \
  docs/clang-fix-campaign/tools/symbol_audit.py \
  docs/clang-fix-campaign/tools/table_audit_bridge.py

.venv/bin/ruff check \
  docs/clang-fix-campaign/tools/symbol_audit.py \
  docs/clang-fix-campaign/tools/table_audit_bridge.py

.venv/bin/python -m py_compile \
  docs/clang-fix-campaign/tools/symbol_audit.py \
  docs/clang-fix-campaign/tools/table_audit_bridge.py

python3 docs/clang-fix-campaign/tools/symbol_audit.py
python3 docs/clang-fix-campaign/tools/table_audit_bridge.py
```

Expected summaries:

```text
pytest: 846 passed, 1 skipped (847 collected)
lint-imports: Contracts: 4 kept, 0 broken
symbol audit: 42 SYMBOL OK | 4 MODULE-SCOPE OK (48 SYMBOLS COVERED) | 0 MISMATCH | 0 INCOMPLETE
table bridge: 42 SYMBOL OK | 4 MODULE-SCOPE OK | all missing/mismatch/parse counts zero
```

## Implementation Diff Stat

Command: `git diff 698bd7c..6def1ed --stat`

```text
 .github/workflows/ci.yml                           |   7 +-
 .importlinter                                      |  34 ++
 README.md                                          |   6 +
 docs/clang-fix-campaign/dev_memory/INDEX.md        |   2 +-
 .../stage07_p49_step0/commit1-evidence.md          | 195 +++++++++
 .../dev_memory/stage07_p49_step0/progress.md       | 440 ++++++++++++++++++++-
 .../history/p49-step0-design-v2.1-FROZEN.md        |  66 +++-
 .../p49-step0-design-v2.1-FROZEN.md                |  66 +++-
 .../review/p49-step0-symbol-audit.md               | 219 +++++-----
 docs/clang-fix-campaign/tools/symbol_audit.py      | 152 +++++--
 .../clang-fix-campaign/tools/table_audit_bridge.py | 194 +++++++++
 pyproject.toml                                     |   9 +
 tests/integration/test_build_verify_real_git.py    |   6 +-
 tests/integration/test_gerrit_submit_real_git.py   |   7 +-
 tests/unit/test_build_verify.py                    |   6 +-
 tests/unit/test_campaign_reconcile.py              |   2 +-
 tests/unit/test_campaign_repair_step.py            |  30 +-
 tests/unit/test_campaign_state.py                  |   2 +-
 tests/unit/test_ci_triage.py                       |   2 +-
 tests/unit/test_ci_triage_entrypoints.py           |  21 +-
 tests/unit/test_ci_triage_state.py                 |   2 +-
 tests/unit/test_failure_classify.py                |   2 +-
 tests/unit/test_gerrit_submit.py                   |  18 +-
 tests/unit/test_verify_workspace.py                |   5 +-
 .../scripts/tizen_ci_shared/__init__.py            |   1 +
 .../scripts/tizen_ci_shared/classify.py            | 364 +++++++++++++++++
 tizen-ci-shared/scripts/tizen_ci_shared/env.py     |  19 +
 .../scripts/tizen_ci_shared/quickbuild_http.py     | 233 +++++++++++
 .../scripts/tizen_ci_shared}/state/__init__.py     |   6 +-
 .../scripts/tizen_ci_shared}/state/db.py           |   0
 .../scripts/tizen_ci_shared}/state/keys.py         |   0
 .../scripts/tizen_ci_shared}/state/records.py      |   2 +-
 tizen-ci-shared/scripts/tizen_ci_shared/types.py   |  48 +++
 .../scripts/tizen_ci_shared/workspace/__init__.py  | 230 +++++++++++
 tizen-ci-triage/scripts/ci_triage/batch_cli.py     |   5 +-
 .../scripts/ci_triage/campaign_repair_step.py      |  22 +-
 .../scripts/ci_triage/campaign_state.py            |   3 +-
 tizen-ci-triage/scripts/ci_triage/cli.py           |   8 +-
 tizen-ci-triage/scripts/ci_triage/gerrit.py        |  40 +-
 tizen-ci-triage/scripts/ci_triage/orchestrator.py  |   8 +-
 .../scripts/ci_triage/previous_evidence.py         |   3 +-
 tizen-ci-triage/scripts/ci_triage/quickbuild.py    | 256 ++----------
 .../scripts/ci_triage/quickbuild_log.py            |  10 +-
 tizen-ci-triage/scripts/ci_triage/report.py        |   3 +-
 tizen-ci-triage/scripts/ci_triage/runner.py        |  30 +-
 tizen-ci-triage/scripts/ci_triage/sources.py       |   2 +-
 .../scripts/ci_triage/verify/build_verify.py       |  19 +-
 .../scripts/ci_triage/verify/failure_classify.py   | 379 +-----------------
 .../scripts/ci_triage/verify/gerrit_submit.py      |   4 +-
 .../scripts/ci_triage/verify/workspace.py          | 236 ++---------
 50 files changed, 2329 insertions(+), 1095 deletions(-)
```

## Deferred Review

Confirm that these closing batches are acceptable:

1. GBS report work: triage-report extraction batch.
2. Shim deletion: after all six P4.9 skills are extracted.
3. Root/skill contracts and `containers`: first skill batch.
4. C21 subprocess path anchoring: before the first convergence-judge
   subprocess smoke is added or changed.
