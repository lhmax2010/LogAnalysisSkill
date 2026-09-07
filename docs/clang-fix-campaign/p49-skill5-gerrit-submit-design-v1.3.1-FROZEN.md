# P4.9 skill-5 设计:tizen-gerrit-submit 抽取(v1.3.1-FROZEN)

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
>
> **v1.2 修订(三家 v1.1;四条 MAJOR 全部实测坐实)**:①**成员数改回 5→6**
> (v1.1 正文写 6→7 是**又修出一个错数**,且与本文档修订说明的 5→6 自相
> 矛盾;实测 `.importlinter` 现有 **5** 成员);②**§3.1 的
> "shared/workspace 亦有 symlink 判定"实际删除**(v1.1 变更⑨**声称已修
> 却未执行**,实测 shared 全目录零 symlink,且与本文档 §4③ 直接冲突);
> ③**timeout 现状锁定拆为两条路径**——实测**并非统一原样传播**:
> `_run_git` 裸传播,而 `ls-remote`(:291)捕获 `SubprocessError`(含
> `TimeoutExpired`)转 `target_head_unknown:<exc>` warning 并驱动 :163 的
> `action="dry_run_unverified_remote"`;④**§3.2 timeout 设计补齐 cancellation
> /中断清理/结果映射**(skill-3 延期的是整套策略,v1.1 只给了可选 timeout
> 与错误码,仍属部分空手再延);⑤**A₀ 继承改为"参数化"**(实测脚本 7 处
> 硬编码 skill4:模块 docstring / 版本序列 / `history/skill4` 语料目录 /
> v1.12 冻结名 / draft 文件名模式 / target-corpus 两处 v1.12 断言)
> ;⑥§0 计数分解修正(7 有消费公开 + 2 零消费公开 + 14 私有)、§0.1 标题
> "3 处"→**4 处**;⑦P4.9 末批次加**终止批次条款**;⑧跨稿引用写全
> "skill-4 FROZEN §…"。
>
> **v1.3 修订(两家 freeze-ready;冻结期澄清)**:①§4 warning 分支锚点范围
> 补全至 `:280-299`,并给 branch None 补 `:280`;②A0 脚本硬编码计数由 6
> 更正为 7,逐处穷举;③§3.2 结果映射明确末批 parity 须预先登记
> `timeout=None` 透传 kwarg;④§8 为分支表、结果映射表与门禁成员扩展补
> 三条引用式 DoD,不复述定义节数字;⑤skill 批次模板首次独立入库,确立
> “每行分支须有代码锚”与“引用侧无承重条目即无 binding”。
>
> **v1.3.1 修订(commit C 接入前补正)**:v1.3 漏掉 23 行权威归属表,
> commit C 接入 bridge 时由 fail-closed parser 暴露;此前设计评审四轮未撞到,
> 根因是没有工具实际读取该表。§0 现由源码 AST 机械生成并显式穷举
> `symbol | definition | owner`;所有 skill 批次冻结前必须先过 parser-only。

- **总铁律**:行为等价——逐字节迁移 + import 翻转,零语义变更
- **门禁**:**继承 skill-4 的 A₀**(`design_drift_ledger.py`),**不重造**;
  但**继承 ≠ 直接复用**(v1.3 更正):实测脚本**7 处硬编码 skill-4**
  (模块 docstring / 版本序列 / `history/skill4` 语料目录 / v1.12 冻结名 /
  draft 文件名模式 / target-corpus 两处 v1.12 断言)。**A₀ 的第一项工作是
  将这些参数数据化**——
  语料目录、版本序列、冻结目标、准入快照与必抓 binding 一律**由 skill-5
  独立数据文件提供**;**不得覆盖 skill-4 数据文件**;
  **回归要求(v1.3 扩;参数化改公共执行路径)**:改造后 skill-4 **全部
  门禁与负向证伪**须复跑且不退化——`check` 全绿 + `admission-v19` 仍红 +
  **`negative-fixture out-of-scope-misuse`(47 项)全红 + 全部 22 个
  per-binding `negative-binding` 用例全红**;仅主检查全绿不能证明各负控制
  未退化

---

## §0 判据 dry-run(冻结前置,已完成)

以下 23 行是本批唯一权威归属表,由
`tizen_gerrit_submit/gerrit_submit.py` 顶层 AST 机械生成:

| symbol | definition | owner |
|---|---|---|
| `SubprocessRunner` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `GerritSubmitOptions` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `GerritSubmitResult` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `ReleaseWorktreeResult` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `gerrit_submit` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `_target_head_unknown_warning` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `release_verified_worktree` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `write_gerrit_submit_result` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `write_release_result` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `exit_code_for_submit` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `exit_code_for_release` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `_verification_mismatch` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `_dirty_reason` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `_target_warnings` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `_target_branch` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `_push_command` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `_remote_url` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `_git_stdout` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `_run_git` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `_result` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `_record_result` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `_build_id_from_failure_key` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |
| `_subprocess_env` | `tizen_gerrit_submit/gerrit_submit.py` | `skill/tizen_gerrit_submit` |

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
[外部消费 7 / 无外部消费 16 = 2 零消费公开(§1.2 显式裁决)+ 14 私有]
[twin] 4 组:
   - SubprocessRunner: 8 处 — analyzer_runner.py:16, build_verify.py:47, campaign_repair_step.py:81, formatter.py:18, gerrit.py:22, gerrit_submit.py:28, runner.py:39, workflow.py:29
   - _git_stdout: 3 处 — build_verify.py:556, campaign_repair_step.py:1273, gerrit_submit.py:332
   - _run_git: 3 处 — __init__.py:205, gerrit.py:227, gerrit_submit.py:341
   - _result: 2 处 — campaign_repair_step.py:1066, gerrit_submit.py:356
```

### 0.1 twin 辨明留痕(⑩;raw-grep 初判 **4 处**命中,经定义点逐条核销)

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

下表只描述 SKILL.md 公开契约,不是权威归属表;归属仅以 §0 三列表为准。

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

1. **root-layers 增列第五个 skill**;**skill-independence 由 5 成员扩至 6**(v1.2 更正;实测现有 5:四个已抽 skill + skill-4 为具名例外加入的 `gbs_patch_suggest`);root-layers skill 层同步 5→6;
   **forbidden 扩列**(shared 不得 import 本 skill);
2. **无具名例外**(§1.1:零跨包依赖)——`gbs_patch_suggest` 相关配置不动;
3. **三条负控制**(exit code 入 dev_memory):①skill 内临时 `import ci_triage`
   → root-layers 红;②skill 内临时 `import tizen_build_verify` →
   skill-independence 红(**非"首次实测"**——skill-4 的 N1 已在 5 成员下跑红);③shared 内临时 import 本 skill
   → forbidden 红;
4. **正向证据**:全部契约绿;**skill→shared 下行**(state / workspace)单列
   报告,**与负控制③配对陈述**(正向绿不单独作证,skill-3 立)。

## §3 [本批实质议题] 两项继承 DEFERRED 的处置

skill-3 `v1.3.1` 将二者**具名延期至本批**。**本批是其关门批次,不得空手
再延**——否则 DEFERRED 机制退化为无限展期。

### 3.1 事实基础(实测)

- **timeout(v1.2 更正:并非统一原样传播,实测**两条路径行为不同**)**:
  全文 `timeout` 零命中;唯一注入点是 `subprocess_runner`(:75)。但:
  | 路径 | 现状行为 |
  |---|---|
  | `_run_git`(:341)本地 git | `TimeoutExpired` **裸传播**(与 skill-3 同形) |
  | `_target_warnings` 的 `ls-remote`(:285) | **`:291` 捕获 `(OSError, SubprocessError)`**(含 `TimeoutExpired`)→ 转 `target_head_unknown:<exc>` warning → 驱动 **`:163` `action="dry_run_unverified_remote"`** |
  与 skill-4 的 `wall_timeout` 一等公民相反;**同一模块内两种超时语义并存**
  正是统一批次要解决的对象;
- **悬空 symlink**:本 skill 通过 `release_worktree_protection`(:210)间接
  触及 worktree 保护面;`SOURCE_DIR_UNSAFE` 的判定**唯一位于 skill-3 的
  `_reset_generated_source_dir`(`gerrit.py:237-238`)**;**shared 全目录与
  本 skill 均零 symlink 逻辑**(v1.2 实测更正:v1.0/v1.1 的"判定在
  shared/workspace 与…"为误,v1.1 曾声称修正而未执行)。

### 3.2 裁决:**本批完成设计、实施推迟至专门批次**(理由与新关门批次)

- **不在本批实施**:二者均为**行为变更**,与抽取批次"零语义变更"铁律直接
  冲突(skill-4 已立此纪律:抽取批不得顺手改行为);且其影响面**跨三个
  skill**(gerrit-fetch / build-verify / gerrit-submit)与 shared/workspace,
  在单个抽取批次内实施无法保证 parity;
- **但必须在本批给出设计**(否则违 skill-3 的延期本意):
  - **timeout/cancellation 统一策略(v1.2 补齐;skill-3 延期的是整套策略,
    v1.1 只给了可选 timeout + 错误码,仍属部分空手再延)**:
    ①**调用面清单**:skill-3 `fetch_source_for_commit`、本 skill `_run_git`
    与 `ls-remote`、shared/workspace `_run_git`;
    ②**参数(v1.3 钉死)**:各调用面统一引入**可选 `timeout: float | None`**;
    **默认 `None` = 无 timeout(与现状行为等价,保证末批实施时 parity 可过)**;
    **不强制**——由调用方(wrapper/编排层)注入;
    ③**错误归一化**:超时统一映射为**具名错误码**;**并规定各调用面的
    结果映射**——裸传播型(`_run_git`)转为具名异常;warning 型
    (`ls-remote`)保持 warning 但**码值统一**(现为 `target_head_unknown:
    <exc>`,含原始异常文本,不稳定);
    ④**取消/中断(v1.3 钉死)**:SIGINT/SIGTERM **不捕获、原样传播**(与现状
    一致);**中断清理由调用方(wrapper)负责**,skill 层不引入信号处理;
    ⑤**残留状态(v1.3 钉死)**:超时/中断后 **worktree 与 marker 保持中断
    时刻的状态、不自动回滚**(与 skill-3/skill-4 已冻结的"失败后可能残留"
    契约一致);`release_worktree_protection` 的幂等性保证重试安全;
    ⑥**结果映射表(v1.3 本稿落成,末批只实施)**:
    | 调用面 | 超时(timeout 触发) | 外部中断 | 残留 |
    |---|---|---|---|
    | skill-3 `fetch_source_for_commit` | 具名 `GerritError("FETCH_TIMEOUT")` | 传播 | destination 部分初始化 |
    | 本 skill `_run_git` | 具名 `GerritSubmitError("GIT_TIMEOUT")`(新类型,末批定义) | 传播 | worktree 不变 |
    | 本 skill `ls-remote` | warning 码**统一为 `target_head_unknown:timeout`**(不再含原始异常文本) | 传播 | 无 |
    | shared/workspace `_run_git` | 具名 `WorkspaceViolation("GIT_TIMEOUT")` | 传播 | marker 不变 |
    **末批 parity 须预先把 `timeout=None` 这个透传 kwarg 声明为掩码/白名单
    项**;生产语义等价,但 fake runner 轨迹会新增该 kwarg,不得把它误判为漂移。
    **末批的职责 = 按此表实施 + parity + 评审**;**不得改动本表裁决,除非重开
    设计评审**(v1.2 把这些留给末批"定",B 判为部分空手再延,成立);
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
  - **终止批次条款(v1.3 升级;v1.2 版仍允许"给新关门批次即再延")**:
    **P4.9 末批次是这 4 项的终止批次;未完成即阻塞 P4.9 收口,不得转交
    任何下一批次**。唯一例外是**逐项**在该批次评审中被裁定为"取消"(附
    理由并经三家确认),而非"延期"。
- **本批 DoD 硬项**:二者的**现状必须被测试锁定**(见 §4),否则统一时无
  回归基准。

## §4 分支覆盖与测试所有权

- 新建 `tests/unit/test_tizen_gerrit_submit.py`;三类边界分节(skill 行为 /
  编排集成 / legacy wiring);**包根导出正反测试**(9 正向 identity + 14
  `not hasattr`,**排除子模块名**——skill-4 修订-1 口径);
- **分支表全部契约句逐行有用例**,且每行必有代码锚(行号即证伪手段——
  沿 skill-4 §4 先例)。本表按 v1.3 真实 action 集重写。**首要事实:本
  skill 不执行 push**——`:160`
  `command_argv = _push_command(...)` 只构造,`:167` 存入结果;模块内
  subprocess 调用仅 `:284`(ls-remote)与 `:348`(`_run_git`);**全部 action
  取值中无 pushed/submitted 态**。v1.2 的"推送成功/失败"两支**不存在**,
  已删。

| 契约句 | 分支(代码锚) | 用例(实现期回写) |
|---|---|---|
| 记录不存在 | `action="record_not_found"`(:82) | `test_gerrit_submit_record_not_found` |
| 记录未就绪 | `rejected_not_ready`(:95;另 :103 第二入口) | `test_gerrit_submit_rejects_latest_non_ready`; `test_gerrit_submit_rejects_ready_for_different_verification_id` |
| worktree 缺失 | `rejected_worktree_missing`(:113) | `test_gerrit_submit_rejects_missing_worktree_without_patch_fallback` |
| verification 不匹配 | `rejected_verification_mismatch`(:123) | `test_gerrit_submit_rejects_commit_or_tree_mismatch` |
| worktree dirty | `rejected_worktree_dirty`(:132) | `test_gerrit_submit_rejects_tracked_dirty_worktree`; `test_gerrit_submit_rejects_staged_dirty_worktree` |
| submit 未启用 | `rejected_submit_not_enabled`(:142) | `test_gerrit_submit_submit_mode_is_rejected_without_push` |
| 重复跳过 | `skipped_duplicate`(:152) | `test_gerrit_submit_skips_duplicate_submission_key`; `test_gerrit_submit_skips_duplicate_before_unverified_remote_action` |
| dry-run(远端已验证) | `dry_run`(:163,`remote_unknown=False`) | `test_gerrit_submit_dry_run_returns_command_without_push` |
| dry-run(远端未验证) | `dry_run_unverified_remote`(:163,`remote_unknown=True`,由 :185 `target_head_unknown` 前缀触发) | `test_gerrit_submit_marks_dry_run_unverified_when_ls_remote_fails`; `test_gerrit_submit_marks_dry_run_unverified_when_ls_remote_raises`; `test_gerrit_submit_converts_ls_remote_timeout_to_unverified_warning`; `test_gerrit_submit_marks_dry_run_unverified_when_target_head_missing`; `test_gerrit_submit_marks_dry_run_unverified_for_sandbox_target` |
| 目标 HEAD 未知 warning | `_target_warnings`(:280-299:branch None :280 / ls-remote 异常 :291 / rc≠0 :293 / not_found :296 / drifted :299) | `test_gerrit_submit_marks_dry_run_unverified_for_sandbox_target`; `test_gerrit_submit_marks_dry_run_unverified_when_ls_remote_raises`; `test_gerrit_submit_converts_ls_remote_timeout_to_unverified_warning`; `test_gerrit_submit_marks_dry_run_unverified_when_ls_remote_fails`; `test_gerrit_submit_marks_dry_run_unverified_when_target_head_missing`; `test_gerrit_submit_warns_on_target_branch_drift` |
| release:记录不存在 | `ReleaseWorktreeResult(action="record_not_found")`(:204) | `test_release_verified_worktree_reports_record_not_found` |
| release:已释放 | `action="released"`(:212,`released=True`) | `test_release_verified_worktree_removes_protection` |
| release:未受保护 | `action="not_protected"`(:212,`released=False`) | `test_release_verified_worktree_reports_not_protected` |
| exit code 映射 | `exit_code_for_submit`(:235)/ `exit_code_for_release`(:243) | `test_exit_code_mappings_cover_success_missing_and_rejected_actions` |

**规律留痕**:v1.2 表中带锚的四项全部准确、不带锚的六项两虚构两失真——
**无锚即无证伪**,故本表逐行加锚为硬项。
`test_gerrit_submit_dry_run_returns_command_without_push` 另以 fake runner
锁定 `:160` 只构造、`:167` 只存入命令,全部实际 subprocess argv 均无 push。

- **§3 现状锁定(硬项)**:①**无 timeout**——fake runner 断言**所有
  subprocess 调用均未传 `timeout`**(拦截**全部**传入路径,不只 wrapper;
  skill-3 N2 教训);②**`TimeoutExpired` 两路径分别锁定(v1.3 同步 §3.1)**:`_run_git`(:341)
  **裸传播**;`ls-remote`(:285)**捕获转 `target_head_unknown:<exc>` warning**
  并使 action 为 `dry_run_unverified_remote`——**两条各一用例,不得只锁一条**
  (v1.2 写"原样传播"只覆盖一半,同型于 skill-3 N2);
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
8. **A₀ 数据文件**:语料按 **skill-4 FROZEN §5.4.4** 规则从本批版本序列产出;binding 清单
   覆盖本稿"定义节→下游引用"对。

## §7 commit 划分

- **A₀**(冻结前置):继承 `design_drift_ledger.py`,产出本批语料与 binding,
  **准入证伪**(对本批某一早期版本快照必红;**若本批无更早版本,按 **skill-4 FROZEN §5.4.1-3**
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
- [ ] **§3 两项现状锁定测试**(无 timeout / **TimeoutExpired 两路径各一**:
      `_run_git` 裸传播 + `ls-remote` 转 warning / 悬空 symlink 引 skill-3 既有用例)+ **两项设计已登记且新关门批次具名**;
- [ ] pre-shim parity(一正三反)与 post-shim identity **分列**;
- [ ] 三入口 1/1/2/2;两阶段分列;`release-v1.4.0` 不回填;
- [ ] **双门禁继承 A₀ 且全绿**(check + 准入证伪 + skill-4 全部负向证伪不退化);
- [ ] §4 分支表全部契约句逐行有用例,代码锚与实际实现一致;
- [ ] §3.2 结果映射表由末批实现、parity 与评审逐行销账;
- [ ] §2 门禁成员扩展与三条负控制全部落地并实测。
- [ ] **DEFERRED**:timeout 统一 + 悬空 symlink 归一化 → **P4.9 末跨 skill
      行为统一批次**;shim 删除 → 同批;其余沿既有。

---
## 附:零生产行为 + 零判据变更声明
- **零生产行为变更**:单模块逐字节迁移(模式一),无白名单差异;
- **零判据变更**:§0 dry-run 证明;**零跨批次强制迁移**(§0.2);
- **零新机制**:门禁继承 A₀,parity/三入口/两阶段沿既有范式;
- **本批实质议题**:§3 两项继承 DEFERRED 的设计与关门批次具名。
