# Test Report for M6: full_match

## Environment
- Date: 2026-05-18
- OS: Linux linhao-linux 6.17.0-23-generic x86_64
- Python: 3.12.3
- Commit: 4d23877

## Commands

```bash
.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
```

## Results

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer` | pass | No issues in 22 source files. |
| `.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80` | pass | 236 passed; total coverage 96.93%. |
| `.venv/bin/pytest tests/functional/test_quick_filter_fixtures.py::test_quick_filter_fixtures_run_under_100ms -q` | pass | CI follow-up for GitHub Actions 100ms budget failure. |
| `.venv/bin/pytest tests/unit/test_full_match.py --cov=gbs_analyzer.full_match --cov-report=term-missing -q` | pass | 30 passed; `full_match.py` coverage 96%. |

## Coverage

| Module | Coverage |
| --- | ---: |
| `gbs_analyzer/full_match.py` | 97% in full run; 96% targeted |
| `gbs_analyzer/evidence/base.py` | 100% |
| Total | 96.93% |

## Performance

| Baseline | Result | Notes |
| --- | ---: | --- |
| 3 tier2 fixtures, 900 evaluations | 5.5546ms/eval | Target < 50ms; 900/900 tier2 hits. |

## Known Gaps

- M6 does not assemble packets or consume BudgetPool; that is M7.
- M6 does not add new collector behavior; it consumes M5 evidence only.
