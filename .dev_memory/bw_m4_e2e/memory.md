# Build Workflow Milestone BW-M4: E2E + Cline integration

**Status**: in-progress
**Start commit**: 1740233
**Start date**: 2026-05-20
**Completion date**:
**Estimated effort**: 1 day
**Actual effort**:

## Scope

BW-M4 is the v0.1 workflow acceptance milestone:

- Add workflow E2E tests covering A/B/C/D/unknown suggestion routing.
- Add Cline build workflow integration example and documentation.
- Run real ffmpeg A/B/C/D workflow validation and record artifacts in dev_memory.
- Confirm `CompileErrorSuggester` semantic class packet field behavior.

## Explicit Non-Scope

- No analyzer/build-skill behavior changes.
- No auto-apply or auto-retry implementation.
- No Compiling Agent build workflow integration unless design explicitly requires it later.
- No modifications to `docs/DESIGN.md`, `docs/build_workflow/DESIGN.md`, or `docs/CODEX_PROMPT.md`.

## Planned Work

- [ ] Add workflow E2E tests for A/B/C/D/unknown packets.
- [ ] Add Cline `build_workflow.json` and update integration README.
- [ ] Run real ffmpeg A/B/C/D workflow validation.
- [ ] Record unknown fallback validation.
- [ ] Confirm compile-error semantic_class field behavior.
- [ ] Run full regression gates and open PR.
