# P4.9 skill-5 设计:tizen-gerrit-submit 抽取(v1.0-draft)

- 阶段:P4.9 第五个 skill 批次(skill-4 CLOSED @7bfa070 / 签批 @8ed7588)
- 权威并行:step-0 `v2.1`、skill-1 `v1.4`、skill-2 `v1.3`、skill-3 `v1.3.1`、
  skill-4 `v1.12.1`(均 FROZEN)
- **基线**:`897 passed, 1 skipped`(skill-4 建立;遵"既有集合不缩小且无失败")
- **总铁律**:行为等价——逐字节迁移 + import 翻转,零语义变更
- **门禁**:**直接继承 skill-4 的 A₀**(`design_drift_ledger.py`),语料按
  §5.4.4 生成规则从本批版本序列产出,**不重造**(skill-4 签批已立此规则)

---

## §0 判据 dry-run(冻结前置,已完成)

Claude 实测 @8ed7588:

```
[dry-run] 规划 SPECS 23 符号 (owner=skill/tizen_gerrit_submit)

  SubprocessRunner             <- ['build_verify.py', 'campaign_repair_step.py', 'gerrit.py', 'runner.py']  => MISMATCH
  GerritSubmitOptions          <- ['cli.py']  => OK
  GerritSubmitResult           <- []  => OK
  ReleaseWorktreeResult        <- []  => OK
  gerrit_submit                <- ['cli.py']  => OK
  _target_head_unknown_warning <- []  => OK
  release_verified_worktree    <- ['cli.py']  => OK
  write_gerrit_submit_result   <- ['cli.py']  => OK
  write_release_result         <- ['cli.py']  => OK
  exit_code_for_submit         <- ['cli.py']  => OK
  exit_code_for_release        <- ['cli.py']  => OK
  _verification_mismatch       <- []  => OK
  _dirty_reason                <- []  => OK
  _target_warnings             <- []  => OK
  _target_branch               <- []  => OK
  _push_command                <- []  => OK
  _remote_url                  <- []  => OK
  _git_stdout                  <- ['build_verify.py', 'campaign_repair_step.py']  => MISMATCH
  _run_git                     <- ['gerrit.py', 'workspace.py']  => MISMATCH
  _result                      <- ['campaign_repair_step.py']  => OK
  _record_result               <- []  => OK
  _build_id_from_failure_key   <- []  => OK
  _subprocess_env              <- []  => OK

[SUMMARY] 23 OK / 0 MISMATCH  [外部消费 11 / 私有 12]
[twin] 0 组: []
[依赖] tizen_ci_shared.state(下行) + tizen_ci_shared.workspace.release_worktree_protection(下行);零 ci_triage 内部 import;零跨包
```

### 0.1 twin 辨明留痕(⑩;raw-grep 初判 3 处 MISMATCH,经定义点核销)

| twin | 独立定义处 | 处置 |
|---|---|---|
| `SubprocessRunner` | build_verify / runner / gerrit_submit / campaign_repair_step / gbs_workflow / gbs_patch_suggest(**6 处**) | 同形类型别名,各随各模块 |
| `_git_stdout` | gerrit_submit / campaign_repair_step / build_verify(**3 处**) | 签名分化,各随各模块 |
| `_run_git` | gerrit_submit / shared-workspace / gerrit_fetch(**3 处**) | **第四次遇到**,沿既有裁决 |
| `_result` | gerrit_submit / campaign_repair_step(**2 处**) | campaign_repair_step 自有定义,非消费 |

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
  `verify/__init__.py` re-export 面随之调整;
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

其余 14 项为**包根不导出的实现符号**(三概念口径沿 skill-3:实测消费面 /
包根公开面 / 不导出面,数字各在定义节出现一次)。

## §2 门禁

1. **root-layers 增列第五个 skill**;**skill-independence 扩五成员**;
   **forbidden 扩列**(shared 不得 import 本 skill);
2. **无具名例外**(§1.1:零跨包依赖)——`gbs_patch_suggest` 相关配置不动;
3. **三条负控制**(exit code 入 dev_memory):①skill 内临时 `import ci_triage`
   → root-layers 红;②skill 内临时 `import tizen_build_verify` →
   skill-independence 红(五成员后首次实测);③shared 内临时 import 本 skill
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
  - **悬空 symlink 归一化(设计)**:`path.exists() and path.is_symlink()`
    的判定改为 `path.is_symlink()`(悬空链接 `exists()` 为 False 会被跳过,
    现状是**静默放行**),使 `SOURCE_DIR_UNSAFE` 覆盖悬空态;
  - **实施批次**:**P4.9 末的"跨 skill 行为统一批次"**(与 shim 删除同批,
    该批本就允许行为变更、且届时六 skill 全部抽完、影响面可一次性 parity);
    **本批将该批次登记为具名关门批次,并附上述两项设计**;
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
  ③`release_worktree_protection` 对悬空 symlink 的**现状行为**锁定;
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
2. `shared/state` 各符号中以 gerrit_submit 为消费方的条目同步翻转;
3. `REGISTERED_SKILL_ROOTS` / `ROOT_LAYERS_HIGH_TO_LOW` 加 `tizen_gerrit_submit`;
4. `MODULE_OWNERS` 新增条目;
5. **`surface_checks` 硬编码接入**(仅加源根不会启用护栏,skill-4 教训);
6. **bridge 冻结稿路径常量**加 skill-5 正文;
7. symbol_audit 源根新增 `tizen-gerrit-submit/scripts`;
8. **A₀ 数据文件**:语料按 §5.4.4 规则从本批版本序列产出;binding 清单
   覆盖本稿"定义节→下游引用"对。

## §7 commit 划分

- **A₀**(冻结前置):继承 `design_drift_ledger.py`,产出本批语料与 binding,
  **准入证伪**(对本批某一早期版本快照必红)+ per-binding 证伪;
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
