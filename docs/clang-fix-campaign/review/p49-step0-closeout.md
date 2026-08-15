# P4.9 Step-0 Closeout

Authority: `docs/clang-fix-campaign/p49-step0-design-v2.0-FROZEN.md`, including
revisions 1 through 7a.

Implementation commits:

- `8dca6c1c0f286c60de172b46ddd1e41053955cc9` - shared package, state, types.
- `ab58bfdabe5f2845beb6d6d216b22d0847756bc5` - workspace, classify, env.
- `6def1edea087627a68e7343e458174d780401013` - QuickBuild HTTP and final L0 guard.

## DoD Account

Summary: **12 DONE / 4 DEFERRED**. The deferred items are deliberate downstream
work with named closing batches; no step-0 verification debt is unnamed.

| # | DoD text | Status | Evidence anchor | Measured output excerpt |
|---:|---|---|---|---|
| 1 | "tizen_ci_shared independent package established, three layers + step-0 four active contracts lint-imports positive green" | DONE | `8dca6c1`; `dev_memory/stage07_p49_step0/commit1-evidence.md:23`; `.importlinter` | `Contracts: 4 kept, 0 broken`, exit 0; closeout rerun also 4/0 |
| 2 | "four negative-verification classes each turn red and record exit code" | DONE | `8dca6c1`, `ab58bfd`, `6def1ed`; `progress.md:350` | shared-layers=1; shared-no-uplink=1; L1 state->workspace=1 and workspace->classify=1; L0 HTTP->env=1 and env->HTTP=1 |
| 3 | "commit 1 four placeholder files each contain only one docstring line, zero imports/definitions/logic" | DONE | `8dca6c1`; `commit1-evidence.md:136` | four files passed `wc -l == 1` and full `cat`; later commits replaced them only in their assigned batches |
| 4 | "two marker format constants uniquely defined in shared, excluding release snapshot copies" | DONE | `ab58bfd`; `progress.md:205`; `tizen_ci_shared/workspace/__init__.py:13` | exact-name grep returns only `MARKER_FILENAME` and `PROTECTED_FILENAME` in shared/workspace |
| 5 | "S-1 mechanical verification: write_workdir_marker landed + create_worktree body has no FILENAME" | DONE | `ab58bfd`; `tizen_ci_shared/workspace/__init__.py:33`; `progress.md:207` | five kw-only metadata inputs, returns `Path`; clean primitive at line 55; scoped grep has zero matches (exit 1) |
| 6 | "workspace function attribution follows section 3.2; discover_sibling_pythonpath is audited with four consumers" | DONE | `ab58bfd`; revision-6/7a closeout audit; `p49-step0-symbol-audit.md` | revision-6 added `_is_relative_to`; final workspace public surface complete; discover consumers are batch_cli/cli/orchestrator/build_verify |
| 7 | "audit scope matches actual step-0 surface; all shared entity guards green; gbs_report has no inventory, guard, or production diff" | DONE | `6def1ed`; `progress.md:471`; revision-7a audit | `gbs_inventory_entries=0`, `gbs_surface_guards=0`; `git diff 698bd7c..6def1ed -- gbs_report.py` empty |
| 8 | "full tests equal baseline and remain green; test diff only section 5.1 classes; every commit lint-imports green" | DONE | commits 1-3 validation sections; closeout rerun | 847 collected, `846 passed, 1 skipped in 19.41s`; import-linter 4/0; mypy 99 files; ruff/py_compile green |
| 9 | "parity: build-verify/convergence critical paths normalize equal before and after extraction" | DONE | `ab58bfd`; `progress.md:210`; `6def1ed`; `progress.md:473` | marker normalized JSON equal, marker suffix equal, `cmp` exit 0; 13 workspace ASTs + env equal; classify and HTTP bytewise `cmp` exit 0 |
| 10 | "workspace/discover audit is all OK" plus the section 7 audit-completeness obligation | DONE | revisions 6, 7, 7a; `p49-step0-symbol-audit.md` | `42 SYMBOL OK + 4 MODULE-SCOPE OK (48 SYMBOLS COVERED)`, 0 MISMATCH, 0 INCOMPLETE; bridge 42+4 with all zero difference counts |
| 11 | "three commits each double-green; shim list registered for deletion at P4.9 end" | DONE | `8dca6c1`, `ab58bfd`, `6def1ed`; section 6.2; shim table below | every commit has tests + lint green; state old package deleted without shim; all required compatibility surfaces remain visible |
| 12 | Method 12 bridge mechanized and protected by negative controls | DONE | `6def1ed`; `tools/table_audit_bridge.py`; revision-7a audit | owner mismatch=exit 1; missing symbol=exit 1; missing module body row=exit 1; restored fifth-table bridge exit 0 |

## Revision-6 And Revision-7a Closure

Closeout itself found that `_is_relative_to` had moved across the workspace
boundary without entering section 3.2 or `SPECS`. Revision-6 registered it and
made completeness follow every physical shared module. That stronger guard
then exposed 47 unaudited classify/state symbols: the previous 42/42 result had
been complete only within an incomplete inventory.

Revision-7a closed the root cause with four module-scope declarations. This is
not an open-ended abbreviation: each module row covers its mechanically
enumerated top-level surface and must satisfy physical-shared location, deleted
or pure-shim legacy state, and zero overlap with per-symbol inventory. The
final derived count is 42 per-symbol entries plus four module entries covering
48 symbols.

## Shim Account

| Compatibility location | Current re-export count | Closing batch |
|---|---:|---|
| `ci_triage/gerrit.py` | 3 | P4.9 all six skills extracted |
| `ci_triage/quickbuild_log.py` | 1 | P4.9 all six skills extracted |
| `ci_triage/verify/workspace.py` | 17 | P4.9 all six skills extracted |
| `ci_triage/verify/failure_classify.py` | 13 | P4.9 all six skills extracted |
| `ci_triage/runner.py` | 1 (`discover_sibling_pythonpath`) | P4.9 all six skills extracted |
| `ci_triage/quickbuild.py` | 17 | P4.9 all six skills extracted |
| `ci_triage/verify/__init__.py` | 14 package re-exports across classify/workspace | P4.9 all six skills extracted |

`runner.py` also consumes shared HTTP/types directly; those imports are not
compatibility shims. `ci_triage/state/` is absent and intentionally has no shim.

## Deferred Account

| Item | Status | Owner / closing batch | Evidence |
|---|---|---|---|
| GBS report fetch/parse split and seven inherited constraints | DEFERRED | triage-report extraction batch | frozen design section 8 and `progress.md:17` |
| Compatibility shim deletion | DEFERRED | one cleanup commit after all six P4.9 skills are extracted | frozen design section 6.2 and shim table above |
| `root-layers` and `skill-independence` activation, including pinned-version `containers` proof | DEFERRED | first skill extraction batch (`convergence-judge`) | frozen design section 1.3/8.1 and `progress.md:47` |
| C21 subprocess test environment anchoring | DEFERRED | before the first convergence-judge subprocess smoke is added or changed | `progress.md:57` |

## Current Verification

```text
pytest: 846 passed, 1 skipped in 19.41s (847 collected)
lint-imports: Contracts: 4 kept, 0 broken
mypy packages: Success: no issues found in 99 source files
mypy audit tools --strict: Success: no issues found in 2 source files
ruff audit tools: All checks passed!
py_compile audit tools: PASS
frozen canonical/history cmp: exit 0, byte-identical
symbol audit: 42 SYMBOL OK + 4 MODULE-SCOPE OK (48 covered), 0/0
table bridge: 42 SYMBOL OK + 4 MODULE-SCOPE OK, all difference counts zero
```
