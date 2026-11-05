# SKEL-RESTORE-08 发现页面只读取证

当前状态:RESTORE-12路径与脱敏修复已实施,全仓既有字段测试失败,
按RESTORE-13停止(见`../redaction-12/stop-report-SKEL-RESTORE-13.md`),未获真机门禁。
六页读取事实保留,iframe/日志未读取,没有重新启动真机。

## RESTORE-12存档修正

原PageRedactor使用splitlines偏移,与HTMLParser的LF行号不一致,独立CR导致
身份单元格漏遮蔽且标签被误改。旧run/validation记录中的“检查通过”不代表
没有此缺陷。按裁定对live-01(无正文)、live-02全部六份正文后处理,
只改02.response.html中的完整会话身份一次,全六份复检残留0;
前后hash与计数见`archive-redaction-12.json`。历史run中的原hash保留,
当前文件hash以该清单为准,不改写git历史。

`02.response.html`中的`</thea&lt;USER&gt;`保留原样:原始未脱敏正文没有存盘,
无法逐字恢复被覆盖片段,不能凭猜测修补标签。该文件只作为读取/脱敏后处理
证据,不作为原始HTML结构完全保真的样本。

新worker显式使用SessionPageRedactor,仅在内存记住本次会话账号与显示名,
对文本和属性值全局替换,不动标签名或属性名;凭据检查不放宽。
元数据改记identity_replacement_count(替换次数)和identity_remaining_count(必须0),
不再以登记位置外计数代替残留检查。新捕获只读html_report及其两级唯一链接,
使用live-03新目录;须完成门禁并由用户确认开始,不复读其它前置六页。

## 工具

- `capture.mjs`:复用生产createRuntime与Agent.login;独立精确路径包装只允许当前
  主帧GET,保留原登录规则。固定六页依序核验后,从惰性正文取唯一iframe,
  再取zlib/armv7l失败日志链接;没有运行、填表、提交命令。
- `redact_capture.py`:长驻内存PageRedactor上下文;HTML登记身份与凭据,
  文本严格解码后不经过DOMParser,已登记身份按单词边界遮蔽;
  写前/写后检查,失败删除新建文件。原始正文与脱敏上下文不落盘。
- `offline.test.mjs`:私有Xvfb、本地HTTPS与测试证书;只有此测试入口模拟登录。
  现场入口不传host-resolver或测试证书参数。

历史live-01命令(不可复用;RESTORE-12只允许剩余三页,当前尚未获真机门禁):

```sh
/home/linhao/.local/bin/node docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/evidence/restore/discovery-capture/capture.mjs --live
```

输出为本目录`live-01/`:顺序编号的脱敏正文、`run.json`。
每页包含请求URL、状态、Content-Type/Content-Disposition、重定向链、Download标记、
主帧标记、耗时、脱敏正文sha256及登记位置外身份计数。失败也写run.json并清理浏览器。
只在内存取两个获准响应字段,不读请求头、不落盘其它响应字段。
登记URL逐字记录;被拒的非登记URL不取可能含凭据的查询值,记`<UNREGISTERED>`。
profile删除结果必须为true。不得因失败改读其它构建或重新登录。

## 离线验证

`offline-01/command.json`记录命令、UTC起止与退出码;stdout/stderr原样保留。
Node **7 passed / 0 failed / 0 skipped**,20.21秒:

1. 同源URL、构建号、查询/片段、用户信息、穿越/编码分隔符检查;UTF-8非法字节与64MiB上限。
2. 当前主帧唯一GET与请求/响应阶段;子帧、POST、其它阶段、/log、/artifacts、REST、307/308均拒绝。
3. 完整八页正常读取:iframe自动加载未到服务器,显式主帧读取仅一次;日志尖括号保留,合成身份与token遮蔽。
4. 外站iframe在请求前停止。
5. 307停止,目标服务器未收到后续禁止请求。
6. Content-Disposition attachment以QB_DOWNLOAD_UNSUPPORTED停止。
7. 上述真实Chromium集成父测试通过,每次profile均删除。

以上只验证取证工具,不是恢复第3批功能验收。

## 真机结果

用户确认原话:“开始”。命令及UTC起止见`live-01.command.json`,exit 4,
2026-11-04 12:27:40.533至12:28:41.214 UTC,共60.681秒。

| 项目 | 实测 | 证据 |
| --- | --- | --- |
| 登录 | ok=true | `live-01/run.json:50` |
| 首个请求 | GET https://quickbuild.tizen.org/overview/1917,主帧 | 同文件`:19` |
| 响应元数据 | HTTP 200,text/html;charset=utf-8,无Content-Disposition | 同文件`:9`,`:28` |
| 重定向/Download | 观察到的请求redirect=false,Download事件0;page.goto未完成,完整重定向链未取得 | 同文件`:12`,`:34`,`:39` |
| 首条起因 | Fetch.continueRequest/read/request/\<other\>/generation=2/REQUEST_ID_INVALID | 同文件`:84` |
| 安全停止 | AGENT_STOPPED,FETCH_CONTINUE_FAILED | 同文件`:93`;`live-01.stderr.log:2` |
| 工具退出 | STOPPED,CAPTURE_ERROR,exit 4 | 同文件`:3`,`:53`;`live-01.command.json` |
| 清理 | PAGE_CLOSED=59447ms,disconnected=59965ms,profile_removed=true;事后/dev/shm无p5q-browser目录 | 同文件`:40`,`:103` |

首个配置页正文尚未归档;其它五个固定页、iframe和包日志均未读取。
四项实施条件没有取齐,不能宣称通过。详见
[stop-report-SKEL-RESTORE-09.md](stop-report-SKEL-RESTORE-09.md)。

## RESTORE-10重取证:live-02

修复提交b29d6f3先完成离线门禁并推送,用户再次回复“开始”后启动。
调用原capture导出函数,仅输出目录改为live-02;完整命令/UTC/exit见
`live-02/command.json`,exit4,190.095秒。登录成功,固定六页200并归档,
无重定向/Download,均text/html;charset=utf-8,无Content-Disposition。

`06.response.html:803`唯一iframe src为
`/download/1204736/html/HTML REPORT/index.html`;原exactLink在URL解析前拒绝空格,
故CAPTURE_PATH_UNSUPPORTED。没有显式读取iframe或日志,没有绕路与重试。
离线标准解析与原工具拒绝的对照见`live-02/path-probe.json`。
父overview身份计数为2,其余五页0;未输出名字,需人工确认新身份位置。
trace无OPERATION_FAILED/AGENT_STOPPED,最终profile删除且无残留。

详见[SKEL-RESTORE-11停止报告](stop-report-SKEL-RESTORE-11.md)。
