# Build Workflow Milestone BW-M1: gbs_build_skill

**Status**: in-progress
**Start commit**: 1b1e64d
**Latest commit**: 1b1e64d
**Start date**: 2026-05-20
**Completion date**:
**Estimated effort**: 1-1.5 days
**Actual effort**:

## Scope

BW-M1 creates `gbs_build_skill`, a small build runner product that invokes `gbs`, streams
stdout/stderr into one buildlog, and returns the original gbs exit code.

## Explicit Non-Scope

- Do not call `gbs_analyzer`.
- Do not create `gbs_workflow` or any Suggester.
- Do not modify `gbs_analyzer/`, `patterns/`, `templates/`, existing analyzer fixtures,
  `docs/DESIGN.md`, or `docs/CODEX_PROMPT.md`.
- Do not auto-apply patches, auto-retry builds, or modify source code.

## Planned Work

- [ ] Implement `gbs_build_skill.runner` with streamed log writing and timeout handling.
- [ ] Implement `python -m gbs_build_skill` CLI.
- [ ] Add unit tests for command construction, log streaming, timeout handling, and exit passthrough.
- [ ] Run existing analyzer regression tests to prove zero regression.
- [ ] Run real ffmpeg gbs validation for one successful build and one depsolve failure.
- [ ] Record validation data and final status.

## Test Targets

| Test type | Target |
| --- | --- |
| Unit | `gbs_build_skill` coverage >= 85% |
| Regression | Existing LogAnalysisSkill tests pass |
| Real gbs success | Clean ffmpeg build invocation writes log and returns gbs exit code |
| Real gbs failure | `real_smoke/B_20260519_171554` depsolve failure writes log and returns gbs exit code |

## Notes for the Next Developer

1. Read `docs/build_workflow/DESIGN.md`.
2. Confirm this milestone stays limited to `gbs_build_skill` plus tests/dev_memory.
3. Continue only after BW-M1 PR review is complete.
