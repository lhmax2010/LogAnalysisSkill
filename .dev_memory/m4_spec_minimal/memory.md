# Milestone M4: spec_minimal

**Status**: in-progress
**Start commit**: b600505
**Latest commit**: in-progress
**Start date**: 2026-05-15
**Completion date**:
**Estimated effort**: 1.5 days
**Actual effort**:

## Scope

M4 implements the Tizen spec minimal parser from `docs/DESIGN.md` v0.5 §6.1.
It also includes the approved M3 review follow-ups:

- Clarify README project-status wording.
- Clarify M3 test-report counts.
- Add generic_error gating combination tests where useful.

M4 must not implement M5 evidence collectors, `toolchain_detector`, `werror_analyzer`,
macro expansion, conditional evaluation, subpackage ownership resolution, or version
constraint semantic comparison.

## Planned Work

- [x] Start M4 dev_memory and branch state.
- [ ] Apply remaining M3 review follow-ups.
- [ ] Implement `gbs_analyzer/tizen/spec_minimal.py`.
- [ ] Implement `SpecMinimalParser.find_spec_file`.
- [ ] Implement BuildRequires, Patch, Source, and section extraction.
- [ ] Implement failure-context extraction from `+ ` shell command markers.
- [ ] Implement `get_parse_status` uncertainty markers and warnings.
- [ ] Add M4 prompt-warning template placeholder under `templates/`.
- [ ] Add 15+ unit tests and 5 functional spec fixtures.
- [ ] Record M4 test report, guide, and performance baseline.

## Key Change Details

Pending implementation commits.

## Test Status

| Test type | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Unit | 0 | 0 | 0 |
| Functional | 0 | 0 | 0 |
| M4 spec fixtures | 0 | 0 | 0 |

Initial baseline: `.venv/bin/pytest tests/` passed before M4 implementation.

## Next Stage Entry

- Entry modules after M4: `gbs_analyzer/evidence/*`
- Depends on this milestone: minimal spec metadata and parse-status uncertainty flags
- Gate: do not start M5 until the M4 PR is reviewed and merged.

## Token Performance Baseline

Pending. M4 must record spec extraction runtime under the 200ms target.

## Notes for the Next Developer

1. Read `docs/DESIGN.md` §6.1 before changing spec parsing behavior.
2. Do not implement M5 evidence collectors in this milestone.
3. Start M5 only after the M4 PR is reviewed and merged.
