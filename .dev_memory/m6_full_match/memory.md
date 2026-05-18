# Milestone M6: full_match

**Status**: completed
**Start commit**: b134492
**Latest implementation commit**: 15769a6
**Start date**: 2026-05-18
**Completion date**: 2026-05-18
**Estimated effort**: 1 day
**Actual effort**: 1 day

## Scope

M6 implements Layer 4b full pattern matching from `docs/DESIGN.md` v0.5 §3.5
and the full tier1/tier2 pattern schema behavior needed by §4.

M6 includes only:

- Backward-compatible pattern loading for M2 flat tier1 patterns.
- Optional `direct_answer_tier1` / `direct_answer_tier2` schema support.
- `determine_verdict()` with `DIRECT_TIER1`, `DIRECT_TIER2`, and `NEEDS_LLM`.
- Tier2 evidence completeness checks via `Evidence.contains_all()`.
- Functional tier2 fixtures and a performance baseline.

M6 must not implement packet assembly, fallback raw context, BudgetPool reclaim,
or new collector behavior.

## Planned Work

- [x] Start M6 dev_memory and branch state.
- [x] Apply M5 review follow-ups.
- [x] Add full_match module and pattern compatibility loader.
- [x] Extend pattern schema and patterns with tier2 direct-answer fields.
- [x] Add unit tests and at least 3 tier2 fixture hits.
- [x] Record performance baseline, test guide, and PR.

## Key Change Details

### Change 1: M6 start state
- **Files**: `.dev_memory/current.yaml`, `.dev_memory/m6_full_match/*`, `README.md`
- **Reason**: M5 was merged and M6 is now the active feature branch.
- **Source**: v0.5 §7, §8
- **Tests**: Documentation/state-only.

### Change 2: M5 review follow-up
- **Files**: `tests/unit/test_evidence_base.py`, `.dev_memory/m5_evidence/decisions.md`
- **Reason**: M5 review requested 95%+ coverage for `evidence/base.py` and explicit declaration of collector coverage blind spots.
- **Source**: M5 review feedback, v0.5 §7.3
- **Tests**: `.venv/bin/pytest tests/unit/test_evidence_base.py --cov=gbs_analyzer.evidence.base --cov-report=term-missing -q` passes with 100% module coverage.

### Change 3: full_match verdict engine
- **Files**: `gbs_analyzer/full_match.py`, `patterns/schema.json`, `patterns/gbs_errors.yaml`, `gbs_analyzer/quick_filter.py`
- **Reason**: M6 requires Layer 4b verdicts and backward-compatible tier1/tier2 pattern schema support.
- **Source**: v0.5 §3.5, §4; M2 decision d003
- **Tests**: `tests/unit/test_full_match.py` covers loader compatibility, `determine_verdict()`, degraded rejection, required context, and invalid schema cases.

### Change 4: tier2 fixture hits
- **Files**: `tests/functional/test_full_match_fixtures.py`
- **Reason**: M6 DoD requires tier2 hits on at least 3 fixtures.
- **Source**: v0.5 §9.4
- **Tests**: 3/3 tier2 fixture cases hit `compile_undeclared_identifier_tier2`, `linker_undefined_reference_tier2`, and `rpm_phase_failure_tier2`.

## Test Status

| Test type | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Unit | 212 | 0 | 0 |
| Functional | 24 | 0 | 0 |
| M6 tier2 fixture cases | 3/3 | 0 | 0 |

Coverage: 96.92% overall; `gbs_analyzer/full_match.py` is 97%.

## Next Stage Entry

- Entry module after M6: `gbs_analyzer/packet_assembler.py`
- Depends on this milestone: `gbs_analyzer/full_match.py`
- Gate: do not start M7 until the M6 PR is reviewed and merged.

## Token Performance Baseline

- Full-match tier2 fixture per-evaluation runtime: 5.5546ms across 900 evaluations.
- Baseline: `.dev_memory/m6_full_match/perf_baselines/full_match_3_tier2_fixtures.json`

## Notes for the Next Developer

1. Read `docs/DESIGN.md` §3.5 and §4 before changing verdict behavior.
2. Preserve M2 decision d003: flat `tier: tier1` patterns remain valid shorthand.
3. Do not add packet assembly or BudgetPool reclaim in M6.
4. M7 should consume `FullMatchResult.as_dict()` but may choose its own packet-level verdict shape.
