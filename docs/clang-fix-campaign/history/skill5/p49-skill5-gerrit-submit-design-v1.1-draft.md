# P4.9 skill-5 设计:tizen-gerrit-submit 抽取(v1.1-draft)

- 阶段:P4.9 第五个 skill 批次(skill-4 CLOSED @7bfa070 / 签批 @8ed7588)
- 权威并行:step-0 `v2.1`、skill-1 `v1.4`、skill-2 `v1.3`、skill-3 `v1.3.1`、
  skill-4 `v1.12.1`(均 FROZEN)
- **基线**:`897 passed, 1 skipped`(skill-4 建立;遵"既有集合不缩小且无失败")
> **v1.1 修订(三家评审;三条 MAJOR 全为可机械核验的事实错误,Claude 实测
> 逐条坐实)**:①**`SubprocessRunner` 8 处**(v1.0 写 6,**漏掉
> `tizen_gerrit_fetch/gerrit.py:22`——那是 skill-3 冻结稿亲自登记过的一处,
> 等于跨批次丢了一条已冻结登记**;且把 gbs_patch_suggest 的两处并成一处);
> ②**§4③ 现状锁定打错对象**——`release_worktree_protection` **零 symlink
> 逻辑**(实测),真正对象是 `tizen_gerrit_fetch/gerrit.py:237-238`;
> **DEFERRED 三项对价中"现状锁定"这一半当场落空**;③**§0 dry-run 自相
> 矛盾**(逐行 3 MISMATCH vs SUMMARY 0;`[twin] 0 组` vs §0.1 四组;
> `_result` 同为 twin 却判 OK)——已按 skill-3 格式**分两趟重跑**;
> ④关门批次章程**改为显式扩展登记**(P4.9 末批次原章程仅"shim 删除",
> "该批本就允许行为变更"**无据**);⑤independence/root-layers 成员
> **5→6**("五成员首次实测"不成立,skill-4 的 N1 已在 5 成员下跑过);
> ⑥§6 第 2 项枚举(实为 3 条 module-scope,且为**计算值非声明值**);
> ⑦两个零消费方公开符号显式裁决;⑧A₀ 准入证伪补构造式回退;
> ⑨symlink 现状描述对齐 skill-3 冻结措辞;⑩§1 空操作句删除;
> ⑪**P4.9 末批次继承项清单**(防其变成新的无限展期容器)。

- **总铁律**:行为等价——逐字节迁移 + import 翻转,零语义变更
- **门禁**:**直接继承 skill-4 的 A₀**(`design_drift_ledger.py`),语料按
  §5.4.4 生成规则从本批版本序列产出,**不重造**(skill-4 签批已立此规则)

---

## §0 判据 dry-run(冻结前置,已完成)

Claude 实测 @8ed7588:

```
=== PASS-1 raw-grep 初判 → PASS-2 twin 核销终判(两趟分列,沿 skill-3 内联留痕格式)===

  SubprocessRunner           raw=['build_verify.py', 'campaign_repair_step.py', 'gerrit.py', 'runner.py']
      → [同名 twin,8 处独立定义:analyzer_runner.py:16, build_verify.py:47, campaign_repair_step.py:81, formatter.py:18, gerrit.py:22, gerrit_submit.py:28, runner.py:39, workflow.py:29;AST 核销后消费方=[]] => OK
  GerritSubmitOptions        <- ['cli.py'] => OK
  GerritSubmitResult         <- [] => OK
  ReleaseWorktreeResult      <- [] => OK
  gerrit_submit              <- ['cli.py'] => OK
  _target_head_unknown_warning <- [] => OK
  release_verified_worktree  <- ['cli.py'] => OK
  write_gerrit_submit_result <- ['cli.py'] => OK
  write_release_result       <- ['cli.py'] => OK
  exit_code_for_submit       <- ['cli.py'] => OK
  exit_code_for_release      <- ['cli.py'] => OK
  _verification_mismatch     <- [] => OK
  _dirty_reason              <- [] => OK
  _target_warnings           <- [] => OK
  _target_branch             <- [] => OK
  _push_command              <- [] => OK
  _remote_url                <- [] => OK
  _git_stdout                raw=['build_verify.py', 'campaign_repair_step.py']
      → [同名 twin,3 处独立定义:build_verify.py:556, campaign_repair_step.py:1273, gerrit_submit.py:332;AST 核销后消费方=[]] => OK
  _run_git                   raw=['gerrit.py', 'workspace.py']
      → [同名 twin,3 处独立定义:__init__.py:205, gerrit.py:227, gerrit_submit.py:341;AST 核销后消费方=[]] => OK
  _result                    raw=['campaign_repair_step.py']
      → [同名 twin,2 处独立定义:campaign_repair_step.py:1066, gerrit_submit.py:356;AST 核销后消费方=[]] => OK
  _record_result             <- [] => OK
  _build_id_from_failure_key <- [] => OK
  _subprocess_env            <- [] => OK

[SUMMARY] 23 OK / 0 MISMATCH(twin 核销后终判;PASS-1 的 raw 命中已逐条核销)
[外部消费 7 / 模块内私有 16]
[twin] 4 组:
   - SubprocessRunner: 8 处 — analyzer_runner.py:16, build_verify.py:47, campaign_repair_step.py:81, formatter.py:18, gerrit.py:22, gerrit_submit.py:28, runner.py:39, workflow.py:29
   - _git_stdout: 3 处 — build_verify.py:556, campaign_repair_step.py:1273, gerrit_submit.py:332
   - _run_git: 3 处 — __init__.py:205, gerrit.py:227, gerrit_submit.py:341
   - _result: 2 处 — campaign_repair_step.py:1066, gerrit_submit.py:356
```

### 0.1 twin 辨明留痕(⑩;raw-grep 初判 3 处 MISMATCH,经定义点核销)

| twin | 独立定义处 | 处置 |
|---|---|---|
| `SubprocessRunner` | **8 处**(v1.1 更正):`analyzer_runner:16`、`build_verify:47`、`campaign_repair_step:81`、`formatter:18`、**`gerrit.py:22`(skill-3 已冻结登记,v1.0 漏)**、`gerrit_submit:28`、`runner:39`、`workflow:29` | 同形类型别名,各随各模块 |
| `_git_stdout` | gerrit_submit / campaign_repair_step / build_verify(**3 处**) | 签名分化,各随各模块 |
| `_run_git` | gerrit_submit / shared-workspace / gerrit_fetch(**3 处**) | **第四次遇到**,沿既有裁决 |
| `_result` | gerrit_submit:356 / campaign_repair_step:1066(**2 处**) | 自有同名定义,raw-grep 假阳 |

**严禁合并**(沿 skill-2 `_normalize_text`、skill-3 `_run_git`、skill-4 八组
先例);二元组键(skill-2)+ import-binding 追踪(skill-3)已能正确区分。

### 0.2 跨批次强制迁移面(⑰补强,skill-4 立;本批首次正式执行)

`grep` 全部已冻结稿中 `owner=本 skill` 的符号:**结果为空**——step-0 未预判
任何符号给 gerrit-submit;`release_worktree_protection` 是本 skill **消费**
的 shared 符号(owner=shared/workspace),**非迁移面**。

**但检出两项本批继承的具名 DEFERRED**(见 §3,skill-3 `v1.3.1` §7):
①悬空 symlink 归一化(`SOURCE_DIR_UNSAFE` 处置);②统一 timeout/取消/
中断清理策略。**二者均具名"gerrit-submit 批次",本批是其关门批次**。

**结论:本批零判据变更、零跨批次强制迁移**(由 dry-run 与 grep 证明)。

## §1 skill 形态(六批里最简)

```
tizen-gerrit-submit/scripts/tizen_gerrit_submit/
  __init__.py     # 薄导出:仅 §1.2 公开面(9 个)
  gerrit_submit.py # 现 verify/gerrit_submit.py 整体迁入(420 行,模式一:逐字节 cmp)
```

- **迁移模式:模式一(逐字节 cmp)**——单模块、无双角色、无锚点行,**不适用
  模式二/三**(skill-4 的三模式判据在此只用第一种);
- 逐符号注册 **23 行**(三列 `symbol | definition | owner`);
- 旧址 `verify/gerrit_submit.py` → **纯 re-export shim**(零 def/class);
  (`verify/__init__.py` **无需调整**:实测其未 re-export 任何 gerrit_submit 符号);
- **迁移副本注释语义复核**(skill-3 N-A 通则);
- **一道 INCOMPLETE 护栏**,判据为**集合等价**(`_top_level_symbols == SPECS`,
  精确 23),配 `MixedCaseAlias` 负 fixture(skill-4 立)。

### 1.1 依赖闭包(双向实测)

**本 skill 依赖**:`tizen_ci_shared.state`(多符号)+
`tizen_ci_shared.workspace.release_worktree_protection` —— **均为 skill→shared
下行,合法**;**零 ci_triage 内部 import、零跨包依赖**(与 skill-4 的
`gbs_patch_suggest` 例外形成对照,本批**无需任何例外契约**)。

**消费本 skill**:7 个公开符号**全部只被 `cli.py` 消费**(单一编排层消费方)。

### 1.2 公开契约(SKILL.md)

| symbol | 契约 |
|---|---|
| `gerrit_submit` | 核心:向 Gerrit 推送已验证 change(三道闸第三道) |
| `GerritSubmitOptions` / `GerritSubmitResult` | 输入/输出类型 |
| `release_verified_worktree` | 释放受保护 worktree |
| `ReleaseWorktreeResult` | 其结果类型 |
| `write_gerrit_submit_result` / `write_release_result` | 结果落盘 |
| `exit_code_for_submit` / `exit_code_for_release` | 退出码映射 |

**零消费方公开符号的显式裁决(v1.1,沿 skill-4 §1.3-4 先例)**:
`GerritSubmitResult` / `ReleaseWorktreeResult` 实测**外部消费方为空**,
仍保留为包根公开面属**显式裁决**(它们是两个公开函数的返回类型,调用方
必需),非沿袭。

其余 14 项为**包根不导出的实现符号**(三概念口径沿 skill-3:实测消费面 /
包根公开面 / 不导出面,数字各在定义节出现一次)。

## §2 门禁

1. **root-layers 增列第五个 skill**;**skill-independence 由 6 成员扩至 7**(v1.1 更正:现有 6 含 skill-4 为具名例外加入的 `gbs_patch_suggest`);root-layers skill 层同步;
   **forbidden 扩列**(shared 不得 import 本 skill);
2. **无具名例外**(§1.1:零跨包依赖)——`gbs_patch_suggest` 相关配置不动;
3. **三条负控制**(exit code 入 dev_memory):①skill 内临时 `import ci_triage`
   → root-layers 红;②skill 内临时 `import tizen_build_verify` →
   skill-independence 红(v1.1 更正:**非"首次实测"**——skill-4 的 N1 已在 6 成员下跑红);③shared 内临时 import 本 skill
   → forbidden 红;
4. **正向证据**:全部契约绿;**skill→shared 下行**(state / workspace)单列
   报告,**与负控制③配对陈述**(正向绿不单独作证,skill-3 立)。

## §3 [本批实质议题] 两项继承 DEFERRED 的处置

skill-3 `v1.3.1` 将二者**具名延期至本批**。**本批是其关门批次,不得空手
再延**——否则 DEFERRED 机制退化为无限展期。

### 3.1 事实基础(实测)

- **timeout**:`gerrit_submit.py` 全文 `timeout` **零命中**;唯一 subprocess
  入口是 `subprocess_runner: SubprocessRunner = subprocess.run`(:75),
  与 skill-3 的 `fetch_source_for_commit` **同形**(无 timeout、
  `TimeoutExpired` 原样传播);与 skill-4 的 `wall_timeout` 一等公民**相反**;
- **悬空 symlink**:本 skill 通过 `release_worktree_protection`(:210)间接
  触及 worktree 保护面;`SOURCE_DIR_UNSAFE` 的判定在 shared/workspace 与
  skill-3 的 `_reset_generated_source_dir`,**本 skill 无自有 symlink 判定**。

### 3.2 裁决:**本批完成设计、实施推迟至专门批次**(理由与新关门批次)

- **不在本批实施**:二者均为**行为变更**,与抽取批次"零语义变更"铁律直接
  冲突(skill-4 已立此纪律:抽取批不得顺手改行为);且其影响面**跨三个
  skill**(gerrit-fetch / build-verify / gerrit-submit)与 shared/workspace,
  在单个抽取批次内实施无法保证 parity;
- **但必须在本批给出设计**(否则违 skill-3 的延期本意):
  - **timeout 统一策略(设计)**:三处 Gerrit/git 外部调用面(skill-3 fetch、
    本 skill submit、shared/workspace 的 `_run_git`)统一引入**可选
    `timeout` 参数 + 超时归一化为具名错误码**(不再让 `TimeoutExpired`
    裸传播);默认值与是否强制由该批次定;
  - **悬空 symlink 归一化(设计)**:`gerrit.py:237` 的
    `path.exists() and path.is_symlink()` 改为 `path.is_symlink()`(悬空链接
    `exists()` 为 False 会被跳过,现状为**落到 `mkdir` 抛 `FileExistsError`**),使 `SOURCE_DIR_UNSAFE` 覆盖悬空态;
  - **实施批次(v1.1 更正为显式章程扩展)**:step-0 §6.2 给 P4.9 末批次的
    原章程仅为"shim 删除清单,统一执行,单 commit"(**行为保持**),
    **"该批本就允许行为变更"无据**。故本批**显式扩展该批次章程**为
    "**shim 删除 + 跨 skill 行为统一**",并规定:两项行为变更以 §3.2 设计
    为输入,**须经该批次自己的设计与评审窗口**(不在本批冻结),
    **且行为统一与 shim 删除至少分 commit 验收**;
  - **P4.9 末批次的当前继承项清单(v1.1 补;防其成为新的无限展期容器)**:
    ①shim 删除(step-0 §6.2 原章程);②测试私有件消费面收窄(skill-4);
    ③悬空 symlink 归一化(本批);④timeout/取消/中断清理统一(本批)。
    **该批次开工前须以本清单为输入做一次 ⑰ 跨批次检查**;
- **本批 DoD 硬项**:二者的**现状必须被测试锁定**(见 §4),否则统一时无
  回归基准。

## §4 分支覆盖与测试所有权

- 新建 `tests/unit/test_tizen_gerrit_submit.py`;三类边界分节(skill 行为 /
  编排集成 / legacy wiring);**包根导出正反测试**(9 正向 identity + 14
  `not hasattr`,**排除子模块名**——skill-4 修订-1 口径);
- **分支表**(契约句 → 分支 → 用例,实现期回写真实用例名):
  推送成功 / 推送失败 / 目标 HEAD 未知警告(:185)/ verification 不匹配
  (:247)/ 工作区 dirty(:264)/ 目标分支解析(:304)/ release 成功 /
  release 失败 / 两个 `exit_code_*` 映射;
- **§3 现状锁定(硬项)**:①**无 timeout**——fake runner 断言**所有
  subprocess 调用均未传 `timeout`**(拦截**全部**传入路径,不只 wrapper;
  skill-3 N2 教训);②`TimeoutExpired` **原样传播**(不归一化);
  ③**悬空 symlink 现状锁定(v1.1 更正对象)**:真正的判定在
  **`tizen_gerrit_fetch/gerrit.py:237-238`**(`path.exists() and
  path.is_symlink()` → `SOURCE_DIR_UNSAFE`);`release_worktree_protection`
  **零 symlink 逻辑**(实测),v1.0 锁错对象、致 DEFERRED 对价落空。
  **本批的现状锁定改为**:在 skill-3 既有用例基础上确认该行为已被锁定
  (若已有则引用其用例名,不重写);**现状描述对齐 skill-3 v1.3.1 冻结
  措辞**——悬空链接 `exists()` 为 False → 不触发 `SOURCE_DIR_UNSAFE`
  → `_reset` 空转 → **`mkdir(exist_ok=True)` 抛 `FileExistsError`**
  (非"静默放行");
- **⑧ arch 豁免**:`arch` 全文实测 **零命中**,维度不存在(非"未覆盖"),
  证据入档——与 skill-1/2/3 同,**与 skill-4 不同**(后者不可豁免)。

## §5 parity 与交付面(沿既有范式,零新机制)

- **pre-shim parity**(取证于改 shim 之前):载荷五项穷举 + **唯一掩码逐字段
  施加** + **一正三反 normalizer**(正:仅路径不同→掩码后相等;反:改
  `status`/换命令顺序/改退出码,变异落非路径部分→必红);
  **易变源冻结**:UUID/时间戳/`GIT_*_DATE`(照 skill-4 口径,实现期实测确认
  有无第四类);双跑隔离用 `importlib.reload` 或子进程;
- **post-shim identity**:9 公开面 + 迁移符号逐项 `is`(**只证接线**);
- **三入口**:pyproject(`packages` + `mypy_path`)/ ci.yml mypy 清单 /
  README PYTHONPATH;**四条精确计数自检**(先在已完成 skill 样本验命令);
  `release-v1.4.0/` **不回填**;
- **两阶段验证**:B 临时脚手架 / C `pip install -e .` 后 `env -u` 无脚手架
  复跑,证据分列。

## §6 机械同步清单(commit C 先做;漏则审计必红)

1. `release_worktree_protection` 的 declared consumer
   `ci_triage.verify.gerrit_submit` → `tizen_gerrit_submit.gerrit_submit`;
2. **`shared/state` 三条 module-scope**(`state/db.py`、`state/keys.py`、
   `state/records.py`):其消费方为**计算值而非声明值**(ModuleScopeSpec 无
   consumers 字段),迁后自动指向新模块——**无 SPECS 条目可改**;
   commit C **实跑确认**输出指向 `tizen_gerrit_submit.gerrit_submit`
   (v1.1 更正:v1.0 写"同步翻转"会让实现者去找不存在的条目);
3. `REGISTERED_SKILL_ROOTS` / `ROOT_LAYERS_HIGH_TO_LOW` 加 `tizen_gerrit_submit`;
4. `MODULE_OWNERS` 新增条目;
5. **`surface_checks` 硬编码接入**(仅加源根不会启用护栏,skill-4 教训);
6. **bridge 冻结稿路径常量**加 skill-5 正文;
7. symbol_audit 源根新增 `tizen-gerrit-submit/scripts`;
8. **A₀ 数据文件**:语料按 §5.4.4 规则从本批版本序列产出;binding 清单
   覆盖本稿"定义节→下游引用"对。

## §7 commit 划分

- **A₀**(冻结前置):继承 `design_drift_ledger.py`,产出本批语料与 binding,
  **准入证伪**(对本批某一早期版本快照必红;**若本批无更早版本,按 §5.4.1-3
  预防性分支改用构造式注入替代**——v1.1 补回退路径)+ per-binding 证伪;
- **A**:抽取主体(模式一 cmp + pre-shim parity + 纯 shim + 消费方翻转);
- **B**:测试所有权 + 分支表 + §3 现状锁定;
- **C**:门禁三扩列 + 三负控制 + 23 行入 SPECS + 护栏 + bridge + 三入口 +
  SKILL.md + 两阶段。

## §8 DoD

- [ ] 全量:897 基线集合不缩小、无失败;新基线如实记录;
- [ ] 模式一 `cmp` 空;旧址零 def/class;
- [ ] 23 符号入册;**bridge 输出含该 definition 路径且计数精确 23**;
- [ ] **一道 INCOMPLETE 护栏为集合等价** + `MixedCaseAlias` 负 fixture 红;
- [ ] 四组 twin 各自注册,限定作用域精确命令证未合并;
- [ ] 契约绿 + **三条负控制红** + §2.4 下行正向与负控制③配对陈述;
- [ ] **§3 两项现状锁定测试**(无 timeout / TimeoutExpired 直传 / 悬空
      symlink 现状)+ **两项设计已登记且新关门批次具名**;
- [ ] pre-shim parity(一正三反)与 post-shim identity **分列**;
- [ ] 三入口 1/1/2/2;两阶段分列;`release-v1.4.0` 不回填;
- [ ] **双门禁继承 A₀ 且全绿**(check + 准入证伪);
- [ ] **DEFERRED**:timeout 统一 + 悬空 symlink 归一化 → **P4.9 末跨 skill
      行为统一批次**;shim 删除 → 同批;其余沿既有。

---
## 附:零生产行为 + 零判据变更声明
- **零生产行为变更**:单模块逐字节迁移(模式一),无白名单差异;
- **零判据变更**:§0 dry-run 证明;**零跨批次强制迁移**(§0.2);
- **零新机制**:门禁继承 A₀,parity/三入口/两阶段沿既有范式;
- **本批实质议题**:§3 两项继承 DEFERRED 的设计与关门批次具名。
