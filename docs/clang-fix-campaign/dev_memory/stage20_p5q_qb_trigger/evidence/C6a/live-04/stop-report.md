# live-04: login超时,未进入提交

## 授权与前置

FatTank在2026-10-19重新回复“确认提交”,并要求当场核对,不复用10-15的检查。
`preflight-2.json`记录11:53:59至11:54:19(Asia/Shanghai)的只读核对:

- 专用库SHA256匹配,三张QB表均0行,unit为SANDBOX_PUSHED。
- 无P5Q profile、代理或Playwright Chromium残留;冻结稿hash和配置未变。
- 10秒间隔三次D状态均0,未触发持续/home磁盘阻塞的人工闸门。
- free显示内存available12Gi,swap剩余478Mi;/home可用231G。

## 一次执行

生产argv逐字等于live-01,见`trigger/command.json`;没有--retrigger或测试参数。
2026-10-19 11:55:15至12:05:59(Asia/Shanghai),总耗时644.008秒。
生产CLI exit5;外层记录命令exit0仅表示证据保存成功。
stdin为DEVNULL;没有终端登录输入,未读取或记录账号、密码、Cookie。

完整stdout在`trigger/stdout.json`:

```json
[{"action":"submit_failed","campaign_unit_key":"p5q-c6-libtirpc-20261015","diagnostic_dir":null,"error_code":"QB_LOGIN_TIMEOUT","message":null,"qb_build_id":null,"request_id":null,"request_seq":null,"sbs_target":"platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0","status":"SANDBOX_PUSHED"}]
```

stderr只有固定登录提示,没有QB_AGENT_STOPPED行。生产trace归档为`trigger/trace.jsonl`:

```json
{"action":"BROWSER_COMMAND_FAILED","agent_error_code":"QB_LOGIN_TIMEOUT","agent_exit_code":null,"agent_exited":false,"command":"login","failure_category":null}
```

该trace记录的是login错误发生时的进程状态,不是清理结束后的退出状态。
没有request_id,未生成提交意图,三张QB表仍空。因此没有成功提交或构建号;
按裁定“其它任何结果停止”,不重试、不运行fetch,不做人工绑定、不进入C6b。

## 关闭阶段与证据边界

被动/proc采样在t=608.895秒最后观察到本次Chromium,CLI在t=644.008秒结束,
其间约35.113秒,与P5Q-C6A-04接受的关闭延迟一致。该差值不是直接的close调用
计时。采样没有取得代理的终态wait status,所以代理实际退出码为NOT_COLLECTED,
不能把已知缺陷常见的-15伪写成本次实测。生产CLI退出码5是确定值。

没有保存真实页面、登录请求链或三条件快照,不能据超时推断“没有人工登录”、
“窗口未弹出”或“登录检测有错”。固定提示与Chromium进程存在也不能证明用户
看到了窗口。后续若需定位,先由FatTank补充现场事实,再由设计方指定取证范围;
本轮不自行重跑、不改变时限或任何生产逻辑。

## 状态与补充要求

`stop-audit.json`确认SQL与live-01逐字相同,DB原字节SHA256仍为
`bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405`;
冻结稿hash不变。无P5Q代理/Chromium/profile或.transport残留。

完整argv、起止时间、exit、stdout、stderr、SQL导出和DB hash均在`trigger/`。
fetch未执行,故不建立虚假的fetch输出目录。父构建BUILD_NOTES、BUILD_REFERENCE、
SNAPSHOT_NUM回显均NOT_COLLECTED,无可比较的请求标记或新冻结值。
campaign_qb_profiles为0行,“提交成功后”检查新快照manifest的条件未满足,
本次没有发起manifest GET;不能用diag-01历史快照冒充本次冻结值。

原始网络请求数未采集,不填0。本轮只有一次qb-trigger调用,没有额外QB诊断请求、
Gerrit推送或Accept/Ready to Accept操作。全部收尾只改文档与脱敏证据,不做修复。
