# P4.9 Skill-2 QB-Discover Closeout

Authority:
`docs/clang-fix-campaign/p49-skill2-qb-discover-design-v1.3-FROZEN.md`.

Implementation commits: `097294f`, `95ed550`, `41152fe`, `812b213`.

## Summary

- Frozen §6 implementation DoD: **8 DONE / 2 DEFERRED**.
- Additional downstream environment ledger: **1 DEFERRED**.
- Combined account: **8 DONE / 3 DEFERRED**.

## DoD Account

| # | DoD text | Status | Evidence anchor | Measured output excerpt |
|---|---|---|---|---|
| 1 | “全量 == 847/1 基线,原样全绿;测试 diff 仅 §5.1 两类” | DONE | `41152fe`, `812b213`; `stage09.../progress.md:99-115`, `:220-231`; `tests/unit/test_ci_triage.py:48-52` | Target closeout replay: `847 passed, 1 skipped in 17.81s`. The complete test diff from `d02a15a..812b213` is one import replacement in `test_ci_triage.py` (`1 insertion, 1 deletion`); no fixture or assertion changed. |
| 2 | “gbs_report.py 零 diff” | DONE | `41152fe`; hard boundary in frozen §6; closeout replay | `git diff --stat d02a15a..812b213 -- tizen-ci-triage/scripts/ci_triage/gbs_report.py` produced no output (`gbs_report_stat=<empty>`). |
| 3 | “同名件未合并:两侧各存一份” | DONE | `41152fe`; `tizen_qb_discover/sources.py:279-287`; `ci_triage/gbs_report.py:349-357` | `_normalize_text=2`, `_attrs_to_map=2`, `_class_names=2`; every count names one definition in each module. |
| 4 | “bridge 键加固四条断言” | DONE | `95ed550`; `progress.md:11-69`; `symbol_audit.py`; `table_audit_bridge.py` | (a) `before=81 after=81 verdict_changes=0`; (b) duplicate-SPECS root mismatch returned exit 1 for `skill-owned symbol defined outside its registered root`; (c) source-only twin returned OK; (d) both binary-key tools distinguished two definitions, while both name-only fixtures returned exit 1. |
| 5 | “旧址 sources.py 零 def/class” | DONE | `41152fe`; `ci_triage/sources.py:1-15`; `progress.md:99-102` | `rg -n '^(def|class) ' .../ci_triage/sources.py` produced no output; measured count `0`. |
| 6 | “六契约正向绿 + 三条负控制红 + 一条正向回归绿” | DONE | `812b213`; `.importlinter:1-46`; `progress.md:145-184` | Positive replay: `Contracts: 6 kept, 0 broken`. QB→orchestration, QB→convergence, and shared→QB each returned exit 1 under root-layers, skill-independence, and forbidden respectively; restored tree returned 6/0. This is the first measured activation of skill-independence. |
| 7 | “双道审计全绿;parity 掩码一致;arch 豁免” | DONE | `812b213`; `progress.md:186-213` | Symbol audit: `96 SYMBOL OK + 4 MODULE-SCOPE OK`, zero mismatch/incomplete. Bridge: same 96+4, all four difference classes plus parse errors zero. Shim/skill JSON SHA-256 both `96783e837cd25f76f79134c31edc5c4faee195ae302a4d84b62b360fe56f0d01`, `byte_equal=True`. `grep -c arch` printed 0 and exited 1. |
| 8 | “SKILL.md 落盘;shim 清单更新” | DONE | `812b213`; `tizen-qb-discover/SKILL.md:1-39`; frozen §2.2 lines 182-184; `progress.md:215-230` | Skill validator: `Skill is valid!`. The four-name `ci_triage.sources` shim is explicitly registered for the one-shot P4.9 final cleanup. |
| 9a | “同名件合并/去重议题 → triage-report 批次” | DEFERRED | Frozen §6 lines 271-272; step-0 moved-items ledger | Closing batch: `triage-report` extraction. Until then, the three same-named helpers deliberately remain independent authorities. |
| 9b | “shim 删除 → P4.9 末” | DEFERRED | Frozen §2.2 lines 182-184 and §6 lines 270-272 | Closing batch: one-shot P4.9 final shim cleanup after all six skill extractions. |

## Clean-Environment Comparison

The target machine is green at `847 passed, 1 skipped`. The independent Claude
clean environment reported `845 passed` plus these two failures:

- `tests/unit/test_build_runner.py::test_python_module_invocation_runs_fake_gbs`
- `tests/unit/test_workflow.py::test_workflow_werror_patch_ready_context_suppresses_generic_fallback`

The same two environment-sensitive failures were already reproduced at the
skill-1 closeout point `e7900bb`; the skill-1 frozen §4 records that independent
environment's stable two-failure precondition. In addition,
`git diff --stat e7900bb..812b213` for those two test files is empty. The
failures therefore predate skill-2 and were not introduced by this extraction.
They remain a named C21-family debt rather than being silently counted green.

| Item | Status | Closing batch | Evidence |
|---|---|---|---|
| Anchor the two residual environment-sensitive subprocess/workflow tests | DEFERRED | Next skill extraction batch, before its test changes | Independent Claude result supplied at closeout; zero diff for both test files from `e7900bb..812b213` |

## Definition-Column Contract

Commit `95ed550` added `definition` to all three frozen per-symbol authorities:

- step-0: `p49-step0-design-v2.1-FROZEN.md`;
- skill-1: `p49-skill1-convergence-judge-design-v1.4-FROZEN.md`;
- skill-2: `p49-skill2-qb-discover-design-v1.3-FROZEN.md`.

Canonical/history snapshots compare byte-for-byte. The bridge keys each row by
`(definition, symbol)` and has no name-only fallback. A temporary table lacking
the column produced:

```text
PARSE_ERROR | table lacks symbol/definition/owner columns after '### 2.2 ': | symbol | owner |
EXIT_CODE=1
```

## Eight Mechanical Synchronizations

| # | Inventory entry | Disposition |
|---|---|---|
| 1 | `HttpFetcher` declared consumer | `ci_triage.sources` → `tizen_qb_discover.sources` |
| 2 | `QuickBuildError` declared consumer | same replacement |
| 3 | `_raise_if_login_page` declared consumer | same replacement |
| 4 | `_urllib_fetch` declared consumer | same replacement |
| 5 | `DEFAULT_COOKIE_PATH` declared consumer | same replacement |
| 6 | `DEFAULT_QUICKBUILD_BASE_URL` declared consumer | same replacement |
| 7 | `load_cookie_jar` declared consumer | same replacement |
| 8 | `MODULE_OWNERS` | stale `ci_triage.sources` key replaced by `tizen_qb_discover.sources = skill/tizen_qb_discover`; not left as verified-inert |

Companion registration is also complete: `REGISTERED_SKILL_ROOTS` and
`ROOT_LAYERS_HIGH_TO_LOW` contain QB-discover; setuptools packages, mypy path,
CI mypy invocation, and development `PYTHONPATH` include its script root.

## Final Verification

Fresh closeout runs on `812b213`:

```text
pytest: 847 passed, 1 skipped in 17.81s
lint-imports: 6 kept, 0 broken
symbol_audit: 96 SYMBOL OK + 4 MODULE-SCOPE OK; 0 MISMATCH; 0 INCOMPLETE
table bridge: 96 SYMBOL OK + 4 MODULE-SCOPE OK; all differences and parse errors zero
same-name counts: _normalize_text=2, _attrs_to_map=2, _class_names=2
legacy sources shim def/class count: 0
gbs_report diff stat: empty
```

## 最终签批

| Signer | Date | Confirmation |
|---|---|---|
| Claude | 2026-08-15 | 独立核验七项，包含双道审计亲跑及两个环境敏感失败与 skill-1 基线的对比，确认零 finding。 |
| 评审 A | 2026-08-15 | 独立实跑全部门禁与 binary/name-only fixtures，确认 skill-2 CLOSED，零 finding。 |
| 评审 B | 2026-08-15 | 独立实跑全部门禁与 binary/name-only fixtures，确认八处机械同步完整、DEFERRED 可接受，零 finding。 |

状态：**skill-2 CLOSED @ `90b90e4`**（开发者放行日期：2026-08-15）。

系列里程碑：本批是 P4.9 skill 抽取系列首个终审零 finding 批次；
v1.0→v1.1 的 §1.2 动机重设及其断言 d 是直接原因，留档供后续批次参照。
