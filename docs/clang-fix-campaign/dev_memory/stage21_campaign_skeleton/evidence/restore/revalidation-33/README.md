# SKEL-RESTORE-33 重新验收

基线dbdc8ee,恢复后的生产代码仍为582c65d。只修改文档与证据运行器,
不修改生产、测试、冻结稿或安全规则。RESTORE-30/32原始失败与等待记录原样保留。

## 执行口径

SwapFree每次采样记录,不作门槛。每次启动前要求MemAvailable≥6291456KiB、load1≤4,
最多等待1800秒。全部测试串行使用systemd user scope CPU400%/MemoryMax6G/
MemorySwapMax0/nice10;不加-x、xdist或其它并行参数。
`run_one.py`记录argv、UTC、exit、前后free/loadavg、CPU前十进程名/占用及等待采样。
`run_three.py`任一次非零即停止,没有无条件继续测试的路径。

## 三次单独重跑

nodeid:`tests/unit/test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass[build]`。

| 运行 | 结果 | pytest耗时 | 三个CLI关闭尾段(秒,按执行顺序) |
| --- | --- | --- | --- |
| retry-1 | 1 passed | 30.78 | 0.075697 / 0.074626 / 0.078695 |
| retry-2 | 1 passed | 23.13 | 0.076763 / 0.073094 / 0.077076 |
| retry-3 | 1 passed | 23.27 | 0.077059 / 0.076798 / 0.074612 |

各次独立command.json、stdout/stderr、pytest.xml、c5a/build/下的代理/请求/CLI记录
均保留。第二次等待30.080秒、第三次等待10.039秒才满足资源条件,没有因前一次通过
而跳过前置。三次全过,无需仓外b7a55d8对照。这里只用假HTTPS服务器/本地裸库。

## 完整门禁

三次全过后执行`tests/run_quiet.py tests/ -q`,完整记录写入full/。
启动前available6744872KiB、load1=0.98,SwapFree=4KiB仅观测。
生产与测试等546份文件的前置hash写入source-before.json,完成后再核验。
完整门禁最终结果以后续记录为准,不以三次单例通过代替。

最终结果:2026-11-06 16:19:10–16:38:51 +08:00,exit0,
**3549 passed、0 failed、1既有skipped**,pytest耗时1180.28秒。
没有计时清单失败或新增C8包装失败,无追加重跑或基线对照。
运行后available6766016KiB、load1=2.44、SwapFree100KiB;前后完整采样见command.json。
546份源码/测试/冻结稿前后无变化,profiles_remaining为空,历史身份扫描残留0,
详见summary.json。完整JUnit四处测试标识符与登记身份重合,脱敏审计见
identifier-redaction.json;无结果改写。合成故障场景的预期错误保留,不计为新增失败。

本轮没有生产/测试改动,mypy、ruff生产检查、import-linter、design与安全/静态门禁
已有RESTORE-29通过证据;本轮按RESTORE-31/33要求补完三次单例和完整pytest。
这不是对RESTORE-30的UNKNOWN根因作出新判断。提交推送后等待用户新回复“开始”。

附加证据脚本/文档检查:doc-checks首次Ruff报5处import排序,只整理新证据脚本后,
doc-checks-2 exit0,Ruff通过、design 0 problem、文档diff --check通过,
再次扫描源码变化0、身份残留0。首次输出保留,未改旧测试或功能代码。
原始pytest stdout/stderr/XML与合成HTML中的行尾空白不清洗;
被通用build/忽略的C5a证据目录单独强制纳入,不修改.gitignore。

## 边界

无真实QuickBuild、Gerrit或gbs操作;没有新建真实运行目录、状态库或登录窗口。
已知限制仍为“包仅部分架构unresolvable时说明行拒绝”,不扩大解析规则。
只有全部门禁满足、证据提交推送后才进入“等待用户确认开始”,不复用历史确认。
