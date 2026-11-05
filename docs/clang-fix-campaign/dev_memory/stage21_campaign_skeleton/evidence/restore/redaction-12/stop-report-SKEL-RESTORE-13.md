# SKEL-RESTORE-13 停止报告:既有字段窗口断言失败

## 1. 事实

2026-11-05,基线57cac6e,RESTORE-12离线阶段。
执行`.venv/bin/python tests/run_quiet.py tests/ -q --junitxml=.../full/pytest.xml`,
不加-x。02:55:20.188至03:14:27.703 UTC,exit 1,
3433 passed / 1 failed / 1 existing skipped,1147.496秒。
完整argv、负载、CPU前十见`full/command.json`,输出见`full/stdout.log`与`full/pytest.xml`。

唯一失败nodeid:
`tests/unit/test_qb_browser_node.py::test_node_c2c_trusted_reads_and_fields[test_qb_browser_fields.mjs]`。
内部子例:
`continuous denied refresh GETs do not extend quiet; uncheck and @freeze still complete`。
`tests/node/test_qb_browser_fields.mjs:530`原断言:

```js
assert.ok(window.endedAt - window.beganAt < 3000,
  `${window.name}: denied refresh must not extend quiet`);
```

失败原文:`Build Package List: denied refresh must not extend quiet`。
Node输出该子例总耗时16710.953ms,未输出该字段窗口的实际数值。
该行之前的完整fill读回、总耗时<20000ms、uncheck/@freeze操作核对已执行通过;
Build Package List对应被拒刷新未更新lastActivity的前一行断言也已通过。
这不足以确定耗时成因,不能推断为负载问题或改写安全规则。

20核;全仓前loadavg=2.95/2.94/4.57,结束=3.69/3.73/3.98。
没有中间峰值证据,不以两个端点推断运行全程负载。
该Node用例直接导入生产代理,不调用此次修改的Python脱敏或capture工具;
代理与既有测试均未改。但这不是因果排除证明。

## 2. 已完成与停点

脱敏专项最终115/115、capture本地Node9/9通过;六份旧正文复检残留0。
mypy、ruff、import-linter、design通过。安全矩阵、静态负例、安全四组封装、
C5a六参数、C8调查在本次全仓均通过,见`gate-summary.json`。
测试结束无P5Q进程/profile残留。

全仓开始后,新增脱敏实现改为稀疏匹配边界映射并增加一项实体负例;
本次收集3435,最终收集3436。最终代码仅专项验过,
**完整最终树尚未验收**,不将本次全仓标为通过。
此失败不在SKEL-B1-05计时敏感名单内,也不是SKEL-R-08的C8观测豁免。
按既有纪律停止,未修改其断言、未抬高阈值、未加skip/xfail、未重跑覆盖证据。
未启动真机,未创建live-03;正式discovery与第四批未开始。

## 3. 候选处理(未实施)

由设计方授权单独定位此既有用例:在原基线和修复树上记录每个字段的登记、
回调结束与quiet结束时间及负载,判断是否是浏览器调度延迟或其它路径。
只增加测试观测,不放宽3000ms阈值、不改Policy或代理停止规则;
在取得证据并裁定后,重新完整验收最终树,再决定能否开展唯一一次三页真机取证。
本报告不自行将它加入计时豁免清单。
