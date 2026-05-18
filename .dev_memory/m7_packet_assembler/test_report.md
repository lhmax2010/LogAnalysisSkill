# Test Report for M7: packet_assembler

## Environment
- Date: 2026-05-18
- OS: Linux linhao-linux 6.17.0-23-generic x86_64
- Python: 3.12.3
- Commit: 528ad7f

## Commands

```bash
.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
```

## Results

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer` | pass | No issues in 23 source files. |
| `.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80` | pass | 262 passed; total coverage 95.66%. |
| `.venv/bin/pytest tests/unit/test_packet_assembler.py --cov=gbs_analyzer.packet_assembler --cov-report=term-missing -q` | pass | 23 passed; `packet_assembler.py` coverage 89%. |

## Coverage

| Module | Coverage |
| --- | ---: |
| `gbs_analyzer/packet_assembler.py` | 89% |
| Total | 95.66% |

## Performance

| Baseline | Result | Notes |
| --- | ---: | --- |
| Direct-tier2 packet assembly, 1000 iterations | 0.0608ms/eval | Token estimate 295/1800; BudgetPool conservation 1400/1400. |

## Known Gaps

- M7 does not run the full wrapper pipeline; M8 owns CLI/wrapper/e2e wiring.
- M7 packet token estimate is local and deterministic; M8 should include end-to-end `perf_report.json`.
