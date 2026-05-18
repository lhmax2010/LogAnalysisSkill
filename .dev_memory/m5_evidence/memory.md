# Milestone M5: evidence collectors

**Status**: completed
**Start commit**: 9216996
**Latest implementation commit**: 36a02e9
**Start date**: 2026-05-15
**Completion date**: 2026-05-15
**Estimated effort**: 3 days
**Actual effort**: 2 days equivalent

## Scope

M5 implements Layer 3 evidence collection from `docs/DESIGN.md` v0.5 §3.4 and
the evidence-collection parts needed by the pattern schema in §3.5.

M5 includes only:

- EvidenceCollector ABC interface with `estimate()` and `collect(granted_budget)`.
- Routing for compile / link / spec / deps evidence.
- ctags three-level fallback: ctags -> regex + brace pairing -> line window +-30.
- Compile collector evidence.
- Link collector evidence.
- Spec collector evidence.
- Deps collector evidence.

M5 must not implement patch/install/generic collectors, full_match, packet assembly,
complete BudgetPool reclaim logic, or fallback_raw_context.

## Planned Work

- [x] Start M5 dev_memory and branch state.
- [x] Read M5 design sections and map collector boundaries.
- [x] Implement EvidenceCollector ABC and routing.
- [x] Implement ctags fallback helper with dedicated tests.
- [x] Implement compile evidence collector.
- [x] Implement link evidence collector.
- [x] Implement spec evidence collector.
- [x] Implement deps evidence collector.
- [x] Add 30+ unit tests and at least 2 fixtures per collector.
- [x] Record happy-path and ctags-failure performance baselines.
- [x] Record M5 test report, guide, and PR.

## Key Change Details

### Change 1: EvidenceCollector ABC and ctags fallback
- **Files**: `gbs_analyzer/evidence/base.py`, `gbs_analyzer/_utils/ctags_loader.py`, `tests/unit/test_ctags_loader.py`, `tests/unit/test_evidence_base.py`
- **Reason**: M5 requires a stable collector interface and ctags -> regex/brace -> line-window fallback chain.
- **Source**: v0.5 §3.4
- **Tests**: 8 unit tests covering Evidence shape and all ctags fallback methods.

### Change 2: MVP evidence collectors and router
- **Files**: `gbs_analyzer/evidence/{compile,link,spec,deps,router}.py`, `tests/unit/test_evidence_collectors.py`
- **Reason**: M5 includes only compile, link, spec, and deps collectors with `estimate()` and `collect(granted_budget)`.
- **Source**: v0.5 §3.4 and §3.5
- **Tests**: 28 collector unit tests, including ctags failure handling.

### Change 3: collector fixtures
- **Files**: `tests/fixtures/evidence_*`, `tests/functional/test_evidence_fixtures.py`
- **Reason**: M5 DoD requires each collector to have at least 2 fixtures and ctags fallback to trigger at least once.
- **Source**: v0.5 §9.4
- **Tests**: 8 collector fixture cases plus a ctags line-window fallback fixture.

### Change 4: README status update
- **Files**: `README.md`
- **Reason**: M4 is now merged, so the repository status should show M4 as the latest merged milestone.
- **Source**: M3 review workflow correction
- **Tests**: Documentation-only.

## Test Status

| Test type | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Unit | 174 | 0 | 0 |
| Functional | 21 | 0 | 0 |
| M5 collector fixture cases | 8/8 | 0 | 0 |

Full validation: `.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80`
passed with 195 tests and 96.55% coverage.

M5-specific unit tests: 36 (`test_ctags_loader.py`, `test_evidence_base.py`,
`test_evidence_collectors.py`).

## Next Stage Entry

- Entry module after M5: `gbs_analyzer/full_match.py`
- Depends on this milestone: stable EvidenceCollector interface and collector outputs
- Gate: do not start M6 until the M5 PR is reviewed and merged.

## Token Performance Baseline

- Happy-path 8-fixture collector batch mean runtime: 1.3961ms (target < 500ms per collection)
- ctags-failure 8-fixture collector batch mean runtime: 1.1176ms
- Happy-path per evaluation mean runtime: 0.1745ms
- ctags-failure per evaluation mean runtime: 0.1397ms
- Baselines:
  - `.dev_memory/m5_evidence/perf_baselines/collectors_8_fixtures_happy.json`
  - `.dev_memory/m5_evidence/perf_baselines/collectors_8_fixtures_ctags_failure.json`

## Notes for the Next Developer

1. Read `docs/DESIGN.md` §3.4 and §3.5 before changing collector behavior.
2. Do not implement M6 full_match or M7 packet assembly in this milestone.
3. Treat ctags fallback tests as a release gate.
