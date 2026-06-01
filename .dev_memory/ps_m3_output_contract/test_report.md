# Test Report for PS-M3 Output Contract

## Summary

PS-M3 validation passed.

## Commands

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/ruff check tizen-gbs-patch-suggest tests/unit/test_patch_suggest.py` | pass | No lint errors. |
| `.venv/bin/mypy tizen-gbs-patch-suggest/scripts/gbs_patch_suggest` | pass | 6 source files checked. |
| `.venv/bin/pytest tests/unit/test_patch_suggest.py -q` | pass | 15 patch-suggest tests passed. |
| `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | pass | 432 passed, coverage 95.97%. |

## Coverage Notes

- Output `README.md` is generated and points to `context.md` as the primary file.
- `meta.json` includes `readme_md`, `context_md`, and `meta_json` output paths.
- Level A context includes unified-diff candidate guidance and semantic-class-as-hint wording.
- Level B unavailable context asks the outer assistant to read `file:line` first.
- Level B ambiguous context lists candidates and asks the outer assistant to choose before patching.
- Level C context says not to generate a patch from diagnostic-only information.
- Not-applicable context points back to workflow suggesters.
- The D13/D14 `Instructions — MUST follow` block remains the final context block.
