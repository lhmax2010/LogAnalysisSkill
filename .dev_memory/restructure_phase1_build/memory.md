# Restructure Phase 1: tizen-gbs-build

**Status**: completed
**Start date**: 2026-05-25
**Completed date**: 2026-05-25

## Scope

- Move build-only skill files under `tizen-gbs-build/`.
- Preserve Python package name `gbs_build_skill`.
- Add a local `scripts/run_build.py` launcher that supports both installed-package and direct skill-folder usage.
- Keep analyzer and workflow source locations unchanged in this phase.

## Non-Scope

- Do not move `gbs_analyzer`.
- Do not move `gbs_workflow`.
- Do not implement workflow sibling discovery.
- Do not change analyzer pattern data or analysis behavior.

## Key Changes

1. Moved the build skill publish folder to `tizen-gbs-build/`.
   - Files: `tizen-gbs-build/SKILL.md`, `tizen-gbs-build/scripts/gbs_build_skill/*`
   - Reason: Match the repository-as-published-skill structure while keeping the Python package name stable.

2. Added the direct local launcher.
   - File: `tizen-gbs-build/scripts/run_build.py`
   - Reason: Support direct skill-folder usage without requiring pip install.

3. Updated package discovery.
   - File: `pyproject.toml`
   - Reason: Keep `gbs_build_skill` importable from `tizen-gbs-build/scripts/` for workflow and tests.

4. Moved developer build-skill notes out of the publish folder.
   - File: `docs/build_workflow/build_skill.md`
   - Reason: Keep `tizen-gbs-build/` clean with only `SKILL.md` and `scripts/`.

## Validation Summary

- Installed mode: clean uv venv install from repo, then `python -m gbs_build_skill --help` from `/tmp` passed.
- Installed mode workflow import: `from gbs_workflow.workflow import run_workflow` and `from gbs_build_skill.runner import BuildOptions` passed from `/tmp`.
- Direct folder mode: copied only `tizen-gbs-build/` to `/tmp`, cleared `PYTHONPATH`, and ran `scripts/run_build.py --help` from `/tmp`; passed.
- Focused build tests: `7 passed`.
- Full regression: `399 passed`, coverage `96.01%`.
