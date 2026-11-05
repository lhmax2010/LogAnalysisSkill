# SKEL-RESTORE-19:发现入口复用QB驱动与同层独立契约冲突

日期:2026-11-05。基线79cbe9f。按RESTORE-18第五.3停止,没有真机操作。

## 1. 相互约束

- RESTORE-01第〇.2:包分层与import-linter合约不放宽。
- RESTORE-01第三.2.a/b:入口为`python -m tizen_campaign_intake campaign-discover`,
  登录复用`tizen_qb_verify`浏览器代理;RESTORE-18第二条继续该接口。
- [骨架冻结稿§4.3](../../../../campaign-skeleton-design-v1.3-FROZEN.md):
  intake与qb-verify同层,明确“同层各包之间互不依赖”,新增跨包依赖须书面裁定。
- `.importlinter:31`用`|`声明独立同层,不是可互相导入的`:`。
- 已有生产驱动为`tizen-qb-verify/scripts/tizen_qb_verify/qb_browser.py:346`的
  `QbBrowser`;脱敏位于同包`qb_redact.py:203,388`。
  该包现有`__main__.py`只提供qb-trigger和qb-result-fetch,没有可复用的只读会话CLI。

RESTORE-08/18批准了网络精确表及正文读取范围,没有明确撤销同层独立约束。
这里的冲突是直接复用实现接口与依赖合约,不是日志响应缺失,不需要继续真机取证。

## 2. 离线证据

运行`batch3/r18/probe_dependencies.py`,读取当前完整root_packages及root-layers配置,
直接调用已安装import-linter的`LayersContract.check`。
每次新建依赖图,仅在内存中加一个拟议模块和一条import边,不在仓内临时修改生产文件。

| 内存图 | 实测 |
| --- | --- |
| 原图 | kept=true |
| + intake.campaign_discover → qb_verify.qb_browser | kept=false |
| + intake.campaign_discover → qb_verify.qb_config | kept=false |
| + intake.campaign_discover → qb_verify.qb_redact | kept=false |

三项负例均为`tizen_campaign_intake is not allowed to import tizen_qb_verify`的
同层违规路径,详见[probe.json](batch3/r18/probe.json)。558个已跟踪源码/冻结稿/合约文件
前后hash一致。实际合约全量检查与文档检查输出见[validation.json](batch3/r18/validation.json)。
探针4项通过不等于新增功能4项通过;本轮没有新增业务用例或运行全仓门禁。

## 3. 候选裁定(均未实施)

### A. 准许发现适配模块的精确依赖例外

候选文字diff:

```diff
- 恢复任务的包分层与import-linter合约不放宽。
+ 除发现适配模块tizen_campaign_intake.campaign_discover可直接复用
+ tizen_qb_verify.qb_browser、qb_config、qb_redact外,分层与合约不变。
+ 仅为上述三个精确模块边增加root-layers ignore_imports,
+ unmatched_ignore_imports_alerting=error保持不变;未实际使用的边不登记。
+ 其它intake模块及其它执行包对qb-verify仍禁止;反向依赖仍禁止。
```

副作用:这是一次明确的同层依赖例外,不能宣称原合约逐字不变。
优点是复用现有驱动超时、关闭、协议错误分类与脱敏,避免双份实现。
发现专用解析可放intake,不再为复用解析而增加其它跨包依赖;代理仍在原包。
测试需加:实际使用的精确边绿例;其它intake模块→qb_browser、发现模块→qb_trigger、
qb_result_fetch、反向qb_verify→intake的红例;CLI离线全链与干净wheel入口检查。

### B. 准许独立只读桥接入口,维持Python静态合约

候选文字diff:

```diff
+ campaign-discover不得直接导入qb-verify;批准qb-verify提供只读会话桥接入口,
+ intake以固定argv调用。桥接复用QbBrowser,只接受登录、已核验发现链读取、关闭,
+ 不提供open_form/fill/submit,不接受任意URL或可执行模块参数。
+ 在subprocess-boundaries中登记该跨包运行时依赖;设计方补定桥接请求/应答schema、
+ 超时/退出分类、日志落盘所有权和父进程中止时的浏览器清理契约后实施。
```

副作用:静态合约仍绿,但新增运行时依赖和一层进程生命周期,不是“无依赖”;
协议、关闭和凭据隔离的测试面增加。当前缺少此接口契约,本轮不自行发明。
需新增:协议非白名单命令/字段拒绝、损坏应答与超时、管道EOF、父进程终止清理、
精确路径来源不可注入、stdout/trace敏感值扫描、打包后的桥接可用性测试。

不选择复制QbBrowser/脱敏代码、动态导入躲检查或把整个层的`|`替换为`:`。
建议裁定A的窄例外,保留其余依赖红例。若要求绝对保持同层独立,需裁定B的接口。

## 4. 停止范围

RESTORE-18已登记;RESTORE-17的链接形态/未知日志响应停点由其处置。
本轮仅文档与离线依赖探针,未改生产代码、代理、测试断言、冻结稿、.importlinter,
未执行真实campaign-discover、QB/Gerrit/gbs。恢复第3/4批未完成,不宣称验收通过。
