# Build Workflow Milestone BW-M1: gbs_build_skill

**Status**: completed
**Start commit**: 1b1e64d
**Latest implementation commit**: 0dd1a91
**Start date**: 2026-05-20
**Completion date**: 2026-05-20
**Estimated effort**: 1-1.5 days
**Actual effort**: 1 day

## Scope

BW-M1 creates `gbs_build_skill`, a small build runner product that invokes `gbs`, streams
stdout/stderr into one buildlog, and returns the original gbs exit code.

## Explicit Non-Scope

- Do not call `gbs_analyzer`.
- Do not create `gbs_workflow` or any Suggester.
- Do not modify `gbs_analyzer/`, `patterns/`, `templates/`, existing analyzer fixtures,
  `docs/DESIGN.md`, or `docs/CODEX_PROMPT.md`.
- Do not auto-apply patches, auto-retry builds, or modify source code.

## Completed Work

- [x] Implement `gbs_build_skill.runner` with streamed log writing and timeout handling.
- [x] Implement `python -m gbs_build_skill` CLI.
- [x] Add unit tests for command construction, log streaming, timeout handling, and exit passthrough.
- [x] Include `gbs_build_skill*` in package discovery so console-script pytest can import it after editable install.
- [x] Run existing analyzer regression tests to prove zero regression.
- [x] Run real ffmpeg gbs validation for one successful build and one depsolve failure.
- [x] Record validation data and final status.

## Key Change Details

### Change 1: Build runner and CLI
- **Files**: `gbs_build_skill/runner.py`, `gbs_build_skill/__main__.py`, `gbs_build_skill/__init__.py`
- **Reason**: `docs/build_workflow/DESIGN.md` §3 requires a build-only skill that invokes gbs,
  writes a combined compiler log, and returns the gbs exit code.
- **Source**: BW-M1 design scope.
- **Tests**: `tests/unit/test_build_runner.py`

### Change 2: Unit coverage for subprocess boundaries
- **Files**: `tests/unit/test_build_runner.py`
- **Reason**: Timeout, missing binary, stdout/stderr merge, and exit passthrough are BW-M1's main
  risk boundaries.
- **Source**: User BW-M1 test requirements.
- **Tests**: `pytest tests/unit/test_build_runner.py --cov=gbs_build_skill --cov-report=term-missing`

### Change 3: Package discovery for the new product
- **Files**: `pyproject.toml`
- **Reason**: `.venv/bin/pytest` uses the editable package metadata; without including
  `gbs_build_skill*`, the new tests cannot import the new package under the normal test command.
- **Source**: BW-M1 local test failure before package discovery was updated.
- **Tests**: Reinstalled editable package and reran unit tests successfully.

## Real gbs Validation

| Case | ffmpeg branch | Command result | Log size | Notes |
| --- | --- | --- | ---: | --- |
| Success | `tizen` | exit `0` | 98,715 bytes | Clean ffmpeg build completed and wrote RPMs. |
| Failure B depsolve | `real_smoke/B_20260519_171554` | exit `1` | 2,412 bytes | Log contains `nothing provides pkgconfig(nonexistent-pkg-xxxyzz)`. |

Validation logs were written locally under `/tmp/loganalysis_bw_m1/` and are not committed.

## Test Status

| Test type | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: |
| Unit | 6 | 0 | 0 |
| Regression | 352 | 0 | 0 |
| Real gbs validation | 2 | 0 | 0 |

Coverage:
- `gbs_build_skill`: 90% (target >= 85%)
- existing `gbs_analyzer`: 96.01% (no regression)

## Notes for the Next Developer

1. Read `docs/build_workflow/DESIGN.md`.
2. Confirm BW-M1 PR is reviewed and merged before starting BW-M2.
3. BW-M2 starts `gbs_workflow` and `DepsolveSuggester`; it may consume this runner but must not
   modify `gbs_analyzer`.
