# Memory for build_skill v0.2 Phase B

## Status

Completed; waiting for review.

## Scope

Switch `gbs_workflow` to consume `BuildResult.analysis_log_path` from
`gbs_build_skill` v0.2 Phase A, then remove workflow's duplicate
`select_analysis_log` implementation.

Strictly out of scope: build skill changes, analyzer changes, pattern changes,
suggester changes, and any new workflow feature.

## Baseline

- Branch: `feature/build-skill-v0.2-phase-b`
- Starting commit: `4e9ef15` (`Merge pull request #28`)
- Design baseline: `docs/build_skill_v0.2_design.md` §13

## Progress

- Confirmed references to `select_analysis_log` and workflow-local
  `GBS_FAILURE_LOG_PATTERN` were limited to workflow source/tests when ignoring
  local build artifacts.
- Updated workflow failure path to use `build_result.analysis_log_path` with a
  defensive fallback to `build_result.log_path`.
- Removed workflow-local log-selection helper and tests for the removed helper.
- Updated workflow tests to verify both the new `analysis_log_path` behavior and
  the fallback path when fake/legacy build results omit it.
- Validated A/B/C/D/E real ffmpeg workflow scenarios with no routing regression.

## Validation Summary

- Focused workflow tests: `12 passed`.
- Full regression with coverage: `408 passed`, coverage `96.01%`.
- Ruff and import-order checks: pass.
- Mypy over build/analyzer/workflow packages: pass.
- Real ffmpeg A/B/C/D/E workflow routes all matched BW-M4 expectations.
