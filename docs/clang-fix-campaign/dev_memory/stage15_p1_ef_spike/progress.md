# Stage15 P1 EF-5 Environment Spike

日期:2026-10-08。状态:**BLOCKED_REST_ACCESS**。
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
