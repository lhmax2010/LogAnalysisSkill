# P4.9 skill-4 设计:tizen-build-verify 抽取(v1.1-draft)

- 阶段:P4.9 第四批(skill-3 CLOSED @1ca2206)
- 权威并行:step-0 `v2.1-FROZEN`、skill-1 `v1.4`、skill-2 `v1.3`、skill-3 `v1.3.1`
- **基线**:`883 passed, 1 skipped`(遵"既有集合不缩小且无失败,非总数冻结")
- **总铁律**:行为等价——逐字节迁移 + **具名白名单差异**(§1.3),零语义变更

> **v1.1 重写说明**:三家评审判 v1.0 不可冻结(2 BLOCKER + 若干 MAJOR),
> 本稿据此重写,非补丁。核心变更:①三模块 45 符号(B-2);
> ②`default_extra_pythonpath` 的 `__file__` 锚点裁决(B-1);③例外契约钉死
> 含 `include_external_packages` 与四条负控制;④twin 补至 8 组;⑤arch 集
> 设计期钉死 + 结果态补 `build_timeout`;⑥§0 test 列标注非权威;
> ⑦补 §5.1/§5.2 完整定义。

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

**计数**:build_verify 29 + edit_spec_guard 12 + workspace 迁入 4 = **45**
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
  workspace.py       # 4 符号(自 ci_triage/verify/workspace.py 迁入,step-0 已判归属)
```

**三道 INCOMPLETE 护栏**(每模块一道,MINOR-①):三模块公共面全覆盖,防后续
新增符号漏册;自证断言**精确钉定 29/12/4**,不接受"三路径各≥1 行"。

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
1. **调整锚点为位置无关**:改为自身包根向上定位仓库根(实现期给出精确表达式),
   使迁移前后**返回值集合相同**;
2. **申报为 cmp 白名单差异**:该行是逐字节迁移的**具名例外**(与 import 翻转
   同类),白名单逐行列出、不得泛化;
3. **补测试锁定**(本批新增):迁移前后各断言其返回值集合相同——**零测试覆盖
   正是它能静默漂移的原因**;该函数输出并入 §5.2 parity 载荷。

## §2 具名例外:`tizen_build_verify.build_verify → gbs_patch_suggest.formatter`

采方案 (d):`gbs_patch_suggest` **保持 skill 身份**,不重定义层级;
skill-independence 不放宽;**例外须具名、单向、单模块**。

### 2.1 配置规格(钉死,MAJOR-②)
- **`include_external_packages = True`**(实测硬前提:缺它 lint 直接 exit 1);
- `gbs_patch_suggest` 加入 root_packages(实测其零 ci_triage/零 shared 依赖,不引爆既有边);
- 例外精确到**模块级**:`tizen_build_verify.build_verify -> gbs_patch_suggest.formatter`;
- **`unmatched_ignore_imports_alerting = error`**(防例外字符串失效后静默漂移)。

### 2.2 负控制四条(v1.0 仅一条,不足以证"未泛化")
| # | 构造 | 期望 |
|---|---|---|
| N1 | `tizen_qb_discover → gbs_patch_suggest.formatter` | 红(他 skill 不可用) |
| N2 | `tizen_build_verify.edit_spec_guard → formatter` | 红(同 skill 错模块) |
| N3 | `tizen_build_verify.build_verify → gbs_patch_suggest.analyzer_runner` | 红(错子模块,未泛化为整包) |
| N4 | `gbs_patch_suggest → tizen_build_verify` | 红(单向) |
正向:上述精确边绿。

### 2.3 subprocess 盲区(v1.1 更正为真实链,MAJOR-⑥)
v1.0 登记的 `gbs_patch_suggest→gbs_analyzer` **与本批例外无关**(formatter 不调
analyzer_runner)。真实链是 **`build_verify.py:401`:
`options.python_executable, "-m", "gbs_analyzer", "analyze", ...`**,即
`tizen_build_verify.build_verify --subprocess/python -m--> gbs_analyzer`;
另有 `gbs`、`git`、迁入 workspace 后的 `cp -a` 等外部命令依赖。
**登记为静态门禁盲区**:import-linter 不可见,"六契约全绿"不等于跨包依赖已全覆盖。
持久登记位置:`.importlinter` 头部注释 + campaign 级总账(NIT-⑤)。

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
**新增 DEFERRED**:`EDIT_SPEC_SCHEMA` 是跨包 schema 版本标识的**双权威**——
一侧升版另一侧未同步时 `validate_edit_spec` 会静默接受旧 schema;
**schema 常量单一权威 → patch-suggest 相关批次**。

测试侧同名 helper(`_git` 等)列为 **raw-grep false positive**,不入 twin 表。

## §4 §5.1 分支覆盖表(结果态补全,MAJOR-③/⑤)

**arch 维度(设计期钉死,不留实现期裁量)**:
`standard-aarch64→aarch64`、`standard-armv7l→armv7l`、`standard-x86_64→x86_64`、
`aarch64→aarch64`(无前缀代表样本);并验证 **GBS argv 用 norm 值、failure key/record
保留 raw 值**。既有 `test_gbs_arch_removes_standard_prefix` 已参数化覆盖,矩阵须
写明"既有覆盖 vs 本批新增 delta",避免重复计数。

**结果态(v1.0 四支 → 补全)**:成功 / 构建失败(classify)/ patch 应用失败 /
edit-spec 违规 / **`build_timeout`(:223-232,断言 `repair_allowed=REPAIR_DENIED`)** /
**`build_mutated_source`(:236-244,同断言 DENIED)** / 两种 `no_effective_changes` /
`git diff --check` 失败 / unexpected paths / analyzer 失败或未产 evidence /
分类失败 / marker/DB 写入异常原样传播。

**超时契约形状对照(写入设计,防混用)**:skill-3 冻结"无 timeout、TimeoutExpired
原样传播";**本 skill 有一等公民 `wall_timeout`**(:63 必填,:359 下传)——两者
形状相反。

**既有测试优先迁入**(timeout、no-effective、mutation 等已有覆盖),
落入唯一"契约句 → 分支 → 用例"表,不重写重复 fixture。

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
- **逐字段相等为主证据**,固定 JSON SHA 仅作锚;
- **一正三反 normalizer**:正(仅路径不同→掩码后相等);反(改 `failure_class`、
  换命令顺序、改 `repair_allowed`→ 必红,**变异落非路径部分**);
- 取证于**改 shim 之前**;双跑隔离用 `importlib.reload` 或子进程。

### 5.3 post-shim identity / 三入口 / 两阶段
沿 skill-3 范式:identity 只证接线;三入口(pyproject packages+mypy_path /
ci.yml mypy 清单 / README PYTHONPATH)+ 四条精确计数自检(先在已完成 skill
样本上验命令);`release-v1.4.0` 不回填;B 临时脚手架 / C `pip install -e .`
后 `env -u` 无脚手架复跑,证据分列。

## §6 commit 划分
- **A** 抽取主体(三模块 cmp + §1.3 白名单 + pre-shim parity + 三址 shim + 消费方翻转);
- **B** 测试所有权(§4 矩阵 + monkeypatch 六处翻转 + 包根正反);
- **C** 门禁与审计(root-layers/independence/forbidden 扩列 + §2 例外规格与四负控制 +
  45 行入 SPECS + 三护栏 + bridge 接入与三路径钉定自证 + 三入口 + SKILL.md + 两阶段收口)。

## §7 DoD
- [ ] 三模块 cmp 逐字节 + **§1.3 白名单逐行列出**(锚点行 + import 翻转行);
- [ ] `default_extra_pythonpath` 迁移前后**返回值集合相同**(新增测试 + parity 载荷);
- [ ] 45 符号入册,**bridge 输出三个 definition 路径的行且计数精确 29/12/4**;
- [ ] 三道 INCOMPLETE 护栏各生效;
- [ ] §2 例外:正向绿 + **四条负控制红** + `include_external_packages` 与
      `unmatched_ignore_imports_alerting=error` 落盘;
- [ ] twin 八组各自注册,限定作用域精确命令证未合并;
- [ ] §4 分支表逐行有用例(含 build_timeout / mutated 的 **DENIED 断言**);
      arch 四例 + norm/raw 双向验证;
- [ ] pre-shim parity 一正三反 + post-shim identity 分列;
- [ ] 三入口 1/1/2/2;两阶段分列;subprocess 盲区双处登记;
- [ ] **DEFERRED**:`EDIT_SPEC_SCHEMA` 单一权威→patch-suggest 批次;
      测试私有件消费面收窄→P4.9 末;其余沿既有四项。

---
## 附:声明
- **零生产行为变更**:三模块逐字节迁移,**除 §1.3 白名单外**无差异;
- **零归属判据变更**:§0/§0.1 dry-run 证明;
- **本批机制新增**:§2 例外契约(含仓库级 `include_external_packages`);
- **非抽取交付项**:三入口、§4 矩阵补测、§1.3 锚点测试、注释复核、盲区登记。
