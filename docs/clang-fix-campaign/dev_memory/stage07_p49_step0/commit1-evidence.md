# P4.9 Step-0 Progress

## Commit 1 Scope

- Frozen authority: `docs/clang-fix-campaign/p49-step0-design-v2.1-FROZEN.md`.
- Baseline command without repository package roots failed during collection with
  14 `ModuleNotFoundError: ci_triage` errors. The reproducible repository command is:

  ```bash
  PYTHONPATH=tizen-gbs-build/scripts:tizen-gbs-log-analysis/scripts:tizen-gbs-build-workflow/scripts:tizen-gbs-patch-suggest/scripts:tizen-ci-triage/scripts .venv/bin/pytest
  ```

- Pre-change baseline: `846 passed, 1 skipped in 17.94s` (847 collected).

## Import Linter Version

Command:

```bash
.venv/bin/python -m pip show import-linter
```

Relevant output:

```text
Name: import-linter
Version: 2.3
```

## Positive Contract Check

Command:

```bash
PYTHONPATH=tizen-ci-shared/scripts:tizen-ci-triage/scripts .venv/bin/lint-imports
```

Output:

```text
=============
Import Linter
=============

---------
Contracts
---------

Analyzed 32 files, 54 dependencies.
-----------------------------------

shared internal layers: L1 -> L0 -> types KEPT
shared must not import orchestration KEPT
shared L1 domains are independent KEPT
shared L0 primitives are independent KEPT

Contracts: 4 kept, 0 broken.
LINT_IMPORTS_EXIT=0
```

## Negative A: shared-layers

Temporary violation: add `import tizen_ci_shared.state` to
`tizen_ci_shared/types.py`.

Output:

```text
=============
Import Linter
=============

---------
Contracts
---------

Analyzed 32 files, 55 dependencies.
-----------------------------------

shared internal layers: L1 -> L0 -> types BROKEN
shared must not import orchestration KEPT
shared L1 domains are independent KEPT
shared L0 primitives are independent KEPT

Contracts: 3 kept, 1 broken.


----------------
Broken contracts
----------------

shared internal layers: L1 -> L0 -> types
-----------------------------------------

tizen_ci_shared.types is not allowed to import tizen_ci_shared.state:

- tizen_ci_shared.types -> tizen_ci_shared.state (l.8)


NEGATIVE_A_EXIT=1
```

The temporary import was removed after this check.

## Negative B: shared-no-uplink

Temporary violation: add `import ci_triage` to
`tizen_ci_shared/state/db.py`.

Output:

```text
=============
Import Linter
=============

---------
Contracts
---------

Analyzed 32 files, 55 dependencies.
-----------------------------------

shared internal layers: L1 -> L0 -> types KEPT
shared must not import orchestration BROKEN
shared L1 domains are independent KEPT
shared L0 primitives are independent KEPT

Contracts: 3 kept, 1 broken.


----------------
Broken contracts
----------------

shared must not import orchestration
------------------------------------

tizen_ci_shared is not allowed to import ci_triage:

-   tizen_ci_shared.state.db -> ci_triage (l.23)


NEGATIVE_B_EXIT=1
```

The temporary import was removed. The restored positive check again reported
`Contracts: 4 kept, 0 broken.` and `RESTORED_POSITIVE_EXIT=0`.

## Shared Types Closure Guard

The v2.0 revision-1 negative probe temporarily added a field typed as the
higher-layer `ci_triage.gerrit.GerritError` to `FailedPackage`.

```text
FailedPackage | ... | MISMATCH: type-closure escapes L-1: FailedPackage.audit_escape_probe references GerritError from ci_triage/gerrit.py
SUMMARY | 40 OK | 1 MISMATCH | 0 INCOMPLETE
TYPE_CLOSURE_NEGATIVE_EXIT=1
```

The temporary field was removed. The positive audit reports
`SUMMARY | 41 OK | 0 MISMATCH | 0 INCOMPLETE`.

## Named Deferrals

- `shared-l1-independence` negative control is bound to commit 2, after the
  workspace capability replaces its placeholder. Commit 2 must record the real
  exit-1 output; without it, step-0 must not be declared complete.
- `shared-l0-independence` negative control is bound to commit 3, after
  quickbuild_http and env replace their placeholders. Commit 3 must record the
  real exit-1 output; without it, step-0 must not be declared complete.

## Commit 1 Validation

- Affected test selection: `230 passed in 11.23s`.
- Full regression: 847 collected, `846 passed, 1 skipped in 18.92s`, matching
  the pre-change baseline exactly.
- Mypy: `Success: no issues found in 100 source files`.
- Py_compile: `PASS` for all Python files under `tizen_ci_shared` and
  `ci_triage`.
- Final import-linter: `4 kept, 0 broken`, exit 0.
- Final symbol audit: `41 OK, 0 MISMATCH, 0 INCOMPLETE`, exit 0.
- Frozen canonical/history comparison: `cmp` exit 0.
- Placeholder mechanical check: each of workspace/__init__.py, classify.py,
  env.py, and quickbuild_http.py is one line containing only its docstring.
- State migration proof: old HEAD content, after only replacing
  `ci_triage.state` with `tizen_ci_shared.state`, has an empty diff against the
  moved files.
- Type migration proof: AST dumps for `GerritPatchSet`, `GerritChange`,
  `SourceFetchResult`, and `FailedPackage` match their HEAD definitions 4/4.

The broad command `.venv/bin/ruff check .` also scanned the pre-existing,
untracked root file `audit_four_sigs.py` and reported its eight formatting
violations. That unrelated file was deliberately not changed or staged. Ruff
passes for all tracked Python files plus every Python file added by commit 1.
