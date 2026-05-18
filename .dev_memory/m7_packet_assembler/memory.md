# Milestone M7: packet_assembler

**Status**: in-progress
**Start commit**: 3159fd1
**Latest commit**: pending
**Start date**: 2026-05-18
**Completion date**:
**Estimated effort**: 2 days
**Actual effort**:

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
- [ ] Implement BudgetPool.
- [ ] Implement MinimalRedactor and token estimation.
- [ ] Implement packet assembler and fallback_raw_context.
- [ ] Add 20+ unit tests and BudgetPool conservation checks.
- [ ] Record test guide, performance notes, and PR.

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

## Test Status

| Test type | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Unit | 0 | 0 | 0 |
| Functional | 0 | 0 | 0 |
| Integration | 0 | 0 | 0 |

Coverage: pending

## Next Stage Entry

- Entry module after M7: wrapper / external integration layer
- Depends on this milestone: `gbs_analyzer/packet_assembler.py`
- Gate: do not start M8 until the M7 PR is reviewed and merged.

## Token Performance Baseline

- Packet assembly runtime/token budget: pending

## Notes for the Next Developer

1. Read `docs/DESIGN.md` §3.6 and §5 before changing packet shape.
2. Preserve M6 `FullMatchResult` semantics; M7 consumes them.
3. Do not add wrapper/e2e behavior in M7.
