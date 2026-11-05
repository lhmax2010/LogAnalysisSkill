# SKEL-RESTORE-17:live-04 日志链接匹配停止

## 1. 执行范围与结果

基线5721a32,RESTORE-16最终树门禁已通过。用户本次确认原话:“开始”。
前置hash一致、输出目录不存在、P5Q进程/profile与私有run均0;
见`live-04.preflight.json`。没有修改生产代码或取证工具,没有使用测试证书/解析参数。
只运行一次,UTC 2026-11-05 08:18:21.154–08:19:42.051,80.831秒,exit4;
argv与授权见`live-04.command.json`。没有再次请求、没有换包或换构建。

| 页面 | 实测 | 来源 |
| --- | --- | --- |
| `/build/1204736/html_report` | 主帧GET,200,text/html;charset=utf-8,Content-Disposition=null,单跳,Download=false | `live-04/run.json:7`,`:9`,`:12`,`:15`;`01.response.html` |
| 唯一iframe目标 | 主帧GET `/download/1204736/html/HTML%20REPORT/index.html`,200,text/html; charset=utf-8,`inline;filename*=UTF-8''index.html`,单跳,Download=false | `run.json:28`,`:30`,`:32`,`:33`,`:36`;`02.response.html` |
| zlib/armv7l日志 | NOT_READ;没有请求或正文,Content-Type/Download/跳转未知 | `run.json:49`请求清单;`report-structure.json` |

原iframe属性值仍为`/download/1204736/html/HTML REPORT/index.html`
(`01.response.html:803`);本次首次确认实际请求为%20形式,不是离线推算。
前六页没有重复读取,其已取事实仍沿用live-02。

## 2. 首个停止原因与附加安全停止

`capture.mjs:120`的logLink要求zlib行中的链接具有class token `failed`,
然后按armv7l/zlib.txt后缀过滤。实测Details表为四列:
`name | standard armv7l | standard aarch64 | standard x86_64`
(`02.response.html:47`),zlib行恰好一行(`:1596`),主架构链接恰好一个:

```html
<td><a href="logfiles/standard/armv7l/zlib.txt">failed</a></td>
```

来源`02.response.html:1597`;另两架构链接在`:1598`、`:1599`。
三个链接均没有class属性,失败由链接文字`failed`表示。因此当前class匹配得到0,
触发CAPTURE_LOG_LINK_MISMATCH(`run.json:113`),并非zlib不存在或armv7l链接不唯一。
`live-04/inspect_report.py`只读已脱敏归档,输出`report-structure.json`:
zlib行=1、class匹配=0、armv7l href=1、日志请求=0。没有为验证候选而联网。

stderr先记录CAPTURE_LOG_LINK_MISMATCH,后记录
`QB_AGENT_STOPPED category=FETCH_CONTINUE_FAILED`。trace另有:

```json
{"action":"OPERATION_FAILED","operation":"Fetch.continueResponse","phase":"idle","stage":"response","path":"<other>","generation":5,"category":"REQUEST_ID_INVALID"}
```

来源`run.json:205`与`:214`。该操作不属于R-04/RESTORE-10的豁免,按原规则停止正确。
它记录在已完成两页读取、工具因链接匹配失败退出的过程中;trace没有独立时间戳,
不能进一步断言是浏览器关闭导致,也不把它当作日志链接失配的根因。
本轮不改停止逻辑、不扩大豁免、不重跑。

## 3. 脱敏与清理

RESTORE-16流程成功:浏览器关闭后才离线归档两页。
Welcome区域1,登记身份1,替换次数共1(两页分别1/0),已登记身份残留均0;
整个discovery-capture目录由同一worker身份上下文扫描后才删除私有原文。
见`run.json:17`、`:38`、`:221`。本次没有脱敏阶段失败码。
PAGE_CLOSED=78863ms,BROWSER_DISCONNECTED=78988ms,profile_removed=true;
私有run `capture-r339m3f1`删除成功(`run.json:219`,`:226`)。
原文、登录身份、账号密码/Cookie未进入提交;后验清理/逐文件检查见`live-04/validation.json`。
不从已删除原文恢复身份,后验凭据检查不冒称为重建了本次身份集合。

## 4. 四条件与停点

- iframe同源HTTPS:已证实;日志href离线解析为同源,但日志未请求,不能当作响应证据。
- 307/308与异源302:已读两页均无;日志链仍UNKNOWN。
- 纯文本日志且无Download:NOT_COLLECTED。
- 实际路径:iframe wire path符合批准规则;日志href形态符合候选,但最终响应未知。

四项事实没有全部取得,且出现未豁免的安全停止。按RESTORE-08第三.2、
RESTORE-10第五条与RESTORE-16第三.2停止,不进入正式campaign-discover与第四批。

## 5. 候选处理(仅建议,未实施)

1. 取证工具改用本次四列表头定位主架构列,要求唯一zlib行、该列唯一普通链接,
   链接文字恰为failed;仍按exactLink解析与armv7l/zlib.txt精确路径核验。
   不保留未经取证的class兜底,不因其它架构也失败而判歧义。
   补归档形态夹具正例与表头缺/重、zlib缺/重、主列缺/双链接、文字非failed、
   外站/跨构建/其它包或架构负例;服务器仅收到获准主架构一次请求。
2. continueResponse的安全规则保持不变。若需细分此次附加停止,另行授权在本机
   复现关闭窗口与待处理响应竞争,补固定事件时间信息,再由设计方决定处理;
   不直接推广continueRequest的例外。
3. 补证需新的设计方执行裁定。本轮没有再弹窗,没有自行修工具后重跑。

本轮设计检查0 problem、离线摘录脚本ruff通过。diff检查仅两份响应HTML原始空白
476项警告,不改写字节;非HTML检查exit0,见`live-04/diff-check.json`。
生产与既有工具/测试530份源码hash保持门禁树一致,本轮没有重跑全仓。
