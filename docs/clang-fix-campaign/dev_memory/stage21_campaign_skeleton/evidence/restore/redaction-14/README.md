# SKEL-RESTORE-14 最终树门禁

基线f6216ec,2026-11-05。**离线门禁通过,尚未真机读取**。
名单变更仅在progress §10.1/§38、design §4.6登记;没有改测试断言或生产代码。

| 项目 | 结果 | 证据 |
| --- | --- | --- |
| 原失败nodeid独立重跑 | 三次全部通过,122.118/117.935/118.226秒(wrapper) | `fields-rerun-01/`至`03/` |
| 最终树完整pytest,无-x | 3435 passed,0 failed,1 existing skipped;pytest 1158.44秒 | `full/stdout.log`, `full/pytest.xml` |
| 全仓wrapper | exit 0,1163.983秒;前后loadavg 1.75/2.94/3.72与2.25/2.49/3.49 | `full/command.json` |
| mypy | 169源码通过 | `mypy/` |
| ruff | 通过,运行器专项也通过 | `ruff/`, `runner-ruff/` |
| lint-imports | 7 kept,0 broken | `imports/` |
| design检查 | 0 problem | `design/` |

唯一skip是大小写敏感文件系统上的平台专用用例,不是新增豁免。
字段nodeid在本次全仓中也通过;没有门禁后追加重跑,没有新增读取失败观测。
C5a六参数、C8、代理矩阵/静态负例、四组安全测试封装均通过,见`summary.json`。

每次运行的`command.json`含完整argv、UTC起止、exit、前后loadavg、CPU核数,
以及前后CPU前十进程名/占用。只记名称与数值,不记录命令行。
`load-samples.jsonl`是非连续的额外采样,不代表全程峰值。

`run_gates.py`顺序执行三次专项、完整全仓和各门禁,任何非零先停止交还判定,
不自动把全仓所有失败都重跑,不吞掉失败。所有浏览器测试用私有显示与本机夹具。
`inputs.json`记录526份既有Python/Node源码与193份原RESTORE-13证据的hash;
`unchanged-after.json`确认运行结束全部字节不变,旧失败记录没有覆盖。
`cleanup.json`确认无P5Q profile或自身进程残留。
源码/说明文档diff-check通过;23处合成HTML原始证据行尾空白保留,不格式化证据。

下一步由用户确认后仅运行一次剩余三页取证,输出到新的`discovery-capture/live-03`。
本目录不证明iframe/日志的真机响应事实,不作为发现CLI实现验收。
