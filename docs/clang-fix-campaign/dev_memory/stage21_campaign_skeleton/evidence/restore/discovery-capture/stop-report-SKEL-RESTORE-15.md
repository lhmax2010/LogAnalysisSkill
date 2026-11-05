# SKEL-RESTORE-15:live-03首个报告页脱敏失败

状态:STOPPED。没有重试、没有更换页面/包,未实施正式发现CLI或恢复第四批。

## 1. 已执行事实

基线41ce708,RESTORE-14最终离线门禁通过(3435 passed/1既有skip,
字段三次独立重跑也通过)。用户本次确认原话:“开始”。
`live-03.preflight.json`证明输出目录原不存在、源码与冻结稿hash匹配,
P5Q进程/profile无残留。没有改生产代理或capture工具。

`live-03.command.json`保存完整argv。调用capture导出入口,仅给
`[PATHS.at(-1)]`,预定html_report→唯一iframe→zlib/armv7l唯一失败日志。
UTC 2026-11-05 06:03:42.545至06:04:35.243,wrapper52.698秒,exit4。

| 项目 | 事实 | 证据 |
| --- | --- | --- |
| 登录 | ok=true | `live-03/run.json:61` |
| 首个业务页 | GET https://quickbuild.tizen.org/build/1204736/html_report,主帧,HTTP200 | `run.json:7`,`:23`,`:32` |
| 元数据 | text/html;charset=utf-8;无Content-Disposition;单跳;无Download | `run.json:10`,`:12`,`:15` |
| 脱敏归档 | QB_EVIDENCE_REDACTION_FAILED;正文0份,没有成功body应答 | `run.json:64`;`live-03/validation.json` |
| 下游 | iframe/日志没有显式读取;一个未登记other帧请求被拒 | `run.json:40` |
| 清理 | PAGE_CLOSED=48386ms,disconnected=48428ms,profile_removed=true;事后无残留 | `run.json:53`,`:57`,`:116`;`validation.json` |

trace只有FRAMEWORK_SELF_TEST 1与DENIED 8(login4/read4),
没有OPERATION_FAILED、AGENT_STOPPED、CONTINUE_TARGET_GONE或DENY_TARGET_GONE。
本次不是已观察到的Fetch继续/拒绝异常。没有表单/提交操作,没有重读前六页。

## 2. 能定位到哪里,不能定位到哪里

停止发生在`capture.mjs:219`的`writer.write(..., raw, 'html')`。
`redact_capture.py:31`脱敏、`:32`身份完整性检查、`:38`写前检查、
`:40`文件写入、`:45`写后检查均由`:53`的统一except转换成同一固定错误码。
所以不能从run.json判断具体失败点,也不能声称归档后身份残留为0;
当前替换次数/残留都记NOT_COLLECTED。原始正文不落盘,会话已关闭,
不恢复缓存、不另开窗口、不额外请求来补原因。

代码层存在一个值得验证的候选:
`SessionPageRedactor.remember_session_identity`目前只在Welcome文本完整匹配
`account (display)`时才将session_identity_complete标为true(`qb_redact.py:399`)。
这是当前工具实现的一种格式假设,不代表现场页面必然使用此格式。
`live-03/offline-worker-probe.json`纯合成探针证明:
复合格式可归档并复检0;只有单项的Welcome也会返回相同错误且不归档。
**它不是现场根因证明**,现场Welcome结构及完整性布尔值均未取得。
其它脱敏/实体映射/文件检查分支仍未排除。

## 3. 候选处理(仅建议,未实施)

只为capture worker增加封闭的阶段/原因码,例如
IDENTITY_REGISTER、IDENTITY_INCOMPLETE、REDACT、PRECHECK、WRITE、POSTCHECK,
再加Welcome区域数、已登记身份数、完整性布尔值。
不输出身份原文、异常原文/堆栈、页面内容或请求/响应头;
不改变身份完整性要求、不允许失败正文落盘、不放宽网络或重试规则。
若后续证据确认身份格式假设不符,须明确同一会话账号与显示名的可信来源后再修,
不能猜用旧会话名字或取消检查。需要离线覆盖各阶段失败元数据及敏感值扫描,
新真机操作另经裁定及用户在场确认。本轮没有应用任何候选修改。

## 4. 实施分叉与验收边界

RESTORE-08的四条件尚未全部满足:iframe/日志的同源和实际路径、跳转链、
纯文本/Download行为、日志链接文法仍UNKNOWN。仅首个报告页HTTP事实不能替代它们。
按RESTORE-12第三.3立即停止,保持第三批取证停点。
本次只新增元数据、纯合成离线探针结果与文档;生产/工具源码和冻结稿前后不变。
6份元数据经PageRedactor逐文件检查,validation本身也写前/写后检查;
这些检查不被用来宣称未归档的正文已经脱敏通过。
