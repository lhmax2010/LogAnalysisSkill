# Memory for build_skill v0.2 Phase A

## Status

Completed; waiting for review.

## Scope

Implement build skill v0.2 Phase A from `docs/build_skill_v0.2_design.md`:

- add failure log path extraction from compiler log A
- add `BuildResult.failure_log_path`, `analysis_log_path`, and `package_name`
- add `--src-dir` CLI parameter using existing `BuildOptions.cwd`
- print structured stderr summaries
- update `tizen-gbs-build/SKILL.md`

Strictly out of scope: workflow changes, analyzer changes, pattern changes, `pyproject.toml`, and any Phase B `select_analysis_log` removal.

## Baseline

- Branch: `feature/build-skill-v0.2-phase-a`
- Starting commit: `47bb5b2` (`Merge pull request #27`)
- Design baseline: `docs/build_skill_v0.2_design.md`

## Completed Changes

- Added structured failure log extraction to `gbs_build_skill.runner` using the
  v0.2 design regex.
- Appended `failure_log_path`, `analysis_log_path`, and `package_name` to
  `BuildResult` while preserving all v0.1 fields.
- Added `--src-dir` CLI support through existing `BuildOptions.cwd`; missing
  source directories return exit code `2`.
- Added structured stderr summaries for success, failure with B log, and failure
  without B log.
- Updated `tizen-gbs-build/SKILL.md` with `--src-dir`, analysis-log metadata, and
  an ffmpeg failure-log example.
- Left `tizen-gbs-build-workflow/`, analyzer code, patterns, and `pyproject.toml`
  unchanged.

## Validation Summary

- Focused build tests: `15 passed`.
- Focused workflow compatibility tests: included in `tests/unit/test_workflow.py`,
  combined focused run `28 passed`.
- Full regression with coverage: `409 passed`, coverage `96.01%`.
- Ruff and import-order checks: pass.
- Mypy over build/analyzer/workflow packages: pass.
- Real ffmpeg success (`tizen`): exit `0`, `analysis_log_path == log_path`,
  `failure_log_path is None`.
- Real ffmpeg failure (`real_smoke/E_compile_20260520`): exit `1`, B path found,
  file exists, package `ffmpeg-8.0.1-0`.
- Fallback no-B-log scenario: exit `9`, `analysis_log_path == log_path`,
  `failure_log_path is None`.
