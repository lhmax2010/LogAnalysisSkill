# P4.9 skill-4 设计:tizen-build-verify 抽取(v1.0-draft)

- 阶段:P4.9 第四个 skill 批次(skill-3 CLOSED @1ca2206 / 签批 @92111c4 之后)
- 权威并行:step-0 `v2.1-FROZEN`、skill-1 `v1.4-FROZEN`、skill-2 `v1.3-FROZEN`、
  skill-3 `v1.3.1-FROZEN`
- **基线**:`883 passed, 1 skipped`(skill-3 建立;本批含补测,新基线以实测记录,
  遵"既有集合不缩小且无失败,非总数冻结")
- **总铁律**:行为等价——逐字节迁移 + import 翻转,零语义变更

---

## §0 三面判据 dry-run(v1.3 新规,冻结前置,已完成)

Claude 实测 @92111c4:

```
=== 面1: build_verify.py (29 符号) ===
  SubprocessRunner             prod=['campaign_repair_step.py', 'gerrit.py', 'gerrit_submit.py', 'runner.py'] test=['test_gerrit_fetch.py']
  BuildVerifyOptions           prod=['campaign_repair_step.py', 'cli.py'] test=['test_build_verify_real_git.py', 'test_campaign_repair_step.py', 'test_ci_triage_entrypoints.py']
  BuildVerifyResult            prod=['campaign_repair_step.py'] test=['test_campaign_repair_step.py', 'test_ci_triage_entrypoints.py']
  build_verify                 prod=['campaign_repair_step.py', 'cli.py'] test=['test_build_verify_real_git.py', 'test_campaign_repair_step.py', 'test_ci_triage_entrypoints.py']
  _format_and_apply_patch      prod=[] test=['test_build_verify_real_git.py']
  _git                         prod=[] test=['test_campaign_reconcile.py', 'test_campaign_repair_step.py', 'test_gerrit_submit.py', 'test_verify_workspace.py']
  _git_stdout                  prod=['campaign_repair_step.py', 'gerrit_submit.py'] test=[]
  _read_json                   prod=['cli.py'] test=[]
  _sha256_file                 prod=['campaign_repair_step.py'] test=[]
  _build_subprocess_env        prod=['runner.py'] test=[]
  build_verify_to_json         prod=['cli.py'] test=[]

=== 面2: edit_spec_guard.py (12 符号) ===
  EDIT_SPEC_SCHEMA             <- ['test_patch_suggest.py']
  EditSpecViolation            <- ['__init__.py', 'build_verify.py']
  validate_edit_spec           <- ['__init__.py', 'build_verify.py']
  _is_relative_to              <- ['workspace.py']

=== 面3: 外部包依赖 ===
  gbs_patch_suggest.formatter <- build_verify.py:25 (FormatPatchOptions, format_patch)
  gbs_patch_suggest 自身: 零 ci_triage / 零 tizen_ci_shared 依赖(可下行,不循环)
  注: gbs_patch_suggest 经 subprocess 调 gbs_analyzer(静态门禁盲区)
```

### 0.1 twin 辨明留痕(⑩,raw-grep 初判经定义点核销)

**五组同名 twin,均为各自独立顶层定义,非跨界消费**:

| 符号 | 独立定义处 | 本批处置 |
|---|---|---|
| `_git_stdout` | build_verify:556 / gerrit_submit:332 / campaign_repair_step:1273 | 3 处,各随各模块 |
| `_read_json` | build_verify:589 / cli:397 | 2 处 |
| `_sha256_file` | build_verify:596 / campaign_repair_step:1269 | 2 处 |
| `_build_subprocess_env` | build_verify:608 / runner:372 | 2 处 |
| `_is_relative_to` | edit_spec_guard:160 / shared/workspace | 2 处(第三次遇到) |
| `SubprocessRunner` | build_verify 及仓内多处同形别名 | 仅本冲突面计 |

**严禁合并**(沿 skill-2 `_normalize_text`、skill-3 `_run_git` 先例):签名/语义
已分化者合并即语义变更;字节相同者合并制造跨模块耦合。二元组键(skill-2)与
import-binding 追踪(skill-3)在本批**首次同时应对五组 twin**。

### 0.2 生产侧跨界面(实测,比预期干净)

生产代码对 build_verify 的消费**仅公开面**:`BuildVerifyOptions`/
`BuildVerifyResult`/`build_verify`(campaign_repair_step、cli)、
`build_verify_to_json`(cli);对 edit_spec_guard 仅 `EditSpecViolation`/
`validate_edit_spec`(build_verify、verify/__init__)。
**唯一私有件跨界**:`tests/unit/test_build_verify.py:9` 直接 import 私有实现
——抽取后翻转到 skill 私有路径(测试改动仅 import 行,§5.1 边界内)。

**结论:本批零归属判据变更**(由 dry-run 证明,非检视得出)。

## §1 skill 形态:一个 skill 两个模块(首次)

```
tizen-build-verify/
  SKILL.md
  scripts/tizen_build_verify/
    __init__.py        # 薄导出:仅 §1.2 公开面
    build_verify.py    # 现 verify/build_verify.py 整体迁入(636 行,cmp)
    edit_spec_guard.py # 现 verify/edit_spec_guard.py 整体迁入(165 行,cmp,S-2b)
```

**逐符号注册 41 行**(build_verify 29 + edit_spec_guard 12),三列
`symbol | definition | owner`,**两个 definition 路径**——bridge 首次解析
"同一 skill 两个 definition"的表,须验证二元组键在此形态下正确(见 §4)。

### 1.1 旧址处置(双址纯 shim)
- `ci_triage/verify/build_verify.py` → 纯 re-export shim(零 def/class);
- `ci_triage/verify/edit_spec_guard.py` → 同上;
- `verify/__init__.py` 的 re-export 面(现转出 edit_spec_guard 两符号)保持
  可用,随 P4.9 末统一清理;
- **迁移副本注释复核**(skill-3 N-A 通则):逐字节迁移会继承注释,须核对
  两文件内是否有在新位置语义反转的注释(如 shim 字样),发现即在 commit 中
  修正注释文字(不触碰代码行为)并留痕。

### 1.2 公开契约(SKILL.md 机器侧)

| symbol | 契约 |
|---|---|
| `build_verify` | 核心:本地构建验证(三道物理闸第一道) |
| `BuildVerifyOptions` / `BuildVerifyResult` | 输入/输出类型 |
| `build_verify_to_json` | 结果落盘 |
| `default_extra_pythonpath` | 默认 PYTHONPATH 派生 |
| `EditSpecViolation` / `validate_edit_spec` | edit-spec 校验(S-2b 随本 skill) |

其余 33 项为**包根不导出的实现符号**(概念三分:实测消费面 / 包根公开面 /
不导出面,沿 skill-3 §2.1 口径,数字各在定义节出现一次)。

## §2 门禁:具名例外放行 skill → gbs_patch_suggest(本批唯一机制变更)

**事实**:`build_verify.py:25` 现有
`from gbs_patch_suggest.formatter import FormatPatchOptions, format_patch`。
`gbs_patch_suggest` 是**独立 skill**(开发者确认),非 shared、非六抽取
skill 之一,当前 `.importlinter` **零覆盖**。

**裁决:采方案 (d) 具名例外,不重定义其层级**
- `gbs_patch_suggest` **保持 skill 身份**,不塞入底座层;
- skill-independence 契约"六 skill 互不依赖"**不放宽**;
- **新增一条具名例外**:允许 `tizen_build_verify → gbs_patch_suggest.formatter`
  **单向、单模块**;理由入档:build-verify 需 patch 格式化能力,系**既有生产
  事实**(:25),抽取只是把隐含依赖显式化;
- **拒绝方案 (b)**(把它当底座层)的理由写入设计:那会使"skill 不许横向"
  可被"把某 skill 挪到底层"绕过——**规则的例外须显式登记,不得靠重新定义
  概念消化**(step-0 gbs_report"受控例外"先例)。

**known-limitation(新登记)**:`gbs_patch_suggest` 经 **subprocess 调
`gbs_analyzer`**(`analyzer_runner.py`),该依赖是运行时路径依赖,
**import-linter 等静态门禁不可见**。本批不处理,登记为门禁盲区,防后续
误以为"静态全绿=无跨包依赖"。

**负控制(本批新增第 4 条)**:临时让**另一个 skill**(如 qb-discover)
`import gbs_patch_suggest` → **必须红**(证明例外是具名的、未泛化为
"所有 skill 都能用")。

## §3 ⑧ 三架构测试矩阵(本批不可豁免)

前三批 arch 维度均"有据豁免"(grep 零命中)。**本批实测 `arch` 命中 6 处**
(`BuildVerifyOptions.arch:69`、`_gbs_arch:389`、构建命令拼装 :384 等),
build-verify 是唯一真正跑多架构的 skill,**豁免不成立**。

**矩阵维度**(非笛卡尔积,每维至少一例):
- **arch**:三架构(以 P4.5 账本既有架构集为准,实现期按实测枚举钉定)
  × `_gbs_arch` 的 `standard-` 前缀剥除行为;
- **结果态**:成功 / 构建失败(classify 分类)/ patch 应用失败 / edit-spec 违规;
- **worktree 态**:tracked 变更检测(`_tracked_worktree_mutated`)、
  allowed paths 越界(`_allowed_paths`)。

**纪律**:全部固化现状,任一实测与预期不符 → **停止报告**,不改生产代码。

## §4 审计与 bridge(两模块形态)

- 41 行入 SPECS(两个 definition 路径);
- **bridge 首次解析"一 skill 两模块"表**——DoD 硬项:bridge 输出中
  **两个 definition 路径的行都出现**(自证条件沿 skill-3:输出含该对象条目,
  非仅总绿);
- **五组 twin 二元组键实测**:各组贴各自注册行与消费集;未合并由**限定
  作用域的精确命令**证明(skill-3 N-C 通则:`rg '^def X\(' --glob` 形态,
  并说明仓库级计数差异);
- shared 侧 declared consumers 更新:`classify`/`env`/`state`/`workspace`
  的消费方 `ci_triage.verify.build_verify` → `tizen_build_verify.build_verify`
  (机械同步,漏则审计红)。

## §5 parity 与交付面(沿用既立范式,不新增机制)

- **pre-shim parity**(取证于改 shim 之前):同 fixture 双跑 `build_verify`
  (fake subprocess runner,不跑真实 GBS),§5.2 载荷穷举 + 唯一掩码
  (**逐字段施加**,不全局替换)+ **一正三反 normalizer**;双跑隔离用
  `importlib.reload` 或子进程;
- **post-shim identity**:公开面 + 迁移符号逐项 `is`(只证接线);
- **三入口交付面**:pyproject(packages + mypy_path)/ ci.yml mypy 清单 /
  README PYTHONPATH;四条**精确计数自检**(先在已完成 skill 样本上跑
  1/1/2/2);`release-v1.4.0/` 不回填;
- **两阶段验证**:B 临时脚手架 / C `pip install -e .` 后 `env -u` 无脚手架
  复跑,证据分列。

## §6 commit 划分(每 commit 全量 + lint 双绿)

- **A(抽取主体)**:建包 + 两模块迁移(先 cmp)+ pre-shim parity + 双址
  纯 shim + 消费方翻转 + 注释语义复核;
- **B(测试所有权)**:新建 `tests/unit/test_build_verify_skill.py`(命名待
  定,避免与既有 `test_build_verify.py` 冲突——**实现期先确认现有文件归属
  再定**);§3 矩阵落该文件;三类边界分节(skill 行为 / 编排集成 / legacy
  wiring);包根导出正反测试;
- **C(门禁与审计)**:root-layers 增列 + independence 扩四成员 + forbidden
  扩列 + **§2 具名例外** + 四条负控制(含例外未泛化)+ 41 行入 SPECS +
  bridge 接入与双路径自证 + 三入口 + SKILL.md + 两阶段收口。

## §7 DoD

- [ ] 全量:既有集合不缩小、无失败;新基线如实记录;
- [ ] 两模块 cmp 逐字节;双址纯 shim(零 def/class);
- [ ] 41 符号三列入册;**bridge 输出含两个 definition 路径的行**;
- [ ] 五组 twin:各自注册 + 限定作用域精确命令证未合并;
- [ ] **§2 具名例外生效** + **例外未泛化负控制红**;subprocess 盲区登记;
- [ ] **§3 三架构矩阵**逐维有例(arch 豁免本批不适用);
- [ ] pre-shim parity(一正三反)与 post-shim identity 分列;
- [ ] 三入口 1/1/2/2;两阶段证据分列;`release-v1.4.0` 不回填声明;
- [ ] 迁移副本注释语义复核留痕;
- [ ] **DEFERRED**:`test_build_verify.py` 私有件消费面收窄(若保留私有
  路径 import)→ P4.9 末;其余沿既有四项。

---
## 附:零生产行为 + 零归属判据变更声明
- **零生产行为变更**:两模块逐字节迁移,业务行为不变;
- **零归属判据变更**:§0 dry-run 证明;
- **本批机制新增(必须做)**:§2 的具名例外契约 + 其未泛化负控制;
- **非抽取交付项**:三入口同步、§3 三架构矩阵补测、注释语义复核、
  subprocess 盲区登记。
