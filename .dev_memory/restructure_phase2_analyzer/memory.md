# Restructure Phase 2: tizen-gbs-log-analysis

**Status**: completed
**Start date**: 2026-05-25
**Completed date**: 2026-05-25

## Scope

- Move analyzer-only skill files under `tizen-gbs-log-analysis/`.
- Preserve Python package name `gbs_analyzer`.
- Keep `patterns/` inside the analyzer package so hotfix_003 `Path(__file__)` anchors keep working.
- Add a local `scripts/run_analyzer.py` launcher that supports installed-package and direct skill-folder usage.
- Keep build and workflow source locations unchanged in this phase.

## Non-Scope

- Do not move `gbs_workflow`.
- Do not implement workflow sibling discovery.
- Do not change analyzer pattern contents or analysis behavior.
- Do not modify build skill behavior.

## Key Changes

1. Moved the analyzer skill publish folder to `tizen-gbs-log-analysis/`.
   - Files: `tizen-gbs-log-analysis/SKILL.md`, `tizen-gbs-log-analysis/scripts/gbs_analyzer/*`
   - Reason: Match the repository-as-published-skill structure while keeping `gbs_analyzer` import paths stable.

2. Preserved package-relative pattern data.
   - Files: `tizen-gbs-log-analysis/scripts/gbs_analyzer/patterns/*`
   - Reason: Keep hotfix_003 `Path(__file__)` pattern loading valid in installed and direct skill-folder modes.

3. Added the direct local analyzer launcher.
   - File: `tizen-gbs-log-analysis/scripts/run_analyzer.py`
   - Reason: Support direct skill-folder usage without requiring pip install.

4. Updated package discovery.
   - File: `pyproject.toml`
   - Reason: Keep `gbs_analyzer` importable from `tizen-gbs-log-analysis/scripts/` for tests and workflow.

## Validation Summary

- Installed mode: clean uv venv install from repo, then `python -m gbs_analyzer analyze ...` from `/tmp` passed.
- Installed mode package data: `site-packages/gbs_analyzer/patterns/` contains `README.md`, `error_semantics.yaml`, `gbs_errors.yaml`, and `schema.json`.
- Direct folder mode: copied only `tizen-gbs-log-analysis/` to `/tmp`, cleared `PYTHONPATH`, and ran `scripts/run_analyzer.py analyze ...` from `/tmp`; passed.
- Real av_temp_lss log: both modes produced Top-1 `compiler libavcodec/utils.c:109`.
- Workflow analyzer import dependency: `gbs_analyzer.tizen.spec_minimal.SpecMinimalParser` import passed.
- Workflow analyzer subprocess entry: `python -m gbs_analyzer analyze ...` from `/tmp` passed after editable install.
- Full regression: `399 passed`, coverage `96.01%`.
