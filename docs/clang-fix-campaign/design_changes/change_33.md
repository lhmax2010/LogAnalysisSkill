# change_33:崩溃恢复联合对账与 change 台账收口(→ v1.5.9)

**输入**:外部 review(1 BLOCKER + 4 MAJOR + 1 MINOR)、Claude 复审
(执行断层四项 + 1 MAJOR 新发现 + 2 MINOR 偏差)。
**性质**:BLOCKER 修正改动 §4.1 冻结步骤序,走 R1/R2 流程。

---

## A. BLOCKER:PASS 崩溃恢复与唯一索引冲突(外部 B1)

**问题**:v1.5.8 步骤序——第 1 步补孤儿 invocation、第 3 步 PASS
对账。崩溃场景(consume 已计费 → build_verify 已写 PASS record →
wrapper 于 link 前崩溃)重入时:第 1 步把该 invocation 写成
`orphan_invocation` 占掉 `ux_convergence_per_invocation` 唯一槽,
第 3 步 b 分支补 link + PASS CONVERGENCE(必须引用同一 invocation)
→ IntegrityError,**合法恢复路径永久不可达**。v1.5.7 谓词下 n_a
不占槽、该序列反而通过——这是 change_32 A1 收紧引入的回归。

**探针结论(附录 B,实测)**:死路复现(IntegrityError);修正序
(relink 先行)通过;纯孤儿场景不受影响。

**修正(已落盘 §4.1 第 3 步,顺序本身是契约)**:合并为**联合对账**:
1. 扫描 S_pass(未 link PASS)与 S_orph(无 outcome invocation);
2. a) 已 link → 幂等 exit 0(6b 补偿:link 在而 PASS CONVERGENCE
   缺 → 补写,invocation 取 link 既有绑定);
3. b) S_pass 恰一条精确匹配 **且** 同 (round, arch) 的 S_orph
   恰一条 → **原子补 link + PASS CONVERGENCE(落座该旧 invocation
   槽)**,不计费不 build;
4. b') S_pass 恰一条但 S_orph 为零(PASS 无处落座——其 invocation
   已有 outcome,外力改动信号)或多条(归属无数据可证)→ **不猜**,
   按 c 处理;
5. c) 冲突/歧义 → ORPHAN_PASS + HELD(reason=orphan_pass, arch_norm),
   **不补写任何孤儿**(冻结现场);
6. d) PASS 侧完结后,残余无匹配 PASS 的 S_orph 才补写
   `orphan_invocation`——**补写永远在 relink 之后**。

BUILD_INVOCATION 契约行的"重入时先补写再继续"与 DoD 的"第 1 步
扫描补写"措辞同步改写;DoD 新增顺序反向验证(补写挪回 relink 前
→ 用例必须转红)与 b' 零/多候选两变体。

## B. MAJOR:预检失败路径 HELD 不可达(Claude 复审新发现)

v1.5.8 契约要求 previous_evidence_missing 的 CONVERGENCE 必带
invocation_event_id,而预检在 consume 之前、无 receipt;原文又写
"预检失败不写任何事件"→ 主路径下 CONVERGENCE 与 HELD 都落不下,
unit 卡死 REPAIR_ROUND_RUNNING,rebaseline 授权检查永远找不到依据。
**修正**:预检失败 → 不写 gate 事件,但**必须**
`append_status(HELD_FOR_INVESTIGATION, previous_evidence_missing,
arch_norm)` 后 exit 4;6a 为 TOCTOU 备份路径(有 receipt,照写事件)。
DoD 补正例(该 arch rebaseline 可用、他 arch 被拒)与反向验证
(去掉 status 写入 → 复现卡死)。

## C. MAJOR × 3:提案与主文的"第二权威"收口(外部 2/3/4)

裁决:**主文为唯一契约权威**(已写入 v1.5.9 台账)。change_32 回写
四处:①payload 双写为准(作废"仅真实列");②result 按 reason 分流
(作废"非空只能 PASS/FAIL"——orphan 携 id 且 n_a);③不引入
PENDING_CLEANUP(status_log + 派生路径方案,人工恢复枚举算法已在
主文 §4.1 显式化:终态 SQL → iter_<round> 枚举 → workspace 安全
清理 API,marker 拒删转人工,带外恢复不写事件仅限人工);
④TG 错误码名对齐 §4.3(StateInconsistent /
REJECTED_PRIMARY_BASELINE_MISSING)。

## D. MAJOR:执行断层(外部 5 + Claude 复审四项)——发 prompt 阻塞项

以下截至 v1.5.9 **均未落地**,主文台账已加诚实标注("设计检查
OK: 0 problem 不证明本版新契约"):
1. p45-implementation-prompt.md:旧索引名清零、InvocationReceipt /
   条件枚举 / 联合对账序同步、DoD 新用例(TG 系 + 本轮 A/B 用例)、
   路径修正(tools/ 实际位置);
2. check_design_doc.py:CK-API-01(冻结 API ast.parse)、CK-IDX-01
   (索引名 design/prompt 集合一致)、CK-XREF-01(§ 引用可解析)、
   CK-MMD-01(Mermaid 先声明后引用),各配失败 fixture;
3. Ruff 18 项清零(E741 改名、E501 断行)+ `ruff check --select E,F`
   入 checker 自测闸门,重跑 20/20 + v1.5.2 回归确认行为不变;
4. 本文件与 change_32 修订版落盘至 design_changes/。

## E. MINOR:change_31 台账收口(外部 6)

change_31.md 头部状态改为:**"已采纳(v1.5.7 落盘);其中唯一索引
谓词(`verdict <> 'n_a'`)已被 change_32 supersede——实现方不得
照抄该谓词,以主文 §3.4 为准"**;§0 supersede 台账同步一行。

## F. 方法论教训(入 §7.13 精神,供后续 review checklist)

连续两轮同一索引漏判:上轮漏**取值逃逸面**(验证了意图路径、没枚举
n_a 侧写入面),本轮漏**时序碰撞面**(枚举了数据组合、没枚举崩溃
重入的步骤序)。固化:**唯一约束/CHECK 的探针必须同时枚举
①全部写入方的取值组合(§7.13 6f)与②跨崩溃重入的步骤时序**——
每条恢复路径(orphan 补写、relink、6b 补偿、rebaseline)两两组合
在同一约束下走一遍。

---

## 附录 B:探针实测输出(2026-08-04 第二轮,内存 SQLite)

```
== v1.5.8 现行步骤序(第1步补写先行)==
[BUG 复现] PASS relink 被自己的补写堵死: IntegrityError(UNIQUE constraint failed: ev.invocation_event_id)
  → 合法崩溃恢复路径永久不可达;v1.5.7 谓词下该序列反而通过(n_a 不占槽)——A1 收紧引入的回归
== 修正后步骤序(联合对账:先 relink、后补孤儿)==
[OK] relink 先行:PASS 占 X 槽成功
[OK] 残余无 outcome invocation = 0(无需补写)
== 修正序下纯孤儿场景(无 PASS record)仍工作 ==
[OK] 补 orphan(X1)→ 重试(X2)→ 实质 outcome 序列不受影响
```

## DoD

A/B 落盘 v1.5.9 且 DoD 用例齐备(已完成)+ C 回写(已完成,
change_32 修订版)+ D 四项落地 + E 一行收口。**D/E 完成前不发
P4.5 实现 prompt**。
