# SKEL-RESTORE-28:首次发现试运行结构核验停止

日期:2026-11-06。执行基线97217e0(生产代码6f5e801)。依据RESTORE-25/27。
用户本次确认原话:“开始”。唯一一次qb-discover已执行,失败后停止,未重试。

## 1. 命令与资源

完整argv/UTC/exit/free -m/loadavg见[producer-command.json](producer-command.json)。
实际业务命令为:

```bash
systemd-run --user --scope -p CPUQuota=200% -p MemoryMax=3G -p MemorySwapMax=0 nice -n 10 /home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python -m tizen_qb_verify qb-discover --config /home/linhao/Toolchain/campaign-discover-trial/r01/config.yaml --state-root /home/linhao/Toolchain/campaign-discover-trial/r01/state-root --qb-project tizen_base --build-id 1204735
```

首次资源查询1分钟负载12.96,当时未启动;准备记录工具期间负载下降,
正式启动前新采样6.86,可用内存9555MiB。启动UTC05:45:48.258756,
结束UTC05:47:25.550388,耗时97.291秒,exit4。
运行后可用内存9277MiB,loadavg三值3.65/5.81/3.96。
运行中systemctl实查CPUQuotaPerSecUSec=2s、MemoryMax=3221225472、MemorySwapMax=0;
argv明确nice10,没有无限制回退、并行门禁、资源加压或结束他人进程。

## 2. CLI原始结构化结果

```json
{"error_code":"DISCOVERY_REPORT_AMBIGUOUS","failure":{"agent_error_code":"DISCOVERY_REPORT_AMBIGUOUS","agent_exit_code":null,"agent_exited":false,"command":"discovery_read","failure_category":null},"reason":"REPORT_STRUCTURE"}
```

可确定:discovery_read返回了结构核验拒绝,不是成功采集。
不可确定:具体是哪一页、哪一项结构检查、是否已读到Details或包日志;
应答不含路径或first_failed_check,不能根据通用错误名猜成“Details有重复包”。
agent_exited=false仅为错误捕获时观察;null退出码不是正常退出0的证据。
代理trace(含elapsed_ms)、Content-Type原值、重定向链、Download事件均按RESTORE-27
记NOT_COLLECTED。stderr未见固定QB_AGENT_STOPPED行,但这不能替代缺失的代理trace,
不据此宣称安全事件为0;报告以CLI错误码为准。

## 3. 产物与dry-run

仓外state-root仍为空,无discover-manifest.json、无归档包日志、无SHA/字节清单可填。
没有清单,所以没有运行campaign-discover --dry-run,没有analyzer结果或过滤结论。

| 预期观察对象(不是实测失败包清单) | 本次状态 | 跳过/将建档结论 |
| --- | --- | --- |
| zlib | NOT_COLLECTED | 未进入dry-run,不能判为过滤跳过 |
| libtirpc | NOT_COLLECTED | 未进入dry-run,不能判为过滤跳过 |
| elfutils | NOT_COLLECTED | 未进入dry-run,不能判为过滤跳过 |

日志读取是否全部成功:NOT_COLLECTED。没有status=ok日志,不填“已通过read_text检查”。
没有状态库、KB或workspace产物;无克隆、建档、构建提交或推送。
执行后的scope为inactive/dead,未发现本仓库代理进程或/dev/shm/p5q-browser-*目录。
私有运行脚本、stdout/stderr原件留r01,不提交正文或配置。
结构化摘要见[result-summary.json](result-summary.json)。

## 4. 候选后续(本轮未实施)

先离线将已有1204735/1204736脱敏归档代入当前discoveryDOM/DiscoveryScope,
逐个核对页面身份、Child Build/变量/Details表与当前文法,保留首次失败项。
若归档不能复现,另行批准只增加封闭的页面pathShape与first_failed_check诊断;
不放宽任何身份、帧归属、精确路径或失败单元格规则,不直接修改过滤器。
本轮不补字段、不换构建、不二次登录,等待设计方裁定。

## 5. 归档与结论

只归档命令/资源事实、固定CLI应答及本报告;生产脱敏检查通过,
已知本机身份完整词边界残留扫描为0。未读取或导出登录账号/显示名,
本次会话身份原文为NOT_COLLECTED,不声称进行了未知身份的字符串比对。
全部正文与配置均未入仓,生产/测试/冻结稿未改。
**自动发现真机只读已执行但未通过验证;dry-run未执行。**
