# Stage17 P3 aggregate

日期:2026-10-08。状态:**READY_FOR_REVIEW**。

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
