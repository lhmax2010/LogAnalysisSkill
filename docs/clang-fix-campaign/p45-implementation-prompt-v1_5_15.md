# P4.5 实现任务:campaign-repair-step 与联合对账(design v1.5.16-FROZEN)

> 本文件为 P4.5 **唯一权威 prompt**(change_39 立、后续 change 逐号 supersede;与任何 change 文档冲突时,以**编号最大的相关 change**为准,当前 = change_40);DDL/契约以
> design.md 为准,本文不复述。旧 `p45-implementation-prompt.md`
> 与 `p45-implementation-prompt-v1_5_14.md` **均已归档 history/**,
> 根目录仅保留本文件;两份归档件不得作为实现输入。

## 0. 角色与总原则

你是本仓库的实现工程师。本任务实现 clang-fix-campaign 的 **P4.5 阶段**
(修复轮唯一入口 `campaign-repair-step` 及其全部冻结 API)。

**硬性协议(违反任何一条即任务失败)**:
1. **唯一契约权威** = `docs/clang-fix-campaign/design.md`
   (**v1.5.16-FROZEN**,冻结于 2026-08-04,含 change_39/40)。`design_changes/change_*.md`
   仅为历史;**任何与主文的冲突一律以主文为准**。
2. **停止并报告,永不自修设计**:实现中发现设计矛盾、缺失定义、
   无法实现的契约,立即**停止**,输出"矛盾报告"(引用 design.md
   行号 + 冲突描述 + 候选方案),等待裁决(将立案 change_41+)。
   禁止自行取舍、禁止"合理推断后继续"。
3. **实测验证不脑补**:所有"已验证"结论必须贴命令与实际输出原文;
   反向验证(guard 去除后用例必须转红)未通过的 guard 视为不存在。
4. **fail-closed**:所有不确定形态按设计规定的拒绝/HELD 路径处理,
   不猜、不静默降级。
5. **零修改名单**:`build_verify` 及既有安全核心(design.md §边界
   与零修改名单节)**一个字节不改**;P4.5 全部为 additive
   (新文件/新表/新 CLI 子命令)。`_primary_fingerprint` 按设计
   经 import 私有函数复用 + parity 测试锁定,**不提取 helper、
   不改 convergence.py**。
6. 禁止修改 design.md;禁止修改本 prompt。

## P0. 前置任务(发布闸门清零,先于任何 P4.5 代码)

按 design.md 冻结裁决记录,以下 E 项清零前 P4.5 不得开工。逐项做完
并贴验证输出后,才进入 P1。

**P0-1 change_31 台账回写**:将
`docs/clang-fix-campaign/design_changes/change_31.md` 头部状态行
替换为(逐字):
> 状态:已采纳(v1.5.7 落盘);其中唯一索引谓词(`verdict <> 'n_a'`)
> 已被 change_32 supersede——实现方不得照抄该谓词,以主文 §3.4 为准。

**P0-2 checker 四规则(口径 = change_39 经 change_40 supersede 后的合成口径;
冲突以**编号最大的相关 change**为准,当前 = change_40)**:在 `docs/clang-fix-campaign/tools/check_design_doc.py` 新增:
- **CK-API-01**:design.md 内**每个 ```python 围栏块**
  `compile(block, "<design.md:块定位>", "exec")` 必须通过
  (change_40:ast.parse 抓不住重复形参——B4 立规事故在语法树层
  放行、在编译符号表层才报错;compile 只编译不执行、不解析名字,
  skeleton 无 import 亦通过);并在**排除全部 fence 后的裸文本**上
  扫描签名起始行
  `^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\(`,命中即 FAIL(单行与
  多行签名同被起始式覆盖;§4.2 转换完成后应归零,转换前实测
  62 处);
- **CK-IDX-01**:**仅扫描根目录唯一权威件
  `p45-implementation-prompt-v1_5_15.md`**(确切文件名,非 glob),其索引名
  形态 token(`\b[iu]x_[a-z0-9_]+\b`)集合必须为 design.md 索引
  集合的**非空子集**;design 侧提取式冻结为
  `CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)`;
  history/ 不扫描;
- **CK-XREF-01**:文内 `§n(.m)` 引用必须解析到存在的章节;
- **CK-MMD-01**:Mermaid 块节点先声明后引用。
每条规则按 change_39+40 合成口径配齐失败 fixture(CK-API ≥3 含真实多行裸
签名;CK-IDX 含旧名残留 FAIL / 非空子集 PASS / **空集 FAIL**);
与既有 fixture(当前 22 个)合并运行,输出**最终实数 `N/N`**——
不预钉总数,以合并后实跑为准。

**P0-3 Ruff 清零**:修复 checker 自身 18 个 Ruff 问题(E741 改名、
E501 断行),将 `ruff check --select E,F` 纳入 checker 自测入口;
修复后重跑全部自测 + 对 v1.5.2 历史样本的 12 问题回归,确认行为
不变。对当前 design.md 跑 checker,预期 `OK: 0 problem`。

**P0 验证输出要求**:贴 ①change_31.md 头部 diff;②checker 自测
`N/N` 原文;③`ruff check` 空输出原文;④对 design.md 的检查输出;
⑤**落盘断言(先于 ①–④ 执行)**:对本文件跑 `sha256sum`,输出必须
等于**编号最大的、含落盘校验值的 change** 写死的 SHA(当前 =
change_40 B.4;旧编号 change 中的 SHA 一律视为已作废;值仅维护在
change 文档,不写入本文件——写入即自变);同贴 design.md 冻结快照
`cmp` 空输出。
任一不符 = 落错版本,**停止,不得执行 P0 其余项**。

## P1. P4.5 范围与交付物

范围以 design.md **P4.5 阶段节**为准(以其为清单逐项对照)。核心
交付:
1. `ci_triage/campaign_repair_step.py` + CLI 子命令
   `campaign-repair-step`(修复轮**唯一入口**;剧本禁止直调裸
   `build-verify`);
2. `campaign_state` 冻结 API 族(签名逐字对齐 design.md §4.2):
   `reconcile_pass_and_invocations` / `ReconcileResult`、
   `consume_build_invocation -> InvocationReceipt`、
   `append_event`(payload 校验 + invocation 绑定事务校验)、
   `append_status`(arch_norm 语义)、
   `link_verification_with_convergence`、
   `adopt_secondary_target_with_convergence`、
   `find_unlinked_pass`(v1.5.14 起:**无 round_index 形参**)、
   rebaseline 授权检查、previous_evidence.resolve(预检与 6a 复用
   同一函数);
3. DDL(§3.4 逐字实现):七表、
   `ux_convergence_per_invocation`(WHERE
   `event_type='CONVERGENCE' AND invocation_event_id IS NOT NULL`)、
   campaign_units 三元组 CHECK、campaign_status_log.arch_norm;
4. stdout JSON(§4.1 冻结 schema,含
   `reconciliation{other_round_relinks, non_campaign_verification_ids}`
   与 `warnings[]` **固定字段、非空元素对象 schema、确定性排序**;
   单 JSON,禁止 JSON 外文本);
5. §4.3 错误码全表接线(含 `REJECTED_PRIMARY_BASELINE_MISSING`)。

## P2. 硬性契约清单(实现自查表,逐条打勾,附 design.md 定位)

- [ ] **九步序(恢复原序,v1.5.14 立)**:锁 → 只读身份校验(不读
  conf/src_clean/evidence 文件,仅元数据)→ create_round+复核 →
  联合对账 → previous 预检(失败 → **写 HELD status
  (previous_evidence_missing, arch_norm)** 后 exit 4,无 gate 事件)
  → consume(持 InvocationReceipt)→ build_verify → 6a/6b → 释锁。
  **成功出口永远不得先于 create_round 的 round 权威绑定**。
- [ ] **进程文件锁 (unit, arch_norm)**,`<workspace_root>/.repair_step.lock`,
  fcntl 非阻塞;BUSY → exit 5 无写入。
- [ ] **联合对账 = reconcile 单事务唯一入口**:BEGIN IMMEDIATE 内
  重查、判定、落库一体;wrapper **禁止任何"读列表→另起事务写"**
  两段式路径(加静态断言/审查项)。
- [ ] **a0 精确一对一绑定**(事务内第一个判定):每条已 link
  verification 按 verification_id 查 PASS CONVERGENCE **恰一条**,
  且 unit/round/arch/verification_id 逐项一致、result==PASS、
  verdict==n_a、invocation_event_id 指向同 unit/round/arch 的
  BUILD_INVOCATION;**不得降级为存在性查询**;任一不符 →
  state_inconsistent_held(同事务 HELD 提交后返回,**不抛异常**)。
- [ ] **归属算法**:failure_key+arch 候选 → edit_spec_sha256 反查
  campaign_rounds;恰一命中归组;零命中 → non_campaign 清单
  (无事件无 HELD)+ stdout WARN;多命中 → state_inconsistent_held。
- [ ] **分支表 a/b/b'/c/d 与出口优先级**:a 仅限
  `link.edit_spec_sha256 == 本次 edit_spec`;b 组内唯一配对同事务
  relink(payload 逐字段确定性重建:
  `git diff --name-only --no-renames -z <base> <verified> --`、NUL
  切分、POSIX 归一、字典序;`at`=重建时刻;无源字段不猜转 c);
  其它 round 组 relink 只入 other_round_relinks、**永不抬升
  branch**;c 冻结组不补写;d 仅对"组内已证无未 link PASS"残余
  补写,且 **a/b 出口前同样执行**;优先级
  state_inconsistent_held > orphan_pass_held > 当前组成功 > proceed。
- [ ] **计费语义**:consume 无取消无回退,apply_failed 同样计费;
  a/b 出口不计费不 build;receipt.event_id 回填为一切 outcome 的
  invocation_event_id,禁止"查最新 BUILD_INVOCATION"顶替。
- [ ] **result/verdict/invocation_event_id 条件枚举**(§3.4 契约表
  逐字)与 append_event 事务绑定校验(不符 → StateInconsistent
  不写入)。
- [ ] **secondary primary-first**:primary REPRODUCE 缺失 →
  `REJECTED_PRIMARY_BASELINE_MISSING` 无事件;primary=baseline_pass
  时 secondary FAIL 一律 different_failure。
- [ ] **rebaseline 授权**:最新 HELD 行 reason==previous_evidence_missing
  **且 arch_norm == 本次 arch**。
- [ ] **终态不释放副本**(泄漏窗口按 §4.1 文档语义,不实现清理)。

## P3. 测试闸门(design.md P4.5 DoD 全表为准,以下为强调项)

DoD 清单**逐条**变成测试;每个 guard 类用例必须附**反向验证**
(去掉索引/CHECK/校验/顺序后用例必须失败)。特别强调:
1. 唯一性三违例(双 PASS / PASS 后实质 / 双实质)+ 合法
   orphan→重试序列 + 回退旧谓词后双 PASS 必须转绿;
2. 绑定校验四负例(不存在/非 BUILD_INVOCATION/跨 unit/跨
   round-arch);
3. 崩溃恢复族:relink 占旧槽不 orphan 化(+把补写挪回 relink 前
   必须 IntegrityError);恢复优先于预检(previous 被删仍 relink
   成功;预检挪回第 1 步必须 HELD 失败);a/b 出口前执行 d
   (跨轮残余);历史组补账不授出口(round 2 照建照测照计费;
   按 v1.5.12 快照语义必须复现聚合死锁);round N 部分 PASS 不
   短路 N+1;
4. a0 族:历史半状态(link 在事件缺)→ held 且 d 未补写(跳过
   a0 必须复现掩盖);同 verification_id 多 invocation 形态必须被
   精确绑定检查拒绝(仅索引拦不住,用例证明);
5. 归属族:零命中无事件 + WARN(改写 ORPHAN_PASS 必须破 schema);
   多命中(测试中显式 DROP UNIQUE 构造)→ held;约束完好时
   INSERT 同 spec 第二轮 → IntegrityError;
6. 身份族:`--round-index N+1 --edit-spec <round N hash>` 死在
   create_round(恢复 v1.5.12 序必须 exit 0 逃逸——用例咬得住);
7. 锁族:同 (unit,arch) **同 round 与不同 round** 两变体并发 →
   一方 BUSY;
8. parity 族:fingerprint parity(campaign vs check-convergence
   逐字节);actual_changed_paths parity(fixture 含"文件名带
   空格/引号"用例,去掉 -z 必须失败);
9. stdout schema:所有 branch 固定含 reconciliation/warnings 字段;
   非空元素对象 schema 与排序断言;禁裸 tuple 序列化断言;
10. CI evidence 半空 CHECK、HELD arch 绑定、预检失败 HELD 可达
    (去掉 status 写入 → rebaseline 永拒,复现卡死)、真实 CLI
    进程级 smoke。

## P4. 产出与验收

1. 分支:`codex/p45-campaign-repair-step`;提交粒度:P0 单独一
   commit,DDL/API/CLI/测试分层提交。
2. 提交报告(中文)含:①P2 自查表逐条打勾 + 代码定位;②全部
   测试运行原文(含每条反向验证的红/绿双态输出);③P0 四项验证
   输出;④未决问题/矛盾报告(如有,格式见协议 2)。
3. 完成定义:P0 全绿 + P3 全绿(含反向验证)+ `ruff check` 干净 +
   checker 对 design.md `OK: 0 problem` + 真实 CLI smoke 通过。
4. 任何测试为通过而修改被测语义 = 任务失败;测试必须验设计,
   不是验实现碰巧的行为。
