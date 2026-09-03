# P4.9 skill-4 设计:tizen-build-verify 抽取(v1.10-draft)

- 阶段:P4.9 第四批(skill-3 CLOSED @1ca2206)
- 权威并行:step-0 `v2.1-FROZEN`、skill-1 `v1.4`、skill-2 `v1.3`、skill-3 `v1.3.1`
- **基线**:`883 passed, 1 skipped`(遵"既有集合不缩小且无失败,非总数冻结")
- **总铁律**:行为等价——**三模式各自的等价形式**(§1.4):模式一逐字节;
  模式二逐字节 + §1.3 三处具名白名单;模式三定义区段逐字节 + 重构 import 头;
  三者均零语义变更

> **v1.1 重写说明**:三家评审判 v1.0 不可冻结(2 BLOCKER + 若干 MAJOR),
> 本稿据此重写,非补丁。核心变更:①三模块 45 符号(B-2);
> ②`default_extra_pythonpath` 的 `__file__` 锚点裁决(B-1);③例外契约钉死
> 含 `include_external_packages` 与四条负控制;④twin 补至 8 组;⑤arch 集
> 设计期钉死 + 结果态补 `build_timeout`;⑥§0 test 列标注非权威;
> ⑦补 §5.1/§5.2 完整定义。
>
> **v1.2 修订(三家 v1.1 评审)**:①【C,新 MAJOR】恢复重写中丢失的**机械同步
> 清单**(§2.4);②【A,BLOCKER】SPECS **迁移语义**写明(41 新增 + 3 definition
> 翻转 + 1 新裁)并要求 bridge relocation 校验(§2.5);③【A/B,MAJOR】例外
> **承载契约改 skill-independence + 单边 ignore**(forbidden 单向,拦不住 N4),
> **删除 `include_external_packages`**(两家实测不含亦绿;C 的 exit 1 属另一形态);
> ④【A,MAJOR】护栏改**集合等价**(`_public_surface` 漏 `SubprocessRunner`);
> ⑤【A,MAJOR】§5.2 补**时钟/UUID 冻结**(否则 parity 必因非行为差异变红);
> ⑥【A/B】§1.3 锚点表达式**设计期钉死为 `parents[1]`**(Claude 实测等价)+
> 白名单旧侧行枚举;⑦【B/C】`DEFAULT_MIN_FREE_BYTES` 系本批新裁(非 step-0 已判);
> ⑧【C】`default_extra_pythonpath` **生产零消费方**,公开面须显式裁决;
> ⑨【A】§4 落成真实表 + 消解"分类失败"重复;⑩【A】盲区补 `SubprocessRunner`
> 部分可见。
>
> **v1.3 修订(三家 v1.2 评审:2 BLOCKER + 6 MAJOR/MINOR,仲裁项已实测收敛)**:
> ①【BLOCKER,B/C】`include_external_packages` **全文清除**(§2.1 已删,但 §7
> DoD 与附录仍要求落盘——**验收要求一个正文禁止的配置项**,按 DoD 执行会破坏
> 模块级 ignore 精度);②【MAJOR,C】**workspace.py 第三迁移模式**(§1.4)——
> 该文件是**双角色**:120 行 = 4 真实定义 + 17 行 shared re-export,逐字节副本
> 会把 8 个多余 re-export 挂上 skill 包(违 skill-3 §1.2);③【BLOCKER,B】
> relocation 改**三元组双翻转**映射 + 目的端负控制;④【MAJOR,A/B/C】§2.4 补
> workspace 侧 9 条 + `surface_checks`(:1431)+ bridge 路径常量(:228-240)+
> binding fixture d(:1797);⑤【MAJOR,B/C】cmp 白名单**收窄为三处并钉死
> old→new 文本**(`:25`/`:43-45` 无差异);⑥【MAJOR,B】§5.2 补**第四类易变源**
> (formatter 的随机 `TemporaryDirectory` 进 argv)+ 受控环境输入具名枚举;
> ⑦【MAJOR,B】§4 **真实表落地**并删除"分类失败"重复项;⑧【NIT,A】写明
> `gbs_patch_suggest` 的 **root-layers 层表位置**与 N1–N4 **预期 broken 集合**。

> **v1.4–v1.9 修订与历史论证(v1.10 补录:此前被删而非被移,§5.4 五处
> "见修订说明块"曾悬空;本块即其指向)**
>
> - **v1.4**:relocation 六条负控制 + 纯函数;§5.4 判定改章节作用域;
>   DoD/附录四处漂移修正;模式三三处精确化;白名单钉死;环境字段列出;
>   §4 行号锚点。
> - **v1.5**:synthetic 正向控制;ledger 携带期望命中集;检查范围扩至
>   全部规范正文。
> - **v1.6 及其失败**:ledger 脚本化三件套。**立规依据**:评审把 v1.5
>   的模式回跑 v1.4,**三条漏检**——`函数体 diff` 命中 0(真实旧文
>   **跨行+缩进**)、`17 行 re-export` 命中 1 而实有 3(旧文**多一个
>   `shared` 词**)、`逐字节迁移+具名白名单` 因 **markdown 强调符插入**
>   失配。**即按该 ledger 写出的脚本会对带漂移的稿子报全绿**。教训:
>   把"人工清点不可靠"换成"手写 regex 不可靠",同型问题只换了载体。
> - **v1.7**:撤销 v1.6 的"语境锚必须与数字在同一 regex 内"通则。
>   **证伪链**:按它写的三条示范 regex 回跑 v1.4 **全部 0 命中**
>   (规范化后 `relocation` 距目标数百字符),按 5.4.1-3 连准入资格都
>   没有;而纯字面 `五条负控制` 在 v1.4 命中 **1**(正是那处错值),
>   证伪通过。**该通则排除了唯一能通过证伪的正确解**。
>   另:A₀ 冻结前置、候选处置台账、11 条初始语料。
> - **v1.8 及其失败**:5.4.1-4 推广为"不得手写具体值"。**立规依据
>   (七次同型)**:v1.5 手写 regex(3 条漏检)、v1.6 手写示范 regex
>   (3 条全 0)、v1.7 手写期望集(**实测 `§5.4=2`、总 8,文写 1、7,
>   且含本节自己排除的豁免章节**)、v1.7 手写 11 条语料(**缺 7 条**
>   可证伪模式:总铁律旧措辞、字面 `五条负控制`、`_analyze_failure\(:295`、
>   evidence 缺失分支旧描述、`§4 §5.1` 双章节号、"建议同时做整文件"、
>   语境锚通则)。**只要文档留有任何一处手写具体值,下一轮必在同一位置
>   出同一类错**。
>   **另一条历史实例**:v1.6 自跑称"`函数体 diff` 由 0 变 2 验证规范化"
>   ——那 2 处在 v1.5 **全落 §5.4 豁免区**,不构成判别力证明;真正的
>   证伪是对 v1.4 的 0→1(落 §7 DoD 受检区)。**故立"命中须落在受检
>   范围"**。
> - **v1.9**:新增 §5.5 正向门禁(根因:八次翻车全是"定义节改了下游没跟",
>   §5.4 只查反向);台账④ 改锚原始 `git diff`(锚"实质 diff"只是把自指
>   上移一级,且与 `FORMAT_ONLY` 恒空矛盾);SUBSUMED 钉死 re.search。
> - **v1.10**:见下方本轮条目。
>
> **v1.10 修订(三家 v1.9;C 的诊断:新门禁带着 §5.4 v1.6/v1.7 的两个
> 幼儿病——判据未经实测、完整性锚自指,教训未随机制迁移)**:
> ①**补录 v1.4–v1.9 修订块**(上轮"移入"实为删除,五处引用悬空、27 行
> 八轮诊断链丢失);②**§5.5 判据改 canonical snippet 包含式**——Claude
> 实测:"两侧规范化文本一致"**在其自列的用例三对上即 False**(DoD 是摘要式
> 引用),且**朴素包含式也 False**(DoD 括注插在承重子句中间),故 snippet
> 须切至不含可变括注;并加 `TEXT_CONTAINS` / `COUNT_EQUAL` 两类谓词;
> ③**§5.5 补外部锚**:§7 DoD **每条**必须绑定至少一个定义节 snippet,
> 未绑定即红(解自指,同 §5.4 台账④);④**§5.5 准入证伪**:A₀ 首跑对
> v1.9 的 `BINDING_DRIFT` **必须 ≥1 且含本轮已知两处**,为 0 判定为
> 清单漏登而非文档干净;⑤修 §5.4.4/§5.4.3 两处"实质 diff"残留(第九次
> 同型,C 预测原地二次应验);⑥MINOR:重复句、两处历史叙述移出、
> "手写具体值"外延界定、陈旧标签。

---

## §0 权威归属表(45 行,唯一权威;bridge 与 parser-only 解析此表)

| symbol | definition | owner |
|---|---|---|
| `SubprocessRunner` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `BuildVerifyOptions` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `BuildVerifyResult` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_ApplyPatchResult` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `build_verify` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_BuildProcessResult` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_format_and_apply_patch` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_run_gbs_build` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_gbs_command` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_gbs_arch` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_analyze_failure` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_classification_fail` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_fail` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_actual_changed_paths` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_tracked_worktree_mutated` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_allowed_paths` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_run_git_diff_check` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_canonical_diff_sha256` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_normalize_build_log` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_git` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_git_stdout` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_run` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_read_json` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_sha256_file` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_sha256_text` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_build_subprocess_env` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `_string_or_empty` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `build_verify_to_json` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `default_extra_pythonpath` | tizen_build_verify/build_verify.py | skill/tizen_build_verify |
| `EDIT_SPEC_SCHEMA` | tizen_build_verify/edit_spec_guard.py | skill/tizen_build_verify |
| `EditSpecViolation` | tizen_build_verify/edit_spec_guard.py | skill/tizen_build_verify |
| `_LocatedEdit` | tizen_build_verify/edit_spec_guard.py | skill/tizen_build_verify |
| `validate_edit_spec` | tizen_build_verify/edit_spec_guard.py | skill/tizen_build_verify |
| `_validate_schema` | tizen_build_verify/edit_spec_guard.py | skill/tizen_build_verify |
| `_validate_target_path` | tizen_build_verify/edit_spec_guard.py | skill/tizen_build_verify |
| `_locate_edit` | tizen_build_verify/edit_spec_guard.py | skill/tizen_build_verify |
| `_find_old_from_line` | tizen_build_verify/edit_spec_guard.py | skill/tizen_build_verify |
| `_find_unique_old` | tizen_build_verify/edit_spec_guard.py | skill/tizen_build_verify |
| `_line_starts` | tizen_build_verify/edit_spec_guard.py | skill/tizen_build_verify |
| `_check_no_overlaps` | tizen_build_verify/edit_spec_guard.py | skill/tizen_build_verify |
| `_is_relative_to` | tizen_build_verify/edit_spec_guard.py | skill/tizen_build_verify |
| `DEFAULT_MIN_FREE_BYTES` | tizen_build_verify/workspace.py | skill/tizen_build_verify |
| `create_worktree` | tizen_build_verify/workspace.py | skill/tizen_build_verify |
| `check_disk_and_maybe_cleanup` | tizen_build_verify/workspace.py | skill/tizen_build_verify |
| `_copy_repository` | tizen_build_verify/workspace.py | skill/tizen_build_verify |

**计数**:build_verify 29 + edit_spec_guard 12 + workspace 迁入 4(**3 已判 + 1 本批新裁**,§2.5)= **45**
(数字仅此一处定义,他节一律引用"§0 全部行")。

### 0.1 依赖闭包实测(v1.1 新增,B-2 根因)

v1.0 的 dry-run **只测"谁消费我"、未测"我依赖谁"**,亦未回查前批冻结表中
owner 已判本 skill 的符号,故漏 B-2。本稿补齐双向:

**build_verify.py 的仓内依赖(实测)**:
- `gbs_patch_suggest.formatter`(:25)→ §2 具名例外;
- `tizen_ci_shared.{classify,env,state,workspace}`(:26/:31/:32/:39)→ 下行合法;
- `ci_triage.verify.edit_spec_guard`(:41)→ **同 skill 兄弟模块**,迁后改包内 import;
- `ci_triage.verify.workspace`(:42,`create_worktree`/`check_disk_and_maybe_cleanup`)
  → **step-0 冻结表已判 owner=build-verify**,本批必须一并迁入,否则终态
  `tizen_build_verify → ci_triage` 上行必红。

**通则(⑰跨批次补强,记入 methodology)**:**每个 skill 批次开工前,须 grep
全部已冻结设计稿中 `owner=本 skill` 的符号——它们是本批的强制迁移面**;
闭包不仅含本文件依赖,还含前批已裁归属。

### 0.2 消费面(生产侧,AST 口径)

生产对本 skill 的消费**仅公开面**:`BuildVerifyOptions`/`BuildVerifyResult`/
`build_verify`/`build_verify_to_json`(campaign_repair_step、cli)、
`EditSpecViolation`/`validate_edit_spec`(verify/__init__)、workspace 四符号
(经 `verify/workspace.py` 组合 shim)。

**测试侧消费(须翻转,非"仅 import 行")**:
- `tests/unit/test_build_verify.py:9-15` import **三个私有件**
  (`_format_and_apply_patch`/`_gbs_arch`/`_gbs_command`);
- `tests/integration/test_build_verify_real_git.py:15` import `_format_and_apply_patch`;
- **六处 `monkeypatch.setattr("ci_triage.verify.build_verify...")`** 必须翻到新模块,
  否则只 patch legacy shim、不影响新函数 globals(**测试会失真**);
- 测试改动口径:**import 行 + monkeypatch/setattr 目标字符串**(沿 skill-3)。

### 0.3 §0 证据面口径(⑩,v1.1 更正)

symbol_audit **显式跳过 tests**,故任何 `test=` 列**只能来自 raw-grep、非权威**
——v1.0 的 test 列含系统性误报(`EDIT_SPEC_SCHEMA←test_patch_suggest` 实为
formatter twin;`SubprocessRunner←test_gerrit_fetch` 实为断言字面量;
`_git←4 测试` 实为各自 helper)。本稿 **test 列一律标注"非权威,仅供规划"**,
归属判定只采 AST 生产侧。

## §1 skill 形态:三模块

```
tizen-build-verify/scripts/tizen_build_verify/
  __init__.py        # 薄导出:仅 §1.2 公开面
  build_verify.py    # 29 符号(cmp + §1.3 白名单)
  edit_spec_guard.py # 12 符号(cmp)
  workspace.py       # 4 符号(3 系 step-0 已判归属 + DEFAULT_MIN_FREE_BYTES 本批新裁)
```

**三道 INCOMPLETE 护栏**(每模块一道):自证断言**精确钉定 29/12/4**,不接受
"三路径各≥1 行"。**判据改为集合等价(v1.2,A-MAJOR)**:
`_top_level_symbols(source) == SPECS 中该 definition 的 symbol 集合`——
现有 `_public_surface()` 只收函数/类/全大写赋值,**实测漏 `SubprocessRunner`**
(build_verify AST 顶层 29 vs `_public_surface` 28);配 **`MixedCaseAlias = ...`
负 fixture** 证明集合等价护栏能抓到此类符号。

### 1.4 [v1.3 新增] workspace.py 的第三迁移模式(C-MAJOR)

**实测双角色**:`ci_triage/verify/workspace.py` 共 120 行 =
**4 个真实定义**(§0 的四符号)+ **17 个 shared re-export 名字**(MARKER_FILENAME /
PROTECTED_FILENAME / DisposableWorktree / WorkspaceViolation /
_exclude_private_files / _is_relative_to / _oldest_worktrees / _read_marker /
_run_git / _verify_cleanup_handle / clean_repository_preserving_markers /
cleanup_disposable_copy 等)。

**故本批存在三种迁移模式,验收方式各异**:

| 模式 | 模块 | 验收 |
|---|---|---|
| 一 逐字节 cmp | `edit_spec_guard.py` | `cmp` 空输出 |
| 二 cmp + 具名白名单 | `build_verify.py` | `diff --unified=0` 仅 §1.3 三处 |
| **三 部分抽取 + 构造 import 头** | **`workspace.py`** | **见下(cmp 不适用)** |

**模式三规格**:
- 新 `tizen_build_verify/workspace.py` **只含四个真实定义**,其
  **四个定义区段**(v1.4 更正:三个 `FunctionDef` **完整源区段**含签名/注解/
  默认参数 + `DEFAULT_MIN_FREE_BYTES` 常量赋值区段——原"函数体"措辞会让
  常量与签名逃逸)**逐字节等同**旧址对应区段;
- **import 头重新构造**:只引入这四个定义**实际使用**的 **9 个 shared 名字**
  (实测:`DisposableWorktree`、`WorkspaceViolation`、`_exclude_private_files`、
  `_oldest_worktrees`、`_run_git`、`clean_repository_preserving_markers`、
  `cleanup_worktree`、`is_protected`、`write_workdir_marker`)——
  **不得照抄那 17 个 re-export 名字**(v1.4 更正:旧址为 **17 个名字 / 物理
  21 行**,两个括号式 import 跨行),否则 skill 成为 shared 符号的二级来源
  (违 skill-3 §1.2 立规);
- **旧址保留全部 17 个 re-export 名字**(其 shim 角色不变)+ 四符号的 skill 侧
  re-export(组合 shim,§1.1);
- **验收(替代 cmp,v1.4 精确化)**:
  ① **四个定义区段** AST source-segment 逐字节相等(三 FunctionDef 完整区段
     + 常量赋值区段);**并**做整文件 `diff --unified=0` 断言**全部 hunk
     落在 import 头区域**(v1.6:去"建议",与 DoD 硬项对齐)(与 §1.3 白名单验收同构);
  ② **shared import binding 集合等价**:`{{新模块的 shared import 名}} == S9`
     (v1.4 更正:改集合等价、与本批护栏同口径;并写明是 **9 条 shared import**
     ——模块另有 `__future__`/`shutil`/`subprocess`/`Path` 等 stdlib 头,
     照总行数会误判);ruff F401 作未使用 import 的双保险;
  ③ **禁止其余 S8**;且新模块 9 条 import **一律不得使用 `as X` 同名别名形式**
     (A:该形式是本仓 re-export 惯用法,grep 可判,比"__all__ 自证"少裁量);
     **包根公共面不得导出 S9**(B:Python 模块语义下"零 re-export"不能靠
     `__all__` 保证,故判据落在**包根导出面**);
  ④ §7 对本模块的验收**改为本条**(不适用 cmp)。

### 1.1 旧址处置
- `verify/build_verify.py`、`verify/edit_spec_guard.py` → 纯 re-export shim(零 def/class);
- **`verify/workspace.py` → 组合 re-export shim**:同时转出 shared 侧原语与 skill 侧
  四符号(该文件仍是 ci_triage 内的兼容入口);
- `verify/__init__.py` re-export 面随之调整;
- **迁移副本注释语义复核**(skill-3 N-A 通则)。

### 1.2 公开契约(SKILL.md)
`build_verify` / `BuildVerifyOptions` / `BuildVerifyResult` / `build_verify_to_json`
/ `default_extra_pythonpath` / `EditSpecViolation` / `validate_edit_spec`
/ `create_worktree` / `check_disk_and_maybe_cleanup`;其余为不导出实现面。

### 1.3 [BLOCKER-1 裁决] `default_extra_pythonpath` 的 `__file__` 锚点

**事实**:`:633-636` 用 `Path(__file__).resolve().parents[2] / "run_ci_triage.py"`。
现址 parents[2]=`tizen-ci-triage/scripts`(launcher 存在);迁后
parents[2]=`tizen-build-verify`(**launcher 不存在**)→ `discover_sibling_pythonpath`
返回 `()`。**cmp 逐字节绿、全仓零测试覆盖,行为静默由"两路径"变"空"**——
撞零语义变更铁律。

**裁决(三条,缺一不可)**:
1. **锚点表达式设计期钉死(v1.2)**:新址改为
   ```python
   Path(__file__).resolve().parents[1] / "run_ci_triage.py"
   ```
   **Claude 实测等价**:`discover_sibling_pythonpath` 只用 `launcher.parents[1].parent`
   求仓库根、**不要求 launcher 文件存在**;新址 `parents[1]` =
   `tizen-build-verify/scripts`,其 `.parent` 即仓库根,与现址
   `tizen-ci-triage/scripts` 的 `.parent` 相同 → 两者返回**完全一致的有序 tuple**
   (实测均为 `(tizen-gbs-log-analysis/scripts, tizen-gbs-patch-suggest/scripts)`);
2. **cmp 白名单(v1.3 收窄为三处并钉死 old→new 文本)**:三家实测
   `:25`(`from gbs_patch_suggest.formatter import ...`)迁移前后**字节相同**、
   `:43-45` 为续行无差异,故白名单**仅三处**:
   | # | old | new |
   |---|---|---|
   | 1 | `from ci_triage.verify.edit_spec_guard import EditSpecViolation, validate_edit_spec` | `from tizen_build_verify.edit_spec_guard import EditSpecViolation, validate_edit_spec`(v1.4 钉死:绝对 import,不留二选一) |
   | 2 | `from ci_triage.verify.workspace import (` | `from tizen_build_verify.workspace import (`(v1.4 钉死;续行 :43-45 不变) |
   | 3 | `launcher_path=Path(__file__).resolve().parents[2] / "run_ci_triage.py"` | `...parents[1] / "run_ci_triage.py"` |
   **白名单按集合等价判定**(与本批护栏判据一致):多列一项即红;
   验收用 `diff --unified=0` 精确比对;
3. **补测试锁定**(本批新增):断言迁移前后返回**有序 tuple 相等**,且
   **断言其非空**(当前 direct-folder 场景应得两条路径)——防"两边都空"假绿;
   该函数输出并入 §5.2 parity 载荷。
4. **公开面裁决(v1.2,C-MINOR)**:`default_extra_pythonpath` **生产侧零消费方**
   (全仓除定义外零命中)。保留其为包根公开面属**显式裁决**(它是 skill 对外
   提供的环境发现能力,供未来独立调用),非沿袭;此裁决与"不导出面不以消费方
   数量推断"口径互为反向,一并写明。

## §2 具名例外:`tizen_build_verify.build_verify → gbs_patch_suggest.formatter`

采方案 (d):`gbs_patch_suggest` **保持 skill 身份**,不重定义层级;
skill-independence 不放宽;**例外须具名、单向、单模块**。

### 2.1 配置规格(v1.2 钉死)
- **`gbs_patch_suggest` 加入 `root_packages`**(实测其零 ci_triage/零 shared 依赖,
  不引爆既有边);
- **不使用 `include_external_packages`**(v1.2 更正:两家独立实测不含该项亦全绿;
  且 external 形态下 `gbs_patch_suggest` 会被压成整包、模块级 ignore 报
  `MissingImport`。此前"硬前提"的 exit 1 实测应属"契约引用未入 root 的包"另一
  形态。该开关为**仓库级**、改变全部契约分析范围,属多余暴露面);
- **承载契约 = `skill-independence` 扩成员 + 单边 ignore**(v1.2 更正,MAJOR):
  forbidden **单向**,拦不住 N4(`gbs_patch_suggest → tizen_build_verify`);
  independence **双向对称**,且 2.3 支持 `ignore_imports`;
- 例外精确到**模块级**:`tizen_build_verify.build_verify -> gbs_patch_suggest.formatter`;
- **`unmatched_ignore_imports_alerting = error`**;**精确 ignore 与该项须分别写入
  `root-layers` 与 `skill-independence` 两契约,不共享配置**;
- **落盘时机**:ignore 必须在迁移完成后同 commit C 落盘(否则未匹配即红);
- **`gbs_patch_suggest` 的 root-layers 层表位置(v1.3,A-NIT)**:须与六抽取
  skill **同层**列入 root-layers 的 skill 行,否则 root-layers 看不见该边、
  "ignore 写入两契约"中 root-layers 那份失去意义,且 N1–N4 的预期 broken 集合
  不可验收;
- **落盘实测**:若加入 root_packages 后 lint 不绿,**停止报告**贴原文,由设计侧裁。

### 2.2 负控制四条(v1.0 仅一条,不足以证"未泛化")
| # | 构造 | 期望 |
|---|---|---|
| N1 | `tizen_qb_discover → gbs_patch_suggest.formatter` | 红(他 skill 不可用) |
| N2 | `tizen_build_verify.edit_spec_guard → formatter` | 红(同 skill 错模块) |
| N3 | `tizen_build_verify.build_verify → gbs_patch_suggest.analyzer_runner` | 红(错子模块,未泛化为整包) |
| N4 | `gbs_patch_suggest → tizen_build_verify` | 红(单向) |
正向:上述精确边绿。
**预期 broken 集合(v1.3 钉死)**:`gbs_patch_suggest` 入 root-layers 同层后,
N1–N4 **各自应 root-layers 与 skill-independence 双红**(三家实测一致);
正向精确边两契约**均绿**,且**去掉 root-layers 的 ignore 后正向立即转红**
(证明两契约各自持有一份精确 ignore、不共享)。
**N1–N4 fixture 纪律**:须保留正向边,并断言**失败来自预期 contract 与精确非法边**,
不得因 allowlist 未匹配而"错误原因变红"。
**传递闭包缺口(登记)**:import-linter 会直接删除被 ignore 的边,故若未来
`formatter → analyzer_runner`,两项架构契约仍绿。本批**承认例外允许 formatter 的
传递闭包**,并登记为已知缺口(与 §2.3 盲区同处登记)。

### 2.3 subprocess 盲区(v1.1 更正为真实链,MAJOR-⑥)
v1.0 登记的 `gbs_patch_suggest→gbs_analyzer` **与本批例外无关**(formatter 不调
analyzer_runner)。真实链是 **`build_verify.py`(command 构造 :401,argv 元素 :402-404):
`options.python_executable, "-m", "gbs_analyzer", "analyze", ...`**,即
`tizen_build_verify.build_verify --subprocess/python -m--> gbs_analyzer`;
另有 `gbs`、`git`、迁入 workspace 后的 `cp -a` 等外部命令依赖。
**登记为静态门禁盲区**:import-linter 不可见,"六契约全绿"不等于跨包依赖已全覆盖。
持久登记位置:`.importlinter` 头部注释 + campaign 级总账(NIT-⑤)。

## §2.4 机械同步清单(v1.2 恢复,重写中丢失;漏则 commit C 必红)

commit C **先做**,逐项报告:
1. **5 个符号的 declared consumers 翻转** `ci_triage.verify.build_verify` →
   `tizen_build_verify.build_verify`:`check_disk_and_maybe_cleanup`、
   `cleanup_worktree`、`create_worktree`、`discover_sibling_pythonpath`、
   `mark_worktree_protected`;
2. **三个迁移符号的 definition 翻转**:由 workspace 常量路径改为
   `tizen_build_verify/workspace.py`;
3. **`DEFAULT_MIN_FREE_BYTES` 新注册**(本批新裁,见 §2.5);
4. **`MODULE_OWNERS` 新增** `tizen_build_verify.build_verify` 条目
   (**MODULE_OWNERS 在 symbol_audit.py:612-623**;:292/:301/:308 是 SPECS
   消费方行,v1.4 更正引用);
5. `REGISTERED_SKILL_ROOTS` / `ROOT_LAYERS_HIGH_TO_LOW` / pyproject
   `packages` 与 `mypy_path` / `.importlinter` root_packages 加
   `tizen_build_verify`;
6. **symbol_audit 源根新增** `tizen-build-verify/scripts`;
7. **`surface_checks` 硬编码接入**(symbol_audit.py:1431):现只显式选择前三个
   skill 文件,**仅加源根不会启用新三模块的护栏**——须显式加入三模块;
8. **bridge 冻结稿路径常量**(table_audit_bridge.py:228-240):现注册前四批,
   须加入 skill-4 正文路径,再应用 §2.5 relocation;
9. **workspace 侧 9 条 declared consumers 翻转**(v1.3 补,A-MAJOR;漏则必红):
   `DisposableWorktree`、`WorkspaceViolation`、`cleanup_worktree`、
   `is_protected`、`_oldest_worktrees`、`_run_git`、`_exclude_private_files`、
   `write_workdir_marker`、`clean_repository_preserving_markers` ——
   其真实使用方是本批迁走的三个组合函数,迁后消费方变为
   `tizen_build_verify.workspace`(旧址组合 shim 的 re-export **不计入消费方**);
10. **binding fixture d 硬编码断言**(symbol_audit.py:1797):
   `"ci_triage.verify.workspace" in workspace_consumers` ——组合函数迁走后
   旧址不再 load,须同步改为期望 `tizen_build_verify.workspace` 或重安置 fixture。

## §2.5 SPECS 变更语义(v1.2,A-BLOCKER)

45 行**不是纯新增**,须分三类执行,否则旧行残留或重复注册:
- **41 新增**(build_verify 29 + edit_spec_guard 12);
- **3 迁移(definition 翻转)**:`create_worktree`/`check_disk_and_maybe_cleanup`/
  `_copy_repository` —— step-0 已判 owner=build-verify,本批**改 definition**
  (supersession),非新增;
- **1 新裁**:`DEFAULT_MIN_FREE_BYTES`(step-0 两版冻结稿**零命中**,本批随唯一
  消费者迁入,符合既有判据,不构成判据变更)。

**bridge relocation 校验(v1.3 强化,B-BLOCKER)**:三行实为
**definition + owner 同时翻转**(旧 owner 标签 `build-verify` → 新
`skill/tizen_build_verify`),非仅路径变更。映射须钉死为**三元组双射**:

```
(old_definition, symbol, old_owner) -> (new_definition, symbol, new_owner)
```
- 映射集合**精确等于三项且双射**(非"至少包含");
- **每个目的三元组必须同时存在于新正文表与 SPECS**;
- **relocation 落成可注入 mapping 的纯函数(v1.4,B)**,并断言:
  `consumed_sources == mapping.keys()`;每个 source **恰消费一次**、每个
  destination **恰产生一次**;未映射项**原样进入普通比较**;
- **六条负控制(v1.5 更正标题;原四条全是终态断言,拦不住"不做映射")**:
  ①目的行缺失 → 红;②目的 definition 错误 → 红;③目的 owner 错误 → 红;
  ④源端旧键仍残留 → 红;
  **⑤(针对映射工件本身,A-MAJOR)**:映射缺失该三元组、或映射集合
  **≠ 精确三项 / 非双射** → 红;且 **N4 须产出具名 verdict
  `UNMAPPED_SOURCE`**(不接受笼统 exit 1),使"未消费旧键"是失败的**直接原因**,
  而非被无关前置断言掩盖;
  **⑥源端校验(C-NIT)**:映射**源端三元组须与 step-0 冻结表逐行一致**,
  否则红——防"源端 owner 写错而目的端全对";
- **synthetic mapping 正向控制(v1.5,A-MAJOR;证明 mapping 被真实使用)**:
  六条仍可被"保留正确 mapping 常量但按硬编码 `LEGACY_KEYS` 删除、并把
  `consumed_sources` 直接报告为 `mapping.keys()`"的伪实现全过。故补一条
  **正向**控制:向纯函数注入一组**完全不同于生产三项**的 synthetic 映射
  `A → B`,断言 **A 被消费、B 被产生**;**任何硬编码 `LEGACY_KEYS` 的实现
  必然在此用例失败**。并明确规定:**`consumed_sources` 只能由逐行 mapping
  lookup 的实际命中产生**,不得由 `mapping.keys()` 直接赋值。
- **synthetic 用例二(封死自报,A/C-NIT)**:注入 `A→B` 但**输入表不含 A**
  ⇒ 断言 `consumed_sources` **为空**并报 `UNMAPPED_SOURCE`——
  `consumed_sources = mapping.keys()` 的 echo 实现在此**必红**;
- **synthetic 用例三(封死多余项;v1.8 定义节补齐产出断言)**:注入
  `{A→B, C→D}`、输入含 **A + X**(X 为未映射项)⇒ 断言 `consumed == {A}`
  (非 `{A,C}`)**且产出含 B、不含 A/C/D、C 报 `UNMAPPED_SOURCE`、
  X 原样保留**。(v1.7 只把产出断言写进 DoD、定义节未补——按"正文为准"
  产出断言当时不成立,第六次同型;且原文写"输入只含 A"却要求"未映射项
  原样保留",测试中根本无未映射项,故输入改为 A + X。)
- **断言落点(v1.7 更正措辞,A-MINOR-c)**:v1.6 写"一律落在函数输出、不得
  只看自报值",但用例二/三的牙齿**恰在 `consumed_sources` 上**,措辞自相
  矛盾。正确表述:**不得仅以 `consumed_sources` 为证据,须同时断言产出表/
  verdict**。
- **明令不得静默过滤旧表**;relocation 必须是**显式映射**而非删除——
  **该条款由负控制⑤⑥ + synthetic 正向控制共同物理强制**(v1.6 更正:防硬编码删除的实际是 synthetic 控制,⑤⑥ 验证映射工件与源端)(v1.4 前它是无强制的散文:A 推演证明
  "不做映射、按旧键删三行+新增三行"可让原四条全过)。
**owner 标签演化说明(A-NIT)**:step-0 表中 owner 为占位标签 `build-verify`,
新表为 `skill/tizen_build_verify`;relocation 的 owner 比对**以新表为准**,
标签对应关系随映射登记,避免实现期误判 OWNER_MISMATCH。

## §3 twin 八组(v1.0 漏两组,均在审计盲区外)

| 组 | 定义处 | 性质 |
|---|---|---|
| `SubprocessRunner` | build_verify 与仓内多处同形别名 | 类型别名碰撞(仅本冲突面计) |
| `_git_stdout` | build_verify:556 / gerrit_submit:332 / campaign_repair_step:1273 | 三处 |
| `_read_json` | build_verify:589 / cli:397 | 两处 |
| `_sha256_file` | build_verify:596 / campaign_repair_step:1269 | 两处 |
| `_build_subprocess_env` | build_verify:608 / runner:372 | 两处 |
| `_is_relative_to` | edit_spec_guard:160 / shared/workspace | 两处(第三次) |
| **`EDIT_SPEC_SCHEMA`** | edit_spec_guard:13 / gbs_patch_suggest/formatter:16 | **字节相同常量** |
| **`_locate_edit`** | edit_spec_guard:110 / formatter:342 | **签名已分化** |

**严禁合并**(沿既有先例)。**审计盲区说明**:`gbs_patch_suggest` 不在
symbol_audit 源根内,故后两组对 twin-guard **不可见**,须人工登记。
**补充(v1.2)**:`SubprocessRunner` 在 `gbs_patch_suggest` 与 `gbs_workflow`
中的成员**同样位于源根外**,故该组仅"**部分可见**",全仓定义数不可由审计工具
自证,须以限定作用域的精确命令 + 人工说明并用。
**新增 DEFERRED**:`EDIT_SPEC_SCHEMA` 是跨包 schema 版本标识的**双权威**——
一侧升版另一侧未同步时 `validate_edit_spec` 会静默接受旧 schema;
**schema 常量单一权威 → patch-suggest 相关批次**。

测试侧同名 helper(`_git` 等)列为 **raw-grep false positive**,不入 twin 表。

## §4 分支覆盖表(结果态与 arch 维度)

**arch 维度(设计期钉死,不留实现期裁量)**:
`standard-aarch64→aarch64`、`standard-armv7l→armv7l`、`standard-x86_64→x86_64`、
`aarch64→aarch64`(无前缀代表样本);并验证 **GBS argv 用 norm 值、failure key/record
保留 raw 值**。既有 `test_gbs_arch_removes_standard_prefix` 已参数化覆盖,矩阵须
写明"既有覆盖 vs 本批新增 delta",避免重复计数。

**结果态(v1.0 四支 → 补全)**:成功 / 构建失败(classify)/ patch 应用失败 /
edit-spec 违规 / **`build_timeout`(:223-232,断言 `repair_allowed=REPAIR_DENIED`)** /
**`build_mutated_source`(:236-244,同断言 DENIED)** / 两种 `no_effective_changes`
(:155、:194) / `git diff --check` 失败(:170) / unexpected paths(:184) /
analyzer 非零退出 / analyzer 未产 evidence / marker 写入异常 / DB 写入异常
(后两者原样传播)。
**"分类失败"已删除(v1.3,B-MAJOR)**:它与"构建失败经 classify 分类"
(`gbs_build_failed`,:253/:434-437)重复,统一为后者单一条目,不另列。

**超时契约形状对照(写入设计,防混用)**:skill-3 冻结"无 timeout、TimeoutExpired
原样传播";**本 skill 有一等公民 `wall_timeout`**(:63 必填,:359 下传)——两者
形状相反。

**真实表(v1.3 落地,B-MAJOR)**:下表即"契约句 → 分支 → 用例"三列表,
用例列**实现期填入真实用例名**并回写本表(不得只留要求):

| 契约句(SKILL.md) | 分支(代码锚) | 用例 |
|---|---|---|
| 成功返回 PASS | `result="PASS"`(:267/:297 同一路径) | existing |
| patch 应用失败 | `apply_failed` ×3(:143 含 EditSpecViolation / :162 / :172) | existing + delta |
| 无有效变更 | `no_effective_changes` ×2(:155 / :194) | existing |
| 越界路径 | `apply_unexpected_paths`(:184) | delta |
| diff --check 失败 | (:170) | delta |
| 构建超时 → DENIED | `build_timeout`(:226),断言 `repair_allowed=REPAIR_DENIED` | existing(补 DENIED 断言) |
| 构建改动 tracked 源 → DENIED | `build_mutated_source`(:239),同断言 DENIED | existing(补 DENIED 断言) |
| 构建失败经 classify | `gbs_build_failed`(:253 / :436) | existing |
| analyzer 非零退出 | 调用点 :248 / 定义 :393 / **非零退出分支 :417-418**(`except CalledProcessError → return None`) | delta |
| analyzer 未产 evidence | **:419-421**(`evidence_path = …; if not is_file(): return None`)——v1.6 第三次更正:v1.4 模糊但正确、v1.5 "精确化"改成了错行(与非零退出撞号) | delta |
| marker 写入异常原样传播 | `mark_worktree_protected`(:294) | delta |
| DB 写入异常原样传播 | `write_pass_record`(:295) | delta |
| arch norm/raw 双向 | argv 用 `_gbs_arch` norm(:384);failure_key(:116)/record(:288) 保留 raw | existing(参数化四例) |

逐行标注 **existing / delta**,既有覆盖不重写(重复项处置见上文 §4 首段)。
**引言与表对齐(v1.4,C-NIT)**:引言中"edit-spec 违规"**并入表中
`apply_failed`×3 的 :143 分支**,不单列——与消解"分类失败"重复同型处置。
**用例名回写(B-MAJOR 的可执行折中)**:用例列现为 `existing`/`delta` 标记,
**实现期须回写真实用例名并更新本表**,该回写**列为 §7 DoD 硬项**——
用例尚不存在时无法预先填名,但"必须回写"是可验收的。
**既有测试优先迁入**,不重写重复 fixture。

## §5 parity 与交付面

### 5.1 测试所有权
新建 skill 行为测试文件(**命名实现期先确认既有 `test_build_verify.py` 归属再定**);
三类边界分节(skill 行为 / 编排集成 / legacy wiring);包根导出正反测试。

### 5.2 pre-shim parity(载荷穷举,唯一掩码)
- **payload**:`BuildVerifyResult` 全字段、fake runner 有序命令轨迹(含 argv 与
  timeout 参数)、destination/worktree 相对文件树 + 阶段标记、
  **`default_extra_pythonpath()` 返回值**(§1.3)、受控环境输入;
- **唯一掩码**:worktree/destination 绝对路径 → `<DEST>`,**逐字段施加**
  (argv 元素、路径字段、symlink target),**不做全局字符串替换**;
- **非行为易变源冻结(v1.2,A-MAJOR;否则 parity 必因非行为差异变红)**:
  冻结随机 **UUID**(build_verify:266)、**UTC clock**(marker 时间,
  shared/workspace:49)、**`GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE`**
  (git commit 时间);**第四类(v1.3 补,B-MAJOR)**:`gbs_patch_suggest.formatter`
  的随机 `TemporaryDirectory`(formatter.py:184)其路径进入
  `git diff --no-index` 的 **argv**(:509)——实跑证 patch 内容相同但
  `TRACE_EQUAL=False`,**须注入确定性临时目录**,不能靠 `<DEST>` 掩码;
  四者均以注入/固定值方式控制,**不进掩码白名单**(掩码仍只作用于路径承载字段);
- **受控环境输入(v1.4 真正列出字段,B-MAJOR)**:生产 `_build_subprocess_env`
  (:608)**复制整个 `os.environ`** 并派生 `PYTHONPATH`。**parity payload 只记
  两项**:①`PYTHONPATH` 的**值或 null**(即该函数的派生结果);
  ②`GIT_AUTHOR_DATE`/`GIT_COMMITTER_DATE`(已在易变源冻结项内,记其**冻结值**
  以自证冻结生效)。**其余继承环境一律排除出 payload**(宿主变量入载荷即
  非行为变红,正是本项要防的)。
- **DB 副作用**:若 parity 载荷含 DB 行,须纳入**逻辑行**并冻结
  `state/db.py:319` 的独立 UTC clock;
- **逐字段相等为主证据**,固定 JSON SHA 仅作锚;
- **一正三反 normalizer**:正(仅路径不同→掩码后相等);反(改 `failure_class`、
  换命令顺序、改 `repair_allowed`→ 必红,**变异落非路径部分**);
- 取证于**改 shim 之前**;双跑隔离用 `importlib.reload` 或子进程。

### 5.3 post-shim identity / 三入口 / 两阶段
沿 skill-3 范式:identity 只证接线;三入口(pyproject packages+mypy_path /
ci.yml mypy 清单 / README PYTHONPATH)+ 四条精确计数自检(先在已完成 skill
样本上验命令);`release-v1.4.0` 不回填;B 临时脚手架 / C `pip install -e .`
后 `env -u` 无脚手架复跑,证据分列。

## §5.4 修订漂移门禁(v1.6 重写:脚本化,文档不再维护模式表)

**沿革与失败教训**:见修订说明块(v1.9:历史论证整体移出本节,使
5.4.1-4"不得手写具体值"字面可判——否则需人工区分"叙述值 vs 规范值",
那是语义判断第三次换皮回潮)。

### 5.4.1 门禁形态(v1.6 定死)

**ledger 不再是文档表格,而是 `tools/design_drift_ledger.py` + 数据文件**;
本设计稿只规定其**规格与验收**,不维护模式清单(手写清单正是失效根源)。

**三件套(缺一不可)**:
1. **模式自动导出 + 候选处置台账**:从 `v(n-1) → v(n)` 的**原始 `git diff`** 自动
   生成候选模式(被删除/被替换的原文行),**人工只许删、不许增**。
   **台账四条(v1.8;前三条 v1.7,第四条为 B/A 指出的外部锚)**:
   ①`exported_candidates == retained ∪ explicitly_ignored`;②两集合**不相交**,
   **禁止静默删除**;③每个 ignored 项携带**原 diff span 与机械可判的忽略
   类别**——`FORMAT_ONLY` 须机械断言 `normalize(old)==normalize(new)`;
   `SUBSUMED` 须**引用 retained candidate ID**,且判定谓词钉死为:**该 retained
   模式对 `normalize(ignored_old_span)` 的 `re.search` 实际命中**(非区间包含
   ——否则可引用一个毫不相干但区间更大的候选);
   ④**span 覆盖率(外部锚,解自指;v1.9 改锚原始 diff)**:**原始 `git diff`
   的每一行删除**(不是"实质 diff")都须被某个 retained 模式的来源 span 或
   某个 ignored 项的 span 覆盖,**存在未覆盖行即红**。
   **为何必须是原始 diff**:锚到"实质 diff"只是把自指**上移一级**——导出器
   若在实质化过滤阶段吃掉一行,④ 同样看不见;且与 ③ 的 `FORMAT_ONLY` 直接
   矛盾(实质化若已滤掉纯格式差异,该类别恒为空集、成死条文)。
   **故:实质化过滤不得在 diff 阶段静默进行,一律作为 `FORMAT_ONLY` 显式
   登记进 ignored**——④ 才是真外部锚,③ 的该分支才有意义。
   **为何必须有④**:①②③ 中 `exported` 既是被检对象又是全集定义——
   导出器若在规范化或"行→模式"转换中吃掉某处删除,它根本不进 `exported`,
   台账仍全绿。这正是方法论 **⑬"完整性锚不得自指"** 禁止的形态,而 ⑬ 是
   本 campaign 自订规则。④ 把 `exported` 锚到**外部事实(diff 的删除行)**,
   ①②③ 才从"内部一致"升级为"对外完整"。
   **candidate 身份**:以 `(旧版本, diff hunk/span, 规范化文本 hash)` 为 ID,
   按 ID multiset 做 partition(**不得按模式字符串集合**,否则同一旧行的
   多个 span 会被去重);
2. **正文规范化后匹配**:比对前对两侧做规范化——**去 markdown 强调符
   (`**`/`` ` ``)、折叠空白与换行、统一全角/半角标点**;上述漏检均源于未规范化(实例见修订说明块);
3. **回跑证伪(ledger 必备字段)**:每个模式**必须在 v(n-1) 上跑出命中数
   ≥1 且等于其实际出现次数**;不满足者视为写错、**不得进入 ledger**。
   **两条限定(v1.7,A-MINOR)**:
   - **回归性 vs 预防性**:上述规则适用于**回归性模式**(针对已发生漂移);
     **预防性模式**(为尚未发生的漂移所设)在 v(n-1) 必然 0 命中,改用
     **构造式证伪**——人工造一份注入该漂移的副本,跑出命中 ≥1;
   - **命中须落在受检范围**:证伪的命中若全部落在豁免区(修订说明 / §5.4),
     **不构成判别力证明**(历史实例见修订说明块);
4. **本节不得出现任何手写的具体值(v1.8 根治,三家一致诊断)**:
   **模式、期望集、语料清单一律由 A₀ 脚本产出后引用;文档只写生成规则与
   验收标准**。**外延界定(v1.10)**:本条限于**漂移模式串、期望集数值、
   语料成员**三类;**机制标识符与判定谓词**(如 `FORMAT_ONLY`、`re.search`、
   `normalize(old)==normalize(new)`、规范化函数的三条定义)**不在其列**。
   **立规依据(七次同型)**:见修订说明块。

### 5.4.4 数据文件初始语料(v1.8:改为生成规则,不写死清单)

ledger 表移出文档后,历轮累积的已知模式**无处承载**,故规定其**生成规则**
(而非清单;立规依据见修订说明块):

> **初始语料 = 对 `v1.0 … v(n)` 每一相邻版本对做**原始 `git diff`**、逐条按 5.4.1-3
> 证伪(回归性回跑 / 预防性构造式)、取并集**;由 **A₀ 脚本产出**,
> 文档不列举成员。
> **前置断言(v1.9)**:A₀ 须断言**参与 diff 的版本序列连续且无缺号**
> (`v1.0..v(n)` 逐一存在,缺一即红)——防某版被归档后脚本静默少算一段。

### 5.4.2 判定规则

- **检查范围**:除**显式修订说明块**与 `§5.4` 自身外的**全部规范正文**;
- **期望命中集**:由**脚本的数据文件**持有(`模式 → {章节: 计数}`),
  **不得从本次扫描反推**;文档不重复维护(避免规格与表两处漂移)。
  **关键**:期望集须精确到 `{章节: 计数}`,脚本**只比对计数、不判断任何
  一处命中是否"正当"**(历史论证见修订说明块)。**期望集的具体值由 A₀ 脚本对冻结版正文产出并存入
  数据文件,本文档不书写任何示例值**(5.4.1-4)。
  **两点流程规定(A-MINOR)**:①期望集的**首次基线**仍是一次性人工确认,
  故**基线及其后续变更须随正文 diff 一并评审**,防基线被顺手改绿;
  ②新增一处合法引用也会因计数不符而红——**这是特性不是缺陷**,处置流程为
  "更新数据文件 + 在评审中说明该新增",不得为消红而回避登记。
- **通配数字模式禁用,一律用字面模式 + `(章节:计数)` 期望集**;v1.6 的
  "语境锚必须与数字在同一 regex 内"通则**已撤销**(实测证伪,论证见修订说明块)。
- **表面形式覆盖**:同一语义的多种表面形式须各自登记;**具体示例由 A₀
  产出,本节不书写**(立规依据见修订说明块)。

### 5.4.3 验收(§7 DoD 硬项)

**落地时点(v1.7 改为冻结前置,B-BLOCKER-1)**:本稿 §5.4.1-3/§5.4.3 要求
"脚本存在并实际跑过",若在无脚本时冻结即**冻结门自我违反**;且 A/B/C 各
commit 的正文引用将处于无门禁状态。故 **`design_drift_ledger.py` 与数据
文件作为 `commit A₀` 在冻结之前落地并首次实跑**(§6),其产物是冻结的
**前置证据**。**版本钉定(A-MINOR)**:A₀ 的实跑须**对冻结那一版正文**取得;
冻结前正文若再修改,**须重跑并同评审更新期望集**。

- [ ] `design_drift_ledger.py` **脚本存在并实际跑过**(不接受自跑叙述);
- [ ] 每个模式附**回跑 v(n-1) 的命中数**,且等于该版实际出现次数;
- [ ] **`v(n-1)→v(n)`(本轮)**的**原始 `git diff`** 已自动导出模式并全部证伪通过;
- [ ] 扫描结果:实际命中集 == 数据文件的期望命中集。

**跨批次沉淀(v1.7 恢复,A-MAJOR-4:随整节重写丢失)**:本节门禁与已有三项
(附录对账 / 计数对账 / 契约↔用例)**并列为第四项冻结必检,写入 skill 模板**,
供 skill-5/6 及后续批次继承——这是本稿最有价值的跨批次泛化,不得随节重写丢失。

**旧规则块处置(C-MAJOR-1)**:v1.4 的"§0–§4 作用域 + 五类允许位置"规则
**已被本节取代,原块删除**(留存即本节要防的残留)。

## §5.5 定义-引用一致性门禁(v1.9 新增,正向;B 的根因诊断)

**为何必须新增**:§5.4 是**反向**门禁——查"被删除/改写的旧串是否残留";
但本稿**八次同型翻车全部是另一个方向**:定义节改了,**下游引用点没跟上**
(§2.5 用例三 ↔ DoD、§5.4.4 轮次 ↔ §6、§1.4 四条 ↔ DoD 首项、§2.2 四条 ↔
DoD 例外项、§2.4 十项 ↔ DoD、§2.5 六条 ↔ DoD)。反向门禁**在结构上查不出**
这类缺陷:新表述没有"旧串"可查。**两个门禁互补,缺一不可**。

**机制(由 A₀ 脚本承载)**:
1. 为每一对 **`定义节 → 下游引用点`** 编一个 **binding ID**;
2. 数据文件登记该对的 **定义侧锚**(章节 + 规范化文本片段)与 **引用侧锚**;
3. **判据(v1.10 改;原"两侧规范化文本一致"实测在其自列的对上即失败)**:
   定义侧登记一段 **canonical snippet(承重子句)**,断言
   **`norm(snippet) ⊆ norm(引用侧文本)`**;每个 binding 按类别登记谓词:
   - **`TEXT_CONTAINS`**:承重子句须逐字出现于引用侧(允许 DoD 摘要、
     加括注);**snippet 须切至不含可变括注**——Claude 实测:DoD 侧写
     "输入含 A + X(X 为未映射项,**v1.9 同步 §2.5**)",括注插在承重子句
     中间,朴素包含式亦 False;
   - **`COUNT_EQUAL`**:引用侧数词 == 定义侧枚举项计数(计数规则随
     binding 登记)——六对中有三对是计数式引用(四条/十项/六条),
     两侧文本**永远不相等**,等价判据对它们结构上不可判;
   不满足即红,报 `BINDING_DRIFT(<id>)`;
4. **binding 清单由脚本从"定义节被改动"的 diff 自动提出候选**,人工只许
   删(同 5.4.1-1 的会计恒等式与台账约束);
5. **外部锚(v1.10 补,解自指;同 §5.4 台账④)**:**§7 DoD 的每一条都必须
   绑定到至少一个定义节的 canonical snippet;存在未绑定的 DoD 条目即红**。
   ——机制 1–4 相当于 §5.4 台账 ①②③:清单全集由脚本自己定义,仍属 ⑬
   禁止的自指;文中六对是**历史事故清单,不是覆盖面**(实测另有十余对未列:
   §1.3↔DoD、§0 计数↔DoD、§3 twin↔DoD、§4 arch↔DoD、§5.2 三类冻结↔DoD、
   §5.3 三入口↔DoD 等)。把完整性锚到"DoD 全部条目"这一外部事实;
6. **引用侧候选发现**:新版文本中 snippet 的**全部规范化出现点**自动成为
   候选引用锚(否则"人工只许删"的会计恒等式在引用侧无来源);
7. **准入证伪(v1.10 补;⑬ 与 5.4.1-3 的教训迁移)**:**A₀ 首跑对 v1.9 的
   `BINDING_DRIFT` 必须 ≥1,且必须包含本轮已知两处**——
   ①`原始 git diff`(5.4.1-1/④)↔ §5.4.4/§5.4.3 —— **该处已在 v1.10 修复**,
   故首跑须**对 v1.9 快照**执行(证伪素材在 v1.9 中);
   ②§2.5 用例三"X 原样保留" ↔ DoD"未映射输入项原样保留"(同上,对 v1.9)。
   **即:准入证伪的被测对象是 v1.9,不是冻结版**;冻结版随后须为 0(机制 8)。
   **首跑为 0 即判定 binding 清单漏登,而非文档干净**。
   (理由:一个 binding 清单为空的脚本会立刻报 0、完美通过"BINDING_DRIFT 为 0"
   的验收——§5.4 用三轮才学会"门禁自身须先被证伪一次才有准入资格";
   本条把该教训**随机制迁移**,不再重上一课。)
8. **验收**:准入证伪通过后,冻结版的 `BINDING_DRIFT` 数为 0。

**准入证伪已将该事实规格化**(见机制 7),不再以散文形式存在。

## §6 commit 划分
- **A₀(冻结前置,v1.7 新增)**:`tools/design_drift_ledger.py` + 数据文件
  (**初始语料按 §5.4.4 的生成规则产出**(v1.9:删写死轮次))+ 首次实跑记录
  + 候选处置台账;**排在冻结与 commit A 之前**;
- **A** 抽取主体(**三模块按 §1.4 三模式各自验收**(非统一 cmp)+ §1.3 白名单 + pre-shim parity + 三址 shim + 消费方翻转);
- **B** 测试所有权(§4 矩阵 + monkeypatch 六处翻转 + 包根正反);
- **C** 门禁与审计(root-layers/independence/forbidden 扩列 + §2 例外规格与四负控制 +
  45 行入 SPECS + 三护栏 + bridge 接入与三路径钉定自证 + 三入口 + SKILL.md + 两阶段收口)。

## §7 DoD
- [ ] **迁移三模式各按其验收**(§1.4):edit_spec_guard `cmp` 空;
      build_verify `diff --unified=0` 仅三处白名单;
      **workspace 按 §1.4 四条**:①四个定义区段(三 FunctionDef 完整源区段
      含签名/注解/默认参数 + 常量赋值区段)AST source-segment 逐字节 + 整文件
      hunk 全落 import 头区;②**shared import binding 集合 == S9**(9 条
      shared import,另有 stdlib 头);③禁其余 S8 + 9 条一律不得用 `as X`
      同名别名 + **包根不导出 S9**;④本模块不适用 cmp;
- [ ] `default_extra_pythonpath` 迁移前后**返回有序 tuple 相等且非空**(新增测试 + parity 载荷);
- [ ] 45 符号入册,**bridge 输出三个 definition 路径的行且计数精确 29/12/4**;
- [ ] 三道 INCOMPLETE 护栏各生效;
- [ ] §2 例外:正向绿 + **四条负控制红(N1–N4,预期 broken 集合见 §2.2)** +
      `unmatched_ignore_imports_alerting=error` **分别落入两契约**;
      **`include_external_packages` 不得出现在配置中**(反向验收:grep 为 0);
- [ ] twin 八组各自注册,限定作用域精确命令证未合并;
- [ ] §4 分支表逐行有用例(含 build_timeout / mutated 的 **DENIED 断言**);
      arch 四例 + norm/raw 双向验证;
- [ ] pre-shim parity 一正三反 + post-shim identity 分列;
- [ ] 三入口 1/1/2/2;两阶段分列;subprocess 盲区双处登记;
- [ ] **§2.4 机械同步 10 项逐项**;**§2.5 三类 SPECS 语义**与 bridge relocation
      **六条负控制**(§2.5);
- [ ] 护栏为**集合等价**且 `MixedCaseAlias` 负 fixture 红;
- [ ] parity 的 UUID/UTC/GIT_*_DATE 冻结生效(非掩码);
- [ ] **§5.5 正向门禁**:A₀ 的 `BINDING_DRIFT` 数为 0(定义节与全部下游
      引用点规范化文本一致);
- [ ] **§4 表用例名已回写真实用例**(实现期硬项);
- [ ] **§5.4 ledger(四条,v1.10 现行)**:①`design_drift_ledger.py`
      存在且实跑(commit A₀);②**每模式附回跑 v(n-1) 命中数**且等于实际出现
      次数(预防性模式附构造式证伪);③本轮 diff 已自动导出并附**候选处置
      台账四条**(exported == retained ∪ ignored、不相交、**每个 ignored 带
      diff span 与机械类别**、**span 覆盖全部删除行**);④实际命中集 == 期望
      命中集,范围为全部规范正文(除修订说明与 §5.4 自身);
- [ ] **relocation synthetic 三用例(v1.7 补齐)**:①A→B 被消费/产生
      (硬编码 LEGACY_KEYS 必失败);②输入不含 A ⇒ consumed 为空 +
      `UNMAPPED_SOURCE`(echo 实现必失败);③`{A→B, C→D}`、**输入含 A + X**
      (X 为未映射项,v1.9 同步 §2.5)⇒
      `consumed=={A}` **且产出含 B、不含 A/C/D、C 报 `UNMAPPED_SOURCE`、
      未映射输入项原样保留**;三者断言**须同时落在产出表/verdict**,
      不得仅以 `consumed_sources` 为证据;
- [ ] **DEFERRED**:`EDIT_SPEC_SCHEMA` 单一权威→patch-suggest 批次;
      测试私有件消费面收窄→P4.9 末;其余沿既有四项。

---
## 附:声明
- **零生产行为变更**:edit_spec_guard 逐字节;build_verify 逐字节除 §1.3 三处白名单;
  workspace **按模式三部分抽取**(四定义区段逐字节 + 重构 import 头,§1.4);
- **零归属判据变更**:§0/§0.1 dry-run 证明;
- **本批机制新增**:§2 例外契约(`gbs_patch_suggest` 入 root_packages +
  skill-independence 承载 + 模块级 ignore;**不含** `include_external_packages`);
- **非抽取交付项**:三入口、§4 矩阵补测、§1.3 锚点测试、注释复核、盲区登记。
