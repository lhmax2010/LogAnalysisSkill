# change_37:补账/出口解耦与归属修正(→ v1.5.13)

**输入**:外部 review(4 BLOCKER/MAJOR)、Claude 复审(1 BLOCKER +
1 MINOR)。两方在 a 分支扩展上**独立同判 BLOCKER**(聚合死锁推演
完全同构),这是异构互查的理想形态。
**性质**:收回 v1.5.12 快照的两处附带裁量;**v1.5.12 快照作废、
从未落盘、禁止落盘**,由 v1.5.13 快照直接取代。

---

## A. 丙-B1:落盘断层的记账与规程冻结

外部 B1 指出目标机 design.md 仍为 v1.5.11 而 change_36 自称"已
落盘"。**事实**:本工作流的交付物是快照文件
(`clang-fix-campaign-design-v1_5_N-draft.md`),评审对象亦为快照
(Claude 复审已按此口径执行);目标机 design.md 的替换是发布闸门
动作,与 change_31 回写、checker、prompt 同属 E 项。**规程自本版
冻结**:①change 文档中"已落盘"一律指快照;②目标机未同步前,
对旧 design.md 跑 checker 的 `0 problem` **不代表**新契约(已在
台账标注);③快照落盘时**跳过被作废的中间版**(v1.5.12 不落,
直接 v1.5.11 → v1.5.13)。

## B. 丙-B3(BLOCKER,双方同判):a 分支扩展收回

v1.5.12 快照把 a 扩至"本 arch 任一 round 已 link 即 exit 0"。
推演(Claude 复审给出完整链条):round 1(spec v1) primary/arch2
PASS、arch3 FAIL → round 2(v2);调 repair-step(primary, round2)
→ 被 round 1 link 短路 exit 0 **且不计费** → v2 组永远只有 arch3
可能 PASS → §3.4 聚合(同一 edit_spec_sha256 三 arch 齐备)永久
缺员 → unit 死锁;不计费同时绕过双闸的失控保护。**根因**:混淆
"某 arch 在旧 spec 下 PASS"与"整包在同一 spec 下三 arch 齐备"。

**修正(已入 v1.5.13 快照)**:
- a) 回收为 `link.edit_spec_sha256 == 本次 edit_spec`(由
  UNIQUE(unit, edit_spec_sha256),同 hash ⟺ 同 round);
- **统一规则重新定性**:统一的是"账本补全"动作,不是"成功出口"
  ——历史组 relink 只补该轮的账,branch 仅由当前 edit_spec 组
  决定;历史 relink 非空照走 proceed(照建照测照计费);
- DoD 补正面断言("round N 部分 PASS → N+1 同 arch 必须重新
  build")与卡死复现反向验证。

## C. 丙-B2(BLOCKER):归属零/多命中的可执行落点

v1.5.12 快照令零/多命中"按 c) 写 ORPHAN_PASS"——不可执行:
ORPHAN_PASS 契约必填 round_index,零命中无合法 round,写事件必然
猜或破 schema。且"多命中合法可构造"**有误**:
`UNIQUE(campaign_unit_key, edit_spec_sha256)` 物理禁止同 spec 占
两轮(本轮探针实锤;上轮探针的多命中系绕过约束直写所得——
**探针教训:谈"可构造"前先验证约束存在性**)。

**修正(已入快照)**:①恰一命中 → 归组;②零命中 = 非 campaign
所有 → **无 gate 事件、无 HELD**,入
`non_campaign_verification_ids` + stdout WARN(campaign 账本只记
campaign 事实,对非己方记录无管辖权);③多命中 = 约束被破坏 →
`state_inconsistent_held`(同 a 半状态的事务化出口)。

## D. 丙-B4(MAJOR):ReconcileResult 当前/历史双维度

多组补完与单值结果不相容;"verification_id 取最大 round"作废——
最大历史 round 的 verification 不属于本次请求,拿它装配 stdout
PASS 是张冠李戴。**修正(已入快照)**:
`current_verification_id` / `current_relinked_invocation_event_id`
(出口与 stdout 仅由此装配)+
`historical_relinks: tuple[(round, verification_id, invocation_event_id)]`
+ `non_campaign_verification_ids`;优先级修订:HELD > 当前组成功 >
proceed,**历史 relink 永不抬升 branch**。

## E. 维持阻塞(不变)

change_31 一行回写 + D 项四件 + **目标机 design.md 同步至
v1.5.13**(v1.5.12 跳过)。prompt 同步面累计至 v1.5.13:归属四则、
双维度 ReconcileResult、补账/出口解耦语义、本轮全部 DoD。
**E 清零前不发 P4.5 prompt。**

## F. 方法论记账(续 change_36 F)

①**附带裁量单独立项**:a 扩展、对账前移这类"顺手优化"混在主
变更里,评审注意力被主变更吸走——今后附带修正在 change 文档单列
"附带变更"节,逐条独立论证;②**探针先验约束**:构造反例前先
确认 DDL 允许该构造,绕约束造出的"反例"会把外力改库误标为合法
路径;③**出口语义与账本语义分离**:凡"修复了历史状态"的操作,
默认不改变当前调用的成功判定,除非显式论证。

---

## 附录:探针实测输出(2026-08-04 第六轮,内存 SQLite)

```
[实锤] 同 unit 同 edit_spec 占两轮被 DDL 物理禁止: UNIQUE constraint failed:
  campaign_rounds.campaign_unit_key, campaign_rounds.edit_spec_sha256
  → 归属'多命中'在完好约束下不可达;上轮探针的多命中系绕过约束直写所得,
    不是合法路径 —— 多命中出现即约束被破坏,应判 StateInconsistent 而非'合法重试'
[OK] 唯一命中路径正常:bbb → round 2;零命中 = record 非本 campaign 所有,无合法 round 可填
```
