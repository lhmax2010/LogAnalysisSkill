# Memory for PS-M2 Source Context

## Status

Completed; waiting for review.

## Scope

PS-M2 adds explicit source context collection to `tizen-gbs-patch-suggest`:

- reintroduce `--src-root` for explicit source searches
- keep no-src-root behavior as Level B advisory
- search under src-root by basename prefilter + path-segment suffix matching
- upgrade to Level A only on a unique match
- keep zero/multiple matches as Level B advisory
- handle absolute paths only when they exist inside src-root

No analyzer, workflow, Suggester, or pattern behavior changed.

## Baseline

- Starting branch: `main`
- Starting commit: `d619551` (`Merge pull request #37`)
- PS-M1 merge commit: `2c554bc`
- Branch: `feature/ps-m2-source-context`

## Completed Changes

- Added PS-M2 design section to `docs/patch_suggest_design.md`.
- Added suffix search and ambiguity handling to patch-suggest resolver.
- Added `--src-root` back to patch-suggest CLI, with no auto default.
- Rendered candidate paths in Level B ambiguous context and `meta.json`.
- Added tests for unique hit, zero hit, multiple hit, segment alignment, skip dirs,
  no src-root behavior, and absolute path boundaries.

## Validation

- `ruff check tizen-gbs-patch-suggest tests/unit/test_patch_suggest.py` passed.
- `mypy tizen-gbs-patch-suggest/scripts/gbs_patch_suggest` passed.
- `pytest tests/unit/test_patch_suggest.py -q` passed: `14 passed`.
- Full regression passed: `431 passed`, coverage `95.97%`.
