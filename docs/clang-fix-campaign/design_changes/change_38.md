# change_38:身份权威复位与完整性预检(→ v1.5.14)

**输入**:外部 review(1 BLOCKER + 3 MAJOR + 1 MINOR)、Claude 复审
(1 MINOR + 1 NIT)。
**性质**:撤销 v1.5.12 引入、v1.5.13 沿用的步骤重排,走 R1/R2。

---

## A. 丁-B1(BLOCKER):对账前移撤销,恢复 create_round → 对账

**归因**:对账前移是 change_36 的附带裁量(change_37 F①刚立
"附带裁量单独立项"之规,病例本尊却已随 v1.5.12 混入并存活到
v1.5.13)。旁路链:`--round-index 2 --edit-spec round1_hash`
→ 对账步把旧 hash 判为"当前组"→ linked_already exit 0 → 后置的
create_round 永不执行 ⇒ UNIQUE 同 hash 拒占新轮、序号连续性、ref
绑定、闸一 max_rounds **全部旁路**。

**前提复审**:前移动机(历史 relink 出口留空 round)已被 change_37
"补账不授出口"消解——other-round relink 走 proceed 照建 round;
仅 HELD 出口可能留空 round,而 HELD 下 campaign 已冻结,可接受。
**冻结原则:成功出口永远不得先于 round 权威绑定。**恢复原序:
锁 → 身份校验 → create_round(+复核)→ 联合对账 → 预检+consume →
build → 6a/6b → 释锁。全部步号引用回卷(上轮 Claude 复审列出的三处
"第 3 步"残留在原序下自然归正)。DoD 增双向用例:同 hash 占新轮的
调用必须死在 create_round(反向验证:恢复 v1.5.12 序 → 该调用
exit 0 逃过全部身份校验,必须能捕获)。

## B. 丁-M4(MAJOR):a0 全 round link↔CONVERGENCE 完整性预检

半状态检查此前只挂当前 spec 的 a 分支。探针实锤掩盖路径:历史
round 的 link 在、PASS CONVERGENCE 被外力删 → 该 verification 不在
S_pass(已 link)、其 invocation 在 S_orph(无 outcome)、组内
S_pass 为空 ⇒ **d 把它补成"正常孤儿"**,不一致被静默掩盖。
**修正**:新增 **a0 预检,先于一切分支**——全 round 每条已 link
verification 必须对应**恰一条** PASS CONVERGENCE,且
unit/round/arch/verification 逐项与 link 一致,result=PASS、verdict=n_a,
invocation 指向同 unit/round/arch 的 BUILD_INVOCATION。这不是
`EXISTS(verification_id)` 弱检查:DB 唯一索引只锁 invocation,不锁
verification_id。缺失/重复/错绑任一形态 →
state_inconsistent_held(同事务 HELD)。a0 先行,b/d 才可信;
DoD 补缺失、重复、错 round/arch/invocation 反例。

## C. 丁-M2/M3/M5(MAJOR×2 + MINOR,契约一致性)

- **M2**:§3.4 未链接 PASS 选择规则重写(旧文按 (unit, round,
  arch) 直接选,与"record 无 round 列"矛盾,两套算法并存)——
  统一为 failure_key+arch 候选 + edit_spec 反查归属;
  `find_unlinked_pass` **去 round_index 形参**(按 round 过滤是旧
  契约残留),返回含 edit_spec_sha256 供归属诊断。
- **M3**:stdout JSON 固定新增
  `"reconciliation": {"other_round_relinks": [],
  "non_campaign_verification_ids": []}` 与 `"warnings": []`——所有
  branch 均输出、空时空数组;**单 JSON 契约不破,禁止 JSON 外附加
  文本行**(此前"stdout WARN"无落点,附加文本会破坏机器消费)。
  非空 schema 同步冻结:`other_round_relinks` 序列化为
  `{round_index, verification_id, invocation_event_id}` 对象数组(禁止
  JSON 三元数组),`non_campaign_verification_ids` 为排序后字符串数组,
  `warnings` 为 `{code: non_campaign_verification, verification_id}` 对象
  数组;全部按冻结键确定性排序。
- **M5**:`historical_relinks` 更名 **`other_round_relinks`**
  (r 与当前入参无大小约束,可含 future round);DoD 的
  `ReconcileResult.verification_id` 更正为 `current_verification_id`。

## D. 丁-NIT(Claude):聚合职责边界

"由其 edit_spec 组自行推进"无主语。冻结:**reconcile 不触发聚合/
沙箱提交;各 edit_spec 组三 arch 齐备性的检查与推进由编排层(剧本)
在 unit 出口后执行**——本 API 职责止于账本一致。

## E. 维持阻塞(累计)

change_31 一行回写 + D 项四件 + **目标机同步 v1.5.14**(v1.5.12
跳过;v1.5.13 已落盘,本版覆盖)。prompt 同步面累计至 v1.5.14。
另按 Claude 复审建议,checker 增补一条 fixture 素材:**步骤重排后
全文步骤号引用核对**(CK-XREF-01 只查 § 引用,管不到步号)。
**E 清零前不发 P4.5 prompt。**

## F. 方法论记账(续 change_37 F)

**④前提失效即裁量复审**:对账前移的动机(空 round)被 change_37
消解后,裁量本身没有被回头审视——支撑某裁量的前提被后续变更
移除时,该裁量必须重新立案,而不是靠惯性存活。**⑤"当前组"的
判定输入必须先经权威绑定**:任何以调用方入参(round/hash)界定
作用域的逻辑,其入参必须先过 DB 权威校验——对账前移的本质错误
是让未经绑定的入参直接驱动了成功出口。

## G. 冻结裁决(2026-08-04)

开发者确认 v1.5.14 设计语义正式 Frozen。change_38 后最终复审
又将 a0 收紧为“恰一条 PASS CONVERGENCE +
unit/round/arch/verification/invocation 精确绑定”,并冻结
stdout 非空元素 schema 与确定性排序;`check_design_doc.py`
返回 0 problem。E 节剩余项定性为实施/目标机/prompt 发布闸门,
不再阻塞设计语义冻结,但 E 清零前仍不得发布 P4.5 prompt。
Frozen 后任何设计修改必须按 R1 新建 `change_39.md` 或后续编号,
禁止静默改写 v1.5.14-FROZEN。

---

## 附录:探针实测输出(2026-08-04 第七轮,内存 SQLite)

```
== v1.5.13 语义(半状态检查只挂当前 spec 的 a 分支)==
S_orph(round1) = [(1,)](X1 在列);S_pass(round1) = [](V1 已 link,不在未 link 集合)
→ round1 组 S_pass 为空 ⇒ d 补写 orphan_invocation(X1) —— 半状态被 d 掩盖成'正常孤儿'
== 修正:a0 全 round link↔CONVERGENCE 完整性预检 ==
完整性缺口 = [('V1',)] → state_inconsistent_held(同事务 HELD),先于 b/d —— 掩盖路径关闭
```
