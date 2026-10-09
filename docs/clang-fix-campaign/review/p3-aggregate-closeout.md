# P3 Aggregate Closeout

日期:2026-10-09。状态:**FIXES_APPLIED**,未自行签批CLOSED。
首次实现证据保留;本轮PM裁决见末尾“评审修复”。

权威:`../design.md` v1.5.19-FROZEN §3.4/§4.2/§7 Phase 3。
基线`7bbccc9`;本期新增`ci_triage/aggregate.py`与`tests/unit/test_aggregate.py`,
不修改既有API、design.md或旧入口。提交由Git外部锚定。

## DoD 对照

| 条文 | 结论 | 用例/证据 |
|---|---|---|
| aggregate_verifications(ids,state_db)返回冻结字段 | PASS | `test_consistent_aggregate_binds_real_columns_without_writing`,真实SQLite三record正例,返回有序原record |
| verified_tree_sha两两相等 | PASS | `test_each_binding_mismatch_reports_concrete_values[verified_tree_sha]` |
| base_commit相等 | PASS | 同上`[base_commit]` |
| spec_name相等(package真实列) | PASS | 同上`[spec_name]` |
| project相等(gerrit_path真实列) | PASS | 同上`[project]` |
| edit_spec_sha256相等,不改原始字节摘要语义 | PASS | 同上`[edit_spec_sha256]` |
| gbs_conf_sha256相等 | PASS | 同上`[gbs_conf_sha256]` |
| 归一化arch集合恰为目标集合,不泛化前缀 | PASS | `test_arch_set_must_include_each_target`;gcov/emulator/裸CPU/未知/空串五例拒绝 |
| 全PASS且三份完整record | PASS | 非PASS替身、数量0/2/4、缺ID、重复ID分别拒绝;真实DB的PASS CHECK未改 |
| reasons逐项具体差异 | PASS | 六字段独立负例均比对原值/异值/ID/arch;多差异样本断言三条均在 |
| 全仓/类型/lint/import门禁/设计门禁无新增失败 | PASS | `evidence/current/commands.json`,全量1440/1;90设计门禁与基线exit相同 |

## 验证与边界

证据根:[stage17 evidence](../dev_memory/stage17_p3_aggregate/evidence/)。
定向`python -m pytest tests/unit/test_aggregate.py -v`:20 passed,exit0。
基线1420 passed/1 skipped → 当前1440 passed/1 skipped;新增20,旧1410+10个PASS及
1个skip全保留。`comparison.json`中missing_nodeids/changed_outcomes/exit_changes均空。
全量、mypy、ruff、lint-imports均exit0;6个import契约全绿;双道198+4全绿。
94条实际命令及exit在baseline/current两目录,复现命令见
[progress §3](../dev_memory/stage17_p3_aggregate/progress.md#3-验证与dod)。
远端CI对应本阶段提交,推送后查验GitHub完整结果并在交付回报给出run链接。

非行为/安全边界的实现补足:结果采用frozen dataclass/tuple;
不存在的ID/数量不符以ok=False及具体reason拒绝;失败摘要返回None;
沿用既有get_record与arch映射,不新建schema版本或绑定字段。
不自动挑选最新round、不写campaign状态、不选择主arch路径。

遗留:沿P2的三项checker既有问题(设计文档self-test历史样本缺失、
两个symbol fixture仍指向已删除旧址),两树exit分别1/0/1,无新增。
不放宽这些检查、不把它们记作已修复。待设计方核验与评审。

## 评审修复

按2026-10-09 PM轻量裁决执行;design.md零修改,待P5设计修订统一同步。
单家评审P3可签收,本轮修复后仅标FIXES_APPLIED,等待设计方核验。

| 发现 | 处置 | 证据(stage17) |
|---|---|---|
| branch未绑定 | 加入_BINDING_FIELDS和AggregateResult,任意reason时branch=None | `evidence/review-fixes/targeted.log`:原参数化branch/仅branch不同/全一致返回值 |
| 共同空值被相等性放行 | 七字段逐record非空(strip判空),每空值reason带ID和字段名;不做hex校验 | 同上七字段乘空串/空白串,每组恰三条原因,无数据库写入 |
| 拒绝摘要一致性 | branch与原摘要统一在失败时None,其它字段/arch/records语义不变 | 同上各字段负例;生产diff仅绑定、判空、返回branch |

命令:`.venv/bin/python -m pytest tests/unit/test_aggregate.py -v`,
36 passed,exit0。全仓先行P4的1480/1→本轮1496/1(+16);
相对固定4a6873d共增39项(含P4的23项),原1458 nodeid全部保留且结果不变。
全仓/mypy/ruff/lint-imports各exit0;90项既有设计门禁与基线逐条相同,
三条历史偏差保留。证据:`current/commands.json`、各日志、`comparison.json`;
完整复现命令与PM“设计正文待同步”清单见
[progress §5-6](../dev_memory/stage17_p3_aggregate/progress.md#5-评审修复与pm轻量裁决2026-10-09)。
先行P4远端success已存`p4-remote-ci.json`/`.log`;P3本提交CI在推送后独立核验,
由GitHub run外部锚定并在交付回报给出,不以P4 CI替代。
