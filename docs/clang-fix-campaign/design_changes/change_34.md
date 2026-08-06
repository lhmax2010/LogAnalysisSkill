# change_34:联合对账原子化与恢复优先序(→ v1.5.10)

**输入**:外部 review(3 BLOCKER + 2 MAJOR)、Claude 复审(4 MINOR)。
**合并关系**:外部 B2 = Claude MINOR-2(外部升级理由成立——不只是
防御性死分支,是**表里没有字段、承诺不可实现**);Claude MINOR-3/4
为独立新发现,本轮一并落。外部 M4(change_31 回写)与 M5(D 项闸门)
维持阻塞状态,见 E 节。

---

## A. BLOCKER-1:联合对账缺原子 API(TOCTOU)

v1.5.9 冻结了分支语义(a/b/b'/c/d)但没冻结执行载体——wrapper 若经
`find_unlinked_pass` 先查列表、再另起事务写入,基数判定与落库之间
存在 TOCTOU 窗口。**修正(已落盘 §4.2)**:冻结
`reconcile_pass_and_invocations(state_db, unit, *, round_index,
arch_norm, failure_key, edit_spec_sha256) -> ReconcileResult`:
单一 BEGIN IMMEDIATE 内**重查两集合**(不信调用方预读)→ 判定 →
完成全部写入(b 的 link+PASS 事件复用 link_verification 校验逻辑于
本事务内、不嵌套第二事务;c 的 ORPHAN_PASS+HELD 同事务;d 补写
幂等)→ 返回 `branch ∈ {linked_already, relinked, orphan_pass_held,
proceed}` 供 wrapper 定出口。`find_unlinked_pass` 降级为内部只读
原语/诊断用途。锁语义同 consume(busy → CAMPAIGN_STATE_BUSY 无写入);
进程文件锁仍为第一道互斥,事务为物理保底。

## B. BLOCKER-2:a 分支"补偿"不可实现(= Claude MINOR-2)

"link 在而 PASS CONVERGENCE 缺 → 补写,invocation 取 link 既有绑定"
——campaign link 表**没有 invocation 列**,绑定不存在;且 v1.5.3 起
link 与 PASS 事件单事务,该半状态**构造上不可达**。**裁决(采外部
推荐项)**:删除补偿承诺(§4.1 a 分支与 §4.1 6b 两处),该形态改判
**StateInconsistent**(外力改库信号,HELD,拒绝矩阵①类)。不采
备选项(link 表加列)——为一个不可达状态扩冻结 schema 不值。

## C. BLOCKER-3:预检早于恢复,PASS 被无关缺失挡死

合法场景:PASS record 已写、link 前崩溃、旧 previous evidence 随后
丢失 → v1.5.9 序在第 1 步预检即 HELD,**到不了第 3 步 relink**。
**修正(已落盘)**:预检自第 1 步移至第 3 步联合对账之后、consume
之前(新第 4 步前半)——恢复路径(a/b 命中即终结)不需要 previous;
预检只在真的要发起新 build 时执行。预检失败落 HELD status 的
v1.5.9 语义不变,仅位置后移。第 1 步收拢为纯身份校验。

## D. Claude MINOR-3/4(独立新发现,已落盘)

- **M3:a/b 出口前执行 d**。探针实锤(附录):round N 崩溃留无
  outcome invocation → round N+1 成功 link → 后续进入全部命中 a)
  幂等出口;b) 的基数过滤按"同 (round, arch)"看不到历史残余,若
  a/b 跳过 d),unit 进 LOCAL_3ARCH_PASS 后**再无 repair-step 入口**,
  "恰好一条 CONVERGENCE"不变量永久缺位。冻结:d 的扫描不过滤
  round,且在 a)/b) 返回之前同样执行。
- **M4:人工恢复算法两处修正**——终态清单补 `ROUNDS_EXHAUSTED`;
  路径改为 `<campaign_ws>/<unit_hash>/<arch_norm>/iter_<round_index>`
  并按 (arch × round) 对枚举(旧文字漏 arch 层,照抄找不到目录)。

## E. 维持阻塞(外部 M4/M5,文件在目标机、本轮无法代落)

1. **change_31.md 一行回写**(确切文本,照抄即可):
   > 状态:已采纳(v1.5.7 落盘);其中唯一索引谓词
   > (`verdict <> 'n_a'`)已被 change_32 supersede——实现方不得
   > 照抄该谓词,以主文 §3.4 为准。
2. **D 项四件**(checker 四规则+fixtures、prompt 同步、Ruff 清零、
   change 落盘)状态不变:未落地,发 P4.5 prompt 前置。prompt 同步
   面本轮又增:reconcile API 与 ReconcileResult、步骤序(对账→预检→
   计费)、本轮五组新 DoD 用例。

## F. DoD

A/B/C/D 落盘 v1.5.10 且 DoD 用例齐备(已完成)+ E 两项落地。
**E 完成前不发 P4.5 实现 prompt**(与 change_33 D 节合并计数)。

---

## 附录:探针实测输出(2026-08-04 第三轮,内存 SQLite)

```
b) 基数过滤(round=2 视角)命中残余 = 0 → X1 不影响 b) 判定
d) 全局残余扫描 = [(1,)](即 X1=1)——若 a/b 提前返回跳过 d,
  unit 进 LOCAL_3ARCH_PASS 后再无 repair-step 入口,
  X1 的"恰好一条 CONVERGENCE"不变量永久缺位
[OK] a/b 返回前执行 d:X1 补写落座,残余清零 —— 修正可行
```
