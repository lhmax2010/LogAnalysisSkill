# Restructure Phase 3: tizen-gbs-build-workflow

**Status**: completed
**Start date**: 2026-05-26
**Completed date**: 2026-05-26

## Scope

- Move workflow skill files under `tizen-gbs-build-workflow/`.
- Preserve Python package name `gbs_workflow`.
- Add a local `scripts/run_workflow.py` launcher with installed-mode imports and direct sibling discovery.
- Ensure analyzer subprocess calls can find sibling analyzer code in direct folder mode.

## Non-Scope

- Do not change workflow business logic or suggester behavior.
- Do not vendor build or analyzer code into the workflow skill.
- Do not move build or analyzer files again.
- Do not perform Phase 4 docs/integration cleanup.

## Key Changes

1. Moved the workflow skill publish folder to `tizen-gbs-build-workflow/`.
   - Files: `tizen-gbs-build-workflow/SKILL.md`, `tizen-gbs-build-workflow/scripts/gbs_workflow/*`
   - Reason: Complete the three-skill publish layout for build, analyzer, and workflow.

2. Added the direct workflow launcher.
   - File: `tizen-gbs-build-workflow/scripts/run_workflow.py`
   - Reason: Support direct sibling-folder usage without pip installing the three packages.

3. Added analyzer subprocess environment support.
   - File: `tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py`
   - Reason: Direct mode needs `python -m gbs_analyzer` child processes to inherit sibling scripts paths through `PYTHONPATH`.

4. Updated package discovery and type-check paths.
   - Files: `pyproject.toml`, `.github/workflows/ci.yml`
   - Reason: Keep installed mode and CI working after the workflow package moved.

## Validation Summary

- Installed mode: clean uv venv install from repo, then `python -m gbs_workflow` from `/tmp` passed.
- Installed mode real failure: ffmpeg `real_smoke/B_20260519_171554` produced depsolve analyzer output and a depsolve advisory suggestion.
- Direct mode isolation: system Python with `PYTHONPATH=` could not import `gbs_workflow`, `gbs_build_skill`, or `gbs_analyzer` before launcher execution.
- Direct mode real failure: copied only the three skill folders to `/tmp`, ran `run_workflow.py`, and produced the same depsolve analyzer output and advisory suggestion.
- Env-var discovery: non-sibling folders with `TIZEN_GBS_BUILD_SKILL_DIR` and `TIZEN_GBS_LOG_ANALYSIS_SKILL_DIR` reached workflow CLI help.
- Full regression: `401 passed`, coverage `96.01%`.
