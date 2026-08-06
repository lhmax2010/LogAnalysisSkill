# R14 闭环裁决:三方评审(设计 v1.5.16 + 代码 P4.5)

**输入**:评审 A(design 11 findings / code 23 findings)、评审 B
(design 无 MAJOR + code 1 MAJOR + minors)。合并去重后逐条处置。
**总裁决**:PR #76 **维持不 merge**;开 **change_44**(设计修订 →
v1.5.17-FROZEN)+ **代码修复批次 FIX-1**;修复后出 delta 包回送两家
做闭环确认,双家确认 + 开发者放行,方可 merge。

---

## 一、change_44(设计修订,应用后升 v1.5.17-FROZEN)

| # | 来源 | 修订内容 |
|---|---|---|
| D1 | C1/B#13 合并裁决 | §4.1 step 2:`edit_spec_ref` 冻结为 **unit 级 canonical 路径** `ws/<unit_hash>/rounds/round_<N>/edit_spec.json`(替换"realpath(--edit-spec)"字面;canonical 副本优于调用方路径,但 **ref 不得含 arch 层**——arch 入 ref 使 unit 级 round 单 arch 化,三 arch 聚合经唯一入口不可达);per-arch 副本仅作 build 输入 |
| D2 | F1 | previous 回溯规则修订:回溯遇 `result=PASS` → synthetic_zero 锚点;遇 `reason=rebaselined` → 回退至其后首个 REPRODUCE;**不得穿越两类锚点**。DoD 补 n_a-over-PASS / n_a-over-rebaselined 两用例 |
| D3 | F2 | reconcile 写集单一规则冻结:**a0 失败与④多命中 → 仅提交 HELD、立即返回**(不做任何 b/b'/c/d 写入);"写入全部执行+优先级公式"仅适用于 c 与 clean 组共存(与现实现一致) |
| D4 | F3 | 冻结 ROUNDS_EXHAUSTED 写入者:wrapper 捕获 RoundsExhausted/BudgetExhausted → `append_status(ROUNDS_EXHAUSTED, reason=rounds\|budget)` → exit 4;DoD 补用例(含 release 白名单可达性) |
| D5 | F4 | §4.2 记录冻结前提:`state/db.py` 的 `PRAGMA foreign_keys=ON`/WAL/busy_timeout 为 FK"物理禁止"的成立条件;DoD 补反向用例(pragma 关闭时漂移 link 测试必须失败) |
| D6 | F5 | fence 奇偶修复:§4.1 外层块改**四反引号** fence(或抽出内嵌 JSON);恢复丢失的 `#` 前缀;CK-API/IDX/XREF 的 fence 提取算法冻结入 checker 注释;**checker 新增 fence 奇偶 fixture**(CommonMark 语义下 python fence 数量 > 0 断言) |
| D7 | B-MAJOR 后半 | 残留 worktree 恢复语义冻结:build 前发现 `iter_<N>` 已存在——无 protected 标记且无匹配 PASS record → 经 `cleanup_disposable_copy` 清理后重建;有标记 → state_inconsistent_held。不开自由删除旁路 |
| D8 | C20/B#2、F9、F10、B#3 | 错误码与枚举补冻结:新增 `REJECTED_ORPHAN_PASS_HELD`(supersede 此前"复用 REJECTED_STATE_INCONSISTENT"的裁量——既然开修订窗口,专码成本归零);§4.3 登记 ReleaseNotAllowed / AmbiguousQbReference;ORPHAN_PASS reason 增 `no_free_invocation_slot`(b' 零候选形态);§7.13 grep 放宽至非 REJECTED 前缀 |
| D9 | B#4 | n_a 类 CONVERGENCE(d 补写/rebaselined/apply\|analyzer\|toolchain failed)的 `actual_changed_paths`/`previous_basis`/`verification_id` 逐字段取值规则补冻结(建议:均 null/none,d 补写 previous_basis="none") |
| D10 | F6/F7/F8/F11、B#1/#5/#7 | 文本一致性清扫:event_type 注释补全、derive 注释对齐 §3.6 表格与三 API 名、step5 残留旧文删除、adopted_fingerprint 单数、§3.6 转移表补 REJECTED_ARCH_NOT_ALLOWED、stdout 注释限定 reconciliation 出口 |
| D11 | B#6 | step 1 是否含 unit 状态检查:澄清措辞——冻结为"step 1 校验 unit 状态 ∈ 可执行集(REPAIR_ROUND_RUNNING 等白名单),HELD/终态 → exit 4",不靠剧本纪律 |

## 二、FIX-1(代码修复批次,Codex)

**BLOCKER**
- X1(C1):ref 改 unit 级 canonical(per D1);`_revalidate_round`/冲突判定随改;**新增双 arch 同 round 测试**(arch A 建轮后 arch B 同内容调用必须通过并 build)

**MAJOR(修复)**
- X2(B-MAJOR/C7 合并):wrapper 顶层 catch-all → 固定 schema 错误 JSON + exit 5;argparse 错误亦先出 JSON;残留 worktree 按 D7 处理;反向测试:build_verify_fn 抛非枚举异常 → 单 JSON+exit 5;补 exit∈{4,5} 子进程级测试
- X3(C2):a0 要求已 link PASS 的 invocation_event_id 为非空 int,NULL → 不完整 → held
- X4(C3):append_event 拒 `result=="PASSED"→PASS` 的 CONVERGENCE(PayloadSchemaError 指向 link API);**同步修正依赖此洞的测试**(test_previous_resolver_handles_pass_and_na_history 改走 link API 构造历史)
- X5(C4):`_evidence_truncated` 增查 `error_clusters.truncated`
- X6(D2):previous_evidence.resolve 实现锚点规则 + 两用例
- X7(D4):wrapper 写 ROUNDS_EXHAUSTED status
- X8(D11):step 1 unit 状态白名单检查

**MAJOR(测试补强)**
- X9(C5):link 原子性证伪测试(预占收敛槽 → StateInconsistent 且 link 计数 0)
- X10(C6):order 追踪纳入 resolve/lock/identity;precheck 测试补 invocations_used==0 与零 BUILD_INVOCATION 断言

**MINOR 随批修(小护栏,fail-open 洞)**
- X11(C10/B#8):a0 扫描加 `AND campaign_unit_key=?`
- X12(C11):rebaselined 带非空 invocation → PayloadSchemaError
- X13(C12/B#12):append_status 校验 HELD_REASON 白名单
- X14(C13):create_round 先拒空/空白 ref
- X15(C14/B#10):定义并改抛 AmbiguousQbReference
- X16(B#11):adoption/append_event 的裸 IntegrityError 映射 StateInconsistent;修正固化逃逸的测试
- X17(C16):campaign_verifications 双 UNIQUE raw-SQL 正向测试
- X18(C17):wrapper link_failed 路径测试
- X19(D8):REJECTED_ORPHAN_PASS_HELD 接线

**完成后**:全量回归 + 70 异构复跑 + 新增测试全绿;checker(含新 fence
fixture)全绿;生成 delta 评审包(FIX-1 diff + change_44 diff + 逐
finding 处置表)回送两家评审闭环确认。

## 三、dev_memory TODO(不阻塞,登记留名)

C8(denied 短路先后,竞态罕见)、C9(canonical 落盘时机)、C15(源码
子串断言脆弱)、C18–C23 六条 NIT、评审 A 正面确认节中"gate_view/
lifecycle API 属后续里程碑"的 DoD 措辞显式化。每条登记:来源编号、
现象、约定关门阶段(多数标 P4.9 重构或 P5 前)。

## 四、程序性记录

1. 两家结论冲突(设计侧 0 MAJOR vs 5 MAJOR)按 unanimity 处置:任一家
   的 finding 均计入,单家 PASS 不抵消;F1 由 A 家独得——异构评审的
   价值实证,入 dev_memory。
2. C1 未被 820 测试与 E2E 演练捕获的根因:**多架构维度零真实覆盖**
   (fixture 单 arch、演练单 arch)。教训⑧入方法论账:**测试矩阵必须
   覆盖设计声明的每个基数维度**(arch×round×并发),单点覆盖 = 未覆盖。
3. E2E 演练结论修正一行:演练"全绿"限定于单架构范围,多架构弧留待
   FIX-1 后按 X1 新测试 + 后续三架构真机补验。
