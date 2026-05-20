# Build Workflow Milestone BW-M2: workflow + DepsolveSuggester

**Status**: completed
**Start commit**: d1b0bf2
**Latest implementation commit**: da3cbeb
**Start date**: 2026-05-20
**Completion date**: 2026-05-20
**Estimated effort**: 1 day
**Actual effort**: 1 day

## Scope

BW-M2 implements the `gbs_workflow` orchestrator, Suggester ABC, registry, and exactly one
Suggester: `DepsolveSuggester`.

## Explicit Non-Scope

- Do not implement LinkerMissing, LinkerUndef, PatchFailed, SpecScript, CompileError, or Fallback
  Suggesters; they belong to BW-M3.
- Do not add workflow E2E tests or Cline integration; they belong to BW-M4.
- Do not modify `gbs_analyzer/`, `gbs_build_skill/`, `patterns/`, `templates/`,
  `docs/DESIGN.md`, `docs/build_workflow/DESIGN.md`, or `docs/CODEX_PROMPT.md`.
- Do not auto-apply patches, auto-retry builds, modify source code, or branch behavior by confidence.

## Planned Work

- [x] Implement `gbs_workflow.workflow` main flow and `python -m gbs_workflow` CLI.
- [x] Call `gbs_build_skill` by Python import.
- [x] Call `gbs_analyzer` by subprocess CLI.
- [x] Implement `Suggestion`, `SuggesterBase`, registry, and `DepsolveSuggester`.
- [x] Write unit tests for workflow and depsolve suggester behavior.
- [x] Run real ffmpeg B depsolve workflow validation.
- [x] Verify generated depsolve patch can be applied with `git apply --check`.

## Key Change Details

### 1. Suggester ABC and Depsolve registry

- **Files**: `gbs_workflow/suggesters/base.py`,
  `gbs_workflow/suggesters/depsolve.py`, `gbs_workflow/suggesters/registry.py`
- **Reason**: BW-M2 needs a stable Suggester contract while registering only
  `DepsolveSuggester`.
- **Source**: `docs/build_workflow/DESIGN.md` §4.2-§4.4; user BW-M2 clarification.
- **Tests**: `tests/unit/suggesters/test_depsolve.py`

### 2. Workflow orchestration and CLI

- **Files**: `gbs_workflow/workflow.py`, `gbs_workflow/__main__.py`
- **Reason**: Provide the build -> analyzer -> suggestion -> summary flow without
  modifying source files or importing analyzer internals.
- **Source**: `docs/build_workflow/DESIGN.md` §4.1 and §4.6.
- **Tests**: `tests/unit/test_workflow.py`

### 3. Monorepo package discovery

- **Files**: `pyproject.toml`
- **Reason**: `python -m gbs_workflow` and editable-install tests must discover the
  new product package.
- **Source**: BW-M1 d005 precedent.
- **Tests**: `.venv/bin/python -m gbs_workflow --help`, unit tests under `.venv/bin/pytest`.

### 4. Real ffmpeg B depsolve validation

- **Files**: `.dev_memory/bw_m2_workflow/test_report.md`,
  `.dev_memory/bw_m2_workflow/perf_baselines/real_workflow_B_validation.md`
- **Reason**: BW-M2 requires one real workflow validation using the existing
  `real_smoke/B_20260519_171554` depsolve branch.
- **Source**: User BW-M2 instruction.
- **Tests**: Workflow exit 1, analyzer packet `direct_answer/fast_path/tier1`,
  generated patch passed `git apply --check`.

## Notes for the Next Developer

1. Read `docs/build_workflow/DESIGN.md` current revision.
2. Read `.dev_memory/bw_m1_build_skill/decisions.md` for build runner contracts.
3. Continue only within the BW-M2 scope above.
4. BW-M3 should add the remaining six Suggesters and must not reinterpret BW-M2
   as permission to auto-apply or retry builds.
