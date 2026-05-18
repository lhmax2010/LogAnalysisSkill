# Test Report for M8: wrapper_and_e2e

## Environment
- Date: 2026-05-18
- OS: Linux linhao-linux 6.17.0-23-generic x86_64
- Python: 3.12.3
- Commit under test: 69812b9

## Commands

```bash
.venv/bin/ruff check .
.venv/bin/mypy gbs_analyzer
.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
.venv/bin/pytest tests/e2e/test_m8_wrapper_e2e.py -q
```

## Results

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer` | pass | No issues in 26 source files. |
| `.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80` | pass | 301 passed; total coverage 96.39%. |
| `.venv/bin/pytest tests/e2e/test_m8_wrapper_e2e.py -q` | pass | 21 passed in 3.27s. |

## Coverage

| Module | Coverage |
| --- | ---: |
| `gbs_analyzer/analyze.py` | 89% |
| `gbs_analyzer/tracing/perf_report.py` | 89% |
| `gbs_analyzer/packet_assembler.py` | 99% |
| Total | 96.39% |

## Performance

| Metric | Result | Gate |
| --- | ---: | ---: |
| 20-fixture E2E runtime | 1.5928s | < 15s |
| Fast-Path hit rate | 30% | >= 25% |
| Direct-answer rate | 65% | >= 35% |
| Top-1 primary error accuracy | 100% | >= 80% |
| BudgetPool conservation | 100% | 100% |

Baseline: `.dev_memory/m8_wrapper_and_e2e/perf_baselines/e2e_20_fixtures.json`

## MVP Acceptance

| Gate | Status | Notes |
| --- | --- | --- |
| 20 fixtures all pass | pass | Every `tests/fixtures/e2e_*` directory has `buildlog`, `expected_packet.json`, and `README.md`. |
| Fast-Path hit rate >= 25% | pass | 6/20 = 30%. |
| Top-1 accuracy >= 80% | pass | 20/20 = 100%. |
| E2E < 15s | pass | 1.5928s baseline; pytest E2E suite 3.27s. |
| BudgetPool conservation 100% | pass | 14/14 full-path packets with BudgetPool fields conserve. |
| dev_memory complete | pass | M8 memory, decisions, known_issues, patches, test_report, perf_baselines present. |
