# Test Report for M3: rank_causes

## Environment
- Date: 2026-05-15
- OS: local development environment
- Python: 3.12.3
- Start commit: 77c7ad5

## Commands

```bash
.venv/bin/pytest tests/
.venv/bin/pytest tests/unit/test_quick_filter.py --cov=gbs_analyzer.quick_filter --cov-report=term-missing -q
.venv/bin/pytest tests/functional/test_rank_fixtures.py -v
.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
.venv/bin/ruff check .
.venv/bin/mypy gbs_analyzer
```

## Results

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/pytest tests/` | pass | Initial baseline before M3 implementation, 88 passed. |
| `.venv/bin/pytest tests/unit/test_quick_filter.py --cov=gbs_analyzer.quick_filter --cov-report=term-missing -q` | pass | M2 follow-up: 39 passed, quick_filter.py 100% coverage. |
| `.venv/bin/pytest tests/functional/test_rank_fixtures.py -v` | pass | 3 passed; 5/5 fixture cases have expected Top-1 class. |
| `.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80` | pass | 130 passed, total coverage 99.44%. |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer` | pass | No issues in 10 source files. |

## Coverage

| Module | Coverage |
| --- | ---: |
| `gbs_analyzer/quick_filter.py` | 100% |
| `gbs_analyzer/rank_causes.py` | 100% |
| `gbs_analyzer/_utils/semantic_classifier.py` | 98% |
| Total | 99.44% |

## Test Count Summary

- Total pytest test functions: 130.
- Unit test functions: 116.
- Functional test functions: 14.
- M3 ranking fixtures: 5 fixture cases asserted inside `tests/functional/test_rank_fixtures.py`; these are a subset of the 14 functional tests, not an additional test-count category.

## Performance

| Baseline | Result | Target |
| --- | ---: | ---: |
| Top-1 accuracy on 5 M3 fixtures | 100% | >= 80% |
| 5-fixture rank batch mean | 0.1092ms | < 50ms |
| 5-fixture rank batch p95 | 0.1578ms | < 50ms |
| Per-evaluation mean | 0.0218ms | < 50ms |
| Cold-start 5-fixture rank batch mean | 6.5737ms | < 50ms |
| Cold-start 5-fixture rank batch p95 | 7.3806ms | < 50ms |
| Cold-start per-evaluation mean | 1.3147ms | < 50ms |

Raw baselines:
- `.dev_memory/m3_rank_causes/perf_baselines/rank_5_fixtures.json`
- `.dev_memory/m3_rank_causes/perf_baselines/rank_5_fixtures_cold.json`

## Known Gaps

- No known M3 gaps.
- M4 `spec_minimal` and M5 evidence collectors were intentionally not implemented.
