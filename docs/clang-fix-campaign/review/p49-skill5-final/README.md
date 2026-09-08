# P4.9 Skill-5 Gerrit-Submit Final Review Package

> 评审只读：发现问题报 finding，不得修改被审文件。
> This is the active repository review protocol at `../README.md:3`.

Review request:

> skill-5 已 CLOSED；本轮仅做 v1.3.1→v1.3.2 的 §3.2 映射表 delta
> 确认。请确认①query/git 两态残留与 skill-3 冻结契约一致
> ②六个 subprocess 调用面已穷举 ③三类异常构造形态可执行
> ④marker 残留符合真实调用顺序。无需重审其余实现与 DoD。

The v1.3.2 delta-review scope is only frozen §3.2's deferred result mapping:
query/git residual-state separation, the added `_exclude_private_files` call
surface, executable exception signatures, and measured marker-write order.
The completed extraction and other DoD rows are unchanged.

## Inputs

- Frozen contract:
  `../../p49-skill5-gerrit-submit-design-v1.3.2-FROZEN.md`.
- DoD account: `../p49-skill5-closeout.md`.
- Stage result:
  `../../dev_memory/stage12_p49_skill5_gerrit_submit/result.md`.
- Detailed measured output:
  `../../dev_memory/stage12_p49_skill5_gerrit_submit/progress.md`.
- Pre-shim evidence:
  `../../dev_memory/stage12_p49_skill5_gerrit_submit/commit-a-evidence/`.

## Seven Lifecycle Commits

```text
f2bc050e9878a77ad8f46014f4ffb1cf14b56356 docs(clang-fix-campaign): freeze P4.9 skill-5 gerrit-submit design v1.3
31a91cb9825e412ee00cd9eef695766d7fc80790 tools(clang-fix-campaign): parameterize design drift ledger and bootstrap skill-5 gates (P4.9 skill-5 A₀)
a97c40bc2ffcfd453f52d3657336282c689c3873 feat(tizen-gerrit-submit): extract gerrit-submit skill (P4.9 skill-5 commit A)
0dfa5f1e0221d2dbdcf10e323259a4e922a04510 test(tizen-gerrit-submit): establish skill test ownership, branch matrix, and status locks (P4.9 skill-5 commit B)
a8620f1ba7caea6ea083b042596830be54bd2fd6 feat(tizen-gerrit-submit): activate gates and audit for skill-5 (P4.9)
d51145fc42415d063cb0cd53c7d3fa75a0566148 docs(clang-fix-campaign): close out P4.9 skill-5 gerrit-submit
Git-anchored containing commit             docs(clang-fix-campaign): amend skill-5 frozen design to v1.3.2 (deferred mapping table precision)
```

The seventh SHA is deliberately not self-recorded. Git anchors this package and
the closeout result outside their own contents (`⑬/⑲`).

## Reproduction Commands

Run from the repository root after refreshing the editable installation:

```bash
.venv/bin/python -m pip install -e .
env -u PYTHONPATH -u MYPYPATH .venv/bin/python -m pytest -q
env -u PYTHONPATH -u MYPYPATH .venv/bin/python -m pytest -q \
  tests/unit/test_tizen_gerrit_submit.py \
  tests/integration/test_gerrit_submit_real_git.py \
  tests/unit/test_ci_triage_entrypoints.py
env -u PYTHONPATH -u MYPYPATH .venv/bin/mypy
git ls-files -z '*.py' | xargs -0 .venv/bin/ruff check
git ls-files -z '*.py' | xargs -0 .venv/bin/python -m py_compile
env -u PYTHONPATH -u MYPYPATH .venv/bin/lint-imports
env -u PYTHONPATH -u MYPYPATH .venv/bin/python \
  docs/clang-fix-campaign/tools/symbol_audit.py
env -u PYTHONPATH -u MYPYPATH .venv/bin/python \
  docs/clang-fix-campaign/tools/table_audit_bridge.py
```

Exact surface, authority, and twin checks:

```bash
! env -u PYTHONPATH -u MYPYPATH .venv/bin/python \
  docs/clang-fix-campaign/tools/symbol_audit.py \
  --surface-fixture mixed-case-alias

env -u PYTHONPATH -u MYPYPATH .venv/bin/python \
  docs/clang-fix-campaign/tools/table_audit_bridge.py \
  > /tmp/p49-skill5-bridge.txt
test "$(rg -c '^tizen_gerrit_submit/gerrit_submit\.py \|' \
  /tmp/p49-skill5-bridge.txt)" -eq 23

test "$(rg '^SubprocessRunner = ' tizen-*/scripts --glob '*.py' | wc -l)" -eq 8
test "$(rg '^def _git_stdout\(' tizen-*/scripts --glob '*.py' | wc -l)" -eq 3
test "$(rg '^def _run_git\(' tizen-*/scripts --glob '*.py' | wc -l)" -eq 3
test "$(rg '^def _result\(' tizen-*/scripts --glob '*.py' | wc -l)" -eq 2
! rg -n '^(def|class) ' \
  tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py
```

Skill-5 drift gates and negative controls:

```bash
LEDGER=docs/clang-fix-campaign/tools/design_drift_ledger.py
SKILL5=docs/clang-fix-campaign/tools/design_drift_ledger.skill5.json
.venv/bin/python "$LEDGER" --data "$SKILL5" check
! .venv/bin/python "$LEDGER" --data "$SKILL5" admission v1.2
! .venv/bin/python "$LEDGER" --data "$SKILL5" \
  negative-fixture out-of-scope-misuse
for id in B-BRANCH-DOD B-BRANCH-FABRICATION B-GATE-CONTROLS \
  B-GATE-MEMBERS B-PRIVATE-COUNT B-RESULT-MAPPING \
  B-TIMEOUT-BRANCH-LOCK B-TIMEOUT-TWO-PATHS; do
  ! .venv/bin/python "$LEDGER" --data "$SKILL5" negative-binding "$id"
done
.venv/bin/python -m pytest -q tests/unit/test_design_drift_ledger.py
```

Inherited skill-4 gate regression:

```bash
LEDGER=docs/clang-fix-campaign/tools/design_drift_ledger.py
SKILL4=docs/clang-fix-campaign/tools/design_drift_ledger.json
.venv/bin/python "$LEDGER" --data "$SKILL4" check
! .venv/bin/python "$LEDGER" --data "$SKILL4" admission-v19
! .venv/bin/python "$LEDGER" --data "$SKILL4" \
  negative-fixture out-of-scope-misuse
```

All 22 skill-4 per-binding commands and their exit-1 results are retained in
the stage12 progress record. Repeating them is mechanical: invoke
`negative-binding <id>` for every `bindings[].id` in the skill-4 data file.

Three-entry and protected-surface checks:

```bash
test "$(rg -F -c 'mypy tizen-gerrit-submit/scripts/tizen_gerrit_submit' \
  .github/workflows/ci.yml)" -eq 1
test "$(rg -F -c '$PWD/tizen-gerrit-submit/scripts' README.md)" -eq 1
test "$(rg -F -c '"tizen-gerrit-submit/scripts"' pyproject.toml)" -eq 2
test "$(rg -F -c '"tizen_gerrit_submit' pyproject.toml)" -eq 2
! rg -n 'include_external_packages' .importlinter

git diff --stat f2bc050^..a8620f1 -- \
  release-v1.4.0 \
  tizen-ci-triage/scripts/ci_triage/gbs_report.py \
  docs/clang-fix-campaign/design.md
```

The three import-linter negative controls and pre-shim parity require temporary
or migration-time state. Their exact mutations, exit-1 output, restoration
checks, five partition comparisons, and one-positive/three-negative normalizer
results are preserved in `progress.md:261-350` and `progress.md:667-714`.

## Expected Summaries

```text
pytest: 912 passed, 1 skipped
targeted skill/integration/CLI set: 46 passed
lint-imports: 6 kept, 0 broken
symbol audit: 173 SYMBOL OK | 4 MODULE-SCOPE OK | 0 MISMATCH | 0 INCOMPLETE
table bridge: 173+4; all differences zero; 23 skill-5 rows present
skill-5 check: RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | 38 exported | 34 retained | 4 ignored
skill-5 admission v1.2: BINDING_DRIFT=7 | RED_AS_EXPECTED
skill-4 check: RESIDUAL_DRIFT=0 | BINDING_DRIFT=0
entry counts: 1/1/2/2
protected historical surfaces diff: empty
```

## Deferred Review

Confirm that the following terminal obligations and frozen §3.2 design are
acceptable:

1. Dangling-symlink normalization in the P4.9 final behavior-unification
   batch.
2. Timeout, cancellation, interruption, residual-state, and result-map
   unification in that batch.
3. Compatibility-shim deletion in a separate P4.9 final cleanup commit.
4. Private test-consumer narrowing in the same final cleanup.

None may be deferred beyond P4.9 final closure. Cancellation requires a named
item, written rationale, and three-party confirmation.
