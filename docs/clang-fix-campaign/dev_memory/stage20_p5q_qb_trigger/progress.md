# Stage20 P5Q QuickBuild Trigger

日期:2026-10-21。状态:**C7 ACCEPTED,C8 PREPARED_WAITING_CONFIRMATION,当前权威 v1.8-FROZEN**。P5Q不标CLOSED。
本轮裁定、离线小修与C8准备见§49。新的十二字段确认前不访问QuickBuild,不复用旧提交授权。
本轮冻结登记与离线实现见§47;以下C6及旧权威记录保留为历史。
最新执行见§45–46/P5Q-C6B-01:终态重读exit0、RESULT仍为3、专用库逐字节不变;
成功父1201886/子1201889及配置1917的五页50项比对一致,身份计数均0。
成功样本与BUILD_NOTES样本挂账已CLOSED,第9.4节第2步真实提交已完成(1201886)。
关闭尾段0.213秒;v1.6自动绑定、验证性提交、历史登录超时原因仍开放。
以下旧轮次概述保留作历史,以§45–46和第5节最新台账为当前状态。
本轮见§41/P5Q-C6A-04与§42:关闭后退出问题由设计方判为已知缺陷,修复后置;
live-04已获新“确认提交”,当场核对通过后仅执行一次;login超时停止,见§42.4。
live-04停止后未重试、未运行fetch或进入C6b。
最新续执行见§43:FatTank再次明确确认,live-05单独记账,不覆盖live-04;
一次trigger返回QB_SUBMIT_UNCERTAIN,已写提交意图;先前“未找到”记录保留于§43.5。
FatTank随后提供1201886,见§43.6;一次生产fetch人工绑定及首次读取exit0,
子构建1201889已为PASS,落库SANDBOX_QB_PASS,见§43.7–43.9。未重提、未修代码,
不再fetch、不进入C6b或标P5Q CLOSED。
§38–40保留历史,不复用其中的授权或将其结果改写为本轮结果。
最新续任务见§39.4–39.5:live-02记录进程遇本地磁盘同步阻塞后终止,未取得生产返回;
专用库hash未变、无残留进程。FatTank再次要求弹窗并新回复“确认提交”,仅授权live-03一次;
live-03已返回exit5/QB_BROWSER_UNAVAILABLE,登录调用已返回但意图未落库,具体代理失败阶段未知。
上一轮C6a见§37–38:libtirpc目标已确认,manifest/专用库/本地镜像/离线前置核验完成;
FatTank已回复“确认提交”;仅运行一次生产qb-trigger,exit5/QB_LOGIN_TIMEOUT,
无request_id/构建号、无库变更,立即停止,未运行qb-result-fetch,见§38.6–38.8。
C5a基线39e4bde,离线集成与第1.6步工具见§34。C5b基线b134d16,六页原始/活动比对通过;
填表演练exit1且未落盘阶段证据,见§35。C6a live-03登录调用已返回,无提交意图落库或构建号;
成功/BUILD_NOTES样本挂账开放。
§36按P5Q-C5B-02完成工具失败落盘及离线验证:2639 passed/1 skipped;
5afb645推送后FatTank回复“沿用。开始”,fill-rehearsal-02一次实跑通过,
12字段各1获准/0拒绝/HTTP200,not_released/action放行0,见§36.6–36.9。
以下各轮“不进入下一阶段”只约束当轮,均保留为历史记录;§36轮次止于C5b,
§38的停止为live-01历史事实,续任务按§39处理;旧确认仍不授权重跑。
C4最新裁定与执行见§33;§32停点已由P5Q-C4-02关闭。
C4本轮基线ec3be74;源格式对齐要求已撤回,旧探针作废,实现与验收见§33。
C4本轮不访问真实QuickBuild/Gerrit,不弹登录窗口,不进入C5。
C3本轮基线7f3c60e;实施与验收见§31。§29的C3-01由C3-02关闭,
§30的C3-03由C3-04关闭。以下“不进入C3”与STOPPED为先前轮次的历史记录。
上述C3边界为历史记录;C5/C6真机挂账仍开放。
最新权威改为v1.5-FROZEN,冻结登记与C2c执行见§27;以下v1.2及R1待决状态均为历史记录。
§27.3历史停止已由§28的C2C-03关闭;本轮C2c执行见§28。最近真机执行见§26:生产2ee8ab6、取证19792bb已推送;新“开始”后完成live-12,
五个构建页/配置通过,Full→Partial→Full联动成功,release0。以下停点均为历史事实。
现场取证成功不等于R1设计差异已关闭,不进入C3。
当前轮基线540b316;P5Q-C2B-06裁定及实施见§22。§18至§21保留历史停点。
身份脱敏与取证入口已分别推送6028356/47a1f8e;live-04在子主页构建号核对停下,
§21只补取证通道;本轮§22按批准裁定修正read/openForm并跟进取证路径。
live-05的启动错误见§21.5;
live-06已完成ping/pong与一次人工登录,七页归档(两页ID_UNVERIFIED),配置1917
五项/两项检查通过;form_evidence的open_form返回QB_FORM_CHANGED后立即停止,
release=0,未设值/未提交,见§21.9。live-07收到新的聊天开始并完成ping/pong,
等待600秒后QB_LOGIN_TIMEOUT;登录POST=0、归档构建页=0,见§22.6。
live-07原样保留。live-08登录及五个构建页核对通过,配置登记的sibling_tabs
精确相对路径检查失败,见§22.8。§23按P5Q-C2B-07裁定修正取证URL解析;
live-08原始证据保留,生产与冻结稿不改。live-09在b9b4d71后收到新的聊天“开始”,
完成ping/pong与登录、五个构建页核对、配置1917五项/两项核对;
open_form导航到表单后QB_FORM_CHANGED,立即停止,release=0,见§23.5。不标C2b完成。
§24按P5Q-C2B-08增加spikes表单失败只读取证,284c5c0推送后收到新的聊天“开始”,
live-10完成五个构建页与配置1917五项/两项核对,表单首失败点为PROJECT_NAME精确值不等;
已归档form_unverified页及逐条件诊断,无字段差集/重复,release=0,见§24.6。
不改变生产规则,不将历史推测当成live-10实测;C2b仍未完成。
§25按已批准C2B-09裁定修正页面主环境字符串规整,分生产/取证脚本两提交;
生产修正4a4a727已推送,spikes跟进与九项原生布尔记录离线验收通过;
cbedcf5推送后收到新的聊天“开始”,live-11已按顺序取证:五个构建页与配置通过,
初始表单通过;Full→Partial实际XHR POST附带random,被精确地址规则拒绝,
等待结束后QB_FORM_CHANGED,诊断并清理,release=0,见§25.7/25.8。
八次原生性采样均trim=false,其余八项true。历史live-10结论原样保留。
live-03原样保留且仅作参考,不作为字段形态证据;C3不启动。
C0开工基线:`26e9e3d`;C1开工基线:`3e073bc`,分支`clang-fix-campaign`。
已读INDEX、stage15 §14及之后、stage19 §21;工作树中.gitignore和docs四个删除文件
是既有无关改动,不处理、不纳入本次交付;其余历史草稿也不纳入。

## 1. 权威与冻结哈希

本节原文为C0入库记录。当前权威已由§47更新为v1.8-FROZEN,
SHA256=d0242ca8b708e9c1e3e714387bae963f8f6f16fc765179e6ed60d8be56493364;
v1.5与v1.2原样保留备查。v1.5的原始hash见§27与§47。

权威:[p5q-qb-trigger-design-v1.2-FROZEN.md](../../p5q-qb-trigger-design-v1.2-FROZEN.md)。
FatTank放入的文件原字节保留,未修改标题、附录或其它内容。校验原文:

```text
$ sha256sum docs/clang-fix-campaign/p5q-qb-trigger-design-v1.2-FROZEN.md
0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950  docs/clang-fix-campaign/p5q-qb-trigger-design-v1.2-FROZEN.md
exit=0
```

与FatTank给定hash一致。冻结稿随本次C0原字节入库,提交由Git外部锚定,
文件内不自记本提交SHA;完整验收见§9。
冻结稿已用满两轮评审;RBS待实测位置按失败即停,不拿SBS样本代补。

## 2. 提交计划(冻结稿第10节)

| 提交 | 交付 | 依赖/当前状态 |
|---|---|---|
| C0 | 冻结稿原字节入库;附录A同步design.md v1.5.22;本stage与INDEX/移交表 | DONE @3e073bc;C0-01已落实,§9门禁全部通过 |
| C1 | qb_redact.py;配置解析;campaign_qb_profiles;四个按连接写入原语/公共API重构/qb_profile;精确表集合测试与第9.1节对应用例 | DONE;§10验收通过,本次提交由Git外部锚定 |
| C2 | qb_browser_agent.mjs三拦截面/协议适配层;qb_browser.py/假代理;第9.2节与第9.3节本机安全子集;随后第9.4节第1/1.5步、回填附录C | C2a COMPLETE;§26.6 live-12五页/配置与两次联动通过,release0;附录C补现场结果,待R1核对,无C3 |
| C2c | v1.5第10节①–⑥:隔离读取/原始字节、惰性位置脱敏/诊断、刷新删除、字段窗口/启动自检、design.md照录 | COMPLETE;§28裁定及验收;C5/C6挂账仍开放,不标P5Q CLOSED |
| C3 | qb-trigger CLI及触发/填表/崩溃/多unit/隔离传输用例 | COMPLETE @3ef542a;§31;C3-01/C3-03均已裁定关闭 |
| C4 | qb-result-fetch CLI、人工绑定及读取/落库用例 | COMPLETE @39e4bde;§33;C4-01已由C4-02关闭 |
| C5a | 第9.3节本机浏览器集成;第1.6步工具准备 | COMPLETE;§34;全部离线,2638 passed/1 skipped,四组安全4/4 |
| C5b | 第1.6步原始/活动文档比对、填表演练与样本补齐 | COMPLETE;§36.6–36.9演练及§35六页比对通过,成功/BUILD_NOTES两个样本由§45补齐并CLOSED |
| C6 | 第9.4节第2步确认的真实提交与收口文档 | C6 完成,等待 v1.6 自动绑定;§43人工绑定1201886/子1201889 PASS,§45终态重读与样本补证完成;P5Q收口尚未获准 |

C2真机取证与冻结稿假设不符时按R1修订,不得直接继续C3。
C0授权不含实现;C1/C2a已完成。本轮C2b授权浏览器人工登录、只读与BUILD_TYPE联动取证,
不授权表单提交、真实构建或C3-C6。遇到§17新增停止条件立即停止,不重试。

## 3. FatTank裁定(2026-10-10)

以下以本冻结稿第0.1/0.5节为当前口径;stage15历史事实记录不改写:

1. 复验用RBS/TRIGGER,按unit.branch区分Tizen-Base-Toolchain与Tizen-Unified-Toolchain;
   Unified表单未取证前保持关闭,不用SBS/TRIGGER替代。
2. 目标写入Build Package List,仓库路径@commit一行一个;本版每次只填唯一目标行。
   SBS_TARGET是内部旧名,sbs_target列不改名;RBS回显变量必须按第9.4节实测确定。
3. 合入正式快照由人Accept,工具永远不点Accept/Ready to Accept;
   ILinkListener-content-buildHead-promote永久禁止。
4. sandbox推送不自动触发QB,仅工具显式提交表单产生构建;
   P12首次真实sandbox推送后仍做观察,不是本轮已验证事实。
5. 独立真实浏览器按标签填表、等待联动、逐项读回再提交;不拼HTTP请求,
   每个字段显式设值,不依赖默认值;Run打开Specify Build Options,Ok才提交。
6. 登录在弹出的浏览器窗口内由FatTank完成,自动检测登录完成,无需回终端;
   取代stage15 §17的终端账号密码方案,不再要求手抄Cookie。
7. 复验基准为Ref. Snapshot,首次触发时取当时选中的SNAPSHOT_NUM,
   按campaign×工程冻结;同campaign后续复用,冻结值下架拒绝触发,
   既有终态RESULT不受影响。当前config影响新campaign,不能覆写存量冻结参数。
8. 凭据可信边界为Chromium浏览器 + 专用Node代理;请求头/请求体在协议适配层
   立即丢弃,不向Python输出、不用于业务解析、不持久化或开启协议日志。
9. 失败样本父构建1186372,先核实属于RBS/TRIGGER,再从Child Build取得子构建;
   若不是RBS即停止,不把它当作合格样本。

Successful与Accept分开:默认qb_pass_requires_accept=false;冻结稿附录A第6条
(同步后design.md §4.5第6条)还要求FAIL_FAST/架构/逐架构状态按契约核对,
不以旧SBS样本宣布RBS已通过这些核对。

## 4. 附录A同步清单

所有位置均存在。design.md已作以下修改,附录原文比对通过,见§9:

| 附录A条目 | design.md位置 | 处置 |
|---|---|---|
| §4.5引文 | :2747 | 13条原文(去引用前缀)加入§4.4之后 |
| 元信息/§4.4标题 | :5/:6/:2700 | v1.5.22版本与变更记录;标题覆盖v1.5.20至v1.5.21 |
| EF-5指引 | :250 | 仅追加指定指引行 |
| campaign schema/迁移说明 | :736/:751 | 照录第2.2节DDL;追加指定迁移注记,不改实现 |
| 状态迁移 | :1094/:1114 | QB_REQUESTED进入条件;第6.3节转移行;失败终态显式retrigger说明 |
| CLI三处指引 | :1817/:1828/:1855 | qb-sbs-trigger/qb-result-fetch之前、review-submit第2项之前 |
| qb_profile签名 | :2368 | campaign_state签名块追加指定一行 |
| 错误码登记 | :2622/:2631起 | 第7节新增码登记;两个既有码说明修订 |
| Phase 5Q/5R/8.5 | :3145/:3157/:3215 | 5Q标题更名,三处指定指引 |
| 跨文档章节引用 | 上述位置 | 使用P5Q设计文件第x节,不用内部§引用 |
| C0-01第1项 | :3480 | 仅文末版本改为v1.5.22-FROZEN,2026-10-10日期及其余文字不动 |
| C0-01第2项 | :3485 | EF台账原行之后新增指定指引,原有文字不动 |

没有扩改历史REST/SBS正文;以附录A指定的新增权威节和指引覆盖其旧口径。
首次设计检查器因下节问题停止;获批后仅按§8裁定修改文末两处,
不改冻结稿或检查器。

## 5. 挂账与人工闸门

| 项目 | 状态/关门点 |
|---|---|
| 第9.4节第1步RBS只读取证 | DONE;C2b/live-12及§26,Base失败样本1193469;1186372为Unified,不替代Base样本 |
| 第9.4节第1.5步表单联动 | DONE;§26/live-12,Full→Partial→Full;§36.6填表演练12字段各1获准/0拒绝/HTTP200、提交放行0 |
| 第9.4节第1.6步a原始字节比对 | CLOSED;C5b固定六页60项一致,本轮成功父子与1917五页50项一致、身份计数均0;见§45.4 |
| 第9.4节第1.6步成功样本 | CLOSED;1201886/1201889,live-05与C6b双份证据及逐项行号见§45.5 |
| 第9.4节第1.6步BUILD_NOTES样本 | CLOSED;完整请求标记逐字相等,无首尾空白、HTML转义或截断;见§45.5 |
| 第9.4节第2步一次真实提交 | DONE;1201886经人工绑定,1201889 PASS;§43/live-05及§45终态重读,本轮未再提交 |
| 附录C待填 | 已取证内容见C2b/appendix-c.md、§26及v1.5;成功样本/快照关系由§45补证登记,本轮冻结稿原字节不改 |
| v1.8自动绑定与验证性提交 | C7 ACCEPTED;C8小修e393a1f已推送,专用库准备完成;等待本轮逐字“确认提交”,未执行真实提交或零提交读取;见§49 |
| P12 sandbox推送观察 | PENDING_P12;首次真实Gerrit推送后观察是否自发QB构建;本批不提前真实推送 |
| Unified配置 | 未取证保持disabled,不能猜配置ID/默认值 |

## 6. 停止报告

### P5Q-C0-01 CLOSED:附录A未列文末版本同步,检查器拒绝头尾不一致

- 位置:冻结稿:738只指定“§0 元信息:版本行改为 v1.5.22”;停止时design.md:5
  为v1.5.22-FROZEN,但文末:3480仍为v1.5.21-FROZEN(现已按§8关闭)。
- 判据:tools/check_design_doc.py:451-463要求头尾版本相同。
- 实测命令与输出:

```text
$ .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
== check_design_doc: docs/clang-fix-campaign/design.md ==
[VERSION] 头 v1.5.22-FROZEN ≠ 尾 v1.5.21-FROZEN
-- 1 problem(s) --
exit=1
```

- 困难:任务要求附录A严格照录且不能自行改写;现有文末版本未在其同步清单中,
  本轮不能同时按明确列出的范围执行并取得检查器0 problem。
- 候选处置:设计方按轻量流程授权将design.md文末版本声明中的v1.5.21-FROZEN
  单独同步为v1.5.22-FROZEN,其它文字不动;冻结稿hash与检查器都保持不变。
- 上轮未执行该候选,停止报告1条。现经FatTank批准、设计方裁定关闭,
  处置见§8;停止记录保留,不以复跑覆盖历史失败。

## 7. 首次暂停时的验收状态(历史记录)

- 冻结稿sha256:PASS,原字节未动。
- 设计检查器:exit1,仅报告上述VERSION问题,不能记整体验收PASS。
- 全量pytest/mypy/ruff:本轮尚未执行,不引用历史1937/1冒充新实跑。
- DDL内存执行、附录逐字比对/新增错误码控制:待裁定后继续。
- 全部改动仅文档中间态,生产代码/测试/检查器零改动。

## 8. 实施裁定

### P5Q-C0-01(2026-10-10,FatTank批准,设计方出具)

原因:冻结稿附录A漏列文末版本声明与EF台账两处。

1. 允许把design.md文末版本声明中的v1.5.21-FROZEN改为v1.5.22-FROZEN,
   日期保持2026-10-10,其余文字不动。
2. 同段EF台账“仅剩 EF-5 四项(**P5Q 开工前**)——”之后新增原文:
   “(v1.5.22)EF-5 按 §4.5 第 8 条处理,不再作为 P5Q 开工门。”
   原有文字不删不改。
3. 冻结稿不改,sha256仍为
   0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950;
   检查器不改。
4. 完成C0原任务,检查器须0 problem,全量测试/mypy/ruff通过后提交推送。

本轮只按以上两处改动落实,不扩展其它正文改写;复跑证据见§9。
裁定不授权C1实现、浏览器登录、QuickBuild请求或真实Gerrit推送。

## 9. C0验收(2026-10-10)

所有命令在26e9e3d基础上的本轮工作树执行,ruff单列干净树路径如下。
原始日志目录:[evidence/C0](evidence/C0/)。退出码均来自本轮实跑。

```text
$ .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
== check_design_doc: docs/clang-fix-campaign/design.md ==
-- OK: 0 problem --
exit=0 (design-check.log)
$ .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py --self-test
-- self-test: 38/38 passed --
exit=0 (checker-self-test.log,各正反fixture原文在日志)
$ .venv/bin/python -m pytest -q
1937 passed, 1 skipped in 65.09s (0:01:05)
exit=0 (pytest.log)
$ .venv/bin/mypy
Success: no issues found in 110 source files
exit=0 (mypy.log)
```

全树ruff在干净工作树`/tmp/p5q-c0-26e9e3d`(26e9e3d)执行,
本轮没有任何Python/配置变更,与C0代码集合相同;不将主树无关未跟踪草稿纳入检查:

```text
$ /home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/ruff check .
All checks passed!
exit=0 (ruff.log)
```

生产回归仍为1937/1,与26e9e3d的已归档基线一致,新增测试0;
没有进入C1,没有改production/tests/checker,新表只进入设计DDL。

### 9.1 照录、错误码登记与DDL可执行性

使用内存Python核验,不产生代码文件或修改检查器:

- 从冻结稿附录A提取引用块,去掉Markdown引用前缀,与design.md的§4.5逐字比较;
  13条全部一致。
- 第2.2节DDL与design.md新表段逐字相等;第6.3节七条转移行完整照录。
- 附录A指定指引、qb_profile签名、C0-01两处按原文检查;
  P5Q跨文档引用没有“P5Q 设计文件 §”。
- 第7节14个错误码在design.md **§4.3本节**各登记一次(相对基线新增13个);
  QB_SUBMIT_FAILED按附录A指定说明改写,REJECTED_QB_BINDING_MISMATCH扩展说明。
- 内存删除QB_LOGIN_TIMEOUT定义、保留引用,原检查器报告未登记,不修改磁盘design。
- sqlite3内存库实际执行design.md完整campaign schema,合法profile写入成功;
  profile_sha256为空、63位、65位、大写、非hex、全角数字的六例均被CHECK拒绝。

实测输出(transcription-ddl-final.log,exit0):

```text
appendix_A_section_4.5: byte_equal=true; clauses=13
campaign_qb_profiles_DDL: byte_equal=true
state_transitions: byte_equal=true; rows=7
guidance/signature/external_references/C0-01: PASS
error_code_registration: 14/14; new=13
missing_new_error_code_control: RED_AS_EXPECTED ['[ERRCODE] QB_LOGIN_TIMEOUT 未登记于 §4.3']
sqlite=3.45.1; complete_campaign_DDL=PASS; valid_profile_insert=PASS
profile_sha256/empty: CHECK_REJECTED
profile_sha256/short: CHECK_REJECTED
profile_sha256/long: CHECK_REJECTED
profile_sha256/uppercase: CHECK_REJECTED
profile_sha256/nonhex: CHECK_REJECTED
profile_sha256/unicode: CHECK_REJECTED
transcription_and_in_memory_DDL=PASS; repository_DB_writes=0
```

首次一次性核验调用checker.check时漏传CLI会自动读取的权威prompt,
在照录/14码比对通过后触发断言(exit1;已保留transcription-ddl.log部分stdout)。
诊断原文:`helper_without_prompt=['[CK-IDX-01] 缺少唯一权威 prompt: p45-implementation-prompt-v1_5_15.md']`。
随后使用与CLI相同的_find_authoritative_prompt解析输入再核验,exit0。
这是临时核验调用的参数遗漏,不是设计/检查器变更;正式CLI检查始终为0 problem。

### 9.2 交付范围与停止点

本提交仅冻结稿、design.md、stage20文档/验收输出、INDEX和stage19移交表。
冻结稿原字节hash不变;既有无关改动不暂存。C0-01 CLOSED,未闭合停止报告0条。
C0完成后停止,等待下一步指令;第9.4节真机三步及附录C均未执行/未填写,
没有读取凭据、发起QuickBuild请求或真实Gerrit推送。

## 10. C1离线实现与验收(2026-10-10)

基线3e073bc;冻结稿SHA256仍为
`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`。
design.md、冻结稿、检查器、sandbox_submit及P2-P5其它模块均无diff。
没有浏览器/CLI实现、没有新依赖,没有对QuickBuild或Gerrit的网络请求。

### 10.1 交付与接口

| 冻结稿 | 文件/接口 | 结论 |
|---|---|---|
| 第3.7节 | `ci_triage/qb_redact.py`:PageRedactor.redact/check_bytes/check_written | spike身份定位和敏感值规则移入;USER/REDACTED;palette:recorder保留;写后读取原始字节,失败删除并抛QB_EVIDENCE_REDACTION_FAILED |
| 第2.1节 | `ci_triage/qb_config.py`:parse_qb_config/project_for_branch | 输入campaign的qb段,一次校验六条;INVALID_ARGS与REJECTED_QB_PROJECT_NOT_READY分别由异常code提供,无CLI/浏览器调用 |
| 第2.2节 | canonical_profile_json(project, frozen_snapshot=...) | 纯函数,不修改输入;@freeze替换为给定实际值;五个顶层字段含完整form,sort_keys/紧凑分隔/ensure_ascii=False |
| 第2.2/6.2节 | campaign_state新增表与_insert_qb_profile_on_connection | DDL逐字照录;内部计算UTF-8 hash/UTC created_at,INSERT ON CONFLICT DO NOTHING后回读;不同原文字节StateInconsistent |
| 第6.2节 | _create_qb_request_on_connection/_append_qb_event_on_connection/_append_status_on_connection | 不初始化schema、不接管连接/事务;原有校验与写入保持 |
| 第6.2节 | create_qb_request/append_qb_event/append_status | 公共签名不变,既有连接前校验不变;开事务后调原语;request同输入幂等并保留单条SUBMITTED |
| 第2.2/6.1节 | qb_profile(state_db, branch) | mode=ro按branch读完整行(dict,含profile_json/hash/created_at),不存在返回None;不初始化schema |
| 第9.5节 | test_campaign_state.py精确表集合 | 仅增加campaign_qb_profiles,原测试其它代码未改;CHECK负例在test_qb_state.py |

实施细节(不改设计规则):

- 配置解析入口接收已加载的qb映射,不引入第二个配置文件加载器;SNAPSHOT_NUM的具体值
  为非空选项文字,不猜日期/数字格式;项目选择与规范化函数消费已校验配置。
- profile查询返回数据库行,调用方从profile_json读取冻结参数;原语接收调用方生成的
  规范化JSON,不再次序列化。无更新/删除profile API。
- 既有create_qb_request已同时写SUBMITTED,新原语完整保留;append_qb_event仍拒绝
  外部SUBMITTED,不能在C3组装事务时重复写事件。
- 双列表例外按已归档HTML的name末两段`palette:recorder`识别;
  普通名为recorder的隐藏输入仍脱敏。HTML占位符以实体保存,显示为<USER>/<REDACTED>。
- 冻结DDL注释行101列,超过ruff的100列;仅在该SQL字面量末尾标注E501例外并说明
  保留原文,不改DDL或ruff配置。新增测试初轮6处长行由格式化修复,最终ruff全绿。

### 10.2 新增测试清单与DoD映射

完整104个nodeid见[evidence/C1/new-nodeids.log](evidence/C1/new-nodeids.log)。

| 文件/数量 | 用例组 | 覆盖 |
|---|---|---|
| test_qb_config.py / 50 | test_six_rules_valid_config_and_canonical_profile、test_rule1至test_rule6 | 六规则正反;三个路径各拒相对/不存在/空;form增减键;SNAPSHOT_NUM空/错误类型;架构单个/缺少/重复/多组;false失败传播/非空image及Add/Remove;布尔类型 |
| 同文件 | test_project_not_ready、test_canonical_freeze_needs_actual_value、test_profile_includes_every_freezing_field | 缺branch/disabled;未提供freeze值拒绝;各顶层参数影响规范化JSON,Unicode原文与输入不变 |
| test_qb_state.py / 35 | test_all_primitives_accept_outer_transaction_and_do_not_manage_it、test_primitives_do_not_initialize_schema | 外层BEGIN IMMEDIATE成功,SQL trace无BEGIN/COMMIT/ROLLBACK/CREATE,未提交时其它连接不可见,连接仍可用;无表则失败且不初始化 |
| 同文件 | test_each_write_group_rolls_back_on_injected_failure | 意图/未放行/绑定/非终态/结果五种组装事务注入异常,所有四表恢复原快照;此处仅原语组合,不是C3/C4 CLI验收 |
| 同文件 | test_profile_first_write_idempotence_and_bytes、test_other_connection_wins_concurrent_freeze | 首写、no-op、不同原文字节拒绝;UTF-8 sha256/UTC时间;另一连接并发同/异内容,异内容无request |
| 同文件 | test_branches_and_campaigns_have_independent_profiles、test_qb_profile_query_is_read_only | 两branch分别取行;新DB可冻结新配置;查询不写文件/不建schema |
| 同文件 | test_profile_sha256_check_rejects_invalid_values、test_profile_ddl_is_frozen_verbatim | 空/63/65位/大写/非hex/全角CHECK拒绝;DDL与冻结原文相等 |
| 同文件 | test_request_primitive_keeps_submitted_and_idempotence、test_each_profile_key_change_conflicts_without_request、test_frozen_profile_detects_each_form_field_change | 原request幂等;五个顶层字段及十个form键逐项变更拒绝 |
| test_qb_redact.py / 19 | test_redact_roundtrip_and_raw_written_scan、test_header_lines_never_returned、test_triggered_by_column_and_entities、test_encoded_and_quoted_secrets | 页面植入身份/token/session/URL/头,原始字节扫描与stdout/stderr无泄漏;recorder保留;重复脱敏稳定 |
| 同文件 | test_self_check_failure_deletes_evidence、test_fresh_redactor_self_check_does_not_need_prior_secrets、test_ordinary_recorder_named_input_is_not_palette_exception | 写后注入失败删除;新实例也能检测未脱敏身份和敏感字段;非双列表隐藏项不豁免 |

### 10.3 实测结果与公共API等价证明

全部日志在[evidence/C1](evidence/C1/),下列最终验收exit均为0:

```text
.venv/bin/python -m pytest tests/unit/test_campaign_state.py -q
36 passed in 5.68s (重构前,state-before.log)
.venv/bin/python -m pytest tests/unit/test_campaign_state.py tests/unit/test_qb_state.py tests/unit/test_qb_config.py tests/unit/test_qb_redact.py -q
140 passed in 6.22s (focused.log,含既有36个)
.venv/bin/python -m pytest -q
2041 passed, 1 skipped in 60.78s (0:01:00) (pytest.log)
.venv/bin/mypy
Success: no issues found in 112 source files (mypy.log)
git ls-files -z -- '*.py' | xargs -0 .venv/bin/ruff check --force-exclude
All checks passed! (ruff-tracked.log)
.venv/bin/ruff check tizen-ci-triage/scripts/ci_triage/qb_config.py tizen-ci-triage/scripts/ci_triage/qb_redact.py tests/unit/test_qb_config.py tests/unit/test_qb_redact.py tests/unit/test_qb_state.py
All checks passed! (ruff-new.log)
.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md
-- OK: 0 problem -- (design-check.log)
.venv/bin/lint-imports
Contracts: 6 kept, 0 broken. (lint-imports.log)
```

ruff覆盖tracked Python与本批全部新增Python,不包含无关untracked历史草稿。
全量1937→2041,新增104,仍1 skipped;旧API用例全部通过,没有改断言迁就重构。
内存AST比对3e073bc与工作树,实测[api-equivalence.log](evidence/C1/api-equivalence.log):

```text
create_qb_request: public_signature=IDENTICAL; transaction_body_AST=IDENTICAL
append_qb_event: public_signature=IDENTICAL; transaction_body_AST=IDENTICAL
append_status: public_signature=IDENTICAL; transaction_body_AST=IDENTICAL
legacy_test_file: AST_IDENTICAL except one required table-set addition; no test body relaxed
frozen_sha256=UNCHANGED
```

### 10.4 挂账与停止点

无新增设计矛盾或停止报告。C1完成,C2及后续未开始;§5真机挂账原样保留。
第9.1节的假代理/CLI错误码输出、profile变化时代理零启动、全部触发/结果事务业务链、
代理应答敏感键拒收分别仍归C2/C3/C4;不能以本轮组件测试冒充这些集成验收。
Git提交推送仅交付代码与证据,不访问QuickBuild、不启动浏览器、不读取真实凭据。

## 11. C2a能力验证与停止报告(2026-10-10)

### 11.1 范围与权威

开工HEAD为`d1f09cc`,分支`clang-fix-campaign`。冻结稿sha256再次实测为
`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`,未改动。
先读本进度与冻结稿§3/§9.2,按“真实输入验证规格可满足性”先查新目标拦截。
Playwright使用spike已有路径(1.58.2),Chromium为145.0.7632.6。
PATH未找到独立node;离线探针用VS Code的`ELECTRON_RUN_AS_NODE=1`运行,
实际Node版本24.21.0。此方式仅用于能力取证,不冒充生产Node启动交付。

### 11.2 P5Q-C2A-01 历史停止报告:已由§12批准裁定替代

- 原文位置:冻结稿:180(§3.1新窗口执行前关闭,不得以创建后关闭替代)、
  :216(§3.4第三拦截面)、:576(验收第11条)。
- 方法:先装浏览器级`Target.setAutoAttach`与另一CDP会话的
  `Target.autoAttachRelated`,均`waitForDebuggerOnStart=true`;两者使用独立会话,
  避免后者取消前者。测试只用about:blank与内存Blob,代理侧不恢复任何新目标。
- 最小反例:opener执行`window.open('about:blank')`,继而对返回窗口
  `document.write`一个把opener布尔标记设为true的脚本。
- 实测:弹窗事件`waitingForDebugger=true`,但`popupRan=true`;
  同样设置下Worker标记为false。立即调用`Target.closeTarget`返回success=true,
  弹窗脚本仍已执行。不能以关闭成功判定“执行前阻断”成功。
- 证据与完整命令:[C2a/README.md](evidence/C2a/README.md);
  最小复现:[target_pause_probe.mjs](evidence/C2a/target_pause_probe.mjs)。

| 控制 | 原始输出 | exit | 结论 |
|---|---|---|---|
| baseline:不加暂停,验证样本确实能执行 | [baseline](evidence/C2a/target-pause-baseline.log) | 0 | workerRan=true,popupRan=true |
| hold:启动暂停,不恢复 | [hold](evidence/C2a/target-pause-hold.log) | 1 | workerRan=false,popupRan=true,执行前阻断失败 |
| close:挂接回调立即关闭,不恢复 | [close](evidence/C2a/target-pause-close.log) | 1 | closeTarget成功但popupRan=true,执行前阻断失败 |

三次`PROFILE_REMOVED=true`;每次页面请求仅`blob:1`,HTTP(S)/WS(S)均零,
未访问QuickBuild/Gerrit/外部页面,未读凭据、未加载日常profile。
日志只记录固定标签、布尔值、协议方法结果及运行版本,未开启协议调试输出。

困难:本机栈的Target启动暂停不能保证初始同源弹窗文档不被opener同步执行;
这是真实反例,不等同于证明所有可能的Chromium实现路径均不可行。
候选处置:请设计方裁定窗口创建前拒绝的补充机制及防绕过验收;
不能直接采用事后关闭,也不擅自注入window.open覆写或降低冻结的安全边界。
本轮停止报告1条,不自行关闭。

### 11.3 尚未交付与验收边界

本轮只新增能力探针/原始日志/说明,更新进度与INDEX。生产源码、既有测试、
冻结稿、design.md、检查器均零修改;原有无关工作树改动保持原样。

- HTTP逐跳Fetch请求/响应拦截:未实现,不得记PASS。
- WebSocket:`BrowserContext.routeWebSocket`拒绝路由已在探针安装;
  未执行WebSocket安全验收,不得记PASS。
- 新目标:上述两种CDP拦截均实测,弹窗执行前阻断失败。
- Python驱动/假代理/login_timeout校验/§9.2完整用例:停止后未开始。
- 正常/异常/SIGTERM清理矩阵、完整pytest/mypy/ruff/lint-imports:
  本轮未跑,不借用C1的2041/1作为本轮结果。
- C2a验收未完成,未提交C2a完成commit、未推送;C2b与真实安全子集未开始。

### 11.4 同任务再次下发后的复核(2026-10-10)

本轮先重读§11,核对HEAD仍为`d1f09cc`,冻结稿sha256仍与§11.1完全相同。
任务再次要求执行前阻断、做不到即停,未包含解除P5Q-C2A-01的设计裁定。
没有据此自行放宽拦截规则。

按[C2a/README.md](evidence/C2a/README.md)的同一完整命令重跑`close`模式,
不修改探针,输出另存[target-pause-close-recheck.log](evidence/C2a/target-pause-close-recheck.log),
不覆盖首次取证。原始结果:exit=1,`waitingForDebugger=true`,
`closeResults=[{"success":true}]`,`workerRan=false`,`popupRan=true`,
`EXPECTATION=FAIL`,`PROFILE_REMOVED=true`。
页面请求仍只有`blob:1`,未访问QuickBuild/Gerrit/外部页面。

P5Q-C2A-01仍OPEN,没有新增停止条目。需要设计方裁定补充的窗口创建前
拒绝机制及验收口径;生产代码、冻结稿与既有测试仍未改动。
未运行完整交付验收,未提交/推送,未进入C2b。

## 12. 实施裁定 P5Q-C2A-01(2026-10-10,FatTank已批准)

设计方裁定:冻结稿§3.1/§3.4的新窗口与弹窗执行前阻断改为根本不允许创建。
冻结稿原字节不改。原因是暂停中的弹窗仍可被opener同步执行脚本,
暂停后关闭不满足执行前阻断。§11旧探针只保留历史记录,不再复跑或作为验收依据。

1. 主机制:Chromium启动参数加`--block-new-web-contents`。
2. 纵深:在任何页面脚本之前注入不可再改写的`window.open`,恒返回null,
   首个导航前装好。
3. 保留浏览器级自动挂接与Worker类目标启动即暂停;仍出现任何新页面目标,
   视为机制失效,关闭整个浏览器并以QB_BROWSER_UNAVAILABLE停止。
4. 附带探针在浏览器级CDP会话启用请求拦截,实测弹窗/Worker请求覆盖;
   能则加为额外拦截层,不能只记录,不得冒称生效。
5. 新探针使用本机Chromium和仅绑定loopback的假服务器,以服务器实收清单
   与新页面目标数为判据:window.open同源页、about:blank同步写脚本fetch、
   脚本点击target=_blank链接、脚本提交target=_blank表单、Worker与SharedWorker
   fetch均须无请求且无新页面目标;去掉窗口防护的a/b对照必须能触发请求。
6. a-e任一失败即汇总新探针逐项结果并停止,不降级为事后关闭。
   全部通过才继续C2a原任务,不进入C2b。

裁定已收到并按要求在新探针落实,不再请求重复确认。

### 12.1 新探针与实装API

新增`tests/node/p5q_creation_probe.mjs`,仅本机loopback假服务器、合成HTML与Blob。
完整命令、原始输出、脚本hash和环境见
[creation-probe-report.md](evidence/C2a/creation-probe-report.md)。
最终原始日志:[creation-probe-layered.log](evidence/C2a/creation-probe-layered.log),exit=1。

- 主机制:`--block-new-web-contents`,由`Browser.getBrowserCommandLine`证实存在。
- 纵深:`BrowserContext.addInitScript`首个导航前登记,Object.defineProperty
  固定window.open恒null、不可写、不可配置;页面中实读描述符。
- 去掉Playwright默认`--disable-popup-blocking`再测,排除反向参数;
  实际启动记录为blockNewWebContents=true、disablePopupBlocking=false。
- 浏览器级`Target.setAutoAttach`与另一个会话`Target.autoAttachRelated`,均启动暂停;
  browser会话承接SharedWorker,related会话承接Worker,从不恢复。
- `Target.setDiscoverTargets`观察到新page即`browser.close()`;
  该处置是失败兜底,不算禁止创建成功。
- 浏览器级`Fetch.enable`/`Fetch.requestPaused`/`Fetch.failRequest`附带探针
  证实覆盖弹窗/Worker/SharedWorker目标请求(3/3,服务器均未收到),
  已作为额外层加入最终保护组;不替代page目标数断言。
- `BrowserContext.routeWebSocket`拒绝路由已安装,尚无完整WebSocket专项验收。

### 12.2 逐项结果

| 项目 | 目标请求实收 | 新page目标 | 结果 |
|---|---:|---:|---|
| a:window.open同源页面 | 0 | 0 | PASS |
| b:about:blank后同步写入fetch脚本 | 0 | 0 | PASS |
| c:脚本click target=_blank链接 | 0 | 1 | FAIL,关闭整个浏览器 |
| d:脚本submit target=_blank表单(GET) | 0 | 1 | FAIL,关闭整个浏览器 |
| e:Worker fetch | 0 | 0 | PASS |
| e:SharedWorker fetch | 0 | 0 | PASS |
| f-a:无防护观察对照 | 1 | 1 | PASS,确实收到/probe/a |
| f-b:无防护观察对照 | 1 | 1 | PASS,确实收到/probe/b |

总计8项,6通过/2失败。正常fixture/favicon请求不冒称为0,逐条列于原始日志。
附带Fetch探针3种来源均拦到且服务器未收到;仅请求阶段的已测事实,
不声称307/308响应或全部重定向已验证。测试过程全部临时profile已删除。

### 12.3 P5Q-C2A-02 历史停止报告:已由§13批准裁定替代

这不是§11旧探针复跑:当前无window.open调用的两条原生路径c/d仍新建page目标,
即使block参数存在、window.open不可改写,且已排除反向默认参数。
按裁定a-e任一失败即停,停止后续生产实现。新目标触发关闭整个浏览器,
但“请求没到服务器”不能替代“没有创建新page”,故不降级放行。

此前未加入浏览器级Fetch时,SharedWorker还曾有一次请求先到达服务器,
见`creation-probe-no-default-disable.log`;保留该失败,不抹掉竞态迹象。
按裁定加入已实测有效的额外Fetch层后,最终e项通过,c/d仍失败。

已批准的P5Q-C2A-01裁定登记完毕;本轮新的停止条目1条(P5Q-C2A-02)。
冻结稿/design.md/生产代码/既有测试未改,旧探针未复跑。
JS语法检查exit0,完整pytest/mypy/ruff/lint-imports尚未运行,
代理/驱动/假代理未实现,未提交/推送C2a完成commit,未进入C2b。

## 13. 实施裁定 P5Q-C2A-02(2026-10-12,FatTank已批准)

本节记录设计方提示词裁定,不修改冻结稿。威胁模型为“任何未经判定的请求
到达QuickBuild”,不是“浏览器内是否出现新页面目标”。§12的停止条目按本裁定关闭,
旧实跑原文保留,不作为本轮通过的证据。

1. 浏览器级CDP会话上的`Fetch.enable`/`Fetch.requestPaused`/`Fetch.failRequest`
   升为必需主拦截层,首个导航前装好,覆盖所有目标。请求逐跳判定与响应307/308
   终止均在此层。frameId不属于当前工作页帧树或无法归属时一律拒绝。
   页面级拦截只可作第二层。
2. 保留`--block-new-web-contents`、不可改写的window.open恒null、上下文级
   WebSocket拒绝、Worker类目标启动即暂停。任何新page仍关闭整个浏览器,
   以QB_BROWSER_UNAVAILABLE停止,不允许继续运行。
3. c/d改为三项同时成立:服务器实收请求0(含新页文档);新页脚本请求0;
   检测新page后关闭浏览器并报QB_BROWSER_UNAVAILABLE。不再要求新page数0。
4. 新增g:同源blob页面通过_blank链接打开,脚本尝试fetch/ws/wss;
   服务器HTTP0、WebSocket握手0,随后关闭浏览器。新增h:rel=opener的_blank
   链接点击后,opener经window.open('', name)或其它路径尝试取得引用并写脚本;
   须取不到引用且服务器实收0。任一不满足即停止,不得降级。
5. a/b/e/f标准不变,与c/d/g/h一并重跑归档。全部通过才继续C2a原任务,
   不进入C2b。所有探针使用本地假服务器与合成数据,零外网。

本轮首先实施帧归属与a-h新探针;结果与完整命令随后登记,不预记PASS。

### 13.1 实跑结果与停止报告: h引用结果未取得

完整命令、逐项结果与原始日志hash见
[request-boundary-report.md](evidence/C2a/request-boundary-report.md)。
新探针为`tests/node/p5q_request_boundary_probe.mjs`。

- a/b均恒null、服务器0、新page0;Worker/SharedWorker均服务器0、新page0。
- c/d/g均服务器HTTP0与WS握手0、新page1、浏览器关闭并标记QB_BROWSER_UNAVAILABLE,
  按新判据通过;不再沿用旧的“新page必须0”。
- 无防护f-a/f-b实际收到攻击请求;另加无防护g,HTTP1、ws/wss握手各1。
- h保护组:服务器0、新page1、已关闭;但`FIXTURE_INTERRUPTED`且
  `referenceAttempts=[]`,未取得window.open/命名查找/frames的引用尝试结果。
  改为普通同源h页面后仍相同;无防护对照经message.source取得引用并产生HTTP请求。
  这是取证不足,不是已证明保护组获得引用或发生请求逃逸。不能将零请求直接
  代替“取不到引用”的独立断言,也未为取证推迟立即关闭。
- a-h集合exit1:10/11通过(含附加g对照);h补充对照exit1:1/2通过。
  JS语法检查exit0;临时profile与证书均已删除。

停止条目1项(h取证),不重复请求确认P5Q-C2A-02。候选后续取证方向:
设计方确认能同时保留立即关闭与证明引用不可取得的观察口径,
或补充不依赖关闭后页面回传的独立观察方式;本轮不自行把h改为仅验网络计数。
此处不声称现有实现无法做到请求安全,只报告本次证明未闭合。

浏览器级Fetch请求/响应层、Page事件帧集合、上下文WebSocket拒绝与新目标暂停/关闭
均已落实到探针,尚非生产代理交付。完整pytest/mypy/ruff/lint-imports尚未跑;
冻结稿、design.md、生产代码及既有测试未改,未进入C2b。

## 14. 实施裁定 P5Q-C2A-03(2026-10-12,FatTank已批准)

冻结稿原字节不改。威胁模型为“任何未经判定的请求到达QuickBuild”。
§13.1的h停点由本裁定关闭,“取不到引用”的要求作废,不再请求确认。

1. 仅探针诊断模式关闭“发现新page立即关闭浏览器”;其它保护全部保留:
   block-new-web-contents、window.open不可改写恒null、浏览器级Fetch与帧归属、
   上下文routeWebSocket、Worker启动暂停。
2. h1为rel=opener的_blank链接打开同源blob页面,该页postMessage给opener,
   后者经message.source取得引用。h2在10秒内反复经引用发起fetch、XHR、
   表单提交、location导航、ws/wss。所有目标均为本地假服务器。
   服务器HTTP0与WS握手0为判据;引用及每次尝试结果只作记录,
   页面console经Runtime.consoleAPICalled实时归档,不依赖关闭后的回传。
3. 正常模式开启全部保护,同场景必须关闭浏览器并报QB_BROWSER_UNAVAILABLE,
   服务器实收0。诊断开关仅限探针入口,Python驱动与生产CLI不得传入,须有静态断言。
4. 对照组在诊断模式下再去掉浏览器级Fetch,必须实际收到h2请求。
   a-g既有结果保留,本轮不重复运行。h通过后继续完整C2a;否则逐项报告并停止,
   不降级,不进入C2b。

本节裁定先于实现登记。下列结果均来自本次实跑,不以历史结果替代。

### 14.1 h最终验收

完整命令、测试对应与边界见[completion.md](evidence/C2a/completion.md),
原始实时console转录及服务器请求清单见[h-final.log](evidence/C2a/h-final.log)。

| 模式 | HTTP(整个h窗口) | WS握手 | 引用记录 | console记录 | 判定 |
|---|---:|---:|---:|---:|---|
| 诊断:仅关闭新page立即关闭机制 | 0 | 0 | 20 | 221 | PASS |
| 正常:全部保护 | 0 | 0 | 0 | 1 | PASS;关闭浏览器,QB_BROWSER_UNAVAILABLE |
| 诊断去Fetch对照 | 80 | 0 | 20 | 221 | PASS;确有HTTP到服务器 |

exit=0,3/3。诊断/对照各在10秒窗口尝试fetch、fetch-eval、XHR、表单、location、
ws/wss各20次。引用确实取得,不作拒绝条件;INVOKED是尝试,不冒称请求已到达。
保护组fetch后续转录REJECTED;正常组在取得引用回报前关闭,只见launch。
最终夹具图标改为内联,HTTP断言包含窗口内全部路径,没有排除favicon凑零。
所有临时profile与证书均已删。a-g按裁定保留§13通过结果,未重跑。

探针直接调用生产installGuards;诊断开关仅测试入口传入。
两个主拦截条件为浏览器级Fetch逐跳判定与当前工作页frameId集合归属;
Page.getFrameTree初始化,Page.frameAttached/Detached/Navigated维护,无归属即拒绝。
WebSocket由context.routeWebSocket拒绝;Worker由Target.setAutoAttach/
autoAttachRelated启动暂停后关闭。block-new-web-contents与不可改写window.open保留;
新page正常模式触发全浏览器关闭。API清单见completion表。

### 14.2 实现与测试范围

- 新增正式qb_browser_agent.mjs、qb_browser.py;qb_config补正整数超时校验。
- 新增Python假代理,记录逐条命令;驱动参数列表固定、不经shell,嵌套凭据键拒收,
  HTML再自检。已登录后的read可在提交后执行;导航离开表单使旧表单不可再提交。
- Node离线单元53项;真实DOM脱敏与307/308/302测试2项;正常/异常/SIGTERM清理3项;
  h三组3项。Python协议31项、配置59项(其中9项新增),Node包装6个pytest用例(含h)。
- 包含第9.2节全部组:永久禁止/各阶段/逐字段/阶段机/适配器/清理/静态断言。
  不将Node内部用例重复加进pytest总数;本机无Node/PW跳过。
- 实现细节登记:login协议负载附配置超时与启用工程的id/path/name,无凭据;
  pyproject仅加.mjs包数据,确保安装后驱动邻接的代理文件存在;无新Python依赖。
  测试使用VSCode内置Node,不替换生产配置的Node路径。

### 14.3 验收与挂账

| 命令 | exit | 输出/证据 |
|---|---:|---|
| .venv/bin/python -m pytest -q | 0 | 2087 passed,1 skipped;[pytest-final.log](evidence/C2a/pytest-final.log) |
| .venv/bin/pytest -q -s tests/unit/test_qb_browser_node.py tests/unit/test_qb_browser.py tests/unit/test_qb_config.py | 0 | 96 passed;[offline-final.log](evidence/C2a/offline-final.log) |
| .venv/bin/mypy | 0 | 113 source files;[mypy.log](evidence/C2a/mypy.log) |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;[lint-imports.log](evidence/C2a/lint-imports.log) |
| check_design_doc.py design.md | 0 | 0 problem;[design-check.log](evidence/C2a/design-check.log) |
| ruff check .(干净暂存树导出) | 0 | All checks passed;[ruff-clean-tree.log](evidence/C2a/ruff-clean-tree.log) |

基线2041/1增加46个pytest用例。主工作树ruff扫到4个无关未跟踪历史脚本的53个错误;
不改这些草稿、不放宽配置,对完整待交付树导出重跑通过。无关.gitignore/文档删除保留。
冻结稿SHA256仍为0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950,
design.md/检查器/P2-P5未改。C2a本轮停止报告0项。

继续挂账:第9.3节完整假QuickBuild页面流程及指定HTTPS夹具的安全子集,
C2b真机只读/联动、附录C实测、后续C3-C6。已有loopback探针不冒充真实站点取证。
按本轮停点,不登录、不进入C2b、不触发构建;完成后等待下一任务。

## 15. 实施裁定 P5Q-C2A-04

设计方核对ca43b5d后的三项修正。原因:冻结稿第3.6节“子页用页面标题中的构建号”
与真实归档页面不符;第3.5节错误映射表漏列读取类与浏览器不可用。冻结稿不改。

1. 所有build页从导航标签`/^Build \((?:id|Id|ID):(\d+)\)$/`取唯一数字;
   主页另从唯一Summary表thead的唯一Id列取tbody首行同列值。主页两处、子页导航
   均须等于请求id;缺失/重复/不等均QB_READ_ID_MISMATCH。不再用title的#数字。
   正例直接用web-cookie-02的01/03/04.response.txt原文page.setContent,零外网。
2. QB_BROWSER_UNAVAILABLE及QB_EVIDENCE_REDACTION_FAILED同名映射;
   read的QB_READ_REDIRECTED/QB_READ_ID_MISMATCH映射QB_FETCH_FAILED,其余表外INTERNAL_ERROR。
   submit错误应答仅在released严格为布尔false时抛QbBrowserError并携带released=False;
   缺失/true/非布尔、非法应答或进程异常一律unknown,不得当作确定未提交。
   符合既有协议的成功build落点仍保留;含凭据键的应答丢弃,不向调用方返回原载荷。
3. 点击Ok后先等实际请求的policy.released,至多10秒;未放行才作未放行处理。
   放行后至多60秒等导航完成,不把旧表单已load误作新导航完成。refresh精确地址仅GET。

### 15.1 逐项落实与离线测试

| 修正 | 实现 | 证据/结果 |
|---|---|---|
| 构建号身份 | qb_browser_agent.mjs buildId/read/submit;nav-link唯一匹配,Summary列查找,删除title回退 | 01/03/04原文正例;Id/ID大小写;Id列移位;主页/子页缺失、重复、不等;匹配title不能救活错误。19个浏览器子用例全绿 |
| 映射与放行状态 | qb_browser.py decode_response/QbBrowser.command/QbBrowserError.released | 完整映射;read限定;false/true/null/0/1/字符串/对象/数组;缺字段、非法JSON、非法结构、进程退出/写入失败/关闭管道/解码异常;合法成功落点保留。驱动96/96 |
| 提交时序与refresh | qb_browser_agent.mjs submit/Policy.allow | 请求延迟150ms放行后才等导航;实际10秒未放行返回released=false并撤销action;放行后导航超时为unknown;refresh GET绿/POST红。Node单元57/57 |

原始日志:[offline.log](evidence/C2a-04/offline.log)。命令为:
`.venv/bin/pytest -q -s tests/unit/test_qb_browser.py tests/unit/test_qb_browser_node.py`,
exit=0,102 passed。其中Python驱动96(基线31,新增65),Node包装6(数量不变)。
Node内部单元57(原53+4);浏览器22(原2+19子用例+1入口);
h诊断/正常/去Fetch对照3/3、清理normal/exception/SIGTERM 3/3仍绿。
Node内部计数不重复加入pytest总数,本机Node/浏览器包装没有skip。

归档页面仅page.setContent,测试策略拒绝所有请求并关闭DNS解析;其余浏览器夹具仅loopback。
没有登录、QuickBuild/Gerrit访问或真实触发。首次驱动测试94绿/2红是新增夹具忘记登录前置,
修正夹具后全绿,没有改动阶段机;说明见[证据索引](evidence/C2a-04/README.md)。

### 15.2 完整验收与停点

| 命令 | exit | 实测摘要与证据 |
|---|---:|---|
| .venv/bin/python -m pytest -q | 0 | 2152 passed,1 skipped;[pytest.log](evidence/C2a-04/pytest.log) |
| .venv/bin/mypy | 0 | 113 source files;[mypy.log](evidence/C2a-04/mypy.log) |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;[lint-imports.log](evidence/C2a-04/lint-imports.log) |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;[design-check.log](evidence/C2a-04/design-check.log) |
| .venv/bin/ruff check .(完整暂存树导出) | 0 | All checks passed;[ruff-clean-tree.log](evidence/C2a-04/ruff-clean-tree.log) |

基线2087/1增加65,无新skip。主工作树ruff仍因4个无关未跟踪脚本报53错(exit=1),
文件清单与完整待交付树导出方式见证据索引;[原文](evidence/C2a-04/ruff-working-tree.log)保留,
未修改草稿、未放宽lint配置。无关.gitignore和文档删除未入提交。
冻结稿SHA256仍为0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950。
design.md、检查器、P2-P5未改。本轮无新增停止报告项。提交由Git外部锚定。
C2b及§14挂账不变;按任务完成后停止,不进入真机部分。

## 16. C2b 本机安全前置与停止记录

基线09e14c5。冻结稿sha256实测仍为
0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950。
先读本进度、冻结第9.3/9.4节及C2a现有测试;四组覆盖/缺口已先登记到
[coverage.md](evidence/C2b/coverage.md),未拿旧loopback结果代替本次HTTPS准入。

新增tests/node/p5q_c2b_safety.mjs,仅测试入口传主机解析与证书SPKI参数;
生产createRuntime/Policy/拦截器原样复用。假服务器仅绑定127.0.0.1,
quickbuild.tizen.org与外站重定向对照域名均映射到该服务器,其它DNS拒绝。
四组按顺序运行,首个失败后停止,不运行余组。

### 16.1 P5Q-C2B-01: 新增夹具过约束停点

实跑命令(exit=1):

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  tests/node/p5q_c2b_safety.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome
```

原始结果:[safety-first.log](evidence/C2b/safety-first.log)。首组Worker/WebSocket:
- 服务器实际仅收到初始GET /build/1;攻击HTTP=0,WS握手=0。
- trace:shared_worker与worker均WORKER_BLOCKED、paused=true;两次WEBSOCKET_DENIED。
- 夹具FAIL,输出为LOCAL_SAFETY_ASSERTION_FAILED / Expected values to be strictly equal:。
  对照已记录请求与trace、逐条核对断言,停在`assert.equal(runtime.failure, null)`;
  createRuntime的失效关闭标志只能取QB_BROWSER_UNAVAILABLE。原日志未保存异常的
  actual/expected与触发关闭的底层原因,不把源码推断冒充额外采集事实。
- 临时证书/profile目录清理完成。后三组307/308、逐跳拦截、凭据隔离NOT_RUN。

**口径核查**:上述“runtime.failure必须为null”是本轮夹具额外添加的条件,
不是冻结第3.1节/第9.3节的明确验收条文。冻结稿允许无法可靠阻止目标时关闭整个浏览器;
本次没有请求越界证据,也尚未坐实生产缺陷。应修正夹具为实测目标关闭及请求清单判据,
同时记录失败原文与具体关闭事件,不可将额外条件冒称设计要求。
按任务“任一失败即停止报告”,本轮不删断言重跑、不进入余组/真机,不改生产代码。

### 16.2 附录C与后续状态

[appendix-c.md](evidence/C2b/appendix-c.md)显式登记NOT_COLLECTED,无真实字段结论。
真实浏览器没有启动;1193467/1193469/1186372及其子构建均未读取;
未推测overview_id,未open_form/设BUILD_TYPE/点Ok。真实请求数0。
待本机四组全部满足后才能继续第9.4节;本次没有C3开工许可。
通用回归单列归档,不将其绿灯当作四组安全前置通过。

### 16.3 停点提交的通用回归

| 命令 | exit | 实测 |
|---|---:|---|
| .venv/bin/python -m pytest -q | 0 | 2152 passed,1 skipped;[pytest.log](evidence/C2b/pytest.log) |
| .venv/bin/mypy | 0 | 113 source files;[mypy.log](evidence/C2b/mypy.log) |
| .venv/bin/ruff check .(完整暂存树导出) | 0 | All checks passed;[ruff-clean-tree.log](evidence/C2b/ruff-clean-tree.log) |
| C2b安全子集独立Node入口(§16.1完整命令) | 1 | 1组执行/0通过/1夹具失败;3组NOT_RUN;[safety-first.log](evidence/C2b/safety-first.log) |

新增Node安全入口尚未接入pytest自动包装,单独记录其非零结果;不能以pytest绿覆盖它。
Ruff按既有方式检查全部待交付树,不改工作树无关草稿的53个既有错误;
导出树93c73f09a60381deed4e7c31c801f193ef7a8804,目录/tmp/p5q-c2b-lint-RL8iHh。
命令`git archive <tree> | tar -x -C <目录>`,导出完成后用仓库.venv/bin/ruff在该目录检查。
此后只更新本文与证据。冻结稿、design.md、全部生产源码零diff;未改凭据、未开真机。
本提交仅保存离线夹具、原始失败和进度,不声明C2b完成。提交SHA由Git外部锚定。

## 17. 实施裁定 P5Q-C2B-01

设计方出具、FatTank批准,立即执行;冻结稿与生产代码不改。
§16.1停点的夹具条件由本裁定关闭,不把旧日志改写为通过。
原因:Worker/SharedWorker启动暂停、攻击HTTP及WS握手均零时,关闭被暂停目标失败
可按冻结第3.1节关闭整个浏览器并报QB_BROWSER_UNAVAILABLE;原夹具额外要求
runtime.failure为空与该fail-closed契约不符。

- Worker/WebSocket组:攻击HTTP与WS握手必须均为零;另满足(a)目标成功关闭且
  runtime.failure为空,或(b)runtime.failure=QB_BROWSER_UNAVAILABLE且浏览器已关闭、
  临时目录已删除。任何其它failure仍失败。逐项记录实际分支及两种Worker的
  Target.closeTarget成功/失败/异常类别。测试观察器不改CDP返回值或异常;
  分支(b)在测试finally清理之前断言,不得由测试清理动作证明代理已关闭。
- 其它三组判据不变,四组从头完整重跑;四组全绿才允许真机只读与表单联动。
- 真机read/open_form/字段取证一旦出现WORKER_BLOCKED、NEW_PAGE或runtime.failure,
  立即停止,记录触发页面路径形态及trace,不重试绕过。
- 第二、三步沿原C2b任务:单次浏览器人工登录;按顺序只读取证;仅BUILD_TYPE
  Full→Partial→Full,不点Ok、不提交、不产生构建。完成或停点后均不进入C3。

### 17.1 本轮实跑

完整命令沿§16.1,exit=0,原文[safety-c2b-01.log](evidence/C2b/safety-c2b-01.log)。
四组从头重跑,summary=4/ passed=4/ failed=0,network=loopback-only。

| 组 | 实测 |
|---|---|
| Worker/WebSocket | 分支(b);shared_worker closeTarget success=true;worker closeTarget异常类别Error。runtime.failure=QB_BROWSER_UNAVAILABLE;浏览器已关闭、临时目录已删除;攻击HTTP=0/WS握手=0 |
| 307/308 | 各自仅第一跳到达,合法302的/build/999第二跳正常到达 |
| 逐跳 | REST/promote/外站的第二跳均零;307登录POST重放零 |
| 凭据隔离 | 合成cookie/auth/password均实际到达本地服务器;代理输出与适配层异常输出均无合成值,用户显示名已<USER>脱敏 |

原始失败safety-first.log保留。新增pytest本机integration包装,无运行环境时显式skip;
新增静态用例钉死取证脚本无submit命令、Ok点击、submitUrl设置及启动覆盖参数。
真机专用入口为docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs,
原样调用生产createRuntime/Agent,不传testOptions;仅观察已脱敏HTML与协议适配后的元数据。
WORKER_BLOCKED/NEW_PAGE即关闭;runtime.failure由watchdog及每步检查立即关闭。
页面归档前后分别由qb_redact检查,不保存Cookie或原始协议事件。

### 17.2 真机登录停点

实跑入口命令(exit=1):

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-01 \
  .venv/bin/python
```

只发login命令,等待配置600秒;代理返回QB_LOGIN_ABORTED而非超时。
记录[run.json](evidence/C2b/live-01/run.json),逐项源行号见
[appendix-c.md](evidence/C2b/appendix-c.md)。实测GET /signin为200;
人工登录POST为302;后续Document请求被拒。最终浏览器关闭、profile删除,
runtime_failure=null,没有WORKER_BLOCKED/NEW_PAGE。不推断是谁关闭页面或关闭成因。

请求阶段共60条:GET 59(允许46/拒绝13),POST 1(人工登录,允许);
响应阶段38条200与1条302。上述是拦截观察数,非服务器实收数,字体重复尝试单计。
拒绝13条=Script 1 + Document 12,均只存path shape `<other>`;
未保留实际host/path/query,不能据此宣称具体落点、白名单缺项或静态文件名。
登录三条件成功快照未取得;不能把302说成已登录。

没有任何read/open_form/字段命令;pages=[];form_action_releases=0,released=false。
第二步1193467/子构建/1186372/其子构建/配置页均NOT_COLLECTED;
第三步BUILD_TYPE联动NOT_RUN。没有猜overview_id,未用SBS补RBS,未发起构建。
按停止-报告保留现场元数据,不重试、不放宽判据。当前停止项1(真机登录未完成),
尚不能证实具体冻结假设不符;先报告事实,等待下一步授权。C3不启动。

### 17.3 停点验收

| 命令 | exit | 原始输出/结论 |
|---|---:|---|
| .venv/bin/python -m pytest -q | 0 | [pytest-c2b-01.log](evidence/C2b/pytest-c2b-01.log):2154 passed,1 skipped in 103.38s;基线2152/1,新增2,无新skip |
| .venv/bin/mypy | 0 | [mypy-c2b-01.log](evidence/C2b/mypy-c2b-01.log):Success: no issues found in 113 source files |
| .venv/bin/ruff check .(完整待交付树导出) | 0 | [ruff-c2b-01.log](evidence/C2b/ruff-c2b-01.log):All checks passed! |
| .venv/bin/lint-imports | 0 | [lint-imports-c2b-01.log](evidence/C2b/lint-imports-c2b-01.log):6 kept,0 broken |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | [design-check-c2b-01.log](evidence/C2b/design-check-c2b-01.log):0 problem |
| Node安全入口,§16.1原命令 | 0 | [safety-c2b-01.log](evidence/C2b/safety-c2b-01.log):4/4;全量pytest新增integration包装再次实际运行通过 |
| Node --check docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs | 0 | 空输出 |
| git diff --cached --check | 0 | 空输出 |

新增用例:tests/unit/test_qb_browser_node.py中的test_node_c2b_local_https_safety与
test_c2b_evidence_entry_is_not_a_submit_or_launch_override_path。本机均passed,非skip。
前者不访问外部网络,后者只读源码;真实站点脚本不进入pytest执行。

Ruff完整待交付树e5816ee65ca183e6756aaab4b9b81b345e9d61be导出到
/tmp/p5q-c2b-01-lint-NMwly7,命令git archive <tree> | tar -x -C <目录>,
再用仓库.venv/bin/ruff检查该目录全部内容。沿§16既有处理,不修改/排除/暂存
用户无关草稿;此后仅补本节与ruff日志,代码未变。
run.json仅保存协议适配后的元数据,无请求头/请求体/凭据键;
`jq`递归键检查结果true,exit=0。没有登录页原文、Cookie或会话文件归档。

冻结稿sha256仍为0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950;
全部生产源码、design.md及冻结稿零diff。未处理既有.gitignore与docs四处删除,
未入库其它未跟踪草稿。当前提交只闭合本机安全前置并保存真实登录停点,
不声明C2b完成,提交SHA由Git外部锚定。

## 18. 实施裁定 P5Q-C2B-02

设计方出具,FatTank已批准,立即执行;冻结稿不改。以下裁定原文照录:

【裁定原文】
原因:48e8fba 真机登录 POST 返回 302 后,13 条请求(1 Script、12 Document)被放行规则拒绝(都已通过帧归属检查),只存了路径形态 <other>。<other> 不能区分带查询的 /、路径带 ;jsessionid=、http 降级、外站或新路径。冻结稿 §3.4 要求实测登记登录落点,却没有提供取证通道,这是设计缺口,不是实现错误。EF5 用 Playwright 路由拦截,看不到重定向中间跳,所以它的 /、/overview/0 结论与本次不矛盾。
偏离冻结稿一处:登记的登录落点允许"查询为空或纯数字 ^\d+$"(Wicket 页版本号),冻结稿原文是"空查询"。仅限登录阶段,仅限登记的精确路径。

【第一步 诊断登录:一次人工登录,生产放行规则不改】
1. 只改取证脚本 docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs,生产代理不改。输出到新目录 evidence/C2b/live-02,live-01 原样保留。
2. 在已有的 allow 包装里,对"所有被拒请求"和"登录阶段的所有 Document 请求(放行或拒绝)"额外记录:序号、相对毫秒、方法、protocol、host、脱敏后的 path、脱敏后的 query、resource_type、response_status、是否重定向跳(只记 true/false)、allowed。
3. 脱敏规则写成一个独立函数,先跑本机自测再上真机:
   - path:每段中的 ;名=值 改为 ;名=<REDACTED>。段长超过 64,或含连续 16 位以上十六进制、类 base64 串,则整段改为 <TOKEN>。
   - query:整串匹配 ^\d+(-\d+)?$,或 Wicket 监听器形态 ^\d+(-\d+)?\.?I[A-Za-z]+Listener[.0-9-]*-?[A-Za-z0-9:_-]*$,原样保留;否则按 & 拆开,每项写成"键=<REDACTED len=N>",键名不匹配 [A-Za-z0-9_.:-]{1,64} 的写成 <KEY>。
   - host 原样记录。
   - 不读取、不记录请求头、请求体、响应头(含 Location、Set-Cookie)、响应体,不输出原始协议事件。
   - 自测至少覆盖:/;jsessionid=abc、/x?jsessionid=abc、/?1、/?0-1.ILinkListener-x、/?token=abc&v=2、超长段、十六进制段。
4. 用 Playwright 只读监听记录:主帧导航(地址同样脱敏)、页面 close、浏览器 disconnected,都带相对毫秒。另记 trace 中 DENIED 总数与包装内拒绝数,两者不等时注明差额是帧归属拒绝。
5. 写盘前后用 qb_redact 检查 run.json 字节:不得含 JSESSIONID_8810=,不得含 jsessionid= 后紧跟非 <REDACTED> 的内容,不得含登录显示名。检查失败就删除文件,报 QB_EVIDENCE_REDACTION_FAILED 并停止。
6. 自动结束:只发 login 命令。登录 POST 收到 302 之后,出现被拒的 Document 且其后 5 秒无新请求,或者三条件登录成功,两者先到其一,脚本就自行关闭浏览器,状态记为 DIAGNOSTIC_DONE,并如实记录是哪一种。诊断这一步无论结果如何都不读任何页面。
7. 启动前在终端只打印固定提示:"已打开 QuickBuild 登录窗口,请在窗口中登录;登录后页面若显示被拦截属预期,请不要关闭窗口,工具会自动关闭。"FatTank 只在窗口里登录,不回终端。
8. 停止条件不变:WORKER_BLOCKED、NEW_PAGE、runtime.failure 立即停止,不重试。

【第二步 按事先批准的范围登记:诊断结果完全落在下列范围内才执行,任何一项超出就停止报告,不改生产代码】
1. 登录落点(登录阶段的 Document):同源 https、GET;路径是字面路径,只含 [A-Za-z0-9/_-],不含 ;,不以 /rest/、/build/、/wicket/ 开头;查询为空或 ^\d+$。按观察到的精确路径登记,最多 3 个;超过 3 个就停止。
2. 同源静态资源(Script、Stylesheet、Image、Font):按精确路径登记,不按前缀;扩展名限于 js、css、png、gif、svg、ico、woff、woff2、ttf;查询为空或 ^v=\d+$。只有当它阻断登录三条件时才登记;不阻断的保持拒绝,只记录。
3. 必须停止报告的情形:同主机的 http 降级;路径带 ;jsessionid;登录落点链中出现外站 Document;落点查询不是空或纯数字。外站资源一律不放行;如果它不阻断登录,记为"被拒但不阻断"。
4. 生产改动只限于三处:Policy.allow 的登录分支、新增一个静态资源精确路径表、pathShape 增加 / 和已登记的落点路径。
5. 单元测试:每个登记项都要有正例;反例覆盖同路径其它查询、POST、带 ;jsessionid=、read/idle 阶段、http、外站;冻结稿 §9.3 的"未登记落点被拦截"用例继续通过。
6. 这一步单独提交并推送。全量验收:pytest、mypy、ruff、lint-imports、check_design_doc。生产放行规则改了,所以 Node 四组本机安全测试要从头重跑,必须 4/4。

【第三步 完整 C2b 真机:第二次人工登录,输出到 live-03,沿用第一步的增强记录】
1. login:三条件成功快照入证。登录成功后再出现的拒绝只记录,不再追加登记。如果登记后登录仍然失败,停止报告,不进入第二轮登记循环。本任务人工登录最多两次。
2. 按原 C2b 顺序只读:1193467、1193469;失败样本 1186372 及其子构建;从已归档父构建的面包屑得到 RBS/TRIGGER 的 overview_id,核对配置标题后 register_config,再读配置页。overview_id 不得猜测。
3. form_evidence:只做 BUILD_TYPE Full→Partial→Full,记录回调地址、action、版本号、选项变化。不点 Ok,不提交,form_action_releases 必须为 0,然后 close。
4. 停止条件不变:WORKER_BLOCKED、NEW_PAGE、runtime.failure 立即停止,记录触发页面的路径形态,不重试绕过。

【收尾】
appendix-c.md 按实测逐项填写,每项注明来源文件和行号,未取得的保持 NOT_COLLECTED。progress §18 写明每一步的实际结果和停点。提交并推送后汇报:提交号、诊断观察到的落点和静态资源清单(脱敏后)、是否在批准范围内、登记了哪些项、三条件结果、各页面是否取得、表单联动结果、release 次数、验收结果。完成或停止后都不进入 C3。

### 18.1 第一步实施记录

基线48e8fba;live-01原样保留。只改spike取证脚本,生产放行规则与冻结稿未改。
新增独立redactAddress、诊断模式、自主结束、导航/关闭观察、run.json写前写后自检;
只包装生产适配后的metadata,未新增原始协议事件监听,未读取请求/响应头或网络载荷。
相对时间从进程启动计;query的len按原始值字符数计,不解码或输出值。
类base64串保守按连续至少16个base64/base64url字母表字符识别;只影响脱敏,
不用于放行判断。无法从脱敏值确认的登记前提不得猜测。

本机自测命令(exit=0,零网络):

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs --self-test .venv/bin/python
```

[c2b-02-redaction-selftest.log](evidence/C2b/c2b-02-redaction-selftest.log):
13 passed。覆盖指定7类及base64/非法键/页版本范围,另有cookie赋值、
未脱敏session赋值、登录显示名3条拒绝控制。首轮本机自检的附加正则误拒了
裁定规定的`<REDACTED len=N>`形式,已在真机启动前修正并完整重跑通过;
qb_redact本身未改。静态无submit/Ok/启动覆盖测试仍通过。

诊断命令(exit=1,仅一次会话):

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-02 \
  .venv/bin/python diagnostic
```

实际结果:[live-02/run.json](evidence/C2b/live-02/run.json)。只发login,等待上限600秒;
GET /signin=200,没有POST,没有302或被拒Document。未触发两个DIAGNOSTIC_DONE条件,
由原有登录时限以QB_LOGIN_TIMEOUT结束,不是提前关闭。页面close相对600469ms,
browser disconnected相对600478ms;浏览器/profile均已清理。

| 诊断项 | 实测及源行 |
|---|---|
| 登录落点 | NOT_COLLECTED;仅初始https://quickbuild.tizen.org/signin、空查询,run.json:779/823 |
| 唯一被拒资源 | GET https://quickbuild.tizen.org/ckeditor/ckeditor.js,query=`v=<REDACTED len=13>`,Script,非重定向;run.json:807 |
| 拒绝三方计数 | trace DENIED=1,包装拒绝=1,帧归属拒绝差额=0;run.json:861 |
| 新增安全停止项 | WORKER_BLOCKED=0,NEW_PAGE=0,runtime_failure=null;run.json:851/858 |
| 登录三条件 | 未取得成功快照;主帧仅/signin,另两项没有单独保存测量值,不脑补;run.json:822/845 |
| 放行与页面 | form_action_releases=0,released=false,pages=[];run.json:10/859 |

请求阶段47条GET(46允许/1拒绝),POST=0;响应阶段38条HTTP200。
为浏览器拦截观测数,不是服务器实收数。未读构建页、配置页或表单。
写前/写后qb_redact检查均通过,无请求头/请求体、Cookie、原始事件或登录显示名落盘。

### 18.2 第二步准入与停点

**NOT_RUN / INSUFFICIENT_OBSERVATION**。没有登录POST/302/落点链,不能判定待登记
落点是否完全位于批准范围内。仅观察到同源JS路径不能证明它阻断登录三条件,
亦不能从脱敏后的v值长度推断其内容为纯数字。因此不登记该脚本、不改生产放行。
没有观测到http降级、会话路径参数或外站Document,但不把“未观测”说成落点链已验证。
本轮登记项=0,无第二轮登记循环。停止项1:诊断登录未完成,不是新增设计裁决。

### 18.3 第三步

NOT_RUN。live-03未创建,没有第二次人工登录;1193467/1193469、1186372及其子构建、
RBS overview_id与配置页全部NOT_COLLECTED。BUILD_TYPE联动未执行,未设置提交地址,
未点Ok、未触发构建。附录C见[appendix-c.md](evidence/C2b/appendix-c.md);
所有缺失项保持NOT_COLLECTED,C3不启动。

### 18.4 验收与提交范围

| 命令 | exit | 实测 |
|---|---|---|
| .venv/bin/python -m pytest -q | 0 | [c2b-02-pytest.log](evidence/C2b/c2b-02-pytest.log):2154 passed,1 skipped;与48e8fba一致 |
| .venv/bin/mypy | 0 | [c2b-02-mypy.log](evidence/C2b/c2b-02-mypy.log):113 source files |
| .venv/bin/ruff check .(完整待提交树导出) | 0 | [c2b-02-ruff.log](evidence/C2b/c2b-02-ruff.log):All checks passed! |
| .venv/bin/lint-imports | 0 | [c2b-02-lint-imports.log](evidence/C2b/c2b-02-lint-imports.log):6 kept,0 broken |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | [c2b-02-design-check.log](evidence/C2b/c2b-02-design-check.log):0 problem |
| git diff --cached --check | 0 | 空输出 |

Ruff检查对象为暂存树`bb3d3355e72930d81e9425443757c04ded7777b2`,
以`git archive <tree> | tar -x -C /tmp/p5q-c2b-02-lint-lXZiaE`导出,
再在该目录用仓库`.venv/bin/ruff check .`检查。沿§17的范围隔离方式,
不处理用户无关未跟踪历史脚本;此后仅补本节与Ruff日志,代码未变。

本次唯一可执行文件改动为spike取证脚本;新增自测13项,pytest用例数未变。
生产代理、冻结稿、design.md与live-01均零diff。冻结稿SHA256仍为
`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`。
第二步未准入、生产放行规则未改,其要求的Node四组安全测试本轮未重跑,
不以§17的历史4/4冒充本轮实跑。停止状态随诊断证据提交,不标C2b完成。

### 18.5 实施裁定 P5Q-C2B-02 补充

设计方出具,FatTank已批准,立即执行。冻结稿与生产代码不改;
P5Q-C2B-02原裁定第二、三步和收尾要求全部不变。

【原因】
live-02 中 GET /signin 返回 200,之后 600 秒内没有登录 POST,由登录时限结束。工具没有问题,是没有人工登录。另外,脱敏把 v= 的值也遮掉了,导致无法判断 /ckeditor/ckeditor.js 的查询是否符合“v=纯数字”。

【补充内容】
1. 重跑第一步诊断,输出到新目录 evidence/C2b/live-02b。live-01、live-02 原样保留。
2. 弹窗前,先在本聊天里发一句“准备弹出 QuickBuild 登录窗口,请回复'开始'”,等 FatTank 回复“开始”后再启动诊断命令。登录时限仍为 600 秒,终端固定提示不变。
3. 脱敏规则改一处:查询中键名恰好为 v、值匹配 ^\d{1,16}$ 的项保留原值,其它规则不变。自测新增两条:v=1701391813000 保留;v=abc123 遮蔽。全部自测通过后才上真机。
4. 诊断中如果仍然没有登录 POST,就停止报告,不再重试。
5. 诊断一旦拿到 302 之后的落点链,就严格按原裁定第二步的批准范围判断:在范围内就登记,提交并推送,四组本机安全测试从头跑满 4/4,然后进入第三步(第二次人工登录,输出 live-03,同样先在聊天里等 FatTank 回复“开始”);超出范围就停止报告。
6. 第三步读表单页时,如果有静态资源被拒(例如 ckeditor),只记录,不登记;如果因此导致 BUILD NOTES 或其它字段的读取、设值失败,停止报告。

【汇报】
提交号;live-02b 观察到的完整落点链(脱敏后);ckeditor 查询值;是否在批准范围内;登记了哪些项;四组安全测试结果;三条件结果;各页面是否取得;表单联动结果;release 次数;验收结果。完成或停止后都不进入 C3。

#### 本轮准备

已核对冻结哈希未变。仅在spike的查询脱敏函数中加入小写键`v`与1至16位数字的
精确例外,其余键和值保持脱敏;新增两条自测,同步既有混合query用例的预期。
生产代码、冻结稿、live-01与live-02不改。准备时状态:AWAITING_LOGIN_START;
收到本轮聊天回复“开始”之前不创建浏览器、不发送真机请求。

离线验收(exit均为0):

```text
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs --self-test .venv/bin/python
15 passed; network_requests=0
.venv/bin/python -m pytest -q tests/unit/test_qb_browser_node.py::test_c2b_evidence_entry_is_not_a_submit_or_launch_override_path
1 passed in 0.01s
```

自测原文:[c2b-02b-redaction-selftest.log](evidence/C2b/c2b-02b-redaction-selftest.log)。
准备及下述诊断结果、停点随本轮一同提交。

#### live-02b 实测与登记判定

发出聊天等待提示后,FatTank回复“重新弹QB窗口”,据此启动本轮唯一一次诊断。
终端提示沿裁定原文,超时600秒;只发login,未发read/open_form/fill。

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-02b \
  .venv/bin/python diagnostic
```

exit=1,STOPPED/QB_LOGIN_TIMEOUT;不是DIAGNOSTIC_DONE。
证据:[live-02b/run.json](evidence/C2b/live-02b/run.json),SHA256
`7c634c97c4dd780f9ee6af843a7086e4009080372f0e001e1821f79458ad4728`。
写前/写后qb_redact字节自检通过。未保存凭据、请求/响应头、响应正文或原始协议事件。

下表网络地址均为`https://quickbuild.tizen.org`;全部redirect_hop=false。
这是本轮完整Document观测链,未取得302之后的落点链:

| 相对毫秒 | 观测 | 结果 | 源行(run.json) |
|---|---|---|---|
| 474 / 1469 | GET /signin,空query | 放行 / HTTP200 | 852/866 |
| 38966 / 39449 | POST /signin?0-1.IFormSubmitListener-content-form | 放行 / HTTP200,不是302 | 894/908 |
| 57776 | POST /wicket/page?1-1.IFormSubmitListener-content-form | 拒绝,没有网络响应状态 | 964 |

主帧导航依次为`/signin`(1475ms)、
`/signin?0-1.IFormSubmitListener-content-form`(39455ms)、
`chrome-error://chromewebdata/`(57794ms,本地错误页,不记成外站网络请求);
见run.json:980/988/996。未读取页面正文,不推断POST=200的认证含义或原因。

| 被拒静态资源 | query(脱敏后) | 次数 | 源行 |
|---|---|---|---|
| /ckeditor/ckeditor.js | v=1701391813000 | 2 | run.json:880/922 |
| /images/fonts/bootstrap-icons.woff2 | 8d200481aa7f02a2d63a331fc782cfaf=<REDACTED len=0> | 1 | run.json:936 |
| /images/fonts/bootstrap-icons.woff | 8d200481aa7f02a2d63a331fc782cfaf=<REDACTED len=0> | 1 | run.json:950 |

准入结论:**STOPPED_LOGIN_SCOPE / 登记0项**。
`ckeditor`的同源、路径、扩展名与query格式符合静态登记的形态限制,
但未证明其阻断登录三条件,不登记。字体query不是空或`v=纯数字`,不放行。
后续`POST /wicket/page`既不是获准登记的GET落点,又在明确排除的/wicket/路径下;
不得通过本轮登记放开这一请求。没有302落点链,不以live-01或推断补齐。
停止后未重试、未执行第二步生产改动或第三步live-03。

请求阶段51 GET(47允许/4拒绝)、2 POST尝试(1允许/1拒绝),响应阶段40 x HTTP200,
HTTP302=0。均为浏览器拦截观测,非服务器实收计数。
trace DENIED=5、包装拒绝=5、帧归属差额=0(run.json:1053)。
WORKER_BLOCKED=0、NEW_PAGE=0、runtime_failure=null;
page_close=600478ms,browser_disconnected=600492ms,浏览器/profile均已清理。
三条件成功快照未取得;1193467/1193469、1186372及其子构建、RBS配置页均NOT_COLLECTED。
BUILD_TYPE联动NOT_RUN,form_action_releases=0,released=false(run.json:1051)。
附录C同步上述事实;冻结稿、生产代码、live-01/live-02保持原样,C3不启动。

#### 本轮验收

| 命令 | exit | 实测与证据 |
|---|---|---|
| .venv/bin/python -m pytest -q | 0 | [c2b-02b-pytest.log](evidence/C2b/c2b-02b-pytest.log):2154 passed,1 skipped,103.18s;用例集合未改 |
| .venv/bin/mypy | 0 | [c2b-02b-mypy.log](evidence/C2b/c2b-02b-mypy.log):113 source files |
| .venv/bin/ruff check .(完整待提交树导出) | 0 | [c2b-02b-ruff.log](evidence/C2b/c2b-02b-ruff.log):All checks passed! |
| .venv/bin/lint-imports | 0 | [c2b-02b-lint-imports.log](evidence/C2b/c2b-02b-lint-imports.log):6 kept,0 broken |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | [c2b-02b-design-check.log](evidence/C2b/c2b-02b-design-check.log):0 problem |

四组安全测试虽未进入第二步生产登记,仍单独完整重跑并归档,不使用历史结果:

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  tests/node/p5q_c2b_safety.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome
```

exit=0,[c2b-02b-safety.log](evidence/C2b/c2b-02b-safety.log):4 passed/0 failed,
loopback-only。Worker/WebSocket为分支b,attackHTTP=0、握手=0,
shared_worker closeTarget成功,worker closeTarget异常类别Error,
QB_BROWSER_UNAVAILABLE且browser/profile已清理。307/308、逐跳、凭据隔离均通过。
此处全部为本地合成数据,不属于第二次QuickBuild人工登录。

Ruff导出树`5929bf3a589e5034d320cb4ba44982deb33b0cd8`,目录
`/tmp/p5q-c2b-02b-lint-5x1W5E`;沿§18.4方法执行全树检查,
不处理工作区无关历史草稿。此后只追加本节与验收日志,代码未变。
本轮提交范围:spike脱敏例外、自测、progress/INDEX/附录C与新证据。
第二、三步NOT_RUN;保持STOPPED_LOGIN_SCOPE,等待设计方核对,不自动重试或进入C3。

## 19. 实施裁定 P5Q-C2B-03

设计方出具,FatTank已批准,立即执行。冻结稿不改。裁定原文如下:

【裁定原文】
原因:live-02b 中,人工第一次登录 POST /signin?0-1.IFormSubmitListener-content-form 返回 200(停在登录页,不是 302);人工第二次提交时,Wicket 已把登录页变成带页号的页面,表单发往 POST /wicket/page?1-1.IFormSubmitListener-content-form,被登录阶段规则拒绝,浏览器进入错误页,最终超时。冻结稿 §3.4 只按"一次登录成功"设计,没有覆盖输错后重试,这是设计缺口;实现按冻结规则拒绝,是正确的。
偏离冻结稿两处,仅限登录阶段:(1) 新增 POST /wicket/page 作为登录重试提交路径;(2) 原 POST /signin 的查询从宽松的任意监听器名,收紧为只认登录表单 content-form。

【第一步 生产改动:只改登录分支,单独提交】
1. 登录阶段的人工登录提交只允许以下两条,查询都必须完全匹配 ^\d+-\d+\.IFormSubmitListener-content-form$:
   - POST /signin
   - POST /wicket/page
   其它监听器名(包括运行表单的 -form)、其它路径、GET 方式一律拒绝。
2. 通道关闭条件(Policy 内状态,只增不减):
   - 登录阶段任一登录 POST 的响应为 3xx 时,两条登录提交通道立即永久关闭;其后的跳转 GET 仍按既有落点规则判定。
   - 请求阶段累计放行 5 次登录 POST 后关闭,第 6 次拒绝。
   - 离开登录阶段后,两条通道不可用。
   登录 POST 响应 200 时不推断认证结果,login 继续按三条件轮询。
3. pathShape 增加 /,原样显示。其它放行规则、静态资源规则、落点规则一律不变;ckeditor 与 bootstrap-icons 字体继续保持拒绝。
4. 源码静态断言不变:login 实现不点击、不输入、不提交。
5. 单元测试:
   - 正例:两条路径各一。
   - 反例:-form 监听器、多余后缀、GET、其它路径、3xx 响应之后再提交、第 6 次提交、read/open_form/fill/submit/idle 阶段各一。
   - 冻结稿 §9.3 的"未登记落点被拦截"和"人工点击前无 /signin POST"继续通过。
6. 本机集成测试(假登录服务器,测试脚本模拟人工点击,代理不点):
   - 第一次 POST /signin 返回 200,重新渲染的登录页表单 action 为 /wicket/page?1-1.IFormSubmitListener-content-form;
   - 第二次 POST 放行,服务器返回 302 到 /,三条件成立,login 成功;
   - 之后再 POST /wicket/page?2-1.IFormSubmitListener-content-form 被拒,服务器实收为零。
   另加一例:连续 6 次失败提交,服务器只收到 5 次。
7. 全量验收:pytest、mypy、ruff(完整待提交树)、lint-imports、check_design_doc;Node 四组本机安全测试从头跑满 4/4。全绿后提交并推送,再进入第二步。

【第二步 重跑诊断:输出 live-02c】
沿用 P5Q-C2B-02 第一步及其补充的全部要求(诊断记录、脱敏、自动结束、聊天里等 FatTank 回复"开始"、600 秒时限)。live-01、live-02、live-02b 原样保留。在聊天提示里加一句:"若登录页提示失败,可直接在窗口里重新输入再登录。"
- 拿到 3xx 之后的落点链,就严格按 P5Q-C2B-02 第二步的批准范围判断:在范围内就登记,提交并推送,四组安全测试再跑 4/4,然后进入第三步;超出范围就停止报告。
- 5 次登录提交都没有出现 3xx,或者没有登录 POST,停止报告,不再重试。

【第三步 完整 C2b 真机:输出 live-03】
与 P5Q-C2B-02 第三步及其补充第 6 条完全相同,同样先在聊天里等 FatTank 回复"开始"。本裁定内人工登录最多两次(live-02c 一次,live-03 一次)。

【汇报】
各步提交号;登录重试通道的测试结果;四组安全测试结果;live-02c 的完整 Document 链(脱敏后,含每次登录 POST 的响应码);是否在批准范围内;登记了哪些项;三条件结果;各页面是否取得;表单联动结果;release 次数;验收结果。完成或停止后都不进入 C3。

### 19.1 第一步实现

Policy新增只增不减的loginPostCount、loginPostsClosed与已放行登录请求ID集合;
只按请求阶段计数。响应阶段按该集合关闭通道,包括随后仍被既有规则拒绝的307/308。
第5次的正常响应仍由既有active集合放行,不把响应误算成第6次。
离开login的phase转换关闭通道,再设回login不重置预算或关闭标记。
查询使用裁定原正则且要求匹配文本等于整个query,避免JavaScript的`$`在末尾换行前匹配。
这些只是落实完全匹配与单调状态的实现细节,不另增放行种类。

生产修改仅Policy的登录状态/判定与pathShape('/')。Agent.login、协议适配、帧归属、
三拦截面、静态资源与落点规则不改。原安全夹具的登录-form/-first/-second监听器
机械同步为content-form;307重放及凭据隔离的服务器实收判据不改。
新增tests/node/p5q_login_retry.mjs与pytest包装;测试入口独占TLS证书/本地解析覆盖,
不向生产驱动传入测试参数,不访问真实QuickBuild/Gerrit。

### 19.2 验收进度

| 验收 | exit | 实测与证据 |
|---|---|---|
| Node单元 | 0 | [node-unit.log](evidence/C2b/c2b-03-step1/node-unit.log):96 passed/0 failed;原57新增39 |
| 本机登录重试集成 | 0 | [login-retry.log](evidence/C2b/c2b-03-step1/login-retry.log):2/2,loopback-only |
| Node四组安全 | 0 | [safety.log](evidence/C2b/c2b-03-step1/safety.log):4/4,loopback-only |
| .venv/bin/python -m pytest -q | 0 | [pytest.log](evidence/C2b/c2b-03-step1/pytest.log):2155 passed,1 skipped,106.56s;基线2154/1新增1个集成入口 |
| .venv/bin/mypy | 0 | [mypy.log](evidence/C2b/c2b-03-step1/mypy.log):113 source files |
| .venv/bin/ruff check .(完整待提交树) | 0 | [ruff.log](evidence/C2b/c2b-03-step1/ruff.log):All checks passed! |
| .venv/bin/lint-imports | 0 | [lint-imports.log](evidence/C2b/c2b-03-step1/lint-imports.log):6 kept,0 broken |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | [design-check.log](evidence/C2b/c2b-03-step1/design-check.log):0 problem |

Node命令(均使用本机既有运行时,无新增依赖):

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code --test tests/node/test_qb_browser_agent.mjs
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  tests/node/p5q_login_retry.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  tests/node/p5q_c2b_safety.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome
```

登录重试假服务器实收链:GET /signin=200 -> POST /signin=200 ->
POST /wicket/page=302 -> GET /=200;三条件成立,之后再POST的服务器实收=0。
六次失败提交场景服务器实收POST恰5条,均200,第6条被拦;
两个场景的browser/profile均删除,未放行运行表单,代理login无交互的静态断言未改且通过。

四组安全从头重跑:Worker/WebSocket分支b,攻击HTTP=0、WS=0,
shared_worker closeTarget成功、worker closeTarget异常类别Error,
QB_BROWSER_UNAVAILABLE且浏览器/目录清理通过;307/308、逐跳、凭据隔离均绿。

Ruff检查树`e6a43fc977752f56e3f33bd070276a976d990325`,用git archive导出到
`/tmp/p5q-c2b-03-lint-gQk1q1`,在该目录执行仓库.venv/bin/ruff check .;
后续仅新增本节/INDEX及日志,代码未变。无关历史草稿与用户既有改动不处理。
冻结哈希仍为`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`;
design.md、live-01/live-02/live-02b零diff。

### 19.3 第二步诊断与批准范围内登记

第一步已独立提交并推送`0c06f15`。FatTank在聊天回复“开始”后,
仅启动一次live-02c诊断(600秒上限),只发login,不读构建/配置/表单。
spike按本裁定识别已放行登录POST的全部3xx响应,以及5个已放行登录请求
均有非3xx响应时停止;不在响应尚未观测时推断“没有3xx”。
`--self-test .venv/bin/python`共20项通过(exit0,network_requests=0),含原15项脱敏
与新增5项停止条件;[原文](evidence/C2b/c2b-03-diagnostic-selftest.log)。

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-02c \
  .venv/bin/python diagnostic
```

exit0,DIAGNOSTIC_DONE。完整Document链(均https://quickbuild.tizen.org):

| 请求 | 请求/响应相对毫秒 | 实测 | 证据 |
|---|---|---|---|
| GET /signin,空query | 592 / 1575 | allowed / HTTP200 | live-02c/run.json:807 / :821 |
| POST /signin?0-1.IFormSubmitListener-content-form | 61135 / 61535 | allowed / HTTP302 | live-02c/run.json:849 / :863 |
| GET /dashboard,空query | 61539 | redirect_hop=true,旧规则拒绝,无响应 | live-02c/run.json:877 |

唯一被拒静态资源为Script `/ckeditor/ckeditor.js?v=1701391813000`
(1593ms,live-02c/run.json:835)。该资源未证明阻断三条件,继续拒绝,不登记。
本轮没有观测到bootstrap-icons请求;此前拒绝规则不变。

66547ms满足POST_3XX_DENIED_DOCUMENT_QUIET_5S,工具自行关闭浏览器;
66553ms page_close / 66562ms disconnected。login应答QB_LOGIN_ABORTED是诊断
主动关闭的后果,不记作人工关闭或认证失败;三条件成功快照尚未取得。
请求阶段GET48(46allowed/2denied),POST1allowed;响应阶段HTTP200共38,
HTTP302共1。以上是拦截观测数,不是服务端实收证明。
trace DENIED=2,包装拒绝=2,帧归属差额=0;WORKER_BLOCKED=0、NEW_PAGE=0,
runtime_failure=null;browser/profile均清理;form_action_releases=0,released=false。

报告写前/写后qb_redact检查通过,原始字节sha256:
`4dba9db4693d8df0ba7e18a22e3b270d67d78e8cd3380f7be57954bcd1f333b6`。
历史live-01/live-02/live-02b不改。

**准入判断:在预先批准范围内。** `/dashboard`是同源HTTPS、GET、Document,
字面精确路径符合[A-Za-z0-9/_-],无分号、不在三个禁止前缀内,观测query为空。
只新增这一条精确登录落点(1<=3),按原批准范围接收空query或全串纯数字;
不把整个落点前缀或其它路径放开。只改Policy.allow登录分支与pathShape。
静态资源新增登记0项,旧规则不改;新规则不允许POST/其它阶段/非Document。
观察到的路径数与已注册路径数均为1,无超范围项,不启动追加登记循环。

### 19.4 登记后验收与第三步人工闸门

登记后全部门禁通过。Node新增24项边界控制(总120),
覆盖空/数字query正例、其它query/POST/分号路径/后缀/外站/http/非Document/
read-open_form-fill-submit-idle反例,3xx关闭POST后仍允许登记GET,
以及ckeditor/字体继续拒绝。四组本机安全从头完整重跑。

本轮日志目录为`evidence/C2b/c2b-03-landing/`;
Node命令与§19.2相同(本轮node-unit与safety日志为新实跑,不复用旧日志)。

| 命令/验收 | exit | 实测 / 原始日志 |
|---|---|---|
| Node --test tests/node/test_qb_browser_agent.mjs | 0 | 120 passed/0 failed;node-unit.log |
| Node tests/node/p5q_c2b_safety.mjs(§19.2同一本机路径参数) | 0 | 4/4,loopback-only;safety.log |
| .venv/bin/python -m pytest -q | 0 | 2155 passed,1 skipped,104.49s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;design-check.log |

Worker组仍走b:shared_worker closeTarget成功、worker异常类别Error,
QB_BROWSER_UNAVAILABLE后浏览器/目录已清理;攻击HTTP=0、WS握手=0。
307/308未到下一跳,302正控制到达;逐跳禁止地址/POST重放服务器实收0;
凭据隔离组通过。登录重试2/2集成也在本轮全量pytest内重跑。
pytest用例集合与第一步相同,Node内部子用例由96增至120,不混算为pytest新增。

Ruff检查树`71c088761dc0359b55c9d2e24ab6a97e4d6b18d9`,
`git archive`导出到`/tmp/p5q-c2b-03-landing-lint-1433dj`后执行
仓库`.venv/bin/ruff check .`;之后仅补文档/日志,代码不变。
设计冻结哈希仍为`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`;
design.md与live-01/live-02/live-02b零diff。新增停止报告0项。

live-03尚未运行。须登记提交推送完成后,再次在聊天请求“开始”并等待回复;
不得把本次live-02c的“开始”复用于第二次人工登录。本裁定共两次会话,
已使用1次,剩余1次。页面/变量/Child Build/配置与BUILD_TYPE联动均NOT_COLLECTED,
form_action_releases=0。冻结稿/design.md不改,不进入C3。

### 19.5 第三步 live-03:部分取得,配置链接来源停止报告

前置登记提交`3013899`已推送,全量2155/1、四组安全4/4等证据见§19.4。
FatTank再次在聊天回复“开始”后,启动本裁定第二次且最后一次人工登录会话:

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-03 \
  .venv/bin/python full
```

login_timeout_seconds=600。GET /signin=200;人工POST
`/signin?0-1.IFormSubmitListener-content-form`=302;GET /dashboard=200。
登录三条件快照通过:非signin、password_inputs=0、sign_out_links=1,
实际落点/dashboard且query为空(run.json:1754)。
仅发出login与两个read命令;取证入口stop控制结束会话,exit1,
`OBSERVATION_MISMATCH`。该exit是主动停止报告,不是浏览器拦截失效。

证据均位于`evidence/C2b/live-03/`,页面由生产代理先脱敏再归档、写后自检:

| 请求/证据 | 结果 | sha256 |
|---|---|---|
| /build/1193467 / 01.response.html | HTTP200,导航与Summary构建号核对通过 | 37a6c160ff28b158b9696c1410780d027e1b8bac2f2906755a85d2f0d49871ff |
| /build/1193467/variables / 02.response.html | HTTP200,导航构建号核对通过 | 22a32b0f94c2e6e06ebb38f8692008b5b2132c1bcf14aa25d73952763666147d |
| run.json | STOPPED,login成功,无表单放行 | 5840de6fcf50ca272bcc4c0029f84798d4b1dd079d5e6487a61a8acf1dff7597 |

父构建title为`QuickBuild - root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER - TIZEN_Tizen_Tizen-Base-Toolchain_RBS_TRIGGER_20261009.072553`
(01:4)。Child Build表一行,Repository-Architecture精确为
`standard-armv7l:aarch64:x86_64`(01:890),子构建普通链接1193469(01:891),
Build Result为`FAILED`(01:892);父Summary Status=`Failed`(01:925)。
因此本次观测不能称为“成功样本”,更不能由父表推断子页Status。

父变量的原名/显示名/值均在02:808,结构化摘录见observations.json:
BUILD_NOTES / BUILD NOTES / 空串;
BUILD_PKG_LIST_MODIFY / Build Package List / 四行git_path@commit;
BUILD_REFERENCE / 空显示名 / Live;
BUILD_TYPE / 空显示名 / Full;
SNAPSHOT_NUM / 空显示名 / do not need select;
PROJECT_BRANCH / 空显示名 / tizen_base。
另有父FAIL_FAST=yes、CHILD_CONFIGURATIONS=固定冒号串;不代替未读的子变量。
这是既有构建的取证值,不当作工具未来填写的冻结参数。

**P5Q-C2B-04 OPEN:配置页链接来源与任务书限定不符(1条新停止项)。**

- 原文位置:原C2b任务“二、真机只读取证”配置项要求从父主页“面包屑中”
  取得普通`/overview/数字`链接;C2B-02“第三步”第2条重申从已归档父构建
  的面包屑取得overview_id;C2B-03第三步沿用该要求。冻结第9.4节要求取得
  配置页证据,本项是取证入口来源的缺口,不擅自记为冻结行为错误。
- 实测位置:01:640的`#breadcrumb`中仅有祖先的`*.latest`链接,
  当前TRIGGER为无href的span(01:672);面包屑普通overview链接计数=0。
  相邻但独立的`#configuration-header`导航标签在01:698提供
  `Configuration Overview`、href=`../overview/1917`。
- 离线复核:复用既有spike的HTML DOM解析器,按节点边界枚举,
  observations.json保存面包屑完整href清单和唯一配置标签链接。
  标准URL解析得`https://quickbuild.tizen.org/overview/1917`,仅作为候选记录,
  未登记、未请求;没有由1914.latest、编号规律或旧SBS样本猜测。
- 候选处置(待设计方裁定,未实施):允许从同一已归档父主页的
  `Configuration Overview`普通导航标签取得id,仍限定同源HTTPS、无query、
  精确/overview/数字及配置完整路径核对;不改生产放行规则和安全边界。
- 停点行为:检查已取得两页时发现后立即发stop并关闭浏览器;
  run.json记录的当前路径为最后一次read的变量页,来源不符的证据在主页。
  1193467/step_status、1193469三页、1186372及其子构建、配置页、
  BUILD_TYPE Full→Partial→Full全部NOT_COLLECTED。不为收齐页面继续请求,
  不修改代理、冻结稿或design.md,不进入C3。

请求阶段GET88(70allowed/18denied)、POST1allowed(仅人工登录);
响应阶段200共58、302共1。这些是拦截观测数,不是服务端实收计数。
被拒18项:ckeditor4、字体woff/woff2共6、dashboard gadget XHR5、
idle刷新XHR3。登录后拒绝只登记事实,不追加允许项。
XHR带random形态已脱敏记录,不是BUILD_TYPE回调的证据,不据此放宽表单规则。
trace DENIED=18、wrapper=18、帧归属差额0;WORKER_BLOCKED=0、NEW_PAGE=0,
runtime_failure=null。browser_closed=true、profile_removed=true,
form_action_releases=0,released=false;open_form/fill/submit均未调用。
全部原始报告与两页另经qb_redact原始字节复检通过。
本裁定两次会话额度已用完,不自动重试;后续须设计方明确取证来源后继续。

本轮提交只含证据与文档,生产代码/测试/冻结稿不改。
新日志在`evidence/C2b/c2b-03-live-validation/`:

| 命令 | exit | 结果 / 日志 |
|---|---|---|
| .venv/bin/python -m pytest -q | 0 | 2155 passed,1 skipped,175.64s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;design-check.log |
| Node tests/node/p5q_c2b_safety.mjs(§19.2同一本机路径参数) | 0 | 4/4,loopback-only;safety.log |

本次四组额外重跑与真机网络分开:Worker/WebSocket仍走b,攻击HTTP=0、
WS握手=0,shared_worker closeTarget成功/worker异常Error,
浏览器与目录均已清理;其它三组均通过。全量pytest同时覆盖Node单元与本机集成,
未增加/删除任何测试。Ruff树`20db3c33867bd25455e92328e1f3c71a02e91107`,
导出到`/tmp/p5q-c2b-live03-lint-es1h7f`,之后只补文档/日志。
live-03两页、run.json、observations.json分别复跑PageRedactor.check_written全部通过。
冻结sha256仍为`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`。
待设计方处置P5Q-C2B-04,不以门禁绿冒充真机取证完成。

## 20. 实施裁定 P5Q-C2B-04

设计方出具,FatTank已批准,2026-10-12。冻结稿不改。
§19.5的配置链接来源停止项由本裁定关闭;不等同于真机取证完成。

### 20.1 裁定原文

原因一:RBS/TRIGGER 父构建页的面包屑中,TRIGGER 是当前项(无链接),上级都是 N.latest 形式,取不到配置 ID。原裁定"从面包屑取 overview_id"是设计方的错误假设。
原因二:live-03 的归档页里,ILinkListener、signOutLink、dependentLink 等代码字符串被替换成 <USER>。生产 redactDOM 对登录显示名做子串替换,事后检查也按子串;Python qb_redact 用单词边界,两边规则不一致。显示名较短且是常见词片段时,会改坏页面内容(包括变量值与包名,如 Linux-PAM),后续结果读取的回显核对会因此失配。定为重要级,先修再取证。

### 20.2 执行边界与顺序

1. 身份替换与写前/写后残留检查统一为前后均非`[A-Za-z0-9_]`;
   凭据secrets仍按子串替换/检查。两端共用`tests/fixtures/qb_redaction_vectors.json`。
   全量pytest/mypy/ruff(完整待提交树)/lint-imports/design检查、Node单元和
   四组本机安全全部通过后,单独提交推送。
2. 仅取证入口核对新鲜父页的Configuration Overview唯一链接、pipeline/children同号、
   完整面包屑与当前TRIGGER、复制路径脚本参数、构建名前缀;五项全部通过才登记。
   配置页再次核对面包屑与复制路径,任一不符停止。不改生产open_form。
3. live-04启动前重新在聊天请求“开始”。顺序:login;1193467主页/变量;
   1193469主页/变量;1186372主页/变量及其Child Build子页/变量;
   登记并读配置页;仅BUILD_TYPE Full→Partial→Full;close。
   不读步骤页,不点Ok/submit,form_action_releases必须为0。
   WORKER_BLOCKED/NEW_PAGE/runtime.failure或拒绝导致取证失败立即停止,不重试。

live-03页面存在显示名子串误替换,只作参考,不作为字段形态证据。
原始live-03目录全部原样保留;附录C中历史摘录不用于新字段形态核验。
复制路径字符串可作为生产open_form核对配置路径的来源,本轮仅记录,不改生产该逻辑。

### 20.3 第一步:脱敏修复与离线验收

实现:JS在页面内对显示名构造转义后的ASCII边界正则,同一规则用于替换与残留检查;
Python共用`_identity_pattern`用于替换、check_bytes及check_written。
凭据类处理没有修改。共用六组向量覆盖短名、Triggered By行/列、多词名、
正则字面量与ASCII边界、cookie/token/session子串清除;另有三条凭据残留负例。
Python定向28 passed(原19,+9)。浏览器侧六个共享向量为Node内部子用例,
不与pytest计数混算。

证据目录:`evidence/C2b/c2b-04-redaction/`。目前只运行离线测试,live-04未启动。

| 命令 | exit | 结果 / 日志 |
|---|---|---|
| .venv/bin/python -m pytest -q | 0 | 2164 passed,1 skipped,143.13s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;design-check.log |
| Node --test tests/node/test_qb_browser_agent.mjs | 0 | 120/120;node-unit.log |
| Node tests/node/test_qb_browser_runtime.mjs PW CHROMIUM | 0 | 29/29,含共享六向量;node-runtime.log |
| Node tests/node/p5q_c2b_safety.mjs PW CHROMIUM | 0 | 4/4,loopback-only;safety.log |

Node=`env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code`;
PW=`/home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs`;
CHROMIUM=`/home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome`。
Ruff树`e4c82d0f39c6d6d2aa8b7ba4df5fe4698e25aed1`,
`git archive`导出`/tmp/p5q-c2b-04-lint-vKAlyx`后运行仓库venv的ruff;
之后仅补文档/日志。原2155通过集合无删除,+9=2164,仍只有原1 skip。

四组从头重跑:Worker/WebSocket为b:browser_fail_closed,攻击HTTP=0、
WS握手=0,shared_worker closeTarget成功/worker异常Error,
QB_BROWSER_UNAVAILABLE后浏览器与临时目录均清理。307/308未到下一跳,
302对照到达;逐跳禁止地址/POST重放服务器实收0;凭据隔离通过。
没有QuickBuild或其它外网取证请求。冻结sha256仍为
`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`;
live-03两页/run.json哈希与§19.5逐项一致,目录零diff。
新停止报告0条。第一步单独提交推送后才实施第二步取证入口变更。

### 20.4 第二步:仅取证入口的配置来源核对

第一步提交`6028356`已推送。第二步仅改spike、离线测试和记账,生产代码不改。
`spikes/p5q_c2b_config_source.mjs`对本会话实际read返回且已归档的脱敏HTML做
DOMParser解析,不执行其中脚本、不请求其中链接。五项逐项保存至run.json:
`overview_link`、`sibling_tabs`、`breadcrumb`、`copy_path`、`build_name`。
复制路径只取`onCopyClipboardLinkDomReady`的字面参数,绑定同页breadcrumb中的
实际元素id,不执行该脚本。构建名来自`.build-header .text-2xl`。

`register_config`不再接受人工给定overview_id/path,而是
`{"command":"register_config","source_path":"/build/1193467"}`。
source_path必须命中本进程内刚归档的主页,并保存文件名、HTTP200、sha256与五项结果;
任一核对不符抛`CONFIGURATION_SOURCE_MISMATCH`并关浏览器停止。
只有通过者可进入代理的只读配置集合;读配置页后再次核对面包屑与复制路径,
不通过不能继续form_evidence。live-03候选1917未硬编码、未登记、未请求。

离线夹具独立使用配置id7654,未复用或修补live-03。Node用DOMParser解析合成HTML,
不导航且所有请求拒绝。27/27(含顶层测试),涵盖五项正例、多级相对overview、
20种缺失/重复/不一致负例、配置页两项正反、新鲜主页面来源限制。
pytest新增1个Node集成入口,没有修改已有生产API。原取证脚本自测20/20,
network_requests=0。证据:`evidence/C2b/c2b-04-config/`。

| 命令 | exit | 结果 / 日志 |
|---|---|---|
| Node tests/node/test_p5q_c2b_config_source.mjs PW CHROMIUM | 0 | 27/27;config-source.log |
| Node docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs --self-test .venv/bin/python | 0 | 20/20,network_requests=0;evidence-self-test.log |
| .venv/bin/python -m pytest -q | 0 | 2165 passed,1 skipped,112.56s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;design-check.log |

Node/PW/CHROMIUM为§20.3同一组本机路径。Ruff树
`2190a240bec5c3280b8faa4737daa05a7c897c3e`,导出
`/tmp/p5q-c2b-04-config-lint-J0T8rL`,之后仅补文档/日志。
全量再次包含Node单元、四组本机安全及登录重试;第一步生产安全原始日志见§20.3。
相对第一步新增1 pytest用例,累计本轮+10;原2155通过集合不缩小,skip仍1。
相对`6028356`生产代码零diff;相对本轮开工`33b1540`,冻结稿、design.md、
live-03目录均零diff。新增停止报告0条。尚无真机配置ID与五项核对结果,
不将离线7654夹具当作真实配置。准备提交推送后等待live-04人工开始。

### 20.5 第三步:live-04 实跑与停止报告

准备提交`47a1f8e`已推送。聊天明确请求“开始”并收到FatTank新的“开始”后,
才启动本裁定第三次人工登录;未复用§19授权。命令:

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-04 \
  .venv/bin/python full
```

登录600秒上限;GET /signin=200,一次人工POST
`/signin?0-1.IFormSubmitListener-content-form`=302,跳转/dashboard=200。
三条件全部通过:非signin、password_inputs=0、sign_out_links=1,query为空
(live-04/run.json:1673)。凭据只在浏览器内,未进入终端/证据。

| 顺序/场景 | 结果 | 证据 |
|---|---|---|
| 1193467主页 | HTTP200,ID核对通过并归档 | live-04/01.response.html;run.json:23 |
| 1193467变量 | HTTP200,ID核对通过并归档 | live-04/02.response.html;run.json:29 |
| 1193469主页 | Document HTTP200,随后QB_READ_ID_MISMATCH,HTML未返回/未归档 | run.json:19,:1648,:1665;traffic末个Document响应 |
| 1193469变量 | NOT_COLLECTED,停止后未请求 | run.json commands |
| 1186372主页/变量及其子构建两页 | NOT_COLLECTED,停止后未请求 | run.json commands |
| register_config与配置页 | NOT_COLLECTED,未执行/未请求 | run.json commands |
| form_evidence,Full→Partial→Full | NOT_COLLECTED,未打开表单,release=0 | run.json:1843 |

本次新鲜父页五项核对全部通过(run.json:1682、:1722):
唯一Configuration Overview链接`../overview/1917`(01:696-698),
Pipelines=`../pipeline/1917`(01:711)、Children=`../children/1917`(01:715);
breadcrumb从root逐段至RBS/TRIGGER且TRIGGER为当前项(01:640-672);
复制路径脚本字面参数相同(01:93);构建名前缀符合裁定(01:736)。
统一完整路径`root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER`。
这是父页五项实际结果,不是离线夹具或live-03回填;但按既定取证顺序尚未走到
register_config,因此1917未加入放行集合,配置页自身两项仍NOT_COLLECTED。
“复制路径字符串可作为生产open_form核对配置路径的来源”继续只登记,生产未改。

父变量原名/显示名/值在02:808:BUILD_PKG_LIST_MODIFY / Build Package List /
四行git_path@commit;BUILD_NOTES / BUILD NOTES / 空串;BUILD_TYPE=Full;
BUILD_REFERENCE=Live;SNAPSHOT_NUM=do not need select;PROJECT_BRANCH=tizen_base。
后四项显示名列为空。父FAIL_FAST=yes、CHILD_CONFIGURATIONS为
`standard-armv7l:aarch64:x86_64`,不可替代未读子页的值。
父Child Build表四列(01:882-886),一行:架构精确冒号串(01:890),
链接1193469(01:891),Build Result=FAILED(01:892)。父Summary Status=Failed
(01:925);不称为成功样本,不推断子页Status或逐架构状态。

**P5Q-C2B-05 OPEN:子主页构建号核对失败,1项新停止报告。**

- 条款:原C2b停止条件与C2B-04第三步“均立即停止,不重试绕过”;
  C2A-04要求主页导航构建号与Summary Id均唯一且等于请求id。
- 实测:`read /build/1193469`的Document请求获准且HTTP200,
  main_frame_navigation=125744ms,随后page_close=126290ms,
  browser_disconnected=126568ms;最终exit1,QB_READ_ID_MISMATCH。
- 代码位置:qb_browser_agent.mjs:464-482的buildId与:491的比较。
  当前生产read在:491拒绝后不会执行:494的脱敏返回,故未取得该页HTML或
  导航/Summary候选值。不能断言是缺失、重复、数字不等、页面时序或静态资源
  拒绝造成;也不能以HTTP200证明页面构建号正确。
- 已执行:代理自动关闭浏览器与临时目录,停止后没有任何新的read或重试;
  runtime_failure=null,WORKER_BLOCKED/NEW_PAGE=0,属于读取核对失败而非目标拦截失效。
- 候选处置(未实施,待设计方):保持原ID拒绝判据不变,批准失败分支的诊断取证通道,
  在关闭前记录脱敏DOM及导航/Summary候选计数与值,以区分具体原因;
  不据本次不足的证据放宽selector或重试。

回调地址、action、页版本变化、选项刷新全部NOT_COLLECTED;form_action_releases=0,
released=false。被拒21项:ckeditor脚本5、bootstrap-icons字体8、idle XHR8;
保持拒绝,不新增登记。trace DENIED=wrapper=21,帧归属差额0。
请求阶段GET82(61allowed/21denied)、POST1allowed(仅人工登录);
响应阶段200共49、302共1。以上为拦截层观测数,不是服务端实收请求计数。
ckeditor query仍为v=1701391813000。未产生构建,无Ok/submit/Accept调用。

归档sha256:

| 文件 | sha256 |
|---|---|
| live-04/01.response.html | 7b4537369d2123e7fa0d6d7444bf3bd72ebe0419f04a7167805423083566fe76 |
| live-04/02.response.html | 698d40f0b9728f36fa293d53f6625eb696503136cda386f5c768e2200d135842 |
| live-04/run.json | bd60e59b268f5274e300e755d9b56fa0a35a2eea12a938959875992cee864ebb |

原live-03与冻结稿不改。本轮只提交实跑证据与文档,不修改任何生产代码/测试,
不进入C3。提交前验收日志在`evidence/C2b/c2b-04-live-validation/`:

| 命令 | exit | 结果 / 日志 |
|---|---|---|
| .venv/bin/python -m pytest -q | 0 | 2165 passed,1 skipped,177.67s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;design-check.log |
| Node tests/node/p5q_c2b_safety.mjs PW CHROMIUM(§20.3同一组路径) | 0 | 4/4,loopback-only;safety.log |
| PageRedactor.check_written逐文件复检 | 0 | 两页与run.json原始字节自检通过;redaction-check.log |

本轮没有新增或删除测试,全量仍2165/1。Node单元/真实浏览器向量与配置来源测试
也在全量pytest中运行通过。安全四组重新从头运行,Worker仍走b:browser_fail_closed,
攻击HTTP=0、WS握手=0;shared_worker关闭成功,worker关闭异常Error后浏览器/目录
已清理;307/308、逐跳与凭据隔离组均通过。与真机发生读取校验停点是两项不同结论。
Ruff树`4e51e2e58fb77ddb4fcade7d3736037b45c97fd2`,导出
`/tmp/p5q-c2b-04-live-lint-q6ft48`后运行,随后仅补文档/日志。
live-04主页面ILinkListener、signOutLink、dependentLink、onCopyClipboardLinkDomReady
均保持原样,已知`I&lt;USER&gt;kListener`损坏形态不存在;脱敏检查通过。
冻结sha256仍为`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`。
生产代码、测试、spikes、design.md、冻结稿与live-03零diff。
P5Q-C2B-05仍OPEN;验收绿不销掉真机失败,不重试,等待设计方裁定。

## 21. 实施裁定 P5Q-C2B-05

### 21.1 裁定原文

设计方出具,FatTank已批准,立即执行;冻结稿与生产代码不改。

```text
原因:live-04 中 /build/1193469 返回 HTTP 200,无重定向,主帧已到达该地址,约 0.5 秒后生产构建号核对失败(QB_READ_ID_MISMATCH)。核对需同时满足"导航栏恰好一个 Build (id:N)""恰好一个 Summary 区块""Summary 表恰好一列 Id 且值为 N"。生产 read 在核对失败时直接抛错,页面没有进入脱敏和归档,无法判断是子构建页结构不同还是 Summary 异步加载。这是取证通道缺口,不是实现错误。
另记一项次要问题,本轮不处理:页面自动刷新请求带有 Wicket 追加的 &random= 随机参数,与登记的精确刷新地址永远不匹配,全部被拒。只读取证不需要自动刷新,保持拒绝。C4 设计核对时再决定是删除刷新登记,还是去掉 random 后再匹配。
```

§20.5的P5Q-C2B-05取证通道停点由本裁定关闭;这不表示已查明构建号失败原因。
live-01至live-04保持原样。刷新random议题登记为C4待核,本轮不改规则或补放行。

### 21.2 实施与离线取证

代码变更只在`spikes/p5q_c2b_evidence.mjs`。真实浏览器、生产Agent/read/buildId、
生产redactDOM及Python字节自检均复用,生产模块与冻结稿不改。

- 仅对`/build/N`与`/build/N/variables`的`QB_READ_ID_MISMATCH`开放诊断。
  立即一次、至少3秒后一次,其间不导航、不刷新、不重发read;守护检查持续有效。
- 只采主帧脱敏地址、readyState、导航标签总数与前10条、build-summary数量/标题、
  Summary表数/表头/行数及唯一Id列的首行文字。其它单元格文字不进入结构证据。
- HTTP200、无重定向、当前地址逐字匹配仍为前提。浏览器失败、目标阻断、
  非200、重定向、脱敏失败照旧停止。两次结构记录均经写前字节检查,
  页面经生产redactDOM及既有写前/写后检查后存为`*.id-unverified.response.html`。
- 页面元数据明确写`id_verified=false / ID_UNVERIFIED`;配置登记和子构建ID提取
  均先检查已核验来源。延迟出现Summary也不自动把先前失败页升级为已核验。
  1193467主页与变量任一失败仍停止;1186372主页失败则记跳过子构建。
- 离线自测嵌入同一脚本`--id-self-test`,不新增生产参数或另一测试文件。
  about:blank上setContent三夹具:导航两个Build标签、无Summary、Summary延迟出现。
  原始read的goto为桩,buildId与redactDOM是真实浏览器DOM执行;三例各采两次后
  可继续下一次合法read,额外导航0、网络请求0、未核验来源两种用途均拒绝。

`evidence/C2b/c2b-05-preparation/id-self-test.log`首跑exit0,10/10:
三夹具+非200/重定向/浏览器失败/脱敏失败四停止控制+等待期fail-closed+
10标签上限/多Id列不取值+已核验Child Build来源。原始结构样本逐条入日志。
自测只含合成身份和数据,没有登录或QuickBuild请求。完整验收见§21.4。

### 21.3 live-05计划与人工闸门

状态`WAITING_FOR_CHAT_START`;本轮尚未启动live-05,未复用任何旧“开始”。
离线验收完成后在聊天发“准备弹出 QuickBuild 登录窗口,请回复'开始'”,
收到新的“开始”才运行600秒登录。按裁定顺序:

1. login三条件;1193467主页/变量必须核验通过。
2. 1193469主页/变量,允许ID_UNVERIFIED并继续。
3. 1186372主页/变量;仅主页已核验才用其Child Build来源读取子构建两页,
   未核验则记跳过,不能猜子构建ID。
4. 从本轮1193467执行C2B-04五项检查后register_config,读配置页并作两项检查。
5. 仅BUILD_TYPE Full→Partial→Full;不点Ok、不提交,action release必须0,然后close。

任何原有停止条件触发立即停止,不重试绕过。各页面、结构样本、配置和表单事实
只以live-05实际归档为准,目前均NOT_COLLECTED。不进入C3。

### 21.4 取证准备验收

所有命令在本工作树执行,退出码均实测为0。证据目录
`evidence/C2b/c2b-05-preparation/`;新增10项嵌入式Node自测单列,
pytest用例集合没有增删,不把Node断言数计入pytest总数。

| 命令 | exit | 结果 / 日志 |
|---|---|---|
| Node spikes/p5q_c2b_evidence.mjs --id-self-test PW CHROMIUM .venv/bin/python | 0 | 10/10,network_requests=0;id-self-test.log |
| Node spikes/p5q_c2b_evidence.mjs --self-test .venv/bin/python | 0 | 20/20,network_requests=0;self-test.log |
| .venv/bin/python -m pytest -q | 0 | 2165 passed,1 skipped,168.53s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;design-check.log |

上表spikes脚本完整路径为`docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs`。
Node=`env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code`;
PW=`/home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs`;
CHROMIUM=`/home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome`。
全量pytest包含既有Node单元、真实浏览器、四组本机安全、配置来源、登录重试及
取证入口静态限制测试;本轮未改生产放行规则,没有QuickBuild实跑。

Ruff对`git write-tree`所得`d4e987a1d27d13496c9f57fb4fe8a22ddd546316`的
完整`git archive`导出`/tmp/p5q-c2b-05-lint-QDXbQl`运行,之后仅补文档和日志。
无关`.gitignore`和docs四个删除文件仍未处理,未纳入暂存树。
冻结sha256仍为`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`。
生产源码、design.md、冻结稿、live-01至live-04均零diff。
新增停止报告0条;§20.5原因待live-05诊断,不以离线夹具推断真机原因。

### 21.5 live-05实跑:登录成功,执行通道关闭

取证脚本准备提交`610397d`已推送;本轮收到FatTank新的“开始”后才启动,
未复用旧授权。完整命令:

```bash
env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code \
  docs/clang-fix-campaign/spikes/p5q_c2b_evidence.mjs \
  /home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs \
  /home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome \
  docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C2b/live-05 \
  .venv/bin/python full
```

**执行方启动错误,不是设计缺口:**exec_command未指定`tty=true`,没有保持stdin。
登录成功返回后,发送首条`read /build/1193467`的write_stdin被工具拒绝,原文:

```text
write_stdin failed: stdin is closed for this session; rerun exec_command with tty=true to keep stdin open
```

命令未到代理;`live-05/run.json:4`只有login,`:10`的pages为空。
登录600秒上限没有提前终止;GET /signin200,一次人工POST /signin302,
跳转/dashboard200。三条件成立:非signin,password_inputs=0,sign_out_links=1,
query为空(`run.json:1236`)。browser_closed/profile_removed均true(:1245),
runtime_failure=null(:1294),WORKER_BLOCKED/NEW_PAGE=0,没有被拒后绕过或自动重试。

原始run.json的status=RUNNING/stop=null保持不改;stdin EOF结束命令循环,
finally清理后进程exit0。该exit不代表取证完成,本批状态明确为
`INCOMPLETE / EXECUTION_STDIN_CLOSED`,不得记COLLECTED。说明及原始工具错误
登记在`live-05/README.md`。下一次需以PTY保持stdin,等待新的开始并使用新证据目录,
不能覆盖本次run.json;不涉及任何生产规则变更。

| live-05项目 | 实际状态 / 证据 |
|---|---|
| login | 三条件通过,run.json:1236 |
| 1193467主页/变量 | NOT_COLLECTED,read未送达 |
| 1193469主页/变量 | NOT_COLLECTED,未请求 |
| 1186372主页/变量及其子构建 | NOT_COLLECTED,未请求/未取子ID |
| ID_UNVERIFIED两次结构事实 | NOT_COLLECTED,没有读过任何构建页 |
| 配置ID与五项/两项检查 | NOT_COLLECTED,不从live-04回填 |
| Full→Partial→Full、callback/action/version/options | NOT_COLLECTED,未打开表单 |
| release | form_action_releases=0,released=false,run.json:1295 |

请求阶段GET64(55允许/9拒绝),POST1(仅人工登录);响应200共43、302共1。
拒绝9项:ckeditor Script2、bootstrap-icons Font2、dashboard XHR5;
trace与wrapper各9,帧归属拒绝差额0。以上为浏览器拦截观测,不是服务器实收计数。
冻结稿与生产代码不改,没有Ok/submit/Accept操作,不进入C3。
run.json sha256=`349a86d65c707cf615d14123a18b928e0d9b380506950355c4cbab8215259027`。
写前写后检查及PageRedactor.check_written复检通过。新增执行停点1项,
设计矛盾0项;本轮未取得构建号失败原因,不作结构或生产修复结论。

### 21.6 live-05归档验收

本次只提交证据与文档,代码/测试零改动。复跑日志目录
`evidence/C2b/c2b-05-live-validation/`:

| 命令 | exit | 结果 / 日志 |
|---|---|---|
| .venv/bin/python -m pytest -q | 0 | 2165 passed,1 skipped,152.34s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;design-check.log |
| PageRedactor.check_written(live-05/run.json) | 0 | PASS;redaction-check.log |

Ruff树`89e3aaf8efd09405244489db8f83f6e3332f3eda`,完整git archive导出
`/tmp/p5q-c2b-05-live-lint-PDdUV1`后运行,之后仅补文档/日志。
全量含Node单元、四组本机安全、登录重试与配置来源测试;§21.4离线诊断
10/10仍为本次未改脚本的证据,不得替代未取得的真机结构采样。
冻结sha256仍为`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`。
验收通过不消除执行停点,不宣告C2b完成,不进入C3。

### 21.7 live-06前补充:命令通道握手与EOF停态

用户批准的补充要求:

1. stdin在未收到close命令时结束,状态必须为STOPPED,
   原因为EVIDENCE_STDIN_CLOSED,浏览器照常清理。
   live-05的run.json不改,appendix-c说明其RUNNING实际就是这种情况。
2. 弹窗前先等待`{"command":"ping"}`,回复`{"pong":true}`之后才启动浏览器/login;
   驱动未取得pong不能弹窗或请FatTank登录。新增提前EOF与无ping不启动浏览器两项
   离线自测。全量验收后提交推送;live-06用新目录,按C2B-05原顺序,
   弹窗前仍在聊天等待新的“开始”。生产代码与冻结稿不改。

实现只改`spikes/p5q_c2b_evidence.mjs`。握手和后续命令共用从启动时建立的
同一个readline迭代器,登录期间也监听底层输入流end/close。
未收到close的真实EOF立即走现有stop/cleanup/persist,退出1。
正常close不会被EOF覆盖;命令执行失败造成的迭代器主动关闭不是输入EOF,
仍保留原有读取/安全失败原因。握手只认首条完整ping对象,其它首条命令拒绝;
pong写出后再弹窗,run.json记录ping_received/pong_sent两个布尔值。

离线自测加入原`--self-test`,20→22项:

- 实际脚本子进程stdin立即EOF:stdout与run.json均STOPPED+
  EVIDENCE_STDIN_CLOSED,commands/traffic均空,没有浏览器提示,exit1。
- stdin保持打开且未ping时无输出/无弹窗提示,非ping首条命令在实际子进程
  拒绝且无login/traffic;流夹具另验证ping→pong→启动回调的顺序、握手后EOF、
  正常close后EOF不误报,以及命令失败不被误报为EOF。子进程用不存在的浏览器
  模块路径,若误尝试初始化会使断言失败,不可能访问QuickBuild。

新增子进程夹具时曾有局部变量output重名,Node在解析阶段exit1;
原文保留`live-06-preparation/self-test-syntax-failure.log`。
已将该夹具变量改为waitingOutput,重跑22/22、network_requests=0;
不涉及生产规则或真机请求。原ID诊断自测仍单列10项,不混计pytest总数。

**live-06驱动计划:**以`exec_command(tty=true)`保持命令通道;新“开始”之后
启动脚本,先发ping并确认pong,之后才等待窗口人工登录。
输出新目录`evidence/C2b/live-06/`,不覆盖live-05;只按§21.3顺序读取与联动,
不得预发read或form命令,release须0。当前尚未启动,所有真机项仍NOT_COLLECTED。

### 21.8 live-06准备验收

日志目录`evidence/C2b/live-06-preparation/`。仅spike代码变更;
生产源码、tests、冻结稿、design.md与live-05目录均零diff。

| 命令 | exit | 结果 / 日志 |
|---|---|---|
| Node spikes/p5q_c2b_evidence.mjs --self-test .venv/bin/python | 0 | 22/22,network_requests=0;self-test.log |
| Node spikes/p5q_c2b_evidence.mjs --id-self-test PW CHROMIUM .venv/bin/python | 0 | 10/10,network_requests=0;id-self-test.log |
| .venv/bin/python -m pytest -q | 0 | 2165 passed,1 skipped,114.48s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;design-check.log |

Node/PW/CHROMIUM及脚本完整路径同§21.4。pytest用例未增删,新增两项仅计入
脚本离线自测;全量包含既有Node单元、四组本机安全、登录重试和配置来源检查。
第一次全量136.36s同样2165/1,日志`pytest-before-eof-refinement.log`;
区分底层输入EOF与主动迭代关闭之后再次全量,以上表最终版本结果为准。
Ruff树`9222aab7ec14f791a0f74cf79d6082ec76dfbd7e`,完整git archive导出
`/tmp/p5q-live-06-lint-SiFTve`,之后仅补文档/日志。

sha256复核:

- 冻结稿:`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`。
- live-05/run.json:`349a86d65c707cf615d14123a18b928e0d9b380506950355c4cbab8215259027`。

本轮没有QuickBuild请求。两项补充完成后提交推送,live-06仍须新的聊天开始指令;
不将离线成功当作真机取证完成,不进入C3。

### 21.9 live-06实跑:通道保持、结构采样与表单停点

2026-10-13收到新的聊天“开始”,基线93421b1。按§21.7命令改用新目录
`evidence/C2b/live-06/`,exec_command指定tty=true并保持同一stdin。
先发ping、收到pong=true后才等待人工登录,没有预发read。完整启动参数见
`live-06/README.md`;run.json:2414记录握手两布尔值均true。
login600秒上限未提前结束:一次人工POST返回302,落/dashboard200,
三条件通过(not_signin=true,password_inputs=0,sign_out_links=1,query为空),
证据run.json:2421。没有凭据进入聊天、终端输入或证据。

| 顺序 / 页面 | 实测状态 | live-06证据 |
|---|---|---|
| 1193467主页 | 200,VERIFIED;子构建1193469 | 01.response.html;run.json:41 |
| 1193467变量 | 200,VERIFIED | 02.response.html |
| 1193469主页 | 200,ID_UNVERIFIED;即时/3秒后均仅一个正确Build标签、build-summary=0 | 03.id-unverified.response.html;run.json:2486 |
| 1193469变量 | 200,VERIFIED | 04.response.html |
| 1186372主页 | 200,ID_UNVERIFIED;两次均仅一个正确Build标签、build-summary=0 | 05.id-unverified.response.html;run.json:2526 |
| 1186372变量 | 200,VERIFIED | 06.response.html |
| 1186372子构建 | NOT_COLLECTED;按裁定跳过,不从未核对主页提取子ID | run.json:2568 |
| 配置1917 | 200;父页五项+配置页两项均通过 | 07.response.html;run.json:2572/:2591 |
| form_evidence | STOPPED/QB_FORM_CHANGED,operation=form_evidence,path_shape=/overview/<id> | run.json:2409 |

两页诊断均在原页即时及3秒后采样,未导航/刷新/重试;原始结构对象逐字引于
appendix-c的live-06节。相对时间分别201291/204330ms与249025/252066ms;
readyState均complete,build_summaries均[]。ID_UNVERIFIED没有升级为核对通过,
不作为配置或子ID来源。两次采样没有Summary,不能据此推断放宽生产核对标准。

配置1917只从本次VERIFIED父页取得:Overview/Pipelines/Children三处ID相同,
breadcrumb与copy-path均为root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER,
TRIGGER为current,构建名前缀符合裁定;配置页title、breadcrumb/copy-path亦一致。
没有猜ID、没有使用live-04回填。完整事实与行号见appendix-c。

**新增停点:**已核对配置页07.response.html:722的Run入口是button,
没有href,onclick中含`../wicket/page?9-1.ILinkListener-run`。
生产openForm仍在qb_browser_agent.mjs:509读取href,:510缺失即QB_FORM_CHANGED。
本次open_form重新GET配置页200后返回该错误,没有运行表单Document请求,
没有report.form、没有BUILD_TYPE设值、没有action/callback/version/options样本。
重新GET的DOM未另归档,以上按钮形态来自紧邻的已归档配置页;
该对照支持href前提不符,不伪称有失败分支堆栈或表单内容。
候选修复须由设计方核对后授权,本轮不改生产、不改规则、不尝试改用onclick点击。

停止后进程exit1,browser_closed/profile_removed=true,runtime_failure=null,
WORKER_BLOCKED/NEW_PAGE=0,form_action_releases=0,released=false。
未点Ok/Accept、未提交、未新建构建、不进入C3。
请求阶段GET112(允许71/拒绝41),POST1(仅人工登录);响应200共59、302共1。
这是浏览器拦截观测,不是服务器实收计数。拒绝:ckeditor Script10,
bootstrap-icons两个Font各9,Wicket XHR13;trace与包装拒绝各41,帧归属差额0。
不以静态资源被拒直接推断它导致本次表单停点,不新增资源登记。

附录C本次补得子变量TRIGGER_ID=1193467、FAIL_FAST=yes、
EACH_GBS_BUILD_STATUS存在但空、BUILD_PKG_LIST为245行git_path@commit;
子配置路径末段RBS/build。1193467实际Status=Failed,Child Build结果FAILED,
不能充当Successful样本。失败样本子构建、子主页Status、逐架构结果与表单联动
仍NOT_COLLECTED;父摘要不补子状态。详见带行号的appendix-c。

run.json sha256=`e13a202e2e245052160d2da140a36b5d1e10ecdf387c3d2901ed7bd5cbd53213`。
代理脱敏及含内存身份的写前/写后检查通过;离线PageRedactor.check_bytes
对七页与run.json原始字节复检通过。live-01至live-05原样保留,冻结稿hash不变。

### 21.10 live-06归档验收

本轮只有文档与新证据,生产/取证脚本/tests/冻结稿/design.md均零diff。
日志目录`evidence/C2b/live-06-validation/`:

| 命令 | exit | 结果 / 日志 |
|---|---|---|
| .venv/bin/python -m pytest -q | 0 | 2165 passed,1 skipped,202.54s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;design-check.log |
| Node spikes/p5q_c2b_evidence.mjs --self-test .venv/bin/python | 0 | 22/22,network_requests=0;self-test.log |
| Node spikes/p5q_c2b_evidence.mjs --id-self-test PW CHROMIUM .venv/bin/python | 0 | 10/10,network_requests=0;id-self-test.log |
| PageRedactor.check_bytes(live-06七页与run.json) | 0 | 8文件PASS;redaction-check.log |
| 归档一致性核对 | 0 | 七页hash/状态、两组引用原文、间隔、配置、清理、零release、历史目录零diff;evidence-consistency.log |

Node/PW/CHROMIUM完整路径与§21.4和live-06/README一致。
全量包含既有Node单元、四组本机安全、登录重试与配置来源测试;
没有新增pytest用例,总数与93421b1基线一致。离线自测数字不混计全量。
Ruff用树`d615f872fc6066b5d7526badffb9becb53c70de9`完整git archive导出
`/tmp/p5q-live-06-validation-lint-GB4tB8`,排除既有未暂存的无关工作;
之后只补本节与验收日志。HTML保留脱敏归档原字节,不为消除空白提示重排。

冻结稿sha256仍为
`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`;
live-05/run.json仍为
`349a86d65c707cf615d14123a18b928e0d9b380506950355c4cbab8215259027`。
验收通过不消除真机QB_FORM_CHANGED停点;本轮只归档并停止等设计方核对,不进入C3。

## 22. 实施裁定 P5Q-C2B-06

### 22.1 裁定原文

原因一:QuickBuild 按会话记住上次选中的构建子标签。live-06 里 /build/1193469 与 /build/1186372 都在读完变量页之后才读,打开时显示的是 Variables 子标签(归档页里当前选中的子标签可证),所以没有 Summary 区块;不是页面结构不同。
原因二:配置页的运行控件是 button,onclick 为 "var win = this.ownerDocument.defaultView || this.ownerDocument.parentWindow; if (win == window) { window.location.href='../wicket/page?N-1.ILinkListener-run'; } ;return false",没有 href(live-06/07.response.html:722)。
另记三项与冻结稿假设不符的事实,留待表单取证完成后一并按 R1 修订设计,本轮不实现:
(1) Full 构建的子构建 BUILD_PKG_LIST 是全量包列表(1193469 为 245 行,含父构建 BUILD_PKG_LIST_MODIFY 的 4 行),不是只有目标行;
(2) 父构建回显 BUILD_REFERENCE=Live、SNAPSHOT_NUM=do not need select,子构建回显 BUILD_REFERENCE=Ref. Snapshot 且有 SNAPSHOT_NUM_URL;
(3) 1186372 属于 Tizen-Unified-Toolchain/RBS/TRIGGER,FAIL_FAST=no,CHILD_CONFIGURATIONS 用逗号分隔。按 FatTank 裁定第 9 条,它不是 Base 的合格失败样本。改用 1193469 作为 Base 失败样本(父构建 Child Build 表 Build Result=FAILED,EACH_GBS_BUILD_STATUS 存在且为空)。

### 22.2 执行计划与边界

FatTank已批准,设计方出具;冻结稿不改。按顺序:

1. 生产read将Summary核对只用于/build/N/overview;裸/build/N只核对唯一导航标签,
   variables/step_status不变。openForm仅允许唯一button运行控件,onclick完整匹配
   裁定文法,解析后再次核对同源、/wicket/page和完整监听器名,不退回a[href]。
   独立提交推送前跑pytest/mypy/完整待提交树ruff/lint-imports/check_design_doc,
   Node单元及四组本机安全全部通过。
2. 仅spikes跟进:主页与可信配置/子ID来源改为overview;保留ID_UNVERIFIED、
   ping/EOF、配置五项/两项核对。补离线自测后独立提交。live-07不再读1186372。
3. 等新的聊天“开始”再运行live-07,顺序为1193467 overview/variables,
   1193469 overview/variables/step_status,配置登记与读取,Full→Partial→Full,close。
   记录BUILD_REFERENCE/SNAPSHOT_NUM值与选项、回调/action/版本/重渲染/random;
   不点Ok/Accept,不提交,release必须0,停止条件不变,不进入C3。

三项R1事实仅登记,不实现字段/样本之外的行为变更。生产放行集合/pathShape不改,
无外网取证发生于前两步;历史live目录原样保留。无关既有工作树改动不纳入提交。

### 22.3 第一步生产修正与验收

buildId只在精确/build/N/overview路径执行Summary表Id核对;裸地址、variables与
step_status仍要求唯一正确导航标签。openForm要求唯一button运行控件,onclick
按裁定完整匹配,包括拒绝末尾换行/多余语句;解析出的同源/path/query再次核对。
没有a[href]回退,没有新增资源、落点或刷新放行。代码仅改qb_browser_agent.mjs。

tests/node/test_qb_browser_runtime.mjs使用live-06/03、05已脱敏Variables归档验证
裸地址通过而overview缺Summary拒绝;原Summary正反矩阵迁到overview路径。
使用live-06/07已脱敏归档测试button正例与a/双button/多语句/promote/run2/
外站/缺onclick/末尾换行反例。真实Chromium DOM,导航与点击在该夹具中替换为
记录器,网络判定全拒绝,反例click=0/runUrl=null,正例仅注册精确地址并click=1。
Node runtime计数29→41(含父测试与子测试);pytest入口未新增,不混计。
live-06的Variables选中态可机械定位到03.response.html:783-784,
历史证据不重写。

日志目录`evidence/C2b/c2b-06-production/`。Node命令前缀为
`env ELECTRON_RUN_AS_NODE=1 /snap/code/current/usr/share/code/code`;
PW=`/home/linhao/.bun/install/cache/playwright-core/1.58.2@@@1/index.mjs`,
CHROMIUM=`/home/linhao/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome`。

| 命令(仓库根目录) | exit | 结果 / 日志 |
|---|---|---|
| Node tests/node/test_qb_browser_runtime.mjs PW CHROMIUM | 0 | 41/41;node-runtime.log |
| Node --test tests/node/test_qb_browser_agent.mjs | 0 | 120/120;node-unit.log |
| Node tests/node/p5q_c2b_safety.mjs PW CHROMIUM | 0 | 四组4/4,loopback-only;safety.log |
| .venv/bin/python -m pytest -q | 0 | 2165 passed,1 skipped,110.27s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;design-check.log |

四组从头实跑:Worker/WebSocket攻击HTTP0、握手0,本次走b:browser_fail_closed,
shared_worker closeTarget成功,worker closeTarget异常Error,最终QB_BROWSER_UNAVAILABLE
且browserClosed/temporaryDirectoryRemoved=true;307/308后继拒绝、合法302继续;
逐跳forbiddenSecondHops=0/postReplay=0;凭据隔离通过。
Ruff完整树`ed2783513624524cc7c7c1b72d916a1e4b1f8669`导出到
`/tmp/p5q-c2b-06-production-lint-GESLrU`,之后只补文档/完整日志。
第一步全绿后独立提交推送;第二步尚未修改,live-07尚未登录,不进入C3。

### 22.4 第二步取证脚本跟进

第一步已提交推送`a364489`。第二步只改spikes内的evidence/config_source模块及
配套离线测试;不再改生产代理。原ID_UNVERIFIED即时/3秒后采样、身份脱敏、
ping/pong、EOF停态和五项/两项配置判据保持。

- 构建页只允许本轮五个完整路径:1193467 overview/variables;
  1193469 overview/variables/step_status。裸地址与1186372拒绝,不会默认补读。
- 配置登记仅以本次已归档并核对通过的/build/1193467/overview为来源;
  子ID也仅从核对通过的overview提取。1193469需在该父页Child Build表内,
  不能凭旧证据、变量页或未核对页面补入。
- 成功的step_status读回也标注VERIFIED;诊断例外仍仅overview/variables,
  其它错误立即停止。1193467两页必须核对通过。
- formFacts保存base/action/callback、page_version、BUILD_REFERENCE/SNAPSHOT_NUM
  当前显示值与完整选项;保持其它select选项快照。新增form_network仅观察协议
  适配后的Document/XHR/Fetch元数据,按既有URL脱敏,不读头/体,记录has_random。
  两次设值各记录before/after、主帧导航和Document GET,不把尚未取得的联动
  写为成功;失败时保留已采集的before/网络事实。所有记录仍走写前/写后检查。

新增四项id-self-test:非overview不能作为子ID来源、本轮路径/父子关系闭集、
step_status导航核对、表单参考值/选项/页号。原10项全部保留,10→14,
包括双标签、缺Summary、延迟Summary、非200/重定向/运行时异常等停止控制。
config-source既有27项同步为已核对overview输入,另在既有拒绝表里覆盖裸地址与
id_verified缺失/false。握手/EOF自测仍22项。无需实际登录即可全部离线执行。

live-07运行计划(未执行):PTY启动相同脚本,输出全新`evidence/C2b/live-07/`,
先ping并收到pong,再只在窗口人工登录。按§22.2顺序,配置来源显式传
`{"command":"register_config","source_path":"/build/1193467/overview"}`,
仅用返回ID读配置;随后form_evidence,确认release=0后close。
所有真实页面状态、1193469 Summary Status、回调/action/版本/重渲染/random及
release实际值此时均NOT_COLLECTED。必须等新的聊天“开始”,不进入C3。

### 22.5 第二步验收与live-07闸门

日志目录`evidence/C2b/c2b-06-spike/`,Node/PW/CHROMIUM全路径沿§22.3。

| 命令 | exit | 结果 / 日志 |
|---|---|---|
| Node spikes/p5q_c2b_evidence.mjs --self-test .venv/bin/python | 0 | 22/22,network_requests=0;self-test.log |
| Node spikes/p5q_c2b_evidence.mjs --id-self-test PW CHROMIUM .venv/bin/python | 0 | 14/14,network_requests=0;id-self-test.log |
| Node tests/node/test_p5q_c2b_config_source.mjs PW CHROMIUM | 0 | 27/27;config-source.log |
| .venv/bin/python -m pytest -q | 0 | 2165 passed,1 skipped,106.64s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;design-check.log |

Ruff完整树`ea336fe71127455987780d112eacef58c76ac443`导出到
`/tmp/p5q-c2b-06-spike-lint-hC3NFo`;之后只补文档/完整日志。生产代码相对
第一步a364489零diff,冻结稿仍为
`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`。
历史live-01至live-06目录原样保留;本轮前两步没有QuickBuild请求。
第二步提交推送后在聊天请求“开始”;此前不启动浏览器、不创建live-07实测证据,
不把离线通过当作真机结果。三项R1事实保留待设计修订,不进入C3。

### 22.6 live-07实跑与登录停点

2026-10-13,基线e683175,收到FatTank新的聊天“开始”后执行一次。PTY保持打开,
先发ping并收到pong才启动浏览器;600秒登录时限,未提前结束、未EOF、未重试。
脚本exit=1,状态STOPPED,原因QB_LOGIN_TIMEOUT,operation=login,path_shape=/signin。
browser_closed=true、profile_removed=true、runtime_failure=null。

原始脱敏记录`evidence/C2b/live-07/run.json`,sha256:
`79d07795dfa6d54647f9981ff7fe1884e5f860cc1e1e6037f5db5ec3869a533e`。
启动命令、PTY与协议输出见同目录README;此前live目录均原样保留。

| 本轮事项 | 实测 / 证据 |
|---|---|
| 命令通道 | ping_received/pong_sent=true;run.json:845 |
| 登录Document | 仅GET /signin,HTTP200,query为空,redirect_hop=false;run.json:778 |
| 登录POST/重定向 | POST=0,login_response_count=0,login_redirect_seen=false;run.json:868 |
| 登录三条件 | NOT_COLLECTED,login_response为QB_LOGIN_TIMEOUT;没有成功快照;run.json:849 |
| 请求阶段 | GET47,放行46/拒绝1,POST0;响应阶段38条HTTP200;按traffic元数据计,不冒充服务端实收数 |
| 唯一拒绝 | Script /ckeditor/ckeditor.js?v=1701391813000;既有规则不改;run.json:807 |
| 拒绝对账 | trace DENIED=1,wrapper=1,帧归属拒绝=0;WORKER_BLOCKED/NEW_PAGE=0;run.json:855 |
| 构建页 | pages=[],1193467 overview/variables和1193469 overview/variables/step_status均NOT_COLLECTED;run.json:10 |
| 子Summary/父Child Build | 本轮未取得,不拿live-06摘要代替 |
| 配置ID与五项/两项核对 | NOT_COLLECTED;没有register_config,未沿用历史1917 |
| 表单联动/参考值选项 | NOT_COLLECTED;无open_form/fill/submit,回调/action/版本/重渲染/random均未取得 |
| 放行与清理 | form_action_releases=0,released=false;browser/profile清理均true;run.json:853/:863 |

相对毫秒起点是脚本启动(含等待ping),不是浏览器启动:
首次Document请求134390ms、响应135905ms、主帧导航135911ms、关闭734394ms。
不把734秒说成登录时限延长,也不从无POST推断人的操作或页面登录失败原因。
本轮无新设计裁决/生产修复;附录C最新结果更新为登录停点,三项R1挂账仍保留。
按停止协议只归档、验收、提交推送,不自动重试、不进入C3。

### 22.7 live-07归档验收

日志目录`evidence/C2b/live-07-validation/`,命令全集见该目录README。
本轮代码与测试零diff,新增测试0;不新增资源/登录落点登记,不修改冻结稿。

| 命令 | exit | 结果 / 日志 |
|---|---|---|
| .venv/bin/python -m pytest -q | 0 | 2165 passed,1 skipped,115.49s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;design-check.log |
| pytest -v -s 三个Node入口(该目录README列完整nodeid) | 0 | 3 passed,19.44s;Node单元120/120、runtime41/41、四组安全4/4;node-gates.log |
| run.json原始字节/结构/hash与历史证据核对 | 0 | PASS;page列表为空、只执行login、零POST/零release、清理完成、历史目录与冻结hash不变;evidence-check.log |

安全四组本次重新实跑,仅loopback:Worker/WebSocket攻击HTTP0/握手0,走b:
browser_fail_closed;shared_worker closeTarget成功,worker异常类别Error,
QB_BROWSER_UNAVAILABLE且browserClosed/temporaryDirectoryRemoved=true。
307/308后继拦截、302继续;逐跳forbiddenSecondHops0/postReplay0;凭据隔离通过。
这些是本机合成控制,不能与live-07的runtime_failure=null或真实请求计数混算。

Ruff完整待提交树`04b17a954d7ec3eb220868c474e5361c4b6e6665`导出到
`/tmp/p5q-live-07-lint-B3z2Sf`;之后仅补文档与验收日志,未纳入无关工作树改动。
运行中的身份检查使用内存身份集合;离线PageRedactor.check_bytes复查不持有
原登录身份,不将离线检查冒充对未知身份字符串的检索。run.json hash与§22.6一致。
全量通过不消除QB_LOGIN_TIMEOUT停点;C2b仍未完成,停止等后续指示,不进入C3。

### 22.8 live-08原样重跑与配置登记停点

FatTank授权按P5Q-C2B-06第三步原样重跑一次,新目录live-08,live-07原样保留。
2026-10-13,基线962ad58;先在聊天请求“开始”,收到后PTY启动原脚本,
先ping/pong再弹窗,时限600秒,没有修改生产/取证脚本/冻结稿。实际一次人工登录
POST返回302,落点/dashboard200,三条件成立;随后严格逐条读五页,无1186372。

| 顺序 | 结果 | 证据(均在evidence/C2b/live-08/) |
|---|---|---|
| ping/login | ping/pong=true;not_signin=true,password_inputs=0,sign_out_links=1,empty_query=true | run.json:1936/:1943 |
| 1193467 overview | HTTP200,VERIFIED;Child Build含1193469,结果FAILED | 01.response.html:891/:892;run.json pages |
| 1193467 variables | HTTP200,VERIFIED | 02.response.html |
| 1193469 overview | HTTP200,VERIFIED;Summary Status=Failed | 03.response.html:808/:828 |
| 1193469 variables | HTTP200,VERIFIED;TRIGGER_ID=1193467,FAIL_FAST=yes,EACH_GBS_BUILD_STATUS存在且空 | 04.response.html:800 |
| 1193469 step_status | HTTP200,VERIFIED;21个显示步骤,含组合步骤;master/BUILD/Build/Build_GBS为failed | 05.response.html:812/:944/:1235/:1281;完整表见appendix-c |
| register_config | CONFIGURATION_SOURCE_MISMATCH,停止,未登记/未读配置页 | run.json:1931/:1997 |
| form_evidence | NOT_COLLECTED;未open_form、未设值、未点Ok、未submit | run.json commands;form_action_releases=0 |

父overview五项机械结果是4绿1红,不是ID不等:
`overview_link=true,sibling_tabs=false,breadcrumb=true,copy_path=true,build_name=true`。
实际原文为`../../overview/1917`、`../../pipeline/1917`、`../../children/1917`
(01.response.html:698/:711/:715),三者尾部ID相同;现有
spikes/p5q_c2b_config_source.mjs的sibling_tabs仍逐字要求`../pipeline/1917`
与`../children/1917`。只登记差异,没有把正则改宽、没有用历史1917直接登记。
来源记录的overview_id=1917只是提取值,不代表登记通过。

原始stop.path_shape保留了最后一次read的/build/<id>/step_status;
实际operation=register_config,送入的source_path为/build/1193467/overview。
该日志字段不作为“step_status读取失败”的证据,不修改原始run.json。
新的停点待设计方核对,无运行时故障:runtime_failure=null,
WORKER_BLOCKED/NEW_PAGE=0,browser_closed/profile_removed=true。

请求阶段93条:GET92/POST1(仅人工登录),放行66/拒绝27;
响应阶段HTTP200=53/302=1。拒绝为ckeditor7、bootstrap-icons.woff6/woff2六条、
/wicket/page XHR8;trace与wrapper均27、帧归属拒绝0。
以上为拦截元数据计数,非服务端实收;不把两阶段相加,不把人工登录POST当构建提交。
自动刷新仍按原规则拒绝,没有新登记。release=0,released=false。

run.json sha256=`ebe9226207c9d08ac8b5df0ba03e8a5e614092431f26e65468d2a8d80f902080`。
本轮已取得子Summary真实Status,但表单回调/action/版本/选项/重渲染/random及
表单BUILD_REFERENCE/SNAPSHOT_NUM当前值仍NOT_COLLECTED,不拿变量页代替表单。
三项R1事实仍待设计修订;不再请求任何页面、不进入C3。

### 22.9 live-08归档验收

日志目录`evidence/C2b/live-08-validation/`,命令全集见该目录README。
新增测试0,本轮生产/测试/取证脚本/冻结稿/design.md零diff。

| 命令 | exit | 结果 / 日志 |
|---|---|---|
| .venv/bin/python -m pytest -q | 0 | 2165 passed,1 skipped,117.49s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;design-check.log |
| pytest -v -s 三个Node入口(README列完整nodeid) | 0 | 3 passed,19.38s;单元120/120、runtime41/41、四组安全4/4;node-gates.log |
| 原始字节脱敏/hash/结构事实与历史证据核对 | 0 | 6文件PASS;五页核对/哈希、配置4绿1红、变量与21步骤、流量、零release、历史目录与冻结hash不变;evidence-check.log |

安全测试全部loopback-only,Worker/WebSocket走b:browser_fail_closed,
attackHTTP=0/websocketHandshakes=0;shared_worker closeTarget成功,
worker异常类别Error,最终QB_BROWSER_UNAVAILABLE且browser/profile清理true。
307/308终止/302继续、逐跳forbiddenSecondHops0/postReplay0、凭据隔离均通过。
与真机run的runtime_failure=null分列,不互相替代。

Ruff完整待提交树`3aace796a64a902a944829a24566581d193b2ab3`导出到
`/tmp/p5q-live-08-lint-biq1PI`,之后仅补文档与验收日志。五页保留生产脱敏后的
原字节,不为修空白重排HTML。运行中写前/写后检查使用内存身份集合;
离线PageRedactor.check_bytes不持有原身份,不冒充未知身份字符串扫描。
live-07/run.json仍为`79d07795dfa6d54647f9981ff7fe1884e5f860cc1e1e6037f5db5ec3869a533e`,
冻结稿仍为`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`。
验收绿不消除CONFIGURATION_SOURCE_MISMATCH,只归档停点等设计方核对,不进入C3。

## 23. 实施裁定 P5Q-C2B-07

### 23.1 裁定原文

原因:P5Q-C2B-04 的五项配置来源核对里,总览链接允许任意层 ../,Pipelines 和 Children 两个标签却写死为 ../pipeline/N 与 ../children/N。改读 /build/N/overview 后,链接变为 ../../pipeline/1917 与 ../../children/1917,解析后的指向不变。这是设计方规则写法错误,不是实现错误。
另记 live-08 新取得的事实:子构建 1193469 的配置路径为 root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/build(overview 1915),构建名形如 TIZEN_Tizen_Tizen-Base-Toolchain_RBS_build_standard-armv7l:aarch64:x86_64_<时间>;子构建 Summary Status 为 Failed;父构建 Child Build 表 Build Result 为 FAILED。

### 23.2 改动范围与执行顺序

FatTank批准、设计方出具,开工基线0f89d4f。冻结稿sha256仍为
`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`;
live-08/run.json仍为`ebe9226207c9d08ac8b5df0ba03e8a5e614092431f26e65468d2a8d80f902080`。

只改spikes/p5q_c2b_config_source.mjs的来源URL判定,以及evidence.mjs该判定调用处
传入归档页source.path,配套离线测试同步;不改生产代理、冻结稿或其他设计规则。
三个href分别以`https://quickbuild.tizen.org + source.path`用URL API解析,
同源、无查询/片段、精确/overview/N或/pipeline/N或/children/N、正整数且相同,
个数各恰好一个。保留原有安全整数保护。归档来源只取已核对overview的限制不变。
面包屑/复制路径/构建名三项、配置页两项、停止条件均不变。

测试覆盖../(裸build地址)与../../(overview地址)两种正确解析;
同源绝对URL与根相对路径按本裁定解析规则为正例,替换旧的仅接受../形态反例。
查询/片段/外站/尾段/非法整数等对三个标签分别验证;缺失/重复/ID不一致拒绝。
增加live-08父overview离线回归,不改旧run.json的原始4绿1红记录。
归档HTML中的base元素不能替换来源基址;未传来源路径或错误深度也须拒绝。

先跑离线配置来源测试、既有self-test/id-self-test及全量门禁,全绿后提交推送。
之后在聊天请求新的“开始”;收到后PTY启动live-09,先ping/pong再弹窗,
不提前创建实测结果。顺序保持live-08五页,新鲜父overview登记配置并读配置页,
再form_evidence只做Full→Partial→Full,不点Ok/Accept、不submit,release必须0,
记录回调/action/版本/选项/重渲染/random及表单BUILD_REFERENCE/SNAPSHOT_NUM。
任一停止条件触发即归档并停止,不重试绕过、不进入C3。

### 23.3 离线落实与验收

三个链接均由归档source.path提供基址,不使用当前浏览器地址或HTML的base标签。
结果仍是五个具名布尔检查,配置页仍为两个,没有把某项失败改为可忽略。
三个链接的查询/片段(含空分隔符)、外站/http、路径多段、非正整数/非法URL
逐个拒绝;三个标签缺失/重复/ID不一致均拒绝。解析形态变化只影响取证脚本。
生产代理的放行面、openForm、read和所有停止条件零改动。

离线配置测试27→67(净增40个Node测试计数,含子测试),pytest包装入口未新增,
不把Node计数与全仓pytest混算。旧的同源绝对地址/根相对路径反例按新裁定
转为正例,其它原有来源/路径/面包屑/复制路径/构建名/配置页控制保留。
live-08/01.response.html作为本地只读DOMParser输入,五项全绿;另用其原run.json
facts复核,结果写`c2b-07-offline/live08-offline-source-check.json`。原run.json仍记录
sibling_tabs=false,新证据明确mode=offline-only/network_requests=0/live09_started=false。

日志目录`evidence/C2b/c2b-07-offline/`,完整命令见该目录README。

| 命令 | exit | 实测 / 日志 |
|---|---|---|
| Node tests/node/test_p5q_c2b_config_source.mjs PW CHROMIUM | 0 | 67/67;config-source.log |
| Node spikes/p5q_c2b_evidence.mjs --self-test .venv/bin/python | 0 | 22/22,network_requests=0;self-test.log |
| Node spikes/p5q_c2b_evidence.mjs --id-self-test PW CHROMIUM .venv/bin/python | 0 | 14/14,network_requests=0;id-self-test.log |
| .venv/bin/python -m pytest -q | 0 | 2165 passed,1 skipped,109.30s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| .venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md | 0 | 0 problem;design-check.log |
| pytest -v -s 三个Node入口(README列nodeid) | 0 | 3 passed,19.48s;Node单元120/120、runtime41/41、安全4/4;node-gates.log |

Node前缀/PW/CHROMIUM沿§22.3且在README列全路径。四组本机安全从头实跑,
Worker/WebSocket走b:browser_fail_closed,HTTP0/握手0,shared_worker closeTarget成功,
worker异常Error,浏览器与临时目录清理true;307/308终止、302继续、逐跳与凭据隔离绿。
Ruff完整待提交树`9234e0897556f15922df41969375adcfb4785439`导出到
`/tmp/p5q-c2b-07-lint-xeWsfZ`;之后仅补记录与验收日志。无关既有改动未纳入。

### 23.4 live-09待开始(启动前记录)

本次先提交推送修正,再在聊天请求FatTank回复“开始”。未收到前不运行真机脚本,
不创建live-09实测证据,不提前登记1917。未来配置ID仍须来自本轮读到并核对通过的
1193467/overview,旧离线复核不能替代新来源。live-08及更早目录原样保留。
live-09的页面/配置两项/表单回调/action/版本/选项变化及release均NOT_COLLECTED;
只有实跑后才填实际值。C2b尚未完成,不进入C3。

### 23.5 live-09实跑与停止报告

2026-10-13,基线b9b4d71,本聊天新的“开始”后启动;未修改脚本、生产或冻结稿。
PTY持续保留,先ping/pong再弹窗。一次人工登录POST302,落点/dashboard;
三条件not_signin=true/password_inputs=0/sign_out_links=1,空查询。
命令、原始脱敏页面、trace与增强诊断在`evidence/C2b/live-09/`,详情见README和
appendix-c最新节。旧live-08及更早目录原样保留。

| 顺序 | 实测 | 证据(live-09下) |
|---|---|---|
| 1193467 overview/variables | HTTP200且VERIFIED;Child Build含1193469 | 01.response.html;02.response.html;run.json pages |
| 1193469 overview/variables/step_status | HTTP200且VERIFIED;无ID_UNVERIFIED页 | 03.response.html;04.response.html;05.response.html |
| 父配置来源五项 | 全绿,从新鲜01页取1917,非历史值回填 | run.json:2457;01.response.html:698/:711/:715/:93/:736 |
| /overview/1917两项 | HTTP200,面包屑/复制路径均等于Base/RBS/TRIGGER全路径 | 06.response.html:4/:710/:93;run.json:2513 |
| form_evidence/open_form | GET run监听器302,跳转GET /wicket/page?10返回200,随后QB_FORM_CHANGED | run.json:2519;run.json:2328 |
| BUILD_TYPE Full→Partial→Full | 未执行;form/form_transitions未产生 | run.json commands及form_network |
| release/清理 | form_action_releases=0,released=false;浏览器/临时目录清理true | run.json:2599/:2784 |

本轮子Summary仍Failed(03.response.html:828),父Child Build仍FAILED(:892),
父Build Package List映射BUILD_PKG_LIST_MODIFY四行,子BUILD_PKG_LIST245行包含四行;
子TRIGGER_ID=1193467、FAIL_FAST=yes、EACH_GBS_BUILD_STATUS存在且空。
变量逐项离线解析在variables-check.log,不能替代表单默认值或可选项。

停止事实:生产open_form重新GET /overview/1917,随后放行
GET /wicket/page?9-1.ILinkListener-run(302),再GET /wicket/page?10(200)。
生产命令返回QB_FORM_CHANGED,脚本停止且exit1。stop.path_shape仍为/overview/<id>,
因为脚本只有open_form成功后才更新current为/wicket/page;真实导航见events/form_network。
不得把该path_shape误作配置来源再次失败。没有表单HTML/snapshot归档,无法定位
validateForm的具体失败子条件,也不把被拒ckeditor与错误作未证实的因果归因。
不改生产、不放宽规则、不重试、不另开浏览器,等待设计方裁定。

表单action/回调地址/字段值与选项/两次设值后的版本变化、重渲染与random均
NOT_COLLECTED。仅打开表单的Document链已观测(页号10、has_random=false),
不冒充逐字段联动证据。六页写前写后自检通过;离线integrity.log再核hash及脱敏,
离线检查不持有原身份集合,不冒充运行中基于内存身份的检查。

请求阶段GET110/POST1(唯一POST为人工登录),allowed75/denied36;
响应阶段HTTP200x60/302x2。均为拦截事件计数,不是服务端实收统计。
拒绝ckeditor10、bootstrap-icons.woff9/woff2x9、Wicket XHR8;不追加任何放行。
trace/wrapper拒绝36/36,帧归属拒绝0,WORKER_BLOCKED/NEW_PAGE均0,
runtime_failure=null。run.json SHA256:
`9cb7a31f1afd8e2241dc32b2e848d8b71076532f501c2b39bceae4fd062152e3`。

### 23.6 live-09归档验收

以下全部在本次停止取证后重跑,日志均在live-09;完整命令见该目录README。

| 命令 | exit | 实测 / 日志 |
|---|---|---|
| .venv/bin/python -m pytest -q | 0 | 2165 passed,1 skipped,125.61s;pytest.log |
| .venv/bin/mypy | 0 | 113 source files;mypy.log |
| .venv/bin/ruff check .(完整待提交树) | 0 | All checks passed!;ruff.log |
| .venv/bin/lint-imports | 0 | 6 kept,0 broken;lint-imports.log |
| check_design_doc.py design.md | 0 | 0 problem;design-check.log |
| pytest -v -s三个Node入口 | 0 | 3 passed,19.45s;Node120/120、runtime41/41、安全4/4;node-gates.log |
| evidence.mjs --self-test / --id-self-test | 0 / 0 | 22/22、14/14,network_requests=0;self-test.log/id-self-test.log |
| PageRedactor与文件hash/运行不变量核对 | 0 | 六页与run.json通过;integrity.log |

Worker/WebSocket组为b:browser_fail_closed,attackHTTP0/WS0,shared_worker
closeTarget成功、worker异常Error;浏览器/目录清理true。其余三组通过,
无真实QB流量;与真机runtime_failure=null分列。配置来源67个Node控制由全量
pytest入口再次覆盖,没有新增测试或修改判据。
Ruff导出树`8f5a45213fe05fbfee55ec06f764aa54e4c05578`,目录
`/tmp/p5q-live-09-lint-4KgVAM`;之后仅补文档与日志。六页HTML不为格式检查重排,
保留生产脱敏原字节。冻结稿sha256与live-08/run.json哈希仍与§23.2相同。
本次只提交文档和证据。全部回归绿不改变真机QB_FORM_CHANGED停止结论,
C2b未完成,待设计方处理表单取证缺口,不继续C3。

## 24. 实施裁定 P5Q-C2B-08

### 24.1 裁定原文

原因:live-09 中 Run 返回 302,/wicket/page?10 返回 200,约 0.37 秒后 open_form 以 QB_FORM_CHANGED 结束(等待标题的时限是 30 秒,说明标题已出现,是之后的结构核对失败)。生产 open_form 在核对失败时直接抛错,表单页未进入取证。这和 P5Q-C2B-05 是同一类取证通道缺口。本裁定把"失败时先取证再停止"推广到表单阶段的全部失败点。
设计方推测(不作结论):1193467 变量页上 ADD_TO_IMG_LIST(Add rpm list to Image)、RM_FROM_IMG_LIST(Remove rpm list from Image)、IMAGE_BUILD_ID、USER_DEFINED_GBS_BUILD_MACRO 带显示名,可能是表单新增字段,不在冻结稿第 257 行的 13 个字段集合内;也可能是 BUILD NOTES 改为富文本编辑器、ckeditor 被拒导致控件数不符。以现场取证为准。

### 24.2 实施范围

开工基线81e90f5,git pull --ff-only:Already up to date;冻结稿sha256仍为
`0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950`。
仅spikes新增表单失败诊断/自测并接入取证入口,生产与冻结稿零改动。
先离线验收、提交推送;live-10等新的聊天“开始”,保持ping/pong与原读取顺序。
不重试live-09,所有历史证据保持原样。

失败时生产formDOM原快照只留内存,复算validateForm;诊断JSON中input/textarea仅长度,
select仅选项文字/选中状态,不写option value、原控件value或原onchange代码。
回调仅记录存在性、调用数、生产callbackURL是否通过及固定失败类别。
保存标签差集/重复、按生产顺序的判定与reached标记、首个失败位置、action形态,
PROJECT_NAME只读值、button class、ckeditor节点/隐藏textarea事实。
null快照退回全部form个数与脱敏action;不靠历史表单猜标签。
冻结稿第3.5节第4项的明确标签集合为13个(已含PROJECT_NAME),生产FIELDS为12个
可编辑标签。诊断按`[...FIELDS, 'PROJECT_NAME']`唯一集合计算并记录实际数量,
不因提示词的“13个字段 + PROJECT_NAME”措辞再造一个第14字段或修改判定。

仅同源/wicket/page可做失败诊断,先后均执行停止检查;浏览器失效、跳转、HTTP失败、
脱敏失败优先停止。诊断完成仍抛出原错误,不续跑设值、不生成新的页面请求。
新增form-unverified.response.html经生产redactDOM及既有写前/写后检查归档;
run.json中明确form_unverified=true,不能冒充open_form成功。
逐条件复算与生产validateForm的实际结果必须相等,不等则停止而不改生产判据。

### 24.3 验收启动记录

离线五类夹具:新增字段、缺少字段、富文本控件、onchange写法变化、action不匹配;
另核null快照、重复标签、PROJECT_NAME/双列表角色、后续联动失败、立即停止和
隐私控制。启动时验收待执行,最终结果见§24.5;live-10尚未创建,
真机字段差集/失败位置/联动均NOT_COLLECTED。
完成或停止后均不进入C3。

### 24.4 诊断口径与离线结果

新增spikes/p5q_c2b_form_diagnostics.mjs与同目录p5q_c2b_form_diagnostics_test.mjs,
由evidence入口的--form-self-test运行;没有新增或修改tests目录/生产模块。
必需五类夹具及其实际首失败点在form-self-test.log:

| 夹具 | 首个失败判定 | 同步观测 |
|---|---|---|
| 多出字段 | label_set | extra=[ADD_TO_IMG_LIST],missing=[] |
| 缺少字段 | label_set | extra=[],missing=[BUILD_TYPE] |
| BUILD NOTES富文本 | single_control | 第12行(零基)控件2个、cke节点1个、textarea隐藏 |
| onchange其它写法 | callback | BUILD_TYPE,WICKET_AJAX_POST_COUNT |
| action不匹配 | action | snapshot非null,action_matches=false |

上述均仍以QB_FORM_CHANGED停止,form_unverified=true,无网络请求且released=false。
这是合成夹具,不是live-09原因判定。其余控制包括null快照两表单与action脱敏,
重复标签、PROJECT_NAME错误、双列表角色、回调缺失/多个/外站、行内button,
后续联动失败保留原异常、立即停止条件与诊断期间跳转/脱敏失败。
总计26/26;独立于pytest计数。当前文档HTTP状态来自取证入口已有form_network的
最后同URL Document响应;不是200或查不到即拒绝诊断,不新增网络请求。

validation.checks按生产顺序列出,首失败点之后reached=false;这些行的ok仅为
同一快照上的诊断重算,不冒充生产执行过。逐条件表对应validateForm:
shape→label_set→unique_rows→逐行project_name/palette_controls/single_control/callback
→action。生产私有ACTION/PALETTES的spikes副本由离线测试核对源文本;
复算总体通过/失败必须与实际调用validateForm一致。null快照只记form全集及脱敏
action,标签与差集为null(未知),不误写成“全部缺失”。form_unverified页依旧用生产redactDOM与写前写后检查;
HTML可含脱敏后的业务值,诊断JSON不保存input/textarea值或select option value。

### 24.5 最终验收与等待人工登录

日志目录`evidence/C2b/c2b-08-offline/`,完整命令见README。全部exit0:

| 验收 | 实际结果 | 日志 |
|---|---|---|
| 新表单失败自测 | 26/26,network_requests=0,released=false | form-self-test.log |
| 既有通道/地址与ID诊断自测 | 22/22、14/14,network_requests=0 | self-test.log,id-self-test.log |
| 全量pytest | 2165 passed,1 skipped,130.89s;测试集合计数不变 | pytest.log |
| mypy | 113 source files无问题 | mypy.log |
| Ruff完整待提交树 | All checks passed! | ruff.log |
| lint-imports | 6 kept,0 broken | lint-imports.log |
| check_design_doc | 0 problem | design-check.log |
| Node三个定向入口 | 3 passed,19.30s;120/120、41/41、安全4/4 | node-gates.log |

26个新控制在spikes的独立自测中,不与pytest计数混算。最终full pytest是在
补齐HTTP200/未知状态诊断前提与null快照差集口径后重新实跑。Ruff最终树
`5ccb1f803b3df61365da34d486ea00c9fa1a0a9e`导出到
`/tmp/p5q-c2b-08-final-lint-xkDdMI`,之后仅补文档与日志。
四组本机安全全部通过,Worker/WebSocket的实际fail-closed分支见node-gates.log;
不访问QuickBuild。源码静态约束仍通过,未改变生产浏览器/冻结稿/设计检查器。
live-09/run.json仍为`9cb7a31f1afd8e2241dc32b2e848d8b71076532f501c2b39bceae4fd062152e3`。
无关既有.gitignore改动、docs四个删除文件与历史草稿均未纳入。

提交推送后请求新的聊天“开始”,收到后才执行live-10。命令通道先ping/pong,
生产代理人工登录,读取1193467 overview/variables、1193469 overview/variables/step_status,
从本轮父overview取配置ID并五项/两项核对,再form_evidence。
若核对通过仍只Full→Partial→Full;若失败先做本裁定只读取证再按原错误停止。
不点Ok、不submit、不重试;release必须0;所有新真机结论留空直到现场取得。

### 24.6 live-10实跑与表单结构停止报告

基线284c5c0,收到FatTank新的聊天“开始”后才启动,先ping/pong再弹窗。
仅本次人工登录,没有重复取证或追加资源登记。证据目录`evidence/C2b/live-10/`;
run.json sha256=`9b384c1671f2825e17b0e3fd40443c0ed9a9b40b3b18402cf297a0d63672cbb9`。

| 顺序 | 实测 / 证据 |
|---|---|
| login | 三条件通过,/dashboard,无password控件、Sign Out=1;run.json:2447 |
| 1193467 overview/variables | HTTP200,均VERIFIED;01/02.response.html |
| 1193469 overview/variables/step_status | HTTP200,均VERIFIED;03/04/05.response.html |
| 配置来源/配置页 | 本轮父overview推得1917,五项true;配置页两项true;run.json:2564/:2583,06.response.html |
| 子/父失败文字 | 子Summary Failed(03:828),父Child Build FAILED(01:892),分别读取 |
| open_form | 配置重读200,Run302,表单/wicket/page?10为200;run.json:2626 |
| 失败诊断 | QB_FORM_CHANGED,stage=open_form,readyState=complete,快照非null;run.json:2706 |
| 表单归档 | form-unverified.response.html,form_unverified=true;sha256=8f8b50258cf0db849b557428cc54479fe764888fa45b64096d9b4c2edefee12e |
| 停止/清理 | 原错误保留,exit1;browser_closed/profile_removed=true,runtime_failure=null;run.json:2436/:3400 |

**本轮新停止事实1项:PROJECT_NAME逐字不等。** 同一快照的shape、label_set、
unique_rows均通过;首失败为project_name,row=0,reached=true(run.json:3212)。
该行controls=0,viewer=1,但其值为以下JSON字符串(run.json:2780):

```json
"Tizen-Base-Toolchain \n\t\t\n\t\t\t\n\t\t\t\n\t\t\n    "
```

登记期望为`"Tizen-Base-Toolchain"`(run.json:2567)。原页面结构在
form-unverified.response.html:727/:732/:733。额外/缺少/重复标签均为空(run.json:2770),
不是新增字段或字段缺失导致的本次首失败。生产formDOM的viewer读取已经调用trim
(qb_browser_agent.mjs:315),validateForm在:342精确比较;本轮仅报告返回值事实,
没有在现场读取原型实现,不推断为何页面上下文trim后仍有尾部空白,不自行修复。

首失败之后的逐行控件/回调与action重算均ok=true、reached=false,只证明该快照上的
诊断计算,不冒充生产执行过。BUILD NOTES为一个可见TEXTAREA,input角色,长度0;
cke节点0、四个textarea均未隐藏(run.json:3184)。两双列表均三个控件,
recorder回调有效,choices/selection无onchange不属于生产需检查的回调。
完整逐行标签/控件/选项/button/PROJECT_NAME及判定顺序见run.json:2706。

表单初始BUILD_TYPE=Full,选项Full/Partial;BUILD_REFERENCE=Ref. Snapshot,
选项Live/Ref. Snapshot/Snapshot Number;SNAPSHOT_NUM唯一选项并选中
tizen-base-toolchain_20260924.094908。只记录初始快照,没有执行Full→Partial→Full。
action形态通过,/wicket/page?10-1.IFormSubmitListener-form;BUILD_TYPE初始onchange
通过callbackURL且只有一个wicketAjaxPost,原文见form-unverified.response.html:757。
联动后的callback/action/版本变化、选项刷新、重渲染/random仍NOT_COLLECTED。

请求阶段GET114/POST1(人工登录),allowed75/denied40;响应阶段200x61/302x2。
这是拦截器观测,不是服务端实收计数。拒绝:ckeditor10、两种bootstrap字体各9、
Wicket XHR12;trace/wrapper=40/40,帧归属拒绝0,WORKER_BLOCKED/NEW_PAGE=0。
form_action_releases=0,released=false;没有Ok/submit,没有构建提交。
stop.path_shape仍/overview/<id>是open_form成功前current未更新,实际表单地址在
form_diagnostics.main_frame与form_network中,不可误读成配置页失败。
本轮停止后不重试、不加放行项、不进入C3;等待设计方裁定。

### 24.7 live-10归档验收

完整命令及原始日志在live-10/README.md和同目录,归档后实跑,全部exit0:

| 验收 | 结果 | 日志 |
|---|---|---|
| pytest全量 | 2165 passed,1 skipped,158.66s,较284c5c0计数不变 | pytest.log |
| mypy | 113 source files,无问题 | mypy.log |
| Ruff完整待提交树 | All checks passed! | ruff.log |
| lint-imports | 6 kept,0 broken | lint-imports.log |
| check_design_doc | 0 problem | design-check.log |
| Node三个入口 | 3 passed,27.10s;unit120/120、runtime41/41、安全4/4 | node-gates.log |
| 表单失败自测 | 26/26,network_requests0,released=false | form-self-test.log |
| 既有通道/地址、ID诊断自测 | 22/22、14/14,network_requests0 | self-test.log,id-self-test.log |
| 归档核对 | 七页sha256/脱敏检查、精确失败值、五项/两项、清理、零release通过 | integrity.log |

四组安全的Worker实际走b:browser_fail_closed:shared_worker closeTarget成功,
worker为Error类异常,浏览器/profile清理为true;attackHTTP0/WS0。其余三组均绿。
不访问QuickBuild,未重复真机。Ruff对暂存树
`26280747be55b9b18b32d91efb09ceb043a378bf`导出到
`/tmp/p5q-live10-lint-NI7isH`运行,之后只补文档与日志。
hashes.log确认冻结稿仍0a3f5e0b…1950、live-09/run.json仍9cb7a31f…152e3。
本提交仅文档与live-10证据,生产/冻结稿/检查器/spikes/tests均零改动;
无关用户改动与历史草稿不纳入。门禁绿不消除真机表单停点,C2b未完成。

## 25. 实施裁定 P5Q-C2B-09

### 25.1 裁定原文

原因:live-10 表单字段集合、回调与 action 全部符合。唯一失败点是 PROJECT_NAME:property-viewer 原始 textContent 为"前导空白 + Tizen-Base-Toolchain + 尾部空白",生产 formDOM 调用 .trim() 后只去掉了前导空白(form-unverified.response.html:732-736,run.json 表单诊断)。这符合"正则缺少 g 标志的 trim 替代实现"的特征,说明页面脚本覆盖了 String.prototype.trim。我们用 page.evaluate 在页面主环境中运行取数函数,会受页面对内置函数的改写影响。这是设计缺口:冻结稿没有考虑页面主环境的内置函数不可信。
长期方案(改到隔离环境运行)留待 R1 设计修订,本轮只做最小修正。

### 25.2 执行顺序与边界

基线befd9a8,git pull --ff-only为Already up to date。冻结稿仍为
0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950。
先在本机缺陷trim夹具上复现,生产取数返回原始文本,Node规整比较;
redactDOM必须在页面完成的身份规整用裁定指定局部正则。首提交仅生产修正、测试与记账。
其次spikes跟进表单/结构/配置取数,记录每页九个内置函数的原生布尔值,单独提交。
两步离线验收通过后再请求新的聊天“开始”,ping/pong后才能启动live-11。
本裁定不等于已完成隔离环境方案,不扩大网络放行或改写冻结稿;历史证据不改。
live-11未启动,表单联动与页面内置函数原生性仍NOT_COLLECTED;不进入C3。

### 25.3 第一步生产改动与缺陷夹具

formDOM只返回原始label/viewers/option text/name/body_text;Agent.snapshot在Node调用
normalizeFormDOM,统一规整并生成role/heading。buildId在页面只采原始标签/表头/单元格,
在Node做恰好一个、Summary/Id列及数字一致性判定。registerRefresh仅从页面采原始
脚本/属性文本,Node提取回调与解码;fill双列表choices文字也在Node规整,与快照一致。
redactDOM的Welcome/Triggered By用函数内局部正则
`/^[\s\u00a0]+|[\s\u00a0]+$/g`,不使用页面trim;身份边界与secret子串规则不变。
没有更改Policy、拦截面、放行集合、登录交互、form action或校验器接受的字段集合。

真实Chromium离线夹具在about:blank,只导入live-10表单DOM,拒绝网络与外站解析。
分正常/缺陷trim两趟:表单/option规整、buildId、Welcome/Triggered By脱敏及Python
写前/写后检查、刷新登记共8子例,加外层1例;原41个DOM测试全部保留。
页面取数函数的静态断言拒绝trim/trimStart/trimEnd/matchAll/toLowerCase/toUpperCase调用;
规整函数不序列化到页面。所有原始文本仅在代理内存,不越过Python协议边界。

修前before-fix.log含夹具自身PageRedactor构造参数错误,不作纯回归证明;
改为实例化后更新identities,再跑before-fix-corrected-fixture.log(exit1):45pass/5fail,
其中缺陷trim的表单QB_FORM_CHANGED、buildId=null与Triggered By身份残留均复现;
另有新增option空白规整要求及外层聚合失败。修后Node为50/50,
unit120/120、安全4/4,见evidence/C2b/c2b-09-production/node-gates.log。
正常/缺陷两趟的规整快照与脱敏HTML逐字/逐字段相等,旧41个DOM用例不变。
现场trim是否真的被改写要等live-11九项布尔探测,本轮不把合成夹具当真机事实。

### 25.4 第一步验收

evidence/C2b/c2b-09-production/记录完整命令/原文。全部门禁exit0:
pytest2165 passed/1 skipped(116.91s);mypy113 files;Ruff clean;
lint-imports6 kept/0 broken;check_design_doc0 problem。
Node三个入口3 passed(22.81s),unit120/120、DOM50/50(原41+新9),安全4/4。
Python测试计数不变;Node子用例单列。完整暂存树Ruff:
5cf878164d9c9b7a983993788a46a70e3e74e40b -> /tmp/p5q-c2b09-production-lint-di6avA。
之后仅补记账。第一步推送后仍不真机,先同步spikes原始DOM消费者;
不把此处测试通过当成live-11已经取证。

### 25.5 第二步取证脚本跟进

第一步已独立提交推送4a4a727。本步仅spikes代码与证据/记账,不再改生产。
表单诊断调用生产normalizeFormDOM;ID结构采样只在Node处理导航标签、Summary/Id
列与数值;配置来源采样的面包屑、构建名、复制路径脚本解析和Child Build标题
也移到Node。仍按原顺序复算validateForm,不改五项/两项配置判据、不放宽任何停止条件。
ID采样中的非Id单元格只在内存用于选择Id列,不写入结构诊断。

新增spikes/p5q_c2b_intrinsics.mjs:login成功后、每个read(含可诊断的ID不符)
及open_form可诊断结果后,只读采样如下九项,每项只返回true/false:
String.prototype.trim/replace/split/includes、Array.prototype.map/filter/includes、
JSON.stringify、RegExp.prototype.exec。按Function.prototype.toString.call(f)中
是否含[native code]判定,不归档函数源码;记录command/页面脱敏地址/相对时间。
WORKER_BLOCKED、NEW_PAGE、runtime.failure及其它立即停止错误仍先停止,不为探测绕过。
采样前后检查运行状态与页面地址,地址变化仍QB_READ_REDIRECTED。

离线新增14项:form诊断1、ID/child来源1、原生性及配置12(九项逐一包装后对应false,
其余不变;正常九项全true;父/配置归档在缺陷trim下的核对结果不变)。
自测form27/27、ID15/15、intrinsics12/12、既有通道/地址22/22,
均network_requests=0、无release。Node配置67/67、unit120/120、DOM50/50、安全4/4。
完整命令与日志:evidence/C2b/c2b-09-spikes/README.md。

本次修正不是任意页面内置函数篡改下的完整隔离方案。局部正则仍处于页面环境,
Array/RegExp等也未迁入隔离环境,按裁定留R1;原生布尔值只是现场观察不是安全证明。
live-11尚未创建目录或打开浏览器,没有页面原生性/新联动事实。

### 25.6 第二步验收与live-11人工闸门

日志同c2b-09-spikes目录,全部exit0:

| 验收 | 结果 | 日志 |
|---|---|---|
| pytest全量 | 2165 passed/1 skipped,109.10s;较第一步计数不变 | pytest.log |
| mypy | 113 files,无问题 | mypy.log |
| Ruff完整待提交树 | All checks passed! | ruff.log |
| lint-imports | 6 kept/0 broken | lint-imports.log |
| check_design_doc | 0 problem | design-check.log |
| Node四入口 | 4 passed,20.64s;配置67/67、unit120/120、DOM50/50、安全4/4 | node-gates.log |
| 自测 | intrinsics12/12、form27/27、ID15/15、既有22/22 | *self-test.log |

Ruff完整暂存树d0d06745f648af32d69e4397e816319451a39083导出到
/tmp/p5q-c2b09-spikes-lint-X8ohj2;之后仅补文档/日志。git diff --cached --check为空。
四安全组Worker走b:browser_fail_closed:shared_worker closeTarget成功,
worker为Error类异常,cleanup=true、attackHTTP0/WS0;其它三组通过。
hashes.log确认冻结稿与live-10/run.json、form-unverified.response.html字节不变。
本步相对4a4a727生产、design.md、冻结稿零diff。无关既有改动不纳入。

第三步待新回复“开始”,先ping/pong才弹浏览器。按live-10顺序只读父overview/variables、
子overview/variables/step_status,由当次父页五项核对取得配置ID,登记后只读配置并核对两项;
form_evidence仅Full→Partial→Full,不点Ok、不submit、form_action_releases须0。
表单失败先按§24取证再停止;其它立即停止条件不变。页面/原生性/联动/现场release
仍NOT_COLLECTED,不能拿离线零release代替。没有新增停止项,不进入C3。

### 25.7 live-11实际取证

基线cbedcf5,本轮新聊天“开始”后启动;ping/pong先于浏览器,人工登录一次,
登录POST一次,无重试。完整命令/逐页状态与原文见evidence/C2b/live-11/README.md。
冻结稿仍0a3f5e0b…1950;live-01至live-10不改。退出1,STOPPED/QB_FORM_CHANGED;
浏览器与临时目录均清理,不是等待后主动降级或另开会话。

| 项目 | 实测 | 证据(均live-11/) |
|---|---|---|
| 登录 | /dashboard;not_signin=true,password_inputs0,Sign Out1 | run.json:2384 |
| 父1193467 overview/variables | HTTP200,VERIFIED | 01.response.html;02.response.html |
| 子1193469 overview/variables/step_status | HTTP200,VERIFIED | 03.response.html;04.response.html;05.response.html |
| 失败状态 | 子Summary=Failed;父Child Build=FAILED;组合架构一行 | 03.response.html:828;01.response.html:890/:892 |
| 配置来源与页 | 本次父页取得1917,五项全true;配置页面包屑/复制路径两项全true | run.json:2678/:2697;06.response.html |
| 初始表单 | open_form成功;PROJECT_NAME=Tizen-Base-Toolchain;validateForm通过 | run.json:2548/:2846;form-initial.html |
| BUILD_TYPE联动 | 仅尝试Full→Partial;本地选中Partial,回调POST被拒;没有完成后快照,未执行Partial→Full | run.json:2819/:2978/:3192 |
| 失败只读取证 | stage=BUILD_TYPE_Partial,结构重算仍全绿,字段无差集/重复,原错误保留 | run.json:3113/:3617;form-unverified.response.html |
| 零提交与清理 | form_action_releases0,released=false,runtime_failure=null;browser/profile清理true | run.json:3802/:3992 |

九项原生性只存布尔值,未读取/归档源码。以下八次均为trim=false,其余八项true:
login:2394、父overview:2416、父variables:2438、子overview:2460、子variables:2482、
子step_status:2504、配置:2526、open_form:2548(均run.json行号)。
其余项为String.prototype.replace/split/includes、Array.prototype.map/filter/includes、
JSON.stringify、RegExp.prototype.exec。这是按指定Function.prototype.toString方法
取得的现场记录,不声称覆盖任意内置函数篡改或证明隔离环境安全。

run.json sha256=832cb060ad4dde6b31b081148b4d8e6390ea5dd99cb8532e1c381295690b4cf1。
八个HTML文件的hash/脱敏检查均通过,见integrity.log。两份表单HTML都为
8f8b5025…e12e;HTML属性未反映select当前selected状态的变化,运行时Partial选中
由诊断快照证明,不能据HTML相同声称没有本地设值。现场身份自检用内存身份集合,
归档后仅对已脱敏字节复查,没有保存身份或凭据。

### 25.8 新停止事实:字段回调带random被拒

初始表单页版本10,action为
`/wicket/page?10-1.IFormSubmitListener-form`;
BUILD_TYPE登记回调为
`/wicket/page?10-1.IBehaviorListener.0-form-editor-content-basicProperties-1-property-editor-editor-wrapper-select`,
无random(run.json:2848;form-initial.html:757)。
相对时间66421ms,fill阶段实际XHR POST /wicket/page的脱敏query是
`<KEY>=<REDACTED len=0>&random=<REDACTED len=19>`,has_random=true,allowed=false,
没有响应状态(run.json:2819)。监听器作为无等号查询项被既有脱敏规则遮蔽,
本轮不恢复原文、不声称证明其余查询逐字等于登记值;但额外random已被直接记录。
生产Policy.allow在:113按url===fieldUrl匹配,没有放行该POST。

随后71222ms还有一个fill阶段GET XHR带action/random被拒(run.json:2832);
没有fill阶段Document GET、没有主帧重新导航、没有成功回调响应。
字段等待30秒后QB_FORM_CHANGED;失败诊断的production_passed=true、first_failure=null,
所以不是又一次PROJECT_NAME/结构失败。未重试、未追加放行、未忽略random。
候选修订只能由设计方界定回调附加参数的接受范围并保留逐字段约束,本轮不实施。
**新增停止事实1项**,等待裁定;不执行返回Full或进入C3。

初始BUILD_REFERENCE=Ref. Snapshot,选项Live/Ref. Snapshot/Snapshot Number;
SNAPSHOT_NUM=tizen-base-toolchain_20260924.094908,唯一选项。
停止诊断仍显示这些值,页面版本/action与初始相同;这不证明服务端联动后的结果。
完成后的回调版本/action/选项刷新仍NOT_COLLECTED。
父/子现状字段以本轮归档重新提取,fields.log记原名/显示名/行号:
父Build Package List对应BUILD_PKG_LIST_MODIFY四行;子BUILD_PKG_LIST245行包含该四行;
子TRIGGER_ID1193467、FAIL_FAST=yes、EACH_GBS_BUILD_STATUS存在且空。
父Live/do not need select与子Ref. Snapshot/URL差异沿§22裁定留R1。

拦截器请求阶段GET110/POST2,allowed75/denied37;两POST为人工登录获准一次与
字段回调被拒一次,不是两次构建提交。响应阶段200x61/302x2。被拒:
ckeditor10、bootstrap两字体9+9、GET XHR8、POST XHR1;trace/wrapper37/37,
帧归属拒绝0,WORKER_BLOCKED/NEW_PAGE0。不是服务端实收统计。

### 25.9 live-11归档验收

本轮真机已经停止,以下均为离线/本机门禁,没有再次访问QuickBuild。
完整命令与原始日志在live-11/README.md,全部exit0:

| 验收 | 结果 | 日志 |
|---|---|---|
| pytest全量 | 2165 passed/1 skipped,111.67s;计数不变 | pytest.log |
| mypy | 113 source files,无问题 | mypy.log |
| Ruff完整待提交树 | All checks passed! | ruff.log |
| lint-imports | 6 kept/0 broken | lint-imports.log |
| check_design_doc | 0 problem | design-check.log |
| Node三入口 | 3 passed,19.93s;unit120/120、DOM50/50、安全4/4 | node-gates.log |
| 归档核对 | 八HTML hash/脱敏、native八样本、五项/两项、停点/清理/零release均通过 | integrity.log |

安全Worker组走b:browser_fail_closed:shared_worker closeTarget成功,worker为Error,
browser/profile已清理,attackHTTP0/WS0;其它三组通过。
Ruff对暂存树df3ff86eacd400fd4d11904457cddc22a6f60feb导出到
/tmp/p5q-live11-lint-plJJ6v执行;之后仅补文档/日志。文档diff --check为空,
原始脱敏HTML的缩进/行尾不为消除whitespace提示而改动。
本提交只有INDEX/progress/appendix-c与live-11证据;生产、spikes、tests、冻结稿、
design.md、检查器零改动,历史证据原样保留。无关既有改动不纳入。
门禁绿不能销掉实际回调停点;C2b仍STOPPED,等待设计方裁定,不重试、不进入C3。

## 26. 实施裁定 P5Q-C2B-10

### 26.1 裁定原文

原因:live-11 初始表单核对通过。BUILD_TYPE 设为 Partial 时,浏览器实际发出的字段回调 POST 是"登记的回调地址 + &random=<19 个字符的值>",与登记的精确地址不等,被拒,随后 QB_FORM_CHANGED。冻结稿 §3.4(第 247 行)已预先规定:观察到这一行为时,"精确原文"规则改为"登记原文 + 末尾恰好一个 random= 十进制小数参数",并按 R1 记入附录 C。本裁定按此落实,不属于偏离冻结稿。
另记 live-11 取得的表单事实:BUILD_REFERENCE 选项为 Live / Ref. Snapshot / Snapshot Number,默认 Ref. Snapshot;SNAPSHOT_NUM 只有一个选项 tizen-base-toolchain_20260924.094908,与子构建 1193469 的 SNAPSHOT_NUM_URL 一致。

### 26.2 执行顺序与边界

基线56b6d2b,git pull --ff-only为Already up to date。冻结稿sha256仍为
0a3f5e0b3848ac077e836fea208aec4bd540d2458f9f4d627d8ae3f842191950,不修改。
第一步只改Policy.allow的fill当前字段POST:登记原文,或其后缀恰为
`&random=0.<1至20位数字>`;先匹配完整登记前缀,后缀全长匹配,不忽略换行或编码差异。
仍一次放行、消费fieldUrl;阶段/帧归属/响应307和308规则不变。
提交action不得带random,定时刷新附加random继续拒绝。不全局剥离参数。

第二步仅spikes:诊断保留匹配指定数值语法的random和Wicket监听器键名,
不反向扩大生产接受范围(科学计数法只可记录,不能放行)。
第三步等待新“开始”,ping/pong后人工登录live-12,顺序同live-11;
仅BUILD_TYPE Full→Partial→Full,不点Ok、不提交,form_action_releases必须0。
现场未实跑前页面/配置/联动均NOT_COLLECTED;任何原停止条件仍有效,不进入C3。

### 26.3 第一步测试与验收

evidence/C2b/c2b-10-production/保存命令、原始输出与哈希。
新增Node单元22例,共142/142:4个正向边界(含1/20位小数)、16个非法后缀,
当前字段/方法/阶段约束1例、action/refresh隔离1例。监听器不同、一次用完、
多参数、重复random、空/负/科学计数/字母、编码差异、尾部换行均拒绝。
新增真实Chromium本机夹具1例,DOM总数51/51:Math.random生成的两个POST由
本地服务器实收,分别为Partial和Full;fieldFinished=true,action实收0、released=false。
这些是合成数据,非真机证据。既有Node/Python用例均保留,Python nodeid数不变。

四安全组4/4:Worker走b:browser_fail_closed,shared_worker closeTarget成功,
worker为Error异常;browser/profile清理true,attackHTTP0/WS0;307/308、逐跳、
凭据隔离组全部通过。该fail-closed分支符合既有C2B-01裁定。

| 门禁 | 实跑结果 | exit/证据 |
|---|---|---|
| 全量pytest | 2165 passed/1 skipped,119.15s | 0,pytest.log |
| mypy | 113 source files,无问题 | 0,mypy.log |
| Ruff完整待提交树 | All checks passed! | 0,ruff.log |
| lint-imports | 6 kept/0 broken | 0,lint-imports.log |
| check_design_doc | 0 problem | 0,design-check.log |
| Node三个入口 | 3 passed,28.92s;unit142/142,DOM51/51,safety4/4 | 0,node-gates.log |

Ruff在暂存树303ab28330205afa574af59278201ef159ff1a64的导出副本运行,
导出目录已清理,不再累积临时副本;之后仅补文档/日志。
hashes.log确认冻结稿与live-11的run/form字节未变。历史live目录不改;
无关.gitignore/四个文档删除及未跟踪草稿不纳入。
本提交不启动浏览器真机、不开展C3。现场联动仍待live-12。

### 26.4 第二步取证脚本跟进

第一步生产提交2ee8ab6已推送。本步仅spikes/p5q_c2b_evidence.mjs及文档/证据。
诊断query逐项保留键名恰为random且值全长匹配
`^\d(\.\d+)?(e-\d+)?$`的原值;Wicket监听器形态的键名不再受64字符普通键名
限制,无等号的裸监听器项仍记录为裸项,有值时值照常遮蔽。
其它v/路径/凭据/身份脱敏与写前写后自检不变。
记录允许科学计数、重复random是为了如实取证,生产仍按第一步严格拒绝。
新增14个离线向量,包括实际长监听器形态、数值/科学计数、重复项、错误语法、
大小写、凭据值和长的非监听器键;不生成任何网络请求。
本步验收后才请求新的聊天“开始”;live-12未启动,历史live目录原样保留。

首跑14个新增向量逐项全部PASS,但旧selfTest汇总常量仍写22;
self-test-before-count-fix.log保留该原文,不作为新计数依据。
已将汇总改为随实际通过条目累加,重跑self-test.log为36/36、network_requests=0;
此处只更正测试报告计数,未改变判定或脱敏规则。

### 26.5 第二步验收与live-12人工闸门

全部命令与输出:evidence/C2b/c2b-10-spikes/README.md和相邻日志。

| 门禁 | 实跑结果 | exit/证据 |
|---|---|---|
| 查询/通道自测 | 36/36(原22+新增14),network_requests0 | 0,self-test.log |
| 表单/ID/原生性自测 | 27/27、15/15、12/12,零网络/零release | 0,*self-test.log |
| 全量pytest | 2165 passed/1 skipped,120.89s | 0,pytest.log |
| mypy | 113 source files,无问题 | 0,mypy.log |
| Ruff完整待提交树 | All checks passed! | 0,ruff.log |
| lint-imports | 6 kept/0 broken | 0,lint-imports.log |
| check_design_doc | 0 problem | 0,design-check.log |
| Node四入口 | 4 passed,23.49s;unit142/142,DOM51/51,配置67/67,安全4/4 | 0,node-gates.log |

Worker仍走b:browser_fail_closed,shared_worker成功/worker异常Error,
browser/profile清理true、attackHTTP0/WS0;其余三组通过。
Ruff暂存树bb8abe5a9d4a9ffc4b97b9b96810047a1e36fc99导出后校验,副本已删除。
其后只补文档/日志。本步相对2ee8ab6生产与冻结稿零diff;
hashes.log确认冻结稿/live-11仍同字节。无关用户改动不处理、不提交。

live-12尚未启动,未创建live-12目录、未请求QuickBuild、未弹窗。
待本步推送后新的聊天“开始”,命令通道ping/pong先于浏览器,顺序严格同live-11:
login、父1193467 overview/variables、子1193469 overview/variables/step_status、
由本次已核对父overview取得配置ID并登记、读配置页完成两项核对、
BUILD_TYPE Full→Partial→Full、close。不是预先假定配置ID。
记录各回调query的random原值、action/版本/选项/整页重渲染;
form_action_releases必须0。不点Ok、不submit,失败按§24先取证后停止。
WORKER_BLOCKED、NEW_PAGE、runtime.failure等立即停止条件不变。
页面/配置/联动/release的真机结果全部NOT_COLLECTED,不以本机夹具代替;不进入C3。

### 26.6 live-12现场完成

2026-10-14,19792bb推送后收到新的聊天“开始”。按§26.5顺序执行,先ping/pong,
再弹窗一次人工登录,之后只读五个构建页、由本次父overview五项核对取得1917、
register_config、读配置页两项核对、BUILD_TYPE Full→Partial→Full、close。
命令与逐页锚点:evidence/C2b/live-12/README.md;现场run.json原字节保留。
exit0,COLLECTED,stop=null,无重试;未读1186372,未点Ok/submit/Accept。

| 项目 | 实测 | 证据(live-12/) |
|---|---|---|
| 登录 | POST/signin302→GET/dashboard200,空查询;not_signin=true,password0,SignOut1 | run.json:2442与diagnostics |
| 父1193467 | overview/variables均200且VERIFIED | 01/02.response.html |
| 子1193469 | overview/variables/step_status均200且VERIFIED | 03/04/05.response.html |
| 失败状态 | 子Summary Failed;父Child Build FAILED,架构组合一行 | 03.response.html:828;01.response.html:883/:892 |
| 配置 | 1917,RBS/TRIGGER,五项来源/两项页面核对均通过 | run.json:2737/:2756;06.response.html |
| 联动 | 初始Full,Partial成功后返回Full;两POST均200 | run.json:2944/:3076/:3206;form_network |
| 安全/清理 | form_action_releases0,released=false,runtime_failure=null;browser/profile清理true | run.json:3870/:4064 |

原始登记callback始终为
`/wicket/page?10-1.IBehaviorListener.0-form-editor-content-basicProperties-1-property-editor-editor-wrapper-select`。
Full→Partial:147147ms请求、147435ms响应,末尾random=0.3453609721766676,
逐字等于登记原文加一个允许后缀(run.json:2885/:2898)。
Partial→Full:148678ms请求、148963ms响应,random=0.6594204778800775
(run.json:2911/:2924)。均fill/XHR POST、allowed=true、HTTP200。

三个快照的action始终`/wicket/page?10-1.IFormSubmitListener-form`,page_version10,
callback原文不变。两次main_frame_navigations与document_gets均空
(run.json:3599/:3600/:3865/:3866),未观察到整页重渲染导航;
不据此推断服务端没有内部刷新或局部DOM替换。
选项文字/值集合全相同,只有BUILD_TYPE的selected标志Full→Partial→Full;
其它字段选中项不变。BUILD_REFERENCE仍Ref. Snapshot,选项Live/Ref. Snapshot/
Snapshot Number;SNAPSHOT_NUM唯一选项tizen-base-toolchain_20260924.094908。
三张HTML hash相同,因selected运行时属性不必反映在序列化属性中;
以运行时快照与实际回调响应证明联动,不把相同HTML当成没有设值。

拦截器请求阶段GET112/POST3,allowed77/denied38;响应200x63/302x2。
三POST为人工登录一次、字段回调两次,构建表单action放行0。
拒绝ckeditor10、bootstrap两字体9+9、GET刷新XHR10,没有补登记静态资源;
本轮未阻断取证。trace/wrapper38/38,帧归属拒绝0,WORKER_BLOCKED/NEW_PAGE0。
该统计是拦截器观察,不冒充服务端接收数。八个原生性样本trim=false、其余八项true。

fields.log重新按HTML结构提取:父BUILD_PKG_LIST_MODIFY四行,显示名Build Package List;
子BUILD_PKG_LIST245行包含全部四行,TRIGGER_ID1193467/FAIL_FAST=yes/
EACH_GBS_BUILD_STATUS存在且空。父Live/do not need select与子Ref. Snapshot/URL
差异仍留R1,不自行认定等价;自动刷新random仍拒绝,隔离环境方案仍待R1。
成功Base子构建样本/真正提交后的响应与build-id映射本轮NOT_COLLECTED。
附录C已补回调取证;本轮新增停止事项0,不标设计闭合、不进入C3。

run.json sha256=e74fa531d4f8857912a0fbbf9f70ccbca4479a226ce8b41ef094f40c1d271a08。
九HTML逐一hash与写后脱敏检查通过。离线核对脚本首跑误以为表单快照也有status,
KeyError原文与exit1保留在integrity.log;不改原始证据,按read页/表单快照各自结构
重跑integrity-final.log exit0,全部hash、联动、五项/两项、零release与清理通过。
该修正只涉及本次临时离线核对,未改任何生产/取证脚本、判据或现场记录。

### 26.7 live-12归档验收

真机close之后不再请求QuickBuild,只跑离线/本机门禁。完整命令与原文见live-12/README.md。

| 门禁 | 实跑 | exit/日志 |
|---|---|---|
| 全量pytest | 2165 passed/1 skipped,118.52s,计数不变 | 0,pytest.log |
| mypy | 113 source files,无问题 | 0,mypy.log |
| lint-imports | 6 kept/0 broken | 0,lint-imports.log |
| check_design_doc | 0 problem | 0,design-check.log |
| Node三入口 | 3 passed,20.07s;unit142/142,DOM51/51,safety4/4 | 0,node-gates.log |
| Ruff完整待提交树 | All checks passed! | 0,ruff.log |

Worker组仍走b:browser_fail_closed,shared_worker closeTarget成功/worker异常Error,
browser/profile已清理、attackHTTP0/WS0;其它三组通过。
本次提交只含INDEX/progress/appendix-c/live-12证据,生产/spikes/tests/冻结稿/
design.md/检查器零diff,历史live目录保留,无关用户改动不处理。
Ruff对暂存树80058cb1811f0422d813802e34c0641fd3b9006c导出副本运行,
/tmp/p5q-live12-lint-XClBU8已清理;之后只补文档与日志。
文档diff --check为空;原始脱敏HTML缩进/行尾保持归档字节,不为消除whitespace提示而改动。

## 27. 实施裁定 P5Q-C2C-01:v1.5 冻结

### 27.1 冻结登记与范围

2026-10-14,开工HEAD=b6bec94f4336740d5fd6fb9b58607cd1af355128,
分支clang-fix-campaign。已读本stage计划、闭合记录及挂账;无关.gitignore改动、
docs四个删除与未跟踪草稿不处理。
冻结文件:docs/clang-fix-campaign/p5q-qb-trigger-design-v1.5-FROZEN.md。
实跑sha256=f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c,
与FatTank给定值逐字相等;文件不得修改。
v1.5取代v1.2-FROZEN成为P5Q权威设计,v1.2-FROZEN保留备查。
下一步为C2c,只做第10节C2c六项补齐与第9.2/相关9.1/9.5门禁;
拦截安全子集从头复跑,第9.3其它用例与第9.4真机不在本任务范围。
不访问真实QuickBuild、不弹登录窗口、不做Gerrit推送,永不点击Accept/Ready to Accept。

### 27.2 计划与挂账

1. 本机可满足性验证:隔离环境与设值事件计数,全部使用合成页面。
2. 代理读取改为响应原始字节+严格解码+隔离环境惰性解析;活动表单只在隔离环境取数。
3. 惰性诊断与身份位置遮蔽、刷新删除、字段完整窗口/启动自检、结构失败诊断。
4. design.md按附录A末尾同步v1.5.23;测试逐条补齐,静态断言逐名称反控。
5. 全量门禁与四安全组,同步证据后提交推送,不进入C3。

具名挂账:第9.4节第1.6步a的原始字节与活动文档比对、成功样本,
b的BUILD_NOTES样本均放C5。成功样本与BUILD_NOTES样本可由C6补齐;
原始字节比对及完整填表演练必须先于真实提交,挂账未核验关闭前不得CLOSED。
本机合成夹具不能替代这些真机前提。

### 27.3 停止报告 P5Q-C2C-02:stop查询正例与闭集不相容

状态:已由 P5Q-C2C-03 裁定关闭(见§28)。以下保留原停止事实,不是新停点。
权威文件未修改,未自行放宽规则或改写验收用例。

| 原文位置(v1.5冻结稿) | 要求与实际冲突 |
|---|---|
| 第9.2节首条,L756 | 必须有“查询中含stop字样但监听器名无破坏性动作的合法回调→放行”正例 |
| 第3.5节open_form第6项,L306 | 字段回调query完整匹配`^\d+-\d+\.IBehaviorListener\.\d+-[A-Za-z0-9:_-]+$`,不能登记额外`&value=stop` |
| 第3.4节fill行,L282 | 登记原文之外只容许末尾一个十进制random参数,不能容纳stop值 |
| 第3.4节永久禁止,L268-L269 | stop若放入监听器组件名,会命中破坏性动作正则,必须拒绝 |
| 第3.4节已登录只读行,L280 | 定时刷新全部拒绝,且删除刷新登记集合;不能沿用旧刷新正例 |

既有`tests/node/test_qb_browser_agent.mjs:209`正例实际是登记的refresh GET,
`?1-1.IBehaviorListener-refresh&action=ajaxRefresh&value=stop`。
它在b6bec94能放行,但按v1.5必须拒绝。改用字段回调时,stop只可能位于
额外参数(不符合登记文法)或监听器组件(触发永久禁止);数字前缀/random
均不能承载stop。故这条端到端放行正例无法与现有闭集同时满足。

离线取证:[spec-gap-check.mjs](evidence/C2c/spec-gap-check.mjs)从本地不可变
`b6bec94:.../qb_browser_agent.mjs`读取规则,不使用未提交实现,不启动浏览器。
[spec-gap.log](evidence/C2c/spec-gap.log)五项断言全部符合实测,主动exit2表示规格停止:
普通字段回调放行;带`&value=stop`的callbackURL与beginField各拒绝;
组件名form-stopper被永久禁止;旧登记刷新GET在基线放行。
网络请求0。该探针证明旧实现/登记文法的事实,不冒充C2c验收绿。

候选处理(未执行,需裁定):将第9.2节这一个用例拆清层次,在永久禁止判定层
断言非监听器查询值中的stop不被误判为破坏动作;最终请求仍遵守阶段/文法闭集,
不能据此新增放行。旧refresh用例改为必须拒绝的回归例。
若设计方希望保留“最终放行”的正例,需提供与现有闭集兼容的具体URL,
或另行裁定文法/安全边界;实现方不自行补参数例外。

本机可行性预检已证明CDP隔离环境可建立,selectOption/check/fill+blur的change
计数为1/1/1,网络0,见[preflight-baseline.log](evidence/C2c/preflight-baseline.log)。
它不证明完整隔离生命周期、原始响应读取或所有字段窗口要求已经实现。
停止前的未完成实现存入[implementation-wip.patch](evidence/C2c/implementation-wip.patch),
仅供续做定位,未验收、不可部署;包含暴露此冲突的未完成测试,不是可应用的交付补丁。
已只撤销本轮自己对生产/tests的修改,`git diff --stat -- tizen-ci-triage tests`为空;
design.md尚未同步,冻结稿不改,用户既有改动不处理。

第二步1-6均未交付,第9.2新增静态断言逐名变异测试NOT_RUN。
下节如有基线门禁结果,只证明此次冻结登记/停止报告的文档提交未改坏现状,
不代表C2c完成。停止后不继续编码、不运行真机取证、不进入C3。

### 27.4 冻结登记与停止报告的基线回归

以下均为本轮重新实跑,生产/tests仍为b6bec94;不是v1.5新增验收。
完整命令和日志在[evidence/C2c/README.md](evidence/C2c/README.md)。

| 门禁 | 本轮结果 | exit/证据(C2c/) |
|---|---|---|
| 全量pytest | 2165 passed / 0 failed / 1 skipped,123.74s,新增测试0 | 0,pytest-baseline.log |
| mypy | 113 source files,无问题 | 0,mypy-baseline.log |
| lint-imports | 6 kept / 0 broken | 0,lint-imports-baseline.log |
| design.md检查器 | 0 problem,仍为既有v1.5.22,不是待同步v1.5.23 | 0,design-check-baseline.log |
| Node三入口 | 3 passed / 0 failed / 0 skipped,20.14s;unit142/142、DOM51/51 | 0,node-baseline.log |
| 四安全组 | 从头重跑4/4,仅loopback假服务器 | 0,node-baseline.log |
| Ruff完整待提交树 | All checks passed! | 0,ruff-baseline.log |

Worker组走b:browser_fail_closed,shared_worker closeTarget成功,worker异常Error,
attackHTTP0/WS0,浏览器及临时目录已清理。其它三组全部通过。
Ruff导出暂存树4d86fe86dedb138db7cc7a7dc8a6da35a929ebdb,
临时目录/tmp/p5q-c2c-lint-tp36xd已清理;此后只补文档与日志。
静态断言逐名字负例NOT_RUN;第二步1-6仍未交付,没有借基线绿标完成。
本提交范围仅v1.5原字节、INDEX/progress和C2c证据;真实QuickBuild/Gerrit访问0。

## 28. 实施裁定 P5Q-C2C-03:查询含 stop 的用例按层验收

### 28.1 裁定原文

1. 冻结稿第 9.2 节首条中"查询中含 stop 字样但监听器名无破坏性动作的合法回调 → 放行",按以下三层验收,冻结稿不改:
   a. 永久禁止判定层(破坏性监听器正则)单元测试:
      - stop 只出现在监听器组件名以外的查询里(例如合法字段回调后接 &value=stop,以及 ?q=stop)→ 判定为"不命中永久禁止";
      - 组件名含 stop(例如 form-stopper)→ 命中永久禁止。
   b. 端到端放行判定:上面带 &value=stop 的地址最终仍被拒,因为它不符合放行文法。不得为这条用例增加任何放行例外或参数例外。
   c. tests/node/test_qb_browser_agent.mjs 第 211 行"登记的刷新 GET 带 value=stop 放行"的旧正例,改为"在任何阶段都必须拒绝"的回归例。
2. 已接受残余:破坏性正则按子串匹配,组件名中含 desktop、nonstop 之类的词会被误拒,后果是该字段失败、表单作废(方向安全)。本版接受;真机遇到时停止并按 R1 处理。
3. 理由:v1.5 下只读页面查询必须为空,字段回调文法闭合,只允许末尾一个十进制 random,stop 放进组件名又会命中永久禁止,因此不存在"含 stop 且合法放行"的地址。该用例的原意是"永久禁止不误伤查询值",按层拆开后原意保留。
4. 下次修订设计文档时并入正文。

### 28.2 续做边界

开工HEAD=68b71aa;冻结哈希复核仍为f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c。
按§27计划续做①–⑥,旧WIP只参考不套用。C5/C6挂账不变,只做本机/离线,
不访问真实QuickBuild、不做Gerrit推送、永不点击Accept/Ready to Accept、不进入C3。

### 28.3 实现过程与原始字节取证

①隔离读取、②位置脱敏/惰性诊断、③删除刷新、④字段计数窗口/启动自检、
⑤错误诊断应答、⑥附录A照录已在工作树实现,最终门禁通过前不标DONE。
未直接套用§27归档的WIP;重新按v1.5检查函数及测试,冻结稿原字节未改。

解码本机测试曾发现`response.body()`不是所有charset下的原始字节:
Latin-1的`636166e9`变为UTF-8的`636166c3a9`,非法UTF-8的`c328`变为
`efbfbd28`。初轮Node入口因此1 failed/4 passed,原始失败留在
[node-gates.log](evidence/C2c/implementation/node-gates.log),不冒充绿。
随后用同一loopback HTTPS服务器、同一浏览器级双阶段拦截,对照冻结稿允许的
另一路`Fetch.getResponseBody`,在`Fetch.continueResponse`前取正文:
Latin-1、非法UTF-8、合法UTF-8、合法U+FFFD四组均逐字节等于服务器发送值,
`base64Encoded=true`,4/4;非法UTF-8严格解码拒绝、合法U+FFFD正常。
见[raw-bytes-probe.log](evidence/C2c/implementation/raw-bytes-probe.log),
复现入口`tests/node/p5q_c2c_raw_bytes_probe.mjs`。仅4次本机GET,无外网,
浏览器/证书临时目录已清理。据此采用第3.1节明确允许的Fetch路径,
不是设计矛盾或新裁定;不使用替换字符猜测、不补发HTTP请求、不放宽严格解码。

已完成的中间检查:Python脱敏+驱动193/193;静态逐名变异183/183;
mypy113 source files;lint-imports6 kept/0 broken;design.md检查器0 problem。
最终完整门禁及源码位置以下节为准,本段不是最终验收结论。

### 28.4 最终实现与逐项落点

以下行号为本轮交付工作树;提交SHA由Git外部锚定,本文件不自记。

| C2c条目 | 实现与验收落点 |
|---|---|
| ①隔离环境/原始字节 | `qb_browser_agent.mjs:159`主拦截响应阶段Fetch正文;`:334`TrustedPage逐导航重建;`:364`严格charset解码;`:648`同次主帧导航请求ID绑定,读完清空;`test_qb_browser_trusted.mjs`37/37 |
| ②惰性脱敏/身份位置 | `qb_browser_agent.mjs:254`惰性document,Welcome/Triggered By/Requested By遮蔽,登记外只计数;`qb_redact.py:49/:238`三位置与字节自检;20组共用向量,Python+driver233/233,DOM63/63 |
| ③刷新删除 | `qb_browser_agent.mjs:44`Policy无刷新登记/提取;`:182`仅获准请求更新活动时间;所有阶段刷新拒绝,连续被拒流不延长字段静默窗口 |
| ④字段与启动自检 | `qb_browser_agent.mjs:711`fill一次设值/change,文本受控blur,`@freeze`仍回调,计数延续到下一字段/末字段读回;`:811`启动合成控件1/1/1,版本trace;`test_qb_browser_fields.mjs`12/12 |
| ⑤结构诊断应答 | `qb_browser_agent.mjs:554/:635`先撤销登记再惰性取证,失败无部分输出;`qb_browser.py:37/:130`逐个解码后的HTML/结构字符串自检并保留原错误;不把JSON转义串当HTML解析 |
| ⑥design.md | v1.5.23;`:5`元信息/记录;`:2645`QB_FETCH_FAILED补句;`:2757`第6条追加;`:2765`第14条新增;`:3482`文末版本;附录A逐字照录,第11条原样;检查器0 problem |

`stop`三层用例在`tests/node/test_qb_browser_agent.mjs`:
`:207`永久禁止层、`:214`最终闭集拒绝、`:190`六阶段旧刷新回归。
没有新增参数或放行例外。完整逐名静态负例见
[static-mutations-final.log](evidence/C2c/implementation/static-mutations-final.log):
对生产源码的内存副本逐项加一行,使用同一AST判据证明变红;183/183,
包括第9.2末条的所有名字、唯一addInitScript守卫、setContent位置及Python参数限制。

内部核对修正了两处实现问题:JSON转义HTML被误作HTML解析,以及显示名为USER时
登记位置的占位符被算入登记外次数。新增含hidden字段诊断接收/嵌套凭据拒绝用例,
及两端共用USER向量(登记外次数恰1)。没有更改设计规则或安全边界。
旧read单元mock未提供新Fetch捕获槽导致首轮全仓1 failed/2236 passed/1 skipped,
原文保留`pytest-full.log`;更新mock后最终全仓绿,未删除/跳过该测试。

### 28.5 最终门禁与边界

完整命令、环境、原始输出及中间失败解释:
[implementation/README.md](evidence/C2c/implementation/README.md)。

| 门禁 | 实跑结果 | exit / 证据(implementation/) |
|---|---|---|
| 全量pytest | 2277 passed / 0 failed / 1 skipped,257.03s;基线2165/1,增加112个通过用例 | 0 / pytest-final.log |
| Python脱敏+驱动 | 233 passed / 0 failed / 0 skipped | 0 / python-final.log |
| Node六入口 | 6 passed / 0 failed / 0 skipped;单元152、静态183、可信读取37、字段12;最终DOM向量单列63 | 0 / node-final.log、dom-final.log |
| mypy | 113 source files,无问题 | 0 / mypy.log |
| Ruff完整待提交树 | All checks passed;导出树ed66947ef18eef798eefc00fb656e148740a6163,临时目录已清理 | 0 / ruff-final.log |
| lint-imports | 6 kept / 0 broken | 0 / lint-imports.log |
| design.md检查器 | 0 problem | 0 / design-check.log |
| 四组拦截安全 | 从头重跑4/4,loopback-only | 0 / node-final.log |
| 冻结文件 | v1.5与v1.2哈希均未改变,相对68b71aa diff为空 | 0 / frozen-hashes.log |

四安全组按服务器实收核对:Worker/WebSocket、307/308、凭据隔离、逐跳拦截全绿。
Worker走b:shared_worker成功关闭,worker closeTarget为Error,随后整体fail-closed;
attackHTTP=0、WS握手=0、浏览器与临时目录已清理。没有因此降级保护。
第9.5的campaign_qb_profiles精确表集合/CHECK负例在全量中原样复跑通过。

本轮与冻结稿不一致或做不到的地方:无。C2C-02已由C2C-03关闭。
原始响应读取选Fetch是冻结稿允许的路径选择,不是新裁定;查询stop的分层裁定
仍须下次设计修订并入正文。冻结稿不改,无真实QuickBuild/Gerrit访问,
无人工登录,无Accept/Ready to Accept点击。C5/C6真机挂账见§27.2,未关闭前
不得P5Q CLOSED。C2c至此完成,提交推送后停止,不进入C3。
原始失败日志的pytest/Node缩进行尾空格原样保留,不为消除diff --check提示
改写证据;源代码、测试与Markdown的diff --check为空。

## 29. C3启动、C2c评审遗留与停止报告P5Q-C3-01

### 29.1 权威、范围与计划

基线`332878d6e595a139b850c2eac6ceaefb5fcec27d`,分支`clang-fix-campaign`。
开工已读本进度的计划、闭合结论和C5/C6挂账,并逐段核对冻结稿第2.1、2.2、
3.2、3.5、4、6.2、9.1节与现有状态原语/锁/隔离传输/代理协议。
权威`p5q-qb-trigger-design-v1.5-FROZEN.md`未改,sha256仍为
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`。

本轮计划:先修两项C2c遗留;再接qb-trigger CLI,按unit持sandbox锁、幂等表逐格
实现、单事务提交意图、隔离ls-remote、提交落点/诊断落盘;最后以假代理+本地裸库
完成第9.1节相关组及通用门禁。当前停在下一节所述协议缺口,未新增CLI/状态写入。
没有真实QuickBuild/Gerrit请求、没有登录弹窗、没有Accept/Ready to Accept操作。
用户已有`.gitignore`修改与docs四文件删除、其它未跟踪草稿原样保留,不纳入提交。

### 29.2 C2c评审遗留,已于C3修复

1. `qb_config.py`:读配置时按第2.1节第7条检查父配置路径必须以`root/`开头、
   以`/RBS/TRIGGER`结尾;`child_configuration_path`将最后一段替换为`build`。
   子路径不额外写入profile。测试`test_rule7_configuration_path`三种负例及
   `test_child_configuration_path_derived_not_stored`正例通过。
   CLI层的INVALID_ARGS/不启动代理集成用例仍待C3主体,不以纯函数测试冒充。
2. `qb_redact.py::_UserFields`:每个新表头行重新确定身份列,不沿用先前列号。
   共用向量`repeated-header-resets-identity-columns`在同一表内设置两段表头,
   第一段Triggered By遮蔽、第二段Package/Status保留;JS/Python共用21组向量。
   生产JS已有该行为,本轮不改生产代理或任何放行规则。

### 29.3 停止报告P5Q-C3-01:快照不可用错误应答缺少当前值

状态:**已由 P5Q-C3-02 裁定关闭**。这是C3接入现有代理时暴露的接口缺口,
不是把冻结快照下架本身当成异常设计;正常拒绝行为保持不变。

**要求位置**:

- 冻结稿§0.5:70要求stdout提示“参考快照已从 <冻结值> 变为 <当前值>,
  需在新campaign中处理”。§4.3第5步:436与§9.1填表组:702再次要求两值。
- §3.5 fill第2步:313和第6步:336只在成功返回readback/选项数;
  错误映射表规定SNAPSHOT_NUM不可用映射为REJECTED_QB_SNAPSHOT_UNAVAILABLE,
  没有指定该错误的当前选中值应答字段。

**代码事实与实测**:

- `qb_browser_agent.mjs:731-736/:756-758`:当要求的冻结值不在选项中,
  生产fill抛`AgentError('QB_FORM_VALUE_UNAVAILABLE', 'SNAPSHOT_NUM')`。
- `qb_browser_agent.mjs:587-602`:该错误只输出`ok/error/field`,且表单作废;
  不属于当前可产出diagnostic的错误集合。`open_form`成功也只返回released=false。
- `qb_browser.py:17-24/:105-111/:140-143`:Python异常只有code/released/
  diagnostic/diagnostic_failed,没有实际快照值。不能从冻结行反推当前选中项。
- [snapshot-response-probe.mjs](evidence/C3/snapshot-response-probe.mjs)调用生产
  `Agent.fill`与`Agent.command`,只替换DOM快照/定位器为离线夹具,无浏览器/网络。
  同一冻结值`frozen-snapshot`,分别提供当前选中值`current-snapshot-A`和
  `current-snapshot-B`,两次应答均为:

```json
{"ok":false,"error":"QB_FORM_VALUE_UNAVAILABLE","field":"SNAPSHOT_NUM"}
```

两次均form_state=invalid、released=false。原始输出:
[snapshot-response-probe.json](evidence/C3/snapshot-response-probe.json)。
同两应答经生产`decode_response`所得异常属性也完全相同,diagnostic=null:
[snapshot-driver-probe.json](evidence/C3/snapshot-driver-probe.json)。
探针exit=0表示成功复现信息缺失,**不是C3验收通过**。

**为什么停止**:现有协议下CLI无法区分两个不同当前值,因而无法如实满足stdout
契约。不能编造当前值、用父构建历史值代替,也不能重开表单/改用@freeze再fill
来绕过首次失败。只加Python字段而代理不提供原始事实同样无效。

**候选处理(未实施,请设计方明确)**:

1. 在SNAPSHOT_NUM不可用的错误应答中携带同一可信表单快照的选中项文字和选项数,
   经脱敏后由Python保留至QbBrowserError;CLI用冻结值与此值输出固定提示,
   错误码/表单作废/零提交/零DB写入不变。需明确字段名、无选中项或多个选中项时
   的表示方式,以及该错误是否携带诊断。首选这一条,不增加请求或额外设值。
2. 或明确扩展被动诊断的错误范围,由同一可信快照产出足以取得当前快照的结构字段,
   Python从该字段取值;不得依赖未登记的原始页面或额外请求。

没有自行选定应答形状,没有修改冻结稿/生产代理/驱动。qb-trigger主体、幂等表逐格、
事务/崩溃窗口、隔离传输变异、多unit和诊断集成测试均**NOT_IMPLEMENTED**,
不宣称C3完成,不进入C4。C5/C6挂账仍按§27.2保持开放。

### 29.4 验收

本轮仅验收两项遗留修复与零网络停点探针;全仓回归不代表C3主体交付。
完整命令和原始日志:[evidence/C3/README.md](evidence/C3/README.md)。

| 项目 | 结果 | exit / C3证据文件 |
|---|---|---|
| 全量pytest | 2282 passed / 0 failed / 1 skipped,256.98s;相对332878d的2277/1新增5通过 | 0 / pytest.log |
| 配置与Python脱敏定向 | 154 passed / 0 failed / 0 skipped | 0 / focused.log |
| Node单元 | 152 passed / 0 failed / 0 skipped | 0 / node-unit.log |
| Node DOM(含共用21向量) | 64 passed / 0 failed / 0 skipped;含新增重复表头向量 | 0 / node-dom-safety.log |
| 四组拦截安全 | 从头重跑4/4;仅本机HTTPS假服务器 | 0 / node-dom-safety.log |
| mypy | 113 source files,无问题 | 0 / mypy.log |
| Ruff完整待提交代码树 | All checks passed,树511932966057615ffab3ffb7a85202d0cacbb258 | 0 / ruff.log |
| lint-imports | 6 kept / 0 broken | 0 / lint-imports.log |
| design.md检查器 | 0 problem | 0 / design-check.log |
| 冻结hash/未改代理与驱动 | 哈希符合,生产代理/驱动与冻结稿零diff | 0 / frozen-hashes.log |

本轮未触碰放行规则,四组安全仍额外从头跑并保留逐组服务器实收结果。
Worker走b:browser_fail_closed,attackHTTP=0、WS握手=0,浏览器和临时目录清理成功。
DOM/安全两个pytest入口计2 passed,不与Node内部64+4重复计数。
第9.1节触发前置与幂等/填表与提交的CLI用例及§4.2每格映射未实现(0条),
参数冻结与配置沿用既有全量用例加本次4个配置函数用例;
凭据与脱敏新增1个共用向量。不得把既有通过数记为C3全部用例完成。
提交只包含两项遗留修复、测试、状态与停点证据,不进入C4。

## 30. 实施裁定 P5Q-C3-02:快照不可用应答携带当前选中项

### 30.1 裁定原文

1. 代理应答:fill 在 SNAPSHOT_NUM 字段返回 QB_FORM_VALUE_UNAVAILABLE 时(包括冻结值不在选项中、@freeze 时无选中项、多个选中项或下拉框为空),应答增加 snapshot_state 对象,键集合恰好为两个:
   - selected:取自该字段开始时那一次隔离环境表单快照,为全部选中项文字(在 Node 中去掉首尾空白)组成的列表,可以是 0 项、1 项或多项。任一项长度超过 200,或不完全匹配 ^[A-Za-z0-9._:+-]+$,则 selected 整体置为 null,不返回原文。
   - option_count:该下拉框的选项数,为整数。
   不增加任何请求,不额外设值,不重开表单;该错误不产生诊断;表单照常作废,released=false。其它错误应答不带 snapshot_state。
2. Python 驱动:decode_response 校验 snapshot_state 的形状:键集合恰为 selected 和 option_count;selected 为 null 或由字符串组成的列表,且每项都符合上面的长度与字符限制;option_count 为非负整数。不符合即按协议错误处理,报 QB_BROWSER_UNAVAILABLE。校验通过后,把它保存在 QbBrowserError.snapshot_state 上。
3. CLI 输出:qb-trigger 在 stdout 中每个 unit 的对象新增 message 键,值为字符串或 null,只填固定模板文字:
   - 冻结值不可用且 selected 恰好 1 项:"参考快照已从 <冻结值> 变为 <当前值>,需在新 campaign 中处理";
   - selected 为 0 项:"参考快照冻结值 <冻结值> 已不在下拉框中,当前无选中项,需在新 campaign 中处理";
   - selected 为多项:"参考快照冻结值 <冻结值> 已不在下拉框中,当前选中多项:<逐项以逗号分隔>,需在新 campaign 中处理";
   - selected 为 null:"参考快照冻结值 <冻结值> 已不在下拉框中,当前选中项形态不在登记范围,需在新 campaign 中处理";
   - 首次冻结(@freeze)失败时,把模板中的"冻结值 <冻结值>"改为"尚无冻结值",其余同上;
   - 冻结稿第 4.3 节第 10 步 landed: unknown 的提示文字同样放在 message 中;
   - 其它情况为 null。
   同一段文字写入 trace。错误码 REJECTED_QB_SNAPSHOT_UNAVAILABLE、skip_reason=qb_snapshot_unavailable、零提交、零数据库写入都不变。
4. 理由:冻结稿第 0.5 节和第 4.3 节第 5 步要求输出两值,但第 3.5 节应答格式没有给当前值留字段,属设计前后不一致;最小改法是只在应答里增加字段,不改放行规则。
5. 下次修订设计时并入正文。

### 30.2 实施计划与边界

基线16b9148;权威v1.5 hash仍为
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`,不改冻结稿。
先落快照错误应答、驱动校验、探针与测试,再实现qb-trigger与第9.1节集成用例。
Policy/installGuards不得改;不访问真实QuickBuild/Gerrit,不弹登录窗;
ls-remote仅本地裸仓库,无构建/无Accept,完成后不进入C4。
原§29探针历史输出保留,新的期望与结果单列C3/implementation证据。
当前状态:C3_STOPPED,见§30.3。C5/C6挂账不受本轮影响。

### 30.3 停止报告 P5Q-C3-03:首次冻结失败且恰有一个选中项的提示模板

状态:**已由 P5Q-C3-04 裁定关闭**。没有修改冻结稿,没有触碰Policy/installGuards。

**原文位置**:本节30.1第3条的单项模板为
“参考快照已从 <冻结值> 变为 <当前值>,需在新 campaign 中处理”;随后首次冻结
条款要求把模板中的“冻结值 <冻结值>”替换成“尚无冻结值”。前一模板没有该
待替换片段,首次冻结也没有实际冻结值。0项/多项/null的三种模板不存在此问题。

**实测可达,不是仅作措辞推测**:生产fill在@freeze时先取得唯一选中项,随后仍
按选项文字查找且要求恰好一个匹配。给下拉框两个同名选项(不同value)、仅第一个
selected=true,就会走QB_FORM_VALUE_UNAVAILABLE,而snapshot_state.selected恰好1项。
这不是“多个选中项”,不能输出该模板;不能把字面@freeze冒充旧的实际快照。

最小输入:SNAPSHOT_NUM=@freeze;options=[
{text:current-snapshot-A,value:current-snapshot-A,selected:true},
{text:current-snapshot-A,value:other,selected:false}]。

生产Agent.command/fill的原始应答:

```json
{"ok":false,"error":"QB_FORM_VALUE_UNAVAILABLE","field":"SNAPSHOT_NUM","snapshot_state":{"selected":["current-snapshot-A"],"option_count":2},"released":false}
```

form_state=invalid,网络0/提交0;用current-snapshot-B重复同样成立。
证据:[first-freeze-single-selected.json](evidence/C3/implementation/first-freeze-single-selected.json);
复现:`snapshot-response-probe.mjs --duplicate-first-freeze`。探针只替换DOM输入/定位器,
调用生产fill/command,不修改生产判定;Node单元也固化同输入。

**候选处理,均未擅自实施**:

1. 建议补一个首次@freeze失败且selected恰为1项的固定模板,例如
   “参考快照尚无冻结值,当前选中项为 <当前值>,需在新 campaign 中处理”。
   仅补输出文字,保持错误码、skip_reason、表单作废、零提交/零数据库写入不变。
2. 或由设计方明确把重复选项文字改归QB_FORM_CHANGED。此项会改变错误分类,
   超出本轮只补应答字段的授权,不能自行采用。

CLI集成代码尚未验收,已从活动生产/测试树撤下,只保存
[implementation-wip.patch](evidence/C3/implementation/implementation-wip.patch)作为定位参考。
不得直接套用当交付;其中首次冻结单项提示分支未满足裁定,测试矩阵也未完成。
§4锁/幂等表/事务/远端隔离/诊断CLI/崩溃窗口本轮均**未交付**,
不宣称第9.1节三组或幂等表12格已验收,不进入C4。

### 30.4 本轮已闭合范围

- 代理:仅fill开始处取当前字段快照的selected与option_count,长度/字符校验后
  随SNAPSHOT_NUM不可用应答返回;表单仍作废,released=false,不生成diagnostic。
- Python:exact-key/type/字符/长度校验,非法协议QB_BROWSER_UNAVAILABLE;
  合法事实保留到QbBrowserError.snapshot_state。非对应错误不得携带该对象。
- 原§29的两个探针已按新应答期望重跑,不同当前值现在可区分,见
  [snapshot-response.json](evidence/C3/implementation/snapshot-response.json)与
  [driver-response.json](evidence/C3/implementation/driver-response.json)。
  §29旧json原样保留;旧脚本原文可由16b9148取得,新脚本对应本轮裁定。
- Node新增7例(含新停点输入);Python新增17例。CLI message没有交付,
  不把协议字段可用等同于CLI要求完成。

### 30.5 验收

日志与命令见[evidence/C3/implementation/README.md](evidence/C3/implementation/README.md)。
本轮仅验收协议补齐与停点取证;全仓绿不表示C3主体完成。

| 项目 | 实测结果 | exit / 证据文件 |
|---|---|---|
| 全量pytest | 2299 passed / 0 failed / 1 skipped,258.23s;基线2282/1增加17 | 0 / pytest.log |
| Python驱动定向 | 160 passed / 0 failed / 0 skipped | 0 / driver-tests.log |
| Node单元 | 159 passed / 0 failed / 0 skipped;增加7 | 0 / node-unit.log |
| 第9.2静态护栏与负例 | 183 passed / 0 failed / 0 skipped | 0 / static-guards.log |
| 四组本机拦截安全 | 虽非强制,额外从头重跑4/4,loopback-only | 0 / safety.log |
| mypy | 113 source files,无问题 | 0 / mypy.log |
| Ruff完整待提交代码树 | All checks passed;树49d7784f43ea4522f4c4b7f3ff8c59e95520f3a4,后续仅补文档日志 | 0 / ruff.log |
| lint-imports | 6 kept / 0 broken | 0 / lint-imports.log |
| design.md检查器 | 0 problem | 0 / design-check.log |
| Policy/installGuards逐字比较 | 与16b9148相同,不触发放行规则变更 | 0 / guard-identity.log |
| v1.5哈希 | f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c | 0 / frozen-hashes.log |

Safety日志中的quickbuild.tizen.org由测试host-resolver映射到本机HTTPS假服务器,
合成登录由测试脚本操作,不是真实QuickBuild登录。四组summary=4/4;
Worker fail-closed与原规则一致,attackHTTP=0、websocketHandshakes=0,临时目录清理成功。
`implementation-wip.patch`中unified diff的空白上下文行按补丁格式保留,
不把它当生产代码或已通过的C3测试矩阵。第9.1三组CLI用例数与幂等12格交付数仍为0。
停止报告新增1条(P5Q-C3-03),本轮不进入C4。

## 31. 实施裁定 P5Q-C3-04:同名下拉选项归为结构变化,快照提示模板收敛为两个

### 31.1 裁定原文

1. 同名选项:普通下拉框(双列表的 choices 与 selection 不在此列)中,选项显示文字在 Node 中去掉首尾空白后若有重复,即视为表单结构与已取证结构不符。检查放在 open_form 与 fill 每一次表单快照的结构校验里(validateForm 或同等位置),覆盖全部普通下拉框,不只 SNAPSHOT_NUM。代理应答 QB_FORM_CHANGED,按冻结稿第 3.2 节先取证再报错,CLI 侧为 REJECTED_QB_FORM_CHANGED;该应答不带 snapshot_state;零提交,零数据库写入。诊断结构事实的 first_failed_check 记为 duplicate_option_text。
2. 提示模板:P5Q-C3-02 第 3 条里关于快照的五种模板全部作废,改为以下两个。第 4.3 节第 10 步 landed: unknown 的提示仍放在 message 中,不受影响。
   a. 已有冻结值,且 snapshot_state.selected 恰好 1 项:"参考快照已从 <冻结值> 变为 <当前值>,需在新 campaign 中处理"。
   b. 其它所有 SNAPSHOT_NUM 不可用的情况,一律使用:"参考快照不可用:冻结值 <V>,当前选中项 <S>,共 <N> 个选项;<后续>"。槽位规则:
      - V:有冻结值时为冻结值原文,首次冻结时为"尚无";
      - S:selected 为 1 项时为该项原文,0 项时为"无",多项时为各项以逗号分隔,null 时为"形态不在登记范围";
      - N:option_count;
      - 后续:有冻结值时为"需在新 campaign 中处理",首次冻结时为"请人工核对 SNAPSHOT_NUM 下拉框后重跑"。
   同一段文字写入 trace。错误码 REJECTED_QB_SNAPSHOT_UNAVAILABLE、skip_reason=qb_snapshot_unavailable、表单作废、零提交、零数据库写入均不变。
3. 理由:工具按选项显示文字选值,文字重复时选值目标有歧义,而已取证的表单中选项文字都不重复;把它报成"快照不可用"会误导处置。另外,逐种列举的模板存在组合遗漏,改为一个特定模板加一个带槽位的通用模板,覆盖全部情况。
4. 下次修订设计时并入正文。

### 31.2 实施计划

基线7f3c60e;已重读§29、§30。冻结v1.5哈希仍为
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`。
状态C3_IN_PROGRESS。先实现同名选项结构校验与探针,再按第2.2、4节重新核对
CLI选择/锁/幂等/事务/隔离传输/诊断,完成第9.1相关组与9.5门禁。
旧implementation-wip.patch仅参考,逐块重新核对后实现;不修改Policy/installGuards。
无真实QuickBuild/Gerrit连接、无登录窗、无推送构建、无Accept操作;测试远端仅本地裸库。
每个提交同步本文件;完成C3即停,不进入C4,C5/C6挂账保持开放。

### 31.3 已实现的逐项落点

- 同名选项:validateForm每次校验普通SELECT,Node trim后文字重复即
  QB_FORM_CHANGED;formFacts记录duplicate_option_text。双列表不在此列。
  open_form与fill共用校验,诊断仍走既有惰性文档与脱敏路径,不带snapshot_state。
  Policy/installGuards与7f3c60e逐字一致,见completion/audit.json。
- 两个模板:qb_trigger.snapshot_message以数据库是否已有冻结行区分首次冻结,
  不以配置是否写了具体快照判断。10个组合和“具体配置但无冻结行”独立验证;
  stdout与trace文字一致,其它unit的终态事件与结果文件保持逐字不变。
- CLI:qb-trigger两种选择入口、每unit独立sandbox锁、按P5规则检查记录和unit
  base/project/spec/branch、最新round、配置冻结比对、一致gate快照及12格幂等。
- 流程:一个CLI一次登录;open_form/fill/读回后,在全新.transport裸库中用
  原SandboxGit环境和全部覆盖项ls-remote,不读取主副本git配置或对象。
  该只读查询无需alternates,未调用P5中用于推送且读取主副本对象的_transport。
  这是第4.3(6)隔离机制的只读接入,不另起git环境,不改P5行为。
- 意图:一个BEGIN IMMEDIATE事务重查状态/最新request/PUSH事件与冻结行,
  四个既有原语负责profile/request+SUBMITTED/状态。期间无浏览器调用。
  不初始化schema。提交之后只有显式released=false才写QB_SUBMIT_FAILED;
  unknown不补事件;build落点只读父variables核对标记与唯一目标行再绑定。
  意图已提交后即处于不确定态,异常出口不伪称确定未放行;异常出口不写库。
- 诊断:UTC时间戳-unit_hash目录;HTML与结构JSON逐字符串写前/写后检查,
  失败删除目录,原结构错误码保留。原始页面与身份信息不写trace。
- 原WIP未直接套用:重新按冻结稿核对选择顺序/绑定、事务、消息模板、错误状态;
  新测试重新构造真实DB与本地裸库。历史补丁和历史探针json原样保留。

用例、幂等表12格与完整命令索引:
[completion/README.md](evidence/C3/completion/README.md)。
本轮新增139个pytest CLI用例;机械分组为触发前置38、填表提交70、参数冻结27、
凭据脱敏4,诊断重叠不重复计数。既有C1配置/原语/驱动/脱敏一并定向488/488。
Node新增4净单元用例(移除已失效的重复选项快照不可用旧例),另新增4个真实
本机浏览器诊断用例。Node内部数字不累加到pytest总数。

### 31.4 验收记录

最终全量pytest为2438 passed / 0 failed / 1 skipped,279.06s,exit0;
相对7f3c60e的2299/1新增139个用例,原集合不缩小。
唯一skip仍为test_case_insensitive_bypass_is_platform_specific。
定向488/488、Node单元163/163、静态护栏及负例183/183、
真实字段DOM16/16全部exit0,均无失败或跳过。隔离传输八个覆盖项逐个在独立进程移除,
八次均pytest exit1,runner exit0;原文transport-mutation-1.log至-8.log。
四组安全虽非放行规则改动的必检,仍额外从头复跑4/4,仅loopback;
Worker走b:browser_fail_closed,attackHTTP=0、WS握手0、临时目录已清理。
mypy(114 source files)、完整待提交代码树Ruff、lint-imports(6 kept / 0 broken)、
design.md检查器(0 problem)全部exit0。Ruff树与导出路径见ruff.log;
随后仅补文档和实测日志。冻结稿哈希未变,Policy/installGuards/驱动/design.md
与基线逐字比较通过,见audit.json。重复选项探针与原两个当前值探针均exit0。
全部证据位于[evidence/C3/completion](evidence/C3/completion/README.md)。

开发中测试夹具曾触发round identity/UNIQUE/composite-FK约束,修正夹具的
round/hash与绑定后重跑;不改生产约束、不关闭foreign_keys。原文保留
fixture-setup-failures.log。Ruff长断言拆行,不改变期望。
没有发现新的设计或裁定不一致,没有新增停止报告。
状态C3_COMPLETE;未访问真实QuickBuild/Gerrit,未弹人工登录窗口,不进入C4。
C5/C6原始字节/活动文档比较、成功样本、BUILD_NOTES样本挂账仍开放,
P5Q不标CLOSED。只纳入本轮文件,既有无关修改、删除与草稿未处理。

## 32. C4 开工与停止报告 P5Q-C4-01:源格式查询与主副本 argv 禁令

### 32.1 上下文与计划

基线为3ef542a985712c340c333addedde092d818cc8b7,分支clang-fix-campaign。
已读取本文件与冻结稿第1、3、5、6、9节。v1.5冻结稿sha256仍为
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`,未修改。
P5Q-C2C-03、P5Q-C3-02、P5Q-C3-04继续有效,C5/C6挂账未关闭。

本轮计划依次为:修复C3传输仓库对象格式;实现C4入口/锁/绑定、父子页面核对、
快照漂移、辅助step_status、证据与原子结果发布;离线假代理矩阵与第9.5门禁。
在第一项规格核对即发现下述冲突,未将候选方案写入生产代码。

### 32.2 P5Q-C4-01(已由 P5Q-C4-02 裁定关闭)

**原文位置与冲突**:

- 本轮任务第一步要求以P5相同方式,按源仓库`rev-parse --show-object-format`
  选择sha1/sha256,修正C3的`.transport`格式。
- 冻结稿第4.3(6),L437:远端核对不得以主副本为`-C`/`--git-dir`。
  第9.1节隔离传输验收,L692进一步写成“没有任何 git 命令以主副本为
  `-C`/`--git-dir`”,并非仅限`ls-remote`。
- P5 `sandbox_submit.py:681`把primary_arch对应的验证worktree作为派生主副本;
  `:833/:834`的`_transport`取该worktree并调用
  `s.git.run(source, "rev-parse", "--show-object-format")`。
  `_sandbox_git.py:52`把非空cwd编码为`git -C <source>`。
  因此照搬这一格式查询会违反当前冻结验收的全称禁令。

**离线实测**:

- 直接调用现有P5 `_transport`,分别用临时sha1/sha256源仓库;
  两种传输仓库格式均与源相同,退出后临时传输目录清理成功。
- 两种情况均实际执行`git -C <primary-worktree> ... rev-parse --show-object-format`;
  单独将该命令交给第9.1节全称禁令检查,均红。没有复制P5实现或修改生产函数。
- 原C3隔离用例不改动实跑:1 passed,exit0。新规格探针:2 failed,exit1,
  两处失败都在最后的冻结禁令断言,不是格式选择失败。
- 探针没有`ls-remote`、push或浏览器调用,只操作临时本地仓库。

原始argv、失败原文与复现命令:
[format-preflight/README.md](evidence/C4/format-preflight/README.md)。

**候选处理(未实施,需设计方裁定)**:

1. 建议允许一条具名例外:仅为选择传输格式,允许用既有SandboxGit及全部
   环境/覆盖项在P5同一源主副本上执行只读`rev-parse --show-object-format`。
   白名单只含这一条元数据查询;网络核对仍全部在`.transport`,不得读取源仓库
   remote/url配置来确定远端。第9.1断言相应分开“源元数据精确一条”和
   “其余命令不得以主副本为上下文”,八条环境覆盖的变异证伪保持。
   新增sha256源/传输相等、sha1不传object-format、未知格式/格式不等拒绝用例。
2. 若保持绝对禁令,需设计方另行指定不运行源仓库git命令的权威格式来源及校验
   方式;本轮不猜测、不按sha长度推导、不借换cwd/路径拼写绕过断言。

### 32.3 交付边界与验收

状态C4_STOPPED。C3遗留未标为“已于C4修复”;qb-result-fetch未实现,
第5.3负例矩阵和C4第9.1各组交付数为0。没有修改生产代码、已有测试、
Policy、installGuards、冻结稿或design.md。本次只提交停止报告、离线探针与证据。
完整C4 pytest/mypy/Node/lint-imports门禁未执行,不沿用C3数字当作本轮验收。
证据脚本Ruff、设计检查器结果见证据索引。未访问真实QuickBuild/Gerrit,
未弹登录窗口,没有Accept操作;不进入C5。无关既有改动与草稿保持原样。

## 33. 实施裁定 P5Q-C4-02:撤回传输仓库格式对齐

### 33.1 裁定原文

1. 撤回上一轮任务第一步"qb-trigger 传输仓库按源仓库对象格式选择"的要求。qb_trigger.py 的 _remote_check 保持 C3 的写法:用默认格式新建一次性 bare 传输仓库,只做 ls-remote,用后删除。冻结稿第 9.1 节"没有任何 git 命令以主副本为 -C/--git-dir"的全称禁令不变,不增加任何例外。
2. 理由:P5 对齐格式,是因为它要借源仓库的对象做推送;qb-trigger 的传输仓库只做 ls-remote,不需要对象,与源仓库格式无关。为一个用不到的对齐,在隔离禁令上开例外,得不偿失。
3. 已接受残余:远端仓库若为 sha256,ls-remote 可能报错或得不到匹配,结果一律为 REJECTED_SANDBOX_NOT_BOUND,不会误判绑定。Tizen Gerrit 为 sha1。
4. 补一例坐实残余:远端为 sha256 本地裸仓库时,qb-trigger 的结果只能是"sha 相符则通过",或 REJECTED_SANDBOX_NOT_BOUND,不得出现其它结果;并记录实测走的是哪一种。该用例中的全部 git argv 仍须满足第 9.1 节的全称禁令。
5. 第 32 节的规格探针按本裁定改为期望"不查询源仓库格式",或标注为已作废,二选一并在 progress.md 说明。

### 33.2 执行计划与边界

基线ec3be74;已读§32,冻结稿哈希核对一致,仍为
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`。
选择把§32旧探针标为已作废,保留原始脚本/日志作为历史停点证据,不再作为验收。
_remote_check不改;先补残余实测,再实现第5节入口/锁、父子页面核对、
快照与辅助页分类、证据/结果原子发布和事务重查,按第9.1/9.5节验收。
不改Policy/installGuards,不访问真实QuickBuild/Gerrit,不弹窗,不进入C5。
C2C-03/C3-02/C3-04仍有效;C5/C6挂账保持开放。无关工作区改动不处理。

### 33.3 C4 实现与局部接口接线

- qb_trigger._remote_check保持原字节,不查源格式、不取源对象。新增本地sha256
  裸库用例,本机实测SHA_MATCHED;全部git argv只以.transport为仓库上下文,
  无主副本-C/--git-dir,无object-format查询,无push,结束清理传输目录。
- qb-result-fetch入口新增三种单项引用与批量引用;漂移开关限单request。
  先只读定位unit锁,随后入口校验至最后落库均持.sandbox_submit.lock;
  同次调用一个代理/一次登录,每项独立返回;网络不占数据库事务。
- qb_result_html只解析代理返回的脱敏HTML,stdlib HTMLParser构造节点树;
  live-12的01-05作为离线模板。配置URL只用请求地址,忽略base元素。
  父overview与variables都读取并核对后才能绑定/决定pending。
  子目标行、配置、FAIL_FAST、三架构、快照均按冻结规则;不推断服务端行为。
- 手工绑定、非终态、RESULT使用既有按连接原语,各自一个BEGIN IMMEDIATE;
  事务内重查request/绑定/目标,状态按6.3迁移。结果文件先fsync/rename/
  fsync父目录后写库;重查或写库失败删除本轮文件。终态三分支保留旧事件/文件。
- step_status只在FAIL/CANCELLED/TIMEOUT读取。driver在既有映射码之外保留
  agent_code,使ID不符/重定向可降为null,可信环境失效/代理异常不可吞掉。
  driver原映射与submit语义不变。结构错误诊断照常自检归档。
- Agent.read只把已有outside_identity_count随成功应答返回;不增加读取/请求,
  不碰Policy/installGuards。Python校验非负整数后写trace;业务HTML仍写前/写后
  自检。代理内身份计数算法、qb_redact不改。
- 第5.3要求的漂移/未取证格式处置指引放stdout每项message并同文写trace,
  其它情况为null。此接线沿用C3消息承载方式,不改错误码或准入判据。

逐项实现、§5.3全部负例及§9.1分组见
[completion/README.md](evidence/C4/completion/README.md),精确nodeid/源码行由
audit_completion.py从实跑JUnit与AST生成,不手填枚举数字。
开发中修正两处夹具设置:profile参数使用既有frozen_snapshot;状态序号使用
log_id。绑定重查负例改为带外SQL损坏,因为公共API本来就拒绝改绑;不改公共约束。

### 33.4 最终验收与交付边界

证据目录`evidence/C4/completion/`。每条命令、退出码与耗时写入commands-*.json;
pytest/focused/Node的完整逐用例日志与JUnit均入档。audit.json机械统计:

| 验收 | 实测 | 原始证据 |
|---|---|---|
| 全量pytest | 2632 passed / 0 failed / 1 skipped,331.87s,exit0 | pytest.log / pytest.xml |
| 原集合不缩小 | 2439→2633 nodeid,removed=[],新增194 | audit.json collection |
| C4读取与落库 | 155 passed / 0 failed / 0 skipped | focused.xml / audit.json |
| C4事务与原语 | 15 passed / 0 failed / 0 skipped | focused.xml / audit.json |
| C4凭据与脱敏 | 14 passed / 0 failed / 0 skipped | focused.xml / audit.json |
| Python驱动 | 169 passed(含新增9),无失败/跳过 | focused.xml |
| sha256远端残余 | 1 passed,SHA_MATCHED,无源格式查询 | focused.log末尾git_argv |
| 定向合计 | 354 passed / 0 failed / 0 skipped,exit0 | focused.log |
| Node入口 | 13 passed / 0 failed / 0 skipped,exit0 | node-gates.log / node-gates.xml |
| Node内部 | 单元163、静态护栏及变异183、可信读取37、字段DOM16、runtime64、配置来源67,全部通过 | node-gates.log |
| 四组安全 | 从头复跑4/4,loopback-only | node-gates.log:616 |
| mypy | exit0,116 source files | mypy.log |
| Ruff完整待提交树 | exit0,All checks passed | ruff.log(含tree及导出路径) |
| lint-imports | exit0,6 kept / 0 broken | lint-imports.log |
| design.md检查器 | exit0,0 problem | design-check.log |
| 机械边界检查 | exit0,冻结稿/design/trigger/redact/state/Policy/installGuards逐字不变 | audit.json |

唯一skip仍为test_case_insensitive_bypass_is_platform_specific。新增194=fetch184+
driver9+sha256残余1,Node内部断言不重复加入pytest计数。
四组中的Worker实际走b:browser_fail_closed,攻击HTTP0/WS握手0,临时目录清理;
不是访问真实QuickBuild。常规网络读取全为假代理,ls-remote只到本地裸库。

最后自查补齐诊断I/O与脱敏失败的区别:前者保留原读取错误,后者删除诊断并报
QB_EVIDENCE_REDACTION_FAILED;必读/辅助页各一正反,4/4。初版全量2628/1日志
另存pytest-initial.log,最终以2632/1为准,不是用初版代替最终验收。
_remote_check及P2-P5生产模块、schema/API无改动;冻结稿哈希仍为§33.2钉值。
无新的规范矛盾或做不到事项,停止报告新增0。不进入C5,不把C4完成写成P5Q CLOSED。
原始字节/活动文档比对、成功样本、BUILD_NOTES样本与真实提交继续由C5/C6履行。
仅纳入本轮实现/测试/证据与进度,未处理用户既有.gitignore改动、文档删除及草稿。

## 34. C5a:本机浏览器集成与第1.6步工具准备

### 34.1 范围与计划

基线39e4bde;已核对§33的C4完成记录与开放挂账。v1.5冻结稿SHA256仍为
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`。
C2C-03、C3-02、C3-04、C4-02继续有效。先列第9.3节逐项覆盖,再补真实CLI/
真实代理/本地HTTPS服务器链路,然后准备原始正文与活动文档比对、完整填表演练
两项工具并离线验证。最后跑第9.5门禁及四组拦截安全测试。

只访问测试入口映射的loopback HTTPS与本地git裸库,不访问真实QB/Gerrit,
不弹真实登录窗口,不点击Accept/Ready to Accept。不改Policy/installGuards/
冻结稿;如需改动,按停止报告协议记录事实与候选处理。每个提交同步本节。
C5a不关闭第9.4节真机义务,不进入C5b/C6。用户既有改动与草稿不处理。

覆盖清单与缺口见[evidence/C5a/coverage.md](evidence/C5a/coverage.md);
清单中未跑项目不借历史结果冒充本轮通过。

### 34.2 本机集成与取证工具

- 新增tests/node/p5q_fake_quickbuild.mjs,从live-12的结构蓝本重新构造响应,
  不把归档活动HTML当响应体。保留坏trim、random回调、版本递增、记住Variables、
  dashboard、刷新脚本。已有假登录服务器复跑失败后wicket重提交/五次上限。
  测试证书在临时目录生成,以SPKI精确信任,DNS映射只从tests入口传入。
  假服务器监听loopback;其它域名映射NOTFOUND;实际收取请求逐条归档。
- 新增真实Python CLI链路,真实Agent通过测试node入口启动,测试入口模拟人工登录,
  生产login不点击/输入。build模式提交一次并绑定,再Running/PENDING、Successful/
  PASS,检查状态、RESULT及fsync发布的结果文件。另测error-created、error-no-build、
  no-navigation三种unknown,再次调用CLI零新增提交。git只用本地裸库,没有push。
- spikes/p5q_compare_raw_active.mjs复用生产Agent/installGuards,同一次导航捕获
  正文字节并严格解码,隔离环境序列化活动文档;两者分别惰性脱敏后落盘。
  包含变量表thead td及br换行,所有要求字段逐项比较;登记位置外身份计数分列。
  首个差异页留证后停止,不回退生产read。路径参数先按只读集合验证。
- spikes/p5q_fill_rehearsal.mjs只login/open_form/fill/close,独立rehearsal request_id,
  无DB、无提交命令、无Ok点击、无submitUrl写入。通过只读包装生产快照和已适配
  协议元数据,记录12字段窗口、随机值、HTTP状态、版本、已相等值、读回与指纹。
  实际action获准次数与policy.released双断言为0/false。配置页与各表单快照的
  登记位置外身份计数也记录。无生产trace扩展,无Policy/installGuards改动。
- 共用p5q_c5_tools.mjs负责惰性字段提取、元数据观察与双端写前/写后检查;
  两份同名.md运行说明列完整C5b命令,仅目标构建号/目标行留待FatTank指定。
  本轮没有执行说明中的真机命令,没有弹真实登录窗口。

### 34.3 测试补齐与开发记录

第9.3节16项逐条映射见[evidence/C5a/coverage.md](evidence/C5a/coverage.md)。
已有trusted/fields、安全四组、h三模式、login retry、源码护栏全部原义复跑;
仅在既有trusted/fields测试追加服务器实收导出,未删减断言。
新增pytest参数用例4个(完整CLI的四模式)、Node工具入口1个、工具静态护栏1个。
工具Node矩阵12项(含外层):三种比对、十二字段演练、四种登录真假阳性、
重定向读取错误映射、window.open/外站iframe、DOM与实际回调不一致。

开发期focused-01为18 passed/1 failed:新增工具测试对合成父变量表误写>=10行
(实际9行),以及调用decode_response漏传既有必需参数submit_sent=False。
两者均修正测试自身,不改生产API或放行规则;不把该轮计作验收通过。
其余合成夹具纠正包括QB_TRIGGER_ID、FAIL_FAST显示名、快照URL不带尾斜杠、
unknown退出码5/再次幂等退出码0、测试入口stdin清理,均以既有设计/实现为准。
第一轮全量full-01实测2638 passed/1 skipped,0 failed;随后补齐演练每页身份计数,
最终以full-02全量重新执行结果为准,不拿旧轮绿灯代替新代码验收。

### 34.4 开放边界

C5a仅准备并离线验证工具。第9.4节1.6a原始字节/活动文档真机比对、1.6c真机
完整演练仍须C5b完成,两者都先于任何真实提交。成功样本与BUILD_NOTES非空样本
仍具名挂账,允许按冻结稿由C6补齐;挂账未关闭不得P5Q CLOSED。
本轮不修改冻结稿、design.md、生产代码或P2-P5;不执行Accept/Ready to Accept,
不访问真实QB/Gerrit。没有新的规格不一致或做不到事项,停止报告新增0。

### 34.5 最终验收与提交边界

证据总索引:[evidence/C5a/README.md](evidence/C5a/README.md)。所有命令与exit
记录在对应目录commands.json;集合、请求数与不可变边界由audit.py实跑生成。

| 项目 | 最终实测 | 证据(相对evidence/C5a) |
|---|---|---|
| 全仓pytest | 2638 passed / 0 failed / 1 skipped,496.40s,exit0 | full-02/pytest.log、pytest.xml |
| 集合对账 | 2633→2639,新增6、removed=[] | audit.json |
| 真实CLI四模式 | 4 passed,无失败/跳过;一次提交,错误落点不重提 | full-02/artifacts/{build,error-created,error-no-build,no-navigation}/ |
| 正常链路 | 35个本地实收请求,1次运行表单提交,submitted_bound→RUNNING→PASS,RESULT与结果文件存在 | full-02/artifacts/build/commands.json、server-requests.json、state-facts.json、result.json |
| 新工具Node | 12 passed / 0 failed / 0 skipped | full-02/pytest.log,full-02/artifacts/tools/ |
| 两文档三种比较 | 六页全字段一致;插入导航仅活动文档有;改Status值不同 | full-02/artifacts/tools/{equal,insert-nav,change-status}/ |
| 填表演练 | 12字段各1次获准POST、HTTP200、12版本,not_released,action放行0,16次身份计数均0 | full-02/artifacts/tools/rehearsal/run.json |
| 既有Node | 单元163/静态183/可信读取37/字段DOM16/runtime64/配置来源67,全部通过 | full-02/pytest.log |
| 安全四组 | 从头复跑4/4,攻击HTTP0/WS0;Worker分支b且浏览器/profile已清理 | safety.json |
| 其它浏览器组 | h三模式3/3,登录重试2/2,正常/异常/SIGTERM清理3/3 | full-02/pytest.log |
| mypy | exit0,116 source files | tools-02/mypy.log |
| Ruff完整待提交树 | exit0,All checks passed | ruff-02/ruff.log |
| lint-imports | exit0,6 kept / 0 broken | tools-02/lint-imports.log |
| design.md检查器 | exit0,0 problem | tools-02/design-check.log |
| 机械边界检查 | exit0,冻结hash匹配、生产/design零diff | audit.json |

唯一skip仍为大小写不敏感文件系统平台用例,不是Node/浏览器跳过。
源码/文档diff-check通过;开发失败原始日志/JUnit保留pytest输出的尾部空白,
不为消除空白提示而改写证据。所有新增内容限tests、spikes、stage证据/进度及INDEX。
用户既有.gitignore改动、四个文档删除及未跟踪草稿未纳入提交。
C5a COMPLETE,不进入C5b,不把本轮离线通过记作P5Q CLOSED。

## 35. C5b 真机执行

### 35.1 第零步参数与授权

日期2026-10-15(Asia/Shanghai);基线b134d16,分支clang-fix-campaign。
已读本文件并核对C5a完成、C5b/C6挂账与已登记实施裁定。v1.5冻结稿SHA256:
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`,匹配且不修改。

FatTank给出llvm参数表,工具说明Snapshot Number不等于本批要求的Ref. Snapshot
成功父样本,随后在聊天列明以下登记值;FatTank回复“开始吧”确认并授权启动:

```text
目标行：platform/upstream/llvm@67619ec8bbbac7238a6cfc33a481ccfbcd12206f
Ref. Snapshot 成功父子样本：暂无
BUILD NOTES 非空样本：暂无
```

目标行已机械核验完整匹配`^[^\s@]+@[0-9a-f]{40}$`。此前两张参数表中的Live与
Snapshot Number不当作Ref. Snapshot证据,不照抄其快照值到演练。成功样本和
BUILD_NOTES样本继续挂账。本轮两个工具、共用helper与生产目录对b134d16零diff。

### 35.2 执行顺序与边界

仅运行C5a已验收的比较工具,一次人工浏览器登录,固定六页按任务顺序读取,
输出evidence/C5b/raw-active-01;输出目录开工时不存在,不得覆盖旧证据。
所有字段一致且登记位置外身份计数处理完后,才允许另一次登录进行填表演练。
任何失败/差异立即停止,保留脱敏证据,不重试、不换路径继续。

不发送submit、不点Ok/Accept/Ready to Accept,不运行qb-trigger/qb-result-fetch,
不写state DB、不做Gerrit推送;登录只由FatTank在浏览器内完成,不读终端输入。
不修改生产代码、冻结稿与两个工具。既有无关改动和草稿不纳入提交。

第一步预定命令(仓库根;无测试证书/DNS覆盖;600秒登录时限):

```bash
env -u QB_COOKIE -u QB_PASSWORD -u DEBUG -u PWDEBUG -u NODE_OPTIONS /home/linhao/.local/bin/node docs/clang-fix-campaign/spikes/p5q_compare_raw_active.mjs --path /build/1193467/overview --path /build/1193467/variables --path /build/1193469/overview --path /build/1193469/variables --path /build/1193469/step_status --path /overview/1917 --output docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C5b/raw-active-01
```

### 35.3 第一步实际结果

上列命令实际执行一次,exit0。终端仅有固定浏览器登录提示(生产login写stderr)。
FatTank完成一次浏览器人工登录,没有终端输入。比较工具自行结束并关闭浏览器。
19个输出文件均由工具写前/写后自检,随后再次用生产PageRedactor.check_written
离线复核19/19通过。证据在`evidence/C5b/raw-active-01/`,run.json保留完整trace。

| 页路径 | 比较文件 | 全部10类比较项 | 原始/活动身份计数 |
|---|---|---|---|
| /build/1193467/overview | 01.comparison.json | 一致 | 0 / 0 |
| /build/1193467/variables | 02.comparison.json | 一致 | 0 / 0 |
| /build/1193469/overview | 03.comparison.json | 一致 | 0 / 0 |
| /build/1193469/variables | 04.comparison.json | 一致 | 0 / 0 |
| /build/1193469/step_status | 05.comparison.json | 一致 | 0 / 0 |
| /overview/1917 | 06.comparison.json | 一致 | 0 / 0 |

六页navigation均VERIFIED。trace无WORKER_BLOCKED/NEW_PAGE,无运行失败;
DENIED共22条(仍按原规则拒绝,未增加登记),IDENTITY_OUTSIDE_REGISTERED共18条。
原始字节比对前提在本批固定六页范围通过;没有新增身份位置需要人工确认。
成功样本和BUILD_NOTES样本仍暂无,不因上述固定页通过而销账。

### 35.4 第二步实际结果与停止报告 P5Q-C5B-01

状态:已由 P5Q-C5B-02 裁定处理。历史失败证据原样保留,本轮执行见§36。

第一步通过、身份计数均0后,再次在聊天请求“开始”;FatTank回复“开始”,仅授权
本次演练登录。下列命令执行一次,没有重试,没有改用其它工具或路径:

```bash
env -u QB_COOKIE -u QB_PASSWORD -u DEBUG -u PWDEBUG -u NODE_OPTIONS /home/linhao/.local/bin/node docs/clang-fix-campaign/spikes/p5q_fill_rehearsal.mjs --target platform/upstream/llvm@67619ec8bbbac7238a6cfc33a481ccfbcd12206f --output docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C5b/fill-rehearsal-01
```

终端先出现固定登录提示,随后`EVIDENCE_STOPPED`,进程exit1。结束后首次检查
输出目录存在但为空,没有run.json、代理应答、trace、回调记录或诊断HTML。
外层工具会话4739的结束结果和命令记入[evidence/C5b/execution.json](evidence/C5b/execution.json);
`fill-rehearsal-01/STOPPED.md`是事后停止说明,不是探测工具的运行产出。

事实与证据缺口:

- `spikes/p5q_fill_rehearsal.mjs:79`登录错误直接抛出;`:33`打开表单错误也直接
  抛出;`:41`运行状态检查、`:42`记录组装及`:65`写出也可能失败。`:84`统一
  只输出EVIDENCE_STOPPED,未把阶段或固定代理错误码落盘。
- 不能据此判断本次是哪一个阶段失败,不能断言登录成功、open_form失败或
  任一具体字段失败;没有把代码中的可能分支冒充实测原因。
- 十二字段的获准/被拒次数、HTTP状态、random、读回、版本及action变化全部
  NOT_COLLECTED;release_state与form_action_releases同样NOT_COLLECTED,不补写0。
- 工具命令路径只有login/open_form/fill/close,静态护栏本轮1 passed;未发送
  submit命令,未点击Ok/Accept/Ready to Accept,未运行触发/结果CLI或写state DB。
  这是源码边界证据,不替代缺失的运行时放行计数。finally保留原关闭逻辑,
  进程已退出;结束后/dev/shm只见前一天遗留目录,未删除或处理它们。

处理:按本轮“任何失败立即停止”要求,不再访问QB,不修改工具补取,第三步
离线事实分析也未继续执行。没有将C5a假服务器演练结果当作本次真机通过。

候选处理(待设计方批准,本轮未实施):仅补取证工具的失败落盘通道,在各阶段
保存固定阶段/错误类别、已有且脱敏的代理应答/诊断/trace,在finally中写出已取得
的事实后清理;写出失败仍固定报错,不得泄露原始异常/凭据。经离线验证后另获
FatTank真机授权,使用新目录重跑。当前停点不要求也不授权放宽生产规则。

### 35.5 第三步状态、挂账与C6前置

第二步失败后停止,第三步五个问题均未执行生产解析函数:

| 问题 | 本轮结论 |
|---|---|
| 成功子构建Status原文/归一结果 | NOT_COLLECTED:未提供合格成功样本 |
| 成功子构建EACH_GBS_BUILD_STATUS | NOT_COLLECTED:未提供合格成功样本 |
| 成功父SNAPSHOT_NUM/子SNAPSHOT_NUM_URL/snapshot_kind | NOT_COLLECTED:未提供合格成功样本;不以Live/Snapshot Number表代替 |
| 非空BUILD_NOTES回显、空白/转义/换行/截断 | NOT_COLLECTED:未提供非空样本 |
| 1193469 failed_steps/Error Message | NOT_RUN_AFTER_STOP:原始/活动脱敏页已归档05与03,未执行本轮第三步解析 |

| 义务/前置 | 状态与依据 |
|---|---|
| 第1.6a原始/活动文档比对 | PASS:固定六页60项一致,身份计数均0;§35.3 |
| 成功样本 | OPEN:暂无,可按冻结稿由C6补齐,关闭前不得P5Q CLOSED |
| BUILD_NOTES非空样本 | OPEN:暂无,同上 |
| 第1.6c十二字段真机演练 | NOT_PASSED:本次exit1,字段与放行计数未取得;§35.4 |
| 本机集成门禁 | C5a已通过@b134d16;本轮未重跑,不冒充C5b结果 |
| FatTank对C6真实提交的确认 | NOT_GIVEN:本轮“开始”仅授权C5b登录/演练 |
| C6前置合取 | NOT_MET;不得进入C6 |

### 35.6 离线收尾校验与提交边界

停止后只做证据检查、文档登记及GitHub文档/证据提交推送,无新增QB请求。
命令与输出见[evidence/C5b/README.md](evidence/C5b/README.md)及validation.log:
原始19个文件PageRedactor写后自检19/19;六页60项一致断言通过;
取证工具静态护栏1 passed/0 failed/0 skipped;design.md检查器0 problem。
收尾说明的首轮全目录脱敏检查exit1:新写的execution.json与STOPPED.md用
session标签记录终端工具的进程编号,触发既有SECRET_VALUE规则,被check_written
删除。用合成非凭据值复现后,仅将这两个事后记录的标签改为process_handle;
不改脱敏规则、不改原始19个文件。最终全目录重新自检,结果见validation.log。
冻结hash仍匹配;生产目录、spikes及冻结稿对b134d16零diff。
本轮未跑全仓pytest/mypy/ruff/Node浏览器测试,不将C5a的2638 passed/1 skipped
记为本轮执行。仅提交stage20进度、INDEX与C5b脱敏证据/说明,不纳入用户既有
改动或草稿。状态C5b_STOPPED,停止报告新增1(P5Q-C5B-01),不自行关闭。
暂存区diff-check全量exit2,2150处均为12份归档HTML自身的尾空白或混合缩进;
不格式化原始证据。排除这12份HTML后同一检查exit0,字节hash保持原值。

## 36. 实施裁定 P5Q-C5B-02:取证工具补失败落盘后重跑填表演练

### 36.1 裁定原文

1. 第 1.6 步 a 的原始字节比对已在固定六页通过(60 项一致,身份计数均为 0),本轮不重跑。
2. 批准只修改两个取证工具及其共用库(docs/clang-fix-campaign/spikes/ 下的 p5q_fill_rehearsal.mjs、p5q_compare_raw_active.mjs、p5q_c5_tools.mjs),不修改任何生产代码、Policy 或 installGuards。修改内容:
   a. 失败落盘:每个阶段(login、open_form、fill、记录组装、写出)都要有阶段名;无论成功还是失败,都在 finally 中写出 run.json。run.json 记录以下内容:
      - 阶段名;
      - 代理应答中的固定字段(ok、error、field、released、snapshot_state,以及是否带 diagnostic);
      - 代理返回的诊断(本已脱敏,仍经 checkedWrite 写前写后自检,单独存为 diagnostic.html 与 diagnostic.json);
      - agent.runtime.trace;
      - 已观察到的回调元数据;
      - 身份计数;
      - 已取得的 snapshot 结构事实。
      异常信息只记录:AgentError 的 code;本工具自己抛出的固定大写错误名(完整匹配 ^[A-Z_]+$);其它异常只记类名。不得记录异常原文或堆栈。终端 stderr 只输出固定格式"EVIDENCE_STOPPED stage=<阶段> code=<错误名>"。run.json 写出本身失败时,stderr 输出固定的"EVIDENCE_WRITE_FAILED"。
   b. 身份计数钩子不得影响生产流程:演练工具挂在 agent.snapshot 与 page.goto 上的身份计数,出错时只记录错误码(按 a 的规则),不得向外抛出;生产的 open_form、fill 按原样继续执行。只要有任何一次身份计数失败,本次演练的结论标为"证据不完整",不得算作通过。
   c. observeCallbacks 的事件监听:adaptProtocol 抛错时只记录一条"ADAPT_FAILED",不得向外抛出;出现过该记录的,本次演练结论同样不得算作通过。
3. 静态护栏不变,另增一条断言:两个工具源码中不出现 error.message 与 error.stack 的输出或落盘。
4. 离线验证:在 C5a 的假服务器上逐一注入以下失败,断言 run.json 存在、阶段名与错误名正确、不含原始异常文本、prompt 中禁止的内容一律不出现:
   - 登录超时;
   - open_form 返回 QB_FORM_CHANGED 并带诊断;
   - fill 在第 3 个字段失败;
   - 身份计数钩子抛错,但生产 fill 仍完成,结论为"证据不完整";
   - 监听器遇到非法地址;
   - run.json 写出失败。
   另跑一次完整的正常演练。全量 pytest、mypy、ruff、lint-imports、Node 自检、design.md 检查器全部通过。
5. 先提交并推送工具修改与离线验证证据,再进入真机重跑。

### 36.2 本轮计划与边界

基线78212fe,冻结SHA256已实算匹配f16621bb…cf91c。先实现工具层finally落盘、
失败诊断、非干扰身份/回调观察及离线注入测试,跑全部门禁并独立提交推送。
不改生产/Policy/installGuards/冻结稿,不重跑raw-active-01,不覆盖历史证据。
本轮离线阶段仅假服务器;真机演练须在工具提交后确认目标行并重新收到“开始”。
成功样本与BUILD_NOTES样本仍暂无。只login/open_form/fill/close,不提交、不点Ok、
Accept或Ready to Accept,不运行真实触发/结果CLI、不写state DB、不推Gerrit。
未来真机目录fill-rehearsal-02,现阶段不创建、不启动。第三步仅解析既有脱敏归档。
第四步提示词末尾截在“页面版本与”,已明确的逐字段与前后action记录要求照前轮执行。

### 36.3 工具实现与离线注入

三个spikes文件为本轮唯一可执行工具改动,生产目录/Policy/installGuards/design.md/
冻结稿零diff。共享EvidenceRun记录stage、固定应答字段、trace、观察器错误、
身份计数与已脱敏snapshot结构事实;withEvidence的finally统一写run.json。
诊断HTML与结构JSON经同一checkedWrite写前/写后检查后分文件保存。
失败只记录AgentError.code、EvidenceError固定大写code或其它异常的类名;
不读任意异常message/stack作为日志,未登记的异常文本即使是大写也不采纳。
身份钩子失败仅记IDENTITY_COUNT_FAILED,不向生产snapshot/goto抛出;
非法协议事件仅记ADAPT_FAILED,不把事件原文带出。任一观察失败均标
EVIDENCE_INCOMPLETE,即使生产fill成功也不判演练通过。

运行环境只复用C5a的本地HTTPS假服务器/测试证书/DNS映射。测试入口模拟人工
登录,生产login未改。未启动真机窗口;未读/写真实state DB,未访问Gerrit。

定向复跑证据:`evidence/C5b/tool-fix-01/focused-02.log`,pytest 3 passed;
新增Node矩阵12 passed(含外层测试),既有工具Node矩阵12 passed。
其中包含额外的goto/snapshot两个身份失败入口、记录组装失败与比较读取失败。

| 注入/对照 | 阶段与错误/状态 | 落盘及副作用证据 |
|---|---|---|
| 登录超时 | login / QB_LOGIN_TIMEOUT | run.json存在;假服务器仅GET signin;关闭浏览器/profile |
| open_form结构变化 | open_form / QB_FORM_CHANGED | 固定应答+diagnostic.html/json;零表单提交 |
| 第3字段失败 | fill / QB_FORM_CHANGED | BUILD_REFERENCE窗口拒绝1;前2回调实收;诊断与snapshot保存 |
| goto身份钩子抛TypeError | EVIDENCE_INCOMPLETE | fill仍成功完成12字段;仅类名,无异常原文 |
| snapshot身份钩子抛TypeError | EVIDENCE_INCOMPLETE | 同上,降级只保存结构计数并标facts_unavailable |
| 观察监听器非法URL | EVIDENCE_INCOMPLETE / ADAPT_FAILED | 不抛出、不保存原始事件,fill仍完成 |
| run.json不能写 | write / EVIDENCE_WRITE_FAILED | 固定stderr,退出失败;故意把该路径设为目录,不伪造run.json |
| 正常演练 | PASSED | 12字段各1允许/0拒绝/HTTP200;not_released,action放行0 |
| 组装抛TypeError | assemble / TypeError | run.json仍保存已有快照、12回调与成功fill应答,不是通过 |
| 比较工具读取跳转 | read / QB_READ_REDIRECTED | run.json保存失败应答和trace,不继续取其它页 |

写出失败用例按裁定的EVIDENCE_WRITE_FAILED出口验收;存储本身不可写时不可能
同时要求有效run.json,没有伪报文件存在或通过。其它失败均断言run.json存在。
全部用例检查模拟异常原文、模拟密码、未遮蔽身份与会话文本不出现在归档;
工具源码静态护栏补message/stack禁用断言。每例浏览器关闭、临时profile删除。

开发期focused-01为1 failed/1 passed:额外的assembly注入已经正确写出
assemble/TypeError,但测试随后误执行成功场景的registrations.length断言;
仅改此测试的分支,改查已取得snapshot/回调,未改生产或放宽验收。
失败日志与首轮产物保留,不把focused-01计作通过。

Node独立自检`node-selftest.log`:346 passed/0 failed/0 skipped。
mypy exit0(116 source files)、lint-imports exit0(6 kept/0 broken)、design检查0 problem。
工作目录`ruff check .`发现53项,全部在开工前已有且未跟踪的audit_four_sigs.py、
hashobj2.py、ident_check3.py、norm_diff5.py;不改这些草稿。沿用C5a的
git checkout-index完整待提交树导出方式运行`ruff check .`,exit0。两份日志均保留。
全仓pytest与最终新增集合对账已完成,见§36.4,未把定向通过当作全量验收。

### 36.4 离线验收与提交边界

证据根目录:[evidence/C5b/tool-fix-01](evidence/C5b/tool-fix-01/README.md)。
完整命令/环境/exit分别保存于`full-command.json`、`gate-commands.json`、
`node-selftest-command.json`与`ruff-pending-tree-command.json`。

| 门禁 | 本轮结果 | 证据 |
|---|---|---|
| 全仓pytest -v -s | exit0;2639 passed/0 failed/1 skipped,636.12s | full.log、full.xml |
| 基线集合对账 | 2639→2640项;新增1,删除0 | test-set-audit.json |
| 新增故障矩阵 | Node 12 passed/0 failed/0 skipped;含外层测试 | full.log、full-injections/outcomes.json |
| 原有C5a工具用例 | Node 12 passed/0 failed/0 skipped;原始/活动比较及演练 | full.log、full-local-integration/ |
| Node独立自检/源码护栏 | 346 passed/0 failed/0 skipped | node-selftest.log |
| mypy | exit0;116 source files | mypy.log |
| Ruff完整待提交树 | exit0;All checks passed | ruff-pending-tree.log |
| lint-imports | exit0;6 kept/0 broken | lint-imports.log |
| design.md检查器 | exit0;0 problem | design-check.log |

集合对账使用C5a已归档`full-02/pytest.xml`与本轮JUnit XML逐testcase比较。
唯一新增pytest入口是`test_node_c5b_failure_evidence`;唯一skip仍是大小写敏感
文件系统上的既有平台特定测试,不是Node或真hook跳过。故障注入与既有本机
浏览器测试均在本机实跑,不涉及真实QuickBuild或Gerrit。

全目录附加脱敏自检先发现full.log/full.xml含既有负例nodeid中的合成凭据字面量
与HTML夹具片段,不是运行时真实凭据。入库前仅遮蔽这些日志参数并对控制台日志
做HTML转义;XML用结构化解析再序列化,测试总数/失败/跳过数不变。原始日志与
处理后hash见`log-redaction.json`;集合对账在日志脱敏前执行,未对nodeid集合
新增例外。原始日志不入库;216个最终证据文件均过PageRedactor.check_bytes。

完整运行的正常对照12字段均1获准/0拒绝/HTTP200,读回匹配、@freeze为
初始选中项,release_state=not_released、form_action_releases=0。
`full-injections/`逐用例保留run、诊断(如有)、服务器请求记录和固定stderr;
写出故障只证明固定失败出口及清理,不虚构可写的run文件。
生产路径、Policy/installGuards、设计正文、冻结稿及raw-active-01对78212fe零diff。
原始19份C5b文件hash不变;新证据脱敏复核与正常演练字段对账见
`artifact-audit.json`。暂存仅三个spikes工具、相关离线测试、本节/INDEX及
本轮证据,不包含用户既有.gitignore改动、四个docs删除或未跟踪草稿。
暂存区全量diff-check exit2仅报告28处生成日志/合成页面的尾空白,保留取证输出;
工具、测试及progress/INDEX范围的同一检查exit0,不格式化归档页面。

### 36.5 真机闸门与挂账

工具修复提交由Git外部锚定;推送后先询问是否沿用
`platform/upstream/llvm@67619ec8bbbac7238a6cfc33a481ccfbcd12206f`,
若换行先核对完整格式。确认后再请求新的“开始”;历史“开始”不复用。
本次离线阶段没有启动真机浏览器,没有创建fill-rehearsal-02,没有新增QB请求。

| 项目 | 当前状态 |
|---|---|
| P5Q-C5B-01停点 | 已由P5Q-C5B-02裁定处理;历史exit1与原因未知事实保留 |
| 固定六页原始/活动字节比较 | PASS保留,本轮不重跑;60项一致/身份计数0 |
| 工具失败落盘与离线验证 | COMPLETE;本节证据 |
| fill-rehearsal-02 | WAITING_TARGET_AND_START;不得记为通过 |
| 1193469离线failed_steps/child_overview分析 | PENDING;按本轮顺序在真机重跑后执行 |
| 成功样本、非空BUILD_NOTES样本 | OPEN;仍暂无 |
| C6前置 | NOT_MET:真机填表未通过,且未获C6真实提交确认 |

无生产规则变更,未新增需要放宽设计的请求;本轮已记录的存储故障按裁定规定
走EVIDENCE_WRITE_FAILED出口。完成工具提交不等于完成C5b,不得进入C6。

### 36.6 真机重跑授权与执行

§36.5为工具提交时的历史闸门状态。工具修复`5afb645`已推送origin/clang-fix-campaign,
FatTank本轮明确回复“沿用。开始”。确认目标行原样为:

```text
platform/upstream/llvm@67619ec8bbbac7238a6cfc33a481ccfbcd12206f
```

完整格式核对通过,冻结hash仍为f16621bb…cf91c;三个工具及生产代码相对
5afb645无工作树改动,新输出目录事前不存在。仅运行一次下列命令,登录只由
FatTank在窗口完成,不读终端输入、不取凭据、不重跑原始/活动文档比对:

```bash
env -u QB_COOKIE -u QB_PASSWORD -u DEBUG -u PWDEBUG -u NODE_OPTIONS /home/linhao/.local/bin/node docs/clang-fix-campaign/spikes/p5q_fill_rehearsal.mjs --target platform/upstream/llvm@67619ec8bbbac7238a6cfc33a481ccfbcd12206f --output docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C5b/fill-rehearsal-02
```

exit0;login/open_form/fill/close四个应答均ok=true,无diagnostic。
run.json状态PASSED,失败为空;未出现WORKER_BLOCKED、NEW_PAGE或ADAPT_FAILED。
浏览器由工具close关闭,进程结束,未重试。命令/授权/退出码见
`evidence/C5b/fill-rehearsal-02/execution.json`。
run.json SHA256:`c975d19eed9ad0e13c7592fb672436ac6f3e255816b921e504197d93757a97e7`。

### 36.7 十二字段真机验收

原始运行记录:[fill-rehearsal-02/run.json](evidence/C5b/fill-rehearsal-02/run.json);
逐项机械对账:[acceptance.json](evidence/C5b/fill-rehearsal-02/acceptance.json)。
以下12行均为获准1/拒绝0/回调HTTP200,读回逐字段等于要求值;
SNAPSHOT_NUM的@freeze等于该字段开始时的唯一选中项。

| 字段 | 初值已等 | 获准/拒绝 | HTTP | random原值 | 读回 |
|---|---|---|---|---|---|
| BUILD_TYPE | 是 | 1/0 | 200 | 0.18186181716435856 | Full |
| REPO_TYPE | 是 | 1/0 | 200 | 0.6711595992734872 | ALL |
| BUILD_REFERENCE | 是 | 1/0 | 200 | 0.5303376859101842 | Ref. Snapshot |
| SNAPSHOT_NUM | @freeze | 1/0 | 200 | 0.3966841414702431 | tizen-base-toolchain_20260924.094908 |
| PROJECT_BRANCH | 是 | 1/0 | 200 | 0.09292005471267772 | tizen_base |
| Immediate Stop With Error | 是 | 1/0 | 200 | 0.24318240062835306 | true |
| CHILD_CONFIGURATIONS | 是 | 1/0 | 200 | 0.39746795008835334 | [standard-armv7l:aarch64:x86_64] |
| Build Package List | 否 | 1/0 | 200 | 0.08296163547319368 | §36.6目标行,逐字相等 |
| Add Package List | 是 | 1/0 | 200 | 0.4214171457659791 | 空串 |
| Remove Package List | 是 | 1/0 | 200 | 0.03201454955146443 | 空串 |
| TARGET_IMAGE | 是 | 1/0 | 200 | 0.2044692257376286 | [] |
| BUILD NOTES | 否 | 1/0 | 200 | 0.2388493290930449 | clang-fix-campaign request=rehearsal-59518afe99534d119917d66c416cb87f |

10个值已相等的字段(含@freeze及双列表)均触发一次回调,不是跳过。
全部字段记录的页面均为`https://quickbuild.tizen.org/wicket/page?4`,
全部action及最终action均为`https://quickbuild.tizen.org/wicket/page?4-1.IFormSubmitListener-form`,
版本/action未变。回调完整原文、初值、读回与指纹在run.json中保留;
指纹为`3ea1c735a8ac260d2cd0f5e319ddbd3b8f35744dc8611aafb180a25227b6e62b`。

身份观察20次全部0,observer_errors=[];没有身份计数失败或ADAPT_FAILED。
trace仍有16条其它请求DENIED(login4/open_form11/fill1),路径仅为代理记录的
形态,不据此猜资源名;它们不是被拒字段回调,不曾追加放行或绕过。
release_state=not_released、form_action_releases=0,无submit命令、无Ok/Accept/
Ready to Accept点击、无构建产生,未运行真实qb-trigger/qb-result-fetch或写state DB。

附加审计初次误将formFacts.first_failed_check必须为空作为断言而exit1;
核对生产`formFacts`后确认该诊断辅助函数无结构问题时返回默认
field_window_or_readback,而open_form轮询早期可返回heading。它不是命令失败标志。
原始快照保持4次heading/15次默认标记,未删改;验收按裁定规定的命令应答、
12字段窗口、读回、身份与release记录完成。不修改工具、不重跑真机。

### 36.8 既有归档的离线事实

只调用`ci_triage.qb_result_html.failed_steps`与`child_overview`,不运行CLI,
不访问网络、不写state DB。分别解析raw-active-01中的03/05原始字节脱敏页及
活动文档脱敏页,两种来源的解析结果逐字段相同。完整原文/输入hash/调用参数见
[archived-analysis-02.json](evidence/C5b/archived-analysis-02.json),exit0。

- 失败步骤:`master > BUILD > Build > Build_GBS`。归档
  `raw-active-01/05.raw-redacted.html:814/:946/:1237/:1283`为对应层级名称,
  与冻结稿附录C第13项的路径一致。
- 子构建Status原文`Failed`,归一`FAIL`;配置为
  `root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/build`。
  状态来源`raw-active-01/03.raw-redacted.html:828`。
- Error Message区块从同页`:848`开始,标题在`:849`;生产函数原样返回整个
  区块文本(2093字符,含Step/Error表头、四行错误及命令输出),不是一条摘要。
  附录C第13项的`Composite step 'BUILD' failed due to unsatisfied success condition`
  对应`:868`的完整句子(原文带句末点号),确实包含于返回值。
  `:862/:874/:880`另有master/Build/Build_GBS的错误,不删减冒充单句原文。

未发现本次已取得事实与第5.3节/附录C第13项的矛盾。成功样本与非空BUILD_NOTES
样本仍未提供,没有用本次未提交的演练BUILD NOTES读回来替代构建回显样本。

### 36.9 挂账、验收与收尾

| 义务/前置 | 当前结论 |
|---|---|
| 第1.6a原始/活动文档比对 | PASS保留:固定6页60项一致,身份计数0;本轮不重跑 |
| 第1.6c填表演练 | PASS:fill-rehearsal-02一次运行,十二字段全部满足裁定 |
| 1193469失败步骤/错误原文 | COMPLETE:§36.8离线解析,两种归档结果一致 |
| 成功Ref. Snapshot样本 | OPEN:暂无,可按冻结稿由C6补齐,未关闭前不得P5Q CLOSED |
| 非空BUILD_NOTES构建回显样本 | OPEN:暂无,同上 |
| C6三项技术前置 | 本机集成/第1.6c/原始字节比对均PASS |
| FatTank对C6真实提交的确认 | NOT_GIVEN:本次“沿用。开始”仅授权C5b演练 |
| C6最终准入 | NOT_MET:尚缺C6明确确认;本轮止于C5b |

本轮只新增脱敏证据和进度/INDEX文档;生产、三个工具、冻结稿、历史证据均未改。
§36.4的全量2639 passed/1 skipped及全部代码门禁来自5afb645工具修复提交,
不冒称本次文档收尾重新跑了全仓。收尾复跑取证静态护栏和design检查,
并核对新文件写后脱敏、原始19份历史hash与冻结hash;命令/exit见
`evidence/C5b/fill-rehearsal-02/validation.json`。无新增停止报告,不进入C6。

## 37. 实施裁定 P5Q-C6-01:C6 的状态库与远端核对

### 37.1 裁定原文

1. 冻结稿未写明 C6 如何准备"已推送到 sandbox 分支"的 unit;而 P12 之前不允许任何真实推送。C6 因此使用专用的 state DB 与专用配置,放在 <仓库外的专用目录>/p5q-c6/ 下(具体路径由实现方确定并记入 progress.md),不使用、也不触碰任何真实 campaign 的 state DB。
2. 状态库构造方式照搬 C5a 完整链路用例(tests/unit/test_p5q_c5a_integration.py)中的 state DB 与本地裸仓库:三份 verification record、unit、DERIVE 事件(derived_commit_sha 为目标 commit)、PUSH 事件(result=ok,ref 为 sandbox 白名单内的一个 ref 名,pushed_sha 为目标 commit)。
3. 远端核对:专用配置的 gerrit_ssh_base 指向本机一个 bare 镜像目录。在镜像中建立上述 sandbox ref,指向目标 commit。目标 commit 的对象只允许从 Tizen Gerrit 只读拉取(fetch),严禁任何 push。拉取与建 ref 的命令全部记入 progress.md。
4. 除远端地址外,代理、浏览器、qb-trigger、qb-result-fetch、QuickBuild 全部走生产路径;不传任何测试专用参数(--host-resolver-rules、测试证书等)。远端核对这一步已由 C3 离线验证,C6 不覆盖它;收口文档须写明这一点。
5. 下次修订设计时并入第 9.4 节第 2 步。

### 37.2 专用路径与隔离边界

开工HEAD `1c770da`,分支clang-fix-campaign。已读§35及之后;
权威v1.5冻结稿SHA256实算为
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`,匹配且不改。
以下专用根目录位于仓库外,开工检查不存在,待目标确认后创建:

```text
/home/linhao/Toolchain/p5q-live-validation/p5q-c6/
  state.db
  config.yaml
  state/
  ws/
  remotes/<目标仓库路径>
```

上面的remotes子路径使用目标仓库路径(如platform/upstream/libtirpc),
待目标确认后登记完整路径。`gerrit_ssh_base`仅指向该专用remotes目录。
构造依据是C5a集成测试引用的`tests/unit/test_qb_trigger.py::Campaign.add`;
三份PASS verification与DERIVE/PUSH均为本裁定专用合成前提,不是真实gbs验证
或真实推送的证明,不得混入任何真实campaign。C6仅验证真实QB路径,不覆盖
真实Gerrit远端绑定;此限制移交收口文档。

生产代码、工具和冻结稿不改。已有.gitignore改动、四个docs删除与未跟踪草稿
原样保留,不纳入提交。不读取/保存账号、密码、Cookie;永不点Accept/Ready to Accept。

## 38. C6a 真实提交

### 38.1 计划与当前人工闸门

当前状态WAITING_TARGET。已向FatTank询问目标行,未把C5b的“沿用。开始”
当作C6a目标选择或真实提交授权。待选候选:

- `platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0`
- `platform/upstream/pam@119d738652c19a33e8cc5d959f416185fb34c6cb`
- `platform/upstream/llvm@67619ec8bbbac7238a6cfc33a481ccfbcd12206f`

候选hash目前只来自任务书,尚未宣称经过manifest实测。确认目标后依次:

1. 一次普通HTTP GET取得任务指定的20260924.094908 manifest,解析XML并保留
   目标project元素原文,逐字比较revision。若选择LLVM,记录任务指定的非快照
   commit限制,不得把构建结果归因于工具链路本身。
2. 在§37.2专用路径用C5a形态建立本地镜像和状态前提;仅fetch目标对象与本地
   update-ref,不推送Gerrit。所有构造命令、合成事实与SQL导出单列入证。
3. 用假代理做无真浏览器/无QB请求的前置核验;另核对本地镜像ref等于目标sha。
   不得留下SUBMITTED/BUILD_BOUND等假执行结果污染真实一次提交的起点。
4. 展示十二字段拟填值与专用路径后,请求FatTank逐字回复“确认提交”。
   “开始”或其它答复不算授权。request_id由生产命令生成,不伪造预先已生成的值。
5. 获授权后只运行生产qb-trigger一次,绝不带--retrigger。submitted_bound记录
   构建号;QB_SUBMIT_UNCERTAIN只请FatTank按标记查号并走人工绑定,不重提。
   其它结果立即停止。随后只运行一次规定的生产qb-result-fetch。
6. 登记父页回显、请求标记/冻结值、stdout/exit/状态迁移与脱敏证据,提交推送后
   停止。约24小时后的终态读取与收口属于C6b,不在本轮范围。

当前尚无manifest GET、Gerrit fetch、专用状态库写入、真实浏览器或QB请求;
拟填值完整确认表、真实执行命令和证据在目标确认后追加,不提前填入结果。
§36的成功样本与BUILD_NOTES构建回显样本挂账仍开放。
本准备提交仅progress/INDEX;运行`.venv/bin/python docs/clang-fix-campaign/tools/check_design_doc.py docs/clang-fix-campaign/design.md`,exit0/0 problem。
冻结hash匹配;未改代码,未重跑全仓,不把§36历史验收记为本轮实跑。

### 38.2 目标确认与快照原文

§38.1为fa26715准备提交时的历史状态。本轮FatTank回复原文:

```text
platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0
```

目标格式核对通过;此回复只确认目标,不是“确认提交”。冻结稿hash仍匹配。
对任务指定manifest只做一次普通HTTP GET,无重试、无重定向、无浏览器:

```bash
curl --silent --show-error --retry 0 --max-time 60 --max-redirs 0 --proto '=http' --output /home/linhao/Toolchain/p5q-live-validation/p5q-c6/preparation/manifest.xml --write-out '%{json}\n' http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20260924.094908/builddata/manifest/tizen-base-toolchain_20260924.094908_standard.xml
```

exit0/HTTP200,Content-Type=`text/xml; charset=utf-8`,33380字节。
完整公共manifest归档[evidence/C6a/preparation/manifest.xml](evidence/C6a/preparation/manifest.xml),
SHA256=`aa8ff39bd437a625fe2db2927311b071149b836a5f0212aa49638d8b728d6d69`。
XML解析恰好命中一个目标project,revision与目标逐字相等。
第97行原文(保留前导两个空格):

```xml
  <project name="platform/upstream/libtirpc" path="platform/upstream/libtirpc" revision="7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0"/>
```

核对命令、属性与原始行见[manifest-check.json](evidence/C6a/preparation/manifest-check.json)。
这是指定20260924.094908快照的证明,尚未打开当前QB表单;
不把历史/manifest快照值冒称为本轮表单当前选中项。

### 38.3 专用状态与镜像构造

全部构造入口为本轮独立证据脚本
[prepare_c6.py](evidence/C6a/preparation/prepare_c6.py),不进入生产包。
四个阶段各执行一次:

```bash
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/preparation/prepare_c6.py manifest
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/preparation/prepare_c6.py fetch
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/preparation/prepare_c6.py construct
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/preparation/prepare_c6.py preflight
```

四阶段exit0。fetch阶段复用生产SandboxGit统一环境与八项`-c`覆盖,
SSH固定`ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=20`,
不输入凭据、不放松主机校验。以下为逐条git子命令,完整argv/exit/stdout/stderr
均在[mirror-commands.json](evidence/C6a/preparation/mirror-commands.json):

```text
git init --bare /home/linhao/Toolchain/p5q-live-validation/p5q-c6/remotes/platform/upstream/libtirpc
git -C <上述镜像> fetch --no-tags --no-recurse-submodules --depth=1 ssh://review.tizen.org:29418/platform/upstream/libtirpc 7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0
git -C <上述镜像> cat-file -t 7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0
git -C <上述镜像> rev-parse 7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0^{tree}
git -C <上述镜像> update-ref refs/heads/sandbox/p5q-c6-libtirpc 7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0
git -C <上述镜像> show-ref --verify refs/heads/sandbox/p5q-c6-libtirpc
```

六条exit0,实际fetch一次、Gerrit push零次。对象类型commit,
tree=`9ef054c6187444dedb07aab80fb04279f5683bf4`,本地sandbox ref与目标一致,
见[mirror-check.json](evidence/C6a/preparation/mirror-check.json)。

专用库`/home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db`,
专用配置同根`config.yaml`,state-root同根`state/`,workspace同根`ws/`。
配置无凭据,Node/Playwright/Chromium均为生产本机路径,登录时限600秒;
无测试证书、DNS覆盖或其它测试专用参数。配置副本与hash见
[config.yaml](evidence/C6a/preparation/config.yaml)和
[state-prepared.json](evidence/C6a/preparation/state-prepared.json)。

unit=`p5q-c6-libtirpc-20261015`,verification IDs为该前缀加`-v0/-v1/-v2`,
对应aarch64/armv7l/x86_64。按C5a形态建立三份合成PASS、一个unit/round、
DERIVE/PUSH两事件和SANDBOX_PUSHED状态;均明确标注C6-01合成前提。
实际目标commit/tree来自只读fetch,不伪称已执行gbs、derive或Gerrit push。
专用合成说明见[synthetic-basis.json](evidence/C6a/preparation/synthetic-basis.json),
SQL导出见[state-before.sql](evidence/C6a/preparation/state-before.sql);不提交二进制数据库。

### 38.4 离线前置与远端核对

使用生产`cli.main`进入qb-trigger,仅在证据脚本中把代理进程替换为既有
`tests/fixtures/qb_fake_agent.py`;它在login处主动返回QB_LOGIN_ABORTED。
这是计划内的无浏览器边界探针,不是一次真实登录失败,不进入open_form/fill/submit。
CLI exit5、status=SANDBOX_PUSHED、request_id/request_seq均null;
假代理收到恰好login/close两条命令,前置校验已通过。生产代码与生产配置未改。

另在同一unit锁内调用生产`_snapshot`与`_remote_check`,使用
`ws/fe30a222b971/.transport`和生产统一git环境,执行本地镜像ls-remote;
核对通过、比对sha为目标commit,临时传输仓库已删除。
全部argv见[preflight.json](evidence/C6a/preparation/preflight.json),
没有git命令以主副本为-C/--git-dir,没有访问真实Gerrit做ls-remote。

专用库前后SQL完全一致,数据库原始字节SHA256也完全一致:
`bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405`。
campaign_qb_requests/profiles/events均0行;没有假SUBMITTED/BUILD_BOUND/RESULT或
假冻结值污染真实一次提交。真实浏览器0、QuickBuild请求0、真实提交0。

本轮定向验收:
- `pytest -q tests/unit/test_qb_trigger.py tests/unit/test_qb_config.py`:203 passed,
  0 failed/0 skipped,exit0,全部本地/假代理;
- 证据脚本ruff exit0;设计检查exit0/0 problem;
- 冻结稿/生产模块/既有工具/既有测试相对fa26715零diff。

命令与日志见[validation.json](evidence/C6a/preparation/validation.json)。
准备脚本初次ruff有行宽问题,仅格式化/拆行修正后通过;未修改生产或放宽检查。
本轮未重跑全仓,不把203定向测试称为全仓结果。

### 38.5 待确认的十二字段与真实提交闸门

目标配置为`root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER`,
overview_id=1917,qb_pass_requires_accept=false。拟填值:

| 字段 | 拟填值 |
|---|---|
| BUILD_TYPE | Full |
| REPO_TYPE | ALL |
| BUILD_REFERENCE | Ref. Snapshot |
| SNAPSHOT_NUM | @freeze:取真实填表时的唯一选中项并冻结,不预设历史值 |
| PROJECT_BRANCH | tizen_base |
| Immediate Stop With Error | true/勾选 |
| CHILD_CONFIGURATIONS | [standard-armv7l:aarch64:x86_64] |
| Build Package List | platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0 |
| Add Package List | 空串 |
| Remove Package List | 空串 |
| TARGET_IMAGE | []/空 |
| BUILD NOTES | clang-fix-campaign request=<生产qb-trigger将生成的request_id> |

状态WAITING_SUBMIT_CONFIRMATION。以上值与专用路径将呈交FatTank;
尚未收到“确认提交”,不开浏览器、不运行真实qb-trigger/qb-result-fetch。
生产request_id尚未生成。已批准的目标选择不替代此次完整字段确认。
无新增设计矛盾/停止报告;C6b终态读取仍不在本轮范围。

### 38.6 明确提交授权与一次执行

e08bcc9已推送,十二字段与专用路径已完整呈交后,FatTank本轮回复原文:

```text
确认提交
```

本条仅授权既定libtirpc目标的一次生产qb-trigger及随后一次生产qb-result-fetch,
不授权--retrigger、Gerrit push或Accept/Ready to Accept。登录只在浏览器窗口由
FatTank本人完成。执行前再次核对冻结hash、专用配置与状态库的准备hash;
启动/结束时间、完整argv、stdout/exit及SQL快照落evidence/C6a/live-01。
一次执行记录采用新目录排他创建,不覆盖、不重跑;结果在执行后追加。

### 38.7 一次生产调用结果与停止报告

本轮代码基线e08bcc9。仅运行下列记录入口一次,它不修改生产代码、不替换代理,
不传测试参数,只排他登记调用及检查生产输出后落盘:

```bash
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/run_c6_once.py trigger
```

实际生产argv(没有--retrigger):

```bash
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python -m ci_triage qb-trigger --verification-ids p5q-c6-libtirpc-20261015-v0,p5q-c6-libtirpc-20261015-v1,p5q-c6-libtirpc-20261015-v2 --state-db /home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db --state-root /home/linhao/Toolchain/p5q-live-validation/p5q-c6/state --config /home/linhao/Toolchain/p5q-live-validation/p5q-c6/config.yaml
```

清除QB_COOKIE/QB_PASSWORD/DEBUG/PWDEBUG/NODE_OPTIONS/PYTHONPATH/MYPYPATH环境项,
stdin为DEVNULL,不读终端输入,登录只由FatTank在生产浏览器窗口操作。
配置/冻结稿hash及准备DB字节hash在启动前再次匹配。未访问真实Gerrit或推送。

- UTC开始:`2026-10-15T07:03:21.402428+00:00`。
- UTC结束:`2026-10-15T07:13:57.523871+00:00`。
- CLI exit **5**;记录入口exit0只表示输出保存完成,不代表生产命令成功。
- 配置登录时限600秒,未提前终止;总耗时636.12秒含启动和退出,不把总耗时
  当成精确登录等待时长。
- stderr只有生产固定登录提示;无诊断目录、页面证据或异常堆栈。

完整stdout原文见[stdout.json](evidence/C6a/live-01/trigger/stdout.json),核心结果:

```json
{"action":"submit_failed","campaign_unit_key":"p5q-c6-libtirpc-20261015","error_code":"QB_LOGIN_TIMEOUT","status":"SANDBOX_PUSHED","request_id":null,"request_seq":null,"qb_build_id":null,"diagnostic_dir":null,"message":null,"sbs_target":"platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0"}
```

停止点为生产login,未走到生成request_id、填表、提交意图或submit。
不是submitted_bound,也不是允许人工查号绑定的QB_SUBMIT_UNCERTAIN。
因此按任务第三步第2条“其它任何结果停止”执行:不重试、不换路径,
不运行qb-result-fetch,不构造人工绑定,不进入C6b。

现有证据只有生产错误码,没有登录请求链或三条件逐项结果。
不得据此断言“没有人工登录”,也不得断言“落点被拒/检测器错误”。
原因未确定,未取得足以证明与冻结稿矛盾的事实;不自行改等待时间、工具或规则。
后续若需继续,须由FatTank/设计方另行明确新的登录取证或执行安排;
本次“确认提交”不解释为重试授权。

### 38.8 停止后核对、挂账与证据

证据目录[evidence/C6a/live-01](evidence/C6a/live-01):
command.json/execution.json记录授权、完整argv、时间与CLI exit;
stdout.json/stderr.txt保存生产输出;state-after.sql是只读SQL导出。
所有写出均调用PageRedactor.check_bytes做写前/写后检查,未保存凭据或浏览器配置目录。
生产CLI及代理进程已结束,未发送额外QB请求排障。
清理核对时/dev/shm另有一个目录,mtime为2026-10-14T07:02:58Z,早于本轮,
没有引用它的进程;仅记录目录元数据,不读内容、不删除既有目录,
见`evidence/C6a/live-01/cleanup-metadata.json`。不将此旧目录误报为本轮新建残留。

[stop-audit.json](evidence/C6a/live-01/stop-audit.json)确认:
- 真实qb-trigger调用数1;没有第二次调用,无--retrigger;
- state-after.sql与准备阶段state-before.sql逐字节相等;
- DB SHA256仍为`bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405`;
- campaign_qb_requests/profiles/events均0行,状态日志仅SANDBOX_PUSHED;
- 无fetch执行目录,没有qb-result-fetch stdout或状态迁移;
- request_id、构建号、提交落点均未取得,父构建BUILD_NOTES/BUILD_REFERENCE/
  SNAPSHOT_NUM回显未取得,无法做请求标记与冻结值的比对。

| 义务 | 当前结论 |
|---|---|
| 目标与manifest | PASS,保持§38.2逐字匹配 |
| 专用状态/镜像/离线前置 | PASS,保持§38.3–38.4;合成前提不代表真实gbs/推送 |
| 明确提交授权 | RECEIVED,原话“确认提交”;一次生产调用已消耗 |
| 真实提交与绑定 | NOT_COMPLETED,QB_LOGIN_TIMEOUT;未产生提交 |
| 首次qb-result-fetch | NOT_RUN,按停止规则跳过 |
| 成功样本/非空BUILD_NOTES回显 | OPEN,本次未补齐 |
| C6b终态读取 | NOT_READY,无request_id/构建号可供执行;不伪造查询命令 |

生产模块、已验收工具、冻结稿不改;仅本节/INDEX、一次执行记录脚本与脱敏证据。
收尾运行证据脚本ruff、design检查及新证据自检,结果见
`evidence/C6a/live-01/validation.json`。未重跑全仓,§38.4的203定向测试仍为
e08bcc9准备阶段结果,不冒称本次重跑。用户既有改动原样保留。

## 39. C6a 第二次执行记录

### 39.1 现场确认与分支

续任务基线3db000d;已重读§38及live-01的命令、exit/stdout/停止后状态证据,
权威冻结稿实算hash仍为
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`。
向FatTank询问了07:03 UTC那次是否弹出窗口、是否在窗口完成登录。
FatTank先回复:

```text
重跑
```

该答复未说明现场,没有据此启动。再次询问后,FatTank回复原文:

```text
没有弹出窗口
```

问题1已答“没有弹出窗口”;问题2未另行回答,不补造另一条原话。
依据本轮任务第一步明确将“窗口未弹出”归入的分支,登记为
**人工未在时限内登录**,进入第二步的本地准备与重新确认。
这仅是执行分支分类,不将未弹窗归因于人工疏忽,也不声称查明了未弹窗的技术原因。
不满足“窗口弹出且已完成登录”分支,本轮不写P5Q-C6A-02。

### 39.2 重跑前的只读核验

证据:[precheck.json](evidence/C6a/retry-preparation/precheck.json)。
读取前/后专用state.db的SHA256均为
`bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405`,
与live-01结束时相同,SQL导出也与其state-after.sql逐字节一致。
campaign_qb_requests/profiles/events各0行,unit最新状态SANDBOX_PUSHED。
配置与准备阶段归档逐字节相同;live-02目录尚不存在。
本次检查不初始化schema、不写数据库、不访问网络、不启动浏览器。

记录入口run_c6_once.py仅增加`--evidence-run live-02`输出选择;
此参数不转发给生产CLI或代理。生产argv、环境处理、600秒登录时限和
目录排他创建保护不变;live-01原始文件保持原样。
准备使用的记录入口如下,**本节登记时未执行**:

```bash
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/run_c6_once.py trigger --evidence-run live-02
```

其中实际生产qb-trigger命令必须与§38.7完整argv相同,无--retrigger。
本轮最多一次生产调用;若再次登录超时或出现其它非准许结果,停止并保留证据,
不再自行重跑。未生成新request_id,未取得父页回显或读取结果。

记录入口四项全模拟检查4 passed/0 failed/0 skipped:默认live-01输出保持;
live-02的生产argv/环境/stdin/stdout处理与live-01相同且旧文件未变;
fetch只取所选执行目录的request;重复目录在创建进程前即拒绝。
所有Popen均为桩,临时测试DB与专用C6库分离,无浏览器/网络请求。
结果见[recording-path-tests.json](evidence/C6a/retry-preparation/recording-path-tests.json)。
记录脚本ruff exit0、design检查exit0/0 problem、diff-check exit0;
未改生产代码,未重跑全仓。live-01与冻结稿原样保留。

### 39.3 新的确认闸门

重新呈交十二字段,与§38.5相同:

| 字段 | 拟填值 |
|---|---|
| BUILD_TYPE | Full |
| REPO_TYPE | ALL |
| BUILD_REFERENCE | Ref. Snapshot |
| SNAPSHOT_NUM | @freeze:取填表时的唯一选中项并冻结 |
| PROJECT_BRANCH | tizen_base |
| Immediate Stop With Error | true/勾选 |
| CHILD_CONFIGURATIONS | [standard-armv7l:aarch64:x86_64] |
| Build Package List | platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0 |
| Add Package List | 空串 |
| Remove Package List | 空串 |
| TARGET_IMAGE | []/空 |
| BUILD NOTES | clang-fix-campaign request=<生产命令将生成的request_id> |

专用路径仍为`/home/linhao/Toolchain/p5q-live-validation/p5q-c6/`下的
state.db、config.yaml、state/和ws/;目标配置RBS/TRIGGER,overview_id=1917。
提醒FatTank浏览器弹出后须在600秒内在窗口完成登录,不读终端输入。
仅新的逐字答复“确认提交”解锁本轮启动;“重跑”“开始”和上一轮确认都不算。
当前状态LIVE02_WAITING_CONFIRMATION,无新增QB请求,不进入C6b。

### 39.4 live-02本地停止

上述等待状态为准备时的历史记录。FatTank随后新回复“确认提交”,启动一次
`run_c6_once.py trigger --evidence-run live-02`,原始command.json保持原样。
记录开始于2026-10-15T07:55:15.941017+00:00。
记录进程1197349在写执行记录期间处于D状态,等待点jbd2_log_wait_commit;
对应/home位于/dev/sda1 ext4,日志进程jbd2/sda1-8也为D状态。
历次采样在34秒至2分59秒期间均未取得启动输出,2分12秒采样无子进程。
为避免恢复后突然继续提交,对该记录进程发送SIGTERM,记录入口exit143;
回收时收到C6A_TRIGGER_STARTED,但没有取得生产stdout/exit。
该标记不能证明生产CLI未启动,也不能当作生产CLI成功或失败的结论。

停止后无run_c6_once.py、qb-trigger或qb_browser_agent.mjs进程;
专用库SHA256仍为bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405,
与live-01结束时逐字节相同。没有请求记录/冻结行/构建号,未执行qb-result-fetch。
未采到网络日志,不伪造HTTP请求数;不将本次记为QB_LOGIN_TIMEOUT。
证据见[evidence/C6a/live-02/stop-report.md](evidence/C6a/live-02/stop-report.md)。

### 39.5 live-03新的授权

FatTank在live-02停止后原话“重新再弹一次窗口”。再次明确说明生产命令会在
登录后自动提交,且仍沿用§39.3十二字段及同一libtirpc目标后,FatTank新回复:

```text
确认提交
```

仅据此授权live-03一次调用,不复用live-02的授权。执行前复核冻结稿hash、专用库
hash与无残留进程;新增目录live-03,不覆盖live-01/live-02。
记录工具仅扩展--evidence-run的输出选择,不转发给生产命令,argv/环境处理/600秒
登录时限不变,不加--retrigger。先做同文件系统同步探针,通过后再启动。
本轮不改生产代码或冻结稿,不进入C6b;执行结果见§39.6。

同文件系统checked_write及目录fsync探针通过,耗时0.603秒,临时合成文件已清理;
专用库只读查询三张QB表各0行,SQL导出仍与live-01逐字节相等。
记录工具ruff exit0,design检查exit0/0 problem,定向diff-check exit0。
live-03记录开始于2026-10-15T08:03:41.724509+00:00,生产argv与live-01逐项相等;
记录进程1199083、生产CLI1199087、代理1199088、Chromium1199302均已观察到。
本次600秒登录等待交由生产代理处理,不代填凭据、不额外发请求排障。

### 39.6 live-03实际结果与停止报告

本次记录入口命令:

```bash
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/run_c6_once.py trigger --evidence-run live-03
```

生产argv见[evidence/C6a/live-03/trigger/command.json](evidence/C6a/live-03/trigger/command.json),
与live-01完全相同,无--retrigger;新目录参数只作用于记录入口。
开始2026-10-15T08:03:41.724509+00:00,结束08:08:04.355155+00:00;
记录入口exit0表示落盘成功,**生产CLI exit5**,不能混用。
生产stdout完整保存在[stdout.json](evidence/C6a/live-03/trigger/stdout.json),摘要:

```json
{"action":"rejected","error_code":"QB_BROWSER_UNAVAILABLE","status":"SANDBOX_PUSHED","request_id":"e724b5428a4a45a5a2d03a0a93e6eb25","request_seq":null,"qb_build_id":null,"diagnostic_dir":null,"message":null}
```

从qb_trigger.py:571–579的控制流可知:request_id只在browser.login()正常返回后生成。
因此本次不同于live-01的登录超时,但没有另存三条件现场快照,不补造现场描述。
request_seq为空,三张QB表0行,SQL及DB hash逐字节未变,说明没有完成提交意图落库;
结合提交必须在_intent成功后调用的代码顺序,未进入提交步骤。request_id只在本次
内存/stdout中产生,不是可供qb-result-fetch使用的已登记请求。

[stop-audit.json](evidence/C6a/live-03/stop-audit.json)逐项核对:
- DB SHA256仍为bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405;
  SQL与live-01及本次归档逐字节相等,唯一状态仍SANDBOX_PUSHED;
- 请求/冻结/事件三表均空,无qb_traces或qb_diagnostics目录;
- 记录/CLI/代理/本次Chromium四个已知PID均不存在,无.transport残留;
- /dev/shm有两个p5q-browser目录,mtime均早于live-03开始,无进程引用;
  仅记录元数据,不读取内容、不删除、不据此推断来源;
- HTTP请求数没有采集,不伪填0;没有运行qb-result-fetch,没有重提/--retrigger。

停止点与证据边界见[stop-report.md](evidence/C6a/live-03/stop-report.md):
现有输出只能将失败限定在登录返回后、提交意图落库前,不能区分open_form、fill
以及驱动拒收/代理退出等具体原因。没有父构建页,BUILD_NOTES、BUILD_REFERENCE、
SNAPSHOT_NUM回显和冻结值均NOT_COLLECTED;不凭配置值冒充页面实测。
候选后续:由设计方批准只增加固定阶段/错误类别与安全trace的取证通道后定位,
不记录原始协议事件/凭据/响应正文;本轮不实施、不自行再跑。

### 39.7 挂账与本轮验收

| 义务 | 结论 |
|---|---|
| 目标与manifest | 保持§38.2 PASS,libtirpc原commit逐字匹配 |
| 专用状态/镜像/生产参数 | PASS,不触碰真实campaign;本地镜像边界保持P5Q-C6-01 |
| live-02停止 | 本地I/O阻塞,记录入口143,生产exit未知;原始command保留 |
| live-03一次新授权调用 | 已执行,生产exit5/QB_BROWSER_UNAVAILABLE,立即停止 |
| 提交、绑定、首次结果读取 | NOT_COMPLETED/NOT_RUN,无已登记request或构建号 |
| 父构建回显/成功样本/BUILD_NOTES样本 | OPEN,本轮未补齐 |
| C6b | NOT_READY,不能对未入库request伪造可执行读取命令 |

本轮只改记录工具输出目录选项、progress/INDEX和脱敏证据;生产模块、spikes、测试、
冻结稿与live-01全部未改。记录工具ruff、design检查、diff-check及证据字节自检结果
见[evidence/C6a/live-03/validation.json](evidence/C6a/live-03/validation.json)。
记录工具的五项全模拟检查5 passed/0 failed/0 skipped,所有Popen均为桩,不启动
浏览器、不联网、不写专用数据库;见[recorder-checks.json](evidence/C6a/live-03/recorder-checks.json)。
未重跑全仓pytest;§38.4的203定向测试与§36的2639/1均保持历史结果,不冒称本次重跑。
用户既有工作区改动不处理。等待设计方核对本次停止证据,不进入C6b。

## 40. 实施裁定 P5Q-C6A-03:先补生产诊断信息,再做一次不提交的真机诊断

### 40.1 裁定原文

a. 连续三次 C6a 执行各自因不同原因中止(live-01 未见窗口,登录超时;live-02 本机磁盘 I/O 阻塞;live-03 登录后报 QB_BROWSER_UNAVAILABLE),生产路径缺少足以定位的诊断信息。在定位清楚之前,不再进行真实提交。
b. 批准对生产代码做以下最小改动,只增加诊断信息,不改变任何放行、拒绝或判定逻辑:
   - 代理:runtime.failure 被置位时,同时记录一个固定的停止类别,枚举为 NEW_PAGE、WORKER_BLOCKED、WORKER_NOT_PAUSED、CLOSE_TARGET_FAILED、BROWSER_DISCONNECTED、PAGE_CLOSED、ADAPT_FAILED、FETCH_CONTINUE_FAILED、UNKNOWN。installGuards 中各个 onStop 调用处只允许增加这个类别参数,不得改动任何判定条件。浏览器的 disconnected 事件、page 的 close 事件也映射到对应类别。代理因此返回的错误应答增加 failure_category 字段(只能取上述枚举值)。代理异常停止时,stderr 输出一行固定格式"QB_AGENT_STOPPED category=<类别>"。
   - Python 驱动 qb_browser.py:decode_response 校验并保存 failure_category(取值不在枚举内,按协议错误处理);命令失败时,把命令名、agent 错误码、failure_category、代理进程是否已退出及退出码,记到 QbBrowserError 上。
   - qb-trigger 与 qb-result-fetch:任何代理命令失败时,把上述字段与命令名写入 state_root 下的 trace(沿用现有 _trace 写法与脱敏自检),stdout 结构不变。
c. 这些改动涉及 installGuards 函数体内的 onStop 调用点,因此四个拦截安全组必须从头重跑;第 9.2 节静态断言全部必须通过。
d. 真机诊断使用一个不提交的驱动脚本:只调用生产 QbBrowser 的 login → open_form → fill → close,源码中不出现 submit 命令。

### 40.2 现场询问与计划

开工基线66485ca;已核对§38、§39与三次停止证据。冻结稿hash仍为
f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c;
专用库hash仍为bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405。
已向FatTank询问live-03窗口、配置页/表单、其它点击/新窗口及关闭情况;答复待登记,
不将先前live-01的“没有弹出窗口”当作本次答案。

顺序:固定类别及命令元数据→不提交探针与离线注入→全量门禁和四组安全测试→
提交推送→环境采样/仅无进程引用的残留清理→等待新的“开始”→diag-01仅一次。
不改冻结稿/Policy判据,不运行真实qb-trigger/qb-result-fetch,不写专用状态库。
正常close的事件不误记为异常;事件类别只补诊断,不增加停止条件。

FatTank对live-03现场询问的回复原文:

```text
不记得了  应该弹出了
```

据此只记录“可能弹出,记忆不确定”;是否进入配置页/Specify Build Options、
是否有其它点击/新标签页/新窗口/手动关闭、是否自行消失均UNKNOWN。
不把上述不确定回忆当作故障原因,后续仍按本裁定的离线验收与一次不提交诊断执行。

### 40.3 实现与离线证据

- `qb_browser_agent.mjs`:固定九类、首个停止原因、固定stderr与failure_category应答;
  installGuards原onStop条件不动,仅补类别;正常close不归为异常。浏览器断开优先于
  同一次关闭伴随的page.close,单页关闭仍记录PAGE_CLOSED。Policy全文未变。
- `qb_browser.py`:校验类别;QbBrowserError保存command/agent_error_code/
  failure_category/agent_exited/agent_exit_code;驱动trace只含固定元数据。
- `qb_trigger.py`与`qb_result_fetch.py`:沿用_trace与脱敏检查,每次失败去重记账;
  原stdout键集合、错误码映射、状态库写入分支不变。trace写出失败不覆盖原结果。
- `spikes/p5q_c6_driver_probe.py`:只用生产QbBrowser的login/open_form/fill/close,
  12字段沿用§38.5、BUILD NOTES用probe专用标记;核对读回、指纹和released=false;
  finally写result.json并关闭进程。源码无submit字符串、不接收state DB参数。
- 测试入口`tests/node/p5q_cli_agent.mjs`只在本机HTTPS夹具中模拟人工登录和故障,
  不向生产驱动增加任何测试参数。新页面/断开/关页均为真实浏览器事件,不是伪造应答。

证据根:[diagnostic-preparation](evidence/C6a/diagnostic-preparation/README.md)。
完整命令与退出码在各子目录commands.json;测试stdout/JUnit保存原文。

| 验证 | 本轮结果与位置 |
|---|---|
| 全仓pytest | 2680 passed / 0 failed / 1 skipped;`full-02/pytest.log`、`pytest.xml`;较2639/1基线新增41项 |
| 停止类别Node+既有矩阵+§9.2静态负例 | 362 passed / 0 failed / 0 skipped;`tools-01/node.log` |
| 驱动/两CLI固定类别链路 | 九类分别保留,非法类别拒收;`test_qb_browser.py`、`test_p5q_c6_diagnostics.py` |
| 本机真实驱动正常路径 | login/open_form/fill/close全ok;读回及指纹一致;not_released、action放行0;`full-02/artifacts/normal/` |
| 本机新页面 | open_form记录NEW_PAGE;无构建;`full-02/artifacts/NEW_PAGE/` |
| 本机浏览器断开 | open_form记录BROWSER_DISCONNECTED;无构建;`full-02/artifacts/BROWSER_DISCONNECTED/` |
| 本机单页关闭 | open_form记录PAGE_CLOSED;无构建;`full-02/artifacts/PAGE_CLOSED/` |
| 四组安全从头重跑 | 4 passed / 0 failed,loopback-only;`safety-01/safety.log`;实际请求及Worker关闭分支在原文 |
| mypy | exit0,116 source files;`tools-01/mypy.log` |
| lint-imports | exit0;`tools-01/lint-imports.log` |
| design checker | exit0,0 problem;`tools-01/design.log` |
| Ruff完整待提交树 | exit0;`ruff-01/ruff.log`,索引导出不混入用户既有改动与草稿 |

`audit.json`确认Policy逐字节相同、installGuards仅有类别参数差异;冻结稿与专用库
hash均仍匹配任务指定值。trace不写原始异常文本、协议事件或任何凭据。

每个本机故障探针的命令、exit、固定stderr、服务端请求清单、结果JSON及agent trace
均单独归档。测试配置不接触专用库;本机正常/故障四例均确认合成state DB原字节不变。
WORKER_BLOCKED是允许枚举且已测传播;成功关闭暂停Worker仍不停止,失败仍走原有
WORKER_NOT_PAUSED/CLOSE_TARGET_FAILED条件,不为凑类别而新增停止行为。
首轮新增测试曾把fetch的既有QB_FETCH_FAILED映射写成QB_BROWSER_UNAVAILABLE,
已修正测试期望,未改生产映射;进程退出测试先关闭输入管道避免制造额外缓冲区错误。
初始记录入口full-01路径定位错误,pytest未启动;修正记录脚本后full-02完整执行。
这些修正只涉及本轮工具/测试,不把失败尝试计作通过。

代码门禁通过后先提交推送;环境检查和一次真机诊断另记。仍无新真实QB请求、
无Gerrit推送、无专用库写入。冻结稿未变,成功/BUILD_NOTES样本仍挂账,不进入C6b。

### 40.4 环境检查与残留清理

代码及离线证据提交`c88142b`,已推送origin/clang-fix-campaign,然后执行:

```bash
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/diagnostic-preparation/environment_audit.py --clean --output docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/diagnostic-preparation/environment.json
```

exit0;2026-10-15T09:31:06Z至09:31:28Z。原始df/free输出、三次ps采样、
目录元数据与两次lsof检查结果见[environment.json](evidence/C6a/diagnostic-preparation/environment.json)。

- `/dev/shm`:16G,已用119M,可用16G;`/home`在`/dev/sda1`,1.8T,已用1.4T,可用396G(78%)。
- 内存30Gi,available15Gi;swap4.0Gi,已用4.0Gi,可用8.3Mi。仅记录,不将可用内存等同于整机无负载。
- 10秒间隔三次D状态计数为1/1/2。PID1239372的`kworker/u81:1+i915_flip`三次均在;
  `jbd2/nvme0n1p1-8`只在第三次出现。wchan只可见0,未进一步推断内核原因。
  没有观察到`/home`所在sda1关联任务持续三次D状态,不满足本任务的持续磁盘阻塞闸门;
  这不是“没有任何D状态”或“机器完全空闲”的结论。
- `/dev/shm/p5q-browser-NJmrwJ`:7953928字节,mtime2026-10-15T07:59:47.970001Z;
  `/dev/shm/p5q-browser-q8VW3u`:18字节,mtime2026-10-14T07:02:58.657438Z。
  两者uid1000、两次lsof均无引用/无警告,记录后已删除;总计7953946字节,约7.59MiB。
  不读取或归档目录内容,未删除其它路径。
- 环境检查前后专用库hash均为bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405。

### 40.5 一次真机诊断人工闸门

当前WAITING_START,`diag-01`尚未创建或执行。拟执行命令:

```bash
.venv/bin/python docs/clang-fix-campaign/spikes/p5q_c6_driver_probe.py --config /home/linhao/Toolchain/p5q-live-validation/p5q-c6/config.yaml --output docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/diag-01
```

只login/open_form/fill/close,不提交、不产生构建、不运行真实qb-trigger/qb-result-fetch,
不写专用库。请求FatTank新回复“开始”后才运行一次;600秒内只在窗口登录,登录后
不点击其它内容、不打开新标签页/窗口。任何结果都停止,不重跑、不进入真实提交。
本轮未发现冻结稿/裁定的新增不一致或做不到之处。真机结果仍NOT_RUN,不得以离线
四例代替diag-01实测。成功/BUILD_NOTES样本与C6b仍未关闭。

### 40.6 diag-01一次执行与停止记录

§40.5为执行前状态。环境证据提交`471b0a8`已推送后,FatTank新回复原文“开始”。
随后按§40.5原命令仅执行一次,未带测试参数;执行前专用config与C6准备归档逐字节
一致,新目录不存在,专用库及冻结稿hash均符合指定值。没有重复真实提交授权。

2026-10-15 17:39:48至17:41:40(Asia/Shanghai;原始JSON保留UTC),探针exit5。
命令与exec输出记录见[command.json](evidence/C6a/diag-01/command.json),
未修改的探针输出见[result.json](evidence/C6a/diag-01/result.json)。

| 命令 | 结果 | 秒 | failure_category | 代理退出码 |
|---|---|---:|---|---|
| login | ok | 58.354 | null | 当时未退出 |
| open_form | ok | 2.429 | null | 当时未退出 |
| fill | ok,12字段读回与指纹符合 | 15.957 | null | 当时未退出 |
| close及进程清理 | QB_BROWSER_UNAVAILABLE | 35.070 | null | -15 |

fill实际参考快照为`tizen-base-toolchain_20260924.094908`;目标为已批准libtirpc行,
BUILD NOTES为probe专用标记。`release_state=not_released`,`form_action_releases=0`,
`state_db_access=false`;未运行真实qb-trigger/qb-result-fetch,无提交、无Gerrit推送。

driver trace显示close协议应答ok;随后驱动等待进程退出,清理耗时35秒并最终得到
-15(SIGTERM)。探针因非零退出码构造QB_BROWSER_UNAVAILABLE,而不是收到代理失败
应答,因此failure_category为null。未观察到QB_AGENT_STOPPED固定行;不伪填类别。
四命令全ok的验收未通过,立即停止,不重跑、不实施额外修复。

停止报告见[stop-report.md](evidence/C6a/diag-01/stop-report.md)。生产main与本机测试
入口的stdin清理不同,提供待验证的生命周期候选原因,不是已确认根因;也不能据
本次前三步成功推断live-03原故障原因。后续候选为先离线复现实际生产入口的退出
行为,由设计方裁定最小修复。冻结稿未改,本轮不改变任何退出/放行/拒绝逻辑。

收尾仅新增脱敏证据和progress/INDEX;离线证据核对命令:

```bash
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6a/diag-01/validate_evidence.py
```

结果见[validation.json](evidence/C6a/diag-01/validation.json):结构化输出、读回/指纹、
写后自检及原字节hash复核,只读文件不打开数据库;另执行探针静态护栏、design检查
和diff检查。专用库hash仍为bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405;
冻结稿仍为f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c。
全仓2680/1、Node362/0、四组安全4/4仍是§40.3代码提交前的本轮实跑结果,
本次证据收尾不冒称又跑了一遍。成功/BUILD_NOTES样本与真实提交仍挂账;不进入C6b。
收尾静态护栏1 passed/0 failed/0 skipped,design 0 problem、Ruff、diff检查均exit0;
目录元数据检查未发现剩余p5q-browser目录,没有追加清理。新离线记录脚本首次检查
出现3条E501及设计检查器缺少路径参数,已仅修正记录脚本后重跑;原始失败摘要保留
在[initial-validation.json](evidence/C6a/diag-01/initial-validation.json),不改生产代码或检查器。
新增证据逐文件字节自检通过;把整份progress当HTML证据检查会命中早先裁定原文里的
禁止键名示例,父版本同样被拒且该历史行未变。本次新增文档文字单独检查通过,
未删改历史原文或放宽检查器,见[scoped-self-check.json](evidence/C6a/diag-01/scoped-self-check.json)。

## 41. 实施裁定 P5Q-C6A-04:diag-01 结论与关闭后进程不退出的处理

### 41.1 裁定原文

1. diag-01 证明:生产 Python 驱动 → 生产代理 → 真机 QuickBuild 这条路径的 login、open_form、fill 均成功,12 个字段读回相符,放行 0 次。live-03 的失败未复现;生产诊断信息(停止类别)已生效,如再出现即可定位。
2. 关闭后进程不退出,判定为已知缺陷:生产代理主循环在收到 close 后,没有像测试入口(tests/node/p5q_cli_agent.mjs:37)那样销毁标准输入;同时 Python 驱动 qb_browser.py 在 wait 之后才关闭标准输入。两边互相等待,直到 35 秒超时后 SIGTERM。测试入口与生产入口不一致,是该缺陷未被测试发现的原因。
3. 该缺陷只发生在全部工作完成并落库之后。QbBrowser.close 遇到超时只会终止进程,不抛出异常,不改变 qb-trigger 与 qb-result-fetch 的 stdout 与退出码,因此不阻断 C6a 真实提交。C6a 执行时出现"close 后约 35 秒、代理退出码 -15",按已知缺陷记录,不作为停止条件。
4. 修复安排在 C6a 提交之后、C6b 之前的离线修复轮,另行下达任务。本任务不改任何代码。

### 41.2 执行边界

上述为本轮设计方裁定,不重写diag-01原始证据或先前的候选根因说明。本任务不改
生产代码、取证工具、测试、冻结稿或设计正文;不在本轮实施退出修复。
仅将该已知关闭表现从停止条件中排除,其它异常仍立即停止、不重试。
本轮最多一次qb-trigger,绝不带--retrigger,不推送Gerrit,不点Accept/Ready to Accept。
提交成功才执行一次规定的qb-result-fetch;终态读取和收口仍属于C6b。

## 42. C6a 第四次执行

### 42.1 前置核对与当前状态

开工HEAD为`c677504`,已读§38–40与diag-01/stop-report.md。
2026-10-15 18:02:09(Asia/Shanghai)只读核对通过,证据为
[live-04/preflight.json](evidence/C6a/live-04/preflight.json):

- 专用库读取前后SHA256均为
  `bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405`。
- campaign_qb_requests、campaign_qb_profiles、campaign_qb_events各0行;
  unit `p5q-c6-libtirpc-20261015`最新状态为SANDBOX_PUSHED。
- `/dev/shm/p5q-browser-*`为0个;无生产代理、Playwright Chromium或带P5Q profile
  参数的残留进程。只检查/proc元数据,不输出原始argv或凭据;无权限读取失败。
- 另有日常Google Chrome及VS Code crashpad进程,exe分别在`/opt/google/chrome/`
  和`/snap/code/`,全部无P5Q profile标记;不将它们称为本任务残留,未关闭或改动。
- 专用config与准备阶段归档逐字节一致;权威冻结稿SHA256仍为
  `f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`。
- live-04在检查前不存在;本次仅新建前置核对证据,未启动浏览器、未访问QB、
  未运行qb-trigger/qb-result-fetch、未写状态库。

状态WAITING_SUBMIT_CONFIRMATION。旧“确认提交”和“开始”均不复用。
本轮前置核对不代表真实提交已经发生;确认等待期间不保持任何浏览器或执行会话。

### 42.2 十二字段、路径与待执行命令

配置`root/CI_TIZEN/TIZEN/Tizen/Tizen-Base-Toolchain/RBS/TRIGGER`,overview_id=1917。
这次将真实产生一个约24小时的Full构建,不是演练。拟填值保持§38.5:

| 字段 | 拟填值 |
|---|---|
| BUILD_TYPE | Full |
| REPO_TYPE | ALL |
| BUILD_REFERENCE | Ref. Snapshot |
| SNAPSHOT_NUM | @freeze:取实际填表时唯一选中项并冻结,不预设历史值 |
| PROJECT_BRANCH | tizen_base |
| Immediate Stop With Error | true/勾选 |
| CHILD_CONFIGURATIONS | [standard-armv7l:aarch64:x86_64] |
| Build Package List | platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0 |
| Add Package List | 空串 |
| Remove Package List | 空串 |
| TARGET_IMAGE | []/空 |
| BUILD NOTES | clang-fix-campaign request=<生产命令将生成的request_id> |

专用目录`/home/linhao/Toolchain/p5q-live-validation/p5q-c6/`,
数据库`state.db`,配置`config.yaml`,state-root为`state/`,workspace为`ws/`,
只读远端核对使用`remotes/platform/upstream/libtirpc`本地镜像。
收到新的“确认提交”后,实际生产argv必须与live-01一致:

```bash
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python -m ci_triage qb-trigger --verification-ids p5q-c6-libtirpc-20261015-v0,p5q-c6-libtirpc-20261015-v1,p5q-c6-libtirpc-20261015-v2 --state-db /home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db --state-root /home/linhao/Toolchain/p5q-live-validation/p5q-c6/state --config /home/linhao/Toolchain/p5q-live-validation/p5q-c6/config.yaml
```

启动环境与live-01保持一致,输出记录到新目录live-04。既有run_c6_once.py只接受
live-01至03;不修改它,确认后由命令执行层按同一生产argv记录本次输出。
FatTank只在弹出的窗口中登录,须在600秒内完成;登录后不点击其它内容、不打开
新标签页。结束时浏览器关闭后可能额外等待约35秒,按§41已知缺陷记录。
本次尚未收到确认、尚无request_id/构建号/stdout/父构建回显或状态迁移。

本准备提交仅本节/INDEX与前置证据,设计检查exit0/0 problem、diff检查exit0,
新证据与新增文档文字字节自检通过;见
[preparation-validation.json](evidence/C6a/live-04/preparation-validation.json)。
生产、测试、spikes、既有执行记录工具与冻结稿均零改动,未重跑全仓测试;
§40.3的2680/1仍作为历史代码验收记录,不冒称本次重跑。

### 42.3 2026-10-19重新核对与新授权

FatTank本轮确认原话为“确认提交”,并要求启动前重新只读核对、完整保留trigger/fetch
证据,以及成功提交后对变更的实际冻结快照做一次公共manifest GET并记录目标revision。
本次确认只授权live-04一次qb-trigger及成功后一次首次结果读取,不复用旧授权。

11:53:59至11:54:19(Asia/Shanghai)完成当场核对,
见[preflight-2.json](evidence/C6a/live-04/preflight-2.json)。
DB前后hash仍为bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405;
三张QB表均0行,unit最新SANDBOX_PUSHED;P5Q profile、代理、Playwright Chromium残留
均0。冻结稿hash与专用config均未变。间隔10秒的三次D状态采样全部0,无持续磁盘
阻塞,不触发等待机器空闲确认的闸门。free原文显示内存available12Gi、swap剩余478Mi;
/home为/dev/sda1,可用231G,/dev/shm可用16G。

接下来按§42.2完整生产argv仅运行一次,输出排他新建于live-04/trigger;成功后fetch
另存live-04/fetch。记录完整argv、UTC起止时间、exit、stdout/stderr、只读SQL导出与
DB hash;仅增加命令执行层的被动进程元数据观察,不修改代码或代理参数。
记录到本条时尚未启动命令,不得将授权/前置通过写成提交成功。

### 42.4 live-04一次生产执行与停止

§42.3后仅执行一次§42.2的生产argv,与live-01完整参数逐字相同。代码HEAD为
`6dc24e9`;生产模块、spikes、既有记录工具和冻结稿未改。输出落在
[live-04/trigger](evidence/C6a/live-04/trigger/),完整启动环境项与argv见command.json。
没有--retrigger、测试证书或DNS覆盖。没有运行qb-result-fetch或任何额外QB读取。

- 开始2026-10-19 11:55:15,结束12:05:59(Asia/Shanghai),JSON保留UTC。
- 生产CLI exit5,总耗时644.008秒;外层记录exit0仅表示证据保存成功。
- stdout:action=submit_failed,error_code=QB_LOGIN_TIMEOUT,status=SANDBOX_PUSHED;
  request_id/request_seq/qb_build_id/diagnostic_dir/message均null。
- stderr仅固定登录提示;配置600秒时限未缩短,没有提前中断或追加第二次调用。

生产trace新增的固定事实见[trace.jsonl](evidence/C6a/live-04/trigger/trace.jsonl):

```json
{"action":"BROWSER_COMMAND_FAILED","agent_error_code":"QB_LOGIN_TIMEOUT","agent_exit_code":null,"agent_exited":false,"command":"login","failure_category":null}
```

trace中的进程状态为login错误时的瞬间,不是清理结束后的退出结果。被动/proc采样
最后观察到Chromium为t=608.895秒,CLI结束t=644.008秒,尾段约35.113秒;与已知
关闭延迟一致,不作为额外停止原因。采样没有取得代理终态wait status,代理退出码
如实记NOT_COLLECTED,不能直接套用diag-01的-15;也没有直接的close调用计时。
本次停止原因是QB_LOGIN_TIMEOUT,不属于§41豁免的关闭表现。

没有request_id/提交意图或构建号,故按其它结果立即停止,不fetch、不人工绑定、
不重试。没有登录请求链或页面快照,不能断言人工未登录、窗口未弹出或检测器错误。
停止报告见[stop-report.md](evidence/C6a/live-04/stop-report.md)。

### 42.5 停止后状态、挂账与收尾

[stop-audit.json](evidence/C6a/live-04/stop-audit.json)确认:
DB hash仍为bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405,
只读SQL导出与live-01及本次归档逐字节一致,三张QB表仍0行,
状态历史仅SANDBOX_PUSHED。冻结稿hash不变;无P5Q代理/Playwright Chromium、
profile或.transport残留。检查可执行文件与参数项,不按shell命令正文子串误判。

| 项目 | 本次结果 |
|---|---|
| 新授权与当场前置 | 完成,preflight-2.json,三次D状态0/0/0 |
| trigger argv/起止/exit/stdout/stderr | 已保存,trigger/command.json、execution.json、stdout.json、stderr.txt |
| 执行后SQL与DB hash | 已保存,trigger/state-after.sql与execution.json |
| trace与清理表现 | 已保存trace.jsonl与process-observations.json;最终代理退出码未采得 |
| 提交落点、构建号 | NOT_COLLECTED,登录超时,未提交 |
| 父构建三项回显与请求标记比对 | NOT_COLLECTED,无父构建页/请求标记 |
| qb-result-fetch stdout与状态迁移 | NOT_RUN,无fetch目录,状态未迁移 |
| 本次冻结SNAPSHOT_NUM | NOT_CREATED,profiles为0行,不借用历史快照值 |
| 新快照manifest GET/revision比较 | NOT_RUN,“提交成功后”的条件未满足 |
| 成功样本/BUILD_NOTES样本/C6b | 仍挂账,本次不进入 |

HTTP请求总数没有采集,不伪填0。停止后无新增网络取证、无Gerrit推送。
首次停止后全/proc审计碰到系统进程权限限制和shell源码字符串误匹配,未修改生产或
运行规则;只读复核改为检查候选可执行文件及独立参数项,结果如上,未删除任何进程。
本次只改progress/INDEX和脱敏证据;收尾复跑设计检查与diff检查,逐文件字节自检,
结果见live-04/validation.json。不重跑全仓代码测试,§40.3仍为历史验收结果。

## 43. C6a 第五次执行

### 43.1 新授权与当场前置

live-04停止证据已由`c26922e`推送。FatTank随后说“重新弹出窗口”;已说明这会启动
新一次真实提交尝试、沿用原libtirpc目标与十二字段,旧确认不复用。FatTank再次回复
原文“确认提交”,据此只授权本轮live-05的一次qb-trigger及成功后一次首次fetch。
仍不带--retrigger、不推送Gerrit、不点Accept/Ready to Accept、不做代码修复。

2026-10-19 13:19:42至13:20:02(Asia/Shanghai)重新完成只读前置:
[live-05/preflight.json](evidence/C6a/live-05/preflight.json)。
专用库hash仍为bd4380eacf2409c40137ad8b648939261b3a3eebe20d4101a6e2269b2c4eb405;
QB三表各0行、unit仍SANDBOX_PUSHED;无P5Q代理/Playwright Chromium/profile残留,
冻结稿hash和专用config均未变。10秒间隔D状态0/1/0,仅第二次短暂出现
`kworker/u81:0+i915_flip`,没有持续D进程;不触发磁盘阻塞人工闸门。
内存available12Gi、swap剩余491Mi,/home可用231G,/dev/shm可用16G。

拟执行生产argv保持live-01及§42.2逐字相同;本次证据排他写入live-05/trigger,
成功后fetch写入live-05/fetch。保持600秒窗口内人工登录,已知关闭延迟按§41处理。
若本次冻结快照不是20260924.094908,成功提交后按上一轮补充要求做一次公共manifest
GET核对libtirpc revision,只记录、不改变判定。任何其它异常停止,不自行重试。
本条为启动前记录,尚不表示已产生请求或构建。

### 43.2 一次生产执行:提交落点未知

仅执行一次§42.2的生产argv,代码HEAD为`c26922e`,与live-01参数逐字一致。
未修改生产/取证/测试/记录工具或冻结稿,无测试参数、无--retrigger。
完整证据见[live-05/trigger](evidence/C6a/live-05/trigger/):command.json、execution.json、
stdout.json、stderr.txt、state-after.sql、process-observations.json。

- UTC开始2026-10-19T05:20:49.637083+00:00,结束05:22:03.444859+00:00;
  Asia/Shanghai为13:20:49至13:22:03,生产CLI耗时73.756秒,exit5。
- stdout:action=submit_uncertain,error_code=QB_SUBMIT_UNCERTAIN,status=QB_REQUESTED。
- request_id=`9fe02dc3927c4b7fa55a3dffce699d03`,request_seq=1,qb_build_id=null。
- sbs_target=`platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0`。
- 观察落点`/wicket/page`,未取得父构建号。stderr仅固定登录提示。
- 生产stdout的通用message中含--retrigger建议,本任务不执行,只走已批准的人工绑定分支。

trace-before.jsonl保留本次前的历史trace;trace-after.jsonl为执行后全量;
[trace-new.jsonl](evidence/C6a/live-05/trigger/trace-new.jsonl)仅本次新增两条:
first_freeze=true、snapshot_option_count=1、填表fingerprint,
以及observed=/wicket/page与相同request_id的提示。没有新增BROWSER_COMMAND_FAILED条目;
不能把trace-before中live-04的QB_LOGIN_TIMEOUT归于本次。
本次trace未记录failure_category或最终代理wait status,不推断这些值。

### 43.3 意图、快照与关闭表现

[pending-audit.json](evidence/C6a/live-05/pending-audit.json)为执行后只读复核:

- DB SHA256=`d1ff348dda02521b55759e92bc2dda360a268848012ae1741b9dc22b8bfe7140`,
  复核前后未变,SQL导出与trigger/state-after.sql一致。
- QB requests/profiles/events各1行。唯一事件为SUBMITTED(提交意图),尚无BUILD_BOUND/RESULT;
  状态从SANDBOX_PUSHED迁到QB_REQUESTED。不能以SUBMITTED行证明服务器已经创建构建。
- 本次实际冻结SNAPSHOT_NUM=`tizen-base-toolchain_20261013.024319`;
  profile_sha256=`c8504d8c2d0385c98cf71c2e4f79353492ef6230591b0dfecc36a194451bf69d`。
  它不同于原manifest核对的20260924.094908;新manifest GET待人工绑定确认构建后执行,
  只记录libtirpc revision比较,不改变判定。
- 请求标记应为`clang-fix-campaign request=9fe02dc3927c4b7fa55a3dffce699d03`;
  尚无父构建页面,BUILD_NOTES/BUILD_REFERENCE/SNAPSHOT_NUM实际回显均NOT_COLLECTED。
- 最后观察到本次Chromium为t=38.787秒,CLI结束t=73.756秒,尾段约34.969秒,
  与§41已知关闭延迟一致。未采到最终代理退出码,记NOT_COLLECTED,不套用-15。
- 复核没有P5Q代理、Playwright Chromium、profile或.transport残留;
  冻结稿SHA256不变。没有删除其它浏览器、目录或用户文件。

### 43.4 等待人工构建号

已在聊天请FatTank按完整BUILD NOTES请求标记查找RBS/TRIGGER父构建号,不要再次Run,
不要点击Accept/Ready to Accept;若未找到则如实回复,不猜号、不重提。
当前状态WAITING_MANUAL_BUILD_ID,尚未收到构建号,未运行qb-result-fetch,
没有fetch目录、额外QuickBuild页面访问或manifest GET,不进入C6b。
收到正整数构建号后才按原授权执行一次生产qb-result-fetch,使用--request-id与
--qb-build-id人工绑定并首次读取;证据另存live-05/fetch,不再调用qb-trigger。

等待报告见[pending-manual-binding.md](evidence/C6a/live-05/pending-manual-binding.md)。
本次只入库progress/INDEX与脱敏执行证据,不修改代码。收尾仅运行设计检查、diff检查、
逐文件写后字节自检,结果见live-05/validation.json;不重跑全仓代码测试,
§40.3的2680 passed/1 skipped仍为历史验收结果。

### 43.5 FatTank回复“未找到”:停止

2026-10-19,FatTank对按完整BUILD NOTES标记查找父构建号的问题回复原文:

> 未找到

§43.4及pending-manual-binding.md保留为当时的等待记录,现由本节更新为
STOPPED_BUILD_NOT_FOUND。没有取得正整数父构建号,不能执行人工绑定或首次fetch。
“未找到”是人工查找结果,不是服务器未创建构建的证明;服务器是否创建构建、
为何落在/wicket/page仍未知,不将QB_SUBMIT_UNCERTAIN改判为提交失败或成功。

只读复核专用DB SHA256仍为
`d1ff348dda02521b55759e92bc2dda360a268848012ae1741b9dc22b8bfe7140`,
与§43.3一致。保留QB_REQUESTED、request_seq=1、SUBMITTED提交意图与冻结profile;
没有清库、删除记录、回退状态或重提。冻结稿hash仍为
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`。
本回复后未启动浏览器,未访问QB或Gerrit,未运行trigger/fetch,未读取新快照manifest。
父构建回显、首次fetch、新快照revision比较和C6b继续挂账。

停止报告:[live-05/stop-report.md](evidence/C6a/live-05/stop-report.md)。
候选处理仅提交设计方:确定是否需要另行批准的只读取证或不提交诊断,以定位提交
落点未知的原因;不自行增加请求、修改规则或再运行提交。原始执行证据一律保留。
本次仅登记人工回复与停止状态,设计检查/diff检查/新增文字脱敏自检见
[manual-lookup-validation.json](evidence/C6a/live-05/manual-lookup-validation.json),
未重跑代码测试。

### 43.6 FatTank提供父构建号:人工绑定与首次读取准备

2026-10-19,FatTank补充提供原文“构建号是：1201886”,并给出以下页面信息:

| 用户提供字段 | 原文 |
|---|---|
| Build Package List | platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0 |
| Build Type | Full |
| Build Reference | Ref. Snapshot |
| Profile URL | http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261013.024319 |
| Base URL | http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/reference |
| Build Notes | clang-fix-campaign request=9fe02dc3927c4b7fa55a3dffce699d03 |

§43.5保留为此前人工查找结果;本次正整数父构建号解除人工绑定的输入缺口,
不把用户提供的表格冒充生产HTML取证。按既有QB_SUBMIT_UNCERTAIN分支授权,
只运行一次生产qb-result-fetch,以--request-id与--qb-build-id人工绑定并首次读取,
不再运行qb-trigger、不带--retrigger、不进入C6b。
启动前只读确认DB仍为d1ff348dda02521b55759e92bc2dda360a268848012ae1741b9dc22b8bfe7140,
request_seq=1仍仅SUBMITTED、状态QB_REQUESTED,专用config与准备归档一致,冻结稿hash未变。
预定命令及输出另存live-05/fetch,不改写trigger证据或既有停止报告。

```bash
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python -m ci_triage qb-result-fetch --request-id 9fe02dc3927c4b7fa55a3dffce699d03 --qb-build-id 1201886 --state-db /home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db --state-root /home/linhao/Toolchain/p5q-live-validation/p5q-c6/state --config /home/linhao/Toolchain/p5q-live-validation/p5q-c6/config.yaml
```

本条为准备记录,实际命令结果、数据库迁移及父构建回显须以随后证据为准。

### 43.7 人工绑定与首次读取完成

执行基线`8f66d7d`;生产代码、测试、spikes、记录工具、design.md和冻结稿均未改。
收到FatTank提供的1201886后,按§43.6命令只调用一次生产qb-result-fetch,
未调用qb-trigger、未带--retrigger或--accept-snapshot-drift,没有额外QB读取。
此次人工绑定与首次结果读取合为同一次命令,不再追加第二次fetch。

当场前置见[live-05/fetch/preflight.json](evidence/C6a/live-05/fetch/preflight.json):
DB仍为d1ff348dda02521b55759e92bc2dda360a268848012ae1741b9dc22b8bfe7140,
QB三表各1行、状态QB_REQUESTED,无P5Q代理/Chromium/profile残留;
10秒间隔D状态1/0/1,无持续D进程,冻结稿hash与专用config保持一致。
登录仅由FatTank在浏览器内完成,命令stdin为DEVNULL,无测试证书或DNS覆盖参数。

- UTC开始2026-10-19T05:57:35.892507+00:00,结束05:58:58.626026+00:00;
  Asia/Shanghai为13:57:35至13:58:58,耗时82.675秒,生产CLI exit0。
- 父构建1201886人工绑定成功;子构建1201889首次读取时已为Successful/PASS,
  terminal=true。按C6a“首次读取若已终态照实记录”的规则保留,不另起C6b轮询。
- 新事件:BUILD_BOUND(event_id=2)、RESULT(event_id=3,status=PASS);
  状态QB_REQUESTED → QB_TRIGGERED → SANDBOX_QB_PASS,未经过SANDBOX_QB_PENDING。
- 完整stdout、stderr、argv、UTC起止、exit、SQL与hash见fetch/。
  [stdout.json](evidence/C6a/live-05/fetch/stdout.json)原文:

```json
[{"child_build_id":"1201889","diagnostic_dir":null,"error_code":null,"message":null,"qb_build_id":"1201886","qb_result_path":"qb_results/9fe02dc3927c4b7fa55a3dffce699d03/20261019T055823425754Z.json","request_id":"9fe02dc3927c4b7fa55a3dffce699d03","result_event_id":3,"status":"PASS","terminal":true}]
```

四个页面均通过生产读取核对与脱敏,已按原字节复制到fetch/state/qb_evidence/:

| 页面 | 归档文件 | 登记位置外身份计数 |
|---|---|---|
| /build/1201886/overview | 01.1201886-overview.html | 0 |
| /build/1201886/variables | 02.1201886-variables.html | 0 |
| /build/1201889/overview | 03.1201889-overview.html | 0 |
| /build/1201889/variables | 04.1201889-variables.html | 0 |

原始状态目录路径与归档hash逐项见[fetch/analysis.json](evidence/C6a/live-05/fetch/analysis.json)。
未读取step_status(不是终态失败)、未点Accept/Ready to Accept,未做Gerrit推送。
业务页共4个,未采集登录/静态资源等全部HTTP请求数,不把4写成总请求数。

### 43.8 父子回显与新快照manifest

下面是生产归档HTML经qb_result_html离线解析的事实,不是只引用用户表格。
父变量均在fetch/state/qb_evidence/9fe02dc3927c4b7fa55a3dffce699d03/
02.1201886-variables.html:810(三列表格在同一源行):

| 变量 | 回显原文 | 对照 |
|---|---|---|
| BUILD_NOTES | clang-fix-campaign request=9fe02dc3927c4b7fa55a3dffce699d03 | 与请求标记逐字相等,解码单元格无首尾空白、无换行、无截断 |
| BUILD_PKG_LIST_MODIFY | platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0 | 恰好一行,与目标逐字相等 |
| BUILD_REFERENCE | Ref. Snapshot | 与冻结profile相等 |
| SNAPSHOT_NUM | tizen-base-toolchain_20261013.024319 | 与实际冻结值相等(本项按设计只记录) |

子构建Summary Status=Successful;父Child Build表Build Result=SUCCESSFUL。
子BUILD_REFERENCE=Ref. Snapshot,子SNAPSHOT_NUM_URL为
`http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261013.024319`,
生产snapshot_kind离线复核为same,snapshot_drift_accepted=false;
EACH_GBS_BUILD_STATUS存在且为空。accepted=null,未推断人工Accept已发生。
这些是回显记录,不扩张为“服务端实际消费快照”之外的新判据。

按FatTank补充要求,对已变更的冻结快照只做一次普通HTTP GET,无重试、无重定向跟随:

```text
http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261013.024319/builddata/manifest/tizen-base-toolchain_20261013.024319_standard.xml
```

curl exit0、HTTP200;命令/起止/原始XML/项目元素/结构解析结果见
[manifest-20261013/result.json](evidence/C6a/live-05/manifest-20261013/result.json)。
XML SHA256=`a70c799cea8c9265a107154af818da0a5ff5cf533c94f65dd43e21d3a9b574eb`。
response.xml:97恰好一个对应project,原字节元素为:

```xml
<project name="platform/upstream/libtirpc" path="platform/upstream/libtirpc" revision="7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0"/>
```

revision仍等于目标commit;仅记录,未改变生产结果判定。

### 43.9 关闭表现、收尾与边界

最后观察到Chromium为t=47.633秒,CLI结束t=82.675秒,尾段约35.042秒,
与§41已知关闭缺陷一致。未采得代理最终wait status,退出码仍如实记NOT_COLLECTED,
不将CLI exit0或历史-15当作本次代理退出码。本轮不修复。

[fetch/post-audit.json](evidence/C6a/live-05/fetch/post-audit.json)确认无代理、Playwright
Chromium、profile或.transport残留,DB hash为
`08ed202e69a73a480e7282a198565f32adae8157a332804df4df970238eacd30`,QB三表为1/1/3。
RESULT文件SHA256为`feebbbe78c7bb2444dcb46a50a5b1bda7584d34e275a2dcea710c45e3415932b`,
与数据库event_id=3一致。原文件及四页证据按字节归档,SQL导出只读取得,
不提交二进制state.db或任何凭据。trigger与先前停止证据一律原样保留。

| 项目 | 当前状态 |
|---|---|
| 本次真实提交的构建身份 | 已由父页核对、人工绑定与BUILD_BOUND确认,1201886 |
| C6a首次fetch | 已完成,子1201889首次已PASS,RESULT=3 |
| 父回显与请求标记/冻结值 | 一致,四页身份计数均0 |
| 变更快照manifest核对 | 一次GET/200,libtirpc revision一致 |
| 成功样本与非空BUILD_NOTES样本 | 新证据已取得;正式挂账核验及收口交后续C6b,不在本轮标CLOSED |
| 关闭缺陷修复 | 按设计方安排另行离线任务,本轮未实施 |
| C6b | 未进入,不因首次已终态而追加读取或自动收口 |

无新的冻结稿/裁定不一致;提交落点unknown的人工绑定分支及已知关闭延迟均按既有规则
处理。本次只改文档/INDEX与证据,收尾设计检查0 problem、diff检查、逐文件脱敏自检
见[fetch/validation.json](evidence/C6a/live-05/fetch/validation.json)。未重跑全仓代码测试,
历史2680 passed/1 skipped不冒称本轮结果。

暂存区补充核验:`git diff --cached --check`返回2,仅四份原字节HTML的行尾空白/缩进
告警;保持取证字节不改。排除这四份原始HTML后,其余全部待提交文件的同一检查返回0。
完整告警、路径归属与原文件hash复核见fetch/staged-validation.json及其输出日志;
不将完整暂存区检查声称为0,不修改git规则以隐藏告警。

## 44. 实施裁定 P5Q-C6A-05:修复关闭后进程不退出、补登录诊断

### 44.1 裁定原文

1. C6a 已由 live-05 完成:父构建 1201886 经人工绑定,子构建 1201889 首次读取即 PASS。仍有两项待修:
   a. 关闭后进程不退出(P5Q-C6A-04 登记的已知缺陷),每次 CLI 结束多等约 35 秒并以 SIGTERM 结束代理;
   b. 登录阶段没有诊断信息,live-01、live-04 两次登录超时无法区分原因。
2. 批准对生产代码做以下最小改动,不改变任何放行、拒绝或判定逻辑,不改冻结稿:
   a. 关闭修复:生产代理主循环结束后销毁 process.stdin,确保收到 close 后进程自行退出;Python 驱动 QbBrowser.close 在写出 close 命令后立即关闭 stdin,再 wait。删除测试入口 tests/node/p5q_cli_agent.mjs 中专门为退出而做的 stdin 销毁,使测试入口与生产入口的退出行为一致。
   b. 登录诊断:代理的 login 在返回 QB_LOGIN_TIMEOUT 或 QB_LOGIN_ABORTED 时,应答增加 login_facts 对象,键集合固定为:
      - final_path_shape:用现有 pathShape 处理当前页面路径;
      - on_signin、password_present、sign_out_present:最后一次检查时三个登录条件各自的布尔值;
      - checks:检查次数;
      - login_posts_released:登录 POST 的放行次数;
      - login_channel_closed:登录通道是否已关闭;
      - denied:登录阶段被拒请求的计数,按 pathShape 分组。
      不含任何查询值、请求头、请求体、账号、密码或 Cookie。Python 驱动严格校验 login_facts 的键集合与类型,不合格按协议错误处理;qb-trigger 与 qb-result-fetch 把它写入 trace。
3. 以上改动涉及代理文件,四个拦截安全组必须从头重跑;第 9.2 节静态断言全部通过。

### 44.2 执行范围与计划

基线243df59。已读§38–43及diag-01/live-04停止报告。冻结稿SHA256仍为
`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`;
专用库`/home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db` SHA256仍为
`08ed202e69a73a480e7282a198565f32adae8157a332804df4df970238eacd30`。
本轮仅离线修复与本机假HTTPS测试,不访问真实QuickBuild、不登录、不写专用库,
不做Gerrit推送、不进入收口。Policy/installGuards判定逻辑保持原样。

- DONE:生产入口退出回归、Python先关stdin、测试入口去掉退出特例。
- DONE:四种登录事实、严格协议校验、两个CLI trace核对;focused-01为242 passed。
- DONE:全仓2709 passed/1 skipped/0 failed;Node单元及静态负例362 passed,
  mypy/ruff/lint-imports/design检查通过,四组安全测试4/4,hash复核通过。

证据目录:`evidence/C6a/offline-fix-01/`。已有与本任务无关的工作区变更保留不动。

### 44.3 实现与诊断口径

生产改动仅`qb_browser_agent.mjs`与`qb_browser.py`:
main的finally清理后销毁stdin;Python写close后关闭管道再wait;
测试入口删除stdin.destroy,额外的关闭计时只在测试入口记录。
login保留原有成功条件,复用最后一次隔离环境检查的三个布尔值,
在关闭页面及离开login阶段之前记录路径形态、POST计数、通道状态和DENIED分组。
没有新增网络请求、页面取数或判定条件。若连一次检查都未完成,checks=0,
三个布尔值初始为false,不把它们解释为已检查到页面不存在对应元素。

Python对键集合、布尔值、非负整数与现有pathShape输出集合严格校验,
非法诊断不回显。新增login_facts仅在login超时/中止应答中接受。
两个CLI已有的BROWSER_COMMAND_FAILED trace统一调用failure_facts,
通过它传递已校验对象,CLI stdout与两个CLI模块本身不变。

离线四场景:停留signin、POST302到未登记路径、POST302到dashboard但没有Sign Out、
关闭窗口;前三项TIMEOUT,最后ABORTED/PAGE_CLOSED。未登记跳转被拒后浏览器错误页
的pathname为`/`,故final_path_shape为`/`,拒绝项另按`<other>`记1次;
不据此误称登录到了站点首页。每项仅合成账号、密码与会话值,输出无残留。

baseline-close复现生产代理收到close成功应答仍超过5秒不退出(预期红)。
close-fixed中的首次驱动测试遇到本轮诊断解析变量顺序错误,已修正;
focused-01两项退出测试均绿,未调用terminate。临时Node命令误用了相对路径,
未执行任何Node测试;随后node-unit用绝对路径实跑362/0/0。
正式门禁以本节最终结果和各command.json为准,不以中间试跑替代。

### 44.4 最终验收与关闭耗时

状态:`C6a_OFFLINE_FIX_VERIFIED`,不进入C6b或收口。本轮新增29个pytest用例,
基线2680 passed/1 skipped,本轮2709 passed/1 skipped/0 failed。
唯一skip为既有`test_case_insensitive_bypass_is_platform_specific`,
不是Node、浏览器或本轮新增用例。完整argv、UTC时间、exit和输入hash见每个
command.json;[summary.json](evidence/C6a/offline-fix-01/summary.json)为机械汇总。

| 门禁 | 本轮结果 | 证据(相对offline-fix-01/) |
|---|---|---|
| pytest全量 | 2709 passed / 1 skipped / 0 failed, exit0 | full/output.log、full/pytest.xml |
| 定向回归 | 242 passed / 0 failed, exit0 | focused-01/output.log |
| Node单元与§9.2静态负例 | 362 passed / 0 failed / 0 skipped, exit0 | node-unit/output.log |
| 本机登录四场景 | 4 passed / 0 failed / 0 skipped | full/artifacts/login-*.json、full/output.log |
| mypy | 116 source files, exit0 | mypy/output.log |
| ruff完整待提交树 | All checks passed, exit0 | ruff-final/output.log、command.json |
| lint-imports | 6 kept / 0 broken, exit0 | lint-imports/output.log |
| design.md检查 | 0 problem, exit0 | design/output.log |
| 四组拦截安全测试 | 4 passed / 0 failed, exit0 | safety/output.log、command.json |

四组独立重跑,全量pytest中也重新运行。Worker/WebSocket组走已批准分支b:
shared_worker closeTarget成功,worker closeTarget抛Error;
runtime.failure=QB_BROWSER_UNAVAILABLE/category=CLOSE_TARGET_FAILED,
浏览器已关闭、临时目录已删除,攻击HTTP=0、WS握手=0。
307/308均拦下、302对照放行;逐跳禁路请求及POST重放均0;
凭据隔离的合成会话、授权与密码不进入协议输出,ADAPT_FAILED注入按预期停止。
没有为此放宽任何原有判据。

关闭耗时分别记录,不混用:

| 测量 | 修复前 | 修复后(全量运行) | 证据 |
|---|---|---|---|
| 生产入口close应答后,保持stdin打开等待退出 | 5秒内不退出(预期红) | 0.015秒,exit0 | baseline-close/、full/artifacts/production-close.json |
| 实际QbBrowser.close,已完成启动 | diag-01为35.070秒、exit -15 | 0.114秒,exit0,terminate调用0次;wait前stdin已关闭 | full/artifacts/driver-close.json |
| qb-trigger关闭命令开始至CLI退出 | live-05尾段约34.969秒,未采代理退出码 | 0.127秒,CLI exit0 | full/cli-artifacts/build/commands.json |
| qb-result-fetch关闭命令开始至CLI退出 | live-05尾段约35.042秒,未采代理退出码 | RUNNING读取0.129秒、PASS读取0.124秒,均exit0 | 同上 |

历史live-05的数值只是进程观察尾段,不冒称直接测得的close耗时或代理-15。
修复后实际生产入口退出0由专门回归证明;CLI计时来自仅测试入口增加的时间戳,
生产代码不加入测试计时开关。原C5a四种落点模式及原诊断用例全部通过。

### 44.5 落点、边界与交付

- `qb_browser_agent.mjs:642`:保留登录判定并记录最后检查;
  `:674`汇总login_facts,`:996`生产主循环退出后销毁stdin。
- `qb_browser.py:97`:固定键/类型/路径形态校验;
  `:176`解码保存,`:76`统一failure_facts透传,`:399`先关闭stdin再wait。
- 两个CLI沿用既有`qb_trigger.py:291`的统一失败trace入口;
  `qb_result_fetch.py:603`登录失败也走同一入口。两个CLI文件原字节不变,
  `test_cli_login_facts_trace`四例验证timeout/aborted分别落盘、stdout不增字段、库不写。
- `tests/node/p5q_cli_agent.mjs`删除退出特例;新增实际生产入口测试,
  `tests/node/test_qb_login_facts.mjs`覆盖四种真实本地浏览器场景。

summarize.py逐字节核对Agent之前的整个源码前缀(含Policy、installGuards、pathShape)
与243df59一致,hash为`40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16`。
冻结稿、design.md和专用状态库均保持原hash,没有真实QB/Gerrit操作或真实状态库写入。
原有与本轮无关的工作区变更未纳入提交。
与冻结稿或裁定新发现的不一致/做不到之处:无。新停止报告0条。
完整入口见[证据索引](evidence/C6a/offline-fix-01/README.md);本轮结束,等待下一任务。

暂存核验补记:完整`git diff --cached --check`为exit2,仅baseline-close/close-fixed
两份原始失败日志及八份合成overview HTML的原字节行尾空白;
不改写证据、不改检查器。排除原始log/html后的同一检查exit0。
完整输出与命令见offline-fix-01/staged-diff及staged-nonraw;本轮要求的全部门禁仍为exit0。

## 45. 实施裁定 P5Q-C6B-01:C6b 范围与两项决定

### 45.1 裁定原文

1. FatTank 于 2026-10-19 作出两项决定:
   a. 提交后落点不明时,由工具自动查找构建号并绑定。此功能纳入 P5Q,由设计 v1.6 规定。v1.6 经三方评审冻结并实现,再经一次验证性真实提交,之后 P5Q 才能 CLOSED。本轮不实现。
   b. 快照判据(冻结稿第 9.4 节第 2 步要求的 R1 决定)。依据:1201886/1201889 实测,Ref. Snapshot 模式下,父构建回显的 SNAPSHOT_NUM、冻结值、子构建 SNAPSHOT_NUM_URL 的最后一段三者相同。决定:
      - 子构建快照地址按现行规则正式作为判据:最后一段等于冻结值时照常落库;同形态但不相等为快照漂移,默认停止,可对单个 request 人工接受;其它不符一律停止;
      - 父构建 SNAPSHOT_NUM 继续只记录,不作判据;
      - 本轮不改代码;停止提示里"须取一个以 Ref. Snapshot 提交的子构建样本后按 R1 定判据"这句,留到 v1.6 实现时修改。
2. C6b 范围:
   a. 对已绑定的 request 9fe02dc3927c4b7fa55a3dffce699d03 做一次真机终态重读;
   b. 用现有比对工具,对成功样本做原始正文与活动文档比对(冻结稿第 9.4 节第 1.6 步 a"找到成功样本时一并覆盖"),同时取一份新的配置页 1917 样本供 v1.6 设计;
   c. 正式关闭成功样本与 BUILD_NOTES 样本两个挂账项,写 C6 阶段小结。
3. 9cc481f 验收的三点备注,只记录,不改代码:
   - login_facts 的 final_path_shape 为"/"时,可能是跳到未登记地址后的浏览器错误页,必须和 denied 里的 <other>、login_channel_closed 一起看,不能理解为登录到了首页;
   - QbBrowser.close 会两次关闭 stdin,无害;
   - 关闭修复和 login_facts 由本轮真机重读做首次真机核对。

### 45.2 执行计划与边界

执行基线9cc481f。已读§5、§43–44及p5q_compare_raw_active.md;
冻结稿SHA256为`f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c`。
本轮不改生产代码、取证工具、design.md或冻结稿。只执行一次生产终态重读,
随后仅在前项符合预期时执行一次五页原始正文/活动文档比对。每次浏览器启动前重新
归档只读前置;任何异常停止、不重试。当前两项均PENDING,不提前关闭样本挂账。
证据目录为`evidence/C6b/`;不提交state.db二进制或任何凭据。

### 45.3 一次生产终态重读

两次操作均在聊天预告后由FatTank在窗口内登录,不读终端输入。
各自启动前重新检查专用库SHA256、三表1/1/3、SANDBOX_QB_PASS、无P5Q代理/
Playwright Chromium/profile/.transport残留及冻结稿hash,全部通过。
前置文件分别为`evidence/C6b/reread-01/preflight.json`与
`evidence/C6b/raw-active-execution-01/preflight.json`。

```bash
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python -m ci_triage qb-result-fetch --request-id 9fe02dc3927c4b7fa55a3dffce699d03 --state-db /home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db --state-root /home/linhao/Toolchain/p5q-live-validation/p5q-c6/state --config /home/linhao/Toolchain/p5q-live-validation/p5q-c6/config.yaml
```

UTC 2026-10-19T07:16:07.430044+00:00至07:16:32.790632+00:00,exit0,
stderr仅一行固定登录提示。stdout仍为PASS、terminal=true、parent1201886/child1201889、RESULT event_id=3,
指向既有`qb_results/9fe02dc3927c4b7fa55a3dffce699d03/20261019T055823425754Z.json`。
完整原文见[reread-01/stdout.json](evidence/C6b/reread-01/stdout.json)。
DB执行前后均为`08ed202e69a73a480e7282a198565f32adae8157a332804df4df970238eacd30`,
三表仍1/1/3,最新状态仍SANDBOX_QB_PASS。没有新事件,accepted仍null;
既有RESULT复用路径为`qb_result_fetch.py:500–506`,未触发accepted变化追加分支。

qb_evidence新增且仅新增四份05.1201886-overview.html、06.1201886-variables.html、
07.1201889-overview.html、08.1201889-variables.html;qb_results新增保留文件0,
既有文件无改写/删除。四条新增trace均outside_identity_count=0。
原字节证据、逐文件hash、trace前后与增量、只读SQL导出在reread-01/。
生产命令由仓库外执行记录器直接Popen,只清除与旧轮次相同的凭据/调试环境变量,
不注入代理参数、不包装或改写生产代码。每个命令均只运行一次。

进程观察每0.1秒采样,最后观察到Chromium为t=25.098941秒,CLI结束t=25.311512秒,
尾段0.212571秒。代理最终退出码未直接采到,如实记NOT_COLLECTED,不从CLI exit0推断。
执行后无残留。登录成功,未产生login_facts;本轮不能把登录失败事实字段称为已触发
真机验证,其格式和失败场景沿用§44离线验收。

### 45.4 成功样本五页比对与配置页摘录

```bash
/home/linhao/.local/bin/node docs/clang-fix-campaign/spikes/p5q_compare_raw_active.mjs --path /build/1201886/overview --path /build/1201886/variables --path /build/1201889/overview --path /build/1201889/variables --path /overview/1917 --output docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6b/raw-active-01
```

目录首次执行前不存在。UTC07:16:49.567295至07:17:31.919075,exit0,
run.json=PASSED,login/5次read/close均ok。stdout为空,stderr仅一行固定登录提示;
专用DB前后仍为上述08ed202e…acd30,三表1/1/3,专用state目录无新增/修改/删除文件。
记录器关闭尾段0.318026秒;代理退出码NOT_COLLECTED,这不是直接close调用计时。

| 页面 | 证据序号 | 导航核对 | 十项比对 | 身份计数raw/active |
|---|---|---|---|---|
| /build/1201886/overview | 01 | VERIFIED | 10/10一致 | 0/0 |
| /build/1201886/variables | 02 | VERIFIED | 10/10一致 | 0/0 |
| /build/1201889/overview | 03 | VERIFIED | 10/10一致 | 0/0 |
| /build/1201889/variables | 04 | VERIFIED | 10/10一致 | 0/0 |
| /overview/1917 | 05 | VERIFIED | 10/10一致 | 0/0 |

十项为navigation、summary、child_build、variables、configuration_tabs、breadcrumb、
copy_path、build_name、failed_steps、error_message;不适用的项目在两侧均为空,
不把空项说成读取到了字段。逐页逐字段事实见raw-active-01/NN.comparison.json;
表格见[C6b/README.md](evidence/C6b/README.md)。

1917的Build Requests共1行,Recent Builds共10行。1201886只出现在Recent Builds
第2行(raw-redacted:971,构建链接:983),不在Build Requests中。
逐行全量摘录、表头、链接、状态class、Begin Date/Duration见
[configuration-1917.md](evidence/C6b/configuration-1917.md)。
两表HTML均非逐字一致:活动文档在change/下拉菜单锚点增加
`popup-trigger close popup-target` class。单元格文字、构建链接及状态class一致,
完整差异见configuration-tables.diff;这里仅记录,不据此修订v1.6或声称整表字节一致。
本轮工具规定的十项比较没有该差异;成功样本四页的全部规定字段均一致。

### 45.5 挂账关闭表

以下每条均引用live-05与本轮raw-active双份证据,不是仅依据RESULT复述。
旧文件基址为`evidence/C6a/live-05/fetch/state/qb_evidence/9fe02dc3927c4b7fa55a3dffce699d03/`,
新文件基址为`evidence/C6b/raw-active-01/`;行号指原字节HTML。

| 项目 | 事实与结论 | live-05来源 | C6b来源 |
|---|---|---|---|
| 成功子构建Summary | Successful,归一PASS | 03.1201889-overview.html:830 | 03.raw-redacted.html:830 |
| 父Child Build结果 | SUCCESSFUL,指向1201889 | 01.1201886-overview.html:891 | 01.raw-redacted.html:891 |
| EACH_GBS_BUILD_STATUS | 存在,单元格原文为空 | 04.1201889-variables.html:802 | 04.raw-redacted.html:802 |
| 父SNAPSHOT_NUM | tizen-base-toolchain_20261013.024319 | 02.1201886-variables.html:810 | 02.raw-redacted.html:810 |
| 子SNAPSHOT_NUM_URL | http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261013.024319 | 04.1201889-variables.html:802 | 04.raw-redacted.html:802 |
| 快照关系 | 父回显=冻结值=子URL末段;snapshot_kind=same;父回显仍只记录 | 上述父子变量页及live-05/fetch结果JSON | 上述父子变量页及C6b/offline-analysis.json |
| BUILD_NOTES | clang-fix-campaign request=9fe02dc3927c4b7fa55a3dffce699d03;单元格文本及内部HTML逐字相等,无首尾空白、转义、换行或截断 | 02.1201886-variables.html:810 | 02.raw-redacted.html:810 |

成功样本挂账=CLOSED,BUILD_NOTES样本挂账=CLOSED;前提为本轮对应四页原始/活动
规定字段全部一致,已满足。解析用生产qb_result_html的parent_overview、child_overview、
snapshot_kind及HTMLParser源位置;完整事实、单元格原文与引用在offline-analysis.json。
离线摘录初稿错误假设td不带属性,在旧归档的`td class="vat"`处断言失败;
已改为按HTMLParser定位单元格内部原字节,核对值而非臆定标签写法后通过。
这不是生产/真机失败,未因此重读或修改任何页面/工具。

### 45.6 验收与边界

仅运行本轮要求的设计检查、diff检查、逐个新增文件原始字节脱敏自检及JSON字符串
递归检查;不重跑pytest、不将§44的2709/1冒称本轮结果。结果见C6b/validation.json。
冻结稿/design.md/生产代码/既有spikes均保持原字节,专用DB保持08ed202e…acd30。
没有qb-trigger、retrigger、accept-snapshot-drift、Gerrit推送或Accept操作;
除了两次授权只读浏览器操作,没有其它QuickBuild请求,没有重试。
新停止报告0条。配置两表HTML class差异仅按任务要求留档,不扩大样本关闭结论。

验收结果:design.md检查exit0/0 problem;新增证据逐文件原始字节及JSON递归脱敏检查
均通过。完整暂存区diff检查exit2,仅14份原字节HTML和configuration-tables.diff
的原始空白告警,最终加入原始检查输出log后共16份;不修改证据字节或检查规则。
排除原始HTML/diff及该原始输出log后的检查exit0。
命令、告警路径、逐文件hash见validation.json及gates/;最终暂存复核见final-validation.json。

## 46. C6 阶段小结

状态:**C6 完成,等待 v1.6 自动绑定**;P5Q不是CLOSED。

| 坐实的事实 | 证据 |
|---|---|
| 一次真实提交已创建父1201886,人工按BUILD_NOTES查号后绑定,子1201889 PASS | §43.7及C6a/live-05/trigger、fetch |
| 现行已绑定request终态重读幂等,RESULT仍为3、数据库不变 | C6b/reread-01/stdout.json、post-audit.json |
| 成功样本原始正文/活动文档字段相等,身份计数0 | C6b/raw-active-01/01–04.comparison.json |
| 非空BUILD_NOTES与请求标记逐字一致,样本挂账关闭 | §45.5与C6b/offline-analysis.json |
| Ref. Snapshot下父回显/冻结值/子快照名三者相同,R1决定按§45.1执行 | §45.5及live-05/fetch既有RESULT |
| 关闭修复首次真机核对:尾段0.212571秒,旧轮35.042秒;未直接观察代理退出码 | C6b/reread-01/execution.json、process-observations.json;旧live-05/fetch/execution.json |
| 配置1917两表新样本已取得,表格HTML不逐字一致但摘录字段一致 | C6b/configuration-1917.md、configuration-tables.diff |

仍开放:自动查找并绑定构建号须由v1.6三方评审冻结、实现及一次验证性真实提交闭环;
live-01/live-04登录超时原因仍未知,现有login_facts可供下次出现时区分,
本轮两次登录成功未触发失败事实应答。停止提示旧措辞留到v1.6修改。
C6使用专用构造状态库及本地bare镜像,不覆盖真实Gerrit远端核对;该项沿用C3离线验证,
首次真实sandbox推送仍在P12。Unified未取证仍disabled。完成本轮后停止,不自行收口。

## 47. 实施裁定 P5Q-C7-01:v1.8 冻结与 C7 范围

### 47.1 裁定原文

a. v1.8-FROZEN 取代 v1.5-FROZEN 成为 P5Q 的权威设计;v1.5-FROZEN 原样保留备查,哈希不变。v1.5 冻结后登记的实施裁定已全部并入 v1.8 正文(附录 I),以后以 v1.8 正文为准。
b. 本轮只做 v1.8 第 10 节 C7 一行所列内容,包括附录 I 第 14 条、附录 J、附录 K 的全部采纳项;不做 C8,不做任何真机操作。
c. 实现中发现 v1.8 条文与代码无法同时满足、条文有歧义或做不到:停止并写停止报告,不要自行改设计或自行选一种解释。

### 47.2 冻结核对与计划

基线48b0aa9dd2d793a103839ca6239fbec668fdb648,分支clang-fix-campaign。
已读第5、44–46节,已关闭的成功样本与BUILD_NOTES挂账保持CLOSED;
P12观察、Unified配置与验证性提交仍开放。本轮不访问真实QuickBuild/Gerrit,
不弹登录窗口、不点击Accept/Ready to Accept、不写专用状态库。

| 原字节输入 | SHA256实算值 | 结果 |
|---|---|---|
| docs/clang-fix-campaign/p5q-qb-trigger-design-v1.8-FROZEN.md | d0242ca8b708e9c1e3e714387bae963f8f6f16fc765179e6ed60d8be56493364 | 与给定值一致,原字节入库 |
| docs/clang-fix-campaign/p5q-qb-trigger-design-v1.5-FROZEN.md | f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c | 保留不改 |
| /home/linhao/Toolchain/p5q-live-validation/p5q-c6/state.db | 08ed202e69a73a480e7282a198565f32adae8157a332804df4df970238eacd30 | 只读核对,不得写入 |

实施顺序:冻结与design.md附录A同步;驱动失败分类/上限/终止trace;
自动查找解析与绑定复用;两个CLI接入;单元/静态负例/本机HTTPS集成与四组安全测试;
全部门禁与字节核对。证据目录evidence/C7/。每次提交同步本节。
工作树原有.gitignore修改、docs四文件删除与其它草稿不属于本任务,不纳入提交。

### 47.3 停止报告 P5Q-C7-02:read 的 CDP 等待预算

已由§48的P5Q-C7-03裁定关闭。以下为原停止事实,原始证据保留。v1.8第3.2节:259要求read路径上其它等待也不得超过30000毫秒,
但现有TrustedPage.run(:361/:362/:363/:373/:382)的五个CDP等待没有时限。
本轮代理仅允许改导航timeout与登录提示,没有授权增加TrustedPage/read的预算包装。
两条不能由这两处编辑同时落实;Python60秒应答上限不能证明代理30秒保证。

已用不可变48b0aa9生产Agent加“仅导航显式timeout”的内存变体实测:
五个合成CDP等待均在31010毫秒时仍pending;释放后均正常返回。零网络/零浏览器。
首次命令exit1;复跑及完整元数据由evidence/C7/capture-checks.mjs归档到checks.json,
事实原文见budget-probe.stdout.json。没有真实QuickBuild故障或真机重试。

完整事实、代码行号、框架源码依据与两个未实施候选见
[stop-report.md](evidence/C7/stop-report.md):由设计方选择收敛代理预算表述,
或授权可信读取/清理的预算实现并明确错误与清理语义。未自行选择解释。
本轮尝试的生产/驱动与design.md同步改动已全部撤回至48b0aa9,
只交付冻结登记、探针和停点记录。C7其余实现与完整验收未完成,不进入C8。

### 47.4 本轮实际检查与交付

| 检查 | 结果 | 证据 |
|---|---|---|
| read后续等待契约探针 | exit1,5/5超过30秒仍pending;释放后5/5正常返回 | C7/budget-probe.stdout.json |
| 既有源码静态护栏与负例 | exit0,183 passed/0 failed/0 skipped;含159项RED变异负例 | C7/source-guards.stdout.txt |
| design.md检查器(基线文档) | exit0,0 problem | C7/design-check.stdout.txt |
| v1.8/v1.5/专用库前后hash | 均逐字节不变,匹配给定值 | C7/checks.json |
| 代理完整文件及前缀 | 均与48b0aa9相等;前缀hash为40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16 | C7/checks.json |
| 新增C7文件脱敏自检 | 10文件通过,0失败;JSON另检查解码字符串 | C7/redaction-check.json |
| 暂存差异空白检查 | git diff --cached --check,exit0 | 本轮提交前执行 |
| 全量pytest/mypy/ruff/lint-imports/完整Node/本机HTTPS与四个安全组 | NOT_RUN;因规格停点终止,没有生产改动交付 | C7/stop-report.md |

归档脚本首轮调用检查器时漏传design.md路径,exit2/usage错误;
按既有命令补入路径后重跑exit0,未改检查器或正文。最终argv/UTC起止/exit均在checks.json。
本轮提交范围仅新冻结稿原字节、progress/INDEX、C7探针与证据;v1.7草稿不入库。
design.md附录A同步及C7其余交付仍待裁定后继续,不把基线检查通过作为v1.5.24已完成。
脱敏自检最初把探针源码的局部变量session赋值误识别为会话值;
该局部变量仅改名为cdp后复查全部通过,探针行为不变,未改脱敏规则。

## 48. 实施裁定 P5Q-C7-03:代理侧等待预算的范围

### 48.1 裁定原文

1. 停止报告 P5Q-C7-02 成立。v1.8 第 3.2 节"read 应答等待上限"一段中"并保证 read 路径上没有其它可超过该值的等待"一句作废,改为:
   a. 代理侧显式超时只约束以下两类:read 的页面导航(30000 毫秒);submit 中已有的三个显式等待(Ok 点击 60 秒、放行等待 10 秒、跳转等待 60 秒)。
   b. 可信读取环境的 CDP 调用(新建会话、取帧树、建隔离环境、Runtime.evaluate、断开会话),以及读取响应头等其它框架调用,代理侧不设预算,列为已接受残余。理由:它们只与本机浏览器进程交互、不经网络,挂起说明浏览器本身已坏。
   c. 统一由驱动侧应答上限兜底:read 60 秒、submit 150 秒。超时即终止代理,写 agent_terminated 记录,按第 3.2 节归类。驱动侧上限是唯一的硬上限;代理侧显式超时的作用只是不依赖框架默认值。
2. 第 9.2 节相应断言改为:
   a. 源码静态断言:read 路径的页面导航带显式 timeout,值为 30000,且小于驱动的 read 上限 60 秒;submit 路径三个显式超时之和小于驱动的 submit 上限 150 秒;每条各有负例。不对 CDP 调用做预算断言。
   b. 行为用例:用与 evidence/C7/probe-read-budget.mjs 相同的方法,分别让五处 CDP 等待之一挂起 → 驱动在 read 上限到时终止代理、写 agent_terminated、结果为读取失败(qb-result-fetch 为 QB_FETCH_FAILED,自动查找中为"读取失败");submit 路径中让一次可信读取挂起 → 驱动在 submit 上限到时终止,按驱动侧失败处理、不查找。
   c. 计时方式:测试可以通过驱动的构造参数缩短上限;生产入口固定为 60 秒与 150 秒,不经命令行或配置暴露;至少一例 read 按生产默认值真实计时。
3. 代理改动授权不变,仍只允许两处:read 导航显式 timeout: 30000、登录固定提示补齐。以"export class Agent {"为末端的源码前缀(含 Policy、installGuards、TrustedPage)保持与 48b0aa9 逐字节一致,hash 应为 40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16。
4. 本裁定在下次修订设计时并入正文,并列入 C8 收口文档的已接受残余。

### 48.2 续实施计划与边界

基线edee2f2。重读§47与C7/stop-report.md,三项输入哈希与§47.2一致。
旧探针保留为历史证据;不恢复未验收草稿。按新裁定重新实现驱动上限、失败来源、
终止记录,然后实现第5.5节两种查找、两个CLI与共享绑定,同步design.md附录A。
CDP等待无代理侧预算是已接受残余,由驱动硬上限兜底;C8须明确列出。
全部新增证据放C7/continuation/;离线测试与本机HTTPS、安全四组、全部门禁完成后交付。
不访问真实QuickBuild、不弹登录窗口、不推送Gerrit、不点Accept、不写专用库、不进入C8。

### 48.3 代码与用例落点

下表模块路径均在`tizen-ci-triage/scripts/ci_triage/`下。逐项用例及证据索引见
[coverage.md](evidence/C7/continuation/coverage.md),JUnit保留测试函数名,参数部分用稳定SHA256代替,
避免脱敏负例的合成HTML进入证据;与当前collect清单逐项对账。

| v1.8条文或裁定 | 落点 | 本轮落实 |
|---|---|---|
| 5.5配置页身份与Recent Builds | qb_result_html.py:158 | 直接子元素flex-1、六列表头、Id/链接、重复与50行上限 |
| 5.5两模式、基线、候选、截止点 | qb_discovery.py:83 | 提交后180秒/至多10轮;读取时一次;严格大于截止点才停,覆盖概览读取;轮询假时钟测试 |
| 5.2同核对/同事务 | qb_binding.py:87/:105;qb_result_fetch.py:229 | 自动与人工共用父页核对及单写事务,重查最新request、状态与已有绑定 |
| 4.3第2.5/10步 | qb_trigger.py:310/:502 | 基线失败分身份/表结构;驱动unknown不查找;代理合法unknown才查找;未匹配不重提 |
| 4.2第5步、4.3第1步 | qb_trigger.py:596 | already_requested提示;中途不可用不重启,保留最初失效unit名称,其它幂等项不变 |
| 5.1读取时恢复 | qb_result_fetch.py:519 | 未绑定只接受最新QB_REQUESTED,保持requests-file输入顺序;绑定后继续原结果读取 |
| 5.3证据续编、5.5隐私 | qb_evidence.py:8;qb_discovery.py:230 | 最后配置页先归档,仅匹配候选两页落盘;非匹配页及诊断不落盘/不进trace |
| 3.2、C7-03第1/2条 | qb_browser.py:170/:346 | 驱动unknown以内存类型标识,JSON不增加键;read60/submit150秒;五CDP挂起与submit挂起验证 |
| 3.1终止记录 | qb_trigger.py:301;qb_browser.py:448 | 超时终止记录,CLI关闭后写trace,写出失败不覆盖业务结果 |
| C7-03第3条 | qb_browser_agent.mjs:643/:716 | 只补登录提示及导航timeout30000;Agent之前前缀与48b0aa9逐字节相等 |
| 5.3第4项b | qb_result_fetch.py:63 | 停止提示改为核对主机、路径根与形态后按R1修订附录C第6项 |
| 附录A v1.6增补 | design.md:5/:2757/:3483 | v1.5.24版本/记录、4.5第5条追加/第6条替换;4.3不改 |

附录A照录时,替换引文之外的旧`(v1.5.23)`标记按“其余文字不变”保留,
故4.5第6条相邻显示`(v1.5.23)(v1.5.24)`。未修改任何冻结稿或检查器。
没有恢复旧草稿;绑定/证据抽取只为两条CLI共用现有规则,没有改变判据。

### 48.4 验收记录(完成)

`continuation/run_checks.py`逐命令记录argv、UTC起止、exit、前后输入hash与代理精确两处diff。
定向测试初轮164 passed,含五处CDP等待的read/submit与CLI映射、生产默认read真实计时
60.007633秒、六条预算RED变异。另补三条进程不存在/已退出/管道断开的真实驱动CLI用例,
纳入最终全量回归。Node362 passed,含既有159项RED静态负例。
四个安全组从头重跑4/4:Worker组走已批准的browser_fail_closed分支,
worker closeTarget抛固定Error类别、shared_worker关闭成功;攻击HTTP0、WS握手0,
浏览器已关且临时目录删除。307/308、逐跳、凭据隔离均通过。

本机HTTPS集成新增delayed-build与late-build两例已独立通过,假时钟推进轮询:
第二轮出现的新构建完成自动绑定;十轮未出现后,读取时模式一次查找绑定并继续RUNNING/PASS。
最终全量运行归档六种模式的协议命令、实际服务器请求、stdout、结果与脱敏页面。
`full-01`为主动中断的未完成回归(exit2):补齐上述两例之后重新从头运行`full-final`,
不把中断运行作为验收。mypy119文件、lint-imports6条契约、design检查器0problem已通过;
完整暂存树导出后的ruff通过,不把工作区既有草稿/无关删除纳入本轮。

最终全仓命令为`.venv/bin/pytest -q --junitxml=<full-final/junit.xml>`,
结果2878 passed/0 failed/1 skipped,exit0,1134.40秒。
该次收集之后补齐的3条预算边界用例单独运行,3 passed/0 failed/0 skipped,
见`wait-boundaries-final/`:149秒合法unknown继续查找绑定;150秒终止且不查找;
close实等35.093729秒后终止,trace恰一条且已完成结果不变。
两次互不重叠的JUnit合并覆盖当前`pytest --collect-only -q`的2882项,
合计2881 passed/0 failed/1 skipped,并非声称一次命令执行了2881项。
唯一skip为`test_tizen_build_verify.py::test_case_insensitive_bypass_is_platform_specific`,
原因`case-sensitive filesystem`,与基线一致。

| 门禁/分组 | 最终结果 | continuation/下证据 |
|---|---|---|
| 全仓pytest + 3条补充边界 | 2881 passed/0 failed/1 skipped,两次exit均0 | full-final/;wait-boundaries-final/;collection-final/;delivery-audit.json |
| 自动查找Python | 123 passed | full-final/junit.xml,test_qb_discovery |
| 驱动预算/分类/CLI映射 | 47 passed(44+3) | 两份JUnit,test_qb_driver_budget |
| 既有trigger/fetch | 140/184 passed | full-final/junit.xml |
| 真实CLI+本地HTTPS六模式 | 6 passed,新增2例 | full-final/cli-artifacts/;integration-added/ |
| Node单元/静态断言 | 362 passed/0 failed/0 skipped | node-01/ |
| 静态变异负例 | 159个既有名字负例+6个预算负例全部RED | node-01/output.log;focused-01/output.log |
| 拦截安全四组 | 4 passed/0 failed,全部重跑 | safety-01/ |
| mypy | exit0,119 source files | mypy-final-2/ |
| ruff完整待提交树 | exit0,All checks passed | ruff-delivery-final/ |
| lint-imports | exit0,6 kept/0 broken | imports-final/ |
| design.md检查器 | exit0,0 problem | design-final/ |

每个目录的`command.json`有完整argv与UTC起止,包括Node/Playwright/Chromium本机路径。
新增pytest数量172(123查找+47预算+2本机集成),基线2709 passed/1 skipped。
pytest参数原文中的合成HTML触发了归档自检,改为测试名加参数SHA256;
安全日志中JSON内嵌HTML用Unicode转义保存尖括号,解析后的结构与值逐字不变。
不改变生产脱敏规则;`audit_delivery.py`同时检查原始字节与JSON解码字符串,
并核对两份JUnit与当前collect集合相等。处理过程首轮遇到中断JUnit的无名testcase,
改为保留该中断记录后完成;不将该记录计入验收。证据哈希详见`delivery-audit.json`。
完整`git diff --cached --check`只报告原样归档HTML的行尾空白;
排除`continuation/**/qb_evidence/*.html`后exit0。原始页面不为样式检查改写,
逐文件例外由`delivery-audit.json`登记并断言除此之外没有其它空白问题。

### 48.5 交付边界与后续挂账

新增停止报告0项,与v1.8加C7-03不一致/有歧义/做不到的地方:无。
代理前缀SHA256为`40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16`,
与48b0aa9逐字节相等;整个代理文件也只出现授权的两处变更。
v1.5、v1.8与专用库前后SHA256均与§47.2相同。

C8须写入已接受残余:CDP及其它本机框架调用没有代理侧预算,由驱动60/150秒兜底;
Recent Builds约10条的恢复窗口;身份计数不能发现未登记、且不等于登录显示名的账号列。
C8验证性真实提交未执行;P12推送观察与Unified配置挂账保持原样。
本轮提交只含C7实现、测试、design.md照录同步、进度与脱敏证据;
没有修改两个冻结稿、专用状态库或工作区原有无关变更,没有真实QB/Gerrit操作。

## 49. 实施裁定 P5Q-C8-01:C7 验收、小修与 C8 范围

### 49.1 裁定原文

1. C7(0b27c49)验收通过。
2. 两处小修,只改 Python 与测试,不改代理:
   a. 第 4.3 节第 2.5 步失败归类:配置页 HTTP 非 200、重定向、可信读取环境不可用,归"页面身份"类提示(v1.8 第 4.3 节第 2.5 步 a);read 应答超时或代理不可用,error_code 为 QB_BROWSER_UNAVAILABLE(不是 REJECTED_QB_FORM_CHANGED),并按第 4.3 节第 1 步处理本批剩余 unit。对每种情况补测试,断言错误码和提示类别。
   b. 本机集成的假配置页按 C6b 05.raw-redacted.html 补上每行的下拉菜单链接(href="javascript:void(0);"),保留停止链接,重跑自动查找本机集成用例。
3. C8 范围:v1.8 第 9.4 节第 3 步全部内容(验证性真实提交;随后对构造的未绑定请求做零提交读取验证)。不写收口文档,收口另行下达。

### 49.2 计划、输入与授权边界

基线0b27c49;已重读§37–48及v1.8第9.4节第3步。
v1.8 SHA256=d0242ca8b708e9c1e3e714387bae963f8f6f16fc765179e6ed60d8be56493364;
v1.5 SHA256=f16621bb1e09ac6fbf16371c6130d24a281293e0cf5a102a548c409dfedcf91c;
C6专用库SHA256=08ed202e69a73a480e7282a198565f32adae8157a332804df4df970238eacd30。
本轮不修改冻结稿、代理或C6目录任何文件。代理前缀须保持
40f8f22bd0f5f4078b6012083c457a7b423e52fd69e5603f03dfc7a09d363a16。

先完成基线失败归类、夹具菜单链接、离线门禁并提交推送;
然后在仓库外新建p5q-c8专用库、配置和只读fetch取得对象的本机bare镜像,
只构造unit 1。完成前置、列出十二字段、提交推送准备证据后等待本轮逐字“确认提交”。
unit 2、真实提交、结果轮询与零提交读取均未执行,旧确认不得复用。
证据统一放evidence/C8/。无关.gitignore、docs删除、草稿不纳入提交。

### 49.3 小修落点与离线用例

- `ci_triage/qb_discovery.py:20`:configuration_http/configuration_read纳入身份提示集合,
  Recent Builds结构提示不变。
- `ci_triage/qb_trigger.py:310`:基线read的驱动失效归QB_BROWSER_UNAVAILABLE,
  保留原QbBrowserError的命令/退出/停止类别诊断;沿用批次不可用处理,不重启代理。
- `tests/node/p5q_fake_quickbuild.mjs:35`:每行补javascript:void(0);菜单链接,
  停止链接保留;只改本机假服务器的测试夹具。
- `tests/unit/qb_discovery_fixtures.py`:同样补菜单,与C6b原始页蓝本保持一致。
- `tests/unit/test_qb_discovery.py:67/:478/:499`:新增1项链接解析、5项页面身份、
  4项驱动失效用例。批次覆盖u1失败,u2/u3不可用,u4已有请求仍幂等,整库不写。
  既有HTTP/重定向用例新增身份提示断言。

定向133 passed/0 failed;新增10项。全量门禁完成,最终结果见§49.4。
证据脚本首轮ruff发现两条长行,只修正该脚本排版,复跑完整待提交树通过。
代理文件完整字节与0b27c49一致,不只比较前缀;无生产放行规则变更。

### 49.4 小修验收完成

| 门禁 | 结果 | evidence/C8/offline/证据 |
|---|---|---|
| 全量pytest | 2891 passed / 1 skipped / 0 failed,exit0,896.30秒 | full/output.log、junit.xml、command.json |
| 定向自动查找 | 133 passed / 0 failed | focused/ |
| 本机HTTPS六种模式 | 6/6通过,配置页含菜单与停止链接 | full/cli-artifacts/各模式的commands.json、server-requests.json |
| mypy | exit0,119 source files | mypy/ |
| ruff完整待提交树 | exit0,All checks passed | ruff-final/ |
| lint-imports | exit0,6 kept / 0 broken | imports/ |
| design.md检查器 | exit0,0 problem | design/ |
| 冻结稿/C6库/代理字节 | 前后相同,前缀hash与§49.2相同 | 每个command.json、audit.json |

唯一skip仍为大小写不敏感文件系统用例,原因case-sensitive filesystem。
本轮单次完整回归覆盖当前collect的2892项,参数名哈希化后逐项集合对账相等。
全量中Node静态断言、浏览器DOM、四组本机安全测试包装用例均通过;
代理未改,本轮不另称独立重跑并归档了四组原始日志。
本机六模式的协议与服务器请求分别归档,延迟出现/读取时恢复均通过;
其中预期submit_uncertain的CLI exit5是用例规定结果,不是pytest失败。
关闭尾段0.075–0.177秒。证据逐文件原字节与JSON解码字符串自检通过,
详见audit.json;合成负例的参数名按C7方式哈希化,不改生产脱敏规则。
归档HTML保留原字节,其行尾空白为diff检查的具名例外,不格式化原始证据。

未发现与冻结稿或本裁定不一致/做不到的地方。小修先独立提交推送;
随后才开始C8专用目录准备,当前没有真实QB请求、没有Gerrit fetch或push。

### 49.5 C8专用准备(小修e393a1f推送之后)

新目录`/home/linhao/Toolchain/p5q-live-validation/p5q-c8/`此前不存在。
目标固定为`platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0`。
不复用C6的库或镜像,不复制其冻结快照行。unit 2尚未构造。

构造入口(仓库根目录运行,完整实现与证据在evidence/C8/preparation/):

```bash
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C8/preparation/prepare_c8.py fetch
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C8/preparation/prepare_c8.py construct
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C8/preparation/prepare_c8.py preflight
```

fetch只执行一次,2026-10-21T09:01:09Z至09:01:13Z,exit0。
实际Git命令依次如下;均由SandboxGit加统一环境与8项-c覆盖,
完整argv/起止/exit/stdout/stderr逐条存于mirror-commands.json,没有真实push:

```bash
git init --bare /home/linhao/Toolchain/p5q-live-validation/p5q-c8/remotes/platform/upstream/libtirpc
git -C /home/linhao/Toolchain/p5q-live-validation/p5q-c8/remotes/platform/upstream/libtirpc fetch --no-tags --no-recurse-submodules --depth=1 ssh://review.tizen.org:29418/platform/upstream/libtirpc 7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0
git -C /home/linhao/Toolchain/p5q-live-validation/p5q-c8/remotes/platform/upstream/libtirpc cat-file -t 7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0
git -C /home/linhao/Toolchain/p5q-live-validation/p5q-c8/remotes/platform/upstream/libtirpc rev-parse 7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0^{tree}
git -C /home/linhao/Toolchain/p5q-live-validation/p5q-c8/remotes/platform/upstream/libtirpc update-ref refs/heads/sandbox/p5q-c8-libtirpc 7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0
git -C /home/linhao/Toolchain/p5q-live-validation/p5q-c8/remotes/platform/upstream/libtirpc show-ref --verify refs/heads/sandbox/p5q-c8-libtirpc
```

对象类型commit,tree=`9ef054c6187444dedb07aab80fb04279f5683bf4`,本机sandbox ref精确匹配目标。
SSH只用BatchMode/StrictHostKeyChecking/ConnectTimeout,未索要或记录凭据。
可选的当前公共manifest GET本轮未执行,不声称已核对当前快照revision。

unit=`p5q-c8-libtirpc-20261021`,verification_ids为同名前缀的-v0/-v1/-v2,
分别standard-aarch64、standard-armv7l、standard-x86_64。
三份PASS、round、DERIVE、PUSH按C6-01构造,明确是合成前提,
不是实际gbs验证、派生提交或Gerrit推送。构造来源及占位字段见synthetic-basis.json、state-before.sql。
库`p5q-c8/state.db`,配置`p5q-c8/config.yaml`,state_root=`p5q-c8/state`,工作区=`p5q-c8/ws`。
配置的gerrit_ssh_base仅指向本机remotes;浏览器路径/600秒登录时限均为生产配置,
没有host-resolver或测试证书参数。SNAPSHOT_NUM=@freeze,当前没有冻结行。

### 49.6 前置、清理与准备验收

构造命令尚未结束时误提前启动了一次只读preflight,因此关联尚未齐全,
exit1/REJECTED_ARCH_AGGREGATE_MISMATCH。等待construct成功后再检查;
这次顺序错误没有真实QB访问、没有提交意图写入,不把它当生产规格缺口。
随后检查发现一个旧profile残留(2026-10-21T07:24Z创建),只有socket和19字节symlink,
没有普通文件或进程引用。保留原检查于preflight-before-cleanup.json;
lsof exit1且stdout/stderr均空,逐项校验owner/类型/inode后仅删除该目录,
不读取或输出链接值。清理命令如下,exit0,证据orphan-cleanup.json:

```bash
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C8/preparation/clean_orphan.py
```

最后一次preflight在09:03:47Z至09:04:07Z完成,exit0,证据preflight.json:

| 检查 | 实际结果 |
|---|---|
| C8库SHA256前后 | dd43219d2964e23d711e904ab640a73eb3c328e6685940dc7711beb4f7563ff2,相等 |
| unit数/最新状态 | 1 / SANDBOX_PUSHED |
| QB requests/profiles/events | 0 / 0 / 0 |
| 本机远端核对 | PASS,derived/ref均等于目标commit,隔离.transport已删除 |
| 代理/Playwright Chromium/profile/.transport | 均0残留,进程扫描错误0 |
| 磁盘 | /home可用214G,占用88%;/dev/shm可用16G |
| 内存 | available 6.3Gi;swap已用约4Gi,如实记录不称空闲 |
| D状态进程(间隔10秒3次) | 0 / 0 / 0 |
| v1.8/v1.5/C6库 | 与§49.2相同 |
| C6目录 | 逐文件内容hash/链接目标与c6-tree-before.json相等,未写任何C6文件 |

只读前置直接调用生产_snapshot、_idempotency与_remote_check,没有实例化代理,
没有运行qb-trigger或qb-result-fetch命令。未提交state.db二进制,
只提交SQL文本快照、无凭据配置副本与脱敏JSON。准备脚本ruff通过;
生产代码没有在小修提交之后改变,完整回归结果仍见§49.4。
准备交付的validate.py实跑通过:14份文件原字节/JSON解码脱敏自检,
ruff、design.md检查器(0 problem)、暂存diff检查均exit0;
完整记录见preparation/validation.json。本准备提交不重跑全量pytest,
没有修改小修已验收的生产代码或测试。

### 49.7 十二字段与待确认闸门

| 字段 | 拟填值 |
|---|---|
| BUILD_TYPE | Full |
| REPO_TYPE | ALL |
| BUILD_REFERENCE | Ref. Snapshot |
| SNAPSHOT_NUM | @freeze,提交时表单的唯一当前选中项,不预设历史值 |
| PROJECT_BRANCH | tizen_base |
| Immediate Stop With Error | true(勾选) |
| CHILD_CONFIGURATIONS | standard-armv7l:aarch64:x86_64,一个组合项 |
| Build Package List | platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0 |
| Add Package List | 空字符串 |
| Remove Package List | 空字符串 |
| TARGET_IMAGE | 空列表 |
| BUILD NOTES | clang-fix-campaign request=<生产qb-trigger生成的request_id> |

目前新“确认提交”=NOT_RECEIVED。准备证据先提交推送后,在对话列出上表与专用路径,
等待FatTank逐字确认。之前所有“确认提交”与“开始”均不复用。
待授权生产命令(未执行):

```bash
.venv/bin/python -m ci_triage qb-trigger --verification-ids p5q-c8-libtirpc-20261021-v0,p5q-c8-libtirpc-20261021-v1,p5q-c8-libtirpc-20261021-v2 --state-db /home/linhao/Toolchain/p5q-live-validation/p5q-c8/state.db --state-root /home/linhao/Toolchain/p5q-live-validation/p5q-c8/state --config /home/linhao/Toolchain/p5q-live-validation/p5q-c8/config.yaml
```

下一步仅允许一次真实trigger,无retrigger。只有unknown后自动绑定成功才继续规定的结果读取;
直接build落点、未找到/超时/多于一个、基线失败或其它异常均停止,不重提。
约25分钟首次fetch,非终态时至少间隔20分钟;每次浏览器登录前预告。
终态之后才构造unit 2并做一次读取时模式零提交验证,e1/e2/e3a/e3b均待执行。
本轮未写收口文档,P5Q不标CLOSED。当前未发现新的设计不一致或做不到之处。
