# P4.9 skill-2 设计:tizen-qb-discover 抽取(v1.3-FROZEN)

- 阶段:P4.9 第二个 skill 批次(skill-1 CLOSED @e7900bb 之后)
- 权威并行:step-0 `v2.1-FROZEN`、skill-1 `v1.4-FROZEN`
> **v1.1 修订(两家评审)**:①【MAJOR,Claude Code】§1.2 的动机**证伪并
> 重设**——symbol_audit 早有 twin-guard(`symbol_audit.py:746`,同名
> 本地实现自动跳过),AST 工具**不会**串台;v1.0 引为理由的"8 件被误
> 报"是我 raw-grep dry-run 脚本的产物,不是工具缺陷。真实风险改锚
> **bridge 的 name-only 解析键**(triage-report 批次注册第二张同名表
> 时碰撞),并**补上唯一能证伪 name-only 键的断言 d**(双侧同时注册、
> 各测各的消费集)。②【NIT-1,Kimi】负 fixture sharpen 为 duplicate-
> SPECS 场景。③§0 贴全 19 行、计数更正(4 外部 / 15 私有,含 8 同名)。
> ④root-layers 去花括号。⑤NIT-4/5:quickbuild_http 的 7 处 declared
> consumers 与 pyproject/mypy_path/审计注册表同批更新。⑥DoD 计数改
> "三负控红 + 一正向回归绿"。
> **v1.3 修订**:§2.2 补为含 `definition` 的 19 行真表格,并要求
> step-0/skill-1 逐符号表同步补列;bridge 二元组键需要正文侧显式
> 提供 definition,原表仅 symbol/owner。

- **总铁律**:行为等价——整体搬移 + import 翻转,零语义变更;基线 ==
  skill-1 收口全量数(847/1),原样全绿。

---

## §0 判据 dry-run(v1.3 新规,冻结前置,已完成)

Claude 实测 @d02a15a,以"规划终态 SPECS(sources.py 19 顶层符号,
owner=skill/tizen_qb_discover)+ 实测消费方"喂入 v1.3 层化判据:

```
  QUICKBUILD_OVERVIEW_CONFIG_ID  <- ['batch_cli.py']  => OK
  _STATUS_CLASSES                <- []  => OK
  FailedBuild                    <- ['orchestrator.py']  => OK
  FailedBuildSource              <- ['orchestrator.py']  => OK
  QuickBuildSource               <- ['batch_cli.py', 'orchestrator.py']  => OK
  _Anchor                        <- [] [same-name twin in gbs_report; AST twin-guard@746 already excludes it]  => OK
  _Cell                          <- [] [same-name twin in gbs_report; AST twin-guard@746 already excludes it]  => OK
  _Row                           <- [] [same-name twin in gbs_report; AST twin-guard@746 already excludes it]  => OK
  _BuildsTable                   <- []  => OK
  _CellBuilder                   <- [] [same-name twin in gbs_report; AST twin-guard@746 already excludes it]  => OK
  _AnchorBuilder                 <- [] [same-name twin in gbs_report; AST twin-guard@746 already excludes it]  => OK
  _BuildsTableParser             <- []  => OK
  _parse_builds_table            <- []  => OK
  _row_to_build                  <- []  => OK
  _status_from_classes           <- []  => OK
  _strip_snapshot_prefix         <- []  => OK
  _attrs_to_map                  <- [] [same-name twin in gbs_report; AST twin-guard@746 already excludes it]  => OK
  _class_names                   <- [] [same-name twin in gbs_report; AST twin-guard@746 already excludes it]  => OK
  _normalize_text                <- [] [same-name twin in gbs_report; AST twin-guard@746 already excludes it]  => OK

[SUMMARY] 19 OK / 0 MISMATCH  (owner=skill/tizen_qb_discover)
[有外部消费方 4 项 / 模块内私有 15 项;其中同名 twin 8 项]
```

结论:**skill owner 全合法**(4 项有外部消费方,全属 ci_triage 编排层,
下行;15 项模块内私有)。**本批零判据变更**——由上述 dry-run 证明,
非检视得出(⑥补强首次正式执行)。注:本 dry-run 用 raw-grep 估算消费
方,故对同名 twin 需人工剔除;**symbol_audit 的 AST 实现无此问题**
(twin-guard@746),两者差异见 §1.2。

## §1 关键发现:8 个与 gbs_report **同名不同源**的私有件(高危)

实测:`sources.py` 与 `gbs_report.py` **无任何 import 关系**,却各自
独立定义同名 HTML 解析件:
`_Anchor` `_Cell` `_Row` `_CellBuilder` `_AnchorBuilder`
`_attrs_to_map` `_class_names` `_normalize_text`

实现比对:`_normalize_text` 逐字节相同;`_attrs_to_map` 返回类型不同
(`Mapping[str,str]` vs `dict[str,str]`);`_class_names` 有差异——
**是历史平行演化的两份实现,不是共享**。

### 1.1 裁决:严禁合并、严禁抽公共件

- 两套同名件**各随各模块走**:sources 侧随 qb-discover,gbs_report 侧
  留 ci_triage(属 triage-report 批次);
- **`_normalize_text` 即使逐字节相同也不合并**——合并会在两个 skill
  之间制造共享点,反噬 skill-independence;且触碰 gbs_report =
  越界(§1.3);
- 合并/去重诉求登记为 **triage-report 批次的可选议题**,由那时同时
  持有两侧上下文的批次裁决,本批不动。

### 1.2 bridge 键碰撞加固(v1.1 重设动机)

**先澄清一个非缺陷(v1.0 错误动机的更正)**:`symbol_audit.py:746` 已
有 twin-guard——`if symbol in source.top_level: continue`,任何自身
定义同名顶层符号的模块被自动排除,故 AST 审计**不会**把 gbs_report
误算为 sources 私有件的消费方(两家实测确认,`_actual_consumers` 对
8 件均返回 `()`)。v1.0 §1.2 引用的"误报"是本设计 §0 raw-grep 脚本
的产物,**不是工具缺陷**;以不存在的缺陷论证工具变更违反本项目⑩/⑭
标准,故动机重设如下。

**真实风险(未来态,现在治便宜)**:`table_audit_bridge` 与 SPECS 的
`specs_by_name` 按**符号名**建键。本批后仓内已有两组同名符号,当
triage-report 批次把 gbs_report 侧同名件也注册进 SPECS/正文表时,
name-only 键将**碰撞**(后者覆盖前者或解析歧义),且 `_audit_one` 的
cross-boundary caller 查找可能取错 spec。

**变更**:SPECS 与 bridge 的匹配键由"符号名"改为
**(定义模块路径, 符号名)** 二元组。

**断言四条(⑮:判据/索引变更必配防滥用与正确性断言)**:
a. **回归锁定**:变更后 step-0 42+4 与 skill-1 35 项判定逐条不翻转
   (verdict_changes=0)——索引精化非判据放松;
b. **duplicate-SPECS 负 fixture,触发机制定死为方案 B(Kimi NIT-3)**:
   现审计**没有**"skill owner 的 definition 必须位于注册 skill root"
   这条规则(`REGISTERED_SKILL_ROOTS` 目前只服务 module-scope 断言 a),
   故 v1.1 描述的 fixture 按现实现**红不了**。本批**新增该规则**:
   `owner` 以 `skill/` 开头时,其 `definition` 路径必须落在
   `REGISTERED_SKILL_ROOTS` 中对应 root 之下,否则
   `MISMATCH: skill-owned symbol defined outside its registered root`。
   fixture 即"同名、definition=ci_triage/gbs_report.py、owner=skill/
   tizen_qb_discover" → 因 root 不匹配而红,红因明确为**归属规则**;
   该新增规则同受断言 a 的回归锁定约束(不得翻转任何既有判定);
c. **同名共存正向**:sources 侧 `_attrs_to_map` 在册、gbs_report 侧
   不在册时,前者判 OK 且不受后者存在影响;
d. **【决定性,Claude Code 补】双侧同时注册辨别断言**:把 sources 侧
   与 gbs_report 侧的 `_attrs_to_map` **同时注册进 SPECS/bridge**
   (后者用临时 fixture spec),断言二者**各自测得自己的消费集、
   互不覆盖**——这是**唯一在 name-only 键下必然失败**的断言,即本
   变更的存在性证明;name-only 实现必红、二元组实现必绿。

**bridge 跨表重复检查同步改造(Kimi NIT-4)**:`table_audit_bridge`
现以纯名字交集判重(`body.keys() & skill_body.keys()` → PARSE_ERROR),
triage-report 批次注册同名件时会**误报**;本批一并改为
**`(definition, symbol)` 相同才判重**,名字相同而定义模块不同视为
合法共存(断言 d 覆盖此路径)。

**已知限制(NIT,登记不修)**:twin-guard 会 over-skip——某模块若既
遮蔽同名又真实 import 了原件,其真实消费将被漏计;对本批 8 个私有件
不可达,且二元组键也不解决该问题,登记入工具 known-limits 注释——**写进 `symbol_audit.py` 源码注释**
(不只设计稿),防后续维护者把 over-skip 当 bug 修掉(Kimi NIT-5)。

### 1.3 边界写死:gbs_report 整模块不许碰

step-0 已裁定 gbs_report.py 整模块 out-of-scope、归 triage-report 批次
(含 fetch/parse 拆分与七条继承约束)。**本批对 gbs_report.py 零 diff**
(DoD 硬项);其同名私有件、HTTP 消费方式一律不动。

## §2 skill 物理形态与迁移

### 2.1 布局

```
tizen-qb-discover/
  SKILL.md
  scripts/tizen_qb_discover/
    __init__.py     # 薄导出:仅 §2.3 三公开符号 + 配置常量
    sources.py      # 现 ci_triage/sources.py 整体迁入(288 行,逐行搬移/cmp)
```

PYTHONPATH 与 pyproject packages 增 `tizen-qb-discover/scripts` /
`tizen_qb_discover`;C21 的 glob 派生自动纳入(无需改测试基建,
skill-1 commit D 的收益兑现)。

### 2.2 逐符号注册(19 行,纯逐符号;不用 module-scope)

理由同 skill-1:公开契约有逐行冻结诉求 + 同文件两制互斥(修订-7
断言③)。表由脚本自源码机械生成(⑩):

| symbol | definition | owner |
|---|---|---|
| QUICKBUILD_OVERVIEW_CONFIG_ID | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _STATUS_CLASSES | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| FailedBuild | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| FailedBuildSource | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| QuickBuildSource | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _Anchor | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _Cell | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _Row | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _BuildsTable | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _CellBuilder | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _AnchorBuilder | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _BuildsTableParser | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _parse_builds_table | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _row_to_build | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _status_from_classes | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _strip_snapshot_prefix | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _attrs_to_map | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _class_names | tizen_qb_discover/sources.py | skill/tizen_qb_discover |
| _normalize_text | tizen_qb_discover/sources.py | skill/tizen_qb_discover |

旧址 `ci_triage/sources.py` 变**纯 re-export shim**(零 def/class),
入 shim 删除清单(P4.9 末)。INCOMPLETE 护栏覆盖 skill 包 sources.py
公共面(护栏跟模块走)。

### 2.3 公开契约(SKILL.md 机器侧)

| symbol | 契约 |
|---|---|
| `FailedBuild` | 发现结果类型(字段冻结如现状) |
| `FailedBuildSource` | Protocol:失败构建来源抽象 |
| `QuickBuildSource` | QuickBuild 实现,消费 shared/quickbuild_http |
| `QUICKBUILD_OVERVIEW_CONFIG_ID` | 配置常量(batch_cli 消费) |

**无私有跨界**(与 skill-1 不同,本批不需要别名契约)——实测三公开
符号 + 一常量即全部对外面。

### 2.4 依赖方向

`tizen_qb_discover.sources` → `tizen_ci_shared.quickbuild_http`
(skill→shared,下行合法,root-layers 已表达);消费方
orchestrator/batch_cli ∈ ci_triage(编排→skill,下行合法)。
**零上行、零横向**。

## §3 门禁

1. **root-layers 增列**:`ci_triage > tizen_convergence_judge | tizen_qb_discover > tizen_ci_shared`
   (import-linter 2.3 同层语法**不带花括号**,Kimi NIT-3);须验证
   重写后 ci_triage→skills→shared 三层结构完整、两 skill 同层;
2. **skill-independence 首次启用**(step-0/skill-1 的 DEFERRED 关门项
   到期——independence 需 ≥2 模块,本批满足):
   `modules = tizen_convergence_judge, tizen_qb_discover`;
3. **forbidden 扩列**:shared 不得 import `tizen_qb_discover`;
4. **负控制(exit code 全入 dev_memory)**:
   ①qb-discover 内临时 `import ci_triage` → root-layers 红;
   ②qb-discover 内临时 `import tizen_convergence_judge` →
     **skill-independence 红(本条是该契约的首次实测,⑭)**;
   ③shared 内临时 `import tizen_qb_discover` → forbidden 红;
   ④既有契约正向仍绿(5→6 契约,以实跑为准)——**此条为正向回归,非
     负控制**;independence 对称,①②③中 qb→convergence 一条即证激活,
     反向由同一 contract 保证(备述一行)。

## §4 审计与 parity

- SPECS/bridge 扩展:§2.2 的 19 行入 SPECS;bridge 解析本稿 §2.2 表;
  **bridge 键加固(§1.2)与四条断言**同批落地;双道全绿(symbol 侧
  预期 77+19=96 量级,以实跑为准);
- parity:同 fixture 双跑 `QuickBuildSource` 的发现流程(HTTP 层用
  既有测试 fixture/fake fetcher,不打真实网络),输出掩码后逐字节
  一致;
- **⑧ 基数维度**:本 skill 维度 = 状态类(failed/successful/cancelled)
  × 表格解析分支(有表/无表/畸形行);arch 维度 grep 实测为零(证据
  入档,有据豁免)。

## §5 commit 划分(每 commit 全量 + lint 双绿)

- **A(审计工具)**:SPECS/bridge 键改二元组 + 四条断言(a 回归锁定 /
  b duplicate-SPECS 负 fixture / c 同名共存正向 / d 双侧注册辨别)——
  **先于抽取**,使工具在同名共存出现前即具备正确键;
- **B(抽取主体)**:建 skill 包 + sources.py 整体迁移(先 cmp 后动)
  + 旧址纯 shim + 消费方翻转(orchestrator/batch_cli/测试);
- **C(门禁与登记)**:**先做机械同步**(Kimi NIT-4/5,漏则全量审计必红):
  ①`shared/quickbuild_http` 7 符号的 declared consumers
  `ci_triage.sources` → `tizen_qb_discover.sources`;**①b 第 8 处
  (Claude Code MINOR):`MODULE_OWNERS["ci_triage.sources"]`
  (symbol_audit.py:518)——本批经实测为 inert(sources 只 import
  stdlib+shared,不触发该路径),但仍须**显式处置**:更新为
  `tizen_qb_discover.sources` 或标注 verified-inert 并留审计痕迹,
  不得让已迁移模块的引用静默留在域归属表中;②symbol_audit 的
  `REGISTERED_SKILL_ROOTS` / `ROOT_LAYERS_HIGH_TO_LOW` 加
  `tizen_qb_discover`;③pyproject 的 `packages` **与 `mypy_path`** 均加;
  然后 root-layers 增列 + **skill-independence 首次
  启用** + forbidden 扩列 + 三条负控制红 + 一条正向回归绿 + 19 行入 SPECS + bridge +
  SKILL.md + arch 豁免证据 + parity。

## §6 DoD

- [ ] 全量 == 847/1 基线,原样全绿;测试 diff 仅 §5.1 两类;
- [ ] **gbs_report.py 零 diff**(§1.3 硬项;`git diff --stat` 中
      **单独列出该文件为空**,防全局格式化顺手改到,Kimi NIT-2);
- [ ] 同名件未合并:两侧各存一份,`_normalize_text` 仍两处(grep 自证
      "不合并"被执行,而非顺手去重);
- [ ] **bridge 键加固四条断言**:回归锁定 verdict_changes=0、
      duplicate-SPECS 负 fixture 红、同名共存正向 OK、**双侧同时注册
      辨别断言绿(且在 name-only 键下可复现为红)**;
- [ ] 旧址 sources.py 零 def/class;
- [ ] 六契约正向绿 + **三条负控制红 + 一条正向回归绿**(含
      skill-independence 首测,Kimi NIT-7);
- [ ] 双道审计全绿(96 量级);parity 掩码一致;⑧ arch 豁免证据;
- [ ] SKILL.md 落盘;shim 清单更新;
- [ ] **DEFERRED**:同名件合并/去重议题 → triage-report 批次;
      shim 删除 → P4.9 末。

---
## 附:与既有机制的关系
零新机制;唯一工具变更 = symbol_audit 的**同名索引加固**(§1.2,配
四条断言,且 dry-run 已证不影响现有判定);skill-independence 由
DEFERRED 转正式启用(⑯ 转正闸门兑现)。
