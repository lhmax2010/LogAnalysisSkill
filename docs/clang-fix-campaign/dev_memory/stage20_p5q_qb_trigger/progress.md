# Stage20 P5Q QuickBuild Trigger

日期:2026-10-15。状态:**C2a_COMPLETE;C2b_LIVE12_COLLECTED;C2c_COMPLETE;C3_COMPLETE;C4_COMPLETE;C5a_COMPLETE;C5b_STOPPED**。
C5a基线39e4bde,离线集成与第1.6步工具见§34。C5b基线b134d16,六页原始/活动比对通过;
填表演练exit1且未落盘阶段证据,见§35。C6未开始,成功/BUILD_NOTES样本挂账开放。
以下各轮“不进入下一阶段”只约束当轮,均保留为历史记录;当前边界为停止C5b、不进入C6。
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
| C5b | 第1.6步原始/活动文档比对、填表演练与样本补齐 | STOPPED;§35:六页比对通过,演练exit1/无运行记录,未重试;两个样本仍挂账 |
| C6 | 第9.4节第2步确认的真实提交与收口文档 | C5 + FatTank明确确认;NOT_STARTED |

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
| 第9.4节第1步RBS只读取证 | PENDING_C2;安全子集本机先绿,父1193467/子1193469及失败父1186372;配置ID/title、变量映射、Child Build表、登录落点/被拒资源等全量取证 |
| 第9.4节第1.5步表单联动 | PENDING_C2;Full改Partial再改回Full,不submit,记录回调/action/版本/重渲染变化 |
| 第9.4节第2步一次真实提交 | PENDING_C6/FatTank;先展示十二字段/目标行并确认,再提交并fetch,取得响应落点与build ID闭环;完成前不CLOSED |
| 附录C待填 | PENDING_C2;冻结稿当前保持原字节;取证后按授权照录,不得猜字段或拿SBS替代 |
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
