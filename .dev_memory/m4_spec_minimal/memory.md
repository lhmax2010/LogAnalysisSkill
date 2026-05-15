# Milestone M4: spec_minimal

**Status**: completed
**Start commit**: b600505
**Latest implementation commit**: 3db8153
**Start date**: 2026-05-15
**Completion date**: 2026-05-15
**Estimated effort**: 1.5 days
**Actual effort**: 1 day

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
- [x] Apply remaining M3 review follow-ups.
- [x] Implement `gbs_analyzer/tizen/spec_minimal.py`.
- [x] Implement `SpecMinimalParser.find_spec_file`.
- [x] Implement BuildRequires, Patch, Source, and section extraction.
- [x] Implement failure-context extraction from `+ ` shell command markers.
- [x] Implement `get_parse_status` uncertainty markers and warnings.
- [x] Add M4 prompt-warning template placeholder under `templates/`.
- [x] Add 15+ unit tests and 5 functional spec fixtures.
- [x] Record M4 test report, guide, and performance baseline.

## Key Change Details

### Change 1: M3 review follow-ups
- **Files**: `README.md`, `.dev_memory/m3_rank_causes/test_report.md`, `tests/unit/test_semantic_classifier.py`
- **Reason**: M3 review requested README project-status wording, clearer test-count semantics, and generic_error gate combination coverage.
- **Source**: M3 review follow-up
- **Tests**: `tests/unit/test_semantic_classifier.py`

### Change 2: minimal spec parser
- **Files**: `gbs_analyzer/tizen/spec_minimal.py`, `gbs_analyzer/tizen/__init__.py`, `templates/spec_parse_uncertainty.md`, `tests/unit/test_spec_minimal.py`
- **Reason**: M4 requires `SpecMinimalParser` with six public methods plus parse-status uncertainty markers.
- **Source**: v0.5 §6.1
- **Tests**: 17 spec parser unit tests.

### Change 3: spec fixtures
- **Files**: `tests/fixtures/spec_*`, `tests/functional/test_spec_fixtures.py`
- **Reason**: M4 DoD requires 5 spec extraction successes and runtime under 200ms.
- **Source**: v0.5 §9.4
- **Tests**: 5/5 fixtures extract BuildRequires, Source, section text, failure context, and parse status.

## Test Status

| Test type | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Unit | 138 | 0 | 0 |
| Functional | 16 | 0 | 0 |
| M4 spec fixture cases | 5/5 | 0 | 0 |

Full validation: `.venv/bin/pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80`
passed with 154 tests and 98.49% coverage.

M4-specific unit tests: 17 (`tests/unit/test_spec_minimal.py`).

## Next Stage Entry

- Entry modules after M4: `gbs_analyzer/evidence/*`
- Depends on this milestone: minimal spec metadata and parse-status uncertainty flags
- Gate: do not start M5 until the M4 PR is reviewed and merged.

## Token Performance Baseline

- Spec extraction 5-fixture batch mean runtime: 0.7204ms (target < 200ms)
- Spec extraction per evaluation mean runtime: 0.1441ms
- Spec extraction success rate on M4 fixtures: 100%
- Baseline: `.dev_memory/m4_spec_minimal/perf_baselines/spec_5_fixtures.json`

## Notes for the Next Developer

1. Read `docs/DESIGN.md` §6.1 before changing spec parsing behavior.
2. Do not implement M5 evidence collectors in this milestone.
3. Start M5 only after the M4 PR is reviewed and merged.
