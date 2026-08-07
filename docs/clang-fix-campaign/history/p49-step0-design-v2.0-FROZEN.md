# P4.9 step-0 设计:共享层下沉与 marker 权威归位(v2.0-FROZEN)

- 阶段:P4.9 step-0(六 skill 抽取的地基,先于任何 skill)
- 前置:P4.5 已 merge(v1.5.18-FROZEN);提纲四轮评审收敛(v3.1)
- **版本说明**:本稿为 **v2.0-FROZEN**,收敛自 v1.0–v1.12 全部裁决;
  生效结论已合并进正文对应节,不再叠补丁(消除 body/appendix 三次
  漂移)。归属表经
  symbol_audit 最新轮次 **N/N** 机械核验(design SHA 见审计报告)。
- **总铁律**:行为等价——只搬家 + 建共享层 + 改 import 路径,零语义
  变更;完成后测试数 == P4.9 启动 merge 基线数,原样全绿(测试内容
  不变、import 路径与 patch 目标字符串可改)。

---

## §1 C 类库物理归属与内部分层

### 1.1 决策:独立 `tizen_ci_shared` 顶级包

现状 state/keys/records 物理在 `ci_triage/state/`(编排包内)。若 skill
`import ci_triage.state` 则 skill 反依赖编排层。**决策**:建独立顶级
包 `tizen_ci_shared`(物理 `tizen-ci-shared/scripts/tizen_ci_shared/`,
与六 skill、ci_triage 平级),承载全部 C 类库。依赖单向:

```
skill ──→ tizen_ci_shared ←── ci_triage(编排层)
           内部再分三层(§1.3),types 为最底
```

- PYTHONPATH 前缀加 `tizen-ci-shared/scripts`(与现四路径并列);
- release:`release-v1.4.0/` 新增 `tizen-ci-shared/` 项,pyproject
  packages 加 tizen_ci_shared;`runner.py:241` sibling 名单扩充属各
  skill 批次的语义变更,step-0 不动(下沉 discover_sibling_pythonpath
  行为等价,见 §3.3)。

### 1.2 shared 内部结构(下沉清单,一次冻结)

```
tizen_ci_shared/
  types.py            # L-1 最底:纯数据类型(§2),零 shared 内部依赖
  env.py              # L0 :commit ① 空占位;commit ② 迁 discover_sibling_pythonpath
  quickbuild_http.py  # L0 :commit ① 空占位;commit ③ 迁 HTTP 公共面(§4)
  state/              # L1 :commit ① 迁 ci_triage/state/{db,keys,records}
  workspace/          # L1 :commit ① 空占位;commit ② 迁 marker/worktree(§3)
  classify.py         # L1 :commit ① 空占位;commit ② 迁 failure_classify
```

commit ① 的四个占位文件各自**仅含一行 docstring**,零 import、零定义、
零逻辑;能力仍分别在 commit ②/③ 迁入。占位期不得夹带实现,验收必须
逐文件贴 `wc -l` 与 `cat` 原文。占位只让四条层级契约能加载,不改变
symbol_audit 归属清单(空文件无符号)。

**edit_spec_guard 不在此**:实测仅 build_verify 消费(单消费方),随
build-verify skill,非 shared(S-2b)。

### 1.3 shared 内部三层契约(方法论⑪:共享层必须内建层级)

```
L1: state | workspace | classify   (领域层,互相独立)
       ↓ 只能向下
L0: quickbuild_http | env          (原语层)
       ↓ 只能向下
L-1: types                         (纯数据,最底)
```

层规则:①L-1 不 import 任何上层;②L0 只 import L-1,L0 内模块互不
import;③L1 只 import L-1/L0,L1 三域互不 import;④全 shared 不 import
skill / ci_triage 编排层。同层互不 import 由 independence 契约强制,
不是依赖 `layers` 配置中的并列语法假设。

**import-linter step-0 实际落盘版(随 commit ① 落盘)**:

```ini
[importlinter]
root_packages =
    tizen_ci_shared
    ci_triage

[importlinter:contract:shared-layers]
name = shared 内层:L1 -> L0 -> types
type = layers
layers =
    state | workspace | classify
    quickbuild_http | env
    types
containers = tizen_ci_shared

[importlinter:contract:shared-no-uplink]
name = shared 不得 import 编排层或 skill
type = forbidden
source_modules = tizen_ci_shared
forbidden_modules = ci_triage

[importlinter:contract:shared-l1-independence]
name = shared L1 领域互不 import
type = independence
modules =
    tizen_ci_shared.state
    tizen_ci_shared.workspace
    tizen_ci_shared.classify

[importlinter:contract:shared-l0-independence]
name = shared L0 原语互不 import
type = independence
modules =
    tizen_ci_shared.quickbuild_http
    tizen_ci_shared.env
```

step-0 **只落上述 4 条生效契约**。四个空占位使所有模块路径真实存在;
正向 `lint-imports` 必须在 commit ① 对这四条同时 exit 0。下面是
**目标全集模板**,step-0 配置中整体注释或省略,不得以生效 contract
落盘:

```ini
# [importlinter:contract:root-layers]
# name = 根级:ci_triage / skills / shared 单向
# type = layers
# layers =
#     ci_triage
#     tizen_qb_discover | tizen_gerrit_fetch | tizen_build_verify | tizen_convergence_judge | tizen_gerrit_submit | tizen_triage_report
#     tizen_ci_shared
# containers = <按 import-linter==2.3 实测确认,不得照抄猜测>
# 首个 skill 抽取批次启用;每个 skill 批次填入自身那格。

# [importlinter:contract:skill-independence]
# name = 六个 skill 互不 import
# type = independence
# modules =
#     <已抽取的真实 skill root;随批次增量填入>
# 首个 skill 批次启用,并同补该 skill 的横向负控制。
```

**四类反向验证(S3-A,每条生效契约一类)**:

1. commit ①:types 加 `import tizen_ci_shared.state` → shared-layers 红;
2. commit ①:shared 加 `import ci_triage` → shared-no-uplink 红;
3. **顺延 commit ②**:workspace 能力落地后,state↔workspace 横向 import
   → shared-l1-independence 红;
4. **顺延 commit ③**:quickbuild_http/env 能力落地后,L0 横向 import
   → shared-l0-independence 红。

顺延不是免做:commit ②/③ 的验收报告必须分别贴对应 `lint-imports`
exit 1 与报错原文并回填 dev_memory;任一顺延项未在绑定 commit 转正,
step-0 不得声称完成。目标全集中的 root-layers/skill-independence 在
首个 skill 批次启用,同时补横向负控制;`containers` 写法按钉定版本
实测,不得沿用未经验证的 `containers = .` 假设。

**每 commit 后 `lint-imports` 必须绿**。commit ① 用钉定的
`import-linter==2.3` 实跑四条正向 exit 0 + 上述两条可构造的反向
exit 1;若空占位、layers/independence/forbidden 或其它配置语法与 2.3
不兼容,立即停止报告,不得改契约凑绿。`shared/__init__.py` 冻结为
**空或仅导出 types**,避免 `import tizen_ci_shared` 连带拉起 state。

**import-linter 为新增 dev-dep**,pyproject dev-deps精确钉定
`import-linter==2.3`,挂现有 .github workflow。

## §2 跨 skill 数据类型下沉(types.py,L-1)

| 类型 | 现定义 | 实测消费方 | 归属 |
|---|---|---|---|
| `SourceFetchResult` | gerrit.py | report | shared/types |
| `FailedPackage` | quickbuild_log.py | orchestrator/report/runner | shared/types |
| `FailureClassification` | failure_classify.py | build_verify(随 classify 模块) | shared/classify |
| `DisposableWorktree` | workspace.py | build-verify + 清理链 | shared/workspace |
| `WorkspaceViolation` | workspace.py | campaign_repair_step + 清理链 | shared/workspace |

原定义处留 re-export shim,P4.9 全 skill 抽完统一删(§6)。

## §3 workspace 函数级归属 + 双 marker 权威

### 3.1 两个 marker 全归 shared/workspace(权威唯一)

| marker | 常量 | 写 | 读 |
|---|---|---|---|
| protected | `PROTECTED_FILENAME` | build-verify(何时写,调原语) | wrapper/submit(经原语) |
| workdir | `MARKER_FILENAME` | `write_workdir_marker`(§3.2 待建) | 清理链 |

两个 FILENAME 常量 + `_read_marker` + marker 结构 = shared 唯一定义;
build-verify **不自持任何 marker 格式常量**,只调 shared 原语。

### 3.2 函数级归属表(调用图证据,方法论⑩硬闸;经 symbol_audit 核)

| 符号 | 完整调用图 | 归属 |
|---|---|---|
| `create_worktree` | 仅 build_verify:133 | build-verify(调 shared write_workdir_marker) |
| `check_disk_and_maybe_cleanup` | 仅 build_verify:126;内部调 cleanup_worktree | build-verify(下行依赖 shared) |
| `_copy_repository` | 仅 create_worktree:58 | build-verify |
| `write_workdir_marker(worktree_path: Path) -> None` | create_worktree 将调;写 MARKER_FILENAME + marker dict | **shared/workspace**(`to-be-created`) |
| `cleanup_worktree` | build_verify:143 + workspace 内部:124/186 | shared/workspace |
| `cleanup_disposable_copy` | campaign_repair_step | shared/workspace |
| `is_protected` | campaign_repair_step | shared/workspace |
| `release_worktree_protection` | gerrit_submit | shared/workspace |
| `mark_worktree_protected` | build_verify(调用) | shared/workspace(格式权威) |
| `_oldest_worktrees`/`_run_git`/`_verify_cleanup_handle`/`_exclude_private_files`/`_read_marker` | 清理链/marker 内部 | shared/workspace |
| marker 常量 ×2 + `DisposableWorktree`/`WorkspaceViolation` | §2/§3.1 | shared/workspace |

判据:单消费方随消费者(create_worktree/_copy_repository→build-verify);
多消费方或格式权威→shared。skill→shared 下行合法。

### 3.3 build_verify 反向依赖清理(前置)

`build_verify.py:27` 反向 `import ci_triage.runner.discover_sibling_pythonpath`
——编排层→被抽 skill 的反向边。**裁决**:`discover_sibling_pythonpath`
下沉 **shared/env.py**(L0,纯 stdlib、按调用方传入 `launcher_path`
锚定、不用 `__file__`,行为等价安全)。当前实测直接消费方为
`ci_triage.batch_cli` / `ci_triage.cli` / `ci_triage.orchestrator` /
`ci_triage.verify.build_verify`;`runner.py` 是定义模块,不是消费方。
四方均改 `import tizen_ci_shared.env`。该符号**单点入
symbol_audit 清单**(此前盲区);`runner.py` 属不抽取的编排层,
不加公共面全面 INCOMPLETE 护栏,其余 14 个公共符号不进入 step-0
归属清单。

## §4 QuickBuild HTTP 归属(分层落地)

### 4.1 HTTP 件下沉 shared/quickbuild_http(L0)

实测消费面横跨编排层 + 多消费方,无单一 skill 独占 → 全归 shared:
`HttpFetcher`/`HttpResponse`/`QuickBuildError`/`_raise_if_login_page`/
`_urllib_fetch`/`load_cookie_jar`/`download_full_log`/
`download_package_buildlog`/`DEFAULT_COOKIE_PATH`/
`DEFAULT_QUICKBUILD_BASE_URL` 等 quickbuild.py 全部 HTTP 公共面(17 项,
symbol_audit INCOMPLETE 护栏覆盖)。qb-discover 保留"失败发现语义"
(sources.py discovery + 失败包解析),消费 shared HTTP 层。

`gbs_report.py` 整模块不在 step-0 改动与审计范围内;它继续从
`quickbuild.py` 的兼容 re-export 消费 HTTP 件。fetch/parse 拆分及
模块内类型归属统一延期到 triage-report 抽取批次(§8)。

## §5 回归绑定与 parity(行为等价证明)

### 5.1 测试改动边界(v1.1 S-5 放宽,已并入正文)

允许的测试修改**仅两类**:①import 路径(`ci_triage.verify.*` →
`tizen_ci_shared.*`/skill 路径);②**monkeypatch/setattr 目标字符串
中的模块路径**(patch 目标含模块路径,下沉后必须跟改)。断言与
fixture 数据内容一字不改。diff 审核标准:测试文件 diff 只含这两类。
C15(源码子串断言清理)在 step-0 顺带处理这类字符串。

### 5.2 parity 归一化规则

比对下沉前后同输入的输出对象,掩码易变字段:①`at` 时间戳;
②worktree 绝对路径;③tmp 文件名;④**cookie 路径 / base_url 等环境
派生绝对路径**(S3-3);⑤**workdir marker 内嵌的 `workspace_root`
绝对路径**(两次 checkout 临时根不同必不等,入掩码——或双跑固定同
一 fixture 根,二选一:**本设计取掩码**);⑥`check_disk_and_maybe_cleanup`
的 `warnings` 含实际磁盘余量、非纯输入函数 → parity 豁免;
⑦`_oldest_worktrees` 的 mtime 序 → fixture 固定 mtime。
**其余字段严格相等**;§5.2 拒绝"所有路径"泛化,任何新增掩码须附
parity 差异证据。marker 文件内容除时间戳 + 上述路径掩码外逐字节相等。

### 5.3 import-linter 全集契约

见 §1.3。step-0 落盘 **4 条生效契约**:shared-layers、
shared-l1-independence、shared-l0-independence、shared-no-uplink。
root-layers 与 skill-independence 仅为目标全集注释模板,首个 skill
批次填入真实模块后启用;skill↛skill 最终由 skill-independence 强制,
不是 `layers` 中的并列符号附带表达。

### 5.4 全量基线

step-0 完成后测试数 == P4.9 启动 merge 基线数(change_46 落测试后
的数,不写死),原样全绿 + lint-imports 绿。

### 5.5 审计锚点

本稿归属表经 symbol_audit round-N 核验(N/N OK)。审计报告
`p49-step0-symbol-audit.md` 记录本设计稿的 SHA-256、审计命令与
审计结果;报告与本稿的完整性由其所在 Git commit 锚定,文件内
不自记自身 SHA。验完整性时用 `git show <commit>:<path>` 取得
commit 中的版本,再用 `sha256sum` 复算;锚在 commit,不锚在文件内容。

## §6 shim 生命周期与执行

### 6.1 三 commit 划分(每 commit 后全量测试 + lint-imports 双绿)

- **commit ①**:建 tizen_ci_shared 包 + 迁 state/types + 四个一行
  docstring 空占位 + **import-linter 4 条契约配置落盘**(必须随 ①,
  否则 ②③ 无 lint 可跑);正向四条全绿、反向两条实测;
- **commit ②**:迁 workspace(双 marker + write_workdir_marker 新建)
  + **classify**(edit_spec **不搬**,随 build-verify,S-2b)+ 反向
  依赖清理(discover_sibling_pythonpath → shared/env);补做 L1
  independence 顺延反向验证并回填证据;
- **commit ③**:HTTP 件下沉 shared/quickbuild_http(quickbuild.py 17
  符号);`gbs_report.py` 原样不动;补做 L0 independence 顺延反向
  验证并回填证据。

### 6.2 shim 删除清单(P4.9 六 skill 全抽完后统一执行,单 commit)

- gerrit.py / quickbuild_log.py / workspace.py / failure_classify.py
  的 re-export 行;
- **`quickbuild.py` 的 17 个 HTTP 符号 re-export**(明确属主:随
  commit ③ 下沉后原位留 shim);
- **`verify/__init__.py` 包级 re-export 面**(S-4,转出 workspace/
  classify 等);
- **不含 `edit_spec_guard.py`**(不下沉、无 shim,S-2b)。
- `ci_triage/state/`:commit ① **全量翻转 import、不留 shim**(state
  包内部仅包内 import、无上行依赖,整体迁移干净)。

## §7 DoD

- [ ] tizen_ci_shared 独立包建立,三层 + step-0 **4 条生效契约**
  `lint-imports` 正向绿;**4 类反向验证**各自转红并记录 exit code:
  commit ① 实测 shared-layers/shared-no-uplink 两类,L1 independence
  具名顺延 commit ②,L0 independence 具名顺延 commit ③;顺延项未在
  对应 commit 补做并贴 exit code,step-0 不得声称完成;
- [ ] commit ① 四个占位文件各仅一行 docstring(`wc -l` + `cat`
  原文留证),零 import/定义/逻辑;能力迁入前不得扩写;
- [ ] 两个 marker 格式常量在 shared 唯一定义(`grep FILENAME =` 仅
  shared 命中,**排除 `release-v1.4.0/` 快照副本**);
- [ ] **S-1 机械验证**:`write_workdir_marker` 落地 +
  `create_worktree` 函数体 grep 无 `FILENAME`(marker 写入已移原语);
- [ ] workspace 函数级归属按 §3.2 落地;discover_sibling_pythonpath
  单点入 symbol_audit 且四消费方一致,全 OK;runner.py 不加全面护栏;
- [ ] **审计范围一致**:symbol_audit 只覆盖 step-0 实际触碰面;
  quickbuild.py 公共面护栏全绿,`gbs_report.py` 无 inventory、无公共面
  护栏、无生产 diff(延期项见 §8);
- [ ] 全量测试 == 基线数、原样全绿;测试 diff 仅 §5.1 两类;每 commit
  lint-imports 绿;
- [ ] parity:build-verify/convergence 关键路径下沉前后归一化相等
  (§5.2 掩码);
- [ ] 三 commit 各自双绿;shim 清单(§6.2)登记待 P4.9 末删除。

## §8 移出项:GBS report 整模块延期

`ci_triage/gbs_report.py` 在 step-0 **原样不动**,其全部公共面与私有
helper 均不进入 step-0 symbol_audit。fetch/parse 拆分、
`GbsReportPackage`/`GbsReport` 类型归属、iframe 抽取闭包与
`_attrs_to_map`/htmlutil 层位统一延期至 **triage-report 抽取批次**。
该批次必须把 fetch 与 parse 放在同一设计窗口内,一次性解决完整闭包,
不得再作为 HTTP 下沉的附带裁量夹入其它主变更。

七轮推演形成的约束保留为后续批次输入:

1. 若引入 raw 抓取结果,其字段必须覆盖 parse 的真实输入,至少包括
   `iframe_url` 与 `build_id`;字段由调用图实测决定,不得凭空冻结。
2. 跨边界迁移按完整依赖闭包设计;闭包至少核对
   `QuickBuildError`、HTTP 原语、iframe 定位链和 parser 输入,且闭包内
   不得留下未声明的上行依赖。
3. 结构断言按阶段执行:拆分前不得拿目标态 AST 约束现状;实现完成后
   必须转入严格结构校验,出现新增算法分支即红。
4. 若未来确有“范围内但目标形态尚未形成”的符号,审计状态须明确区分
   `existing`/`to-be-created`/`to-be-refactored`;过渡态必须显著计数并
   绑定转正 DoD,不能成为永久免检。
5. 若保留 composition shell,它只能组合已归属的 raw fetch、parse、
   类型构造与 return,并以 AST 允许调用集合防滥用;也可在同批次裁定
   直接拆分,但不得临场猜测。
6. `find_iframe_src`/`_IframeParser` 与 `_attrs_to_map` 的层位必须随完整
   调用闭包重新裁定;不得只迁入口符号。是否新建 htmlutil 由该批次
   的真实复用面决定。
7. `gbs_report.py` 的 inventory 与公共面完整性护栏必须同进同出;
   triage-report 批次重新纳入时二者同一 commit 恢复。

备选的 `deferred/out-of-scope` 审计状态本轮**不实现**。只有未来出现
“符号仍在当前抽取范围内但确需延期”的真实案例时,才另行设计其
防滥用契约;模块整体移出范围不需要临时豁免。

### 8.1 step-0 实现期遗留(不阻塞本次冻结,有关闭时点)

- **⑫ 自证桥脚本化**:当前设计表格 ↔ symbol_audit inventory 仍是
  硬编码 + 人工对账。机械 diff 必须在 step-0 实现期落地,最晚不超过
  commit ③;未完成前每轮改归属表都须保留人工逐项对账证据。
- **root-layers `containers` 语法**:step-0 实际配置不落跨 root
  contract。首个 skill 批次启用 root-layers 时,必须用钉定版本实测
  `containers` 写法的正向 exit 0 与反向非零;未经实测不得采用
  `containers = .`。同批次启用 skill-independence 并补横向负控制。

---

## 附:方法论账(⑩—⑰ + 本稿相关)

- **⑩**(归属/切割断言须 symbol_audit,人工表仅草案):本稿归属表经
  最新轮次 N/N,新增 discover_sibling_pythonpath 入册补盲区。
- **⑪**(共享层必须内建依赖层级,不做扁平包):§1.3 三层 + import-linter
  layered contract,倒置构建期物理不可能。
- **⑫**(本稿新立):**正文即契约,附录不得携带未合入正文的生效裁决。**
  本文档 body/appendix 漂移三次复发(§5.1/§6/§7 旧文与附录裁决并存、
  自相矛盾),违反⑨"正文为准"。自本稿起:每轮修订**直接改正文**,
  附录仅记过程摘要;冻结前必过一遍"正文 grep vs 裁决清单"一致性检查
  (可脚本化:设计稿表格 ↔ symbol_audit 清单自动 diff,消除人工声明
  的审计桥缺口)。
- **⑬**(完整性锚点禁止自指):任何产物不得在自身内容中记录其自身
  SHA、长度、位置等“记录后即改变”的属性;完整性锚必须落在产物
  之外的不可变载体(Git commit、外部清单或上游 change 文档)。本稿
  与审计报告均不自记自身 SHA,由包含二者的 Git commit 锚定。
- **⑭**(护栏必须由自身工具实测):配置文本不是生效证据;每条
  import-linter contract 必须有正向 exit 0 与故意违反后的非零 exit。
- **⑮**(审计判据按符号结构分类):数据类型、能力函数与组合外壳的
  归属逻辑不同;新增类别必须同时提供防滥用结构断言。
- **⑯**(审计状态覆盖时间维度):待建与待重构是延期而非豁免;每个
  过渡态必须绑定转正时点、转正后的强校验和显著计数。
- **⑰**(跨边界迁移以依赖闭包为单位):迁入口而漏被调者会把上行依赖
  藏进函数体;设计期须列闭包且闭包内符号层级不得高于入口。
  v2.0-FROZEN 把持续外溢的 GBS 闭包整体移出 step-0,是该规则的
  范围治理应用。
