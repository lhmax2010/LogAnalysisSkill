# change_32:v1.5.7 双 review 合并修正(→ v1.5.8)

**状态(v1.5.9 收口)**:已采纳并落盘于 design.md v1.5.8。**本文与主文
不一致处一律以主文为准**;下列四处为落盘时的有意修订,已回写(原稿
文本保留删除线语义、以"作废"标注)。A1 的步骤序含隐藏回归,由
**change_33 补正**(第 3 步联合对账,relink 先行)。

## 落盘时的四处修订(v1.5.9 回写,消除"第二权威")

1. **A2.2 存储位置(作废原稿"仅真实列、payload 不含")**:落盘为
   **payload 含 `invocation_event_id` 且与真实列同值**,走 v1.5.6
   提升规则(同 round_index/arch_norm)。理由:原稿方案迫使
   `append_event` 改冻结签名,提升规则零签名变更且与既有契约同构。
2. **A3 条件表(作废原稿"invocation_event_id 非空只能 PASS/FAIL")**:
   orphan 补写、apply/analyzer/toolchain failed、previous_evidence_missing
   **携带 invocation_event_id 且 result=n_a**。落盘口径:**按 reason
   分流**——PASS/FAIL 限 6a/6b 实质 outcome;n_a 限六 reason 白名单;
   `invocation_event_id IS NULL` 仅 reason='rebaselined'。
3. **B7(作废原稿"落 PENDING_CLEANUP 审计事件")**:落盘为**不引入
   新事件类型**——status_log 终态行为凭证、`iter_<round>` 派生路径
   可枚举;人工恢复算法见主文 §4.1(v1.5.9 显式化)。
4. **错误码名对齐 §4.3(作废 TG 表中的 E_* 临时名)**:
   `E_INVOCATION_BINDING` → 绑定校验失败复用 **StateInconsistent**
   (持错 receipt/状态被篡改同族信号,不新增码);
   `E_PRIMARY_FINGERPRINT_MISSING` → **REJECTED_PRIMARY_BASELINE_MISSING**
   (已入 §4.3)。prompt 与测试断言一律按 §4.3 名。

## 原始裁决记录(历史,保留供审计)

A1 索引重锚 / A2 receipt 端到端 / A3 条件枚举 / A4 冻结签名语法 /
B5 HELD 绑 arch / B6 三元组 CHECK / B7 泄漏窗口 / B8 primary-first /
C prompt 补丁 / D 测试闸门 TG-1~8 / E checker 硬化(CK-API-01 /
CK-IDX-01 / CK-XREF-01 / CK-MMD-01 + Ruff 清零)/ F 执行顺序与 DoD。
详细内容见 v1.5.8 主文对应章节;TG 编号在主文 DoD 中已展开为具体
用例文本,以主文 DoD 为准。

## 附录 A:探针实测输出(2026-08-04 第一轮,内存 SQLite)

```
[OK] 合法序列: orphan补写(X) + 实质outcome(Y) 共存通过
[OK] TG-1 同 invocation 第二条 PASS(verdict=n_a): IntegrityError(UNIQUE constraint failed: campaign_gate_events.invocation_event_id)
[OK] TG-2 同 invocation PASS 后补实质 verdict: IntegrityError(UNIQUE constraint failed: campaign_gate_events.invocation_event_id)
[OK] 同 invocation 二次实质 outcome: IntegrityError(UNIQUE constraint failed: campaign_gate_events.invocation_event_id)
[OK] rebaselined(NULL) 多条不撞索引(合法,由 reason 白名单约束)
[OK] 反向验证: v1.5.7 谓词下同 invocation 双 PASS 落库成功 —— 逃逸面实锤
[OK] TG-5 三元组半空插入: IntegrityError(CHECK constraint failed: ...)
[OK] 全空(arch 拒绝)与全非空均可插入
```

结论:v1.5.7 谓词的 PASS 逃逸为实测事实而非纸面推理;v1.5.8 索引对
三类违例均拒、对合法序列均放行。**局限(change_33 教训)**:本轮探针
只枚举了"事件类型 × reason"的数据组合,未枚举**崩溃重入的步骤时序**,
漏掉第 1 步补写与第 3 步 relink 争夺同一槽的死路——已由 change_33
探针复现并修正。
