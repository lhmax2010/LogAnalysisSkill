# M8 Test Guide: wrapper_and_e2e

## Scope

M8 validates the MVP wrapper, runtime skill contract, perf report, integration
examples, and 20 fixture E2E acceptance set.

## Commands

```bash
.venv/bin/ruff check .
.venv/bin/mypy tizen-gbs-log-analysis/scripts/gbs_analyzer
.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
.venv/bin/pytest tests/e2e/test_m8_wrapper_e2e.py -q
```

## E2E Acceptance

The E2E suite runs `python -m gbs_analyzer analyze` against every
`tests/fixtures/e2e_*` directory and checks:

- `evidence_packet.json`, `evidence_packet.md`, `perf_report.json`, and `trace.jsonl`
  are written.
- 20 fixture contracts match their `expected_packet.json`.
- Fast-Path hit rate is at least 25%.
- Direct-answer rate is at least 35%.
- Top-1 primary error accuracy is at least 80%.
- BudgetPool conservation is 100% for full-path packets.
- End-to-end fixture batch runtime stays below 15 seconds.

## Representative Manual Run

```bash
python -m gbs_analyzer analyze tests/fixtures/e2e_compile_undeclared/buildlog \
    --src-root tests/fixtures/e2e_compile_undeclared/src \
    --output-format both \
    --output-dir /tmp/gbs_m8_manual \
    --package demo \
    --no-tiktoken
```

Expected outputs:

- `/tmp/gbs_m8_manual/evidence_packet.json`
- `/tmp/gbs_m8_manual/evidence_packet.md`
- `/tmp/gbs_m8_manual/perf_report.json`
- `/tmp/gbs_m8_manual/trace.jsonl`
