# P4.9 Skill-6 Triage-Report Closeout

Authority:
`docs/clang-fix-campaign/p49-skill6-triage-report-design-v1.8-FROZEN.md`.

Pre-closeout commits: `bdb5a55`, `3dc0466`, `3da12a4`, `2cc3dd3`,
`dfbbf3b`. The closeout commit is anchored externally by Git and its SHA is
not recorded inside itself (`⑬/⑲`).

## Summary

- Frozen section 8 account: **10 DONE / 0 DEFERRED**.
- Skill-6 introduces no implementation deferral. The five inherited terminal
  obligations remain in the P4.9 extraction-phase ledger and must close before
  P4.9 can close.
- Baseline chain: **912/1 -> 914/1 -> 941/1**, with no missing baseline test at
  either transition and the same results reproduced in the clean review
  environment.
- Final audit state: **197 per-symbol entries + 4 module scopes**, zero
  mismatch/incomplete; the bridge independently agrees and prints the skill-6
  split **21/3**.

## Baseline Chain

| Milestone | Preservation evidence | Result |
|---|---|---|
| Freeze/A0 `bdb5a55`/`3dc0466` | `stage13.../progress.md:136-152` | `912 passed, 1 skipped`; clean-environment baseline reproduced |
| Commit A `3da12a4` | `progress.md:323-337`: before `913` collected, after `915`, `missing=0`, two package/wiring additions | `914 passed, 1 skipped`; clean environment matched |
| Commit B `2cc3dd3` | `progress.md:363-386`: `missing_function_names=[]`, seven moved ASTs equal, 27 delta tests | `941 passed, 1 skipped`; clean environment matched |
| Commit C `dfbbf3b` | `progress.md:734-756`: no test changes; installed no-scaffold run preserves commit-B collection | `941 passed, 1 skipped` |

The baseline is a set-preservation claim, not a frozen-total claim. Seven
behavior tests moved owners without changing their function ASTs; all net-new
tests pass and no existing case became a failure or new skip.

## Section 8 DoD Account

| # | DoD text | Status | Evidence anchor | Measured output excerpt |
|---|---|---|---|---|
| 1 | “24 符号 parser-only + bridge 两 definition 路径精确 21/3” | DONE | `3dc0466`, `dfbbf3b`; `progress.md:19-42`, `:506-542` | Parser-only `24/24`; bridge `197+4`, all difference counts zero; skill rows split `21/3`; both exact-set guards reject `MixedCaseAlias`. |
| 2 | “gbs_report 模式二仅一处白名单; report 模式一 cmp 空; 旧址双纯 shim” | DONE | `3da12a4`; `progress.md:163-183`, `:266-287` | `report.py` SHA/cmp equal; zero-context gbs diff contains only the shared HTTP import; both legacy modules have zero top-level def/class. |
| 3 | “七约束逐条销账(3 执行 + 4 未触发各附依据)” | DONE | Frozen §2; `3da12a4`, `dfbbf3b`; seven-row account below | Constraints 2/6/7 execute. Constraints 1/3/4/5 do not trigger because fetch and parse move together without raw/shell/refactoring states. |
| 4 | “三项同名件议题裁决关闭... EDIT_SPEC_SCHEMA 排除、归 patch-suggest” | DONE | Frozen §3/§3.1; `dfbbf3b`; `progress.md:652-679` | All three optional consolidation debates close as “keep independent”; D2 is limited to seven non-schema twins. `EDIT_SPEC_SCHEMA` remains owned by patch-suggest. |
| 5 | “8 组 twin 各自注册,精确命令证未合并” | DONE | `dfbbf3b`; `progress.md:652-679`; `symbol_audit.py` | Eight scoped probes each return exactly two definitions across qb-discover and triage-report; binary inventory keys preserve independent ownership. |
| 6 | “契约绿 + 三负控红 + 下行配对” | DONE | `dfbbf3b`; `progress.md:545-650` | Positive `6 kept, 0 broken`; each upward/sideways negative exits 1. Real quickbuild_http/types imports are the legal downward counterpart to negative 3. |
| 7 | “分支表逐行用例; pre/post-shim 分列; 三入口; 两阶段” | DONE | `3da12a4`, `2cc3dd3`, `dfbbf3b`; `progress.md:212-290`, `:408-436`, `:681-713`, `:734-750` | All 25 rows name collected tests; pre-shim six-part parity is distinct from 9+15 identity; entry counts `1/1/2/2`; B scaffolding and C no-scaffold evidence are separate. |
| 8 | “双门禁全绿(A0 独立数据 + 前批回归不退化)” | DONE | `3dc0466`, `2cc3dd3`, `dfbbf3b`; `progress.md:64-124`, `:438-477`, `:715-731` | Three independent ledgers are green; skill-4 and skill-5 admissions remain red; skill-6 admission is red `2/2`. |
| 9 | “§11 准入:声明值由脚本产出,ID 唯一,引用闭合,EXTERNAL_BRANCH 绑定齐” | DONE | `3dc0466`, `dfbbf3b`; `progress.md:19-42`, `:292-317`, `:726-731` | `19/24`, `22/4`, `ids=69`, `collisions=0`; rows `25`, referenced `62`, unreferenced `7`, external `2`, unknown `0`; both external rows require `COOKIE_EXPIRED`. |
| 10 | “P4.9 末批次清单核实:本批不新增实施 DEFERRED” | DONE | Frozen §0.3/§3/§11; closed-decision and terminal-ledger sections below | The three merge debates close, schema ownership stays with patch-suggest, and BoolOp remains a template design question. The inherited terminal list remains exactly five named obligations. |

## Step-0 Seven Constraints

| # | Disposition | Evidence and reason |
|---|---|---|
| 1, raw fields cover parser input | NOT TRIGGERED | No raw type is introduced. Fetch and parse move together; frozen §2 records the future input closure as `html_text`, `build_id`, `arch`, and `iframe_url`. |
| 2, migrate the complete call closure | EXECUTED | Commit A moves the entire gbs_report semantic closure. Its only repository dependency is the lower shared HTTP layer; iframe/parser helpers stay local and there is no uplink. |
| 3, phase structural assertions | NOT TRIGGERED | No `to-be-refactored` composition shell exists. |
| 4, use three audit states | NOT TRIGGERED | All 24 migrated symbols enter as `existing`; no deferred structural state exists. |
| 5, choose composition shell or direct split | NOT TRIGGERED | The premise is avoided by the frozen decision to keep fetch and parse together. No raw/shell boundary is created. |
| 6, place iframe/html helpers by the measured closure | EXECUTED | `find_iframe_src`, `_IframeParser`, and `_attrs_to_map` stay in the skill. The qb-discover twin has a different type/model closure, so no unowned htmlutil module is created. |
| 7, restore inventory and guard together | EXECUTED | Commit C `dfbbf3b` adds the 21 gbs_report SPECS rows and its exact-set `surface_checks` entry together. The same run prints 21 bridge rows and the MixedCaseAlias negative exits 1. |

Constraint 7 has two independent same-commit proofs: the positive inventory
and bridge output names all 21 rows, while the surface fixture proves that an
extra mixed-case public symbol is rejected rather than silently absorbed.

## Closed Consolidation Decisions

| Source debate | Decision | Mechanical boundary |
|---|---|---|
| Skill-2 eight HTML/parser twins | CLOSED: keep independent | Eight exact scoped probes return two definitions each; importing between the two skills breaks skill-independence. |
| Skill-3 D1 Gerrit/report helper twins | CLOSED: retain the already frozen independent definitions | These helpers do not overlap either skill-6 module. Closing preserves prior authorities; consolidation would require reopening their designs. |
| Skill-4 D2 build/report/formatter twins | CLOSED for the **seven non-schema twins** | `EDIT_SPEC_SCHEMA` is excluded because its issue is schema-version authority, not implementation-helper reuse. |

`EDIT_SPEC_SCHEMA` remains assigned to the patch-suggest owner and is not a
skill-6 deferral or one of the five P4.9 terminal obligations.

## Authoritative 25-Row Branch Map

| Contract row | Collected test names |
|---|---|
| Fetch success | `test_gbs_report_fetch_uses_iframe_src_without_reencoding`; `test_fetch_gbs_report_preserves_raw_arch_in_url_and_packages` |
| Report-page login | `test_fetch_gbs_report_rejects_report_page_login` |
| Missing iframe | `test_gbs_report_without_iframe_reports_no_gbs_report`; `test_fetch_gbs_report_no_iframe_error_preserves_raw_arch` |
| Iframe-page login | `test_fetch_gbs_report_rejects_iframe_page_login` |
| No build-status table | `test_parse_gbs_report_packages_ignores_non_status_tables` |
| Package log download success | `test_download_gbs_package_buildlog_returns_text` |
| Iframe HTTP non-200 | `test_gbs_report_iframe_download_failure_remains_retryable` |
| Missing buildlog URL | `test_download_gbs_package_buildlog_requires_url` |
| Package-log HTTP non-200 | `test_download_gbs_package_buildlog_rejects_non_200` |
| Four malformed-row exits | `test_row_to_package_rejects_short_row`; `test_row_to_package_rejects_empty_spec_name`; `test_row_to_package_rejects_header_row`; `test_row_to_package_rejects_missing_status_anchor`; `test_row_to_package_rejects_unknown_status` |
| Render fixture A | `test_render_report_fixture_a_all_optional_fields_present` |
| Render fixture B | `test_render_report_fixture_b_all_optional_fields_absent` |
| Render fixture C | `test_render_report_fixture_c_outer_present_inner_absent` |
| Render fixture D | `test_render_report_fixture_d_middle_present_leaf_absent` |
| Primary location file+line | `test_primary_location_includes_file_and_line` |
| Primary location file only | `test_primary_location_returns_file_without_line` |
| Primary location absent | `test_primary_location_returns_na_without_file` |
| Status class priority | `test_status_from_anchor_prefers_status_classes` |
| Status text fallback | `test_status_from_anchor_falls_back_to_text` |
| Class/text conflict | `test_status_from_anchor_class_wins_over_conflicting_text` |
| `successful` alias | `test_status_from_anchor_accepts_successful_alias` |
| Build-status-table three states | `test_looks_like_build_status_table_covers_three_detection_states` |
| Package row href present/absent | `test_row_to_package_builds_urls_with_and_without_href` |
| `failed_packages` mixed filtering | `test_gbs_report_failed_packages_filters_mixed_statuses` |
| Raw arch success/error pair | `test_fetch_gbs_report_preserves_raw_arch_in_url_and_packages`; `test_fetch_gbs_report_no_iframe_error_preserves_raw_arch` |

The malformed-row row contains separate empty-`spec_name` and header-row
inputs for the two line-317 operands. The class/text conflict proves class
priority (`failed` class plus `Succeeded` text). Both `EXTERNAL_BRANCH` login
tests assert `QuickBuildError.code == "COOKIE_EXPIRED"`. The four render
fixtures remain independent, and the arch success case proves packages are
non-empty before checking URL, report arch, and every package arch.

## Pre-Shim And Post-Shim Evidence

Pre-shim parity was captured before either legacy implementation became a
shim, using four explicitly reloaded and distinct module objects and no real
QuickBuild network traffic. Its six payload partitions are:

1. all GBS report/package fields plus an independently materialized ordered
   `failed_packages` tuple;
2. ordered fake-fetcher URL/cookie/kwargs calls;
3. all `TriageReportData` fields plus complete rendered text;
4. controlled cookie/base-URL inputs;
5. exception type, code, and full message;
6. exact package-buildlog return text.

```text
field_equal[gbs_report]=True
field_equal[fake_fetcher_trace]=True
field_equal[triage_render]=True
field_equal[controlled_environment]=True
field_equal[error]=True
field_equal[download_gbs_package_buildlog]=True
payload_equal=True
normalizer_positive.cookie_path_only=True
normalizer_negative.failed_packages=True
normalizer_negative.http_call_order=True
normalizer_negative.iframe_url=True
```

Only the named cookie path field is masked; no payload-wide replacement is
used. Post-shim identity is recorded separately as `9+15` and proves wiring
only. It is not substituted for the independent behavior evidence.

## Four Gate Families

```text
skill-4 ledger: RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | bindings=22
skill-5 ledger: RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | bindings=8
skill-6 ledger: RESIDUAL_DRIFT=0 | BINDING_DRIFT=0 | bindings=5
branch parser-only: 24/24 | missing=0 | extra=0 | OWNER_MISMATCH=0
branch inventory: ids=69 | collisions=0 | unknown_refs=0 | missing_reasons=0
admission-v17: required=2/2 | RED_AS_EXPECTED | exit=1
```

The three ledger datasets are separate files and no batch overwrites another.
The branch inventory reports `19/24` and `22/4` both before and after source
migration. Parser-only and branch admission complete the fourth gate family.

## Delivery And Two-Stage Verification

```text
CI mypy command                     1
README script root                  1
pyproject script-root occurrences   2
pyproject package occurrences       2
```

Commit B used explicit `PYTHONPATH`/`MYPYPATH` scaffolding. Commit C refreshed
the editable installation and reran pytest, mypy, ruff, py_compile,
lint-imports, symbol audit, and bridge under
`env -u PYTHONPATH -u MYPYPATH`. The final results are `941 passed, 1 skipped`,
`6 kept, 0 broken`, and `197+4` for both audit views. `release-v1.4.0/` remains
an unchanged historical snapshot.

## Execution Clarifications

1. The branch-inventory source-path change in commit A is a mechanical
   evidence-path synchronization, not a predicate change. Only the two source
   paths changed; selectors, IDs, subset rules, external bindings, and
   uniqueness checks stayed unchanged. Before and after both report
   `19/24`, `22/4`, 69 IDs, and zero collisions.
2. “X is a freeze prerequisite” means X's real execution must precede the
   freeze. Its artifact commit may follow the freeze commit. Here parser-only
   and branch inventory ran before `bdb5a55`; `3dc0466` then Git-anchored the
   exact tool/data version and outputs.

## Deferred And Terminal Account

Skill-6 adds **no implementation DEFERRED**:

- all three inherited consolidation debates are closed;
- `EDIT_SPEC_SCHEMA` belongs to patch-suggest, not this batch;
- BoolOp per-operand obligations remain a template-level design question and
  do not enter the P4.9 terminal ledger.

The extraction phase still carries exactly five inherited terminal
obligations:

| # | Terminal obligation | Closing work |
|---|---|---|
| T1 | Delete every legacy compatibility shim | One-shot P4.9 final cleanup |
| T2 | Narrow tests that consume implementation-private symbols | Same final cleanup, without promoting private names into package APIs |
| T3 | Normalize dangling-symlink handling | P4.9 final cross-skill behavior-unification batch |
| T4 | Unify timeout, cancellation, interruption, residual state, and result mapping | Same behavior-unification batch, implementing skill-5 frozen §3.2 |
| T5 | Decide protected-marker write order | Terminal design review must choose reorder or retain-with-rationale; “recorded” is not closure |

**Terminal clause:** unfinished T1-T5 blocks P4.9 closure. None may be handed
to a later phase or silently reclassified.
