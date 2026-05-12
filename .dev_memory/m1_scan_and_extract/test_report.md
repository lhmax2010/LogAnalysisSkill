# Test Report for M1: scan_and_extract

## Environment
- Date: 2026-05-11
- OS: local development environment
- Python: 3.12.3
- Start commit: 4778b75

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
| `.venv/bin/pytest tests/` | pass | Initial baseline before M1 implementation, 1 passed. |
| `.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80` | pass | 57 passed, 98.93% coverage. |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer` | pass | No issues found in 7 source files. |

## Coverage

98.93% total coverage. M1 scanner module coverage: 99%.

## Performance

100 MB single-pass scan: 0.6199s, below the 8s M1 target.

Baseline file: `.dev_memory/m1_scan_and_extract/perf_baselines/scan_100mb.json`

## Known Gaps

- No M1-blocking gaps currently open.
