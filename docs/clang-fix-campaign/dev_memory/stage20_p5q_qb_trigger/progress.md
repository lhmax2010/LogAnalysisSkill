# Stage20 P5Q QuickBuild Trigger

日期:2026-10-10。状态:**C0_COMPLETE / P5Q-C0-01 CLOSED;C1 NOT_STARTED**。
本轮仅C0文档工作,不写实现、不执行QuickBuild请求或真实推送。
开工基线:`26e9e3d`,分支`clang-fix-campaign`。
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
| C0 | 冻结稿原字节入库;附录A同步design.md v1.5.22;本stage与INDEX/移交表 | DONE;C0-01已落实,§9门禁全部通过;本提交为外部锚 |
| C1 | qb_redact.py;配置解析;campaign_qb_profiles;四个按连接写入原语/公共API重构/qb_profile;精确表集合测试与第9.1节对应用例 | C0;NOT_STARTED |
| C2 | qb_browser_agent.mjs三拦截面/协议适配层;qb_browser.py/假代理;第9.2节与第9.3节本机安全子集;随后第9.4节第1/1.5步、回填附录C | C1;NOT_STARTED |
| C3 | qb-trigger CLI及触发/填表/崩溃/多unit/隔离传输用例 | C2且只读取证结论完整;NOT_STARTED |
| C4 | qb-result-fetch CLI、人工绑定及读取/落库用例 | C3;NOT_STARTED |
| C5 | 第9.3节其余本机浏览器集成与证据 | C4;NOT_STARTED |
| C6 | 第9.4节第2步确认的真实提交与收口文档 | C5 + FatTank明确确认;NOT_STARTED |

C2真机取证与冻结稿假设不符时按R1修订,不得直接继续C3。
本轮授权不包含C1-C6实现、登录、浏览器填表、表单联动或真实提交。

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
