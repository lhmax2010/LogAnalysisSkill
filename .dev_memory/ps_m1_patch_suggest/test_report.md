# Test Report for PS-M1 Patch Suggest

## Summary

PS-M1 validation passed.

## Commands

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/ruff check .` | pass | No lint errors. |
| `.venv/bin/mypy tizen-gbs-log-analysis/scripts/gbs_analyzer tizen-gbs-build-workflow/scripts/gbs_workflow tizen-gbs-patch-suggest/scripts/gbs_patch_suggest` | pass | 46 source files checked. |
| `.venv/bin/python tizen-gbs-patch-suggest/scripts/run_patch_suggest.py --help` | pass | Launcher exposes `--evidence`, `--src-root`, and `--output-dir`. |
| `.venv/bin/pytest tests/unit/test_patch_suggest.py -q` | pass | 8 PS-M1 tests passed. |
| `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | pass | 425 passed, coverage 95.97%. |

## PS-M1 Coverage Notes

- Level A via analyzer `evidence.source_snippet`.
- Level A via `--src-root` file read when evidence has only file and line.
- Level B file:line present but source unavailable.
- Level C diagnostic-only when file and line are absent.
- Non-compiler packets produce a not-applicable context.
- CLI rejects unreadable evidence and invalid `--src-root`.
- All generated contexts include the D13/D14 mandatory instruction tail.
