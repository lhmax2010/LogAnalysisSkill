# P4.9 Skill-5 Gerrit-Submit Closeout

Authority:
`docs/clang-fix-campaign/p49-skill5-gerrit-submit-design-v1.3.2-FROZEN.md`.

Lifecycle commits before this amendment: `f2bc050`, `31a91cb`, `a97c40b`,
`0dfa5f1`, `a8620f1`, and closeout `d51145f`. The seventh lifecycle commit is
the v1.3.2 amendment containing this update. Git anchors its integrity
externally; its SHA is intentionally not recorded inside itself (`⑬/⑲`).

## Summary

- Frozen section 8 account: **13 DONE / 1 DEFERRED umbrella**.
- The umbrella is expanded below into **4 named DEFERRED obligations**. P4.9
  final cleanup and cross-skill behavior unification are their terminal batch;
  no further deferral is permitted without an explicit three-party
  cancellation ruling.
- Baseline chain: **897 -> 899 -> 905 -> 912 passed**, with one intentional
  skip throughout. Each transition preserved the preceding collected-test
  set and introduced no failures or new skips.
- Final audit state: **173 symbol entries + 4 module scopes**, zero mismatch
  and zero incomplete. The bridge independently prints all 23 skill-5 rows.

## Baseline Chain

| Milestone | Set-preservation evidence | Result |
|---|---|---|
| Pre-skill baseline | `f2bc050`; `progress.md:172-181` | `897 passed, 1 skipped`; independently reproduced in the clean review environment |
| Commit A `a97c40b` | `progress.md:352-379`; collection `898 -> 900`, `MISSING_BASELINE=0`, two additions | `899 passed, 1 skipped`; clean-environment reproduction matched |
| Commit B `0dfa5f1` | `progress.md:543-570`; collection `900 -> 906`, ownership remap applied, `MISSING_AFTER_OWNERSHIP_RENAME=0`, six additions | `905 passed, 1 skipped`; clean-environment reproduction matched |
| Commit C `a8620f1` | `progress.md:779-815`; collection `906 -> 913`, `existing_collection_missing=0`, seven ledger-version tests | `912 passed, 1 skipped`; editable-install run with `PYTHONPATH` and `MYPYPATH` removed matched the clean delivery environment |

The chain is a nodeid-set preservation claim, not a frozen-total claim. Test
ownership moves are normalized before comparison, and every net-new test is
green.

## Section 8 DoD Account

| # | DoD text | Status | Evidence anchor | Measured output excerpt |
|---|---|---|---|---|
| 1 | “全量:897 基线集合不缩小、无失败;新基线如实记录” | DONE | `a97c40b`, `0dfa5f1`, `a8620f1`; `progress.md:352-379`, `:543-570`, `:779-815` | Baseline chain is `897 -> 899 -> 905 -> 912 passed`, always one skip; missing prior nodeids are zero at every transition. |
| 2 | “模式一 cmp 空;旧址零 def/class” | DONE | `a97c40b`; `progress.md:202-237`; `tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:1` | Pre-migration source and the skill copy share SHA `ead701d...107f`; `cmp` exited 0. Exact `rg '^(def|class) '` on the legacy path has no matches and exits 1. |
| 3 | “23 符号入册;bridge 输出含该 definition 路径且计数精确 23” | DONE | `a8620f1`; frozen §0; `progress.md:588-634`, `:716-746`; `symbol_audit.py`, `table_audit_bridge.py` | Parser-only is `23/23`; bridge prints all 23 `tizen_gerrit_submit/gerrit_submit.py` rows and ends with 173+4, all five difference classes zero. |
| 4 | “一道 INCOMPLETE 护栏为集合等价 + MixedCaseAlias 负 fixture 红” | DONE | `a8620f1`; `progress.md:636-665`; `symbol_audit.py` | Skill surface is pinned at 23 and compared in both directions. `--surface-fixture mixed-case-alias` reports `present in source but not audited: MixedCaseAlias` and exits 1. |
| 5 | “四组 twin 各自注册,限定作用域精确命令证未合并” | DONE | `a8620f1`; `progress.md:716-746`; exact commands below | Production script-root probes return `SubprocessRunner=8`, `_git_stdout=3`, `_run_git=3`, `_result=2`; the skill-5 audit rows retain their own definition and consumer sets. |
| 6 | “契约绿 + 三条负控制红 + §2.4 下行正向与负控制③配对陈述” | DONE | `a8620f1`; `.importlinter`; `progress.md:667-714` | Positive run: `6 kept, 0 broken`. Skill-to-orchestration, skill-to-skill, and shared-to-skill mutations each exit 1. Skill-to-shared state/workspace is the explicit green opposite of the third negative. |
| 7 | “§3 两项现状锁定测试... + 两项设计已登记且新关门批次具名” | DONE | `0dfa5f1`; frozen §3.2/§4; `progress.md:473-495`; tests at `test_tizen_gerrit_submit.py:199`, `:223`, `:238`, `:385`; `test_gerrit_fetch.py:535` | The fake runner sees both subprocess paths and no `timeout`; local timeout propagates by identity, remote timeout becomes an unverified warning/action, the dangling-symlink test preserves its disk state, and executed argv never contains `push`. The two behavior changes are designed and assigned to the P4.9 terminal batch. |
| 8 | “pre-shim parity(一正三反)与 post-shim identity 分列” | DONE | `a97c40b`; `progress.md:261-318`, `:320-350`; `commit-a-evidence/pre-shim-parity.txt` | Five pre-shim payload partitions compare equal; destination-only normalizes green while action/order/exit mutations turn red. Post-shim 9+14 identity is recorded separately as wiring-only evidence. |
| 9 | “三入口 1/1/2/2;两阶段分列;release-v1.4.0 不回填” | DONE | `a8620f1`; `progress.md:748-815`; CI/README/pyproject | CI, README, source-root, and package-name probes are `1/1/2/2`. B used explicit path scaffolding; C used editable install with both path variables unset. The release snapshot has zero diff. |
| 10 | “双门禁继承 A₀ 且全绿” | DONE | `31a91cb`, `a8620f1`; `progress.md` “v1.3.2 post-closeout deferred-mapping amendment” | The v1.3.2 check is `38/34/4` with zero drift; v1.2 admission remains red with seven drifts and both required defects. Skill-4 remains green, while all 47 OUT_OF_SCOPE and 22 per-binding controls remain red. |
| 11 | “§4 分支表全部契约句逐行有用例,代码锚与实际实现一致” | DONE | `0dfa5f1`; frozen §4; `progress.md:441-471` | Mechanical closure reports `branch_rows=14`, `rows_with_use_cases=14`, `unresolved=0`; every row carries both a source anchor and collected test name. |
| 12 | “§3.2 结果映射表由末批实现、parity 与评审逐行销账” | DONE | Frozen §3.2 lines 250-298; deferred ledger below | The six-part design and its four-row result map are complete and immutable input to the terminal behavior-unification batch. This extraction intentionally does not implement them early. |
| 13 | “§2 门禁成员扩展与三条负控制全部落地并实测” | DONE | `a8620f1`; `.importlinter`; `progress.md:667-714` | The sixth skill is in root-layers and skill-independence and is forbidden from shared. All six contracts are green and all three new negative edges are red. No new exception exists. |
| 14 | “DEFERRED:timeout 统一 + 悬空 symlink 归一化...;shim 删除...;其余沿既有” | DEFERRED | Frozen §3.2 lines 250-298 and §8; named ledger below | Four obligations remain. Every item has the P4.9 terminal batch, a current-state test boundary, and a no-further-deferral clause. |

## Mode-One, API, and Twin Evidence

The mode-one comparison used the pre-migration implementation, before the old
path became a shim:

```text
cmp old-pre-migration.py tizen_gerrit_submit/gerrit_submit.py
(no output)
CMP_EXIT=0
sha256(both)=ead701d0e943f395225729be5daef94f53912002d97534f2309cc264e037107f
```

The package-root test proves exactly nine public identities and fourteen
absent private names. The legacy path re-exports all 23 objects and contains
no function or class definitions.

Twin counts use exact syntax and the production script-root scope:

```bash
rg '^SubprocessRunner = ' tizen-*/scripts --glob '*.py' | wc -l  # 8
rg '^def _git_stdout\(' tizen-*/scripts --glob '*.py' | wc -l    # 3
rg '^def _run_git\(' tizen-*/scripts --glob '*.py' | wc -l       # 3
rg '^def _result\(' tizen-*/scripts --glob '*.py' | wc -l        # 2
```

## Branch and Current-State Locks

The frozen 14-row branch table is closed by named tests. In particular:

- both `rejected_not_ready` entries have independent tests;
- all five `_target_warnings` outcomes are exercised;
- `dry_run` and `dry_run_unverified_remote` remain distinct;
- submit/release exit-code mappings are covered;
- `test_gerrit_submit_dry_run_returns_command_without_push` asserts that every
  executed subprocess argv is free of `push`.

The three current-state locks are explicit countervalue for the deferred
behavior work:

1. `test_gerrit_submit_all_subprocess_paths_omit_timeout` intercepts direct
   `ls-remote` and wrapper `_run_git` calls and proves neither receives a
   `timeout` keyword.
2. `test_run_git_propagates_timeout_expired_unchanged` and
   `test_gerrit_submit_converts_ls_remote_timeout_to_unverified_warning` lock
   the two different timeout outcomes.
3. `test_fetch_source_dangling_symlink_propagates_file_exists_error` is reused
   from skill-3 and asserts both the exception and post-failure disk state.

## Gate and Audit Evidence

```text
pytest: 912 passed, 1 skipped
targeted skill/integration/CLI set: 46 passed
lint-imports: 6 kept, 0 broken
symbol audit: 173 SYMBOL OK + 4 MODULE-SCOPE OK (48 covered); 0 MISMATCH; 0 INCOMPLETE
table bridge: 173+4; all differences zero; 23 skill-5 rows present
skill-5 design check: RESIDUAL_DRIFT=0; BINDING_DRIFT=0
skill-5 admission v1.2: BINDING_DRIFT=7; RED_AS_EXPECTED
skill-5 negatives: 4 OUT_OF_SCOPE + 8 per-binding, all red
skill-4 check: RESIDUAL_DRIFT=0; BINDING_DRIFT=0
skill-4 negatives: 47 OUT_OF_SCOPE + 22 per-binding, all red
entry counts: 1/1/2/2
release-v1.4.0 / gbs_report.py / P4.5 design.md diff: empty
```

The skill has no named import exception. The existing `gbs_patch_suggest`
exception lines are byte-unchanged; `include_external_packages` remains
absent. The green downward edge from the skill to shared state/workspace is
paired with the red shared-to-skill mutation, so the directionality is
mechanically demonstrated rather than inferred.

## Frozen-Design Revision and Ledger Grammar

Commit C's bridge integration failed closed because v1.3-FROZEN omitted the
three-column authoritative attribution table. The correction generated the 23
rows from the migrated module's AST, promoted the authority and history copy
to v1.3.1-FROZEN, and added a universal parser-only requirement to the skill
batch template. Parser-only and the full bridge both report 23/23.

The v1.3.2 delta corrects only the factual precision of the deferred §3.2
mapping: it splits skill-3 query/git residual states, adds the independently
executed `_exclude_private_files` call surface, pins real exception constructor
shapes, and records the measured marker-write order. No implemented behavior
or prior extraction verdict changes.

The same correction required the inherited ledger to parse patch versions.
`_version_key` now returns `(N, M, P)`, with omitted P equal to zero. Legal
successors are exactly patch +1 at fixed N/M or minor +1 with P reset to zero.
Direct tests prove:

```text
1.3 -> 1.3.2       red
1.3.1 -> 1.4.1     red
1.3 -> 1.3.1 -> 1.4 green
```

Additional skip cases `1.3 -> 1.4.1`, `1.3.1 -> 1.3.3`, and
`1.3.1 -> 1.5` are also red. Skill-4's corpus now includes its real
v1.12 -> v1.12.1 transition. Skill-5 now supplies the rule's next real use:
`1.3 -> 1.3.1 -> 1.3.2`, accepted with three retained transition candidates.
All inherited gates remain intact.

## Deferred Terminal Ledger

Frozen §3.2 supplies these six binding decisions to the terminal behavior
batch:

1. The call surface is closed: skill-3 `fetch_source_for_commit` query and git
   stages, this skill's `_run_git` and `ls-remote`, and shared/workspace
   `_run_git` and `_exclude_private_files`.
2. Every surface accepts optional `timeout: float | None`; the default is
   `None`, callers inject it, and terminal parity admits only the added
   `timeout=None` runner kwarg.
3. Timeout errors become named outcomes: bare-propagation helpers raise named
   exceptions while `ls-remote` remains warning-shaped with a stable code.
4. `SIGINT` and `SIGTERM` propagate unchanged; caller wrappers, not skills,
   own interruption cleanup.
5. Timeout or interruption preserves worktrees and markers at their
   interruption state; no automatic rollback is introduced.
6. The result mapping is fixed as follows and may change only through a
   reopened design review:

| Call surface | Timeout outcome | External interruption | Residual state |
|---|---|---|---|
| skill-3 `fetch_source_for_commit` query stage | `GerritError("FETCH_TIMEOUT", <message>)` | propagate | destination unchanged |
| skill-3 git stage | `GerritError("FETCH_TIMEOUT", <message>)` | propagate | stage-specific destination residue |
| this skill `_run_git` | `GerritSubmitError("GIT_TIMEOUT", <message>)` | propagate | worktree unchanged |
| this skill `ls-remote` | `target_head_unknown:timeout` warning | propagate | none |
| shared/workspace `_run_git` | `WorkspaceViolation(<message>)`, prefixed `GIT_TIMEOUT:` | propagate | marker unchanged |
| shared/workspace `_exclude_private_files` | `WorkspaceViolation("GIT_TIMEOUT: …")` | propagate | workdir marker retained; protected marker not yet written; exclude incomplete |

These decisions are implementation input, not topics to redesign casually.

| # | Obligation | Status | Terminal batch | Frozen design and current boundary |
|---|---|---|---|---|
| D1 | Normalize dangling-symlink handling | DEFERRED | P4.9 final cross-skill behavior-unification batch | §3.2 requires `path.is_symlink()` to yield `SOURCE_DIR_UNSAFE`; current skill-3 test locks `FileExistsError` plus unchanged disk state. |
| D2 | Unify timeout, cancellation, interruption, and residual-state behavior | DEFERRED | P4.9 final cross-skill behavior-unification batch | §3.2 fixes injection location, no-default-timeout compatibility, normalized error outcomes, signal propagation, residual state, and the six-row result map. Current two-path timeout tests lock the starting point. |
| D3 | Delete all legacy compatibility shims | DEFERRED | P4.9 final cleanup, separate commit from behavior unification | The Gerrit-submit legacy module is a pure re-export with zero def/class; compatibility remains test-covered until the one-shot deletion. |
| D4 | Narrow tests that consume implementation-private symbols | DEFERRED | P4.9 final cleanup | Private names remain absent from package-root API; test access is explicit and must be narrowed without promoting those names. |

**Terminal clause:** P4.9 final cleanup/behavior unification is the last allowed
batch for D1-D4. An unfinished item blocks P4.9 closure and may not be deferred
again. The only alternative is an item-specific cancellation with rationale
and three-party confirmation.
