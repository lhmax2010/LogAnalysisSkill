# Milestone M3: rank_causes

**Status**: completed
**Start commit**: 77c7ad5
**Latest implementation commit**: 4229204
**Start date**: 2026-05-15
**Completion date**: 2026-05-15
**Estimated effort**: 1.5 days
**Actual effort**: 1 day

## Scope

M3 implements Layer 2 root-cause ranking from `docs/DESIGN.md` v0.5 §3.3.
It also includes the approved M2 review follow-ups:

- Record pattern schema flattening and `event_kinds` extension decisions.
- Improve `quick_filter.py` coverage to 90%+.
- Update README project status and PR checklist.
- Correct M2 test count bookkeeping.

M3 must not implement M4 `spec_minimal` or M5 evidence collectors.

## Planned Work

- [x] Start M3 dev_memory and branch state.
- [x] Apply M2 review follow-ups.
- [x] Add `patterns/error_semantics.yaml`.
- [x] Implement semantic classifier for 8 classes.
- [x] Implement `gbs_analyzer/rank_causes.py`.
- [x] Implement generic_error gating and confidence_reason output.
- [x] Add 15+ unit tests and ranking accuracy fixtures.
- [x] Record M3 test report, guide, and performance baseline.

## Key Change Details

### Change 1: M2 review follow-ups
- **Files**: `.dev_memory/m2_quick_filter/*`, `README.md`, `.github/pull_request_template.md`, `tests/unit/test_quick_filter.py`
- **Reason**: M2 review requested explicit pattern-schema decisions, README status update, patches/test-count cleanup, and quick-filter coverage above 90%.
- **Source**: M2 review follow-up, v0.5 §7.3 and §7.4
- **Tests**: `tests/unit/test_quick_filter.py` passes with 100% module coverage.

### Change 2: semantic classification config
- **Files**: `patterns/error_semantics.yaml`, `gbs_analyzer/_utils/semantic_classifier.py`, `tests/unit/test_semantic_classifier.py`
- **Reason**: M3 requires the 8 semantic classes from v0.5 §4.3 / Appendix C before ranking can score events.
- **Source**: v0.5 §3.3 and §4.3
- **Tests**: 13 semantic-classifier unit tests.

### Change 3: root-cause ranking
- **Files**: `gbs_analyzer/rank_causes.py`, `tests/unit/test_rank_causes.py`
- **Reason**: Rank scanner events into Top-K root-cause candidates with structured `confidence_reason` output.
- **Source**: v0.5 §3.3
- **Tests**: 10 ranker unit tests.

### Change 4: accuracy and runtime fixtures
- **Files**: `tests/fixtures/rank_*`, `tests/functional/test_rank_fixtures.py`
- **Reason**: M3 DoD requires Top-1 accuracy >= 80% and runtime under 50ms.
- **Source**: v0.5 §9.4
- **Tests**: 5/5 ranking fixtures hit expected Top-1 class; cached 5-fixture batch mean runtime 0.1092ms.

### Change 5: cached semantic classifier config
- **Files**: `gbs_analyzer/_utils/semantic_classifier.py`
- **Reason**: CI Python 3.11 + coverage made repeated YAML loading push the functional runtime test just above 50ms.
- **Source**: M3 CI follow-up
- **Tests**: `tests/functional/test_rank_fixtures.py`, `tests/unit/test_semantic_classifier.py`, `tests/unit/test_rank_causes.py`

## Test Status

| Test type | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Unit | 116 | 0 | 0 |
| Functional | 14 | 0 | 0 |
| M3 ranking fixture cases | 5/5 | 0 | 0 |

Full validation: `.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80`
passed with 130 tests and 99.44% coverage.

M3-specific unit tests: 23 (`test_semantic_classifier.py` + `test_rank_causes.py`).

## Next Stage Entry

- Entry module after M3: `gbs_analyzer/tizen/spec_minimal.py`
- Depends on this milestone: ranked Top-K candidate output
- Gate: do not start M4 until the M3 PR is reviewed and merged.

## Token Performance Baseline

- Ranking 5-fixture batch mean runtime: 0.1092ms (target < 50ms)
- Ranking per evaluation mean runtime: 0.0218ms
- Cold-start 5-fixture batch mean runtime: 6.5737ms (target < 50ms)
- Cold-start per evaluation mean runtime: 1.3147ms
- Top-1 accuracy on M3 fixtures: 100% (target >= 80%)
- Baselines:
  - `.dev_memory/m3_rank_causes/perf_baselines/rank_5_fixtures.json`
  - `.dev_memory/m3_rank_causes/perf_baselines/rank_5_fixtures_cold.json`

## Notes for the Next Developer

1. Read `docs/DESIGN.md` §3.3 before changing ranking behavior.
2. Do not implement Layer 3 evidence collection in this milestone.
3. Start M4 only after the M3 PR is reviewed and merged.
