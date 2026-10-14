# C5a 第9.3节逐条对照

基线39e4bde。顺序对应冻结稿第9.3节16个复选框。既有部分不重写,
每项本轮均由全量pytest实际调用本机Chromium复跑,不是引用历史绿灯。
最终日志为[full-02/pytest.log](full-02/pytest.log),JUnit为同目录pytest.xml;
结果机械汇总见[audit.json](audit.json)。以下简称的源码均在仓库tests下。

- CLI: `unit/test_p5q_c5a_integration.py:23`,四参数模式。
- 工具: `node/test_p5q_c5_tools.mjs:20`,12个Node测试(含外层测试)。
- 安全: `node/p5q_c2b_safety.mjs:80`,四组JSON直接记服务器实收。
- 可信读取: `node/test_qb_browser_trusted.mjs:369`。
- 字段: `node/test_qb_browser_fields.mjs:319`。

| 条目 | 既有提交/本轮补齐与精确测试位置 | 本轮结果及实收证据(相对full-02/artifacts) |
|---|---|---|
| 1 正常提交与精确载荷 | 新增CLI `[build]`;C3 3ef542a原为假代理 | PASS;build/server-requests.json,只提交一次;Build Package List/BUILD NOTES/recorder逐字断言 |
| 2 逐跳302/307 | 0c06f15安全 `per-hop` | PASS;../../safety.json,禁止第二跳与POST重放均0 |
| 3 读取重定向到另一Successful构建 | 新增工具:108 `read redirected to different Successful build stays a read failure` | PASS;tools/redirect-response.json,QB_READ_REDIRECTED经真实Python驱动为QB_FETCH_FAILED |
| 4 已建/未建+错误表单均unknown且不重提 | 新增CLI `[error-created]` / `[error-no-build]` | PASS;对应目录server-requests.json及commands.json,builds分别1/0,各只提交一次,再次CLI already_requested |
| 5 提交落点记住Variables | 新增CLI `[build]`,fakeQuickBuild裸地址返回Variables | PASS;build/agent-0.json,landed build并BUILD_BOUND,不要求裸地址有Summary |
| 6 不跳转/多字段诊断/no-store/刷新 | 新增CLI `[no-navigation]`;可信读取:692 extra-field;字段:509 continuous denied refresh,既有39e4bde/3ef542a | PASS;no-navigation/server-requests.json;existing-trusted-requests.json;existing-fields-requests.json |
| 7 hostile outerHTML/trim | 39e4bde可信读取:373 `hostile main-world builtins` | PASS;existing-trusted-requests.json;新增假服务器也注入有缺陷trim,完整填表仍通过 |
| 8 原始无导航/脚本改Status | 39e4bde可信读取:418/:432;新增工具:27 insert-nav/change-status | PASS;tools/insert-nav及change-status,分别只在活动文档中/值不同;生产read不回退 |
| 9 登录真假阳性/重试/五次上限 | 新增工具:93四种false-positive;0c06f15 node/p5q_login_retry.mjs:45 | PASS;tools/server-requests.json;pytest.log的retry-success/five-failure-limit实际实收,第六次不到服务器 |
| 10 window.open/外站iframe | 新增工具:124;ca43b5d node/p5q_h_interception_probe.mjs:45原三模式 | PASS;tools/window-frame-trace.json;pytest.log h三模式3/3 |
| 11 Worker/WebSocket | 0c06f15安全worker-websocket,按C2B-01允许fail-closed分支b | PASS;../../safety.json,攻击HTTP0/WS握手0,浏览器关闭且临时目录删除 |
| 12 307/308合法URL及302对照 | 0c06f15安全307-308 | PASS;../../safety.json,307/308无第二跳,302有第二跳 |
| 13 版本递增/十二回调/不一致拒绝 | 3ef542a字段:409/:436/:449/:460;新增工具:65/:143 | PASS;existing-fields-requests.json;tools/rehearsal/run.json十二版本/十二POST;tools/inconsistent-callback.json零服务器POST |
| 14 人工点击前无POST/未登记落点 | 0c06f15安全credential-isolation及login_retry;新增工具:93 unregistered-landing | PASS;../../safety.json;tools/server-requests.json无未登记落点请求 |
| 15 凭据隔离 | 0c06f15安全credential-isolation | PASS;../../safety.json仅cookie/authorization/password存在布尔,不含合成值;Node/Python/stdout/stderr/trace检查 |
| 16 全部执行记录归档 | 本轮run_validation.py与各测试的实收导出 | PASS;full-02/commands.json、pytest.log/xml、artifacts请求清单,命令与exit入档 |

新假服务器为`tests/node/p5q_fake_quickbuild.mjs`,由live-12结构蓝本重新构造响应,
不读归档HTML作为响应体。保留脚本行为:坏trim、random、子标签记忆、dashboard、
动态回调版本、定时刷新。登录失败后wicket重提交由既有login_retry假服务器覆盖。
证书与DNS参数只从tests入口传入;生产Agent/Policy/installGuards与驱动零diff。

`focused-01`为开发记录(18 passed/1 failed,失败是新增工具测试自身两处断言/调用错误),
不作为最终验收。`full-01`为补每页身份计数前的全量记录,最终统一以full-02为准。
Node内部用例数不重复计入pytest通过数;全部既有nodeid保留,新增数由audit.py对账。
