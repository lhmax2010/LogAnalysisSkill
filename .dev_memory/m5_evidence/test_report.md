# Test Report for M5: evidence collectors

## Environment
- Date: 2026-05-15
- OS: local development environment
- Python: 3.12.3
- Start commit: 9216996

## Commands

```bash
.venv/bin/pytest tests/
.venv/bin/pytest tests/unit/test_ctags_loader.py tests/unit/test_evidence_base.py tests/unit/test_evidence_collectors.py -q
.venv/bin/pytest tests/functional/test_evidence_fixtures.py -q
.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
.venv/bin/ruff check .
.venv/bin/mypy gbs_analyzer
```

## Results

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/pytest tests/` | pass | Initial baseline before M5 implementation, 154 passed. |
| `.venv/bin/pytest tests/unit/test_ctags_loader.py tests/unit/test_evidence_base.py tests/unit/test_evidence_collectors.py -q` | pass | 40 passed; ctags, ABC, collectors covered. |
| `.venv/bin/pytest tests/functional/test_evidence_fixtures.py -q` | pass | 5 passed; 8/8 collector fixtures collected. |
| `.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80` | pass | 195 passed, total coverage 96.55%. |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer` | pass | No issues in 21 source files. |

## Coverage

| Module | Coverage |
| --- | ---: |
| `gbs_analyzer/_utils/ctags_loader.py` | 95% |
| `gbs_analyzer/evidence/base.py` | 88% |
| `gbs_analyzer/evidence/compile.py` | 95% |
| `gbs_analyzer/evidence/link.py` | 97% |
| `gbs_analyzer/evidence/spec.py` | 95% |
| `gbs_analyzer/evidence/deps.py` | 93% |
| `gbs_analyzer/evidence/router.py` | 95% |
| Total | 96.55% |

## Performance

| Baseline | Result | Target |
| --- | ---: | ---: |
| Happy-path 8-fixture collector batch mean | 1.3961ms | < 500ms per collection |
| Happy-path per evaluation mean | 0.1745ms | < 500ms |
| ctags-failure 8-fixture collector batch mean | 1.1176ms | < 500ms per collection |
| ctags-failure per evaluation mean | 0.1397ms | < 500ms |
| Collector fixture success rate | 100% | 100% |

Raw baselines:
- `.dev_memory/m5_evidence/perf_baselines/collectors_8_fixtures_happy.json`
- `.dev_memory/m5_evidence/perf_baselines/collectors_8_fixtures_ctags_failure.json`

## Known Gaps

- No known M5 gaps.
- patch/install/generic collectors, full_match, BudgetPool reclaim, and fallback_raw_context were intentionally not implemented.
