# Milestone M3: rank_causes

**Status**: in-progress
**Start commit**: 77c7ad5
**Latest commit**: in-progress
**Start date**: 2026-05-15
**Completion date**:
**Estimated effort**: 1.5 days
**Actual effort**:

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
- [ ] Apply M2 review follow-ups.
- [ ] Add `patterns/error_semantics.yaml`.
- [ ] Implement semantic classifier for 8 classes.
- [ ] Implement `gbs_analyzer/rank_causes.py`.
- [ ] Implement generic_error gating and confidence_reason output.
- [ ] Add 15+ unit tests and ranking accuracy fixtures.
- [ ] Record M3 test report, guide, and performance baseline.

## Key Change Details

Pending implementation commits.

## Test Status

| Test type | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Unit | 77 | 0 | 0 |
| Functional | 11 | 0 | 0 |
| M3 accuracy fixtures | 0 | 0 | 0 |

Initial baseline: `.venv/bin/pytest tests/` passed before M3 implementation.

## Next Stage Entry

- Entry module after M3: `gbs_analyzer/tizen/spec_minimal.py`
- Depends on this milestone: ranked Top-K candidate output
- Gate: do not start M4 until the M3 PR is reviewed and merged.

## Token Performance Baseline

Pending. M3 must record ranking runtime under the 50ms target.

## Notes for the Next Developer

1. Read `docs/DESIGN.md` §3.3 before changing ranking behavior.
2. Do not implement Layer 3 evidence collection in this milestone.
3. Stop after opening the M3 PR.
