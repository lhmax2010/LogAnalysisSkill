# P4.9 Skill-4 Build-Verify Closeout

Authority:
`docs/clang-fix-campaign/p49-skill4-build-verify-design-v1.12.1-FROZEN.md`.

Pre-closeout commits: `148b7f6`, `09da87d`, `3da2529`, `f85bd58`,
`da6d503`. The sixth lifecycle commit is this closeout commit; its integrity is
anchored externally by Git and its SHA is not recorded inside itself
(`⑬/⑲`).

## Summary

- Frozen section 7 account: **16 DONE / 1 DEFERRED umbrella**.
- The umbrella is expanded below into **4 named DEFERRED obligations**, each
  with a closing batch.
- Baseline chain: commit A established **886 passed / 1 skipped**; commit B
  established **897 passed / 1 skipped**; commit C preserved 897/1 without
  changing tests.
- Audit state: **150 symbol entries + 4 module scopes**, zero mismatch and zero
  incomplete; the bridge independently agrees and prints the skill-4 split
  **29/12/4**.

## Baseline Chain

| Milestone | Preservation evidence | Result |
|---|---|---|
| Commit A `3da2529` | `stage11.../progress.md:375`; pre-A `884` collected nodeids, post-A `887`, `missing_baseline_nodeids=0`, three new tests | `886 passed, 1 skipped`; independently reproduced in the clean review environment |
| Commit B `f85bd58` | `progress.md:503`; pre-B `887`, post-B `898`, `missing_after_ownership_remap=0`, eleven new parameter instances | `897 passed, 1 skipped`; independently reproduced in the clean review environment |
| Commit C `da6d503` | `progress.md:722`; no test-file diff and the 898-nodeid collection is unchanged | `897 passed, 1 skipped`; independently reproduced in the clean review environment |

The comparisons are set-preservation checks, not total-only checks. Commit B
accounts for ownership moves before comparing nodeids; no earlier test silently
disappears behind the larger total.

## Section 7 DoD Account

| # | DoD text | Status | Evidence anchor | Measured output excerpt |
|---|---|---|---|---|
| 1 | “迁移三模式各按其验收 (§1.4)” | DONE | `3da2529`; `progress.md:251`, `:314` | Mode 1 `cmp` exit 0. Mode 2 zero-context diff contains exactly the two import replacements and `parents[2] -> parents[1]`. Mode 3 reports four AST source segments equal, changed hunks header-only, `S9_EXACT=True count=9`, no aliases, and no package-root S9 leaks. |
| 2 | “default_extra_pythonpath 迁移前后返回有序 tuple 相等且非空” | DONE | `3da2529`; `progress.md:269`, `:348`; `tests/unit/test_tizen_build_verify.py:692` | Pre-shim payload reports `field_equal[default_extra_pythonpath]=True` and `default_extra_pythonpath_nonempty=True`; the permanent anchor test is green. |
| 3 | “45 符号入册，bridge 三路径计数 29/12/4” | DONE | `da6d503`; `progress.md:560`, `:763`; `symbol_audit.py`, `table_audit_bridge.py` | Ten-sync checker was `21/21`; bridge prints every row under `tizen_build_verify/build_verify.py`, `edit_spec_guard.py`, and `workspace.py`, with exact counts `29/12/4`. |
| 4 | “三道 INCOMPLETE 护栏各生效” | DONE | `da6d503`; `progress.md:630`; `symbol_audit.py:1518` | Each skill module compares its complete top-level symbol set with SPECS in both directions and pins the count. The anti-abuse fixture sees `MixedCaseAlias` and exits 1. |
| 5 | “§2 例外正向绿、N1-N4 红、两契约各持 ignore、无 include_external_packages” | DONE | `da6d503`; `progress.md:649`; `.importlinter` | Positive run: `6 kept, 0 broken`. N1-N4 each exit 1 with root-layers and skill-independence both broken. Removing only root-layers' ignore gives `5 kept, 1 broken`; exact ignore count `2`, unmatched-alert count `2`, forbidden option count `0`. |
| 6 | “twin 八组各自注册，限定作用域精确命令证未合并” | DONE | `da6d503`; `progress.md:630` | Exact anchored probes report `SubprocessRunner=8`, `_git_stdout=3`, and `_read_json`, `_sha256_file`, `_build_subprocess_env`, `_is_relative_to`, `EDIT_SPEC_SCHEMA`, `_locate_edit` each `=2`; independent definitions remain. |
| 7 | “§4 分支表逐行有用例，DENIED 与 arch raw/norm 双向验证” | DONE | `f85bd58`; `progress.md:452`, `:478`; frozen §4 | Mechanical mapping reports `branch_rows=13`, `rows_with_test_names=13`, `missing_test_references=[]`. Timeout and tracked mutation assert `REPAIR_DENIED`; the four-arch matrix checks normalized GBS argv while record and failure key retain raw arch. |
| 8 | “pre-shim parity 一正三反 + post-shim identity 分列” | DONE | `3da2529`; `progress.md:269`, `:348` | Independent pre-shim modules have five equal payload partitions and one positive/three red normalizer controls. Post-shim identity covers all 45 migrated symbols plus 17 shared workspace bindings and is explicitly wiring-only evidence. |
| 9 | “三入口 1/1/2/2；两阶段分列；subprocess 盲区双处登记” | DONE | `da6d503`; `progress.md:703`, `:722`; `.importlinter`; `dev_memory/subprocess-boundaries.md` | CI/README/source-root/package-name counts are `1/1/2/2`. B used explicit path scaffolding; C ran after editable install with both path variables unset. The static blind spot is named in `.importlinter` and the campaign ledger. |
| 10 | “§2.4 十项机械同步；§2.5 三类 SPECS 与 relocation 六负控制” | DONE | `da6d503`; `progress.md:560`, `:596` | Sync assertions are `21/21`. SPECS implements 41 additions, three definition/owner supersessions, and one new `DEFAULT_MIN_FREE_BYTES` ruling. Relocation consumes and produces `3/3`; all six named negative categories exit 1 for their expected verdicts. |
| 11 | “护栏为集合等价且 MixedCaseAlias 负 fixture 红” | DONE | `da6d503`; `progress.md:630`; `symbol_audit.py:1518-1580` | Exact source and inventory sets agree at `29/12/4`; `--surface-fixture mixed-case-alias` prints `MISMATCH: present in source but not audited` and exits 1. |
| 12 | “parity 的 UUID/UTC/GIT_*_DATE 冻结生效” | DONE | `3da2529`; `progress.md:269` | UUID, shared-workspace UTC, author/committer dates, and formatter temporary directory are deterministic inputs. The only normalization is the named destination path mask. |
| 13 | “§5.5 正向门禁：全部 binding、准入证伪、per-binding 证伪、DoD 绑定、冻结版零漂移” | DONE | `148b7f6`, `da6d503`; `progress.md:49`, `:73`, `:93`, `:763` | All 22 bindings pass; every binding's constructed mutation exits red; v1.9 reports three drifts including both required known defects; current `BINDING_DRIFT=0`; all 17 DoD rows are bound or explicitly `PROCESS_ONLY`. |
| 14 | “§4 表用例名已回写真实用例” | DONE | `f85bd58`; frozen authority §4; `progress.md:452`, `:528` | All 13 rows name collected tests. Canonical/history copies are byte-equal after writeback, and the ledger was rebuilt before returning to green. |
| 15 | “§5.4 ledger 四条：自动导出、回跑/构造证伪、完整分区与 span 覆盖、实际集等于期望集” | DONE | `148b7f6`, `da6d503`; `progress.md:24`, `:49`, `:93`, `:106`, `:763` | Current check is `RESIDUAL_DRIFT=0`; ledger partition is `exported=130`, `retained=83`, `ignored=47`. All 47 OUT_OF_SCOPE anti-abuse mutations and all per-binding mutations turn red. |
| 16 | “relocation synthetic 三用例同时断言产出表/verdict” | DONE | `da6d503`; `progress.md:596`; `table_audit_bridge.py` | A→B consumes A and produces B; missing A leaves consumed empty and emits `UNMAPPED_SOURCE`; `{A→B,C→D}` with A+X outputs B+X, omits A/C/D, and emits `UNMAPPED_SOURCE` for C. All three exit 0 only when those assertions hold. |
| 17 | “DEFERRED：EDIT_SPEC_SCHEMA 单一权威、测试私有件收窄及既有延期” | DEFERRED | Frozen §7; named ledger below | Four obligations remain outside this behavior-preserving extraction. Each has a named closing batch and a tested current boundary. |

## Three Migration Modes

| Mode | Artifact | Acceptance evidence |
|---|---|---|
| 1: byte-for-byte | `edit_spec_guard.py` | Pre-shim `cmp` exit 0; authoritative skill copy remains byte-identical to the pre-move implementation. |
| 2: named whitelist | `build_verify.py` | `diff --unified=0` contains only edit-spec import, workspace import, and `parents[2] -> parents[1]`. |
| 3: split ownership | `workspace.py` | Four owned definition source segments are byte-equal; all other changed hunks are in the import header; shared binding set is exactly S9; no same-name aliases; S9 is absent from the skill package root. |

## Pre-Shim and Post-Shim Evidence

Pre-shim parity was captured before replacing any legacy module with a shim.
`importlib.reload` kept old and new implementation modules distinct. The five
closed payload partitions were result, ordered subprocess trace, destination
tree/markers, ordered extra-pythonpath tuple, and controlled environment.

```text
field_equal[result]=True
field_equal[runner_trace]=True
field_equal[destination_tree]=True
field_equal[default_extra_pythonpath]=True
field_equal[controlled_environment]=True
normalizer_positive_destination_only=True
normalizer_negative[failure_class]=True
normalizer_negative[command_order]=True
normalizer_negative[repair_allowed]=True
```

UUID, UTC, `GIT_AUTHOR_DATE`, `GIT_COMMITTER_DATE`, and formatter
`TemporaryDirectory` were frozen. Destination masking was applied only to
named path-bearing fields, never to the payload globally.

Post-shim identity was then measured separately. It proves only that the three
legacy locations re-export the authoritative implementation and shared
workspace objects; it is not substituted for the behavior evidence above.

## Authoritative 13-Row Branch Map

| Contract row | Test coverage |
|---|---|
| PASS | `test_pass_writes_verification_record_and_commits_before_build` |
| `apply_failed` at edit-spec validation / formatter / git apply | `test_invalid_edit_spec_fails_before_build`; `test_apply_failure_fails_before_build`; `test_diff_check_failure_returns_apply_failed_and_preserves_applied_worktree` |
| `no_effective_changes` before and after apply | `test_no_effective_changes_fails_before_build`; `test_successful_apply_with_no_changed_paths_returns_no_effective_changes` |
| unexpected changed paths | `test_unexpected_changed_paths_are_checked_before_no_effective_changes` |
| `git diff --check` failure | `test_diff_check_failure_returns_apply_failed_and_preserves_applied_worktree` |
| timeout + `REPAIR_DENIED` | `test_gbs_timeout_fails_without_repair` |
| tracked mutation + `REPAIR_DENIED` | `test_build_mutated_tracked_source_after_commit_fails` |
| GBS failure classification | `test_gbs_fail_source_werror_returns_repair_allowed`; `test_gbs_fail_toolchain_denylist_not_repair_allowed` |
| analyzer nonzero | `test_analyzer_nonzero_exit_returns_no_evidence_and_preserves_worktree` |
| analyzer missing evidence | `test_analyzer_success_without_evidence_returns_none_and_preserves_worktree` |
| marker exception propagates | `test_marker_write_exception_propagates_before_db_write_and_leaves_clean_copy` |
| DB exception propagates | `test_pass_write_record_failure_is_not_silent`; `test_db_write_exception_propagates_after_marker_and_preserves_protected_copy` |
| four arch raw/norm cases | `test_gbs_arch_removes_standard_prefix`; `test_arch_matrix_normalizes_gbs_argv_and_preserves_raw_state` |

The exception tests assert disk state, not only return values: cleanup absence,
applied source retention, analyzer directory/evidence presence, marker state,
Git cleanliness, and state-DB rows are checked at the relevant interruption
point.

## Gate and Audit Evidence

```text
pytest: 897 passed, 1 skipped
single skill behavior file (test_tizen_build_verify.py): 44 passed, 1 skipped
three-file targeted set (skill + legacy wiring + real-git integration): 53 passed, 1 skipped
lint-imports: 6 kept, 0 broken
symbol audit: 150 SYMBOL OK + 4 MODULE-SCOPE OK (48 covered); 0 MISMATCH; 0 INCOMPLETE
table bridge: relocation consumed=3/3, produced=3/3; 150+4; all differences zero
skill-4 bridge split: 29/12/4
design check: RESIDUAL_DRIFT=0; BINDING_DRIFT=0
admission v1.9: BINDING_DRIFT=3; RED_AS_EXPECTED
entry counts: 1/1/2/2
release-v1.4.0 / gbs_report.py / P4.5 design.md diff: empty
```

The four import-linter exception controls each exit 1 with both root-layers
and skill-independence broken. Removing only the root-layers ignore also exits
1 while independence remains green, proving that the precise exception is
held independently by both contracts. `include_external_packages` is absent.

## Frozen-Design Execution Clarification

The v1.12 freeze exposed a Python resolution conflict immediately after the
first real implementation action: exporting package-root function
`build_verify` shadows the same-named implementation submodule for dotted
string monkeypatch resolution. The v1.12.1 in-place ruling preserved the
public API and limited the six affected tests to an equivalent object patch:

```python
module = importlib.import_module("tizen_build_verify.build_verify")
monkeypatch.setattr(module, name, replacement)
```

Package-root API assertions exclude naturally attached submodule attributes;
they continue to test the explicit nine-name `__all__`. This is an execution
mechanics correction, not a production behavior change. The authority/history
pair and both design gates were regenerated and revalidated before commit A
continued.

## Deferred Ledger

| # | Obligation | Status | Closing batch | Current boundary |
|---|---|---|---|---|
| D1 | Make `EDIT_SPEC_SCHEMA` a single authority | DEFERRED | `patch-suggest` extraction batch | The two byte-equal constants remain separate and are recorded as a twin; no silent consolidation occurred. |
| D2 | Decide whether same-named build/report/formatter helpers should be consolidated | DEFERRED | `triage-report` extraction batch | All eight twin groups remain physically separate and scope-limited probes record their current counts. |
| D3 | Delete build-verify and other legacy compatibility shims | DEFERRED | One-shot P4.9 final cleanup | Old build-verify/edit-guard paths are pure re-exports; old workspace is a composition shim. Current callers remain compatible. |
| D4 | Narrow tests that consume implementation-private symbols | DEFERRED | One-shot P4.9 final cleanup | Behavior coverage remains explicit, but private test imports are not promoted into package-root API. |

No deferred item is ownerless, and none was silently implemented during this
behavior-preserving extraction.

## Targeted-Test Counting Convention

The two supported targeted counts are intentionally different and must be
quoted with their file scope:

- Skill behavior only:
  `tests/unit/test_tizen_build_verify.py` = **44 passed, 1 skipped**.
- Three-file verification set:
  `tests/unit/test_tizen_build_verify.py` +
  `tests/unit/test_build_verify_legacy_wiring.py` +
  `tests/integration/test_build_verify_real_git.py` =
  **53 passed, 1 skipped**.

The second count includes compatibility wiring and existing real-Git
integration coverage; it must not be reported as the size of the skill
behavior file.

## 最终签批

| 签批方 | 日期 | 结论 |
|---|---|---|
| Claude | 2026-09-04 | 独立核验每个 commit 的干净环境结果一致，亲跑双道审计 `150+4` 与 §5.4/§5.5 双门禁，确认 bridge 三路径 `29/12/4`，并验证 `include_external_packages` 零命中，结论 CLOSED。 |
| 评审 A | 2026-09-04 | 独立复跑全部门禁、准入证伪与破坏性验证，零 finding，确认 skill-4 CLOSED。 |
| 评审 B | 2026-09-04 | 独立复跑全部门禁、准入证伪与破坏性验证，零 finding，确认 skill-4 CLOSED。 |
| 评审 C | 2026-09-04 | 独立复跑全部门禁、准入证伪与破坏性验证，零 finding，确认 skill-4 CLOSED。 |

**状态：skill-4 CLOSED @ `7bfa070`（开发者放行日期：2026-09-04）。**
