# Test Report for M2: quick_filter

## Environment
- Date: 2026-05-12
- OS: local development environment
- Python: 3.12.3
- Start commit: c6dbec9

## Commands

```bash
.venv/bin/pytest tests/
.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
.venv/bin/ruff check .
.venv/bin/mypy gbs_analyzer
```

## Results

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/pytest tests/` | pass | Initial baseline before M2 implementation, 57 passed. |
| `.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80` | pass | 88 passed, 94.54% coverage. |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer` | pass | No issues found in 8 source files. |

## Coverage

94.54% total coverage. `gbs_analyzer/quick_filter.py` coverage: 85%.

## Performance

Quick-filter 4-fixture batch: 11.6705ms, under the 100ms M2 target.

Densified scanner review follow-up: 10,492,781 bytes, 500 commands, 90 events,
0.066908s under the 2s follow-up target.

## Known Gaps

- No M2-blocking gaps currently open.
