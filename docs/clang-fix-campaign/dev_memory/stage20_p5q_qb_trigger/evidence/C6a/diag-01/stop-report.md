# diag-01: close 后代理进程未正常退出

## 实测结果

FatTank回复“开始”后仅运行一次生产QbBrowser诊断,未重试。代码提交
`c88142b`,执行时HEAD为`471b0a8`。命令与exit见`command.json`,
原始结构化输出为`result.json`,不改写该文件。

执行时间为2026-10-15 17:39:48至17:41:40(Asia/Shanghai),
对应result.json的09:39:48至09:41:40 UTC。探针exit5。

| 命令 | ok | 耗时秒 | 错误码 | failure_category | 代理退出码 |
|---|---|---:|---|---|---|
| login | true | 58.354 | null | null | null(当时仍运行) |
| open_form | true | 2.429 | null | null | null(当时仍运行) |
| fill | true | 15.957 | null | null | null(当时仍运行) |
| close及进程清理 | false | 35.070 | QB_BROWSER_UNAVAILABLE | null | -15 |

12字段读回与要求相等,指纹通过;SNAPSHOT_NUM读到
`tizen-base-toolchain_20260924.094908`。`release_state=not_released`,
`form_action_releases=0`,没有调用真实qb-trigger/qb-result-fetch、没有提交或Gerrit推送。
专用库原字节hash与冻结稿hash保持任务指定值,见`validation.json`。

## close应答与清理的区别

result.json的driver trace中`close`为`ok:true`,而commands中的close为false,
不是互相矛盾:前者是代理协议应答,后者还包含Python清理进程的结果。

- `qb_browser_agent.mjs:588`:close命令等待runtime.close后返回ok。
- `qb_browser.py:355`:close清理在进程未退出时再次写close,然后wait(timeout=35);
  OSError或超时后terminate,最终才关闭stdin/stdout。
- `p5q_c6_driver_probe.py:127`:finally先调用close命令,再调用驱动close;
  进程退出码非0时由探针构造QB_BROWSER_UNAVAILABLE。
- 本次先收到close ok,清理耗时35.070秒,最终退出码-15(SIGTERM)。与上述超时终止
  路径一致;没有保存原始TimeoutExpired异常,不伪称有异常堆栈证据。
- `failure_category=null`,没有收到代理错误应答或观察到固定QB_AGENT_STOPPED行。
  不将其填成UNKNOWN/BROWSER_DISCONNECTED,也不归因于拦截判据。

## 停止与候选后续

本轮四命令全ok的验收未通过,已停止,不修复后重跑、不进入真实提交。
登录至填表这条路径本次成功,但这不能解释或证明live-03失败的根因。

只读代码比较发现:生产main在`qb_browser_agent.mjs:958`建立stdin readline循环,
closed时退出循环;本机集成入口`tests/node/p5q_cli_agent.mjs:37`在finally显式
`process.stdin.destroy()`,生产main没有对应动作。Python清理则在wait之后才关闭stdin。
这提供了“stdin/readline或其它Node句柄仍存活”的候选解释,尚未用实际生产入口的
离线退出探针证实,不能当作已定根因。本轮不改变任何退出或判定逻辑。

候选处理供设计方裁定:在本机about:blank/假服务器上,用实际生产main和保持打开的
Python stdin复现close后进程存活,核对句柄生命周期;定位后再批准最小清理修复,
补真实生产入口的正常退出回归。不得用强行忽略-15把本次判绿。

## 证据边界

`result.json.trace`是生产Python驱动的命令trace,不是完整浏览器runtime事件转录;
本次未采集服务端HTTP请求数,不填写0。提交放行0依据已验证的fill应答与本探针无
提交命令。没有账号、密码、Cookie、页面正文或原始协议事件入档。
本轮收尾只新增本目录证据与进度文档,未修改已验收生产代码或冻结稿。
