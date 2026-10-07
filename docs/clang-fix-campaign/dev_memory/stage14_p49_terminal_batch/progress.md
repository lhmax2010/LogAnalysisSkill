# P4.9 末终止批次进度与实施前复述

状态: A0_PART2_STRUCTURE_COMPLETE_PENDING_SEG3。更新日期: 2026-10-07。
判定条件 v1.2 取代 v1.0/v1.1 作为编码来源,两旧版本保留。
PRED-01..05 全部 CLOSED;编码已由设计方核对、FatTank 批准并于
6601cfc 单独冻结(第12节)。第15节记录 item3/item4 首跑及 verifier PASS。
勘误2已核对原字节;DIFF-01..04 CLOSED。第17节记录第2段收尾裁决、
预期差异门禁结构/登记/人工准入证伪;§6改前实跑为PENDING_SEG3。
本轮未运行任何 producer或真实双跑;既有两项产出不变,生产实现未开始。
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
| A₀ 第1段 | AWAITING_PREDICATE_REVIEW_V12 | 第11节:134编号条件节点、95人工测试绿、B-0四项exit=0;待核对及单独冻结,不运行producer |
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

### 10.2 v1.1 停止项(历史记录;已由v1.2关闭,见11.1)

以下`P:Lx`均指v1.1原件行号。当轮新增开放项为2,旧PRED-01/02/03保持CLOSED。
当前 PRED-04/05 均 CLOSED;以下保留当时的问题与候选,不反写历史实测。

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

## 11. A₀ 第1段续:按v1.2编码、人工控制与B-0(2026-09-28)

### 11.1 输入、裁决关闭与人工批准边界

本轮先读本记录,再执行`git pull --ff-only origin clang-fix-campaign`:
`Already up to date.`,exit=0。续跑起点为`8241f293e956b8387705d2385497346768145a30`。
交付原件已位于目标路径,本轮不改其字节,不改v1.31冻结设计。
v1.2取代v1.0/v1.1为编码来源,旧两份原件保留。

```text
$ sha256sum docs/clang-fix-campaign/p49-terminal-obs-predicates-v1.2.md
3397ee5b097142c0e956bfe8162033791641d752097662689b86d24d91a6b3f1  docs/clang-fix-campaign/p49-terminal-obs-predicates-v1.2.md
exit=0
```

| 停止项 | 当前状态 | v1.2处理位置与本轮证据 |
|---|---|---|
| PRED-04 | CLOSED | §1:L68-84给出封闭record、optional、array、map、判别union与Common/Evidence/CodeState/MarkerState;§3十五个output_schema逐个重写为结构化形状。编码逐层展开,`test_schema_four_groups`四组通过,CodeState/嵌套字段控制另见item3测试 |
| PRED-05 | CLOSED | item3#5:L155-161的LIVE分支含`eq(state,"VALUE")`;CodeState在L81限定ABSENT无value/VALUE有value。`test_item3_all_inputs`含原反例、LIVE合法与LIVE无value三个输入,以及悬空四输入,全部符合预期 |

旧PRED-01/02/03仍CLOSED。**本轮新增停止报告条目数=0**。
这是可编码性和人工样本测试结果,不是十五个OBS对真实仓库均成立的声明。
H1仍有人工闸门:设计方逐条核对本候选JSON、FatTank批准、另commit冻结带hash。
本提交不是该冻结commit,未生成真实OBS产物,不宣称SEAL-15整体已通过。

### 11.2 交付路径与编码对账

| 产物 | 路径(相对仓库根) |
|---|---|
| 逐claim候选与豁免表 | `docs/clang-fix-campaign/tools/p49_terminal_data/predicates.json`;同目录`measurement_exemptions.json`=`[]` |
| 比较器/renderer/canonical hash | `docs/clang-fix-campaign/tools/terminal_predicates.py` |
| generated block与控制目录 | 同数据目录`predicates.generated.md`、`control_catalog.json`、`README.md` |
| 人工假产出与测试 | `tests/fixtures/p49_terminal_predicates/synthetic.json`;`tests/unit/test_terminal_predicates.py` |
| 编码/测试原始证据 | 本目录`a0-evidence/predicates-v1.2/` |
| 固定旧树基线 | 本目录`a0-evidence/B-0/` |

每条编号条件是claim根`all`的一个直接子节点;同一编号下多个显式表达式以
`all`按原顺序组合。每个子表达式和引用操作数都带该条件的`source`。
四共用条件先于专属条件;不把schema中的动态map改成开放record。
schema从v1.2的显式结构记法转录,不从生产输出反推。
subject/quantifier保留原文字段;不补与当前树有关的expected常量。

下表由文档编号行与JSON直接子节点对比得到,原始结果:
`a0-evidence/predicates-v1.2/encoding-counts.json`。
自动检查证明编号/覆盖数量一致;逐条语义核对仍留给设计方,不把数量检查称为审批。

| claim | 文档专属条件 + G1–G4 | 编码编号节点 | 递归表达式节点(含根) |
|---|---|---|---|
| OBS-1.item1-basis | 6 + 4 | 10 | 27 |
| OBS-1.item2-scope | 8 + 4 | 12 | 33 |
| OBS-1.item3-predicate | 6 + 4 | 10 | 44 |
| OBS-1.item4-anchors | 8 + 4 | 12 | 60 |
| OBS-1.item5-order | 8 + 4 | 12 | 40 |
| OBS-2.seg1-staleness | 3 + 4 | 7 | 24 |
| OBS-2.seg2-form | 5 + 4 | 9 | 29 |
| OBS-3.commit-order | 3 + 4 | 7 | 30 |
| OBS-3.transition-map | 5 + 4 | 9 | 34 |
| OBS-4.owner-attribution | 4 + 4 | 8 | 29 |
| OBS-5.entry-consumers | 4 + 4 | 8 | 28 |
| OBS-6.proxy-count | 3 + 4 | 7 | 24 |
| OBS-6.intra-package-shim | 3 + 4 | 7 | 22 |
| OBS-7.falsification-samples | 4 + 4 | 8 | 21 |
| OBS-7.class-c-projection | 4 + 4 | 8 | 25 |
| 合计 | 74 + 60 = 134 | 134 | 470 |

唯一文档条件编号为78个(74专属+4共用);共用条件实例化到15个claim后为134个。
470含组合、子表达式、引用操作数与每claim组装根,不是新增470条要求。

候选canonical hash(UTF-8/排序对象键/紧凑JSON/保留数组序,含完整claim对象,
不含renderer_version):

```text
8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6
```

verifier要求外部expected hash与已保存generated block,不从待验输入自行生成
oracle;翻转predicate或交换subject均被外部hash拒绝。renderer_version=1,
每节点一行中文,旁注只通过renderer生成。工具无producer/子进程执行入口;
`$file`只读取指定根之内的JSON,`$ref`只读取传入的事实。

### 11.3 verifier、控制测试与开发检查实跑

所有命令cwd为§9.2干净工作区。测试与工具使用主工作树的**绝对路径**读取本轮
新文件;这些文件不谎称已存在于43a6aa6。各`*.command.json`记录读取版本的
tool/tests SHA,与执行cwd/tree分开。fixture的`synthetic-tree`等均为人工值,
不是固定树观测。95项测试未调用任何OBS producer。

复现命令(变量仅缩写实跑记录中的绝对路径):

```bash
cd /home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6
R=/home/linhao/Toolchain/development/LogAnalysisSkill
V=/tmp/p49-a0-baseline-v12-43a6aa6
E=$R/docs/clang-fix-campaign/dev_memory/stage14_p49_terminal_batch/a0-evidence/predicates-v1.2
env -u PYTHONPATH -u MYPYPATH -u PYTEST_ADDOPTS -u PYTEST_PLUGINS "$V/bin/python" -m pytest "$R/tests/unit/test_terminal_predicates.py" -vv --junitxml="$E/tests.xml"
"$V/bin/ruff" check "$R/docs/clang-fix-campaign/tools/terminal_predicates.py" "$R/tests/unit/test_terminal_predicates.py"
"$V/bin/mypy" --follow-imports=silent "$R/docs/clang-fix-campaign/tools/terminal_predicates.py" "$R/tests/unit/test_terminal_predicates.py"
"$V/bin/python" -m py_compile "$R/docs/clang-fix-campaign/tools/terminal_predicates.py" "$R/tests/unit/test_terminal_predicates.py"
"$V/bin/python" "$R/docs/clang-fix-campaign/tools/terminal_predicates.py" "$R/docs/clang-fix-campaign/tools/p49_terminal_data/predicates.json"
```

最后一条加`--render`取得generated block。六个命令的argv/env/exit及完整
stdout/stderr分别保存为`tests/ruff/mypy/py_compile/validate/render.*`。
输出摘录:

```text
============================== 95 passed in 0.35s ==============================
tests exit 0
All checks passed!
ruff exit 0
Success: no issues found in 2 source files
mypy exit 0
py_compile exit 0  (stdout/stderr empty)
registry_valid claims=15 canonical_hash=8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6
validate exit 0
render exit 0
```

| 控制组 | 实测条目/内容 | 结果 |
|---|---|---|
| 封闭语言 | 28种节点/参数表达式,各含正反 | PASS |
| ASSERTION | 翻转predicate/交换subject/旧snapshot/round-trip不一致 | 四条均拒绝 |
| 型别 | 空predicate/解析失败/无理由豁免 | 三条均拒绝 |
| 豁免上界 | 通配/决策引用/GATE引用/带predicate | 四条均拒绝 |
| claim事实变异 | 15个claim各改坏一个相关事实 | 原人工样本全绿,各变异红 |
| 求值语义 | 缺必填/多字段/未短路缺失错误/已短路不求值/空量词 | 五组PASS |
| item3#5 | 悬空四输入+LIVE三输入(含PRED-05反例) | 七项PASS |
| schema记法 | Evidence各变体与非法值/map/optional/嵌套extra | 四组PASS |
| 其它边界 | 外部hash、renderer版本、JSON Pointer、缺引用、非法AST、union结构、batch空豁免等 | PASS |
| CTRL-INTRA-PKG-PROXY | G-DETECTOR同包代理正控制与near-miss | NOT_RUN;只登记,扫描器尚未实现 |

测试命令exit=0表示它成功断言负输入被拒绝,不表示负输入本身通过。
逐控制nodeid、来源与测试证据见`control_catalog.json`。实跑JUnit生成其状态,
不把NOT_RUN算进通过分子。未生成真实B-11控制产物或扫描器结论。

开发过程如实记录:首轮人工测试89 passed/1 failed,原因是手构正样本把
closeout路径误写成`p49-skill-1-closeout.md`这类名字,违反已正确编码的正则。
只修fixture为实际契约的`p49-skill1-closeout.md`形态,未改predicate;
之后90/90,补齐边界测试后为上列95/95。ruff行宽与mypy注解错误均已修复。

### 11.4 B-0原始基线(不是OBS产出)

继续复用§9.2工作区,HEAD/tree不变。独立venv:
`/tmp/p49-a0-baseline-v12-43a6aa6`,Python 3.12.3。
在该工作区执行`python -m pip install -e '.[dev]' -r requirements-dev.txt`,
exit=0,安装记录`B-0/install.log`与`install.command.json`;
`pip freeze`原文在`packages.log`。运行时清除PYTHONPATH/MYPYPATH/
PYTEST_ADDOPTS/PYTEST_PLUGINS,PATH与VIRTUAL_ENV指向独立环境。

| 命令(cwd固定工作区) | 实测输出摘录 | exit |
|---|---|---|
| `pytest tests/ -vv --tb=short --junitxml=<B-0绝对路径>/pytest.xml` | `941 passed, 1 skipped in 20.64s` | 0 |
| `mypy` | `Success: no issues found in 114 source files` | 0 |
| `ruff check .` | `All checks passed!` | 0 |
| `lint-imports` | `Analyzed 67 files, 129 dependencies.`;`Contracts: 6 kept, 0 broken.` | 0 |

完整输出分别为`a0-evidence/B-0/{pytest,mypy,ruff,lint-imports}.log`;
每项`*.command.json`含精确argv、cwd、必要环境、exit、HEAD/tree。
`nodeids.json`记录942个唯一nodeid及结果,逐项来自verbose日志并与JUnit
计数核对。这里的941/1是本次实跑,不从历史报告复制;新人工测试95项另计,
不加进固定旧树的B-0。没有运行OBS producer。

环境准备的系统`python3 -m venv`因缺ensurepip退出1;改用uv并显式选择
`/usr/bin/python3`。最初uv默认选到3.13,在安装/采集之前已将本轮自建临时
环境重建为3.12.3。固定工作区tracked文件始终未改,详见B-0/README.md。

### 11.5 边界、自检与下一停点

- 原v1.31设计、v1.0/v1.1判定来源、生产源码、既有测试均不改;
  仅新增本段verifier测试/人工fixture、工具/数据与记账文档。
- 主树既有`.gitignore`修改、四份文档删除、其余untracked草稿保持原样;
  继承§9.2的差异清单,精确add本轮产物,不处理环境卫生。
- 固定工作区`git status --porcelain=v1`为空,HEAD/tree为§9.2值。
- 当前判定编码待核对;`CTRL-INTRA-PKG-PROXY`与全部OBS producer仍NOT_RUN。
  H2/H3等后续事实输入和A₀其余工具未提前完成,生产A/B/C/D未开始。
- **本段新增停止项:0。交付后停止,等设计方逐条核对与FatTank批准冻结。**
  完整性由包含本记录/源码/数据/原始输出的Git commit外部锚定,
  本文件不自记自身SHA,也不把提交入库当成predicate冻结批准。

## 12. A₀ 第2段:判定条件冻结(先于任何 producer)

### 12.1 批准与不可变锚

批准来源:本轮开发者指令确认,设计方已逐条核对
`c79e893be0830af3969449d908de75314296d47d` 的编码与 v1.2 一致,
FatTank 于 **2026-09-28** 批准冻结。H1 的人工批准前提 CLOSED。
编码来源仍为 `p49-terminal-obs-predicates-v1.2.md`,不重写任何条件。

| 冻结文件(T/p49_terminal_data/) | canonical SHA-256 |
|---|---|
| predicates.json | `8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6` |
| measurement_exemptions.json | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |

冻结提交为包含本节的独立 Git commit;本 commit 完整性由 Git 外部锚定,
其实际 SHA 将在后续提交的 §12.2 引用,不在本提交内自记。
两文件相对批准版本原字节不变,`git diff --` 精确两路径为空。
以后修改须走 v1.31 勘误流程,不可通过 CLI 自带新 hash 授权自己。

`terminal_predicates.py` 的批次 CLI 在验证/render 前核对固定的双 hash;
不匹配报 `FROZEN_HASH_MISMATCH` 并 exit 1。低层求值器仅为通用比较及
人工构造控制服务,不充当生产采集的授权入口。

### 12.2 冻结前实测与执行边界

后续提交登记的冻结 SHA:
`6601cfc60fcbed8d2f8fa91301f7693d52723d94`。
该 commit 已先于任何 producer 落盘;以下保留冻结时的实测记录。

本提交前没有运行任何 OBS producer。所有运行 cwd 为 §9.2 干净工作区,
HEAD=`43a6aa625f27da46daba190657bf62256080c68e`,
tree=`ca9331190e878af465e7968fe56e735585a5866e`;
独立环境 `/tmp/p49-a0-baseline-v12-43a6aa6`,清除 PYTHONPATH/MYPYPATH。
工具与人工测试通过主树绝对路径加载,观测对象仍为固定旧树。
命令、环境、输入工具 hash、exit、原始输出见 `E/part2/freeze-*.command.json/.log`。

| 命令(完整 argv 见原始记录) | 原始输出摘录 | exit |
|---|---|---|
| python -m pytest -q -o addopts= <main>/tests/unit/test_terminal_predicates.py | `99 passed in 0.20s` | 0 |
| ruff check <main>/tools/terminal_predicates.py <main>/tests/unit/test_terminal_predicates.py | `All checks passed!` | 0 |
| mypy <上述两文件> | `Success: no issues found in 2 source files` | 0 |
| python <main>/tools/terminal_predicates.py <main>/tools/p49_terminal_data/predicates.json | `registry_valid claims=15 canonical_hash=8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6` | 0 |

新增四项人工测试:批准双 hash 正向、predicate 篡改拒绝、豁免篡改拒绝、
CLI 传篡改后的 hash 仍拒绝。未改生产源码/冻结设计/判定条件,无真实事实采集。
本轮后续只授权 item3/item4,其它 producer(含 item5)仍 NOT_RUN。

## 13. A₀ 第2段停止报告:预期差异的取值来源

### 13.1 本轮完成与未完成的边界

已完成独立冻结提交与双 hash 核对。进入 §6 的来源核对时发现以下两项
无法自行确定的口径,按冻结稿开头第3条(第10-11行)停止。
这些是**差异登记规格的停止项**,不是 OBS claim 的失败结论。
没有执行任何 producer,不借尚不存在的观测输出填充旧值。
没有修改已冻结 predicates/exemptions,也没有修改任何生产文件。

| ID | 状态 | 原文位置与困难 | 候选处置(仅提请裁决,未实施) |
|---|---|---|---|
| DIFF-01 | CLOSED | 历史停止项:新值来源未含默认 `timeout=None` 的表外规定。 | 附录 C 勘误1 **E1-1** 明定四类来源及逐调用面登记,禁止全局掩码;FatTank批准,见§14。 |
| DIFF-02 | CLOSED | 历史停止项:`<message>` 与 `GIT_TIMEOUT:` 后缀未钉定,不能形成精确期望值。 | 附录 C 勘误1 **E1-2** 明定 `TIMEOUT_MESSAGE_FROM_EXC` / `GIT_TIMEOUT_PREFIX_PLUS_EXC` 和固定 warning,在固定fixture上派生并逐字比对;见§14。 |

DIFF-02 只报告超时映射的消息规则缺口,不假定尚未取证的旧异常内容。
这里的候选例子不构成新增设计裁决,也未写入任何 expected 值。

### 13.2 原文证据与复现

来源为 §9.2 固定工作区的 Git tree,不是主树 untracked 草稿。
精确命令/环境/exit 与 stdout 位于:

- `E/part2/diff-source-terminal.command.json` / `.log`:终止稿 §4/§6 的来源限制关联条款;
- `E/part2/diff-source-mapping.command.json` / `.log`:映射表原文及表外 `timeout=None` 条款;
- `E/part2/stop-source-hashes.command.json` / `.log`:两份被引用文档的原字节 SHA-256。

以上为文档读取,exit 均0;**不是 OBS producer,不输出/冒充任何 claim 事实**。
原始 hash 输出:

```text
66fd8684950004524ae7d86fb4e29328a1998ba48985a944ad39ae4d03a8598c  docs/clang-fix-campaign/p49-terminal-batch-design-v1.31-FROZEN.md
0e2de5ff80c7f36940e455ec75f4f6872caa4fd93be360ad0fcfd0e59c755f27  docs/clang-fix-campaign/p49-skill5-gerrit-submit-design-v1.3.2-FROZEN.md
```

### 13.3 交付状态与恢复条件

| 交付项 | 状态 | 命令/exit/证据 |
|---|---|---|
| predicate 冻结 | DONE | §12;独立提交 `6601cfc60fcbed8d2f8fa91301f7693d52723d94`;两文件原字节未改 |
| 冻结 hash 核对与人工测试 | DONE | §12.2;99 passed,pytest/mypy/ruff/CLI exit均0 |
| scenario_manifest/result_schema/expected_diff | NOT_CREATED | 来源口径未闭合,未写入占位值或自行设计的新值 |
| §6 正常对照与七条准入证伪 | NOT_RUN | 门禁尚未实现;命令/exit=N/A,不把verifier人工测试冒充这组控制 |
| OBS-1.item3-predicate | NOT_RUN | 无产出、无verifier结论、无事实证据路径;不是FAIL或PASS |
| OBS-1.item4-anchors | NOT_RUN | 同上;query/git残留及第六格的动态核对尚未执行 |
| OBS-1.item5-order及其它producer | NOT_RUN | 本段禁行,未越权采集读取方全集 |
| expected_diff 每条登记来源 | 无登记 | 文件未创建,因此不存在已登记差异/来源清单;不是“空表已验收” |
| 新增停止项 | 2 OPEN | DIFF-01、DIFF-02 |

恢复条件:设计方给出两项来源/精确消息口径,由FatTank批准后继续 §6 与
item3/item4。冻结提交已有效,不重复冻结或修改判定条件来消化本次停止项。
本次保持主工作树既有 `.gitignore` 修改、四份文档删除和其它untracked稿不动。
仅精确提交本段工具、人工测试、证据与记账文档;不开始生产 A/B/C/D。

## 14. A₀ 第2段续:勘误1入库

本节覆盖§13的历史停点状态。开发者本轮确认FatTank已批准附录C勘误1。
主工作树目标文件已放入批准原件,实测hash一致,直接保留原字节入库,
不自行重排/改写正文。

- 新原件 SHA-256: `d44584592b54bfaf1406c13369da5f2f6a5894fc3dd8de04b3905eadd6213c3f`。
- 勘误前原件 SHA-256: `66fd8684950004524ae7d86fb4e29328a1998ba48985a944ad39ae4d03a8598c`。
- `git diff --numstat -- docs/clang-fix-campaign/p49-terminal-batch-design-v1.31-FROZEN.md`:
  **40 added / 0 deleted**;两个hunk仅为状态行后新增提示及原文件末尾追加附录C。
- DIFF-01/02分别依E1-1/E1-2 CLOSED;原predicate批准与冻结提交`6601cfc`不变。
- 观测cwd/HEAD/tree仍为§9.2的干净工作区/`43a6aa6`/`ca933119...`;
  文档规则从本次主分支入库的新hash读取,不把旧工作区内勘误前文档当作新规则。
- 当前未运行producer;后续授权仅item3/item4。item5(含读取方全集)仍禁行。
- 规则入库与后续工具/事实记录分开提交,后续记录补本次入库SHA(Git外部锚)。

## 15. 勘误1后:两项首跑PASS,差异登记新停止项

### 15.1 入库锚、判定与代码来源分离

勘误入库 commit=`32b7f432bdeed0b7f6aeeb26c9e37bd1d13486e1`。
`E/part2/e1-intake-diff.log`为该commit相对`4cf85aa`的完整设计稿diff;
`e1-intake-numstat.log`原文为`40 0 <design path>`,无删除行。
新hash仍为§14所列`d4458459...`。文首提示与附录C之外一字未动。

工具/测试从主树加载;全部执行cwd仍是干净的`LogAnalysisSkill-a0-43a6aa6`,
观测HEAD/tree仍为§9.2固定值。独立环境`/tmp/p49-a0-baseline-v12-43a6aa6`;
PYTHONPATH/MYPYPATH清除。producer检查HEAD/tree、空git status、生产模块
实际`__file__`及主树规则文档hash;原始产出同时记录code_root与独立rules来源。

冻结提交仍为`6601cfc`,两文件原字节及canonical hash均未变:
`8271f1d0...`/`4f53cda1...`(全值见§12)。仅增加verifier的显式`--claim`选择:
先校验**完整registry**的冻结hash/renderer,再要求产出键与显式选择精确相等。
默认仍要求全部claim;空选择/重复/未知claim拒绝;未运行的claim不输出PASS。
不修改任何predicate、schema、求值判据;四项人工控制见新增测试。

### 15.2 两个producer的首次运行与verifier

`T/verify_anchors.py`只开放item3/item4,无item5入口;输出`output.json`为原始
schema事实,不含verdict。`raw.json`保存源区段、完整调用轨迹、异常内容、
隔离fixture目录状态与子进程exit。verdict独立由已冻结判据的CLI生成。

| claim | producer exit | verifier原始输出 | verifier exit | 原始事实/判定证据 |
|---|---|---|---|---|
| OBS-1.item3-predicate | 0 | `{"claim_id":"OBS-1.item3-predicate","verdict":"PASS"}` | 0 | `E/part2/e1-item3/{output,raw,context}.json`;`e1-item3-verifier.log` |
| OBS-1.item4-anchors | 0 | `{"claim_id":"OBS-1.item4-anchors","verdict":"PASS"}` | 0 | `E/part2/e1-item4/{output,raw,context}.json`;`e1-item4-verifier.log` |

各命令精确argv/cwd/env/exit在同名`*.command.json`,可直接复跑,不以本表缩写
代替原始命令。item3验证PASS后才运行item4;没有改动或重生成失败事实。

item3:AST机械selector命中1处BoolOp.And,同receiver的exists/is_symlink;
四场景分别为悬空链接`FileExistsError`且code ABSENT、live链接
`GerritError/SOURCE_DIR_UNSAFE`、真实目录与不存在目录均正常建目录。
产出记录了完整异常message与执行后路径状态,不是只记期望code。

item4:表六行保留单元格原文,六个FunctionDef/Call selector各命中1处。
六调用面分别执行默认/注入TimeoutExpired/SIGINT/SIGTERM;另对完整fetch流程
query/init/fetch/checkout逐点注入超时与两种信号,合计36条观察。
signals在独立子进程真实`os.kill`触发:各SIGINT exit=-2,SIGTERM exit=-15,
不是用异常文字伪造信号。查询阶段sentinel字节和目录保持不变;
git各阶段旧sentinel已被重置、destination仍存在。源码的重置/建目录是真实执行,
外部git/ssh均为fake runner,无真实网络,不把stub成功当成真实Gerrit/clone验证。

§5要求专项:exclude超时/SIGINT/SIGTERM均观察到workdir marker PRESENT
(原字节hash已存)、protected marker ABSENT、exclude_completed=false。
故query/git残留**须区分**,表最后一格与本次观测一致。
`E/part2/e1-observation-summary.log`是对raw JSON的机械汇总,不是第二份期望。
未运行item5、未枚举其依赖的读取方全集,未把第六格观测冒充item5完成。

### 15.3 DIFF-03:悬空链接的message新值来源仍未定义

| ID | 状态 | 原文位置 + 困难 | 候选处置(未实施) |
|---|---|---|---|
| DIFF-03 | CLOSED (2026-10-07) | 勘误后terminal §3第1454-1458行的“预期差异”仅钉code/type;§6第1516-1517行要求精确差集、第1526行要求message必填。E1-1第2082-2091行只准四类来源,E1-2第2093-2106行的消息派生明确仅适用于TimeoutExpired,未覆盖悬空链接。item3 raw `/observations/0/outcome/exception/value/message`实测旧值为`[Errno 17] File exists: '<dest>'`;相邻live场景和当前gerrit.py第236-238行的安全分支消息为`source directory is a symlink: <dest>`。让悬空输入进入这个既有分支还会改变message,但无法从获准的§3预期差异条目取得该message的新值/派生规则。现有实现字符串可证明缺口,不是实现方可自行追加的第五类新值来源。 | 附录C勘误2 E2-1批准`EXISTING_BRANCH_OUTPUT`,锚定ANCHOR-3与LIVE_SYMLINK_TO_DIR的既有观测,代入悬空场景路径。第16.2节自检逐字相等(exit0);此来源缺口已关闭,不因DIFF-04重开。左栏保留勘误1时期的停止原因及原行号。 |

原始实测摘录(未改写产出):

```text
DANGLING_SYMLINK:
  type=FileExistsError
  message=[Errno 17] File exists: '/tmp/p49-item3-vy6s9vtw/DANGLING_SYMLINK/destination'
  code={"state":"ABSENT"}
LIVE_SYMLINK_TO_DIR:
  type=GerritError
  message=source directory is a symlink: /tmp/p49-item3-vy6s9vtw/LIVE_SYMLINK_TO_DIR/destination
  code={"state":"VALUE","value":"SOURCE_DIR_UNSAFE"}
```

证据:`e1-dangling-message-evidence.log`直接jq提取raw字段;
`e1-source-dir-message.log`为固定树精确函数名rg;
`e1-message-rule-scope.log`为新hash规则文档的原文定位。对应command.json均exit0。
这不是claim判红:两项claim仍PASS;是§6登记来源的独立停止项。
DIFF-01/02不重开,勘误1已生效。**本轮新增停止项1条,当前OPEN总数1条。**

### 15.4 工具自检与本轮未交付项

| 验证 | 实测输出 | exit/证据 |
|---|---|---|
| verifier+机械selector人工控制 | `111 passed in 0.92s` | 0;`e1-unit-tests.command.json/.log` |
| mypy(两工具+两测试) | `Success: no issues found in 4 source files` | 0;`e1-tools-mypy-final.*` |
| ruff(同上) | `All checks passed!` | 0;`e1-final-ruff.*` |
| py_compile(同上) | 空输出 | 0;`e1-py-compile.*` |
| 冻结registry核对 | `registry_valid claims=15 canonical_hash=8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6` | 0;`e1-approved-hashes.*` |

开发时首次mypy有6项工具注解错误,修正后复跑全绿;初次输出保留在
`e1-tools-mypy.log`,不冒充首次即绿。发生在任何producer首跑之前,
不涉及修predicate/重写产出。采集后工具源码未再修改。

`scenario_manifest.json` / `result_schema.json` / `expected_diff.json`尚未生成;
门禁及七条准入证伪仍**NOT_RUN**,命令/exit=N/A。不存在已登记差异的来源清单,
不能把空清单或两个claim PASS当成§6门禁通过。旧值事实已有上述两份raw证据,
续跑时可按hash复用;新值只能在裁决DIFF-03后依获准规则登记。
生产源码及已冻结predicate/exemptions零diff,干净观测工作区status空;
主树既有无关修改/删除/untracked稿保持不动。下一步只等DIFF-03裁决,
不启动其它producer或生产实施。

## 16. 勘误2入库与复用预检停止(2026-10-07)

### 16.1 原字节入库、规则范围与不变量

`git pull --ff-only origin clang-fix-campaign` 输出 `Already up to date.`;
开工HEAD为 `27fb46077d2c3c91197bcedb534995f6987c9ef5`。
批准文件已在主工作树目标路径,本轮未重排或改写任何字节;没有独立附件副本,
以用户给定的全长SHA核对交付原件。

| 版本 | SHA-256 | 证据 |
|---|---|---|
| 勘误前 | `66fd8684950004524ae7d86fb4e29328a1998ba48985a944ad39ae4d03a8598c` | 原始入库记录;不是本轮文档来源 |
| 勘误1 | `d44584592b54bfaf1406c13369da5f2f6a5894fc3dd8de04b3905eadd6213c3f` | `git show 27fb460:docs/clang-fix-campaign/p49-terminal-batch-design-v1.31-FROZEN.md`;既有OBS采集时规则来源保持此值 |
| 勘误2 | `73dad3c6f2f30541998a228cfb05f83718cd1273e2948b4d23b13d0941b6079e` | 本轮规则来源;与用户提供值完全一致 |

`E/part2/e2-intake-diff-verified.command.json/.log` 保存完整命令与原始diff:

```text
append_only=PASS additions=27 deletions=0
insertions=[('insert', 4, 4, 4, 5), ('insert', 2108, 2108, 2109, 2135)]
```

两段均为插入:文首勘误2生效行、附录C末尾勘误2。没有删除或修改旧行。
E2-1关闭DIFF-03;E2-2将timeout关键字差异登记扩至**所有经过新签名的场景**,
含默认、外部中断以及§3/§5中的相应调用,不是只扩默认场景。必须逐调用、逐场景登记;
仍不允许全局掩码或省略字段。超时结果旧值依§4取ABSENT,其它旧值须有OBS字段。

本轮只读复核在固定干净工作区执行:
`/home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6`;
HEAD=`43a6aa625f27da46daba190657bf62256080c68e`,
tree=`ca9331190e878af465e7968fe56e735585a5866e`,status为空。
上轮`/tmp/p49-a0-baseline-v12-43a6aa6`已不存在;本轮建立仅供读取JSON的独立
stdlib环境`/tmp/p49-e2-artifact-check-43a6aa6`,清除PYTHONPATH/MYPYPATH及pytest环境覆盖。
首次普通venv创建因缺ensurepip失败;改用`python3 -m venv --without-pip`成功,
未安装项目、未import生产模块。这里不是B-0或生产行为复跑。

`e2-reuse-integrity.*` exit0核对下列原件均与`27fb460`逐字节一致,
且raw SHA与各claim证据引用相符:

| 原件 | SHA-256 |
|---|---|
| `e1-item3/raw.json` | `cdd0c1065c458ae80d7a0a7440c4bdf6c1df4ff15ad77bb9ded760ccb7071bd5` |
| `e1-item4/raw.json` | `7a8b93b5ffe31511c9e93da06441f41c817be4b341e079ac29aad2f7529cdfe2` |

同一日志还核对两组output/context未变、producer源码未变且未执行,
predicates/exemptions与`6601cfc`原字节一致;canonical hash分别仍为
`8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6`与
`4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`。
不把旧OBS中的规则SHA重写成勘误2SHA;采集来源与本轮登记规则来源分别留痕。

### 16.2 E2-1相邻观测自检

命令、完整代码参数与输出:`e2-live-message-selfcheck.command.json/.log`,exit0。
只读既有item3 JSON,未运行producer。ANCHOR-3 selector与`matched_count=1`
取自`e1-item3/output.json`;相邻观测路径:
`e1-item3/raw.json#/observations/1/outcome/exception/value`。

```text
observed_live_message=source directory is a symlink: /tmp/p49-item3-vy6s9vtw/LIVE_SYMLINK_TO_DIR/destination
expected_live_message=source directory is a symlink: /tmp/p49-item3-vy6s9vtw/LIVE_SYMLINK_TO_DIR/destination
E2-1_LIVE_SELF_CHECK=PASS exact_string_equal=true
EXISTING_BRANCH_OUTPUT(Erratum2/E2-1)=source directory is a symlink: /tmp/p49-item3-vy6s9vtw/DANGLING_SYMLINK/destination
derived_value_status=NOT_REGISTERED; full Section6 gate blocked by missing observations
```

这证明E2-1形式成立,不代表三个派生规则的门禁已实现或通过。

### 16.3 DIFF-04:现有产出不足以闭合§6改前结果与场景

| ID | 状态 | 原文位置 + 实测困难 | 候选处置(均未实施,待人工裁决) |
|---|---|---|---|
| DIFF-04 | CLOSED (本轮设计方裁决,FatTank确认) | 当前冻结稿§6第1525-1533行要求封闭场景及必填字段,第1530行明确要求protected marker既有读取方结果;§5第1499行与第1502行要求marker写入中断场景。现有item3/item4产出只有marker存在状态/原字节SHA,没有读取结果;没有marker写入中断的观测。上轮任务明确“缺字段则停止报告”,且只能复用产出。 | 原prompt混淆门禁双跑与OBS采集;两者分开。E1-1旧值来源仅约束DIFF_SET登记,不约束其余字段的双跑取值。读取方全集取自item5;门禁改前实跑移至第3段。本轮交付结构、登记与人工控制,不补造读取结果、不重跑producer。裁决不改冻结稿,第17节落实。 |

具体证据(同一停止项的两个缺口):

1. `e1-item4/raw.json#/observations/20/protected_marker`(`surface6-none`)
   为 `{"state":"PRESENT","sha256":"dc4eaeb7c6b3081096788fdc6bd3ec6eb38bae11eade8bfe4a63b0f1e0537af1"}`。
   原始对象无读取方返回/异常结果;producer `verify_anchors.py:71`的`marker_state`
   也只采存在与SHA。不能由存在状态或SHA推导读取结果。
2. item4的全部`residual_obs.injected_at`只有exclude subprocess与fetch
   query/init/fetch/checkout故障注入;无marker写入中断。`surface6-SIGINT/SIGTERM`
   的注入点是exclude,不是§5(ii)的marker写入。item3有4份观测,item4有36份;
   这40份是既有观测记录数,**不是已冻结scenario_manifest的场景数**。

`e2-reuse-coverage-verified.command.json/.log`保存按原JSON计算的缺口检查,exit1:

```text
recorded_marker_write_sites=[]
missing_evidence=["Section6 existing-reader outcomes missing from the PRESENT marker observation", "Section5(ii) marker-write interruption has no archived residual observation"]
scope=artifact preflight only; NOT Section6 admission gate; no claim producer executed
status=STOP_DIFF04
```

item5上轮已明确未运行,其读取方全集依赖第3段名字兜底引擎。本停止项是
**输入证据完整性不足**,不是新的取值来源争议,也不是已冻结claim判红。
上轮两claim PASS保持历史事实,本轮没有重新执行producer或重新宣称verifier通过。
不通过扫临时目录或临时调用读取方绕过“只复用”限制。

### 16.4 本轮交付边界与未执行项

| 项目 | 状态/计数 | 命令及exit |
|---|---|---|
| 勘误2原字节与仅追加 | PASS;27新增/0删除 | `e2-intake-diff-verified.command.json`,exit0 |
| 旧产出SHA复用与冻结JSON不变 | PASS | `e2-reuse-integrity.command.json`,exit0 |
| E2-1相邻消息形式 | PASS;精确相等 | `e2-live-message-selfcheck.command.json`,exit0 |
| 复用输入完整性 | STOP_DIFF04 | `e2-reuse-coverage-verified.command.json`,exit1;非门禁准入证伪 |
| scenario_manifest/result_schema/expected_diff | NOT_CREATED;场景数与NO_DIFF/DIFF_SET计数N/A | 未执行;不是0场景通过 |
| 每条DIFF_SET来源清单 | N/A,尚无登记 | 新值来源规则已生效;缺旧观测不得补造清单 |
| §6正常对照及七条准入证伪 | NOT_RUN | 命令/exit均N/A;不得用上述预检替代 |
| 生产/测试/冻结predicate/exemptions/producer源码 | 零改动 | 本轮只入库文档与只读复核证据 |

所有本轮证据命令的完整argv(含`python -c`源码)、cwd、环境、HEAD/tree、exit及
输出SHA保存于同名command.json;读取日志不依赖未提交的临时驱动脚本。
首次仅追加自检误把文首插入位置当作零基索引3,实际为4,exit1原文保留于
`e2-intake-diff.*`;随后用“勘误1生效行之后”的锚定关系复验通过,
没有修改批准的输入。初次`e2-reuse-coverage.*`是人工停止说明输出;
最终证据为`-verified`版本按读取到的缺口决定exit,不冒充七条负控制之一。

DIFF-01/02/03 CLOSED;**本轮停止报告1条,当前OPEN总数1条(DIFF-04)**。
不启动A₀第3段、item5或任何生产改动;等补采/分段裁决。

## 17. 第2段收尾:结构、登记与人工准入证伪

### 17.1 DIFF-04关闭与执行边界

设计方裁决、FatTank确认(本轮任务):原prompt把§6门禁自己的双跑与OBS采集
混为一谈。OBS只为差异登记提供旧值事实;读取结果、marker写入中断残留这些
不变字段由门禁自己的双跑直接比较,无需从OBS补造旧值登记。
读取方名单以已核验的`OBS-1.item5-order`全集为准,不得手挑成员。

**§6改前实跑:PENDING_SEG3。** 第3段名字兜底引擎及item5就绪后才接入真实
collector。本段的`Gate.collect/dual_run`仅以人工callback运行,不导入生产代码,
不执行真实改前/改后采集,不运行任何OBS producer。A₀整体未宣称完成。
冻结稿保持SHA `73dad3c6f2f30541998a228cfb05f83718cd1273e2948b4d23b13d0941b6079e`。
`git pull --ff-only origin clang-fix-campaign`为`Already up to date.`,
开工HEAD=`77f55ebeb2c4167de69bb1a848cd6dcb358088f2`。

### 17.2 交付与封闭规则

以下均在`docs/clang-fix-campaign/tools/`:

| 产物 | 本段作用 |
|---|---|
| `p49_terminal_data/scenario_manifest.json` | 30场景封闭枚举:§3四输入、§4六调用面各none/timeout/SIGINT/SIGTERM、§5两个中断时点(SIGINT固定fixture)。记录fixture、逐调用及旧kwarg引证 |
| `p49_terminal_data/result_schema.json` | 返回值、异常type/code/message、warnings/action、calls、destination/worktree存在状态及路径状态、workdir marker、exclude完成状态、exit code均必填。protected marker必含exists/原字节sha256/readers |
| `p49_terminal_data/expected_diff.json` | 每场景恰一模式;每项具old/new来源及非空理由,派生值不写占位串 |
| `p49_terminal_data/expected_diff_sources.md` | 从登记JSON生成的56行来源清单;逐项列场景/字段/旧OBS指针或§4ABSENT/新权威节与派生规则。完整source对象的文件SHA、原文quote、规则inputs在JSON内 |
| `build_terminal_diff_data.py` | 只读批准文档与存档JSON生成登记,不是producer。`--check`验证四个生成物原字节一致;默认拒绝覆盖已有文件 |
| `terminal_expected_diff.py` | 封闭场景/结果与来源校验、三种派生规则精确求值、精确差集比较、注入式双跑框架。真实compare入口须提供before/after/item5产物 |
| `terminal_diff_controls.py` | 明示ARTIFICIAL的正/反结果对象;不作为OBS或改前实跑证据 |
| `tests/unit/test_terminal_expected_diff.py` | 本轮61项人工测试,包含双跑callback接线、来源错行、三规则非前缀比较及完整性控制 |

结果外层、marker及reader记录、调用参数记录均封闭;return_value与reader返回
负载显式为JSON值(返回形状异构),**完整比较其全部内容**,不是忽略嵌套字段。
`ABSENT`与`VALUE(null)`分开;bool不作为int;不做路径替换、全局掩码、前缀比较。
未登记字段一律要求相等,没有“不重要字段”跳过分支。
运行参数readers非空且唯一,每个场景实际readers集合须恰等于该参数;
真实CLI从item5产物提取名单,两中断场景的名单须相同。调用者须先用冻结
verifier核验item5。当前人工名单明确名为`ARTIFICIAL_READER_DO_NOT_USE_AS_ITEM5`。

§5两行的`obs_ref`只为经过exclude调用的timeout旧关键字提供引证:
exclude中断用`e1-item4/raw.json#/observations/22`,marker写入中断用
`#/observations/20`的既有exclude调用。**没有把后一条默认场景当成marker
写入中断实跑**,也没有从该引用推导任何reader结果或磁盘残留。

### 17.3 场景计数、56条登记来源与精确值

`gate-structure/final-structure.log`:

```text
STRUCTURE_SOURCES=PASS scenarios=30 NO_DIFF=0 DIFF_SET=30 registrations=56
REAL_BEFORE=PENDING_SEG3
```

NO_DIFF为0不是放宽不变性:四个§3场景都先经query,REAL_DIR/ABSENT还经过
后续git调用;§5两个时点都经过exclude。按E2-2,这些场景与§4场景全部至少有
一条新增timeout kwarg,所以场景模式都是DIFF_SET;除登记字段外全部逐字段相等。
未额外造一个场景凑NO_DIFF数。NO_DIFF模式本身另有人工正/反单测。

| 登记组 | 条数 | 旧值来源 | 新值来源 |
|---|---:|---|---|
| 逐调用timeout | 38 | 对应OBS `trace/<i>/kwargs`成员中timeout不存在,按hash读取并检查;不是推测ABSENT | 附录C/E2-2;默认/中断为VALUE(null),timeout为该fixture的0.125 |
| 悬空链接type/code/message | 3 | item3 `observations/0/outcome/exception/value/{type,code,message}` | §3 type/code;E2-1 `EXISTING_BRANCH_OUTPUT` + ANCHOR-3 + LIVE邻例 + 本fixture destination |
| fetch query/git与submit git超时 | 9 | §4新timeout场景结果为ABSENT | skill-5 §3.2⑥相应行的type/code单元格;E1-2 `TIMEOUT_MESSAGE_FROM_EXC` |
| shared git/exclude超时 | 4 | 同上§4ABSENT | 相应单元格的WorkspaceViolation;E1-2 `GIT_TIMEOUT_PREFIX_PLUS_EXC`(一个半角空格) |
| ls-remote超时warnings/返回列表 | 2 | 同上§4ABSENT | E1-2固定列表项`target_head_unknown:timeout`,不附原异常文本;本fixture为helper返回面,action仍由双跑直接比较 |

逐条清单见[expected_diff_sources.md](../../tools/p49_terminal_data/expected_diff_sources.md);
登记JSON是唯一机器决策表,清单只是生成视图。
旧来源实际计数:`OBS_ABSENT_TIMEOUT=38 / OBS_VALUE=2 / OBS_STATE=1 /
ABSENT_SECTION4=15`。新来源实际计数:`TIMEOUT_KWARG=38 / LITERAL=10 /
TIMEOUT_MESSAGE_FROM_EXC=3 / GIT_TIMEOUT_PREFIX_PLUS_EXC=2 /
EXISTING_BRANCH_OUTPUT=1 / TIMEOUT_WARNING=2`。

三种派生规则均在固定fixture上算出精确字符串;超时使用存档cmd/timeout构造
标准库TimeoutExpired并复核其str与旧注入消息一致;E2-1重新核对既有LIVE观测
消息形式再代入悬空路径。来源quote须落在声明章节,映射表须对应本调用面单元格,
不能因相邻行同为GerritError而借用错行。

### 17.4 实跑命令、准入证伪与质量闸门

最终证据目录:`E/part2/gate-structure/`。每个`final-*.command.json`含完整
argv/cwd/环境/HEAD/tree/工具与数据SHA/exit;同名log为原始合并输出。
工具在固定干净工作区运行(HEAD/tree同§16.1),规则与存档通过主树的绝对路径
只读加载。独立环境`/tmp/p49-a0-gate-seg2-43a6aa6`:
Python3.12.3 / pytest9.0.3 / mypy2.0.0 / ruff0.15.12;
清除PYTHONPATH/MYPYPATH/pytest覆盖,禁自动加载pytest插件,未安装生产包。

可复现命令(在仓库根,`P`为上述独立环境python,`T`为tools绝对路径):

```bash
P=/tmp/p49-a0-gate-seg2-43a6aa6/bin/python
T="$PWD/docs/clang-fix-campaign/tools"
env -u PYTHONPATH -u MYPYPATH "$P" "$T/terminal_expected_diff.py" check
env -u PYTHONPATH -u MYPYPATH "$P" "$T/build_terminal_diff_data.py" --check
env -u PYTHONPATH -u MYPYPATH "$P" "$T/terminal_diff_controls.py" normal
```

以下每行命令均为`env -u PYTHONPATH -u MYPYPATH "$P" "$T/terminal_diff_controls.py" <参数>`:

| §6控制 | 参数 | 实际exit | 拒绝原因 |
|---|---|---:|---|
| 正常对照 | `normal` | 0 | `EXACT_DIFF=PASS` |
| ①额外变化 | `extra-change` | 1 | `DIFF_PATHS: extra=['/action'] missing=[]` |
| ②漏改登记项 | `missed-change` | 1 | `DIFF_PATHS: extra=[] missing=['/calls/0/kwargs/timeout']` |
| ③空理由 | `empty-reason` | 1 | `EMPTY_REASON` |
| ④不可能的登记 | `impossible-registration` | 1 | `REGISTRATION_PATH_CLOSED_SET`;未获授权的action变化在登记层即拒绝 |
| ⑤缺mode | `missing-mode` | 1 | `MODE_MISSING_OR_UNKNOWN` |
| ⑤未知mode | `unknown-mode` | 1 | `MODE_MISSING_OR_UNKNOWN` |
| ⑥NO_DIFF带differences | `no-diff-with-differences` | 1 | `CLOSED_FIELDS: NO_DIFF` |
| ⑦空DIFF_SET | `empty-diff-set` | 1 | `EMPTY_DIFF_SET` |
| 读取方空列表 | `readers-empty` | 1 | `READERS_EMPTY_OR_MISSING` |
| 读取方缺失 | `readers-missing` | 1 | `READERS_EMPTY_OR_MISSING` |

⑤两种非法形态分别运行,不把控制数改写成八条。④另有纯比较器构造式单测
`test_registered_but_impossible_difference_cannot_pass_exact_set_comparison`,
证明即使越过登记准入,登记变化未实际发生也会被精确差集拒绝。

| 验证 | 命令/最终证据 | 实际exit与原文 |
|---|---|---|
| 结构/来源 | `terminal_expected_diff.py check`;`final-structure.*` | 0;上列30/0/30/56 |
| 生成物一致 | `build_terminal_diff_data.py --check`;`final-regeneration.*` | 0;`REGISTRATION_DATA=MATCH scenarios=30` |
| 人工测试及既有回归 | `python -m pytest tests/unit/test_terminal_expected_diff.py tests/unit/test_terminal_predicates.py tests/unit/test_terminal_anchors.py -vv`;`final-unit-tests.*` | 0;`172 passed in 2.96s`(新增61+既有111) |
| mypy | 三个新工具+新测试;`final-mypy.*`完整argv | 0;`Success: no issues found in 4 source files` |
| ruff | 同上;`final-ruff.*` | 0;`All checks passed!` |
| py_compile | 同上;`final-py-compile.*` | 0;空输出 |

开发中ruff先报20项格式/未使用import,格式化后剩一条长行已修正;
mypy首次一项测试fixture类型推导错误,显式注解后通过。未将开发首跑描述为全绿。
首次归档测试171全绿后补了“同异常类型但引用错行”反例,最终172全绿;
`final-*`对应最终工具版本,早期证据保留不覆写。未重跑生产全量/B-0,
上述172只证明门禁工具与人工控制,不是新的生产基线。

### 17.5 完整性、挂账与停点

`final-integrity.*` exit0记录三个生成物canonical SHA-256:

| 文件 | canonical SHA-256 |
|---|---|
| scenario_manifest.json | `42e7955d7b79123cf450893df076a64e4edfd858b4466a8ce053340fb3e552e0` |
| result_schema.json | `9def71e68aaa114f9f64cf03d2fbefc125f28bb80735055f41b5b412d8eeaf96` |
| expected_diff.json | `e129c5a8ac060a3ced28383d4c0605980e5f9657e6939661f3866e0d516cb824` |

同一命令证:生产源码、P4.5 design.md、release快照零diff;两份冻结JSON与
6601cfc原字节一致;item3/item4的raw/output/context与27fb460原字节一致。
本轮未改冻结稿、既有verifier或producer实现,未改既有OBS产出。
原有.gitignore修改、无关文档删除与untracked历史稿不纳入提交。

DIFF-01..04全部CLOSED;**本轮停止报告0条,当前OPEN停止项0条**。
**挂账不是完成**:§6改前实跑PENDING_SEG3;依赖第3段名字兜底引擎、item5
读取方全集及已核验的item5产物。真实双跑须与人工控制分开归档,不得复用人工
磁盘/reader值。push后停止,不启动第3段或生产实施。
