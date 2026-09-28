# P4.9 末终止批次进度与实施前复述

状态: A0_PART1_BLOCKED_V11。更新日期: 2026-09-28。
2026-09-27 完成冻结稿入库与实施前复述;2026-09-28 接收 predicate 来源并建立
干净工作区。原三项停止问题已由判定条件v1.1关闭(第9.3节),v1.1取代v1.0
作为编码来源;新发现两项编码阻塞(第10节)。未运行任何 OBS producer,
未编写 verifier/测试,未采集 B-0;生产实现未开始。
后续每个 commit 必须同步本文件的进度、证据、人工输入前提与挂账。

## 0. 权威、输入与记录边界

- 唯一批次权威: `../../p49-terminal-batch-design-v1.31-FROZEN.md`。
  下文 `F:Lx` 指该文件原始行号;节号和条款正文优先,行号仅帮助定位。
- FatTank 已批准冻结。本记录是执行计划,不增加、替换或修正冻结裁决。
  遇矛盾/无法执行时保留中间态,报告原文位置、事实与候选处理方式;
  由设计方出勘误、FatTank 批准,实现方不自行改变判据。
- 收到的交付文件已位于目标路径,当时未被 Git 跟踪。本次直接入库该字节串,
  不重新排版、不改标题、不生成另一个修改版。输入 SHA-256:
  `66fd8684950004524ae7d86fb4e29328a1998ba48985a944ad39ae4d03a8598c`。
  该值记录在本文件,不写回被哈希的冻结稿;提交时另比对 index blob。
- 同目录旧 `p49-terminal-batch-design-*-draft.md` 全部保留原样。
  既有 `.gitignore` 修改、无关文档删除及未跟踪草稿不纳入本提交。
- 并行有效的前批权威按冻结稿开头所列版本核对;不得拿历史草稿替代。
- 本轮只做阅读与入库检查。A₀ 基线及 OBS 事实必须重新由脚本产出,
  不沿用聊天数字,不把以下计划写成已通过的验收结果。

### 已闭合的本步事实

| 项 | 命令/证据 | 结果与边界 |
|---|---|---|
| 分支与同步 | `git status --short --branch`; `git pull --ff-only origin clang-fix-campaign` | 当前为 `clang-fix-campaign`; pull 输出 `Already up to date.` |
| 开工前 Git 锚 | `git rev-parse HEAD HEAD^{tree}` | HEAD `53e1bad73fa5df06b34e601abdb82f1d1e7c6328`; tree `2155aa3f2dcfa1079eaeb28057befe6376848872` |
| 交付文件原始指纹 | `sha256sum docs/clang-fix-campaign/p49-terminal-batch-design-v1.31-FROZEN.md` | 等于上列输入 SHA;本轮以已位于目标路径的交付原件为输入,未取得独立附件副本 |
| 阅读范围 | F §0–§8、附录 A/B;skill-5 v1.3.2 §3.2;当前 gerrit-fetch/workspace 对应函数 | 已用于下述复述与取证计划;尚未生成 `OBS-1.*` 或通过 SEAL |

## 1. 本批目标与验收复述(任务 3a)

### 项 1:兼容位置分类与清理(F §1)

目标是关闭真实的旧址兼容义务,同时保留真实依赖。台账与当前树扫描是两个
独立来源:三段台账保持各来源声明的粒度,扫描覆盖完整 tracked tree 和四级
候选,两者做 reconciliation;不能用当前扫描结果反向制造台账分母。

先由本模块/词法作用域的 Load 求 A、前批具名保护裁决求 B,再取得一个处置:
①零消费者直接删;②仅纯接线测试,处理测试后删;③真实消费者迁移后删;
④保留依赖并私有化绑定;⑤保留真实依赖,只移除错误 shim 标记。
`#MODULE`/`#PROXY` 的 A 固定为否;binding 才按 Load 求 A。
④必须先闭合并处理外部消费者:行为测试迁移保留,纯接线测试按 §2 处置;
私有名冲突不能临时另取名。⑤不迁消费者、不删导出。

验收不能只看删除后的扫描计数:⑤去掉注释后会从结构扫描消失。
必须以 SEAL-9 冻结的 inventory、hash 和逐 candidate 证据包为分母,
通过 §1.3 分区/清零/一致性/检出与判定四项,再按登记顺序执行。
误删真实依赖须回退;①②按 shim 模块分组提交。删除后验证见第 6 节。

### 项 2:测试私有消费收窄(F §2)

目标是让行为测试跟随真实契约,关闭仅为旧 shim 接线服务的测试。
使用与项 1 相同的消费者解析引擎,递归穿透 helper、fixture、参数化回调和
assertion wrapper,不能用测试文件名或一个顶层 assert 判断整组测试可删。
所有叶子在实际调用形态下都是 IDENTITY/EXISTENCE 才归 (a) 并随 shim 删;
任一 BEHAVIOR 归 (b),保留并迁到公开面或同包测试;(c) 不可闭合/语义不明
进入 `UNRESOLVED_DISPOSITION`,不能人为写成“接线测试”。

验收包括现存漏检样本逐个命中、样本集非空、(c) 类投影、白名单逐形态证伪,
以及被删测试与三分表逐项闭合。允许总数变化,但每项增减都须给替代或理由;
pytest 总数增长不能抵消某个行为测试被误删。

### 项 3:悬空 symlink 归一化(F §3)

目标是让源目录安全检查也拒绝悬空 symlink,进入 `SOURCE_DIR_UNSAFE`。
旧异常路径与旧 code 是否缺省由 `OBS-1.item3-predicate` 采集,不手填。
该输入登记 `DIFF_SET`;相邻非悬空输入登记 `NO_DIFF`,其它输出保持。
ANCHOR-3 用函数内存在性/符号链接判定的布尔合取式定位,不靠旧行号。
实现后须同步 skill-3 的现状描述,以本次批准的行为变更留痕。

### 项 4:timeout/cancellation 统一(F §4)

目标是逐调用面兑现 skill-5 v1.3.2 §3.2 的既定映射,不是重新设计它。
覆盖 fetch query、fetch git、submit `_run_git`、submit `ls-remote`、shared
`_run_git`、shared `_exclude_private_files`。统一可选 `timeout: float | None`,
默认 None;SIGINT/SIGTERM 不捕获,磁盘残留不自动回滚。
fetch 使用 `GerritError("FETCH_TIMEOUT", message)`;submit git 新建同形
`GerritSubmitError("GIT_TIMEOUT", message)`;ls-remote 保持 warning 路径,
码为 `target_head_unknown:timeout`;shared 保持 `WorkspaceViolation` 签名,
message 用 `GIT_TIMEOUT:` 前缀。

每个调用面分别验默认 None parity、显式 timeout 超时映射及磁盘残留、外部
中断传播。默认轨迹唯一允许的新增项是 `timeout=None` kwarg,须预先声明。
不能只测 wrapper 而漏 query/ls-remote/独立 subprocess 调用。

### 项 5:protected marker 顺序(F §5)

本稿已选择 B:保持 verify → exclude → 写 protected marker,不再作“待选 A/B”
处理。它关闭的是顺序议题,没有授权改变生产顺序。exclude 中断时 marker
尚未生成;marker 写入中断时可能不存在或不完整,读取方语义保持现状。
这两处须分别做失败态测试并登记 `NO_DIFF`;不能把未跑的失败态当作已证事实。
除用户要求的 fetch 残留复核外,还须经 `OBS-1.item4-anchors` 核对映射表最后
一行,并由 `OBS-1.item5-order` 采集写入序与不完整 marker 的真实读取结果。

### §6:预期差异门禁

固定 fixture 双跑得到结构化结果。A₀ 先冻结场景集和封闭结果 schema,
再用机器表逐场景登记模式,以“实际差异精确等于登记差异”判定,不能用子集。
`NO_DIFF` 必须有非空 reason 且禁止 differences 字段;
`DIFF_SET` 的 differences 必须非空,每个 JSON Pointer 登记旧值/新值/理由。
不存在用 `{state: ABSENT}`,有值用 `{state: VALUE, value: ...}`,不与 null 混同。

场景至少含 symlink/相邻对照、§4 每面的默认/超时/中断和 §5 两时点。
schema 覆盖返回值、异常 type/code/message、warnings/action、调用参数、
destination/worktree/workdir marker 状态、exclude 完成状态,以及 protected
marker 的存在、原字节 hash、既有读取方结果。缺场景、缺字段、未声明字段、
模式非法、空理由、未登记差异或登记差异未发生均红。七条准入证伪须各自实跑,
与 RC-1、detector 控制、golden 分开计数。

## 2. A₀ 交付清单(任务 3b,以下均未实施)

### 2.1 路径约定

为使计划可执行,以下前缀是精确的仓库相对路径缩写;`T/x` 表示在 T 下的 x。
这些是拟产出路径,本提交不创建脚本、JSON、fixture 或测试文件。
若实现时必须拆文件,先更新本表与证据索引,不能因此减少义务。

| 前缀 | 路径 |
|---|---|
| T | `docs/clang-fix-campaign/tools` |
| D | `docs/clang-fix-campaign/tools/p49_terminal_data` |
| E | `docs/clang-fix-campaign/dev_memory/stage14_p49_terminal_batch/a0-evidence` |
| U | `tests/unit` |
| X | `tests/fixtures/p49_terminal_batch` |

附录 B 的各节是对应产物的 schema/claim 权威;原始输出、输入 hash、命令、
exit code 按 B 编号在 E 留档。本计划不往不可改动的冻结稿填实测值。
predicate 原件与机器产物分离;renderer 旁注由机器产生,不手写等价句。

### 2.2 §7 A₀ 与 DoD 的交付映射

| ID | 设计出处 | 拟产出(脚本/数据/测试/证据) | 验收方式 |
|---|---|---|---|
| A00 | §7;B-0 | `E/B-0-baseline.txt`, `E/B-0-nodeids.json`;既有 pytest/mypy/ruff 命令 | 记录本次固定快照的命令、环境、exit、逐 nodeid 基线;收口逐项说明增减,不抄旧总数 |
| A01 | §6;§7 A₀ | `T/expected_diff_gate.py`;`D/scenario_manifest.json`, `D/result_schema.json`, `D/expected_diff.json`;`U/test_terminal_expected_diff.py`;`E/expected-diff/` | 封闭 schema、JSON Pointer、两模式与精确相等;七条准入逐条红,正常对照绿;baseline/after 载荷分存 |
| A02 | §2;B-7 | `T/private_consumption.py`;`E/private_consumption.json`;`U/test_terminal_private_consumption.py`;`X/private_consumption/` | 共用消费者引擎;现存漏检样本非空且全命中;闭合调用图三分、(c) 投影与逐测试去向 |
| A03 | §1.1e 12b-1/2/3b/5/6;B-8 | `T/terminal_scan.py`;`E/scan_manifest.json`, `E/scan_matrix.json`, `E/completion.json`;`U/test_terminal_scan.py` | 完整固定 Git tree + mode/lstat,处理集精确相等,每 entry 有 SCANNED;原子完成标记、tree/run ID/hash 一致,不按目录或文档清单缩面 |
| A04 | §1.1b;12b-3/3c/8 | `D/provider_registry.json`, `D/capability_registry.json`, `D/non_shim_predictions.json`;`T/terminal_scan.py`;`U/test_terminal_scan.py` | provider/kind 全函数、四条完备性、四态逐格记录;未知/FAILED/UNSUPPORTED 阻塞;预测不免 candidacy/行级下界/reconciliation;终态证伪钩不可提前 |
| A05 | §1.1 三段;§1.1b;B-2/B-3 | `T/shim_inventory.py`;`D/ledger_sources.json`;`E/ledger_inventory.json`, `E/B-2-sources.json`, `E/B-3-transitions.json`;`U/test_terminal_shim_inventory.py` | 三段保持来源粒度;七来源覆盖;四 provenance 字段与真实抽取 SHA;不按提交序位猜,不由当前树展开来源 |
| A06 | §1.1/1.1c;B-9 | `T/terminal_scan.py`, `T/shim_inventory.py`;`E/raw_findings.json`, `E/B-9-shapes.json`;`X/candidates/`;`U/test_terminal_shim_inventory.py` | MODULE/REEXPORT/INLINE/PROXY 全扫,A/B/D 与代理各种 callable;零命中显式记录;ID 无行号,span 带 guard,all/import 同删同留 |
| A07 | §1.1c-0;SEAL-2/7/7b/11 | `T/shim_inventory.py`;`E/normalization.json`;`U/test_terminal_normalization.py`;`X/normalization/` | N1 guard 归并、π 最细优先全函数、最多一个 primary;covers 与 primary 分离;独立不变式、七格、E1–E12、R1–R7/非法组合、独立 lstat 存在性 |
| A08 | §1.1c-0 时序出口;§1.1c;B-14a | `T/terminal_scan.py`, `T/shim_inventory.py`;`E/dynamic_span_universe.json`, `E/admission.json`, `E/B-14a-resolution.json`;`U/test_terminal_normalization.py` | 独立 raw-syntax/config universe 冻结;严格单调/有界;新 site 不在 universe 则 UNSUPPORTED+整轮重启;admission A/B/C 后才求 SEAL-3,祖先 fallback 取得终态 |
| A09 | §1.1 原子表;SEAL-16b | `T/terminal_consumers.py`;`D/consumer_closure_registry.json`;`E/consumer_callsites.json`, `E/consumer_closure.json`;`U/test_terminal_consumers.py`;`X/consumers/` | 表/registry/closure/控制/实际参与点五方按(形态,consumer.branch)精确对账,保留投影原记录;零/多命中阻塞;详见 2.3 |
| A10 | §1.1a;SEAL-13 | `T/terminal_scan.py`;`E/resolution_layer.json`;`U/test_terminal_scan.py`;`X/resolution/` | 五类解析层全扫;存在性遮蔽与解析未决分别记录;DYNAMIC_UNRESOLVED 六字段销账,不能写理由直接改 resolved |
| A11 | §1.1d 叶子/guard;§2;B-10 | `T/private_consumption.py`;`D/trusted_leaves.json`, `D/decorators.json`;`E/B-10-whitelists.json`;`U/test_terminal_private_consumption.py` | callable×实参形态键,实际 leaf sites 不交并;每个登记形态独立语义控制与 hash;try/except 八谓词;白名单只关闭调用图,不直接授权删除 |
| A12 | §1.1d/e;§1.3;§7 DoD | `T/shim_inventory.py`;`D/seal_rules.json`;`E/seal_results.json`, `E/effective_inventory.json`, `E/B-15-disposition_evidence.json`;`U/test_terminal_seal.py` | 六阶段偏序、同阶段无循环,全 SEAL/12b、§1.3 四断言;完整事实再分类;SEAL-9 比 preseal 并冻结证据;详见 2.4 |
| A13 | 12b-10/11/12;§7 机制;B-11 | `D/control_catalog.json`, `D/golden_cases.json`;`X/controls/`;`U/test_terminal_controls.py`;`E/B-11-controls.json` | capability 机械导出目录,精确 findings/near-miss;外部答案的四元 golden;非 consumer 四方对账与 consumer 五方分开;全部控制见第 3 节 |
| A14 | §8-2;SEAL-15/16 | `T/terminal_claims.py`;`D/claims.json`, `D/measurement_exemptions.json`, `D/predicates.json`;`E/claim_results.json`, `E/claim_generated.md`;`U/test_terminal_claims.py` | 默认 ASSERTION/空豁免;producer 原始事实与 verifier 分离;predicate 首跑前授权冻结;引用精确覆盖、逐句纪律、renderer_version/round-trip 与全部型别控制 |
| A15 | §0/3/4/5;B-1/B-4 | `T/verify_anchors.py`;`D/anchor_selectors.json`;`E/B-1-anchors.json`, `E/B-4-owner.json`;`U/test_terminal_anchors.py` | OBS-1 五键全部实跑、ANCHOR-3/4/5 用机械 selector,实际函数/签名/调用序与磁盘证据;SEAL-14;详见第 4 节 |
| A16 | §1.1a;B-5/B-12 | `T/terminal_runtime_anchor.py`;`D/runtime_entries.json`;`X/runtime/`;`U/test_terminal_runtime_anchor.py`;`E/B-5-entries.json`, `E/B-12-runtime.json` | 新解释器导入前装钩子,覆盖继承安装机制的子进程;独立全部文档入口 smoke;RC-1/a/b/c 精确 sentinel/child pid/父侧零事件;不得用 PYTHONSTARTUP |
| A17 | §1.1c 排期;§2;§7 | `E/B-6-proxies.json`, `E/B-7-private.json`, `E/schedule-review.md` | 由 OBS-6.proxy-count/OBS-7.class-c-projection 对照人工裁决预算;超预算只调资源/排期,不能缩判据 |
| A18 | §1.1 删除后验证;MECH_POST_DELETE;§7 | `T/terminal_post_delete.py`;`X/post_delete/`;`U/test_terminal_post_delete.py`;`E/post-delete-control.json` | A₀ 先在隔离 fixture 证明删除后转红/按组回退与 near-miss 全绿;真实 C 后再跑五项并在 B-8 留痕,不在 A₀ 删除真实 shim |
| A19 | §7 前七批回归 | 既有 `T/design_drift_ledger.py`,三份独立 ledger JSON,`T/branch_inventory.py`, `T/branch_inventory.skill6.json`, `T/symbol_audit.py`, `T/table_audit_bridge.py`;`E/regression/` | 前七批门禁、负向控制与基线逐项复跑;三批 ledger 不覆盖,保留 admission/per-binding/OUT_OF_SCOPE、审计 fixture、分支 inventory/parser-only、lint-imports 控制 |

`D/control_catalog.json` 是 B-11 唯一目录的机器载体,各测试报告引用同一 ID;
不再另造一份可以与它各自漏项的控制清单。§8-1 的历史文档自检工具、元规则
(九)、B-13/B-14 已被撤销,不恢复为本批交付或冻结门槛。

### 2.3 消费者表、兜底和代码来源的完整实施范围

每一行由 `T/terminal_consumers.py` 识别,在 `D/capability_registry.json` 与
`D/consumer_closure_registry.json` 登记,由 `U/test_terminal_consumers.py` +
`X/consumers/` 逐形态控制,原记录和归属落 `E/consumer_callsites.json`/B-8。

| 形态 | 必须识别的边界(完整谓词以 F §1.1 为准) |
|---|---|
| C1 | 无 as 的 Import alias;level=0 的 ImportFrom |
| C4 | 有 as 的 Import alias,含包子模块 alias |
| C5a | level>0 的相对 ImportFrom |
| C2a | importlib.import_module 的常量首参 |
| C2b | 同调用非常量首参,保留 DYNAMIC_UNRESOLVED |
| C3 | 字符串式 monkeypatch/patch/dict/multiple;指定 patch 族非常量仍归 C3 且未决 |
| C6a | monkeypatch setattr/delattr 的非字符串首参 |
| C6b | patch.object |
| C5b | 内建 __import__ |
| C5c | runpy.run_module |
| C5d | importlib.util 的冻结五函数集合 |
| C5e | sys.modules 下标/get/pop/setdefault/in/not in;集合外操作阻塞 |
| C6c | setattr/delattr 首参解析为模块对象 binding |
| C6d | getattr/hasattr 模块对象,属性名常量解析,变量未决 |
| C8a | 进程启动封闭族经解释器文法归一为 python -m,含紧贴/簇写法 |
| C8b | 同进程族其它命令;无法归一为未决,无模块命令仍记录参与点 |
| C7a | pyproject entry-points/scripts/gui-scripts 与 setup.cfg 入口 |
| C7b | manifest 分类为 CI 的文件中模块入口 |
| C7c | shell 文件/shebang sh/bash 的模块入口 |
| C7d | Makefile/GNUmakefile/*.mk/*.spec/Dockerfile/*.service/tox.ini 的解释器行 |

- 独立参与点枚举覆盖 Import alias、监控调用、受监控裸读取、sys.modules
  访问、模块对象属性操作;先分文件类别,每点恰一形态。监控集合按冻结的
  导入/打桩/进程族穷举,MagicMock/CalledProcessError/PIPE 不能误当参与点。
  未登记操作、零命中/多命中都是 `UNKNOWN_CAPABILITY`,解除只能走勘误扩表。
- 名字命中兜底同时搜索点分名、源路径、包目录、拆分 `from a.b import c`,应用
  冻结词边界并支持空白/括号/逗号/as。全 tracked 文本逐命中登记去处,二进制
  跳过也逐个登记;解释器命令里名字命中却无消费边必须阻塞。
- 文档排除按文件类别、可执行位、shebang 判定,不能把 docs 整树豁免。
  doctest、-c、脚本、stdin 载荷作为 Python,不适用文本排除。其它字符串
  仅按冻结封闭位置排除;无法归类的名字不能吞掉。
- 解释器兜底与名字兜底并存:按封闭 token 集识别 python/变量/宏;续行合并,
  引号外 &&/||/;/管道/换行切命令,每个解释器 token 独立参与;未知文件类阻塞。
- 选项文法先于脚本位判定:无参字符 `{b,B,d,E,h,i,I,O,P,q,R,s,S,u,v,V,x,?}`;
  W/X 消费簇内剩余或下个 token;c/m 同样取参并结束选项;支持 `--`、单独 `-`、
  `--check-hash-based-pycs` 的等号/分离参数、`--help`/`--version`。
  未知选项、缺参、未展开变量/宏一律 DYNAMIC_UNRESOLVED,不能猜脚本位。
- 代码来源封闭四类:`-m` 模块;`-c` Python 源;脚本文件/输入重定向文件;
  stdin。支持无扩展名 tracked 脚本,不在版本控制中的文件未决。stdin 包括
  heredoc/here-string/echo或printf字面量/cat tracked文件;展开不明保持未决。
  Python 进程调用沿相同文法,仅常量 `input=` 可解析 stdin;
  `stdin=`/communicate/.stdin.write 非静态链不假称无消费。
- 命令载荷取参按 subprocess、shell命令、execl/execv、spawnl/spawnv、
  posix_spawn、pty、asyncio 的签名族分别处理,禁止全部取首参。
  每条命令记录行内序号、文法结果、来源类别、载荷界定及消费边/未决原因。
- 静态承诺边界之外的运行时自定义包装引用由删除后验证兜底,不把运行时 trace
  当作发现全集。承诺边界内漏检是规格/实现问题,按停止-报告处理。

### 2.4 SEAL、阶段与附录覆盖

`D/seal_rules.json` 逐条对应 F §1.1d/e 的阶段列与分组表;每条断言配一条
独立违例,完整输出进入 `E/seal_results.json` 和 `E/B-11-controls.json`。

| 阶段 | 本阶段须覆盖 |
|---|---|
| A₀ 期 | 12b-9、12b-10、12b-11、12b-12 的投产控制 |
| 扫描期 | SEAL-12/13/14;12b-1/2/3/3b/3c/4/5/6;12b-7 是明确空洞不造实现 |
| 标准化期 | SEAL-2/7/7b/16;N1/π;covers 包含 primary 的独立不变式 |
| admission 期 | SEAL-1/3/4/5/16b;有效后代覆盖的 A/B/C 有界子步骤 |
| disposition 期 | SEAL-6/8/8b/10/11/11b;12b-8 的终态证伪钩 |
| 终局 | SEAL-9/12b/15;§1.3 四断言;暂态与阻塞态清零;冻结 hash/逐条证据 |

补充不可省的 DoD:π 不以逆像至多一条为约束;同一 key 合并 provenance;
PRESENT 只代表存在,ABSENT 必须独立正证;E6 两侧证据与 E12 分开;
R1 展开 E1–E4;七格第 3 格不造普通 item,第 4–6 格可造 fallback;
`uncertainty_kinds` 来自 predicate AST 失败叶子,八类输出域取交集;
补事实不等于人工给 disposition,①不能由消化出口取得。

| 附录 | 拟产出证据与完整性要求 |
|---|---|
| B-0 | baseline 命令与结果、nodeids;开工/收口各一次 |
| B-1 | OBS-1 五 claim + verify_anchors,含源锚、命令、结构化观测与验证结果 |
| B-2 | OBS-2.seg1-staleness / OBS-2.seg2-form;来源可用性不沿用历史结论 |
| B-3 | OBS-3.commit-order / OBS-3.transition-map;实际抽取 SHA、跃迁证明 |
| B-4 | OBS-4.owner-attribution;canonical owner 与消费者签名依赖证据 |
| B-5 | OBS-5.entry-consumers;独立文档入口全集与 smoke/trace 关系 |
| B-6 | OBS-6.proxy-count / OBS-6.intra-package-shim;四级扫描不加跨顶层包过滤 |
| B-7 | OBS-7.falsification-samples / OBS-7.class-c-projection;非空准入样本与排期对价 |
| B-8 | manifest/matrix、全函数分类、原始/有效 covers、fallback、consumer五方与非consumer四方原记录、兜底、universe、hash/run/completion、控制结果、删除后五项与回退记录 |
| B-9 | 四粒度/解析形态分布;callable、getattr、dir、动态all、modules注入、hook/meta_path、打包入口、symlink/pth、namespace、gitlink、非Python provider、条件导入逐项含零记录 |
| B-10 | leaf/decorator 白名单来源/hash/轮次、逐形态语义控制与不交并 |
| B-11 | 唯一控制目录+fixture ID/输入/应有结论/命令/exit/实际红绿,下节分组 |
| B-12 | sentinel、父子 PID、父侧事件零值、精确 child trace 红因、钩子与结论边界 |
| B-14a | 逐项补事实、失败子句导出的 kind、多类输出交集与机械重判结果 |
| B-15 | 每 candidate 输入/判据/消费者/调用图/叶子/A-B/lstat/π/冲突双侧与 disposition,随 SEAL-9 冻结 |

## 3. B-11 全部构造式控制计划

本节是对 F 的实施索引;目录最终由 `D/control_catalog.json` 承载。
所有行落 `U/test_terminal_controls.py` 或第 2 节所列领域测试,输入在
`X/controls/`(消费者边界在 `X/consumers/`),原文输出与 exit 在
`E/B-11-controls.json` + `E/controls/`。此时均为 NOT_RUN。

| 组 | 原文出处 | 必须独立保留的控制与判定 |
|---|---|---|
| G-DIFF | §6;§7 A₀ | 七条:额外改字段、漏已登记差异、空理由、登记不可能差异、mode缺失/未知、NO_DIFF带differences、空DIFF_SET均红;schema缺场景/缺字段/多字段也红;正常两模式绿 |
| G-PRIVATE | §2;B-7 | 每个既有漏检样本都被抓到,空样本集红;(a)/(b)/(c) 各有已知实例;行为叶子不被判可删 |
| G-SEAL-ALL | §1.1d;B-11甲 | SEAL-1/2/3/4/5/6/7/7b/8/8b/9/10/11/11b/12/12b/13/14/15/16/16b 每条至少一个针对本断言的违例,不是只跑一个最终失败 |
| G-SEAL-1 | §1.1d 反向 | 非空来源删一条红;连自身粒度不能枚举的来源红;合法MODULE粒度near-miss绿,不得强制展开binding |
| G-SEAL-4 | 同上 | LEDGER_PRESENT_NO_FINDING裁ALREADY_REMOVED红;INDETERMINATE同禁 |
| G-SEAL-6 | 同上;B-11旧自述 | 人工直接写终态红;完整性未决靠人工补全集得到②红;消化终态越出kind交集红 |
| G-SEAL-7 | §1.1c/d | ID或跨ID span重复红;未归并public bound name重复红;互斥producer合法归并绿,冲突/非互斥未决 |
| G-SEAL-8b | §1.1d | 行为assert藏helper中不能判②;真实依赖误删红;SEAL-11b双向成员/disposition关系破坏红 |
| G-SEAL-9/10 | §1.1d;B-15 | 未通过前置就seal、冻结集不等preseal、漏证据包红;跨candidate删除链顺序漏登红 |
| G-SEAL-11 | §1.1c/d | 显式非法组合逐条;导出表外UNKNOWN_RECONCILIATION;π一对多;E6/两侧证据与E12分开;七格表外UNKNOWN_LEDGER_EXIT;后代全拒后祖先仍第3格或fallback未终态红 |
| G-SEAL-12/13/14 | §1.1d | finding漏进reconciliation红;预测项finding被抑制红;解析形态未扫/未记零红;selector不命中真实代码红 |
| G-SEAL-15 | §8-2;B-11 | ASSERTION四条:翻predicate/换subject/旧snapshot/round-trip不等;MEASUREMENT空产出;型别三条:空块/解析错/无理由豁免;上界四条:通配/决策引用/GATE引用/豁免带块全部红 |
| G-SEAL-16/16b | §1.1d | claim定义无引用/引用无定义红;未闭合消费者必须归上半且禁②;五方删边红,缺原记录或多/零命中红 |
| G-12b-9 | §1.1e;B-11甲 | 十条逐跑:删输入;语法错;中途终止;manifest漏tracked项;预测规则放宽覆盖已知shim且跑完整admission后红;kind无detector;逐条删required edge;恒SCANNED空findings;大量假阳;九类表分支改为registry不存在项 |
| G-REGISTRY | 12b-3c/8 | 漏provider kind、查找未命中、非全函数分类、capability反向缺项各红;行级下界含预测项;预测只能在正确终态证伪 |
| G-DETECTOR | 12b-10 | 每(detector,branch)精确finding正控制+near-miss;取材来自九类映射/四种代理假阴/消费者原子表/解析五类/A-B-D;目录须机械导出,零命中未知分支红 |
| G-GOLDEN | 12b-11 | 五终态正例;guard五规则正反例含try八谓词;A/B四格且MODULE/PROXY、REEXPORT/INLINE分别覆盖;入口分流正反;E6独立golden;答案由规则常量给出,空理由红 |
| G-12b-12 | §1.1e | classifier域/registry/九类表/正控制golden按非consumer的(branch,owner)四方双向;每侧删/错项红,consumer扩充不得误使此门红 |
| G-WHITELIST | §1.1d;B-10 | 每个已登记叶子实际形态分别证伪;零匹配/多匹配/动态实参落(c);pytest.raises两形态、warns、approx不能判接线;源码/依赖hash漂移被捕获 |
| G-PHASE | §1.1d阶段分层 | 清空阶段列红;表列与分组表不一致红;跨阶段提前求值/同阶段循环红;两侧一致near-miss绿 |
| G-RENDERER | §8-2 | 同版本同predicate字节不等红;版本升级与predicate同改红;不兼容须先等价predicate迁移;renderer版本不得污染predicate哈希 |
| G-RC1 | §1.1a;B-12 | 子进程动态拼名导入静态零消费sentinel必须红;精确child trace、不同PID、父侧无该事件三断言分别留证,不夸大覆盖范围 |
| MECH_CLASSIFIER7 | §1.1c-0;B-11乙 | 后代覆盖祖先仅第3格绿;暂态且被覆盖仅第1格绿;有primary无covers第7格红;PRESENT无covers仅第4格near-miss;前两构造旧v1.17误红/新规则绿对照 |
| MECH_FIVE_WAY | §1.1d;B-11乙 | 任一方删注册边红;fixture同步加形态/分支/五方记录绿且12b-12不误红;不得在真实registry越过勘误自行扩形态 |
| MECH_AST_CLAUSE_ID | §1.1c;B-11乙 | predicate AST少leaf但mapping不动红;AST与mapping一致改动near-miss绿;AST未动而人工clause/mapping两边同时漏leaf仍须红 |
| MECH_UNIVERSE_ENUM | §1.1c-0;B-11乙 | 独立universe少span而detector遇到→UNSUPPORTED/整轮重启红;scanner漏掉独立枚举的site红;非动态span不进入universe的near-miss绿 |
| MECH_INVARIANT | §1.1c-0;B-11乙 | covers不包含primary独立红,暂态同样红;暂态合法near-miss绿,不让第1格吞构造错误 |
| MECH_POST_DELETE | §1.1末;B-11乙 | 运行时配置+自定义包装的残余引用导致删除后红并回退组;真实零引用near-miss删除后绿且不回退 |

### 消费者控制的逐例展开(归 MECH_FIVE_WAY/G-DETECTOR,不替代逐branch目录)

以下来源为 F §1.1 原子表后的正控制/near-miss;测试落上述消费者路径。

1. `import pkg.sub as a` 只归 C4;相对 import 只归 C5a;
   Python `-m` subprocess 只归 C8a;对象 monkeypatch 只归 C6a。
2. `gbs build` 只归 C8b 且无消费边;README 非 doctest 提名按第9类;
   spec 的 `BuildRequires: python3-devel` 不误成解释器参与点。
3. os.popen Python -m 得边;os.execve 从第二参取 argv 得边;
   Makefile Python -m 归 C7d 得边;spec 宏未展开为 DYNAMIC_UNRESOLVED。
4. Makefile `-c` 拆分导入得边;docstring doctest 导入得边、不被排除。
5. importlib.import_module 裸读取、sys.modules.update、pkgutil.resolve_name、
   importlib.reload 无原子形态须 UNKNOWN_CAPABILITY;未登记 *.bat 解释器行同样阻塞。
6. heredoc 中相邻字面量拼接导入得边;here-string 得边;未知管道上游未决;
   subprocess 常量 input 得边;subprocess stdin=f 未决。
7. shell 与 Python subprocess 的 `-W ignore scripts/check` 都正确识别无扩展
   名脚本,不得把 ignore 当脚本;紧贴 `-m<sentinel>` 得边。
8. 同一行两条 `python -m ... && python -m ...` 各一参与点/消费边;
   引号内 `x && y` 不切分的near-miss;docs/Makefile 照 C7d 扫描;
   未知选项未决;echo 中名字看似命令但无实际消费边须 UNKNOWN_CAPABILITY。
9. 为冻结文法各分支补受控样本:短选项簇/紧贴W-X-c-m、长选项两种取参、
   缺参/未知/变量、重定向/无扩展脚本、heredoc各界定方式与展开、
   echo/printf/cat管道、非字面input/communicate/stdin.write。
   这些测试执行既有封闭规则,不扩充形态或改变registry分类。

## 4. OBS-1 与残留专项取证(任务 3c)

`T/verify_anchors.py` 以固定 tree、skill-5 v1.3.2 原件 hash、机械 selector 和
测试场景为输入,只产生原始事实;predicate/verifier 单独核验。

| claim | A₀ 拟采证据 | 验收/产出 |
|---|---|---|
| OBS-1.item1-basis | step-0 §6.2 与当前候选来源逐项对应、时效与保护裁决 | 不抄历史计数;`E/B-1-anchors.json` 的该键指向 B-2/B-3 |
| OBS-1.item2-scope | 历批私有测试义务与 private_consumption 结果比较 | 引 B-7 三分/样本,不以文件名替代判定 |
| OBS-1.item3-predicate | ANCHOR-3 AST;悬空/非悬空 fixture 的真实旧异常及目录状态 | 供 §3 expected_diff 旧值,不从目标行为反推现状 |
| OBS-1.item4-anchors | 完整映射表各行、六个源码调用面、异常签名、顺序与磁盘观察 | query/git/两种submit/两种shared 分开记录;与 §4/5 裁决不一致即停 |
| OBS-1.item5-order | verify/exclude/marker写入顺序,两个中断时点与既有读取方结果 | marker存在、字节hash和reader结果齐备,§5 两场景 NO_DIFF |

### gerrit-fetch query/git 残留专项

1. 从 skill-5 v1.3.2 §3.2 的 Markdown 表读取 query/git 两行并保存原文、hash、
   章节定位;同时读取 skill-3 已冻结的 query失败/destination不动与git阶段
   失败/残留契约。此处须显式回答“是否区分阶段”,不能压成一个 fetch 残留值。
2. 按函数名和 Call AST 定位 `fetch_source_for_commit` 内 query、reset、mkdir、
   git init/fetch/checkout 的顺序,保留源区段与行号用于复核;行号不是selector。
3. 在隔离临时目录建带 sentinel 的旧 destination。fake runner 在 query 注入
   TimeoutExpired、SIGINT/SIGTERM 对应中断场景;记录 reset 是否发生、原目录
   与 sentinel 字节、调用轨迹、异常,证明 query失败前提下 destination 是否不动。
4. 同样输入分别在 init/fetch/checkout 注入故障,逐阶段记录重建与已产生文件,
   验“阶段残留、不自动回滚”;预期值依据批准表,观测值来自真实执行。
   信号传播场景须隔离子进程,不只用异常文字冒充真实信号证据。
5. A₀ 在现状上采旧值;commit A 用相同 fixture 采新值并验 FETCH_TIMEOUT 映射。
   产出 `E/anchors/fetch-stage-residuals.json`、命令与输出,归属
   `OBS-1.item4-anchors`;发现当前代码/既有契约/映射表三者冲突即停止报告。
6. 另核 §5 真正引用的映射表最后一行:在 `_exclude_private_files` 中断前后观察
   workdir/protected 两种 marker 与 exclude 状态,不能以 fetch 两行核对替代。
   marker 写入故障还要记录不完整内容 hash 与现有读取方行为。

这些均是拟取证步骤。本轮源码阅读用于选择注入点,不冒充 A₀ 动态证据。

## 5. 人工裁决前提与挂账

| ID | 前提/挂账 | 关闭时点与处置 |
|---|---|---|
| H1 | §8-2 禁止实现方补写 expected;附录 B 当前只有claim键/型别/producer/义务,没有授权实现方编造结构化oracle | A₀ 首跑前由设计方给出/批准非空predicate与规则常量,记录来源hash并冻结;未满足不得宣称SEAL-15通过 |
| H2 | 台账外候选、动态值域、无法判定事实须结构化人工输入;UNKNOWN_CAPABILITY只许扩表勘误 | 对应admission/disposition前完成;人工补事实,机械重判,不直接手填终态 |
| H3 | proxy/(c)投影与裁决预算需要开工前排期检查 | A₀ 投影出来后对照批准预算;不足调排期/资源,不缩发现面 |
| H4 | 部署前固定tree的证据必须可复算;当前工作树有既有无关修改 | A₀ 从明确固定tree取得只读输入,报告工作树差异;不把脏工作树结果伪标为HEAD快照 |
| H5 | 末批全部五项与删除后验证均须关闭,不能再延期 | D前硬门;残余静态边界通过真实删除后验证兜底,失败组回退后重新A₀判定 |

上述是冻结稿已规定的执行前提,不是本轮新裁决或已完成结论。既有设计确认
不等于这些运行输入已经产出。待 A₀ 实现授权后,先用真实输入做可满足性检验;
任一前提缺失或断言出现真矛盾立即停止并报告。

## 6. Commit 计划与停点(任务 3d)

| 阶段 | 交付与顺序 | 进入下一步前须满足 |
|---|---|---|
| 本次登记 | 冻结稿原字节 + progress + INDEX,单docs commit | push后停止;不开始A₀ |
| A₀ | 第2/3/4节全部工具、注册表、数据、fixture、claim与基线证据 | predicate首跑前冻结;全部准入/构造控制和既有门禁实跑;排期检查与缺输入报告 |
| A(项4) | 逐调用面实现timeout,登记允许差异与三类场景 | 默认None仅允许kwarg差异;逐面超时映射/残留、中断parity |
| B(项3+项5) | symlink归一化;marker按B裁决维持顺序,只落失败态测试与NO_DIFF | 相邻输入不变,两marker中断时点与reader结果全量对比 |
| C(项1+项2) | 按⑤→④→③→②→①并遵SEAL-10跨candidate依赖;⑤保真依赖,④先处理外部再私有化,③迁移真实消费者 | 每candidate依冻结证据执行;每次commit同步progress/证据;测试三分闭合 |
| C删除组 | ①/②按shim模块分组,每组一个独立commit,列出删除条目 | 不把C压成一个大删除commit;删除组可独立revert |
| C后验证 | 以下五项全跑,结果归B-8 | 任一失败revert所涉删除组并停报;先勘误+正控制,从A₀重跑,不能就地补丁重试删除 |
| D | 五项销账、测试逐项增减、旧冻结现状变更留痕、末批收口/P4.9关闭 | 所有组及删除后五项通过,无未完成/转交项 |

删除后五项:①全量测试与前七批全部门禁;②运行时锚和独立文档入口全部冒烟;
③新解释器逐一 import 所有 tracked Python 模块;④以已删名字形态重扫全树
名字/解释器兜底,第9类排除外零残留;⑤按仓库打包描述构建、干净环境安装,
C7a每个入口跑 `--help`。每项保留输入/命令/输出/exit/回退记录。

## 7. 首次入库的阅读发现(2026-09-27,原任务 3e)

无。本轮未发现需新增裁决的自相矛盾、无法执行条文或 prompt/冻结稿冲突;
新增问题条目数: 0。

该结论只覆盖本轮实施前阅读,不是 A₀ 可满足性或 SEAL 的通过声明。
第5节既定人工输入前提仍须履行,不能以“无新问题”跳过。
用户点名的 fetch 残留专项与 §5 的 exclude 残留核对并列执行,二者不互相替代。

## 8. 进度与后续更新规则

| 阶段 | 状态 | 证据 |
|---|---|---|
| 冻结稿入库与复述 | DONE @43a6aa6 | 本文件§0、Git提交三文件清单与冻结稿blob hash |
| A₀ 第1段 | BLOCKED_V11 | 第10节:原三项CLOSED,新两项待裁决;干净worktree仍固定43a6aa6,无producer/verifier/B-0运行结果 |
| A / B / C各组 / 删除后验证 / D | NOT_STARTED | 依第6节顺序推进,不提前标完成 |

每个后续 commit 追加:执行命令和exit原文、输入tree/hash、输出路径、已闭合结论、
人工输入来源、未闭合项及关门点。自己的提交SHA不写回同一提交内的文件;
由Git外部锚定,下一次进度更新再引用已存在的前置SHA。

## 9. A₀ 第1段:判定条件入库与停止报告(2026-09-28)

### 9.1 已完成事项与输入指纹

- 已先读本进度并执行 `git pull --ff-only origin clang-fix-campaign`;
  exit 0,stdout 为 `Already up to date.`。
- 判定条件来源: `../../p49-terminal-obs-predicates-v1.0.md`,交付原件已位于
  目标路径且尚未跟踪。本次原字节入库,不修订、不重新排版。
- `sha256sum docs/clang-fix-campaign/p49-terminal-obs-predicates-v1.0.md`
  的实测输出为:

```text
12e01f6f6e3aa42816047265c3529999328bdd3f1ab0b25c7d162193948bb712  docs/clang-fix-campaign/p49-terminal-obs-predicates-v1.0.md
```

- 既有 H1 的设计方输入已收到,但其可编码性尚未闭合。本文不把“原件获批”
  等同于“实现方的 JSON 编码获批冻结”;仍须设计方逐条核对、FatTank 批准,
  然后另 commit 冻结 predicate,此后才可首跑 producer。
- 原 v1.31-FROZEN 不改。以下只报告困难与候选,不改来源文档中的条件。

### 9.2 H4 干净工作区与主工作树隔离

用途为只读快照输入,未修改其中任何 tracked 文件,不是以主工作树的脏状态
作为观测对象。建立命令(在主工作树执行,exit 0):

```bash
git worktree add --detach /home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6 43a6aa625f27da46daba190657bf62256080c68e
```

| 字段 | 固定值 |
|---|---|
| 工作区 | `/home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6` |
| HEAD / 后续 `$ctx.head` | `43a6aa625f27da46daba190657bf62256080c68e` |
| tree / 后续 `$ctx.tree` | `ca9331190e878af465e7968fe56e735585a5866e` |
| 分支状态 | detached HEAD,不移动主分支、不复用主工作树的 editable 安装作为干净环境证据 |

在上述工作区实跑:

```text
$ git rev-parse HEAD HEAD^{tree}
43a6aa625f27da46daba190657bf62256080c68e
ca9331190e878af465e7968fe56e735585a5866e
exit=0

$ git status --porcelain=v1 --untracked-files=all
(stdout empty)
exit=0
```

主工作树的既有改动完整列表、所用命令与输出见
`a0-evidence/intake/context.json` 的 `main_worktree_status`。
该列表在本次编辑前采集,其中唯一属本任务的输入是未跟踪的 predicate 原件;
`unrelated_changes` 已排除该输入,逐项保留其余状态。
概要: `.gitignore` 的修改;`docs/BACKLOG.md`、
`docs/analyzer_error_clusters_design.md`、`docs/architecture.md`、
`docs/build_skill_v0.2_design.md` 的删除;`.claude/`、历史草稿、旧脚本、备份和
其它未跟踪文件。仅记录,不 stash、不清理、不合并进本次提交。

后续 A₀ 采集与测试须在此干净工作区使用独立环境运行,工具/数据另记内容hash;
本轮仅做 Git/文档入库检查,未将新工具安装进去,未产出任何 OBS 事实。
本次文档提交不会改变上述只读 worktree 固定的 HEAD/tree。

### 9.3 v1.0 编码前停止项(三项,已由v1.1裁决关闭)

以下 `P:Lx` 为 predicate 来源原件行号,`F:Lx` 为 v1.31-FROZEN 原件行号。

| ID | 原文位置与要求 | 困难与影响 | 候选处理,须设计方裁决 |
|---|---|---|---|
| PRED-01 | P:L9“一条要求对应一个节点”;P:L61“每条 predicate 都以这四项开头”;P:L67 G4“由 verifier 按 schema 检查,不另写节点”;本次任务§3同时要求G1–G4逐条编码 | 若给G4节点,违反“不另写节点”;若只有schema校验,不能声称每项条件都有predicate节点。影响逐条件映射与节点数口径,不能隐去G4或把schema偷偷当新op | 方案A:保留原件G4的schema专属校验,以非predicate的condition引用绑定G4,将“条件数/AST节点数/schema义务数”分列;方案B:设计方明确修订G4,批准以封闭语言已有的keys_eq表示其适用范围。实现方不自行选 |
| PRED-02 | P:L223–229,`OBS-6.intra-package-shim#3`:“不设必须为空或必须非空”,并称证明发现面没有用跨顶层包排除;P:L28封闭节点集 | #3没有可执行表达式;没有用于独立枚举“应发现的同包候选”的字段/路径。现有#1的forall与#2的subset在records=[]时均成立,不能因此证明未漏同包候选。删#3、写恒真节点或自行补独立全集都改变了要求 | 方案A:设计方将#3明确归为说明性约束,不计可执行节点,同时明确覆盖义务由哪道既有门禁承担;方案B:设计方提供独立全集的schema/路径与明确set_eq条件,再逐字编码。不得擅加常量或用producer自报“未排除”顶替 |
| PRED-03 | P:L22–26路径定义、L33–35 present/eq/ne;P:L105 `exception_code{state,value?}`;P:L113 `not(eq(@/exception_code/value,"SOURCE_DIR_UNSAFE"))`;F §3 的ABSENT旧值登记 | value允许缺省,但eq/not对缺失路径的求值规则未规定。对人工输入`{"exception_code":{"state":"ABSENT"}}`,将缺失比较为false再取not会通过;将缺失视为求值失败则整条失败。这不是两个等价实现,亦不能用null代替缺失 | 方案A:设计方补语言规则,明确可选路径MISSING的eq/ne/not及组合节点语义,必填缺失仍由schema拒绝;方案B:设计方把该条件改成按state显式分支且先检查value存在的封闭表达式,并明确其它缺失路径统一失败。不得实现方改写#5 |

PRED-02 的空数组例和 PRED-03 的 ABSENT 例仅为输入文档的语义分析,
不是真实 producer 观测,也不是已实现 verifier 的测试结果。
上述表保留v1.0时的困难与候选,不是本次开放项。设计方判定条件v1.1已获
FatTank批准,本次按以下位置销账;不把v1.1的另两处困难重新挂回旧问题。

| 原问题 | 当前状态 | v1.1 处理位置与关闭依据 |
|---|---|---|
| PRED-01 | CLOSED | §1:L58新增`schema_closed()`;§2:G4:L83显式使用该节点,消除“另行校验却要求逐条节点”的冲突 |
| PRED-02 | CLOSED | §3 `OBS-6.intra-package-shim#3`:L248–252改为与`same_top_package_candidate_ids`的set_eq;§4:L288–290把扫描未漏的覆盖义务交给`CTRL-INTRA-PKG-PROXY` |
| PRED-03 | CLOSED | §1:L60–66定义MISSING、求值错误与从左到右短路;item3#5:L129–132对悬空场景按ABSENT/VALUE显式分支,不再对缺失value直接取反 |

v1.0原件保留不删。v1.1来源见第10节;未运行producer,未宣称JSON编码已经核准。

### 9.4 条件清点与未完成交付

编码前只对输入文档做编号清点,无 claim producer 调用。命令在干净worktree
运行,显式读取主工作树的交付原件(独立输入hash见9.1,不冒称该原件已在基线tree中)。
完整命令、cwd、exit与stdout见 `a0-evidence/intake/context.json` 的
`condition_inventory`;只统计每个`### B-... OBS-...`小节内的编号行,
不从生产源码或既有证据提取事实。

```text
OBS-1.item1-basis: 6 numbered conditions
OBS-1.item2-scope: 8 numbered conditions
OBS-1.item3-predicate: 6 numbered conditions
OBS-1.item4-anchors: 8 numbered conditions
OBS-1.item5-order: 8 numbered conditions
OBS-2.seg1-staleness: 3 numbered conditions
OBS-2.seg2-form: 5 numbered conditions
OBS-3.commit-order: 3 numbered conditions
OBS-3.transition-map: 5 numbered conditions
OBS-4.owner-attribution: 4 numbered conditions
OBS-5.entry-consumers: 4 numbered conditions
OBS-6.proxy-count: 3 numbered conditions
OBS-6.intra-package-shim: 3 numbered conditions
OBS-7.falsification-samples: 4 numbered conditions
OBS-7.class-c-projection: 4 numbered conditions
CLAIMS=15; SECTION_3_NUMBERED_CONDITIONS=74
COMMON_CONDITIONS=4; COMMON_INSTANCES=60
NUMBERED_OBLIGATIONS=134 (not encoded node count; G4/#3 pending ruling)
exit=0
```

这里的134是按原件编号统计的义务实例(74+15×4),**不是134个AST节点**。
复合条件含子节点,G4及说明性#3的计数口径又待裁决,不能宣称已对齐。

| 交付 | 状态 | 实测/缺项说明 |
|---|---|---|
| 来源文档 | 原字节入库 | 9.1 SHA;由Git外部锚定 |
| 干净工作区 | 已建,内容未改 | 9.2 identity与空status,exit均0 |
| `predicates.json` | NOT_CREATED | 编码节点0;canonical hash不存在,不填占位hash |
| `measurement_exemptions.json` | NOT_CREATED | 规范值仍为[],待恢复编码时与判定条件一起交付 |
| verifier / renderer / canonical实现 | NOT_STARTED | 因PRED-01–03停在编码前,无测试命令/exit |
| 节点正反与各组构造式控制 | NOT_RUN | 无虚构通过数或exit |
| B-0 pytest(含nodeids) | NOT_RUN | 第3步停止,不越过停点执行第4步;exit=N/A |
| B-0 mypy | NOT_RUN | exit=N/A |
| B-0 ruff | NOT_RUN | exit=N/A |
| B-0 lint-imports | NOT_RUN | exit=N/A |
| OBS producers | NOT_RUN | 仍受先批准冻结predicate再首跑的禁令约束 |
| 本段停止报告 | 3 OPEN | PRED-01、PRED-02、PRED-03;待设计方裁决 |

恢复条件:设计方明确上述编码口径并由FatTank批准后继续第3步,再进入B-0。
本次只提交原件与停止记录;不把本段标为完成,不将当前编码状态称作冻结。

## 10. v1.1 续跑:来源替换与新的编码前停止报告

### 10.1 输入与工作区复核

本节为最新状态,第9.4节的三项OPEN/NOT_RUN表是v1.0停点历史。
执行`git pull --ff-only origin clang-fix-campaign`,exit=0,
stdout=`Already up to date.`。开工HEAD为
`e8519d3eba92c52bfb47e5d6b1cc63fcd8041eb9`。

编码来源现为`../../p49-terminal-obs-predicates-v1.1.md`,原件已在目标路径,
本轮原字节入库,不自行修正文档。实测命令与输出:

```text
$ sha256sum docs/clang-fix-campaign/p49-terminal-obs-predicates-v1.1.md
7f4beb2886733a6e2820324677c38463c19ee2482bbf34beeb329890299d00da  docs/clang-fix-campaign/p49-terminal-obs-predicates-v1.1.md
exit=0
```

H4工作区仍为`/home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6`。
在那里复跑`git rev-parse HEAD HEAD^{tree}`得到:

```text
43a6aa625f27da46daba190657bf62256080c68e
ca9331190e878af465e7968fe56e735585a5866e
exit=0
```

同目录`git status --porcelain=v1 --untracked-files=all`的stdout为空,exit=0。
未安装工具或改动该工作区;文档检查显式读取主工作树中v1.1原件,不把原件
错误标成已经包含在43a6aa6中。原始命令/cwd/exit/stdout记录在
`a0-evidence/intake/v1.1-preflight.json`,不是OBS产出或B-0证据。

### 10.2 新停止项(待设计方裁决)

以下`P:Lx`均指v1.1原件行号。本轮新增开放项为2,旧PRED-01/02/03保持CLOSED。

| ID | 原文位置与要求 | 困难与影响 | 候选处理,须设计方裁决 |
|---|---|---|---|
| PRED-04 | P:L58要求schema_closed递归核对所有嵌套对象与数组元素;G3:L81–82要求evidence元素带两种证据字段;各claim如L93仅声明`evidence[]`;L236的`by_form{}`、L266的`reasons{}`又在L240/L270–271使用运行时键 | 当前schema缩写没有声明evidence元素的对象字段,也没有规定空花括号表示“无字段对象”还是“运行时键的map”。若按封闭字段集取空集,带证据或非空map会红;若自行允许未声明键,违反L58/L73。不能借G3的present检查擅自推导schema的required/optional/union规则 | 方案A:设计方提供统一schema记法:显式证据变体及字段、封闭record与动态map的区别、map的键/值约束;方案B:给出等价的完整结构化output_schema。字段形状与允许范围须来自设计方,不得用开放对象临时放行 |
| PRED-05 | P:L128的LIVE分支只含`eq(exception_type,"GerritError")`和`eq(exception_code/value,"SOURCE_DIR_UNSAFE")`;L133又要求`state`不为VALUE即红;L121仅把value标可选 | 两种要求不等价。人工输入LIVE场景、type=GerritError、code={state:ABSENT,value:SOURCE_DIR_UNSAFE}满足逐字表达式,却违反L133。schema_closed只是字段存在性/封闭性,没有授权增加state/value的条件关联。逐字编码会漏验;自行补eq(state,VALUE)又违反不增改表达式的边界 | 方案A:设计方在LIVE分支all中显式补`eq(@/exception_code/state,"VALUE")`,保留L133;方案B:设计方撤销L133额外要求。实现方不选择、不修改来源或predicate |

PRED-04尚未被实现为任何schema规则;PRED-05仅做了以下人工反例的直接
布尔求值,不是通用verifier测试,也没有读取生产事实或调用producer。

```text
SOURCE: v1.1 line 128 expression vs line 133 state requirement
INPUT: {'scenario_id': 'LIVE_SYMLINK_TO_DIR', 'exception_type': 'GerritError', 'exception_code': {'state': 'ABSENT', 'value': 'SOURCE_DIR_UNSAFE'}}
LITERAL_EXPRESSION: True
PROSE_STATE_REQUIREMENT: False
COUNTEREXAMPLE_CONFIRMED (not a verifier/producer run)
exit=0
```

其完整可复现命令已随原文输出保存在`v1.1-preflight.json`。
不把反例确认的exit=0混称为verifier/控制测试通过。

### 10.3 文档条件数与编码状态

下表由输入文档每个claim小节的编号行机械清点;四条共用条件逐claim计入,
编号连续性已检查。它是编号义务数,不是递归AST总节点数。
因停在schema/表达式的可编码性核对,没有创建部分predicate来伪装完整交付。

| claim | §3编号条件 + G1–G4 | 编码节点数 |
|---|---|---|
| OBS-1.item1-basis | 6 + 4 | 0 |
| OBS-1.item2-scope | 8 + 4 | 0 |
| OBS-1.item3-predicate | 6 + 4 | 0 |
| OBS-1.item4-anchors | 8 + 4 | 0 |
| OBS-1.item5-order | 8 + 4 | 0 |
| OBS-2.seg1-staleness | 3 + 4 | 0 |
| OBS-2.seg2-form | 5 + 4 | 0 |
| OBS-3.commit-order | 3 + 4 | 0 |
| OBS-3.transition-map | 5 + 4 | 0 |
| OBS-4.owner-attribution | 4 + 4 | 0 |
| OBS-5.entry-consumers | 4 + 4 | 0 |
| OBS-6.proxy-count | 3 + 4 | 0 |
| OBS-6.intra-package-shim | 3 + 4 | 0 |
| OBS-7.falsification-samples | 4 + 4 | 0 |
| OBS-7.class-c-projection | 4 + 4 | 0 |
| 合计 | 74 + 60 = 134 | 0 |

清点命令在固定worktree运行,exit=0,逐claim输出见`v1.1-preflight.json`。

| 交付/验证 | 当前状态 | exit / hash |
|---|---|---|
| v1.1原件与旧三项关闭 | 已登记 | 原件SHA见10.1;v1.0不删 |
| predicates.json / canonical hash | NOT_CREATED | N/A,不提供占位hash |
| measurement_exemptions.json | NOT_CREATED | 规范值仍为[],未运行任何豁免判定 |
| verifier / renderer / 节点正反 / ASSERTION与型别豁免控制 / 每claim变异 / 求值语义五条 / item3四输入 | NOT_RUN | N/A |
| CTRL-INTRA-PKG-PROXY | NOT_RUN | 扫描器未实现;恢复后只登记control_catalog,本段不运行 |
| B-0 pytest(逐nodeid) | NOT_RUN | N/A |
| B-0 mypy | NOT_RUN | N/A |
| B-0 ruff | NOT_RUN | N/A |
| B-0 lint-imports | NOT_RUN | N/A |
| OBS producers | NOT_RUN | 未满足predicate核对/批准/单独冻结门禁 |

本轮只完成输入与停止记录,生产代码和测试零改动。等待PRED-04/05裁决后
从编码继续;不越过停止点运行B-0,不把原件获批等同于JSON编码获批。
