# Milestone M8: wrapper_and_e2e

**Status**: completed
**Start commit**: 18e4d33
**Latest implementation commit**: cdc992f
**Start date**: 2026-05-18
**Completion date**: 2026-05-18
**Estimated effort**: 2 days
**Actual effort**: 1 day

## Scope

M8 implements the MVP wrapper and acceptance surface from `docs/DESIGN.md` v0.5 §6, §8, §10, §11, and §13.

M8 includes only:

- `python -m gbs_analyzer analyze <buildlog_path>` wrapper entrypoint.
- End-to-end orchestration: scan -> quick_filter -> rank -> evidence -> full_match -> assembler.
- `perf_report.json` with layer timing, token breakdown, decisions, warnings, and degradations.
- Runtime `SKILL.md`.
- Cline and Compiling Agent example integrations.
- 20 fixture E2E acceptance tests.

M8 must not implement post-MVP collectors, expand behavior, full deployment integration, or post-MVP pattern work.

## Planned Work

- [x] Start M8 dev_memory and branch state.
- [x] Apply M7 review follow-ups.
- [x] Implement analyze wrapper and module entrypoint.
- [x] Implement perf_report generation.
- [x] Rewrite `SKILL.md` for runtime use.
- [x] Add integration examples.
- [x] Add 20 E2E fixtures and acceptance tests.
- [x] Record final test report and PR.

## Key Change Details

### Change 1: M8 start state
- **Files**: `.dev_memory/current.yaml`, `.dev_memory/m8_wrapper_and_e2e/*`, `README.md`
- **Reason**: M7 was merged and M8 is now the active MVP acceptance feature branch.
- **Source**: v0.5 §7, §8, §13
- **Tests**: Documentation/state-only.

### Change 2: M7 review follow-ups
- **Files**: `gbs_analyzer/packet_assembler.py`, `tests/unit/test_packet_assembler.py`, `.dev_memory/m7_packet_assembler/decisions.md`
- **Reason**: M7 review required `packet_assembler.py` targeted coverage to reach 95%+ and asked for a d006 reflection on the 1-day finish plus 89% module coverage signal.
- **Source**: M7 review feedback, v0.5 §7.3, §9.4
- **Tests**: `.venv/bin/pytest tests/unit/test_packet_assembler.py --cov=gbs_analyzer.packet_assembler --cov-report=term-missing -q` passes with 33 tests and 99% targeted coverage.

### Change 3: wrapper and perf report
- **Files**: `gbs_analyzer/analyze.py`, `gbs_analyzer/__main__.py`, `gbs_analyzer/tracing/perf_report.py`
- **Reason**: M8 requires a single analyzer entrypoint plus `perf_report.json` for wrapper consumers.
- **Source**: v0.5 §10.2, §11.3, §13
- **Tests**: Smoke-tested `python -m gbs_analyzer analyze` on fast-path and full-path fixtures; ruff and mypy pass for new modules.

### Change 4: wrapper and perf unit tests
- **Files**: `tests/unit/test_analyze_wrapper.py`, `tests/unit/test_perf_report.py`
- **Reason**: M8 wrapper contract needs focused coverage before larger E2E fixtures.
- **Source**: v0.5 §9.4, §10.2, §11.3
- **Tests**: `.venv/bin/pytest tests/unit/test_analyze_wrapper.py tests/unit/test_perf_report.py -q` passes with 8 tests.

### Change 5: runtime SKILL.md
- **Files**: `SKILL.md`
- **Reason**: M8 turns the repository from setup/runtime placeholder into a usable Anthropic-style skill.
- **Source**: v0.5 §8, §11.3, §13
- **Tests**: Documentation-only.

### Change 6: integration examples
- **Files**: `integrations/cline/*`, `integrations/compiling_agent/*`, `integrations/README.md`
- **Reason**: M8 requires Cline and Compiling Agent example contracts without live deployment.
- **Source**: v0.5 §11
- **Tests**: `.venv/bin/ruff check integrations/compiling_agent/log_analysis.py` and `.venv/bin/mypy integrations/compiling_agent/log_analysis.py` pass.

### Change 7: 20 fixture E2E
- **Files**: `tests/fixtures/e2e_*/*`, `tests/e2e/test_m8_wrapper_e2e.py`, `gbs_analyzer/analyze.py`
- **Reason**: M8 is the MVP acceptance milestone; wrapper behavior must be validated end to end across Fast-Path, compile, link, spec, cascade, Clang, Werror, and unknown fallback cases.
- **Source**: v0.5 §9.3, §10.3, §13
- **Tests**: `.venv/bin/pytest tests/e2e/test_m8_wrapper_e2e.py -q` passes with 21 tests over 20 fixtures.

### Change 8: E2E perf baseline and guide
- **Files**: `.dev_memory/m8_wrapper_and_e2e/perf_baselines/e2e_20_fixtures.json`, `docs/test_guides/m8_wrapper_and_e2e.md`
- **Reason**: M8 is the MVP acceptance point and needs durable reproduction notes plus perf data.
- **Source**: v0.5 §9.5, §10.3, §13
- **Tests**: Baseline records 20 fixtures in 1.5928s, Fast-Path 30%, Top-1 100%, BudgetPool conservation 100%.

## MVP Acceptance Baseline

- Fixtures: 20/20 pass.
- E2E batch runtime: 1.5928s (target < 15s).
- Fast-Path hit rate: 30% (target >= 25%).
- Direct-answer rate: 65% (target >= 35%).
- Top-1 primary error accuracy: 100% (target >= 80%).
- BudgetPool conservation: 100% on full-path packets.

## Test Status

M7 follow-up targeted test passed:

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/pytest tests/unit/test_packet_assembler.py --cov=gbs_analyzer.packet_assembler --cov-report=term-missing -q` | pass | 33 passed; `packet_assembler.py` coverage 99%. |
| `.venv/bin/ruff check gbs_analyzer/analyze.py gbs_analyzer/tracing/perf_report.py gbs_analyzer/__main__.py` | pass | New M8 modules lint clean. |
| `.venv/bin/mypy gbs_analyzer` | pass | No type errors in 26 source files. |
| `.venv/bin/pytest tests/unit/test_analyze_wrapper.py tests/unit/test_perf_report.py -q` | pass | 8 passed. |
| `.venv/bin/ruff check integrations/compiling_agent/log_analysis.py` | pass | Example adapter lint clean. |
| `.venv/bin/mypy integrations/compiling_agent/log_analysis.py` | pass | Example adapter type-checks standalone. |
| `.venv/bin/ruff check gbs_analyzer/analyze.py tests/e2e/test_m8_wrapper_e2e.py` | pass | E2E test and wrapper update lint clean. |
| `.venv/bin/pytest tests/e2e/test_m8_wrapper_e2e.py -q` | pass | 21 passed; 20 fixture contracts plus aggregate MVP metrics. |
| `.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80` | pass | 301 passed; total coverage 96.39%. |

## Final Test Status

| Test type | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Full suite | 301 | 0 | 0 |
| M8 E2E fixture contracts | 20 | 0 | 0 |
| M8 acceptance metrics | 1 | 0 | 0 |

Coverage: 96.39% overall.

## Next Stage Entry

- Entry after M8: MVP review and delivery.
- Gate: do not continue to post-MVP/full milestones until the M8 PR is reviewed and merged.

## Notes for the Next Developer

1. M8 starts from merge commit `18e4d33`.
2. M7 review follow-ups must be completed before wrapper implementation.
3. Treat the 20 E2E fixtures as MVP acceptance data; do not tune expected outputs only to satisfy tests.
4. M8 is complete and waiting for PR review; do not start post-MVP/full milestones from this branch.
