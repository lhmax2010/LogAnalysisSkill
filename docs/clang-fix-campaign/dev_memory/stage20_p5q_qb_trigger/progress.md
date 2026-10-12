# Stage20 P5Q QuickBuild Trigger

日期:2026-10-12。状态:**C2a_COMPLETE;C2A-04_COMPLETE;C2b NOT_STARTED**。
当前轮按§15完成P5Q-C2A-04;基线ca43b5d,2152 passed/1 skipped。§14的证据保留。
本轮只使用归档HTML与本地合成数据;不访问QuickBuild/Gerrit,不进入C2b。
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
| C2 | qb_browser_agent.mjs三拦截面/协议适配层;qb_browser.py/假代理;第9.2节与第9.3节本机安全子集;随后第9.4节第1/1.5步、回填附录C | C2a COMPLETE:见§14及§15修正;C2b NOT_STARTED,真机前须完成第9.3节指定HTTPS夹具的四组安全子集 |
| C3 | qb-trigger CLI及触发/填表/崩溃/多unit/隔离传输用例 | C2且只读取证结论完整;NOT_STARTED |
| C4 | qb-result-fetch CLI、人工绑定及读取/落库用例 | C3;NOT_STARTED |
| C5 | 第9.3节其余本机浏览器集成与证据 | C4;NOT_STARTED |
| C6 | 第9.4节第2步确认的真实提交与收口文档 | C5 + FatTank明确确认;NOT_STARTED |

C2真机取证与冻结稿假设不符时按R1修订,不得直接继续C3。
C0授权不含实现;C1已完成。本轮仅授权C2a离线实现与本机about:blank能力验证,
不含C2b-C6、人工登录、真实站点填表/联动/提交。

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
