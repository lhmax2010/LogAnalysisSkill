# P4.9 step-0 设计:共享层下沉与 marker 权威归位(v1.0-draft)

- 阶段:P4.9 step-0(六 skill 抽取的**地基**,先于任何 skill)
- 前置:P4.5 已 merge(v1.5.18-FROZEN);提纲四轮评审收敛(v3.1)
- 输入契约来源:提纲 V3-1/2/3/4 + 两家评审调用图证据
- **总铁律**:行为等价——本 step 只搬家 + 建共享层 + 改 import 路径,
  **零语义变更**;完成后**以 merge 基线 commit 的全量测试数为准,
  原样全绿(测试内容不变、import 路径可改)**。

---

## §1 C 类库物理归属(V3-4,第一节,先于一切)

### 1.1 决策:独立 `shared` 顶级包,不留在 ci_triage 内

**现状**:`state/keys/records` 物理在 `ci_triage/state/`(编排包内)。
若六个 skill 包 `import ci_triage.state`,则 **skill 反向依赖编排层
包的内部子模块**——违背"skill 消费共享库、不消费编排层"的精神,
且 release 打包时六 skill 各自都要拖一份 ci_triage 依赖。

**决策**:建独立顶级包 **`tizen_ci_shared`**(与六 skill、ci_triage
编排层平级),承载全部 C 类库。依赖方向单向冻结,
shared 内部也不是扁平层:

```
skill 包  ──→  tizen_ci_shared  ←──  ci_triage(编排层)
                    |
                    v
      L1: state | workspace | classify
                    |
                    v
             L0: quickbuild_http
                    |
                    v
              L-1: types(最底层)

依赖只能沿箭头向下:types < quickbuild_http < L1。
```

- **shared 不 import 任何 skill、不 import ci_triage 编排层**(CI 加
  一条 import-linter 规则物理保证,违反即构建失败);
- skill 之间禁横向依赖(规则 3)不变;
- ci_triage 编排层继续存在(campaign_repair_step 等不抽),改为
  `import tizen_ci_shared.*` + `import <skill>.*`。

### 1.2 shared 包内部结构(下沉清单一次冻结)

```
tizen_ci_shared/
  types.py             # L-1:跨 skill 纯数据类型(§2)
  quickbuild_http.py   # L0:QuickBuild HTTP 公共面 + GBS fetch(§4)
  state/               # L1:现 ci_triage/state/{db,keys,records}.py
  workspace/           # L1:marker 权威 + 跨消费方原语(§3)
  classify.py          # L1:现 verify/failure_classify.py
```

**归属边界(符号自证 round 2 + v1.3 分层)**:
- QuickBuild HTTP 基础件横跨编排层、discovery 与 report,
  归 `shared/quickbuild_http`;GBS 结果类型归最底层
  `shared/types`,HTTP/fetch 向下依赖 types 合法;
- `fetch_gbs_report` / `download_gbs_package_buildlog` 归
  `shared/quickbuild_http`,parse/render 留 triage-report,两组不直接互调;
- `edit_spec_guard` 实测消费方仅 build_verify,随
  **build-verify** 移动,不进 shared;
- `failure_classify` 模块语义被 wrapper 消费,整体归
  `shared/classify`;`FailureClassification` 随模块同宿。

### 1.3 shared 内部三层契约(v1.3)

shared 内部顺序冻结为:

```
L1:  state | workspace | classify
                    ↓
L0:        quickbuild_http
                    ↓
L-1:             types
```

三条可机械验证的层规则:
1. **低层禁止上行**:`types` 不 import 任何 shared 子层;
   `quickbuild_http` 只可 import `types`,不可 import L1。
2. **L1 同层独立**:`state` / `workspace` / `classify` 之间不得
   直接或间接横向 import;三者可依赖 L0/L-1。
3. **shared 不得上行**:任何 shared 子层都不得 import
   `ci_triage` 编排层或六个 skill 包。

#### import-linter 配置草案(step-0 实现时落盘)

以下是 `.importlinter` 契约草案,层次从高到低排列;
`|` 表示同层 sibling 独立。实现时若包 import root 改名,
包名与此配置必须在同一 commit 一起改,不得改语义。

```ini
[importlinter]
root_packages =
    tizen_ci_shared
    ci_triage
    tizen_qb_discover
    tizen_gerrit_fetch
    tizen_build_verify
    tizen_convergence_judge
    tizen_gerrit_submit
    tizen_triage_report

[importlinter:contract:shared-layers]
name = shared layers: L1 -> quickbuild_http -> types
type = layers
containers =
    tizen_ci_shared
layers =
    state | workspace | classify
    quickbuild_http
    types

[importlinter:contract:shared-l1-independence]
name = shared L1 domains are independent
type = independence
modules =
    tizen_ci_shared.state
    tizen_ci_shared.workspace
    tizen_ci_shared.classify

[importlinter:contract:shared-no-upward-imports]
name = shared must not import orchestrator or skills
type = forbidden
source_modules =
    tizen_ci_shared
forbidden_modules =
    ci_triage
    tizen_qb_discover
    tizen_gerrit_fetch
    tizen_build_verify
    tizen_convergence_judge
    tizen_gerrit_submit
    tizen_triage_report
```

S3-A 反向验证(每条都必须在 step-0 实现时先证明会红,
再撤销故意违规):
- **layers contract**:在 `types.py` 故意 import `quickbuild_http`,
  或在 `quickbuild_http.py` 故意 import `state`,
  `lint-imports` 必须失败;
- **independence contract**:在 `state` 故意 import `workspace`,
  `lint-imports` 必须失败;
- **forbidden contract**:在 `classify.py` 故意 import `ci_triage`
  (或任一 skill root),`lint-imports` 必须失败。

## §2 跨 skill 数据类型下沉(types.py)

实测跨界类型(定义位置 → 消费方):

| 类型 | 现定义 | 消费方 | 处置 |
|---|---|---|---|
| `SourceFetchResult` | gerrit.py | report + gerrit-fetch 产出 | 迁 shared/types |
| `FailedPackage` | quickbuild_log.py | orchestrator + report + runner | 迁 shared/types |
| `DisposableWorktree` | verify/workspace.py | workspace 内部创建/清理链(外部无直接类名引用) | 迁 shared/workspace |
| `WorkspaceViolation` | verify/workspace.py | campaign_repair_step + workspace 内部链 | 迁 shared/workspace |
| `FailureClassification` | verify/failure_classify.py | 类名直接消费方仅 build_verify;classify 模块语义另被 wrapper 消费 | 随 shared/classify 同宿 |
| `GbsReportPackage` | gbs_report.py | orchestrator + runner | 迁 shared/types |
| `GbsReport` | gbs_report.py | `fetch_gbs_report` 内部构造/返回 | 迁 shared/types(最底层) |

**原定义处留 re-export shim**(`from tizen_ci_shared.types import X`),
**P4.9 全部 skill 抽取完成后统一删除**(不留永久 shim,提纲第 0 条)。
shim 仅存活于 P4.9 期间,§6 列删除清单。

## §3 workspace 函数级归属 + 双 marker 权威(V3-1 + V3-2 v3.1)

### 3.1 两个 marker 全部归 shared(权威唯一)

workspace.py 有**两个** marker,均为格式权威,**整体归 shared**,
消除两处定义的第二权威(V3-1 收 PROTECTED、v3.1 补 workdir):

| marker | 常量 | 写入方 | 读取方 |
|---|---|---|---|
| protected | `PROTECTED_FILENAME` (.ci_triage_protected) | build-verify(何时写) | wrapper/submit(经 shared 原语) |
| workdir | `MARKER_FILENAME` (.ci_triage_workdir) | build-verify 调 shared `write_workdir_marker` | shared 清理链 |

**格式权威归位**:两个 FILENAME 常量 + `_read_marker` + marker 结构
= shared 唯一定义;**build-verify 只拥有"何时写"的调用语义**,调
shared/workspace 的 `mark_worktree_protected` /
`write_workdir_marker`,不自持任何 marker 格式常量。

### 3.2 函数级归属表(附调用图证据,⑩补强要求)

| 符号 | 完整调用图(非仅 import) | 归属 |
|---|---|---|
| `create_worktree` | 仅 build_verify;目标实现调 shared `write_workdir_marker` | **build-verify** |
| `check_disk_and_maybe_cleanup` | 仅 build_verify;内部调 cleanup_worktree | **build-verify**(下行依赖 shared/workspace) |
| `_copy_repository` | 仅 create_worktree:58(单消费方) | **build-verify**(随 create_worktree) |
| `cleanup_worktree` | build_verify + workspace 内部链 | **shared/workspace** |
| `cleanup_disposable_copy` | campaign_repair_step(wrapper) | **shared/workspace** |
| `is_protected` | campaign_repair_step(wrapper) | **shared/workspace** |
| `release_worktree_protection` | gerrit_submit(submit) | **shared/workspace** |
| `mark_worktree_protected` | build_verify | **shared/workspace**(格式权威) |
| `write_workdir_marker(worktree_path: Path) -> None` | S-1 待建原语;create_worktree 将调用;写 `MARKER_FILENAME` + marker dict | **shared/workspace**(`status=to-be-created`) |
| `_oldest_worktrees`/`_run_git`/`_verify_cleanup_handle` | workspace 清理链内部 | **shared/workspace** |
| `_exclude_private_files` | create_worktree + mark 侧(跨界) | **shared/workspace** |
| marker 全套(2×FILENAME + `_read_marker`) | 三方 | **shared/workspace** |
| `DisposableWorktree` | workspace 内部创建/清理链 | **shared/workspace** |
| `WorkspaceViolation` | campaign_repair_step + workspace 内部链 | **shared/workspace** |

**判据**:单消费方随消费者(`create_worktree`/`_copy_repository`→
build-verify);多消费方或格式权威→shared。**skill→shared 的下行
依赖合法**(`check_disk_and_maybe_cleanup` 在 build-verify 却调 shared
的 `cleanup_worktree`,不是横向依赖)。

### 3.3 build_verify 反向依赖清理(前置)

`build_verify.py:27` 反向 `import ci_triage.runner.discover_sibling_pythonpath`
——编排层→被抽 skill 的反向边。**裁决**:`discover_sibling_pythonpath`
下沉 shared(它是环境路径 helper,无编排语义);build_verify 与
runner 均改 `import tizen_ci_shared`。

## §4 QuickBuild HTTP / GBS report 归属(v1.3 分层)

`quickbuild.py` 和 `gbs_report.py` 当前混合 HTTP、GBS 抓取、解析
与编排层默认值。round-2 符号自证后的完整归属为:

| 组 | 完整符号面 | 实测消费方/内部链 | 归属 |
|---|---|---|---|
| HTTP 常量/类型 | `DEFAULT_QUICKBUILD_BASE_URL` / `DEFAULT_COOKIE_PATH` / `DOWNLOAD_LINK_MARKER` / `DOWNLOAD_TIZEN_BASE_URL` / `HttpFetcher` / `HttpResponse` / `QuickBuildDownload` / `PackageBuildLog` / `QuickBuildError` | gbs_report + sources + runner/orchestrator/CLI;其余为 HTTP 内部契约 | **shared/quickbuild_http(L0)** |
| HTTP 函数 | `load_cookie_jar` / `download_full_log` / `find_download_href` / `derive_package_buildlog_url` / `download_package_buildlog` / `_raise_if_login_page` / `_urllib_fetch` / `normalize_quickbuild_url` | 多消费方或 HTTP 内部链 | **shared/quickbuild_http(L0)** |
| GBS fetch | `fetch_gbs_report` / `download_gbs_package_buildlog` | orchestrator + runner | **shared/quickbuild_http(L0)** |
| 编排默认值 | `DEFAULT_ARCHES` | 仅 orchestrator | **ci_triage(orchestrator,不下沉)** |
| GBS 结果类型 | `GbsReportPackage` / `GbsReport` | orchestrator + runner / fetch 内部 | **shared/types(L-1 最底层)** |
| parse/render | `find_iframe_src` / `parse_gbs_report_packages` / `_Anchor` / `_Cell` / `_Row` / `_Table` / `_CellBuilder` / `_AnchorBuilder` / `_IframeParser` / `_ReportTableParser` / `_looks_like_build_status_table` / `_row_to_package` / `_status_from_anchor` / `_attrs_to_map` / `_class_names` / `_normalize_text` | parse 内部链 | **tizen-triage-report** |

`GbsReportPackage` / `GbsReport` 是无行为的数据契约,放在
types 最底层;`quickbuild_http` 的 fetch 组向下 import types 合法。
**解耦约束**:fetch 组只抓取并返回原始 report 对象,
不直接调 triage-report 的 `find_iframe_src` /
`parse_gbs_report_packages`;调用方在编排或 report 侧显式解析。
最终依赖方向为上层 → quickbuild_http → types,
不存在 shared → skill/report 的上行依赖。

## §5 回归绑定与 parity(行为等价证明)

1. **import 路径改动是唯一允许的测试修改**:测试 import 从
   `ci_triage.verify.workspace`/`ci_triage.gerrit` 等改为
   `tizen_ci_shared.*`/skill 路径;**断言与 fixture 内容一字不改**。
   diff 审核标准:测试文件 diff 只含 import 行。
2. **parity 归一化规则冻结**(字面逐字节做不到):比对下沉前后同
   输入的输出对象,只掩码白名单内的易变字段——`at` 时间戳、
   worktree 绝对路径、tmp 文件名、cookie 路径及 `base_url` 等
   环境派生绝对路径;其余字段严格相等。marker 文件内容除时间戳外
   逐字节相等。白名单不得用宽泛的“所有路径”替代,新增项须有
   parity 差异证据。
3. **import-linter 规则**:CI 落 §1.3 的 layers / independence /
   forbidden 三条 contract,并保留 skill 间独立约束,物理保证依赖方向。
4. **全量基线**:step-0 完成后测试数 == P4.9 启动 merge 基线数
   (change_46 落测试后的数,不写死),原样全绿。
5. **round-2 审计锚点**:归属基线报告为
   `docs/clang-fix-campaign/review/p49-step0-symbol-audit.md`,commit
   `4b3029a`,报告文件 SHA-256
   `54ab1b5cc5c7eac59f38475e85620c2e10ebeda813bf40a11c5f1324b25a37dc`。
   v1.3 只细化 shared 子层标签,不得改变该轮实测消费方。

## §6 shim 生命周期与执行

- 下沉件在**原位置留 re-export shim**(P4.9 期间兼容未抽 skill 的
  旧 import);
- **删除清单**(P4.9 六 skill 全抽完后统一执行,单独 commit):
  gerrit.py/quickbuild_log.py/workspace.py/failure_classify.py/
  edit_spec_guard.py 的 re-export 行,以及 `quickbuild.py` 中全部
  HTTP 件的 re-export shim;
- step-0 自身分**三个 commit**:①建 shared 包 + 迁 state/types
  ②迁 workspace(双 marker)+ classify/edit_spec + 反向依赖清理
  ③gbs_report 切分 + import-linter 规则;**每个 commit 后全量测试
  与 `lint-imports` 都必须绿**,不得只在第三个 commit 才检查层级。

## §7 DoD

- [ ] shared 独立包建立,§1.3 三条 import-linter contract 生效;
  layers / independence / forbidden 各自按冻结反向用例故意违规时
  `lint-imports` 必须红,撤销违规后恢复绿;
- [ ] 两个 marker 格式常量在 shared 唯一定义(grep 全仓 `FILENAME =`
  仅 shared 命中);
- [ ] workspace 函数级归属按 §3.2 表落地,调用图证据附 dev_memory;
- [ ] gbs_report 切分,report 无 qb-discover 私有 import(grep 证);
- [ ] 全量测试 == 基线数、原样全绿;测试 diff 仅 import 行;
- [ ] parity:build-verify/convergence 关键路径下沉前后归一化相等;
- [ ] 三 commit 各自全量测试 + `lint-imports` 全绿;shim 清单登记
  待 P4.9 末删除。

---

## 附:方法论遵循自证(按⑩补强)
本稿每张归属表的"完整调用图"列,证据取自 `grep -rn <symbol>`(函数
体内调用,非仅 import 行);转正式冻结前,Codex 须对 §3.2/§4 逐符号
复跑调用图并附输出,任一不符即停止报告(§3.2 是本 step 的高危表,
已在提纲 v3→v3.1 栽过一次)。

---

# 附:v1.1 修正(两家评审,2 必改 + 1 必答 + 数条)——§2/§3.2/§4 三表按完整调用图重做

**性质**:两家一致确认架构决策(shared 独立包/双 marker 单权威/
选项③/shim 生命周期)全部成立;但作为"归属表即契约"的地基文档,
§2/§3.2/§4 三张表各有失实——**且都落在文档自己按⑩自证的位置**。
⑩第三次同类立规事故(v1 印象→v2 import 行→v3.1 调用图→本次函数
体内写操作与切割清单不全),记账见文末。以下按完整调用图重做。

## S-1 [必改] create_worktree 的 marker 写入抽为 shared 原语

**实锤**:`create_worktree` 函数体 `workspace.py:53` 亲手拼
`MARKER_FILENAME` 路径 + 构造 marker dict 写入。§3.2 归 build-verify
skill 会把 marker 格式代码留在 skill,§7 DoD"FILENAME 仅 shared 命中"
必然失败;§3.1"create_worktree 归 shared"又违反单消费方判据。
**裁决**:从 create_worktree 抽出 shared 原语
`write_workdir_marker(worktree_path) -> None`(marker 格式在 shared
唯一定义);skill 侧 create_worktree **调它**,自身不含 FILENAME。
§3.2 表补一行 `write_workdir_marker → shared`;§3.1 措辞改为
"create_worktree(build-verify)调 shared 的 write_workdir_marker /
mark_worktree_protected"。同理审 `_read_marker` 与读侧对称。

## §4 gbs_report 切分表(重做——公共面实测六符号,非一个)

| 符号 | 实测消费方 | 半边 | 去向 |
|---|---|---|---|
| `fetch_gbs_report` (:56) | runner + orchestrator | fetch | 过渡停 quickbuild.py(见 S-2) |
| `download_gbs_package_buildlog` (:103) | runner + orchestrator | fetch | 同上(v1.1 补:漏切) |
| `DEFAULT_ARCHES` (:20) | orchestrator(:70 做默认值) | fetch 侧常量 | 同上(v1.1 补:无归属) |
| `GbsReportPackage` (:30) | runner + orchestrator | **跨 skill 类型** | **shared/types**(v1.1 补:§2 也漏收) |
| `GbsReport` (:42) | (仅内部) | 数据类型 | 随 parse 半边或 shared/types(正式设计定) |
| `parse_gbs_report_packages` (:133) + `find_iframe_src` + `_*` helper | (仅内部/被 fetch 调) | parse/render | tizen-triage-report(纯渲染) |

**§2 类型表补两行**:`GbsReportPackage`、`GbsReport` 迁 shared/types。
report 侧改依赖 shared/types + 从 qb-discover 取已抓数据;fetch 侧
三符号(fetch/download/DEFAULT_ARCHES)+ 私有(`_raise_if_login_page`/
`_urllib_fetch`)整组随 fetch 走。

## S-2 [必改] §4 时序:step-0 期 fetch 半边停靠 quickbuild.py

qb-discover 到批次 2 才存在,step-0 不得提前建 skill 包(违"先于
任何 skill")。**裁决**:commit ③ 把 fetch 半边(六符号中的 fetch 组)
**物理并入 `quickbuild.py`**(qb-discover 的现居地),随批次 2 一起
被抽走;parse 半边留 gbs_report.py(将随 report 批次)。step-0 只
做"fetch/parse 分家 + 类型下沉",不建任何 skill 包。

## S-2b [必改] edit_spec_guard 随 build-verify(非 shared)

**实锤**:src 树消费方**仅 build_verify.py**(campaign_repair_step
零引用——⑩第三次:v1.0 写的"wrapper 侧亦引"是不存在的消费方)。
按单消费方判据**随 build-verify skill**,§1.2 shared 清单删
edit_spec.py。(未来 review-submit 2.5 若成消费方,届时按真实消费
方重归,不预支。)failure_classify 保持 shared(它真被 wrapper 的
6a denied 短路消费,已实测)。

## S-3 [必答] §1 补完 V3-4 物理位置 + 打包

- **物理布局**:`tizen-ci-shared/scripts/tizen_ci_shared/`(与
  tizen-ci-triage 等平级顶级目录,scripts 子层对齐现有 skill 布局);
- **PYTHONPATH**:测试/README 的 PYTHONPATH 前缀加
  `tizen-ci-shared/scripts`(与现四路径并列);
- **release 打包**:`release-v1.4.0/` 现五 skill 平级目录,新增
  `tizen-ci-shared/` 一项;pyproject 的 packages 清单加
  tizen_ci_shared;**runner.py:241 的 sibling 名单扩充属各 skill
  批次的语义变更,step-0 不动**(评审明确:下沉 discover_sibling_
  pythonpath 行为等价安全,但名单扩充不在 step-0)。

## S-4 [MINOR] shim 清单补两项
- `verify/__init__.py` 的包级 re-export 面(转出 workspace/classify
  等)纳入 shim 清单,P4.9 末统一删;
- `ci_triage/state/`:**commit ① 全量翻转 import、不留 shim**(实测
  state 包内部仅包内 import、无上行依赖,整体迁移干净——无需 shim
  过渡)。

## S-5 [MINOR] §5.1 测试 diff 标准放宽
"测试 diff 只含 import 行" → **"import 行 + monkeypatch/setattr 目标
字符串中的模块路径"**(patch 目标含模块路径,下沉后必须跟改)。
C15(源码子串断言清理)在 step-0 顺带收,一并处理这类字符串。

## §3.2 行号更正 + NIT
- `check_disk_and_maybe_cleanup` 调用点 `build_verify.py:126`、
  `create_worktree` 在 `:133`(v1.0 对调,已改);
- §3.2 删 `verify/__init__` 作 `mark_worktree_protected` 消费方
  (re-export 非消费方);
- §7 DoD"grep FILENAME="**排除 `release-v1.4.0/` 快照副本**;
- import-linter 声明为**新增开发依赖**(pyproject dev-deps + 配置
  契约 + 挂现有 .github workflow);§7 反向验证措辞改
  "故意加一条**违反规则的 import** → 构建必须红"。

## 方法论记账(⑩ 第三次,升为硬闸)
⑩ 前两次:凭印象 / 只 grep import 行。本次拉了调用图,却漏了
**函数体内的写操作**(create_worktree 写 marker)、**切割清单的
完整公共面**(gbs_report 六符号只列一)、**不存在的消费方**
(edit_spec"wrapper 亦引")。**升为硬闸:凡"归属表/切割清单"类
契约,冻结前 Codex 必须对每个符号复跑 `grep -rn <symbol>`(消费方)
+ 函数体扫描(该符号是否被内部写/读),输出附设计稿;任一符号的
声明消费方与 grep 不符 → 停止报告,不得冻结。** step-0 因此在送
三方评审前先过一道"符号自证脚本"(Codex 产出,列每符号的实测
消费方 + 内部引用点)。

---

# 附:v1.2 修正(符号自证 16 MISMATCH 裁决)——归属表按脚本证据重定

**依据**:`p49-step0-symbol-audit.md`(design SHA
031c0ab3…,commit d06ad9a),32 OK / 16 MISMATCH / 0 INCOMPLETE。
脚本用完整调用图 + AST 抓出人工三轮(v1/v2/v3.1)漏掉的 16 处。
**处置权在设计侧,以下按 grep 证据逐类裁决;裁决后 Codex 更新
symbol_audit 输入清单并复跑,须达全部符号 OK
(N/N,N 由清单实际长度决定),且 0 MISMATCH / 0 INCOMPLETE,
方可冻结。**

## 类 A:HTTP 件全部归 shared(消费面横跨编排层 + 多 skill)

自证实测:`DEFAULT_COOKIE_PATH` 6 消费方(batch_cli/cli/gbs_report/
orchestrator/runner/sources)、`QuickBuildError` 5 方、`HttpFetcher`/
`_raise_if_login_page`/`_urllib_fetch`/`DEFAULT_QUICKBUILD_BASE_URL`
均 gbs_report+sources 双方以上。这些是 quickbuild.py 的 HTTP 基础件,
消费面横跨**编排层(不抽)+ qb-discover + report/sources**——**没有
单一 skill 能独占,归属只能是 shared**。

**裁决(推翻 v1.1 的"HTTP 件归 qb-discover")**:quickbuild.py 的
HTTP 基础层(`HttpFetcher`/`QuickBuildError`/`_raise_if_login_page`/
`_urllib_fetch`/`DEFAULT_COOKIE_PATH`/`DEFAULT_QUICKBUILD_BASE_URL`/
`load_cookie_jar` 等)**下沉 shared**(新增 `shared/http.py` 或
`shared/quickbuild_http.py`)。qb-discover 保留的是**失败发现语义**
(sources.py 的 discovery 逻辑、失败包解析),消费 shared 的 HTTP 层。
——这修正了我对 qb-discover 边界的误解:它是"发现"skill,不是"HTTP
client"skill;HTTP 是所有抓取者的公共地基。

## 类 B:gbs_report 的 fetch 组归 shared,非 quickbuild/qb-discover

`fetch_gbs_report`/`download_gbs_package_buildlog` 均 orchestrator+
runner 双消费(编排层),`DEFAULT_ARCHES` 仅 orchestrator 消费。
**裁决**:
- `fetch_gbs_report`/`download_gbs_package_buildlog`(编排层双消费 +
  依赖 shared HTTP 层)→ **shared**(GBS 报表抓取是编排层直接调的
  公共能力,非某 skill 私有);
- `DEFAULT_ARCHES`(仅 orchestrator)→ 随 **orchestrator 留 ci_triage**
  (单消费方是编排层本身,不下沉、不入任何 skill);
- **§4 的"fetch 半边切给 qb-discover"整体作废**——真实消费面是编排
  层,不是 qb-discover。gbs_report 拆为:抓取组→shared,parse/render
  组(`parse_gbs_report_packages`/`find_iframe_src`/`_*` 表解析)→
  triage-report。

## 类 C:cross-boundary 内部调用消解(find_iframe_src/parse_*)

自证报 `find_iframe_src`/`parse_gbs_report_packages` 被
`fetch_gbs_report` 内部调用而分属两侧——**类 B 裁决后自动消解**:
fetch 组入 shared 后,shared 内部调 parse 组会变成 shared→report 的
上行依赖(非法)。**裁决**:parse/render 组保持独立、**fetch 组不在
shared 内直接调 parse**——`fetch_gbs_report` 返回原始 report 对象,
由调用方(编排层/report)自行调 parse。即 fetch 与 parse **解耦**,
不互调;这也符合"抓取"与"解析"本就该分离。§4 补此解耦约束。

## 类 D:跨 skill 类型补入 shared/types(§2 漏收)

- `FailedPackage`:自证 3 消费方(orchestrator/report/runner)→ 确认
  shared/types(v1.1 已列,但 v1.1 消费方只写了 report,补全);
- `FailureClassification`:自证仅 build_verify 消费(campaign_repair_step
  **未消费**——v1.0/v1.1 的"wrapper 亦消费"再次证伪)→ 但
  `failure_classify` 模块本身因 `REPAIR_DENIED` 被 wrapper 6a 消费仍
  归 shared;`FailureClassification` 类型随模块 → shared(单消费方
  build_verify,但与 classify 模块同宿,不拆);
- `DisposableWorktree`/`WorkspaceViolation`:自证消费方是
  campaign_repair_step + workspace 内部链 → shared(§2 已列,消费方
  更正);
- **`GbsReport`(未裁定项)**:自证仅被 `fetch_gbs_report` 内部构造/
  返回 → 它是**抓取结果类型**,随 fetch 组 → **shared/types**
  (类 B 后 fetch 在 shared,其返回类型同域)。

## 类 E:write_workdir_marker 是待建原语(NOT_FOUND 属预期)

自证报 `write_workdir_marker` 定义未找到——**这是正确的**:它是 S-1
裁决要新建的 shared 原语,当前源码里本就不存在。**修正 symbol_audit
输入**:把 `write_workdir_marker` 标为 `status=to-be-created`,审计
对该类符号只校验"归属声明=shared"、不校验定义存在(建后再验)。
同理任何 step-0 新建原语走此标记,避免 NOT_FOUND 假 MISMATCH。

## 复冻条件

Codex 依类 A–E 更新 symbol_audit 输入清单(归属改定、
`DEFAULT_ARCHES`/`GbsReport` 等归属更正、`write_workdir_marker` 标
to-be-created)→ 复跑 → **必须全部符号 OK(N/N,N 动态;
to-be-created 项按归属声明校验),且 0 MISMATCH / 0 INCOMPLETE** →
报告贴新输出 → 方可送三方评审。仍有 MISMATCH/INCOMPLETE →
停止报告。

## 方法论记账(⑩ 终局)
人工三轮收敛到 32/48,机械一次补齐 16——**⑩硬闸(归属表须脚本自证)
的价值实证:结构归属这类"全调用图"断言,人工不可靠是稳定事实,不是
偶发失误。** 自本 step 起,归属/切割类契约冻结前**必过 symbol_audit
全部符号 OK(N/N,N 动态),且 0 MISMATCH / 0 INCOMPLETE**,
Claude 的人工表仅作草案、以脚本输出为准。这是⑥/⑨/⑩三条
"实测优先"方法论的合流终点:能机械核验的结构断言,不接受人工"我
看过了"。

---

# 附:v1.3 修正(两家 step-0 冻结前评审)——shared 内部分层 + 收口项

**依据**:两家评审在同一洞的两面收敛——评审 A S3-1(shared 分层
依赖倒置风险)+ 评审 B S3-A(import-linter 无法表达"包内分层")。
核验确认:HTTP 件当前**不依赖 state**(grep 空),故 shared 五子层
可分层、非既有坏依赖;评审要的是**设计上先立层级、防未来长出倒置**。
以下按两家一致意见补,补后送第二轮 step-0 评审。

## §1.3 shared 内部分层(v1.3 新增,S3-1/S3-A 合并裁决)

shared 不是扁平包,内部按**依赖层级**冻结,层间单向向下:

```
shared/
  L0 基础层(无 shared 内部依赖):
    types.py            # 纯数据类型,不 import 任何 shared 子模块
    quickbuild_http.py  # HTTP 原语,依赖 types(仅类型),不依赖 state
  L1 领域层(可依赖 L0):
    state/              # 账本,依赖 types
    workspace/          # marker + worktree,依赖 types
    classify.py         # 失败分类,依赖 types
```

**层规则(import-linter 用 layered contract 表达,S3-A)**:
- L0 不得 import 任何 L1(types/quickbuild_http 不碰 state/workspace/
  classify);
- L1 之间不得横向 import(state 不依赖 workspace,反之亦然);
- 全 shared 不得 import skill / ci_triage 编排层(原规则不变)。
- **import-linter 配置**:用 `layers` contract 声明 L0<L1 + 每层
  内模块 `independence` contract 声明同层不横向;**三条 contract
  各配一个"故意违反→构建红"的反向验证**(S3-A 要求可证伪)。

## 收口项(两家 MINOR/NIT,逐条)

- **S3-2(评审 A)**:§4 明确 fetch 组入 shared/quickbuild_http 后,
  其对 `GbsReportPackage` 的依赖方向——`GbsReportPackage` 属 types(L0),
  fetch 组(L0 quickbuild_http)依赖 types(L0)属**同层**,违反"L0
  内 quickbuild_http 不 import 其它 L0"?**裁决**:类型是 L0 的
  **最底**,quickbuild_http 依赖 types 合法(types 是 L0 的 L0,即
  "L-1 纯类型层");import-linter 里 types 单列最底层,quickbuild_http
  可依赖 types、不可依赖任何有逻辑的模块。§1.3 层图 types 降为最底。
- **S3-3(评审 A)**:parity 归一化白名单补 **cookie 路径 / base_url
  等环境派生绝对路径**(除已列的 at/worktree/tmp 三类)——HTTP 件
  下沉后测试会触及这些;
- **S3-B(评审 B)**:§6 三 commit 划分补一句"每 commit 后 import-linter
  必须绿",不只全量测试绿——分层规则每步都要守;
- **S3-C(评审 B)**:`write_workdir_marker` 待建原语的签名在 §3.2
  预冻(`write_workdir_marker(worktree_path: Path) -> None`,写
  MARKER_FILENAME + marker dict),避免 Codex 实现时再猜;
- **S3-D(评审 B)**:shim 删除清单(§6)补 `quickbuild.py` 的 HTTP
  件 re-export（下沉 shared 后原位留 shim,P4.9 末删);
- **NIT(两家)**:审计报告 SHA 锚点写进设计稿 §5(可追溯到具体
  59/59 那次);§1.1 依赖图补 types 最底层箭头。

## 复评条件
Codex 按 v1.3 更新设计稿正文(§1.1/§1.3 分层、§4 types 层级、§6
commit 约束)+ symbol_audit 若因 types 分层需调归属则复跑至全 OK →
送第二轮 step-0 评审。分层是新增结构决策,值得两家再过一轮再冻。

## 方法论记账(⑪)
**⑪ 共享层必须内建依赖层级,不做扁平包。** 两家独立指出"扁平 shared
会允许未来分层倒置"——单一共享包是"把所有共享物平摊,靠纪律不互相
依赖"的隐性赌注,与本项目"物理强制优于软约束"相悖。凡建共享层,
须同时冻结层级 + import-linter layered contract,让倒置在构建期物理
不可能,而非评审期靠人看。
