# SKEL-RESTORE-09:真机首个配置页读取安全停止

## 1. 结论与范围

SKEL-RESTORE-08第二步仅执行一次。用户在对话回复“开始”,登录成功;
读取首个`/overview/1917`时发生`FETCH_CONTINUE_FAILED`,立即停止。
没有重试、换构建、扩放行或实施campaign-discover。代理与驱动原文件未修改。

命令、UTC起止、exit 4见`live-01.command.json`;标准输出/错误见
`live-01.stdout.log`与`live-01.stderr.log`。现场只执行login与逐页GET,
没有调用运行、填表或提交,没有访问Gerrit或运行gbs。

## 2. 事件顺序与证据

所有毫秒均相对于工具启动,来源`live-01/run.json`:

1. 登录返回ok=true(行50),框架启动自检通过(行55);登录期间4个DENIED,
   路径均为既有脱敏形态`<other>`(行64-83)。不追溯或输出凭据。
2. 59109ms开始读取`https://quickbuild.tizen.org/overview/1917`(行7-8);
   59111ms主帧Document GET请求,响应采样为59428ms(行29)。
3. 响应HTTP 200,Content-Type `text/html;charset=utf-8`,未观察到
   Content-Disposition、重定向跳或Download(行9-14、28-39)。
   page.goto没有完成,redirect_chain=[]表示未取得完整链,不是证明不存在其它跳。
4. 首条OPERATION_FAILED为(行84-92):

   ```json
   {"operation":"Fetch.continueRequest","phase":"read","stage":"request","path":"<other>","generation":2,"category":"REQUEST_ID_INVALID"}
   ```

   随后AGENT_STOPPED类别FETCH_CONTINUE_FAILED(行93-96)。该条没有时间戳,
   不能精确断言它在59428ms之前或之后;可以确定关闭/读取失败发生于本次导航窗口。
5. 59447ms页面关闭,59965ms浏览器断开(行40-48)。工具只记录固定
   `CAPTURE_ERROR`,不保留原始异常消息或堆栈(行53)。profile_removed=true(行103),
   结束后只读复核`/dev/shm/p5q-browser-*`为空。

配置页响应元数据已留存,正文未归档。1204735/1204736全部构建页、
html_report、iframe与日志都是NOT_COLLECTED。

## 3. 判据与不能推断的事项

SKEL-R-04/R-08只豁免**Fetch.failRequest**的REQUEST_ID_INVALID。
本次是**Fetch.continueRequest**,应继续安全停止,不能套用DENY_TARGET_GONE豁免。
不是原窄化实现失效的证据,也不是允许继续读取的理由。

失败路径为`<other>`,与主导航`/overview/<id>`形态不同。按取证包装的允许分支,
可能是导航边界上的静态资源继续操作;现有trace没有精确资源路径/类型、请求ID生命周期,
不能唯一确定浏览器为何使该ID失效,也不能判定与历史live-01是同一根因。
“底层请求已取消”仍是候选解释,不由错误分类直接推出可安全放行。

RESTORE-08第三.1四项条件:iframe/日志同源、重定向链、日志文本/Download、
候选文法均未取齐,保持UNKNOWN。第二批已验收内容不受影响。

## 4. 候选后续(仅方案,待裁定)

- 保持所有安全停止条件不变,先授权一次离线调查:在仓外临时副本/测试入口记录
  封闭资源类型、匿名请求编号、导航代次与相对时间,复现登录页静态资源与首个read
  导航竞争。新增continueRequest失败的原停止断言,不得改成忽略异常。
- 如离线证据确认仅为切换时序,再单独裁定是否允许取证脚本增加有上限的静默等待,
  或调整观察采样时点;必须用可控延迟假服务器验证,不在本次真机上试错。
- 页面URL/iframe/日志事实仍需另行授权一次只读取证。本次“一次”额度已经使用,
  不自行重跑。没有依据提出扩大白名单、重试写请求或豁免continue操作的方案。

以上均未实施。提交本报告后停止,等待设计方裁定。
