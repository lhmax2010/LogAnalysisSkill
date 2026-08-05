# change_36:归属算法与统一分组(→ v1.5.12)

**状态(change_37 收口)**:v1.5.12 快照**作废、从未落盘**。本文的
B1(归属)与 B2 主体(h 撤销、统一 b/b'/c、对账前移)被 v1.5.13
继承;以下三处被 change_37 **supersede**,实现方不得照抄:
①"a 分支扩至任意 round"——收回(聚合死锁+计费绕过);
②归属零/多命中"按 c 写 ORPHAN_PASS"与"多命中合法可构造"——
改忽略+non_campaign 清单 / state_inconsistent_held(UNIQUE 禁止);
③"verification_id 取最大 round"——改 current/historical 双维度。
以 v1.5.13 快照为准。

**输入**:外部 review(2 BLOCKER + 2 MAJOR + 1 MINOR)、Claude 复审
(2 MINOR)。
**性质**:B2 撤销 v1.5.11 冻结的 h 分支并重排步骤序,走 R1/R2。

---

## A. BLOCKER-1:S_pass(r) 缺 round 归属算法

未 link 的 verification_records 没有 round 列,campaign link 的
round_index 只在 link 后存在——v1.5.11 的"round r 的未 link PASS"
无可实现定义。**冻结(已落盘)**:①failure_key + arch 匹配候选;
②`record.edit_spec_sha256` 反查本 unit `campaign_rounds`,恰一命中
→ 归组;③零命中(不属任何轮)或多命中(**同 edit_spec 多轮重试
合法可构造,探针实锤**)→ 不猜 round,record 按 c) 处理
(ORPHAN_PASS 记 attribution 明细),不入任何组。S_orph 有真实
round 列,归属天然。

## B. BLOCKER-2:h 分支被证伪,撤销改统一规则

**认账**:change_35 写的"relink 通道保留"是纸面承诺——
HELD(orphan_pass) 是终态,rebaseline 只认 previous_evidence_missing,
release 只放副本不恢复状态,通道不存在;合法 PASS 会被永久冻结。
外部论证成立:**唯一配对 + 身份全验(failure_key、edit_spec 归属、
marker 完好)的 relink 不是猜,是补完一次被中断的写入**;上轮真正
的猜是"历史组出现即异常需人工"这个假设本身。

**裁决(采外部推荐项,已落盘)**:h 撤销,**全部 round 组统一
b/b'/c 规则**——任意组唯一配对即同事务 relink(link 落该组
round),歧义才 c);分组与 r 和当前入参的大小关系无关(r>当前
不再是未定义形态)。两项附带修正:
- **对账前移至 create_round 之前**(第 2↔3 步互换):统一规则下
  历史组 relink 出口若在 create_round 后发生,本次已建的当前 round
  成为无 invocation 的**空 round**、白占闸一名额;前移后
  create_round 仅在 branch='proceed' 时执行。对账所需
  failure_key/edit_spec_sha256 第 1 步已备,无 round 依赖。
- **a 分支扩至任意 round**:本 arch 任一 round 已有 linked PASS →
  修复目标已达成,linked_already 出口(与统一分组同构)。

## C. MAJOR × 2(外部,已落盘)

- **M3 锁粒度**:文字键 (unit, arch, round) 与锁文件路径
  (workspace_root 只含 unit+arch)互相矛盾;且对账扫全 round,
  跨 round 并发本就必须互斥。冻结为 **(unit, arch_norm)**;DoD 增
  "同 unit/arch 不同 round 并发 → 一方 BUSY"变体。
- **M4 时间落点**:契约 payload 只有 `at`,"PASS record 时间入
  payload 原字段"无落点。裁决取外部方案一:**`at` = 重建(事件
  写入)时刻;原始时间不入 payload,经 verification_id 回查
  verification_records**——权威留在源表不复制,避免契约扩列连锁
  (validator/checker/prompt)。

## D. MINOR × 3(外部 M5 + Claude 两条,已落盘)

- **外部 M5**:diff 命令钉死为
  `git diff --name-only --no-renames -z <base> <verified> --`,NUL
  切分、POSIX 归一、字典序——排除 rename 侦测、引号转义与含换行
  文件名对本机 Git 配置的依赖;DoD parity fixture 须含触发 quoting
  的文件名(不带 -z 必须失败)。
- **Claude M1 出口优先级**:多组并行命中此前未定义。冻结:写入
  全部执行,branch 按 state_inconsistent_held > orphan_pass_held >
  linked_already/relinked > proceed——任一组触发 c) 即整体 HELD,
  **exit 0 不得把异常藏在成功后面**;relinked 的 verification_id 取
  最大 round。
- **Claude M2 第 1 步收窄补全**:conf hash 与 src_clean HEAD 两项
  文件读取自第 1 步删除(与 M4/B3 同构——relink 不 build 不碰
  conf/src;第 5 步调用前本就有权威校验,第 1 步副本是冗余且有害的
  提前拦截)。

## E. 维持阻塞(不变,累计)

change_31 一行回写 + D 项四件。prompt 同步面累计:reconcile 全
签名族与归属算法、统一分支表与优先级、v1.5.12 新九步序
(锁→身份→**对账**→create_round→预检→计费→build→6a/6b→释锁)、
v1.5.10–12 全部 DoD。**E 清零前不发 P4.5 prompt。**

## F. 方法论记账

change_35 的 h 分支是"以不猜为名的猜"——把确定性可判的场景
(唯一配对+全验)让渡给人工,本质是对"历史组=异常"做了无证据
假设,且未验证 HELD 的恢复边是否存在。固化两条:**①任何"转人工"
裁决必须同时给出人工恢复边(状态机上存在回边),否则它就是终态
死路的委婉说法;②fail-closed 的对象是"无法确定的事",不是
"可以确定但罕见的事"。**

---

## 附录:探针实测输出(2026-08-04 第五轮,内存 SQLite)

```
[OK] B1 归属(唯一):P1.edit_spec=aaa → round 1(campaign_rounds 反查,无需 vrec 存 round)
[实锤] 归属歧义可构造:edit_spec=aaa 命中 2 个 round → 不猜,转 c)
[OK] B2 统一规则:历史 round 1 组唯一配对 → 同事务 relink 落座,无 HELD、无终态死路
[OK] 残余 = 0;且 reconcile 前移至 create_round 之前 → 本次入口不再产生空 round
```
