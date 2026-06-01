# Test Report for PS-M2 Source Context

## Summary

PS-M2 validation passed.

## Commands

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/ruff check tizen-gbs-patch-suggest tests/unit/test_patch_suggest.py` | pass | No lint errors. |
| `.venv/bin/mypy tizen-gbs-patch-suggest/scripts/gbs_patch_suggest` | pass | 6 source files checked. |
| `.venv/bin/pytest tests/unit/test_patch_suggest.py -q` | pass | 14 patch-suggest tests passed. |
| `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | pass | 431 passed, coverage 95.97%. |

## Coverage Notes

- Unique suffix match upgrades to Level A.
- Zero match stays Level B.
- Multiple matches stay Level B and list candidates.
- Path segment alignment rejects `mylibavcodec/utils.c` for `libavcodec/utils.c`.
- `.git`, `GBS-ROOT*`, `build`, `.gbs_workflow`, `.gbs_patch_suggest`, and
  `node_modules` are skipped.
- Absolute path inside src-root upgrades to Level A.
- Absolute path outside src-root or missing stays Level B.
