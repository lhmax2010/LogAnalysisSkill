# P4.9 skill-3 设计:tizen-gerrit-fetch 抽取(v1.3-FROZEN)

- 阶段:P4.9 第三个 skill 批次(skill-2 CLOSED @90b90e4 之后)
- 权威并行:step-0 `v2.1-FROZEN`、skill-1 `v1.4-FROZEN`、skill-2 `v1.3-FROZEN`
> **v1.1 修订(两家评审,四条实测坐实)**:①【Kimi MAJOR】`_run_git`
> 消费方歧义为真——`workspace.py:25` 是 `from tizen_ci_shared.workspace
> import _run_git as _run_git` 且**自身零顶层定义**,twin-guard 不生效,
> 抽取后必红;新增 commit A' 工具加固(import-binding 追踪)。②【CC①】
> §1.2 明列的类型 import **两处并存、角色不同**,skill 副本必须自带(签名真依赖:
> :37/:87/:100/:129/:203/:211),v1.0"不随 skill 迁移"照字面实现会崩。
> ③【CC②a】两份 `SubprocessRunner` **逐字节相同**,理由改沿 skill-2
> `_normalize_text` 先例。④【CC②b】SPECS 中 `_run_git` 仅注册
> workspace 一份,本批为**两份注册**(workspace+gerrit),非三份。
> ⑤Kimi NIT-1/3/5、CC③④ 一并收。
> **v1.2**(两家 delta,均 conditional freeze-ready):⑥【两家共提,唯一
> 实质】§5 注册面漏改——v1.1 已在 §1.3/§7 更正为"两份注册",§5 仍写
> "三份 `_run_git` 与两份 `SubprocessRunner`",**撞⑫批内漂移**,本版
> 改齐;`SubprocessRunner` 亦仅 gerrit 一份入册(runner 侧属编排层不抽)。
> ⑦Kimi NIT-2/3/4:负 fixture 补"构造文件自身零顶层定义 S"前提;
> `import X; X.S` 形式列 known-limitation;workspace `_run_git` 措辞
> 更正为 module-scope 覆盖。⑧CC NIT:§1.2 语义接缝顺句。
> **性能评审 1 裁决:A(暴露无界阻塞契约 + 性能等价取证 + 超时延期)**:
> SSH 查询与全部 git 调用均不新增 timeout/cancellation;在 SKILL.md
> Errors / Side effects 暴露无限阻塞、`TimeoutExpired` 传播及中断残留。
> §5.2 既有有序命令轨迹同时验收调用次数、发生顺序与每次调用的完整
> `argv` 逐元素不变,并从 `argv` 验收 fetch 次数及 `--depth 1/50`,作为
> pre-shim parity 的性能等价证据;统一超时/取消/错误归一化/清理
> 策略具名延期至 `gerrit-submit` 批次,不得在抽取批次顺手实施。
> **v1.3 修订(本轮架构/代码质量/测试/性能/一致性评审全量合入;
> 本次三项必检通过后落章为 FROZEN)**:
> - 交付面显式同步与历史 release 边界 → §2 / §4a / §7;
> - `ImportFrom` 来源名/本地名绑定语义 → §1.3a / §6 / §7;
> - 破坏性输入、混合失败与残留契约 → §2.2 / §5.1 / §7;
> - pre-shim parity 与 post-shim identity 证据分流 → §5 / §6 / §7;
> - 交付入口 DoD 命令及已知绿样本自检 → §7;
> - 总结/附录边界重述 → 文末附录;
> - import-binding 断言在规则、执行与验收层对齐 → §1.3a / §6 / §7;
> - 负控制与正向证据按极性分组 → §3 / §6 / §7;
> - 验证脚手架与正式交付入口分段取证 → §6 / §7;
> - 失败、返回与破坏性边界的行为分支表 → §5.1 / §6 / §7;
> - parity canonical payload、白名单掩码与反向证明 → §5.2 / §6 / §7;
> - skill 行为、编排集成与 legacy wiring 测试所有权 → §5.3 / §6 / §7;
> - 无界阻塞契约、传播边界与具名延期 → §2.2 / §5.2 / §7;
> - 调用拓扑、清理成本与结构性能等价 → §2.2 / §5.2 / §7;
> - 消费测量、package-root API 与旧址兼容面分离 → §0 / §1.2 /
>   §2.1 / §5.3 / §7;
> - §0 唯一归属表与设计期/实现期取证分离 → §0 / §6 / §7;
> - FROZEN 版本身份与单独冻结门 → 本修订块 / §7。

- **总铁律**:行为等价——整体搬移 + import 翻转,零语义变更;基线 ==
  skill-2 收口全量数(847/1),原样全绿。

---

## §0 判据 dry-run(v1.3 新规,冻结前置,已完成)

Claude 实测 @57c04e2,将规划终态 SPECS 与实测消费方喂入 v1.3 层化
判据。下表是本稿**唯一权威归属表**;bridge parser 读取本节首张表,
其余章节只引用本表全部行。

| symbol | definition | owner | measured_consumers | verdict |
|---|---|---|---|---|
| `GERRIT_HOST` | `tizen_gerrit_fetch/gerrit.py` | `skill/tizen_gerrit_fetch` | - | OK |
| `GERRIT_PORT` | `tizen_gerrit_fetch/gerrit.py` | `skill/tizen_gerrit_fetch` | - | OK |
| `SubprocessRunner` | `tizen_gerrit_fetch/gerrit.py` | `skill/tizen_gerrit_fetch` | - | OK |
| `GerritError` | `tizen_gerrit_fetch/gerrit.py` | `skill/tizen_gerrit_fetch` | - | OK |
| `query_change_for_commit` | `tizen_gerrit_fetch/gerrit.py` | `skill/tizen_gerrit_fetch` | - | OK |
| `parse_gerrit_query_output` | `tizen_gerrit_fetch/gerrit.py` | `skill/tizen_gerrit_fetch` | - | OK |
| `change_from_query_obj` | `tizen_gerrit_fetch/gerrit.py` | `skill/tizen_gerrit_fetch` | - | OK |
| `find_patchset_by_revision` | `tizen_gerrit_fetch/gerrit.py` | `skill/tizen_gerrit_fetch` | - | OK |
| `fetch_source_for_commit` | `tizen_gerrit_fetch/gerrit.py` | `skill/tizen_gerrit_fetch` | `runner.py` | OK |
| `_run_git` | `tizen_gerrit_fetch/gerrit.py` | `skill/tizen_gerrit_fetch` | - | OK |
| `_reset_generated_source_dir` | `tizen_gerrit_fetch/gerrit.py` | `skill/tizen_gerrit_fetch` | - | OK |
| `_optional_int` | `tizen_gerrit_fetch/gerrit.py` | `skill/tizen_gerrit_fetch` | - | OK |

**非权威 dry-run 原始输出(仅作测量证据,不得反向覆盖上表)**:

```
  GERRIT_HOST                  <- []  => OK
  GERRIT_PORT                  <- []  => OK
  SubprocessRunner             <- []  => OK  [同名 twin;runner.py:39 为独立同名顶层定义,twin-guard 正常生效,无 import-binding 歧义;不在 commit A' 加固范围内]
  GerritError                  <- []  => OK
  query_change_for_commit      <- []  => OK
  parse_gerrit_query_output    <- []  => OK
  change_from_query_obj        <- []  => OK
  find_patchset_by_revision    <- []  => OK
  fetch_source_for_commit      <- ['runner.py']  => OK
  _run_git                     <- []  => OK  [同名 twin,各自独立定义于 gerrit_submit.py:341, shared/workspace:205;**见 §1.3a:workspace.py 为 import-binding 消费,twin-guard 不生效,属 commit A' 加固对象**]
  _reset_generated_source_dir  <- []  => OK
  _optional_int                <- []  => OK

[SUMMARY] 12 OK / 0 MISMATCH  (owner=skill/tizen_gerrit_fetch)
[实测边界外消费(1 个符号):fetch_source_for_commit <- runner.py;
其余 11 个定义当前无边界外消费]
```

**两期取证边界**:

- **设计期(FROZEN 落章前)**:对本文件的 §0 首表执行 parser-only
  检查,必须输出本表每个 `(definition, symbol)` 键且列齐
  `symbol/definition/owner`;本证据只证明文档形态可解析,不证明与 SPECS
  一致。
- **实现期(commit C)**:代码与 SPECS 按 §0 全部行落地后,再把最终
  FROZEN 文件路径加入 `table_audit_bridge.py` 常量并跑完整 bridge。
  绿色输出中必须逐行出现 `tizen_gerrit_fetch/gerrit.py` 的键,不能只看
  SUMMARY 总绿;本证据才证明 body ↔ inventory 一致。
- **禁止提前注册**:设计阶段不得把规划行预写入 SPECS;代码尚未迁移时
  `symbol_audit` 必红,会破坏 commit 顺序。parser-only 绿与完整 bridge
  绿不得互相冒充。

**twin 辨明过程留痕**(⑩:raw-grep 初判 2 处 MISMATCH,经定义点核查
消解):`SubprocessRunner` 与 `_run_git` 的 raw-grep 命中来自**各自
独立定义的同名件**,非跨界消费——
- `SubprocessRunner`:gerrit.py:22 与 runner.py:39 各自定义同一形状
  类型别名(`Callable[..., CompletedProcess[str]]`),build_verify /
  campaign_repair_step 用的是各自模块内的;
- `_run_git`:**三处独立定义**——gerrit.py:227、gerrit_submit.py:341
  (签名不同,带 worktree/runner 参数)、shared/workspace:205;
  gerrit_submit 调用的是自身 :341,非 import gerrit。

结论:**skill owner 全合法,本批零判据变更**(由 dry-run 证明,非
检视得出)。

## §1 本批新形态(前两批未覆盖)

### 1.1 skill → shared/types 下行依赖(首次)

gerrit.py 无任何 ci_triage 内部 import,唯一外部依赖是
`tizen_ci_shared.types` 中 §1.2 明列的 Gerrit 类型(step-0 已下沉)。抽取后
形态为 **skill → shared 下行**,root-layers 已表达、合法。本批的
门禁价值:**首次实测"消费 shared 类型的 skill"在相关 root-layers /
forbidden / independence 契约下的表现**(前两批分别是"零外部
依赖"与"消费 shared HTTP 实现")。

### 1.2 gerrit.py 的双重身份:实现宿主 + step-0 shim 宿主

gerrit.py 现同时是:①§0 全部行的实现
宿主;②step-0 给三个 Gerrit 类型留的 **re-export shim 宿主**
(`from tizen_ci_shared.types import GerritChange/GerritPatchSet/
SourceFetchResult  # P4.9 shim`)。

**裁决:两个身份分离处理**——
- §0 全部实现行随 skill 走;
- **上述类型 import 两处并存,角色不同(v1.1 关键更正,CC①)**:
  - **skill 副本 `tizen_gerrit_fetch/gerrit.py` 必须自带上述 import**——
    它们是自身函数签名的真实依赖(`-> GerritChange` :37/:87、
    `-> GerritPatchSet` :100、`-> SourceFetchResult` :129/:203/:211),
    删则 NameError;这正是 §1.1 的 skill→shared/types 下行;
  - **旧址 `ci_triage/gerrit.py` 同样保留上述 import**,角色是 re-export
    shim(服务尚未翻转的旧 import);
  - **不是"搬或留"的互斥选择**;shim 的服务对象是"尚未翻转的旧 import 路径",跟着 skill 走
  即失去其存在意义,且会把 shared 类型的 re-export 挂到 skill 包上
  (制造 skill 作为类型二级来源的歧义);
- 故旧址 gerrit.py 抽取后**不是空 shim,而是“§1.2 类型 shim + §0
  inventory 全部实现符号的 re-export shim”**,零 def/class 不变
  (全部 import 行)。这是旧路径兼容面,不代表新 package root 公开相同
  表面;
- 这些类型 re-export 仍按 step-0 §6.2 在 P4.9 末统一删除,**本批不动其生命周期**。

### 1.3 同名 twin(二元组键实战首用)

`_run_git`×3(gerrit / gerrit_submit / shared-workspace)、
`SubprocessRunner`×2(gerrit / runner)。**沿 skill-2 裁决:严禁合并**,但两类理由不同(v1.1 更正,CC②a):
- `_run_git`×3:**签名确已分化**(gerrit `(command, runner)`、
  gerrit_submit `(worktree, args, runner, *, check)`、workspace
  `(args)->None`),合并即语义变更;
- `SubprocessRunner`×2:**逐字节相同**(两处均为
  `Callable[..., subprocess.CompletedProcess[str]]`)——理由沿
  **skill-2 `_normalize_text` 先例**:字节相同但合并会制造跨模块
  耦合点,且属可延期的语义中性去重,非本批范围。

**注册面(v1.2 更正,Kimi NIT-4)**:SPECS 当前通过 **module-scope**
覆盖 `tizen_ci_shared/workspace` 的 `_run_git`(非显式逐符号行);本批新增 `gerrit._run_git` **逐符号行**,合为**两份可解析定义**(shared module-scope + skill 逐符号),
`gerrit_submit._run_git` **不在册**(属未来 submit skill 批次)。故:
- 二元组键的**首个真实生产符号用例**由这**两份**触发(此前均为构造
  fixture)——里程碑成立;
- **未合并**由 `grep -c "^def _run_git"` **= 3** 证明(三处物理定义在);
- DoD 贴**两行** SPECS 输出,不是三行。

### 1.3a [MAJOR,v1.1 新增] `_run_git` 消费方歧义与工具加固

**实锤**:`ci_triage/verify/workspace.py:25` 以
`from tizen_ci_shared.workspace import _run_git as _run_git` 引入并在
:66/:67 调用,**该文件自身零顶层 `_run_git` 定义** → `symbol_audit`
的 twin-guard(@746,只跳过"自身顶层定义同名"的文件)**不生效**;
抽取后 `tizen_gerrit_fetch/gerrit.py:_run_git` 会把 workspace.py 误
算为 undeclared consumer,审计必红。v1.0 §0 的"twin-guard 自动排除"
标注**失实,已更正**。

**裁决:采推荐方案——`_actual_consumers` 增加 import-binding 追踪**
(而非把 workspace 声明为 gerrit `_run_git` 的消费方,后者只是"让审计
变绿",语义上 workspace 用的是 shared 那份):
- 只处理 **module-scope `ImportFrom`** 节点;
- `alias.name` 是**来源符号名**,用于与被审计符号比对;
  `alias.asname or alias.name` 是**本地引用名**,`_ReferenceVisitor` 必须
  追踪该本地名;
- 文件内对本地引用名的加载归属到“来源模块 + 来源符号”的定义,不计入
  其它同名符号的消费方;
- **性质**:与 skill-2 的二元组键同类,属**消费方解析精化**,非判据
  变更(§0"零判据变更"仍成立,Kimi NIT-4);
- **断言(⑮,必配;四组)**:
  - **a 回归锁定**:加固后既有全部判定逐条不翻转
    (`verdict_changes=0`),且真实生产形态 `campaign_state.py` 的本地
    `_primary_fingerprint` 引用必须归属到
    `tizen_convergence_judge.convergence.primary_fingerprint` 来源符号,
    不得误归到 skill-1 内同名 `_primary_fingerprint`;
  - **b 异名 fixture(存在性证明)**:构造文件
    `from A import S as LocalS`(`LocalS != S`)且该文件自身零顶层定义 S
    (否则 twin-guard 先跳过),同时存在 B 模块的同名 S;断言 A.S 的
    消费方**含**该文件、B.S 的消费方**不含**该文件,包含/排除双向
    断言合为一组,并证明旧实现下必红;
  - **c 同名 fixture**:独立测试 `from A import S as S`,覆盖本批
    `_run_git as _run_git` 退化形态;该 fixture **不作为“含 as”泛化
    能力的证据**;
  - **d 本批真实用例**:加固后
    `tizen_gerrit_fetch.gerrit._run_git` 消费方为空、
    `tizen_ci_shared.workspace._run_git` 消费方含
    `ci_triage.verify.workspace`。

**known-limitation(Kimi NIT-3,写进工具源码注释)**:本次加固只解析
`from X import S`(含 `as`)绑定;**`import X` + `X.S` 属性访问形式
不在覆盖内**(对本批无影响,gerrit/workspace 均为 from-import),后续
维护者勿误以为所有 attribute access 均被解析。

**执行位置**:新增 **commit A'**(工具加固),排在 commit A(环境测试)
之后、commit B(抽取)之前——抽取前工具必须先能正确解析。A' 只处理
import-binding 形态;`SubprocessRunner` 的 runner.py 同名件是独立顶层
定义,twin-guard 已正常生效,不在 A' 范围。其不合并理由仍是 §1.3 的
skill-2 `_normalize_text` 先例,不得与 import-binding 加固混写。

## §2 skill 物理形态与迁移

```
tizen-gerrit-fetch/
  SKILL.md
  scripts/tizen_gerrit_fetch/
    __init__.py   # 薄导出:§2.1 全部公开符号
    gerrit.py     # §0 全部实现行(现文件约 250 行,逐行搬移/cmp)
```

- §0 全部行逐符号注册(纯逐符号,不用 module-scope;三列
  `symbol | definition | owner`,definition 一律
  `tizen_gerrit_fetch/gerrit.py`);
- 旧址处理见 §1.2;INCOMPLETE 护栏覆盖 skill 包 gerrit.py 公共面;
- **交付面入口同步(commit C)**:
  - `pyproject.toml` 的 package discovery 与 mypy 配置分别增加
    `tizen-gerrit-fetch/scripts` / `tizen_gerrit_fetch`;
  - `.github/workflows/ci.yml` 的 Type check 显式清单增加
    `mypy tizen-gerrit-fetch/scripts/tizen_gerrit_fetch`;
  - `README.md` 的开发 `PYTHONPATH` 显式清单增加
    `$PWD/tizen-gerrit-fetch/scripts`;
  C21 glob 会自动纳入,但以上入口均为显式枚举,不得以 glob 已覆盖为由
  漏改任一入口;
- `release-v1.4.0/` 是历史发布快照,本批明确不回填;下一次发布统一纳入
  `tizen-gerrit-fetch`,DoD 须留边界声明,区分“故意不动”与“遗漏”。

### 2.1 公开契约(SKILL.md 机器侧)

下表只描述 SKILL.md / package-root 的公开契约,**不是归属表**;
definition / owner / measured consumers 的唯一权威仍是 §0。

**包根公开契约(4 个符号)**:

| symbol | 契约 |
|---|---|
| `fetch_source_for_commit` | 核心:按 commit 取源;当前消费测量见 §0 |
| `GerritError` | 错误类型 |
| `GERRIT_HOST` | Gerrit 主机常量 |
| `GERRIT_PORT` | Gerrit 端口常量 |

**包根不导出的实现符号(8 个)**:`SubprocessRunner`、
`query_change_for_commit`、`parse_gerrit_query_output`、
`change_from_query_obj`、`find_patchset_by_revision`、`_run_git`、
`_reset_generated_source_dir`、`_optional_int`。这里的“不导出”是 package
root API 裁决,不以 Python 下划线命名或当前消费方数量推断。

旧址 `ci_triage.gerrit` 为兼容历史 import re-export §0 inventory 全部
实现面;新包根只导出本节公开契约。两处 re-export 面故意不同:旧址
优先保证迁移期兼容,新包根建立收窄且稳定的正式 API。

### 2.2 SKILL.md 行为契约(架构评审-3,零行为变更)

SKILL.md 必须有以下五节,逐项暴露现有实现,不得把返回与抛出混写:

#### Inputs

- `project`、`commit_hash`、`destination`,以及可选
  `subprocess_runner` / `git_ssh_command`;
- `destination` 是**破坏性输入**,必须是本工具拥有的生成目录。调用会
  删除并重建该路径,严禁传入含用户数据的普通工作目录。

#### Outputs

`fetch_source_for_commit` 有三个返回分支:

1. 成功返回 `SourceFetchResult(status="source_available")`;
2. `git init` / remote / fetch / checkout 的
   `subprocess.CalledProcessError` 返回
   `SourceFetchResult(status="FAILED_SOURCE")`;
3. try 内的 `GerritError` 返回 `SourceFetchResult(status=exc.code)`,当前
   生产路径为 `PATCHSET_REVISION_NOT_FOUND`。它不是第二个字面量
   `FAILED_SOURCE`。

#### Errors

- `query_change_for_commit` 在 fetch try 块之前执行,其
  `GERRIT_QUERY_FAILED` / `GERRIT_CHANGE_NOT_FOUND` /
  `GERRIT_CHANGE_AMBIGUOUS` 以 `GerritError` **抛出**,不包装成返回值;
- `_reset_generated_source_dir` 对“存在且可解析”的 symlink 抛
  `GerritError(code="SOURCE_DIR_UNSAFE")`;
- **不存在 catch-all**:查询函数只把 query runner 的
  `subprocess.CalledProcessError` 转成 `GerritError`;解析和 change 转换
  抛出的其它异常原样传播。`_reset_generated_source_dir` 与
  `destination.mkdir` 位于 fetch try 块之外;除前述显式 symlink
  `GerritError` 外,其文件系统异常原样传播。git try 块只把
  `subprocess.CalledProcessError` 与 `GerritError` 转成
  `SourceFetchResult`;runner 抛出的其它异常原样传播。调用方不可只检查
  返回值,还必须处理这些抛出路径;
- 实现不设置 timeout 或 cancellation;SSH 查询与全部 git 调用都可能
  无限阻塞。调用方可通过自定义 `subprocess_runner` 施加 deadline;
  `subprocess.TimeoutExpired` 当前不归一化,会继续向上传播——不转换成
  `GerritError`,也不返回 `FAILED_SOURCE`,调用方须自行 catch;
- **悬空 symlink 边界(实测)**:`path.exists()` 为 false,故不会触发
  `SOURCE_DIR_UNSAFE`,也不会进入删除分支;随后的
  `destination.mkdir(..., exist_ok=True)` 抛 `FileExistsError`,目标不被
  清理、fetch 不继续。本批按行为等价铁律只记录、不修复。

#### Side effects

- Gerrit 查询成功后,调用删除并重建 `destination`;
- git 阶段失败时可能留下部分初始化目录,例如 git init 已成功但 fetch
  失败的中间态;调用方必须把它当失败残留而非可用源码树。
- 超时或外部终止时,`destination` 可能停在任意已完成阶段的残留状态;
  该边界与上述 git 失败残留同源,此处明确覆盖调用被中断的情形。

**性能成本契约(封闭拓扑,不新增机制)**:

1. 每次调用先尝试一次 SSH Gerrit query;查询成功后,对已有
   `destination` 同步扫描并删除,再执行 git 阶段。
2. git 网络 fetch 的业务分支穷举如下:NEW 且有匹配 patchset = 一次
   `--depth 1` ref fetch;NEW 但无匹配 patchset = 零次 fetch;非 NEW
   直接成功 = 一次 `--depth 1` commit fetch;非 NEW 首次 fetch 失败且
   有 branch = 一次失败的 `--depth 1` commit fetch + 一次
   `--depth 50` branch fetch;非 NEW 首次 fetch 失败且无 branch = 仅一次
   失败的 `--depth 1` commit fetch。任一终止性 git 异常会截断后续步骤,
   不产生额外重试。
3. 目录清理由同步 `shutil.rmtree` 遍历完成,耗时随目录项数量和文件系统
   性能增长;大型生成目录下该成本非平凡。全部 query、清理与 git 步骤
   串行执行,无并行、无进度回调,调用方不能观测中间进度。
4. 本批不设置墙钟性能阈值:fake runner 不代表 Gerrit、网络或目标文件
   系统性能,任何由其产生的墙钟数字都不是有效门禁。§5.2 的同一份
   有序命令轨迹只验收迁移前后的拓扑、次数、顺序与 `depth` 参数不变;
   不增加真实 Gerrit 基准,也不登记缓存/并发类优化 DEFERRED。未来只有
   在真实容量测量证明问题后,才由测量数据驱动另案设计。

#### Idempotency

该操作**非幂等**:每次调用都会重建目标目录,且结果依赖远端 Gerrit
状态。对同一工具自有目录重复调用是允许的,但每次都具有破坏性。

## §3 门禁

1. **root-layers 增列第三个 skill**(无花括号):
   `ci_triage > tizen_convergence_judge | tizen_qb_discover | tizen_gerrit_fetch > tizen_ci_shared`;
2. **skill-independence 扩为三成员**;
3. **forbidden 扩列**:shared 不得 import `tizen_gerrit_fetch`;
4. **负控制(三条)**:每条均须记录 `exit 1` 与报错原文入 dev_memory:
   ①skill 内临时 `import ci_triage` → root-layers 红;
   ②skill 内临时 `import tizen_qb_discover` → skill-independence 红
   (三成员后的首次实测);
   ③shared 内临时 `import tizen_gerrit_fetch` → forbidden 红。
5. **正向证据**:六契约全部绿;其中 skill →
   `tizen_ci_shared.types` 的下行 import 新形态(§1.1)须单列报告,不得
   只报总数。该正向绿本身不可证伪,必须与第 4 项负控制③配对,以
   “skill 可向下依赖 shared / shared 不可反向依赖 skill”的双向实测
   共同证明边界生效。

## §4 顺带项:两个环境敏感测试(skill-2 DEFERRED 关门)

skill-2 登记的两项(`test_build_runner.py::test_python_module_invocation_runs_fake_gbs`、
`test_workflow.py::test_workflow_werror_patch_ready_context_suppresses_generic_fallback`)
在 Claude 干净环境稳定失败、目标机绿。本批**独立 commit A** 处置:
- 诊断根因(疑为子进程/外部 GBS 依赖的环境假设,与 C21 同族但未被
  glob 修复覆盖);
- 修法优先级:①使其环境无关(同 C21 glob 派生思路);②若确需外部
  依赖,改为 `pytest.mark.skipif` 明确声明前置条件(**不得直接删除
  或无条件 skip**);
- **验收信号(v1.1 加牙,CC④)**:首选 `847 passed`;**仅当 ① 被证明
  不可行且不可行原因入档时**,方允许 ②(`845 passed + 2 skipped`,
  skip 原因可读)——**二者非等价通过**,降级须留证(本项目一贯标准);
- **diff 范围硬限**(Kimi NIT-3):仅
  `tests/unit/test_build_runner.py` 与 `tests/unit/test_workflow.py`,
  零生产改动;
- **基线漂移点明(CC④)**:commit A 建立 **Claude 干净环境 847 基线**;
  B/C 的"原样全绿"以此为基线,目标机 847 恒真——两者不得混写。

## §4a 机械同步清单(Kimi NIT-1/5,commit C 先做)

1. **shared/types Gerrit 类型的 declared consumers 更新**(必做,
   漏则审计红):`GerritPatchSet`/`GerritChange`:`ci_triage.gerrit` →
   `tizen_gerrit_fetch.gerrit`;`SourceFetchResult`:
   `ci_triage.gerrit, ci_triage.report` →
   `ci_triage.report, tizen_gerrit_fetch.gerrit`(旧址 shim 的
   `from ... import` 不被 `_ReferenceVisitor` 计入消费方);
2. `REGISTERED_SKILL_ROOTS` / `ROOT_LAYERS_HIGH_TO_LOW` / `.importlinter`
   root-packages 加 `tizen_gerrit_fetch`;
3. **旧址 re-export 范围(NIT-5)**:保留 §0 全部实现行 re-export
   ——理由:行为等价优先,旧 import 路径一律不破(实际外部在用的仅
   `fetch_source_for_commit`/`find_patchset_by_revision`/
   `GerritChange`,但收窄属语义变更,留 P4.9 末 shim 清理批统一处置);
   本条理由须写入 DoD 说明。
4. **交付面入口(架构评审-1)**:按 §2 的完整入口清单同步
   `pyproject.toml`(安装/package discovery + mypy)、
   `.github/workflows/ci.yml`(CI Type check)与 `README.md`(源码运行
   `PYTHONPATH`);这些入口都是显式枚举,漏一处即静默失效。执行归 commit C;
   `release-v1.4.0/` 按历史快照裁决只读,下一次发布再统一纳入。

## §5 审计与 parity

- SPECS/bridge:§0 全部行入册;**二元组键实测**严格采用 §1.3 的
  注册面、物理定义计数和 grep 阈值,逐项输出各自消费集——DoD 硬项;
- 双道全绿(symbol 侧以当前基线 + §0 全部行为预期,精确总数以实跑为准);
- **pre-shim 行为 parity(真正迁移证据)**:commit B 中先落新副本,旧址
  尚未改成 shim 时,两份独立实现用同一 fixture、各自独立的临时
  destination 双跑 `fetch_source_for_commit`(既有 fake subprocess
  runner,不打真实 Gerrit);按 §5.2 的封闭 schema 与唯一掩码生成
  canonical payload,先逐字段断言相等,再记录两份 SHA。同时 `cmp` 两份
  源码逐字节一致。`cmp` 证“没有改字”,双跑证“新模块加载上下文下
  行为未漂移”,两者互不替代;
- **post-shim identity(只证接线)**:旧址换成 shim 后,断言 §0 全部实现
  符号 + §1.2 明列的 shared 类型逐项 `old.X is new.X`;此证据只说明 shim
  指向正确对象,不得再称为行为 parity,也不得替代 pre-shim 双跑;

### 5.1 `fetch_source_for_commit` 分支覆盖表

本表不是笛卡尔积;每个不同的返回、抛出或破坏性边界至少有一个
fake-runner fixture。原先单列的固化测试并入本表,不另作平行计数。

| 分支 | 期望(仅固化现状) |
|---|---|
| 查询命令失败 | 抛 `GerritError(GERRIT_QUERY_FAILED)`;destination 不动 |
| 零 change | 抛 `GerritError(GERRIT_CHANGE_NOT_FOUND)`;destination 不动 |
| 多 change | 抛 `GerritError(GERRIT_CHANGE_AMBIGUOUS)`;destination 不动 |
| 畸形 JSON | 原样抛 `json.JSONDecodeError`;destination 不动 |
| query 阶段 `TimeoutExpired` | 原样向上传播,不转 `GerritError`、不返回 `FAILED_SOURCE`;destination 不动 |
| NEW + 有匹配 patchset | fetch 匹配 ref 并 checkout `FETCH_HEAD`;返回 `source_available` |
| NEW + 无匹配 patchset | 返回 `PATCHSET_REVISION_NOT_FOUND`;已初始化的部分目录可观测 |
| 非 NEW + commit fetch 成功 | checkout commit;返回 `source_available` |
| 非 NEW + fetch 失败 + 有 branch | 以 depth 50 fetch branch 后 checkout commit;返回 `source_available` |
| 非 NEW + fetch 失败 + 无 branch | 返回 `FAILED_SOURCE`;部分目录可观测 |
| destination 不存在 | 创建为目录 |
| destination 已有目录 | 原内容删除并重建 |
| destination 已有普通文件 | 文件删除并重建为目录 |
| destination 为有效 symlink | 抛 `GerritError(SOURCE_DIR_UNSAFE)`;链接及目标不动 |
| destination 为悬空 symlink | 不触发 `SOURCE_DIR_UNSAFE`、不清理链接;`mkdir(..., exist_ok=True)` 抛 `FileExistsError`,git 不执行 |
| 提供 `git_ssh_command` | 每条 git 调用的 env 均含正确 `GIT_SSH_COMMAND` |
| 各终止性 `_run_git` 失败点 | init、remote add、NEW fetch/checkout、branch fallback fetch、非 NEW checkout 的 `CalledProcessError` 返回 `FAILED_SOURCE`;按失败点断言 destination 与 fake `.git`/阶段标记残留。非 NEW 首次 commit fetch 失败且有 branch 属上方 fallback 分支,不是终止性失败 |
| git 阶段 `TimeoutExpired` / 受控中断 | 在 init 后、fetch 中、checkout 前选取代表阶段参数化注入;异常原样向上传播,并断言各阶段已完成操作的 destination 残留;不做全量笛卡尔积 |
| `rmtree` / `unlink` / `mkdir` 抛 `OSError` | 参数化注入并原样向上传播;逐项断言部分删除、原文件保留或目录未创建的现状 |
| 全部 subprocess 调用 | fake runner 断言 kwargs 中不存在 `timeout`;发现任一实际 timeout 即停止并重裁契约,不得删断言迁就 |

**测试纪律**:

1. 全部测试只固化现状;任一分支实测与表中预期不符,必须停止报告并
   更正对现行为的理解,不得修改生产代码迁就测试。
2. 使用参数化测试与共用 fake subprocess runner,不访问真实 Gerrit;
   所有 destination 都来自 `tmp_path`,不得触碰其外路径。fake runner
   可在 `tmp_path` 内模拟 git init、remote add、fetch、checkout 的
   阶段性磁盘痕迹。
3. 所有破坏性分支必须断言磁盘状态(路径类型、是否重建、原内容是否
   删除、失败残留),不得只断言返回值或异常。

**冻结期唯一契约/分支/用例对照表**:下表是 closeout
“用例名 ↔ 契约分支”与 SKILL.md Errors / Side effects 运行时承诺的唯一
映射源。方括号是参数化 case id,不是另一个用例名。实现时用例名必须与
本表一致;任一 §2.2 运行时契约句无分支、任一 §5.1 分支无用例或任一
用例无反向契约锚,冻结门均为红。

| §2.2 契约句 | §5.1 分支 | 用例名 |
|---|---|---|
| Errors:查询 `CalledProcessError` 转 `GERRIT_QUERY_FAILED`;删除发生在查询之后 | 查询命令失败 | `test_fetch_source_query_outcomes_preserve_destination[command-failed]` |
| Errors:查询零结果抛 `GERRIT_CHANGE_NOT_FOUND`;删除发生在查询之后 | 零 change | `test_fetch_source_query_outcomes_preserve_destination[not-found]` |
| Errors:查询多结果抛 `GERRIT_CHANGE_AMBIGUOUS`;删除发生在查询之后 | 多 change | `test_fetch_source_query_outcomes_preserve_destination[ambiguous]` |
| Errors:JSON 异常不归一化;删除发生在查询之后 | 畸形 JSON | `test_fetch_source_query_outcomes_preserve_destination[malformed-json]` |
| Errors:`TimeoutExpired` 不归一化;删除发生在查询之后 | query 阶段 `TimeoutExpired` | `test_fetch_source_query_outcomes_preserve_destination[timeout]` |
| Outputs/成本拓扑:NEW 匹配 patchset 成功并执行浅 fetch | NEW + 有匹配 patchset | `test_fetch_source_for_new_change_fetches_matching_patchset_ref` |
| Outputs:try 内 `GerritError` 以 code 返回;失败残留可观测 | NEW + 无匹配 patchset | `test_fetch_source_new_without_matching_patchset_returns_code` |
| Outputs/成本拓扑:非 NEW 一次浅 fetch 成功 | 非 NEW + commit fetch 成功 | `test_fetch_source_non_new_paths[direct-fetch]` |
| Outputs/成本拓扑:非 NEW 首次失败后按 branch fallback | 非 NEW + fetch 失败 + 有 branch | `test_fetch_source_non_new_paths[branch-fallback]` |
| Outputs:git `CalledProcessError` 返回 `FAILED_SOURCE`;失败残留可观测 | 非 NEW + fetch 失败 + 无 branch | `test_fetch_source_non_new_paths[failed-without-branch]` |
| Inputs/Side effects/Idempotency:每次调用重建工具自有 destination | destination 不存在 | `test_fetch_source_rebuilds_destination[missing]` |
| Inputs/Side effects/Idempotency:已有内容被同步删除并重建 | destination 已有目录 | `test_fetch_source_rebuilds_destination[directory]` |
| Inputs/Side effects/Idempotency:已有普通文件被删除并重建 | destination 已有普通文件 | `test_fetch_source_rebuilds_destination[file]` |
| Errors:存在且可解析的 symlink 抛 `SOURCE_DIR_UNSAFE` | destination 为有效 symlink | `test_fetch_source_rejects_live_symlink` |
| Errors:悬空 symlink 不拒绝、不清理,随后 `FileExistsError` | destination 为悬空 symlink | `test_fetch_source_dangling_symlink_propagates_file_exists_error` |
| Inputs/Side effects:`git_ssh_command` 进入每条 git 调用环境 | 提供 `git_ssh_command` | `test_fetch_source_sets_git_ssh_command_on_all_git_calls` |
| Outputs/Side effects:各终止性 git 失败返回 `FAILED_SOURCE` 并留阶段残留 | 各终止性 `_run_git` 失败点 | `test_fetch_source_git_failures_leave_observable_state[fail-point]` |
| Errors/Side effects:`TimeoutExpired` 或受控中断原样传播并留阶段残留 | git 阶段 `TimeoutExpired` / 受控中断 | `test_fetch_source_git_interruption_propagates_and_leaves_state[interrupt-point]` |
| Errors/Side effects:文件系统异常不归一化且磁盘状态可观测 | `rmtree` / `unlink` / `mkdir` 抛 `OSError` | `test_fetch_source_filesystem_errors_propagate[operation]` |
| Errors/性能成本:实现不设置 timeout,调用可能无界阻塞 | 全部 subprocess 调用 | `test_fetch_source_subprocess_calls_have_no_timeout` |

§2.2 中“无真实 Gerrit 基准、无 fake-runner 墙钟阈值、优化由未来真实
测量驱动”是测试政策与范围裁决,不是运行时分支,由 §5.2 命令轨迹和
closeout 命令审计验收,不得伪造一个墙钟用例塞入本表。

### 5.2 pre-shim parity canonical payload

payload 只含以下五项,清单封闭,不得增加“等”或运行时任意忽略字段:

1. **`SourceFetchResult` 全字段**:`status`、`src_root`、`remote_url`、
   `change`、`error`;
2. **嵌套 Gerrit 类型全字段**:`GerritChange(project, branch, status,
   number, subject, url, matching_patchset)` 与
   `GerritPatchSet(number, revision, ref)`;
3. **fake runner 有序调用轨迹**:每次调用记录完整 `argv`、`check`、
   `capture_output`、`text`,保持发生顺序;迁移前后同时验收调用次数、
   发生顺序及每次调用的完整 `argv` 逐元素相等,并从 `argv` 明确验收
   fetch 次数及 `--depth 1/50`,证明抽取没有新增网络往返。该项
   是 pre-shim parity 的组成部分及评审 4 裁决的取证点,同时是 §2.2
   Side effects 成本拓扑的唯一性能等价证据,不另建性能机制或平行流程;
4. **受控环境输入**:只记录具名字段 `GIT_SSH_COMMAND`(值或 null)。继承
   自 `os.environ.copy()` 的其它环境不进入 payload;
5. **destination 状态**:按相对路径字典序记录文件树条目
   `(relative_path, kind, content_sha256_or_symlink_target)`,并记录 fake
   runner 的有序阶段标记;目录的第三列为 null。

**唯一允许的掩码**:两次运行使用独立 destination,规范化时只允许把
各自 destination 的绝对路径前缀替换为字面量 `<DEST>`。不得删除或
掩盖 `status`、`remote_url`、`change`、`error`、命令顺序、非路径命令
参数或上述其它字段。

**两层比较**:

1. 路径替换后的 canonical payload 直接逐字段相等,作为主证据;
2. 对纯 JSON payload 执行
   `json.dumps(..., sort_keys=True, ensure_ascii=False, separators=(",", ":"))`
   并按 UTF-8 计算 SHA-256;SHA 只作记录锚,不得替代逐字段比较。

**normalizer 反向测试(存在性证明)**:基于同一 canonical payload 分别
只改 `error`、交换两条命令的顺序、只改 `status`,三类样本均必须触发
parity 失败。每类测试须记录“变异 payload 比较不等/断言失败”的证据
及对应 pytest 命令 `exit 0`;没有必红样本的 normalizer 不算验证机制。

### 5.3 测试所有权与三类边界

1. **skill 行为测试**:`tests/unit/test_gerrit_fetch.py` 直接 import
   `tizen_gerrit_fetch`,独占 §5.1 分支表、共用 fake runner、磁盘状态
   断言、§5.2 parity normalizer 及反向测试。现有
   `test_find_patchset_by_revision_uses_matching_revision_not_current` 与
   `test_fetch_source_for_new_change_fetches_matching_patchset_ref` 从
   `test_ci_triage.py` 整体迁入;除 import 翻转与必要的 monkeypatch
   目标字符串外,fixture 和断言内容逐字不改,以移动 diff 证据自证。
   本类另含 §2.1 package-root 公开契约测试:公开面逐项与
   `tizen_gerrit_fetch.gerrit` 中同名对象做 identity 断言,不导出面
   逐项做 `not hasattr(tizen_gerrit_fetch, name)` 反向断言;
2. **编排集成测试**:`tests/unit/test_ci_triage.py` 只保留 runner 如何
   调用 fetch 并消费 `SourceFetchResult` 的串联验证,不再承载 skill
   内部分支行为测试。
3. **legacy-path wiring / shim identity**:以独立分节、测试类或
   `test_legacy_path_wiring_*` 前缀显式标注,只证明旧 import 路径接线
   正确;不得计入 skill 行为覆盖或称为 parity 证据。

closeout 直接引用 §5.1 唯一对照表,全部用例落在
`tests/unit/test_gerrit_fetch.py`,不得跨文件拼接或另抄一份映射。定向
测试与全量回归分别取证,前者不替代后者。

**⑧ 基数维度**:本 skill 的有效维度由本表按分支覆盖,不做查询结果、
change 状态、fallback 与 destination 状态的全量笛卡尔积;arch 维度
grep 实测(证据入档,有据豁免)。

## §6 commit 划分(每 commit 全量 + lint 双绿)

- **A(环境测试修复)**:§4 全部环境用例,零生产改动,先行;
- **A'(工具加固)**:§1.3a 的 `_actual_consumers` import-binding 追踪
  + §1.3a 全部断言组,**先于抽取**:
  - **a 回归锁定**:`verdict_changes=0`,并锁定 `campaign_state.py` 的
    本地 `_primary_fingerprint` → 来源符号
    `tizen_convergence_judge.convergence.primary_fingerprint`;
  - **b 异名 fixture**:`from A import S as LocalS`(`LocalS != S`),
    A.S 包含 / B.S 排除合为一组,且旧实现下必红;
  - **c 同名 fixture**:`from A import S as S` 独立存在,只覆盖退化
    情形,**不作为“含 as”泛化能力的证据**;
  - **d 本批真实用例**:gerrit `_run_git` 消费方空 / workspace
    `_run_git` 消费方含 `ci_triage.verify.workspace`;
- **B(抽取主体,顺序硬约束)**:①建 skill 包 + §0 全部实现行副本;②在旧址仍为
  独立实现时完成源码 `cmp` 与 pre-shim 行为 parity并记录 SHA;③仅在
  前两项绿后才把旧址改为双 shim(§1.2),完成 §0 全部实现行 + §1.2
  类型的 post-shim identity;④消费方翻转(runner.py 及测试);⑤实现
  §5.1 分支覆盖表的全部参数化行为测试,共用 fake runner、destination
  仅用 `tmp_path`,并对破坏性分支断言磁盘状态。任一预期与现行为不符
  必须停止报告,不得改生产代码迁就测试;其中必须覆盖 query
  `TimeoutExpired`、git 阶段 `TimeoutExpired` / 受控中断、
  `rmtree` / `unlink` / `mkdir` 的 `OSError` 以及所有 subprocess 调用
  不含 `timeout` kwarg 的全部现状锁;⑥按 §5.2 实现封闭 canonical
  payload、唯一 destination 路径掩码、逐字段比较 + SHA 记录,并完成
  §5.2 全部 normalizer 反向测试;⑦按 §5.3 新建
  `tests/unit/test_gerrit_fetch.py`,整体迁入 §5.3 指定的既有 Gerrit 用例并
  落下全部 skill 行为测试;`test_ci_triage.py` 只保留 runner 编排串联,
  legacy-path wiring / shim identity 单独标注且不混算;⑧为 §2.1 包根
  公开/不导出两面分别实现 identity 正向与 `not hasattr` 反向测试,
  归入 skill 公开契约子集。**本 commit 的验证
  脚手架**:显式把 `$PWD/tizen-gerrit-fetch/scripts` 追加到临时
  `PYTHONPATH` 与 `MYPYPATH`,再跑全量 pytest、mypy、ruff 与现有
  import-linter;报告必须列出实际环境变量与命令,不得隐式继承 shell
  环境。临时路径只保证本 commit 的门禁可执行,**不构成交付面**;
- **C(门禁与审计)**:§3 全部门禁扩列、负控制和正向验证 + §0 全部行入
  SPECS + bridge + twin 实测 + SKILL.md + arch 豁免 + §2/§4a 第 4 项
  交付面入口同步。更新
  同时把最终 FROZEN 设计路径接入 bridge 常量;完整 bridge 输出必须出现
  skill-3 的 `(definition, symbol)` 行。更新 `pyproject.toml` / CI /
  README 后,先执行
  `.venv/bin/python -m pip install -e .` 刷新 editable package mapping;
  随后显式清除临时 `PYTHONPATH`/`MYPYPATH`(例如以
  `env -u PYTHONPATH -u MYPYPATH` 启动各命令),无脚手架重跑 pytest、
  mypy、ruff、`lint-imports` 与双道审计。此阶段证明正式安装入口生效,
  不得用 B 阶段结果替代。

**两阶段取证**:dev_memory 与 closeout 必须分列“B 阶段:显式临时路径
下绿”和“C 阶段:editable 重装后、无临时路径下绿”的完整命令与结果;
前者只证代码本身可用,后者才证用户/CI 的正式发现路径可用,二者不可
互相替代。

## §7 DoD

**冻结落章检查(设计期,与实现 DoD 分离)**:

- 附录逐句与正文当前裁决面对账;
- 全文所有计数类表述与各自定义节对账,非定义章节只引用定义节;
- SKILL.md 契约句与 §5.1 用例完成双向对照;
- 本轮评审收口后,以本次单独 commit 完成 FROZEN 定版;标题与状态均为
  `FROZEN`。

- [ ] 全量 == 847/1(目标机,恒真);**Claude 干净环境:commit A 后
      847 passed**(首选)**或 845+2 明确 skip 且不可行原因入档**;
      B/C 以 A 后的 847 为干净环境基线(基线漂移已点明);
- [ ] **B 阶段验证脚手架证据**:报告显式列出追加
      `$PWD/tizen-gerrit-fetch/scripts` 的临时 `PYTHONPATH`/`MYPYPATH`
      及 pytest、mypy、ruff、现有 import-linter 的完整命令与绿色结果;
      明写该路径不构成交付、不能替代 commit C 的 §2 入口同步;
- [ ] **C 阶段正式交付入口证据**:§2 全部入口更新后先执行
      `.venv/bin/python -m pip install -e .`,再显式清除全部临时
      `PYTHONPATH`/`MYPYPATH`,无脚手架重跑 pytest、mypy、ruff、
      `lint-imports` 与双道审计并全部绿;closeout 与 B 阶段分列;
- [ ] 旧址 gerrit.py 零 def/class,**§1.2 类型 shim 在**,**§0 全部实现行
      re-export 全在**(§1.2/§4a 第 3 项,理由入档);
- [ ] **skill 副本自带 §1.2 类型 import**(签名依赖,grep 自证);
- [ ] **SKILL.md 的 §2.2 全部行为契约节齐全**:Inputs / Outputs / Errors / Side effects /
      Idempotency 明写破坏性 destination、返回与抛出分界、失败残留和
      非幂等语义;Errors 明写无 timeout/cancellation、可由自定义
      `subprocess_runner` 施加 deadline,以及 `TimeoutExpired` 原样传播
      (不转 `GerritError`/`FAILED_SOURCE`,调用方自行 catch);Side effects
      明写超时或外部终止可留下任意已完成阶段的 destination 残留,并
      穷举 SSH query、destination 同步清理、各 git fetch 分支的调用
      拓扑;声明 `rmtree` 成本随目录规模/文件系统性能增长、全链串行、
      无进度回调且不设 fake-runner 墙钟阈值;
- [ ] **§0/§2.1 概念分离**:消费测量只陈述哪些 inventory 定义有或
      无边界外消费;package root 的公开/不导出面只由 §2.1 裁决;旧址
      shim 的完整兼容 re-export 不得反向扩大新包根 API;
- [ ] **package-root 公开契约正反测试**:§2.1 公开面逐项与
      `tizen_gerrit_fetch.gerrit` 同名对象 identity 相同,不导出面逐项
      `not hasattr`;本项归 skill 公开契约测试,与 legacy shim identity
      分列;
- [ ] **SKILL.md/API 双向对照**:SKILL.md 承诺的每个机器侧符号均存在于
      §2.1 package-root 公开面,package-root 每个公开符号亦在 SKILL.md
      有对应承诺;任一方向缺项即红;
- [ ] **§5.1 分支覆盖表全部绿**:每行至少有一个 fake-runner 用例,
      closeout 直接贴 §5.1 唯一对照表,不得重建平行映射;原先单列的
      固化测试并入该表,不重复计数。破坏性分支均断言磁盘状态,destination 仅用
      `tmp_path`;任何预期不符均停下复核,不作语义修复;
- [ ] **异常传播新增分支**:§5.1 对照表中的 query `TimeoutExpired`、
      git `TimeoutExpired` / 受控中断、文件系统 `OSError` 均有参数化
      用例,逐项断言抛出边界与 destination 磁盘状态;
- [ ] **无界阻塞回归锁**:`test_fetch_source_subprocess_calls_have_no_timeout`
      断言 query 与全部 git subprocess 调用均未传 `timeout`;若现状不符
      则停止并重裁 §2.2 契约,不得删除断言迁就;
- [ ] **§5.3 测试所有权闭合**:新建 `tests/unit/test_gerrit_fetch.py`,
      §5.3 指定的既有 Gerrit 用例整体迁入且除 import/monkeypatch 目标外内容
      不变;skill 行为、runner 编排、legacy wiring/shim identity 各类
      测试显式分界,后者不混算为行为或 parity 证据;
- [ ] **定向/全量两层结果**:单列
      `pytest tests/unit/test_gerrit_fetch.py` 绿色结果,随后单列全量 pytest
      绿色结果;定向绿不得替代全量回归;
- [ ] **契约/测试双向对照**:SKILL.md Errors / Side effects 的每句承诺
      均在 §5.1 唯一对照表指向至少一个用例,每个分支与用例亦反向
      指回契约句;全部用例位于 `tests/unit/test_gerrit_fetch.py`,任一
      方向无锚点不得冻结;
- [ ] **设计期 parser-only 证据**:v1.3-FROZEN 的 §0 首表可解析,
      输出逐项出现 §0 全部 `(definition, symbol)` 键且三列齐全;本项只证
      文档形态,不得宣称已与 SPECS 对齐;
- [ ] **实现期完整 bridge 证据**:不得在设计阶段提前写 SPECS;commit C
      待代码与 §0 全部行落地后,把最终 FROZEN 路径接入 bridge,全量绿色
      输出必须逐项出现 skill-3 键;只看 SUMMARY 总绿不算证据;
- [ ] **工具加固(§1.3a)**:module-scope `ImportFrom` 的来源名/本地名映射
      写入实现与源码注释,并验收 §1.3a 全部断言组:
      - **a 回归锁定**:`verdict_changes=0`,且 `campaign_state.py` 的本地
        `_primary_fingerprint` 正确归属到 convergence 来源符号;
      - **b 异名 fixture**:`from A import S as LocalS`(`LocalS != S`),
        旧实现下红,新实现下 A.S 包含 / B.S 排除双向归属绿;
      - **c 同名 fixture**:`from A import S as S` 独立覆盖退化情形,
        **不作为“含 as”泛化能力的证据**;
      - **d 本批真实用例**:gerrit `_run_git` 消费方空 / workspace
        `_run_git` 消费方含 `ci_triage.verify.workspace`;
- [ ] **twin 实测(v1.1 更正)**:按 §1.3 的注册面、输出行和 grep 阈值
      逐项验证;
- [ ] §3 全部契约正向绿 + 全部负控制红;每项负控制逐项贴 `exit 1` 与
      报错原文;§3 正向/负向配对按该节要求陈述
      (正向绿不单独作证);
- [ ] **§4a 机械同步逐项**(尤其该节第 1 项的 shared/types consumers);
- [ ] **§2 交付面入口逐项贴 diff 证据**:安装入口
      `pyproject.toml` / CI 类型门禁 `.github/workflows/ci.yml` / 源码运行
      `README.md` 均加入本 skill;按各文件的真实命名语义执行本项定义的固定
      字符串机械验收(`rg` 不可用时改用 `grep -F -c` 并在报告注明):
      - `rg -F -c "mypy tizen-gerrit-fetch/scripts/tizen_gerrit_fetch" .github/workflows/ci.yml` `>=1`;
      - `rg -F -c '\$PWD/tizen-gerrit-fetch/scripts' README.md` `>=1`;
      - `rg -F -c "tizen-gerrit-fetch/scripts" pyproject.toml` `>=2`
        (package discovery + `mypy_path`);
      - `rg -F -c "tizen_gerrit_fetch" pyproject.toml` `>=2`
        (`tizen_gerrit_fetch*` + `tizen_gerrit_fetch`);
      这些命令须先将 `gerrit` 替换为已完成的 `qb-discover`/`qb_discover`
      同类形态自检,预期计数依次为 `1/1/2/2`;命令在已知应绿样本上不绿,
      判定为验收命令错误而非交付错误;
- [ ] **发布边界显式**:`release-v1.4.0/` 为历史只读快照,本批零 diff;
      下一次发布统一纳入 `tizen-gerrit-fetch`;
- [ ] **pre-shim 行为 parity**:旧址尚未合流时,§5.2 payload 全部字段组
      逐项存在;唯一掩码
      仅为各自 destination 绝对路径 → `<DEST>`。canonical payload
      先逐字段相等,固定 JSON 序列化后的 SHA 再相同,且源码 `cmp`
      相同;逐字段比较证明行为无漂移,SHA 只作记录锚,`cmp` 证明搬移
      未改字,三者均在 shim 覆盖前采集;其中有序命令轨迹须显式报告
      迁移前后调用次数、发生顺序及每次调用的完整 `argv` 逐元素相等,
      并从 `argv` 验收 fetch 次数及 `--depth 1/50`,作为未新增网络往返
      及 §2.2 成本拓扑不漂移的唯一性能等价证据,不单列新流程;
- [ ] **normalizer 反向测试**:§5.2 定义的全部变异样本各自使 parity
      必红;逐项贴变异比较失败证据与对应
      pytest 命令 `exit 0`,证明非白名单字段未被过度归一化;
- [ ] **post-shim identity**:§0 全部实现行 + §1.2 明列的 shared 类型逐项
      `old.X is new.X`;本项只证 shim 接线,不可替代或冒充行为 parity;
- [ ] 双道审计全绿(精确总数以实跑为准);⑧ arch 豁免证据;
- [ ] SKILL.md 落盘;shim 清单更新;
- [ ] **DEFERRED**:同名件合并议题→triage-report 批次;shim 删除→
      P4.9 末(含 §1.2 类型 shim);悬空 symlink 未归一化为
      `SOURCE_DIR_UNSAFE` 的处置议题→gerrit-submit 批次,本批仅按 §2.2
      记录实际 `FileExistsError` 边界;统一 timeout/cancellation、错误
      归一化与中断清理策略→`gerrit-submit` 批次(与本 skill 同属 Gerrit
      外部调用面,届时合并设计并单独评审)。后者是行为变更,不得在任何
      抽取批次内顺手实施。

---
## 附:零生产行为 + 零归属判据变更声明

**零生产行为变更**:`gerrit.py` 的 §0 全部实现行逐字节迁移并以源码
`cmp` 自证,业务行为不变。`_reset_generated_source_dir` 的破坏性语义、
查询与 git 阶段的混合失败语义、悬空 symlink 的既有边界一律保持现状。
§2.2/§5.1 只补写契约并用分支覆盖表固化现行为;任一测试与现行为
不符,必须停止报告,不得修改生产代码迁就测试。

**零归属判据变更**:owner/layer 判据保持不变,由 §0 规划终态 dry-run
证明。

**本批确有的机制新增(必须执行)**:

1. commit A′ 加固 `_actual_consumers` 的 import-binding 解析,建立
   来源名 `alias.name` → 本地名 `alias.asname or alias.name` 的映射;
   以 `verdict_changes=0` 锁定既有全部裁决,并以异名 fixture 在旧实现
   下必红作为存在性证明。
2. §5 引入 pre-shim parity 取证流程,确保行为比较发生在两条 import
   路径被 shim 合流之前。

**本批非抽取交付项(完整清单)**:

1. §4 环境测试修复,关闭 skill-2 DEFERRED;
2. commit A′ 审计工具加固;
3. §2.2 契约补写与 §5.1 分支覆盖表的现行为固化测试;
4. `pyproject.toml` / CI / README 按 §2/§4a 同步全部交付入口,并声明
   `release-v1.4.0/` 历史快照不回填;
5. pre-shim parity / post-shim identity 双段证据流程。

**执行护栏**:本声明圈定的是“生产行为与归属判据必须不变”,不是
“本批什么都不新增”。不得以本声明为由跳过上述机制或非抽取交付项。
