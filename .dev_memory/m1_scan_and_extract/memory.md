# Milestone M1: scan_and_extract

**Status**: in-progress
**Start commit**: 4778b75
**Latest commit**: in-progress
**Start date**: 2026-05-11
**Completion date**:
**Estimated effort**: 3 days
**Actual effort**:

## Scope

M1 implements only Layer 0+1 scanning and the tracing foundation required by
`docs/DESIGN.md` v0.5 §3.1 and §10.

## Planned Work

- [x] Start M1 dev_memory and branch state.
- [ ] Implement tracing logger foundation.
- [ ] Implement plain text and gzip buildlog scanning.
- [ ] Implement phase marker recognition.
- [ ] Implement command boundary recognition with multiline command joining.
- [ ] Implement command parser support for `.rsp` files.
- [ ] Implement 11 diagnostic event categories.
- [ ] Implement cascade source/object suffix mapping.
- [ ] Add `docs/schemas/scan_result_v1.json`.
- [ ] Add 30+ unit tests and 5 scanner fixtures.
- [ ] Record M1 test report, test guide, and performance baseline.

## Key Change Details

Pending implementation commits.

## Test Status

| Test type | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Unit | 1 | 0 | 0 |
| Functional scan fixtures | 0 | 0 | 0 |
| Integration | 0 | 0 | 0 |

Initial baseline: `.venv/bin/pytest tests/` passed before implementation.

## Next Stage Entry

- Entry module after M1: `gbs_analyzer/quick_filter.py`
- Depends on this milestone: scan result schema and event output
- Gate: do not start M2 until the M1 PR is reviewed and merged.

## Token Performance Baseline

Pending. M1 must record 100 MB scan runtime in `perf_baselines/`.

## Notes for the Next Developer

1. Read `docs/DESIGN.md` §3.1 and §10.
2. Do not implement M2 quick filter logic in this milestone.
3. Keep M1 commits reviewable and tied to one feature block each.
