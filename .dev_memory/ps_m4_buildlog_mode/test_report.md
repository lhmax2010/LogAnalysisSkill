# Test Report for PS-M4 Buildlog Mode

## Summary

PS-M4 validation passed.

## Commands

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/ruff check tizen-gbs-patch-suggest tests/unit/test_patch_suggest.py` | pass | No lint errors. |
| `.venv/bin/mypy tizen-gbs-patch-suggest/scripts/gbs_patch_suggest` | pass | 7 source files checked. |
| `.venv/bin/pytest tests/unit/test_patch_suggest.py -q` | pass | 23 patch-suggest tests passed. |
| `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | pass | 440 passed, coverage 95.97%. |

## Coverage Notes

- Existing `--evidence` mode still works.
- `--evidence` and `--buildlog` are mutually exclusive.
- Buildlog mode runs analyzer and consumes generated evidence.
- Analyzer subprocess failure and missing evidence are reported.
- PYTHONPATH is prepended and preserves existing values without mutating `os.environ`.
- Analyzer discovery works through env var and sibling skill layout.
- `--src-root` is only passed when provided.
