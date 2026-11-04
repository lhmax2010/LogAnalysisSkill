# SKEL-RESTORE-11:iframe原始路径含空格,取证工具提前拒绝

状态:STOPPED,等待裁定。没有重试、没有访问另一构建,未进入恢复第三/四批实施。
基线`b29d6f3`已推送,RESTORE-10离线窄化与门禁已完成。

## 1. 唯一一次执行

用户对本次弹窗确认原话:“开始”。2026-11-04 14:26:36.495–14:29:46.590 UTC,
wrapper耗时190.095秒,exit 4。完整argv与输出在`live-02/command.json`、
`stdout.log`、`stderr.log`;调用原capture模块的导出函数,只替换新输出目录。
未传测试解析/证书参数,未调用运行/填表/提交,没有任何构建写操作。

前置`live-02/preflight.json`:目录原不存在,P5Q进程/profile无残留,
代理与两份冻结稿hash符合已验收值。登录ok=true(`run.json:269`)。

| 页 | 正文文件 | HTTP/导航 | 登记位置外身份计数 |
| --- | --- | --- | --- |
| /overview/1917 | `live-02/01.response.html` | 200,单跳主帧 | 0 |
| /build/1204735/overview | `live-02/02.response.html` | 200,单跳主帧 | 2 |
| /build/1204735/variables | `live-02/03.response.html` | 200,单跳主帧 | 0 |
| /build/1204736/overview | `live-02/04.response.html` | 200,单跳主帧 | 0 |
| /build/1204736/variables | `live-02/05.response.html` | 200,单跳主帧 | 0 |
| /build/1204736/html_report | `live-02/06.response.html` | 200,单跳主帧 | 0 |

以上六页Content-Type均text/html;charset=utf-8,Content-Disposition均未出现,
无Download事件,每次导航最终地址与请求一致。前五页配置/构建/父子关系核验通过。
身份计数2见`run.json:43`,需人工确认是否有新身份位置;这里不输出名称,
也不把计数当作凭据泄漏或自动脱敏范围扩展。

trace仅FRAMEWORK_SELF_TEST 1、DENIED 28(login9/read19),没有
OPERATION_FAILED、AGENT_STOPPED、CONTINUE_TARGET_GONE或DENY_TARGET_GONE。
因此本次没有复现上次continueRequest失效,不能据此宣称窄例外被真机触发验证。
子帧自动请求未登记,被拒;没有显式主帧导航到iframe或包日志。
PAGE_CLOSED=173269ms,disconnected=173794ms,profile_removed=true,
事后无P5Q进程/profile残留(`live-02/validation.json`)。

## 2. 停止位置与事实边界

`live-02/06.response.html:803`唯一iframe的属性原文:

```text
/download/1204736/html/HTML REPORT/index.html
```

`capture.mjs:23`在标准URL解析之前用`/[\x00-\x20\\]/`拒绝空格,
故`:239`调用exactLink时抛CAPTURE_PATH_UNSUPPORTED(`run.json:272`)。
这是现有取证工具的过严预检查,不是观察到异源、下载或非法编码。
工具没有改动,按RESTORE-10第五条的未豁免失败规则停止,没有现场修工具再跑。

零网络离线探针`probe-live-02-path.py`用HTMLParser读取已归档src,
分别调用标准URL解析器和原exactLink;结果在`live-02/path-probe.json`:
标准解析为`https://quickbuild.tizen.org/download/1204736/html/HTML%20REPORT/index.html`,
同源、无query/fragment;原exactLink拒绝。这个编码结果只是离线计算,
不是已观察到的iframe主帧请求或响应。

RESTORE-08第三.1的四条件尚未全部成立:

1. iframe按属性解析同源;日志地址未取得,不能完成二者同源核对。
2. 已读取六页无重定向;iframe/日志的跳转链UNKNOWN。
3. 日志Content-Type、严格UTF-8、Download行为均NOT_COLLECTED。
4. iframe实际目录名为HTML REPORT,并非历史GBS Reports多架构例子;
   日志href与实际wire path未取得,不能补猜文法。

## 3. 候选处理(不实施)

建议设计方授权仅取证工具接受上一层唯一src中的路径段内ASCII空格:
保留控制字符/反斜线/穿越/编码分隔符拒绝,仍拒绝首尾空白,
使用标准URL解析一次后核对同源、无用户信息/query/fragment、构建号,
将解析后的精确URL登记为当前唯一主帧读取地址。示意文字diff:

```diff
- /[\x00-\x20\\]/.test(href)
+ /[\x00-\x1f\x7f\\]/.test(href) || href !== href.trim()
```

这只描述候选预检查变化,不是已应用的patch;生产代理与精确表不改,
不开放目录前缀或任意/download。HTML REPORT页是否含目标日志必须另次取证,
不能把旧GBS Reports夹具拼接为替代地址。
需补离线用例:字面空格/等价%20的唯一src正例,首尾空白/控制字符/反斜线/
穿越/编码分隔符/跨构建/外站/query/fragment负例,以及服务器只收到登记的一次主帧请求。
设计方批准且用户在场后才可另行授权读取未完成两跳;本轮不执行。

## 4. 交付检查

六页由同一个PageRedactor内存上下文写前写后检查,归档后再逐文件自检,
正文hash与run.json逐项相同。`validation.json`同时证明live-01、capture工具
和生产代理相对b29d6f3逐字节未变。此次仅新增脱敏证据、离线探针与文档,
不重跑业务命令,不把第三批发现功能标成完成。
说明文档与离线探针diff检查通过;原始脱敏HTML的行尾空白不作格式清理。
