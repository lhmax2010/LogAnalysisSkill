# Build Workflow Milestone BW-M4: E2E + Cline integration

**Status**: completed
**Start commit**: 1740233
**Start date**: 2026-05-20
**Completion date**: 2026-05-20
**Estimated effort**: 1 day
**Actual effort**: 1 day

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

- [x] Add workflow E2E tests for A/B/C/D/unknown packets.
- [x] Add Cline `build_workflow.json` and update integration README.
- [x] Run real ffmpeg A/B/C/D workflow validation.
- [x] Record unknown fallback validation.
- [x] Confirm compile-error semantic_class field behavior.
- [x] Run full regression gates and open PR.

## Key Change Details

### 1. Workflow E2E routing tests

- **Files**: `tests/e2e/test_build_workflow_e2e.py`
- **Reason**: BW-M4 acceptance requires A/B/C/D/unknown workflow routing coverage.
- **Source**: `docs/build_workflow/DESIGN.md` §7; BW-M3 review.
- **Tests**: 6 E2E tests cover linker_undef, depsolve existing BuildRequires,
  patch failed, rpm_phase, unknown fallback, and compile semantic class.

### 2. Structured GBS failure log selection

- **Files**: `gbs_workflow/workflow.py`, `tests/unit/test_workflow.py`
- **Reason**: Real D validation showed wrapper `compiler.log` can rank the final
  `<gbs>some packages failed` line above the real `%install` failure.
- **Source**: BW-M4 real D validation.
- **Tests**: Unit test verifies workflow passes the referenced
  `/logs/fail/.../log.txt` to analyzer when present.

### 3. CompileError semantic class lookup

- **Files**: `gbs_workflow/suggesters/compile_error.py`,
  `tests/e2e/test_build_workflow_e2e.py`
- **Reason**: Real analyzer packets store `semantic_class` on
  `root_cause_candidates[0]`, not on `primary_error`.
- **Source**: BW-M4 review follow-up.
- **Tests**: E2E compile packet test asserts `undeclared_identifier` appears in
  the generated suggestion.

### 4. Cline build workflow example

- **Files**: `integrations/cline/build_workflow.json`,
  `integrations/cline/README.md`, `integrations/README.md`
- **Reason**: BW-M4 includes example Cline contract for running the whole workflow.
- **Source**: `docs/build_workflow/DESIGN.md` §5.
- **Tests**: JSON syntax checked with `python3 -m json.tool`.
