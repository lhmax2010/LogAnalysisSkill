# P5Q-C2A-02 request-boundary probes

日期:2026-10-12。基线d1f09cc,冻结稿sha256保持
`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`。
本报告是能力前置的实测,不是C2a完成验收。h的引用结果未取得,停止继续生产实现。
未重跑“暂停后关闭”旧探针,未访问QuickBuild/Gerrit/外网,未读取凭据。

## 1. 运行方式

本机Node为VS Code内嵌Node 24.21.0,Playwright 1.58.2,Chromium 145.0.7632.6。
仅监听127.0.0.1的HTTP/HTTPS服务器;HTTPS使用现场生成的一日测试证书,
只将该证书SPKI加入测试启动参数,没有设置ignoreHTTPSErrors。
真实生产启动器仍未交付,不把内嵌Node记作生产依赖已解决。

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code --check tests/node/p5q_request_boundary_probe.mjs
# exit=0, stdout为空

# a-h集合;当时脚本版本已由下方源文件快照重建归档。
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code tests/node/p5q_request_boundary_probe.mjs /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome
# exit=1, request-boundary-cached-frames.log

# h取证修正:改为普通同源页面,另加无防护h对照;不修改关闭时机或断言。
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code tests/node/p5q_request_boundary_probe.mjs /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome h
# exit=1, request-boundary-h-observation.log
```

命令实际经`bash -o pipefail`与`tee`归档,保持Node退出码。
日志摘要中的`externalRequests:0`是脚本静态写入的运行范围声明,不是独立抓包计数,
不作为外网请求测量证据。攻击HTTP与WS计数则均来自本地服务器实际接收事件。
第一条整组执行对应[request-boundary-cached-frames.mjs](request-boundary-cached-frames.mjs):
该快照由最终脚本逆向撤销仅h夹具与单项选择器的编辑重建,不是声称运行前已取hash。
sha256=`b3c95ca80b2ef0a1cacd1c029c8802f6ad21335c997beff9a40b5d816bd5e66c`。
最终脚本`tests/node/p5q_request_boundary_probe.mjs`的sha256=
`e6c36f894b34ec590fa846c68bfede7fb1fa5cd52ce6090de16be5c26e444ef6`。

## 2. 三个拦截面与帧归属

- HTTP主层:在`browser.newBrowserCDPSession()`上安装`Fetch.enable`,同时登记
  Request/Response两个阶段。`Fetch.requestPaused`先转为不带请求头/体的元数据;
  未归属帧拒绝,响应307/308拒绝;用`Fetch.failRequest`、`Fetch.continueRequest`、
  `Fetch.continueResponse`落实。没有页面级Fetch作为替代。
- 归属:导航前在工作页CDP会话调用`Page.enable`/`Page.getFrameTree`,建立frameId集合;
  `Page.frameAttached`只接纳已知父帧,`frameDetached`递归删除,
  `frameNavigated`更新工作页与后代。请求frameId缺失或不在集合时直接拒绝。
  无法从请求URL或实际是否到达服务器反推归属。
- WebSocket:`BrowserContext.routeWebSocket('**/*', route => route.close())`,页面创建前安装。
- 新目标:`Target.setDiscoverTargets`检测到非工作page立即`browser.close()`并标记
  `QB_BROWSER_UNAVAILABLE`;`Target.setAutoAttach`与另一会话上的
  `Target.autoAttachRelated`均`waitForDebuggerOnStart=true`,Worker从不恢复,
  `Target.closeTarget`失败则关闭浏览器。
- Chromium启动参数`--block-new-web-contents`;移除Playwright默认的
  `--disable-popup-blocking`;`BrowserContext.addInitScript`中用不可写、不可配置的
  `Object.defineProperty`令window.open恒null。启动参数与页面描述符均有实读结果。

本次获准的工作页请求在两个Fetch阶段均有记录。新page的请求被关闭抢先终止,
不把未出现的跨帧Fetch事件声称为归属负控已覆盖;完整归属负控与307/308专项矩阵
尚未运行。此前浏览器Fetch覆盖弹窗/Worker/SharedWorker的3/3证据保留在
`creation-probe-layered.log`,本轮不伪称重新完成该附带矩阵。

## 3. a-h结果

计数仅指探针攻击请求;夹具导航和favicon正常请求逐条保留在日志,不冒称全进程请求0。

| 探针 | 攻击HTTP | WS握手 | 新page | 浏览器关闭/固定错误 | 判定 |
|---|---:|---:|---:|---|---|
| a window.open同源页 | 0 | 0 | 0 | 无须关闭;returnedNull=true | PASS |
| b about:blank后同步写脚本 | 0 | 0 | 0 | 无须关闭;returnedNull=true | PASS |
| c _blank链接脚本点击 | 0 | 0 | 1 | closed=true / QB_BROWSER_UNAVAILABLE | PASS,按新判据 |
| d _blank表单GET提交 | 0 | 0 | 1 | closed=true / QB_BROWSER_UNAVAILABLE | PASS,按新判据 |
| e Worker fetch | 0 | 0 | 0 | waitingForDebugger=true,关闭兜底 | PASS |
| e SharedWorker fetch | 0 | 0 | 0 | waitingForDebugger=true | PASS |
| f-a去防护对照 | 2 | 0 | 1 | returnedNull=false | PASS,含文档与脚本请求 |
| f-b去防护对照 | 1 | 0 | 1 | returnedNull=false | PASS |
| g blob脚本fetch/ws/wss | 0 | 0 | 1 | closed=true / QB_BROWSER_UNAVAILABLE | PASS |
| g去防护附加对照 | 1 | 2 | 1 | ws与wss各一握手 | PASS,证明载荷有效 |
| h rel=opener,尝试引用并写脚本 | 0 | 0 | 1 | closed=true / QB_BROWSER_UNAVAILABLE | 未通过取证:引用尝试结果未回传 |

整组原始摘要:

```json
{"summary":11,"passed":10,"failed":1,"externalRequests":0}
{"certificateRemoved":true}
```

h首次使用同源blob承载名字与postMessage;后修正为普通同源页面并增加h无防护对照,
保持同样的立即关闭与引用断言。保护组仍为:

```json
{"fixtureError":"FIXTURE_INTERRUPTED","received":[],"handshakes":[],"newPageTargets":1,"referenceAttempts":[],"stopped":"QB_BROWSER_UNAVAILABLE","browserClosed":true,"profileRemoved":true}
```

无防护h对照取得以下记录并收到2个HTTP请求:

```json
{"referenceAttempts":[{"route":"window.open","obtained":false},{"route":"window.name","obtained":false},{"route":"window.frames","obtained":false},{"route":"message.source","obtained":true}]}
{"summary":2,"passed":1,"failed":1,"externalRequests":0}
```

**严格区分**:这没有证明保护组取得了引用或泄漏了请求。保护组在同步引用尝试结果
回传前就关闭,故没有“取不到引用”的独立观测;也不能把`referenceAttempts=[]`
当作引用断言通过。未为拿到观测而推迟browser.close,未删除或放宽该断言。
按本轮“g或h任一不满足即停止”要求停止后续C2a生产实现。

## 4. 调试与清理留痕

最初的`request-boundary-probe.log`不是a-h完成实跑:实现在Fetch暂停期间临时查询
`Page.getFrameTree`,查询等待导航,夹具导航失败。a/b两条setup失败后中止进程,
exit=130,未作能力否定或通过证据。改为导航前种子集合与Page事件维护后导航正常。
这次中止遗留的两个专用`/dev/shm/p5q-boundary-*`目录已按精确路径清除。
后续两轮各用例`profileRemoved=true`,证书目录删除;
最终`ls -d /dev/shm/p5q-boundary-*`为No such file or directory(exit2)。

| 原始日志 | sha256 |
|---|---|
| request-boundary-probe.log | 690745b50d4da982e45a800431ff8a2839f75834dc907f2f2184077124083811 |
| request-boundary-cached-frames.log | b4d80a7cb5408005a2ae1e628c9b2daff03ef24ef6611d0f0e6e85e7d7fe4700 |
| request-boundary-h-observation.log | 5513e044a163907711b9973b1d058554da1e687d774533516b389c3bbd7d3f77 |

完整pytest/mypy/ruff/lint-imports与代理/驱动/假代理尚未开始,不借用C1结果。
生产代码、冻结稿、design.md零改动;未进入C2b。
