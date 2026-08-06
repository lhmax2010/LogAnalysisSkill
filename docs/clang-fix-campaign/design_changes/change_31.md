# change_31:v1.5.6 → v1.5.7(**三条 blocker 预答**:唯一性锚到 invocation、
# n_a 事件的 previous 分支、ci_evidence 两列 nullable;PENDING-SOURCE 权威
# 来源更正)

- 提出人:Claude 触发:两方复审(甲:3 blocker + 5 major;乙:1 blocker +
  2 major + 2 minor) 日期:2026-08-01
- 状态:已采纳(v1.5.7 落盘);其中唯一索引谓词(`verdict <> 'n_a'`)
  已被 change_32 supersede——实现方不得照抄该谓词,以主文 §3.4 为准。
- **性质**:两方对"转 P4.5"的决定均无异议;本轮是**发 prompt 前的预答**
  ——三条 blocker 是经三轮确认的**已知**硬伤,不是待实现发现的未知。

## 0. 我上一轮的判断错误

我把这三条当作"实现细节"随包发送。乙方的反驳成立:**反馈周期该用
"一次 pytest"换的,是那些还不知道的问题,不是已经知道答案的**;按 prompt
自己的硬约束 #1,它们只会变成三次 `[DESIGN_ISSUE]` 往返。
**本轮先用探针复现了两条,确认不是纸面推理**:
```
【B1】补写 orphan_invocation ✓ → 重试真实结果 ✗✗ UNIQUE constraint failed
【B3】arch 拒绝 unit ✗✗ NOT NULL constraint failed: ci_evidence_ref
```

## 1. Blocker 处置(3/3,均带探针)

### B1 invocation/outcome 基数矛盾 —— 唯一性锚点搬家
旧索引 `(unit, round, arch)` 与三条已冻结规则互斥:崩溃重试必须新增
BUILD_INVOCATION、每 invocation 恰好一条 CONVERGENCE、同 (round,arch) 至多
一条。`orphan_invocation` 一旦占槽,重试的真实结果**永远写不进去**。
**处置**:`verdict` 与 `invocation_event_id` **提为真实列**;索引改为
`ux_convergence_per_invocation (invocation_event_id) WHERE
event_type='CONVERGENCE' AND verdict <> 'n_a'` —— 唯一性锚在
**invocation**,且 **n_a 占位/补写不参与唯一性**。
**探针**:合法序列(补 orphan → 新 invocation → 实质 outcome)✓;
同一 invocation 二次实质 outcome 被拒 ✓;n_a 可共存 ✓。

### B2 无 evidence 的 n_a 让 repair/rebaseline 卡死
`resolve()` 的三分支对"最新事件 evidence 为 null"没有任何处理 ⇒ 一律落
"完整性失败 → HELD",**rebaseline 恢复后下一轮原地弹回**。
**处置**:新增 n_a 分支——`rebaselined` → **回退最新 REPRODUCE**;
`orphan_invocation`/`apply_failed`/`analyzer_failed`/`toolchain_failed` →
**沿 event_id 向前取最近 verdict≠n_a 的 CONVERGENCE**,无则回退 REPRODUCE;
**均不视为完整性失败、不置 HELD**;`result` 对非 build 事件取 `n_a`。

### B3 arch-rejected unit 无法插入
`ci_evidence_ref/sha256` 为 NOT NULL,而 arch gate 发生在 analyzer **之前**、
该 unit 无 primary_arch 也无 CI evidence。**处置**:两列改 **nullable**
(**仅 arch 拒绝 unit 可空**,与 primary_arch 同一规则);`create_unit`
**显式补两个必填参数**;`create_arch_rejected_unit` **不接收**该参数,
内部以三列全 NULL 单事务插入 + 写终态。**探针**:可插入并写终态 ✓。

## 2. Major 处置

- **甲-M4 PENDING-SOURCE 查错了权威来源(重要)**:我让实现方去核
  **analyzer 的 evidence schema**,而 fingerprint 的真实语义在
  **`convergence.py::_primary_fingerprint`**(file/code/anchor 各有多级
  fallback)。只看 analyzer 会让 campaign adoption 与 `check_convergence`
  **算出不同 fingerprint**。**冻结**:直接调用该函数或其提取的公共 helper,
  **禁止自行实现字段选取与 fallback**;设计与 prompt 同步更正。
- **甲-M5 secondary REPRODUCE 无可执行分类**:补判据——PASS →
  `baseline_pass`;FAIL 且 primary fingerprint **与 primary_arch 的
  REPRODUCE 相同** → `matched`;不同 → `different_failure`;
  `ci_evidence_sha256_used` 对 secondary 取 unit 级锚点值。
- **甲-M6 prompt 交付范围不自洽**:六表 → **七表**;`campaign_lifecycle`
  **划归 P10**(本 Phase 不实现);§4.3 错误码验收**收窄到 P4.5 范围十项**,
  明列不在范围的 P5/P5Q/P5R/P6 错误码;`campaign_rebaseline` **归 P6**
  并补 §3.2 模块行。
- **甲-M7 payload/API 漂移**:`adopted_fingerprints` 全文统一为**单数**;
  `adopt_secondary_target_with_convergence` **不再接收该入参**(此前"接收
  却声明不信任"自相矛盾),由 API 事务内自算并写入 payload;
  CONVERGENCE payload 补 **`verification_id`**(PASS 必填)。
- **甲-M8 校验器仍有假绿**:①无关表格首列的未登记错误码——权威状态名
  收窄为**仅 §3.6 与 §3.4 两表**的首列;②`*_TIMEOUT/_CONFLICT` 形态补入
  启发式;③**ANCHOR 补正负 fixture**。现 **self-test 20/20**。

## 3. Minor

`REJECTED_CI_EVIDENCE_MISMATCH` 释义改为"与 **unit 级锚点**不符";
prompt 新增"§3.6 `DISCOVERED→CI_EVIDENCE_READY` 与 §3.3 时序相反"的
**P9 待厘清提示**(不阻塞 P4.5)。

## 4. 自我批注

"设计收束"不等于"已知矛盾随包发送"。上一轮我用"剩下的属实现细节"给三条
**已确认**的硬伤放行,而它们连一行代码都还没写就能被 SQL 探针证伪。
判据应当是:**能否在不写业务代码的情况下证伪?能,就必须在设计阶段关掉。**
