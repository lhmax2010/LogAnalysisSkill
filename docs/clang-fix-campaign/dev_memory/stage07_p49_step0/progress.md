# P4.9 step-0 progress

## Current state

- Status: v2.0-FROZEN; implementation commit ① awaits post-freeze approval.
- Contract body: `../../p49-step0-design-v2.0-FROZEN.md`.
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

## Step-0 implementation TODOs

- Mechanize the design-table to symbol-audit inventory diff no later than
  commit ③. Until then, retain a manual row-by-row reconciliation after every
  attribution change.
- `root-layers` and `skill-independence` are target templates, not active
  step-0 contracts. The first skill extraction batch must enable them, verify
  the `containers` syntax against pinned `import-linter==2.3`, and add the
  corresponding cross-skill negative control.
- Commit ① lands four active shared contracts with four one-line placeholder
  modules. It runs the shared-layers and shared-no-uplink negative controls;
  L1 independence is bound to commit ② and L0 independence to commit ③. Each
  deferred control must record the real exit-1 output in this memory tree.
