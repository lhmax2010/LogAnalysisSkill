# SKEL-B1-04: derive_commit试搬的非豁免用例失败

日期:2026-11-02。状态:STOPPED,不进入批量搬家。
续做基线:`f203aec`。裁定:SKEL-B1-03只豁免C8调查的一个nodeid,
不豁免本报告的C5a完整链路用例。冻结稿与测试均未修改。

## 1. 已完成的前置

拆分前C8单nodeid连续5次:PASS、FAIL、PASS、PASS、PASS。
唯一失败形态为`racing-meta-refresh / TargetClosedError /
OTHER_FRAMEWORK_ERROR / FETCH_CONTINUE_FAILED`。
命令、独立输出目录及原始场景JSON:
[flaky-pre/summary.json](baseline/flaky-pre/summary.json)。
仅搬`derive_commit.py`,旧位置使用模块对象别名,补core包发现及mypy登记。
新文件与旧文件原字节相等,旧/新模块对象同一性通过。未搬其它模块。
完整性证据:[derive-only/integrity.json](derive-only/integrity.json)。

## 2. 已观察到的失败

同一全仓运行中,以下两例在
`tests/unit/test_p5q_c5a_integration.py:98`的
`assert 0 <= close_seconds < 5`失败:

| nodeid参数 | 发生阶段 | CLI返回 | close到CLI退出秒数 | 证据 |
|---|---|---|---|---|
| `test_real_cli_browser_submit_bind_pending_pass[build]` | 本机假服务器qb-trigger后关闭 | exit 0,submitted_bound | 14.4371337890625 | [commands.json](derive-only/c5a-failures/build/commands.json) |
| `test_real_cli_browser_submit_bind_pending_pass[no-navigation]` | 本机假服务器第一次qb-result-fetch后关闭 | exit 0,RUNNING | 8.79266881942749 | [commands.json](derive-only/c5a-failures/no-navigation/commands.json) |

两例nodeid均以`tests/unit/test_p5q_c5a_integration.py::`为前缀。
`build/agent-0.json`记录close开始/结束时间分别为
`1793622639363`/`1793622645855`毫秒;
`no-navigation/agent-1.json`分别为`1793622883911`/`1793622892637`毫秒。
代理记录close应答为`ok: true`;不能据此把CLI退出时延断言视为通过。
每例的代理应答、trace及假服务器收到的请求也一并归档在对应目录中。
均为本机合成数据;未访问真实QuickBuild,未执行真实提交或Gerrit推送。

## 3. 停止处置

停止实现,不批量搬家、不修改任何测试、不增加skip/xfail、不提高5秒阈值,
不把SKEL-B1-03的单nodeid豁免扩展到上述两例。不重跑失败用例来替换证据。
保留derive-only试搬供审读,不是第1批已验收交付。
拆分后C8五次独立运行及完整八包验收为NOT_RUN_STOPPED。

冻结稿、安全核心、代理完整/前缀hash不变;design.md未追加声称拆分已落地的修订。
测试物理路径改动0条。试搬collect的2903个nodeid与基线双向差集为空;
既有import-linter为6 kept / 0 broken,但尚未新增八包合约。

## 4. 候选后续,尚未实施

请设计方先批准独立离线定位关闭时延:在可比环境中对照未拆分树与derive-only树,
分开观察代理close、进程退出与Python返回阶段。若证实生产关闭缺陷,另行修复后
重建基线;若拟接受环境相关时延,须另给出明确的验收裁定。
当前证据不足以判定是拆分回归、环境负载还是既有关闭问题,不自行选择原因。
不建议直接修改测试阈值或把这两例归入已有C8豁免。

全量pytest的最终统计与原文以本目录`derive-only/summary.json`、
`command.json`、`stdout.log`、`stderr.log`及`pytest.xml`为准。
最终exit 1:2900 passed / 2 failed / 1 skipped,1422.74秒;没有其它失败。
C8豁免nodeid在本次全仓中通过,但不替代规定的拆分后5次独立运行。
基线与试搬的非豁免失败数分别为0和2,门禁不通过。
