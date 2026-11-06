# SKEL-RESTORE-31 重新验收记录

基线`582c65d`,仅文档与证据脚本;不改生产、测试、冻结稿、安全规则或资源阈值。
本目录不含真实QuickBuild页面、日志或凭据。旧RESTORE-30失败证据原样保留。

## 路径核对

[path-audit.md](path-audit.md)逐项列出582c65d的所有生产改动及其调用条件。
[source-audit.json](source-audit.json)用字节比较确认代理安全前缀与fill至文件末尾
未变,用AST比较确认整个QbBrowser类未变,同时核对C5a/C8入口与冻结稿。
共享异常对象新增默认None字段不改变合法fill/submit/close应答。
代码层认可来源为RESTORE-31,不据此把先前UNKNOWN归因于环境或宣称门禁通过。

## 指定残留目录

[profile-check.json](profile-check.json):fuser与lsof +D均exit1、无输出,未见引用;
目录非符号链接,前缀与C5a调用的createRuntime一致。
[profile-removal.json](profile-removal.json):删除前重复核对,只删除指定的
`/dev/shm/p5q-browser-3ByKn8`,exit0、exists_after=false。未清理其它目录/缓存,
未结束任何进程。脚本以固定路径执行,不是通用清理工具。

## 资源闸门

`run_one.py`每10秒保存free -m、loadavg、CPU核数、CPU前十进程名/占用,
不采集进程argv。开始前要求available≥6291456KiB、SwapFree≥524288KiB、load1≤4,
使用单调时钟最多等待1800秒。成功后唯一执行方式为systemd user scope
CPUQuota400%/MemoryMax6G/MemorySwapMax0/nice10。没有无限制运行的回退。

`retry-1/command.json`中的started表示测试是否实际启动;等待本身不计通过/失败。
测试nodeid为
`tests/unit/test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass[build]`。
同一轮须单独3次全部通过才进入完整pytest;测试失败才进入b7a55d8的仓外对照。
资源等待超时则直接停止报告,不启动对照或真机。

已知限制:包仅部分架构unresolvable时说明行仍拒绝,本轮不扩展。
此项已登记在收尾文档第5节。r02仍须门禁通过及用户新的“开始”。

## 本轮结果:资源前置停止

15:28:18–15:58:18 +08:00等待1800.025秒,181次采样中swap余量最大28752KiB,
始终不足524288KiB;available和load1始终达标。等待器exit125,
started=false、RESOURCE_WAIT_TIMEOUT。测试0次,不计通过/失败/跳过;
无基线worktree、无全仓pytest、无真机。详见[RESTORE-32停止报告](stop-report-SKEL-RESTORE-32.md)。
