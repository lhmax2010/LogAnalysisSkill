# P4.9 step-0 progress

## Current state

- Status: v2.0-FROZEN; implementation commits ① and ② complete.
- Contract body: `../../p49-step0-design-v2.0-FROZEN.md`.
- Mechanical attribution audit: `../../review/p49-step0-symbol-audit.md`.
- Audited scope: only modules and symbols that step-0 will actually modify.
- Latest result: 42/42 OK, 0 MISMATCH, 0 INCOMPLETE after commit ② moves.
- Commit ① command output and validation evidence was mistakenly written under
  the repository-root `.dev_memory/`. It is now relocated without content changes as
  [`commit1-evidence.md`](commit1-evidence.md); no root-side duplicate remains.

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

## Commit ② L1 independence evidence

### Negative A: state imports workspace

Temporary violation: add `import tizen_ci_shared.workspace` to
`tizen_ci_shared/state/db.py`.

Command:

```bash
.venv/bin/lint-imports
```

Output:

```text
=============
Import Linter
=============

---------
Contracts
---------

Analyzed 32 files, 61 dependencies.
-----------------------------------

shared internal layers: L1 -> L0 -> types BROKEN
shared must not import orchestration KEPT
shared L1 domains are independent BROKEN
shared L0 primitives are independent KEPT

Contracts: 2 kept, 2 broken.


----------------
Broken contracts
----------------

shared internal layers: L1 -> L0 -> types
-----------------------------------------

tizen_ci_shared.state is not allowed to import tizen_ci_shared.workspace:

- tizen_ci_shared.state.db -> tizen_ci_shared.workspace (l.16)


shared L1 domains are independent
---------------------------------

tizen_ci_shared.state is not allowed to import tizen_ci_shared.workspace:

- tizen_ci_shared.state.db -> tizen_ci_shared.workspace (l.16)

exit_code=1
```

The temporary import was removed.

### Negative B: workspace imports classify

Temporary violation: add `import tizen_ci_shared.classify` to
`tizen_ci_shared/workspace/__init__.py`.

Command:

```bash
.venv/bin/lint-imports
```

Output:

```text
=============
Import Linter
=============

---------
Contracts
---------

Analyzed 32 files, 61 dependencies.
-----------------------------------

shared internal layers: L1 -> L0 -> types BROKEN
shared must not import orchestration KEPT
shared L1 domains are independent BROKEN
shared L0 primitives are independent KEPT

Contracts: 2 kept, 2 broken.


----------------
Broken contracts
----------------

shared internal layers: L1 -> L0 -> types
-----------------------------------------

tizen_ci_shared.workspace is not allowed to import tizen_ci_shared.classify:

- tizen_ci_shared.workspace -> tizen_ci_shared.classify (l.5)


shared L1 domains are independent
---------------------------------

tizen_ci_shared.workspace is not allowed to import tizen_ci_shared.classify:

- tizen_ci_shared.workspace -> tizen_ci_shared.classify (l.5)

exit_code=1
```

The temporary import was removed.

### Restored positive check

```text
=============
Import Linter
=============

---------
Contracts
---------

Analyzed 32 files, 60 dependencies.
-----------------------------------

shared internal layers: L1 -> L0 -> types KEPT
shared must not import orchestration KEPT
shared L1 domains are independent KEPT
shared L0 primitives are independent KEPT

Contracts: 4 kept, 0 broken.
exit_code=0
```

The commit ① L1 deferral is now closed. The L0 independence negative control
remains explicitly bound to commit ③; step-0 cannot be declared complete until
that run records its real exit-1 output here.

## Commit ② validation

- Workspace authority: both marker constants, marker JSON construction, marker
  path construction, and the marker-preserving `git clean` exclusions now live
  in `tizen_ci_shared.workspace`.
- Marker parity: the same real-Git fixture before and after migration produced
  identical normalized JSON and the same marker path suffix
  `iter_7/.ci_triage_workdir`; `cmp` exited 0.
- Move equivalence: AST comparisons passed for 13 moved workspace definitions
  and `discover_sibling_pythonpath`; the moved classifier file passed a bytewise
  `cmp` against its pre-move content.
- Targeted regression: `113 passed in 4.61s`.
- Full regression: 847 collected, `846 passed, 1 skipped in 21.97s`, matching
  the commit ① baseline.
- Mypy: `Success: no issues found in 99 source files`.
- Py_compile: exit 0 for all Python files under `tizen_ci_shared` and
  `ci_triage`.
- Ruff: all tracked Python files and all task Python files pass `ruff check`.
- Import Linter: `4 kept, 0 broken`, exit 0 after restoring both negative
  probes.
- Symbol audit: `42 OK, 0 MISMATCH, 0 INCOMPLETE`, exit 0.
- Frozen canonical/history comparison: `cmp` exit 0 after revisions 2 and 3.
- `quickbuild_http.py` remains a one-line docstring-only placeholder for
  commit ③.
