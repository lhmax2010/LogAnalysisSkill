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


## Commit ③ L0 independence evidence

### Negative A: quickbuild_http imports env

Temporary violation: add `import tizen_ci_shared.env` to
`tizen_ci_shared/quickbuild_http.py`.

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

Analyzed 32 files, 62 dependencies.
-----------------------------------

shared internal layers: L1 -> L0 -> types BROKEN
shared must not import orchestration KEPT
shared L1 domains are independent KEPT
shared L0 primitives are independent BROKEN

Contracts: 2 kept, 2 broken.


----------------
Broken contracts
----------------

shared internal layers: L1 -> L0 -> types
-----------------------------------------

tizen_ci_shared.quickbuild_http is not allowed to import tizen_ci_shared.env:

- tizen_ci_shared.quickbuild_http -> tizen_ci_shared.env (l.8)


shared L0 primitives are independent
------------------------------------

tizen_ci_shared.quickbuild_http is not allowed to import tizen_ci_shared.env:

- tizen_ci_shared.quickbuild_http -> tizen_ci_shared.env (l.8)


exit_code=1
```

The temporary import was removed.

### Negative B: env imports quickbuild_http

Temporary violation: add `import tizen_ci_shared.quickbuild_http` to
`tizen_ci_shared/env.py`.

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

Analyzed 32 files, 62 dependencies.
-----------------------------------

shared internal layers: L1 -> L0 -> types BROKEN
shared must not import orchestration KEPT
shared L1 domains are independent KEPT
shared L0 primitives are independent BROKEN

Contracts: 2 kept, 2 broken.


----------------
Broken contracts
----------------

shared internal layers: L1 -> L0 -> types
-----------------------------------------

tizen_ci_shared.env is not allowed to import tizen_ci_shared.quickbuild_http:

- tizen_ci_shared.env -> tizen_ci_shared.quickbuild_http (l.5)


shared L0 primitives are independent
------------------------------------

tizen_ci_shared.env is not allowed to import tizen_ci_shared.quickbuild_http:

- tizen_ci_shared.env -> tizen_ci_shared.quickbuild_http (l.5)


exit_code=1
```

The temporary import was removed. The restored positive check reports
`4 kept, 0 broken` with exit code 0.

### Four negative-control classes closed

| Contract | Temporary violation | Exit | Completed |
|---|---|---:|---|
| shared-layers | types imports state | 1 | commit ① |
| shared-no-uplink | shared state imports ci_triage | 1 | commit ① |
| shared-l1-independence | state imports workspace; workspace imports classify | 1 / 1 | commit ② |
| shared-l0-independence | quickbuild_http imports env; env imports quickbuild_http | 1 / 1 | commit ③ |

All four classes now have real fail-closed evidence. No deferred step-0
import-linter negative control remains.

## Commit ③ table-audit bridge evidence

The read-only bridge compares the frozen design's §2, §3.2, §3.3, and §4.1
tables against the complete `symbol_audit.SPECS` inventory. Its final positive
run is `42 OK` with all difference and parse-error counts zero.

### Negative: owner mismatch

```text
symbol | body_owner | inventory_owner | verdict
DEFAULT_COOKIE_PATH | shared/types | shared/quickbuild_http | OWNER_MISMATCH
DEFAULT_QUICKBUILD_BASE_URL | shared/quickbuild_http | shared/quickbuild_http | OK
DOWNLOAD_LINK_MARKER | shared/quickbuild_http | shared/quickbuild_http | OK
DOWNLOAD_TIZEN_BASE_URL | shared/quickbuild_http | shared/quickbuild_http | OK
DisposableWorktree | shared/workspace | shared/workspace | OK
FailedPackage | shared/types | shared/types | OK
FailureClassification | shared/classify | shared/classify | OK
GerritChange | shared/types | shared/types | OK
GerritPatchSet | shared/types | shared/types | OK
HttpFetcher | shared/quickbuild_http | shared/quickbuild_http | OK
HttpResponse | shared/quickbuild_http | shared/quickbuild_http | OK
MARKER_FILENAME | shared/workspace | shared/workspace | OK
PROTECTED_FILENAME | shared/workspace | shared/workspace | OK
PackageBuildLog | shared/quickbuild_http | shared/quickbuild_http | OK
QuickBuildDownload | shared/quickbuild_http | shared/quickbuild_http | OK
QuickBuildError | shared/quickbuild_http | shared/quickbuild_http | OK
SourceFetchResult | shared/types | shared/types | OK
WorkspaceViolation | shared/workspace | shared/workspace | OK
_copy_repository | build-verify | build-verify | OK
_exclude_private_files | shared/workspace | shared/workspace | OK
_oldest_worktrees | shared/workspace | shared/workspace | OK
_raise_if_login_page | shared/quickbuild_http | shared/quickbuild_http | OK
_read_marker | shared/workspace | shared/workspace | OK
_run_git | shared/workspace | shared/workspace | OK
_urllib_fetch | shared/quickbuild_http | shared/quickbuild_http | OK
_verify_cleanup_handle | shared/workspace | shared/workspace | OK
check_disk_and_maybe_cleanup | build-verify | build-verify | OK
clean_repository_preserving_markers | shared/workspace | shared/workspace | OK
cleanup_disposable_copy | shared/workspace | shared/workspace | OK
cleanup_worktree | shared/workspace | shared/workspace | OK
create_worktree | build-verify | build-verify | OK
derive_package_buildlog_url | shared/quickbuild_http | shared/quickbuild_http | OK
discover_sibling_pythonpath | shared/env | shared/env | OK
download_full_log | shared/quickbuild_http | shared/quickbuild_http | OK
download_package_buildlog | shared/quickbuild_http | shared/quickbuild_http | OK
find_download_href | shared/quickbuild_http | shared/quickbuild_http | OK
is_protected | shared/workspace | shared/workspace | OK
load_cookie_jar | shared/quickbuild_http | shared/quickbuild_http | OK
mark_worktree_protected | shared/workspace | shared/workspace | OK
normalize_quickbuild_url | shared/quickbuild_http | shared/quickbuild_http | OK
release_worktree_protection | shared/workspace | shared/workspace | OK
write_workdir_marker | shared/workspace | shared/workspace | OK
SUMMARY | 41 OK | 0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | 1 OWNER_MISMATCH | 0 PARSE_ERROR
exit_code=1
```

### Negative: symbol missing from inventory

```text
symbol | body_owner | inventory_owner | verdict
DEFAULT_COOKIE_PATH | shared/quickbuild_http | shared/quickbuild_http | OK
DEFAULT_QUICKBUILD_BASE_URL | shared/quickbuild_http | shared/quickbuild_http | OK
DOWNLOAD_LINK_MARKER | shared/quickbuild_http | shared/quickbuild_http | OK
DOWNLOAD_TIZEN_BASE_URL | shared/quickbuild_http | shared/quickbuild_http | OK
DisposableWorktree | shared/workspace | shared/workspace | OK
FailedPackage | shared/types | shared/types | OK
FailureClassification | shared/classify | shared/classify | OK
GerritChange | shared/types | shared/types | OK
GerritPatchSet | shared/types | shared/types | OK
HttpFetcher | shared/quickbuild_http | shared/quickbuild_http | OK
HttpResponse | shared/quickbuild_http | - | MISSING_FROM_INVENTORY
MARKER_FILENAME | shared/workspace | shared/workspace | OK
PROTECTED_FILENAME | shared/workspace | shared/workspace | OK
PackageBuildLog | shared/quickbuild_http | shared/quickbuild_http | OK
QuickBuildDownload | shared/quickbuild_http | shared/quickbuild_http | OK
QuickBuildError | shared/quickbuild_http | shared/quickbuild_http | OK
SourceFetchResult | shared/types | shared/types | OK
WorkspaceViolation | shared/workspace | shared/workspace | OK
_copy_repository | build-verify | build-verify | OK
_exclude_private_files | shared/workspace | shared/workspace | OK
_oldest_worktrees | shared/workspace | shared/workspace | OK
_raise_if_login_page | shared/quickbuild_http | shared/quickbuild_http | OK
_read_marker | shared/workspace | shared/workspace | OK
_run_git | shared/workspace | shared/workspace | OK
_urllib_fetch | shared/quickbuild_http | shared/quickbuild_http | OK
_verify_cleanup_handle | shared/workspace | shared/workspace | OK
check_disk_and_maybe_cleanup | build-verify | build-verify | OK
clean_repository_preserving_markers | shared/workspace | shared/workspace | OK
cleanup_disposable_copy | shared/workspace | shared/workspace | OK
cleanup_worktree | shared/workspace | shared/workspace | OK
create_worktree | build-verify | build-verify | OK
derive_package_buildlog_url | shared/quickbuild_http | shared/quickbuild_http | OK
discover_sibling_pythonpath | shared/env | shared/env | OK
download_full_log | shared/quickbuild_http | shared/quickbuild_http | OK
download_package_buildlog | shared/quickbuild_http | shared/quickbuild_http | OK
find_download_href | shared/quickbuild_http | shared/quickbuild_http | OK
is_protected | shared/workspace | shared/workspace | OK
load_cookie_jar | shared/quickbuild_http | shared/quickbuild_http | OK
mark_worktree_protected | shared/workspace | shared/workspace | OK
normalize_quickbuild_url | shared/quickbuild_http | shared/quickbuild_http | OK
release_worktree_protection | shared/workspace | shared/workspace | OK
write_workdir_marker | shared/workspace | shared/workspace | OK
SUMMARY | 41 OK | 1 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | 0 OWNER_MISMATCH | 0 PARSE_ERROR
exit_code=1
```

Both temporary edits were restored. The bridge returned exit code 1 for each
negative control and exit code 0 after restoration.

## Commit ③ validation

- HTTP move equivalence: the pre-move `ci_triage/quickbuild.py` and final
  `tizen_ci_shared/quickbuild_http.py` are byte-identical (`cmp` exit 0).
- Compatibility surface: `ci_triage/quickbuild.py` contains exactly 17
  one-symbol re-export statements and no implementation definitions.
- Direct consumers: orchestrator, runner, batch_cli, cli, and sources import
  `tizen_ci_shared.quickbuild_http`; gbs_report remains unchanged and consumes
  the compatibility shim.
- Full regression: `846 passed, 1 skipped in 22.90s`, matching commits ①/②.
- Mypy: `Success: no issues found in 99 source files`.
- Ruff: `All checks passed!` for tracked Python files plus the new bridge.
- Py_compile: exit 0 for every Python file under `tizen_ci_shared` and
  `ci_triage`.
- Import Linter: `4 kept, 0 broken`, exit 0 after both L0 negative probes were
  restored.
- Symbol audit: `42 OK, 0 MISMATCH, 0 INCOMPLETE`, exit 0.
- Table bridge: `42 OK`; all missing/mismatch/parse-error counts zero, exit 0.
- Frozen canonical/history comparison: `cmp` exit 0 after revisions 4 and 5.
- S-1 regression check: create_worktree has zero `FILENAME` references; marker
  constants remain uniquely defined in `tizen_ci_shared.workspace`.
- Out-of-scope files: `ci_triage/gbs_report.py` and P4.5 `design.md` have zero
  diff.
