# SKEL-RESTORE-30:完整门禁及计时清单重跑失败

## 结论

RESTORE-29已离线定位并实现,但本轮未验收。完整pytest后允许的第二次单独重跑失败,
按SKEL-B1-05/RESTORE-27规则停止。不跑第三次、不访问真机、不进入r02。
这不是对解析修复正确性的否定或对失败根因的确定归因。

## 已完成的离线工作

- `replay-before/`、`replay-checks/`:实际六页顺序中前五页通过,iframe报告首次失败。
  原因是`toybox - details`无链接说明行被当作包名,不是坏thead标签。
- `replay-after/`:六页通过、网络请求0;真实归档回归夹具及六种非法说明行拒绝测试已加入。
- 封闭结构诊断已加入;用户批准第八种page_kind `configuration`。
  Policy、帧归属、精确路径表规则、唯一failed链接及read_text检查不放宽。
- mypy、ruff、7/7依赖合约、design检查、183项Node静态/单元、4/4安全组通过。
  完整门禁收集3550项,既有3502项保留,新增48项。

## 原始失败与允许的重跑

nodeid:`tests/unit/test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass[build]`。

| 运行 | 结果 | 原始证据 |
| --- | --- | --- |
| full | 3548 passed,1 failed,1 skipped;qb-trigger子进程150秒TimeoutExpired | full/stdout.txt、pytest.xml、c5a/build/server-requests.json |
| retry1 | 1 passed,26.61秒 | retry-c5a-build-1/ |
| retry2 | 1 failed,87.93秒;close_seconds为20.91734027862549,不满足小于5 | retry-c5a-build-2/stdout.txt、pytest.xml |
| retry3 | 未执行 | 任一次失败即停止 |

full服务器received为空且没有代理输出,无法进一步归因。
retry2的`c5a/build/agent-0.json`同时记录fill错误QB_BROWSER_UNAVAILABLE,
failure_category=UNKNOWN、AGENT_STOPPED UNKNOWN,未记录OPERATION_FAILED。
close开始1793948196958、结束1793948215358(Unix毫秒),差18.400秒。
因此不能把该次失败只称为关闭计时超限;UNKNOWN起因未确定。
服务器收到本机登录/配置/表单及部分字段回调,submissions为空、builds=0。

## 资源与残留

所有测试均以systemd user scope CPU400%/6GiB/swap0及nice10串行运行。
full前后available为6658/6420MiB,load1为3.37/3.29;
retry2前后available为6403/6635MiB,load1为2.48/14.83。
各次command.json保留完整free/loadavg、等待时间、CPU前十进程名与占用。
没有加压、结束他人进程、清缓存或放宽阈值。

事后存在`/dev/shm/p5q-browser-3ByKn8`,mtime为2026-11-06 14:35:45 +08:00;
未清理,不从mtime推断它属于哪个用例。`archive-check/`和`archive-check-2/`
原始检查失败保留;第二次固定阶段码PROFILES说明是残留断言。
后续完整性记录改为记录残留事实,不改变测试或安全判定。

## 候选后续处置(未执行)

由设计方另行批准对本机150秒启动超时及fill UNKNOWN做隔离诊断,
检查受限scope内浏览器事件和资源竞争;若需重验,仍采用原资源上限及原断言。
残留目录须先确认来源与进程引用再裁定清理。没有证据支持放宽安全规则或计时阈值。
本轮代码保留为未验收实现,待裁定;不追加真实读取来试错。
