# Build Workflow Milestone BW-M3: remaining Suggesters

**Status**: in-progress
**Start commit**: 461850e
**Start date**: 2026-05-20
**Completion date**:
**Estimated effort**: 1.5 days
**Actual effort**:

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

- [ ] Add depsolve existing-BuildRequires advisory guard.
- [ ] Add advisory Suggester helpers and non-patch Suggesters.
- [ ] Add low-confidence linker missing BuildRequires candidate suggestion.
- [ ] Register all BW-M3 Suggesters with fallback last.
- [ ] Add unit tests for each Suggester and workflow routing.
- [ ] Run full regression gates.

## Notes for the Next Developer

1. Read `docs/build_workflow/DESIGN.md` current revision.
2. Read `.dev_memory/bw_m2_workflow/known_issues.md` for the depsolve duplicate guard trigger.
3. BW-M4 remains responsible for real E2E fixtures and Cline examples.
