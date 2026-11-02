# SKEL-B1-02: Baseline Failure Before Module Relocation

日期:2026-11-02。基线:`accd7f4`。状态:`STOPPED_BASELINE_FAILED`。

## 事实

- 冻结稿已在目标位置,指定Downloads源不存在;未复制、未改冻结稿。
- 尚未移动derive_commit或任何其它模块;生产代码、测试与打包/导入配置均未改动。
- collect-only:exit 0,2903个nodeid,见[命令](baseline/collect.command.json)、
  [完整列表](baseline/nodeids.txt)。
- import-linter:exit 0,既有6条合约全部通过,见[命令](baseline/imports.command.json)、
  [输出](baseline/imports.stdout.log)。
- 全量pytest:exit 1,2901 passed / 1 failed / 1 skipped,1012.28秒。见
  [完整stdout](baseline/pytest.stdout.log)、[stderr](baseline/pytest.stderr.log)、
  [命令与起止](baseline/pytest.command.json)、[JUnit](baseline/pytest.xml)、
  [结构化汇总](baseline/summary.json)。唯一skip是
  `test_case_insensitive_bypass_is_platform_specific`,原因`case-sensitive filesystem`。
- 冻结稿/安全核心/代理完整与前缀hash不变,相关生产/测试/配置/design.md无diff,
  见[停止时复核](baseline/unchanged-at-stop.json)。

## 失败证据

用例:`tests/unit/test_p5q_c8_investigation.py::test_post_submit_read_signatures`。
Python入口第26行要求Node子进程exit 0。Node调查入口在
`tests/node/p5q_c8_investigation.mjs:109`要求`facts.harness_failure`不存在。

本次输出:

```text
CASE_COMPLETE control
CASE_COMPLETE idle-script-navigation
CASE_COMPLETE racing-script-navigation
CASE_COMPLETE racing-meta-refresh
CASE_COMPLETE racing-wicket-navigation
CASE_COMPLETE injected-missing-root-membership
CASE_COMPLETE configuration-connection-abort
CASE_COMPLETE configuration-redirect-signin
QB_AGENT_STOPPED category=FETCH_CONTINUE_FAILED
INVESTIGATION_STOPPED AssertionError
```

以上摘录合并stdout与stderr,不声称两流之间的精确时间顺序。
`configuration-redirect-307.json`记录:

```json
{"harness_failure":{"class_name":"TargetClosedError","agent_code":null,"category":"OTHER_FRAMEWORK_ERROR"},"profile_removed":true}
```

原始文件见[Node stdout](baseline/c8-investigation/node.stdout.txt)、
[Node stderr](baseline/c8-investigation/node.stderr.txt)、
[场景事实](baseline/c8-investigation/configuration-redirect-307.json)。
这些来自本轮pytest的临时目录,只含本机假服务器合成数据;没有访问真实QuickBuild。

## 停止与候选处理

失败发生在拆分前,无法将其归因于模块搬迁;本次证据也不足以唯一确定底层原因。
按用户的“遇到冻结稿没写到、或照写会失败的情况,停止并报告”要求停止实施。
不以重试至绿、修改测试、放宽安全规则或豁免该用例继续。

候选处理是由设计方另行批准离线定位该场景的停止/清理时序及期望,修复后重建全绿
基线,再从derive_commit试搬开始。若决定接受基线既有失败,需要明确新的验收裁定。
本轮不实施候选修复,不进入后续批次。

第4.4节七项拆分验收均未完成;当前仅有拆分前的collect/import-linter结果和保护文件hash。
未生成拆分后nodeid列表,不声称差集为空。测试物理路径改动为0条。

提交的原始pytest stdout与JUnit各保留一处`E         `尾随空白,分别在第80/36行;
`git diff --cached --check`因此返回2。排除这两份原始输出后返回0,不修改证据字节。
