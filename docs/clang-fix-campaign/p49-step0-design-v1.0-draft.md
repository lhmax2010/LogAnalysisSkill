# P4.9 step-0 设计:共享层下沉与 marker 权威归位(v1.4-FROZEN-candidate)

- 阶段:P4.9 step-0(六 skill 抽取的地基,先于任何 skill)
- 前置:P4.5 已 merge(v1.5.18-FROZEN);提纲四轮评审收敛(v3.1)
- **v1.4 说明**:本稿为**干净正文**,v1.0→v1.3 的全部附录裁决已合并
  进正文对应节,不再叠补丁(消除 body/appendix 三次漂移)。归属表经
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
  quickbuild_http.py  # L0 :QuickBuild HTTP 公共面 + GBS fetch_raw(§4)
  env.py              # L0 :discover_sibling_pythonpath(§3.3,纯 stdlib)
  state/              # L1 :现 ci_triage/state/{db,keys,records}
  workspace/          # L1 :marker 权威 + worktree 原语(§3)
  classify.py         # L1 :现 verify/failure_classify.py
```

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
skill / ci_triage 编排层。`fetch_gbs_report_raw` 对 types(GbsReport
等)的依赖是 L0→L-1,合法。

**import-linter 配置(随 commit ① 落盘,step-0 阶段名单)**:

```ini
[importlinter]
root_packages =
    tizen_ci_shared
    ci_triage
# 六个 skill root 随各自抽取批次同 commit 加入(演进点,勿在 step-0 落)

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
# 六 skill 随批次加入 forbidden 清单(演进点)

[importlinter:contract:root-layers]
name = 根级:ci_triage / skills / shared 单向(skill↛ci_triage、skill↛skill)
type = layers
layers =
    ci_triage
    tizen_qb_discover | tizen_gerrit_fetch | tizen_build_verify | tizen_convergence_judge | tizen_gerrit_submit | tizen_triage_report
    tizen_ci_shared
containers = .
# step-0 阶段 skill 层为空(包未建);各 skill 批次填入自己那格,
# 该 contract 一次性表达 skill↛ci_triage(向下合法、向上禁)+
# skill↛skill(同层独立)——收口两家三轮重申的 skill 侧契约缺位。
```

**三条反向验证(S3-A 可证伪,每条一个"故意违反→lint 红"用例)**:
①shared 内 types 加一行 `import ...state` → shared-layers 红;
②shared 加一行 `import ci_triage` → shared-no-uplink 红;
③模拟一个 skill 加 `import ci_triage` → root-layers 红。
**每 commit 后 `lint-imports` 必须绿**(配置随 commit ① 在,①②③ 各步
可跑)。`shared/__init__.py` 冻结为**空或仅导出 types**,避免
`import tizen_ci_shared` 连带拉起 state。

**import-linter 为新增 dev-dep**,pyproject dev-deps 钉版本(sibling
`|` 语法版本相关),挂现有 .github workflow。

## §2 跨 skill 数据类型下沉(types.py,L-1)

| 类型 | 现定义 | 实测消费方 | 归属 |
|---|---|---|---|
| `SourceFetchResult` | gerrit.py | report | shared/types |
| `FailedPackage` | quickbuild_log.py | orchestrator/report/runner | shared/types |
| `GbsReportPackage` | gbs_report.py | orchestrator/runner | shared/types |
| `GbsReport` | gbs_report.py | fetch_raw 构造/返回 | shared/types |
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

## §4 QuickBuild HTTP / GBS report 归属(分层落地)

### 4.1 HTTP 件下沉 shared/quickbuild_http(L0)

实测消费面横跨编排层 + 多消费方,无单一 skill 独占 → 全归 shared:
`HttpFetcher`/`HttpResponse`/`QuickBuildError`/`_raise_if_login_page`/
`_urllib_fetch`/`load_cookie_jar`/`download_full_log`/
`download_package_buildlog`/`DEFAULT_COOKIE_PATH`/
`DEFAULT_QUICKBUILD_BASE_URL` 等 quickbuild.py 全部 HTTP 公共面(17 项,
symbol_audit INCOMPLETE 护栏覆盖)。qb-discover 保留"失败发现语义"
(sources.py discovery + 失败包解析),消费 shared HTTP 层。

### 4.2 gbs_report fetch/parse 解耦(收口两轮重申的契约冲突)

**问题**:`fetch_gbs_report` 函数体 @72/@88 调 `find_iframe_src`/
`parse_gbs_report_packages`(parse 组)。若整体下沉 shared,则
shared→ci_triage 上行,被 root-layers/forbidden 打红;若按"改返回原
始对象"解耦,则返回契约变更(现 GbsReport 含已解析 packages),
runner/orchestrator 调用点改动超出 import 行,击穿 §5.1 与行为等价。

**裁决(两家一致解法)**:
- shared/quickbuild_http 出 **`fetch_gbs_report_raw`**(纯抓取:取
  page → iframe → 原始 HTML,**不调 parse**,返回原始响应对象);
- `ci_triage.gbs_report` 留一个**薄组合函数** `fetch_gbs_report`
  = `fetch_gbs_report_raw` + `parse_gbs_report_packages`,**字节等价、
  调用点零改动**;它随 report 批次消亡(parse 组届时入 triage-report,
  组合函数改为 skill 内);
- 即:fetch 与 parse **物理解耦**,shared 不含 parse,ci_triage 侧薄
  壳负责组合——L0 不上行,调用点不变,两个铁律都不破。
- parse/render 组(`parse_gbs_report_packages`/`find_iframe_src`/
  `_ReportTableParser` 等 `_*` helper)**留 ci_triage.gbs_report**,
  随 triage-report 批次抽走;`DEFAULT_ARCHES` 仅 orchestrator 消费,
  随 orchestrator 留 ci_triage(不下沉)。

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

见 §1.3。step-0 落 shared-layers + shared-no-uplink + root-layers 三
契约(root-layers 的 skill 层 step-0 为空、各批次填入);目标全集
(skill↛ci_triage、skill↛skill)由 root-layers 一次表达,**不留待
各 skill 批次现场起草**(收口三轮重申)。

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

- **commit ①**:建 tizen_ci_shared 包 + 迁 state/types + **import-linter
  三契约配置落盘**(必须随 ①,否则 ②③ 无 lint 可跑);
- **commit ②**:迁 workspace(双 marker + write_workdir_marker 新建)
  + **classify**(edit_spec **不搬**,随 build-verify,S-2b)+ 反向
  依赖清理(discover_sibling_pythonpath → shared/env);
- **commit ③**:HTTP 件下沉 shared/quickbuild_http(quickbuild.py 17
  符号)+ gbs_report fetch/parse 解耦(§4.2)。

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

- [ ] tizen_ci_shared 独立包建立,三层 + 三契约 lint-imports 绿;
  三条反向验证(§1.3 ①②③)各自转红;
- [ ] 两个 marker 格式常量在 shared 唯一定义(`grep FILENAME =` 仅
  shared 命中,**排除 `release-v1.4.0/` 快照副本**);
- [ ] **S-1 机械验证**:`write_workdir_marker` 落地 +
  `create_worktree` 函数体 grep 无 `FILENAME`(marker 写入已移原语);
- [ ] workspace 函数级归属按 §3.2 落地;discover_sibling_pythonpath
  单点入 symbol_audit 且四消费方一致,全 OK;runner.py 不加全面护栏;
- [ ] **gbs_report fetch/parse 机械解耦验证**:shared 侧
  `fetch_gbs_report_raw` 不含 parse import;ci_triage 薄壳字节等价
  (调用点零改动,§5.1 diff 标准);**DoD 不再写"report 无 qb-discover
  私有 import"(v2 已作废 qb-discover fetch 角色)**;
- [ ] 全量测试 == 基线数、原样全绿;测试 diff 仅 §5.1 两类;每 commit
  lint-imports 绿;
- [ ] parity:build-verify/convergence 关键路径下沉前后归一化相等
  (§5.2 掩码);
- [ ] 三 commit 各自双绿;shim 清单(§6.2)登记待 P4.9 末删除。

---

## 附:方法论账(⑩⑪ + 本稿相关)

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
