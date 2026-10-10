# P1 EF-5 Environment Report

日期:2026-10-10。累计结论:**WEB_READ_PARTIAL**。本轮为RBS/TRIGGER本地HTML离线解析,网络请求0;Base运行表单已取得,提交响应/新build ID获取方式仍未取得。历史SBS样本记录保留,最新事实与FatTank裁定见文末。
权威:`../design.md` v1.5.19-FROZEN §1.4 EF-5与§4.1。
本报告不修改设计,不宣告EF-5关闭或P5Q开工门通过。
进度与命令:[stage15 progress](../dev_memory/stage15_p1_ef_spike/progress.md)。

## ① Basic Auth轻端点与独立configuration解析

### 观察到的事实

仓库根执行:

```sh
.venv/bin/python docs/clang-fix-campaign/spikes/ef5_probe.py --anonymous-only --output docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/evidence/anonymous-01
```

原始控制台输出:

```text
READ-ONLY: no build submission, trigger, cancellation or state mutation.
version-anonymous: HTTP 401; empty; evidence=version-anonymous.response.txt
Evidence credential self-check: PASS. POST/trigger requests: 0.
exit=0
```

GET `https://quickbuild.tizen.org/rest/version`,未发送Authorization或Cookie。
响应HTTP 401,空body,`WWW-Authenticate: Basic realm="QuickBuild"`,
`Content-Type: text/plain; charset=utf-8`。
脱敏原始响应:
[version-anonymous.response.txt](../dev_memory/stage15_p1_ef_spike/evidence/anonymous-01/version-anonymous.response.txt);
响应元数据:[requests.json](../dev_memory/stage15_p1_ef_spike/evidence/anonymous-01/requests.json)。
空body的SHA-256为`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。

### 对设计假设的影响

随后FatTank在本机终端通过getpass提供密码,未提供Cookie。
同一`/rest/version`携带Basic Auth后的实测HTTP状态是500,不是200;
正文为HTML错误页,经XML解析时root为`html`,**不是版本数据**。原文关键句:

```text
com.pmease.quickbuild.AccessDeniedException: Sorry, you are not allowed to access the system via RESTful API (client ip: 172.17.2.1)
```

脱敏原始响应:
[version-basic.response.txt](../dev_memory/stage15_p1_ef_spike/evidence/authenticated-01/version-basic.response.txt);
逐请求记录:[requests.json](../dev_memory/stage15_p1_ef_spike/evidence/authenticated-01/requests.json)。
独立configuration解析请求`/rest/ids?configuration_path=[REDACTED]`也返回500和同一
AccessDeniedException,没有得到configuration ID。
该configuration输入命中敏感值脱敏规则,不能作为一个已核实配置路径;
不能因为两条请求同错就把配置解析与探活合并成一项成功结论。

结论:服务可达且发出Basic challenge的局部前提**成立**;
“当前访问条件下Basic Auth即可取得REST数据”前提**未成立,需改访问前提**。
服务端文字不足以区分账号权限/IP策略或判定密码正确,不推测具体根因,
不改来源IP、不尝试绕过访问控制。
影响§1.4 EF-5①与§4.1 qb-sbs-trigger/qb-result-fetch的可执行前提;
请管理员/设计方确认允许的账号和访问来源。此时不自动改design.md,
若环境不能开放REST再由设计方裁决接口路径。

## ③ 既有SBS结果与绑定字段

状态:**BLOCKED_REST_ACCESS_AND_PAGE_LOGIN**。
FatTank在终端指定样本build **1069532**,未提供上级TRIGGER号。
对`/rest/builds/1069532`与`/status`、`/variables`、`/steps`、
`/dependencies`、`/request_id`的GET均为500和上述AccessDeniedException。
未提供Cookie,`/build/1069532`匿名GET为302,Location指向signin;
探测器未跟随重定向。没有获得构建业务页,不能独立验证样本类型或字段。
证据:`evidence/authenticated-01/sbs-rest*.response.txt`与`sbs-page.response.txt`,
元数据在同目录`requests.json`;`*.fields.json`只是错误页字段,**不是SBS状态字段**。

取证计划:同一build读取HTML与REST完整响应(先脱敏);REST XML叶字段另作
带路径的机械枚举,保存status/variables/steps/dependencies/request_id响应。
先证明样本确为SBS复验,再核对`repo@commit`回显和架构粒度;
permission-denied或登录页不作为“字段不存在”的证据。

对设计影响:§1.4 EF-5③与§4.1 qb-result-fetch的
`status/sbs_target_echo/per_arch_status`仍待实测,不能判定成立或需改;
拒绝访问不等于字段不存在。

## ④ 上级TRIGGER与accept语义

状态:**PENDING_LINKED_TRIGGER**。
尚无同一SBS对应的上级TRIGGER证据,未发起TRIGGER探测,
不以相近时间/相似版本猜测父子关系,
也不以“SBS自身成功”推断accept不必要。
取得明确对应关系后记录accept字段/表格/步骤及SBS自身状态,分别保留原始证据。
若环境证据不能证明PASS的必要条件,请设计方/服务负责人确认其语义,
不直接调整`qb_pass_requires_accept`。

对设计影响:§1.4 EF-5④与§4.1 review-submit双态判据仍待定。

## 边界与官方资料

上述编号沿设计稿EF-5编号;②真实REST提交仍被人工闸门阻止,
未发送请求,也没有request_id到build_id的实验结论。
目标configuration、SBS_TARGET、其它变量及构建条件参数未确认,
因此未声称已备妥一个可提交的完整请求。它须在目标指定后单列打印,
FatTank明确确认后才允许发送一次。本探测脚本没有POST或trigger入口。

官方REST资料仅用于选择候选读接口,不是本环境实测结果:

- [PMEase Interact with Builds](https://wiki.pmease.com/display/QB16/Interact%2Bwith%2BBuilds):只读build、变量与步骤端点。
- [PMEase Interact with Build Requests](https://wiki.pmease.com/display/QB16/Interact%2Bwith%2BBuild%2BRequests):请求对象与响应的候选协议。

实现复用shared的URL规范化/响应对象/登录识别约定,但不读取现有磁盘cookie文件。
只允许固定只读端点并禁止redirect,因为QuickBuild存在可触发构建的GET入口;
响应正文中的已知凭据、Set-Cookie值、敏感XML字段、HTML隐藏/密码域先脱敏再落盘,
之后自检。网络异常不会打印凭据或Authorization头。

## 输入安全与后续停点

本次configuration输入被已知敏感值规则完全遮蔽。初版探测器在落盘前脱敏,
但未在发出URL前检查,该输入曾出现在发往QuickBuild的GET查询里,
可能进入服务端访问日志。已向FatTank说明:若该栏误填密码,须更换该密码。
不在报告复述、猜测或恢复敏感值。本地证据自检PASS,不含该输入明文。

提交版已增加发送前已知凭据URL拒绝,并把隐藏凭据提示置于可选配置输入之前;
离线控制证明命中时网络调用次数为0且无证据文件产生。
另增加Basic探活非200即停止后续读取的控制,避免重复权限拒绝。
**本轮真实记录来自加固前的采集**(匿名对照1次,本人输入后的批次10次GET);
后续只跑离线控制,没有假称新版本重新取得了鉴权结果。

恢复需:管理员确认REST访问前提、非敏感的有效configuration path、
本人getpass提供可用Cookie(页面取证)、样本1069532对应的TRIGGER依据。
未解决前EF-5保持OPEN,P5Q门不解除,真实提交仍为0次。

## 网页只读续测(2026-10-08)

以下为本轮结果,前文为历史REST实测,未覆盖或重跑。网页脚本
`ef5_web_probe.py`仅使用QB_COOKIE/getpass,不使用Basic密码或磁盘cookie;
严格GET白名单且禁redirect/JS/表单提交。样本仍为1069532。

### 事实与设计影响

| 项目 | 本轮观察到的事实与证据 | 对EF-5假设的影响 | 涉及段落 |
|---|---|---|---|
| 确认样本SBS身份 | 环境无QB_COOKIE,本人getpass输入尚未取得;等待已结束,无网页响应。`stage15/evidence/web-input-attempt.json` | 未能检验,不是否定SBS身份,不把权限/凭据问题当作字段缺失 | §1.4 EF-5③ |
| 状态字段/SBS_TARGET/arch | 未取得业务HTML,无字段全集、回显位置或架构表示的实测结论 | 待核实,不能标成立或需改 | §1.4 EF-5③、§4.1 qb-result-fetch |
| 上级TRIGGER/accept | 未取得任何关联页面,未推断上级build号 | 待核实,不能认定SBS自身PASS即足够,也不能认定必须accept | §1.4 EF-5④、§4.1 review-submit |

上述`stage15/`指
[stage15证据目录](../dev_memory/stage15_p1_ef_spike/evidence/)。
离线安全验证与全仓回归不是环境实测:
网页6项/旧探测器10项安全控制通过,mypy/ruff通过,全量1457 passed/1 skipped;
命令、exit与原文见[web-validation](../dev_memory/stage15_p1_ef_spike/evidence/web-validation/)。
不修改design.md,不解除P5Q门。

### 触发参数清单与人工闸门

本轮没有取得网页表单,故以下只是待采集项,**不是已核实可提交请求**:

| 参数/对象 | 来源与状态 |
|---|---|
| 目标configuration | 待网页明确路径/ID,不能把build 1069532当作configuration ID |
| SBS_TARGET(repo@commit) | 来自设计契约的待核实参数;网页名称、值、位置未取得 |
| 其它变量/构建条件/请求参数 | 待只读构建变量与字段名证据;不能杜撰默认值 |

未打开触发/取消/重跑入口。真实提交仍NOT_GRANTED,本轮提交0次;
完整参数取得后须先打印并由FatTank指定目标及明确确认,当前未执行。
EF-5②的提交响应与request_id→build_id映射仍没有实验结论。

### 网页方式用于自动化的可行性

**实测边界**:本轮未取得鉴权网页,目前没有任何信息可被宣称为已证实能稳定从网页获取。
仅验证了本地工具对人工HTML样本能提取带源行号的可见文本、链接和脱敏表单字段名。
要判断status/SBS_TARGET/per_arch_status/accepted的稳定性,还需该环境实际响应。

**实现风险评估(不是QB实测事实)**:HTML布局、标签名称和链接路由可能随服务端升级变化;
若业务标签依赖JS/Wicket动作链接,当前工具会拒绝而不是自动执行。
后续自动化需逐项核实只读路由、页面类型和字段绑定,不能把空解析当成字段不存在。
Cookie会话续期与登录页检测也是额外维护面。

**相对REST的代价(推论)**:网页方案需要管理会话、请求多页、维护HTML解析与更广脱敏,
且页面上的成功字样不能代替父子关联和accept语义证据;REST原本有结构化字段优势,
但当前环境已实测拒绝其访问。网页只能作为待验证的候选取证路径,不是绕过权限,
也不能凭只读页面证明真实提交的响应协议。是否改设计由设计方在取得实测后决定。

## 本人到场后的重跑结论(35d4052,2026-10-08)

### BLOCKED: 本地Cookie头格式校验拒绝

沿用35d4052探测脚本原字节,在可见终端通过getpass输入,不改白名单。
明确允许10分钟等待;未由代理提前结束任何一次等待,各次脚本自行exit2。
两次诊断重跑实测`stdin_isatty=true`、`error_category=COOKIE_HEADER_FORMAT`。
固定脱敏错误说明(来自脚本常量,不是Cookie内容):

```text
QB_COOKIE must be a Cookie header: name=value; name2=value2
exit=2
```

证据:[前一次诊断](../dev_memory/stage15_p1_ef_spike/evidence/web-02-input-format-rejected.json)、
[最后一次诊断](../dev_memory/stage15_p1_ef_spike/evidence/web-02-launch.json)、
[全部启动/退出记录](../dev_memory/stage15_p1_ef_spike/evidence/web-02-attempts.json)。
初始化在GET前拒绝,web-02目录未创建。**请求0、响应0、已读页面0、POST/触发0**。
未收到HTTP错误页,因此不能将本地错误写成QuickBuild服务端拒绝。

| 页面 | HTTP请求 | build状态 | 步骤 | 日志链接 | 产物列表 | trigger入口 |
|---|---|---|---|---|---|---|
| 计划/build/1069532 | 未发出 | 未读取 | 未读取 | 未读取 | 未读取 | 未读取;未点击 |

没有实际标签页响应可列。状态全集/SBS_TARGET/arch/TRIGGER对应关系/accept均待核实;
不满足WEB_READ_OK或WEB_READ_PARTIAL的实际读取前提,也不能据此判字段不存在。

对设计§1.4 EF-5③④及§4.1 qb-result-fetch的影响:**未能检验**,不能标为假设成立或需改;
EF-5②仍需另行指定目标及明确确认,本轮不执行。
网页自动化可行性仍未得到环境证据,上一节风险评估仅为实现层推论。
不修改design.md、不改变P2-P4代码、不解除P5Q开工门。

## 隔离浏览器登录后实测(2026-10-08):WEB_READ_PARTIAL

本人授权并在新建可见浏览器中手工登录。Cookie只由这个非持久会话取得,
经匿名内存管道传入原有`ef5_web_probe.py`,不复制到聊天/命令行/环境变量/文件。
浏览器使用本机已有Chromium,临时目录在`/dev/shm`,不使用日常profile;
未启用HAR/trace/storage-state,取证结束即关闭并清理。登录由本人提交,
与后台探测严格分开:以下请求统计只指后台业务页面探测,不含人工登录和静态资源。

证据:[web-browser-01](../dev_memory/stage15_p1_ef_spike/evidence/web-browser-01/)。
`run.json`记录结束于`2026-10-08T10:07:34.775015+00:00`,
**3次GET、全部200、0 POST/构建操作、exit=0、脱敏自检PASS**。
三个HTML响应在写入前均由原有PageRedactor处理;Set-Cookie不归档。

### 页面覆盖

| 页面 | HTTP | build状态 | 步骤 | 日志链接 | 产物列表 | trigger入口 |
|---|---|---|---|---|---|---|
| /build/1069532 | 200 | Successful; SR_STATUS=ACCEPTED(20260424.154027) | 仅Step Status入口,未读详情 | /build/1069532/log可见,未访问 | Artifacts列Download_URL与Manifest_URL,未打开产物 | Run the configuration按钮可见,未点击 |
| /build/1069532/overview | 200 | 同上 | 同上 | 同上 | 同上 | 同上,未点击 |
| /build/1069532/variables | 200 | 变量SR_STATUS=ACCEPTED;本页无Summary表 | 仅Step Status入口 | Build Log入口可见,未访问 | 无Artifacts表;有TARGET_SNAPSHOT_URL变量 | Run the configuration按钮可见,未点击 |

实际步骤路由是`/build/1069532/step_status`,不是现有白名单的`/steps`;
因此被记录为NOT_FOLLOWED,没有擅自扩白名单。`/log`、`/gbs_reports`、
所有Wicket动作链接与子构建1069540同样未请求。

### 事实、设计影响与缺口

| 项目 | 实测事实与原文位置 | 对EF-5假设的影响 | 涉及段落 |
|---|---|---|---|
| 样本身份 | `01.response.txt:6/:679`配置为`root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/SBS/TRIGGER`;variables的BUILD_CATEGORY=SBS、QB_CUR_STEP=TRIGGER、QB_TRIGGER_ID=1069532 | 样本属于SBS流程的TRIGGER,不能当作子SBS实跑构建 | §1.4 EF-5③④ |
| 状态与accept | `01.response.txt:915-945`完整Summary列Id/Status/Begin Date/Duration/Triggered By/#Dependents/#Dependencies/SR_STATUS;Status=Successful,SR_STATUS=ACCEPTED(20260424.154027);页面同时显示Ready to Accept操作按钮 | 网页可读取两个独立字段;按钮不是状态证据。单个样本不能证明accept是门2通过的必要条件 | §1.4 EF-5④、§4.1 qb-result-fetch |
| 目标回显 | `03.response.txt:819`的BUILD_PKG_LIST与BUILD_PKG_LIST_MODIFY均为`platform/upstream/python3@7cbaf2d74f3428e706c6cae8b3b06b843d140379`;本次三页未出现SBS_TARGET变量名 | repo@commit形态得到证据,但设计变量名到环境实际变量的映射需核实,不能擅认二者等价 | §1.4 EF-5③、§4.1 qb-sbs-trigger/qb-result-fetch |
| 架构与父子关系 | `01.response.txt:885-899`的Child Build明确链接1069540,Repository-Architecture=`standard-armv7l:aarch64:x86_64`,Build Result=SUCCESSFUL;variables中CHILD_CONFIGURATIONS同值 | 已有明确父子链接,不是时间推断;合并字符串不等于三架构逐项状态,尚缺子页独立取证 | §1.4 EF-5③④、§4.1 qb-result-fetch |
| 触发入口 | `01.response.txt:689`的按钮title为Run the configuration,指向Wicket动作;没有打开 | 仅证明UI入口存在,不证明提交参数/协议可自动化 | §1.4 EF-5②、§4.1 qb-sbs-trigger |

因此选**WEB_READ_PARTIAL**,不是WEB_READ_OK:缺步骤详情、子构建自身状态与
逐架构结果、SBS_TARGET的明确字段映射、accept必要性判据。产物仅取得两个链接,
未枚举实际文件;日志也仅取得链接。真实提交、request_id到build_id映射仍未执行。

### 网页自动化可行性与下一停点

本样本证实无JS的GET HTML可承载Summary、Variables、Artifacts链接和Child Build表。
尚未证明跨版本稳定:路由已出现`step_status`与脚本假设不同的情况,且Wicket动作
不能作为普通只读链接自动跟随。相对REST,需管理登录会话、逐页白名单、HTML
字段定位与脱敏;REST拒绝事实不变,本轮没有重试REST或绕过其权限限制。

下一步只读取证的明确对象是子构建1069540与页面实际步骤路由;需核实路由后
再调整独立spike白名单。本轮会话已丢弃,不保留凭据以便后续暗中续跑。
未读取触发表单,不把Variables页字段直接当成可提交参数。真实提交仍须另行
完整请求确认。本轮不修改design.md、不改变P2-P4代码、不解除P5Q开工门。

## 五路径补测与追加脱敏(2026-10-09)

**累计仍为WEB_READ_PARTIAL;本轮为BLOCKED_LOCAL_HANDOFF,没有新页面事实。**
白名单已精确补入指定五个GET,后台只跑固定队列,不自动跟随其它链接;
动作链接、/log、REST与POST继续拒绝。隔离浏览器已启动并等待10分钟,
未由代理提前结束。启动器最终exit=2,会话交接未完成,探测目录未产生。
后台请求0,不是QuickBuild返回权限拒绝,也不能据此认定本人没有登录。
本人认证/静态资源请求不在后台统计内。会话已关闭,未保存Cookie。
见[本轮启动记录](../dev_memory/stage15_p1_ef_spike/evidence/browser02-launch.json)。

| 新增页面 | 本轮请求/HTTP | Status与SR_STATUS | 架构/步骤/关联/目标变量 |
|---|---|---|---|
| /build/1069540 | 未发出,无响应 | 未读取 | 未读取,不能用父页Child Build摘要代替子页 |
| /build/1069540/overview | 未发出,无响应 | 未读取 | 未读取 |
| /build/1069540/variables | 未发出,无响应 | 未读取 | SBS_TARGET及其它目标变量、父子关联变量均待实测 |
| /build/1069532/step_status | 未发出,无响应 | 不作结论 | 父构建步骤列表及每步状态待实测 |
| /build/1069540/step_status | 未发出,无响应 | 不作结论 | 子构建步骤列表、每步状态及逐架构独立状态待实测 |

历史三页已补做身份脱敏:Welcome!后的登录显示名与Triggered By账号均替换
为`<USER>`(HTML源码写`&lt;USER&gt;`),响应与派生page.json同步更新,
requests.json中的redacted_sha256已重算。源行号与业务数据不变,没有重新GET。
新旧hash、3页的2/2/1个身份字段见
[重脱敏记录](../dev_memory/stage15_p1_ef_spike/evidence/browser02-archive-redaction.json)。
旧提交的历史内容未重写;当前树的三页与派生JSON已按新规则处理。

以下是业务规则,不由本次探测决定,stage15已分别登记**待人工裁定(FatTank)**:

1. 通过判据是只看Successful,还是必须ACCEPTED。
2. SBS_TARGET与BUILD_PKG_LIST是否等价。

因此仍缺:子构建1069540的自身状态与变量实测、父子步骤详情、各架构是否有
独立状态、明确关联字段与目标变量证据;再加上述两项人工裁定。
此前1069532的Successful/ACCEPTED与子链接事实保留,不拿来补齐本轮空缺。
技术上白名单与脱敏准备已完成,下一轮只读采集仍需本人登录并完成终端确认。
离线24项、浏览器策略20项通过;全仓1457 passed/1 skipped,mypy/ruff通过,
这些不是线上页面证据。详情见[stage15 §12](../dev_memory/stage15_p1_ef_spike/progress.md#12-五路径补测与身份脱敏2026-10-09)。
本轮不重试REST、不读取触发表单、不修改design.md或P2-P4代码。

## 五路径再次到场重跑(2026-10-09):BLOCKED

本次按`f507201`的五路径原白名单重新启动隔离浏览器,启动前已在可见终端
写明“先在浏览器里登录，登录后回到本终端按回车。”等待上限仍600000ms,
没有提前结束,没有由代理代按回车。启动器最终自行exit=2,没有完成取证交接。
**后台业务请求0、响应0、POST/触发0**;人工浏览器登录与静态资源不计入该数字。
Cookie未写入文件、日志、证据或聊天。页面抓取器未运行,故本轮没有新增HTML
可做字段分析或脱敏;既有`<USER>`写盘前规则和三页历史重脱敏结果保持不变。

证据:[web-browser-02/launch.json](../dev_memory/stage15_p1_ef_spike/evidence/web-browser-02/launch.json)。
这是退出后补写的启动记录,不是页面采集成功记录;没有`run.json`或响应文件。
启动时只收到GTK模块告警,退出时工具收到空输出;未取得QuickBuild拒绝响应,
因此错误类别只记`LOCAL_HANDOFF_NOT_COMPLETED`,不推断具体认证失败原因。

| 本次预定页面 | 实际请求 | Status/SR_STATUS | 步骤/逐架构状态 | 日志/产物/trigger |
|---|---|---|---|---|
| /build/1069532/step_status | 0 | 未读取 | 未读取 | 未读取;无点击 |
| /build/1069540 | 0 | 未读取 | 未读取 | 未读取;无点击 |
| /build/1069540/overview | 0 | 未读取 | 未读取 | 未读取;无点击 |
| /build/1069540/variables | 0 | 未读取 | 目标变量与关联字段未读取 | 未读取;无点击 |
| /build/1069540/step_status | 0 | 未读取 | 未读取 | 未读取;无点击 |

本次结论选**BLOCKED**,不是WEB_READ_OK或一次新的WEB_READ_PARTIAL。
累计历史证据仍为WEB_READ_PARTIAL,仅依据先前1069532三页,不补齐本轮缺口。
仍缺:1069540自身Status与SR_STATUS、架构是否有各自状态、父子步骤列表及每步
状态、子页中的父子关联字段、SBS_TARGET或其它目标变量回显。实际产物文件
清单未枚举,日志只有历史入口且仍禁止访问。真实触发和request_id映射未执行。

对§1.4 EF-5③④及§4.1 qb-result-fetch:**本轮没有新事实,不能更新假设判断**。
网页自动化可行性评估保持原有部分可读结论;会话交接尚未完成不等于页面字段缺失。
Successful是否足够或必须ACCEPTED、SBS_TARGET与BUILD_PKG_LIST是否等价,
继续**待人工裁定(FatTank)**,不由探测器决定。

离线24项与浏览器策略20项通过;全仓`1457 passed, 1 skipped`,mypy/ruff通过。
命令与原文见[stage15 §13](../dev_memory/stage15_p1_ef_spike/progress.md#13-本人到场后的五路径重跑2026-10-09)。
design.md、P2-P4代码、白名单和凭据处理均未修改,不重试REST、不读触发表单。

## Cookie文件只读取证(2026-10-10)

### FatTank裁定与设计影响

| FatTank 2026-10-10裁定 | 状态与设计影响 |
|---|---|
| 子构建Status=Successful即通过,不要求SR_STATUS=ACCEPTED | 已裁定;qb_pass_requires_accept默认false,在campaign启动时冻结入库,配置变更仅影响新campaign;由P5Q设计稿落实 |
| SBS_TARGET是设计内部名称 | QuickBuild实际填写BUILD_PKG_LIST / BUILD_PKG_LIST_MODIFY / 其它变量待取证后再定,不能擅自认定等价 |
| 不申请REST权限;触发和结果读取均走网页Cookie | REST/Basic Auth前提需改,涉及design.md §1.4 EF-5与§4.1 qb-sbs-trigger/qb-result-fetch;由P5Q设计稿替换,本轮不改design.md、不执行触发 |

### 实跑与逐页事实

本轮只执行一次Cookie探测入口。Cookie由shared load_cookie_jar读取,
权限位0600,不复制文件、不输出值、不落盘请求头。仅GET 1次、HTTP 200,
POST=0、redirect跟随=0、触发=0。第1页已通过登录检查并完成写前脱敏,
但写后校验以read_text读取时把CRLF转为LF,导致字节相等检查误报。
run.json如实为BLOCKED/stage=write/page_index=1/WRITE_FAILED;
不是鉴权失败,后续页面均未请求。

证据根:[web-cookie-01](../dev_memory/stage15_p1_ef_spike/evidence/web-cookie-01/)。
首张响应01.response.txt已保留,未重取或改写;修复后仅离线复核凭据与USER脱敏,
生成01.offline-page.json与offline-integrity.json,不覆盖原run.json/requests.json。
修正为按原字节回读,补CRLF离线控制通过。已询问是否允许不重取第一页而继续剩余页面;
在获准前不再发请求。

| 顺序/页面 | 请求/HTTP | 读到的事实与源行号 |
|---|---|---|
| 1 /build/1069540 | GET/200 | 01.response.txt:6为SBS/build及组合架构标题;:831为1069540,:832为Successful;:841/:844的Dependents/Dependencies均0 |
| 2 /build/1069540/overview | 未请求 | 未读到;第1页write停机,不能用首页代称该URL已读取 |
| 3 /build/1069540/variables | 未请求 | 未读到变量原名/值、SR_STATUS或目标映射 |
| 4 /build/1069540/step_status | 未请求 | 未读到步骤列表及逐步/逐架构状态 |
| 5 /build/1069532/step_status | 未请求 | 未读到父构建步骤列表及逐步状态 |
| 条件项 /overview/1921 | 未请求 | 已归档1069532页:705有普通Configuration Overview链接../overview/1921;本轮因前序停止而NOT_FOLLOWED,非猜路径 |
| 条件项配置变量页 | 未请求 | 尚无配置页响应,没有枚举或猜测变量页URL |

逐项结论(仅对实际所读页面成立):

1. **子构建状态**:1069540首页Status=Successful(:818/:832)。SR_STATUS未读到,
   变量页未请求。Triggered By已替换为USER(:838),不用于关联推断。
   首页未读到明确指向1069532的父子关联字段;只见Dependents/Dependencies数值0,
   不能把这些计数解释为不存在父子关系。历史父页摘要不补齐此缺口。
2. **逐架构独立状态**:未读到。首页:6/:736只有
   standard-armv7l:aarch64:x86_64组合字符串,不等于各架构独立状态。
3. **两个构建步骤**:均未读到。首页:793只有Step Status入口,不能代替步骤详情。
4. **含@的变量与父子比对**:1069540变量页未请求,原名/值及与1069532对应变量的
   一致性均未读到/未确定。不能用旧父页BUILD_PKG_LIST或BUILD_PKG_LIST_MODIFY替代。
5. **配置与prompt**:历史1069532归档页:6/:679显示
   root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/SBS/TRIGGER,
   :705明确配置页链接;这只是链接来源,不是本轮配置页实测。
   运行时prompt变量名、默认值及“运行前会弹出变量页”说明均未读到。
   Run the configuration/Ready to Accept入口均未请求,不推断其点击行为。

### 结论与影响

本次结论:**BLOCKED**,停在write阶段第1页。Cookie网页可读已得到HTTP 200与
真实子构建Successful字段支持;其余字段仍不足,不能宣告WEB_READ_OK或EF-5完成。
按FatTank已裁定的通过规则,该页观察到的Successful满足本次样本的状态条件,
但不证明目标绑定、逐架构覆盖或P5Q整体流程已验证。

网页自动化仍有结构变化与会话有效期风险;本轮只多取得子构建首页,
没有取得配置prompt与变量页,不能据此推断自动触发参数或稳定解析契约。
涉及P5Q待落实的设计段落同上,不改design.md、不改P2-P5代码/冻结稿。

## Cookie文件第二次只读取证(2026-10-10)

### 请求与边界

FatTank已批准续跑。新目录[web-cookie-02](../dev_memory/stage15_p1_ef_spike/evidence/web-cookie-02/)
与web-cookie-01分开,本次按新白名单重新读取首页,未覆盖或重写旧证据。
实跑exit=0,**7 GET / 7个HTTP 200 / POST 0 / redirect跟随0**。
Cookie仅内存,文件权限0600;写前PageRedactor与USER脱敏,写后按原始字节校验。
配置页来源仍为web-browser-01/build-1069532-01.response.txt:705,
归档SHA校验通过;仅允许该链接对应的/overview/1921。
该页没有普通Variables链接,条件变量页记NOT_FOLLOWED/NO_LITERAL_LINK。
不请求Wicket动作、/log、REST、Run/Accept入口或iframe/外站。

下表及后文的短文件名均相对于web-cookie-02;父变量页比较明确使用web-browser-01归档,
不将父页摘要当作子页字段。每页原字节脱敏SHA见requests.json;
facts.json为离线HTML解析结果,保留源SHA、原行号、变量全部值与逐字比较结果。

| 顺序/页面 | 请求/HTTP | 读到的字段与源位置 |
|---|---|---|
| /build/1069540 | GET/200 | 01.response.txt:831为ID,:832为Status=Successful;:841/:844依赖计数均0 |
| /build/1069540/overview | GET/200 | 02.response.txt:831/:832同样明确ID及Successful |
| /build/1069540/variables | GET/200 | 03.response.txt:804有45个变量,含BUILD_PKG_LIST、TRIGGER_ID、REPO_ARCH |
| /build/1069540/step_status | GET/200 | 04.response.txt:816起21个步骤/容器节点及其状态,见下表 |
| /build/1069540/html_report | GET/200 | 05.response.txt:805只有报告iframe入口;未加载其内容 |
| /build/1069532/step_status | GET/200 | 06.response.txt:831起19个步骤/容器节点;:1189直接链接Triggered build 1069540 |
| /overview/1921 | GET/200 | 07.response.txt:6配置完整路径;:895/:905/:926为1069532条目及其SR_STATUS |
| 配置变量页(条件项) | 未请求 | 07.page.json及run.json:无普通Variables链接,NOT_FOLLOWED;不猜路径 |

### 1. 子构建状态与父子关联

- Status=Successful:01.response.txt:818为字段名,:831为1069540,:832为值;
  02.response.txt:818/:831/:832独立重复观察。符合FatTank已裁定的子构建通过条件,
  但不单独证明目标或逐架构绑定。
- **子构建SR_STATUS未读到**:01至05页的实际HTML/可见字段没有该名称;
  不据此推断服务端不存在此字段。
- 子页明确关联字段是`TRIGGER_ID=1069532`(03.response.txt:804),
  同页`QB_TRIGGER_ID=1069540`不能误当父ID。
  04.response.txt:868的TRIGGER是本构建步骤名(skipped),不单独充当父ID证据。
  子页未读到直接指向/build/1069532的链接。
- 另在实际读取的父步骤页06.response.txt:1189,`Triggered build:`后链接
  `/build/1069540`,与子页TRIGGER_ID对应。不是凭时间、版本或Triggered By推断。
- 配置页07.response.txt:895/:905/:926明确展示**父构建**1069532的
  `SR_STATUS=ACCEPTED (20260424.154027)`;这是父字段,不填作子SR_STATUS,
  也不改变FatTank“不要求ACCEPTED”的通过裁定。

### 2. 各架构独立状态与报告边界

| 架构 | 读到的位置 | 独立状态 |
|---|---|---|
| standard-armv7l | 03.response.txt:804的REPO_ARCH/CHILD_CONFIGURATIONS;04.response.txt:726标题;05.response.txt:731标题 | 未读到 |
| aarch64 | 同上,位于同一冒号分隔字符串 | 未读到 |
| x86_64 | 同上,位于同一冒号分隔字符串 | 未读到 |

03.response.txt:804中`ARCHITECTURE=armv7l:aarch64:x86_64`,
`REPO_ARCH=standard-armv7l:aarch64:x86_64`,`EACH_GBS_BUILD_STATUS`值为空。
06.response.txt:1157/:1306/:1353的三个步骤名也使用组合REPO_ARCHS,
不能把单个步骤状态拆成三份独立架构状态。

05.response.txt:805的iframe原路径形态是
`/download/1069540/html/HTML REPORT/index.html`,相对本机站点,**NOT_FOLLOWED**。
05.page.json显式记录iframe与普通链接均未跟随;外站帮助/支持链接
(05.response.txt:576/:822/:828/:831)同样未请求。
03.response.txt:804的SNAPSHOT_NUM_URL含`http://download.tizen.org/snapshots/...`,
只记录变量中的URL,不访问。未执行JavaScript或加载任何子资源,
因此报告内可能存在的逐架构状态仍为未读到,不是宣称不存在。

### 3. 两个构建步骤与每步状态

以下保留页面全部步骤/容器节点(包含master及重复出现的Update_Trigger_Description),
不合并、不把skipped改写为通过。行号列依次为“名称 / 状态”。

| 1069540步骤名 | 原状态 | 源文件:行号(名称 / 状态) |
|---|---|---|
| master | successful | 04.response.txt:818 / :816 |
| TRIGGER | skipped | 04.response.txt:868 / :866 |
| BUILD_ABS | skipped | 04.response.txt:909 / :907 |
| BUILD | successful | 04.response.txt:950 / :948 |
| Enable_SWAP | successful | 04.response.txt:996 / :994 |
| Update_Trigger_Description | successful | 04.response.txt:1043 / :1041 |
| Sync | successful | 04.response.txt:1094 / :1092 |
| Sync_Clean_Workspace | successful | 04.response.txt:1140 / :1138 |
| Sync_Copy_Src_from_Src_Server | successful | 04.response.txt:1187 / :1185 |
| Build | successful | 04.response.txt:1241 / :1239 |
| Build_GBS | successful | 04.response.txt:1287 / :1285 |
| Update_Trigger_Description | successful | 04.response.txt:1334 / :1332 |
| Publish | successful | 04.response.txt:1388 / :1386 |
| NGBS_HTML_REPORT | successful | 04.response.txt:1438 / :1436 |
| Create NGBS build report | successful | 04.response.txt:1484 / :1482 |
| NGBS HTML REPORT | successful | 04.response.txt:1531 / :1529 |
| Publish_Each_Build | successful | 04.response.txt:1581 / :1579 |
| Publish_HTML_Report | skipped | 04.response.txt:1628 / :1626 |
| Publish_Build_Profiling_Report | skipped | 04.response.txt:1665 / :1663 |
| SNAPSHOT | skipped | 04.response.txt:1712 / :1710 |
| IMAGE | skipped | 04.response.txt:1753 / :1751 |

| 1069532步骤名 | 原状态 | 源文件:行号(名称 / 状态) |
|---|---|---|
| master | successful | 06.response.txt:833 / :831 |
| TRIGGER | successful | 06.response.txt:883 / :881 |
| Change_Variable_To_File | successful | 06.response.txt:929 / :927 |
| Chk_Abnormal_Input_Variables | successful | 06.response.txt:976 / :974 |
| Update_Meta_for_RBS | skipped | 06.response.txt:1023 / :1021 |
| Src_Server_Sync | successful | 06.response.txt:1060 / :1058 |
| Parallel_Build | successful | 06.response.txt:1111 / :1109 |
| Trigger_Each_Build?REPO_ARCHS=standard-armv7l:aarch64:x86_64 | successful | 06.response.txt:1157 / :1155 |
| Src_Server_Clear | successful | 06.response.txt:1209 / :1207 |
| AggregateReport | successful | 06.response.txt:1260 / :1258 |
| PublishGBSReport?REPO_ARCHS=standard-armv7l:aarch64:x86_64 | successful | 06.response.txt:1306 / :1304 |
| PublishProfilingReport?REPO_ARCHS=standard-armv7l:aarch64:x86_64 | skipped | 06.response.txt:1353 / :1351 |
| BUILD_ABS | skipped | 06.response.txt:1400 / :1398 |
| BUILD | skipped | 06.response.txt:1441 / :1439 |
| SNAPSHOT | successful | 06.response.txt:1482 / :1480 |
| Update_Trigger_Description | successful | 06.response.txt:1528 / :1526 |
| Snapshot_Create | successful | 06.response.txt:1575 / :1573 |
| Trigger_Image_Create | successful | 06.response.txt:1626 / :1624 |
| IMAGE | skipped | 06.response.txt:1680 / :1678 |

### 4. 变量与逐字比对

子变量页全部45行位于同一HTML物理行03.response.txt:804,
按`Name / Display Name / Value`表列解析(表头:801),不是全文名字搜索。
其中**值含@的变量只有BUILD_PKG_LIST**:

```text
platform/upstream/python3@7cbaf2d74f3428e706c6cae8b3b06b843d140379
```

与web-browser-01/build-1069532-03.response.txt:819中同名BUILD_PKG_LIST
的解码后单元格文本逐字相等(`facts.json:child_at_value_comparison`,exact_equal=true)。
父归档原SHA=d65cdbb41e62c4eb97613d64934adefe0b4b1261a80ef68f6128e69a95844f2f,
本轮离线校验通过,未重取父变量页。

子页**BUILD_PKG_LIST_MODIFY未读到**,故不能做它的同名父子比较;
父归档:819确有BUILD_PKG_LIST_MODIFY(显示名Build Package List),
值与上面相同。该单样本不证明BUILD_PKG_LIST与BUILD_PKG_LIST_MODIFY具有同一输入语义,
更不自行认定它们与SBS_TARGET等价。子变量页SBS_TARGET也未读到。

全部变量名原序如下;脱敏后的全部值见facts.json的child_variables与03.response.txt,
空单元格保留为空,未用父页补值:

```text
ARCHITECTURE
BUILD_CATEGORY
BUILD_HOME
BUILD_META_PATH
BUILD_PKG_LIST
BUILD_PKG_LIST_FILE
BUILD_PKG_LIST_READ_FROM_FILE
BUILD_REFERENCE
CHILD_CONFIGURATIONS
CHILD_CONFIGURATIONS_FIX
DIVISION
DOCKER_NAME
EACH_GBS_BUILD_STATUS
ENABLE_PROFILING
ENV
FAIL_FAST
FIXED_VARIABLES_FILE
GBSBUILD_WORKSPACE
HTML_REPORT_REPO
IMAGE_BUILD_ID
KS_NAME
MASTER_AGENT_NODE
META_PACKAGES_COMMIT_ID
META_PROFILE
PROJECT_NAME
QB_CUR_STEP
QB_SCRIPTS
QB_SCRIPTS_BRANCH
QB_SCRIPTS_ORG_REPO
QB_TRIGGER_ID
REPOSITORY
REPO_ARCH
REPO_TYPE
SNAPSHOT_NUM_URL
TARGET_IMAGE
TARGET_IMAGE_FIX
TARGET_SNAPSHOT_URL
TIZEN_VERSION
TRIGGER_ID
USER_DEFINED_GBS_BUILD_CMD
USE_BRANCH_POLICY
USE_NGBS
VAR_FILE_TRANSFER
WORKSPACE
stepRetried
```

### 5. 配置页与运行时prompt

07.response.txt:6实际标题给出完整路径:
`root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/SBS/TRIGGER`;
:659至:689为面包屑,:759为配置ID 1921。
页中未读到变量定义、运行时prompt标记、prompt变量名/默认值,
也未读到“运行前会弹出变量页”的文字。没有普通Variables链接,
所以条件变量页未请求;不能解释成此配置没有变量或不提示填写。

:699可见`Run the configuration`按钮title,其onclick指向Wicket动作,
**未点击、未请求**;06.response.txt:745的Ready to Accept同样只记录不操作。
不从按钮名称或配置近期构建信息推断Run后会发生什么。

### 结论与P5Q影响

本次为**WEB_READ_PARTIAL**,无停机诊断,并非BLOCKED。
子构建Status、直接父子关联、目标样本回显、两页步骤及其状态均可从只读HTML取得。
但独立架构状态、子SR_STATUS、配置prompt及默认值未读到;
实际触发变量的选择仍待FatTank裁定,任何真实触发继续不在本轮授权内。
Successful规则已由FatTank裁定,不需等待ACCEPTED作为子构建通过条件。

对design.md §1.4 EF-5/§4.1的影响:Cookie网页结果读取获得更完整的正向证据,
但不能宣称P5Q需要的全部状态与触发参数已齐;REST/Basic Auth替换仍由P5Q设计稿落实。
静态HTML中的Wicket结构、变量表及步骤标记可能变动,解析应保留缺字段/会话过期的
显式失败通道。没有加载iframe就无法评价其内容的稳定性。
本轮不改design.md、P2-P5代码或冻结稿。

验证:离线43项全绿(较上轮新增2项),全仓1937 passed/1 skipped,
mypy与ruff全绿;命令及exit见stage15 §16.3及web-cookie-02-validation/。

## RBS运行表单离线解析(2026-10-10)

### 新裁定与取证范围

FatTank 2026-10-10新裁定:复验改用**RBS/TRIGGER**,Base-Toolchain和Unified-Toolchain
按包所属工程各设一项;目标为**BUILD_PKG_LIST**(显示名Build Package List,
git_path@commit_id一行一个)。工具永远不点Accept/Ready to Accept,
`ILinkListener-content-buildHead-promote`列入禁止名单;正式快照合入由人Accept。
Run先进入Specify Build Options,最终提交才开跑,此流程为FatTank截图确认,
本轮不通过执行来验证。工具未来显式填写每个字段,不能沿用默认值。

登录由P5Q设计改为终端提示账号密码、工具登录、会话只存内存,不再手抄Cookie;
不申请REST权限。sandbox推送不会自动触发QB,构建仅由工具显式提交RBS表单发起;
此项依据FatTank给出的团队代码说明,本轮未重新审查团队仓库。
P12首次真实推送后仍须观察是否有自发构建,作为挂账观察项。
子构建Successful即通过的既有裁定仍有效,不得与人工Accept混为同一门槛。

本轮唯一输入是FatTank另存的`/tmp/qb_rbs_trigger_form.html`,
文件先前缺失时已停止,本轮确认存在后继续。**网络请求0,未构造请求,未执行JS,
未提交表单,未加载外部脚本或其它资源**。原文件只在内存处理,不复制入库、不删除。
归档:[rbs-form-01](../dev_memory/stage15_p1_ef_spike/evidence/rbs-form-01/)。
先用PageRedactor及USER规则脱敏;所有已有hidden value定点改为`<REDACTED>`,
会话/token/csrf值也遮蔽。HTML以`&lt;REDACTED&gt;`安全编码,JSON为`<REDACTED>`。
没有value属性的hidden仍如实记缺省,不捏造原值。写后逐字节自检,行号保留。

所有下列位置均指`rbs-form-01/form.redacted.html`。完整机器结构、各select全部选项、
onchange原文、按钮信息与证据行在`form.json`;本节只描述保存页面的事实。

### 表单与工程

| 表单/信息 | 实际内容 | 来源 |
|---|---|---|
| title/配置完整路径 | QuickBuild - root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER | form.redacted.html:6 |
| 页面标题 | Specify Build Options | form.redacted.html:718 |
| PROJECT_NAME | Tizen-Base-Toolchain,只读展示,无HTML name | form.redacted.html:729、:735 |
| 快速搜索表单idd3b | method=post;action=page?50-2.IFormSubmitListener-quicksearch | form.redacted.html:615 |
| 运行表单idd3d | method=post;action=page?50-2.IFormSubmitListener-form;multipart/form-data;UTF-8 | form.redacted.html:720 |

两条action都是Wicket IFormSubmitListener动作,仅保存文本,没有构造请求。
表单method=post不等于本轮执行过POST。Unified-Toolchain运行表单未取得,
不能从Base页面推断其URL、ID或字段默认值。

### 字段表

为了可读,下表HTML name的`P(n)`精确展开为
`editor:content:basicProperties:n:property:editor:editor`,不是实际发送的字符串。
form.json逐项保存完整HTML name。必填栏“未见”仅表示没有HTML required/红星标记,
不保证服务端允许为空。所有默认值只作观察,**未来自动化必须显式填写**。

| 标签 | HTML name | 类型 | 必填标记 | 当前默认/全部选项 | 联动/源行 |
|---|---|---|---|---|---|
| PROJECT_NAME | 无 | 只读显示 | 未见 | Tizen-Base-Toolchain | 无输入;:729/:735 |
| BUILD_TYPE | P(1):wrapper:select | select | 星号:758 | 默认0=Full;选项0 Full、1 Partial | onchange;:759 |
| REPO_TYPE | P(2):wrapper:select | select | 星号:784 | 默认/唯一0=ALL | onchange;:785 |
| BUILD_REFERENCE | P(3):wrapper:select | select | 星号:809 | 默认1=Ref. Snapshot;选项0 Live、1 Ref. Snapshot、2 Snapshot Number | onchange;:810 |
| SNAPSHOT_NUM | P(4):wrapper:select | select | 星号:836 | 默认/唯一0=tizen-base-toolchain_20260924.094908 | onchange;:837 |
| PROJECT_BRANCH | P(5):wrapper:select | select | 星号:861 | 默认/唯一0=tizen_base | onchange;:862 |
| Immediate Stop With Error | P(6):checkbox | checkbox | 未见 | checked;没有value属性 | onchange;:885 |
| CHILD_CONFIGURATIONS | P(7):palette:recorder / :choices / :selection | hidden+双列表 | 未见 | recorder已遮蔽;Available空,Selected显示standard-armv7l:aarch64:x86_64 | recorder onchange;:907/:921/:936/:937 |
| Build Package List | P(8):wrapper:input | textarea | 未见 | 空 | onchange;:964 |
| Add Package List | P(9):wrapper:input | textarea | 未见 | 空 | onchange;:987 |
| Remove Package List | P(10):wrapper:input | textarea | 未见 | 空 | onchange;:1010 |
| TARGET_IMAGE | P(11):palette:recorder / :choices / :selection | hidden+双列表 | 未见 | recorder已遮蔽;Available/Selected均空 | recorder onchange;:1033/:1047/:1062 |
| BUILD NOTES | P(12):wrapper:input | textarea | 未见 | 空 | onchange;:1089 |
| 运行表单辅助hidden(无标签) | idd3d_hf_0 | hidden | 未见 | 原HTML无value属性 | 无;:720 |
| 搜索辅助hidden(无标签) | idd3b_hf_0 | hidden | 未见 | 原HTML无value属性 | 无;:615 |
| 搜索输入(无标签) | input | text | 未见 | 空 | 无字段onchange;:620 |

共19个实际HTML控件(搜索2、运行17),另有PROJECT_NAME只读项。
两个双列表各有recorder/choices/selection三个控件,不能按一项漏计其提交名。
本页未读到radio。Build Package List帮助文字:969列出git_path@commit id及两行示例;
它对应业务BUILD_PKG_LIST是FatTank裁定,不是从动态HTML name推测出的变量名。

### 字段联动与双列表提交载体

上表12个可编辑业务项都存在`onchange`中的`wicketAjaxPost`,URL形态为
`page?50-2.IBehaviorListener.0-form-editor-content-basicProperties-...`。
原文逐字段保存在form.json的events,包含解码后的URL及源行号。
这是**发生字段change时注册了服务端回调**的静态证据,没有执行change。
**未读到BUILD_REFERENCE回调是否刷新SNAPSHOT_NUM、或其它回调刷新的目标字段**;
保存HTML没有对应Ajax响应,不得用“通常如此”补齐。

CHILD_CONFIGURATIONS的隐藏记录字段为
`editor:content:basicProperties:7:property:editor:editor:palette:recorder`(:907)。
可见选择器`...:palette:choices`(:921)及`...:palette:selection`(:936)
在:918/:933被明确标为`Wicket.Form.excludeFromAjaxSerialization.<id>='true'`;
Palette.add/remove/moveUp/moveDown把recorder的id作为第三参(:925至:928)。
所以可确认页面的记录载体及Ajax排除关系,不是把显示名直接当作HTML提交名。
**实际POST未执行**,不宣称两个select永远不会出现在任何正常表单POST中。

Selected项:937的可见option.value为
`7374616e646172642d61726d76376c3a616172636836343a7838365f3634`,
十六进制解码为显示文本`standard-armv7l:aarch64:x86_64`。
脚本在内存核对了原recorder是单个hex值且等于此option.value,仅落布尔证明和
`<REDACTED>`占位,未另存隐藏原值。该样本只有一项,**多项分隔/拼接规则未取得**;
外部palette.js(:108)未加载,不能猜逗号或冒号是通用控件序列化分隔符。
TARGET_IMAGE原recorder为空的形态已记录,实际隐藏值仍遮蔽。

### 按钮表

form.json记录全部25个button/按钮式a。下列各项均**没有name和value属性**,
显示文字为空者不把CSS class臆写成可见标签。URL均为脱敏后的页面文本,没有请求。

| 按钮/显示文字 | 类型与动作形态 | name/value | 来源 |
|---|---|---|---|
| Ok | type=submit;onclick禁用按钮、改文案Please wait...、closest('form').submit();无字面URL,所属form action为page?50-2.IFormSubmitListener-form | 均未见 | form.redacted.html:1109;action:720 |
| Cancel | a,href=page?50-2.ILinkListener-form-cancel | 均未见 | form.redacted.html:1110 |
| CHILD_CONFIGURATIONS四个无文字按钮 | type=button;CSS add/remove/up/down;onclick分别Palette.add/remove/moveUp/moveDown,无URL | 均未见 | form.redacted.html:925/:926/:927/:928 |
| TARGET_IMAGE四个无文字按钮 | 同上,作用于自身choices/selection/recorder | 均未见 | form.redacted.html:1051/:1052/:1053/:1054 |
| 快速搜索两个无文字按钮 | :617为button,:621为submit;未见onclick URL,搜索form action在:615 | 均未见 | form.redacted.html:617/:621 |
| 复制配置图标(显示文字空) | title=Copy this configuration to be under specified configuration;未见内联onclick URL,非本轮动作 | 均未见 | form.redacted.html:679 |
| 导航菜单TIZEN/Tizen/Tizen-10.1/Tizen-10.0/Tizen-9.0/Tizen-8.0/Tizen-7.0/Tizen-6.5/Tizen-6.0/Tizen-5.5/Tizen-5.0/Tizen-4.0 | 12个button,未见内联onclick URL,不属于运行表单字段 | 均未见 | form.redacted.html:487/:491/:508/:513/:518/:523/:528/:535/:540/:545/:550/:555 |

禁止名单另登记`ILinkListener-content-buildHead-promote`(FatTank裁定),
不是本保存页里观察到它被执行。全程没有Accept、Run、Ok、Cancel或任何其它操作。

### 结论与未取得项

离线解析完成,网络请求为0,不把本轮标成一次新在线验证。
已有Base RBS运行表单的字段、选项、必填标记、回调和按钮形态;
观察值不能自动成为P5Q的参数选择规则,Unified工程仍待取证。

**仍未取得：提交后的响应形态、新构建号如何获得。**
这两项需后续一次经FatTank明确确认的真实提交;本轮没有请求授权也没有提交。
Ajax服务端刷新目标、多选recorder通用编码也未取得,不能由本页静态结构反推。
P5Q设计稿需落实新配置/业务变量/账号密码内存会话/永不Accept/显式填写规则;
本轮不改design.md、P2-P5代码或冻结稿。验收命令与日志见stage15 §17。
