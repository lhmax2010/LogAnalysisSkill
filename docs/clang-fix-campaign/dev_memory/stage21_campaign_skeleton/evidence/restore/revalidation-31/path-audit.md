# SKEL-RESTORE-31:fill / submit / close 路径审查

审查范围:`git diff b7a55d8 582c65d`,并读取当前调用点。未修改任何生产代码。

| 改动点 | 是否影响被审查路径 |
| --- | --- |
| qb_browser_agent.mjs:715,Agent.command catch增加诊断应答字段 | 条件限定discovery_read/read_text且error.page_kind存在;fill/submit/close不进入。submit已放行后的unknown返回在新增分支之前,顺序未改。 |
| qb_browser_agent.mjs:880,discoveryRead构建号错误附诊断 | 只由发现命令调用;原QB_READ_ID_MISMATCH条件/码不变;不参与普通read及填表/提交/关闭。 |
| qb_browser.py:34,诊断枚举和validate_discovery_facts | 纯常量/函数定义,没有运行时浏览器操作;只有新字段存在才校验。 |
| qb_browser.py:95,QbBrowserError.discovery_facts初始化 | 所有异常对象新增默认None属性;不抛错、不修改原错误码/阶段/超时。 |
| qb_browser.py:115,failure_facts附诊断 | 仅discovery_facts非None才添加;正常fill/submit/close没有这组字段,原输出不变。 |
| qb_browser.py:228,decode_response局部初始化/新分支 | 正常应答没有page_kind/first_failed_check/counts,不进入新分支。注入含这些字段的非发现命令应答会作为协议错误被拒,属于RESTORE-29诊断协议校验,并非合法fill应答路径。submit_sent时沿用unknown。 |
| qb_browser.py:277,异常对象保存discovery_facts | 常规命令仍为None,不改变既有映射、关闭或进程等待。 |
| qb_discovery_scope.mjs,说明行处理/封闭检查/consume与log包装 | 只由discoveryScope使用。普通C5a命令不执行discovery_start;scope为null,不调用这些函数。模块初始化仅定义常量/函数/类。 |
| 新Node/Python诊断测试及两个pytest包装 | 增加独立测试,没有修改C5a/C8脚本、断言、时限或fixture。 |
| 文档及证据脚本 | 不被生产CLI和C5a导入。 |

结论:没有发现改变fill/submit/close合法执行路径的改动。没有改变Policy、
FrameOwnership、installGuards、表单校验、字段窗口、submit、runtime.close、
QbBrowser.command/close的实现;这些代码与b7a55d8一致。
不能由此推断RESTORE-30失败根因;只支持按裁定进行受限资源下的对照验收。

Agent源码前缀(含export class Agent {)前后hash相同:
594107e04912b90ef803b3f2a1142b5b42afab83399829dba4e3c8e95664095c。
完整代理当前hash:5583d6bec7504fb3ef595bcd5612450a8b577340581f16b3a6fd981afd239ac1。
