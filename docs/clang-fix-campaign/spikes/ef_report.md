# P1 EF-5 Environment Report

日期:2026-10-08。结论:**BLOCKED**(最新网页重跑为本地Cookie格式拒绝,非服务端拒绝)。
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
