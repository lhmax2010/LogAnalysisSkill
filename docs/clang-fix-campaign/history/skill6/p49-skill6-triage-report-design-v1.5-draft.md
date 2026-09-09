# P4.9 skill-6 设计:tizen-triage-report 抽取 + gbs_report 关门(v1.5-draft)

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
>
> **v1.3 修订(两家均不 freeze-ready;Codex 4 MAJOR / Claude Code 2 MAJOR
> + 2 MINOR,收敛在同两处)**:①【MAJOR,两家共提】**§3.1 关账论证重写**
> ——实测两个"八组"**交集为空**、skill-4 八组在本批两模块**零出现**,
> v1.2 的"重叠仅八组"是事实错误;且"持有冻结契约"≠ skill-2 授权条件的
> "持有两侧上下文"(对 D1/D2 本批哪一侧都不持有)。改用**"维持 vs 改变"
> 的不对称性**论证;②【MAJOR,两家共提】**§5 分支表补漏 + 找回删除项**:
> 补 `:82-86 GBS_REPORT_DOWNLOAD_FAILED`、`_row_to_package` **四个 None
> 分支**(:313/:317/:320/:323,v1.1 的"畸形行"整行在 v1.2"落成真实表"时
> **被删**——重写丢失,与 skill-4 v1.1 同型);更正 `:117-121` 为 **HTTP
> 非 200**(非登录页)、`:112` 为**仅 URL 缺失**(无构造失败);
> ③【MAJOR】**arch 场景 A 补 packages 非空断言**(空 tuple 会真空通过);
> ④【MAJOR】parity 补 `download_gbs_package_buildlog` 返回文本、异常
> **message** 比较,掩码改**穷举**(删"等");⑤【MINOR,第三轮未闭合】
> §6-1 待翻转**实测 7 条**(非 17;17 是模块符号总数);⑥【MINOR】§9 纪律
> 措辞钉死为"**全部**未闭合 finding(含 MINOR/NIT)逐条列状态";
> ⑦引言/§0.2/DoD/附录的下游漂移同步(七行台账、D1/D2 显式写入);
> ⑧**新增 §10 重写反向清点纪律**(两家共提的更深根因)。
>
> **上轮未闭合 finding 逐条状态(§9 首次完整执行,含 MINOR)**:
> 模式矛盾=闭合;`EDIT_SPEC_SCHEMA`=闭合;约束 5/6=闭合;arch 两场景=
> 本轮补非空断言后闭合;§3.1 论证=本轮重写;§5 分支表=本轮补 6 行;
> parity=本轮补 2 项;§6-1 条数=本轮闭合(第三轮);§9 覆盖面=本轮钉死。
>
> **v1.4 修订(两家不 freeze-ready;Codex 3 MAJOR / Claude Code 1 MAJOR +
> 1 MINOR。收敛点:问题全在 `report.py` 侧——两家上轮均只盯 gbs_report)**:
> ①【MAJOR,Codex】**`EDIT_SPEC_SCHEMA` 双重管辖自相矛盾**:§3.1 把它列入
> D2 八组统一"不合并关闭",§0.2 又保留其"单一权威→patch-suggest"——
> **单一权威必然结束双定义,不能同时"不合并"**;改为 **D2 按七个非 schema
> twin 关闭,`EDIT_SPEC_SCHEMA` 显式排除、继续由原 D1 管辖**;
> ②【MAJOR,两家共提】**§5 report.py 侧失守**:`render_report` 实测 **20 处
> 条件渲染**(:45–:111)、`_primary_location` **三态**(:121/:123/:124)被压成
> 两行且**零代码锚**——违本表自订"每行必有代码锚";补锚 + **明写两个
> fixture 构造原则(全字段齐备 / 全字段缺失)** 以形成真假双侧覆盖 +
> `_primary_location` 单列三态;③【MAJOR,Codex】**parity 补
> `GbsReport.failed_packages`**——它是 **computed property**(:51-53),不在
> "全字段"内;只改该过滤逻辑可使六项 payload 完全相同而"改 failed_packages
> 必红"落空;④【MAJOR,Codex + MINOR,Claude Code】**§5 补
> `_status_from_anchor` 五态 / `_looks_like_build_status_table` 三态 /
> `_row_to_package` href 有无 / `failed_packages` 过滤**;⑤【NIT】引言
> "skill-2/skill-4 各一项"与七项台账不一致;⑥**新增 §11 分支表准入检查**
> (Claude Code 建议:**声明每模块分支点总数并与 AST 枚举对账,模块级缺项
> 即红**——治"枚举不完整",与 §10 治"重写丢失"并列)。
>
> **v1.5 修订(两家不 freeze-ready:1 BLOCKER + 2 MAJOR / 2 MAJOR,判在同
> 两处)**:①【BLOCKER/MAJOR,两家共提】**§11 的 13/23 不成立且口径不唯一**
> ——Claude 按同一"枚举面"实跑得 gbs_report **24** / report.py **4**;
> 两家各得 18–19 / 23;**三方四个数字全不同,证明"枚举面"定义本身不唯一**,
> 脚本无唯一实现、门禁无法机械执行。改为:**精确 AST selector + branch ID +
> 两种口径分列 + 首次声明值由脚本实跑产出(不得手填)**;
> ②【MAJOR,两家共提】**A/B fixture 对五个嵌套条件的"假"侧不可达**
> (:62 嵌于 :53-else;:77/:81/:83/:85 嵌于 :70-else;B 折叠外层后内层
> **根本不执行**)——补 **C/D 两个 fixture**,并把原则改写为**嵌套逐层剥离**;
> ③【MAJOR,Codex】`_status_from_anchor` **class 优先未被验收**——补
> **冲突样本**(class=`failed` + text=`Succeeded` → 断言 `failed`)与
> `successful` 别名;④【NIT】§0.2/DoD/附录写全"D2 七个非 schema twin";
> ⑤**新增元规则**(Claude Code 提,与 skill-4 §5.4.1-4 同族):**任何"声明
> 数值并与机械枚举对账"的检查,首次声明值必须由该检查的脚本实跑产出,
> 不得人手填;首版声明与首次实跑同轮完成,否则该检查不算落地**。

- **本批双重身份**:①第六个 skill 的抽取;②**step-0 §8 砍出的 gbs_report
  整模块的关门批次**(七条约束 + **三项具名合并议题**:skill-2 八组、
  skill-3 D1、skill-4 D2(限七个非 schema twin);`EDIT_SPEC_SCHEMA` 单一
  权威议题**不在本批**,归 patch-suggest)

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
检出**七项具名欠债**(v1.3 更正:v1.2 称"五类"但表列七行),本批须逐项关门:

| 欠债 | 来源 | 本批处置 |
|---|---|---|
| gbs_report **七条约束** | step-0 §8 | §2 逐条销账 |
| fetch/parse 拆分 + `GbsReportPackage`/`GbsReport` 类型归属 | step-0 §8 | §1.3 裁决 |
| iframe 抽取闭包 + `_attrs_to_map`/htmlutil 层位 | step-0 §8 约束 6 | §1.3 裁决 |
| **同名件合并议题**(8 组) | skill-2 §1.1 | §3 裁决 |
| **同名 Gerrit/report helper 合并** | **skill-3 D1**(closeout:246,具名 triage-report) | §3 裁决(v1.2 补) |
| **同名 build/report/formatter helper 合并** | **skill-4 D2**(closeout:160,具名 triage-report extraction batch) | §3.1 裁决:**限七个非 schema twin**(`EDIT_SPEC_SCHEMA` 排除,归 D1) |
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
指向 triage-report**(skill-3 closeout:246 / skill-4 closeout:160)。

**实测重叠面(v1.3 更正 v1.2 的事实错误)**:
- skill-4 D2 的八组(`SubprocessRunner`/`_git_stdout`/`_read_json`/
  `_sha256_file`/`_build_subprocess_env`/`_is_relative_to`/**`EDIT_SPEC_SCHEMA`
  (v1.4 显式排除,见下)**/`_locate_edit`)与本批(skill-2)八组(`_Anchor`/`_Cell`/`_Row`/
  `_CellBuilder`/`_AnchorBuilder`/`_attrs_to_map`/`_class_names`/
  `_normalize_text`)**交集为空**;实测 skill-4 八组在 gbs_report.py 与
  report.py **零出现**;
- skill-3 D1 涉 `_run_git`×3 与 `SubprocessRunner` 冲突面,同样**与本批两
  模块零重叠**;
- 故正确表述是:**D1/D2 与本批两模块重叠为零**(v1.2 写"重叠仅八组"错,
  两者只是碰巧都是八组)。

**关闭权论证(v1.3 重写;v1.2 的"持有全部模块冻结契约故可一次关账"不成立
——持有冻结契约 ≠ skill-2 授权条件所要求的"同时持有两侧上下文",对 D1/D2
本批哪一侧都不持有)**:

> **"维持"与"改变"的不对称性**。三个登记方的冻结稿**本身即已裁定"严禁
> 合并"**(skill-2 §1.1「裁决:严禁合并、严禁抽公共件」、skill-3 §1.3、
> skill-4 §3 同款);DEFERRED 登记的是"**是否改变该裁决**"这一可选议题。
> 本批作为被具名的关门批次作出的是**"维持现状、不改变"**的裁决——它
> **不推翻任何一方**,因而**不需要任何一方的工作上下文**。若裁决为"合并",
> 才需要持有上下文并重开三批设计,而那正是被否决的选项。

**机械背书(v1.3 补,与 §4 扣合)**:该"不合并"现状**已被门禁物理锁定**——
各批 DoD 的 twin 计数断言 + **skill-independence 契约**(本批 §4 负控制②:
skill 内 `import tizen_qb_discover` → 红)。**关闭只是把可选议题正式收档,
不改变任何可执行状态**;将来若有人为"复用"去 import,契约立刻转红。

**`EDIT_SPEC_SCHEMA` 显式排除(v1.4,MAJOR)**:该符号同时受两条 DEFERRED
管辖——skill-4 D2("同名 helper 是否合并")与 skill-4 的另一条
"**`EDIT_SPEC_SCHEMA` 单一权威**→patch-suggest 批次"(§0.2 台账)。
**二者结论互斥**:"单一权威"必然结束双定义,与"不合并关闭"直接冲突。
**裁决**:D2 **按七个非 schema twin 关闭**;`EDIT_SPEC_SCHEMA`
**排除在本批关闭范围之外,继续由"单一权威"那条 D1 管辖、归 patch-suggest
批次**(与 §0.2 一致)。理由:它的双定义是**跨包 schema 版本标识**的双权威
(两处同值,一侧升版即静默失配),与其余七组"同名实现件各自独立"性质不同,
不适用"维持现状"的关闭逻辑。

**裁决:三项关闭(不合并;D2 限七个非 schema twin),登记为"已裁决关闭,非延期"**,不进 P4.9
末批次清单;末批清单维持 **5 项**(shim 删除、测试私有件收窄、悬空
symlink、timeout 统一、protected marker 顺序)。

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
| **iframe HTTP 非 200** | **`GBS_REPORT_DOWNLOAD_FAILED`(:82-86)**(v1.3 补:独立错误码,v1.2 漏) | |
| 单包日志:buildlog_url 缺失 | `GBS_PACKAGE_LOG_MISSING`(:112-115)(v1.3 更正:**仅 URL 缺失**,无"构造失败") | |
| 单包日志:HTTP 非 200 | `GBS_PACKAGE_LOG_DOWNLOAD_FAILED`(:117-121)(v1.3 更正:**非登录页**,该函数无登录检测) | |
| **畸形行跳过 ×4**(v1.3 找回:v1.1 有"畸形行",v1.2 重写时被删) | `_row_to_package` 四个 `return None`:cells<3(:313)/ 表头行 `package name`(:317)/ 无 status anchor(:320)/ status 解析失败(:323) | |
| `render_report` **A:全部可选字段齐备** | `render_report`(:35),覆盖 **20 处条件渲染的"真"侧**(:45/:47/:49/:53/:62/:64/:66/:70/:77/:81/:83/:85/:89/:91/:93/:100/:102/:104/:108/:111) | |
| `render_report` **B:全部可选字段缺失** | 同上,覆盖 20 处条件的**"假"侧**(含 :53/:70 的 `else` 分支) | |
| `_primary_location` 态一:file+line | `f"{file}:{line}"`(:121) | |
| `_primary_location` 态二:仅 file(line 缺失) | `return file_value`(:123)(v1.4 补:v1.3 表中无) | |
| `_primary_location` 态三:无 file | `return "n/a"`(:124) | |
| `_status_from_anchor` class 优先(failed / succeeded) | `class_names` 命中(:337/:339) | |
| `_status_from_anchor` text 回退(failed / succeeded) | 文本命中(:343/:345)(**只用 class 型 anchor 的用例永不走此路径**) | |
| **`_status_from_anchor` class 优先冲突样本**(v1.5 补,MAJOR) | class=`failed` + text=`Succeeded` → **断言结果为 `failed`**(:337 先于 :343);**text-first 的错误实现在此必红**——仅"class 命中"样本无法证伪它 | |
| **`successful` 别名**(v1.5 补) | `succeeded`/`successful` 两写法均命中(:339 class 侧、:345 text 侧) | |
| `_looks_like_build_status_table` 三态 | status-anchor 命中 / header fallback / 均不命中(:287 起) | |
| `_row_to_package` 成功态 href 有 / 无 | `buildlog_url` 由 `status_anchor.href` 决定(:326) | |
| `GbsReport.failed_packages` 过滤 | computed property(:51-53):含 failed 与非 failed 混合样本 | |
| **arch 场景 A/B** | 见 §5 ⑧ 两场景 | |
**fixture 构造原则(v1.5 更正为"嵌套逐层剥离";A/B 两个不够)**。
**实测问题**:`render_report` 的条件是**嵌套**的——`:62` 嵌于 `:53` 的
`else`;`:77`/`:81`/`:83`/`:85` 嵌于 `:70` 的 `else`。fixture B(全部
置空)使 `:53`/`:70` 走 **True** 分支,内层五个条件**根本不被求值**——
不是"走了假侧",而是**不可达**;而覆盖率未测时 A/B 两用例照样全绿、
DoD"逐行有用例"照样通过(**安全阀依赖实现者恰好想到查嵌套可达性,
正是本 campaign 一直在消除的依赖**)。

**四个 fixture(v1.5 钉死)**:
- **A 全字段齐备**:覆盖 20 条件的"真"侧;
- **B 全字段缺失**:覆盖**外层**条件的"假"侧(`:53`/`:70` 的 True 分支);
- **C 外层在、内层缺**:`selected_package` 存在但 `dest_file` 空;
  `source_fetch` 存在但 `change=None`、`error` 空 → 覆盖 **:62 / :77 / :85**
  的假侧;
- **D 中层在、末层缺**:`source_fetch` 与 `change` 均存在,但 `number=None`、
  `matching_patchset=None` → 覆盖 **:81 / :83** 的假侧。

**原则表述**:**嵌套条件须逐层剥离**——每层外层条件为真时,内层条件的
真假两侧各需一个 fixture;**不得以"全有/全无"两极端冒充双侧覆盖**。
实现期若发现第五层或互斥字段,仍**单列并停止报告**(该安全阀保留,但不再
是唯一防线)。
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
    (:96)③**先断言 `packages` 非空**(v1.3 补,MAJOR:空 tuple 会使"每个 package"
    真空通过),再逐项断言 **`GbsReportPackage.arch`**(:328,经 :149 `_row_to_package`
    ——与②是**两条不同路径**,一条链路跑通不保证两处都被断言到);
  - **场景 B(iframe 缺失)**:断言 `NO_GBS_REPORT` 错误消息(:76)含同一
    arch 值。
  **样例值须带 `standard-` 前缀**:这把"无归一化"的否定断言编进了正向用例
  的输入选择——将来若有人照 skill-4 加 `removeprefix("standard-")`,URL 断言
  立即失败(比单列否定断言更不易被绕过:否定断言可删,此断言一删整个用例
  即失效)。不做多架构矩阵(无分支可覆盖)。**该口径入 skill 模板**,供后续批次复用。
- **pre-shim parity**(取证早于合流)。**载荷**六项**(v1.3 补至穷举)**:
  ①`GbsReport` 全字段(含 `packages` 逐项 `GbsReportPackage` 全字段)
    **+ 派生属性 `failed_packages` 的有序 tuple**(v1.4 补,MAJOR:它是
    **computed property**(:51-53)、不在 dataclass 字段内;只改该过滤逻辑
    可使其余 payload 完全相同,而"改 `failed_packages` 集合必红"的负控制
    落空——**不得以 `packages` 字段间接代替**);
  ②fake fetcher 的**有序调用轨迹**(URL + cookies + kwargs);
  ③`TriageReportData` / `render_report` 输出全文;
  ④受控环境输入(`DEFAULT_COOKIE_PATH` 值 / `DEFAULT_QUICKBUILD_BASE_URL`);
  ⑤抛出的异常**类型 + code + message**(`QuickBuildError.code` 与消息文本,
    v1.3 补 message——错误消息含 build_id/arch/URL,是行为的一部分);
  ⑥**`download_gbs_package_buildlog` 的返回文本**(v1.3 补:v1.2 遗漏该
    公开函数的输出)。
  **唯一掩码(v1.3 穷举,删"等")**:仅 `cookie_path` 的绝对路径 → `<PATH>`;**其余字段一律不掩码**(base_url 为常量、无临时目录、无时间戳——易变源实测确认后若有新增,须显式增列并说明),**逐字段施加,
  不做全 payload 全局替换**;**一正三反**(正:仅掩码字段不同→相等;
  反:改 `failed_packages` 集合 / 换 HTTP 调用顺序 / 改 `iframe_url`,
  **变异落非掩码字段**→必红);易变源实测(grep uuid/datetime/time/random);
  fake fetcher **不打真实 QuickBuild**;
- post-shim identity 9+15;三入口 1/1/2/2;两阶段分列;`release-v1.4.0` 不回填。

## §6 机械同步(commit C 先做)

1. shared/quickbuild_http 中 **declared_consumers 含 `ci_triage.gbs_report`
   的实测为 7 条**(v1.3 钉死;17 是该模块符号总数,非待翻转数):
   `HttpFetcher`、`QuickBuildError`、`_raise_if_login_page`、`_urllib_fetch`、
   `DEFAULT_COOKIE_PATH`、`DEFAULT_QUICKBUILD_BASE_URL`、`load_cookie_jar`
   → 全部翻转为 `tizen_triage_report.gbs_report`(skill-2 时对
   `ci_triage.sources` 同型操作);
2. shared/types 中 `FailedPackage`/`SourceFetchResult` 的消费方
   `ci_triage.report` → `tizen_triage_report.report`;
3. `REGISTERED_SKILL_ROOTS`/`ROOT_LAYERS_HIGH_TO_LOW`/`MODULE_OWNERS`/
   `surface_checks`(**两模块两道护栏**)/ bridge 路径常量 / 源根;
4. **约束 7**:21 行 inventory + gbs_report 护栏**同一 commit** 恢复。

## §7 commit 划分
A₀(继承 ledger,独立数据;**新增 `branch_inventory.py` 实跑产出 §11 声明值与 branch ID 全集**)→ A(两模块迁移 + 白名单一项 + pre-shim parity)
→ B(测试所有权 + 分支表)→ C(门禁 6→7 + 审计 24 行 + 两护栏 + 约束 7 +
三入口)→ 收口。

## §8 DoD
- [ ] 24 符号 parser-only + bridge 两 definition 路径精确 21/3;
- [ ] gbs_report 模式二仅一处白名单;report 模式一 cmp 空;旧址双纯 shim;
- [ ] **七约束逐条销账**(3 执行 + 4 未触发各附依据);
- [ ] **三项同名件议题裁决关闭**(§3 skill-2 八组 + §3.1 **skill-3 D1** +
      **skill-4 D2 的七个非 schema twin**,非延期,论证按"维持 vs 改变"
      不对称性;`EDIT_SPEC_SCHEMA` **排除**、归 D1 → patch-suggest);
      `EDIT_SPEC_SCHEMA` 归宿核实(两处同值);
- [ ] 8 组 twin 各自注册,精确命令证未合并;
- [ ] 契约绿 + 三负控红 + 下行配对;
- [ ] 分支表逐行用例;pre/post-shim 分列;三入口;两阶段;
- [ ] 双门禁全绿(A₀ 独立数据 + 前批回归不退化);
- [ ] **P4.9 末批次清单核实**:本批**不新增**延期项(§3 关闭、§0.3 归他批)。

## §9 变更清单纪律(v1.2 新增,两家共提的根因)

**本轮 BLOCKER 与模式矛盾能穿过一轮的共同原因:它们不在变更清单里**——
评审注意力跟着清单走,清单未列即成盲区(Claude Code 原话)。skill-5 立的
"反向清点每轮必做"防的是**删除面**,本次漏的是**未修面**。

**纪律(入 skill 模板)**:每轮修订的变更清单须**同时列出"上轮**全部**未
闭合 finding(含 MINOR/NIT)的逐条状态"**(含"本轮未处理"及理由),使
**未修项与已修项一样可见**。
**v1.3 措辞钉死**:v1.2 首次执行时**只覆盖 MAJOR/BLOCKER**,把仍开着的
§6-1 MINOR 漏在状态行外——**该纪律在 MINOR 面上重演了它要治的病**。
故明确:**全部级别**逐条列状态。**建议(留末批)**:为 finding 分配稳定 ID,
断言"本轮状态 ID 集合 ⊇ 上轮未闭合 ID 集合",使其不再依赖人工记忆。

## §10 重写反向清点纪律(v1.3 新增,两家共提的更深根因)

**规律**:凡"**重写**"(而非增补)一节,都是丢失的高发点——
skill-4 v1.1 重写丢机械同步清单;skill-5 v1.3 重写分支表(接住了);
**本批 v1.2 把 §5 从要点罗列"落成真实表"时,丢了 v1.1 已有的"畸形行"一行**
(而那一轮的标题恰是"每行必有代码锚")。

**纪律**:**任何一节从"要点罗列"改写为"结构化表格/清单"时,须逐条比对
旧版要点,缺一即红**——它比"每轮反向清点"更具体,因为重写是丢失的高发点。
本稿 §5 的"畸形行"即由此纪律找回。

## §11 分支表准入检查(v1.4 新增;治"枚举不完整",与 §10 并列)

**规律(连续三轮)**:分支表的问题总出在**注意力没扫到的那一侧**——
v1.2 漏 `:83`(gbs_report 第二个错误码)、丢"畸形行"(parser 侧);
**v1.3 gbs_report 侧 13 行全对,而 report.py 整体失守**(20+3 分支压两行、
零锚)。§10 治的是"重写丢失",本条治的是"**枚举不完整**",两者不同源。

**准入检查(冻结前必过;v1.5 重写为机械可执行)**:

**1. 精确 selector(脚本唯一实现的前提)**。v1.4 的 13/23 不可执行——三方
按"同一"枚举面各自实跑得 **24/4**(Claude)、**18–19/23**(Claude Code)、
**15+2+2+4+5 / 22**(Codex),**四个数字全不同**,证明"全部 raise + 返回
None/多态返回 + 条件渲染"这句话不是 selector。故钉死为**两种口径分列、
不得相加**:

| 口径 | AST selector | 排除 |
|---|---|---|
| **decision_points** | `ast.If` ∪ `ast.IfExp` ∪ comprehension `ifs` | `_ReportTableParser` / `_IframeParser`(HTMLParser 回调,非契约面) |
| **terminal_outcomes** | `ast.Raise` ∪ `ast.Return` | 同上 |

**branch ID** = `qualname:lineno:kind`(如 `_row_to_package:318:return`),
分支表每行须引用 ≥1 个 branch ID。

**2. 首次声明值由脚本产出(v1.5 元规则,不得手填)**:本节**不书写具体
数字**;A₀ 脚本 `branch_inventory.py` 对两模块实跑,产出
`{{module: {{decision_points: N, terminal_outcomes: M, ids: [...]}}}}` 存入
数据文件;**分支表所引 branch ID 集合 ⊆ 脚本产出的 ID 全集,且未被任何行
引用的 ID 须显式登记为"无独立可观测行为"并附理由**;模块级缺项即红。
——立规依据:v1.4 的 13 沿用了评审方在**另一套口径**下给的数字,且已被
v1.4 §5 新增四行推翻;**"规则正确、同节手写的实例错误"第四次**
(skill-4 §5.4 三次 + 本节),故与 skill-4 §5.4.1-4「本节不得出现任何手写
的具体值」采同一治法。

**3. 元规则(入模板,与 §10/§11 并列)**:**任何"声明数值并与机械枚举
对账"的检查,其首次声明值必须由该检查的脚本实跑产出,不得由人手填;
首版声明与首次实跑同轮完成,否则该检查不算落地**。

---
## 附:声明
零生产行为变更(两模块逐字节 + 一处 import 白名单);零判据变更;零新机制;
**本批实质 = 关门**:step-0 七约束 3 执行 4 未触发;**skill-2 八组、skill-3 D1、
skill-4 D2(七个非 schema twin)三项议题关闭**;`EDIT_SPEC_SCHEMA` 归宿核实(归 patch-suggest)——**P4.9 抽取阶段的最后一笔欠债在此清零**。
