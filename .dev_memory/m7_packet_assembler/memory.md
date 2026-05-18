# Milestone M7: packet_assembler

**Status**: completed
**Start commit**: 3159fd1
**Latest implementation commit**: 528ad7f
**Start date**: 2026-05-18
**Completion date**: 2026-05-18
**Estimated effort**: 2 days
**Actual effort**: 1 day

## Scope

M7 implements Layer 5 packet assembly from `docs/DESIGN.md` v0.5 §3.6 and §5.

M7 includes only:

- BudgetPool with HardReserve / SoftReserve accounting and 100% conservation tests.
- Evidence packet assembly from scan, ranking, evidence, and full_match outputs.
- `fallback_raw_context` for unknown / collector-missing / budget-exhausted paths.
- Minimal redaction for LLM-facing markdown/prompt while storage JSON preserves raw paths.
- Token estimation via `tiktoken` with local fallback.

M7 must not implement the M8 wrapper, CLI/e2e workflow, or new collectors.

## Planned Work

- [x] Start M7 dev_memory and branch state.
- [x] Apply M6 review follow-ups.
- [x] Implement BudgetPool.
- [x] Implement MinimalRedactor and token estimation.
- [x] Implement packet assembler and fallback_raw_context.
- [x] Add 20+ unit tests and BudgetPool conservation checks.
- [x] Record test guide, performance notes, and PR.

## Key Change Details

### Change 1: M7 start state
- **Files**: `.dev_memory/current.yaml`, `.dev_memory/m7_packet_assembler/*`, `README.md`
- **Reason**: M6 was merged and M7 is now the active feature branch.
- **Source**: v0.5 §7, §8
- **Tests**: Documentation/state-only.

### Change 2: M6 review follow-up commit hash
- **Files**: `.dev_memory/m6_full_match/test_report.md`
- **Reason**: M6 review noted the report listed the implementation commit instead of the PR final HEAD after CI follow-up.
- **Source**: M6 review feedback, v0.5 §7.3
- **Tests**: Documentation-only.

### Change 3: ctags happy-path tier2 follow-up
- **Files**: `tests/functional/test_full_match_fixtures.py`
- **Reason**: M6 review asked whether tier2 hits still hold when ctags succeeds instead of falling back.
- **Source**: M6 review feedback
- **Tests**: `tests/functional/test_full_match_fixtures.py::test_tier2_full_match_fixtures_hit_with_happy_ctags` verifies 3/3 tier2 hits and `ctags` extraction for source-context collectors.

### Change 4: packet assembler primitives
- **Files**: `gbs_analyzer/packet_assembler.py`
- **Reason**: M7 requires BudgetPool, token estimation, fallback raw context, redaction, and final packet assembly.
- **Source**: v0.5 §3.6, §5, §9.4, §10.2
- **Tests**: `tests/unit/test_packet_assembler.py` covers budget conservation, redaction, fallback, packet shape, and trace emission.

### Change 5: assembler tests
- **Files**: `tests/unit/test_packet_assembler.py`
- **Reason**: M7 DoD requires 20+ tests and BudgetPool conservation 100%.
- **Source**: v0.5 §9.4
- **Tests**: 23 unit tests pass; targeted `packet_assembler.py` coverage is 89%.

## Test Status

| Test type | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Unit | 235 | 0 | 0 |
| Functional | 27 | 0 | 0 |
| M7 assembler unit tests | 23 | 0 | 0 |

Coverage: 95.66% overall; `gbs_analyzer/packet_assembler.py` is 89%.

## Next Stage Entry

- Entry module after M7: wrapper / external integration layer
- Depends on this milestone: `gbs_analyzer/packet_assembler.py`
- Gate: do not start M8 until the M7 PR is reviewed and merged.

## Token Performance Baseline

- Packet assembly direct-tier2 baseline: 0.0608ms/eval across 1000 iterations.
- Packet token estimate: 295/1800.
- BudgetPool conservation: 1400/1400, `conservation_ok=true`.
- Baseline: `.dev_memory/m7_packet_assembler/perf_baselines/packet_assembly_direct_tier2.json`

## Notes for the Next Developer

1. Read `docs/DESIGN.md` §3.6 and §5 before changing packet shape.
2. Preserve M6 `FullMatchResult` semantics; M7 consumes them.
3. Do not add wrapper/e2e behavior in M7.
4. M8 should call `assemble_packet()` from the wrapper instead of duplicating packet shape logic.
