# Milestone M8: wrapper_and_e2e

**Status**: in_progress
**Start commit**: 18e4d33
**Latest implementation commit**: TBD
**Start date**: 2026-05-18
**Completion date**: TBD
**Estimated effort**: 2 days
**Actual effort**: TBD

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
- [ ] Rewrite `SKILL.md` for runtime use.
- [ ] Add integration examples.
- [ ] Add 20 E2E fixtures and acceptance tests.
- [ ] Record final test report, perf baseline, and PR.

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

## Test Status

M7 follow-up targeted test passed:

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/pytest tests/unit/test_packet_assembler.py --cov=gbs_analyzer.packet_assembler --cov-report=term-missing -q` | pass | 33 passed; `packet_assembler.py` coverage 99%. |
| `.venv/bin/ruff check gbs_analyzer/analyze.py gbs_analyzer/tracing/perf_report.py gbs_analyzer/__main__.py` | pass | New M8 modules lint clean. |
| `.venv/bin/mypy gbs_analyzer` | pass | No type errors in 26 source files. |

## Next Stage Entry

- Entry after M8: MVP review and delivery.
- Gate: do not continue to post-MVP/full milestones until the M8 PR is reviewed and merged.

## Notes for the Next Developer

1. M8 starts from merge commit `18e4d33`.
2. M7 review follow-ups must be completed before wrapper implementation.
3. Treat the 20 E2E fixtures as MVP acceptance data; do not tune expected outputs only to satisfy tests.
