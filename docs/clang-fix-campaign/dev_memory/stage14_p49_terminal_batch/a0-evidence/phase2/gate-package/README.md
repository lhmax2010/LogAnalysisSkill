# P4.9 末终止批次第二阶段人工审批包

状态: **READY_FOR_HUMAN_GATE / NOT_APPROVED**。本轮只准备,未删除或改写任何
生产兼容壳,未删除或改写既有测试。请设计方审阅、FatTank 批准清单、拟删
nodeid、分组及 PENDING_REVIEW 的处置后,再启动 C 的第一组。

## 输入与边界

- 权威 F 含勘误11,sha256 `b9d720028164faec8c91d87a02cfa75475e1f8e1fff86e8244a2c0ef55bedaf0`,未修改。
- 采纳 PHASE2-01、step-0 closeout 来源扩展及本轮 PHASE2-02 轻量裁决,
  记录见 progress §35。不新增勘误或改已冻结 predicate。
- 删除清单和调用方复扫读取主分支 **b3e0a95 的 Git tree**,
  不读取未提交/未跟踪草稿。完整 commit/tree 在 JSON 中;
  1973 个 tracked 文件全部扫描,4 个二进制不能作为文本,其余逐项有命中记录。
- OBS-5 在固定 **43a6aa6**,tree `ca9331190e878af465e7968fe56e735585a5866e`
  的干净工作区运行,不将 A/B 后代码冒充改前观测。
- 本审批包是上述输入版本的报告,不自记自身 hash。后续新增文件与每组删除
  后都须重新复扫,不能拿本轮计数代替届时的残留检查。

## 删除清单

[deletion-inventory.json](deletion-inventory.json) 含每项来源 a/b/c、原文位置/
抽取 commit、全部转出名字、最终定义位置与本地 Load 证据。

| 口径 | 数量 |
|---|---:|
| 登记来源中的宿主/绑定 | 14 / 184 |
| 拟清理宿主/绑定 | **13 / 183** |
| 真实本地依赖排除 | 1 |
| def/class 到纯 shim 的登记提交跃迁 | 11 |

`runner.discover_sibling_pythonpath` 已补入:旧址1条 import、0处本地 Load,
规范位置为 `tizen_ci_shared.env`。只拟删此兼容行,不删除 runner 模块。
`quickbuild_log.FailedPackage` 有5处真实本地读取,保留 import,不进入删除集。
skill 副本 Gerrit 三类型 import、新包根公开导出、release 快照也明确排除。

## 调用方与保留项

最终表为 [caller-classification.final.json](caller-classification.final.json)。
计数单位是 **候选 × 名字形态 × 字面出现**;同一行多个绑定或形态可重叠,
不是唯一源码行数。每条记录给出候选、宿主位置、原文与用途。
最终表保留全部命中;不重复入库内容相同的粗分大表。粗分可由留档的
`gate-inventory-exact-key.command.json` 内诊断程序重建,再按逐项review复算。

| 类别 | 命中数 |
|---|---:|
| REWRITE | 18 |
| HISTORICAL | 6806 |
| HISTORICAL_KEY | 3 |
| RELEASE | 108 |
| PENDING_REVIEW | 9 |
| OTHER | 0 |
| 合计 | 6944 |

另有 [caller-structured-supplement.json](caller-structured-supplement.json):
legacy wiring 用例:63 的有限 f-string 由字典明确展开为3个旧模块目标,
全部 REWRITE,在同一个拟删 identity 用例中;不混入字面计数。

[historical-keys.json](historical-keys.json) **逐项**登记 bridge:37/46/55 的
三个 workspace 源三元组,各有用途、固定43a6aa6中step-0冻结表文件、sha256、
行号与保留原因。它们不是 import/patch/入口,不能改成新定义路径。
除此之外没有把整个工具文件/目录认作历史键豁免。

### PENDING_REVIEW 汇总

[pending-review.json](pending-review.json) 共9项,均保留不删除、不改写,
原始可归类别为 REWRITE;下列疑义提交人工决定,不是自动许可残留。

| 宿主 | 用途与待审问题 |
|---|---|
| symbol_audit.py:47 | 96符号旧拓扑锁定的 WORKSPACE 键,是否按历史 fixture 键保留 |
| symbol_audit.py:356 | module-scope 的 legacy_path/pure-shim 检查;删宿主后会违反现存纯 shim 检查,须审批如何转为删除态验证,不能削弱断言 |
| symbol_audit.py:2041 | sources 抽取前的 fallback 定义键,当前分支不使用,保留待审 |
| symbol_audit.py:807 | 旧 build-verify 的 MODULE_OWNERS 键,非 import |
| symbol_audit.py:808 | 旧 submit 的 MODULE_OWNERS 键,非 import |
| symbol_audit.py:1772 | 故意越过 skill root 的负 fixture,直接改路径可能改变反例 |
| symbol_audit.py:2055 | 双键 fixture 的旧 report 定义身份 |
| symbol_audit.py:799 | 旧 report 的 MODULE_OWNERS 键,非 import |
| table_audit_bridge.py:731 | binary-key/name-only 反例的 BodyEntry 旧路径身份 |

这些条目未获处置批准前,相关宿主组不得执行。删除后允许的残留仍仅
HISTORICAL、RELEASE、**已逐项批准登记**的 HISTORICAL_KEY;
PENDING_REVIEW 不是永久免检类别。

## 项2与拟删测试

[item2-scope.final.json](item2-scope.final.json) 为最终范围/处置表;
原始 AST 与复核中间产物一并保留。解析当前受版本控制的68个 tests/ Python
文件,20个仓库私有名直接 import 中,skill-4 强制义务对应4处,均已直取定义
模块,不改。`__version__` 按新裁决明确 OUT_OF_SCOPE_DUNDER。
shared/workspace 包根6个私有函数本就在该 `__init__` 定义;测试对它们的
5处属性读取保留。有限模块名循环也已逐项解析,项2无遗留 PENDING_REVIEW。
新增的入口枚举测试文件不导入任何生产私有件,其3个用例全部保留。

[skill4-patch-obligation.json](skill4-patch-obligation.json) 附冻结义务相关
对象式 patch 的实际目标/函数名/源码,继续 patch 定义模块,不改行为测试。

[proposed-test-deletions.json](proposed-test-deletions.json) 含完整函数体、
位置、source sha256、身份断言数量及理由。仅以下4个 nodeid 提请删除:

| 文件(均在 tests/unit/) | 函数 | 理由 |
|---|---|---|
| test_gerrit_fetch.py | test_legacy_module_reexports_implementation_and_types_by_identity | 只检查旧址12实现件及3类型的同一性 |
| test_build_verify_legacy_wiring.py | test_legacy_shims_preserve_all_migrated_symbol_identities | 只检查三个旧模块及shared转出的同一性 |
| test_tizen_gerrit_submit.py | test_legacy_shim_preserves_all_symbol_identities | 只检查旧址23符号同一性 |
| test_tizen_triage_report.py | test_triage_report_legacy_shims_preserve_all_symbol_identities | 只检查gbs/report两旧模块的同一性 |

完整 nodeid 在 JSON 中逐个列出,本轮四个均仍在且 PASS。不删除其所在文件
中的其它用例;convergence 公共别名 identity、路径锚等价测试、版本接口测试
都是实际契约,不属于以上删除许可。

## C 分组与顺序

[commit-groups.json](commit-groups.json) 每组给出宿主、绑定数、调用方、
拟删 nodeid 和五项验收。旧址均相对 `ci_triage/`:

| 组 | 宿主 | 绑定数 | 组内拟删用例 |
|---|---|---:|---|
| C01 | verify/__init__.py | 16 | 无;只去登记转出,保留包 |
| C02 | quickbuild.py | 17 | 无;翻转 test_ci_triage 的HTTP import |
| C03 | runner.py | 1 | 无;只去 discover 兼容行 |
| C04 | gerrit.py | 15 | gerrit-fetch identity |
| C05 | sources.py | 4 | 无 |
| C06 | verify/convergence.py | 8 | 无 |
| C07 | verify/build_verify.py | 29 | build-verify 跨三宿主 identity |
| C08 | verify/edit_spec_guard.py | 12 | 其 identity 已在 C07 经批准去除 |
| C09 | verify/workspace.py | 21 | 同上;历史表键保留 |
| C10 | verify/failure_classify.py | 13 | 无;先决:审批 pure-shim guard 转档方案 |
| C11 | verify/gerrit_submit.py | 23 | submit identity |
| C12 | gbs_report.py | 21 | triage-report 跨两宿主 identity |
| C13 | report.py | 3 | 其 identity 已在 C12 经批准去除 |

这是计划,不是已执行记录。C01 先处理 verify 包旧转出,避免后续删除
failure_classify 宿主时留下该包的旧 import。跨宿主 identity 用例仅在首个
相关组按批准的完整 nodeid 去除一次。每组原子完成调用方改写与壳删除,
无中间断裂态;每组均执行 E11-3(4) 五项删除后验证,任一失败回退该组并停报。

## OBS-5 与验证

独立全集: [B-5-entries.json](../../B-5-entries.json),由固定树打包描述、
tracked `__main__.py` 与全部14份 SKILL.md 入口命令枚举。
31个入口:10个 PACKAGE_MAIN、21个 SKILL_MD_COMMAND、0个 console script;
live 16、release 15。重复文档位置合并入口但保留全部引用位置。
外部 git/gbs 是被调用程序,不是本仓库入口;不执行它们。命令冒烟保留仓库
launcher/模块/具名子命令,用 `--help` 替换会执行实际操作的参数。

产出与日志:

- [obs5/raw.json](obs5/raw.json): 各次 argv、隔离 PYTHONPATH、stdout/stderr、exit。
- [obs5/output.json](obs5/output.json): 仅 claim 原始事实,没有判定字段。
- [../gate-obs5-verifier.log](../gate-obs5-verifier.log): 冻结 verifier 的 PASS。
- 所有 `../gate-*.command.json` 保存完整argv/env/hash与诊断程序,相邻 `.log`
  保存原始输出;没有覆盖旧OBS。

```text
INDEPENDENT_ENUMERATION entries=31 sha256=9a9d8d1f7131776525ee09832b7c85c8bd5a9fe1179db485d9a222ed90059bfe
FACTS_WRITTEN claim=OBS-5.entry-consumers entries=31
[{"claim_id": "OBS-5.entry-consumers", "verdict": "PASS"}]
EXIT=0

pytest tests/unit/test_terminal_entry_observation.py -vv -p no:cacheprovider
3 passed; EXIT=0
pytest tests -vv -p no:cacheprovider
1343 passed, 1 skipped in 25.55s; EXIT=0
NODEIDS old=1341 current=1344 lost=0 status_changes=0 added=3
mypy: Success: no issues found in 88 source files; EXIT=0
mypy new producer: Success: no issues found in 1 source file; EXIT=0
ruff tools/tests: All checks passed!; EXIT=0
lint-imports: Contracts: 6 kept, 0 broken.; EXIT=0
py_compile OK; EXIT=0
```

[regression-set-proof.full.json](regression-set-proof.full.json) 含逐nodeid状态;
完整保留参数ID中的空格。早期诊断以 `\S+` 提取造成计数遗漏,已以整行解析
更正并对pytest汇总核验;不可使用旧诊断日志中的1258/1261部分计数。
同理,早期来源表子串匹配、identity 的 all(generator) 识别及ruff行宽问题
均在本轮程序调试中更正,原始失败日志保留,最终证据使用 exact-key、identity、
nodeid-complete、ruff-final 后缀版本。没有改冻结判据或 OBS 事实使其通过。

本轮新增停止项 **0**;待人工处置条目9。到此停止,等待人工闸门审批。

提交前再次全仓复跑:`gate-full-final.log` 为 **1343 passed, 1 skipped in
25.57s**,exit0。`gate-integrity.log` 核对119个生产文件与回归副本逐字节一致,
既有测试零diff、固定观测树clean、冻结hash不变、清单/归类/分组计数一致,
且OBS-5产出记录的producer hash与本次提交脚本一致,exit0。
