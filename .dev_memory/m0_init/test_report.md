# Test Report for M0: init

## Environment
- Date: 2026-05-11
- OS: local development environment
- Python: 3.12.3
- Commit: d2963f3
- Merged to main: 864ff5e

## Commands

```bash
.venv/bin/python -m pip install -e .
.venv/bin/pytest tests/
.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
.venv/bin/ruff check .
.venv/bin/mypy gbs_analyzer
```

## Results

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/python -m pip install -e .` | pass | System `python` and `pip` are unavailable; local `.venv` was created with `uv`. |
| `.venv/bin/pytest tests/` | pass | 1 passed. |
| `.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80` | pass | 1 passed, 100% coverage. |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer` | pass | No issues found in 2 source files. |

## Coverage

100% statement coverage for the M0 package smoke baseline.

## Performance

Not applicable for M0. The analyzer runtime starts in M1.

## Known Gaps

- CI cannot be observed remotely until the branch is pushed and PR is opened.
- This local machine lacks a `python` command alias, `pip`, `gh`, and non-interactive
  sudo. Validation used a local `uv`-created virtual environment.
