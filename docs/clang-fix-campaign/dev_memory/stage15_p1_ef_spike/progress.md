# Stage15 P1 EF-5 Environment Spike

日期:2026-10-10。状态:**WEB_READ_PARTIAL**(累计结论;最新rbs-form-01为离线解析)。
最新取证:Base工程RBS运行表单,2个form/19个控件/25个按钮,网络请求0,详见§17。
§16的在线续跑7 GET/200与§15停机记录保留;未取得提交响应与新build ID获取方式。
权威:`../../design.md` v1.5.19-FROZEN §1.4 EF-5、§4.1
qb-sbs-trigger/qb-result-fetch。设计稿不改动。

## 1. 计划与安全边界

1. 独立探测Basic Auth轻端点;configuration path解析另行取证。
2. 指定既有SBS build,读取页面与REST字段、SBS_TARGET、架构表示。
3. 同一SBS对应的上级TRIGGER,观察accept事实;不能仅凭一个成功状态
   推断accept为门2通过的必要条件。
4. 准备完整真实提交请求,等待FatTank指定目标并明确确认,未经确认不发出。

凭据仅来自`QB_PASSWORD`/`QB_COOKIE`环境变量或本人终端getpass;
不读磁盘cookie jar、不读既有浏览器凭据、不将秘密放到命令行/日志/Git。
本轮本人另授权新建隔离浏览器并手工登录,仅该临时会话的QuickBuild Cookie
经匿名内存管道交给探测器;不导出storage state、不读取日常浏览器profile。
HTTP只允许白名单只读URL,包括禁用重定向;即使GET也禁止`/rest/trigger`。
以上为前轮授权记录;2026-10-10改用本人导出的Cookie文件,当前边界见§14/§15,
不再运行浏览器转交,不再申请REST权限。§17登记的新P5Q登录裁定取代手工Cookie前提;
本轮只处理已保存HTML,不实现或执行登录。
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
| EF-5③ SBS结果与绑定字段 | WEB_READ_PARTIAL | §11:1069532为SBS/TRIGGER,Successful;变量中BUILD_PKG_LIST含repo@commit,非SBS_TARGET字面 |
| EF-5④ 上级TRIGGER的accept | PARTIAL | §11:该TRIGGER的SR_STATUS=ACCEPTED,Child Build明确列1069540;未读取子页,通过条件仍待核实 |
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

## 11. 隔离浏览器手工登录与内存会话交接

2026-10-08本人改用可见浏览器手工登录的方式,不再粘贴Cookie。
只启动新的非持久Chromium context,不读取本人既有浏览器profile;
使用已安装的Playwright/Chromium,临时文件限`/dev/shm`,关闭后清理。
不录制HAR/trace/storage-state,不读取登录表单内容。
本人登录后回配套终端按回车,最多等待600秒,未提前终止。
Cookie由该context按QuickBuild URL筛选,经匿名stdin管道交给
`ef5_browser_receiver.py`,只在内存组成header与脱敏字典,不用文件/环境变量传递。
用户手工登录所需认证POST与后台探测分开;后者仍是原35d4052的GET-only工具。

### 11.1 实际启动与取证

```sh
env -u LD_LIBRARY_PATH -u LD_PRELOAD -u GTK_PATH -u GIO_MODULE_DIR -u DEBUG -u PWDEBUG -u QB_COOKIE -u QB_PASSWORD TMPDIR=/dev/shm gnome-terminal --wait --title='QuickBuild manual login - press Enter after login (no secrets here)' --working-directory=/home/linhao/Toolchain/development/LogAnalysisSkill -- /home/linhao/.bun/bin/bun docs/clang-fix-campaign/spikes/ef5_browser_login.mjs /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome /home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python /home/linhao/Toolchain/development/LogAnalysisSkill/docs/clang-fix-campaign/spikes/ef5_browser_receiver.py /home/linhao/Toolchain/development/LogAnalysisSkill/docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/web-browser-01
```

启动仅有`Failed to load module "canberra-gtk-module"`告警,浏览器正常显示。
终端wait与子探测器均exit=0(后者见run.json)。
`web-browser-01/run.json`原文摘录:

```json
"builds": {"1069532": "READ_PAGES_COLLECTED"},
"exit_code": 0,
"cookie_stored": false,
"finished_at": "2026-10-08T10:07:34.775015+00:00",
"requests": 3,
"post_requests": 0,
"trigger_authorized": false,
"redaction_self_check": "PASS"
```

requests只计后台业务页面,不冒称包含本人浏览器登录/静态资源请求。
`requests.json`逐条为`/build/1069532`、`/overview`、`/variables`,均GET/200;
页面全文先脱敏后写入,附SHA与带行号的page.json,动作链接一律NOT_FOLLOWED。
实跑时launcher SHA256=`f4b2eaab21b6fc8cfd55ed267ecfd384db5a26f574c1e47127091b4976df7c27`;
实跑后补紧浏览器登录容器的普通页面query拒绝并加12项离线控制,未重新登录或请求。
Python接收器仅修类型注解以通过mypy。后台取证核心文件未改:
`ef5_web_probe.py=60d76e36e6b237053961101c9522469c61dbe1f53eedc2784d00a0b34f35b21c`;
`ef5_probe.py=00c0f3b90d1ea8f6eaa9cd1b84f0bef2e0dbdba39a93c1ff7a4de35f95e63d26`。
`find /dev/shm -maxdepth 1 -name 'ef5-browser-*'`退出0且空输出,临时会话已清理。

### 11.2 结论与停点

**WEB_READ_PARTIAL**。页面证明1069532是SBS/TRIGGER,而不是被假定的子构建。
Summary为Successful、SR_STATUS为ACCEPTED(20260424.154027);
Child Build明确列1069540,架构串standard-armv7l:aarch64:x86_64,结果SUCCESSFUL。
Variables中BUILD_PKG_LIST/BUILD_PKG_LIST_MODIFY含repo@commit,没有SBS_TARGET字面。
Artifacts两个下载链接、Build Log链接、Run the configuration入口均可见且未点击。
Step Status实际链接是`step_status`,未在既有白名单,未读详情;子构建也未访问。
三页逐页字段与证据行号见`../../spikes/ef_report.md`最后一节。
不把READ_PAGES_COLLECTED等同WEB_READ_OK,也不由单一Successful/ACCEPTED样本
断言复验的必要通过条件。缺步骤详情/子页实测/逐架构状态/目标映射与accept判据;
真实触发仍NOT_GRANTED。浏览器已关闭,无持久Cookie,未更改design或P2-P4生产代码。

### 11.3 离线验证

```text
$ env PYTHONPATH=docs/clang-fix-campaign/spikes .venv/bin/python -m unittest discover -s docs/clang-fix-campaign/spikes -p 'test_ef5*.py'
Ran 18 tests in 0.113s
OK
exit=0
$ /home/linhao/.bun/bin/bun docs/clang-fix-campaign/spikes/ef5_browser_login.mjs --policy-self-test
Browser login allowlist: 12 controls PASS; build actions rejected.
exit=0
$ .venv/bin/mypy docs/clang-fix-campaign/spikes/ef5_browser_receiver.py docs/clang-fix-campaign/spikes/test_ef5_browser_receiver.py
Success: no issues found in 2 source files
exit=0
$ .venv/bin/ruff check docs/clang-fix-campaign/spikes/ef5_browser_receiver.py docs/clang-fix-campaign/spikes/test_ef5_browser_receiver.py
All checks passed!
exit=0
$ .venv/bin/python -m pytest -q
1457 passed, 1 skipped in 30.39s
exit=0
```

新增工具初次mypy曾报SimpleCookie不接受类型参数、测试list不变性报错;
分别去掉多余类型参数、改用Sequence[Mapping]形参,无行为变更。
ruff首次仅为import排序,已修复。原有无关工作树改动照旧不处理。

最终复跑同一pytest命令exit=0,完整原文在`evidence/browser-pytest.log`,末行为
`1457 passed, 1 skipped in 30.95s`。提交前用JSON解析requests逐项校验响应hash,
并用SensitiveHTML/PageInventory复核敏感字段,实际输出:

```text
responses=3; SHA256_MATCH=3/3; GET_200=3/3; sensitive_fields=REDACTED_OR_EMPTY; auth_headers_archived=0
probe_exit=0; cookie_stored=false; runtime_redaction_self_check=PASS
```

`git diff 35d4052 -- docs/clang-fix-campaign/spikes/ef5_probe.py docs/clang-fix-campaign/spikes/ef5_web_probe.py 'tizen-*/scripts/**' docs/clang-fix-campaign/design.md`
退出0且空输出,确认只新增隔离登录脚手架与证据/报告,取证核心与生产代码未改。

`git diff --cached --check`对服务器HTML的原有空白/CRLF报exit=2;
保留脱敏响应原字节和已记录hash,不为格式检查改写取证文件。
仅排除三份`*.response.txt`后对其余提交文件的同一检查exit=0、空输出。

## 12. 五路径补测与身份脱敏(2026-10-09)

### 12.1 范围与实跑停点

本轮仅新增本人指定的GET:子构建1069540的根页/overview/variables/step_status,
以及父构建1069532的step_status。1069540不继承其它旧标签白名单;
Wicket动作、/log、REST、POST与触发均拒绝。后台使用固定五路径队列,
`follow_links=False`,不沿其它合法或非法链接扩展请求。
手工登录仍仅允许原有浏览器signin认证;不自动填写或读取登录表单。

启动命令同§11.1,仅输出目录改为`evidence/web-browser-02`。
实际在可见gnome-terminal启动隔离Chromium,10分钟确认窗口未提前终止。
最终`gnome-terminal --wait`实测exit=2,stdout为空;
只有启动时既有`canberra-gtk-module`告警。没有生成web-browser-02目录,
因此**后台业务GET=0、已取得的新页面=0、后台POST=0**。
不能据此认定本人登录失败或QuickBuild拒绝,也不能把未读字段写成不存在。
没有记录登录表单、Cookie或浏览器原始错误;人工认证/资源请求不计入后台统计。
会话已关闭,`find /dev/shm -maxdepth 1 -name 'ef5-browser-*'`退出0、空输出。
证据:`evidence/browser02-launch.json`。后台新取证仍需本人登录并完成终端确认后重跑。

### 12.2 脱敏与历史三页更新

PageRedactor新增结构化规则:Welcome!后显示名、Triggered By表头对应列或
键值行的账号,在写盘前替换为`<USER>`(HTML源码使用`&lt;USER&gt;`)。
不对名字做全局子串替换,保留业务字段和HTML源行号。
归档工具先校验原hash,再同步更新响应、page.json与requests.json的hash;
全部校验通过才写盘。不重新请求历史页面,不改变当时链接的NOT_FOLLOWED决定。

```text
$ .venv/bin/python docs/clang-fix-campaign/spikes/ef5_redact_archive.py --archive docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/web-browser-01 --report docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/browser02-archive-redaction.json
exit=0; network_requests=0; pages=3; user_fields=2/2/1; line_numbers_preserved=true
```

原文JSON与新旧hash完整对照:`evidence/browser02-archive-redaction.json`。
复核命令以requests的hash逐项验响应,以_UserFields验每处均为USER,
并以PageInventory重解析结果逐项比对page.json.visible_text,实际输出:

```text
build-1069532-01.response.txt user_fields=2 all_USER=PASS hash=PASS derived_json=PASS
build-1069532-02.response.txt user_fields=2 all_USER=PASS hash=PASS derived_json=PASS
build-1069532-03.response.txt user_fields=1 all_USER=PASS hash=PASS derived_json=PASS
new_probe_output_exists= False
exit=0
```

这是当前树的重脱敏,不是历史重写;43dbca0中的旧内容仍在Git历史中。

### 12.3 验证

```text
$ env PYTHONPATH=docs/clang-fix-campaign/spikes .venv/bin/python -m unittest discover -s docs/clang-fix-campaign/spikes -p 'test_ef5*.py'
Ran 24 tests in 0.121s
OK
exit=0
$ /home/linhao/.bun/bin/bun docs/clang-fix-campaign/spikes/ef5_browser_login.mjs --policy-self-test
Browser login allowlist: 20 controls PASS; build actions rejected.
exit=0
$ .venv/bin/mypy docs/clang-fix-campaign/spikes/ef5_web_probe.py docs/clang-fix-campaign/spikes/ef5_browser_receiver.py docs/clang-fix-campaign/spikes/ef5_redact_archive.py
Success: no issues found in 3 source files
exit=0
$ .venv/bin/ruff check docs/clang-fix-campaign/spikes/ef5_web_probe.py docs/clang-fix-campaign/spikes/ef5_browser_receiver.py docs/clang-fix-campaign/spikes/ef5_redact_archive.py docs/clang-fix-campaign/spikes/test_ef5_redact_archive.py docs/clang-fix-campaign/spikes/test_ef5_web_probe.py
All checks passed!
exit=0
$ .venv/bin/python -m py_compile docs/clang-fix-campaign/spikes/ef5_web_probe.py docs/clang-fix-campaign/spikes/ef5_browser_receiver.py docs/clang-fix-campaign/spikes/ef5_redact_archive.py
(空输出)
exit=0
$ .venv/bin/python -m pytest -q
1457 passed, 1 skipped in 33.87s
exit=0
```

全仓原文:`evidence/browser02-pytest.log`。离线控制不是环境实测。
工具自测初次发现HTMLParser已有offset属性与辅助方法重名、单测过度限定
可见文本分块,已修正;归档第一次遇到空href锚与历史links过滤不一致,
在写入前拒绝,随后按原提取器的非空href规则对账并补控制;ruff仅修格式。
均未涉及生产行为、白名单放宽或设计变更。

### 12.4 待人工裁定

| 议题 | 状态 | 裁定方 | 本批边界 |
|---|---|---|---|
| 复验通过只看Successful,还是必须ACCEPTED | 待人工裁定 | FatTank | 分别记录Status与SR_STATUS,不由样本推断通过规则 |
| SBS_TARGET与BUILD_PKG_LIST是否等价 | 待人工裁定 | FatTank | 只记录变量原名与回显,不代换或宣称等价 |

结论累计仍WEB_READ_PARTIAL,依据仅是§11历史三页;
本轮五页未取得,子构建自身状态、逐架构状态、步骤详情、关联变量仍待实测。
不重试REST、不读触发表单、不修改design.md或P2-P4代码,不解除P5Q前置闸门。

## 13. 本人到场后的五路径重跑(2026-10-09)

### 13.1 启动与实测结果

基于`f507201`,只在启动器的浏览器启动之前增加中文提示:
“先在浏览器里登录，登录后回到本终端按回车。”
另提示等待上限10分钟,不要在终端粘贴Cookie或密码。
后台固定五路径、`follow_links=False`、600000ms等待、凭据内存管道与
写盘前`<USER>`脱敏逻辑均未改动。实际启动命令:

```bash
env -u LD_LIBRARY_PATH -u LD_PRELOAD -u GTK_PATH -u GIO_MODULE_DIR -u DEBUG -u PWDEBUG -u QB_COOKIE -u QB_PASSWORD TMPDIR=/dev/shm gnome-terminal --wait --title='QuickBuild 登录后回到此终端按回车（勿粘贴凭据）' --working-directory=/home/linhao/Toolchain/development/LogAnalysisSkill -- /home/linhao/.bun/bin/bun docs/clang-fix-campaign/spikes/ef5_browser_login.mjs /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome /home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python /home/linhao/Toolchain/development/LogAnalysisSkill/docs/clang-fix-campaign/spikes/ef5_browser_receiver.py /home/linhao/Toolchain/development/LogAnalysisSkill/docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/web-browser-02
```

代理没有发送终端回车、没有提前结束等待。可见进程在实测elapsed=08:45时
仍运行,之后自行结束,`gnome-terminal --wait`的实际exit=2。
启动输出仅有两条`Failed to load module "canberra-gtk-module"`;
结束时工具收到空输出。没有浏览器原始错误或凭据输出。
终端窗口内部stdout未另行录制;不能把通用exit=2解释成已确定的登录失败原因。

结束后`test -f .../web-browser-02/run.json` exit=1,无运行结果;
该目录在取证期间未产生。**后台GET=0、响应=0、POST=0、构建操作=0**,
未取得登录拒绝页或服务端错误页,不能判为QuickBuild拒绝访问。
`find /dev/shm -maxdepth 1 -name 'ef5-browser-*' -print` exit=0、空输出,
临时会话已清理。随后仅在目标目录写入本次启动记录
`evidence/web-browser-02/launch.json`,不是伪造`run.json`或页面响应。
记录中包括启动器及取证脚本SHA256、预定五路径、实际exit与统计边界。

本轮结论:**BLOCKED(LOCAL_HANDOFF_NOT_COMPLETED)**。
累计历史结论仍为WEB_READ_PARTIAL,来源是§11已经成功的三页,与本轮失败分列。
仍缺子构建自身Status/SR_STATUS、逐架构独立状态、父子步骤与逐步状态、
子页关联字段、SBS_TARGET或候选目标变量实测;产物文件清单与日志内容未读取。
§12.4两项业务规则继续待FatTank裁定,不由本轮推断。

### 13.2 本轮离线验证与范围

```text
$ /home/linhao/.bun/bin/bun docs/clang-fix-campaign/spikes/ef5_browser_login.mjs --policy-self-test
Browser login allowlist: 20 controls PASS; build actions rejected.
exit=0
$ env PYTHONPATH=docs/clang-fix-campaign/spikes .venv/bin/python -m unittest discover -s docs/clang-fix-campaign/spikes -p 'test_ef5*.py'
....................page: HTTP 200; html; evidence=page.response.txt
....
----------------------------------------------------------------------
Ran 24 tests in 0.116s

OK
exit=0
$ .venv/bin/mypy docs/clang-fix-campaign/spikes/ef5_web_probe.py docs/clang-fix-campaign/spikes/ef5_browser_receiver.py docs/clang-fix-campaign/spikes/ef5_redact_archive.py
Success: no issues found in 3 source files
exit=0
$ .venv/bin/ruff check docs/clang-fix-campaign/spikes/ef5_web_probe.py docs/clang-fix-campaign/spikes/ef5_browser_receiver.py docs/clang-fix-campaign/spikes/ef5_redact_archive.py docs/clang-fix-campaign/spikes/test_ef5_redact_archive.py docs/clang-fix-campaign/spikes/test_ef5_web_probe.py
All checks passed!
exit=0
$ bash -o pipefail -c '.venv/bin/python -m pytest -q | tee docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/browser02-rerun-pytest.log'
1457 passed, 1 skipped in 27.10s
exit=0
$ git diff --exit-code -- docs/clang-fix-campaign/design.md 'tizen-*/scripts/**'
(空输出)
exit=0
```

全仓原始输出:`evidence/browser02-rerun-pytest.log`。单测中的HTTP 200来自
人工fixture,不是线上请求。本轮不重试REST、不读取触发表单、不访问/log,
不修改design.md或P2-P4代码。原有无关工作树改动照旧不处理。

## 14. FatTank 2026-10-10裁定

1. QuickBuild通过判据已裁定:子构建Status=Successful即通过,
   不要求SR_STATUS=ACCEPTED。`qb_pass_requires_accept`默认false,
   campaign启动时冻结入库,以后修改配置只影响新campaign。
   此行为由P5Q设计稿落实,本轮只登记,不改生产代码或design.md。
2. SBS_TARGET是设计内部名称。QuickBuild实际填写BUILD_PKG_LIST /
   BUILD_PKG_LIST_MODIFY / 其它变量,待本次取证后再定,不得擅自认定等价。
3. 不申请REST权限。P5Q触发与结果读取均改走网页Cookie,
   REST/Basic Auth方案由P5Q设计稿替换。本轮不触发、不读取触发表单,
   不修改design.md,不将未来自动触发裁定当成本轮写操作授权。

以上取代§12.4/§13中相关待决状态;历史实测记录不改写。
stage19 §21同步本裁定;P5已CLOSED,与本轮EF-5取证状态分开。

## 15. Cookie文件只读续跑(2026-10-10)

计划:新增--cookie-file(默认/tmp/quickbuild_cookies.json),复用shared的
load_cookie_jar,凭据仅内存使用,不复制/输出/落入证据;记录权限位但不按权限拒绝。
不再使用浏览器转交。发送前凭据拒绝检查、PageRedactor与USER脱敏继续有效。

请求顺序固定为1069540根页、overview、variables、step_status,
然后1069532/step_status。仅额外允许从既有1069532归档页找到的普通配置页链接,
以及配置页实际提供的普通变量页链接,各一次;不猜路径。
禁止POST、Wicket动作、/log、REST、触发/接受入口、redirect跟随。
每个失败仅记录固定类别、阶段与HTTP码,不保存异常原文或错误响应正文。

离线控制通过后实跑一次,证据目录evidence/web-cookie-01/;
读取不到的事实记未读到,不借父页摘要填补子页。结果及验收随后追加。

### 15.1 实跑与停点

命令与输出原文:

```text
$ .venv/bin/python docs/clang-fix-campaign/spikes/ef5_web_probe.py --cookie-file /tmp/quickbuild_cookies.json --output docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/web-cookie-01
{"conclusion": "BLOCKED", "diagnostic": {"stage": "write", "page_index": 1, "error_category": "WRITE_FAILED", "http_status": 200}, "requests": 1, "http_statuses": [200], "post_requests": 0}
exit=4
```

Cookie权限0600,只读且仅内存使用;未使用QB_COOKIE/getpass/浏览器转交。
本轮仅第一GET,没有重试、POST、REST、/log、Wicket动作、redirect跟随或触发。
原run.json/requests.json保留停机事实。实跑脚本SHA:
b602aa767e14c56e09fd8911724a403431666c0ea66b048b70be68b67327fb88。

根因是本地写后校验用read_text隐式把CRLF转换为LF,并非登录失效:
首响应写前已经PageRedactor脱敏,实测384个CRLF;回读规范化后与待写文本不等。
修复仅将回读改为read_bytes().decode("utf-8"),不放宽字节相等或脱敏检查,
新增CRLF回归控制。没有以修复后的工具重跑网络,已询问是否允许继续余下页面,
在获准前保持停止。

首响应SHA256:
69c8b2f269fbff08f3fa3be5b43d390660e96adabb2d5231da416288154f06cb。
离线自检PASS、身份片段2处均USER,无额外网络:
`evidence/web-cookie-01/offline-integrity.json`;
`01.offline-page.json`从已经脱敏的01.response.txt派生,未覆盖原证据。

| 页面 | HTTP/请求 | 事实/源行 |
|---|---|---|
| 1069540根页 | 200/1 GET | 01.response.txt:831 ID、:832 Successful;SR_STATUS未读到;:841/:844依赖计数0,无明确1069532关联字段 |
| 1069540/overview | 未请求 | 未读到 |
| 1069540/variables | 未请求 | 含@的变量原名/值、目标映射与父子一致性未读到 |
| 1069540/step_status | 未请求 | 步骤与逐架构独立状态未读到;首页:6组合架构标题不能替代 |
| 1069532/step_status | 未请求 | 步骤与每步状态未读到 |
| 配置页及变量页 | 未请求 | 旧1069532归档:6/:679完整路径SBS/TRIGGER,:705普通../overview/1921链接;本轮NOT_FOLLOWED,未读prompt/默认值 |

本轮结论BLOCKED(write);网页累计仍PARTIAL。完整五项事实、设计影响与源行号
见[ef_report](../../spikes/ef_report.md#cookie文件只读取证2026-10-10)。

### 15.2 验证

命令在仓库根执行,输出日志位于evidence/web-cookie-validation/:

```text
$ env PYTHONPATH=docs/clang-fix-campaign/spikes .venv/bin/python -m unittest discover -s docs/clang-fix-campaign/spikes -p 'test_ef5*.py' -v
Ran 41 tests in 0.328s
OK
exit=0 (offline-crlf.log)
$ .venv/bin/python -m pytest -q
1937 passed, 1 skipped in 59.82s
exit=0 (pytest.log)
$ .venv/bin/mypy
Success: no issues found in 110 source files
exit=0 (mypy.log)
$ .venv/bin/mypy --follow-imports=silent docs/clang-fix-campaign/spikes/ef5_web_probe.py
Success: no issues found in 1 source file
exit=0 (spike-mypy.log)
```

全树ruff在干净工作树/tmp/ef5-cookie-1f0ca30(HEAD=1f0ca30)复制本轮两脚本后执行,
不将主树既有无关未跟踪草稿当成本次代码:

```text
$ /home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/ruff check .
All checks passed!
exit=0 (ruff-final.log)
```

初次静态检查仅import排序/长行与局部path变量重用的类型问题,均在spike内修复。
CRLF控制首次新增时长行E501见ruff.log,修正后ruff-final.log通过。
生产回归集合不变;新增17项spike控制单列(既有24项),不混称为生产新增用例。
COOKIE_EXPIRED停后续、越界/动作零网络、配置NOT_FOLLOWED、固定阶段诊断、
Cookie/服务端会话/隐藏值不出现在stdout或证据、USER脱敏、CRLF逐字节控制均通过。
本轮不改生产源码、tests/、design.md或冻结稿;原有无关工作树改动不处理。

提交前对本轮18个文件用内存Cookie值做扫描,实际输出:
`precommit_secret_scan=PASS; files=18; response_hash_unchanged=PASS; network_requests=0`。
源响应保留服务器空白和CRLF,git diff --check对其CSS缩进报space-before-tab;
只排除01.response.txt后对其余暂存文件检查exit0,不为格式检查改写取证文件。

## 16. Cookie文件第二次只读续跑(2026-10-10)

### 16.1 授权、计划与执行

开工已复核§14裁定与web-cookie-01原始停机记录,git pull --ff-only输出
Already up to date。FatTank批准本轮重新按序读取6个构建页面,
新增的html_report只记iframe与外站URL形态,不跟随。
配置页固定为归档证实的/overview/1921,另只可跟随该页实际存在的普通Variables链接。
工具仍用shared load_cookie_jar,不浏览器交接、不输出Cookie。

实现只改spikes下探测器与离线测试:扩充cookie模式顺序、记录iframe的NOT_FOLLOWED、
拒绝归档中与本轮批准ID不同的配置页。原浏览器工具白名单未扩展。
先跑离线控制43项全绿,随后仅运行一次实际命令:

```text
$ .venv/bin/python docs/clang-fix-campaign/spikes/ef5_web_probe.py --cookie-file /tmp/quickbuild_cookies.json --output docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/web-cookie-02
{"conclusion": "WEB_READ_PARTIAL", "diagnostic": null, "requests": 7, "http_statuses": [200, 200, 200, 200, 200, 200, 200], "post_requests": 0}
exit=0
```

Cookie文件权限0600;无重试、POST、重定向跟随、REST、/log、Wicket动作或真实触发。
全部响应先脱敏后落盘,原始字节回读相等,run.json redaction_self_check=PASS。
配置页未含普通Variables链接,NOT_FOLLOWED/NO_LITERAL_LINK,没有猜URL。
web-cookie-01与web-browser-01原证据保持零diff。

### 16.2 逐页事实、结论与挂账

以下源文件均在[evidence/web-cookie-02](evidence/web-cookie-02/),
每页SHA与GET记录见requests.json,诊断见run.json。字段的完整步骤表、变量名清单
见[ef_report最新节](../../spikes/ef_report.md#cookie文件第二次只读取证2026-10-10)。

| 页面 | 请求/HTTP | 实际字段/源行 |
|---|---|---|
| 1069540根页 | GET/200 | 01.response.txt:831 ID/:832 Successful;未读到SR_STATUS |
| 1069540/overview | GET/200 | 02.response.txt:831 ID/:832 Successful |
| 1069540/variables | GET/200 | 03.response.txt:804,45个变量;TRIGGER_ID=1069532、BUILD_PKG_LIST目标值、组合架构 |
| 1069540/step_status | GET/200 | 04.response.txt:816起21个步骤/容器节点,逐项successful或skipped |
| 1069540/html_report | GET/200 | 05.response.txt:805为/download/1069540/html/HTML REPORT/index.html iframe,NOT_FOLLOWED |
| 1069532/step_status | GET/200 | 06.response.txt:831起19个步骤/容器节点;:1189明确Triggered build链接1069540 |
| /overview/1921 | GET/200 | 07.response.txt:6配置路径;:895/:905/:926为父构建1069532及ACCEPTED时间 |
| 配置变量页 | 未请求 | 无普通Variables链接;NOT_FOLLOWED,没有猜路径 |

五项事实核对:

1. 1069540 Status=Successful(01.response.txt:832、02.response.txt:832),
   子页SR_STATUS未读到。TRIGGER_ID=1069532(03.response.txt:804)是明确子页关联,
   QB_TRIGGER_ID=1069540为自身;子页未读到父构建直接链接。
   父步骤页06.response.txt:1189另有Triggered build指向1069540,不是用父摘要补子状态。
2. 三个架构名只出现在组合字符串(03.response.txt:804、04.response.txt:726、
   05.response.txt:731);EACH_GBS_BUILD_STATUS为空。三个架构各自独立状态均未读到。
   iframe不加载,外站download.tizen.org等一律无请求。
3. 全部步骤已逐项提取:子21项、父19项(均包含master/容器节点),完整名称与状态
   源行对保存在facts.json及报告表;重复Update_Trigger_Description保留,skipped不冒充通过。
4. 子页唯一含@值的变量为BUILD_PKG_LIST:
   `platform/upstream/python3@7cbaf2d74f3428e706c6cae8b3b06b843d140379`
   (03.response.txt:804),与web-browser-01/build-1069532-03.response.txt:819同名变量
   逐字相等。子页BUILD_PKG_LIST_MODIFY与SBS_TARGET未读到;
   父归档确有MODIFY且值相同,但不是同名父子比较或业务等价裁定。
   全部45个变量名与脱敏值见facts.json/报告,不取父值填子空值。
5. 配置实际完整路径为root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/SBS/TRIGGER
   (07.response.txt:6);prompt变量定义/名称/默认值和运行前弹窗说明均未读到。
   :699的Run the configuration为Wicket按钮,没有点击或请求;
   06.response.txt:745的Ready to Accept亦只记录。

离线结构解析由HTMLParser读取已脱敏的表格/步骤span,不做网络;
facts.json记录源SHA、45个变量原序、含@的精确比对和21/19个步骤名称/状态/行号。
校验输出原文:

```text
credential_scan=PASS; original_hashes=PASS; identity_spans= 19
child_variable_count= 45
exact_equal=true (BUILD_PKG_LIST)
```

19处身份片段包含本轮7页及用于比对的3页父归档,均为USER;Cookie值仅内存扫描。
原始脱敏响应不规范化空白或换行,保留服务器行号。

本次结论WEB_READ_PARTIAL,无失败阶段。仍挂账:各架构独立状态、配置prompt及默认值、
QuickBuild实际触发变量的选择(待FatTank裁定)。子SR_STATUS本轮未读到,
但按§14裁定不是通过的必要条件。真实触发继续未授权。
不宣告EF-5 CLOSED或P5Q开工门通过;design.md、P2-P5代码与冻结稿不改。

### 16.3 验收

日志目录[evidence/web-cookie-02-validation](evidence/web-cookie-02-validation/)。
命令及实际输出:

```text
$ env PYTHONPATH=docs/clang-fix-campaign/spikes .venv/bin/python -m unittest discover -s docs/clang-fix-campaign/spikes -p 'test_ef5*.py' -v
Ran 43 tests in 0.349s
OK
exit=0 (offline.log; 上轮41,本轮新增2项)
$ .venv/bin/python -m pytest -q
1937 passed, 1 skipped in 57.41s
exit=0 (pytest.log)
$ .venv/bin/mypy
Success: no issues found in 110 source files
exit=0 (mypy.log)
$ .venv/bin/mypy --follow-imports=silent docs/clang-fix-campaign/spikes/ef5_web_probe.py
Success: no issues found in 1 source file
exit=0 (spike-mypy.log)
```

全树ruff在干净工作树/tmp/ef5-cookie-02-42c6d27(HEAD=42c6d27)复制本轮两个
spike文件后执行,不纳入主树无关的未跟踪草稿:

```text
$ /home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/ruff check .
All checks passed!
exit=0 (ruff.log)
```

新增两个控制:精确六路径顺序及iframe/外站/动作链接零跟随;
普通但不属于批准ID的配置页NOT_FOLLOWED。既有登录页立即停、越界零网络、
诊断无原始异常/凭据、Cookie与USER脱敏、CRLF原字节自检控制全部保留通过。
全仓生产用例集合未变化;spike unittest独立计数,不混入1937。

## 17. RBS运行表单离线解析与新裁定(2026-10-10)

### 17.1 FatTank裁定与执行边界

开工复核§14及之后记录。本轮输入先前不存在时已停止;FatTank通知文件放好后,
确认`/tmp/qb_rbs_trigger_form.html`存在并继续。当前分支clang-fix-campaign,
实现前HEAD=179ce3e;不处理.gitignore、docs四文件删除及历史草稿等无关既有改动。

FatTank 2026-10-10新裁定逐项登记,同步stage19 §21移交表:

1. QB复验用RBS/TRIGGER,不是SBS/TRIGGER;按包所属工程为Tizen-Base-Toolchain与
   Tizen-Unified-Toolchain分别设置配置项,不凭Base样本推断Unified配置ID/URL。
2. 目标变量为BUILD_PKG_LIST,显示名Build Package List,格式git_path@commit_id,
   一行一个。这是业务裁定,不是由动态HTML索引猜变量名,不宣称MODIFY等价。
3. 合入正式快照须有人Accept;工具永远不点Accept/Ready to Accept,
   `ILinkListener-content-buildHead-promote`列入永久禁止名单。
   子构建Successful即通过与人工合入不是同一门槛,§14的默认false裁定继续有效。
4. Run先进入Specify Build Options(/wicket/page?NN),最终提交才开跑,
   依据FatTank截图确认;本轮不执行动作来验证此流程。
5. 自动触发时工具显式填写每个字段,不依赖表单默认值;下表默认值只作为观察。
6. sandbox git push不会自动触发QB,仅工具显式提交RBS表单发起构建。
   来源是FatTank对团队quickbuild-sandbox-branch代码的说明,本轮未另行复核该仓库。
   P12首次真实推送后仍须观察有无自发QB构建,挂账待实测。
7. P5Q改为在FatTank终端提示输入账号密码,工具登录并仅内存保存会话,不落盘,
   不再要求手抄浏览器Cookie;P5Q设计稿落实。本轮不实现登录、不改design.md。

只新增spikes下离线解析器及测试,没有浏览器、HTTP或外部JS执行。
原HTML只在内存读取、先脱敏再归档,不复制原文件、不删除、不改变原字节。
既有PageRedactor/USER规则加hidden value定点遮蔽及session/token/csrf遮蔽;
不把隐藏业务值全局替换而破坏其它可见选项。短显示名用词边界避免误改JS标识符。

### 17.2 实跑与脱敏证据

唯一实际解析命令(不是网络探测):

```text
$ .venv/bin/python docs/clang-fix-campaign/spikes/ef5_rbs_form.py --input /tmp/qb_rbs_trigger_form.html --output docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/rbs-form-01
{"network_requests": 0, "forms": 2, "redaction_self_check": "PASS", "redacted_sha256": "66dad8500ab37c8be9ce981ef61048aea0a4fef2378b25666288b0a7147bad58", "original_unchanged": true}
exit=0
```

证据:[form.redacted.html](evidence/rbs-form-01/form.redacted.html)、
[form.json](evidence/rbs-form-01/form.json)。CLI安装socket审计拒绝钩子,
不执行HTML内任何脚本,GET=0/POST=0/HTTP状态码不适用。写后read_bytes与待写字节比较,
再次脱敏自检及原文件未变检查均通过;行号保留。

内存复核实测输出(验证方法另见rbs-form-01-validation/README.md):

```text
archive_byte_equal=PASS; redacted_sha256=66dad8500ab37c8be9ce981ef61048aea0a4fef2378b25666288b0a7147bad58
hidden_inputs=4; hidden_values_masked=2; hidden_without_value=2
credential_and_identity_scan=PASS; checked_files=9; original_unchanged=PASS
network_requests=0; forms_submitted=0; external_scripts_loaded=0; javascript_executed=false
forms=2; controls=19; buttons=25
```

9个扫描文件为本轮HTML/JSON、5份验收日志、报告与stage19进度(当时已生成);
原始值仅内存比对,不写入命令/日志。JSESSIONID_8810值与登录显示名均未落档。
两个没有value属性的辅助hidden保留缺省事实,其余value均为REDACTED。

### 17.3 字段、联动与按钮

以下源行均为`evidence/rbs-form-01/form.redacted.html`。
:6标题路径为root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER;
:718标题Specify Build Options。PROJECT_NAME在:729/:735只读显示Tizen-Base-Toolchain。
搜索form(:615)method=post/action=page?50-2.IFormSubmitListener-quicksearch;
运行form(:720)method=post/action=page?50-2.IFormSubmitListener-form。
这只是HTML属性,并非已发POST;两条均标记为Wicket动作URL。

`P(n)`只用于缩短下表,展开为`editor:content:basicProperties:n:property:editor:editor`;
form.json保留完整name。必填“未见”表示无HTML required/红星,不是服务端允许为空的断言。

| 标签 | HTML name | 类型 | 必填/默认 | 联动/源行 |
|---|---|---|---|---|
| PROJECT_NAME | 无 | 只读 | 未见/Tizen-Base-Toolchain | 无;:729/:735 |
| BUILD_TYPE | P(1):wrapper:select | select | 星号/0 Full;全部0 Full、1 Partial | onchange;:759 |
| REPO_TYPE | P(2):wrapper:select | select | 星号/0 ALL,唯一选项 | onchange;:785 |
| BUILD_REFERENCE | P(3):wrapper:select | select | 星号/1 Ref. Snapshot;全部0 Live、1 Ref. Snapshot、2 Snapshot Number | onchange;:810 |
| SNAPSHOT_NUM | P(4):wrapper:select | select | 星号/0 tizen-base-toolchain_20260924.094908,唯一选项 | onchange;:837 |
| PROJECT_BRANCH | P(5):wrapper:select | select | 星号/0 tizen_base,唯一选项 | onchange;:862 |
| Immediate Stop With Error | P(6):checkbox | checkbox | 未见/checked;无value属性 | onchange;:885 |
| CHILD_CONFIGURATIONS | P(7):palette:recorder/choices/selection | hidden+双列表 | 未见/hidden遮蔽;Available空,Selected一项standard-armv7l:aarch64:x86_64 | recorder onchange;:907/:921/:936/:937 |
| Build Package List | P(8):wrapper:input | textarea | 未见/空 | onchange;:964 |
| Add Package List | P(9):wrapper:input | textarea | 未见/空 | onchange;:987 |
| Remove Package List | P(10):wrapper:input | textarea | 未见/空 | onchange;:1010 |
| TARGET_IMAGE | P(11):palette:recorder/choices/selection | hidden+双列表 | 未见/hidden遮蔽;两列表均空 | recorder onchange;:1033/:1047/:1062 |
| BUILD NOTES | P(12):wrapper:input | textarea | 未见/空 | onchange;:1089 |
| 运行辅助hidden(无标签) | idd3d_hf_0 | hidden | 未见/无value属性 | 无;:720 |
| 搜索辅助hidden(无标签) | idd3b_hf_0 | hidden | 未见/无value属性 | 无;:615 |
| 搜索输入(无标签) | input | text | 未见/空 | 无字段onchange;:620 |

19个实际控件=搜索2+运行17,另有PROJECT_NAME只读项;没有radio。
12个业务项均挂onchange/wicketAjaxPost,URL为IBehaviorListener.0-form-editor-content-...
形态。只有回调注册证据,**没有BUILD_REFERENCE刷新SNAPSHOT_NUM的响应证据**,
全部服务端刷新目标如实记NOT_OBSERVED_IN_SAVED_HTML。

CHILD_CONFIGURATIONS记录字段为P(7):palette:recorder(:907),两个可见select在
:918/:933被excludeFromAjaxSerialization排除,Palette调用第三参是recorder id(:925-928)。
内存验证当前hidden为单个hex且与:937可见option.value相同,解码等于显示文本;
hidden原值不另存。可见option.value及全部选项在JSON中保留。
只取得单项形态,多项分隔/拼接规则未知,外部palette.js(:108)没有加载。
未执行正常POST,不据Ajax排除断言select绝不会进入普通POST。

| 按钮 | name/value | 动作/源行 |
|---|---|---|
| Ok | 均未见 | submit;closest(form).submit(),无onclick字面URL;:1109,所属form action:720 |
| Cancel | 均未见 | a;page?50-2.ILinkListener-form-cancel;:1110 |
| CHILD_CONFIGURATIONS四个无文字按钮 | 均未见 | Palette.add/remove/moveUp/moveDown,无URL;:925/:926/:927/:928 |
| TARGET_IMAGE四个无文字按钮 | 均未见 | 同上,不同recorder;:1051/:1052/:1053/:1054 |
| 搜索两个无文字按钮 | 均未见 | button/submit,无onclick URL;:617/:621,form action:615 |
| 复制配置图标(文字空) | 均未见 | title=Copy this configuration to be under specified configuration;无内联URL;:679 |
| 导航菜单12个button | 均未见 | TIZEN/Tizen/Tizen-10.1/10.0/9.0/8.0/7.0/6.5/6.0/5.5/5.0/4.0;:487/:491/:508/:513/:518/:523/:528/:535/:540/:545/:550/:555 |

25个按钮/按钮式链接全部见form.json;不把图标CSS类当显示文本,不推断外部JS行为。
**仍未取得：提交后的响应形态、新构建号如何获得。**
两项均待后续一次FatTank明确批准的真实提交。本轮不请求、不提交,累计仍WEB_READ_PARTIAL。
另挂账:Unified表单、逐架构独立状态、Ajax刷新目标、多项palette编码,P12推送观察。
不再把已裁定的BUILD_PKG_LIST当作业务待决项,不把默认观察值变成参数裁决。

### 17.4 验收与交付边界

日志:[rbs-form-01-validation](evidence/rbs-form-01-validation/)。实际输出:

```text
$ env PYTHONPATH=docs/clang-fix-campaign/spikes .venv/bin/python -m unittest discover -s docs/clang-fix-campaign/spikes -p 'test_ef5*.py' -v
Ran 52 tests in 0.457s
OK
exit=0 (offline.log; 既有43+新增9)
$ .venv/bin/python -m pytest -q
1937 passed, 1 skipped in 76.69s (0:01:16)
exit=0 (pytest.log)
$ .venv/bin/mypy
Success: no issues found in 110 source files
exit=0 (mypy.log)
$ .venv/bin/mypy --follow-imports=silent docs/clang-fix-campaign/spikes/ef5_rbs_form.py
Success: no issues found in 1 source file
exit=0 (spike-mypy.log)
```

全树ruff在/tmp/ef5-rbs-form-179ce3e干净工作树(HEAD=179ce3e),复制本轮两个新增
spike文件后执行,避免把主树无关草稿纳入本次检查:

```text
$ /home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/ruff check .
All checks passed!
exit=0 (ruff.log)
```

新增控制覆盖hidden/identity/session脱敏、短身份名不误改动作名、未引号会话URL、
表单字段/选项/红星、双列表、AJAX/按钮只解析、原字节/原文件不变、拒绝覆盖、
源行号与fail-closed诊断/网络拒绝。生产用例未新增,1937/1不混计spike控制。
本轮只提交spikes、stage15证据/进度、stage19移交与INDEX;design.md、P2-P5代码、
测试和冻结稿不改。遗留工作树改动及历史草稿不入库。

最终暂存扫描实际输出:`staged_secret_and_identity_scan=PASS; files=14`;
`scope=docs_spikes_and_evidence_only; staged_bytes_equal_worktree=PASS`。
全量`git diff --cached --check`因保存HTML的原始CRLF/尾部空白exit2;
仅排除form.redacted.html后exit0。保留取证原空白,不为格式检查改写HTML。
`git diff --cached --numstat -- 'tizen-*' tests docs/clang-fix-campaign/design.md '*FROZEN*'`
空输出、exit0,交付范围符合要求。
