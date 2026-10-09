# Stage17 P3 aggregate

日期:2026-10-09。状态:**CLOSED**,PM核对通过,FatTank批准签收。
§1-4保留首次实现及其历史验收;评审裁决与证据见§5-6,最终签收见§7。

## 1. 权威与范围

- `../../design.md` v1.5.19-FROZEN,§3.4聚合绑定、§4.2 aggregate、§7 Phase 3。
- 开工基线:`7bbccc9`,P2 CLOSED;全量与设计门禁在本轮重新实跑,不抄历史数字。
- 只新增`ci_triage/aggregate.py`、独立测试及本阶段记账;不改既有API或design.md。
- 计划:真实record字段核对 → 聚合实现/逐字段负例 → 全仓/既有门禁对比 → 独立提交/CI → READY_FOR_REVIEW。
- 后续P4单独提交,本阶段不实现消息组装、推送、状态转换或round选择。

## 2. 接口与实现口径

`aggregate_verifications(ids, state_db) -> AggregateResult`遵§4.2字段全集。
通过shared/state现有`get_record`读取指定ID,使用campaign_state已有arch穷举表,
不新增第二份映射。§3.4的六个绑定字段逐个检查;记录数和归一化arch集合共同
保证每个目标arch恰一份。全部PASS,不泛化前缀、不按最新状态替换指定record。

不改变行为/安全边界的实现细节(轻量流程留痕):

- 返回类型采用既有frozen dataclass惯例;records/reasons为有序tuple。
- 缺失ID/数量不符归为`ok=False`,reasons带拒绝码、具体ID/数量/原值;
  非法arch原因带`REJECTED_ARCH_NOT_ALLOWED`,其余不一致带
  `REJECTED_ARCH_AGGREGATE_MISMATCH`。不增添§4.2未列出的顶层code字段。
- 失败时绑定摘要字段统一为None,保留已读取records与全部差异,不得消费不完整绑定。
- 仅检查§3.4明确列为必须相等的字段;不把可用的canonical_diff_sha256或
  各arch自然不同的verified_commit_sha/patch/build_log/worktree扩成新约束。
- 不写业务行;既有StateDatabase读取路径保留自身的schema初始化机制。

## 3. 验证与DoD

非PASS负例通过人工读取替身注入,不放宽数据库自身PASS CHECK。

| 设计义务 | 用例与结论 |
|---|---|
| 全一致、真实列映射 | `test_consistent_aggregate_binds_real_columns_without_writing`:PASS,返回六列及原始有序records |
| verified_tree_sha | `test_each_binding_mismatch_reports_concrete_values[verified_tree_sha]`:PASS |
| base_commit | 同上`[base_commit]`:PASS |
| spec_name | 同上`[spec_name]`:PASS |
| project | 同上`[project]`:PASS |
| edit_spec_sha256(原始字节摘要) | 同上`[edit_spec_sha256]`:PASS,不做canonical JSON转换 |
| gbs_conf_sha256 | 同上`[gbs_conf_sha256]`:PASS |
| arch集合及穷举白名单 | `test_arch_set_must_include_each_target`与`test_arch_whitelist_does_not_strip_profiles`五参数例:PASS |
| 全PASS/恰三份/ID完整 | non_pass、exactly_three、missing_id、duplicate_id测试:PASS |
| reasons列全差异 | `test_all_field_differences_are_reported_without_short_circuit`:PASS;独立负例均断言实际值与ID/arch |
| 既有行为不变 | 新增模块未接入旧入口;DB业务行前后dump一致;原1421个nodeid全保留、结果不变 |

全部用例在`tests/unit/test_aggregate.py`,原文输出在`evidence/targeted.log`。
本轮实际执行:

```text
$ .venv/bin/python -m pytest tests/unit/test_aggregate.py -v
============================== 20 passed in 0.19s ==============================
exit=0
```

全套验证使用既有runner,在基线与候选两个干净工作树各跑一遍。候选只增加新模块与测试,
未带入主工作树旧草稿、文档删除或P4中间态。

```sh
R=docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py
E=docs/clang-fix-campaign/dev_memory/stage17_p3_aggregate/evidence
.venv/bin/python "$R" /tmp/p3-baseline-7bbccc9 "$E/baseline"
.venv/bin/python "$R" /tmp/p3-aggregate-7bbccc9 "$E/current"
```

两目录`commands.json`保存每条实际argv/cwd/PYTHONPATH/MYPYPATH/exit与日志摘要,
原始stdout/stderr在同目录日志;逐nodeid结果在pytest.xml。
`comparison.json`记录基线1420 passed/1 skipped → 当前1440 passed/1 skipped,
新增20例,`missing_nodeids=[]`、`changed_outcomes=[]`、`exit_changes=[]`。
全量pytest/mypy/ruff/lint-imports各exit0;94条命令包含90项既有门禁/控制,
仍有三条历史checker与原期望不符但两树exit逐条相同:
design-doc-controls(1)、duplicate-spec-root-mismatch(0)、twin-both-binary-key(1)。
原因沿P2收口遗留表,没有改期望值、判据或历史输入。
测试模块与生产模块sha256记在comparison.json,提交前核对候选与工作树原字节一致。

## 4. 收口与人工前提

收口:`../../review/p3-aggregate-closeout.md`,状态仅READY_FOR_REVIEW。
无新增需设计方裁决的阻塞;第2节实现细节按轻量流程留痕。
本提交及推送后的远端CI由Git/GitHub外部锚定,文件内不自记SHA;
必须在对应run完成后回报结果,不以P2的CI替代本期验证。
现有三条工具遗留不归本阶段修复;P4/P5/P5R移交归属不变。

## 5. 评审修复与PM轻量裁决(2026-10-09)

单家评审结论P3可签收,PM另明确下列修复;当时按裁定实施并等复核,
未自行CLOSED,design.md不改。现已按§7批准签收。

| 发现/裁决 | 处置 | 用例 |
|---|---|---|
| 绑定字段缺branch | _BINDING_FIELDS及AggregateResult均增加branch;任何reason存在时branch与其它摘要一同None | 原逐字段负例加入branch;`test_only_branch_mismatch_rejects_otherwise_consistent_records`独立负例;全一致正例检查返回branch |
| 全部记录共同空值可绕过相等性检查 | 七字段逐记录strip判空,每个空值独立reason带verification_id与字段名;不短路、不改写record或数据库 | `test_all_three_empty_bindings_report_each_record`七字段乘空串/空白串,逐条断言三个reason |
| 不做hex格式校验 | 仅非空与原值一致性,不增格式正则或摘要长度约束 | aggregate生产diff;现有非绑定字段差异及arch规则保持原样 |

本轮只改aggregate模块与其测试。七字段为verified_tree_sha/base_commit/spec_name/
project/branch/edit_spec_sha256/gbs_conf_sha256;strip仅用于判空,不把不同原值归一化。
任意原有拒绝原因也使所有绑定摘要为None;records保留原对象与指定顺序。
未改get_record/schema/其它API,未接入新入口;仓内没有其它AggregateResult构造方。

### 5.1 实跑与回归

先行P4修复`2ba0e0d`建立1480/1;本轮P3再增16例,合计1496/1。
以指定固定基线`4a6873d`重新采集的1457/1作门禁与旧nodeid比较,
基线原文复用stage18本轮`evidence/review-fixes/baseline/`(不是抄历史数)。
候选干净工作树`/tmp/p3-review-fixes-2ba0e0d`,只复制aggregate模块与测试;
取证目录`evidence/review-fixes/`,完整命令/环境/exit/hash在`current/commands.json`。

```sh
R=docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py
E=docs/clang-fix-campaign/dev_memory/stage17_p3_aggregate/evidence/review-fixes
P4=docs/clang-fix-campaign/dev_memory/stage18_p4_derive_commit/evidence/review-fixes
.venv/bin/python "$R" /tmp/p3-review-fixes-2ba0e0d "$E/current"
.venv/bin/python -m pytest tests/unit/test_aggregate.py -v
.venv/bin/python "$P4/compare_validation.py" "$P4/baseline" "$E/current" /tmp/p3-review-fixes-2ba0e0d tizen-ci-triage/scripts/ci_triage/aggregate.py tests/unit/test_aggregate.py
```

```text
============================== 36 passed in 0.34s ==============================
======================= 1496 passed, 1 skipped in 32.43s =======================
Success: no issues found in 106 source files
All checks passed!
Contracts: 6 kept, 0 broken.
completed=94 unexpected=3
```

定向、全仓、mypy、ruff、lint-imports各exit0;90项既有设计门禁按原期望实跑,
相对4a6873d的94命令exit_changes={},missing_nodeids=[]、changed_outcomes=[],
详见`comparison.json`(含受验源码摘要)。三条既有偏差仍为design-doc-controls=1、
duplicate-spec-root-mismatch=0、twin-both-binary-key=1,无新增,未改判据或期望。
`targeted.log`为定向原文;`current/pytest.log`中真实hook integration再次PASSED。
未碰design.md/P2/hook配置,没有本裁决之外的API行为变化。

先行P4远端CI已完成:
`gh run view 37879648575 --json databaseId,headSha,status,conclusion,url,jobs` exit0,
headSha=`2ba0e0d9bf18f430c71d1813b508d18e63e0e8ed`,conclusion=success,
Lint/Type check/Tests全部success;原文`p4-remote-ci.json`及`p4-remote-ci.log`。
远端原文为`1479 passed, 2 skipped in 35.69s`,真实hook用例SKIPPED;
该skip不算验证,其完成证据是本机定向和全仓的PASSED,不混用两种环境。
链接:https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37879648575 。
P3自身远端CI须在本独立提交推送后检查,交付回报给出对应run,不以P4成功替代。

## 6. 设计正文待同步(P5设计修订时)

1. §3.4聚合绑定与§4.2 aggregate:真实列映射的绑定字段增加branch,
   AggregateResult增加branch;任意不符时包括branch在内的全部摘要字段None。
2. 七个绑定字段在每条record上必须strip后非空;空值逐条reason,包含
   verification_id和字段名。相等性比较仍取原值,不增加hex格式校验。
3. §7 Phase 3 DoD:逐字段不符参数化增加branch,另有仅branch不同负例;
   各字段三条共同空串必须拒绝,并覆盖空白串与逐记录原因完整性。

以上为PM直接裁定的待同步内容,本轮不修改设计正文,不开始P5实现。

## 7. 最终签收(2026-10-09)

- 单家评审原结论:P3可签收。
- 签收版本与修复commit:`f12154b`;PM已核对修复与裁定一致。
- FatTank已批准签收,按轻量流程不再进行第二轮评审。
- 状态:**P3 CLOSED**;详见[最终签收](../../review/p3-aggregate-closeout.md#最终签收)。
- §6设计待同步清单完整保留,由P5设计修订统一并入;本次不改代码或design.md。
- P5移交集中在[stage16 §5](../stage16_p2_submission_identity/progress.md#5-p2-01裁决与移交清单),
  本次新增的日期解析与hook摘要失败规则仅登记,不冒称已实施。
