# Stage15 P1 EF-5 Environment Spike

日期:2026-10-08。状态:**BLOCKED**(本轮本地COOKIE_HEADER_FORMAT拒绝,非服务端拒绝)。
权威:`../../design.md` v1.5.19-FROZEN §1.4 EF-5、§4.1
qb-sbs-trigger/qb-result-fetch。设计稿不改动。

## 1. 计划与安全边界

1. 独立探测Basic Auth轻端点;configuration path解析另行取证。
2. 指定既有SBS build,读取页面与REST字段、SBS_TARGET、架构表示。
3. 同一SBS对应的上级TRIGGER,观察accept事实;不能仅凭一个成功状态
   推断accept为门2通过的必要条件。
4. 准备完整真实提交请求,等待FatTank指定目标并明确确认,未经确认不发出。

凭据仅来自`QB_PASSWORD`/`QB_COOKIE`环境变量或本人终端getpass;
不读磁盘cookie jar、不读浏览器凭据、不将秘密放到命令行/日志/Git。
HTTP只允许白名单只读URL,包括禁用重定向;即使GET也禁止`/rest/trigger`。
脚本仅位于`../../spikes/`,不进入任何生产包。
原有无关工作区改动不处理。

## 2. 初始事实与输入

本节为开始时状态;实际本人输入与受阻结果见§7。

- `QB_PASSWORD`/`QB_COOKIE`均未设置,仅检查存在性,未回显值。
- QB用户名、既有SBS/上级TRIGGER build号、configuration path待FatTank提供。
- 本机`gnome-terminal`/DISPLAY可用,拟通过其getpass输入凭据。
- 连接约定复用shared的QuickBuild base URL、URL规范化、HttpResponse及登录页识别;
  qb-discover现有发现器只枚举failed builds并从文件读cookie,不适合完整SBS样本选择,
  不为方便而读取该文件或篡改其生产行为。
- `spikes/ef-spike-protocol.md`为未跟踪历史草稿,不入库、不改写、不作为现行权威。

## 3. 进度与证据

| 项目 | 状态 | 证据/下一步 |
|---|---|---|
| EF-5① Basic Auth/独立配置解析 | BLOCKED_REST_ACCESS | 匿名401;Basic GET版本/配置均500 AccessDeniedException;`evidence/authenticated-01/requests.json` |
| EF-5③ SBS结果与绑定字段 | BLOCKED_REST_ACCESS_AND_PAGE_LOGIN | 样本1069532:REST均500,无Cookie的页面302到signin,未取得业务数据 |
| EF-5④ 上级TRIGGER的accept | PENDING_BUILD_ID | 确认同一SBS对应关系后取证,不凭时间接近猜父子关系 |
| EF-5② 一次真实REST提交与映射 | WAITING_EXPLICIT_CONFIRMATION | 尚无目标/SBS_TARGET/参数确认;未发出提交 |

只读脚本:`../../spikes/ef5_probe.py`。新证据将在本目录`evidence/`落盘,
每个响应先脱敏再写入,附URL/状态/形态/脱敏响应sha256/自检结果。

## 4. 人工闸门与挂账

真实提交只能由FatTank对完整请求确认后执行一次。本轮实现的探测器没有POST入口。
取证不足的假设标为待实测,不以官方API文档或模拟响应冒充Tizen环境事实。
结论写`../../spikes/ef_report.md`,如需改设计只列影响段落,不改`design.md`。

## 5. 本轮实跑

### 5.1 匿名对照(不是Basic Auth成功证据)

```text
$ .venv/bin/python docs/clang-fix-campaign/spikes/ef5_probe.py --anonymous-only --output docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/anonymous-01
READ-ONLY: no build submission, trigger, cancellation or state mutation.
version-anonymous: HTTP 401; empty; evidence=version-anonymous.response.txt
Evidence credential self-check: PASS. POST/trigger requests: 0.
exit=0
```

GET URL、状态、形态与空body的摘要在`evidence/anonymous-01/requests.json`;
响应body原文(空)为同目录`version-anonymous.response.txt`。
401包含`WWW-Authenticate: Basic realm="QuickBuild"`。
run.json明确`password_available=false/cookie_available=false/post_requests=0`。

### 5.2 本人getpass终端

首次gnome-terminal启动exit127,原文:

```text
/usr/bin/gnome-terminal.real: symbol lookup error: /snap/core20/current/lib/x86_64-linux-gnu/libpthread.so.0: undefined symbol: __libc_pthread_init, version GLIBC_PRIVATE
```

仅为子进程清除Snap动态库相关环境后成功启动(exit0):

```sh
env -u LD_LIBRARY_PATH -u LD_PRELOAD -u GTK_PATH -u GIO_MODULE_DIR gnome-terminal --title='P1 EF-5 read-only probe: private getpass input' --working-directory=/home/linhao/Toolchain/development/LogAnalysisSkill -- /home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python docs/clang-fix-campaign/spikes/ef5_probe.py --output docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/authenticated-01
```

无秘密命令行参数。本人填写用户名、configuration path、既有SBS/上级TRIGGER号,
然后用getpass输入QB_PASSWORD/QB_COOKIE(可回车表示不可用)。
不在聊天、stdout、证据或提交中传递凭据。终端尚无鉴权结果时保持PENDING,
不拿API文档或匿名对照补齐。

### 5.3 离线安全控制

`spikes/test_ef5_probe.py`是spike自身的离线测试,不进入生产包或业务测试集合。
覆盖凭据及编码脱敏、服务端XML秘密/HTML隐藏域与敏感表格、未脱敏拒绝、
只读白名单、GET trigger拒绝、跨源/非HTTPS拒绝、redirect拒绝。
命令与实测输出见后续`evidence/offline-validation.json`及原始日志。

## 6. 本人输入前的历史停点

匿名探活局部前提成立;Basic Auth成功、configuration解析、SBS字段和TRIGGER
accept语义均未取得实测结论。状态不是EF-5完成,不解除P5Q开工门。
当前缺QB用户名/本人私密输入/既有SBS样本;没有修改设计或扩大写操作授权。

## 7. 本人getpass实测结果与最终停点

通过§5.2的终端入口完成输入后采集结束,`evidence/authenticated-01/run.json`
记录`password_available=true/cookie_available=false`、样本`1069532`、
`trigger_id=null`、10次GET、`post_requests=0`与`redaction_self_check=PASS`。
gnome-terminal的exit0只证明窗口启动,不冒称其为被启动脚本的独立exit采集。
以下HTTP状态为实际响应,不是预期值:

| 路径 | 鉴权 | HTTP | 结果 |
|---|---|---|---|
| /rest/version | anonymous | 401 | 空响应,Basic challenge |
| /rest/version | basic | 500 | AccessDeniedException,client ip: 172.17.2.1 |
| /rest/ids?configuration_path=[REDACTED] | basic | 500 | 同一拒绝;未解析出configuration ID |
| /rest/builds/1069532 | basic | 500 | 同一拒绝,非SBS业务字段 |
| /rest/builds/1069532/status | basic | 500 | 同一拒绝 |
| /rest/builds/1069532/variables | basic | 500 | 同一拒绝 |
| /rest/builds/1069532/steps | basic | 500 | 同一拒绝 |
| /rest/builds/1069532/dependencies | basic | 500 | 同一拒绝 |
| /rest/builds/1069532/request_id | basic | 500 | 同一拒绝 |
| /build/1069532 | anonymous | 302 | Location为signin,未跟随 |

原文关键句:

```text
com.pmease.quickbuild.AccessDeniedException: Sorry, you are not allowed to access the system via RESTful API (client ip: 172.17.2.1)
```

逐个脱敏原始响应和叶字段在`evidence/authenticated-01/`,请求元数据附各响应sha256。
全是错误页/重定向,未取得status全集、SBS_TARGET或arch数据。
不能凭500区别账号或来源IP规则,也不能据此宣称密码正确。
不绕过服务端访问控制,不以另一个随机build替代此样本。

### 7.1 输入安全事件与本地自检

configuration输入命中凭据规则并已遮蔽。初次采集未做发送前URL秘密检查,
该值曾作为GET查询发往QuickBuild,可能进入服务端访问日志。
已在会话向FatTank提示:若该字段误填密码,须更换密码;不复述或恢复该值。
本地落盘前已脱敏且自检PASS,没有把密码/Basic编码/Cookie明文写入证据。
该记录不得当作有效configuration path,恢复时必须重新确认非敏感路径。

本轮脚本后续加固(未再联网重跑,不冒充原始采集版本):

- `Probe.get`发送前检查URL不得含已知凭据;控制断言HTTP调用0次/文件0个。
- getpass凭据提示先于可选配置输入,降低错位输入风险。
- Basic探活非200时结束,不再连续读取配置/build;控制断言仅两次版本GET。
- 状态形态打印前亦脱敏;配置query只接受唯一`configuration_path`键。

§5.3最初8个离线控制保留在`offline-validation.json`与对应日志;
上述加固后10个控制另存`hardened-validation.json`,不覆盖最初记录。

### 7.2 结论与待办

1. EF-5①:当前REST访问前提不成立,需管理员确认账号/来源准入;配置解析独立未完成。
2. EF-5③:样本1069532业务数据未取得,字段与架构假设不能判成立/需改。
3. EF-5④:无对应TRIGGER证据,accept语义不能判定。
4. 真实提交尚未获目标与明确确认,本轮提交次数0;完整请求也未具备可核实输入。

需改之处首先是环境访问前提;若不能开放REST,涉及design.md §1.4 EF-5①与
§4.1 qb-sbs-trigger/qb-result-fetch,只由设计方决定如何改正文。
本批进度停在权限核对,状态BLOCKED_REST_ACCESS,未宣称EF-5/P1完成。

## 8. 提交前验收

原始命令与输出保存于`evidence/hardened-validation.json`与同名日志:

```text
$ .venv/bin/python docs/clang-fix-campaign/spikes/test_ef5_probe.py -v
Ran 10 tests in 0.023s
OK
exit=0
$ .venv/bin/ruff check docs/clang-fix-campaign/spikes/ef5_probe.py docs/clang-fix-campaign/spikes/test_ef5_probe.py
All checks passed!
exit=0
$ .venv/bin/python -m mypy --follow-imports=silent docs/clang-fix-campaign/spikes/ef5_probe.py
Success: no issues found in 1 source file
exit=0
$ .venv/bin/python -m pytest tests/ -q
1410 passed, 1 skipped in 26.65s
exit=0
```

`evidence/evidence-integrity.json`:匿名1次GET+本人输入批次10次GET,
逐响应SHA-256与metadata一致、采集器秘密自检PASS、无明文凭据头,
configuration值已脱敏、POST计数0,exit0。权限拒绝后未再运行网络采集。

```text
$ git diff --stat -- 'tizen-*/scripts/**' 'tests/**' pyproject.toml docs/clang-fix-campaign/design.md
(空输出)
exit=0
$ sha256sum docs/clang-fix-campaign/design.md
6623f9cae95dbc07bdc8a4408808813eb2b9a54057df82c51b8b9d0cdce11b16  docs/clang-fix-campaign/design.md
exit=0
```

生产包/业务测试/设计稿零改动。原有无关改动和历史草稿均未纳入提交。

## 9. 网页只读续测

本轮按FatTank指令转为Cookie网页观察,不再重试REST。不修改§7的历史实测记录。
样本固定1069532;先确认SBS身份,再取状态字段/SBS_TARGET/arch及明确关联的TRIGGER。
找不到父子对应关系时请FatTank提供上级号,不按时间或版本推测。

脚本:`../../spikes/ef5_web_probe.py`;只读取同源`/build/<id>`及页面实际提供的
overview/status/variables/steps/dependencies/changes只读路径。所有query、
Wicket动作链接、REST、其它build号及跨源URL拒绝;不运行JS、不加载子资源,
不提交表单、不跟随redirect。页面上的未访问链接仍逐项记账,不声称已读其字段。
HTTP非200、登录/拒绝页立即结束,不记作业务字段缺失。

Cookie只来自QB_COOKIE或本人终端getpass,未读取磁盘cookie文件;
不输出请求头、不存Set-Cookie,服务端session/CSRF/隐藏值先脱敏再自检落盘。
复用原Probe的发送前凭据拒绝检查;新增URL策略分派不改变旧REST白名单。

私密输入启动命令(不含凭据):

```sh
env -u LD_LIBRARY_PATH -u LD_PRELOAD -u GTK_PATH -u GIO_MODULE_DIR gnome-terminal --wait --title='P1 EF-5 webpage read-only: private Cookie input' --working-directory=/home/linhao/Toolchain/development/LogAnalysisSkill -- /home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python docs/clang-fix-campaign/spikes/ef5_web_probe.py --build-id 1069532 --output docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/web-01
```

### 9.1 本轮离线验收

完整命令、exit、输出摘要在`evidence/web-validation/commands.json`,原文为同目录日志。

```text
$ .venv/bin/python docs/clang-fix-campaign/spikes/test_ef5_web_probe.py -v
Ran 6 tests in 0.083s
OK
exit=0
$ .venv/bin/python docs/clang-fix-campaign/spikes/test_ef5_probe.py -v
Ran 10 tests
OK
exit=0
$ .venv/bin/ruff check docs/clang-fix-campaign/spikes/ef5_web_probe.py docs/clang-fix-campaign/spikes/test_ef5_web_probe.py docs/clang-fix-campaign/spikes/ef5_probe.py docs/clang-fix-campaign/spikes/test_ef5_probe.py
All checks passed!
exit=0
$ .venv/bin/python -m mypy --follow-imports=silent docs/clang-fix-campaign/spikes/ef5_web_probe.py docs/clang-fix-campaign/spikes/ef5_probe.py
Success: no issues found in 2 source files
exit=0
$ .venv/bin/python -m pytest tests/ -q
1457 passed, 1 skipped in 27.17s
exit=0
```

网页控制:只读白名单/动作拒绝、已知Cookie发送前拒绝、隐藏及session脱敏、
Set-Cookie不落盘、登录/拒绝停机、只随本build明示标签链接(不猜上级)。
初次静态检查的E501和未显式导出import已在spike内修正,未改生产包。

### 9.2 人工闸门

真实提交保持NOT_GRANTED。本轮只能整理页面可观察的触发参数,
不打开触发入口、不发送触发请求。Cookie等待期间无网页实测结论,
不能用离线控制或历史权限拒绝页代替SBS业务证据。

### 9.3 本轮停点

QB_COOKIE未设置。getpass终端启动后仍在等待输入,尚未创建`web-01/`;
输出目录的创建位于读取Cookie之后、首个GET之前。已精确定位本次探测进程,
用SIGINT结束等待;`gnome-terminal --wait`实测exit2。没有挂起的输入进程,
没有网页请求或触发操作;不重用上一轮REST密码。
非敏感记录见`evidence/web-input-attempt.json`。

本轮只完成只读网页工具与离线验证,不是网页实测完成。SBS身份、状态字段全集、
SBS_TARGET、arch、父子对应/accept全部PENDING,不能判字段不存在。
恢复时需FatTank本人在§9命令的getpass输入Cookie;不得在聊天、命令行参数或文件中传递。
若网页登录/拒绝则停止记录,如无明确TRIGGER关联则再请FatTank提供上级号。

## 10. 本人到场后的网页重跑(35d4052原脚本)

本轮仅EF-5,不修改P2-P4、生产代码、业务测试或design.md。
`ef5_web_probe.py`及`ef5_probe.py`对35d4052的git diff为空,原字节未改。
Cookie只由可见gnome-terminal中的getpass输入;启动时对该子进程取消QB_COOKIE
环境变量以确保走getpass,不读取任何磁盘cookie文件。

### 10.1 输入等待与实测退出

北京时间2026-10-08 17:35:05首次启动(UTC09:35:05),明确允许等待10分钟。
本轮**未发送SIGINT/TERM,未提前结束等待**;各次均由探测脚本自行exit2。
第一次直接运行,第二次用runpy保留结束提示,均无web-02目录,原因不作推断。
第三、四次用`evidence/web-02-launch.py`调用同一未修改的main,
仅增加固定错误类别/TTY标记的记录,不打印异常原值、不采集Cookie长度或片段。
最后核对时间UTC09:45:13。

诊断两次的非敏感输出一致:

```json
{
  "stdin_isatty": true,
  "secret_recorded": false,
  "error_category": "COOKIE_HEADER_FORMAT",
  "error_type": "ValueError",
  "exit": 2
}
```

原始记录:`evidence/web-02-input-format-rejected.json`(保留前一次)与
`evidence/web-02-launch.json`(最后一次)。对应脚本内固定错误文本:
`QB_COOKIE must be a Cookie header: name=value; name2=value2`。
该校验位于Redactor初始化,早于创建输出目录与首个GET;
两次诊断均为格式拒绝,不推测输入中具体有什么,不把首次两次无诊断退出强归同因。

启动命令与各次退出、脚本SHA、目录未创建证明、提交面检查见
`evidence/web-02-attempts.json`及`evidence/web-02-integrity.json`。
没有捕获终端输入/录屏/剪贴板,没有明文Cookie、Cookie片段或Set-Cookie落盘。

### 10.2 逐页面证据与结论

本轮HTTP请求0,HTTP响应0,成功读取页面0,POST/触发/修改0;
未获取状态、步骤、日志链接、产物列表或trigger入口。**不能判断这些字段不存在**。

| 计划页面 | 请求是否发出 | build状态 | 步骤 | 日志链接 | 产物列表 | trigger入口 |
|---|---|---|---|---|---|---|
| /build/1069532 | 否,本地凭据格式拒绝 | 未读取 | 未读取 | 未读取 | 未读取 | 未读取,未点击 |

没有已读取的标签页,故不伪造标签页级响应或字段列表。
结论:**BLOCKED**;阻塞类别是本地输入格式,不是QuickBuild拒绝。
只读工具仍有GET白名单且禁redirect/JS/表单/触发;本轮无需、也未扩白名单。
恢复需在getpass输入HTTP Cookie头的name=value配对内容,不是裸值/JSON/整条curl命令;
勿在聊天或命令行传递凭据。本轮不对实际输入作重建或自动修正。
