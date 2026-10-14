# C5a 离线验收索引

基线39e4bde。本目录不含真实QuickBuild/Gerrit请求,不含浏览器凭据或测试私钥。
权威v1.5-FROZEN、design.md、生产代码全部零diff。C5a不代替C5b/C6真机验收。

## 门禁与覆盖

- [第9.3节16项逐条对照](coverage.md):旧提交、测试位置、本轮结果与实收路径。
- [最终机械对账](audit.json):pytest通过/失败/跳过、集合新增/删除、四模式请求数、
  一次提交、十二字段零action放行、冻结哈希、生产零diff。
- [四组安全](safety.json):从最终pytest原文抽取,包括实际收到的每个请求、trace、
  Worker关闭分支与清理结果。不是只记录测试名称。
- full-02/pytest.log、pytest.xml、commands.json:最终全量及Node实跑原文。
- tools-02/:mypy、lint-imports、design.md检查器原文与命令/exit。
- ruff-02/:完整待提交树导出后Ruff检查。忽略主工作树中未纳入提交的用户草稿,
  不删除、不修改这些草稿。

从仓库根复跑,标签必须未存在,防止覆盖旧证据:

```bash
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C5a/run_validation.py recheck-full full
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C5a/run_validation.py recheck-tools tools
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C5a/run_validation.py recheck-ruff ruff
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C5a/audit.py
```

最后一条只对本次full-02归档重新核对。pytest集成测试沿用Node/Chromium不可用时
明确skip的规则;本机本轮全部浏览器入口必须passed,不以skip冒充。唯一既有skip
为大小写不敏感文件系统的平台用例。JUnit中的合成凭据字符串是既有负例nodeid,
不是浏览器协议/凭据泄漏;页面、协议、trace与服务器清单不含合成登录密码。

## 真实CLI链路

测试:tests/unit/test_p5q_c5a_integration.py:23,模式build。
真实Python模块CLI、生产驱动/Agent,仅Node可执行文件配置指向tests入口以注入
本地证书/DNS及模拟人工登录。Agent.login本身仍不点击、不输入。
状态库与本地裸库为每例新建,完整走远端绑定、提交意图、BUILD_BOUND、读取落库。

证据均在full-02/artifacts/:

| 模式 | 实际链路 | 证据 |
|---|---|---|
| build | 一次提交,记住Variables的裸地址落点build,绑定,Running/PENDING,Successful/PASS及RESULT | build/commands.json、server-requests.json、agent-0/1/2.json、state-facts.json、result.json、qb_evidence/ |
| error-created | 创建一次后错误表单,unknown,再次CLI already_requested | error-created/commands.json、server-requests.json、state-facts.json |
| error-no-build | 未创建但已放行,unknown,再次CLI already_requested | error-no-build/同上 |
| no-navigation | 已放行且无导航,真实60秒等待后unknown,不重提 | no-navigation/同上 |

所有模式只有1次运行表单POST。正常模式的目标行、BUILD NOTES、三架构recorder
逐字段精确断言;状态/结果文件校验可见测试源码。禁止请求未到达服务器。
本地测试生成的配置1917与构建1193467/1193469仅模拟页面身份,不是访问这些真机页面。

## 两个取证工具

| 工具 | 运行说明 | 本地结果/证据 |
|---|---|---|
| spikes/p5q_compare_raw_active.mjs | spikes/p5q_compare_raw_active.md | tools/equal:6页全字段一致;tools/insert-nav:导航只在活动文档中;tools/change-status:Summary值不同 |
| spikes/p5q_fill_rehearsal.mjs | spikes/p5q_fill_rehearsal.md | tools/rehearsal/run.json:12字段、各1次获准POST、0次被拒字段POST、HTTP200、12个action版本、完整读回/指纹、not_released、action放行0 |

上表spikes路径相对docs/clang-fix-campaign。工具三种比较每页仅一次导航;
raw/active两份均由生产惰性脱敏后写入,写前/后均经过Python原始字节自检。
不保存未脱敏原始响应。身份计数分列,演练配置页/表单各版本也计数并写trace。
tools/server-requests.json为这一组全部实收,包含刻意制造的安全反例;
不要将反例的期望拒绝误报为工具正常链路失败。

## 历史与边界

focused-01开发轮18 passed/1 failed保留原文,修正的是新测试的父变量行数断言和
decode_response必需参数,不是生产规则。full-01全量2638 passed/1 skipped保留,
之后补工具每页身份计数并全量重跑为full-02;最终以full-02为准。
tools-01/ruff-01为较早工具门禁,tools-02/ruff-02是最终版本。

本轮无生产变更,没有新的规格停点。C5b需要另行授权与人工登录;两个工具说明中
的真机命令本轮均未执行。第1.6a/c真机验证、成功样本、BUILD_NOTES样本、C6真实
提交均保持挂账,P5Q不得标CLOSED。
