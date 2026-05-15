# Test Report for M4: spec_minimal

## Environment
- Date: 2026-05-15
- OS: local development environment
- Python: 3.12.3
- Start commit: b600505

## Commands

```bash
.venv/bin/pytest tests/
.venv/bin/pytest tests/unit/test_spec_minimal.py -q
.venv/bin/pytest tests/functional/test_spec_fixtures.py -q
.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
.venv/bin/ruff check .
.venv/bin/mypy gbs_analyzer
```

## Results

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/pytest tests/` | pass | Initial baseline before M4 implementation, 130 passed. |
| `.venv/bin/pytest tests/unit/test_spec_minimal.py -q` | pass | 17 passed. |
| `.venv/bin/pytest tests/functional/test_spec_fixtures.py -q` | pass | 2 passed; 5/5 fixture cases extracted. |
| `.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80` | pass | 154 passed, total coverage 98.49%. |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer` | pass | No issues in 12 source files. |

## Coverage

| Module | Coverage |
| --- | ---: |
| `gbs_analyzer/tizen/spec_minimal.py` | 95% |
| `gbs_analyzer/tizen/__init__.py` | 100% |
| Total | 98.49% |

## Performance

| Baseline | Result | Target |
| --- | ---: | ---: |
| Spec extraction success on 5 M4 fixtures | 100% | 100% |
| 5-fixture spec batch mean | 0.7204ms | < 200ms |
| 5-fixture spec batch p95 | 1.1619ms | < 200ms |
| Per-evaluation mean | 0.1441ms | < 200ms |

Raw baseline: `.dev_memory/m4_spec_minimal/perf_baselines/spec_5_fixtures.json`.

## Known Gaps

- No known M4 gaps.
- M5 evidence collectors and full-stage analyzers were intentionally not implemented.
