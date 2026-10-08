# P4.9 末终止批次收口材料

日期: 2026-10-08。状态: **READY_FOR_REVIEW**。
五项实现义务已逐项验收,本文件提交设计方核验与一家评审,不代签 CLOSED。
D 是文档与证据归档提交,完整性由所在 Git commit 外部锚定,不自记 SHA。

## 1. 权威、批准与边界

- 权威为 `p49-terminal-batch-design-v1.31-FROZEN.md` 含勘误1-11,
  SHA-256 `b9d720028164faec8c91d87a02cfa75475e1f8e1fff86e8244a2c0ef55bedaf0`。
- 实施按E11两阶段及后续PHASE1/PHASE2轻量裁决;当前采用PHASE2-09。
  E11已取代旧静态全树发现/SEAL作为删除前置的方案,不是宣称旧引擎全部完成。
  未运行的旧OBS和未完成的旧控制不补造PASS;原始停止记录仍在progress。
- 人工审批包固定为 `74ff34c102761df202beb72280b41d40844ec557`:
  13宿主/183绑定、4个拟删完整nodeid、C01-C13顺序均获FatTank原样批准。
  9个PENDING_REVIEW的批准处置为8项逐条HISTORICAL_KEY及1项获批删除态护栏;
  没有按目录豁免。原负fixture保留,新增护栏不改变归属或集合等价判据。
- 本文相对路径 `E` 指
  `../dev_memory/stage14_p49_terminal_batch/a0-evidence/`, `X` 指其
  `phase2/execution/`;各目录的 `*.command.json` 含完整命令、cwd、环境、
  HEAD/tree、exit、原始输出SHA及临时诊断程序源码,同名 `.log` 为原始输出。
  `residual.log.gz` 无损压缩,解压SHA与command.json一致。

## 2. 五项义务销账

VERIFIED表示实现验收证据齐,不等于待办签批已完成。

| 冻结义务 | 结论 | 证据锚点 | 实测摘录 / 边界 |
|---|---|---|---|
| §1 兼容壳分类及删除 | VERIFIED | 审批包`deletion-inventory.json`/`caller-classification.final.json`; C01-C13; `X/C13R/final-proof.log` | hosts=13 / bindings=183;批准11个整模块删除,2宿主仅删绑定;真实依赖保留;OTHER=0 |
| §2 测试私有消费面收窄 | VERIFIED | 审批包`item2-scope.final.json`/`skill4-patch-obligation.json`/`proposed-test-deletions.json`; `X/C13R/nodeids.log` | old=1352 / current=1350 / lost=4 / changed={} / added=2;只删批准identity测试,其余行为函数未改 |
| §3 悬空symlink归一化 | VERIFIED | B `c1ea4ef`; `E/phase1/commit-b/after-b.log`, `after/comparison.json` | AFTER=PASS phase=FULL scenarios=30;悬空改为SOURCE_DIR_UNSAFE,相邻输入与未登记字段精确相等 |
| §4 timeout/cancellation六调用面 | VERIFIED | A `5213c5d`; `E/phase1/commit-a/after-a.log`; B完整比较; `f65949f`更新SKILL文档 | A按来源投影,项4差异全部兑现;B完整登记比较通过;中断传播/残留不自动清理 |
| §5 protected marker顺序显式裁决 | VERIFIED | F §5决策B; B `c1ea4ef`; `E/phase1/prompt-rulings/item5-verifier.log`; `E/phase1/commit-b/targeted.log` | item5 PASS;维持verify→exclude→write,两中断失败态测试通过;marker状态/原字节/reader结果未登记变化 |

项1不是删除所有名字相同的import:有5处本地读取的
`ci_triage/quickbuild_log.py`中`FailedPackage`是真实依赖;skill gerrit三类型
import也是签名依赖,均原字节保留。共享包公开面、skill公开面、release快照不删。
项2已排除dunder;定义就在包根的私有名从该包根取用等于从定义模块取用。
skill-4四处对象式patch仍指向定义模块,无需为删除兼容壳改写行为测试。

项5选择维持现状的理由仍按F §5:exclude未完成时先写protected marker会将
不完整状态标为已保护,不在本批引入这种行为。保留顺序的风险被失败态测试和
既有读取方观测显式锁定,不是留给后续批次再裁决。五项无新增DEFERRED。
`EDIT_SPEC_SCHEMA`仍属patch-suggest;BoolOp逐操作数是模板议题,不混入末批五项。

## 3. 第一阶段真实双跑

固定改前树为`43a6aa625f27da46daba190657bf62256080c68e`,
tree=`ca9331190e878af465e7968fe56e735585a5866e`。OBS item3/item4沿用原始产出,
item5由专用AST枚举器取live且tests外的四个函数:
`clean_repository_preserving_markers`、`release_worktree_protection`、
`is_protected`、`_exclude_private_files`。两个中断现场各对每个reader使用
独立worktree副本,不共享现场;冻结verifier判PASS。

| 阶段 | 原始输出 / hash | 验收 |
|---|---|---|
| 改前 | `E/phase1/prompt-rulings/before-run-verified.log`; `before-verified/before.json` SHA `a0eb4b107bbb7401a9ab3bf0e8dd29267a40e0386d582c049952d30352dfc133` | `BEFORE=PASS scenarios=30`, exit0;封闭schema、登记旧值、item3/item4/item5一致 |
| A项4 | `E/phase1/commit-a/after-a.log`; `after/after.json` SHA `828f4df93cd5b9cbddf59f429168f2d92c6413240ef3bb9b471f74c5486bbb6a` | `AFTER=PASS phase=A scenarios=30`, exit0;来源为§3/E2-1的三字段仍须等于旧值 |
| B项3+项5 | `E/phase1/commit-b/after-b.log`; `after/after.json` SHA `adef6922978fe5e63f99bbcad411e542e6cac28d6f5364447490648d3013ad71` | `AFTER=PASS phase=FULL scenarios=30`, exit0;excluded=[] |

A投影由登记来源机械筛出,不是按实际差异筛选;`item3-projection.json`逐项
列场景/字段/来源。提前改变项3字段和漏改项4的控制各exit1,正常对照exit0。
六超时场景改前按E3在相同调用点注入TimeoutExpired而不传timeout;改后
fetch/submit-git的message仍等于str(exc),shared加具名前缀,remote转固定warning。
每一timeout kwarg按调用单独登记,无全局掩码、前缀比较或忽略字段。

当前结构为30场景、30 DIFF_SET、0 NO_DIFF、53条登记。两marker中断场景
也有E2-2的timeout kwarg差异,但marker存在状态、原字节sha256和reader结果
保持精确相等。早期progress“项5两场景NO_DIFF”的简称只适用于这些失败态
字段,不应误读为整个场景模式。结构CLI旧提示`REAL_BEFORE=PENDING_SEG3`
没有读取真实双跑结果,不能覆盖本节已经完成的采集证据。

## 4. C01-C13逐组记录

每组在自身commit的干净worktree中验证,原始证据位于`X/<证据>/`。每行均
完成E11-3(4):全仓/静态检查/90 checker无新增失败;31入口;import-all;
名字复扫OTHER=0;wheel构建、新venv安装及5个已安装模块入口help。

| 组 | commit | 旧ci_triage宿主 | pytest passed / skipped | import-all | 证据 |
|---|---|---|---|---|---|
| C01 | `f8a289a` | verify/__init__.py | 1351 / 1 | 213 | C01R |
| C02 | `1c42957` | quickbuild.py | 1351 / 1 | 212 | C02R |
| C03 | `ac26333` | runner.py中的discover转出 | 1351 / 1 | 212 | C03R |
| C04 | `99add0d` | gerrit.py | 1350 / 1 | 211 | C04R |
| C05 | `d8e8d85` | sources.py | 1350 / 1 | 210 | C05R |
| C06 | `b54e749` | verify/convergence.py | 1350 / 1 | 209 | C06R |
| C07 | `f962093` | verify/build_verify.py | 1349 / 1 | 207 | C07R |
| C08 | `9da38e6` | verify/edit_spec_guard.py | 1349 / 1 | 206 | C08R |
| C09 | `0e6507e` | verify/workspace.py | 1349 / 1 | 205 | C09R |
| C10 | `1282005` | verify/failure_classify.py | 1351 / 1 | 205 | C10S |
| C11 | `b2ec945` | verify/gerrit_submit.py | 1350 / 1 | 204 | C11R |
| C12 | `8aed0b8` | gbs_report.py | 1349 / 1 | 203 | C12R |
| C13 | `de9099e` | report.py | 1349 / 1 | 202 | C13R |

完整SHA及逐组输出hash闭合见`X/C13R/final-proof.log`。最终生产diff精确
等于批准的13宿主;其它生产实现不动。release和P4.5设计零diff。

### PHASE2-09失败与修复

C10首次`6e27fec`的新增fixture变量`spec/result`与同函数其它分支类型冲突,
定向mypy报5错;按当时规则`63e9a77`回退。原文
`X/C10R/mypy-deletion-guard.log`保留,不改基线来放行。
裁决批准后仅将新分支改用`module_spec/module_result`,修正diff见
`X/C10S/fixture-fix-diff.log`;`controls-unchanged.log`空输出exit0。
`_approved_legacy_deletion`源码与两参数化测试字节均与首次C10一致。

```text
symbol_audit.py --negative-fixture unapproved-deleted-shim
EXIT=1: not an approved deletion
symbol_audit.py --negative-fixture legacy-shim-residual-implementation
EXIT=1: non-re-export FunctionDef
mypy docs/clang-fix-campaign/tools/symbol_audit.py
Success: no issues found in 1 source file
EXIT=0
```

错误文本为完整日志的摘录。新增常设规则只允许工具/测试自身类型、lint、
格式错误组内修复,须保留失败、修正diff及重跑;删除/调用方引起的失败仍回退。

## 5. 最终验收与遗留

C13干净环境Python3.12.3,pytest9.1.1,mypy2.4.0,ruff0.16.10,
import-linter2.3。PYTHONPATH由该worktree的scripts根派生,MYPYPATH未设置;
pytest禁自动加载插件,显式加载pytest_cov。完整值见command.json,不以主树
未跟踪草稿或用户既有改动参与测试。

| 命令/执行项 | exit | 原始输出摘录 / 证据 |
|---|---|---|
| `python -m pytest tests/ -v -p pytest_cov --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80` | 0 | `1349 passed, 1 skipped in 29.75s`; C13R/full-tests.log |
| 逐nodeid比对HASH08 | 0 | base1352/current1350/lost4/changed{}/added2; C13R/nodeids.log |
| `mypy`及audit定向mypy | 0 / 0 | `Success: no issues found in 103 source files` / 1 source file |
| `ruff check .` | 0 | `All checks passed!` |
| `lint-imports` | 0 | `Contracts: 6 kept, 0 broken.` |
| 90 checker原命令矩阵 | 0(比较器) | 87符合各自预期exit,3既有不符,`regressions=[]`; C13R/checkers/commands.json |
| `symbol_audit.py` | 0 | `198 SYMBOL OK; 4 MODULE-SCOPE OK (48 SYMBOLS COVERED); 0 MISMATCH; 0 INCOMPLETE` |
| `table_audit_bridge.py` | 0 | `198 SYMBOL OK; 4 MODULE-SCOPE OK;`全部差异0 |
| 31入口独立冒烟 | 0 | `SMOKE entries=31 passed=31`; C13R/entry-smoke.log |
| tracked live文件逐一新进程import | 0 | `IMPORT_ALL modules=202 passed=202`; C13R/import-all.log |
| 全tracked文本四名字形态复扫 | 0 | `RESIDUAL hits=24788 OTHER=0`; C13R/residual.log.gz |
| wheel / fresh-venv install / installed help | 0 | `PACKAGING wheel=OK install=OK console_scripts=0 installed_module_entries=5` |
| 不可变输入/批准集合/全部组证据核对 | 0 | `FINAL_PROOF=PASS`; C13R/final-proof.log |

31入口沿用改前OBS-5独立全集(10 PACKAGE_MAIN、21 SKILL_MD_COMMAND),
live/release隔离路径;不是重跑新的OBS producer。打包描述没有console_scripts,
明确记录0而不伪造入口。安装后5个包主入口在无PYTHONPATH/MYPYPATH下执行help。

仅以下4个获批nodeid消失,都在首个相关组删一次:

- C04: `tests/unit/test_gerrit_fetch.py::test_legacy_module_reexports_implementation_and_types_by_identity`
- C07: `tests/unit/test_build_verify_legacy_wiring.py::test_legacy_shims_preserve_all_migrated_symbol_identities`
- C11: `tests/unit/test_tizen_gerrit_submit.py::test_legacy_shim_preserves_all_symbol_identities`
- C12: `tests/unit/test_tizen_triage_report.py::test_triage_report_legacy_shims_preserve_all_symbol_identities`

其它既有测试函数AST在只归一批准HTTP import路径后不变,不是只看总数。
新增2例均为`test_approved_shim_deletions.py`护栏反向控制,故1351-4+2=1349。
现有skip保持,没有新skip。失败C10的日志和回退历史未删除。

最终残留分类为HISTORICAL=24671、HISTORICAL_KEY=12、RELEASE=105,
REWRITE/PENDING_REVIEW/OTHER均无。计数单位是候选×名字形态×字面出现,
不是唯一源码行;随历史证据增长增加不代表新增运行时依赖。
12个历史键分别列在`X/historical-keys.approved.json`,包含用途、不可变输入、
hash与保留理由;没有将整个工具目录作为豁免。

### 仍明确保留的基线问题

[遗留清单](../dev_memory/stage14_p49_terminal_batch/carried-over-issues.md)
列20条固定树不符项,17条当前已符合预期,3条OPEN_CARRIED:
design-doc self-test缺未跟踪历史样本、duplicate-spec-root-mismatch反例红因
未成立、twin-both-binary-key旧定义缺失。当前exit分别1/0/1,固定树亦1/0/1;
期望分别0/1/0。它们不冒称绿,原断言不改;按PHASE2-04基线裁决不阻塞末批。

历史工具按PHASE2-08从完整Git历史查找精确(path,sha256),不指定任意closeout
提交、不从当前扫描反推计数。`X/HASH08/history-proof.log`列34个历史输入,
skill-4 v1.12语料自然定位,错hash/不存在路径各红。skill-5 target保持
`0e2de5ff80c7f36940e455ec75f4f6872caa4fd93be360ad0fcfd0e59c755f27`;
当前新类型补册仍由symbol/bridge读当前稿核验。CI checkout完整历史不变。

## 6. 复现导航与停点

从完整Git历史checkout对应组SHA,用该组command.json记录的依赖版本和
scripts根环境执行其argv;90条命令全集在`C13R/checkers/commands.json`。
临时诊断器源码包含在相邻command.json中,可审阅并在独立worktree复跑;
涉及历史路径/证据根时按记录恢复,不要用当前dirty主树替代测量输入。
生成/覆写OBS、改predicate、改冻结稿都不属于复核步骤。

本轮四组远端CI URL及结果随`C10S/C11R/C12R/C13R/remote-ci.log`归档,
最新实现提交为`de9099e`;Tests、Lint、Type check须均成功才交付本材料。
D只提交本closeout、进度/索引/总账/遗留表及最后一组证据。

| 组 | CI run | 实测结果 |
|---|---|---|
| C10 | https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37716799906 | SUCCESS; Tests/Lint/Type check success |
| C11 | https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37717036201 | SUCCESS; Tests/Lint/Type check success |
| C12 | https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37717284067 | SUCCESS; Tests/Lint/Type check success |
| C13 | https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37717635505 | SUCCESS; Tests/Lint/Type check success |

请设计方核验并请一家评审确认:五项义务是否闭合、获批删除范围及真实依赖
保护是否充分、基线遗留是否按批准规则列明。无异议后再登记最终签批。
**本轮停在此处,不自行签批、不新增延期、不启动下一阶段。**
