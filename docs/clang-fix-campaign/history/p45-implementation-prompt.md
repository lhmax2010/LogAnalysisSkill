# Codex Prompt:P4.5 实现(campaign_state + suppress_policy + campaign_repair_step)

> 对应设计 **v1.5.7-draft(实现输入版)**。两方评审均判定"设计层可进入
> P4.5 spike",本阶段目标是**用代码与测试反向验证契约**。

请先复述你理解的任务与全部约束,再动手。

## 0. 硬约束(违反即停)

1. **发现契约不可实现、自相矛盾或与既有代码冲突 → 立即输出
   `[DESIGN_ISSUE]` 并暂停,不得自行变通、不得"选一种合理解释"。**
   这是本阶段最重要的价值:让代码替设计做裁决,而不是让实现悄悄替设计
   做决定。
2. **安全核心零修改(逐文件口径,勿混淆)**:
   - **完全不改**:`state/db.py`、`state/keys.py`、`state/records.py`、
     `verify/build_verify.py`、`verify/edit_spec_guard.py`、
     既有三个 workflow 及其测试。
   - **允许 additive(仅新增,不改既有函数行为/签名)**:
     `verify/workspace.py` —— **新增** `cleanup_disposable_copy(worktree_path,
     expected_workspace_root, *, reject_protected=True)`(design §4.2 已冻结
     签名与实现基础:读 `.ci_triage_workdir` marker 重建 handle → 校验 root
     → `is_protected` 判断 → 复用既有 `cleanup_worktree`,**不另写删除逻辑**);
     `cli.py` —— 注册新子命令。
   - 判断口径:**新增函数 = additive**;**改动既有函数体/签名/行为 = 禁止**,
     确有必要 → `[DESIGN_ISSUE]` 暂停。
3. 凭据不进代码/日志/测试夹具/PR。
4. R13:所有验证命令记录**实际输出**,不得声称通过而无输出摘要。

## 1. 开工首日必做(先于编码)

- **已知时序不同步(v1.5.7 提示,P9 会撞,本 Phase 只需知悉)**:§3.6 的
  `DISCOVERED → CI_EVIDENCE_READY` 与 §3.3 "analyzer 先于 create_unit"
  顺序相反 —— 属**发现层(P9)**的待厘清项,不阻塞 P4.5;若本 Phase 的
  state API 设计受其影响 → `[DESIGN_ISSUE]`。
- **`[PENDING-SOURCE]` 核对**:读 analyzer 源码原文,确认 evidence packet
  的 fingerprint 语义。**权威来源是 `verify/convergence.py` 的
  `_primary_fingerprint`,不是 analyzer 的 evidence schema**(v1.5.7 更正:
  file/code/anchor 各有多级 fallback,只看 analyzer schema 会与
  `check_convergence` 算出不同 fingerprint)。**冻结方案**:直接调用该
  函数或其提取的公共 helper,**禁止自行实现字段选取与 fallback**。
  **产出与判定**:核对结果写入
  `docs/clang-fix-campaign/dev_memory/phase_4_5_pending_source.md`
  (含**源码文件:行号 + 原文片段 + 结论**),并在**首次暂停时一并提交**;
  - 字段名与设计语义一致(仅命名不同)→ 记录实际字段名后**继续**,
    不需 R1;
  - 语义不符(如无 anchor 概念、诊断码不可得)→ `[DESIGN_ISSUE]` 暂停,
    走 R1,**不得自行选一种映射**。
- **R10 预检 + R12 扫描**(见 design §8)。
- **环境**:本仓库无 `python`,一律 `.venv/bin/python`;`ci_triage` 需
  `gbs_patch_suggest` 可导入。

## 2. 交付范围(P4.5)

```
ci_triage/campaign_state.py          # **七表** DDL + 事件/预算/round/QB API
ci_triage/suppress_policy.py         # §3.7 四步序 + forbidden/allowed 检测
ci_triage/campaign_repair_step.py    # §4.1 九步(0–5、6a、6b、7)唯一入口
# 不在本 Phase:campaign_lifecycle(P10)、campaign_rebaseline(P6)、
#              baseline_reproduce(P6)、qb_trigger(P5Q)、sandbox/review_submit(P5/P5R)
cli.py                               # 注册 campaign-repair-step 等子命令
tests/…                              # 见第 3 节
```

**关键契约索引**(逐条对照 design.md):
- §3.4 **七表** DDL(units / gate_events / status_log / rounds /
  verifications / qb_requests / qb_events)(含 `ux_convergence_once` 真实列唯一索引)、payload 契约表
- §3.4 双闸预算(`BUILD_INVOCATION` 计数;`BEGIN IMMEDIATE`)
- §4.1 `campaign-repair-step` 九步、stdout JSON、exit 语义
- §4.2 **`campaign_state` 全部签名**;`campaign_lifecycle` 的三个 release
  API **属 P10**(本 Phase 不实现,仅确保 state 层为其预留所需查询)
- §4.3 错误码:**本 Phase 只需 P4.5 范围内的可达**——
  `RoundsExhausted` / `BudgetExhausted` / `CAMPAIGN_STATE_BUSY` /
  `REJECTED_IDENTITY_MISMATCH` / `REJECTED_CONF_DRIFT` /
  `REJECTED_PREVIOUS_EVIDENCE_MISSING` / `REJECTED_BASELINE_EVIDENCE_MISMATCH` /
  `PayloadSchemaError` / `UnknownEventType` / `StateInconsistent`。
  **属 P5/P5Q/P5R/P6 的错误码不在本 Phase 验收范围**
  (如 REJECTED_SANDBOX_NOT_BOUND / REJECTED_QB_* / REJECTED_REVIEW_* /
  BASELINE_TOOLING_FAILED / REJECTED_REBASELINE_NOT_ALLOWED)

## 3. DoD(全部来自 design §7 的 P4.5 专项,必须真跑)

并发与事务:
- [ ] 双连接竞争 `consume_build_invocation`:上限 1 时只一方成功,
      DB 恰好一条;**去掉 `BEGIN IMMEDIATE` 该用例必须失败**
- [ ] 锁超时 → `CAMPAIGN_STATE_BUSY`,**无事件写入、无 build 启动**
- [ ] `adopt_secondary_target_with_convergence` 并发:只有一个返回 True
- [ ] **CONVERGENCE 唯一性(v1.5.7 口径)**:**合法序列**"补 orphan(n_a)
      → 重试新 invocation → 写实质 outcome"**必须通过**;**违例**"同一
      invocation 二次实质 outcome" → IntegrityError → StateInconsistent;
      n_a 事件不占唯一槽

预算:
- [ ] 每次调用计费 1,apply_failed **同样计费**
- [ ] 达闸二 → `BudgetExhausted` 且**不插事件**;达闸一 → `RoundsExhausted`
- [ ] 崩溃后重试**重新消费**;`rounds_used < max_rounds` 与插入**同事务**

身份与校验:
- [ ] `REJECTED_IDENTITY_MISMATCH` 四类负例(错 unit / edit_spec hash /
      arch 非白名单 / 外部指定 workspace)且**未计费**
- [ ] `REJECTED_IDENTITY_MISMATCH` **不增加 round 数**
- [ ] conf 被改 → `REJECTED_CONF_DRIFT` 且不计费
- [ ] previous evidence 缺失/hash 不符 → **HELD + fail-closed**(不得放行)
- [ ] 预检与 6a **复用同一 `previous_evidence.resolve`**

对账与幂等:
- [ ] "PASS record 已写、link 前崩溃" → 重入补 link 且**不重复计费/不重复 build**
- [ ] 多条未链接 PASS → 全部 `ORPHAN_PASS(ambiguous)` + HELD
- [ ] `BUILD_INVOCATION` 无对应 CONVERGENCE → 第 1 步补写
      `orphan_invocation`(带 invocation_event_id),**预算不退**
- [ ] **n_a previous 分支**:`apply_failed → retry` 与
      `HELD → rebaseline → retry` 两条链**不得原地弹回 HELD**
- [ ] **arch 拒绝 unit**:primary_arch/ci_evidence_* 全 NULL 可插入并写终态;
      `create_unit` 缺 ci_evidence 参数 → 拒
- [ ] `link_verification_with_convergence` 三方一致负例 → **两条都不写**

convergence 与豁免:
- [ ] `FAIL(E) → PASS → FAIL(E)`:第三次 previous 取到**那次 PASS**
      (synthetic_zero),**不得判 stalled**
- [ ] secondary 首次 stalled 可豁免一次;第二次起不再豁免
- [ ] 核验 ③ 有牙:current 指纹 ≠ 基线 → 返回 False
- [ ] 任一侧 evidence 截断 → **禁止 adoption**
- [ ] `denied` 短路:不做 convergence、verdict=denied、DENIED 终态

suppress_policy:
- [ ] 四步序 × source_kind 组合(含 T1-suppression 内容优先)
- [ ] 每条 forbidden 与每种 suppress 检测形态正负例

覆盖率:行 ≥80%、分支 ≥70%、核心模块 ≥90%。

**验收命令(R13:必须贴实际输出,不得只写"通过")**:
```bash
cd ~/Toolchain/development/LogAnalysisSkill
V=.venv/bin/python
$V -m pytest tests/ -q                                  # 全量,含存量 ~750 例
$V -m pytest tests/campaign -q                          # 本 Phase 新增
$V -m pytest tests/campaign --cov=ci_triage.campaign_state \
      --cov=ci_triage.suppress_policy \
      --cov=ci_triage.campaign_repair_step \
      --cov-report=term-missing --cov-branch
$V -m ruff check tizen-ci-triage/scripts/ci_triage/     # lint(按 R12 沿用现有配置)
$V tools/check_design_doc.py docs/clang-fix-campaign/design.md   # 文档一致性
$V tools/check_design_doc.py --self-test                # 守卫工具自检
```
**并发用例的"守卫有效性"验证**(本项目三十轮最贵的一课):
去掉 `BEGIN IMMEDIATE` 后重跑并发用例,**必须失败**;把该反向验证的
输出一并贴入 review prompt。

## 4. 交付纪律(R3)

实现 + UT → R13 命令实录 → `dev_memory/phase_4_5_memory.md` →
checkpoint tag → `review/phase_4_5_review_prompt.md` → GitHub PR
`[Phase 4.5] campaign state + repair step` → R14 闭环。

**既有资产回归(隔离声明的验证,不可省)**:
- [ ] 存量测试全绿(与开工前基线逐条比对,**不得有新失败或被跳过**);
- [ ] **既有 batch manifest 渲染逐字节不变**的回归断言;
- [ ] 现有三个 workflow 文件 `git diff` 为空;
- [ ] `state/db.py` / `keys.py` / `records.py` / `build_verify.py` /
      `edit_spec_guard.py` 的 `git diff` 为空;`workspace.py` 的 diff
      **只含新增函数**(逐行确认无既有行改动)。

R2 决策边界:多方案 / 依赖变更 / 契约或 Schema 变更 / 安全模型调整
→ **暂停问开发者**;其余按规划直接做。

## 5. 本 Phase 的 EF 边界(勿越门)

P4.5 **无 EF 依赖**,可立即开工。但需在代码与 dev_memory 中**显式标注
未验证边界**,避免后续 Phase 误以为已验证:
- **EF-3**(Gerrit 确定性 Change-Id)→ **P5 首次真实 push 前**必须完成;
  P4.5 若涉及 Change-Id 计算,只做纯函数与向量测试,**不得实际 push**。
- **EF-5 四项**(SBS REST 探活/映射/字段/accept 语义)→ **P5Q 开工前**;
  P4.5 不触碰 QB REST 调用。
- 到达门时主动提醒开发者执行对应 spike(协议见 `spikes/ef-spike-protocol.md`)。

现在开始:先做第 1 节(PENDING-SOURCE 核对 + R10/R12),产出后暂停等确认。
