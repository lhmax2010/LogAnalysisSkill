# R14 delta review package

Date: 2026-08-06 (Asia/Shanghai)

Baseline: `4737fb2` on branch `clang-fix-campaign`

Review state: **READY FOR TWO-REVIEWER DELTA CLOSURE; NOT MERGE-READY**

This package closes the R14 findings against design v1.5.16 and P4.5. It is
deliberately split into a design delta and an implementation/test delta:

| Artifact | Scope | SHA-256 |
|---|---|---|
| `change_44.diff.gz` | v1.5.17-FROZEN design, change record, checker and frozen snapshot | `e416c15f981ca0f1bdeb48a6e0b659201542acf13f7c60a94b2690b18410d43a` |
| `fix-1.diff.gz` | campaign state, reconcile, wrapper, CLI, workspace and tests | `d52bd33b52f2ef7d6449c0f0ec633c870add9b45dc1f929cef0a206eaea0319b` |
| `finding-disposition.md` | D1-D11 and X1-X19 closure ledger | review text |

The source R14 decision is `../r14-closure-change44-fixpass.md`; the frozen
design snapshot is
`../../history/clang-fix-campaign-design-v1.5.17-FROZEN.md` and is byte-equal
to `../../design.md` at package generation time.

The diffs are gzip-compressed so the repository whitespace gate does not treat
unified-diff context prefixes as trailing whitespace. Review with
`gzip -cd change_44.diff.gz | less` and `gzip -cd fix-1.diff.gz | less`.

## Blocking regression proved closed

`test_two_architectures_share_one_unit_round_and_both_enter_build` calls the
wrapper first for `standard-aarch64`, then for `standard-armv7l`, with the same
unit, round index and edit bytes. Both calls enter the injected build function.
The test additionally proves:

- one DB round stores `<unit>/rounds/round_1/edit_spec.json`;
- the stored ref contains neither architecture segment;
- build inputs remain separate at
  `<unit>/<arch>/out/round_1/edit_spec.json`.

This test fails under the pre-FIX-1 arch-scoped round ref and therefore covers
the cardinality dimension that the prior 820-test/single-arch E2E baseline
missed.

## Reproducible verification

```bash
PYTHONPATH=tizen-ci-triage/scripts:tizen-gbs-log-analysis/scripts:tizen-gbs-patch-suggest/scripts \
  .venv/bin/pytest -q tests/unit/test_campaign_state.py \
  tests/unit/test_campaign_reconcile.py tests/unit/test_campaign_repair_step.py
# 93 passed in 9.02s (the previous 70 plus FIX-1 coverage)

PYTHONPATH=tizen-ci-triage/scripts:tizen-gbs-log-analysis/scripts:tizen-gbs-patch-suggest/scripts \
  .venv/bin/pytest -q
# 843 passed, 1 skipped in 17.75s

.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py --self-test
# 35/35 passed

.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py \
  docs/clang-fix-campaign/design.md
# OK: 0 problem

.venv/bin/ruff check $(git ls-files '*.py') \
  docs/clang-fix-campaign/tools/check_design_doc.py
# All checks passed!

.venv/bin/mypy
# Success: no issues found in 93 source files

git diff --check
cmp -s docs/clang-fix-campaign/design.md \
  docs/clang-fix-campaign/history/clang-fix-campaign-design-v1.5.17-FROZEN.md
# both exit 0
```

Plain `ruff check .` also scans the unrelated, pre-existing untracked
`audit_four_sigs.py` and reports its historical compact formatting. The
tracked-source command above is the accepted repository result; FIX-1 does not
modify that unrelated audit helper.

## Review gate

Reviewers should apply/read both diffs and check the disposition table. Merge
remains blocked until both review parties confirm the delta and the developer
explicitly releases the gate. This package does not claim a new multi-arch
real-machine GBS run; it closes C1 with deterministic wrapper coverage and
retains the prior real E2E result as single-arch evidence only.
