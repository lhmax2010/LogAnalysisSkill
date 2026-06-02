# PS-M6 Workflow Patch Context

Status: completed, waiting for review.

## Scope

PS-M6 adds a non-fatal optional workflow stage after build failure analysis and
suggestion generation. When the analyzer packet primary error is a compiler
diagnostic, workflow calls `gbs_patch_suggest` with the existing
`analyzer_output/evidence_packet.json` and writes patch context under
`.gbs_workflow/patch_context/`.

## Boundaries

- Workflow does not import `gbs_patch_suggest`; it invokes it by subprocess.
- Workflow does not call any LLM and does not generate/apply patches.
- Analyzer, build skill, patch-suggest core logic, Suggesters, and patterns were
  not changed.
- Existing build/analyze/suggest order, verdict behavior, and exit codes remain
  unchanged.

## Implementation Summary

- Added optional `PatchContextResult` and `maybe_write_patch_context()`.
- Added `TIZEN_GBS_PATCH_SUGGEST_SKILL_DIR` / sibling discovery in the workflow
  direct-folder launcher.
- Added `patch_context/context.md` link and non-fatal error reporting to
  `workflow_summary.md`.
- Added `patch_context_md` to the downstream token estimate when the context
  file exists.

## Validation

- `pytest tests/unit/test_workflow.py -q`: 18 passed.
- `pytest tests/e2e/test_build_workflow_e2e.py -q`: 7 passed.
- `ruff check tizen-gbs-build-workflow tests/unit/test_workflow.py`: passed.
- `mypy tizen-gbs-build-workflow/scripts/gbs_workflow`: passed.
- `pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95`: 446 passed,
  coverage 95.97%.
