# change_35:逐组配对与 PASS payload 确定性重建(→ v1.5.11)

**输入**:外部 review(2 BLOCKER + 3 MAJOR + 1 MINOR)、Claude 复审
(零新发现,收敛确认)。
**性质**:B1 改动 §4.1 冻结分支表与 §4.2 冻结 API,走 R1/R2。

---

## A. BLOCKER-1:跨 round 补写误 orphan 合法历史 PASS

**归因(记账)**:change_34 乙-M3 把 d 子步扩为跨 round 扫描时,
S_pass 仍锚当前 round——**用当前 round 的 PASS 集合给历史 round 判
"无匹配"是跨组污染**。这是 change_34 自己引入的回归,同一唯一索引上
连续第三轮碰撞面漏判;change_33 F 节的时序教训只在轮内应用、未做
跨轮分组推演。

**探针(附录)**:v1.5.10 语义下 round 1 的未 link PASS 对
S_pass(round=2) 不可见,X1 被 d 误 orphan 占槽,P1 事后 relink 撞
IntegrityError——死路复现;逐组配对下 round 1 组见到自己的 PASS,
冻结不补写,relink 通道保留。

**修正(已落盘)**:对账作用域 = (unit, arch) **全部 round,逐组
配对**:当前 round 组走 a/b/b'/c;**新增 h 分支**——历史 round 组
S_pass(r) 非空 → 该组按 c) 冻结(ORPHAN_PASS + HELD,组内 S_orph
一并不补写)。**不自动 relink 历史轮**:历史轮遗留未 link PASS
意味着剧本在未收口的轮上继续推进,自动收编到过去的轮或自动作废
都属于猜。d 的前置条件改为"**其所在组已证 S_pass(r) 为空**"。

## B. BLOCKER-2:崩溃后 PASS payload 无法重建

`actual_changed_paths[]` 只在 BuildVerifyResult 内存/结果 JSON,
不在 PASS record;reconcile 手里只有 key/hash。**修正(逐字段
冻结,已落盘 §4.1 b)**:
- `actual_changed_paths` = 已验证 worktree 内
  `git diff --name-only <base_commit>..<verified_commit_sha> --`,
  POSIX 归一化 + 字典序排序;diff 失败/commit 不在 → worktree 已损
  → 转 c);
- `verification_id`/时间字段 = PASS record 同名字段;
- PASS record 的 arch(raw)白名单映射后必须 == arch_norm,不符 → c);
- result=PASS, verdict=n_a, evidence=null,previous 按 6b PASS 规则;
- **任何必填字段仍无确定性来源 → 不猜,转 c)**。
DoD 增 parity 用例:重建清单与 build 当时记录逐字节一致。

## C. MAJOR × 3(已落盘)

- **M3**:`ReconcileResult` 增 `verification_id: str | None`
  (linked_already/relinked 必填)与 `held_rounds` 清单;wrapper
  stdout PASS JSON 仅由返回值装配(静态断言:无 link 表回查)。
- **M4**:第 1 步"基线 evidence 存在"收窄为**仅事件与元数据身份、
  不读 evidence 文件**——在此读文件会重现 B3 形态(恢复路径不依赖
  基线 evidence);文件级校验归第 4 步预检/第 5 步调用前校验。
- **M5**:a 分支半状态改**事务化出口**——同事务写
  HELD(state_inconsistent, arch_norm) 提交后返回
  branch='state_inconsistent_held',wrapper exit 4
  REJECTED_STATE_INCONSISTENT;**不抛异常**(异常回滚会吞 HELD,
  wrapper 捕获另写又破坏单事务)。append_status 注释同步:
  state_inconsistent 按写入方上下文定 arch(reconcile 场景必填)。

## D. MINOR(已落盘)

泄漏窗口段旧路径 `<unit_hash>/iter_<round>` 统一为
`<unit_hash>/<arch_norm>/iter_<round_index>`,全文单一写法。

## E. 维持阻塞(不变,累计)

change_31 一行回写(文本见 change_34 E.1)+ D 项四件。**prompt
同步面累计**:reconcile 全签名族(含本轮两字段一分支)、
a/b/b'/c/h/d 分支表、九步序(对账→预检→计费)、v1.5.10–11 全部
新增 DoD 用例。**E 清零前不发 P4.5 prompt。**

## F. DoD

A/B/C/D 落盘 v1.5.11 且 DoD 用例齐备(已完成)+ E 两项落地。

---

## 附录:探针实测输出(2026-08-04 第四轮,内存 SQLite)

```
== v1.5.10 语义(S_pass 锚当前 round、d 跨 round)==
S_pass(round=2) 命中 = 0 → 看不到 P1
d) 跨 round 残余扫描命中 = [(1, 1)] → X1 被判'无匹配 PASS'
[BUG 复现] P1 永久无法 relink: IntegrityError —— 合法历史 PASS 被误 orphan 挡死
== 修正语义(按 (unit,arch) 全 round 分组、逐组配对)==
round 1 组:未 link PASS=1 → HELD 冻结、不补写(留待人工/同组 relink)
[OK] 逐组配对下 P1 的 relink 通道保留 —— 修正可行
```
