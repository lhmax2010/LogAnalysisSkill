# P1 EF-5 Environment Report

日期:2026-10-08。状态:**BLOCKED_REST_ACCESS**。
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
