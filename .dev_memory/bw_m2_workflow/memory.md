# Build Workflow Milestone BW-M2: workflow + DepsolveSuggester

**Status**: in-progress
**Start commit**: d1b0bf2
**Latest commit**: d1b0bf2
**Start date**: 2026-05-20
**Completion date**:
**Estimated effort**: 1 day
**Actual effort**:

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

- [ ] Implement `gbs_workflow.workflow` main flow and `python -m gbs_workflow` CLI.
- [ ] Call `gbs_build_skill` by Python import.
- [ ] Call `gbs_analyzer` by subprocess CLI.
- [ ] Implement `Suggestion`, `SuggesterBase`, registry, and `DepsolveSuggester`.
- [ ] Write unit tests for workflow and depsolve suggester behavior.
- [ ] Run real ffmpeg B depsolve workflow validation.
- [ ] Verify generated depsolve patch can be applied with `git apply --check`.

## Notes for the Next Developer

1. Read `docs/build_workflow/DESIGN.md` current revision.
2. Read `.dev_memory/bw_m1_build_skill/decisions.md` for build runner contracts.
3. Continue only within the BW-M2 scope above.
