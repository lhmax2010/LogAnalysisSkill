# Memory for PS-M3 Output Contract

## Status

Completed; ready for review.

## Scope

PS-M3 completes the `tizen-gbs-patch-suggest` output contract:

- add output `README.md`
- expand `context.md` patch-generation guidance
- preserve the fixed `Instructions — MUST follow` footer
- expand `meta.json` outputs to include README/context/meta paths

No resolver logic, analyzer/workflow behavior, Suggester behavior, or pattern content changes.

## Baseline

- Starting branch: `main`
- Starting commit: `543dc8d` (`Merge pull request #38`)
- Branch: `feature/ps-m3-output-contract`

## Completed Changes

- Added output `README.md`.
- Expanded `context.md` with level-specific patch-generation guidance.
- Preserved the fixed `Instructions — MUST follow` footer as the final context block.
- Expanded `meta.json` `outputs` with README/context/meta paths.
- Added tests for README generation, output metadata paths, level-specific guidance,
  ambiguous candidates, and mandatory footer placement.

## Validation

- `ruff check tizen-gbs-patch-suggest tests/unit/test_patch_suggest.py` passed.
- `mypy tizen-gbs-patch-suggest/scripts/gbs_patch_suggest` passed.
- `pytest tests/unit/test_patch_suggest.py -q` passed: `15 passed`.
- Full regression passed: `432 passed`, coverage `95.97%`.
