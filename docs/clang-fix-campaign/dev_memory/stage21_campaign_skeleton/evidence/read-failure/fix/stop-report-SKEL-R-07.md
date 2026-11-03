# SKEL-R-07: C8采样出现新的登录阶段失败形态

日期:2026-11-03。基线:8d60851。状态:STOPPED,不重跑覆盖原证据。

## 已落实范围

SKEL-R-04窄化与SKEL-R-06三处断言更新已实施,生产改动仅限installGuards。
分类正则不变,仅Fetch.failRequest/REQUEST_ID_INVALID不停止,逐次记DENY_TARGET_GONE,
不占第一条OPERATION_FAILED。其它操作和错误类别保持原停止规则。
三处授权测试之外的既有测试字节未改,证据见implementation/integrity.json。

定向pytest223 passed/0 failed/0 skipped;新增Node矩阵23例通过,
真实Chromium取消请求测试通过;四组本机安全4/4。mypy、ruff复核、
import-linter、design检查通过。nodeid3098全部保留,新增2,共3100。
这不是完整验收通过:40次采样与完整全仓均未完成。

## 停点与事实

正式C8序列前三次PASS,第4次FAIL。每轮完整运行原11场景,无筛选、无改阈值。
第4次2026-11-03T11:43:19.088485Z开始,11:46:42.605520Z结束,exit1,
203.517秒。20核,loadavg前3.76/2.48/1.64,后9.94/6.42/3.37。
来源:`implementation/c8-04/command.json`;完整断言与输出:`stdout.log`、`pytest.xml`。

失败场景为第5个`racing-wicket-navigation`,不是先前的racing-meta-refresh。
逐项证据:`implementation/c8-04/c8/racing-wicket-navigation.json`:

- :5、:14、:25:执行阶段仍为login,帧归属为true。
- :9-20、:43-49:服务器只有GET /signin,HTTP200,无登录POST。
- :31:reads=[];:55:synthetic_submissions=0。还未进入表单、提交或read。
- :32-42:trace只有FRAMEWORK_SELF_TEST;无OPERATION_FAILED、DENY_TARGET_GONE、
  AGENT_STOPPED。因此本场景failure_category为NOT_COLLECTED,不能用其它场景的UNKNOWN补齐。
- :50-54:harness_failure为TargetClosedError/OTHER_FRAMEWORK_ERROR,agent_code=null。
- :56:profile_removed=true。

原测试`tests/node/p5q_c8_investigation.mjs:109`要求harness_failure未定义;
此次实际存在上述对象。pytest层在`tests/unit/test_p5q_c8_investigation.py:26`
的`assert result.returncode == 0`失败。stderr为固定INVESTIGATION_STOPPED AssertionError。
现有harness没有保存失败时login命令的返回值或最后进行到哪个模拟登录动作;
不能据此认定登录超时、浏览器自行退出、机器负载或本次修复是根因。

同一轮前面的`racing-meta-refresh`场景已完成,与上述失败区别如下:
- 该场景:1108首次OP为page.goto/NAVIGATION_INTERRUPTED;:1117为原UNKNOWN应答诊断。
- :1161、:1168分别记DENY_TARGET_GONE,均idle/request,/wicket/page,generation6。
- 文件尾runtime_failure=null、browser_connected_after_reply=true、profile_removed=true;
  没有FETCH_CONTINUE_FAILED,没有harness_failure。两个失效拒绝没有导致整体停止。
这两条是自然采样中已观察到的窄化路径,不是新的登录失败的起因证据。

## 判定与未执行项

SKEL-B1-03第3项、SKEL-B1-05第4项仍约束C8新失败形态;
原5次基线仅有racing-meta-refresh/TargetClosedError/OTHER_FRAMEWORK_ERROR/
FETCH_CONTINUE_FAILED,见progress第7.1节。此次场景与阶段均不同,
且没有SKEL-R-04第6项的failRequest/REQUEST_ID_INVALID停止签名。
SKEL-R-06只允许更新三处诊断断言,不能扩展为修改该调查harness或放宽验收。
因此暂停而非重跑覆盖,不把“FETCH_CONTINUE_FAILED为0”当作整轮通过。

- C8正式4/20:3通过、1失败,余16未运行;第4轮余6个场景未运行。
- C5a late-build正式0/20:全部NOT_RUN_STOPPED。
- 完整全仓NOT_RUN_STOPPED,没有使用-x,没有以局部数量冒充完整门禁。
- 三次通过和一次失败均独立留存;另一次包装器汇总失败不计入正式4次,
  原pytest通过证据在implementation/wrapper-error-c8-01,详见README。
- 未运行真机QuickBuild、Gerrit或真实gbs;未新增加压进程或临时代理副本。

## 候选下一步(仅供裁定,本轮不实施)

1. 优先补调查harness的离线观测:只增加固定登录步骤名、login命令应答的固定字段、
   页面关闭/浏览器断开时间点,不记录错误原文/凭据,不改断言或超时。
   在独立本机输出目录复现;需要设计方授权修改此既有测试入口。
2. 可授权在负载可控时对同一未改测试作基线/修复树交替对照,独立保留所有失败。
   对照只能帮助归因,不能自动把新形态纳入豁免,也不能覆盖本次原始失败。
3. 不建议为通过门禁延长模拟登录时限、吞掉TargetClosedError或扩大failRequest例外。
   没有证据支持这类规则变更,本轮均未实施。

等待设计方裁定,不进入第3.5或第4批。实现与测试证据保留供审读,不宣称验收通过。
