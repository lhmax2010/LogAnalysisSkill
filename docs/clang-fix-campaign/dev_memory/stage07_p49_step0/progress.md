# P4.9 step-0 progress

## Current state

- Status: freeze candidate after v1.12 scope convergence.
- Contract body: `../../p49-step0-design-v1.0-draft.md`.
- Mechanical attribution audit: `../../review/p49-step0-symbol-audit.md`.
- Audited scope: only modules and symbols that step-0 will actually modify.
- Latest result: 39/39 OK, 0 MISMATCH, 0 INCOMPLETE.

## Deferred TODO: GBS report extraction

`ci_triage/gbs_report.py` is intentionally unchanged and outside the step-0
inventory and completeness guard. Its entire extraction is deferred to the
triage-report batch so fetch and parse can be designed together.

That batch must consume all of these constraints before implementation:

1. Any raw fetch result must carry the real parser inputs, including
   `iframe_url` and `build_id`.
2. The migration unit is the complete dependency closure, including
   `QuickBuildError`, HTTP primitives, iframe discovery, and parser inputs.
3. Target-state AST checks run only after refactoring; they must not be applied
   to the pre-split implementation.
4. If a symbol remains in scope while awaiting a new shape, an explicit
   `existing` / `to-be-created` / `to-be-refactored` audit state machine is
   required. Transitional states must be counted and have a mandatory
   promotion gate.
5. A composition shell, if retained, may only call the approved raw fetch,
   parse, type-construction, and return operations. Otherwise split directly.
6. Re-evaluate the ownership of `GbsReportPackage`, `GbsReport`,
   `find_iframe_src`, `_IframeParser`, and `_attrs_to_map` from the complete
   measured call graph; do not pre-create `htmlutil` without that evidence.
7. The gbs_report inventory and its public-surface completeness guard must be
   introduced or removed in the same commit.

The alternative `deferred/out-of-scope` audit status is not implemented for
step-0. Reconsider it only when a real symbol is still inside an active
extraction scope but cannot yet satisfy its target form.
