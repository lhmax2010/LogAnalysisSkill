# Milestone M5: evidence collectors

**Status**: in-progress
**Start commit**: 9216996
**Latest commit**: in-progress
**Start date**: 2026-05-15
**Completion date**:
**Estimated effort**: 3 days
**Actual effort**:

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
- [ ] Read M5 design sections and map collector boundaries.
- [ ] Implement EvidenceCollector ABC and routing.
- [ ] Implement ctags fallback helper with dedicated tests.
- [ ] Implement compile evidence collector.
- [ ] Implement link evidence collector.
- [ ] Implement spec evidence collector.
- [ ] Implement deps evidence collector.
- [ ] Add 30+ unit tests and at least 2 fixtures per collector.
- [ ] Record happy-path and ctags-failure performance baselines.
- [ ] Record M5 test report, guide, and PR.

## Key Change Details

Pending implementation commits.

## Test Status

| Test type | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Unit | 0 | 0 | 0 |
| Functional | 0 | 0 | 0 |
| M5 collector fixtures | 0 | 0 | 0 |

Initial baseline: `.venv/bin/pytest tests/` passed before M5 implementation.

## Next Stage Entry

- Entry module after M5: `gbs_analyzer/full_match.py`
- Depends on this milestone: stable EvidenceCollector interface and collector outputs
- Gate: do not start M6 until the M5 PR is reviewed and merged.

## Token Performance Baseline

Pending. M5 must record collector runtime under the 500ms target, including ctags failure fallback.

## Notes for the Next Developer

1. Read `docs/DESIGN.md` §3.4 and §3.5 before changing collector behavior.
2. Do not implement M6 full_match or M7 packet assembly in this milestone.
3. Treat ctags fallback tests as a release gate.
