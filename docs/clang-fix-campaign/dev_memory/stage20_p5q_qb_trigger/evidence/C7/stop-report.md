# P5Q-C7-02:read 的 CDP 等待预算与限定修改范围无法同时落实

状态:STOPPED,待设计方裁定。日期:2026-10-21。基线:48b0aa9。
本报告是离线规格核对,不是一次真实QuickBuild故障,不声称已经完成C7。

## 1. 冲突条款

- v1.8-FROZEN第3.2节:259要求导航显式30000毫秒,同时保证
  `read`路径上没有其它可超过该值的等待。第9.2节:949要求预算静态断言。
- 本轮任务第二步第4项只允许代理改两处:导航timeout和登录提示;
  Policy、installGuards及其之前的源码前缀须与48b0aa9逐字节一致。
- 只加导航timeout不覆盖导航结束后的CDP调用。Python的60秒总应答上限
  可以在60秒终止代理,但不能证明这些代理等待本身不超过30秒。

## 2. 代码事实

`tizen-ci-triage/scripts/ci_triage/qb_browser_agent.mjs`:

| 位置 | 等待 |
|---|---|
| :361 | context.newCDPSession |
| :362 | session.send('Page.getFrameTree') |
| :363 | session.send('Page.createIsolatedWorld') |
| :373 | session.send('Runtime.evaluate'),也没有Runtime.evaluate的timeout参数 |
| :382 | finally中的session.detach |
| :725 | Agent.read在goto之后调用上述TrustedPage.run |

这些调用均未设置本地截止点或超时包装。给TrustedPage或Agent.read增加额外
预算包装都会超出仅两处改动的授权。此冲突不依赖对前缀末端的解释:
即便仅保留到installGuards结束,仍需要批准第三处代理改动。
本轮字节核对沿用更强范围,取Agent类之前的全部源码(其中包含TrustedPage)。
不能把导航timeout当作CDP调用timeout。

本机Playwright 1.58.2源码佐证(只读本地安装,未联网):
`/home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/lib/client/cdpSession.js:42`
的send直接等待channel.send;`lib/server/chromium/crConnection.js:106`的CRSession.send
创建Promise并把resolve/reject存入_callbacks,没有30秒计时器;
CDPSession.send(:174)直接转发到该会话。因此不能假定框架会自动补上30秒预算。

## 3. 可复现探针

命令:

```text
/home/linhao/.local/bin/node docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C7/probe-read-budget.mjs
```

探针从不可变`git show 48b0aa9:.../qb_browser_agent.mjs`导入生产Agent,
仅在内存中添加已批准的`goto(..., { timeout: 30000 })`。
导航立即成功;分别把上表五个异步应答延后。实际执行Agent.read,
不是只对函数源码作文字判断。31秒后记录是否仍pending,再释放应答清理所有Promise。
所有输入均为合成数据,无账号、密码、Cookie;没有浏览器、网络、数据库写入。

首次观察:31010毫秒时五项全部pending;释放后五项全部read_returned。
可复跑归档见`budget-probe.stdout.json`与`checks.json`(记录该次精确毫秒、argv、UTC起止、exit)。
探针exit=1表示上述30秒契约不成立,不是项目已有测试回归。
释放后全部正常返回是正控制,证明不是调用路径本身出错导致的假阳性。

## 4. 候选处理(未实施)

1. 收敛本条的预算表述:明确30000只约束导航,CDP无单独代理预算作为具名残余,
   仍由Python的60秒应答上限终止。优点是不扩大代理改动面;代价是放弃
   “代理其它等待均不超过30秒”的保证,须设计方明确接受,不能由实现方自行解释。
2. 保留严格代理预算,额外授权read后续可信读取与清理的超时实现,并规定
   超时错误码、迟到应答处理与清理上限。可在read边界包装或调整TrustedPage;
   两者均超出两处改动清单,并须明确前缀核对的末端。Policy/installGuards
   不应放宽;须补五个挂起点的控制,再重跑全部门禁与四个安全组。

不擅自选择上述任一方案,不修改v1.8。其余C7自动查找/绑定和C8均停止。

## 5. 本轮交付边界

登记v1.8权威与该停点,提交探针及结果。发现停点前尝试的驱动/代理和design.md
同步改动全部撤回至本轮基线,未作为实现交付;不动用户原有其它工作树改动。
最终生产代码与design.md均与48b0aa9一致。不保留未验收的生产半成品。

代理完整SHA256=c13413a3f46398fa0cf594f483ec25a210e4a9ec369bfdb989ff7a76fa70c913。
以`export class Agent {`为末端(不含该行)的前缀SHA256=
40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16。
该范围包含Policy、installGuards及TrustedPage,比只核对installGuards之前更强。
最终前后实算、冻结稿和专用状态库hash见checks.json。

预算探针、既有源码静态护栏(含负例)、design.md检查器在本轮实际执行。
因按纪律停止且最终没有生产改动,未运行全量pytest/mypy/ruff/lint-imports、
完整Node/DOM/HTTPS集成和四个安全组;不得据旧结果宣称C7门禁通过。
