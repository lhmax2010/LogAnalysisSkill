# P4.5 Code Review Package

## Package Identity

- Diff base: `85310ef684726ee65be480e2b5cb582f1a689ee4`
- Diff head: `b1ad87e`
- Code-ready checkpoint: `checkpoint/p45_code_ready` at
  `269321820abe0eddb7db345dcb26ffaedc7127c6`
- Frozen design: v1.5.16-FROZEN

This package contains the complete `git diff 85310ef..b1ad87e`, including the
stat, after the mapping tables below. It is self-contained for reviewers who
cannot access the repository.

## Review Request

Return findings prefixed by `[BLOCKER]`, `[MAJOR]`, `[MINOR]`, or `[NIT]` and
one of `[CODE_ISSUE]`, `[DESIGN_SUGGESTION]`, or `[ALTERNATIVE]`. Focus on:

- transaction boundaries and accidental nested `BEGIN IMMEDIATE` operations;
- uniqueness/CHECK guards and whether Python paths can bypass them;
- crash recovery, especially PASS-written/link-missing recovery;
- append-only guarantees and deterministic identity/payload reconstruction;
- wrapper ordering, fail-closed exits, and the one-JSON stdout contract.

Finding closure follows R14: BLOCKER must be fixed; MAJOR must be fixed or
explicitly waived by the developer; MINOR is recorded in dev-memory TODOs;
NIT is advisory.

## Contract to Code Map

| Contract | Implementation location | Review focus |
|---|---|---|
| Section 3.4 seven-table schema | `campaign_state.py` schema constants and `ensure_schema` | indexes, CHECKs, FKs, append-only assumptions |
| Section 4.2 state APIs | `campaign_state.py:285-840` | identity checks, immediate transactions, payload binding |
| Section 4.1 reconciliation table | `campaign_state.py:841` `reconcile_pass_and_invocations` | a0/a/b/b-prime/c/d priority, savepoints, no nested transaction |
| Section 4.1 previous selection | `previous_evidence.py` | latest substantive evidence, rebaseline fallback, hash checks |
| Section 4.1 nine-step wrapper | `campaign_repair_step.py:137` | lock through outcome ordering and short-circuit safety |
| CLI/stdout contract | `cli.py` campaign-repair-step parser/handler | routing, exit code, exactly one JSON document |

## DoD to Test Map

| DoD area | Test evidence |
|---|---|
| Seven tables and physical guards | `test_ensure_schema_creates_exact_campaign_tables_and_required_guards`; `test_campaign_unit_check_reverse_validation_fails_when_check_is_removed`; `test_convergence_index_reverse_validation_allows_duplicate_when_dropped` |
| Budget/locking | `test_two_connections_cannot_overspend_one_invocation_budget`; `test_consume_maps_immediate_lock_timeout_to_busy_without_writing`; `test_lock_busy_returns_exit_five_without_creating_round` |
| Atomic link/adoption | `test_link_verification_and_pass_convergence_are_atomic`; `test_link_mismatch_rolls_back_link_and_event`; secondary-adoption transaction/concurrency tests |
| Reconciliation recovery | `test_reconcile_relinks_current_pass_in_one_transaction_and_rebuilds_paths`; `test_reconcile_uses_transaction_internal_link_primitive`; `test_relink_savepoint_prevents_half_link_when_event_insert_fails` |
| A0 integrity | half-state, duplicate binding, wrong round/invocation, and bypassed-attribution tests in `test_campaign_reconcile.py` |
| Exit priority | `test_orphan_pass_overrides_current_linked_success_but_keeps_clean_writes`; `test_orphan_pass_overrides_current_relink_but_commits_the_clean_relink` |
| Frozen wrapper order | `test_pass_runs_frozen_order_and_emits_fixed_schema`; `test_new_round_with_old_hash_dies_in_create_round_before_reconcile`; `test_linked_recovery_runs_before_missing_previous_precheck` |
| HELD/rebaseline reachability | `test_previous_precheck_writes_arch_scoped_held_and_enables_rebaseline`; reverse test removing the status write |
| Previous evidence | pass/n-a/rebaseline/missing-substantive tests in `test_campaign_repair_step.py` |
| Output/entrypoint | deterministic reconciliation/warning tests; `test_python_m_campaign_repair_step_emits_one_json_document` |

## Test Baseline

- Campaign state tests collected: 29.
- Reconciliation tests collected: 20.
- Repair-step tests collected: 21.
- Code-ready full regression: 820 passed, 1 skipped.
- Code-ready mypy: 26 source files clean.
- P0 checker self-test: 33/33; design checker: 0 problems.

## Diff Stat

```text
 docs/clang-fix-campaign/checkpoints.md             |    8 +
 .../clang-fix-campaign/design_changes/change_32.md |   54 +
 .../clang-fix-campaign/design_changes/change_33.md |  112 +
 .../clang-fix-campaign/design_changes/change_34.md |   82 +
 .../clang-fix-campaign/design_changes/change_35.md |   87 +
 .../clang-fix-campaign/design_changes/change_36.md |  104 +
 .../clang-fix-campaign/design_changes/change_37.md |   94 +
 .../clang-fix-campaign/design_changes/change_38.md |  108 +
 docs/clang-fix-campaign/dev_memory/INDEX.md        |   34 +
 docs/clang-fix-campaign/dev_memory/methodology.md  |   33 +
 .../dev_memory/stage01_design_convergence/plan.md  |   21 +
 .../stage01_design_convergence/progress.md         |   21 +
 .../stage01_design_convergence/result.md           |   35 +
 .../dev_memory/stage02_p0_gates/plan.md            |   21 +
 .../dev_memory/stage02_p0_gates/progress.md        |   12 +
 .../dev_memory/stage02_p0_gates/result.md          |   30 +
 .../dev_memory/stage03_m1_state_layer/plan.md      |   18 +
 .../dev_memory/stage03_m1_state_layer/progress.md  |   12 +
 .../dev_memory/stage03_m1_state_layer/result.md    |   19 +
 .../dev_memory/stage04_m2_reconcile/plan.md        |   14 +
 .../dev_memory/stage04_m2_reconcile/progress.md    |   11 +
 .../dev_memory/stage04_m2_reconcile/result.md      |   20 +
 .../dev_memory/stage05_m3_repair_step/plan.md      |   23 +
 .../dev_memory/stage05_m3_repair_step/progress.md  |   12 +
 .../dev_memory/stage05_m3_repair_step/result.md    |   22 +
 docs/clang-fix-campaign/e2e-smoke-runbook.md       |  116 +
 docs/clang-fix-campaign/remediation-task.md        |  102 +
 .../review/claude-review-ledger.md                 |   39 +
 .../review/p0-signature-audit-v1.5.16.md           |   23 +
 tests/unit/test_campaign_reconcile.py              |  816 +++++++
 tests/unit/test_campaign_repair_step.py            |  989 +++++++++
 tests/unit/test_campaign_state.py                  | 1032 +++++++++
 .../scripts/ci_triage/campaign_repair_step.py      | 1167 ++++++++++
 .../scripts/ci_triage/campaign_state.py            | 2288 ++++++++++++++++++++
 tizen-ci-triage/scripts/ci_triage/cli.py           |   52 +
 .../scripts/ci_triage/previous_evidence.py         |  175 ++
 36 files changed, 7806 insertions(+)
```

## Full Diff

<!-- BEGIN FULL DIFF: git diff 85310ef..b1ad87e -->
````````diff
diff --git a/docs/clang-fix-campaign/checkpoints.md b/docs/clang-fix-campaign/checkpoints.md
new file mode 100644
index 0000000..36cbbf8
--- /dev/null
+++ b/docs/clang-fix-campaign/checkpoints.md
@@ -0,0 +1,8 @@
+# Clang Fix Campaign Checkpoints
+
+| Tag | Commit | Coverage | Rollback command | State after rollback |
+|---|---|---|---|---|
+| `checkpoint/p45_code_ready` | `269321820abe0eddb7db345dcb26ffaedc7127c6` | P0 contract gates; M1 state; M2 reconciliation; M3 repair-step and tests | `git reset --hard checkpoint/p45_code_ready` | Code-ready P4.5 implementation with no RA/RB documentation or RC smoke results |
+
+The rollback command is destructive to uncommitted work. Inspect and preserve
+the worktree before using it.
diff --git a/docs/clang-fix-campaign/design_changes/change_32.md b/docs/clang-fix-campaign/design_changes/change_32.md
new file mode 100644
index 0000000..2f8f2e3
--- /dev/null
+++ b/docs/clang-fix-campaign/design_changes/change_32.md
@@ -0,0 +1,54 @@
+# change_32:v1.5.7 双 review 合并修正(→ v1.5.8)
+
+**状态(v1.5.9 收口)**:已采纳并落盘于 design.md v1.5.8。**本文与主文
+不一致处一律以主文为准**;下列四处为落盘时的有意修订,已回写(原稿
+文本保留删除线语义、以"作废"标注)。A1 的步骤序含隐藏回归,由
+**change_33 补正**(第 3 步联合对账,relink 先行)。
+
+## 落盘时的四处修订(v1.5.9 回写,消除"第二权威")
+
+1. **A2.2 存储位置(作废原稿"仅真实列、payload 不含")**:落盘为
+   **payload 含 `invocation_event_id` 且与真实列同值**,走 v1.5.6
+   提升规则(同 round_index/arch_norm)。理由:原稿方案迫使
+   `append_event` 改冻结签名,提升规则零签名变更且与既有契约同构。
+2. **A3 条件表(作废原稿"invocation_event_id 非空只能 PASS/FAIL")**:
+   orphan 补写、apply/analyzer/toolchain failed、previous_evidence_missing
+   **携带 invocation_event_id 且 result=n_a**。落盘口径:**按 reason
+   分流**——PASS/FAIL 限 6a/6b 实质 outcome;n_a 限六 reason 白名单;
+   `invocation_event_id IS NULL` 仅 reason='rebaselined'。
+3. **B7(作废原稿"落 PENDING_CLEANUP 审计事件")**:落盘为**不引入
+   新事件类型**——status_log 终态行为凭证、`iter_<round>` 派生路径
+   可枚举;人工恢复算法见主文 §4.1(v1.5.9 显式化)。
+4. **错误码名对齐 §4.3(作废 TG 表中的 E_* 临时名)**:
+   `E_INVOCATION_BINDING` → 绑定校验失败复用 **StateInconsistent**
+   (持错 receipt/状态被篡改同族信号,不新增码);
+   `E_PRIMARY_FINGERPRINT_MISSING` → **REJECTED_PRIMARY_BASELINE_MISSING**
+   (已入 §4.3)。prompt 与测试断言一律按 §4.3 名。
+
+## 原始裁决记录(历史,保留供审计)
+
+A1 索引重锚 / A2 receipt 端到端 / A3 条件枚举 / A4 冻结签名语法 /
+B5 HELD 绑 arch / B6 三元组 CHECK / B7 泄漏窗口 / B8 primary-first /
+C prompt 补丁 / D 测试闸门 TG-1~8 / E checker 硬化(CK-API-01 /
+CK-IDX-01 / CK-XREF-01 / CK-MMD-01 + Ruff 清零)/ F 执行顺序与 DoD。
+详细内容见 v1.5.8 主文对应章节;TG 编号在主文 DoD 中已展开为具体
+用例文本,以主文 DoD 为准。
+
+## 附录 A:探针实测输出(2026-08-04 第一轮,内存 SQLite)
+
+```
+[OK] 合法序列: orphan补写(X) + 实质outcome(Y) 共存通过
+[OK] TG-1 同 invocation 第二条 PASS(verdict=n_a): IntegrityError(UNIQUE constraint failed: campaign_gate_events.invocation_event_id)
+[OK] TG-2 同 invocation PASS 后补实质 verdict: IntegrityError(UNIQUE constraint failed: campaign_gate_events.invocation_event_id)
+[OK] 同 invocation 二次实质 outcome: IntegrityError(UNIQUE constraint failed: campaign_gate_events.invocation_event_id)
+[OK] rebaselined(NULL) 多条不撞索引(合法,由 reason 白名单约束)
+[OK] 反向验证: v1.5.7 谓词下同 invocation 双 PASS 落库成功 —— 逃逸面实锤
+[OK] TG-5 三元组半空插入: IntegrityError(CHECK constraint failed: ...)
+[OK] 全空(arch 拒绝)与全非空均可插入
+```
+
+结论:v1.5.7 谓词的 PASS 逃逸为实测事实而非纸面推理;v1.5.8 索引对
+三类违例均拒、对合法序列均放行。**局限(change_33 教训)**:本轮探针
+只枚举了"事件类型 × reason"的数据组合,未枚举**崩溃重入的步骤时序**,
+漏掉第 1 步补写与第 3 步 relink 争夺同一槽的死路——已由 change_33
+探针复现并修正。
diff --git a/docs/clang-fix-campaign/design_changes/change_33.md b/docs/clang-fix-campaign/design_changes/change_33.md
new file mode 100644
index 0000000..4a48d9c
--- /dev/null
+++ b/docs/clang-fix-campaign/design_changes/change_33.md
@@ -0,0 +1,112 @@
+# change_33:崩溃恢复联合对账与 change 台账收口(→ v1.5.9)
+
+**输入**:外部 review(1 BLOCKER + 4 MAJOR + 1 MINOR)、Claude 复审
+(执行断层四项 + 1 MAJOR 新发现 + 2 MINOR 偏差)。
+**性质**:BLOCKER 修正改动 §4.1 冻结步骤序,走 R1/R2 流程。
+
+---
+
+## A. BLOCKER:PASS 崩溃恢复与唯一索引冲突(外部 B1)
+
+**问题**:v1.5.8 步骤序——第 1 步补孤儿 invocation、第 3 步 PASS
+对账。崩溃场景(consume 已计费 → build_verify 已写 PASS record →
+wrapper 于 link 前崩溃)重入时:第 1 步把该 invocation 写成
+`orphan_invocation` 占掉 `ux_convergence_per_invocation` 唯一槽,
+第 3 步 b 分支补 link + PASS CONVERGENCE(必须引用同一 invocation)
+→ IntegrityError,**合法恢复路径永久不可达**。v1.5.7 谓词下 n_a
+不占槽、该序列反而通过——这是 change_32 A1 收紧引入的回归。
+
+**探针结论(附录 B,实测)**:死路复现(IntegrityError);修正序
+(relink 先行)通过;纯孤儿场景不受影响。
+
+**修正(已落盘 §4.1 第 3 步,顺序本身是契约)**:合并为**联合对账**:
+1. 扫描 S_pass(未 link PASS)与 S_orph(无 outcome invocation);
+2. a) 已 link → 幂等 exit 0(6b 补偿:link 在而 PASS CONVERGENCE
+   缺 → 补写,invocation 取 link 既有绑定);
+3. b) S_pass 恰一条精确匹配 **且** 同 (round, arch) 的 S_orph
+   恰一条 → **原子补 link + PASS CONVERGENCE(落座该旧 invocation
+   槽)**,不计费不 build;
+4. b') S_pass 恰一条但 S_orph 为零(PASS 无处落座——其 invocation
+   已有 outcome,外力改动信号)或多条(归属无数据可证)→ **不猜**,
+   按 c 处理;
+5. c) 冲突/歧义 → ORPHAN_PASS + HELD(reason=orphan_pass, arch_norm),
+   **不补写任何孤儿**(冻结现场);
+6. d) PASS 侧完结后,残余无匹配 PASS 的 S_orph 才补写
+   `orphan_invocation`——**补写永远在 relink 之后**。
+
+BUILD_INVOCATION 契约行的"重入时先补写再继续"与 DoD 的"第 1 步
+扫描补写"措辞同步改写;DoD 新增顺序反向验证(补写挪回 relink 前
+→ 用例必须转红)与 b' 零/多候选两变体。
+
+## B. MAJOR:预检失败路径 HELD 不可达(Claude 复审新发现)
+
+v1.5.8 契约要求 previous_evidence_missing 的 CONVERGENCE 必带
+invocation_event_id,而预检在 consume 之前、无 receipt;原文又写
+"预检失败不写任何事件"→ 主路径下 CONVERGENCE 与 HELD 都落不下,
+unit 卡死 REPAIR_ROUND_RUNNING,rebaseline 授权检查永远找不到依据。
+**修正**:预检失败 → 不写 gate 事件,但**必须**
+`append_status(HELD_FOR_INVESTIGATION, previous_evidence_missing,
+arch_norm)` 后 exit 4;6a 为 TOCTOU 备份路径(有 receipt,照写事件)。
+DoD 补正例(该 arch rebaseline 可用、他 arch 被拒)与反向验证
+(去掉 status 写入 → 复现卡死)。
+
+## C. MAJOR × 3:提案与主文的"第二权威"收口(外部 2/3/4)
+
+裁决:**主文为唯一契约权威**(已写入 v1.5.9 台账)。change_32 回写
+四处:①payload 双写为准(作废"仅真实列");②result 按 reason 分流
+(作废"非空只能 PASS/FAIL"——orphan 携 id 且 n_a);③不引入
+PENDING_CLEANUP(status_log + 派生路径方案,人工恢复枚举算法已在
+主文 §4.1 显式化:终态 SQL → iter_<round> 枚举 → workspace 安全
+清理 API,marker 拒删转人工,带外恢复不写事件仅限人工);
+④TG 错误码名对齐 §4.3(StateInconsistent /
+REJECTED_PRIMARY_BASELINE_MISSING)。
+
+## D. MAJOR:执行断层(外部 5 + Claude 复审四项)——发 prompt 阻塞项
+
+以下截至 v1.5.9 **均未落地**,主文台账已加诚实标注("设计检查
+OK: 0 problem 不证明本版新契约"):
+1. p45-implementation-prompt.md:旧索引名清零、InvocationReceipt /
+   条件枚举 / 联合对账序同步、DoD 新用例(TG 系 + 本轮 A/B 用例)、
+   路径修正(tools/ 实际位置);
+2. check_design_doc.py:CK-API-01(冻结 API ast.parse)、CK-IDX-01
+   (索引名 design/prompt 集合一致)、CK-XREF-01(§ 引用可解析)、
+   CK-MMD-01(Mermaid 先声明后引用),各配失败 fixture;
+3. Ruff 18 项清零(E741 改名、E501 断行)+ `ruff check --select E,F`
+   入 checker 自测闸门,重跑 20/20 + v1.5.2 回归确认行为不变;
+4. 本文件与 change_32 修订版落盘至 design_changes/。
+
+## E. MINOR:change_31 台账收口(外部 6)
+
+change_31.md 头部状态改为:**"已采纳(v1.5.7 落盘);其中唯一索引
+谓词(`verdict <> 'n_a'`)已被 change_32 supersede——实现方不得
+照抄该谓词,以主文 §3.4 为准"**;§0 supersede 台账同步一行。
+
+## F. 方法论教训(入 §7.13 精神,供后续 review checklist)
+
+连续两轮同一索引漏判:上轮漏**取值逃逸面**(验证了意图路径、没枚举
+n_a 侧写入面),本轮漏**时序碰撞面**(枚举了数据组合、没枚举崩溃
+重入的步骤序)。固化:**唯一约束/CHECK 的探针必须同时枚举
+①全部写入方的取值组合(§7.13 6f)与②跨崩溃重入的步骤时序**——
+每条恢复路径(orphan 补写、relink、6b 补偿、rebaseline)两两组合
+在同一约束下走一遍。
+
+---
+
+## 附录 B:探针实测输出(2026-08-04 第二轮,内存 SQLite)
+
+```
+== v1.5.8 现行步骤序(第1步补写先行)==
+[BUG 复现] PASS relink 被自己的补写堵死: IntegrityError(UNIQUE constraint failed: ev.invocation_event_id)
+  → 合法崩溃恢复路径永久不可达;v1.5.7 谓词下该序列反而通过(n_a 不占槽)——A1 收紧引入的回归
+== 修正后步骤序(联合对账:先 relink、后补孤儿)==
+[OK] relink 先行:PASS 占 X 槽成功
+[OK] 残余无 outcome invocation = 0(无需补写)
+== 修正序下纯孤儿场景(无 PASS record)仍工作 ==
+[OK] 补 orphan(X1)→ 重试(X2)→ 实质 outcome 序列不受影响
+```
+
+## DoD
+
+A/B 落盘 v1.5.9 且 DoD 用例齐备(已完成)+ C 回写(已完成,
+change_32 修订版)+ D 四项落地 + E 一行收口。**D/E 完成前不发
+P4.5 实现 prompt**。
diff --git a/docs/clang-fix-campaign/design_changes/change_34.md b/docs/clang-fix-campaign/design_changes/change_34.md
new file mode 100644
index 0000000..0767737
--- /dev/null
+++ b/docs/clang-fix-campaign/design_changes/change_34.md
@@ -0,0 +1,82 @@
+# change_34:联合对账原子化与恢复优先序(→ v1.5.10)
+
+**输入**:外部 review(3 BLOCKER + 2 MAJOR)、Claude 复审(4 MINOR)。
+**合并关系**:外部 B2 = Claude MINOR-2(外部升级理由成立——不只是
+防御性死分支,是**表里没有字段、承诺不可实现**);Claude MINOR-3/4
+为独立新发现,本轮一并落。外部 M4(change_31 回写)与 M5(D 项闸门)
+维持阻塞状态,见 E 节。
+
+---
+
+## A. BLOCKER-1:联合对账缺原子 API(TOCTOU)
+
+v1.5.9 冻结了分支语义(a/b/b'/c/d)但没冻结执行载体——wrapper 若经
+`find_unlinked_pass` 先查列表、再另起事务写入,基数判定与落库之间
+存在 TOCTOU 窗口。**修正(已落盘 §4.2)**:冻结
+`reconcile_pass_and_invocations(state_db, unit, *, round_index,
+arch_norm, failure_key, edit_spec_sha256) -> ReconcileResult`:
+单一 BEGIN IMMEDIATE 内**重查两集合**(不信调用方预读)→ 判定 →
+完成全部写入(b 的 link+PASS 事件复用 link_verification 校验逻辑于
+本事务内、不嵌套第二事务;c 的 ORPHAN_PASS+HELD 同事务;d 补写
+幂等)→ 返回 `branch ∈ {linked_already, relinked, orphan_pass_held,
+proceed}` 供 wrapper 定出口。`find_unlinked_pass` 降级为内部只读
+原语/诊断用途。锁语义同 consume(busy → CAMPAIGN_STATE_BUSY 无写入);
+进程文件锁仍为第一道互斥,事务为物理保底。
+
+## B. BLOCKER-2:a 分支"补偿"不可实现(= Claude MINOR-2)
+
+"link 在而 PASS CONVERGENCE 缺 → 补写,invocation 取 link 既有绑定"
+——campaign link 表**没有 invocation 列**,绑定不存在;且 v1.5.3 起
+link 与 PASS 事件单事务,该半状态**构造上不可达**。**裁决(采外部
+推荐项)**:删除补偿承诺(§4.1 a 分支与 §4.1 6b 两处),该形态改判
+**StateInconsistent**(外力改库信号,HELD,拒绝矩阵①类)。不采
+备选项(link 表加列)——为一个不可达状态扩冻结 schema 不值。
+
+## C. BLOCKER-3:预检早于恢复,PASS 被无关缺失挡死
+
+合法场景:PASS record 已写、link 前崩溃、旧 previous evidence 随后
+丢失 → v1.5.9 序在第 1 步预检即 HELD,**到不了第 3 步 relink**。
+**修正(已落盘)**:预检自第 1 步移至第 3 步联合对账之后、consume
+之前(新第 4 步前半)——恢复路径(a/b 命中即终结)不需要 previous;
+预检只在真的要发起新 build 时执行。预检失败落 HELD status 的
+v1.5.9 语义不变,仅位置后移。第 1 步收拢为纯身份校验。
+
+## D. Claude MINOR-3/4(独立新发现,已落盘)
+
+- **M3:a/b 出口前执行 d**。探针实锤(附录):round N 崩溃留无
+  outcome invocation → round N+1 成功 link → 后续进入全部命中 a)
+  幂等出口;b) 的基数过滤按"同 (round, arch)"看不到历史残余,若
+  a/b 跳过 d),unit 进 LOCAL_3ARCH_PASS 后**再无 repair-step 入口**,
+  "恰好一条 CONVERGENCE"不变量永久缺位。冻结:d 的扫描不过滤
+  round,且在 a)/b) 返回之前同样执行。
+- **M4:人工恢复算法两处修正**——终态清单补 `ROUNDS_EXHAUSTED`;
+  路径改为 `<campaign_ws>/<unit_hash>/<arch_norm>/iter_<round_index>`
+  并按 (arch × round) 对枚举(旧文字漏 arch 层,照抄找不到目录)。
+
+## E. 维持阻塞(外部 M4/M5,文件在目标机、本轮无法代落)
+
+1. **change_31.md 一行回写**(确切文本,照抄即可):
+   > 状态:已采纳(v1.5.7 落盘);其中唯一索引谓词
+   > (`verdict <> 'n_a'`)已被 change_32 supersede——实现方不得
+   > 照抄该谓词,以主文 §3.4 为准。
+2. **D 项四件**(checker 四规则+fixtures、prompt 同步、Ruff 清零、
+   change 落盘)状态不变:未落地,发 P4.5 prompt 前置。prompt 同步
+   面本轮又增:reconcile API 与 ReconcileResult、步骤序(对账→预检→
+   计费)、本轮五组新 DoD 用例。
+
+## F. DoD
+
+A/B/C/D 落盘 v1.5.10 且 DoD 用例齐备(已完成)+ E 两项落地。
+**E 完成前不发 P4.5 实现 prompt**(与 change_33 D 节合并计数)。
+
+---
+
+## 附录:探针实测输出(2026-08-04 第三轮,内存 SQLite)
+
+```
+b) 基数过滤(round=2 视角)命中残余 = 0 → X1 不影响 b) 判定
+d) 全局残余扫描 = [(1,)](即 X1=1)——若 a/b 提前返回跳过 d,
+  unit 进 LOCAL_3ARCH_PASS 后再无 repair-step 入口,
+  X1 的"恰好一条 CONVERGENCE"不变量永久缺位
+[OK] a/b 返回前执行 d:X1 补写落座,残余清零 —— 修正可行
+```
diff --git a/docs/clang-fix-campaign/design_changes/change_35.md b/docs/clang-fix-campaign/design_changes/change_35.md
new file mode 100644
index 0000000..b53571f
--- /dev/null
+++ b/docs/clang-fix-campaign/design_changes/change_35.md
@@ -0,0 +1,87 @@
+# change_35:逐组配对与 PASS payload 确定性重建(→ v1.5.11)
+
+**输入**:外部 review(2 BLOCKER + 3 MAJOR + 1 MINOR)、Claude 复审
+(零新发现,收敛确认)。
+**性质**:B1 改动 §4.1 冻结分支表与 §4.2 冻结 API,走 R1/R2。
+
+---
+
+## A. BLOCKER-1:跨 round 补写误 orphan 合法历史 PASS
+
+**归因(记账)**:change_34 乙-M3 把 d 子步扩为跨 round 扫描时,
+S_pass 仍锚当前 round——**用当前 round 的 PASS 集合给历史 round 判
+"无匹配"是跨组污染**。这是 change_34 自己引入的回归,同一唯一索引上
+连续第三轮碰撞面漏判;change_33 F 节的时序教训只在轮内应用、未做
+跨轮分组推演。
+
+**探针(附录)**:v1.5.10 语义下 round 1 的未 link PASS 对
+S_pass(round=2) 不可见,X1 被 d 误 orphan 占槽,P1 事后 relink 撞
+IntegrityError——死路复现;逐组配对下 round 1 组见到自己的 PASS,
+冻结不补写,relink 通道保留。
+
+**修正(已落盘)**:对账作用域 = (unit, arch) **全部 round,逐组
+配对**:当前 round 组走 a/b/b'/c;**新增 h 分支**——历史 round 组
+S_pass(r) 非空 → 该组按 c) 冻结(ORPHAN_PASS + HELD,组内 S_orph
+一并不补写)。**不自动 relink 历史轮**:历史轮遗留未 link PASS
+意味着剧本在未收口的轮上继续推进,自动收编到过去的轮或自动作废
+都属于猜。d 的前置条件改为"**其所在组已证 S_pass(r) 为空**"。
+
+## B. BLOCKER-2:崩溃后 PASS payload 无法重建
+
+`actual_changed_paths[]` 只在 BuildVerifyResult 内存/结果 JSON,
+不在 PASS record;reconcile 手里只有 key/hash。**修正(逐字段
+冻结,已落盘 §4.1 b)**:
+- `actual_changed_paths` = 已验证 worktree 内
+  `git diff --name-only <base_commit>..<verified_commit_sha> --`,
+  POSIX 归一化 + 字典序排序;diff 失败/commit 不在 → worktree 已损
+  → 转 c);
+- `verification_id`/时间字段 = PASS record 同名字段;
+- PASS record 的 arch(raw)白名单映射后必须 == arch_norm,不符 → c);
+- result=PASS, verdict=n_a, evidence=null,previous 按 6b PASS 规则;
+- **任何必填字段仍无确定性来源 → 不猜,转 c)**。
+DoD 增 parity 用例:重建清单与 build 当时记录逐字节一致。
+
+## C. MAJOR × 3(已落盘)
+
+- **M3**:`ReconcileResult` 增 `verification_id: str | None`
+  (linked_already/relinked 必填)与 `held_rounds` 清单;wrapper
+  stdout PASS JSON 仅由返回值装配(静态断言:无 link 表回查)。
+- **M4**:第 1 步"基线 evidence 存在"收窄为**仅事件与元数据身份、
+  不读 evidence 文件**——在此读文件会重现 B3 形态(恢复路径不依赖
+  基线 evidence);文件级校验归第 4 步预检/第 5 步调用前校验。
+- **M5**:a 分支半状态改**事务化出口**——同事务写
+  HELD(state_inconsistent, arch_norm) 提交后返回
+  branch='state_inconsistent_held',wrapper exit 4
+  REJECTED_STATE_INCONSISTENT;**不抛异常**(异常回滚会吞 HELD,
+  wrapper 捕获另写又破坏单事务)。append_status 注释同步:
+  state_inconsistent 按写入方上下文定 arch(reconcile 场景必填)。
+
+## D. MINOR(已落盘)
+
+泄漏窗口段旧路径 `<unit_hash>/iter_<round>` 统一为
+`<unit_hash>/<arch_norm>/iter_<round_index>`,全文单一写法。
+
+## E. 维持阻塞(不变,累计)
+
+change_31 一行回写(文本见 change_34 E.1)+ D 项四件。**prompt
+同步面累计**:reconcile 全签名族(含本轮两字段一分支)、
+a/b/b'/c/h/d 分支表、九步序(对账→预检→计费)、v1.5.10–11 全部
+新增 DoD 用例。**E 清零前不发 P4.5 prompt。**
+
+## F. DoD
+
+A/B/C/D 落盘 v1.5.11 且 DoD 用例齐备(已完成)+ E 两项落地。
+
+---
+
+## 附录:探针实测输出(2026-08-04 第四轮,内存 SQLite)
+
+```
+== v1.5.10 语义(S_pass 锚当前 round、d 跨 round)==
+S_pass(round=2) 命中 = 0 → 看不到 P1
+d) 跨 round 残余扫描命中 = [(1, 1)] → X1 被判'无匹配 PASS'
+[BUG 复现] P1 永久无法 relink: IntegrityError —— 合法历史 PASS 被误 orphan 挡死
+== 修正语义(按 (unit,arch) 全 round 分组、逐组配对)==
+round 1 组:未 link PASS=1 → HELD 冻结、不补写(留待人工/同组 relink)
+[OK] 逐组配对下 P1 的 relink 通道保留 —— 修正可行
+```
diff --git a/docs/clang-fix-campaign/design_changes/change_36.md b/docs/clang-fix-campaign/design_changes/change_36.md
new file mode 100644
index 0000000..7e43b97
--- /dev/null
+++ b/docs/clang-fix-campaign/design_changes/change_36.md
@@ -0,0 +1,104 @@
+# change_36:归属算法与统一分组(→ v1.5.12)
+
+**状态(change_37 收口)**:v1.5.12 快照**作废、从未落盘**。本文的
+B1(归属)与 B2 主体(h 撤销、统一 b/b'/c、对账前移)被 v1.5.13
+继承;以下三处被 change_37 **supersede**,实现方不得照抄:
+①"a 分支扩至任意 round"——收回(聚合死锁+计费绕过);
+②归属零/多命中"按 c 写 ORPHAN_PASS"与"多命中合法可构造"——
+改忽略+non_campaign 清单 / state_inconsistent_held(UNIQUE 禁止);
+③"verification_id 取最大 round"——改 current/historical 双维度。
+以 v1.5.13 快照为准。
+
+**输入**:外部 review(2 BLOCKER + 2 MAJOR + 1 MINOR)、Claude 复审
+(2 MINOR)。
+**性质**:B2 撤销 v1.5.11 冻结的 h 分支并重排步骤序,走 R1/R2。
+
+---
+
+## A. BLOCKER-1:S_pass(r) 缺 round 归属算法
+
+未 link 的 verification_records 没有 round 列,campaign link 的
+round_index 只在 link 后存在——v1.5.11 的"round r 的未 link PASS"
+无可实现定义。**冻结(已落盘)**:①failure_key + arch 匹配候选;
+②`record.edit_spec_sha256` 反查本 unit `campaign_rounds`,恰一命中
+→ 归组;③零命中(不属任何轮)或多命中(**同 edit_spec 多轮重试
+合法可构造,探针实锤**)→ 不猜 round,record 按 c) 处理
+(ORPHAN_PASS 记 attribution 明细),不入任何组。S_orph 有真实
+round 列,归属天然。
+
+## B. BLOCKER-2:h 分支被证伪,撤销改统一规则
+
+**认账**:change_35 写的"relink 通道保留"是纸面承诺——
+HELD(orphan_pass) 是终态,rebaseline 只认 previous_evidence_missing,
+release 只放副本不恢复状态,通道不存在;合法 PASS 会被永久冻结。
+外部论证成立:**唯一配对 + 身份全验(failure_key、edit_spec 归属、
+marker 完好)的 relink 不是猜,是补完一次被中断的写入**;上轮真正
+的猜是"历史组出现即异常需人工"这个假设本身。
+
+**裁决(采外部推荐项,已落盘)**:h 撤销,**全部 round 组统一
+b/b'/c 规则**——任意组唯一配对即同事务 relink(link 落该组
+round),歧义才 c);分组与 r 和当前入参的大小关系无关(r>当前
+不再是未定义形态)。两项附带修正:
+- **对账前移至 create_round 之前**(第 2↔3 步互换):统一规则下
+  历史组 relink 出口若在 create_round 后发生,本次已建的当前 round
+  成为无 invocation 的**空 round**、白占闸一名额;前移后
+  create_round 仅在 branch='proceed' 时执行。对账所需
+  failure_key/edit_spec_sha256 第 1 步已备,无 round 依赖。
+- **a 分支扩至任意 round**:本 arch 任一 round 已有 linked PASS →
+  修复目标已达成,linked_already 出口(与统一分组同构)。
+
+## C. MAJOR × 2(外部,已落盘)
+
+- **M3 锁粒度**:文字键 (unit, arch, round) 与锁文件路径
+  (workspace_root 只含 unit+arch)互相矛盾;且对账扫全 round,
+  跨 round 并发本就必须互斥。冻结为 **(unit, arch_norm)**;DoD 增
+  "同 unit/arch 不同 round 并发 → 一方 BUSY"变体。
+- **M4 时间落点**:契约 payload 只有 `at`,"PASS record 时间入
+  payload 原字段"无落点。裁决取外部方案一:**`at` = 重建(事件
+  写入)时刻;原始时间不入 payload,经 verification_id 回查
+  verification_records**——权威留在源表不复制,避免契约扩列连锁
+  (validator/checker/prompt)。
+
+## D. MINOR × 3(外部 M5 + Claude 两条,已落盘)
+
+- **外部 M5**:diff 命令钉死为
+  `git diff --name-only --no-renames -z <base> <verified> --`,NUL
+  切分、POSIX 归一、字典序——排除 rename 侦测、引号转义与含换行
+  文件名对本机 Git 配置的依赖;DoD parity fixture 须含触发 quoting
+  的文件名(不带 -z 必须失败)。
+- **Claude M1 出口优先级**:多组并行命中此前未定义。冻结:写入
+  全部执行,branch 按 state_inconsistent_held > orphan_pass_held >
+  linked_already/relinked > proceed——任一组触发 c) 即整体 HELD,
+  **exit 0 不得把异常藏在成功后面**;relinked 的 verification_id 取
+  最大 round。
+- **Claude M2 第 1 步收窄补全**:conf hash 与 src_clean HEAD 两项
+  文件读取自第 1 步删除(与 M4/B3 同构——relink 不 build 不碰
+  conf/src;第 5 步调用前本就有权威校验,第 1 步副本是冗余且有害的
+  提前拦截)。
+
+## E. 维持阻塞(不变,累计)
+
+change_31 一行回写 + D 项四件。prompt 同步面累计:reconcile 全
+签名族与归属算法、统一分支表与优先级、v1.5.12 新九步序
+(锁→身份→**对账**→create_round→预检→计费→build→6a/6b→释锁)、
+v1.5.10–12 全部 DoD。**E 清零前不发 P4.5 prompt。**
+
+## F. 方法论记账
+
+change_35 的 h 分支是"以不猜为名的猜"——把确定性可判的场景
+(唯一配对+全验)让渡给人工,本质是对"历史组=异常"做了无证据
+假设,且未验证 HELD 的恢复边是否存在。固化两条:**①任何"转人工"
+裁决必须同时给出人工恢复边(状态机上存在回边),否则它就是终态
+死路的委婉说法;②fail-closed 的对象是"无法确定的事",不是
+"可以确定但罕见的事"。**
+
+---
+
+## 附录:探针实测输出(2026-08-04 第五轮,内存 SQLite)
+
+```
+[OK] B1 归属(唯一):P1.edit_spec=aaa → round 1(campaign_rounds 反查,无需 vrec 存 round)
+[实锤] 归属歧义可构造:edit_spec=aaa 命中 2 个 round → 不猜,转 c)
+[OK] B2 统一规则:历史 round 1 组唯一配对 → 同事务 relink 落座,无 HELD、无终态死路
+[OK] 残余 = 0;且 reconcile 前移至 create_round 之前 → 本次入口不再产生空 round
+```
diff --git a/docs/clang-fix-campaign/design_changes/change_37.md b/docs/clang-fix-campaign/design_changes/change_37.md
new file mode 100644
index 0000000..bc82425
--- /dev/null
+++ b/docs/clang-fix-campaign/design_changes/change_37.md
@@ -0,0 +1,94 @@
+# change_37:补账/出口解耦与归属修正(→ v1.5.13)
+
+**输入**:外部 review(4 BLOCKER/MAJOR)、Claude 复审(1 BLOCKER +
+1 MINOR)。两方在 a 分支扩展上**独立同判 BLOCKER**(聚合死锁推演
+完全同构),这是异构互查的理想形态。
+**性质**:收回 v1.5.12 快照的两处附带裁量;**v1.5.12 快照作废、
+从未落盘、禁止落盘**,由 v1.5.13 快照直接取代。
+
+---
+
+## A. 丙-B1:落盘断层的记账与规程冻结
+
+外部 B1 指出目标机 design.md 仍为 v1.5.11 而 change_36 自称"已
+落盘"。**事实**:本工作流的交付物是快照文件
+(`clang-fix-campaign-design-v1_5_N-draft.md`),评审对象亦为快照
+(Claude 复审已按此口径执行);目标机 design.md 的替换是发布闸门
+动作,与 change_31 回写、checker、prompt 同属 E 项。**规程自本版
+冻结**:①change 文档中"已落盘"一律指快照;②目标机未同步前,
+对旧 design.md 跑 checker 的 `0 problem` **不代表**新契约(已在
+台账标注);③快照落盘时**跳过被作废的中间版**(v1.5.12 不落,
+直接 v1.5.11 → v1.5.13)。
+
+## B. 丙-B3(BLOCKER,双方同判):a 分支扩展收回
+
+v1.5.12 快照把 a 扩至"本 arch 任一 round 已 link 即 exit 0"。
+推演(Claude 复审给出完整链条):round 1(spec v1) primary/arch2
+PASS、arch3 FAIL → round 2(v2);调 repair-step(primary, round2)
+→ 被 round 1 link 短路 exit 0 **且不计费** → v2 组永远只有 arch3
+可能 PASS → §3.4 聚合(同一 edit_spec_sha256 三 arch 齐备)永久
+缺员 → unit 死锁;不计费同时绕过双闸的失控保护。**根因**:混淆
+"某 arch 在旧 spec 下 PASS"与"整包在同一 spec 下三 arch 齐备"。
+
+**修正(已入 v1.5.13 快照)**:
+- a) 回收为 `link.edit_spec_sha256 == 本次 edit_spec`(由
+  UNIQUE(unit, edit_spec_sha256),同 hash ⟺ 同 round);
+- **统一规则重新定性**:统一的是"账本补全"动作,不是"成功出口"
+  ——历史组 relink 只补该轮的账,branch 仅由当前 edit_spec 组
+  决定;历史 relink 非空照走 proceed(照建照测照计费);
+- DoD 补正面断言("round N 部分 PASS → N+1 同 arch 必须重新
+  build")与卡死复现反向验证。
+
+## C. 丙-B2(BLOCKER):归属零/多命中的可执行落点
+
+v1.5.12 快照令零/多命中"按 c) 写 ORPHAN_PASS"——不可执行:
+ORPHAN_PASS 契约必填 round_index,零命中无合法 round,写事件必然
+猜或破 schema。且"多命中合法可构造"**有误**:
+`UNIQUE(campaign_unit_key, edit_spec_sha256)` 物理禁止同 spec 占
+两轮(本轮探针实锤;上轮探针的多命中系绕过约束直写所得——
+**探针教训:谈"可构造"前先验证约束存在性**)。
+
+**修正(已入快照)**:①恰一命中 → 归组;②零命中 = 非 campaign
+所有 → **无 gate 事件、无 HELD**,入
+`non_campaign_verification_ids` + stdout WARN(campaign 账本只记
+campaign 事实,对非己方记录无管辖权);③多命中 = 约束被破坏 →
+`state_inconsistent_held`(同 a 半状态的事务化出口)。
+
+## D. 丙-B4(MAJOR):ReconcileResult 当前/历史双维度
+
+多组补完与单值结果不相容;"verification_id 取最大 round"作废——
+最大历史 round 的 verification 不属于本次请求,拿它装配 stdout
+PASS 是张冠李戴。**修正(已入快照)**:
+`current_verification_id` / `current_relinked_invocation_event_id`
+(出口与 stdout 仅由此装配)+
+`historical_relinks: tuple[(round, verification_id, invocation_event_id)]`
++ `non_campaign_verification_ids`;优先级修订:HELD > 当前组成功 >
+proceed,**历史 relink 永不抬升 branch**。
+
+## E. 维持阻塞(不变)
+
+change_31 一行回写 + D 项四件 + **目标机 design.md 同步至
+v1.5.13**(v1.5.12 跳过)。prompt 同步面累计至 v1.5.13:归属四则、
+双维度 ReconcileResult、补账/出口解耦语义、本轮全部 DoD。
+**E 清零前不发 P4.5 prompt。**
+
+## F. 方法论记账(续 change_36 F)
+
+①**附带裁量单独立项**:a 扩展、对账前移这类"顺手优化"混在主
+变更里,评审注意力被主变更吸走——今后附带修正在 change 文档单列
+"附带变更"节,逐条独立论证;②**探针先验约束**:构造反例前先
+确认 DDL 允许该构造,绕约束造出的"反例"会把外力改库误标为合法
+路径;③**出口语义与账本语义分离**:凡"修复了历史状态"的操作,
+默认不改变当前调用的成功判定,除非显式论证。
+
+---
+
+## 附录:探针实测输出(2026-08-04 第六轮,内存 SQLite)
+
+```
+[实锤] 同 unit 同 edit_spec 占两轮被 DDL 物理禁止: UNIQUE constraint failed:
+  campaign_rounds.campaign_unit_key, campaign_rounds.edit_spec_sha256
+  → 归属'多命中'在完好约束下不可达;上轮探针的多命中系绕过约束直写所得,
+    不是合法路径 —— 多命中出现即约束被破坏,应判 StateInconsistent 而非'合法重试'
+[OK] 唯一命中路径正常:bbb → round 2;零命中 = record 非本 campaign 所有,无合法 round 可填
+```
diff --git a/docs/clang-fix-campaign/design_changes/change_38.md b/docs/clang-fix-campaign/design_changes/change_38.md
new file mode 100644
index 0000000..1ed0124
--- /dev/null
+++ b/docs/clang-fix-campaign/design_changes/change_38.md
@@ -0,0 +1,108 @@
+# change_38:身份权威复位与完整性预检(→ v1.5.14)
+
+**输入**:外部 review(1 BLOCKER + 3 MAJOR + 1 MINOR)、Claude 复审
+(1 MINOR + 1 NIT)。
+**性质**:撤销 v1.5.12 引入、v1.5.13 沿用的步骤重排,走 R1/R2。
+
+---
+
+## A. 丁-B1(BLOCKER):对账前移撤销,恢复 create_round → 对账
+
+**归因**:对账前移是 change_36 的附带裁量(change_37 F①刚立
+"附带裁量单独立项"之规,病例本尊却已随 v1.5.12 混入并存活到
+v1.5.13)。旁路链:`--round-index 2 --edit-spec round1_hash`
+→ 对账步把旧 hash 判为"当前组"→ linked_already exit 0 → 后置的
+create_round 永不执行 ⇒ UNIQUE 同 hash 拒占新轮、序号连续性、ref
+绑定、闸一 max_rounds **全部旁路**。
+
+**前提复审**:前移动机(历史 relink 出口留空 round)已被 change_37
+"补账不授出口"消解——other-round relink 走 proceed 照建 round;
+仅 HELD 出口可能留空 round,而 HELD 下 campaign 已冻结,可接受。
+**冻结原则:成功出口永远不得先于 round 权威绑定。**恢复原序:
+锁 → 身份校验 → create_round(+复核)→ 联合对账 → 预检+consume →
+build → 6a/6b → 释锁。全部步号引用回卷(上轮 Claude 复审列出的三处
+"第 3 步"残留在原序下自然归正)。DoD 增双向用例:同 hash 占新轮的
+调用必须死在 create_round(反向验证:恢复 v1.5.12 序 → 该调用
+exit 0 逃过全部身份校验,必须能捕获)。
+
+## B. 丁-M4(MAJOR):a0 全 round link↔CONVERGENCE 完整性预检
+
+半状态检查此前只挂当前 spec 的 a 分支。探针实锤掩盖路径:历史
+round 的 link 在、PASS CONVERGENCE 被外力删 → 该 verification 不在
+S_pass(已 link)、其 invocation 在 S_orph(无 outcome)、组内
+S_pass 为空 ⇒ **d 把它补成"正常孤儿"**,不一致被静默掩盖。
+**修正**:新增 **a0 预检,先于一切分支**——全 round 每条已 link
+verification 必须对应**恰一条** PASS CONVERGENCE,且
+unit/round/arch/verification 逐项与 link 一致,result=PASS、verdict=n_a,
+invocation 指向同 unit/round/arch 的 BUILD_INVOCATION。这不是
+`EXISTS(verification_id)` 弱检查:DB 唯一索引只锁 invocation,不锁
+verification_id。缺失/重复/错绑任一形态 →
+state_inconsistent_held(同事务 HELD)。a0 先行,b/d 才可信;
+DoD 补缺失、重复、错 round/arch/invocation 反例。
+
+## C. 丁-M2/M3/M5(MAJOR×2 + MINOR,契约一致性)
+
+- **M2**:§3.4 未链接 PASS 选择规则重写(旧文按 (unit, round,
+  arch) 直接选,与"record 无 round 列"矛盾,两套算法并存)——
+  统一为 failure_key+arch 候选 + edit_spec 反查归属;
+  `find_unlinked_pass` **去 round_index 形参**(按 round 过滤是旧
+  契约残留),返回含 edit_spec_sha256 供归属诊断。
+- **M3**:stdout JSON 固定新增
+  `"reconciliation": {"other_round_relinks": [],
+  "non_campaign_verification_ids": []}` 与 `"warnings": []`——所有
+  branch 均输出、空时空数组;**单 JSON 契约不破,禁止 JSON 外附加
+  文本行**(此前"stdout WARN"无落点,附加文本会破坏机器消费)。
+  非空 schema 同步冻结:`other_round_relinks` 序列化为
+  `{round_index, verification_id, invocation_event_id}` 对象数组(禁止
+  JSON 三元数组),`non_campaign_verification_ids` 为排序后字符串数组,
+  `warnings` 为 `{code: non_campaign_verification, verification_id}` 对象
+  数组;全部按冻结键确定性排序。
+- **M5**:`historical_relinks` 更名 **`other_round_relinks`**
+  (r 与当前入参无大小约束,可含 future round);DoD 的
+  `ReconcileResult.verification_id` 更正为 `current_verification_id`。
+
+## D. 丁-NIT(Claude):聚合职责边界
+
+"由其 edit_spec 组自行推进"无主语。冻结:**reconcile 不触发聚合/
+沙箱提交;各 edit_spec 组三 arch 齐备性的检查与推进由编排层(剧本)
+在 unit 出口后执行**——本 API 职责止于账本一致。
+
+## E. 维持阻塞(累计)
+
+change_31 一行回写 + D 项四件 + **目标机同步 v1.5.14**(v1.5.12
+跳过;v1.5.13 已落盘,本版覆盖)。prompt 同步面累计至 v1.5.14。
+另按 Claude 复审建议,checker 增补一条 fixture 素材:**步骤重排后
+全文步骤号引用核对**(CK-XREF-01 只查 § 引用,管不到步号)。
+**E 清零前不发 P4.5 prompt。**
+
+## F. 方法论记账(续 change_37 F)
+
+**④前提失效即裁量复审**:对账前移的动机(空 round)被 change_37
+消解后,裁量本身没有被回头审视——支撑某裁量的前提被后续变更
+移除时,该裁量必须重新立案,而不是靠惯性存活。**⑤"当前组"的
+判定输入必须先经权威绑定**:任何以调用方入参(round/hash)界定
+作用域的逻辑,其入参必须先过 DB 权威校验——对账前移的本质错误
+是让未经绑定的入参直接驱动了成功出口。
+
+## G. 冻结裁决(2026-08-04)
+
+开发者确认 v1.5.14 设计语义正式 Frozen。change_38 后最终复审
+又将 a0 收紧为“恰一条 PASS CONVERGENCE +
+unit/round/arch/verification/invocation 精确绑定”,并冻结
+stdout 非空元素 schema 与确定性排序;`check_design_doc.py`
+返回 0 problem。E 节剩余项定性为实施/目标机/prompt 发布闸门,
+不再阻塞设计语义冻结,但 E 清零前仍不得发布 P4.5 prompt。
+Frozen 后任何设计修改必须按 R1 新建 `change_39.md` 或后续编号,
+禁止静默改写 v1.5.14-FROZEN。
+
+---
+
+## 附录:探针实测输出(2026-08-04 第七轮,内存 SQLite)
+
+```
+== v1.5.13 语义(半状态检查只挂当前 spec 的 a 分支)==
+S_orph(round1) = [(1,)](X1 在列);S_pass(round1) = [](V1 已 link,不在未 link 集合)
+→ round1 组 S_pass 为空 ⇒ d 补写 orphan_invocation(X1) —— 半状态被 d 掩盖成'正常孤儿'
+== 修正:a0 全 round link↔CONVERGENCE 完整性预检 ==
+完整性缺口 = [('V1',)] → state_inconsistent_held(同事务 HELD),先于 b/d —— 掩盖路径关闭
+```
diff --git a/docs/clang-fix-campaign/dev_memory/INDEX.md b/docs/clang-fix-campaign/dev_memory/INDEX.md
new file mode 100644
index 0000000..7ffe51f
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/INDEX.md
@@ -0,0 +1,34 @@
+# P4.5 Development Memory Index
+
+This index reconstructs the P4.5 implementation history from the files and
+commits present on the `clang-fix-campaign` branch. It is an audit index, not a
+second contract authority. Runtime behavior remains governed by
+`../design.md` and its frozen API/DDL sections.
+
+| Stage | Status | Commits | Result |
+|---|---|---|---|
+| 01 Design convergence | COMPLETE | design changes 32-40; frozen in `85310ef` | v1.5.16-FROZEN, checker-ready contract |
+| 02 P0 contract gates | COMPLETE | `85310ef`, `185d9c4` | checker 33/33, signature audit 4/4 |
+| 03 M1 state layer | COMPLETE | `98bfa01`, `6930c31` | seven-table append-only state layer; 29 collected tests |
+| 04 M2 reconciliation | COMPLETE | `637e970`, `b8ada93` | atomic branch table and recovery guards; 20 collected tests |
+| 05 M3 repair step | COMPLETE (code) | `5a7a5b3`, `2693218` | frozen order, CLI, JSON contract; 21 collected tests |
+| RA remediation | COMPLETE when this commit lands | checkpoint `checkpoint/p45_code_ready` | historical memory backfilled |
+| RB three-way review package | PENDING | - | self-contained design/code packages |
+| RC real E2E smoke | PENDING | - | synthetic arc, recovery, edges, historical cases |
+| RD close-out | BLOCKED ON RC/REVIEW | - | PR and human review |
+
+## Code-Ready Checkpoint
+
+- Tag: `checkpoint/p45_code_ready`
+- Commit: `269321820abe0eddb7db345dcb26ffaedc7127c6`
+- Meaning: P0 plus M1/M2/M3 code and tests are present; real-environment RC
+  smoke and external review closure have not yet been completed.
+
+## Known Record Difference
+
+The remediation task says that an original `claude-review-ledger.md` was
+delivered with the task. No such source file was present in the repository or
+the available attachment directory at RA execution time. The ledger under
+`../review/` is therefore a provenance-labeled reconstruction from machine
+files (`change_32.md` through `change_40.md`), Git history, and the archived P0
+signature audit. It does not invent missing reviewer quotations.
diff --git a/docs/clang-fix-campaign/dev_memory/methodology.md b/docs/clang-fix-campaign/dev_memory/methodology.md
new file mode 100644
index 0000000..78b8c40
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/methodology.md
@@ -0,0 +1,33 @@
+# P4.5 Methodology Ledger
+
+These seven rules are transcribed from the numbered ledger in
+`change_37.md` through `change_40.md`. They are process safeguards learned
+during design convergence.
+
+1. **Isolate incidental judgment.** A side correction or "small optimization"
+   must have its own change section and rationale so review attention is not
+   hidden behind the primary change.
+2. **Validate probe preconditions.** Before constructing a counterexample,
+   prove that the frozen DDL permits it. A state reachable only by bypassing
+   constraints is corruption evidence, not a valid workflow path.
+3. **Separate ledger repair from exit semantics.** Repairing historical state
+   does not grant success to the current invocation unless the contract says
+   so explicitly.
+4. **Re-review a judgment when its premise disappears.** A later change that
+   removes the reason for an earlier ordering or policy decision must trigger
+   a fresh review of that decision.
+5. **Bind scope inputs before they drive a success exit.** Caller-provided
+   round/hash values cannot define the "current group" until DB authority has
+   validated them.
+6. **Run every checker rule against real input before freezing it.** A checker
+   is code; a rule change without a real-document trial output is incomplete.
+7. **Make the rule reproduce the incident it claims to prevent.** Every guard
+   change needs a fixture proving that the original incident fails under the
+   new rule. A guard that cannot catch its founding incident does not exist.
+
+## Earlier Prelude
+
+`change_36.md` also records two earlier, separately numbered lessons: a human
+handoff needs a real recovery edge, and fail-closed behavior should reject
+uncertainty rather than merely rare but deterministic cases. They predate the
+canonical seven-item ledger above and remain useful context.
diff --git a/docs/clang-fix-campaign/dev_memory/stage01_design_convergence/plan.md b/docs/clang-fix-campaign/dev_memory/stage01_design_convergence/plan.md
new file mode 100644
index 0000000..42ef73b
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage01_design_convergence/plan.md
@@ -0,0 +1,21 @@
+# Stage 01 Plan: Design Convergence
+
+## Goal
+
+Converge the P4.5 campaign repair contract before implementation: append-only
+state, invocation uniqueness, crash recovery, deterministic PASS attribution,
+frozen wrapper ordering, and executable API/checker gates.
+
+## Inputs
+
+- `../../design.md`
+- `../../design_changes/change_32.md` through `change_40.md`
+- External and Claude findings recorded in those change documents
+- Seven SQLite probe transcripts embedded in changes 32-38
+
+## Exit Criteria
+
+- One frozen design is the only runtime contract authority.
+- DDL, branch table, nine-step wrapper order, and API signatures agree.
+- Guard rules are executable and reproduce their founding failures.
+- Any contradiction is handled by stop-and-report, not silent correction.
diff --git a/docs/clang-fix-campaign/dev_memory/stage01_design_convergence/progress.md b/docs/clang-fix-campaign/dev_memory/stage01_design_convergence/progress.md
new file mode 100644
index 0000000..d15123e
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage01_design_convergence/progress.md
@@ -0,0 +1,21 @@
+# Stage 01 Progress: Design Convergence
+
+1. `change_32` tightened convergence uniqueness and evidence tuple integrity.
+2. `change_33` found the crash-recovery ordering dead end and moved orphan
+   backfill behind PASS relinking.
+3. `change_34` froze one `BEGIN IMMEDIATE` reconciliation API and recovery
+   priority.
+4. `change_35` added per-round pairing and deterministic PASS payload rebuild.
+5. `change_36` supplied PASS-to-round attribution through edit-spec identity.
+6. `change_37` separated historical ledger repair from current success exits
+   and rejected impossible multi-round attribution as corruption.
+7. `change_38` restored identity binding before reconciliation and added the
+   all-round link-to-CONVERGENCE integrity precheck.
+8. `change_39` made API/index checker rules executable and consolidated prompt
+   authority.
+9. `change_40` corrected the API checker from `ast.parse` to `compile`, because
+   only the latter catches duplicate function arguments.
+
+The process deliberately stopped when checker reality contradicted the text;
+the intermediate worktree was preserved until each numbered change supplied a
+new ruling.
diff --git a/docs/clang-fix-campaign/dev_memory/stage01_design_convergence/result.md b/docs/clang-fix-campaign/dev_memory/stage01_design_convergence/result.md
new file mode 100644
index 0000000..a906f83
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage01_design_convergence/result.md
@@ -0,0 +1,35 @@
+# Stage 01 Result: Design Convergence
+
+## Conclusion
+
+- Final contract: `design.md` v1.5.16-FROZEN.
+- Frozen snapshot SHA-256:
+  `ff73f5e3c6d54a75ae60771b98eadcfc1a4d1422ca8faf337a3de09eee4346ff`.
+- Snapshot and working design were byte-identical at RA audit time.
+- Authoritative P4.5 prompt SHA-256:
+  `e214d1fb8b806e1ebc12e6e8cfafc57d71cbffcf0340d94c26396ef87816a3fb`.
+- Design/checker landing commit: `85310ef`.
+
+## Decisions That Matter to Implementers
+
+- Success exits occur only after DB-authoritative round identity binding.
+- Reconciliation owns one immediate transaction and uses transaction-internal
+  write primitives; it must not nest a second transaction.
+- Historical relinking repairs the ledger without granting current success.
+- A0 integrity failure and attribution ambiguity are HELD, never guessed.
+- The wrapper order is lock, identity, create round, reconcile, precheck,
+  consume, build, outcome, unlock.
+
+## Record Differences
+
+- The original standalone Claude review ledger referenced by remediation was
+  absent. Review history is reconstructed in
+  `../../review/claude-review-ledger.md` from machine-resident change files.
+- `change_36` contains two pre-ledger methodology lessons while `change_37`
+  restarts numbering at 1. The requested canonical 1-7 ledger follows
+  changes 37-40; the earlier two are retained as a prelude.
+
+## Remaining TODO
+
+- Complete three-way final review (RB).
+- Validate the frozen semantics against real GBS/filesystem behavior (RC).
diff --git a/docs/clang-fix-campaign/dev_memory/stage02_p0_gates/plan.md b/docs/clang-fix-campaign/dev_memory/stage02_p0_gates/plan.md
new file mode 100644
index 0000000..b97f05a
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage02_p0_gates/plan.md
@@ -0,0 +1,21 @@
+# Stage 02 Plan: P0 Contract Gates
+
+## Goal
+
+Turn the frozen document into an executable implementation input before code
+consumes it.
+
+## Inputs
+
+- v1.5.16 frozen design and snapshot
+- Authoritative P4.5 implementation prompt
+- `change_31`, `change_39`, and `change_40`
+- Four-signature independent audit
+
+## Exit Criteria
+
+- Every Python fence compiles.
+- Bare pseudo-signatures are absent.
+- Prompt index tokens are a non-empty subset of design indexes.
+- Cross-reference and Mermaid declaration-order checks pass.
+- Frozen snapshot is byte-identical and prompt SHA is exact.
diff --git a/docs/clang-fix-campaign/dev_memory/stage02_p0_gates/progress.md b/docs/clang-fix-campaign/dev_memory/stage02_p0_gates/progress.md
new file mode 100644
index 0000000..1184d05
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage02_p0_gates/progress.md
@@ -0,0 +1,12 @@
+# Stage 02 Progress: P0 Contract Gates
+
+- Rewrote section 4.2 pseudo-signatures as executable Python skeletons without
+  changing parameter names, order, defaults, or return contracts.
+- Added CK-API, CK-IDX, CK-XREF, and CK-MMD checks plus negative fixtures.
+- Corrected CK-API to use `compile(..., "exec")`, which catches the B4 duplicate
+  argument shape that `ast.parse` accepts.
+- Archived superseded prompts and retained one authoritative root prompt.
+- Recorded a complete 45-declaration old/new audit and an independent 4/4
+  check for the highest-risk signatures.
+- First full-test command lacked component `PYTHONPATH` entries and failed at
+  collection; the corrected command is recorded in the P0 audit.
diff --git a/docs/clang-fix-campaign/dev_memory/stage02_p0_gates/result.md b/docs/clang-fix-campaign/dev_memory/stage02_p0_gates/result.md
new file mode 100644
index 0000000..e498989
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage02_p0_gates/result.md
@@ -0,0 +1,30 @@
+# Stage 02 Result: P0 Contract Gates
+
+## Commits
+
+- `85310ef` - complete P0 contract gates.
+- `185d9c4` - archive independent four-signature check.
+
+## Verified Results
+
+- Checker self-test: 33/33.
+- Historical v1.5.2 regression groups: 5 + 1 + 6 = 12.
+- Design checker: `OK: 0 problem`.
+- Independent signatures: PASS 4/4.
+- Full suite at P0: 750 passed, 1 skipped.
+- Mypy at P0: 23 source files clean.
+
+## Reproduction
+
+```bash
+PYTHONPATH=tizen-ci-triage/scripts:tizen-gbs-log-analysis/scripts:tizen-gbs-patch-suggest/scripts:tizen-gbs-build/scripts \
+  .venv/bin/pytest -q
+PYTHONPATH=tizen-ci-triage/scripts \
+  .venv/bin/mypy tizen-ci-triage/scripts/ci_triage
+python3 docs/clang-fix-campaign/tools/check_design_doc.py --self-test
+python3 docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
+```
+
+## Remaining TODO
+
+None for the P0 contract gate. Real behavior validation belongs to RC.
diff --git a/docs/clang-fix-campaign/dev_memory/stage03_m1_state_layer/plan.md b/docs/clang-fix-campaign/dev_memory/stage03_m1_state_layer/plan.md
new file mode 100644
index 0000000..48167b2
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage03_m1_state_layer/plan.md
@@ -0,0 +1,18 @@
+# Stage 03 Plan: M1 State Layer
+
+## Goal
+
+Implement the frozen seven-table campaign schema and append-only APIs that all
+later reconciliation and wrapper behavior depends on.
+
+## Safety Inputs
+
+- `ux_convergence_per_invocation` must physically prohibit a second outcome.
+- The CI evidence triple must be all-null or all-non-null.
+- Status writes carry `arch_norm` where the frozen reason requires it.
+- Budget consumption and PASS linking are transactionally guarded.
+
+## Exit Criteria
+
+Positive behavior and reverse tests must both prove that the physical guards,
+not only Python conditionals, enforce the contract.
diff --git a/docs/clang-fix-campaign/dev_memory/stage03_m1_state_layer/progress.md b/docs/clang-fix-campaign/dev_memory/stage03_m1_state_layer/progress.md
new file mode 100644
index 0000000..400c8e2
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage03_m1_state_layer/progress.md
@@ -0,0 +1,12 @@
+# Stage 03 Progress: M1 State Layer
+
+- Added `campaign_state.py` with schema creation and public append-only APIs.
+- Implemented unit/round identity, invocation receipts, event payload binding,
+  verification links, adoption, status, and QuickBuild request/result state.
+- Used `BEGIN IMMEDIATE` for mutation races and mapped lock contention to the
+  frozen busy failure.
+- Split transaction-internal validation/write primitives from public
+  transaction-opening wrappers so later reconciliation can reuse logic without
+  nesting transactions.
+- Added reverse validation that drops the unique index or CHECK and proves the
+  prohibited rows then become insertable.
diff --git a/docs/clang-fix-campaign/dev_memory/stage03_m1_state_layer/result.md b/docs/clang-fix-campaign/dev_memory/stage03_m1_state_layer/result.md
new file mode 100644
index 0000000..62d9a56
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage03_m1_state_layer/result.md
@@ -0,0 +1,19 @@
+# Stage 03 Result: M1 State Layer
+
+## Commits
+
+- `98bfa01` - append-only campaign state foundation.
+- `6930c31` - state database guards and reverse tests.
+
+## Result
+
+- Seven campaign tables added without changing the pre-existing state DB
+  contract.
+- 29 test cases currently collect from `test_campaign_state.py`.
+- Concurrency, append-only behavior, exact event binding, evidence CHECK, and
+  convergence uniqueness have direct tests.
+
+## Remaining TODO
+
+- The layer is unit-tested; RC must exercise it through a real build arc and
+  crash-recovery process boundary.
diff --git a/docs/clang-fix-campaign/dev_memory/stage04_m2_reconcile/plan.md b/docs/clang-fix-campaign/dev_memory/stage04_m2_reconcile/plan.md
new file mode 100644
index 0000000..6d6bdb1
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage04_m2_reconcile/plan.md
@@ -0,0 +1,14 @@
+# Stage 04 Plan: M2 Reconciliation
+
+## Goal
+
+Implement the frozen a0/a/b/b-prime/c/d reconciliation table as one atomic
+operation over PASS records, links, invocations, and convergence outcomes.
+
+## Key Constraints
+
+- Re-read all sets inside one `BEGIN IMMEDIATE` transaction.
+- Reuse link validation without starting a nested transaction.
+- Apply A0 integrity validation before orphan backfill can mask corruption.
+- Historical relinks are visible but do not grant current success.
+- Exit priority is deterministic and fail-closed.
diff --git a/docs/clang-fix-campaign/dev_memory/stage04_m2_reconcile/progress.md b/docs/clang-fix-campaign/dev_memory/stage04_m2_reconcile/progress.md
new file mode 100644
index 0000000..4eb0230
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage04_m2_reconcile/progress.md
@@ -0,0 +1,11 @@
+# Stage 04 Progress: M2 Reconciliation
+
+- Added `reconcile_pass_and_invocations` to `campaign_state.py`.
+- Rebuilt PASS payload fields deterministically from verification records and
+  Git state.
+- Implemented current relink, historical relink, linked-already, orphan PASS,
+  non-campaign PASS warning, residual invocation backfill, and A0 integrity
+  branches.
+- Used savepoints/transaction-local helpers so a failed event insert cannot
+  leave a half-link.
+- Sorted result arrays deterministically for the wrapper JSON contract.
diff --git a/docs/clang-fix-campaign/dev_memory/stage04_m2_reconcile/result.md b/docs/clang-fix-campaign/dev_memory/stage04_m2_reconcile/result.md
new file mode 100644
index 0000000..58414fa
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage04_m2_reconcile/result.md
@@ -0,0 +1,20 @@
+# Stage 04 Result: M2 Reconciliation
+
+## Commits
+
+- `637e970` - atomic reconciliation implementation.
+- `b8ada93` - branch-table and recovery guard tests.
+
+## Result
+
+- 20 test cases currently collect from `test_campaign_reconcile.py`.
+- Tests cover all primary branch families, A0 corruption forms, busy lock,
+  deterministic output, savepoint rollback, and preservation of the existing
+  public link API.
+- The implementation uses a transaction-internal link primitive; no nested
+  immediate transaction is opened from reconciliation.
+
+## Remaining TODO
+
+- RC E3 must prove the relink path across a real killed process, with no second
+  build and no second budget charge.
diff --git a/docs/clang-fix-campaign/dev_memory/stage05_m3_repair_step/plan.md b/docs/clang-fix-campaign/dev_memory/stage05_m3_repair_step/plan.md
new file mode 100644
index 0000000..d0bd7db
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage05_m3_repair_step/plan.md
@@ -0,0 +1,23 @@
+# Stage 05 Plan: M3 Repair Step
+
+## Goal
+
+Expose the campaign repair step as the machine-consumable wrapper that executes
+the frozen nine-step order and emits one deterministic JSON document.
+
+## Order
+
+1. Acquire unit/arch lock.
+2. Validate source and unit identity.
+3. Create or validate the round.
+4. Reconcile prior PASS/invocation state.
+5. Preflight previous evidence.
+6. Consume one build invocation.
+7. Run build-verify.
+8. Record FAIL convergence or PASS link/convergence.
+9. Release the lock.
+
+## Exit Criteria
+
+CLI routing, ordering, fail-closed exits, recovery short circuits, HELD
+reachability, and stdout schema all need direct tests.
diff --git a/docs/clang-fix-campaign/dev_memory/stage05_m3_repair_step/progress.md b/docs/clang-fix-campaign/dev_memory/stage05_m3_repair_step/progress.md
new file mode 100644
index 0000000..c16e4ce
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage05_m3_repair_step/progress.md
@@ -0,0 +1,12 @@
+# Stage 05 Progress: M3 Repair Step
+
+- Added `campaign_repair_step.py` and `previous_evidence.py`.
+- Wired `campaign-repair-step` through `ci_triage.cli` and `python -m
+  ci_triage`.
+- Preserved create-round before reconciliation so an old edit-spec hash cannot
+  bypass round identity.
+- Made previous-evidence preflight append arch-scoped HELD before exit, keeping
+  rebaseline reachable.
+- Added post-build TOCTOU checks and fail-closed `n_a`/HELD recording.
+- Fixed stdout to one JSON object with always-present `reconciliation` and
+  `warnings`, structured non-empty entries, and deterministic ordering.
diff --git a/docs/clang-fix-campaign/dev_memory/stage05_m3_repair_step/result.md b/docs/clang-fix-campaign/dev_memory/stage05_m3_repair_step/result.md
new file mode 100644
index 0000000..54ba40a
--- /dev/null
+++ b/docs/clang-fix-campaign/dev_memory/stage05_m3_repair_step/result.md
@@ -0,0 +1,22 @@
+# Stage 05 Result: M3 Repair Step
+
+## Commits
+
+- `5a7a5b3` - repair-step implementation and CLI.
+- `2693218` - ordering, recovery, schema, and entrypoint tests.
+
+## Result
+
+- 21 test cases currently collect from `test_campaign_repair_step.py`.
+- The combined campaign state/reconcile/repair set collects 70 tests.
+- Full branch result at the code-ready checkpoint: 820 passed, 1 skipped.
+- Mypy result at the checkpoint: 26 source files clean.
+- Checkpoint tag: `checkpoint/p45_code_ready` at full commit
+  `269321820abe0eddb7db345dcb26ffaedc7127c6`.
+
+## Remaining TODO
+
+- Real GBS synthetic and historical-case smoke (RC).
+- Process-level kill-window recovery, concurrent lock, budget terminal, and
+  HELD reachability validation (RC).
+- External three-way review closure and final PR (RB/RD).
diff --git a/docs/clang-fix-campaign/e2e-smoke-runbook.md b/docs/clang-fix-campaign/e2e-smoke-runbook.md
new file mode 100644
index 0000000..3036e09
--- /dev/null
+++ b/docs/clang-fix-campaign/e2e-smoke-runbook.md
@@ -0,0 +1,116 @@
+# E2E-SMOKE:真实环境最小 campaign(P4.5 现实验证)
+
+## 0. 定位与协议
+
+**目标**:在 GBS 构建主机上,用**真实 GBS chroot(armv7l,LLVM
+22.1.8)+ 真实 build_verify + 真实文件系统**,把 P4.5 的九步序走完
+一条完整弧:FAIL 收敛(6a)→ PASS 落链(6b)→ 崩溃恢复(reconcile
+b 分支),外加并发/预算/HELD 三个边角。**不触碰 Gerrit 与
+QuickBuild**——smoke 止于闸一,任何 push/QB 提交属 P5,本任务禁止。
+
+**协议不变**:停止-报告(现实与设计不符 → 停,立案 change_41+,
+禁止顺手改代码迁就现实);实测验证不脑补(所有断言贴命令+输出
+原文+文件 sha256);工作全部在**独立 smoke 目录与独立 state DB**
+进行,不碰任何生产状态。
+
+**说明两点**:①unit 创建与 baseline-reproduce CLI 属 P6 未实现,
+本 smoke 用**种子脚本**经冻结公开 API 播 unit 与 REPRODUCE——只许
+`campaign_state` 公开 API,**禁止直写 SQL**(种子脚本因此也是这些
+API 吃真实数据的首次检验);②ci_evidence 用本地捕获的失败日志
+替代真实 QuickBuild 证据,在报告显著标注该替代(P5 前用真实 CI
+证据重验一次)。
+
+## E0. 环境预检(全部贴输出)
+
+1. GBS armv7l chroot 可用:`gbs build --help`;确认 LLVM 22.1.8
+   profile(沿用 libc++ Wave 1 的冻结配置,列出 gbs.conf 路径与
+   sha256);
+2. 选定 smoke 包:**小、快、C++**。推荐从 libc++ 迁移工作里挑一个
+   单次构建 < 5 分钟的真实包;记录其 git 仓库、base_commit;
+3. smoke 目录:`~/campaign-smoke/{state.db, ws/, logs/}`;
+4. 干净基线:该包在当前 chroot 下**能构建通过**(贴尾部日志)——
+   这是注入故障前的对照锚。
+
+## E1. 目标构造与基线(合成故障,受控全弧)
+
+1. **注入故障**:在包源码加一个确定性 clang 错误(建议:C++ 源里
+   引一个未定义符号或删一个必要 `#include`),commit 到本地分支,
+   记 `base_commit_broken`;
+2. **捕获基线失败**:GBS 构建一次 → FAIL,保存完整日志为
+   `ci_evidence.log`,记 sha256——它同时充当 ci_evidence 替代物与
+   REPRODUCE 的 baseline evidence 来源;
+3. **种子脚本 `seed_unit.py`**(冻结 API only):
+   - `ensure_schema` → `create_unit`(真实身份字段、
+     primary_arch=armv7l、failed_arches=["armv7l"]、
+     max_rounds=3、max_build_invocations=6、ci_evidence 三元组);
+   - `append_event(REPRODUCE, ...)`:evidence=基线日志真实路径+
+     sha256,outcome=matched,fingerprint 按
+     `convergence.py::_primary_fingerprint` 对真实日志计算(权威
+     来源,不许自算);
+   - 跑后用 sqlite3 只读查询贴出 unit 行与 REPRODUCE 事件原文。
+4. **准备两份 edit_spec**:
+   - `es_round1.json`:**不完全修复**(改了但引入另一个确定性
+     编译错误)→ 预期 FAIL 且指纹与基线不同 → 6a 应判 advance;
+   - `es_round2.json`:**正确修复** → 预期 PASS。
+
+## E2. 修复弧(核心验证)
+
+**R1(FAIL→6a)**:
+`python -m ci_triage campaign-repair-step --unit <key> --arch armv7l
+--round-index 1 --edit-spec es_round1.json ...`
+断言(逐条贴原文):
+- exit=0(FAIL 但流程正常),stdout 为**单个可 `jq` 解析的 JSON**,
+  固定字段齐(含空 `reconciliation`/`warnings`);
+- `result=FAIL`,`verdict=advance`(指纹异于基线;若判 stalled/
+  regressed,停止报告——说明指纹或 previous 语义与现实有出入);
+- DB:恰 1 条 BUILD_INVOCATION、恰 1 条引用其 event_id 的
+  CONVERGENCE;`invocations_used=1`;
+- evidence 文件存在且 sha256 重算与事件记录一致;
+- worktree 布局 `ws/<unit_hash>/armv7l/iter_1` 与设计一致。
+
+**R2(PASS→6b)**:round 2 + `es_round2.json`。断言:
+- exit=0,`result=PASS`,`verification_id` 非空;
+- link 行存在;PASS CONVERGENCE 占 R2 invocation 唯一槽,
+  verdict=n_a、evidence=null;
+- **previous 链**:6a→6b 间,R2 的 previous 应解析到 R1 evidence
+  (查 resolver 实际取值贴出);
+- protected marker 在 worktree 上真实存在。
+
+## E3. 崩溃恢复实验(本 smoke 的核心价值)
+
+新种一个 unit(同包同故障),直接跑正确修复的 round 1,但:
+1. 起一个 watcher:轮询 PASS record 落盘(verification_records 出现
+   未 link 行)即 `kill -9` repair-step 进程——精确打进"PASS 已写、
+   link 前"窗口(如窗口太窄打不中,允许在 wrapper 外用环境变量
+   注入 link 前 sleep,**仅限 smoke,不进主干代码**;用了必须报告);
+2. 验尸:DB 有 BUILD_INVOCATION 无 CONVERGENCE、有未 link PASS、
+   `invocations_used=1`;
+3. **重入同一 round**:断言 `branch=relinked`、exit=0、
+   `invocations_used` 仍=1(不重复计费)、不重复 build(日志无第二
+   次 gbs 调用)、PASS CONVERGENCE 落座**旧** invocation 的
+   event_id、stdout 的 `verification_id` 与 DB link 一致。
+   ——这是 v1.5.9–v1.5.13 四轮探针战场的现实复验。
+
+## E4. 边角三件(各一条)
+
+1. **并发锁**:同 unit/arch 同时起两个 repair-step(不同 round 亦
+   可)→ 一方 `CAMPAIGN_STATE_BUSY` exit 5,DB 无该方任何写入;
+2. **预算终态**:一次性 unit(max_rounds=2)连跑三轮失败修复 →
+   第三轮 RoundsExhausted exit 4,status_log 落 ROUNDS_EXHAUSTED;
+3. **HELD 可达**:R1 后手工改名 R1 evidence 文件 → 跑 R2 → 预检
+   HELD(previous_evidence_missing, armv7l)且 exit 4;若
+   campaign-rebaseline CLI 已实现则顺带验授权(同 arch 可、异 arch
+   拒),未实现则注明留待 P6。
+
+## E5. 报告格式
+
+`docs/clang-fix-campaign/review/e2e-smoke-report-v1.md`:
+- 每步命令 + stdout 原文 + 关键 DB 查询原文 + 文件 sha256;
+- **现实观测数**:单轮墙钟时间、DB 尺寸、worktree 尺寸;
+- 偏差清单:凡"现实行为 ≠ 设计预期"逐条列出(哪怕最终判无害),
+  含 ci_evidence 替代、sleep 注入等全部妥协项;
+- 结论三选一:全绿 / 有偏差但判无害(附裁决请求)/ 停止报告
+  (候选 change_41)。
+
+**完成定义**:E2 全弧 + E3 恢复 + E4 三件全部有实测输出;任何一处
+现实与设计冲突 → 停在那里,这正是本任务存在的目的。
diff --git a/docs/clang-fix-campaign/remediation-task.md b/docs/clang-fix-campaign/remediation-task.md
new file mode 100644
index 0000000..8c36907
--- /dev/null
+++ b/docs/clang-fix-campaign/remediation-task.md
@@ -0,0 +1,102 @@
+# P4.5 补救与收尾总任务(REMEDIATION,顺序执行 RA→RB→RC→RD)
+
+## 0. 协议与环境事实
+
+协议不变:停止-报告(矛盾立案 change_41+)、实测验证不脑补(全部
+断言贴命令+输出原文+sha256)、fail-closed、零修改名单不碰、禁止
+直写 SQL(状态操作只走冻结公开 API)。
+
+**环境事实(开发者提供)**:
+- `tmp/gbs_llvm.conf`:GBS 编译配置文件(smoke 一律用它);
+- `tmp/`:临时测试信息与数据目录,smoke 的 state.db/ws/日志全放
+  `tmp/campaign-smoke/` 下,不碰生产状态;
+- `tmp/Verification/log/`:开发者历史真实解过的 bug 错误日志;
+- `tmp/Verification/codes/`:对应源码(**patch 已删除**,源码应处
+  于故障态——这使它们成为真实修复用例:你需要自己写出修复);
+- 开发者将另行下载:zlib(合成弧主力)、cynara(C++ 指纹验证)、
+  libtpl-egl(备用)。
+
+## RA. dev_memory 补档(R3,第一优先)
+
+1. 建 `docs/clang-fix-campaign/dev_memory/`:
+   - `INDEX.md`(全 stage 状态/commit/结论一览);
+   - `stage01_design_convergence/`、`stage02_p0_gates/`、
+     `stage03_m1_state_layer/`、`stage04_m2_reconcile/`、
+     `stage05_m3_repair_step/`,每个含 `plan.md`(该 stage 目标与
+     输入)/`progress.md`(过程与决策依据)/`result.md`(结论、
+     commit、测试数、遗留 TODO);
+2. 原始材料:`claude-review-ledger.md`(随本任务交付,先落盘到
+   `docs/clang-fix-campaign/review/`)+ change_32–40 + design 台账 +
+   commit message + p0-signature-audit;**冲突以机上落盘文档为准**,
+   台账与文档不一致处不要调和,列入 result.md 的"记录差异"节;
+3. 方法论账本 ①–⑦ 单列 `dev_memory/methodology.md`;
+4. 打 checkpoint:`git tag checkpoint/p45_code_ready` 于当前 HEAD,
+   在 `docs/clang-fix-campaign/checkpoints.md` 登记(tag/commit/
+   覆盖范围/回退指令/回退后状态一句话);
+5. 以上单独一个 commit:`docs(clang-fix-campaign): backfill R3 dev
+   memory and checkpoint`。
+
+## RB. 三方 review 包生成(第二优先,生成后交开发者分发)
+
+在 `docs/clang-fix-campaign/review/three-way/` 生成两个自足包
+(评审方拿到包即可审,不需要访问仓库):
+1. **设计终版包** `design-v1.5.16-final-review.md`:冻结全文引用
+   路径 + 版本史一页摘要 + "评审请求:对最终文本整体 PASS/列
+   finding,重点 §3.4 契约表、§4.1 九步与分支表、§4.2 冻结 API";
+2. **代码包** `code-review-package.md`:`git diff 85310ef..HEAD`
+   全文(附 --stat)+ 契约→代码定位摘要 + DoD→测试函数映射表 +
+   "评审请求:按 [BLOCKER]/[MAJOR]/[MINOR]/[NIT] 分级,重点
+   事务边界/唯一性/崩溃恢复/append-only";
+3. 包内注明:finding 回收后按 R14 闭环(BLOCKER 必修、MAJOR 修或
+   开发者显式放行、MINOR 进 dev_memory 遗留 TODO);
+4. 单独 commit。生成完毕即报告,**不等评审结果,继续 RC**(外部
+   评审与 smoke 并行,合并主干前两者都须闭环)。
+
+## RC. E2E smoke(真实环境验收,按已交付 runbook 执行,含本地化修订)
+
+基础流程照 `e2e-smoke-runbook.md`(E0–E5),本地化修订如下:
+1. **E0 修订**:GBS 配置一律 `tmp/gbs_llvm.conf`(记录其 sha256);
+   smoke 目录 = `tmp/campaign-smoke/`;
+2. **E1/E2(合成弧)**:用 zlib 走受控全弧(注错→R1 修一半→R2
+   修好),断言按 runbook E2 逐条;
+3. **E3(崩溃恢复)**:照 runbook,watcher + kill -9 打
+   "PASS 已写、link 前"窗口,重入断言 relinked/不重复计费/不重复
+   build;
+4. **E4(边角三件)**:并发锁 / 预算终态 / HELD 可达,照 runbook;
+5. **新增 E6(真实历史用例)**:遍历 `tmp/Verification/` 的每个
+   case:
+   a. 核对 codes 是否带 packaging(.spec 等),缺则列清单报告、
+      跳过该 case,**不许自造 packaging 冒充**;
+   b. 用 GBS 实际构建确认故障可复现,且报错与 log/ 中历史日志
+      **同根因**(报错主体一致;行号/路径漂移可接受,写入报告);
+      复现不了 → 记录环境漂移,跳过不硬怼;
+   c. 以历史日志为 ci_evidence 种 unit(种子脚本只用冻结 API),
+      baseline-reproduce 用**新鲜构建日志**——这里专门验证:
+      `_primary_fingerprint` 对历史日志与新构建日志是否给出可
+      比对的指纹(这是 Claude 押注最可能出偏差的点,任何不一致
+      如实报,不调参迁就);
+   d. **自行编写修复** edit_spec(patch 已删,这是真实修复练习),
+      经 campaign-repair-step 走到 PASS;一轮修不好就多轮,预算内
+      收敛;修不出来 → 记录为"人类难度用例",不硬怼;
+   e. 每 case 独立小节入报告:根因/指纹比对/轮数/最终状态。
+6. cynara 用例:在其一个 C++ 源里注一个模板/重载类错误走一遍
+   R1-FAIL→6a,专验 C++ 报错的指纹稳定性;
+7. 报告:`docs/clang-fix-campaign/review/e2e-smoke-report-v1.md`
+   按 runbook E5 格式,含全部妥协项与偏差清单;偏差 = 停止报告的
+   候选,不许静默吸收。
+
+## RD. close-out 与收尾(RC 全绿或偏差被裁决后)
+
+1. P4.5 close-out 报告(按权威 prompt P4:P2 自查表逐条打勾+代码
+   定位、DoD→测试映射含反向验证双态输出、
+   `git diff 85310ef..HEAD --stat` 证零修改名单未触碰、裁量记录);
+2. dev_memory 各 stage result.md 补终态、INDEX 更新;
+3. **提 PR**(标题 `[P4.5] clang-fix-campaign repair step`,描述含
+   测试数/覆盖/关联 design 章节/已知风险),然后**停止,等开发者
+   人工 review**——三方 review finding 闭环 + smoke 全绿 + PR 人工
+   放行,三者齐备才允许 merge,merge 由你执行。
+
+## 完成定义
+
+RA/RB 两个 commit 落盘 → RC 报告(含 E6 每 case 小节)→ RD PR
+挂起等人工。任何一步现实与设计冲突:停在那里,立案 change_41+。
diff --git a/docs/clang-fix-campaign/review/claude-review-ledger.md b/docs/clang-fix-campaign/review/claude-review-ledger.md
new file mode 100644
index 0000000..9cd099c
--- /dev/null
+++ b/docs/clang-fix-campaign/review/claude-review-ledger.md
@@ -0,0 +1,39 @@
+# Claude Review Ledger (Reconstructed)
+
+## Provenance Warning
+
+The remediation task states that an original ledger was delivered, but no
+standalone ledger was present in the repository or available attachment tree
+when RA ran. This file is therefore reconstructed only from machine-resident
+`change_32.md` through `change_40.md`, Git commit metadata, and the P0 signature
+audit. It is not a verbatim transcript and does not invent missing quotations.
+
+## Review Rounds
+
+| Change | Recorded review input | Material outcome |
+|---|---|---|
+| 32 | dual review, details retained in the change ledger | convergence uniqueness, evidence tuple integrity, checker work identified |
+| 33 | external: 1 BLOCKER, 4 MAJOR, 1 MINOR; Claude: four execution gaps, 1 MAJOR, 2 MINOR | relink-before-orphan recovery; HELD precheck reachability; authority cleanup |
+| 34 | external: 3 BLOCKER, 2 MAJOR; Claude: 4 MINOR | atomic reconciliation API; remove impossible compensation; recovery before precheck |
+| 35 | external: 2 BLOCKER, 3 MAJOR, 1 MINOR; Claude: no new finding | per-round pairing; deterministic PASS payload reconstruction |
+| 36 | external: 2 BLOCKER, 2 MAJOR, 1 MINOR; Claude review recorded in source | edit-spec based round attribution; unified group handling |
+| 37 | external: 4 BLOCKER/MAJOR; Claude: 1 BLOCKER plus additional findings | ledger repair separated from current exit; impossible attribution treated as corruption |
+| 38 | external: 1 BLOCKER, 3 MAJOR, 1 MINOR; Claude: 1 MINOR, 1 NIT | create-round authority restored before reconcile; A0 integrity precheck; fixed stdout schema |
+| 39 | Codex stop-and-report; subsequent reviews recorded as v1-v3 revisions | executable API/index checker rules, prompt authority, signature audit requirement |
+| 40 | Codex stop-and-report on checker contradiction; v2 closes prompt pointer conflicts | checker uses `compile`, exact prompt SHA gate, v1.5.16 freeze |
+
+## Closure Evidence
+
+- `review/p0-signature-audit-v1.5.16.md`: complete 45-item audit and independent
+  high-risk signature PASS 4/4.
+- `tools/check_design_doc.py --self-test`: 33/33 at P0.
+- Frozen design and snapshot SHA:
+  `ff73f5e3c6d54a75ae60771b98eadcfc1a4d1422ca8faf337a3de09eee4346ff`.
+- Authoritative prompt SHA:
+  `e214d1fb8b806e1ebc12e6e8cfafc57d71cbffcf0340d94c26396ef87816a3fb`.
+
+## Outstanding Closure
+
+This reconstructed ledger does not claim final three-way review of the code.
+RB generates the self-contained packages for that review, and RD must close
+BLOCKER/MAJOR findings before merge.
diff --git a/docs/clang-fix-campaign/review/p0-signature-audit-v1.5.16.md b/docs/clang-fix-campaign/review/p0-signature-audit-v1.5.16.md
index 4c68695..1c10b84 100644
--- a/docs/clang-fix-campaign/review/p0-signature-audit-v1.5.16.md
+++ b/docs/clang-fix-campaign/review/p0-signature-audit-v1.5.16.md
@@ -267,3 +267,26 @@ sha256sum docs/clang-fix-campaign/p45-implementation-prompt-v1_5_15.md
 Results: Ruff clean; checker self-test `33/33`; current design `OK: 0
 problem`; snapshot byte-identical; prompt SHA-256
 `e214d1fb8b806e1ebc12e6e8cfafc57d71cbffcf0340d94c26396ef87816a3fb`.
+
+## Independent Four-Signature Check
+
+The independently extracted v1.5.14 parameter table was checked against the
+final Python declarations before P1 started:
+
+```bash
+python3 audit_four_sigs.py docs/clang-fix-campaign/design.md
+```
+
+Output:
+
+```text
+[OK] reconcile_pass_and_invocations
+[OK] adopt_secondary_target_with_convergence
+[OK] consume_build_invocation
+[OK] append_status
+
+result: PASS 4/4
+```
+
+This closes the dual-path transcription check: the implementation-side audit
+and the independent extraction agree on all four high-risk signatures.
diff --git a/tests/unit/test_campaign_reconcile.py b/tests/unit/test_campaign_reconcile.py
new file mode 100644
index 0000000..1359b63
--- /dev/null
+++ b/tests/unit/test_campaign_reconcile.py
@@ -0,0 +1,816 @@
+from __future__ import annotations
+
+import inspect
+import json
+import shutil
+import sqlite3
+import subprocess
+from dataclasses import dataclass
+from pathlib import Path
+from typing import cast
+
+import pytest
+from ci_triage import campaign_state
+from ci_triage.campaign_state import (
+    CAMPAIGN_SCHEMA_VERSION,
+    HELD_FOR_INVESTIGATION,
+    CampaignStateBusy,
+    ReconcileResult,
+    consume_build_invocation,
+    create_round,
+    create_unit,
+    ensure_schema,
+    link_verification_with_convergence,
+    reconcile_pass_and_invocations,
+)
+from ci_triage.state import StateDatabase, VerificationRecord, write_pass_record
+
+UNIT_KEY = "campaign:test-unit"
+FAILURE_KEY = "quickbuild/failure/aarch64"
+EDIT_ONE = "1" * 64
+EDIT_TWO = "2" * 64
+
+pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
+
+
+@dataclass(frozen=True)
+class GitFixture:
+    template: Path
+    base_commit: str
+    verified_commit: str
+    verified_tree: str
+    changed_paths: tuple[str, ...]
+
+
+def _git(cwd: Path, *args: str) -> str:
+    completed = subprocess.run(
+        ["git", "-C", str(cwd), *args],
+        check=True,
+        capture_output=True,
+        text=True,
+    )
+    return completed.stdout.strip()
+
+
+def _git_fixture(tmp_path: Path) -> GitFixture:
+    repo = tmp_path / "template"
+    repo.mkdir()
+    _git(repo, "init")
+    _git(repo, "config", "user.email", "ci-triage-test@example.invalid")
+    _git(repo, "config", "user.name", "CI Triage Test")
+    files = {
+        "src/main.c": "int main(void) { return 0; }\n",
+        "src/name with space.c": "int spaced = 0;\n",
+        'src/say"hi.c': "int quoted = 0;\n",
+    }
+    for relative, content in files.items():
+        path = repo / relative
+        path.parent.mkdir(parents=True, exist_ok=True)
+        path.write_text(content, encoding="utf-8")
+    _git(repo, "add", "-A")
+    _git(repo, "commit", "-m", "base")
+    base = _git(repo, "rev-parse", "HEAD")
+    for relative in files:
+        path = repo / relative
+        path.write_text(path.read_text(encoding="utf-8") + "/* fixed */\n", encoding="utf-8")
+    _git(repo, "add", "-A")
+    _git(repo, "commit", "-m", "verified")
+    verified = _git(repo, "rev-parse", "HEAD")
+    tree = _git(repo, "rev-parse", "HEAD^{tree}")
+    return GitFixture(
+        template=repo,
+        base_commit=base,
+        verified_commit=verified,
+        verified_tree=tree,
+        changed_paths=tuple(sorted(files)),
+    )
+
+
+def _db(tmp_path: Path) -> StateDatabase:
+    db = StateDatabase(tmp_path / "state.sqlite3")
+    ensure_schema(db)
+    return db
+
+
+def _create_unit(db: StateDatabase, git: GitFixture) -> None:
+    create_unit(
+        db,
+        campaign_unit_key=UNIT_KEY,
+        submission_identity_key="submission:test-unit",
+        primary_arch="standard-aarch64",
+        failed_arches=("standard-aarch64",),
+        toolchain_profile="tizen_unified_standard",
+        ci_evidence_ref="/tmp/ci-evidence.json",
+        ci_evidence_sha256="c" * 64,
+        max_rounds=4,
+        max_build_invocations=12,
+        ci_system="quickbuild",
+        source_build_id="1234",
+        project="platform/core/appfw/united-service",
+        branch="tizen",
+        spec_name="united-service",
+        base_commit=git.base_commit,
+    )
+
+
+def _create_campaign_round(
+    db: StateDatabase,
+    round_index: int,
+    edit_sha: str,
+) -> None:
+    create_round(
+        db,
+        UNIT_KEY,
+        round_index=round_index,
+        edit_spec_ref=f"relative/round-{round_index}.json",
+        edit_spec_sha256=edit_sha,
+    )
+
+
+def _protected_worktree(
+    tmp_path: Path,
+    git: GitFixture,
+    verification_id: str,
+) -> Path:
+    path = tmp_path / f"worktree-{verification_id}"
+    shutil.copytree(git.template, path, symlinks=True)
+    exclude = Path(_git(path, "rev-parse", "--git-path", "info/exclude"))
+    if not exclude.is_absolute():
+        exclude = path / exclude
+    with exclude.open("a", encoding="utf-8") as stream:
+        stream.write("\n.ci_triage_protected\n")
+    (path / ".ci_triage_protected").write_text(
+        json.dumps(
+            {
+                "protected_reason": "GERRIT_READY",
+                "verification_id": verification_id,
+                "failure_key": FAILURE_KEY,
+            },
+            sort_keys=True,
+        )
+        + "\n",
+        encoding="utf-8",
+    )
+    assert _git(path, "status", "--porcelain") == ""
+    return path
+
+
+def _write_record(
+    db: StateDatabase,
+    tmp_path: Path,
+    git: GitFixture,
+    verification_id: str,
+    *,
+    edit_sha: str = EDIT_ONE,
+    failure_key: str = FAILURE_KEY,
+    valid_worktree: bool = True,
+) -> VerificationRecord:
+    worktree = (
+        _protected_worktree(tmp_path, git, verification_id)
+        if valid_worktree
+        else tmp_path / f"missing-{verification_id}"
+    )
+    record = VerificationRecord(
+        verification_id=verification_id,
+        result="PASS",
+        timestamp=f"2026-08-05T00:00:{verification_id[-1:]}0+00:00",
+        failure_key=failure_key,
+        base_commit=git.base_commit,
+        verified_commit_sha=git.verified_commit,
+        verified_tree_sha=git.verified_tree,
+        canonical_diff_sha256="d" * 64,
+        patch_sha256="e" * 64,
+        edit_spec_sha256=edit_sha,
+        project="platform/core/appfw/united-service",
+        branch="tizen",
+        spec_name="united-service",
+        arch="standard-aarch64",
+        gbs_conf_sha256="f" * 64,
+        build_log_sha256="a" * 64,
+        worktree_path=str(worktree),
+        command_line="gbs -c conf build -A aarch64 --include-all",
+    )
+    write_pass_record(db, record)
+    return record
+
+
+def _pass_payload(
+    invocation_event_id: int,
+    verification_id: str,
+    *,
+    round_index: int,
+) -> dict[str, object]:
+    return {
+        "round_index": round_index,
+        "arch_norm": "aarch64",
+        "invocation_event_id": invocation_event_id,
+        "result": "PASS",
+        "verdict": "n_a",
+        "reason": "build_passed",
+        "evidence_path": None,
+        "evidence_sha256": None,
+        "verification_id": verification_id,
+        "actual_changed_paths": ["src/main.c"],
+        "previous_basis": "none",
+        "at": "2026-08-05T00:00:00+00:00",
+    }
+
+
+def _reconcile(
+    db: StateDatabase,
+    *,
+    round_index: int = 1,
+    edit_sha: str = EDIT_ONE,
+) -> ReconcileResult:
+    return reconcile_pass_and_invocations(
+        db,
+        UNIT_KEY,
+        round_index=round_index,
+        arch_norm="aarch64",
+        failure_key=FAILURE_KEY,
+        edit_spec_sha256=edit_sha,
+    )
+
+
+def _events(db: StateDatabase, event_type: str) -> list[sqlite3.Row]:
+    conn = db.connect()
+    try:
+        return conn.execute(
+            "SELECT * FROM campaign_gate_events WHERE campaign_unit_key = ? "
+            "AND event_type = ? ORDER BY event_id",
+            (UNIT_KEY, event_type),
+        ).fetchall()
+    finally:
+        conn.close()
+
+
+def _latest_campaign_status(db: StateDatabase) -> sqlite3.Row | None:
+    conn = db.connect()
+    try:
+        return cast(
+            sqlite3.Row | None,
+            conn.execute(
+                "SELECT * FROM campaign_status_log WHERE campaign_unit_key = ? "
+                "ORDER BY log_id DESC LIMIT 1",
+                (UNIT_KEY,),
+            ).fetchone(),
+        )
+    finally:
+        conn.close()
+
+
+def test_reconcile_relinks_current_pass_in_one_transaction_and_rebuilds_paths(
+    tmp_path: Path,
+) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    _write_record(db, tmp_path, git, "V1")
+
+    result = _reconcile(db)
+
+    assert result.branch == "relinked"
+    assert result.current_verification_id == "V1"
+    assert result.current_relinked_invocation_event_id == receipt.event_id
+    assert result.other_round_relinks == ()
+    convergence = _events(db, "CONVERGENCE")
+    assert len(convergence) == 1
+    payload = json.loads(convergence[0]["payload_json"])
+    assert payload["invocation_event_id"] == receipt.event_id
+    assert payload["actual_changed_paths"] == list(git.changed_paths)
+
+
+def test_reconcile_uses_transaction_internal_link_primitive() -> None:
+    source = inspect.getsource(reconcile_pass_and_invocations)
+
+    assert "_link_verification_with_convergence_on_connection(" in source
+    assert "link_verification_with_convergence(" not in source
+
+
+def test_linked_current_branch_still_backfills_other_orphan_invocations(
+    tmp_path: Path,
+) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    orphan = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    _create_campaign_round(db, 2, EDIT_TWO)
+    current = consume_build_invocation(db, UNIT_KEY, round_index=2, arch_norm="aarch64")
+    record = _write_record(db, tmp_path, git, "V2", edit_sha=EDIT_TWO)
+    link_verification_with_convergence(
+        db,
+        UNIT_KEY,
+        convergence_payload=_pass_payload(current.event_id, "V2", round_index=2),
+        arch_raw=record.arch,
+        arch_norm="aarch64",
+        verification_id="V2",
+        round_index=2,
+        edit_spec_sha256=EDIT_TWO,
+    )
+
+    result = _reconcile(db, round_index=2, edit_sha=EDIT_TWO)
+
+    assert result.branch == "linked_already"
+    assert result.current_verification_id == "V2"
+    assert result.backfilled_invocation_event_ids == (orphan.event_id,)
+    payloads = [json.loads(row["payload_json"]) for row in _events(db, "CONVERGENCE")]
+    assert any(
+        item["invocation_event_id"] == orphan.event_id and item["reason"] == "orphan_invocation"
+        for item in payloads
+    )
+
+
+def test_historical_relink_repairs_ledger_without_granting_current_success(
+    tmp_path: Path,
+) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    old = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    _write_record(db, tmp_path, git, "V1")
+    _create_campaign_round(db, 2, EDIT_TWO)
+
+    result = _reconcile(db, round_index=2, edit_sha=EDIT_TWO)
+
+    assert result.branch == "proceed"
+    assert result.current_verification_id is None
+    assert result.other_round_relinks == ((1, "V1", old.event_id),)
+
+
+def test_linked_pass_from_prior_round_does_not_short_circuit_new_round(
+    tmp_path: Path,
+) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    old = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    record = _write_record(db, tmp_path, git, "V1")
+    link_verification_with_convergence(
+        db,
+        UNIT_KEY,
+        convergence_payload=_pass_payload(old.event_id, "V1", round_index=1),
+        arch_raw=record.arch,
+        arch_norm="aarch64",
+        verification_id="V1",
+        round_index=1,
+        edit_spec_sha256=EDIT_ONE,
+    )
+    _create_campaign_round(db, 2, EDIT_TWO)
+
+    result = _reconcile(db, round_index=2, edit_sha=EDIT_TWO)
+
+    assert result.branch == "proceed"
+    assert result.current_verification_id is None
+    assert result.other_round_relinks == ()
+
+
+@pytest.mark.parametrize("orphan_count", [0, 2])
+def test_single_pass_without_exactly_one_invocation_is_held(
+    tmp_path: Path,
+    orphan_count: int,
+) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    for _ in range(orphan_count):
+        consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    _write_record(db, tmp_path, git, "V1")
+
+    result = _reconcile(db)
+
+    assert result.branch == "orphan_pass_held"
+    assert result.orphan_pass_verification_ids == ("V1",)
+    assert result.held_rounds == (1,)
+    assert len(_events(db, "ORPHAN_PASS")) == 1
+    status = _latest_campaign_status(db)
+    assert status is not None
+    assert status["status"] == HELD_FOR_INVESTIGATION
+    assert not _events(db, "CONVERGENCE")
+
+
+def test_multiple_passes_are_all_recorded_and_freeze_the_round(tmp_path: Path) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    _write_record(db, tmp_path, git, "V1")
+    _write_record(db, tmp_path, git, "V2")
+
+    result = _reconcile(db)
+
+    assert result.branch == "orphan_pass_held"
+    assert result.orphan_pass_verification_ids == ("V1", "V2")
+    assert len(_events(db, "ORPHAN_PASS")) == 2
+    assert not _events(db, "CONVERGENCE")
+
+
+def test_damaged_worktree_becomes_orphan_pass_instead_of_partial_link(
+    tmp_path: Path,
+) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    _write_record(db, tmp_path, git, "V1", valid_worktree=False)
+
+    result = _reconcile(db)
+
+    assert result.branch == "orphan_pass_held"
+    orphan = json.loads(_events(db, "ORPHAN_PASS")[0]["payload_json"])
+    assert orphan["reason"] == "worktree_damaged"
+    conn = db.connect()
+    try:
+        assert conn.execute("SELECT COUNT(*) FROM campaign_verifications").fetchone()[0] == 0
+    finally:
+        conn.close()
+
+
+def test_non_campaign_pass_is_reported_without_events_or_held_status(tmp_path: Path) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    _write_record(db, tmp_path, git, "VX", edit_sha="9" * 64)
+
+    result = _reconcile(db)
+
+    assert result.branch == "proceed"
+    assert result.non_campaign_verification_ids == ("VX",)
+    assert not _events(db, "ORPHAN_PASS")
+    assert _latest_campaign_status(db) is None
+
+
+def test_a0_half_state_is_held_before_orphan_backfill_can_mask_it(tmp_path: Path) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    record = _write_record(db, tmp_path, git, "V1")
+    link_verification_with_convergence(
+        db,
+        UNIT_KEY,
+        convergence_payload=_pass_payload(receipt.event_id, "V1", round_index=1),
+        arch_raw=record.arch,
+        arch_norm="aarch64",
+        verification_id="V1",
+        round_index=1,
+        edit_spec_sha256=EDIT_ONE,
+    )
+    conn = db.connect()
+    try:
+        conn.execute("DELETE FROM campaign_gate_events WHERE event_type = 'CONVERGENCE'")
+        conn.commit()
+    finally:
+        conn.close()
+
+    result = _reconcile(db)
+
+    assert result.branch == "state_inconsistent_held"
+    assert not _events(db, "CONVERGENCE")
+    status = _latest_campaign_status(db)
+    assert status is not None
+    assert status["reason"] == "state_inconsistent"
+    assert status["arch_norm"] == "aarch64"
+
+
+def test_a0_rejects_duplicate_pass_binding_that_weak_exists_check_would_accept(
+    tmp_path: Path,
+) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    first = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    record = _write_record(db, tmp_path, git, "V1")
+    link_verification_with_convergence(
+        db,
+        UNIT_KEY,
+        convergence_payload=_pass_payload(first.event_id, "V1", round_index=1),
+        arch_raw=record.arch,
+        arch_norm="aarch64",
+        verification_id="V1",
+        round_index=1,
+        edit_spec_sha256=EDIT_ONE,
+    )
+    second = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    duplicate = _pass_payload(second.event_id, "V1", round_index=1)
+    conn = db.connect()
+    try:
+        conn.execute(
+            "INSERT INTO campaign_gate_events "
+            "(campaign_unit_key, round_index, arch_norm, verdict, invocation_event_id, "
+            "event_type, payload_json, created_at) VALUES (?, 1, 'aarch64', 'n_a', ?, "
+            "'CONVERGENCE', ?, ?)",
+            (
+                UNIT_KEY,
+                second.event_id,
+                json.dumps(duplicate, sort_keys=True, separators=(",", ":")),
+                "2026-08-05T01:00:00+00:00",
+            ),
+        )
+        conn.commit()
+        weak_exists = conn.execute(
+            "SELECT COUNT(*) FROM campaign_gate_events WHERE event_type = 'CONVERGENCE' "
+            'AND payload_json LIKE \'%"verification_id":"V1"%\''
+        ).fetchone()[0]
+    finally:
+        conn.close()
+
+    result = _reconcile(db)
+
+    assert weak_exists >= 1
+    assert result.branch == "state_inconsistent_held"
+
+
+def test_a0_rejects_single_pass_bound_to_wrong_round_invocation(tmp_path: Path) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    first = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    record = _write_record(db, tmp_path, git, "V1")
+    link_verification_with_convergence(
+        db,
+        UNIT_KEY,
+        convergence_payload=_pass_payload(first.event_id, "V1", round_index=1),
+        arch_raw=record.arch,
+        arch_norm="aarch64",
+        verification_id="V1",
+        round_index=1,
+        edit_spec_sha256=EDIT_ONE,
+    )
+    _create_campaign_round(db, 2, EDIT_TWO)
+    wrong = consume_build_invocation(db, UNIT_KEY, round_index=2, arch_norm="aarch64")
+    conn = db.connect()
+    try:
+        row = conn.execute(
+            "SELECT event_id, payload_json FROM campaign_gate_events "
+            "WHERE event_type = 'CONVERGENCE'"
+        ).fetchone()
+        payload = json.loads(row["payload_json"])
+        payload["invocation_event_id"] = wrong.event_id
+        conn.execute(
+            "UPDATE campaign_gate_events SET invocation_event_id = ?, payload_json = ? "
+            "WHERE event_id = ?",
+            (
+                wrong.event_id,
+                json.dumps(payload, sort_keys=True, separators=(",", ":")),
+                row["event_id"],
+            ),
+        )
+        conn.commit()
+    finally:
+        conn.close()
+
+    result = _reconcile(db)
+
+    assert result.branch == "state_inconsistent_held"
+    payloads = [json.loads(row["payload_json"]) for row in _events(db, "CONVERGENCE")]
+    assert all(item["reason"] != "orphan_invocation" for item in payloads)
+
+
+def test_multiple_round_attribution_is_state_inconsistent_when_guard_is_bypassed(
+    tmp_path: Path,
+) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    conn = db.connect()
+    try:
+        conn.execute("PRAGMA foreign_keys=OFF")
+        conn.executescript(
+            """
+            DROP TABLE campaign_verifications;
+            ALTER TABLE campaign_rounds RENAME TO campaign_rounds_guarded;
+            CREATE TABLE campaign_rounds (
+              campaign_unit_key TEXT NOT NULL,
+              round_index INTEGER NOT NULL,
+              edit_spec_ref TEXT NOT NULL,
+              edit_spec_sha256 TEXT NOT NULL,
+              created_at TEXT NOT NULL,
+              PRIMARY KEY (campaign_unit_key, round_index)
+            );
+            INSERT INTO campaign_rounds SELECT * FROM campaign_rounds_guarded;
+            DROP TABLE campaign_rounds_guarded;
+            CREATE TABLE campaign_verifications (
+              link_id INTEGER PRIMARY KEY AUTOINCREMENT,
+              campaign_unit_key TEXT NOT NULL,
+              arch_raw TEXT NOT NULL,
+              arch_norm TEXT NOT NULL,
+              verification_id TEXT NOT NULL UNIQUE,
+              round_index INTEGER NOT NULL,
+              edit_spec_sha256 TEXT NOT NULL,
+              campaign_schema_version TEXT NOT NULL,
+              created_at TEXT NOT NULL,
+              UNIQUE (campaign_unit_key, arch_norm, round_index)
+            );
+            """
+        )
+        conn.execute(
+            "INSERT INTO campaign_rounds VALUES (?, 2, ?, ?, ?)",
+            (
+                UNIT_KEY,
+                str((tmp_path / "round-2.json").resolve()),
+                EDIT_ONE,
+                "2026-08-05T00:00:00+00:00",
+            ),
+        )
+        conn.commit()
+    finally:
+        conn.close()
+    _write_record(db, tmp_path, git, "V1")
+
+    result = _reconcile(db)
+
+    assert result.branch == "state_inconsistent_held"
+    assert not _events(db, "ORPHAN_PASS")
+    status = _latest_campaign_status(db)
+    assert status is not None
+    assert status["reason"] == "state_inconsistent"
+
+
+def test_relink_savepoint_prevents_half_link_when_event_insert_fails(
+    tmp_path: Path,
+    monkeypatch: pytest.MonkeyPatch,
+) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    _write_record(db, tmp_path, git, "V1")
+    original = campaign_state._insert_event_row
+
+    def fail_pass_event(
+        conn: sqlite3.Connection,
+        campaign_unit_key: str,
+        event_type: str,
+        payload: dict[str, object],
+    ) -> int:
+        if event_type == "CONVERGENCE":
+            raise sqlite3.IntegrityError("injected convergence failure")
+        return original(conn, campaign_unit_key, event_type, payload)
+
+    monkeypatch.setattr(campaign_state, "_insert_event_row", fail_pass_event)
+
+    result = _reconcile(db)
+
+    assert result.branch == "orphan_pass_held"
+    conn = db.connect()
+    try:
+        assert conn.execute("SELECT COUNT(*) FROM campaign_verifications").fetchone()[0] == 0
+    finally:
+        conn.close()
+
+
+def test_reconcile_busy_lock_is_retryable_and_writes_nothing(
+    tmp_path: Path,
+    monkeypatch: pytest.MonkeyPatch,
+) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    lock = db.connect()
+    lock.execute("BEGIN IMMEDIATE")
+    original_connect = campaign_state._connect
+
+    def connect_with_short_timeout(state_db: StateDatabase) -> sqlite3.Connection:
+        conn = original_connect(state_db)
+        conn.execute("PRAGMA busy_timeout=1")
+        return conn
+
+    monkeypatch.setattr(campaign_state, "_connect", connect_with_short_timeout)
+    try:
+        with pytest.raises(CampaignStateBusy, match="CAMPAIGN_STATE_BUSY"):
+            _reconcile(db)
+    finally:
+        lock.rollback()
+        lock.close()
+
+    assert not _events(db, "CONVERGENCE")
+    assert _latest_campaign_status(db) is None
+
+
+def test_orphan_pass_overrides_current_linked_success_but_keeps_clean_writes(
+    tmp_path: Path,
+) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    _write_record(db, tmp_path, git, "V1")
+    _write_record(db, tmp_path, git, "V1B")
+    _create_campaign_round(db, 2, EDIT_TWO)
+    current = consume_build_invocation(db, UNIT_KEY, round_index=2, arch_norm="aarch64")
+    record = _write_record(db, tmp_path, git, "V2", edit_sha=EDIT_TWO)
+    link_verification_with_convergence(
+        db,
+        UNIT_KEY,
+        convergence_payload=_pass_payload(current.event_id, "V2", round_index=2),
+        arch_raw=record.arch,
+        arch_norm="aarch64",
+        verification_id="V2",
+        round_index=2,
+        edit_spec_sha256=EDIT_TWO,
+    )
+
+    result = _reconcile(db, round_index=2, edit_sha=EDIT_TWO)
+
+    assert result.branch == "orphan_pass_held"
+    assert result.current_verification_id is None
+    assert result.held_rounds == (1,)
+    conn = db.connect()
+    try:
+        assert (
+            conn.execute(
+                "SELECT COUNT(*) FROM campaign_verifications WHERE verification_id = 'V2'"
+            ).fetchone()[0]
+            == 1
+        )
+    finally:
+        conn.close()
+
+
+def test_orphan_pass_overrides_current_relink_but_commits_the_clean_relink(
+    tmp_path: Path,
+) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    current = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    _write_record(db, tmp_path, git, "V1")
+    _create_campaign_round(db, 2, EDIT_TWO)
+    consume_build_invocation(db, UNIT_KEY, round_index=2, arch_norm="aarch64")
+    _write_record(db, tmp_path, git, "V2A", edit_sha=EDIT_TWO)
+    _write_record(db, tmp_path, git, "V2B", edit_sha=EDIT_TWO)
+
+    result = _reconcile(db)
+
+    assert result.branch == "orphan_pass_held"
+    assert result.current_verification_id is None
+    assert result.orphan_pass_verification_ids == ("V2A", "V2B")
+    conn = db.connect()
+    try:
+        link = conn.execute(
+            "SELECT verification_id FROM campaign_verifications WHERE round_index = 1"
+        ).fetchone()
+        convergence = conn.execute(
+            "SELECT payload_json FROM campaign_gate_events "
+            "WHERE event_type = 'CONVERGENCE' AND invocation_event_id = ?",
+            (current.event_id,),
+        ).fetchone()
+    finally:
+        conn.close()
+    assert link["verification_id"] == "V1"
+    assert json.loads(convergence["payload_json"])["result"] == "PASS"
+
+
+def test_reconcile_result_lists_are_deterministically_sorted(tmp_path: Path) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    _write_record(db, tmp_path, git, "VZ", edit_sha="9" * 64)
+    _write_record(db, tmp_path, git, "VA", edit_sha="8" * 64)
+
+    result = _reconcile(db)
+
+    assert result.non_campaign_verification_ids == ("VA", "VZ")
+
+
+def test_reconcile_keeps_existing_link_api_behavior(tmp_path: Path) -> None:
+    git = _git_fixture(tmp_path)
+    db = _db(tmp_path)
+    _create_unit(db, git)
+    _create_campaign_round(db, 1, EDIT_ONE)
+    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    record = _write_record(db, tmp_path, git, "V1")
+
+    link_verification_with_convergence(
+        db,
+        UNIT_KEY,
+        convergence_payload=_pass_payload(receipt.event_id, "V1", round_index=1),
+        arch_raw=record.arch,
+        arch_norm="aarch64",
+        verification_id="V1",
+        round_index=1,
+        edit_spec_sha256=EDIT_ONE,
+    )
+
+    result = _reconcile(db)
+    assert result.branch == "linked_already"
+    assert result.current_verification_id == "V1"
+    assert CAMPAIGN_SCHEMA_VERSION == "campaign/v1"
diff --git a/tests/unit/test_campaign_repair_step.py b/tests/unit/test_campaign_repair_step.py
new file mode 100644
index 0000000..5dad030
--- /dev/null
+++ b/tests/unit/test_campaign_repair_step.py
@@ -0,0 +1,989 @@
+from __future__ import annotations
+
+import fcntl
+import hashlib
+import json
+import os
+import subprocess
+import sys
+from collections.abc import Callable
+from dataclasses import dataclass
+from pathlib import Path
+
+import pytest
+from ci_triage import campaign_repair_step as repair_step
+from ci_triage import cli
+from ci_triage.campaign_repair_step import (
+    CAMPAIGN_STATE_BUSY,
+    REJECTED_IDENTITY_MISMATCH,
+    REJECTED_PREVIOUS_EVIDENCE_MISSING,
+    CampaignRepairStepOptions,
+    campaign_repair_step,
+)
+from ci_triage.campaign_state import (
+    HELD_FOR_INVESTIGATION,
+    ReconcileResult,
+    append_event,
+    consume_build_invocation,
+    create_round,
+    create_unit,
+    ensure_schema,
+    is_rebaseline_authorized,
+    link_verification_with_convergence,
+    reconcile_pass_and_invocations,
+)
+from ci_triage.previous_evidence import MissingEvidence, ResolvedEvidence, resolve
+from ci_triage.state import (
+    StateDatabase,
+    VerificationRecord,
+    build_failure_key,
+    write_pass_record,
+)
+from ci_triage.verify.build_verify import BuildVerifyOptions, BuildVerifyResult
+from ci_triage.verify.convergence import ConvergenceResult
+
+UNIT_KEY = "campaign:repair-step"
+ARCH_RAW = "standard-aarch64"
+ARCH_NORM = "aarch64"
+PROJECT = "platform/core/appfw/united-service"
+BASE_PACKET = {
+    "schema_version": "evidence_packet/v1",
+    "primary_error": {
+        "kind": "werror",
+        "file": "src/main.c",
+        "line": 1,
+        "message": "error: unused field [-Werror,-Wunused-private-field]",
+    },
+    "error_clusters": {
+        "schema_version": "error_clusters/v1",
+        "clusters": [],
+        "truncated": False,
+    },
+    "root_cause_candidates": [],
+}
+RESULT_KEYS = {
+    "result",
+    "verdict",
+    "repair_allowed",
+    "failure_class",
+    "failure_stage",
+    "adopted",
+    "convergence_reason",
+    "previous_basis",
+    "round_index",
+    "arch_norm",
+    "verification_id",
+    "evidence_path",
+    "reconciliation",
+    "warnings",
+    "invocations_used",
+    "error_code",
+}
+
+
+@dataclass(frozen=True)
+class Fixture:
+    db: StateDatabase
+    options: CampaignRepairStepOptions
+    workspace: Path
+    src: Path
+    evidence: Path
+    conf: Path
+    edit_spec: Path
+    base_commit: str
+
+
+def _git(cwd: Path, *args: str) -> str:
+    completed = subprocess.run(
+        ["git", "-C", str(cwd), *args],
+        check=True,
+        capture_output=True,
+        text=True,
+    )
+    return completed.stdout.strip()
+
+
+def _fixture(tmp_path: Path, *, max_rounds: int = 3) -> Fixture:
+    db = StateDatabase(tmp_path / "state.sqlite3")
+    ensure_schema(db)
+    workspace = tmp_path / "campaign-ws"
+    unit_hash = hashlib.sha256(UNIT_KEY.encode()).hexdigest()[:12]
+    src = workspace / unit_hash / "src"
+    src.mkdir(parents=True)
+    _git(src, "init")
+    _git(src, "config", "user.email", "ci-triage-test@example.invalid")
+    _git(src, "config", "user.name", "CI Triage Test")
+    (src / "src").mkdir()
+    (src / "src/main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
+    _git(src, "add", "src/main.c")
+    _git(src, "commit", "-m", "base")
+    base_commit = _git(src, "rev-parse", "HEAD")
+    _git(src, "remote", "add", "origin", f"ssh://review.tizen.org:29418/{PROJECT}")
+    (src / ".campaign_clone").write_text(
+        json.dumps(
+            {"unit_key": UNIT_KEY, "project": PROJECT, "base_commit": base_commit},
+            sort_keys=True,
+        )
+        + "\n",
+        encoding="utf-8",
+    )
+
+    evidence = tmp_path / "baseline.json"
+    evidence.write_text(json.dumps(BASE_PACKET, sort_keys=True) + "\n", encoding="utf-8")
+    conf = tmp_path / "gbs.conf"
+    conf.write_text("[general]\n", encoding="utf-8")
+    edit_spec = tmp_path / "input-edit-spec.json"
+    edit_spec.write_text(
+        json.dumps(
+            {
+                "schema_version": "gbs_patch_suggest/edit-spec/v1",
+                "patch_name": "repair",
+                "edits": [
+                    {"file": "src/main.c", "old": "return 0", "new": "return 1"}
+                ],
+            },
+            sort_keys=True,
+        )
+        + "\n",
+        encoding="utf-8",
+    )
+    ci_hash = "c" * 64
+    create_unit(
+        db,
+        campaign_unit_key=UNIT_KEY,
+        submission_identity_key="submission:repair-step",
+        primary_arch=ARCH_RAW,
+        failed_arches=(ARCH_RAW,),
+        toolchain_profile="tizen_unified_standard",
+        ci_evidence_ref=str(tmp_path / "ci-evidence.json"),
+        ci_evidence_sha256=ci_hash,
+        max_rounds=max_rounds,
+        max_build_invocations=9,
+        ci_system="quickbuild",
+        source_build_id="1127447",
+        project=PROJECT,
+        branch="tizen",
+        spec_name="united-service",
+        base_commit=base_commit,
+    )
+    append_event(
+        db,
+        UNIT_KEY,
+        "REPRODUCE",
+        {
+            "arch_norm": ARCH_NORM,
+            "outcome": "matched",
+            "evidence_local": str(evidence),
+            "evidence_sha256": _sha(evidence),
+            "synthetic_zero_error": False,
+            "gbs_conf_sha256": _sha(conf),
+            "ci_evidence_sha256_used": ci_hash,
+            "build_log": str(tmp_path / "baseline.log"),
+            "basis": {},
+        },
+    )
+    config = tmp_path / "campaign.yaml"
+    config.write_text(
+        f"campaign_workspace: {workspace}\nclang_conf_path: {conf}\n",
+        encoding="utf-8",
+    )
+    return Fixture(
+        db=db,
+        options=CampaignRepairStepOptions(
+            campaign_unit_key=UNIT_KEY,
+            state_db=db,
+            config_path=config,
+            round_index=1,
+            edit_spec_path=edit_spec,
+            arch_raw=ARCH_RAW,
+            extra_pythonpath=(),
+        ),
+        workspace=workspace,
+        src=src,
+        evidence=evidence,
+        conf=conf,
+        edit_spec=edit_spec,
+        base_commit=base_commit,
+    )
+
+
+def _sha(path: Path) -> str:
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+def _failure_key(fixture: Fixture) -> str:
+    return build_failure_key(
+        ci_system="quickbuild",
+        build_id="1127447",
+        project=PROJECT,
+        branch="tizen",
+        arch=ARCH_RAW,
+        spec_name="united-service",
+        base_commit=fixture.base_commit,
+    )
+
+
+def _write_pass_record(
+    fixture: Fixture,
+    options: BuildVerifyOptions,
+    verification_id: str = "verify-pass",
+    edit_sha: str | None = None,
+) -> None:
+    write_pass_record(
+        fixture.db,
+        VerificationRecord(
+            verification_id=verification_id,
+            result="PASS",
+            timestamp="2026-08-05T00:00:00+00:00",
+            failure_key=_failure_key(fixture),
+            base_commit=fixture.base_commit,
+            verified_commit_sha=fixture.base_commit,
+            verified_tree_sha=_git(fixture.src, "rev-parse", "HEAD^{tree}"),
+            canonical_diff_sha256="d" * 64,
+            patch_sha256="p" * 64,
+            edit_spec_sha256=edit_sha or _sha(options.edit_spec_path),
+            project=PROJECT,
+            branch="tizen",
+            spec_name="united-service",
+            arch=ARCH_RAW,
+            gbs_conf_sha256=_sha(fixture.conf),
+            build_log_sha256="b" * 64,
+            worktree_path=str(fixture.src),
+            command_line="gbs -c conf build -A aarch64 --include-all",
+        ),
+    )
+
+
+def _pass_builder(fixture: Fixture) -> Callable[[BuildVerifyOptions], BuildVerifyResult]:
+    def fake(options: BuildVerifyOptions) -> BuildVerifyResult:
+        _write_pass_record(fixture, options)
+        return BuildVerifyResult(
+            result="PASS",
+            actual_changed_paths=["src/main.c"],
+            verification_id="verify-pass",
+            worktree_path=str(fixture.src),
+        )
+
+    return fake
+
+
+def _assert_fixed_schema(value: dict[str, object]) -> None:
+    assert set(value) == RESULT_KEYS
+    reconciliation = value["reconciliation"]
+    assert isinstance(reconciliation, dict)
+    assert set(reconciliation) == {
+        "other_round_relinks",
+        "non_campaign_verification_ids",
+    }
+    assert isinstance(value["warnings"], list)
+
+
+def test_pass_runs_frozen_order_and_emits_fixed_schema(
+    tmp_path: Path,
+    monkeypatch: pytest.MonkeyPatch,
+) -> None:
+    fixture = _fixture(tmp_path)
+    order: list[str] = []
+    originals: dict[str, Callable[..., object]] = {
+        "create": create_round,
+        "reconcile": reconcile_pass_and_invocations,
+        "consume": consume_build_invocation,
+        "link": link_verification_with_convergence,
+    }
+
+    def track(name: str) -> Callable[..., object]:
+        original = originals[name]
+
+        def wrapper(*args: object, **kwargs: object) -> object:
+            order.append(name)
+            return original(*args, **kwargs)
+
+        return wrapper
+
+    for name, attribute in (
+        ("create", "create_round"),
+        ("reconcile", "reconcile_pass_and_invocations"),
+        ("consume", "consume_build_invocation"),
+        ("link", "link_verification_with_convergence"),
+    ):
+        monkeypatch.setattr(repair_step, attribute, track(name))
+
+    def build(options: BuildVerifyOptions) -> BuildVerifyResult:
+        order.append("build")
+        _write_pass_record(fixture, options)
+        return BuildVerifyResult(
+            result="PASS",
+            actual_changed_paths=["src/main.c"],
+            verification_id="verify-pass",
+            worktree_path=str(fixture.src),
+        )
+
+    outcome = campaign_repair_step(fixture.options, build_verify_fn=build)
+
+    assert outcome.exit_code == 0
+    assert order == ["create", "reconcile", "consume", "build", "link"]
+    value = outcome.result.to_dict()
+    _assert_fixed_schema(value)
+    assert value["result"] == "PASS"
+    assert value["verification_id"] == "verify-pass"
+    assert value["invocations_used"] == 1
+
+
+def test_new_round_with_old_hash_dies_in_create_round_before_reconcile(
+    tmp_path: Path,
+    monkeypatch: pytest.MonkeyPatch,
+) -> None:
+    fixture = _fixture(tmp_path)
+    create_round(
+        fixture.db,
+        UNIT_KEY,
+        round_index=1,
+        edit_spec_ref=str(tmp_path / "round-1.json"),
+        edit_spec_sha256=_sha(fixture.edit_spec),
+    )
+    called = {"reconcile": False}
+
+    def forbidden(*args: object, **kwargs: object) -> ReconcileResult:
+        called["reconcile"] = True
+        raise AssertionError("reconciliation must not run")
+
+    monkeypatch.setattr(repair_step, "reconcile_pass_and_invocations", forbidden)
+    options = CampaignRepairStepOptions(
+        **{
+            **fixture.options.__dict__,
+            "round_index": 2,
+        }
+    )
+    outcome = campaign_repair_step(options, build_verify_fn=_pass_builder(fixture))
+
+    assert outcome.exit_code == 4
+    _assert_fixed_schema(outcome.result.to_dict())
+    assert outcome.result.error_code == REJECTED_IDENTITY_MISMATCH
+    assert called["reconcile"] is False
+
+
+def test_previous_precheck_writes_arch_scoped_held_and_enables_rebaseline(tmp_path: Path) -> None:
+    fixture = _fixture(tmp_path)
+    fixture.evidence.unlink()
+
+    outcome = campaign_repair_step(fixture.options, build_verify_fn=_pass_builder(fixture))
+
+    assert outcome.exit_code == 4
+    _assert_fixed_schema(outcome.result.to_dict())
+    assert outcome.result.error_code == REJECTED_PREVIOUS_EVIDENCE_MISSING
+    assert is_rebaseline_authorized(fixture.db, UNIT_KEY, arch_norm=ARCH_NORM) is True
+    assert is_rebaseline_authorized(fixture.db, UNIT_KEY, arch_norm="armv7l") is False
+    conn = fixture.db.connect()
+    try:
+        row = conn.execute(
+            "SELECT status, reason, arch_norm FROM campaign_status_log "
+            "WHERE campaign_unit_key = ? ORDER BY log_id DESC LIMIT 1",
+            (UNIT_KEY,),
+        ).fetchone()
+        count = conn.execute(
+            "SELECT COUNT(*) AS count FROM campaign_gate_events "
+            "WHERE campaign_unit_key = ? AND event_type = 'CONVERGENCE'",
+            (UNIT_KEY,),
+        ).fetchone()
+    finally:
+        conn.close()
+    assert tuple(row) == (HELD_FOR_INVESTIGATION, "previous_evidence_missing", ARCH_NORM)
+    assert count["count"] == 0
+
+
+def test_removing_precheck_status_write_makes_rebaseline_unreachable(
+    tmp_path: Path,
+    monkeypatch: pytest.MonkeyPatch,
+) -> None:
+    fixture = _fixture(tmp_path)
+    fixture.evidence.unlink()
+    monkeypatch.setattr(repair_step, "append_status", lambda *args, **kwargs: None)
+
+    outcome = campaign_repair_step(fixture.options, build_verify_fn=_pass_builder(fixture))
+
+    assert outcome.exit_code == 4
+    assert is_rebaseline_authorized(fixture.db, UNIT_KEY, arch_norm=ARCH_NORM) is False
+
+
+def test_linked_recovery_runs_before_missing_previous_precheck(tmp_path: Path) -> None:
+    fixture = _fixture(tmp_path)
+    unit_hash = hashlib.sha256(UNIT_KEY.encode()).hexdigest()[:12]
+    canonical = fixture.workspace / unit_hash / ARCH_NORM / "out/round_1/edit_spec.json"
+    canonical.parent.mkdir(parents=True)
+    canonical.write_bytes(fixture.edit_spec.read_bytes())
+    create_round(
+        fixture.db,
+        UNIT_KEY,
+        round_index=1,
+        edit_spec_ref=str(canonical),
+        edit_spec_sha256=_sha(canonical),
+    )
+    receipt = consume_build_invocation(
+        fixture.db,
+        UNIT_KEY,
+        round_index=1,
+        arch_norm=ARCH_NORM,
+    )
+    build_options = BuildVerifyOptions(
+        src_clean=fixture.src,
+        base_commit=fixture.base_commit,
+        edit_spec_path=canonical,
+        gbs_conf=fixture.conf,
+        package="united-service",
+        workspace_root=canonical.parents[2],
+        baseline_evidence=fixture.evidence,
+        output_dir=canonical.parent,
+        iter_index=1,
+        wall_timeout=3600,
+        state_db=fixture.db,
+        ci_system="quickbuild",
+        build_id="1127447",
+        project=PROJECT,
+        branch="tizen",
+        arch=ARCH_RAW,
+    )
+    _write_pass_record(fixture, build_options)
+    link_verification_with_convergence(
+        fixture.db,
+        UNIT_KEY,
+        convergence_payload={
+            "round_index": 1,
+            "arch_norm": ARCH_NORM,
+            "invocation_event_id": receipt.event_id,
+            "result": "PASS",
+            "verdict": "n_a",
+            "reason": "build_passed",
+            "evidence_path": None,
+            "evidence_sha256": None,
+            "verification_id": "verify-pass",
+            "actual_changed_paths": ["src/main.c"],
+            "previous_basis": "none",
+            "at": "2026-08-05T00:00:00+00:00",
+        },
+        arch_raw=ARCH_RAW,
+        arch_norm=ARCH_NORM,
+        verification_id="verify-pass",
+        round_index=1,
+        edit_spec_sha256=_sha(canonical),
+    )
+    fixture.evidence.unlink()
+
+    outcome = campaign_repair_step(
+        fixture.options,
+        build_verify_fn=lambda options: pytest.fail("build must not run"),
+    )
+
+    assert outcome.exit_code == 0
+    _assert_fixed_schema(outcome.result.to_dict())
+    assert outcome.result.result == "PASS"
+    assert outcome.result.convergence_reason == "linked_already"
+    assert outcome.result.invocations_used == 1
+
+
+@pytest.mark.parametrize("repair_allowed", ["auto", "needs_confirmation"])
+def test_fail_stalled_records_convergence_and_terminal_status(
+    tmp_path: Path,
+    repair_allowed: str,
+) -> None:
+    fixture = _fixture(tmp_path)
+    current = tmp_path / "current.json"
+    current.write_text(json.dumps(BASE_PACKET, sort_keys=True) + "\n", encoding="utf-8")
+
+    outcome = campaign_repair_step(
+        fixture.options,
+        build_verify_fn=lambda options: BuildVerifyResult(
+            result="FAIL",
+            actual_changed_paths=["src/main.c"],
+            failure_stage="gbs_build_failed",
+            failure_class="source_repairable",
+            repair_allowed=repair_allowed,
+            evidence=str(current),
+        ),
+    )
+
+    assert outcome.exit_code == 0
+    _assert_fixed_schema(outcome.result.to_dict())
+    assert outcome.result.verdict == "stalled"
+    assert outcome.result.repair_allowed == repair_allowed
+    assert outcome.result.previous_basis == "reproduce"
+    conn = fixture.db.connect()
+    try:
+        status = conn.execute(
+            "SELECT status FROM campaign_status_log WHERE campaign_unit_key = ? "
+            "ORDER BY log_id DESC LIMIT 1",
+            (UNIT_KEY,),
+        ).fetchone()
+    finally:
+        conn.close()
+    assert status["status"] == "STALLED"
+
+
+def test_denied_failure_short_circuits_convergence(tmp_path: Path) -> None:
+    fixture = _fixture(tmp_path)
+    current = tmp_path / "current.json"
+    current.write_text(json.dumps(BASE_PACKET) + "\n", encoding="utf-8")
+
+    def forbidden(*args: object, **kwargs: object) -> ConvergenceResult:
+        raise AssertionError("denied failure must not call convergence")
+
+    outcome = campaign_repair_step(
+        fixture.options,
+        build_verify_fn=lambda options: BuildVerifyResult(
+            result="FAIL",
+            failure_stage="gbs_build_failed",
+            failure_class="toolchain",
+            repair_allowed="denied",
+            evidence=str(current),
+            error="toolchain flag denied",
+        ),
+        convergence_fn=forbidden,
+    )
+
+    assert outcome.exit_code == 0
+    _assert_fixed_schema(outcome.result.to_dict())
+    assert outcome.result.verdict == "denied"
+    assert outcome.result.repair_allowed == "denied"
+
+
+def test_post_build_previous_toctou_failure_records_na_and_held(tmp_path: Path) -> None:
+    fixture = _fixture(tmp_path)
+    current = tmp_path / "current.json"
+    current.write_text(json.dumps(BASE_PACKET) + "\n", encoding="utf-8")
+
+    def build(options: BuildVerifyOptions) -> BuildVerifyResult:
+        fixture.evidence.unlink()
+        return BuildVerifyResult(
+            result="FAIL",
+            actual_changed_paths=["src/main.c"],
+            failure_stage="gbs_build_failed",
+            failure_class="source_repairable",
+            repair_allowed="auto",
+            evidence=str(current),
+        )
+
+    outcome = campaign_repair_step(fixture.options, build_verify_fn=build)
+
+    assert outcome.exit_code == 4
+    _assert_fixed_schema(outcome.result.to_dict())
+    assert outcome.result.error_code == REJECTED_PREVIOUS_EVIDENCE_MISSING
+    conn = fixture.db.connect()
+    try:
+        event = conn.execute(
+            "SELECT payload_json FROM campaign_gate_events "
+            "WHERE campaign_unit_key = ? AND event_type = 'CONVERGENCE' "
+            "ORDER BY event_id DESC LIMIT 1",
+            (UNIT_KEY,),
+        ).fetchone()
+    finally:
+        conn.close()
+    payload = json.loads(event["payload_json"])
+    assert payload["result"] == "n_a"
+    assert payload["verdict"] == "n_a"
+    assert payload["reason"] == "previous_evidence_missing"
+    assert is_rebaseline_authorized(fixture.db, UNIT_KEY, arch_norm=ARCH_NORM) is True
+
+
+def test_lock_busy_returns_exit_five_without_creating_round(tmp_path: Path) -> None:
+    fixture = _fixture(tmp_path)
+    unit_hash = hashlib.sha256(UNIT_KEY.encode()).hexdigest()[:12]
+    lock_root = fixture.workspace / unit_hash / ARCH_NORM
+    lock_root.mkdir(parents=True)
+    with (lock_root / ".repair_step.lock").open("a+", encoding="utf-8") as stream:
+        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
+        outcome = campaign_repair_step(fixture.options, build_verify_fn=_pass_builder(fixture))
+
+    assert outcome.exit_code == 5
+    _assert_fixed_schema(outcome.result.to_dict())
+    assert outcome.result.error_code == CAMPAIGN_STATE_BUSY
+    conn = fixture.db.connect()
+    try:
+        count = conn.execute("SELECT COUNT(*) AS count FROM campaign_rounds").fetchone()
+    finally:
+        conn.close()
+    assert count["count"] == 0
+
+
+@pytest.mark.parametrize("damage", ["head", "origin", "marker"])
+def test_source_identity_joint_check_rejects_each_mismatch(
+    tmp_path: Path,
+    damage: str,
+) -> None:
+    fixture = _fixture(tmp_path)
+    if damage == "head":
+        (fixture.src / "src/main.c").write_text("int changed;\n", encoding="utf-8")
+        _git(fixture.src, "add", "src/main.c")
+        _git(fixture.src, "commit", "-m", "wrong head")
+    elif damage == "origin":
+        _git(fixture.src, "remote", "set-url", "origin", "ssh://review.tizen.org/wrong")
+    else:
+        (fixture.src / ".campaign_clone").write_text("{}\n", encoding="utf-8")
+    called = {"build": False}
+
+    def forbidden(options: BuildVerifyOptions) -> BuildVerifyResult:
+        called["build"] = True
+        raise AssertionError("identity mismatch must stop before build")
+
+    outcome = campaign_repair_step(fixture.options, build_verify_fn=forbidden)
+
+    assert outcome.exit_code == 4
+    assert outcome.result.error_code == REJECTED_IDENTITY_MISMATCH
+    assert called["build"] is False
+
+
+def test_conf_drift_is_rejected_after_invocation_without_build(tmp_path: Path) -> None:
+    fixture = _fixture(tmp_path)
+    fixture.conf.write_text("[general]\nchanged=true\n", encoding="utf-8")
+    called = {"build": False}
+
+    def forbidden(options: BuildVerifyOptions) -> BuildVerifyResult:
+        called["build"] = True
+        raise AssertionError("conf drift must stop before build")
+
+    outcome = campaign_repair_step(fixture.options, build_verify_fn=forbidden)
+
+    assert outcome.exit_code == 4
+    assert outcome.result.error_code == "REJECTED_CONF_DRIFT"
+    assert outcome.result.invocations_used == 1
+    assert called["build"] is False
+
+
+def test_reconciliation_arrays_use_objects_and_deterministic_sorting() -> None:
+    reconciliation, warnings = repair_step._serialize_reconciliation(
+        ReconcileResult(
+            branch="proceed",
+            current_verification_id=None,
+            current_relinked_invocation_event_id=None,
+            other_round_relinks=((2, "V2", 8), (1, "V9", 9), (1, "V1", 7)),
+            backfilled_invocation_event_ids=(),
+            orphan_pass_verification_ids=(),
+            held_rounds=(),
+            non_campaign_verification_ids=("V9", "V1", "V9"),
+        )
+    )
+
+    assert reconciliation["other_round_relinks"] == [
+        {"round_index": 1, "verification_id": "V1", "invocation_event_id": 7},
+        {"round_index": 1, "verification_id": "V9", "invocation_event_id": 9},
+        {"round_index": 2, "verification_id": "V2", "invocation_event_id": 8},
+    ]
+    assert reconciliation["non_campaign_verification_ids"] == ["V1", "V9"]
+    assert warnings == [
+        {"code": "non_campaign_verification", "verification_id": "V1"},
+        {"code": "non_campaign_verification", "verification_id": "V9"},
+    ]
+
+
+def test_non_campaign_record_is_reported_as_sorted_structured_warning(tmp_path: Path) -> None:
+    fixture = _fixture(tmp_path)
+    dummy = BuildVerifyOptions(
+        src_clean=fixture.src,
+        base_commit=fixture.base_commit,
+        edit_spec_path=fixture.edit_spec,
+        gbs_conf=fixture.conf,
+        package="united-service",
+        workspace_root=fixture.workspace,
+        baseline_evidence=fixture.evidence,
+        output_dir=tmp_path / "dummy",
+        iter_index=1,
+        wall_timeout=3600,
+        state_db=fixture.db,
+        ci_system="quickbuild",
+        build_id="1127447",
+        project=PROJECT,
+        branch="tizen",
+        arch=ARCH_RAW,
+    )
+    _write_pass_record(
+        fixture,
+        dummy,
+        verification_id="verify-external",
+        edit_sha="f" * 64,
+    )
+
+    outcome = campaign_repair_step(fixture.options, build_verify_fn=_pass_builder(fixture))
+
+    assert outcome.exit_code == 0
+    assert outcome.result.reconciliation["non_campaign_verification_ids"] == [
+        "verify-external"
+    ]
+    assert outcome.result.warnings == [
+        {
+            "code": "non_campaign_verification",
+            "verification_id": "verify-external",
+        }
+    ]
+
+
+def test_previous_resolver_handles_pass_and_na_history(tmp_path: Path) -> None:
+    fixture = _fixture(tmp_path)
+    first = consume_build_invocation(
+        fixture.db,
+        UNIT_KEY,
+        round_index=_ensure_round(fixture),
+        arch_norm=ARCH_NORM,
+    )
+    current = tmp_path / "first-fail.json"
+    current.write_text(json.dumps(BASE_PACKET) + "\n", encoding="utf-8")
+    append_event(
+        fixture.db,
+        UNIT_KEY,
+        "CONVERGENCE",
+        _fail_convergence(first.event_id, current),
+    )
+    second = consume_build_invocation(
+        fixture.db,
+        UNIT_KEY,
+        round_index=1,
+        arch_norm=ARCH_NORM,
+    )
+    append_event(
+        fixture.db,
+        UNIT_KEY,
+        "CONVERGENCE",
+        _na_convergence(second.event_id, "orphan_invocation"),
+    )
+
+    resolved = resolve(fixture.db, UNIT_KEY, arch_norm=ARCH_NORM)
+
+    assert isinstance(resolved, ResolvedEvidence)
+    assert resolved.basis == "prev_build"
+    assert resolved.evidence_path == str(current)
+
+    third = consume_build_invocation(
+        fixture.db,
+        UNIT_KEY,
+        round_index=1,
+        arch_norm=ARCH_NORM,
+    )
+    append_event(
+        fixture.db,
+        UNIT_KEY,
+        "CONVERGENCE",
+        {
+            **_na_convergence(third.event_id, "orphan_invocation"),
+            "result": "PASS",
+            "reason": "build_passed",
+            "verification_id": "verify-synthetic",
+        },
+    )
+    synthetic = resolve(fixture.db, UNIT_KEY, arch_norm=ARCH_NORM)
+    assert isinstance(synthetic, ResolvedEvidence)
+    assert synthetic.basis == "synthetic_zero"
+    assert synthetic.evidence["primary_error"] is None
+
+
+def test_previous_resolver_rebaselined_falls_back_to_latest_reproduce(tmp_path: Path) -> None:
+    fixture = _fixture(tmp_path)
+    _ensure_round(fixture)
+    append_event(
+        fixture.db,
+        UNIT_KEY,
+        "CONVERGENCE",
+        {
+            "round_index": 1,
+            "arch_norm": ARCH_NORM,
+            "invocation_event_id": None,
+            "result": "n_a",
+            "verdict": "n_a",
+            "reason": "rebaselined",
+            "evidence_path": None,
+            "evidence_sha256": None,
+            "verification_id": None,
+            "actual_changed_paths": [],
+            "previous_basis": "none",
+            "at": "2026-08-05T00:00:00+00:00",
+        },
+    )
+
+    resolved = resolve(fixture.db, UNIT_KEY, arch_norm=ARCH_NORM)
+
+    assert isinstance(resolved, ResolvedEvidence)
+    assert resolved.basis == "reproduce"
+    assert resolved.evidence_path == str(fixture.evidence)
+
+
+def test_previous_resolver_fails_closed_for_missing_substantive_file(tmp_path: Path) -> None:
+    fixture = _fixture(tmp_path)
+    invocation = consume_build_invocation(
+        fixture.db,
+        UNIT_KEY,
+        round_index=_ensure_round(fixture),
+        arch_norm=ARCH_NORM,
+    )
+    missing = tmp_path / "missing-current.json"
+    append_event(
+        fixture.db,
+        UNIT_KEY,
+        "CONVERGENCE",
+        {
+            **_fail_convergence(invocation.event_id, fixture.evidence),
+            "evidence_path": str(missing),
+            "evidence_sha256": "f" * 64,
+        },
+    )
+
+    resolved = resolve(fixture.db, UNIT_KEY, arch_norm=ARCH_NORM)
+
+    assert isinstance(resolved, MissingEvidence)
+
+
+def test_campaign_repair_step_help_uses_dedicated_parser(
+    capsys: pytest.CaptureFixture[str],
+) -> None:
+    with pytest.raises(SystemExit) as excinfo:
+        cli.main(["campaign-repair-step", "--help"])
+
+    assert excinfo.value.code == 0
+    output = capsys.readouterr().out
+    assert "--campaign-unit-key" in output
+    assert "--round-index" in output
+    assert "--edit-spec" in output
+    assert "--src-clean" not in output
+
+
+def test_python_m_campaign_repair_step_emits_one_json_document(tmp_path: Path) -> None:
+    fixture = _fixture(tmp_path)
+    # Prepare an already-linked round so the subprocess smoke never invokes gbs.
+    unit_hash = hashlib.sha256(UNIT_KEY.encode()).hexdigest()[:12]
+    canonical = fixture.workspace / unit_hash / ARCH_NORM / "out/round_1/edit_spec.json"
+    canonical.parent.mkdir(parents=True)
+    canonical.write_bytes(fixture.edit_spec.read_bytes())
+    create_round(
+        fixture.db,
+        UNIT_KEY,
+        round_index=1,
+        edit_spec_ref=str(canonical),
+        edit_spec_sha256=_sha(canonical),
+    )
+    receipt = consume_build_invocation(
+        fixture.db,
+        UNIT_KEY,
+        round_index=1,
+        arch_norm=ARCH_NORM,
+    )
+    dummy = BuildVerifyOptions(
+        src_clean=fixture.src,
+        base_commit=fixture.base_commit,
+        edit_spec_path=canonical,
+        gbs_conf=fixture.conf,
+        package="united-service",
+        workspace_root=canonical.parents[2],
+        baseline_evidence=fixture.evidence,
+        output_dir=canonical.parent,
+        iter_index=1,
+        wall_timeout=3600,
+        state_db=fixture.db,
+        ci_system="quickbuild",
+        build_id="1127447",
+        project=PROJECT,
+        branch="tizen",
+        arch=ARCH_RAW,
+    )
+    _write_pass_record(fixture, dummy)
+    link_verification_with_convergence(
+        fixture.db,
+        UNIT_KEY,
+        convergence_payload={
+            "round_index": 1,
+            "arch_norm": ARCH_NORM,
+            "invocation_event_id": receipt.event_id,
+            "result": "PASS",
+            "verdict": "n_a",
+            "reason": "build_passed",
+            "evidence_path": None,
+            "evidence_sha256": None,
+            "verification_id": "verify-pass",
+            "actual_changed_paths": ["src/main.c"],
+            "previous_basis": "none",
+            "at": "2026-08-05T00:00:00+00:00",
+        },
+        arch_raw=ARCH_RAW,
+        arch_norm=ARCH_NORM,
+        verification_id="verify-pass",
+        round_index=1,
+        edit_spec_sha256=_sha(canonical),
+    )
+    env = os.environ.copy()
+    scripts = str(Path("tizen-ci-triage/scripts").resolve())
+    env["PYTHONPATH"] = (
+        scripts
+        if not env.get("PYTHONPATH")
+        else scripts + os.pathsep + env["PYTHONPATH"]
+    )
+    completed = subprocess.run(
+        [
+            sys.executable,
+            "-m",
+            "ci_triage",
+            "campaign-repair-step",
+            "--campaign-unit-key",
+            UNIT_KEY,
+            "--state-db",
+            str(fixture.db.path),
+            "--config",
+            str(fixture.options.config_path),
+            "--round-index",
+            "1",
+            "--edit-spec",
+            str(fixture.edit_spec),
+            "--arch",
+            ARCH_RAW,
+        ],
+        check=False,
+        capture_output=True,
+        text=True,
+        env=env,
+    )
+
+    assert completed.returncode == 0
+    lines = completed.stdout.splitlines()
+    assert len(lines) == 1
+    value = json.loads(lines[0])
+    _assert_fixed_schema(value)
+    assert value["result"] == "PASS"
+    assert completed.stderr == ""
+
+
+def _ensure_round(fixture: Fixture) -> int:
+    create_round(
+        fixture.db,
+        UNIT_KEY,
+        round_index=1,
+        edit_spec_ref=str(fixture.edit_spec),
+        edit_spec_sha256=_sha(fixture.edit_spec),
+    )
+    return 1
+
+
+def _fail_convergence(invocation_event_id: int, evidence: Path) -> dict[str, object]:
+    return {
+        "round_index": 1,
+        "arch_norm": ARCH_NORM,
+        "invocation_event_id": invocation_event_id,
+        "result": "FAIL",
+        "verdict": "advance",
+        "reason": "fingerprint_changed",
+        "evidence_path": str(evidence),
+        "evidence_sha256": _sha(evidence),
+        "verification_id": None,
+        "actual_changed_paths": ["src/main.c"],
+        "previous_basis": "reproduce",
+        "at": "2026-08-05T00:00:00+00:00",
+    }
+
+
+def _na_convergence(invocation_event_id: int, reason: str) -> dict[str, object]:
+    return {
+        "round_index": 1,
+        "arch_norm": ARCH_NORM,
+        "invocation_event_id": invocation_event_id,
+        "result": "n_a",
+        "verdict": "n_a",
+        "reason": reason,
+        "evidence_path": None,
+        "evidence_sha256": None,
+        "verification_id": None,
+        "actual_changed_paths": [],
+        "previous_basis": "none",
+        "at": "2026-08-05T00:00:00+00:00",
+    }
diff --git a/tests/unit/test_campaign_state.py b/tests/unit/test_campaign_state.py
new file mode 100644
index 0000000..0cc7df8
--- /dev/null
+++ b/tests/unit/test_campaign_state.py
@@ -0,0 +1,1032 @@
+from __future__ import annotations
+
+import hashlib
+import json
+import sqlite3
+import threading
+from pathlib import Path
+
+import pytest
+from ci_triage.campaign_state import (
+    ARCH_NORMS,
+    CAMPAIGN_SCHEMA_VERSION,
+    HELD_FOR_INVESTIGATION,
+    REJECTED_ARCH_NOT_ALLOWED,
+    BudgetExhausted,
+    CampaignStateBusy,
+    PayloadSchemaError,
+    RoundsExhausted,
+    StateInconsistent,
+    UnknownEventType,
+    adopt_secondary_target_with_convergence,
+    append_event,
+    append_qb_event,
+    append_status,
+    consume_build_invocation,
+    create_arch_rejected_unit,
+    create_qb_request,
+    create_round,
+    create_unit,
+    ensure_schema,
+    find_unit_by_qb_build_id,
+    find_unit_by_request_id,
+    find_unlinked_pass,
+    get_round,
+    get_unit,
+    invocations_used,
+    latest_event,
+    latest_qb_result,
+    latest_reproduce,
+    latest_round,
+    latest_status,
+    link_verification_with_convergence,
+)
+from ci_triage.state import StateDatabase, VerificationRecord, write_pass_record
+
+UNIT_KEY = "campaign-unit-1"
+OTHER_UNIT_KEY = "campaign-unit-2"
+EDIT_SHA = "e" * 64
+
+
+def _db(tmp_path: Path, name: str = "state.sqlite3") -> StateDatabase:
+    return StateDatabase(tmp_path / name)
+
+
+def _identity(*, build_id: str = "1127447") -> dict[str, str]:
+    return {
+        "ci_system": "quickbuild",
+        "source_build_id": build_id,
+        "project": "platform/core/appfw/united-service",
+        "branch": "tizen",
+        "spec_name": "united-service",
+        "base_commit": "a" * 40,
+    }
+
+
+def _create_unit(
+    db: StateDatabase,
+    *,
+    unit_key: str = UNIT_KEY,
+    max_rounds: int = 3,
+    max_build_invocations: int = 9,
+    build_id: str = "1127447",
+) -> None:
+    create_unit(
+        db,
+        campaign_unit_key=unit_key,
+        submission_identity_key=f"submission-{unit_key}",
+        primary_arch="standard-aarch64",
+        failed_arches=("standard-x86_64", "standard-aarch64", "standard-armv7l"),
+        toolchain_profile="tizen_unified_standard",
+        ci_evidence_ref="/tmp/evidence.json",
+        ci_evidence_sha256="c" * 64,
+        max_rounds=max_rounds,
+        max_build_invocations=max_build_invocations,
+        **_identity(build_id=build_id),
+    )
+
+
+def _create_round(
+    db: StateDatabase,
+    *,
+    unit_key: str = UNIT_KEY,
+    round_index: int = 1,
+    edit_sha: str = EDIT_SHA,
+    suffix: str = "one",
+) -> None:
+    create_round(
+        db,
+        unit_key,
+        round_index=round_index,
+        edit_spec_ref=f"relative/{suffix}.json",
+        edit_spec_sha256=edit_sha,
+    )
+
+
+def _fail_payload(
+    invocation_event_id: int,
+    *,
+    round_index: int = 1,
+    arch_norm: str = "aarch64",
+) -> dict[str, object]:
+    return {
+        "round_index": round_index,
+        "arch_norm": arch_norm,
+        "invocation_event_id": invocation_event_id,
+        "result": "FAIL",
+        "verdict": "advance",
+        "reason": "fingerprint_changed",
+        "evidence_path": "/tmp/current.json",
+        "evidence_sha256": "d" * 64,
+        "verification_id": None,
+        "actual_changed_paths": ["src/main.c"],
+        "previous_basis": "reproduce",
+        "at": "2026-08-05T00:00:00+00:00",
+    }
+
+
+def _pass_payload(invocation_event_id: int, verification_id: str) -> dict[str, object]:
+    return {
+        "round_index": 1,
+        "arch_norm": "aarch64",
+        "invocation_event_id": invocation_event_id,
+        "result": "PASS",
+        "verdict": "n_a",
+        "reason": "build_passed",
+        "evidence_path": None,
+        "evidence_sha256": None,
+        "verification_id": verification_id,
+        "actual_changed_paths": ["src/main.c"],
+        "previous_basis": "none",
+        "at": "2026-08-05T00:00:00+00:00",
+    }
+
+
+def _orphan_payload(invocation_event_id: int) -> dict[str, object]:
+    payload = _fail_payload(invocation_event_id)
+    payload.update(
+        {
+            "result": "n_a",
+            "verdict": "n_a",
+            "reason": "orphan_invocation",
+            "evidence_path": None,
+            "evidence_sha256": None,
+            "actual_changed_paths": [],
+            "previous_basis": "none",
+        }
+    )
+    return payload
+
+
+def _record(
+    verification_id: str,
+    *,
+    arch: str = "standard-aarch64",
+    edit_sha: str = EDIT_SHA,
+    failure_key: str = "failure-key",
+) -> VerificationRecord:
+    return VerificationRecord(
+        verification_id=verification_id,
+        result="PASS",
+        timestamp="2026-08-05T00:00:00+00:00",
+        failure_key=failure_key,
+        base_commit="a" * 40,
+        verified_commit_sha="b" * 40,
+        verified_tree_sha="c" * 40,
+        canonical_diff_sha256="d" * 64,
+        patch_sha256="f" * 64,
+        edit_spec_sha256=edit_sha,
+        project="platform/core/appfw/united-service",
+        branch="tizen",
+        spec_name="united-service",
+        arch=arch,
+        gbs_conf_sha256="1" * 64,
+        build_log_sha256="2" * 64,
+        worktree_path="/tmp/worktree",
+        command_line="gbs build",
+    )
+
+
+def test_ensure_schema_creates_exact_campaign_tables_and_required_guards(
+    tmp_path: Path,
+) -> None:
+    db = _db(tmp_path)
+
+    ensure_schema(db)
+
+    conn = db.connect()
+    try:
+        tables = {
+            row[0]
+            for row in conn.execute(
+                "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'campaign_%'"
+            )
+        }
+        index_sql = conn.execute(
+            "SELECT sql FROM sqlite_master WHERE type = 'index' "
+            "AND name = 'ux_convergence_per_invocation'"
+        ).fetchone()
+        unit_sql = conn.execute(
+            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'campaign_units'"
+        ).fetchone()
+        status_columns = {
+            row[1] for row in conn.execute("PRAGMA table_info(campaign_status_log)")
+        }
+    finally:
+        conn.close()
+
+    assert tables == {
+        "campaign_units",
+        "campaign_gate_events",
+        "campaign_status_log",
+        "campaign_rounds",
+        "campaign_verifications",
+        "campaign_qb_requests",
+        "campaign_qb_events",
+    }
+    assert index_sql is not None
+    normalized_index = " ".join(str(index_sql[0]).split())
+    assert "WHERE event_type = 'CONVERGENCE' AND invocation_event_id IS NOT NULL" in (
+        normalized_index
+    )
+    assert unit_sql is not None
+    assert "primary_arch IS NULL AND ci_evidence_ref IS NULL" in str(unit_sql[0])
+    assert "primary_arch IS NOT NULL AND ci_evidence_ref IS NOT NULL" in str(unit_sql[0])
+    assert "arch_norm" in status_columns
+
+
+def test_create_unit_round_trip_is_idempotent_and_canonicalizes_arch_order(
+    tmp_path: Path,
+) -> None:
+    db = _db(tmp_path)
+
+    _create_unit(db)
+    _create_unit(db)
+
+    unit = get_unit(db, UNIT_KEY)
+    assert unit is not None
+    assert unit.failed_arches == (
+        "standard-aarch64",
+        "standard-armv7l",
+        "standard-x86_64",
+    )
+    assert unit.schema_version == CAMPAIGN_SCHEMA_VERSION
+    conn = db.connect()
+    try:
+        assert conn.execute("SELECT COUNT(*) FROM campaign_units").fetchone()[0] == 1
+    finally:
+        conn.close()
+
+
+def test_create_unit_rejects_conflicting_retry(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+
+    with pytest.raises(StateInconsistent, match="differs"):
+        create_unit(
+            db,
+            campaign_unit_key=UNIT_KEY,
+            submission_identity_key="changed",
+            primary_arch="standard-aarch64",
+            failed_arches=("standard-aarch64",),
+            toolchain_profile="tizen_unified_standard",
+            ci_evidence_ref="/tmp/evidence.json",
+            ci_evidence_sha256="c" * 64,
+            max_rounds=3,
+            max_build_invocations=9,
+            **_identity(),
+        )
+
+
+def test_create_arch_rejected_unit_atomically_writes_null_tuple_and_status(
+    tmp_path: Path,
+) -> None:
+    db = _db(tmp_path)
+
+    create_arch_rejected_unit(
+        db,
+        campaign_unit_key=UNIT_KEY,
+        submission_identity_key="submission",
+        failed_arches=("emulator-x86_64",),
+        reason="unverified profile",
+        toolchain_profile="tizen_unified_emulator",
+        max_rounds=3,
+        max_build_invocations=9,
+        **_identity(),
+    )
+
+    unit = get_unit(db, UNIT_KEY)
+    assert unit is not None
+    assert (unit.primary_arch, unit.ci_evidence_ref, unit.ci_evidence_sha256) == (
+        None,
+        None,
+        None,
+    )
+    assert latest_status(db, UNIT_KEY) == REJECTED_ARCH_NOT_ALLOWED
+
+
+def test_campaign_unit_half_empty_evidence_tuple_is_blocked_by_check(
+    tmp_path: Path,
+) -> None:
+    db = _db(tmp_path)
+    ensure_schema(db)
+    conn = db.connect()
+    try:
+        with pytest.raises(sqlite3.IntegrityError):
+            _insert_raw_unit(conn, primary_arch="standard-aarch64", evidence_ref=None)
+    finally:
+        conn.close()
+
+
+def test_campaign_unit_check_reverse_validation_fails_when_check_is_removed(
+    tmp_path: Path,
+) -> None:
+    db = _db(tmp_path)
+    ensure_schema(db)
+    source = db.connect()
+    try:
+        row = source.execute(
+            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'campaign_units'"
+        ).fetchone()
+    finally:
+        source.close()
+    assert row is not None
+    table_sql = str(row[0])
+    marker = ",\n  CHECK (\n"
+    assert marker in table_sql
+    schema_without_check = table_sql[: table_sql.index(marker)] + "\n)"
+    conn = sqlite3.connect(tmp_path / "without-check.sqlite3")
+    try:
+        conn.execute(schema_without_check)
+        _insert_raw_unit(conn, primary_arch="standard-aarch64", evidence_ref=None)
+        assert conn.execute("SELECT COUNT(*) FROM campaign_units").fetchone()[0] == 1
+    finally:
+        conn.close()
+
+
+def test_round_crud_enforces_identity_sequence_and_budget(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db, max_rounds=2)
+
+    _create_round(db)
+    _create_round(db)
+    first = get_round(db, UNIT_KEY, 1)
+    assert first is not None
+    assert first.edit_spec_ref == str(Path("relative/one.json").resolve())
+    assert latest_round(db, UNIT_KEY) == first
+
+    with pytest.raises(StateInconsistent):
+        _create_round(db, round_index=1, edit_sha="f" * 64, suffix="other")
+    with pytest.raises(StateInconsistent):
+        _create_round(db, round_index=2, edit_sha=EDIT_SHA, suffix="two")
+    with pytest.raises(StateInconsistent, match="must be 2"):
+        _create_round(db, round_index=3, edit_sha="3" * 64, suffix="three")
+
+    _create_round(db, round_index=2, edit_sha="2" * 64, suffix="two")
+    with pytest.raises(RoundsExhausted):
+        _create_round(db, round_index=3, edit_sha="3" * 64, suffix="three")
+
+
+def test_round_exact_retry_precedes_exhaustion_check(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db, max_rounds=1)
+    _create_round(db)
+
+    _create_round(db)
+
+    conn = db.connect()
+    try:
+        assert conn.execute("SELECT COUNT(*) FROM campaign_rounds").fetchone()[0] == 1
+    finally:
+        conn.close()
+
+
+def test_consume_returns_inserted_receipt_and_enforces_db_budget(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db, max_build_invocations=2)
+    _create_round(db)
+
+    first = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    second = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="armv7l")
+
+    assert first.invocations_used == 1
+    assert first.invocations_remaining == 1
+    assert second.event_id > first.event_id
+    assert second.invocations_used == 2
+    assert second.invocations_remaining == 0
+    assert invocations_used(db, UNIT_KEY) == 2
+    with pytest.raises(BudgetExhausted):
+        consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="x86_64")
+    assert invocations_used(db, UNIT_KEY) == 2
+
+
+def test_two_connections_cannot_overspend_one_invocation_budget(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db, max_build_invocations=1)
+    _create_round(db)
+    barrier = threading.Barrier(2)
+    outcomes: list[str] = []
+
+    def consume() -> None:
+        barrier.wait()
+        try:
+            consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+        except BudgetExhausted:
+            outcomes.append("exhausted")
+        else:
+            outcomes.append("consumed")
+
+    threads = [threading.Thread(target=consume), threading.Thread(target=consume)]
+    for thread in threads:
+        thread.start()
+    for thread in threads:
+        thread.join()
+
+    assert sorted(outcomes) == ["consumed", "exhausted"]
+    assert invocations_used(db, UNIT_KEY) == 1
+
+
+def test_consume_maps_immediate_lock_timeout_to_busy_without_writing(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+    _create_round(db)
+    holder = db.connect()
+    try:
+        holder.execute("BEGIN IMMEDIATE")
+        with pytest.raises(CampaignStateBusy, match="CAMPAIGN_STATE_BUSY"):
+            consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    finally:
+        holder.rollback()
+        holder.close()
+    assert invocations_used(db, UNIT_KEY) == 0
+
+
+@pytest.mark.parametrize("second_kind", ["pass", "substantive"])
+def test_convergence_index_rejects_second_outcome_for_same_invocation(
+    tmp_path: Path,
+    second_kind: str,
+) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+    _create_round(db)
+    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    append_event(db, UNIT_KEY, "CONVERGENCE", _pass_payload(receipt.event_id, "V1"))
+    second = (
+        _pass_payload(receipt.event_id, "V2")
+        if second_kind == "pass"
+        else _fail_payload(receipt.event_id)
+    )
+
+    with pytest.raises(sqlite3.IntegrityError):
+        append_event(db, UNIT_KEY, "CONVERGENCE", second)
+
+
+def test_convergence_index_allows_orphan_then_new_invocation_outcome(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+    _create_round(db)
+    old = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    append_event(db, UNIT_KEY, "CONVERGENCE", _orphan_payload(old.event_id))
+    new = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+
+    append_event(db, UNIT_KEY, "CONVERGENCE", _fail_payload(new.event_id))
+
+    conn = db.connect()
+    try:
+        assert (
+            conn.execute(
+                "SELECT COUNT(*) FROM campaign_gate_events WHERE event_type = 'CONVERGENCE'"
+            ).fetchone()[0]
+            == 2
+        )
+    finally:
+        conn.close()
+
+
+def test_convergence_index_reverse_validation_allows_duplicate_when_dropped(
+    tmp_path: Path,
+) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+    conn = db.connect()
+    try:
+        conn.execute("DROP INDEX ux_convergence_per_invocation")
+        _insert_raw_convergence(conn, invocation_event_id=77, verification_id="V1")
+        _insert_raw_convergence(conn, invocation_event_id=77, verification_id="V2")
+        assert conn.execute(
+            "SELECT COUNT(*) FROM campaign_gate_events WHERE invocation_event_id = 77"
+        ).fetchone()[0] == 2
+    finally:
+        conn.close()
+
+
+def test_convergence_binding_accepts_receipt_and_rejects_four_mismatches(
+    tmp_path: Path,
+) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+    _create_unit(db, unit_key=OTHER_UNIT_KEY, build_id="1127448")
+    _create_round(db)
+    _create_round(db, unit_key=OTHER_UNIT_KEY)
+    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    other_receipt = consume_build_invocation(
+        db, OTHER_UNIT_KEY, round_index=1, arch_norm="aarch64"
+    )
+    policy_id = append_event(
+        db,
+        UNIT_KEY,
+        "POLICY",
+        {
+            "round_index": 1,
+            "verdict": "allowed",
+            "hits": [],
+            "fix_strategy_initial": "code",
+            "fix_strategy_final": "code",
+            "edit_source_kind": "generated",
+        },
+    )
+
+    append_event(db, UNIT_KEY, "CONVERGENCE", _fail_payload(receipt.event_id))
+
+    invalid_payloads = [
+        _fail_payload(999999),
+        _fail_payload(policy_id),
+        _fail_payload(other_receipt.event_id),
+        _fail_payload(receipt.event_id, round_index=2),
+        _fail_payload(receipt.event_id, arch_norm="armv7l"),
+    ]
+    for payload in invalid_payloads:
+        with pytest.raises(StateInconsistent):
+            append_event(db, UNIT_KEY, "CONVERGENCE", payload)
+
+
+def test_convergence_conditional_enums_are_fail_closed(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+    _create_round(db)
+    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+
+    missing_invocation = _orphan_payload(receipt.event_id)
+    missing_invocation["invocation_event_id"] = None
+    wrong_orphan_result = _orphan_payload(receipt.event_id)
+    wrong_orphan_result["result"] = "FAIL"
+    wrong_build_result = _fail_payload(receipt.event_id)
+    wrong_build_result["result"] = "n_a"
+    for payload in (missing_invocation, wrong_orphan_result, wrong_build_result):
+        with pytest.raises(PayloadSchemaError):
+            append_event(db, UNIT_KEY, "CONVERGENCE", payload)
+
+
+def test_append_status_requires_arch_for_arch_scoped_held_reason(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+
+    with pytest.raises(PayloadSchemaError, match="requires arch_norm"):
+        append_status(
+            db,
+            UNIT_KEY,
+            HELD_FOR_INVESTIGATION,
+            reason="previous_evidence_missing",
+        )
+
+    append_status(
+        db,
+        UNIT_KEY,
+        HELD_FOR_INVESTIGATION,
+        reason="previous_evidence_missing",
+        arch_norm="aarch64",
+    )
+    assert latest_status(db, UNIT_KEY) == HELD_FOR_INVESTIGATION
+
+
+def test_reproduce_latest_is_filtered_by_arch(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+    for arch, outcome in (("aarch64", "matched"), ("armv7l", "baseline_pass")):
+        append_event(
+            db,
+            UNIT_KEY,
+            "REPRODUCE",
+            {
+                "arch_norm": arch,
+                "outcome": outcome,
+                "evidence_local": f"/tmp/{arch}.json",
+                "evidence_sha256": "a" * 64,
+                "synthetic_zero_error": outcome == "baseline_pass",
+                "gbs_conf_sha256": "b" * 64,
+                "ci_evidence_sha256_used": "c" * 64,
+                "build_log": f"/tmp/{arch}.log",
+                "basis": {},
+            },
+        )
+
+    event = latest_reproduce(db, UNIT_KEY, arch_norm="armv7l")
+    assert event is not None
+    assert event["payload"]["outcome"] == "baseline_pass"  # type: ignore[index]
+
+
+def test_secondary_adoption_and_convergence_commit_atomically(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+    _create_round(db)
+    baseline = tmp_path / "baseline.json"
+    current = tmp_path / "current.json"
+    evidence = _evidence("same warning")
+    _write_json(baseline, evidence)
+    _write_json(current, evidence)
+    reproduce_id = append_event(
+        db,
+        UNIT_KEY,
+        "REPRODUCE",
+        _reproduce_payload("armv7l", baseline),
+    )
+    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="armv7l")
+    convergence = _fail_payload(receipt.event_id, arch_norm="armv7l")
+    convergence["verdict"] = "stalled"
+    convergence["evidence_path"] = str(current)
+    convergence["evidence_sha256"] = _file_sha(current)
+
+    adopted = adopt_secondary_target_with_convergence(
+        db,
+        UNIT_KEY,
+        arch_norm="armv7l",
+        expected_reproduce_event_id=reproduce_id,
+        convergence_payload=convergence,
+    )
+
+    assert adopted is True
+    adoption = latest_event(db, UNIT_KEY, "SECONDARY_TARGET_ADOPTED")
+    outcome = latest_event(db, UNIT_KEY, "CONVERGENCE")
+    assert adoption is not None
+    assert outcome is not None
+    assert adoption["payload"]["baseline_error_count"] == 1  # type: ignore[index]
+    assert outcome["payload"]["verdict"] == "advance"  # type: ignore[index]
+    assert (
+        adopt_secondary_target_with_convergence(
+            db,
+            UNIT_KEY,
+            arch_norm="armv7l",
+            expected_reproduce_event_id=reproduce_id,
+            convergence_payload=convergence,
+        )
+        is False
+    )
+
+
+def test_secondary_adoption_rejects_changed_or_truncated_evidence(tmp_path: Path) -> None:
+    for suffix, current_evidence in (
+        ("changed", _evidence("different warning")),
+        ("truncated", {**_evidence("same warning"), "truncated": True}),
+    ):
+        db = _db(tmp_path, f"{suffix}.sqlite3")
+        _create_unit(db)
+        _create_round(db)
+        baseline = tmp_path / f"{suffix}-baseline.json"
+        current = tmp_path / f"{suffix}-current.json"
+        _write_json(baseline, _evidence("same warning"))
+        _write_json(current, current_evidence)
+        reproduce_id = append_event(
+            db,
+            UNIT_KEY,
+            "REPRODUCE",
+            _reproduce_payload("armv7l", baseline),
+        )
+        receipt = consume_build_invocation(
+            db, UNIT_KEY, round_index=1, arch_norm="armv7l"
+        )
+        convergence = _fail_payload(receipt.event_id, arch_norm="armv7l")
+        convergence["verdict"] = "stalled"
+        convergence["evidence_path"] = str(current)
+        convergence["evidence_sha256"] = _file_sha(current)
+
+        assert (
+            adopt_secondary_target_with_convergence(
+                db,
+                UNIT_KEY,
+                arch_norm="armv7l",
+                expected_reproduce_event_id=reproduce_id,
+                convergence_payload=convergence,
+            )
+            is False
+        )
+        assert latest_event(db, UNIT_KEY, "SECONDARY_TARGET_ADOPTED") is None
+        assert latest_event(db, UNIT_KEY, "CONVERGENCE") is None
+
+
+def test_secondary_adoption_rolls_back_if_convergence_slot_is_already_filled(
+    tmp_path: Path,
+) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+    _create_round(db)
+    baseline = tmp_path / "baseline.json"
+    current = tmp_path / "current.json"
+    _write_json(baseline, _evidence("same warning"))
+    _write_json(current, _evidence("same warning"))
+    reproduce_id = append_event(
+        db,
+        UNIT_KEY,
+        "REPRODUCE",
+        _reproduce_payload("armv7l", baseline),
+    )
+    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="armv7l")
+    convergence = _fail_payload(receipt.event_id, arch_norm="armv7l")
+    convergence["verdict"] = "stalled"
+    convergence["evidence_path"] = str(current)
+    convergence["evidence_sha256"] = _file_sha(current)
+    append_event(db, UNIT_KEY, "CONVERGENCE", convergence)
+
+    with pytest.raises(sqlite3.IntegrityError):
+        adopt_secondary_target_with_convergence(
+            db,
+            UNIT_KEY,
+            arch_norm="armv7l",
+            expected_reproduce_event_id=reproduce_id,
+            convergence_payload=convergence,
+        )
+
+    assert latest_event(db, UNIT_KEY, "SECONDARY_TARGET_ADOPTED") is None
+
+
+def test_concurrent_secondary_adoption_has_exactly_one_winner(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+    _create_round(db)
+    baseline = tmp_path / "baseline.json"
+    current = tmp_path / "current.json"
+    _write_json(baseline, _evidence("same warning"))
+    _write_json(current, _evidence("same warning"))
+    reproduce_id = append_event(
+        db,
+        UNIT_KEY,
+        "REPRODUCE",
+        _reproduce_payload("armv7l", baseline),
+    )
+    first = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="armv7l")
+    second = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="armv7l")
+    barrier = threading.Barrier(2)
+    outcomes: list[bool] = []
+
+    def adopt(invocation_event_id: int) -> None:
+        convergence = _fail_payload(invocation_event_id, arch_norm="armv7l")
+        convergence["verdict"] = "stalled"
+        convergence["evidence_path"] = str(current)
+        convergence["evidence_sha256"] = _file_sha(current)
+        barrier.wait()
+        outcomes.append(
+            adopt_secondary_target_with_convergence(
+                db,
+                UNIT_KEY,
+                arch_norm="armv7l",
+                expected_reproduce_event_id=reproduce_id,
+                convergence_payload=convergence,
+            )
+        )
+
+    threads = [
+        threading.Thread(target=adopt, args=(first.event_id,)),
+        threading.Thread(target=adopt, args=(second.event_id,)),
+    ]
+    for thread in threads:
+        thread.start()
+    for thread in threads:
+        thread.join()
+
+    assert sorted(outcomes) == [False, True]
+    conn = db.connect()
+    try:
+        assert conn.execute(
+            "SELECT COUNT(*) FROM campaign_gate_events "
+            "WHERE event_type = 'SECONDARY_TARGET_ADOPTED'"
+        ).fetchone()[0] == 1
+        assert conn.execute(
+            "SELECT COUNT(*) FROM campaign_gate_events WHERE event_type = 'CONVERGENCE'"
+        ).fetchone()[0] == 1
+    finally:
+        conn.close()
+
+
+def test_link_verification_and_pass_convergence_are_atomic(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+    _create_round(db)
+    record = _record("V-LINK")
+    write_pass_record(db, record)
+    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+
+    link_verification_with_convergence(
+        db,
+        UNIT_KEY,
+        convergence_payload=_pass_payload(receipt.event_id, record.verification_id),
+        arch_raw="standard-aarch64",
+        arch_norm="aarch64",
+        verification_id=record.verification_id,
+        round_index=1,
+        edit_spec_sha256=EDIT_SHA,
+    )
+
+    conn = db.connect()
+    try:
+        assert conn.execute("SELECT COUNT(*) FROM campaign_verifications").fetchone()[0] == 1
+        assert conn.execute(
+            "SELECT COUNT(*) FROM campaign_gate_events "
+            "WHERE event_type = 'CONVERGENCE' AND verdict = 'n_a'"
+        ).fetchone()[0] == 1
+    finally:
+        conn.close()
+
+
+def test_link_mismatch_rolls_back_link_and_event(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+    _create_round(db)
+    record = _record("V-BAD")
+    write_pass_record(db, record)
+    receipt = consume_build_invocation(db, UNIT_KEY, round_index=1, arch_norm="aarch64")
+    payload = _pass_payload(receipt.event_id, record.verification_id)
+
+    with pytest.raises(StateInconsistent):
+        link_verification_with_convergence(
+            db,
+            UNIT_KEY,
+            convergence_payload=replace_payload(payload, arch_norm="armv7l"),
+            arch_raw="standard-aarch64",
+            arch_norm="aarch64",
+            verification_id=record.verification_id,
+            round_index=1,
+            edit_spec_sha256=EDIT_SHA,
+        )
+
+    conn = db.connect()
+    try:
+        assert conn.execute("SELECT COUNT(*) FROM campaign_verifications").fetchone()[0] == 0
+        assert conn.execute(
+            "SELECT COUNT(*) FROM campaign_gate_events WHERE event_type = 'CONVERGENCE'"
+        ).fetchone()[0] == 0
+    finally:
+        conn.close()
+
+
+def test_find_unlinked_pass_returns_all_matches_without_round_argument(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+    write_pass_record(db, _record("V1"))
+    write_pass_record(db, _record("V2"))
+    write_pass_record(db, _record("V3", arch="standard-armv7l"))
+
+    rows = find_unlinked_pass(
+        db,
+        UNIT_KEY,
+        arch_norm="aarch64",
+        failure_key="failure-key",
+    )
+
+    assert [row["verification_id"] for row in rows] == ["V1", "V2"]
+
+
+def test_qb_request_and_result_follow_two_level_latest_semantics(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+    first = create_qb_request(db, UNIT_KEY, request_id="R1", sbs_target="target")
+    append_qb_event(db, request_seq=first, event_type="BUILD_BOUND", qb_build_id="B1")
+    append_qb_event(
+        db,
+        request_seq=first,
+        event_type="RESULT",
+        qb_build_id="B1",
+        status="FAIL",
+        sbs_target_echo="target",
+        qb_result_sha256="1" * 64,
+    )
+    second = create_qb_request(db, UNIT_KEY, request_id="R2", sbs_target="target")
+    append_qb_event(db, request_seq=second, event_type="BUILD_BOUND", qb_build_id="B2")
+    append_qb_event(
+        db,
+        request_seq=second,
+        event_type="RESULT",
+        qb_build_id="B2",
+        status="PASS",
+        accepted=True,
+        sbs_target_echo="target",
+        qb_result_sha256="2" * 64,
+    )
+
+    result = latest_qb_result(db, UNIT_KEY)
+    assert result is not None
+    assert result["request_seq"] == second
+    assert result["status"] == "PASS"
+    assert find_unit_by_request_id(db, "R2") == UNIT_KEY
+    assert find_unit_by_qb_build_id(db, "B2") == UNIT_KEY
+
+
+def test_unknown_and_stronger_transaction_event_types_are_rejected(tmp_path: Path) -> None:
+    db = _db(tmp_path)
+    _create_unit(db)
+
+    with pytest.raises(UnknownEventType):
+        append_event(db, UNIT_KEY, "INVENTED", {})
+    with pytest.raises(PayloadSchemaError, match="consume_build_invocation"):
+        append_event(
+            db,
+            UNIT_KEY,
+            "BUILD_INVOCATION",
+            {"round_index": 1, "arch_norm": "aarch64"},
+        )
+    with pytest.raises(PayloadSchemaError, match="atomic adoption"):
+        append_event(db, UNIT_KEY, "SECONDARY_TARGET_ADOPTED", {})
+    assert latest_event(db, UNIT_KEY, "CONVERGENCE") is None
+
+
+def _insert_raw_unit(
+    conn: sqlite3.Connection,
+    *,
+    primary_arch: str | None,
+    evidence_ref: str | None,
+) -> None:
+    conn.execute(
+        "INSERT INTO campaign_units "
+        "(campaign_unit_key, ci_system, source_build_id, project, branch, spec_name, "
+        "base_commit, submission_identity_key, toolchain_profile, ci_evidence_ref, "
+        "ci_evidence_sha256, primary_arch, max_rounds, max_build_invocations, "
+        "failed_arches, created_at, schema_version) "
+        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
+        (
+            "raw-unit",
+            "quickbuild",
+            "1",
+            "platform/test",
+            "tizen",
+            "pkg",
+            "a" * 40,
+            "submission",
+            "standard",
+            evidence_ref,
+            "b" * 64,
+            primary_arch,
+            3,
+            9,
+            '["standard-aarch64"]',
+            "2026-08-05T00:00:00+00:00",
+            CAMPAIGN_SCHEMA_VERSION,
+        ),
+    )
+
+
+def _insert_raw_convergence(
+    conn: sqlite3.Connection,
+    *,
+    invocation_event_id: int,
+    verification_id: str,
+) -> None:
+    payload = _pass_payload(invocation_event_id, verification_id)
+    conn.execute(
+        "INSERT INTO campaign_gate_events "
+        "(campaign_unit_key, round_index, arch_norm, verdict, invocation_event_id, "
+        "event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
+        (
+            UNIT_KEY,
+            1,
+            "aarch64",
+            "n_a",
+            invocation_event_id,
+            "CONVERGENCE",
+            json.dumps(payload, sort_keys=True),
+            "2026-08-05T00:00:00+00:00",
+        ),
+    )
+
+
+def replace_payload(payload: dict[str, object], **changes: object) -> dict[str, object]:
+    result = dict(payload)
+    result.update(changes)
+    return result
+
+
+def _evidence(message: str) -> dict[str, object]:
+    return {
+        "primary_error": {
+            "kind": "werror",
+            "normalized_file": "src/main.c",
+            "warning_option": "-Wunused-variable",
+            "symbol": "value",
+            "message": message,
+        },
+        "error_clusters": {
+            "clusters": [
+                {
+                    "kind": "werror",
+                    "diagnostic_kinds": ["werror"],
+                    "count": 1,
+                    "files": ["src/main.c"],
+                    "locations_truncated": False,
+                }
+            ]
+        },
+        "truncated": False,
+    }
+
+
+def _write_json(path: Path, value: dict[str, object]) -> None:
+    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
+
+
+def _file_sha(path: Path) -> str:
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+def _reproduce_payload(arch_norm: str, evidence: Path) -> dict[str, object]:
+    return {
+        "arch_norm": arch_norm,
+        "outcome": "different_failure",
+        "evidence_local": str(evidence),
+        "evidence_sha256": _file_sha(evidence),
+        "synthetic_zero_error": False,
+        "gbs_conf_sha256": "b" * 64,
+        "ci_evidence_sha256_used": "c" * 64,
+        "build_log": "/tmp/build.log",
+        "basis": {},
+    }
+
+
+def test_arch_norm_contract_is_exact_three_value_whitelist() -> None:
+    assert ARCH_NORMS == {"aarch64", "armv7l", "x86_64"}
diff --git a/tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py b/tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py
new file mode 100644
index 0000000..a39dca6
--- /dev/null
+++ b/tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py
@@ -0,0 +1,1167 @@
+"""Atomic campaign repair-step orchestration around the existing build verifier."""
+
+from __future__ import annotations
+
+import fcntl
+import hashlib
+import json
+import os
+import subprocess
+from collections.abc import Callable, Iterator, Mapping
+from contextlib import contextmanager
+from dataclasses import asdict, dataclass
+from datetime import datetime, timezone
+from pathlib import Path
+from typing import Any
+from urllib.parse import urlsplit
+
+import yaml
+
+from ci_triage.campaign_state import (
+    ARCH_RAW_TO_NORM,
+    HELD_FOR_INVESTIGATION,
+    BudgetExhausted,
+    CampaignStateBusy,
+    CampaignStateError,
+    ReconcileResult,
+    RoundsExhausted,
+    StateInconsistent,
+    Unit,
+    adopt_secondary_target_with_convergence,
+    append_event,
+    append_status,
+    consume_build_invocation,
+    create_round,
+    get_round,
+    get_unit,
+    invocations_used,
+    latest_reproduce,
+    link_verification_with_convergence,
+    reconcile_pass_and_invocations,
+)
+from ci_triage.previous_evidence import MissingEvidence, ResolvedEvidence, resolve
+from ci_triage.state import StateDatabase, build_failure_key, get_record
+from ci_triage.verify.build_verify import BuildVerifyOptions, BuildVerifyResult, build_verify
+from ci_triage.verify.convergence import ConvergenceResult, check_convergence
+from ci_triage.verify.failure_classify import (
+    REPAIR_AUTO,
+    REPAIR_DENIED,
+    REPAIR_NEEDS_CONFIRMATION,
+)
+
+EXIT_OK = 0
+EXIT_INVALID_ARGS = 2
+EXIT_REJECTED = 4
+EXIT_TOOLING = 5
+
+REJECTED_IDENTITY_MISMATCH = "REJECTED_IDENTITY_MISMATCH"
+REJECTED_PREVIOUS_EVIDENCE_MISSING = "REJECTED_PREVIOUS_EVIDENCE_MISSING"
+REJECTED_BASELINE_EVIDENCE_MISMATCH = "REJECTED_BASELINE_EVIDENCE_MISMATCH"
+REJECTED_CONF_DRIFT = "REJECTED_CONF_DRIFT"
+REJECTED_STATE_INCONSISTENT = "REJECTED_STATE_INCONSISTENT"
+CAMPAIGN_STATE_BUSY = "CAMPAIGN_STATE_BUSY"
+
+REPAIR_ROUND_RUNNING = "REPAIR_ROUND_RUNNING"
+ROUNDS_EXHAUSTED = "ROUNDS_EXHAUSTED"
+DENIED = "DENIED"
+STALLED = "STALLED"
+REGRESSED = "REGRESSED"
+
+BuildVerifyFn = Callable[[BuildVerifyOptions], BuildVerifyResult]
+ConvergenceFn = Callable[..., ConvergenceResult]
+SubprocessRunner = Callable[..., subprocess.CompletedProcess[str]]
+
+
+@dataclass(frozen=True)
+class CampaignRepairStepOptions:
+    """Authoritative inputs accepted by ``campaign-repair-step``."""
+
+    campaign_unit_key: str
+    state_db: StateDatabase
+    config_path: Path
+    round_index: int
+    edit_spec_path: Path
+    arch_raw: str
+    wall_timeout: int | None = None
+    extra_pythonpath: tuple[Path, ...] = ()
+
+
+@dataclass(frozen=True)
+class CampaignRepairStepResult:
+    """Fixed stdout schema consumed by the campaign workflow."""
+
+    result: str
+    verdict: str
+    repair_allowed: str
+    failure_class: str | None
+    failure_stage: str | None
+    adopted: bool
+    convergence_reason: str
+    previous_basis: str
+    round_index: int
+    arch_norm: str
+    verification_id: str | None
+    evidence_path: str | None
+    reconciliation: dict[str, list[object]]
+    warnings: list[dict[str, str]]
+    invocations_used: int
+    error_code: str | None
+
+    def to_dict(self) -> dict[str, object]:
+        return asdict(self)
+
+
+@dataclass(frozen=True)
+class CampaignRepairStepOutcome:
+    """Result payload plus the process exit code."""
+
+    result: CampaignRepairStepResult
+    exit_code: int
+
+
+@dataclass(frozen=True)
+class _CampaignConfig:
+    campaign_workspace: Path
+    clang_conf_path: Path
+    wall_timeout: int
+
+
+class _StepError(RuntimeError):
+    def __init__(self, code: str, reason: str, exit_code: int) -> None:
+        super().__init__(reason)
+        self.code = code
+        self.reason = reason
+        self.exit_code = exit_code
+
+
+def campaign_repair_step(
+    options: CampaignRepairStepOptions,
+    *,
+    build_verify_fn: BuildVerifyFn = build_verify,
+    convergence_fn: ConvergenceFn = check_convergence,
+    subprocess_runner: SubprocessRunner = subprocess.run,
+) -> CampaignRepairStepOutcome:
+    """Run the frozen lock-to-link repair sequence for one unit and architecture."""
+
+    arch_norm = ARCH_RAW_TO_NORM.get(options.arch_raw, "")
+    try:
+        if not arch_norm:
+            raise _StepError(
+                REJECTED_IDENTITY_MISMATCH,
+                f"arch is not in the verified whitelist: {options.arch_raw!r}",
+                EXIT_REJECTED,
+            )
+        config = _load_config(options.config_path, options.wall_timeout)
+        workspace_root = _workspace_root(config, options.campaign_unit_key, arch_norm)
+        with _repair_step_lock(workspace_root):
+            unit, reproduce = _read_only_identity(options, arch_norm)
+            return _run_locked(
+                options,
+                unit=unit,
+                reproduce=reproduce,
+                config=config,
+                arch_norm=arch_norm,
+                workspace_root=workspace_root,
+                build_verify_fn=build_verify_fn,
+                convergence_fn=convergence_fn,
+                subprocess_runner=subprocess_runner,
+            )
+    except _StepError as exc:
+        return _error_outcome(options, arch_norm, exc)
+    except BlockingIOError:
+        return _error_outcome(
+            options,
+            arch_norm,
+            _StepError(CAMPAIGN_STATE_BUSY, "repair-step lock is already held", EXIT_TOOLING),
+        )
+    except CampaignStateBusy as exc:
+        return _error_outcome(
+            options,
+            arch_norm,
+            _StepError(CAMPAIGN_STATE_BUSY, str(exc), EXIT_TOOLING),
+        )
+    except CampaignStateError as exc:
+        return _error_outcome(
+            options,
+            arch_norm,
+            _StepError(REJECTED_STATE_INCONSISTENT, str(exc), EXIT_REJECTED),
+        )
+    except OSError as exc:
+        return _error_outcome(
+            options,
+            arch_norm,
+            _StepError("BASELINE_TOOLING_FAILED", str(exc), EXIT_TOOLING),
+        )
+
+
+def _run_locked(
+    options: CampaignRepairStepOptions,
+    *,
+    unit: Unit,
+    reproduce: dict[str, object],
+    config: _CampaignConfig,
+    arch_norm: str,
+    workspace_root: Path,
+    build_verify_fn: BuildVerifyFn,
+    convergence_fn: ConvergenceFn,
+    subprocess_runner: SubprocessRunner,
+) -> CampaignRepairStepOutcome:
+    # Step 2: bind the requested edit bytes to a per-round canonical path before
+    # any reconciliation success can return.
+    edit_bytes, edit_sha = _read_edit_spec(options.edit_spec_path)
+    output_dir = workspace_root / "out" / f"round_{options.round_index}"
+    canonical_edit_spec = output_dir / "edit_spec.json"
+    _materialize_canonical_edit_spec(canonical_edit_spec, edit_bytes, edit_sha)
+    try:
+        create_round(
+            options.state_db,
+            options.campaign_unit_key,
+            round_index=options.round_index,
+            edit_spec_ref=str(canonical_edit_spec),
+            edit_spec_sha256=edit_sha,
+        )
+    except RoundsExhausted as exc:
+        append_status(options.state_db, options.campaign_unit_key, ROUNDS_EXHAUSTED, str(exc))
+        raise _StepError("RoundsExhausted", str(exc), EXIT_REJECTED) from exc
+    except StateInconsistent as exc:
+        raise _StepError(REJECTED_IDENTITY_MISMATCH, str(exc), EXIT_REJECTED) from exc
+    _revalidate_round(options, canonical_edit_spec, edit_sha)
+
+    failure_key = _failure_key(unit, options.arch_raw)
+
+    # Step 3: this API is the sole reconciliation read/classify/write boundary.
+    reconciliation = reconcile_pass_and_invocations(
+        options.state_db,
+        options.campaign_unit_key,
+        round_index=options.round_index,
+        arch_norm=arch_norm,
+        failure_key=failure_key,
+        edit_spec_sha256=edit_sha,
+    )
+    reconciliation_json, warnings = _serialize_reconciliation(reconciliation)
+    if reconciliation.branch in {"linked_already", "relinked"}:
+        return CampaignRepairStepOutcome(
+            result=_result(
+                options,
+                arch_norm,
+                result="PASS",
+                verdict="n_a",
+                repair_allowed=REPAIR_AUTO,
+                reason=reconciliation.branch,
+                verification_id=reconciliation.current_verification_id,
+                reconciliation=reconciliation_json,
+                warnings=warnings,
+            ),
+            exit_code=EXIT_OK,
+        )
+    if reconciliation.branch in {"state_inconsistent_held", "orphan_pass_held"}:
+        return CampaignRepairStepOutcome(
+            result=_result(
+                options,
+                arch_norm,
+                result="FAIL",
+                verdict="n_a",
+                repair_allowed=REPAIR_DENIED,
+                reason=reconciliation.branch,
+                reconciliation=reconciliation_json,
+                warnings=warnings,
+                error_code=REJECTED_STATE_INCONSISTENT,
+            ),
+            exit_code=EXIT_REJECTED,
+        )
+    if reconciliation.branch != "proceed":
+        raise _StepError(
+            REJECTED_STATE_INCONSISTENT,
+            f"unknown reconciliation branch {reconciliation.branch!r}",
+            EXIT_REJECTED,
+        )
+
+    # Step 4: previous evidence is checked only after recovery exits have run.
+    previous = resolve(options.state_db, options.campaign_unit_key, arch_norm=arch_norm)
+    if isinstance(previous, MissingEvidence):
+        append_status(
+            options.state_db,
+            options.campaign_unit_key,
+            HELD_FOR_INVESTIGATION,
+            "previous_evidence_missing",
+            arch_norm,
+        )
+        return CampaignRepairStepOutcome(
+            result=_result(
+                options,
+                arch_norm,
+                result="FAIL",
+                verdict="n_a",
+                repair_allowed=REPAIR_DENIED,
+                reason=previous.reason,
+                reconciliation=reconciliation_json,
+                warnings=warnings,
+                error_code=REJECTED_PREVIOUS_EVIDENCE_MISSING,
+            ),
+            exit_code=EXIT_REJECTED,
+        )
+
+    try:
+        receipt = consume_build_invocation(
+            options.state_db,
+            options.campaign_unit_key,
+            round_index=options.round_index,
+            arch_norm=arch_norm,
+        )
+    except BudgetExhausted as exc:
+        append_status(options.state_db, options.campaign_unit_key, ROUNDS_EXHAUSTED, str(exc))
+        raise _StepError("BudgetExhausted", str(exc), EXIT_REJECTED) from exc
+
+    # Step 5: filesystem identity is deliberately checked only once a new build
+    # is known to be necessary; relink recovery does not depend on these files.
+    try:
+        build_options = _build_options(
+            options,
+            unit=unit,
+            reproduce=reproduce,
+            config=config,
+            arch_norm=arch_norm,
+            workspace_root=workspace_root,
+            output_dir=output_dir,
+            canonical_edit_spec=canonical_edit_spec,
+            subprocess_runner=subprocess_runner,
+        )
+    except _StepError as exc:
+        return CampaignRepairStepOutcome(
+            result=_result(
+                options,
+                arch_norm,
+                result="FAIL",
+                verdict="n_a",
+                repair_allowed=REPAIR_DENIED,
+                reason=exc.reason,
+                reconciliation=reconciliation_json,
+                warnings=warnings,
+                invocations_used_count=receipt.invocations_used,
+                error_code=exc.code,
+            ),
+            exit_code=exc.exit_code,
+        )
+    build_result = build_verify_fn(build_options)
+
+    if build_result.result == "PASS":
+        return _handle_pass(
+            options,
+            arch_norm=arch_norm,
+            edit_sha=edit_sha,
+            build_result=build_result,
+            invocation_event_id=receipt.event_id,
+            invocations_used_count=receipt.invocations_used,
+            reconciliation=reconciliation_json,
+            warnings=warnings,
+        )
+    return _handle_fail(
+        options,
+        arch_norm=arch_norm,
+        reproduce=reproduce,
+        previous=previous,
+        build_result=build_result,
+        invocation_event_id=receipt.event_id,
+        invocations_used_count=receipt.invocations_used,
+        reconciliation=reconciliation_json,
+        warnings=warnings,
+        convergence_fn=convergence_fn,
+    )
+
+
+def _handle_pass(
+    options: CampaignRepairStepOptions,
+    *,
+    arch_norm: str,
+    edit_sha: str,
+    build_result: BuildVerifyResult,
+    invocation_event_id: int,
+    invocations_used_count: int,
+    reconciliation: dict[str, list[object]],
+    warnings: list[dict[str, str]],
+) -> CampaignRepairStepOutcome:
+    verification_id = build_result.verification_id
+    if not verification_id or get_record(options.state_db, verification_id) is None:
+        raise _StepError(
+            REJECTED_STATE_INCONSISTENT,
+            "build PASS did not produce a persisted verification record",
+            EXIT_REJECTED,
+        )
+    payload = _convergence_payload(
+        options,
+        arch_norm=arch_norm,
+        invocation_event_id=invocation_event_id,
+        result="PASS",
+        verdict="n_a",
+        reason="build_passed",
+        evidence_path=None,
+        evidence_sha256=None,
+        verification_id=verification_id,
+        actual_changed_paths=build_result.actual_changed_paths,
+        previous_basis="none",
+    )
+    try:
+        link_verification_with_convergence(
+            options.state_db,
+            options.campaign_unit_key,
+            convergence_payload=payload,
+            arch_raw=options.arch_raw,
+            arch_norm=arch_norm,
+            verification_id=verification_id,
+            round_index=options.round_index,
+            edit_spec_sha256=edit_sha,
+        )
+    except StateInconsistent as exc:
+        _record_link_failure(options, arch_norm, build_result, verification_id)
+        return CampaignRepairStepOutcome(
+            result=_result(
+                options,
+                arch_norm,
+                result="FAIL",
+                verdict="n_a",
+                repair_allowed=REPAIR_DENIED,
+                reason=str(exc),
+                failure_stage="link_failed",
+                verification_id=verification_id,
+                reconciliation=reconciliation,
+                warnings=warnings,
+                invocations_used_count=invocations_used_count,
+                error_code=REJECTED_STATE_INCONSISTENT,
+            ),
+            exit_code=EXIT_REJECTED,
+        )
+    return CampaignRepairStepOutcome(
+        result=_result(
+            options,
+            arch_norm,
+            result="PASS",
+            verdict="n_a",
+            repair_allowed=REPAIR_AUTO,
+            reason="build_passed",
+            verification_id=verification_id,
+            reconciliation=reconciliation,
+            warnings=warnings,
+            invocations_used_count=invocations_used_count,
+        ),
+        exit_code=EXIT_OK,
+    )
+
+
+def _handle_fail(
+    options: CampaignRepairStepOptions,
+    *,
+    arch_norm: str,
+    reproduce: dict[str, object],
+    previous: ResolvedEvidence,
+    build_result: BuildVerifyResult,
+    invocation_event_id: int,
+    invocations_used_count: int,
+    reconciliation: dict[str, list[object]],
+    warnings: list[dict[str, str]],
+    convergence_fn: ConvergenceFn,
+) -> CampaignRepairStepOutcome:
+    repair_allowed = build_result.repair_allowed or REPAIR_DENIED
+    if repair_allowed not in {REPAIR_AUTO, REPAIR_NEEDS_CONFIRMATION, REPAIR_DENIED}:
+        repair_allowed = REPAIR_DENIED
+
+    stage_reason = _non_substantive_reason(build_result)
+    if stage_reason is not None:
+        payload = _convergence_payload(
+            options,
+            arch_norm=arch_norm,
+            invocation_event_id=invocation_event_id,
+            result="n_a",
+            verdict="n_a",
+            reason=stage_reason,
+            evidence_path=None,
+            evidence_sha256=None,
+            verification_id=None,
+            actual_changed_paths=build_result.actual_changed_paths,
+            previous_basis="none",
+        )
+        append_event(options.state_db, options.campaign_unit_key, "CONVERGENCE", payload)
+        exit_code = (
+            EXIT_TOOLING
+            if stage_reason in {"analyzer_failed", "toolchain_failed"}
+            else EXIT_OK
+        )
+        return CampaignRepairStepOutcome(
+            result=_result(
+                options,
+                arch_norm,
+                result="FAIL",
+                verdict="n_a",
+                repair_allowed=repair_allowed,
+                reason=stage_reason,
+                failure_class=build_result.failure_class,
+                failure_stage=build_result.failure_stage,
+                reconciliation=reconciliation,
+                warnings=warnings,
+                invocations_used_count=invocations_used_count,
+                error_code=None,
+            ),
+            exit_code=exit_code,
+        )
+
+    current = _load_current_evidence(build_result.evidence)
+    if isinstance(current, MissingEvidence):
+        payload = _convergence_payload(
+            options,
+            arch_norm=arch_norm,
+            invocation_event_id=invocation_event_id,
+            result="n_a",
+            verdict="n_a",
+            reason="analyzer_failed",
+            evidence_path=None,
+            evidence_sha256=None,
+            verification_id=None,
+            actual_changed_paths=build_result.actual_changed_paths,
+            previous_basis="none",
+        )
+        append_event(options.state_db, options.campaign_unit_key, "CONVERGENCE", payload)
+        return CampaignRepairStepOutcome(
+            result=_result(
+                options,
+                arch_norm,
+                result="FAIL",
+                verdict="n_a",
+                repair_allowed=REPAIR_DENIED,
+                reason=current.reason,
+                failure_class="analyzer_failed",
+                failure_stage="analyzer_failed",
+                reconciliation=reconciliation,
+                warnings=warnings,
+                invocations_used_count=invocations_used_count,
+                error_code=None,
+            ),
+            exit_code=EXIT_TOOLING,
+        )
+
+    # Step 6a repeats the exact resolver used by step 4 to close the TOCTOU gap.
+    checked_previous = resolve(options.state_db, options.campaign_unit_key, arch_norm=arch_norm)
+    if isinstance(checked_previous, MissingEvidence):
+        return _record_previous_missing_after_consume(
+            options,
+            arch_norm=arch_norm,
+            invocation_event_id=invocation_event_id,
+            invocations_used_count=invocations_used_count,
+            reconciliation=reconciliation,
+            warnings=warnings,
+            reason=checked_previous.reason,
+        )
+    previous = checked_previous
+
+    if repair_allowed == REPAIR_DENIED:
+        verdict = "denied"
+        reason = build_result.error or "repair denied by failure classifier"
+        adopted = False
+    else:
+        convergence = convergence_fn(
+            current.evidence,
+            previous.evidence,
+            touched_files=set(build_result.actual_changed_paths),
+        )
+        verdict = convergence.verdict
+        reason = convergence.reason
+        adopted = False
+
+    payload = _convergence_payload(
+        options,
+        arch_norm=arch_norm,
+        invocation_event_id=invocation_event_id,
+        result="FAIL",
+        verdict=verdict,
+        reason=reason,
+        evidence_path=current.evidence_path,
+        evidence_sha256=current.evidence_sha256,
+        verification_id=None,
+        actual_changed_paths=build_result.actual_changed_paths,
+        previous_basis=previous.basis,
+    )
+    if verdict == "stalled":
+        reproduce_event_id = reproduce.get("event_id")
+        if not isinstance(reproduce_event_id, int):
+            raise _StepError(
+                REJECTED_STATE_INCONSISTENT,
+                "REPRODUCE event id is invalid",
+                EXIT_REJECTED,
+            )
+        adopted = adopt_secondary_target_with_convergence(
+            options.state_db,
+            options.campaign_unit_key,
+            arch_norm=arch_norm,
+            expected_reproduce_event_id=reproduce_event_id,
+            convergence_payload=payload,
+        )
+        if adopted:
+            verdict = "advance"
+        else:
+            append_event(options.state_db, options.campaign_unit_key, "CONVERGENCE", payload)
+    else:
+        append_event(options.state_db, options.campaign_unit_key, "CONVERGENCE", payload)
+
+    _append_verdict_status(options, verdict)
+    return CampaignRepairStepOutcome(
+        result=_result(
+            options,
+            arch_norm,
+            result="FAIL",
+            verdict=verdict,
+            repair_allowed=repair_allowed,
+            reason=reason,
+            failure_class=build_result.failure_class,
+            failure_stage=build_result.failure_stage,
+            adopted=adopted,
+            previous_basis=previous.basis,
+            evidence_path=current.evidence_path,
+            reconciliation=reconciliation,
+            warnings=warnings,
+            invocations_used_count=invocations_used_count,
+        ),
+        exit_code=EXIT_OK,
+    )
+
+
+def _read_only_identity(
+    options: CampaignRepairStepOptions,
+    arch_norm: str,
+) -> tuple[Unit, dict[str, object]]:
+    if options.round_index < 1:
+        raise _StepError("INVALID_ARGS", "round-index must be positive", EXIT_INVALID_ARGS)
+    unit = get_unit(options.state_db, options.campaign_unit_key)
+    if unit is None:
+        raise _StepError(
+            REJECTED_IDENTITY_MISMATCH,
+            f"campaign unit does not exist: {options.campaign_unit_key}",
+            EXIT_REJECTED,
+        )
+    _read_edit_spec(options.edit_spec_path)
+    reproduce = latest_reproduce(
+        options.state_db,
+        options.campaign_unit_key,
+        arch_norm=arch_norm,
+    )
+    if reproduce is None:
+        raise _StepError(
+            REJECTED_IDENTITY_MISMATCH,
+            f"REPRODUCE metadata is missing for arch {arch_norm}",
+            EXIT_REJECTED,
+        )
+    payload = reproduce.get("payload")
+    if not isinstance(payload, dict) or payload.get("arch_norm") != arch_norm:
+        raise _StepError(
+            REJECTED_IDENTITY_MISMATCH,
+            "REPRODUCE metadata does not match requested architecture",
+            EXIT_REJECTED,
+        )
+    if payload.get("ci_evidence_sha256_used") != unit.ci_evidence_sha256:
+        raise _StepError(
+            REJECTED_IDENTITY_MISMATCH,
+            "REPRODUCE metadata does not match the unit CI evidence identity",
+            EXIT_REJECTED,
+        )
+    return unit, reproduce
+
+
+def _build_options(
+    options: CampaignRepairStepOptions,
+    *,
+    unit: Unit,
+    reproduce: dict[str, object],
+    config: _CampaignConfig,
+    arch_norm: str,
+    workspace_root: Path,
+    output_dir: Path,
+    canonical_edit_spec: Path,
+    subprocess_runner: SubprocessRunner,
+) -> BuildVerifyOptions:
+    payload = reproduce.get("payload")
+    if not isinstance(payload, dict):
+        raise _StepError(REJECTED_STATE_INCONSISTENT, "invalid REPRODUCE payload", EXIT_REJECTED)
+    conf_sha = payload.get("gbs_conf_sha256")
+    if not config.clang_conf_path.is_file() or _sha256_file(config.clang_conf_path) != conf_sha:
+        raise _StepError(REJECTED_CONF_DRIFT, "clang configuration hash changed", EXIT_REJECTED)
+    evidence_value = payload.get("evidence_local")
+    evidence_sha = payload.get("evidence_sha256")
+    if not isinstance(evidence_value, str) or not isinstance(evidence_sha, str):
+        raise _StepError(
+            REJECTED_BASELINE_EVIDENCE_MISMATCH,
+            "REPRODUCE baseline evidence binding is invalid",
+            EXIT_REJECTED,
+        )
+    baseline_evidence = Path(evidence_value)
+    if not baseline_evidence.is_file() or _sha256_file(baseline_evidence) != evidence_sha:
+        raise _StepError(
+            REJECTED_BASELINE_EVIDENCE_MISMATCH,
+            "baseline evidence file is missing or changed",
+            EXIT_REJECTED,
+        )
+    src_clean = config.campaign_workspace / _unit_hash(unit.campaign_unit_key) / "src"
+    _validate_source_identity(
+        src_clean,
+        unit,
+        subprocess_runner=subprocess_runner,
+    )
+    return BuildVerifyOptions(
+        src_clean=src_clean,
+        base_commit=unit.base_commit,
+        edit_spec_path=canonical_edit_spec,
+        gbs_conf=config.clang_conf_path,
+        package=unit.spec_name,
+        workspace_root=workspace_root,
+        baseline_evidence=baseline_evidence,
+        output_dir=output_dir,
+        iter_index=options.round_index,
+        wall_timeout=options.wall_timeout or config.wall_timeout,
+        state_db=options.state_db,
+        ci_system=unit.ci_system,
+        build_id=unit.source_build_id,
+        project=unit.project,
+        branch=unit.branch,
+        arch=options.arch_raw,
+        extra_pythonpath=options.extra_pythonpath,
+    )
+
+
+def _validate_source_identity(
+    src_clean: Path,
+    unit: Unit,
+    *,
+    subprocess_runner: SubprocessRunner,
+) -> None:
+    try:
+        head = _git_stdout(src_clean, ["rev-parse", "HEAD"], subprocess_runner)
+        origin = _git_stdout(src_clean, ["remote", "get-url", "origin"], subprocess_runner)
+    except (OSError, subprocess.CalledProcessError) as exc:
+        raise _StepError(
+            REJECTED_IDENTITY_MISMATCH,
+            f"source identity could not be read: {exc}",
+            EXIT_REJECTED,
+        ) from exc
+    if head != unit.base_commit or _normalize_project(origin) != unit.project:
+        raise _StepError(
+            REJECTED_IDENTITY_MISMATCH,
+            "source HEAD or origin does not match campaign unit",
+            EXIT_REJECTED,
+        )
+    marker = src_clean / ".campaign_clone"
+    try:
+        marker_value: Any = json.loads(marker.read_text(encoding="utf-8"))
+    except (OSError, json.JSONDecodeError) as exc:
+        raise _StepError(
+            REJECTED_IDENTITY_MISMATCH,
+            f"campaign clone marker is unreadable: {exc}",
+            EXIT_REJECTED,
+        ) from exc
+    expected = {
+        "unit_key": unit.campaign_unit_key,
+        "project": unit.project,
+        "base_commit": unit.base_commit,
+    }
+    if marker_value != expected:
+        raise _StepError(
+            REJECTED_IDENTITY_MISMATCH,
+            "campaign clone marker does not match campaign unit",
+            EXIT_REJECTED,
+        )
+
+
+def _load_current_evidence(path_value: str | None) -> ResolvedEvidence | MissingEvidence:
+    if not path_value:
+        return MissingEvidence("build failure did not produce analyzer evidence")
+    path = Path(path_value)
+    try:
+        raw = path.read_bytes()
+        value: Any = json.loads(raw)
+    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
+        return MissingEvidence(f"current evidence is unreadable: {exc}")
+    if not isinstance(value, dict):
+        return MissingEvidence("current evidence must be a JSON object")
+    return ResolvedEvidence(
+        evidence=value,
+        basis="prev_build",
+        evidence_path=str(path),
+        evidence_sha256=hashlib.sha256(raw).hexdigest(),
+    )
+
+
+def _record_previous_missing_after_consume(
+    options: CampaignRepairStepOptions,
+    *,
+    arch_norm: str,
+    invocation_event_id: int,
+    invocations_used_count: int,
+    reconciliation: dict[str, list[object]],
+    warnings: list[dict[str, str]],
+    reason: str,
+) -> CampaignRepairStepOutcome:
+    payload = _convergence_payload(
+        options,
+        arch_norm=arch_norm,
+        invocation_event_id=invocation_event_id,
+        result="n_a",
+        verdict="n_a",
+        reason="previous_evidence_missing",
+        evidence_path=None,
+        evidence_sha256=None,
+        verification_id=None,
+        actual_changed_paths=[],
+        previous_basis="none",
+    )
+    append_event(options.state_db, options.campaign_unit_key, "CONVERGENCE", payload)
+    append_status(
+        options.state_db,
+        options.campaign_unit_key,
+        HELD_FOR_INVESTIGATION,
+        "previous_evidence_missing",
+        arch_norm,
+    )
+    return CampaignRepairStepOutcome(
+        result=_result(
+            options,
+            arch_norm,
+            result="FAIL",
+            verdict="n_a",
+            repair_allowed=REPAIR_DENIED,
+            reason=reason,
+            reconciliation=reconciliation,
+            warnings=warnings,
+            invocations_used_count=invocations_used_count,
+            error_code=REJECTED_PREVIOUS_EVIDENCE_MISSING,
+        ),
+        exit_code=EXIT_REJECTED,
+    )
+
+
+def _record_link_failure(
+    options: CampaignRepairStepOptions,
+    arch_norm: str,
+    result: BuildVerifyResult,
+    verification_id: str,
+) -> None:
+    append_event(
+        options.state_db,
+        options.campaign_unit_key,
+        "ORPHAN_PASS",
+        {
+            "round_index": options.round_index,
+            "arch_norm": arch_norm,
+            "verification_id": verification_id,
+            "worktree_path": result.worktree_path or "<unknown>",
+            "reason": "link_failed",
+            "detected_at": _now(),
+        },
+    )
+    append_status(
+        options.state_db,
+        options.campaign_unit_key,
+        HELD_FOR_INVESTIGATION,
+        "link_mismatch",
+        arch_norm,
+    )
+
+
+def _append_verdict_status(options: CampaignRepairStepOptions, verdict: str) -> None:
+    statuses = {"denied": DENIED, "stalled": STALLED, "regressed": REGRESSED}
+    status = statuses.get(verdict)
+    if status is not None:
+        append_status(options.state_db, options.campaign_unit_key, status, verdict)
+
+
+def _non_substantive_reason(result: BuildVerifyResult) -> str | None:
+    stage = result.failure_stage or ""
+    if stage in {"apply_failed", "apply_unexpected_paths", "no_effective_changes"}:
+        return "apply_failed"
+    if stage in {"analyzer_failed"} or (stage == "gbs_build_failed" and not result.evidence):
+        return "analyzer_failed"
+    if stage in {
+        "build_timeout",
+        "build_mutated_source",
+        "infrastructure_failed",
+        "toolchain_failed",
+    }:
+        return "toolchain_failed"
+    return None
+
+
+def _convergence_payload(
+    options: CampaignRepairStepOptions,
+    *,
+    arch_norm: str,
+    invocation_event_id: int,
+    result: str,
+    verdict: str,
+    reason: str,
+    evidence_path: str | None,
+    evidence_sha256: str | None,
+    verification_id: str | None,
+    actual_changed_paths: list[str],
+    previous_basis: str,
+) -> dict[str, object]:
+    return {
+        "round_index": options.round_index,
+        "arch_norm": arch_norm,
+        "invocation_event_id": invocation_event_id,
+        "result": result,
+        "verdict": verdict,
+        "reason": reason,
+        "evidence_path": evidence_path,
+        "evidence_sha256": evidence_sha256,
+        "verification_id": verification_id,
+        "actual_changed_paths": sorted(actual_changed_paths),
+        "previous_basis": previous_basis,
+        "at": _now(),
+    }
+
+
+def _serialize_reconciliation(
+    value: ReconcileResult,
+) -> tuple[dict[str, list[object]], list[dict[str, str]]]:
+    relinks: list[object] = [
+        {
+            "round_index": round_index,
+            "verification_id": verification_id,
+            "invocation_event_id": invocation_event_id,
+        }
+        for round_index, verification_id, invocation_event_id in sorted(
+            value.other_round_relinks,
+            key=lambda item: (item[0], item[1], item[2]),
+        )
+    ]
+    non_campaign = sorted(set(value.non_campaign_verification_ids))
+    warnings = [
+        {"code": "non_campaign_verification", "verification_id": verification_id}
+        for verification_id in non_campaign
+    ]
+    return (
+        {
+            "other_round_relinks": relinks,
+            "non_campaign_verification_ids": list(non_campaign),
+        },
+        warnings,
+    )
+
+
+def _empty_reconciliation() -> dict[str, list[object]]:
+    return {"other_round_relinks": [], "non_campaign_verification_ids": []}
+
+
+def _result(
+    options: CampaignRepairStepOptions,
+    arch_norm: str,
+    *,
+    result: str,
+    verdict: str,
+    repair_allowed: str,
+    reason: str,
+    failure_class: str | None = None,
+    failure_stage: str | None = None,
+    adopted: bool = False,
+    previous_basis: str = "none",
+    verification_id: str | None = None,
+    evidence_path: str | None = None,
+    reconciliation: dict[str, list[object]] | None = None,
+    warnings: list[dict[str, str]] | None = None,
+    invocations_used_count: int | None = None,
+    error_code: str | None = None,
+) -> CampaignRepairStepResult:
+    used = (
+        invocations_used_count
+        if invocations_used_count is not None
+        else _safe_invocations_used(options)
+    )
+    return CampaignRepairStepResult(
+        result=result,
+        verdict=verdict,
+        repair_allowed=repair_allowed,
+        failure_class=failure_class,
+        failure_stage=failure_stage,
+        adopted=adopted,
+        convergence_reason=reason,
+        previous_basis=previous_basis,
+        round_index=options.round_index,
+        arch_norm=arch_norm,
+        verification_id=verification_id,
+        evidence_path=evidence_path,
+        reconciliation=reconciliation or _empty_reconciliation(),
+        warnings=warnings or [],
+        invocations_used=used,
+        error_code=error_code,
+    )
+
+
+def _error_outcome(
+    options: CampaignRepairStepOptions,
+    arch_norm: str,
+    error: _StepError,
+) -> CampaignRepairStepOutcome:
+    return CampaignRepairStepOutcome(
+        result=_result(
+            options,
+            arch_norm,
+            result="FAIL",
+            verdict="n_a",
+            repair_allowed=REPAIR_DENIED,
+            reason=error.reason,
+            error_code=error.code,
+        ),
+        exit_code=error.exit_code,
+    )
+
+
+def _safe_invocations_used(options: CampaignRepairStepOptions) -> int:
+    try:
+        return invocations_used(options.state_db, options.campaign_unit_key)
+    except Exception:
+        return 0
+
+
+def _read_edit_spec(path: Path) -> tuple[bytes, str]:
+    try:
+        real_path = Path(os.path.realpath(path))
+        raw = real_path.read_bytes()
+        value: Any = json.loads(raw)
+    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
+        raise _StepError(
+            REJECTED_IDENTITY_MISMATCH,
+            f"edit_spec is unreadable or invalid JSON: {exc}",
+            EXIT_REJECTED,
+        ) from exc
+    if not isinstance(value, dict):
+        raise _StepError(
+            REJECTED_IDENTITY_MISMATCH,
+            "edit_spec must be a JSON object",
+            EXIT_REJECTED,
+        )
+    return raw, hashlib.sha256(raw).hexdigest()
+
+
+def _materialize_canonical_edit_spec(path: Path, raw: bytes, digest: str) -> None:
+    path.parent.mkdir(parents=True, exist_ok=True)
+    if path.exists():
+        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
+            raise _StepError(
+                REJECTED_IDENTITY_MISMATCH,
+                f"canonical edit_spec conflicts with round output: {path}",
+                EXIT_REJECTED,
+            )
+        return
+    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
+    temporary.write_bytes(raw)
+    os.replace(temporary, path)
+
+
+def _revalidate_round(
+    options: CampaignRepairStepOptions,
+    canonical_edit_spec: Path,
+    edit_sha: str,
+) -> None:
+    round_row = get_round(options.state_db, options.campaign_unit_key, options.round_index)
+    if (
+        round_row is None
+        or round_row.edit_spec_sha256 != edit_sha
+        or round_row.edit_spec_ref != os.path.realpath(canonical_edit_spec)
+    ):
+        raise _StepError(
+            REJECTED_IDENTITY_MISMATCH,
+            "stored round identity does not match this invocation",
+            EXIT_REJECTED,
+        )
+
+
+def _load_config(path: Path, wall_timeout_override: int | None) -> _CampaignConfig:
+    try:
+        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
+    except (OSError, yaml.YAMLError) as exc:
+        raise _StepError(
+            "INVALID_ARGS",
+            f"campaign config is unreadable: {exc}",
+            EXIT_INVALID_ARGS,
+        ) from exc
+    if not isinstance(raw, Mapping):
+        raise _StepError("INVALID_ARGS", "campaign config must be a mapping", EXIT_INVALID_ARGS)
+    workspace = raw.get("campaign_workspace")
+    conf = raw.get("clang_conf_path")
+    if not isinstance(workspace, str) or not workspace or not isinstance(conf, str) or not conf:
+        raise _StepError(
+            "INVALID_ARGS",
+            "config requires campaign_workspace and clang_conf_path",
+            EXIT_INVALID_ARGS,
+        )
+    configured_timeout = raw.get("wall_timeout", 3600)
+    timeout = wall_timeout_override if wall_timeout_override is not None else configured_timeout
+    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
+        raise _StepError("INVALID_ARGS", "wall timeout must be positive", EXIT_INVALID_ARGS)
+    return _CampaignConfig(
+        campaign_workspace=Path(workspace).expanduser().resolve(),
+        clang_conf_path=Path(conf).expanduser().resolve(),
+        wall_timeout=timeout,
+    )
+
+
+@contextmanager
+def _repair_step_lock(workspace_root: Path) -> Iterator[None]:
+    workspace_root.mkdir(parents=True, exist_ok=True)
+    lock_path = workspace_root / ".repair_step.lock"
+    with lock_path.open("a+", encoding="utf-8") as stream:
+        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
+        try:
+            yield
+        finally:
+            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
+
+
+def _workspace_root(config: _CampaignConfig, unit_key: str, arch_norm: str) -> Path:
+    return config.campaign_workspace / _unit_hash(unit_key) / arch_norm
+
+
+def _unit_hash(unit_key: str) -> str:
+    return hashlib.sha256(unit_key.encode("utf-8")).hexdigest()[:12]
+
+
+def _failure_key(unit: Unit, arch_raw: str) -> str:
+    return build_failure_key(
+        ci_system=unit.ci_system,
+        build_id=unit.source_build_id,
+        project=unit.project,
+        branch=unit.branch,
+        arch=arch_raw,
+        spec_name=unit.spec_name,
+        base_commit=unit.base_commit,
+    )
+
+
+def _sha256_file(path: Path) -> str:
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+def _git_stdout(
+    cwd: Path,
+    args: list[str],
+    subprocess_runner: SubprocessRunner,
+) -> str:
+    completed = subprocess_runner(
+        ["git", "-C", str(cwd), *args],
+        check=True,
+        capture_output=True,
+        text=True,
+    )
+    return (completed.stdout or "").strip()
+
+
+def _normalize_project(remote: str) -> str:
+    value = remote.strip()
+    if "://" in value:
+        path = urlsplit(value).path
+    elif ":" in value and "@" in value.split(":", 1)[0]:
+        path = value.split(":", 1)[1]
+    else:
+        path = value
+    normalized = path.strip("/")
+    if normalized.startswith("git/"):
+        normalized = normalized[4:]
+    return normalized.removesuffix(".git")
+
+
+def _now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds")
diff --git a/tizen-ci-triage/scripts/ci_triage/campaign_state.py b/tizen-ci-triage/scripts/ci_triage/campaign_state.py
new file mode 100644
index 0000000..2ea57f6
--- /dev/null
+++ b/tizen-ci-triage/scripts/ci_triage/campaign_state.py
@@ -0,0 +1,2288 @@
+"""Append-only state primitives for clang fix campaigns.
+
+The campaign schema is additive: it is initialized after ``StateDatabase.connect``
+and never alters the existing verification, status, or submission tables.  The
+database remains a strong workflow constraint, not physical isolation from another
+process running as the same OS user.
+"""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import os
+import sqlite3
+import subprocess
+from collections.abc import Iterator, Mapping, Sequence
+from contextlib import contextmanager
+from dataclasses import dataclass
+from datetime import datetime, timezone
+from pathlib import Path, PurePosixPath
+from typing import Any
+
+from ci_triage.state import StateDatabase
+from ci_triage.verify.convergence import _error_count, _primary_fingerprint
+
+CAMPAIGN_SCHEMA_VERSION = "campaign/v1"
+HELD_FOR_INVESTIGATION = "HELD_FOR_INVESTIGATION"
+REJECTED_ARCH_NOT_ALLOWED = "REJECTED_ARCH_NOT_ALLOWED"
+
+ARCH_RAW_TO_NORM = {
+    "standard-aarch64": "aarch64",
+    "standard-armv7l": "armv7l",
+    "standard-x86_64": "x86_64",
+}
+ARCH_NORMS = frozenset(ARCH_RAW_TO_NORM.values())
+_FAILED_ARCH_ORDER = (
+    "standard-aarch64",
+    "standard-armv7l",
+    "standard-x86_64",
+    "emulator-x86_64",
+    "standard_gcov-armv7l",
+)
+
+_KNOWN_EVENT_TYPES = frozenset(
+    {
+        "REPRODUCE",
+        "BUILD_INVOCATION",
+        "ORPHAN_PASS",
+        "POLICY",
+        "DERIVE",
+        "PUSH",
+        "KB",
+        "REVIEW",
+        "CONVERGENCE",
+        "SECONDARY_TARGET_ADOPTED",
+        "WORKSPACE_CLEANUP",
+        "WORKSPACE_RELEASE",
+    }
+)
+_CONVERGENCE_NA_REASONS = frozenset(
+    {
+        "orphan_invocation",
+        "rebaselined",
+        "apply_failed",
+        "analyzer_failed",
+        "toolchain_failed",
+        "previous_evidence_missing",
+    }
+)
+_ARCH_SCOPED_HELD_REASONS = frozenset(
+    {
+        "previous_evidence_missing",
+        "orphan_pass",
+        "link_mismatch",
+        "verification_mismatch",
+    }
+)
+_IDENTITY_FIELDS = (
+    "ci_system",
+    "source_build_id",
+    "project",
+    "branch",
+    "spec_name",
+    "base_commit",
+)
+
+_SCHEMA_SQL = """
+CREATE TABLE IF NOT EXISTS campaign_units (
+  campaign_unit_key        TEXT PRIMARY KEY,
+  ci_system                TEXT NOT NULL,
+  source_build_id          TEXT NOT NULL,
+  project                  TEXT NOT NULL,
+  branch                   TEXT NOT NULL,
+  spec_name                TEXT NOT NULL,
+  base_commit              TEXT NOT NULL,
+  submission_identity_key  TEXT NOT NULL,
+  toolchain_profile        TEXT NOT NULL,
+  ci_evidence_ref          TEXT,
+  ci_evidence_sha256       TEXT,
+  primary_arch             TEXT,
+  max_rounds               INTEGER NOT NULL CHECK (max_rounds >= 1),
+  max_build_invocations    INTEGER NOT NULL CHECK (max_build_invocations >= 1),
+  failed_arches            TEXT NOT NULL,
+  created_at               TEXT NOT NULL,
+  schema_version           TEXT NOT NULL,
+  CHECK (
+    (primary_arch IS NULL AND ci_evidence_ref IS NULL
+      AND ci_evidence_sha256 IS NULL)
+    OR
+    (primary_arch IS NOT NULL AND ci_evidence_ref IS NOT NULL
+      AND ci_evidence_sha256 IS NOT NULL)
+  )
+);
+
+CREATE TABLE IF NOT EXISTS campaign_gate_events (
+  event_id            INTEGER PRIMARY KEY AUTOINCREMENT,
+  campaign_unit_key   TEXT NOT NULL,
+  round_index         INTEGER,
+  arch_norm           TEXT,
+  verdict             TEXT,
+  invocation_event_id INTEGER,
+  event_type          TEXT NOT NULL,
+  payload_json        TEXT NOT NULL,
+  created_at          TEXT NOT NULL,
+  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key)
+);
+CREATE UNIQUE INDEX IF NOT EXISTS ux_convergence_per_invocation
+  ON campaign_gate_events (invocation_event_id)
+  WHERE event_type = 'CONVERGENCE' AND invocation_event_id IS NOT NULL;
+CREATE INDEX IF NOT EXISTS ix_gate_unit_type
+  ON campaign_gate_events (campaign_unit_key, event_type, event_id);
+
+CREATE TABLE IF NOT EXISTS campaign_status_log (
+  log_id            INTEGER PRIMARY KEY AUTOINCREMENT,
+  campaign_unit_key TEXT NOT NULL,
+  status            TEXT NOT NULL,
+  reason            TEXT,
+  arch_norm         TEXT,
+  created_at        TEXT NOT NULL,
+  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key)
+);
+CREATE INDEX IF NOT EXISTS ix_status_unit
+  ON campaign_status_log (campaign_unit_key, log_id);
+
+CREATE TABLE IF NOT EXISTS campaign_rounds (
+  campaign_unit_key TEXT NOT NULL,
+  round_index       INTEGER NOT NULL CHECK (round_index >= 1),
+  edit_spec_ref     TEXT NOT NULL,
+  edit_spec_sha256  TEXT NOT NULL,
+  created_at        TEXT NOT NULL,
+  PRIMARY KEY (campaign_unit_key, round_index),
+  UNIQUE (campaign_unit_key, edit_spec_sha256),
+  UNIQUE (campaign_unit_key, round_index, edit_spec_sha256),
+  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key)
+);
+
+CREATE TABLE IF NOT EXISTS campaign_verifications (
+  link_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
+  campaign_unit_key       TEXT NOT NULL,
+  arch_raw                TEXT NOT NULL,
+  arch_norm               TEXT NOT NULL,
+  verification_id         TEXT NOT NULL UNIQUE,
+  round_index             INTEGER NOT NULL,
+  edit_spec_sha256        TEXT NOT NULL,
+  campaign_schema_version TEXT NOT NULL,
+  created_at              TEXT NOT NULL,
+  UNIQUE (campaign_unit_key, arch_norm, round_index),
+  FOREIGN KEY (campaign_unit_key, round_index, edit_spec_sha256)
+    REFERENCES campaign_rounds (campaign_unit_key, round_index, edit_spec_sha256),
+  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key),
+  FOREIGN KEY (verification_id) REFERENCES verification_records (verification_id)
+);
+
+CREATE TABLE IF NOT EXISTS campaign_qb_requests (
+  request_seq       INTEGER PRIMARY KEY AUTOINCREMENT,
+  request_id        TEXT NOT NULL UNIQUE,
+  campaign_unit_key TEXT NOT NULL,
+  sbs_target        TEXT NOT NULL,
+  created_at        TEXT NOT NULL,
+  FOREIGN KEY (campaign_unit_key) REFERENCES campaign_units (campaign_unit_key)
+);
+CREATE INDEX IF NOT EXISTS ix_qb_req_unit
+  ON campaign_qb_requests (campaign_unit_key, request_seq);
+
+CREATE TABLE IF NOT EXISTS campaign_qb_events (
+  event_id              INTEGER PRIMARY KEY AUTOINCREMENT,
+  request_seq           INTEGER NOT NULL,
+  event_type            TEXT NOT NULL
+                        CHECK (event_type IN ('SUBMITTED','BUILD_BOUND','RESULT')),
+  qb_build_id           TEXT,
+  status                TEXT,
+  accepted              INTEGER,
+  sbs_target_echo       TEXT,
+  per_arch_status_json  TEXT,
+  qb_result_sha256      TEXT,
+  qb_result_ref         TEXT,
+  degraded              INTEGER NOT NULL DEFAULT 0,
+  created_at            TEXT NOT NULL,
+  FOREIGN KEY (request_seq) REFERENCES campaign_qb_requests (request_seq)
+);
+CREATE INDEX IF NOT EXISTS ix_qb_ev_req
+  ON campaign_qb_events (request_seq, event_id);
+CREATE INDEX IF NOT EXISTS ix_qb_ev_build
+  ON campaign_qb_events (qb_build_id);
+"""
+
+
+class CampaignStateError(RuntimeError):
+    """Base class for campaign-state contract failures."""
+
+
+class StateInconsistent(CampaignStateError):
+    """Stored state conflicts with the requested append-only transition."""
+
+
+class PayloadSchemaError(CampaignStateError, ValueError):
+    """A gate event payload does not satisfy its frozen schema."""
+
+
+class UnknownEventType(PayloadSchemaError):
+    """A caller attempted to write an unregistered gate event type."""
+
+
+class RoundsExhausted(CampaignStateError):
+    """The unit has consumed its edit-spec round budget."""
+
+
+class BudgetExhausted(CampaignStateError):
+    """The unit has consumed its build invocation budget."""
+
+
+class CampaignStateBusy(CampaignStateError):
+    """SQLite could not acquire the required immediate write lock."""
+
+
+@dataclass(frozen=True)
+class Unit:
+    campaign_unit_key: str
+    ci_system: str
+    source_build_id: str
+    project: str
+    branch: str
+    spec_name: str
+    base_commit: str
+    submission_identity_key: str
+    toolchain_profile: str
+    ci_evidence_ref: str | None
+    ci_evidence_sha256: str | None
+    primary_arch: str | None
+    max_rounds: int
+    max_build_invocations: int
+    failed_arches: tuple[str, ...]
+    created_at: str
+    schema_version: str
+
+
+@dataclass(frozen=True)
+class Round:
+    campaign_unit_key: str
+    round_index: int
+    edit_spec_ref: str
+    edit_spec_sha256: str
+    created_at: str
+
+
+@dataclass(frozen=True)
+class InvocationReceipt:
+    event_id: int
+    invocations_used: int
+    invocations_remaining: int
+
+
+@dataclass(frozen=True)
+class ReconcileResult:
+    branch: str
+    current_verification_id: str | None
+    current_relinked_invocation_event_id: int | None
+    other_round_relinks: tuple[tuple[int, str, int], ...]
+    backfilled_invocation_event_ids: tuple[int, ...]
+    orphan_pass_verification_ids: tuple[str, ...]
+    held_rounds: tuple[int, ...]
+    non_campaign_verification_ids: tuple[str, ...]
+
+
+def ensure_schema(state_db: StateDatabase) -> None:
+    """Create all seven additive campaign tables and their indexes."""
+
+    conn = state_db.connect()
+    try:
+        _ensure_schema_on_connection(conn)
+    finally:
+        conn.close()
+
+
+def create_unit(
+    state_db: StateDatabase,
+    *,
+    campaign_unit_key: str,
+    submission_identity_key: str,
+    primary_arch: str,
+    failed_arches: Sequence[str],
+    toolchain_profile: str,
+    ci_evidence_ref: str,
+    ci_evidence_sha256: str,
+    max_rounds: int,
+    max_build_invocations: int,
+    **identity_fields: str,
+) -> None:
+    """Insert one normal campaign unit, or no-op on an exact retry."""
+
+    if not primary_arch or primary_arch not in ARCH_RAW_TO_NORM:
+        raise ValueError("primary_arch must be one of the verified standard arches")
+    if not ci_evidence_ref or not ci_evidence_sha256:
+        raise ValueError("create_unit requires non-empty CI evidence fields")
+    values = _unit_values(
+        campaign_unit_key=campaign_unit_key,
+        submission_identity_key=submission_identity_key,
+        primary_arch=primary_arch,
+        failed_arches=failed_arches,
+        toolchain_profile=toolchain_profile,
+        ci_evidence_ref=ci_evidence_ref,
+        ci_evidence_sha256=ci_evidence_sha256,
+        max_rounds=max_rounds,
+        max_build_invocations=max_build_invocations,
+        identity_fields=identity_fields,
+    )
+    conn = _connect(state_db)
+    try:
+        with _immediate_transaction(conn):
+            _insert_or_compare_unit(conn, values)
+    finally:
+        conn.close()
+
+
+def create_arch_rejected_unit(
+    state_db: StateDatabase,
+    *,
+    campaign_unit_key: str,
+    submission_identity_key: str,
+    failed_arches: Sequence[str],
+    reason: str,
+    toolchain_profile: str,
+    max_rounds: int,
+    max_build_invocations: int,
+    **identity_fields: str,
+) -> None:
+    """Atomically insert an arch-rejected unit and its terminal status."""
+
+    if not reason:
+        raise ValueError("arch rejection reason must be non-empty")
+    values = _unit_values(
+        campaign_unit_key=campaign_unit_key,
+        submission_identity_key=submission_identity_key,
+        primary_arch=None,
+        failed_arches=failed_arches,
+        toolchain_profile=toolchain_profile,
+        ci_evidence_ref=None,
+        ci_evidence_sha256=None,
+        max_rounds=max_rounds,
+        max_build_invocations=max_build_invocations,
+        identity_fields=identity_fields,
+    )
+    conn = _connect(state_db)
+    try:
+        with _immediate_transaction(conn):
+            inserted = _insert_or_compare_unit(conn, values)
+            existing = conn.execute(
+                "SELECT status, reason, arch_norm FROM campaign_status_log "
+                "WHERE campaign_unit_key = ? ORDER BY log_id DESC LIMIT 1",
+                (campaign_unit_key,),
+            ).fetchone()
+            if existing is None:
+                _insert_status_row(
+                    conn,
+                    campaign_unit_key,
+                    REJECTED_ARCH_NOT_ALLOWED,
+                    reason,
+                    None,
+                )
+            elif (
+                _text(existing, "status") != REJECTED_ARCH_NOT_ALLOWED
+                or _optional_text(existing, "reason") != reason
+                or existing["arch_norm"] is not None
+            ):
+                raise StateInconsistent("arch-rejected unit has a conflicting latest status")
+            elif inserted:
+                raise StateInconsistent("new arch-rejected unit unexpectedly had a status row")
+    finally:
+        conn.close()
+
+
+def get_unit(state_db: StateDatabase, campaign_unit_key: str) -> Unit | None:
+    conn = _connect(state_db)
+    try:
+        row = conn.execute(
+            "SELECT * FROM campaign_units WHERE campaign_unit_key = ?",
+            (campaign_unit_key,),
+        ).fetchone()
+    finally:
+        conn.close()
+    return _unit_from_row(row) if row is not None else None
+
+
+def append_event(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    event_type: str,
+    payload: Mapping[str, object],
+) -> int:
+    """Validate and append one gate event.
+
+    Budget events and secondary-target adoption have stronger transactional APIs
+    and cannot be written through this general entry point.
+    """
+
+    if event_type == "BUILD_INVOCATION":
+        raise PayloadSchemaError("BUILD_INVOCATION must be written by consume_build_invocation")
+    if event_type == "SECONDARY_TARGET_ADOPTED":
+        raise PayloadSchemaError(
+            "SECONDARY_TARGET_ADOPTED must be written by the atomic adoption API"
+        )
+    conn = _connect(state_db)
+    try:
+        with _immediate_transaction(conn):
+            return _append_event_on_connection(conn, campaign_unit_key, event_type, payload)
+    finally:
+        conn.close()
+
+
+def latest_event(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    event_type: str,
+) -> dict[str, object] | None:
+    _require_known_event_type(event_type)
+    conn = _connect(state_db)
+    try:
+        row = conn.execute(
+            "SELECT * FROM campaign_gate_events "
+            "WHERE campaign_unit_key = ? AND event_type = ? "
+            "ORDER BY event_id DESC LIMIT 1",
+            (campaign_unit_key, event_type),
+        ).fetchone()
+    finally:
+        conn.close()
+    return _event_from_row(row) if row is not None else None
+
+
+def latest_reproduce(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    *,
+    arch_norm: str,
+) -> dict[str, object] | None:
+    _require_arch_norm(arch_norm)
+    conn = _connect(state_db)
+    try:
+        row = conn.execute(
+            "SELECT * FROM campaign_gate_events "
+            "WHERE campaign_unit_key = ? AND event_type = 'REPRODUCE' "
+            "AND arch_norm = ? ORDER BY event_id DESC LIMIT 1",
+            (campaign_unit_key, arch_norm),
+        ).fetchone()
+    finally:
+        conn.close()
+    return _event_from_row(row) if row is not None else None
+
+
+def adopt_secondary_target_with_convergence(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    *,
+    arch_norm: str,
+    expected_reproduce_event_id: int,
+    convergence_payload: Mapping[str, object],
+) -> bool:
+    """Atomically consume one secondary-target adoption and write convergence."""
+
+    _require_arch_norm(arch_norm)
+    _require_equal(convergence_payload, "arch_norm", arch_norm)
+    _require_equal(convergence_payload, "result", "FAIL")
+    _require_equal(convergence_payload, "verdict", "stalled")
+    conn = _connect(state_db)
+    try:
+        with _immediate_transaction(conn):
+            _require_unit(conn, campaign_unit_key)
+            existing = conn.execute(
+                "SELECT 1 FROM campaign_gate_events "
+                "WHERE campaign_unit_key = ? AND event_type = 'SECONDARY_TARGET_ADOPTED' "
+                "AND arch_norm = ? LIMIT 1",
+                (campaign_unit_key, arch_norm),
+            ).fetchone()
+            if existing is not None:
+                return False
+            reproduce = conn.execute(
+                "SELECT * FROM campaign_gate_events "
+                "WHERE campaign_unit_key = ? AND event_type = 'REPRODUCE' "
+                "AND arch_norm = ? ORDER BY event_id DESC LIMIT 1",
+                (campaign_unit_key, arch_norm),
+            ).fetchone()
+            if reproduce is None or int(reproduce["event_id"]) != expected_reproduce_event_id:
+                return False
+            reproduce_payload = _payload_from_row(reproduce)
+            if reproduce_payload.get("outcome") != "different_failure":
+                return False
+
+            current = _load_bound_evidence(
+                convergence_payload.get("evidence_path"),
+                convergence_payload.get("evidence_sha256"),
+            )
+            baseline = _load_bound_evidence(
+                reproduce_payload.get("evidence_local"),
+                reproduce_payload.get("evidence_sha256"),
+            )
+            if current is None or baseline is None:
+                return False
+            current_truncated = _evidence_truncated(current)
+            baseline_truncated = _evidence_truncated(baseline)
+            if current_truncated or baseline_truncated:
+                return False
+            current_fingerprint = _primary_fingerprint(current, touched_files=None)
+            baseline_fingerprint = _primary_fingerprint(baseline, touched_files=None)
+            if current_fingerprint is None or current_fingerprint != baseline_fingerprint:
+                return False
+            current_count = _error_count(current)
+            baseline_count = _error_count(baseline)
+            if current_count != baseline_count:
+                return False
+
+            revised_convergence = dict(convergence_payload)
+            revised_convergence["verdict"] = "advance"
+            _validate_event_payload(
+                conn,
+                campaign_unit_key,
+                "CONVERGENCE",
+                revised_convergence,
+            )
+            adoption_payload: dict[str, object] = {
+                "arch_norm": arch_norm,
+                "adopted_fingerprint": current_fingerprint.to_dict(),
+                "baseline_error_count": baseline_count,
+                "current_error_count": current_count,
+                "baseline_truncated": False,
+                "current_truncated": False,
+                "expected_reproduce_event_id": expected_reproduce_event_id,
+                "at": _now_iso8601(),
+            }
+            _validate_event_payload(
+                conn,
+                campaign_unit_key,
+                "SECONDARY_TARGET_ADOPTED",
+                adoption_payload,
+            )
+            _insert_event_row(
+                conn,
+                campaign_unit_key,
+                "SECONDARY_TARGET_ADOPTED",
+                adoption_payload,
+            )
+            _insert_event_row(
+                conn,
+                campaign_unit_key,
+                "CONVERGENCE",
+                revised_convergence,
+            )
+            return True
+    finally:
+        conn.close()
+
+
+def find_unlinked_pass(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    *,
+    arch_norm: str,
+    failure_key: str,
+) -> list[dict[str, str]]:
+    """Return every matching unlinked PASS; callers must not choose ambiguities."""
+
+    _require_arch_norm(arch_norm)
+    conn = _connect(state_db)
+    try:
+        _require_unit(conn, campaign_unit_key)
+        rows = conn.execute(
+            "SELECT vr.* FROM verification_records AS vr "
+            "LEFT JOIN campaign_verifications AS cv "
+            "ON cv.verification_id = vr.verification_id "
+            "WHERE vr.failure_key = ? AND cv.verification_id IS NULL "
+            "ORDER BY vr.timestamp, vr.verification_id",
+            (failure_key,),
+        ).fetchall()
+    finally:
+        conn.close()
+    return [
+        {key: str(row[key]) for key in row.keys()}
+        for row in rows
+        if _normalize_arch_raw(str(row["arch"])) == arch_norm
+    ]
+
+
+def append_status(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    status: str,
+    reason: str | None = None,
+    arch_norm: str | None = None,
+) -> None:
+    if not status:
+        raise PayloadSchemaError("status must be non-empty")
+    if arch_norm is not None:
+        _require_arch_norm(arch_norm)
+    if (
+        status == HELD_FOR_INVESTIGATION
+        and reason in _ARCH_SCOPED_HELD_REASONS
+        and arch_norm is None
+    ):
+        raise PayloadSchemaError(f"HELD reason {reason!r} requires arch_norm")
+    conn = _connect(state_db)
+    try:
+        with _immediate_transaction(conn):
+            _require_unit(conn, campaign_unit_key)
+            _insert_status_row(conn, campaign_unit_key, status, reason, arch_norm)
+    finally:
+        conn.close()
+
+
+def latest_status(state_db: StateDatabase, campaign_unit_key: str) -> str | None:
+    conn = _connect(state_db)
+    try:
+        row = conn.execute(
+            "SELECT status FROM campaign_status_log WHERE campaign_unit_key = ? "
+            "ORDER BY log_id DESC LIMIT 1",
+            (campaign_unit_key,),
+        ).fetchone()
+    finally:
+        conn.close()
+    return _text(row, "status") if row is not None else None
+
+
+def is_rebaseline_authorized(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    *,
+    arch_norm: str,
+) -> bool:
+    """Return whether the latest status authorizes rebaseline for this arch.
+
+    Authorization is deliberately narrow: only the exact HELD transition written
+    for a missing previous-evidence binding may reopen the architecture.
+    """
+
+    _require_arch_norm(arch_norm)
+    conn = _connect(state_db)
+    try:
+        row = conn.execute(
+            "SELECT status, reason, arch_norm FROM campaign_status_log "
+            "WHERE campaign_unit_key = ? ORDER BY log_id DESC LIMIT 1",
+            (campaign_unit_key,),
+        ).fetchone()
+    finally:
+        conn.close()
+    return bool(
+        row is not None
+        and _text(row, "status") == HELD_FOR_INVESTIGATION
+        and _optional_text(row, "reason") == "previous_evidence_missing"
+        and _optional_text(row, "arch_norm") == arch_norm
+    )
+
+
+def create_round(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    *,
+    round_index: int,
+    edit_spec_ref: str,
+    edit_spec_sha256: str,
+) -> None:
+    normalized_ref = os.path.realpath(edit_spec_ref)
+    if round_index < 1 or not edit_spec_sha256 or not normalized_ref:
+        raise ValueError("round_index, edit_spec_ref, and edit_spec_sha256 are required")
+    conn = _connect(state_db)
+    try:
+        with _immediate_transaction(conn):
+            unit = _require_unit(conn, campaign_unit_key)
+            exact = conn.execute(
+                "SELECT 1 FROM campaign_rounds WHERE campaign_unit_key = ? "
+                "AND round_index = ? AND edit_spec_sha256 = ? AND edit_spec_ref = ?",
+                (campaign_unit_key, round_index, edit_spec_sha256, normalized_ref),
+            ).fetchone()
+            if exact is not None:
+                return
+            conflict = conn.execute(
+                "SELECT round_index, edit_spec_ref, edit_spec_sha256 "
+                "FROM campaign_rounds WHERE campaign_unit_key = ? "
+                "AND (round_index = ? OR edit_spec_sha256 = ?)",
+                (campaign_unit_key, round_index, edit_spec_sha256),
+            ).fetchone()
+            if conflict is not None:
+                raise StateInconsistent("round identity conflicts with append-only state")
+            count_row = conn.execute(
+                "SELECT COUNT(*) AS count, MAX(round_index) AS max_round "
+                "FROM campaign_rounds WHERE campaign_unit_key = ?",
+                (campaign_unit_key,),
+            ).fetchone()
+            if count_row is None:
+                raise StateInconsistent("round count query returned no row")
+            count = int(count_row["count"])
+            if count >= unit.max_rounds:
+                raise RoundsExhausted("campaign round budget exhausted")
+            max_round = count_row["max_round"]
+            expected = 1 if max_round is None else int(max_round) + 1
+            if round_index != expected:
+                raise StateInconsistent(f"new round_index must be {expected}, got {round_index}")
+            conn.execute(
+                "INSERT INTO campaign_rounds "
+                "(campaign_unit_key, round_index, edit_spec_ref, edit_spec_sha256, created_at) "
+                "VALUES (?, ?, ?, ?, ?)",
+                (
+                    campaign_unit_key,
+                    round_index,
+                    normalized_ref,
+                    edit_spec_sha256,
+                    _now_iso8601(),
+                ),
+            )
+    finally:
+        conn.close()
+
+
+def get_round(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    round_index: int,
+) -> Round | None:
+    conn = _connect(state_db)
+    try:
+        row = conn.execute(
+            "SELECT * FROM campaign_rounds WHERE campaign_unit_key = ? AND round_index = ?",
+            (campaign_unit_key, round_index),
+        ).fetchone()
+    finally:
+        conn.close()
+    return _round_from_row(row) if row is not None else None
+
+
+def latest_round(state_db: StateDatabase, campaign_unit_key: str) -> Round | None:
+    conn = _connect(state_db)
+    try:
+        row = conn.execute(
+            "SELECT * FROM campaign_rounds WHERE campaign_unit_key = ? "
+            "ORDER BY round_index DESC LIMIT 1",
+            (campaign_unit_key,),
+        ).fetchone()
+    finally:
+        conn.close()
+    return _round_from_row(row) if row is not None else None
+
+
+def invocations_used(state_db: StateDatabase, campaign_unit_key: str) -> int:
+    conn = _connect(state_db)
+    try:
+        row = conn.execute(
+            "SELECT COUNT(*) AS count FROM campaign_gate_events "
+            "WHERE campaign_unit_key = ? AND event_type = 'BUILD_INVOCATION'",
+            (campaign_unit_key,),
+        ).fetchone()
+    finally:
+        conn.close()
+    return int(row["count"]) if row is not None else 0
+
+
+def consume_build_invocation(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    *,
+    round_index: int,
+    arch_norm: str,
+) -> InvocationReceipt:
+    _require_arch_norm(arch_norm)
+    conn = _connect(state_db)
+    try:
+        with _immediate_transaction(conn):
+            unit = _require_unit(conn, campaign_unit_key)
+            if _round_on_connection(conn, campaign_unit_key, round_index) is None:
+                raise StateInconsistent("build invocation references a missing round")
+            row = conn.execute(
+                "SELECT COUNT(*) AS count FROM campaign_gate_events "
+                "WHERE campaign_unit_key = ? AND event_type = 'BUILD_INVOCATION'",
+                (campaign_unit_key,),
+            ).fetchone()
+            used = int(row["count"]) if row is not None else 0
+            if used >= unit.max_build_invocations:
+                raise BudgetExhausted("campaign build invocation budget exhausted")
+            event_id = _insert_event_row(
+                conn,
+                campaign_unit_key,
+                "BUILD_INVOCATION",
+                {"round_index": round_index, "arch_norm": arch_norm},
+            )
+            used += 1
+            return InvocationReceipt(
+                event_id=event_id,
+                invocations_used=used,
+                invocations_remaining=unit.max_build_invocations - used,
+            )
+    finally:
+        conn.close()
+
+
+def link_verification_with_convergence(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    *,
+    convergence_payload: Mapping[str, object],
+    arch_raw: str,
+    arch_norm: str,
+    verification_id: str,
+    round_index: int,
+    edit_spec_sha256: str,
+) -> None:
+    """Atomically link one PASS record and its PASS convergence event."""
+    conn = _connect(state_db)
+    try:
+        with _immediate_transaction(conn):
+            _link_verification_with_convergence_on_connection(
+                conn,
+                campaign_unit_key,
+                convergence_payload=convergence_payload,
+                arch_raw=arch_raw,
+                arch_norm=arch_norm,
+                verification_id=verification_id,
+                round_index=round_index,
+                edit_spec_sha256=edit_spec_sha256,
+            )
+    except sqlite3.IntegrityError as exc:
+        raise StateInconsistent(f"verification link violated campaign constraints: {exc}") from exc
+    finally:
+        conn.close()
+
+
+def reconcile_pass_and_invocations(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    *,
+    round_index: int,
+    arch_norm: str,
+    failure_key: str,
+    edit_spec_sha256: str,
+) -> ReconcileResult:
+    """Reconcile interrupted PASS records and invocation outcomes in one transaction."""
+
+    _require_arch_norm(arch_norm)
+    if round_index < 1 or not failure_key or not edit_spec_sha256:
+        raise ValueError("round_index, failure_key, and edit_spec_sha256 are required")
+    conn = _connect(state_db)
+    try:
+        with _immediate_transaction(conn):
+            unit = _require_unit(conn, campaign_unit_key)
+
+            # a0 is deliberately the first state classification. A half-state must
+            # not be disguised later as an ordinary orphan invocation.
+            if not _linked_pass_convergence_is_complete(
+                conn,
+                campaign_unit_key,
+                arch_norm,
+            ):
+                _insert_status_row(
+                    conn,
+                    campaign_unit_key,
+                    HELD_FOR_INVESTIGATION,
+                    "state_inconsistent",
+                    arch_norm,
+                )
+                return _empty_reconcile_result("state_inconsistent_held")
+
+            current_round = _round_on_connection(conn, campaign_unit_key, round_index)
+            if current_round is None or current_round.edit_spec_sha256 != edit_spec_sha256:
+                raise StateInconsistent("reconciliation input does not match the campaign round")
+
+            try:
+                current_link = _current_link_for_edit_spec(
+                    conn,
+                    campaign_unit_key,
+                    arch_norm,
+                    edit_spec_sha256,
+                )
+            except StateInconsistent:
+                _insert_status_row(
+                    conn,
+                    campaign_unit_key,
+                    HELD_FOR_INVESTIGATION,
+                    "state_inconsistent",
+                    arch_norm,
+                )
+                return _empty_reconcile_result("state_inconsistent_held")
+            attributed, non_campaign, attribution_is_inconsistent = _attributed_unlinked_passes(
+                conn,
+                campaign_unit_key,
+                arch_norm=arch_norm,
+                failure_key=failure_key,
+            )
+            if attribution_is_inconsistent:
+                _insert_status_row(
+                    conn,
+                    campaign_unit_key,
+                    HELD_FOR_INVESTIGATION,
+                    "state_inconsistent",
+                    arch_norm,
+                )
+                return _empty_reconcile_result(
+                    "state_inconsistent_held",
+                    non_campaign_verification_ids=non_campaign,
+                )
+
+            orphan_invocations = _orphan_invocations_by_round(
+                conn,
+                campaign_unit_key,
+                arch_norm,
+            )
+            relinks: list[tuple[int, str, int]] = []
+            orphan_pass_ids: list[str] = []
+            held_rounds: list[int] = []
+            frozen_rounds: set[int] = set()
+
+            for candidate_round in sorted(attributed):
+                records = attributed[candidate_round]
+                invocations = orphan_invocations.get(candidate_round, [])
+                if len(records) == 1 and len(invocations) == 1:
+                    record = records[0]
+                    invocation_event_id = invocations[0]
+                    rebuilt, reason = _rebuild_pass_convergence(
+                        unit,
+                        record,
+                        round_index=candidate_round,
+                        arch_norm=arch_norm,
+                        invocation_event_id=invocation_event_id,
+                    )
+                    if rebuilt is not None:
+                        try:
+                            with _savepoint(conn, "reconcile_link"):
+                                _link_verification_with_convergence_on_connection(
+                                    conn,
+                                    campaign_unit_key,
+                                    convergence_payload=rebuilt,
+                                    arch_raw=_text(record, "arch"),
+                                    arch_norm=arch_norm,
+                                    verification_id=_text(record, "verification_id"),
+                                    round_index=candidate_round,
+                                    edit_spec_sha256=_text(record, "edit_spec_sha256"),
+                                )
+                        except (CampaignStateError, sqlite3.IntegrityError):
+                            reason = "link_failed"
+                        else:
+                            relinks.append(
+                                (
+                                    candidate_round,
+                                    _text(record, "verification_id"),
+                                    invocation_event_id,
+                                )
+                            )
+                            continue
+                    _record_orphan_passes(
+                        conn,
+                        campaign_unit_key,
+                        candidate_round,
+                        arch_norm,
+                        records,
+                        reason or "ambiguous",
+                    )
+                else:
+                    _record_orphan_passes(
+                        conn,
+                        campaign_unit_key,
+                        candidate_round,
+                        arch_norm,
+                        records,
+                        "ambiguous",
+                    )
+                orphan_pass_ids.extend(_text(record, "verification_id") for record in records)
+                held_rounds.append(candidate_round)
+                frozen_rounds.add(candidate_round)
+
+            backfilled: list[int] = []
+            all_rounds = sorted(set(orphan_invocations) | set(attributed))
+            for candidate_round in all_rounds:
+                if attributed.get(candidate_round) or candidate_round in frozen_rounds:
+                    continue
+                for invocation_event_id in orphan_invocations.get(candidate_round, []):
+                    _append_event_on_connection(
+                        conn,
+                        campaign_unit_key,
+                        "CONVERGENCE",
+                        _orphan_invocation_payload(
+                            round_index=candidate_round,
+                            arch_norm=arch_norm,
+                            invocation_event_id=invocation_event_id,
+                        ),
+                    )
+                    backfilled.append(invocation_event_id)
+
+            if orphan_pass_ids:
+                _insert_status_row(
+                    conn,
+                    campaign_unit_key,
+                    HELD_FOR_INVESTIGATION,
+                    "orphan_pass",
+                    arch_norm,
+                )
+
+            current_relink = next(
+                (item for item in relinks if item[0] == round_index),
+                None,
+            )
+            if orphan_pass_ids:
+                branch = "orphan_pass_held"
+                current_verification_id = None
+                current_invocation_event_id = None
+            elif current_link is not None:
+                branch = "linked_already"
+                current_verification_id = _text(current_link, "verification_id")
+                current_invocation_event_id = None
+            elif current_relink is not None:
+                branch = "relinked"
+                current_verification_id = current_relink[1]
+                current_invocation_event_id = current_relink[2]
+            else:
+                branch = "proceed"
+                current_verification_id = None
+                current_invocation_event_id = None
+
+            other_round_relinks = tuple(item for item in sorted(relinks) if item[0] != round_index)
+            return ReconcileResult(
+                branch=branch,
+                current_verification_id=current_verification_id,
+                current_relinked_invocation_event_id=current_invocation_event_id,
+                other_round_relinks=other_round_relinks,
+                backfilled_invocation_event_ids=tuple(sorted(backfilled)),
+                orphan_pass_verification_ids=tuple(sorted(orphan_pass_ids)),
+                held_rounds=tuple(sorted(set(held_rounds))),
+                non_campaign_verification_ids=tuple(sorted(non_campaign)),
+            )
+    finally:
+        conn.close()
+
+
+def _link_verification_with_convergence_on_connection(
+    conn: sqlite3.Connection,
+    campaign_unit_key: str,
+    *,
+    convergence_payload: Mapping[str, object],
+    arch_raw: str,
+    arch_norm: str,
+    verification_id: str,
+    round_index: int,
+    edit_spec_sha256: str,
+) -> None:
+    """Transaction-internal primitive shared by normal PASS and reconciliation."""
+
+    _require_arch_norm(arch_norm)
+    if _normalize_arch_raw(arch_raw) != arch_norm:
+        raise StateInconsistent("arch_raw and arch_norm do not match")
+    _require_equal(convergence_payload, "round_index", round_index)
+    _require_equal(convergence_payload, "arch_norm", arch_norm)
+    _require_equal(convergence_payload, "verification_id", verification_id)
+    _require_equal(convergence_payload, "result", "PASS")
+    _require_equal(convergence_payload, "verdict", "n_a")
+    if convergence_payload.get("evidence_path") is not None:
+        raise StateInconsistent("PASS convergence evidence_path must be null")
+    if convergence_payload.get("evidence_sha256") is not None:
+        raise StateInconsistent("PASS convergence evidence_sha256 must be null")
+
+    _require_unit(conn, campaign_unit_key)
+    round_row = _round_on_connection(conn, campaign_unit_key, round_index)
+    if round_row is None or round_row.edit_spec_sha256 != edit_spec_sha256:
+        raise StateInconsistent("verification link does not match the campaign round")
+    record = conn.execute(
+        "SELECT result, edit_spec_sha256, arch FROM verification_records WHERE verification_id = ?",
+        (verification_id,),
+    ).fetchone()
+    if record is None:
+        raise StateInconsistent("verification record not found")
+    if _text(record, "result") != "PASS":
+        raise StateInconsistent("verification record is not PASS")
+    if _text(record, "edit_spec_sha256") != edit_spec_sha256:
+        raise StateInconsistent("verification edit_spec hash mismatch")
+    if _normalize_arch_raw(_text(record, "arch")) != arch_norm:
+        raise StateInconsistent("verification arch mismatch")
+    _validate_event_payload(
+        conn,
+        campaign_unit_key,
+        "CONVERGENCE",
+        convergence_payload,
+    )
+    conn.execute(
+        "INSERT INTO campaign_verifications "
+        "(campaign_unit_key, arch_raw, arch_norm, verification_id, round_index, "
+        "edit_spec_sha256, campaign_schema_version, created_at) "
+        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
+        (
+            campaign_unit_key,
+            arch_raw,
+            arch_norm,
+            verification_id,
+            round_index,
+            edit_spec_sha256,
+            CAMPAIGN_SCHEMA_VERSION,
+            _now_iso8601(),
+        ),
+    )
+    _insert_event_row(
+        conn,
+        campaign_unit_key,
+        "CONVERGENCE",
+        convergence_payload,
+    )
+
+
+def _linked_pass_convergence_is_complete(
+    conn: sqlite3.Connection,
+    campaign_unit_key: str,
+    arch_norm: str,
+) -> bool:
+    links = conn.execute(
+        "SELECT * FROM campaign_verifications "
+        "WHERE campaign_unit_key = ? AND arch_norm = ? ORDER BY link_id",
+        (campaign_unit_key, arch_norm),
+    ).fetchall()
+    if not links:
+        return True
+    convergence_rows = conn.execute(
+        "SELECT * FROM campaign_gate_events WHERE event_type = 'CONVERGENCE' ORDER BY event_id"
+    ).fetchall()
+    parsed: list[tuple[sqlite3.Row, dict[str, object]]] = []
+    for row in convergence_rows:
+        try:
+            payload = _payload_from_row(row)
+        except (json.JSONDecodeError, StateInconsistent):
+            return False
+        parsed.append((row, payload))
+
+    for link in links:
+        verification_id = _text(link, "verification_id")
+        matches = [
+            (row, payload)
+            for row, payload in parsed
+            if payload.get("verification_id") == verification_id
+        ]
+        if len(matches) != 1:
+            return False
+        row, payload = matches[0]
+        if (
+            _text(row, "campaign_unit_key") != campaign_unit_key
+            or row["round_index"] != link["round_index"]
+            or row["arch_norm"] != arch_norm
+            or row["verdict"] != "n_a"
+            or row["invocation_event_id"] != payload.get("invocation_event_id")
+            or payload.get("round_index") != link["round_index"]
+            or payload.get("arch_norm") != arch_norm
+            or payload.get("verification_id") != verification_id
+            or payload.get("result") != "PASS"
+            or payload.get("verdict") != "n_a"
+        ):
+            return False
+        try:
+            _validate_invocation_binding(conn, campaign_unit_key, payload)
+        except CampaignStateError:
+            return False
+    return True
+
+
+def _current_link_for_edit_spec(
+    conn: sqlite3.Connection,
+    campaign_unit_key: str,
+    arch_norm: str,
+    edit_spec_sha256: str,
+) -> sqlite3.Row | None:
+    rows = conn.execute(
+        "SELECT * FROM campaign_verifications WHERE campaign_unit_key = ? "
+        "AND arch_norm = ? AND edit_spec_sha256 = ? ORDER BY link_id",
+        (campaign_unit_key, arch_norm, edit_spec_sha256),
+    ).fetchall()
+    if len(rows) > 1:
+        raise StateInconsistent("multiple current verification links exist")
+    return rows[0] if rows else None
+
+
+def _attributed_unlinked_passes(
+    conn: sqlite3.Connection,
+    campaign_unit_key: str,
+    *,
+    arch_norm: str,
+    failure_key: str,
+) -> tuple[dict[int, list[sqlite3.Row]], tuple[str, ...], bool]:
+    rows = conn.execute(
+        "SELECT vr.* FROM verification_records AS vr "
+        "LEFT JOIN campaign_verifications AS cv "
+        "ON cv.verification_id = vr.verification_id "
+        "WHERE vr.failure_key = ? AND cv.verification_id IS NULL "
+        "ORDER BY vr.timestamp, vr.verification_id",
+        (failure_key,),
+    ).fetchall()
+    attributed: dict[int, list[sqlite3.Row]] = {}
+    non_campaign: list[str] = []
+    for record in rows:
+        if _normalize_arch_raw(_text(record, "arch")) != arch_norm:
+            continue
+        matches = conn.execute(
+            "SELECT round_index FROM campaign_rounds "
+            "WHERE campaign_unit_key = ? AND edit_spec_sha256 = ? "
+            "ORDER BY round_index",
+            (campaign_unit_key, _text(record, "edit_spec_sha256")),
+        ).fetchall()
+        if not matches:
+            non_campaign.append(_text(record, "verification_id"))
+            continue
+        if len(matches) > 1:
+            return attributed, tuple(sorted(non_campaign)), True
+        candidate_round = int(matches[0]["round_index"])
+        attributed.setdefault(candidate_round, []).append(record)
+    return attributed, tuple(sorted(non_campaign)), False
+
+
+def _orphan_invocations_by_round(
+    conn: sqlite3.Connection,
+    campaign_unit_key: str,
+    arch_norm: str,
+) -> dict[int, list[int]]:
+    rows = conn.execute(
+        "SELECT invocation.event_id, invocation.round_index "
+        "FROM campaign_gate_events AS invocation "
+        "WHERE invocation.campaign_unit_key = ? "
+        "AND invocation.event_type = 'BUILD_INVOCATION' "
+        "AND invocation.arch_norm = ? "
+        "AND NOT EXISTS ("
+        "  SELECT 1 FROM campaign_gate_events AS outcome "
+        "  WHERE outcome.event_type = 'CONVERGENCE' "
+        "  AND outcome.invocation_event_id = invocation.event_id"
+        ") ORDER BY invocation.round_index, invocation.event_id",
+        (campaign_unit_key, arch_norm),
+    ).fetchall()
+    grouped: dict[int, list[int]] = {}
+    for row in rows:
+        grouped.setdefault(int(row["round_index"]), []).append(int(row["event_id"]))
+    return grouped
+
+
+def _rebuild_pass_convergence(
+    unit: Unit,
+    record: sqlite3.Row,
+    *,
+    round_index: int,
+    arch_norm: str,
+    invocation_event_id: int,
+) -> tuple[dict[str, object] | None, str | None]:
+    if (
+        _text(record, "base_commit") != unit.base_commit
+        or _text(record, "project") != unit.project
+        or _text(record, "branch") != unit.branch
+        or _text(record, "spec_name") != unit.spec_name
+        or _normalize_arch_raw(_text(record, "arch")) != arch_norm
+    ):
+        return None, "hash_mismatch"
+
+    worktree = Path(_text(record, "worktree_path"))
+    protected = worktree / ".ci_triage_protected"
+    if not worktree.is_dir() or not protected.is_file():
+        return None, "worktree_damaged"
+    try:
+        marker = json.loads(protected.read_text(encoding="utf-8"))
+    except (OSError, json.JSONDecodeError):
+        return None, "worktree_damaged"
+    if not isinstance(marker, dict) or (
+        marker.get("verification_id") != _text(record, "verification_id")
+        or marker.get("failure_key") != _text(record, "failure_key")
+    ):
+        return None, "worktree_damaged"
+
+    verified_tree = _run_git_text(worktree, "rev-parse", "HEAD^{tree}")
+    if verified_tree != _text(record, "verified_tree_sha"):
+        return None, "worktree_damaged"
+    status = _run_git_text(worktree, "status", "--porcelain", "--untracked-files=normal")
+    if status is None or status:
+        return None, "worktree_damaged"
+    changed_paths = _git_changed_paths(
+        worktree,
+        _text(record, "base_commit"),
+        _text(record, "verified_commit_sha"),
+    )
+    if changed_paths is None:
+        return None, "worktree_damaged"
+    return (
+        {
+            "round_index": round_index,
+            "arch_norm": arch_norm,
+            "invocation_event_id": invocation_event_id,
+            "result": "PASS",
+            "verdict": "n_a",
+            "reason": "build_passed",
+            "evidence_path": None,
+            "evidence_sha256": None,
+            "verification_id": _text(record, "verification_id"),
+            "actual_changed_paths": changed_paths,
+            "previous_basis": "none",
+            "at": _now_iso8601(),
+        },
+        None,
+    )
+
+
+def _run_git_text(worktree: Path, *args: str) -> str | None:
+    try:
+        completed = subprocess.run(
+            ["git", "-C", str(worktree), *args],
+            check=False,
+            capture_output=True,
+            text=True,
+        )
+    except OSError:
+        return None
+    if completed.returncode != 0:
+        return None
+    return completed.stdout.strip()
+
+
+def _git_changed_paths(
+    worktree: Path,
+    base_commit: str,
+    verified_commit_sha: str,
+) -> list[str] | None:
+    try:
+        completed = subprocess.run(
+            [
+                "git",
+                "-C",
+                str(worktree),
+                "diff",
+                "--name-only",
+                "--no-renames",
+                "-z",
+                base_commit,
+                verified_commit_sha,
+                "--",
+            ],
+            check=False,
+            capture_output=True,
+        )
+    except OSError:
+        return None
+    if completed.returncode != 0:
+        return None
+    paths: list[str] = []
+    for raw_path in completed.stdout.split(b"\0"):
+        if not raw_path:
+            continue
+        try:
+            path = raw_path.decode("utf-8")
+        except UnicodeDecodeError:
+            return None
+        normalized = PurePosixPath(path)
+        if normalized.is_absolute() or any(part in {".", ".."} for part in normalized.parts):
+            return None
+        paths.append(normalized.as_posix())
+    return sorted(paths)
+
+
+def _record_orphan_passes(
+    conn: sqlite3.Connection,
+    campaign_unit_key: str,
+    round_index: int,
+    arch_norm: str,
+    records: Sequence[sqlite3.Row],
+    reason: str,
+) -> None:
+    for record in records:
+        _append_event_on_connection(
+            conn,
+            campaign_unit_key,
+            "ORPHAN_PASS",
+            {
+                "round_index": round_index,
+                "arch_norm": arch_norm,
+                "verification_id": _text(record, "verification_id"),
+                "worktree_path": _text(record, "worktree_path"),
+                "reason": reason,
+                "detected_at": _now_iso8601(),
+            },
+        )
+
+
+def _orphan_invocation_payload(
+    *,
+    round_index: int,
+    arch_norm: str,
+    invocation_event_id: int,
+) -> dict[str, object]:
+    return {
+        "round_index": round_index,
+        "arch_norm": arch_norm,
+        "invocation_event_id": invocation_event_id,
+        "result": "n_a",
+        "verdict": "n_a",
+        "reason": "orphan_invocation",
+        "evidence_path": None,
+        "evidence_sha256": None,
+        "verification_id": None,
+        "actual_changed_paths": [],
+        "previous_basis": "none",
+        "at": _now_iso8601(),
+    }
+
+
+def _empty_reconcile_result(
+    branch: str,
+    *,
+    non_campaign_verification_ids: Sequence[str] = (),
+) -> ReconcileResult:
+    return ReconcileResult(
+        branch=branch,
+        current_verification_id=None,
+        current_relinked_invocation_event_id=None,
+        other_round_relinks=(),
+        backfilled_invocation_event_ids=(),
+        orphan_pass_verification_ids=(),
+        held_rounds=(),
+        non_campaign_verification_ids=tuple(non_campaign_verification_ids),
+    )
+
+
+def create_qb_request(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    *,
+    request_id: str,
+    sbs_target: str,
+) -> int:
+    if not request_id or not sbs_target:
+        raise ValueError("request_id and sbs_target are required")
+    conn = _connect(state_db)
+    try:
+        with _immediate_transaction(conn):
+            _require_unit(conn, campaign_unit_key)
+            existing = conn.execute(
+                "SELECT request_seq, campaign_unit_key, sbs_target "
+                "FROM campaign_qb_requests WHERE request_id = ?",
+                (request_id,),
+            ).fetchone()
+            if existing is not None:
+                if (
+                    _text(existing, "campaign_unit_key") != campaign_unit_key
+                    or _text(existing, "sbs_target") != sbs_target
+                ):
+                    raise StateInconsistent("request_id is already bound to different input")
+                return int(existing["request_seq"])
+            cursor = conn.execute(
+                "INSERT INTO campaign_qb_requests "
+                "(request_id, campaign_unit_key, sbs_target, created_at) VALUES (?, ?, ?, ?)",
+                (request_id, campaign_unit_key, sbs_target, _now_iso8601()),
+            )
+            request_seq = _lastrowid(cursor)
+            conn.execute(
+                "INSERT INTO campaign_qb_events "
+                "(request_seq, event_type, degraded, created_at) VALUES (?, 'SUBMITTED', 0, ?)",
+                (request_seq, _now_iso8601()),
+            )
+            return request_seq
+    finally:
+        conn.close()
+
+
+def append_qb_event(
+    state_db: StateDatabase,
+    *,
+    request_seq: int,
+    event_type: str,
+    qb_build_id: str | None = None,
+    status: str | None = None,
+    accepted: bool | None = None,
+    sbs_target_echo: str | None = None,
+    per_arch_status_json: str | None = None,
+    qb_result_sha256: str | None = None,
+    qb_result_ref: str | None = None,
+    degraded: bool = False,
+) -> int:
+    if event_type == "SUBMITTED":
+        raise PayloadSchemaError("SUBMITTED can only be written by create_qb_request")
+    if event_type not in {"BUILD_BOUND", "RESULT"}:
+        raise PayloadSchemaError(f"unsupported QB event_type: {event_type!r}")
+    conn = _connect(state_db)
+    try:
+        with _immediate_transaction(conn):
+            request = conn.execute(
+                "SELECT request_seq FROM campaign_qb_requests WHERE request_seq = ?",
+                (request_seq,),
+            ).fetchone()
+            if request is None:
+                raise StateInconsistent("QB event references a missing request")
+            if event_type == "BUILD_BOUND":
+                if not qb_build_id:
+                    raise PayloadSchemaError("BUILD_BOUND requires qb_build_id")
+                if any(
+                    value is not None
+                    for value in (
+                        status,
+                        accepted,
+                        sbs_target_echo,
+                        per_arch_status_json,
+                        qb_result_sha256,
+                        qb_result_ref,
+                    )
+                ):
+                    raise PayloadSchemaError("BUILD_BOUND may not contain result fields")
+                existing_ids = {
+                    _text(row, "qb_build_id")
+                    for row in conn.execute(
+                        "SELECT qb_build_id FROM campaign_qb_events "
+                        "WHERE request_seq = ? AND event_type = 'BUILD_BOUND'",
+                        (request_seq,),
+                    ).fetchall()
+                }
+                if existing_ids and existing_ids != {qb_build_id}:
+                    raise StateInconsistent("QB request is already bound to another build")
+            else:
+                if not status or not sbs_target_echo or not qb_result_sha256:
+                    raise PayloadSchemaError(
+                        "RESULT requires status, sbs_target_echo, and qb_result_sha256"
+                    )
+                bound = conn.execute(
+                    "SELECT 1 FROM campaign_qb_events WHERE request_seq = ? "
+                    "AND event_type = 'BUILD_BOUND' AND (? IS NULL OR qb_build_id = ?) LIMIT 1",
+                    (request_seq, qb_build_id, qb_build_id),
+                ).fetchone()
+                if bound is None:
+                    raise StateInconsistent("RESULT requires an existing valid build binding")
+            cursor = conn.execute(
+                "INSERT INTO campaign_qb_events "
+                "(request_seq, event_type, qb_build_id, status, accepted, "
+                "sbs_target_echo, per_arch_status_json, qb_result_sha256, qb_result_ref, "
+                "degraded, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
+                (
+                    request_seq,
+                    event_type,
+                    qb_build_id,
+                    status,
+                    int(accepted) if accepted is not None else None,
+                    sbs_target_echo,
+                    per_arch_status_json,
+                    qb_result_sha256,
+                    qb_result_ref,
+                    int(degraded),
+                    _now_iso8601(),
+                ),
+            )
+            return _lastrowid(cursor)
+    finally:
+        conn.close()
+
+
+def find_unit_by_request_id(state_db: StateDatabase, request_id: str) -> str | None:
+    conn = _connect(state_db)
+    try:
+        row = conn.execute(
+            "SELECT campaign_unit_key FROM campaign_qb_requests WHERE request_id = ?",
+            (request_id,),
+        ).fetchone()
+    finally:
+        conn.close()
+    return _text(row, "campaign_unit_key") if row is not None else None
+
+
+def find_unit_by_qb_build_id(state_db: StateDatabase, qb_build_id: str) -> str | None:
+    conn = _connect(state_db)
+    try:
+        rows = conn.execute(
+            "SELECT DISTINCT req.campaign_unit_key "
+            "FROM campaign_qb_events AS ev "
+            "JOIN campaign_qb_requests AS req ON req.request_seq = ev.request_seq "
+            "WHERE ev.qb_build_id = ?",
+            (qb_build_id,),
+        ).fetchall()
+    finally:
+        conn.close()
+    units = sorted({_text(row, "campaign_unit_key") for row in rows})
+    if len(units) > 1:
+        raise StateInconsistent("QB build id is ambiguous across campaign units")
+    return units[0] if units else None
+
+
+def latest_qb_result(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+) -> dict[str, object] | None:
+    conn = _connect(state_db)
+    try:
+        row = conn.execute(
+            "SELECT ev.* FROM campaign_qb_requests AS req "
+            "JOIN campaign_qb_events AS ev ON ev.request_seq = req.request_seq "
+            "WHERE req.campaign_unit_key = ? "
+            "AND req.request_seq = (SELECT MAX(request_seq) FROM campaign_qb_requests "
+            "WHERE campaign_unit_key = ?) AND ev.event_type = 'RESULT' "
+            "ORDER BY ev.event_id DESC LIMIT 1",
+            (campaign_unit_key, campaign_unit_key),
+        ).fetchone()
+    finally:
+        conn.close()
+    if row is None:
+        return None
+    return {key: row[key] for key in row.keys()}
+
+
+def _connect(state_db: StateDatabase) -> sqlite3.Connection:
+    conn = state_db.connect()
+    _ensure_schema_on_connection(conn)
+    return conn
+
+
+def _ensure_schema_on_connection(conn: sqlite3.Connection) -> None:
+    conn.executescript(_SCHEMA_SQL)
+
+
+@contextmanager
+def _immediate_transaction(conn: sqlite3.Connection) -> Iterator[None]:
+    try:
+        conn.execute("BEGIN IMMEDIATE")
+    except sqlite3.OperationalError as exc:
+        if _is_busy_error(exc):
+            raise CampaignStateBusy("CAMPAIGN_STATE_BUSY") from exc
+        raise
+    try:
+        yield
+    except Exception:
+        conn.rollback()
+        raise
+    else:
+        conn.commit()
+
+
+@contextmanager
+def _savepoint(conn: sqlite3.Connection, name: str) -> Iterator[None]:
+    conn.execute(f"SAVEPOINT {name}")
+    try:
+        yield
+    except Exception:
+        conn.execute(f"ROLLBACK TO SAVEPOINT {name}")
+        conn.execute(f"RELEASE SAVEPOINT {name}")
+        raise
+    else:
+        conn.execute(f"RELEASE SAVEPOINT {name}")
+
+
+def _is_busy_error(exc: sqlite3.OperationalError) -> bool:
+    message = str(exc).lower()
+    return "locked" in message or "busy" in message
+
+
+def _unit_values(
+    *,
+    campaign_unit_key: str,
+    submission_identity_key: str,
+    primary_arch: str | None,
+    failed_arches: Sequence[str],
+    toolchain_profile: str,
+    ci_evidence_ref: str | None,
+    ci_evidence_sha256: str | None,
+    max_rounds: int,
+    max_build_invocations: int,
+    identity_fields: Mapping[str, str],
+) -> dict[str, object]:
+    if set(identity_fields) != set(_IDENTITY_FIELDS):
+        missing = sorted(set(_IDENTITY_FIELDS) - set(identity_fields))
+        extra = sorted(set(identity_fields) - set(_IDENTITY_FIELDS))
+        raise ValueError(f"identity fields mismatch: missing={missing}, extra={extra}")
+    required_strings = {
+        "campaign_unit_key": campaign_unit_key,
+        "submission_identity_key": submission_identity_key,
+        "toolchain_profile": toolchain_profile,
+        **identity_fields,
+    }
+    empty = sorted(key for key, value in required_strings.items() if not value)
+    if empty:
+        raise ValueError(f"campaign unit fields must be non-empty: {empty}")
+    if max_rounds < 1 or max_build_invocations < 1:
+        raise ValueError("campaign budgets must be positive")
+    arches = _canonical_failed_arches(failed_arches)
+    if not arches:
+        raise ValueError("failed_arches must be non-empty")
+    if primary_arch is not None and primary_arch not in arches:
+        raise ValueError("primary_arch must be present in failed_arches")
+    return {
+        "campaign_unit_key": campaign_unit_key,
+        **{key: identity_fields[key] for key in _IDENTITY_FIELDS},
+        "submission_identity_key": submission_identity_key,
+        "toolchain_profile": toolchain_profile,
+        "ci_evidence_ref": ci_evidence_ref,
+        "ci_evidence_sha256": ci_evidence_sha256,
+        "primary_arch": primary_arch,
+        "max_rounds": max_rounds,
+        "max_build_invocations": max_build_invocations,
+        "failed_arches": json.dumps(arches, separators=(",", ":")),
+        "schema_version": CAMPAIGN_SCHEMA_VERSION,
+    }
+
+
+def _canonical_failed_arches(arches: Sequence[str]) -> tuple[str, ...]:
+    if isinstance(arches, (str, bytes)):
+        raise ValueError("failed_arches must be a sequence of arch names")
+    values = set(arches)
+    if any(not isinstance(value, str) or not value for value in values):
+        raise ValueError("failed_arches entries must be non-empty strings")
+    rank = {arch: index for index, arch in enumerate(_FAILED_ARCH_ORDER)}
+    return tuple(sorted(values, key=lambda value: (rank.get(value, len(rank)), value)))
+
+
+def _insert_or_compare_unit(conn: sqlite3.Connection, values: Mapping[str, object]) -> bool:
+    key = str(values["campaign_unit_key"])
+    existing = conn.execute(
+        "SELECT * FROM campaign_units WHERE campaign_unit_key = ?", (key,)
+    ).fetchone()
+    compare_columns = tuple(values)
+    if existing is not None:
+        differences = [column for column in compare_columns if existing[column] != values[column]]
+        if differences:
+            raise StateInconsistent(f"campaign unit differs in fields: {differences}")
+        return False
+    columns = (*compare_columns, "created_at")
+    placeholders = ", ".join("?" for _ in columns)
+    conn.execute(
+        f"INSERT INTO campaign_units ({', '.join(columns)}) VALUES ({placeholders})",
+        (*[values[column] for column in compare_columns], _now_iso8601()),
+    )
+    return True
+
+
+def _require_unit(conn: sqlite3.Connection, campaign_unit_key: str) -> Unit:
+    row = conn.execute(
+        "SELECT * FROM campaign_units WHERE campaign_unit_key = ?", (campaign_unit_key,)
+    ).fetchone()
+    if row is None:
+        raise StateInconsistent(f"campaign unit not found: {campaign_unit_key}")
+    return _unit_from_row(row)
+
+
+def _unit_from_row(row: sqlite3.Row) -> Unit:
+    raw_arches: Any = json.loads(_text(row, "failed_arches"))
+    if not isinstance(raw_arches, list) or not all(isinstance(item, str) for item in raw_arches):
+        raise StateInconsistent("campaign unit failed_arches is not a string array")
+    return Unit(
+        campaign_unit_key=_text(row, "campaign_unit_key"),
+        ci_system=_text(row, "ci_system"),
+        source_build_id=_text(row, "source_build_id"),
+        project=_text(row, "project"),
+        branch=_text(row, "branch"),
+        spec_name=_text(row, "spec_name"),
+        base_commit=_text(row, "base_commit"),
+        submission_identity_key=_text(row, "submission_identity_key"),
+        toolchain_profile=_text(row, "toolchain_profile"),
+        ci_evidence_ref=_optional_text(row, "ci_evidence_ref"),
+        ci_evidence_sha256=_optional_text(row, "ci_evidence_sha256"),
+        primary_arch=_optional_text(row, "primary_arch"),
+        max_rounds=int(row["max_rounds"]),
+        max_build_invocations=int(row["max_build_invocations"]),
+        failed_arches=tuple(raw_arches),
+        created_at=_text(row, "created_at"),
+        schema_version=_text(row, "schema_version"),
+    )
+
+
+def _round_from_row(row: sqlite3.Row) -> Round:
+    return Round(
+        campaign_unit_key=_text(row, "campaign_unit_key"),
+        round_index=int(row["round_index"]),
+        edit_spec_ref=_text(row, "edit_spec_ref"),
+        edit_spec_sha256=_text(row, "edit_spec_sha256"),
+        created_at=_text(row, "created_at"),
+    )
+
+
+def _round_on_connection(
+    conn: sqlite3.Connection,
+    campaign_unit_key: str,
+    round_index: int,
+) -> Round | None:
+    row = conn.execute(
+        "SELECT * FROM campaign_rounds WHERE campaign_unit_key = ? AND round_index = ?",
+        (campaign_unit_key, round_index),
+    ).fetchone()
+    return _round_from_row(row) if row is not None else None
+
+
+def _insert_status_row(
+    conn: sqlite3.Connection,
+    campaign_unit_key: str,
+    status: str,
+    reason: str | None,
+    arch_norm: str | None,
+) -> None:
+    conn.execute(
+        "INSERT INTO campaign_status_log "
+        "(campaign_unit_key, status, reason, arch_norm, created_at) VALUES (?, ?, ?, ?, ?)",
+        (campaign_unit_key, status, reason, arch_norm, _now_iso8601()),
+    )
+
+
+def _append_event_on_connection(
+    conn: sqlite3.Connection,
+    campaign_unit_key: str,
+    event_type: str,
+    payload: Mapping[str, object],
+) -> int:
+    _require_unit(conn, campaign_unit_key)
+    _validate_event_payload(conn, campaign_unit_key, event_type, payload)
+    if event_type == "ORPHAN_PASS":
+        verification_id = str(payload["verification_id"])
+        rows = conn.execute(
+            "SELECT payload_json FROM campaign_gate_events "
+            "WHERE campaign_unit_key = ? AND event_type = 'ORPHAN_PASS'",
+            (campaign_unit_key,),
+        ).fetchall()
+        for row in rows:
+            existing = json.loads(_text(row, "payload_json"))
+            if isinstance(existing, dict) and existing.get("verification_id") == verification_id:
+                event = conn.execute(
+                    "SELECT event_id FROM campaign_gate_events "
+                    "WHERE campaign_unit_key = ? AND event_type = 'ORPHAN_PASS' "
+                    "AND payload_json = ? ORDER BY event_id DESC LIMIT 1",
+                    (campaign_unit_key, _canonical_json(existing)),
+                ).fetchone()
+                if event is not None:
+                    return int(event["event_id"])
+    _validate_immutable_derive_fields(conn, campaign_unit_key, event_type, payload)
+    return _insert_event_row(conn, campaign_unit_key, event_type, payload)
+
+
+def _insert_event_row(
+    conn: sqlite3.Connection,
+    campaign_unit_key: str,
+    event_type: str,
+    payload: Mapping[str, object],
+) -> int:
+    cursor = conn.execute(
+        "INSERT INTO campaign_gate_events "
+        "(campaign_unit_key, round_index, arch_norm, verdict, invocation_event_id, "
+        "event_type, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
+        (
+            campaign_unit_key,
+            payload.get("round_index"),
+            payload.get("arch_norm"),
+            payload.get("verdict"),
+            payload.get("invocation_event_id"),
+            event_type,
+            _canonical_json(payload),
+            _now_iso8601(),
+        ),
+    )
+    return _lastrowid(cursor)
+
+
+def _validate_event_payload(
+    conn: sqlite3.Connection,
+    campaign_unit_key: str,
+    event_type: str,
+    payload: Mapping[str, object],
+) -> None:
+    _require_known_event_type(event_type)
+    validators = {
+        "REPRODUCE": _validate_reproduce,
+        "BUILD_INVOCATION": _validate_build_invocation,
+        "ORPHAN_PASS": _validate_orphan_pass,
+        "POLICY": _validate_policy,
+        "DERIVE": _validate_derive,
+        "PUSH": _validate_push,
+        "KB": _validate_kb,
+        "REVIEW": _validate_review,
+        "CONVERGENCE": _validate_convergence_shape,
+        "SECONDARY_TARGET_ADOPTED": _validate_adoption,
+        "WORKSPACE_CLEANUP": _validate_workspace_event,
+        "WORKSPACE_RELEASE": _validate_workspace_event,
+    }
+    validators[event_type](payload)
+    if event_type == "CONVERGENCE":
+        _validate_invocation_binding(conn, campaign_unit_key, payload)
+
+
+def _require_known_event_type(event_type: str) -> None:
+    if event_type not in _KNOWN_EVENT_TYPES:
+        raise UnknownEventType(f"unregistered campaign event type: {event_type!r}")
+
+
+def _validate_reproduce(payload: Mapping[str, object]) -> None:
+    _require_keys(
+        payload,
+        {
+            "arch_norm",
+            "outcome",
+            "evidence_local",
+            "evidence_sha256",
+            "synthetic_zero_error",
+            "gbs_conf_sha256",
+            "ci_evidence_sha256_used",
+            "build_log",
+            "basis",
+        },
+    )
+    _require_arch_norm(_payload_str(payload, "arch_norm"))
+    outcome = _payload_str(payload, "outcome")
+    if outcome not in {"matched", "different_failure", "baseline_pass"}:
+        raise PayloadSchemaError("invalid REPRODUCE outcome")
+    _require_nonempty_strings(
+        payload,
+        (
+            "evidence_local",
+            "evidence_sha256",
+            "gbs_conf_sha256",
+            "ci_evidence_sha256_used",
+            "build_log",
+        ),
+    )
+    if not isinstance(payload["synthetic_zero_error"], bool):
+        raise PayloadSchemaError("synthetic_zero_error must be bool")
+    if outcome == "baseline_pass" and payload["synthetic_zero_error"] is not True:
+        raise PayloadSchemaError("baseline_pass requires synthetic_zero_error=true")
+
+
+def _validate_build_invocation(payload: Mapping[str, object]) -> None:
+    _require_keys(payload, {"round_index", "arch_norm"})
+    _require_round_index(payload)
+    _require_arch_norm(_payload_str(payload, "arch_norm"))
+
+
+def _validate_orphan_pass(payload: Mapping[str, object]) -> None:
+    _require_keys(
+        payload,
+        {
+            "round_index",
+            "arch_norm",
+            "verification_id",
+            "worktree_path",
+            "reason",
+            "detected_at",
+        },
+    )
+    _require_round_index(payload)
+    _require_arch_norm(_payload_str(payload, "arch_norm"))
+    _require_nonempty_strings(payload, ("verification_id", "worktree_path", "detected_at"))
+    if payload["reason"] not in {"link_failed", "hash_mismatch", "worktree_damaged", "ambiguous"}:
+        raise PayloadSchemaError("invalid ORPHAN_PASS reason")
+
+
+def _validate_policy(payload: Mapping[str, object]) -> None:
+    _require_keys(
+        payload,
+        {
+            "round_index",
+            "verdict",
+            "hits",
+            "fix_strategy_initial",
+            "fix_strategy_final",
+            "edit_source_kind",
+        },
+    )
+    _require_round_index(payload)
+    if not isinstance(payload["hits"], list):
+        raise PayloadSchemaError("POLICY hits must be a list")
+    if payload["edit_source_kind"] not in {"t1_cherry_pick", "generated", "suppress"}:
+        raise PayloadSchemaError("invalid POLICY edit_source_kind")
+
+
+def _validate_derive(payload: Mapping[str, object]) -> None:
+    keys = {
+        "message_brief",
+        "author_identity",
+        "committer_identity",
+        "author_date",
+        "committer_date",
+        "derived_commit_sha",
+        "verified_tree_sha",
+    }
+    _require_keys(payload, keys)
+    _require_nonempty_strings(payload, tuple(keys))
+
+
+def _validate_push(payload: Mapping[str, object]) -> None:
+    _require_keys(payload, {"ref", "ref_class", "pushed_sha", "result", "url", "at"})
+    _require_nonempty_strings(payload, ("ref", "pushed_sha", "at"))
+    if payload["ref_class"] not in {"sandbox", "review"}:
+        raise PayloadSchemaError("invalid PUSH ref_class")
+    if payload["result"] not in {"ok", "failed"}:
+        raise PayloadSchemaError("invalid PUSH result")
+    if payload["url"] is not None and not isinstance(payload["url"], str):
+        raise PayloadSchemaError("PUSH url must be string or null")
+
+
+def _validate_kb(payload: Mapping[str, object]) -> None:
+    _require_keys(payload, {"kb_id", "dedupe_hit", "status", "at"})
+    _require_nonempty_strings(payload, ("kb_id", "at"))
+    if not isinstance(payload["dedupe_hit"], bool) or payload["status"] != "NEW":
+        raise PayloadSchemaError("invalid KB payload")
+
+
+def _validate_review(payload: Mapping[str, object]) -> None:
+    _require_keys(payload, {"outcome", "review_url", "degraded", "qb_event_id", "at"})
+    if payload["outcome"] not in {"pushed", "manual", "ineligible"}:
+        raise PayloadSchemaError("invalid REVIEW outcome")
+    if not isinstance(payload["degraded"], bool):
+        raise PayloadSchemaError("REVIEW degraded must be bool")
+    if payload["outcome"] == "manual" and payload["degraded"] is not True:
+        raise PayloadSchemaError("manual REVIEW must be degraded")
+    if payload["review_url"] is not None and not isinstance(payload["review_url"], str):
+        raise PayloadSchemaError("REVIEW review_url must be string or null")
+    if payload["qb_event_id"] is not None and not isinstance(payload["qb_event_id"], int):
+        raise PayloadSchemaError("REVIEW qb_event_id must be int or null")
+    _require_nonempty_strings(payload, ("at",))
+
+
+def _validate_convergence_shape(payload: Mapping[str, object]) -> None:
+    _require_keys(
+        payload,
+        {
+            "round_index",
+            "arch_norm",
+            "invocation_event_id",
+            "result",
+            "verdict",
+            "reason",
+            "evidence_path",
+            "evidence_sha256",
+            "verification_id",
+            "actual_changed_paths",
+            "previous_basis",
+            "at",
+        },
+    )
+    _require_round_index(payload)
+    _require_arch_norm(_payload_str(payload, "arch_norm"))
+    reason = _payload_str(payload, "reason")
+    result = _payload_str(payload, "result")
+    verdict = _payload_str(payload, "verdict")
+    invocation_id = payload["invocation_event_id"]
+    if verdict not in {"advance", "stalled", "regressed", "denied", "n_a"}:
+        raise PayloadSchemaError("invalid CONVERGENCE verdict")
+    if payload["previous_basis"] not in {"reproduce", "prev_build", "synthetic_zero", "none"}:
+        raise PayloadSchemaError("invalid CONVERGENCE previous_basis")
+    if not isinstance(payload["actual_changed_paths"], list) or not all(
+        isinstance(item, str) for item in payload["actual_changed_paths"]
+    ):
+        raise PayloadSchemaError("actual_changed_paths must be a string list")
+    if invocation_id is None:
+        if reason != "rebaselined" or result != "n_a" or verdict != "n_a":
+            raise PayloadSchemaError(
+                "only rebaselined n_a convergence may omit invocation_event_id"
+            )
+    elif not isinstance(invocation_id, int) or isinstance(invocation_id, bool):
+        raise PayloadSchemaError("invocation_event_id must be int or null")
+    if reason in _CONVERGENCE_NA_REASONS:
+        if result != "n_a" or verdict != "n_a":
+            raise PayloadSchemaError("non-build convergence reasons require result/verdict n_a")
+    elif result not in {"PASS", "FAIL"}:
+        raise PayloadSchemaError("build outcome convergence requires PASS or FAIL")
+    if result == "PASS":
+        if verdict != "n_a" or not isinstance(payload["verification_id"], str):
+            raise PayloadSchemaError("PASS convergence requires n_a and verification_id")
+        if payload["evidence_path"] is not None or payload["evidence_sha256"] is not None:
+            raise PayloadSchemaError("PASS convergence evidence fields must be null")
+    elif result == "FAIL":
+        if verdict == "n_a":
+            raise PayloadSchemaError("FAIL build outcome requires a substantive verdict")
+        if not isinstance(payload["evidence_path"], str) or not isinstance(
+            payload["evidence_sha256"], str
+        ):
+            raise PayloadSchemaError("FAIL convergence requires evidence path and hash")
+        if payload["verification_id"] is not None:
+            raise PayloadSchemaError("FAIL convergence verification_id must be null")
+    else:
+        if payload["evidence_path"] is not None or payload["evidence_sha256"] is not None:
+            raise PayloadSchemaError("n_a convergence evidence fields must be null")
+        if payload["verification_id"] is not None:
+            raise PayloadSchemaError("n_a convergence verification_id must be null")
+    _require_nonempty_strings(payload, ("reason", "at"))
+
+
+def _validate_adoption(payload: Mapping[str, object]) -> None:
+    _require_keys(
+        payload,
+        {
+            "arch_norm",
+            "adopted_fingerprint",
+            "baseline_error_count",
+            "current_error_count",
+            "baseline_truncated",
+            "current_truncated",
+            "expected_reproduce_event_id",
+            "at",
+        },
+    )
+    _require_arch_norm(_payload_str(payload, "arch_norm"))
+    if not isinstance(payload["adopted_fingerprint"], dict):
+        raise PayloadSchemaError("adopted_fingerprint must be an object")
+    for key in ("baseline_error_count", "current_error_count", "expected_reproduce_event_id"):
+        if not isinstance(payload[key], int) or isinstance(payload[key], bool):
+            raise PayloadSchemaError(f"{key} must be int")
+    if payload["baseline_truncated"] is not False or payload["current_truncated"] is not False:
+        raise PayloadSchemaError("adoption requires untruncated evidence")
+
+
+def _validate_workspace_event(payload: Mapping[str, object]) -> None:
+    _require_keys(payload, {"paths", "reason"})
+    if not isinstance(payload["paths"], list) or not all(
+        isinstance(item, str) for item in payload["paths"]
+    ):
+        raise PayloadSchemaError("workspace paths must be a string list")
+    _require_nonempty_strings(payload, ("reason",))
+    if "confirmed_by" in payload and not isinstance(payload["confirmed_by"], str):
+        raise PayloadSchemaError("confirmed_by must be a string")
+
+
+def _validate_invocation_binding(
+    conn: sqlite3.Connection,
+    campaign_unit_key: str,
+    payload: Mapping[str, object],
+) -> None:
+    invocation_id = payload.get("invocation_event_id")
+    if invocation_id is None:
+        return
+    row = conn.execute(
+        "SELECT campaign_unit_key, event_type, round_index, arch_norm "
+        "FROM campaign_gate_events WHERE event_id = ?",
+        (invocation_id,),
+    ).fetchone()
+    if row is None:
+        raise StateInconsistent("invocation_event_id does not exist")
+    if _text(row, "event_type") != "BUILD_INVOCATION":
+        raise StateInconsistent("invocation_event_id is not BUILD_INVOCATION")
+    if _text(row, "campaign_unit_key") != campaign_unit_key:
+        raise StateInconsistent("invocation_event_id belongs to another unit")
+    if row["round_index"] != payload.get("round_index") or row["arch_norm"] != payload.get(
+        "arch_norm"
+    ):
+        raise StateInconsistent("invocation_event_id round or arch mismatch")
+
+
+def _validate_immutable_derive_fields(
+    conn: sqlite3.Connection,
+    campaign_unit_key: str,
+    event_type: str,
+    payload: Mapping[str, object],
+) -> None:
+    if event_type != "DERIVE":
+        return
+    rows = conn.execute(
+        "SELECT payload_json FROM campaign_gate_events "
+        "WHERE campaign_unit_key = ? AND event_type = 'DERIVE' ORDER BY event_id",
+        (campaign_unit_key,),
+    ).fetchall()
+    immutable = ("message_brief", "author_identity", "author_date", "committer_date")
+    for row in rows:
+        existing = json.loads(_text(row, "payload_json"))
+        if not isinstance(existing, dict):
+            raise StateInconsistent("stored DERIVE payload is not an object")
+        if any(existing.get(key) != payload.get(key) for key in immutable):
+            raise StateInconsistent("DERIVE first-write identity fields changed")
+
+
+def _require_keys(payload: Mapping[str, object], required: set[str]) -> None:
+    missing = sorted(required - set(payload))
+    if missing:
+        raise PayloadSchemaError(f"payload missing required fields: {missing}")
+
+
+def _require_nonempty_strings(
+    payload: Mapping[str, object],
+    keys: Sequence[str],
+) -> None:
+    for key in keys:
+        if not isinstance(payload.get(key), str) or not payload[key]:
+            raise PayloadSchemaError(f"payload field {key} must be a non-empty string")
+
+
+def _require_round_index(payload: Mapping[str, object]) -> None:
+    value = payload.get("round_index")
+    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
+        raise PayloadSchemaError("round_index must be a positive integer")
+
+
+def _require_arch_norm(arch_norm: str) -> None:
+    if arch_norm not in ARCH_NORMS:
+        raise PayloadSchemaError(f"unsupported arch_norm: {arch_norm!r}")
+
+
+def _normalize_arch_raw(arch_raw: str) -> str | None:
+    return ARCH_RAW_TO_NORM.get(arch_raw)
+
+
+def _require_equal(payload: Mapping[str, object], key: str, expected: object) -> None:
+    if payload.get(key) != expected:
+        raise StateInconsistent(f"convergence {key} does not match link input")
+
+
+def _payload_str(payload: Mapping[str, object], key: str) -> str:
+    value = payload.get(key)
+    if not isinstance(value, str):
+        raise PayloadSchemaError(f"payload field {key} must be a string")
+    return value
+
+
+def _canonical_json(payload: Mapping[str, object]) -> str:
+    try:
+        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
+    except (TypeError, ValueError) as exc:
+        raise PayloadSchemaError(f"payload is not JSON serializable: {exc}") from exc
+
+
+def _event_from_row(row: sqlite3.Row) -> dict[str, object]:
+    payload = _payload_from_row(row)
+    return {
+        "event_id": int(row["event_id"]),
+        "campaign_unit_key": _text(row, "campaign_unit_key"),
+        "event_type": _text(row, "event_type"),
+        "round_index": row["round_index"],
+        "arch_norm": row["arch_norm"],
+        "verdict": row["verdict"],
+        "invocation_event_id": row["invocation_event_id"],
+        "payload": payload,
+        "created_at": _text(row, "created_at"),
+    }
+
+
+def _text(row: sqlite3.Row, key: str) -> str:
+    value: Any = row[key]
+    if not isinstance(value, str):
+        raise StateInconsistent(f"expected text value for {key}")
+    return value
+
+
+def _optional_text(row: sqlite3.Row, key: str) -> str | None:
+    value: Any = row[key]
+    if value is None:
+        return None
+    if not isinstance(value, str):
+        raise StateInconsistent(f"expected optional text value for {key}")
+    return value
+
+
+def _now_iso8601() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds")
+
+
+def _payload_from_row(row: sqlite3.Row) -> dict[str, object]:
+    payload: Any = json.loads(_text(row, "payload_json"))
+    if not isinstance(payload, dict):
+        raise StateInconsistent("stored event payload is not an object")
+    return payload
+
+
+def _load_bound_evidence(path_value: object, digest_value: object) -> dict[str, Any] | None:
+    if not isinstance(path_value, str) or not isinstance(digest_value, str):
+        return None
+    path = Path(path_value)
+    try:
+        raw = path.read_bytes()
+    except OSError:
+        return None
+    if hashlib.sha256(raw).hexdigest() != digest_value:
+        return None
+    try:
+        value: Any = json.loads(raw)
+    except (UnicodeDecodeError, json.JSONDecodeError):
+        return None
+    return value if isinstance(value, dict) else None
+
+
+def _evidence_truncated(evidence: Mapping[str, object]) -> bool:
+    if evidence.get("truncated") is True:
+        return True
+    clusters = evidence.get("error_clusters")
+    if not isinstance(clusters, dict):
+        return False
+    raw_clusters = clusters.get("clusters")
+    if not isinstance(raw_clusters, list):
+        return False
+    return any(
+        isinstance(cluster, dict) and cluster.get("locations_truncated") is True
+        for cluster in raw_clusters
+    )
+
+
+def _lastrowid(cursor: sqlite3.Cursor) -> int:
+    if cursor.lastrowid is None:
+        raise StateInconsistent("SQLite insert did not return a row id")
+    return cursor.lastrowid
diff --git a/tizen-ci-triage/scripts/ci_triage/cli.py b/tizen-ci-triage/scripts/ci_triage/cli.py
index e2ea7cf..bdc4552 100644
--- a/tizen-ci-triage/scripts/ci_triage/cli.py
+++ b/tizen-ci-triage/scripts/ci_triage/cli.py
@@ -9,6 +9,10 @@ from json import JSONDecodeError
 from pathlib import Path
 from typing import TextIO
 
+from ci_triage.campaign_repair_step import (
+    CampaignRepairStepOptions,
+    campaign_repair_step,
+)
 from ci_triage.quickbuild import DEFAULT_COOKIE_PATH
 from ci_triage.runner import TriageOptions, discover_sibling_pythonpath, run_triage
 from ci_triage.state import StateDatabase
@@ -144,9 +148,25 @@ def release_worktree_parser() -> argparse.ArgumentParser:
     return parser
 
 
+def campaign_repair_step_parser() -> argparse.ArgumentParser:
+    parser = argparse.ArgumentParser(
+        prog="ci_triage campaign-repair-step",
+        description="Run one locked, budgeted, and reconciled campaign repair build.",
+    )
+    parser.add_argument("--campaign-unit-key", required=True)
+    parser.add_argument("--state-db", type=Path, required=True)
+    parser.add_argument("--config", type=Path, required=True)
+    parser.add_argument("--round-index", type=int, required=True)
+    parser.add_argument("--edit-spec", type=Path, required=True)
+    parser.add_argument("--arch", required=True)
+    parser.add_argument("--wall-timeout", type=int)
+    return parser
+
+
 def main(
     argv: list[str] | None = None,
     *,
+    stdout: TextIO = sys.stdout,
     stderr: TextIO = sys.stderr,
     extra_pythonpath: tuple[Path, ...] = (),
 ) -> int:
@@ -160,6 +180,12 @@ def main(
         return _main_gerrit_submit(argv[1:], stderr=stderr)
     if argv and argv[0] == "release-worktree":
         return _main_release_worktree(argv[1:], stderr=stderr)
+    if argv and argv[0] == "campaign-repair-step":
+        return _main_campaign_repair_step(
+            argv[1:],
+            stdout=stdout,
+            extra_pythonpath=extra_pythonpath,
+        )
 
     parser = build_parser()
     args = parser.parse_args(argv)
@@ -303,6 +329,32 @@ def _main_release_worktree(argv: list[str], *, stderr: TextIO) -> int:
     return exit_code_for_release(result)
 
 
+def _main_campaign_repair_step(
+    argv: list[str],
+    *,
+    stdout: TextIO,
+    extra_pythonpath: tuple[Path, ...],
+) -> int:
+    args = campaign_repair_step_parser().parse_args(argv)
+    paths = extra_pythonpath or discover_sibling_pythonpath(
+        launcher_path=Path(__file__).resolve().parents[1] / "run_ci_triage.py"
+    )
+    outcome = campaign_repair_step(
+        CampaignRepairStepOptions(
+            campaign_unit_key=args.campaign_unit_key,
+            state_db=StateDatabase(args.state_db),
+            config_path=args.config,
+            round_index=args.round_index,
+            edit_spec_path=args.edit_spec,
+            arch_raw=args.arch,
+            wall_timeout=args.wall_timeout,
+            extra_pythonpath=paths,
+        )
+    )
+    print(json.dumps(outcome.result.to_dict(), sort_keys=True), file=stdout)
+    return outcome.exit_code
+
+
 def _read_json(path: Path) -> dict[str, object]:
     raw = json.loads(path.read_text(encoding="utf-8"))
     if not isinstance(raw, dict):
diff --git a/tizen-ci-triage/scripts/ci_triage/previous_evidence.py b/tizen-ci-triage/scripts/ci_triage/previous_evidence.py
new file mode 100644
index 0000000..0c2eab2
--- /dev/null
+++ b/tizen-ci-triage/scripts/ci_triage/previous_evidence.py
@@ -0,0 +1,175 @@
+"""Resolve the trusted previous evidence for one campaign architecture."""
+
+from __future__ import annotations
+
+import hashlib
+import json
+from copy import deepcopy
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Any
+
+from ci_triage.campaign_state import latest_reproduce
+from ci_triage.state import StateDatabase
+
+_SKIP_NA_REASONS = {
+    "orphan_invocation",
+    "apply_failed",
+    "analyzer_failed",
+    "toolchain_failed",
+}
+
+_SYNTHETIC_ZERO_EVIDENCE: dict[str, Any] = {
+    "schema_version": "evidence_packet/v1",
+    "synthetic": True,
+    "reason": "baseline_pass",
+    "primary_error": None,
+    "error_clusters": {
+        "schema_version": "error_clusters/v1",
+        "clusters": [],
+        "truncated": False,
+    },
+    "cascade_summary": "",
+    "root_cause_candidates": [],
+}
+
+
+@dataclass(frozen=True)
+class ResolvedEvidence:
+    """A hash-verified evidence object and the history basis that selected it."""
+
+    evidence: dict[str, Any]
+    basis: str
+    evidence_path: str | None
+    evidence_sha256: str | None
+
+
+@dataclass(frozen=True)
+class MissingEvidence:
+    """A previous-evidence integrity failure that must fail closed."""
+
+    reason: str
+
+
+PreviousEvidence = ResolvedEvidence | MissingEvidence
+
+
+def resolve(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    *,
+    arch_norm: str,
+) -> PreviousEvidence:
+    """Resolve previous evidence using the frozen campaign history semantics.
+
+    Both the pre-build check and the post-build TOCTOU check call this function.
+    A substantive event whose bound file is missing or has a mismatched digest is
+    never downgraded to an empty previous result.
+    """
+
+    reproduce = latest_reproduce(state_db, campaign_unit_key, arch_norm=arch_norm)
+    if reproduce is None:
+        return MissingEvidence("latest REPRODUCE event is missing")
+
+    events = _convergence_payloads(state_db, campaign_unit_key, arch_norm)
+    if events is None:
+        return MissingEvidence("stored CONVERGENCE payload is invalid")
+    if not events:
+        return _from_reproduce(reproduce)
+
+    latest = events[0]
+    if latest.get("result") == "PASS":
+        return ResolvedEvidence(
+            evidence=_synthetic_zero_evidence(),
+            basis="synthetic_zero",
+            evidence_path=None,
+            evidence_sha256=None,
+        )
+
+    if latest.get("verdict") == "n_a":
+        reason = latest.get("reason")
+        if reason == "rebaselined":
+            return _from_reproduce(reproduce)
+        if reason in _SKIP_NA_REASONS:
+            substantive = next(
+                (payload for payload in events[1:] if payload.get("verdict") != "n_a"),
+                None,
+            )
+            return (
+                _from_payload(substantive, basis="prev_build")
+                if substantive
+                else _from_reproduce(reproduce)
+            )
+        return MissingEvidence(f"latest n_a convergence has unsupported reason {reason!r}")
+
+    return _from_payload(latest, basis="prev_build")
+
+
+def _convergence_payloads(
+    state_db: StateDatabase,
+    campaign_unit_key: str,
+    arch_norm: str,
+) -> list[dict[str, object]] | None:
+    conn = state_db.connect()
+    try:
+        rows = conn.execute(
+            "SELECT payload_json FROM campaign_gate_events "
+            "WHERE campaign_unit_key = ? AND event_type = 'CONVERGENCE' "
+            "AND arch_norm = ? ORDER BY event_id DESC",
+            (campaign_unit_key, arch_norm),
+        ).fetchall()
+    finally:
+        conn.close()
+    result: list[dict[str, object]] = []
+    for row in rows:
+        try:
+            value: Any = json.loads(str(row["payload_json"]))
+        except json.JSONDecodeError:
+            return None
+        if not isinstance(value, dict):
+            return None
+        result.append(value)
+    return result
+
+
+def _from_reproduce(event: dict[str, object]) -> PreviousEvidence:
+    payload = event.get("payload")
+    if not isinstance(payload, dict):
+        return MissingEvidence("latest REPRODUCE payload is invalid")
+    return _from_payload(payload, basis="reproduce", path_key="evidence_local")
+
+
+def _from_payload(
+    payload: dict[str, object],
+    *,
+    basis: str,
+    path_key: str = "evidence_path",
+) -> PreviousEvidence:
+    path_value = payload.get(path_key)
+    digest_value = payload.get("evidence_sha256")
+    if not isinstance(path_value, str) or not isinstance(digest_value, str):
+        return MissingEvidence(f"{basis} evidence binding is incomplete")
+    path = Path(path_value)
+    try:
+        raw = path.read_bytes()
+    except OSError as exc:
+        return MissingEvidence(f"{basis} evidence is unreadable: {exc}")
+    if hashlib.sha256(raw).hexdigest() != digest_value:
+        return MissingEvidence(f"{basis} evidence sha256 mismatch")
+    try:
+        value: Any = json.loads(raw)
+    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
+        return MissingEvidence(f"{basis} evidence is invalid JSON: {exc}")
+    if not isinstance(value, dict):
+        return MissingEvidence(f"{basis} evidence must be a JSON object")
+    return ResolvedEvidence(
+        evidence=value,
+        basis=basis,
+        evidence_path=str(path),
+        evidence_sha256=digest_value,
+    )
+
+
+def _synthetic_zero_evidence() -> dict[str, Any]:
+    # Return a fresh object so convergence callers cannot mutate shared state.
+    return deepcopy(_SYNTHETIC_ZERO_EVIDENCE)
````````
