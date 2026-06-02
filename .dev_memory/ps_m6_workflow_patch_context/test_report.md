# PS-M6 Test Report

## Focused Tests

```bash
.venv/bin/pytest tests/unit/test_workflow.py -q
```

Result: 18 passed.

```bash
.venv/bin/pytest tests/e2e/test_build_workflow_e2e.py -q
```

Result: 7 passed.

## Static Checks

```bash
.venv/bin/ruff check tizen-gbs-build-workflow tests/unit/test_workflow.py
```

Result: passed.

```bash
.venv/bin/mypy tizen-gbs-build-workflow/scripts/gbs_workflow
```

Result: passed.

## Full Regression

```bash
.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95
```

Result: 446 passed, coverage 95.97%.

## Scope Checks

- `grep -rn "import gbs_patch_suggest\|from gbs_patch_suggest" ...`: no matches.
- `git diff main -- tizen-gbs-build/ tizen-gbs-log-analysis/ tizen-gbs-patch-suggest/ | wc -l`: 0.
