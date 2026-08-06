# R14 第二轮 delta 闭环裁决:change_45 + FIX-1 收尾

**输入**:评审 B(delta)+ 评审 A(R2-1…R2-16)。两家**独立收敛**于
同一核心结论:①FIX-1 代码闭环(附小 finding);②change_44 **处置表
失实**(D3/D10 标 Closed 而正文未改),不予确认;③merge 维持 blocked。
**总裁决:采纳两家一致意见。开 change_45(纯文本/checker 修订,
零代码语义变更)+ FIX-1 三条随手补;完成后回送第二轮 delta 确认。**

---

## 零、程序性裁决(最重要,先立规)

**处置表失实是本轮头号问题,优先级高于任何技术 finding。**
finding-disposition.md 把 D3/D10/D2 等标 Closed,但正文未改——delta
包的**自证材料不可信**。据此确立两条硬规矩(入方法论账⑨):

1. **"Closed" 必须由正文 diff 证明,不由 change 记录声明**:今后任何
   处置表的 Closed 项,须附"正文修改行号 + 修改前后片段",评审可直接
   对 diff 核验;change_*.md 的记录**弱于**权威正文,冲突以正文为准
   (本轮 R2-13:PASS-bound 中间态,记录强于正文,即按此裁——以正文
   "被 record 引用的副本一律不清"为准,change 记录改口径)。
2. **本轮起,Codex 每个 change 批次交付时自附"正文 grep 自证"**:对
   每条 D/X 项,grep 出正文实际修改点贴入报告;做不到 grep 自证的
   Closed 一律视为 Open。

## 一、FIX-1:确认闭环,三条随手补(不阻塞代码确认)

两家一致 CONFIRM FIX-1 功能闭合(X1–X19 真实、双 arch 测试可证伪、
catch-all/映射/cleanup fail-closed 正确)。三条随批补:

- **R2-1/R2-16(canonical 落盘原子性)**:改 `O_CREAT|O_EXCL`+分离
  write 为**写唯一临时文件 → `os.link` 原子发布(EEXIST 走 hash
  比对)**,消除并发半字节读与 open-write 间崩溃留零字节 canonical
  的死锁;change_45 同步冻结该落盘原语(§4.1 补 O_EXCL/原子发布规则)。
- **R2-2(X6 测试不可证伪)**:rebaselined 锚点更早处埋一条实质 FAIL
  收敛,使修复前代码穿越锚点取到它、修复后取锚定 REPRODUCE——补齐
  红/绿双态。
- **R2-3(X11 测试不可证伪)**:目标 unit 造合法 link + 另一 unit 放坏
  payload_json,使修复前全表扫描炸 held、修复后 proceed。
- 评审 B 的两条 MINOR(`_prepare_build_workspace` 在 consume 之后会
  白扣预算 → 前移到 consume 之前;X8 状态门在 lifecycle API 前无写
  入者 → delta 显式记录"此前需带外写状态")一并随批;后者与 R2-5
  的 orphan HELD 恢复边(见下 change_45)是同一恢复语义,合并处理。

## 二、change_45(收 change_44 未闭合项 + 新矛盾,纯文本/checker)

**代码在争议点上已是对的(R2-6/R2-7 previous 锚点、D3 写集),
以代码为准修文本。**

### A. 处置不实,补正文(R2-4/R2-5)
- **D3 正文**:design.md:1350-1358"写入全部执行+优先级公式"段收窄——
  明写"a0 失败与④多命中:仅提交 HELD、立即返回,不做 b/b'/c/d 写;
  优先级公式仅适用 c 与 clean 组共存",消解与 1252/1222"提交后返回"
  的矛盾。
- **D10 余项**:event_type 注释(528-531)补 CONVERGENCE/
  SECONDARY_TARGET_ADOPTED;derive 终态释放(2273-2277)对齐 §3.6
  表格、§3.6(1027)裸 `release_worktree_protection` 改
  `release_terminal_worktrees`;`adopted_fingerprint[]`(834)改单数。

### B. D2/D9 关旧伤引新矛盾,以代码为准回修(R2-6/7/8/9)
- **D2 锚点方向(R2-6)**:1464-1466"回退到它**之后**首个 REPRODUCE"
  → 改为"锚定至该 rebaselined **之前(≤)最新** REPRODUCE"(与代码
  `_reproduce_before` 及 1658 写序一致)。
- **回溯兜底(R2-7)**:恢复"向前无实质事件 → 回退最新 REPRODUCE"
  兜底(代码已实现,文本漏);解决"首轮即 toolchain_failed 后重试"
  未定义。
- **DoD 旧口径(R2-8)**:删/改 2771-2773 旧 previous 规则;补裁决承诺
  的 n_a-over-PASS / n_a-over-rebaselined 两 DoD 用例(D2 欠账)。
- **D9 删契约(R2-9)**:CONVERGENCE 行重写时误删的 `at` 字段、
  verdict/previous_basis 枚举、FAIL evidence 必填、"其余组合 →
  PayloadSchemaError"兜底**全部恢复**;修 1431 悬空引用;回填 DoD
  2724/2756 的契约表依据。

### C. D5/D6/D8 残项补齐(R2-10/11/12)
- **D6(R2-10)**:恢复丢失 `#` 前缀(1401/1435-1436/1566);**checker
  的 fence 结构检查落地**——python-fence-count>0 断言施于**真文档**
  (非仅 self-test fixture),补未闭合 fence 的显式失败(现静默跳过);
  新增 fence 奇偶 fixture。
- **D8(R2-11)**:§7.13 item12 grep 放宽至非 REJECTED 前缀
  (含 AmbiguousQbReference/ReleaseNotAllowed);§4.2 分支映射
  (2004-2006)接线 REJECTED_ORPHAN_PASS_HELD、step7(1546)同步;
  §4.1 b' 零候选点名写 reason=no_free_invocation_slot 者;
  append_event 注释(1918)"四值"改五值。
- **D5(R2-12)**:§7 补 pragma 关闭时漂移 link 反向 DoD 用例。

### D. 两条设计 MAJOR(评审 B 独得)
- **orphan HELD 恢复边死锁(B-MAJOR/R2-5 同源)**:§4.1 c)"留待人工
  裁决后的下次进入"与 D11 step1"HELD 一律 exit 4"死锁。**裁决:
  明示 orphan_pass / state_inconsistent 类 HELD 为**终态(仅人工带外
  修库 + 带外写状态复位),step1 白名单文档显式说明该类不经 CLI
  恢复;previous_evidence_missing 类 HELD 仍是唯一 CLI 可恢复(经
  rebaseline)的 HELD。DoD 补两类 HELD 的可达性区分用例。
- **REJECTED_ORPHAN_PASS_HELD 孤立(R2-11 含)**:见 C-D8,接线到
  两处出口映射,消除§7.13 自标"孤立错误码"。

### E. NIT/记录(R2-13/14/15)
- finding-disposition.md 修正 D2/D3/D4/D5/D6/D8/D10 表述并注成因;
  §0"change_41"→ change_46+;change_44.md 补记 D10 实际范围。

## 三、方法论账(⑨)

⑨ **处置声明须正文 diff 自证**:change 记录是意图,权威正文是事实,
Closed 只认后者。本轮两家独立抓出处置表失实——延续 C1(多架构盲区)
的教训:**自证材料本身也要被异构核验**,不能因"是我们自己的账"就
默认可信。

---

## 完成定义
change_45 应用(升 v1.5.18-FROZEN)→ 正文 grep 自证表 → FIX-1 三补 →
全量+新测全绿 + checker(真文档 fence 检查)全绿 → 更新
finding-disposition → 生成第二轮 delta 包回送两家。双家确认 + 开发者
放行,方可 merge。
