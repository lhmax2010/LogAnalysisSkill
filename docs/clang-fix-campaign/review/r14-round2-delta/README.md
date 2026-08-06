# R14 round-2 delta review package

Date: 2026-08-06 (Asia/Shanghai)

Baseline: `e622db8` on branch `clang-fix-campaign`

Design commit: `a12d683` (`v1.5.18-FROZEN`, change_45)

FIX-1 supplement commit: `bb4af36`

Review state: **READY FOR TWO-REVIEWER ROUND-2 DELTA CLOSURE; NOT
MERGE-READY**

This package answers `../r14-round2-change45.md`. It corrects the body-vs-ledger
discrepancy found in the first delta, freezes the corrected design, and closes
the three requested FIX-1 supplements.

| Artifact | Scope | SHA-256 |
|---|---|---|
| `change_45.diff.gz` | v1.5.18 design body, change records, checker, methodology, frozen snapshot and round-2 decision | `fd6ff0eb8943cc15efd935d3ea65dde624ba1f67d3a357fc2d903f4770ab5e45` |
| `fix_1_round2.diff.gz` | atomic canonical publish, pre-charge workspace preparation and strengthened X6/X11 tests | `b781b3b53bb825d7374cfa6c0108f11104de43745f6afc1317a39234f07ab257` |
| `body-grep-proof.md` | D1-D11 and X1-X19 authoritative-body/executable grep evidence | review text |
| `finding-disposition.md` | corrected closure ledger; `Closed` now cites body/tests | review text |

The frozen snapshot is
`../../history/clang-fix-campaign-design-v1.5.18-FROZEN.md` and is byte-equal
to `../../design.md` at package generation time. Review compressed diffs with
`gzip -cd <artifact> | less`.

## FIX-1 round-2 supplements

1. Canonical bytes are written to a unique same-directory temporary file,
   flushed/fsynced, and atomically published with `os.link`. EEXIST accepts
   only a hash-identical target. Tests prove no partial target on failure and
   deterministic race handling.
2. The X6 rebaseline test now places an older substantive FAIL before the
   anchor. Traversing past the anchor therefore selects observably wrong
   evidence and makes the pre-fix behavior fail.
3. The X11 test gives the target unit a valid linked PASS while corrupting
   payload JSON in a different unit. A whole-table scan fails; the unit-scoped
   query proceeds.

The minor charging issue is also closed: residual build-copy preparation runs
before invocation consumption, and the rejection tests prove no new charge.
Non-executable status recovery remains explicitly out-of-band except for the
`previous_evidence_missing` rebaseline path.

## Reproducible verification

```bash
PYTHONPATH=tizen-ci-triage/scripts:tizen-gbs-log-analysis/scripts:tizen-gbs-patch-suggest/scripts \
  .venv/bin/pytest -q tests/unit/test_campaign_state.py \
  tests/unit/test_campaign_reconcile.py tests/unit/test_campaign_repair_step.py
# 96 passed in 8.99s

PYTHONPATH=tizen-ci-triage/scripts:tizen-gbs-log-analysis/scripts:tizen-gbs-patch-suggest/scripts \
  .venv/bin/pytest -q
# 846 passed, 1 skipped in 17.61s

.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py --self-test
# 38/38 passed

.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py \
  docs/clang-fix-campaign/design.md
# OK: 0 problem

.venv/bin/ruff check $(git ls-files '*.py') \
  docs/clang-fix-campaign/tools/check_design_doc.py
# All checks passed!

.venv/bin/mypy
# Success: no issues found in 93 source files

cmp -s docs/clang-fix-campaign/design.md \
  docs/clang-fix-campaign/history/clang-fix-campaign-design-v1.5.18-FROZEN.md
git diff --check
# both exit 0
```

Plain `ruff check .` is intentionally not the repository gate because it also
scans the unrelated pre-existing untracked `audit_four_sigs.py`. The command
above checks every tracked Python file plus the design checker explicitly.

## Review gate

Reviewers should verify both compressed diffs, then cross-check every claimed
closure against `body-grep-proof.md`. Merge remains blocked until both review
parties confirm this round-2 delta and the developer explicitly releases the
gate.
