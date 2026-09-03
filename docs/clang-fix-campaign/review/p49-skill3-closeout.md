# P4.9 Skill-3 Gerrit-Fetch Closeout

Authority:
`docs/clang-fix-campaign/p49-skill3-gerrit-fetch-design-v1.3.1-FROZEN.md`.

Implementation commits: `4612167`, `751e7b4`, `f4be9e4`, `f6544df`,
`c41d15a`.

## Summary

- Frozen-design checks: **4 DONE / 0 DEFERRED**.
- Frozen implementation checklist: **28 DONE / 1 DEFERRED umbrella**.
- The umbrella is expanded below into **4 named DEFERRED obligations**, each
  with a closing batch.
- Combined explicit account: **32 DONE / 4 DEFERRED**.

## Frozen-Design Checks

| # | DoD text | Status | Evidence anchor | Measured output excerpt |
|---|---|---|---|---|
| F1 | “附录逐句与正文当前裁决面对账” | DONE | `4612167`; frozen authority lines 795-830 | Freeze review found the appendix aligned with the current body: zero production-behavior change, the import-binding mechanism, pre-shim evidence timing, and all non-extraction deliverables were represented. |
| F2 | “全文所有计数类表述与各自定义节对账” | DONE | `4612167`; frozen authority revision block lines 49-63 | Freeze count audit completed `17/17`; mechanical commands were tightened to exact function names before admission. |
| F3 | “SKILL.md 契约句与 §5.1 用例完成双向对照” | DONE | `4612167`; frozen §5.1 lines 497-530; closeout replay below | `contract_rows=20`, `mapped_rows=20`, `unmapped=0`; all referenced test functions occur in the 38 collected skill tests. |
| F4 | “以单独 commit 完成 FROZEN 定版;标题与状态均为 FROZEN” | DONE | `4612167`; canonical and history files | `cmp .../p49-skill3-gerrit-fetch-design-v1.3.1-FROZEN.md .../history/p49-skill3-gerrit-fetch-design-v1.3.1-FROZEN.md` returned exit 0. |

## Implementation DoD Account

| # | DoD text | Status | Evidence anchor | Measured output excerpt |
|---|---|---|---|---|
| 1 | “全量 847/1;B/C 以 A 后基线验收” | DONE | `751e7b4`, `f6544df`, `c41d15a`; `stage10.../progress.md:107-138`, `:246-310`, `:711-747` | Commit A established `847 passed, 1 skipped`. Before B there were 848 nodeids; after mapping the two intentional file relocations, `missing=0` and `new_nodeids=36`. B established, and C retained, `883 passed, 1 skipped`. Fresh closeout replay: `883 passed, 1 skipped in 17.79s`. |
| 2 | “B 阶段验证脚手架证据” | DONE | `f6544df`; `progress.md:413-435` | B explicitly used `PYTHONPATH=$PWD/tizen-gerrit-fetch/scripts...` and matching `MYPYPATH`; targeted 97, full 883/1, mypy 103 plus skill, ruff, py_compile, and six import contracts were green. The record states this was scaffolding, not delivery. |
| 3 | “C 阶段正式交付入口证据” | DONE | `c41d15a`; `progress.md:438-474`, `:711-747` | Editable install completed; with `env -u PYTHONPATH -u MYPYPATH`, pytest was 883/1, targeted was 38, mypy covered 105 sources, ruff/compileall were green, import-linter was 6/0, and both audits were green. |
| 4 | “旧址 gerrit.py 零 def/class,类型 shim 与实现 re-export 全在” | DONE | `f6544df`; `ci_triage/gerrit.py:1-32`; `progress.md:398-412` | Exact def/class search returned no matches. The file contains three shared-type shim imports and all 12 implementation re-exports. |
| 5 | “skill 副本自带 §1.2 类型 import” | DONE | `f6544df`; `tizen_gerrit_fetch/gerrit.py:14-16` | `GerritChange`, `GerritPatchSet`, and `SourceFetchResult` are imported directly from `tizen_ci_shared.types`. |
| 6 | “SKILL.md 的 §2.2 全部行为契约节齐全” | DONE | `c41d15a`; `tizen-gerrit-fetch/SKILL.md:1-62`; `progress.md:688-710` | Validator printed `Skill is valid!`; Inputs, Outputs, Errors, Side effects, and Idempotency include the destructive destination, propagation, no-timeout, residual-state, call-topology, and serial-cost boundaries. |
| 7 | “§0/§2.1 消费测量、package-root API、legacy shim 概念分离” | DONE | `f6544df`, `c41d15a`; frozen §0/§2.1; `progress.md:398-412`, `:633-687` | Inventory has 12 implementation symbols; the package root exports 4; the legacy path re-exports 12+3. None of these surfaces was used to enlarge another. |
| 8 | “package-root 公开契约正反测试” | DONE | `f6544df`; `tests/unit/test_gerrit_fetch.py:758-783` | Fresh identity probe: `package_root_public_identity=4/4`, `package_root_nonexports_absent=11/11` (8 implementation-only names plus 3 shared types). |
| 9 | “SKILL.md/API 双向对照” | DONE | `c41d15a`; `tizen-gerrit-fetch/SKILL.md:4-12`; `tizen_gerrit_fetch/__init__.py:3-15` | The four machine symbols named by SKILL.md are exactly `fetch_source_for_commit`, `GerritError`, `GERRIT_HOST`, and `GERRIT_PORT`; package-root positive/negative tests lock both directions. |
| 10 | “§5.1 分支覆盖表全部绿” | DONE | `f6544df`; `progress.md:366-397`; authoritative table copied below | Mechanical replay: `contract_rows=20`, `mapped_rows=20`, `unmapped=0`; targeted skill suite: `38 passed`. Destructive branches use `tmp_path` and assert destination state. |
| 11 | “异常传播新增分支逐项断言抛出边界与磁盘状态” | DONE | `f6544df`; `progress.md:366-397`; `tests/unit/test_gerrit_fetch.py:603-736` | Query timeout leaves the sentinel unchanged; three git timeout/interruption points retain their exact completed stages; `rmtree`/`unlink`/`mkdir` `OSError` cases retain the stated path/content state. The focused exception run was `11 passed`. |
| 12 | “无界阻塞回归锁同时拦直接 query 与 _run_git” | DONE | `f6544df`; `tests/unit/test_gerrit_fetch.py:738-753`; `progress.md:394-397` | One injected runner observed both ssh and git paths; every captured kwargs mapping lacked `timeout`. |
| 13 | “§5.3 测试所有权闭合” | DONE | `f6544df`; `tests/unit/test_gerrit_fetch.py:301-846`; `tests/unit/test_ci_triage.py` | Skill behavior, package-root contract, normalizer contract, and legacy wiring are labeled separately. The two legacy Gerrit tests were moved with body equality true; runner orchestration remains in `test_ci_triage.py`. |
| 14 | “定向/全量两层结果” | DONE | `c41d15a`; `progress.md:711-747`; closeout replay | `tests/unit/test_gerrit_fetch.py`: `38 passed in 0.05s`; full suite: `883 passed, 1 skipped in 17.79s`. |
| 15 | “契约/测试双向对照” | DONE | `f6544df`; frozen §5.1 lines 503-524; mapping below | All 20 contract rows resolve to collected tests and no row is unmapped. The sole representative rather than exhaustive exception-type choice is recorded below. |
| 16 | “设计期 parser-only 证据” | DONE | `4612167`; frozen §0 lines 76-89; closeout replay | `parser_only_rows=12`; output named all 12 `(tizen_gerrit_fetch/gerrit.py, symbol)` keys with owner `skill/tizen_gerrit_fetch`. This proves document parseability only. |
| 17 | “实现期完整 bridge 证据须逐项出现 skill-3 键” | DONE | `c41d15a`; `progress.md:633-652`; closeout replay | Bridge printed all 12 `tizen_gerrit_fetch/gerrit.py` rows and `SUMMARY | 108 SYMBOL OK | 4 MODULE-SCOPE OK | 0 MISSING... | 0 PARSE_ERROR`. |
| 18 | “§1.3a import-binding 加固断言 a-d” | DONE | `f4be9e4`, `c41d15a`; `progress.md:140-243`, `:633-687` | (a) `symbols=96`, `verdict_changes=0`; `primary_fingerprint consumers=('ci_triage.campaign_state',)`, internal `_primary_fingerprint consumers=()` (`[-]`). (b) aliased import new attribution was correct while legacy was `OLD_VERDICT=MISMATCH`. (c) same-name import independently passed. (d) planned/current Gerrit `_run_git` consumers were empty while workspace `_run_git` included `ci_triage.verify.workspace`. |
| 19 | “twin 实测” | DONE | `c41d15a`; `progress.md:633-687` | Both `_run_git` definitions are independently registered: shared/workspace reports `ci_triage.verify.workspace`; Gerrit reports no external consumer. Exact repository checks show three `_run_git` definitions and two relevant Gerrit `SubprocessRunner` definitions, with no merge. |
| 20 | “§3 全部契约绿、全部负控制红并正反配对” | DONE | `c41d15a`; `progress.md:475-632` | Positive: `Contracts: 6 kept, 0 broken`. Skill→`ci_triage`, skill→peer skill, and shared→this skill each exited 1 under the expected contracts. The real skill→three shared types edge is the legal downward counterpart to the measured shared→skill failure; positive green alone is not used as proof. |
| 21 | “§4a 机械同步逐项” | DONE | `c41d15a`; `progress.md:438-474`, `:633-687`; `symbol_audit.py`; `.importlinter`; `pyproject.toml` | Skill root, root-layer ordering, independence membership, forbidden roots, 12 SPECS rows, bridge path, and shared-type consumers all name `tizen_gerrit_fetch`; double audit found zero difference. |
| 22 | “§2 三入口逐项贴 diff 与精确计数” | DONE | `c41d15a`; `progress.md:438-474` | The qb-discover analogue first returned `1/1/2/2`; Gerrit then returned CI `1`, README `1`, source-path registrations `2`, package-name registrations `2`. |
| 23 | “release-v1.4.0 历史快照零 diff” | DONE | `c41d15a`; `progress.md:438-474`; closeout replay | `git diff --stat 4612167^..c41d15a -- release-v1.4.0` produced no output. The next release snapshot, not this extraction, will include the skill. |
| 24 | “pre-shim 行为 parity” | DONE | `f6544df`; `progress.md:312-365` | Evidence was captured while old/new modules were distinct via `importlib.reload`. Four recursive payload partitions were equal; ordered six-call argv traces, fetch depth 1/50, controlled environment, and destination tree matched. Both source files had SHA-256 `5df43c...`. Full detail is separated below. |
| 25 | “normalizer 一正三反” | DONE | `f6544df`; `tests/unit/test_gerrit_fetch.py:784-819`; `progress.md:330-365` | Destination-only difference: `PASS`; non-path error, command order, and status changes: each `RED_AS_EXPECTED`. Masking is field-scoped, not a global payload substitution. |
| 26 | “post-shim identity 只证接线” | DONE | `f6544df`; `tests/unit/test_gerrit_fetch.py:831-846`; closeout replay | `post_shim_impl_identity=12/12`; `post_shim_type_identity=3/3`. This is recorded separately from pre-shim behavior and makes no parity claim. |
| 27 | “双道审计全绿;⑧ arch 豁免” | DONE | `c41d15a`; `progress.md:633-710`; closeout replay | Symbol audit: `108 SYMBOL OK + 4 MODULE-SCOPE OK (48 covered)`, zero mismatch/incomplete. Bridge: same 108+4 and all difference/parse counters zero. `grep -c arch .../gerrit.py` printed `0`, exit 1. |
| 28 | “SKILL.md 落盘;shim 清单更新” | DONE | `c41d15a`; `tizen-gerrit-fetch/SKILL.md`; frozen shim ledger; `progress.md:688-710` | Skill validator passed; legacy `ci_triage.gerrit` is registered for the one-shot P4.9 final shim removal. |
| 29 | “DEFERRED:四项具名延期” | DEFERRED | Frozen §7 lines 786-792; expanded ledger below | Four obligations remain deliberately outside this behavior-preserving extraction. Every item has an owner batch and preserved current boundary. |

## Authoritative 20-Row Contract Map

This is copied from frozen §5.1, the sole contract/branch/test mapping. A
closeout parser matched every row to the collected skill test suite:

```text
contract_rows=20
mapped_rows=20
unmapped=0
collected_skill_tests=38
```

| §2.2 契约句 | §5.1 分支 | 用例名 |
|---|---|---|
| Errors:查询 `CalledProcessError` 转 `GERRIT_QUERY_FAILED`;删除发生在查询之后 | 查询命令失败 | `test_fetch_source_query_outcomes_preserve_destination[command-failed]` |
| Errors:查询零结果抛 `GERRIT_CHANGE_NOT_FOUND`;删除发生在查询之后 | 零 change | `test_fetch_source_query_outcomes_preserve_destination[not-found]` |
| Errors:查询多结果抛 `GERRIT_CHANGE_AMBIGUOUS`;删除发生在查询之后 | 多 change | `test_fetch_source_query_outcomes_preserve_destination[ambiguous]` |
| Errors:JSON 异常不归一化;删除发生在查询之后 | 畸形 JSON | `test_fetch_source_query_outcomes_preserve_destination[malformed-json]` |
| Errors:`TimeoutExpired` 不归一化;删除发生在查询之后 | query 阶段 `TimeoutExpired` | `test_fetch_source_query_outcomes_preserve_destination[timeout]` |
| Outputs/成本拓扑:NEW 匹配 patchset 成功并执行浅 fetch | NEW + 有匹配 patchset | `test_fetch_source_for_new_change_fetches_matching_patchset_ref` |
| Outputs:try 内 `GerritError` 以 code 返回;失败残留可观测 | NEW + 无匹配 patchset | `test_fetch_source_new_without_matching_patchset_returns_code` |
| Outputs/成本拓扑:非 NEW 一次浅 fetch 成功 | 非 NEW + commit fetch 成功 | `test_fetch_source_non_new_paths[direct-fetch]` |
| Outputs/成本拓扑:非 NEW 首次失败后按 branch fallback | 非 NEW + fetch 失败 + 有 branch | `test_fetch_source_non_new_paths[branch-fallback]` |
| Outputs:git `CalledProcessError` 返回 `FAILED_SOURCE`;失败残留可观测 | 非 NEW + fetch 失败 + 无 branch | `test_fetch_source_non_new_paths[failed-without-branch]` |
| Inputs/Side effects/Idempotency:每次调用重建工具自有 destination | destination 不存在 | `test_fetch_source_rebuilds_destination[missing]` |
| Inputs/Side effects/Idempotency:已有内容被同步删除并重建 | destination 已有目录 | `test_fetch_source_rebuilds_destination[directory]` |
| Inputs/Side effects/Idempotency:已有普通文件被删除并重建 | destination 已有普通文件 | `test_fetch_source_rebuilds_destination[file]` |
| Errors:存在且可解析的 symlink 抛 `SOURCE_DIR_UNSAFE` | destination 为有效 symlink | `test_fetch_source_rejects_live_symlink` |
| Errors:悬空 symlink 不拒绝、不清理,随后 `FileExistsError` | destination 为悬空 symlink | `test_fetch_source_dangling_symlink_propagates_file_exists_error` |
| Inputs/Side effects:`git_ssh_command` 进入每条 git 调用环境 | 提供 `git_ssh_command` | `test_fetch_source_sets_git_ssh_command_on_all_git_calls` |
| Outputs/Side effects:各终止性 git 失败返回 `FAILED_SOURCE` 并留阶段残留 | 各终止性 `_run_git` 失败点 | `test_fetch_source_git_failures_leave_observable_state[fail-point]` |
| Errors/Side effects:`TimeoutExpired` 或受控中断原样传播并留阶段残留 | git 阶段 `TimeoutExpired` / 受控中断 | `test_fetch_source_git_interruption_propagates_and_leaves_state[interrupt-point]` |
| Errors/Side effects:文件系统异常不归一化且磁盘状态可观测 | `rmtree` / `unlink` / `mkdir` 抛 `OSError` | `test_fetch_source_filesystem_errors_propagate[operation]` |
| Errors/性能成本:实现不设置 timeout,调用可能无界阻塞 | 全部 subprocess 调用 | `test_fetch_source_subprocess_calls_have_no_timeout` |

The only representative rather than exhaustive exception-type choice is the
malformed-JSON row: it fixes `json.JSONDecodeError` as the representative for
other parse/change-conversion exceptions. A missing-field `KeyError` from
`change_from_query_obj` has no separate branch. This is the frozen, explicit
tradeoff, not a claim of exhaustive exception enumeration.

## Exception and Disk-State Ledger

| Case | Injection point | Asserted destination state |
|---|---|---|
| `query/timeout` | Direct query runner raises `TimeoutExpired` | Existing directory and sentinel unchanged; only query ran |
| `timeout-after-init` | `git remote add` raises `TimeoutExpired` | Directory and fake `.git` remain; only init marker exists |
| `interrupt-during-fetch` | NEW fetch raises controlled interruption | Init and remote-add markers remain; source file absent |
| `timeout-before-checkout` | NEW checkout raises `TimeoutExpired` | Init, remote, and fetch markers remain; source file absent |
| `rmtree` | `shutil.rmtree` raises `OSError` | Original directory and sentinel content remain |
| `unlink` | `Path.unlink` raises `OSError` | Original regular file and content remain |
| `mkdir` | `Path.mkdir` raises `OSError` | Destination remains absent |

Six additional `CalledProcessError` cases cover init, remote-add, NEW fetch,
NEW checkout, fallback fetch, and non-NEW checkout, each with its exact partial
stage set. The no-timeout case observes both direct query and wrapper calls.

## Import-Binding Assertions

| Group | Result |
|---|---|
| a: regression and real alias | `symbols=96`, `verdict_changes=0`; `primary_fingerprint` → `ci_triage.campaign_state`; internal `_primary_fingerprint` → `[-]` |
| b: aliased import | New A.S includes the consumer and B.S excludes it; legacy implementation misses the binding and reports `OLD_VERDICT=MISMATCH` |
| c: same-name import | Independently green; explicitly not evidence for generalized `as` handling |
| d: real twin | Gerrit `_run_git` has no external consumer; shared/workspace `_run_git` includes `ci_triage.verify.workspace` |

## Pre-Shim Parity

Behavior was measured before the old module became a shim. `importlib.reload`
kept the legacy and extracted module objects distinct. The field-scoped
normalizer masked destination paths only in argv elements, `src_root`, and
symlink targets.

```text
field_equal.result=True
field_equal.runner_trace=True
field_equal.controlled_environment=True
field_equal.destination_state=True
payload_equal=True
old_sha256=840b9e8ccbaa94a2a1ae253c3644d245e5be3cb27a887b5a006278537ac2655a
new_sha256=840b9e8ccbaa94a2a1ae253c3644d245e5be3cb27a887b5a006278537ac2655a
normalizer_positive.destination_only=PASS
normalizer_negative.error_non_path=RED_AS_EXPECTED
normalizer_negative.command_order=RED_AS_EXPECTED
normalizer_negative.status=RED_AS_EXPECTED
```

The runner trace contains six ordered calls: query, init, remote-add,
depth-1 fetch, depth-50 fallback fetch, checkout. This is the call-count and
network-topology parity evidence.

## Post-Shim Identity

Identity was measured after wiring and proves only that the shim points at the
authoritative objects:

```text
post_shim_impl_identity=12/12
post_shim_type_identity=3/3
```

It does not substitute for the pre-shim behavior evidence above.

## Delivery and Gate Evidence

```text
entry counts: CI=1, README=1, source paths=2, package names=2
pytest: 883 passed, 1 skipped in 17.79s
targeted: 38 passed in 0.05s
lint-imports: Contracts: 6 kept, 0 broken
symbol audit: 108 SYMBOL OK + 4 MODULE-SCOPE OK; 0 MISMATCH; 0 INCOMPLETE
table bridge: 108 SYMBOL OK + 4 MODULE-SCOPE OK; all differences zero
bridge skill-3 rows: 12
skill validator: Skill is valid!
implementation arch matches: 0 (grep exit 1)
release/gbs_report/P4.5 design diff: empty
```

The three import-linter negative controls each returned exit 1:

1. `tizen_gerrit_fetch -> ci_triage`: root-layers broken.
2. `tizen_gerrit_fetch -> tizen_qb_discover`: root-layers and
   skill-independence broken.
3. `tizen_ci_shared -> tizen_gerrit_fetch`: root-layers and
   shared-no-uplink broken.

## Frozen-Design Execution Clarifications

1. Commit A's “diff hard limit” means **zero production-code diff**. Test
   changes were limited to the two named test files; the dev-memory evidence
   document legitimately accompanied the commit and did not widen production
   scope.
2. “Baseline remains green” means the pre-existing test set is not reduced and
   has no failure or new skip; it does not freeze the total when required tests
   are added. Commit B preserved all original 848 nodeids after the two
   intentional path relocations and added 36, establishing 883/1 for commit C.

## Deferred Ledger

| # | Obligation | Status | Closing batch | Current boundary |
|---|---|---|---|---|
| D1 | Decide whether same-named Gerrit/report helpers should be consolidated | DEFERRED | `triage-report` extraction | Independent definitions remain; no cross-module coupling was introduced |
| D2 | Delete all legacy compatibility shims, including three Gerrit type shims | DEFERRED | One-shot P4.9 final cleanup | Legacy imports remain compatible; new consumers use authoritative packages directly |
| D3 | Normalize dangling destination symlinks to `SOURCE_DIR_UNSAFE` | DEFERRED | `gerrit-submit` batch | Current `FileExistsError` propagation is documented and tested unchanged |
| D4 | Design unified timeout/cancellation, error normalization, and interruption cleanup | DEFERRED | `gerrit-submit` batch | Current calls have no internal timeout; injected deadlines and interruption residues are documented and tested |

No deferred item is ownerless, and none was silently implemented during this
behavior-preserving extraction.
