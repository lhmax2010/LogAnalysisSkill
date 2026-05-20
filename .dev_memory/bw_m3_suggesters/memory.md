# Build Workflow Milestone BW-M3: remaining Suggesters

**Status**: completed
**Start commit**: 461850e
**Start date**: 2026-05-20
**Completion date**: 2026-05-20
**Estimated effort**: 1.5 days
**Actual effort**: 1 day

## Scope

BW-M3 extends `gbs_workflow` suggestion coverage after BW-M2:

- Add guard to `DepsolveSuggester` for dependencies already declared in the spec.
- Add `LinkerMissingSuggester`, `LinkerUndefSuggester`, `PatchFailedSuggester`,
  `SpecScriptSuggester`, `CompileErrorSuggester`, and `FallbackSuggester`.
- Register all v0.1 Suggesters while preserving primary-error-only routing.
- Keep all non-depsolve suggestions advisory except `LinkerMissingSuggester`, which may emit low-confidence candidate patch guidance.

## Explicit Non-Scope

- No BW-M4 E2E tests or Cline integration.
- No auto-apply, auto-retry, source-code edits, or multi-error behavior.
- No modifications to `gbs_analyzer/`, `gbs_build_skill/`, `patterns/`, `templates/`,
  `docs/DESIGN.md`, `docs/build_workflow/DESIGN.md`, or `docs/CODEX_PROMPT.md`.

## Planned Work

- [x] Add depsolve existing-BuildRequires advisory guard.
- [x] Add advisory Suggester helpers and non-patch Suggesters.
- [x] Add low-confidence linker missing BuildRequires candidate suggestion.
- [x] Register all BW-M3 Suggesters with fallback last.
- [x] Add unit tests for each Suggester and workflow routing.
- [x] Run full regression gates.

## Key Change Details

### 1. Depsolve duplicate BuildRequires guard

- **Files**: `gbs_workflow/suggesters/depsolve.py`,
  `tests/unit/suggesters/test_depsolve.py`
- **Reason**: BW-M2 real B validation showed that depsolve may mean "declared
  dependency unavailable" rather than "missing BuildRequires".
- **Source**: BW-M2 review.
- **Tests**: Existing dependency emits advisory guidance with no duplicate patch.

### 2. Advisory Suggester set

- **Files**: `gbs_workflow/suggesters/linker_undef.py`,
  `gbs_workflow/suggesters/patch_failed.py`,
  `gbs_workflow/suggesters/spec_script.py`,
  `gbs_workflow/suggesters/compile_error.py`,
  `gbs_workflow/suggesters/fallback.py`,
  `gbs_workflow/suggesters/_common.py`
- **Reason**: BW-M3 needs coverage for the remaining v0.1 error kinds without
  attempting source edits.
- **Source**: `docs/build_workflow/DESIGN.md` §4.5.
- **Tests**: `tests/unit/suggesters/test_bw_m3_suggesters.py`

### 3. LinkerMissing low-confidence patch candidate

- **Files**: `gbs_workflow/suggesters/linker_missing.py`
- **Reason**: v0.1 allows a low-confidence candidate BuildRequires patch for
  missing `-l` libraries, with explicit repository/path risks.
- **Source**: `docs/build_workflow/DESIGN.md` §4.5.
- **Tests**: Generated `libssl-devel` candidate patch passes `git apply --check`.

### 4. Full v0.1 registry

- **Files**: `gbs_workflow/suggesters/registry.py`,
  `gbs_workflow/suggesters/__init__.py`
- **Reason**: BW-M3 registers all v0.1 Suggesters while keeping Fallback last and
  scoped to unsupported primary kinds.
- **Source**: `docs/build_workflow/DESIGN.md` §4.5.
- **Tests**: Registry order and known/unknown routing tests.

## Notes for the Next Developer

1. Read `docs/build_workflow/DESIGN.md` current revision.
2. Read `.dev_memory/bw_m2_workflow/known_issues.md` for the depsolve duplicate guard trigger.
3. BW-M4 remains responsible for real E2E fixtures and Cline examples.
