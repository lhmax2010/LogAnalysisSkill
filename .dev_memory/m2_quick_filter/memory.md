# Milestone M2: quick_filter

**Status**: in-progress
**Start commit**: c6dbec9
**Latest commit**: in-progress
**Start date**: 2026-05-12
**Completion date**:
**Estimated effort**: 2 days
**Actual effort**:

## Scope

M2 implements Layer 4a Quick Pattern Filter from `docs/DESIGN.md` v0.5 §3.2 and §4.
It also includes the approved M1 review follow-ups:

- Densified scanner performance fixture.
- Edge-case tests for scanner behavior.
- Ignore the user's local `temp/` workspace.

M2 must not implement M3 ranking or M5 evidence collectors.

## Planned Work

- [x] Start M2 dev_memory and branch state.
- [x] Ignore local `temp/` workspace.
- [ ] Add M1 review follow-up scanner perf and edge-case tests.
- [ ] Add `patterns/schema.json` and tier1 pattern data.
- [ ] Implement `gbs_analyzer/quick_filter.py`.
- [ ] Enforce tier1 allowlist/forbidden categories and fix-template length rules.
- [ ] Implement required_context and warning-block heuristic.
- [ ] Add 20+ unit tests and 4 Fast-Path fixtures.
- [ ] Record M2 test report, guide, and performance baseline.

## Key Change Details

Pending implementation commits.

## Test Status

| Test type | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Unit | 52 | 0 | 0 |
| Functional scan fixtures | 5 | 0 | 0 |
| M2 Fast-Path fixtures | 0 | 0 | 0 |

Initial baseline: `.venv/bin/pytest tests/` passed before M2 implementation.

## Next Stage Entry

- Entry module after M2: `gbs_analyzer/rank_causes.py`
- Depends on this milestone: quick filter result and pattern loading
- Gate: do not start M3 until the M2 PR is reviewed and merged.

## Token Performance Baseline

Pending. M2 must record quick filter runtime under the 100ms target.

## Notes for the Next Developer

1. Read `docs/DESIGN.md` §3.2 and §4.
2. Do not implement Layer 2 ranking in this milestone.
3. Keep M2 review follow-ups separate from quick-filter implementation commits.
