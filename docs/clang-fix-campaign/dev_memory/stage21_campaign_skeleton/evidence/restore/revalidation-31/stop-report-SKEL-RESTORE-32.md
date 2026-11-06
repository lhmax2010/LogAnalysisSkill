# SKEL-RESTORE-32:重新验收资源前置等待超时

## 结论

按RESTORE-31第二.2条停止。解析修复与诊断的代码层认可不变,但重新验收未开始,
不能算通过,也没有新增测试失败。没有进入真机r02,不要求用户登录。

## 已完成

- [path-audit.md](path-audit.md)逐条审查582c65d生产diff。正常fill/submit/close
  不进入新增发现诊断分支;没有发现改变这些合法执行路径的改动。
- [source-audit.json](source-audit.json):代理安全前缀、fill起至文件末尾逐字节不变;
  整个QbBrowser类AST不变;C5a/C8入口、冻结稿不变。本轮没有生产/测试改动。
- [profile-check.json](profile-check.json)、[profile-removal.json](profile-removal.json):
  fuser与lsof +D两次检查均无引用且无警告,前缀与测试所用createRuntime一致,
  只删除/dev/shm/p5q-browser-3ByKn8,exit0,exists_after=false。
- 收尾文档第5节登记已知限制:包仅部分架构unresolvable时说明行仍fail-closed,
  不修改解析规则。

## 资源事实

首个重跑前置自2026-11-06 15:28:18至15:58:18(Asia/Shanghai),
实际等待1800.025秒,每10秒采样,共181条。

| 条件 | 要求 | 实测范围 | 是否满足 |
| --- | --- | --- | --- |
| MemAvailable | ≥6291456KiB | 6373816–7300576KiB | 全部满足 |
| load1 | ≤4 | 0.05–2.69 | 全部满足 |
| SwapFree | ≥524288KiB | 0–28752KiB | 全部不满足 |

最后采样available约7035MiB、swap约1MiB、load1=0.39。
完整证据:[retry-1/command.json](retry-1/command.json),其中started=false,
stop=RESOURCE_WAIT_TIMEOUT,exit_code=125。没有scope_argv,因为未到执行分支;
不得把等待器退出码解释为pytest退出码。

## 未执行及后续

测试执行0次,三次重验和完整pytest均未完成;通过/失败/跳过数不适用。
不是“三次中任一测试失败”,所以没有创建b7a55d8对照worktree或运行基线测试。
没有QuickBuild、Gerrit、真实gbs操作;未清缓存/调整swap/结束他人进程。
没有不受systemd资源上限约束的测试回退。

资源达标后再按裁定从头进行三次单独重跑,全部通过后才跑完整pytest。
本次不延长等待、不重试、不放宽资源门槛。原RESTORE-30失败证据原样保留。
