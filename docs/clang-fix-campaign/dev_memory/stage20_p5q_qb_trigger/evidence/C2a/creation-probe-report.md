# P5Q-C2A-01 裁定后新探针

日期:2026-10-10。基线:`d1f09cc`。本轮只执行新探针,未复跑旧的暂停后关闭探针。
批准的裁定已原意登记在stage20 progress §12,无需再批准该裁定。

## 命令与完整原始输出

```bash
env -u LD_LIBRARY_PATH -u LD_PRELOAD -u GTK_PATH -u GIO_MODULE_DIR \
  -u DEBUG -u PWDEBUG -u QB_COOKIE -u QB_PASSWORD ELECTRON_RUN_AS_NODE=1 \
  /snap/code/current/usr/share/code/code \
  tests/node/p5q_creation_probe.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome
```

stdout通过`bash -o pipefail`下的`tee`归档于
[creation-probe-layered.log](creation-probe-layered.log),命令exit=1。
Node为本机VS Code内置Node模式24.21.0,Playwright为已有1.58.2,
Chromium为145.0.7632.6,有界面模式。没有下载或更换运行时。

- 探针sha256:`36871cc69ed76312bc319a2bc86825b9832a04e7deb316419524950fba07ec6e`。
- 最终日志sha256:`f9409392f07bec2bb496399ec4763c5e162e970a69ba94a52e43f48da6998595`。
- 冻结稿sha256仍为`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`。

## 已装机制与证实方式

1. `--block-new-web-contents`:不只检查构造参数,用浏览器级
   `Browser.getBrowserCommandLine`实测其确实存在。
2. `BrowserContext.addInitScript`在创建主页面与首个导航之前登记;
   `Object.defineProperty(window, 'open', ...)`恒返回null,
   `writable=false`且`configurable=false`。在每个场景的页面中再次读取描述符。
3. 两个独立浏览器级CDP会话分别执行`Target.setAutoAttach`及
   `Target.autoAttachRelated`,均`waitForDebuggerOnStart=true`、`flatten=true`。
   shared_worker由前者接收,dedicated worker由后者接收;不恢复Worker。
   暂停的Worker调用`Target.closeTarget`,失败则关闭整个浏览器。
4. `Target.setDiscoverTargets`统计主页面之外的page target;一旦出现,
   调用`browser.close()`关闭整个浏览器,记录`UNEXPECTED_PAGE_CLOSE_BROWSER`。
   这是失败处置,不将其计作“禁止创建”通过。
5. 附带探针证实浏览器级`Fetch.enable`有效后,将其请求阶段拦截也加入保护组:
   `Fetch.requestPaused`提取requestId/path/resourceType元数据,
   `Fetch.failRequest(BlockedByClient)`拒绝目标请求;
   `Fetch.continueRequest`只放行本地fixture及其普通资源。
6. `BrowserContext.routeWebSocket`安装拒绝路由。本轮没有运行WebSocket专项用例,
   不能据此宣布整个WebSocket验收通过。

首次组合保留了Playwright默认`--disable-popup-blocking`,c/d失败。
为排除反向默认参数影响,最终组合用`ignoreDefaultArgs`移除该项,
实际命令行显示`disablePopupBlocking=false`;c/d仍失败。未增加新的DOM拦截或
把target改写为其它目标,未降低“零新页面目标”断言。

## 逐项结果

表中请求数仅为攻击/目标端点`/probe/...`的实收数。fixture导航与favicon是
正常准备请求,分别完整记在日志的`setupRequests`与`actualRequests`中,
不能把正常导航说成零网络请求。

| 项目 | 本地合成操作 | 服务器目标请求数 | 新page target数 | 结果 |
|---|---|---:|---:|---|
| a | window.open打开同源普通页面 | 0 | 0 | PASS,返回null |
| b | window.open about:blank后同步document.write脚本fetch | 0 | 0 | PASS,返回null故无法写入 |
| c | 创建target=_blank链接,脚本click | 0 | 1 | FAIL,关闭整个浏览器 |
| d | 创建target=_blank表单,脚本submit(GET) | 0 | 1 | FAIL,关闭整个浏览器 |
| e-worker | Blob Worker脚本fetch | 0 | 0 | PASS,观测到worker等待调试器 |
| e-shared | Blob SharedWorker脚本fetch | 0 | 0 | PASS,观测到shared_worker等待调试器 |
| f-a | 无窗口防护的a正向对照 | 1 | 1 | PASS,服务器实际收到GET /probe/a |
| f-b | 无窗口防护的b正向对照 | 1 | 1 | PASS,服务器实际收到GET /probe/b |

汇总原文:`{"summary":8,"passed":6,"failed":2}`。每项均清理临时目录。
正向对照采用观察模式:不传block参数、不注入window.open替换,也不以其它
失败即关闭/Fetch拒绝机制掩盖其请求,以验证夹具确实能产生新页面与服务器实收。
两组均移除了反向默认参数;日志记录了每个场景的真实启动布尔值与属性描述符。

## 浏览器级Fetch附带探针

在单独无窗口防护的浏览器中启用浏览器级CDP `Fetch.enable`请求阶段拦截,
只阻断`/probe/...`,放行fixture。结果:

| 来源 | Fetch.requestPaused实测 | 服务器收到目标请求 | 结果 |
|---|---|---|---|
| 新弹窗Document | /probe/browser-popup | 否 | 覆盖 |
| Worker XHR/fetch | /probe/browser-worker | 否 | 覆盖 |
| SharedWorker XHR/fetch | /probe/browser-shared | 否 | 覆盖 |

三个`Fetch.failRequest`均成功;fixture和favicon正常到达服务器,
因此不是“所有请求都没发出来”的伪绿。该层已加入最终保护组。
这只证明请求阶段的上述三个场景,不代替307/308响应阶段与逐跳重定向验收。
Fetch可以补充网络边界,不能把已经出现的page target变成未创建。

## 调试记录与边界

- `creation-probe-initial.log`:exit2,探针的DNS全拒规则未豁免loopback,
  没有有效场景结果;已改为EXCLUDE 127.0.0.1,不放开任何外站。
- `creation-probe-final.log`、`creation-probe-startup-verified.log`:早期新组合结果,
  仍含反向默认参数,不作为最终组合记录。
- `creation-probe-no-default-disable.log`:在加入浏览器级Fetch前,SharedWorker
  有一次请求到达服务器,即使附带waitingForDebugger=true;该失败保留原文,
  不声称仅依赖Target暂停便已稳定满足所有Worker网络边界。
- 最终裁定要求的额外Fetch层加入后,采用`creation-probe-layered.log`作为
  当前组合结果;c/d仍然失败,故停止,不继续代理生产实现。
- 假服务器仅监听127.0.0.1,测试仅使用该随机端口与内存Blob。
  无QuickBuild/Gerrit/外网请求,无真实凭据,没有改冻结稿。
- JS语法检查exit0;`/dev/shm/p5q-creation-probe-*`剩余目录数为0。
  未运行全仓pytest/mypy/ruff/lint-imports,未写Python驱动/假代理;
  不把本探针计作完整C2a验收。

## 新停止条目 P5Q-C2A-02

已批准机制在本机仍允许原生target=_blank链接/表单创建page target。
该事实不依赖旧探针,也不要求重复确认P5Q-C2A-01裁定。
按新任务a-e任一失败即停的约定,停止并提交本地记录供设计方判断原生创建
路径的下一步处置;没有以关闭整个浏览器或网络拦截成功替代“未创建”。
C2a未通过,本轮未提交/推送完成commit,未进入C2b。
