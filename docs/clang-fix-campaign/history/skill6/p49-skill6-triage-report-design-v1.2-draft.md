# P4.9 skill-6 设计:tizen-triage-report 抽取 + gbs_report 关门(v1.2-draft)

- 阶段:P4.9 **最后一个** skill 批次(skill-5 CLOSED @d51145f / 签批 @81ada54)
- 权威并行:step-0 `v2.1`、skill-1 `v1.4`、skill-2 `v1.3`、skill-3 `v1.3.1`、
  skill-4 `v1.12.1`、skill-5 `v1.3.2`(均 FROZEN)
- **基线**:`912 passed, 1 skipped`;门禁继承 A₀(参数化、独立数据文件)
- **总铁律**:行为等价——逐字节迁移 + import 翻转,零语义变更
> **v1.1 修订(两家评审)**:①**§5 arch 改为"透传维度一例"**(实测:`arch`
> 仅作 dataclass 字段 :34/:46、参数 :58、URL 拼装 :68、错误消息 :76,
> **无任何分支逻辑**——既非 skill-4 式的判定维度、也非 skill-1/2/3/5 式的
> 完全不存在,应立第三种口径而非二选一,且**实现期不留裁量**);
> ②**§1.3 理由①补"未来消费者"论证**(评审指出"当前无第二消费者"是现状
> 而非结构性论证,补:P5/P6 若需 GBS 抓取,应消费**已在 shared 的 HTTP 层**
> 而非本 skill 的报表语义;报表解析是 triage 语义、非通用能力);
> ③**§2 约束 6 依据加强**(实测 `find_iframe_src`/`_IframeParser` 零跨模块
> 引用,不止"复用面为零"的推断);④**§3 增补"关闭权"论证**(本批是否有权
> 关闭 skill-2 议题);⑤§0.3 `EDIT_SPEC_SCHEMA` 双权威位置实测钉死;
> ⑥§0 符号数 AST 复核(21 = 20 def/class + 1 顶层赋值)。
>
> **v1.2 修订(Codex 判不 freeze-ready:1 BLOCKER + 4 MAJOR;Claude Code 判
> 1 遗留 MAJOR。两家独立抓到同一条模式矛盾——且它 v1.0 已报、v1.1 未修
> 亦未入变更清单)**:①【BLOCKER】**关门台账漏两项**——skill-3 D1、
> skill-4 D2 **均具名指向 triage-report**(twin 合并议题,与 skill-2 同类),
> v1.1 只登记 skill-2 一条,"最后一笔欠债清零"不成立;②【MAJOR】
> `EDIT_SPEC_SCHEMA` **两处同值** `"gbs_patch_suggest/edit-spec/v1"`,
> v1.1 写成两个不同值(且自称"实测钉死",实为看错);③【MAJOR】arch
> "一例三断言"不可执行(成功路径不产生 :76 错误)→ 改**两场景**;
> ④【MAJOR,两家共提、v1.0 即报】**§1:109 模式矛盾**(与 §1.3/§8 的模式二
> 冲突)——**本条穿过一轮的原因是它不在变更清单里**,见 §9 新增纪律;
> ⑤【MAJOR】§2 约束 5 措辞、约束 6 依据、§5 分支表与 parity 载荷未落实。

- **本批双重身份**:①第六个 skill 的抽取;②**step-0 §8 砍出的 gbs_report
  整模块的关门批次**(七条约束 + skill-2/skill-4 各一项具名延期)

---

## §0 权威归属表(24 行,唯一权威;parser-only 冻结前必过)

**由脚本自源码 AST 机械生成,不手抄(⑩)**。**v1.1 AST 复核**:gbs_report 顶层 = 20 `def`/`class` + 1 顶层赋值(`DEFAULT_ARCHES`)= **21**;report.py = **3**;合计 **24**——实现期落表:gbs_report.py
21 行(definition=`tizen_triage_report/gbs_report.py`)+ report.py 3 行
(definition=`tizen_triage_report/report.py`),owner 一律
`skill/tizen_triage_report`。**冻结前 parser-only 24/24**(skill-5 教训:
简单批次漏此项,commit C 才 fail-closed)。

### 0.1 判据 dry-run(冻结前置,已完成;Claude 实测 @81ada54)

```

=== gbs_report.py (21 符号) owner=skill/tizen_triage_report ===
  DEFAULT_ARCHES               <- ['orchestrator.py'] => OK
  GbsReportPackage             <- ['orchestrator.py', 'runner.py'] => OK
  GbsReport                    <- [] => OK
  fetch_gbs_report             <- ['orchestrator.py', 'runner.py'] => OK
  download_gbs_package_buildlog <- ['orchestrator.py', 'runner.py'] => OK
  find_iframe_src              <- [] => OK
  parse_gbs_report_packages    <- [] => OK
  _Anchor                      raw=[] → [twin 2处:gbs_report.py:156, sources.py:100;核销后=[]] => OK
  _Cell                        raw=[] → [twin 2处:gbs_report.py:163, sources.py:107;核销后=[]] => OK
  _Row                         raw=[] → [twin 2处:gbs_report.py:169, sources.py:114;核销后=[]] => OK
  _Table                       <- [] => OK
  _CellBuilder                 raw=[] → [twin 2处:gbs_report.py:179, sources.py:124;核销后=[]] => OK
  _AnchorBuilder               raw=[] → [twin 2处:gbs_report.py:185, sources.py:131;核销后=[]] => OK
  _IframeParser                <- [] => OK
  _ReportTableParser           <- [] => OK
  _looks_like_build_status_table <- [] => OK
  _row_to_package              <- [] => OK
  _status_from_anchor          <- [] => OK
  _attrs_to_map                raw=[] → [twin 2处:gbs_report.py:349, sources.py:279;核销后=[]] => OK
  _class_names                 raw=[] → [twin 2处:gbs_report.py:353, sources.py:283;核销后=[]] => OK
  _normalize_text              raw=[] → [twin 2处:gbs_report.py:357, sources.py:287;核销后=[]] => OK

=== report.py (3 符号) owner=skill/tizen_triage_report ===
  TriageReportData             <- ['runner.py'] => OK
  render_report                <- ['runner.py'] => OK
  _primary_location            <- [] => OK

[SUMMARY] 24 OK / 0 MISMATCH(twin 核销后终判)
[外部消费 6 / 无外部消费 18]
[twin] 8 组:
   - _Anchor: 2 处 — gbs_report.py:156, sources.py:100
   - _Cell: 2 处 — gbs_report.py:163, sources.py:107
   - _Row: 2 处 — gbs_report.py:169, sources.py:114
   - _CellBuilder: 2 处 — gbs_report.py:179, sources.py:124
   - _AnchorBuilder: 2 处 — gbs_report.py:185, sources.py:131
   - _attrs_to_map: 2 处 — gbs_report.py:349, sources.py:279
   - _class_names: 2 处 — gbs_report.py:353, sources.py:283
   - _normalize_text: 2 处 — gbs_report.py:357, sources.py:287
```

**结论:两模块 24 符号 skill owner 全合法**(6 有外部消费,全属 ci_triage
编排层;18 无外部消费);**零判据变更**(由 dry-run 证明)。

### 0.2 ⑰ 跨批次检查(本批为"欠债关门批次",结果非空)

`grep` 全部冻结稿:`owner=triage-report` 的符号**无**(step-0 未预判);但
检出**五类具名欠债**,本批须逐项关门:

| 欠债 | 来源 | 本批处置 |
|---|---|---|
| gbs_report **七条约束** | step-0 §8 | §2 逐条销账 |
| fetch/parse 拆分 + `GbsReportPackage`/`GbsReport` 类型归属 | step-0 §8 | §1.3 裁决 |
| iframe 抽取闭包 + `_attrs_to_map`/htmlutil 层位 | step-0 §8 约束 6 | §1.3 裁决 |
| **同名件合并议题**(8 组) | skill-2 §1.1 | §3 裁决 |
| **同名 Gerrit/report helper 合并** | **skill-3 D1**(closeout:246,具名 triage-report) | §3 裁决(v1.2 补) |
| **同名 build/report/formatter helper 合并** | **skill-4 D2**(closeout:160,具名 triage-report extraction batch) | §3 裁决(v1.2 补) |
| `EDIT_SPEC_SCHEMA` 单一权威 | skill-4 DEFERRED | §0.3:**非本批**,归 patch-suggest 批次(核实) |

### 0.3 前提复核(七约束写于 v1.12 时代)

`gbs_report.py` 自初始入库(`a7d01da`,2026-07-24,早于 step-0)**零改动**
——七约束前提成立。`EDIT_SPEC_SCHEMA` 的双权威**实测位于**
`tizen-build-verify/scripts/tizen_build_verify/edit_spec_guard.py:13` 与
`tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:16`,
**两处值相同**:`"gbs_patch_suggest/edit-spec/v1"`(v1.2 更正:v1.1 误写为
两个不同值并自称"实测钉死"——**同值恰是双权威风险的本体**:一侧升版另
一侧不动即静默失配),
**与 triage-report 两模块零关联**(gbs_report/report 均不引用该常量);
skill-4 closeout 第 17 项登记的关门批次为 patch-suggest 相关批次,
**本批不接、不改其归宿**。

## §1 skill 形态:两模块一 skill(第二次,首例 skill-4)

```
tizen-triage-report/scripts/tizen_triage_report/
  __init__.py     # 薄导出:仅 §1.2 公开面
  gbs_report.py   # 21 符号,**模式二**:cmp + §1.3 一处白名单(:10 import 翻转)
  report.py       # 3 符号,模式一逐字节 cmp
```

### 1.1 依赖闭包(双向实测)

- `gbs_report.py` → **仅** `ci_triage.quickbuild`(现为 shared HTTP 层的
  纯 shim,0 def/class)——迁后 import **翻转为 `tizen_ci_shared.quickbuild_http`**
  (下行合法;此翻转即 §1.3 白名单唯一项);
- `report.py` → 仅 `tizen_ci_shared.types`(下行合法);
- **两模块互不 import**(实测 0)——是"两模块一 skill"而非一条链;
- **消费方**:`fetch_gbs_report`/`download_gbs_package_buildlog`/
  `GbsReportPackage` ← runner + orchestrator;`DEFAULT_ARCHES` ← orchestrator;
  `TriageReportData`/`render_report` ← runner。**全部 ci_triage 编排层**。

### 1.2 公开契约(SKILL.md)

| symbol | 契约 |
|---|---|
| `fetch_gbs_report` | 抓取 GBS 报表页并解析(fetch+parse 一体,现状) |
| `download_gbs_package_buildlog` | 下载单包构建日志 |
| `GbsReportPackage` / `GbsReport` | 报表类型 |
| `DEFAULT_ARCHES` | 默认架构集 |
| `parse_gbs_report_packages` / `find_iframe_src` | 解析入口(公开但当前仅内部调用) |
| `TriageReportData` / `render_report` | 报告渲染 |

其余 15 项为**包根不导出的实现符号**(三概念口径沿 skill-3)。

### 1.3 [本批核心裁决] fetch/parse **不拆分,整体随 skill**(step-0 约束 5 二选一)

step-0 §8 约束 5 允许"保留 composition shell"或"同批次裁定直接拆分";
step-0 v1.2 类 B 曾倾向"fetch 组归 shared"。**本批裁决:不拆分、不下沉,
fetch 与 parse 整体随 triage-report**,理由(全部实测):
1. **消费方全在编排层**(runner/orchestrator),v1.3 层化判据下 skill owner
   合法;**没有第二个 skill 需要 `fetch_gbs_report`**——下沉 shared 会制造
   **无第二消费者的共享物**。
   **结构性论证(v1.1 补;评审指出"当前无第二消费者"只是现状)**:未来
   P5/P6 若需 GBS 抓取能力,**正确的消费对象是已在 shared 的 HTTP 层**
   (`quickbuild_http` 的 `HttpFetcher`/`load_cookie_jar`/`_urllib_fetch` 等),
   而非本 skill 的 `fetch_gbs_report`——后者返回的是**已解析的报表语义**
   (`GbsReport`/`GbsReportPackage`),属 triage 域知识、非通用抓取能力。
   **通用部分已经下沉,留在 skill 的恰是语义部分**;故"无第二消费者"不是
   偶然现状,而是**分层结果**。若未来真出现第二个 skill 需要报表语义,
   届时按 v1.3 层化判据重新裁定归属(与其它符号同一规则),不预支;
2. **fetch 与 parse 紧耦合**(`:72` 调 `find_iframe_src`、`:88` 调
   `parse_gbs_report_packages`、`:94` 返回已解析的 `GbsReport`);拆分需要
   raw 类型 + composition shell + 三档审计状态——**正是 step-0 七轮推演撞出
   的整套复杂度**;整体迁移**零语义变更**,不需要任何一项;
3. step-0 v1.2 "fetch 归 shared"的前提是 HTTP 层尚未下沉;**现 HTTP 层已在
   shared**,fetch 组只是它的一个消费者。

**由此七约束的触发面**(§2 逐条):约束 1/3/4/5 为拆分场景所设,**本批不
触发**(需在 §2 明写"未触发"及依据,不得静默跳过);约束 2/6/7 执行。

**类型归属**:`GbsReportPackage`/`GbsReport` **随 gbs_report.py 留 skill**
(消费方仅编排层;step-0 v1.2 类 D 曾裁"迁 shared/types",前提同上已变)。
**注意 `GbsReportPackage` 是 `runner.py`/`orchestrator.py` 的类型依赖**——
翻转 import 即可,无跨界。

**白名单(模式二,唯一一项)**:`gbs_report.py:10` 的
`from ci_triage.quickbuild import (...)` → `from tizen_ci_shared.quickbuild_http import (...)`;
其余逐字节。`report.py` 无白名单(模式一)。

## §2 step-0 七条约束逐条销账(关门批次硬项)

| # | 约束 | 本批处置 | 依据 |
|---|---|---|---|
| 1 | raw 字段须覆盖 parse 真实输入(`iframe_url`/`build_id`) | **未触发**(不引入 raw) | §1.3;附实测:`parse_gbs_report_packages` 真实输入为 **`html_text`(首参,:134)+ `build_id` + `arch` + `iframe_url`** 四项(v1.2 补 `html_text`——它正是 raw 抓取结果的主体,遗漏它会使未来 raw 类型设计缺主字段),比约束原文多 `arch`,供未来拆分参考 |
| 2 | 跨边界迁移按完整闭包,核对 `QuickBuildError`/HTTP 原语/iframe 链/parser 输入,闭包内无上行 | **执行** | §1.1:唯一仓内依赖 = shared HTTP 层(下行);iframe 链与 parser 均在模块内;`QuickBuildError` 经 shared 取;**零上行** |
| 3 | 结构断言分阶段 | **未触发**(无 to-be-refactored 符号) | §1.3 |
| 4 | 审计三档状态 | **未触发**(全部 `existing`) | §1.3 |
| 5 | composition shell 或直接拆分二选一 | **不拆分,故该二选一的前提不成立、约束不适用**(v1.2 更正措辞:原"均不采"读作在二选一中都不选,逻辑上不通) | §1.3 三条理由 |
| 6 | `find_iframe_src`/`_IframeParser`/`_attrs_to_map` 层位随完整闭包裁定;htmlutil 由真实复用面决定 | **执行**:三者**随 gbs_report 留 skill**;**不建 htmlutil** | 实测:①`find_iframe_src`(:125)/`_IframeParser`(:191)**仅 gbs_report 内部引用**(唯一调用点 :72),**零跨模块引用**;②`_attrs_to_map` 两处独立定义(gbs_report:349 / qb-discover sources:279,返回类型 `dict` vs `Mapping` 不同),**无跨模块调用**。**依据(v1.2 更正为结构性,不再以"目前无跨模块调用"反推)**:两侧解析件
虽同名,但**数据模型与闭包已分化**——`_attrs_to_map` 返回类型不同
(`dict` vs `Mapping`)、各自服务于不同的表结构语义(GBS 报表 vs QuickBuild
概览),**不存在稳定的公共契约**可供抽取;强行合并须先统一数据模型,那是
行为变更。故 htmlutil 无存在依据;新建它等于制造一个**契约未定型**的共享
模块。(注:"当前零跨模块调用"仅为佐证,不作主依据) |
| 7 | inventory 与公共面护栏同进同出 | **执行** | commit C 同一 commit 恢复 21 行 inventory + 集合等价护栏 |

**未触发项的纪律**:约束 1/3/4/5 的"未触发"在 DoD 中**逐条列出并附 §1.3
依据**,不得静默省略——它们是 step-0 用七轮换来的输入,关门须留痕。

## §3 三项具名延期的合并议题裁决(skill-2 八组 + skill-3 D1 + skill-4 D2)

skill-2 §1.1 将 8 组同名件(gbs_report ↔ qb-discover sources)的合并/去重
登记为"triage-report 批次的可选议题,由那时同时持有两侧上下文的批次裁决"。
**本批同时持有两侧,裁决如下**:

- **实测现状**:8 组各 2 处独立定义(行号见 §0.1 twin 表);`_attrs_to_map`
  返回类型不同(`dict` vs `Mapping`);其余多数字节相近但**分属两个已冻结
  的 skill**;
- **裁决:不合并,议题关闭**。理由:①合并 = 制造 qb-discover ↔ triage-report
  **横向依赖**或新建 shared 模块——前者违 skill-independence,后者是**无
  第二消费者以外的共享物**(仅两个 skill 用,且各自已稳定);②合并属**行为
  变更**(至少类型签名),抽取批不得顺手做;③两侧已各自冻结,合并须重开
  两批设计——**成本远超收益**(8 个 HTML 解析小件);
- **登记为"已裁决关闭,非延期"**:不进 P4.9 末批次清单。

### 3.1 skill-3 D1 与 skill-4 D2(v1.2 补,BLOCKER 关门)

二者与 skill-2 议题**同类同源**(均为"同名 helper 是否合并"),且**均具名
指向 triage-report**:
- **skill-3 D1**(closeout:246):同名 Gerrit/report helper——实测
  `_run_git`(3 处)、`_git_stdout`(3 处)等,分属 gerrit-fetch / gerrit-submit /
  build-verify / shared,**与本批两模块无一重叠**;
- **skill-4 D2**(closeout:160):同名 build/report/formatter helper——八组
  twin 分属 build-verify / patch-suggest / 编排层,**与本批两模块的重叠仅
  §3 已裁的八组**(gbs_report ↔ qb-discover)。

**裁决:三项统一按 §3 同一理由关闭**(不合并;合并将造横向依赖或无第二
消费者的共享物,且属行为变更须重开相关批次设计)。**本批同时持有 D1/D2
所涉全部模块的冻结契约**(gerrit-fetch v1.3.1 / gerrit-submit v1.3.2 /
build-verify v1.12.1 均已 CLOSED,其 twin 计数各自在册),故有条件一次关账。
**三项均登记为"已裁决关闭,非延期",不进 P4.9 末批次清单**;末批清单
维持 5 项不变(shim 删除、测试私有件收窄、悬空 symlink、timeout 统一、
protected marker 顺序)。
- **本批的关闭权(v1.1 补,评审问)**:skill-2 §1.1 原文将该议题登记为
  "**triage-report 批次的可选议题,由那时同时持有两侧上下文的批次裁决**"
  ——**授权对象与授权内容均具名指向本批**,且本批确实同时持有两侧
  (gbs_report 侧本批抽取、qb-discover 侧已冻结在册)。故本批**有权作出
  包括"不合并"在内的任一裁决**;登记该议题的 skill-2 冻结稿在其
  closeout 中亦无"必须合并"的约束。**若评审方认为关闭需 skill-2 侧确认,
  可在本批终审时由三家一并背书**(本稿不预设该要求)。

## §4 门禁

- root-layers skill 层 **6→7**;skill-independence **6→7 成员**;forbidden
  扩列;**无具名例外**(零跨包;`gbs_patch_suggest` 配置不动);
- **三条负控制**:①skill 内 `import ci_triage` → root-layers 红;②skill 内
  `import tizen_qb_discover` → independence 红(**与 8 组 twin 的宿主
  skill 直接对垒,最有意义的一条**);③shared 内 import 本 skill → forbidden 红;
- 正向:全部契约绿;skill→shared 下行(quickbuild_http / types)单列,
  **与负控制③配对**。

## §5 测试与 parity

- 新建 `tests/unit/test_tizen_triage_report.py`;三类边界分节;包根 9 正向 +
  15 `not hasattr`(排除子模块名);
- **分支表(v1.2 落成真实表;每行必有代码锚,实现期回写用例名)**:

| 契约句 | 分支(代码锚) | 用例 |
|---|---|---|
| fetch 成功 | `fetch_gbs_report` 返回 `GbsReport`(:94) | |
| 报表页登录态 | `_raise_if_login_page`(:70) | |
| iframe 缺失 | `NO_GBS_REPORT`(:74-78) | |
| iframe 页登录态 | `_raise_if_login_page`(:81) | |
| parse 无 build-status 表 | `_looks_like_build_status_table` 未命中(:146) | |
| 单包日志下载成功 | `download_gbs_package_buildlog`(:103 起) | |
| 单包日志:登录态 | (:118) | |
| 单包日志:URL 缺失/构造失败 | (:112) | |
| `render_report` 有 evidence | `report.py` | |
| `render_report` 无 evidence | `report.py`(`_primary_location` 空路径) | |
| **arch 场景 A/B** | 见 §5 ⑧ 两场景 | |
**仅固化现状**;实测与预期不符 → 停止报告,不改生产代码;
- **⑧ arch:透传维度一例(v1.1 裁定,不留实现期裁量)**。实测 `arch` 出现
  于 dataclass 字段(`GbsReportPackage:34` / `GbsReport:46`)、函数参数
  (`fetch_gbs_report:58`)、URL 拼装(`:68`)与错误消息(`:76`),
  **无任何分支逻辑**。故本批既不同于 skill-4(arch 有判定分支 → 必须矩阵),
  也不同于 skill-1/2/3/5(arch 完全不出现 → 有据豁免),**属第三种:
  透传维度**。裁定(v1.2 更正为**两场景**;v1.1 的"一例同时断言错误消息"**不可执行**
  ——成功路径不产生 :76 的 `NO_GBS_REPORT`):**同一个非默认 arch 值
  `standard-armv7l`,两个场景**:
  - **场景 A(成功)**:断言该值原样出现在①请求 URL(:68)②`GbsReport.arch`
    (:96)③**每个 `GbsReportPackage.arch`**(:328,经 :149 `_row_to_package`
    ——与②是**两条不同路径**,一条链路跑通不保证两处都被断言到);
  - **场景 B(iframe 缺失)**:断言 `NO_GBS_REPORT` 错误消息(:76)含同一
    arch 值。
  **样例值须带 `standard-` 前缀**:这把"无归一化"的否定断言编进了正向用例
  的输入选择——将来若有人照 skill-4 加 `removeprefix("standard-")`,URL 断言
  立即失败(比单列否定断言更不易被绕过:否定断言可删,此断言一删整个用例
  即失效)。不做多架构矩阵(无分支可覆盖)。**该口径入 skill 模板**,供后续批次复用。
- **pre-shim parity**(取证早于合流)。**载荷五项(v1.2 枚举)**:
  ①`GbsReport` 全字段(含 `packages` 逐项 `GbsReportPackage` 全字段);
  ②fake fetcher 的**有序调用轨迹**(URL + cookies + kwargs);
  ③`TriageReportData` / `render_report` 输出全文;
  ④受控环境输入(`DEFAULT_COOKIE_PATH` 值 / `DEFAULT_QUICKBUILD_BASE_URL`);
  ⑤抛出的异常类型与 code(`QuickBuildError.code`)。
  **唯一掩码**:cookie 路径等环境派生绝对路径 → `<PATH>`,**逐字段施加,
  不做全 payload 全局替换**;**一正三反**(正:仅掩码字段不同→相等;
  反:改 `failed_packages` 集合 / 换 HTTP 调用顺序 / 改 `iframe_url`,
  **变异落非掩码字段**→必红);易变源实测(grep uuid/datetime/time/random);
  fake fetcher **不打真实 QuickBuild**;
- post-shim identity 9+15;三入口 1/1/2/2;两阶段分列;`release-v1.4.0` 不回填。

## §6 机械同步(commit C 先做)

1. shared/quickbuild_http **17 符号**中 declared consumer `ci_triage.gbs_report`
   → `tizen_triage_report.gbs_report`(skill-2 时曾做 `ci_triage.sources` 翻转,
   同型);
2. shared/types 中 `FailedPackage`/`SourceFetchResult` 的消费方
   `ci_triage.report` → `tizen_triage_report.report`;
3. `REGISTERED_SKILL_ROOTS`/`ROOT_LAYERS_HIGH_TO_LOW`/`MODULE_OWNERS`/
   `surface_checks`(**两模块两道护栏**)/ bridge 路径常量 / 源根;
4. **约束 7**:21 行 inventory + gbs_report 护栏**同一 commit** 恢复。

## §7 commit 划分
A₀(继承 ledger,独立数据)→ A(两模块迁移 + 白名单一项 + pre-shim parity)
→ B(测试所有权 + 分支表)→ C(门禁 6→7 + 审计 24 行 + 两护栏 + 约束 7 +
三入口)→ 收口。

## §8 DoD
- [ ] 24 符号 parser-only + bridge 两 definition 路径精确 21/3;
- [ ] gbs_report 模式二仅一处白名单;report 模式一 cmp 空;旧址双纯 shim;
- [ ] **七约束逐条销账**(3 执行 + 4 未触发各附依据);
- [ ] **同名件议题裁决关闭**(§3,非延期);`EDIT_SPEC_SCHEMA` 归宿核实;
- [ ] 8 组 twin 各自注册,精确命令证未合并;
- [ ] 契约绿 + 三负控红 + 下行配对;
- [ ] 分支表逐行用例;pre/post-shim 分列;三入口;两阶段;
- [ ] 双门禁全绿(A₀ 独立数据 + 前批回归不退化);
- [ ] **P4.9 末批次清单核实**:本批**不新增**延期项(§3 关闭、§0.3 归他批)。

## §9 变更清单纪律(v1.2 新增,两家共提的根因)

**本轮 BLOCKER 与模式矛盾能穿过一轮的共同原因:它们不在变更清单里**——
评审注意力跟着清单走,清单未列即成盲区(Claude Code 原话)。skill-5 立的
"反向清点每轮必做"防的是**删除面**,本次漏的是**未修面**。

**纪律(入 skill 模板)**:每轮修订的变更清单须**同时列出"上轮未闭合
finding 的逐条状态"**(含"本轮未处理"及理由),使**未修项与已修项一样
可见**。本稿自 v1.2 起执行:上轮 findings 逐条状态见修订说明块。

---
## 附:声明
零生产行为变更(两模块逐字节 + 一处 import 白名单);零判据变更;零新机制;
**本批实质 = 关门**:step-0 七约束 3 执行 4 未触发、skill-2 议题关闭、
skill-4 议题归宿核实——**P4.9 抽取阶段的最后一笔欠债在此清零**。
