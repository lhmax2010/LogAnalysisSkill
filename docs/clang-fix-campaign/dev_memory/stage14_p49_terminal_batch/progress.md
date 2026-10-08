# P4.9 末终止批次进度与实施前复述

状态: READY_FOR_REVIEW。更新日期: 2026-10-08。实现验收完成,等待设计方核验与一家评审签批;
不在此提前宣布 P4.9 CLOSED。当前终态与证据导航见第42节。
判定条件 v1.2 取代 v1.0/v1.1 作为编码来源,两旧版本保留。
PRED-01..05 全部 CLOSED;编码已由设计方核对、FatTank 批准并于
6601cfc 单独冻结(第12节)。第15节记录 item3/item4 首跑及 verifier PASS。
勘误11已核对原字节及SCAN-07;DIFF-01..04、SCAN-01..09 CLOSED。
SCAN-09按E11-5以“被勘误11取代”关闭,不是修复旧静态发现规则。
当前执行计划以E11两阶段和第29节以后批准的轻量裁决为准,取代冲突的旧A0
前置。PHASE1-01/02已闭合:读取方为live非tests的4函数,item5判绿,
30场景改前完成;A/B各自双跑通过。C01-C13已按审批包逐组验证完成。
PHASE2-09已修复并复验;90 checker相对43a6aa6无新增失败,3条既有问题
仍列carried-over-issues.md,不冒称全部历史控制已绿。旧停止记录作为历史保留。
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
| A06 | §1.1/1.1c;B-9;E10 | `T/terminal_scan.py`, `T/shim_inventory.py`, `T/terminal_callable_ids.py`;`E/raw_findings.json`, `E/B-9-shapes.json`;`X/candidates/`;`U/test_terminal_shim_inventory.py`, `U/test_terminal_callable_ids.py` | MODULE/REEXPORT/INLINE/PROXY 全扫,A/B/D 与代理各种 callable;零命中显式记录;ID 无行号,span 带 guard,all/import 同删同留;E10组件已落,全集因SCAN-09未完成(§27) |
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

## 18. 勘误3:超时场景的真实旧值与不变消息

### 18.1 入库、触发原因与仅追加证据

设计方在核对`8e1437d`时发现:§4的“超时场景旧值不存在”与item4已经采到的
TimeoutExpired结果冲突。如果门禁改前实际注入异常,登记ABSENT必红;如果
不运行改前一侧,残留parity无法取证。FatTank批准勘误3,不是实现方改判据。

开工`git pull --ff-only origin clang-fix-campaign`: `Already up to date.`;
HEAD=`8e1437d562517be7f3085e3da8f1f9e0072f04e6`。
批准文件已位于目标路径,本轮原字节纳入,未重写正文或附件。

| 版本 | SHA-256 |
|---|---|
| 勘误2后、勘误3前 | `73dad3c6f2f30541998a228cfb05f83718cd1273e2948b4d23b13d0941b6079e` |
| 勘误3生效 | `7b8531fdd9bcb4b2ecf8f3576eab6285f09f4b22fb1b212775939dbe72d19200` |

证据目录为`E/part2/erratum3/`,其中`final-intake.command.json`保存完整命令,
`final-intake.log`含对`8e1437d`的原始`git diff --unified=3`与机械断言:

```text
APPEND_ONLY=PASS additions=25 deletions=0
```

两个insert区段分别为文首勘误2生效行之后的一行、附录C末尾勘误3;
旧行全部原字节保留。权威文档/本报告的完整性由本次Git commit外部锚定,
不在文件内记录自身SHA或本次commit的自指值。

### 18.2 E3运行计划、旧值绑定与逐场景登记

六个timeout场景新增封闭`before_run`对象:同一fixture、同一调用处注入
`subprocess.TimeoutExpired`,不传timeout参数;保留原来的fixture超时值供
改后使用。记录E3-1原文/文档SHA与同场景`injection_ref`。
这是运行计划,**本轮没有执行改前实跑**。

E3-2取代§4旧ABSENT来源:门禁拒绝`ABSENT_SECTION4`,每项结果旧值须使用
`e1-item4/raw.json`中同一场景的精确outcome指针。远程告警由helper的
`outcome/return_value`同时承载return_value和warnings;未新造OBS字段。
比较前还校验超时旧结果的return/type/code/message/warnings投影与该观测
逐字一致,防止改前/改后两侧同时写错不变消息而伪绿。

| 场景 | 调用面 | 旧OBS行 | 全部登记字段(JSON Pointer) |
|---|---|---|---|
| surface1-timeout | fetch-query | observations/1 | `/calls/0/kwargs/timeout`, `/exception_type`, `/exception_code` |
| surface2-timeout | fetch-git | observations/5 | `/calls/0/kwargs/timeout`, `/exception_type`, `/exception_code` |
| surface3-timeout | submit-git | observations/9 | `/calls/0/kwargs/timeout`, `/exception_type`, `/exception_code` |
| surface4-timeout | submit-remote | observations/13 | `/calls/0/kwargs/timeout`, `/warnings`, `/return_value` |
| surface5-timeout | shared-run-git(manifest名shared-git) | observations/17 | `/calls/0/kwargs/timeout`, `/exception_type`, `/exception_message` |
| surface6-timeout | shared-exclude | observations/21 | `/calls/0/kwargs/timeout`, `/exception_type`, `/exception_message` |

前3面消息均为str(exc),**不登记**,出现该登记即
`UNCHANGED_TIMEOUT_MESSAGE_REGISTERED`。shared两面无code登记,消息按E1-2
逐字增加`GIT_TIMEOUT: `;remote旧列表的异常文本换为固定timeout告警码。
timeout关键字仍按E2-2逐调用登记,不以全局掩码处理。

`final-structure.log`(exit0):

```text
STRUCTURE_SOURCES=PASS scenarios=30 NO_DIFF=0 DIFF_SET=30 registrations=53
REAL_BEFORE=PENDING_SEG3
```

53=38条kwargs+3条悬空链接结果+12条超时结果;较上轮56减少3条不变消息。
完整来源清单已重新生成:
[expected_diff_sources.md](../../tools/p49_terminal_data/expected_diff_sources.md)。
`final-regeneration.log`: `REGISTRATION_DATA=MATCH scenarios=30`,exit0。
第17节的56条与ABSENT说明是勘误前历史,由本节修订,历史证据不覆写。

### 18.3 人工控制与门禁测试

仍在§9.2干净工作区执行,HEAD=`43a6aa625f27da46daba190657bf62256080c68e`,
tree=`ca9331190e878af465e7968fe56e735585a5866e`;复用独立工具环境
`/tmp/p49-a0-gate-seg2-43a6aa6`,清除PYTHONPATH/MYPYPATH/pytest覆盖,禁自动插件。
工具与数据从主树绝对路径只读加载,每份command.json记录实际argv、cwd、
HEAD/tree、环境、exit、输入文件SHA和原始输出SHA。

可复现(仓库根设置`T="$PWD/docs/clang-fix-campaign/tools"`,
`P=/tmp/p49-a0-gate-seg2-43a6aa6/bin/python`):
`env -u PYTHONPATH -u MYPYPATH "$P" "$T/terminal_diff_controls.py" <参数>`。

| 控制 | 参数 | 实际exit | 原文要点 |
|---|---|---:|---|
| 正常对照 | normal | 0 | EXACT_DIFF=PASS |
| ①额外变化 | extra-change | 1 | DIFF_PATHS: extra=['/action'] missing=[] |
| ②漏改登记项 | missed-change | 1 | DIFF_PATHS: extra=[] missing=['/calls/0/kwargs/timeout'] |
| ③空理由 | empty-reason | 1 | EMPTY_REASON |
| ④不可能登记 | impossible-registration | 1 | REGISTRATION_PATH_CLOSED_SET |
| ⑤缺mode/未知mode | missing-mode / unknown-mode | 各1 | MODE_MISSING_OR_UNKNOWN |
| ⑥NO_DIFF带differences | no-diff-with-differences | 1 | CLOSED_FIELDS: NO_DIFF |
| ⑦空DIFF_SET | empty-diff-set | 1 | EMPTY_DIFF_SET |
| 读取方空/缺失 | readers-empty / readers-missing | 各1 | READERS_EMPTY_OR_MISSING |
| E3新增:错误登记fetch消息变化 | unchanged-timeout-message | 1 | UNCHANGED_TIMEOUT_MESSAGE_REGISTERED |

原始输出为`final-control-<参数>.log`,命令为同名command.json。七条规范控制、
两个读取方控制与一个E3新增控制分别记账,不合并计数。

| 验证 | 命令(参数完整形式见同名command.json) | exit与最终原文 |
|---|---|---|
| 门禁全体单元测试 | `python -m pytest tests/unit/test_terminal_expected_diff.py tests/unit/test_terminal_predicates.py tests/unit/test_terminal_anchors.py -vv` | 0;`197 passed in 3.82s`;final-unit-tests.* |
| 结构与来源 | `python tools/terminal_expected_diff.py check` | 0;30/0/30/53;final-structure.* |
| 生成物一致 | `python tools/build_terminal_diff_data.py --check` | 0;REGISTRATION_DATA=MATCH;final-regeneration.* |
| ruff | 三工具+测试文件 | 0;All checks passed!;final-ruff.* |
| mypy | 三工具+测试文件 | 0;Success: no issues found in 4 source files;final-mypy.* |
| py_compile | 三工具+测试文件 | 0;空输出;final-py-compile.* |

197=本门禁86+既有predicate/anchor人工测试111,不是新的生产全量基线。
新增控制覆盖六面旧值/登记字段、六面错场景引用、六面旧ABSENT拒绝、
三面双侧消息同时写错、运行计划缺失/传timeout/错注入处及CLI消息误登记。
全部用人工对象和既有JSON,未调用producer或真实collector。

首轮测试`196 passed,1 failed`:错场景负fixture把submit异常type指向remote
无异常的字段,实际先红MISSING_POINTER,未命中预期的来源绑定红因。
修为另一场景确实存在的同类型字段后通过,未放宽断言。ruff首跑两处行长,
拆分字符串字面量后通过;失败原文保留`unit-tests.*`/`ruff.*`,最终看final-*。

### 18.4 变更范围、完整性与停点

`final-integrity.*` exit0确认:除权威SHA引用更新外,非超时登记未变;
manifest仅六个超时场景增加before_run;result_schema原字节未变。
生产源码/P4.5 design.md/release快照零diff;predicates与exemptions原字节未变;
item3/item4全部原产物和上一轮gate-structure证据原字节未变。

暂存区`git diff --cached --check` exit2仅指向本轮原始日志:final-intake.log的
git diff上下文空行/输出尾空行,unit-tests.log的pytest失败堆栈尾空格。
为保留证据原字节及输出SHA,不清洗日志;排除本轮`erratum3/*.log`后对
源码/数据/文档重跑同一检查exit0。此为证据输出格式,不是规格停止项。

| 文件 | canonical SHA-256 |
|---|---|
| scenario_manifest.json | `28fde83aa7889c41d312bed186b90f0690feeb0dff66bee4b2e52c293807b03f` |
| expected_diff.json | `ef85c44523e9ed1fcdc62e9ab5fbda0d590f29bd54c71a6faa86bc0f3c214539` |
| result_schema.json(未改) | `9def71e68aaa114f9f64cf03d2fbefc125f28bb80735055f41b5b412d8eeaf96` |

本轮停止报告**0条**,OPEN停止项**0条**;DIFF-01..04保持CLOSED。
**§6改前实跑仍PENDING_SEG3**,等名字兜底/item5读取方全集。不运行OBS,
不执行改前实跑,不启动生产改动。原有无关改动保持原样;commit+push后停止。

## 19. A₀ 第3段:扫描注册表口径停止报告(2026-10-07)

### 19.1 开场复核与取证边界

本节为最新状态;第18节的零OPEN结论保留为上一轮历史。
先读本文件(含§2.2交付映射与§2.3消费者控制),再执行
`git pull --ff-only origin clang-fix-campaign`,exit=0,
stdout=`Already up to date.`。本轮起点为上一段提交
`cbd3a22ae6fdb6454ecc5a55254304f72a17ecd1`。

只读核对仍在§9.2工作区与独立工具环境进行:

- cwd: `/home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6`
- Python: `/tmp/p49-a0-gate-seg2-43a6aa6/bin/python`
- HEAD: `43a6aa625f27da46daba190657bf62256080c68e`
- tree: `ca9331190e878af465e7968fe56e735585a5866e`
- `git status --porcelain=v1 --untracked-files=all`: 空输出,exit=0。

证据目录为`a0-evidence/part3/preflight/`。每个`*.command.json`保存
实际argv(含可复跑的完整`python -c`程序)、cwd、环境、exit与原始输出SHA;
对应`*.log`是原始输出。诊断仅读取Git条目、文件元数据与冻结输入,
**不是OBS producer,不是正式scan_manifest,没有completion marker**。
工具/权威文档从主树绝对路径读取,未假称其存在于固定旧树。

```text
tree-and-pins exit=0
tracked_leaf_count=846
git_modes={"100644":845,"100755":1}
py_suffix_leaf_count=272
non_py_suffix_leaf_count=574
authority-kind-references exit=0
main-tracked-status exit=0
```

上述846只是`git ls-tree -rz --full-tree <tree>`的叶条目数,
不是已完成manifest的条目数,也不是扫描处理集/适用性检查已通过。
574是扩展名事实,**不把它推断成574个不受支持的Python provider**。
`tree-and-pins.log`另记录以下实际存在的非Python文本样本的Git blob、
lstat mode、大小及文件SHA: `README.md`、`pyproject.toml`、
`.github/workflows/ci.yml`。三者均可UTF-8解码且无NUL。

冻结输入实测值未变:

| 输入 | 实际指纹 |
|---|---|
| v1.31-FROZEN(含勘误1–3),原字节SHA-256 | `7b8531fdd9bcb4b2ecf8f3576eab6285f09f4b22fb1b212775939dbe72d19200` |
| predicates.json,canonical SHA-256 | `8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6` |
| measurement_exemptions.json,canonical SHA-256 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |

### 19.2 SCAN-01:provider域与全树扫描条目域的注册表接口未定

**状态:CLOSED。勘误4 E4-1/E4-2已明确两层类别与required detectors;
原字节入库及hash见§20.1。以下保留当时的问题,不代表当前仍待裁决。**
这是判据编码前的口径问题,不是claim红、不是已实跑扫描器的失败。
下列行号均对应SHA为`7b8531fd...`的当前冻结稿。

| 原文位置 | 冻结要求 | 需要裁决的接口 |
|---|---|---|
| §1.1b:L564–567 | 封闭artifact universe支持的provider仅为纯`.py`源文件、包目录(含`__init__.py`)、namespace portion;其余一律UNSUPPORTED、扩充走变更流程 | 未说明普通非provider文本是否属于这里的“其余”,以及它们在注册表中的kind如何表达 |
| §1.1e:L1284–1288(12b-1/2/3/3b/3c) | 全部tracked entry无减法;适用性由外部冻结注册表计算;每行至少一个SCANNED;查表未命中为UNSUPPORTED,未知kind阻塞,禁止默认回落 | 必须为真实存在的非Python条目得到明确的kind与required_detectors,不能用缺键/空detector集合代替处理 |
| §1.1:L357、L364–376、L420–423 | 全部tracked文本做名字兜底;文档排除也须逐条记账;C7a配置/C7b CI/C7c shell/C7d构建文件按各自类别扫描 | 它们明确在扫描输入面内,但不能直接套入三种Python provider种类;C7b的kind又依赖manifest分类 |

因此不能在实现侧自行选择以下两种不等价读法:

1. 将provider kind直接作为全部manifest条目的kind:上述README/TOML/YAML
   不在封闭支持清单,不能自行给它们受支持的查表项;会使普通文本被按
   非支持provider分流,而不是只按正文的文本消费规则处理。
2. 将entry/file kind与provider kind拆为两个域:普通非provider文本仍可
   做消费者/名字兜底扫描,但需要明确“非provider”的机械判定、注册表键、
   required_detectors及两域关系。当前正文没有给出这个接口,实现方不能
   自创NOT_A_PROVIDER豁免/默认TEXT分支,也不能偷偷扩consumer.*形态。

**候选处理,由设计方裁决后实施:**

- 方案A:明确区分完整manifest的entry/file kind与Python provider kind。
  设计方给出非provider条目的闭合分类与适用性规则,说明它们通过哪个
  detector满足12b-3b;保留三种支持provider及真正未知provider的
  UNSUPPORTED红路。文档/配置不能被排除出manifest,零命中仍记账。
- 方案B:若两域本来就共用同一个kind,按勘误流程扩充封闭kind表并逐类
  指定required_detectors;同时明确哪些只是消费载体,不得因此把任意
  非Python实现provider放行。不能仅补一个“其它均按TEXT”的默认分支。

本轮不选择方案、不改权威或predicate、不落一个临时分类器来绕过缺口。
完整检索证据为`authority-kind-references.*`,固定树实例为
`tree-and-pins.*`。恢复点是**第1块注册表可编码性确认**,不是第2块。

### 19.3 交付映射、未运行项与恢复条件

§2.2既定路径保持不变,本轮没有移动交付物或引入第二份control catalog。

| 本段块 / §2.2映射 | 当前状态 | 产物/证据 |
|---|---|---|
| 第1块:扫描基础,A03/A04/A10 | STOPPED_BEFORE_ENCODING | 仅19.1只读前置;scan_manifest/scan_matrix/completion未生成,不记SCANNED通过数 |
| 第2块:消费者识别,A09 | NOT_RUN | 20形态控制/near-miss未运行;CTRL-INTRA-PKG-PROXY保持NOT_RUN |
| 第3块:台账/候选,A05/A06 | NOT_RUN | 三段台账与四粒度候选未产出,计数N/A,不以0冒充扫描结果 |
| 第4块:8个获准claim,A15/A17 | NOT_RUN | item1-basis/seg1-staleness/seg2-form/commit-order/transition-map/proxy-count/intra-package-shim/item5-order均无新producer运行、无新verifier结论 |
| 第5块:§6改前实跑,A01 | PENDING_SEG3 | 30场景未采集,无改前文件hash;等待消费者引擎及item5读取方全集 |
| 本轮测试/mypy/ruff | NOT_RUN,exit=N/A | 未改工具、测试或生产代码;不借用上一段197通过数作为本轮验证 |

当轮停止报告新增**1条(SCAN-01当时OPEN)**,当轮OPEN**1条**;
SCAN-01已在§20按勘误4关闭;最新OPEN项以§20为准。
PRED-01..05、DIFF-01..04继续CLOSED。不存在已完成的第3段实现块commit。
本次只提交停止记录、原始诊断证据与INDEX,不把它命名或记账为扫描基础完成。
既有OBS产出、三个差异门禁数据文件、冻结predicate/豁免及设计稿均不改;
主树`.gitignore`修改、无关文档删除、untracked历史稿保持原样。
push后停下,等待设计方澄清上述kind/适用性接口后续跑。

## 20. 勘误4入库与release模块身份歧义停止报告(2026-10-07)

### 20.1 原件、仅追加证明与SCAN-01关闭

开场已读§19及§2.2交付映射。`git pull --ff-only origin clang-fix-campaign`
exit=0,stdout=`Already up to date.`;本轮起点为
`a2f197b9cb8cbdf60fee276b23f4e9f136af9c07`。
批准原件已经位于目标文件,本轮直接入库,没有重写任何正文或勘误字节。

| 版本 | 原字节SHA-256 |
|---|---|
| 勘误1–3版本 | `7b8531fdd9bcb4b2ecf8f3576eab6285f09f4b22fb1b212775939dbe72d19200` |
| 勘误4版本 | `e9b18793d3fea5755e886d55d0dbebdfc8a5d39374237fe0e05757a242ef6e9a` |

证据目录:`a0-evidence/part3/erratum4-preflight/`。
`intake.command.json`保存实际命令、完整可复跑Python程序、cwd、环境、exit
与输出SHA;`intake.log`含未清洗的`git diff --unified=3`与机械断言原文:

```text
intake exit=0
APPEND_ONLY=PASS additions=39 deletions=0 insert_blocks=2
```

两处insert精确为:旧第6行之后新增勘误4生效行;旧文件末尾追加勘误4。
除此以外所有旧行原字节保留,没有删除或替换。

**SCAN-01 CLOSED**:

- E4-1(当前冻结稿L2168–2173)将entry kind与provider kind拆为两层,
  后者只对PY_SOURCE/IMPORTABLE_BINARY求值,§1.1b的“其余”不再误用于
  普通非provider文本。
- E4-2(L2175–2193)逐类给出按序判定的封闭12类及required detectors:
  GITLINK/SYMLINK/IMPORTABLE_BINARY/PTH/BINARY/PY_SOURCE/PACKAGING/
  CI_CONFIG/SHELL/BUILD/DOC/OTHER_TEXT。未知git mode阻塞;BINARY由
  逐项记录满足行级SCANNED下界。该裁决关闭口径缺口,**不等于注册表已实现**。
- E4-3保持20个consumer.*形态及现有去处规则不变。

### 20.2 SCAN-02:全树同一点分名对应live与release两份文件

**状态:CLOSED(勘误5 E5-1/E5-2/E5-3,见§21.1)。以下保留当时停止证据。**
未排除release,未自行决定“优先live”“优先快照”“就近源码根”或“两者都算”。
不是OBS claim判红,也不是已有消费者引擎误报的实跑结论。

取证在§9.2固定干净工作区、独立Python环境执行;HEAD/tree不变:
`43a6aa625f27da46daba190657bf62256080c68e` /
`ca9331190e878af465e7968fe56e735585a5866e`。

机械方法:对完整`git ls-tree -rz --name-only --full-tree <tree>`的tracked
路径,分别读取`pyproject.toml`与`release-v1.4.0/pyproject.toml`的
`tool.setuptools.packages.find.where/include/exclude`,按各自声明的源码根
生成点分名,保留配置来源与文件路径。**这里只展示两份打包描述各自声明的
对应关系,不将它们合成实际运行环境的sys.path、不选择消费者边目标。**
两份配置的hash、源码根、全部重名对应及示例AST原文见
`module-identity.log`;完整命令在同名`command.json`。

```text
module-identity exit=0
tracked_leaf_count=846
cross_config_duplicate_module_count=85
MODULE_IDENTITY_AMBIGUOUS=ci_triage.quickbuild candidates=2 selected=NONE
```

exit=0表示只读诊断完成,不是扫描/闭合门禁通过。85是这两份打包描述下
机械导出的重名数,不是完成全套扫描后的候选数或consumer计数。

**具名实例**:

| 同一点分名 | 来源描述与文件 | 实测结构 |
|---|---|---|
| `ci_triage.quickbuild` | 根`pyproject.toml`: `tizen-ci-triage/scripts/ci_triage/quickbuild.py` | 顶层def/class=0;转发到`tizen_ci_shared.quickbuild_http`的live shim |
| `ci_triage.quickbuild` | `release-v1.4.0/pyproject.toml`: `release-v1.4.0/tizen-ci-triage/scripts/ci_triage/quickbuild.py` | 顶层def/class=12;独立历史实现,不是同一个文件/同一个blob |

实际引用为固定树
`release-v1.4.0/tizen-ci-triage/scripts/ci_triage/gbs_report.py:10–18`:

```python
from ci_triage.quickbuild import (
    DEFAULT_COOKIE_PATH,
    DEFAULT_QUICKBUILD_BASE_URL,
    HttpFetcher,
    QuickBuildError,
    _raise_if_login_page,
    _urllib_fetch,
    load_cookie_jar,
)
```

若只按点分名构图,这个引用无法唯一指定上述两份文件中的哪一份;
如果静默选live,就可能把快照实现的依赖计为待删除live shim的消费者。
这是用户点名的风险实例,**并未声称已经通过运行时import证实选错了文件**。

**对应权威位置/困难**:

- §1.1e 12b-1(当前L1285)与本轮任务第2项要求release照常入完整输入面。
- §1.1名字命中兜底(当前L355–370)从模块名/路径形态产生消费关系;
  12b-6要求同tree/run绑定,但tree本身同时包含上述两套源码根。
- E4-1/E4-2解决条目类别与detector适用性,未规定跨打包根的模块身份或
  绝对import解析优先级。选其中之一、把两者合并或忽略快照都会影响
  candidate身份/消费者归属,不是实现方可自行选择的路径表示细节。

**候选,仅供设计方裁决**:

1. 为模块身份增加明确的打包/解析上下文,规定各上下文的入口与import
   解析关系,并以(source context, module, file)保留证据。具体上下文
   边界、跨上下文引用及无法静态绑定时的出口须由设计方给出;不能由
   扫描器自定“就近”规则。
2. 若仍采用全树单一点分名空间,明确多provider名称的具名未决出口及
   可接受的消歧证据;在消歧前不产出唯一消费边,不视为零消费者。

两方案都保留release在manifest与扫描内。本轮未选方案、未以排除快照
作为候选修法。恢复条件是设计方裁决模块身份/对应规则后继续第1块。

### 20.3 冻结边界、交付状态与未运行项

`frozen-and-scope.command.json`/`.log`(exit=0)实测:

```text
predicates.json canonical=8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6
measurement_exemptions.json canonical=4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945
IMMUTABLE_AND_PRODUCTION_DIFF_EXIT=0
```

最后一项为对生产源码、release快照、tests、tools与既有part2证据运行
`git diff --exit-code`,stdout为空。没有调用任何OBS producer,没有改既有
OBS产出或差异登记,没有执行改前实跑。两次原字节指纹核验不是重新批准
predicate;冻结审批与6601cfc外部锚维持不变。

| 交付项 | 状态/结果 |
|---|---|
| 勘误4入库、SCAN-01关闭 | DONE,本commit由Git外部锚定;不在文件自记SHA |
| 第1块注册表/manifest/解析层 | STOPPED_BEFORE_IMPLEMENTATION;正式manifest/completion未产出;12类正例与2条新控制NOT_RUN,未登记假PASS |
| 第2块20形态正控制/near-miss/CTRL-INTRA-PKG-PROXY | NOT_RUN;唯一control_catalog未改 |
| 第3块三段台账/四粒度候选 | NOT_RUN;计数N/A |
| 第4块8个获准claim | 全部NOT_RUN;无新verifier结论或claim证据路径 |
| 第5块门禁改前采集 | PENDING_SEG3;30场景尚未实跑,无改前文件hash |
| 测试/mypy/ruff | NOT_RUN,exit=N/A;本轮未实现工具或新增测试 |

第4块的八项分别为item1-basis、seg1-staleness、seg2-form、commit-order、
transition-map、proxy-count、intra-package-shim、item5-order,均未运行。
各诊断命令的argv/环境/exit/原始输出与SHA已归档,不借用上一段测试数字。
本轮新增停止项**1条(SCAN-02 OPEN)**;SCAN-01、PRED-01..05、DIFF-01..04
均CLOSED。第1–5块没有完成块,不提供虚假的逐块完成commit。
本次提交仅批准的勘误原件、progress/INDEX与只读诊断证据。原有.gitignore
修改、无关删除、untracked草稿不处理。push后停止等待裁决。

暂存区`git diff --cached --check`的exit=2仅指向
`erratum4-preflight/intake.log:15`中的原始git diff上下文空行(` `)。
不清洗证据字节或重算为别的输出;排除这个原始日志重跑exit=0。
文档三文件的`git diff --check`亦exit=0。这是日志格式记录,不新增规格停止项。

## 21. A0 第3段续二:勘误5入库、上下文基础与SCAN-03停止报告

### 21.1 入库与SCAN-02关闭

开场已读§20,分支`clang-fix-campaign`;`git pull --ff-only origin
clang-fix-campaign`输出`Already up to date.`。此次批准的原件已在目标路径,
未重写内容。入库前HEAD为`c92248088dad103a1e2185d871ab69f6cff7c784`。

- 旧SHA-256:`e9b18793d3fea5755e886d55d0dbebdfc8a5d39374237fe0e05757a242ef6e9a`。
- 新SHA-256:`1c35df1cd9aeafc5511aefaa3bdd468b785af665205319d92cc6d30350be6939`。
- 批准来源:本轮FatTank授权勘误5;文件原字节hash与任务书写死值相等。
- `a0-evidence/part3/erratum5/intake.log`保存完整`git diff --unified=3`;
  同名`command.json`保存命令、原始程序、cwd、环境、exit与输入/输出hash。

```text
APPEND_ONLY=PASS additions=36 deletions=0 insert_blocks=2
EXIT=0
```

两个insert分别位于旧第7行之后和旧EOF;所有旧行原字节保留。
SCAN-02由E5-1(上下文/模块二元身份)、E5-2(本上下文优先及朝闭回退)、
E5-3(release候选仍扫描,第4段admission裁REJECTED_NOT_SHIM)关闭。
E5-3本段仅保留上下文和描述文件hash,未提前运行admission。

### 21.2 已实现的基础能力,不冒充第1块完成

新增`tools/terminal_scan.py`、`entry_registry.json`、`provider_registry.json`
和`tests/unit/test_terminal_scan.py`。包含E4按序全函数分类、E5上下文及
模块索引、精确固定tree/lstat/blob核对、原子JSON写入。工具不导入被观测
代码,不运行OBS producer。独立工具环境为Python 3.12.3;工具依赖stdlib
tomllib,声明Python 3.11+。未修改生产包的Python版本或依赖。

**边界**:这两个JSON目前只是entry/provider required-detector输入,
不是完整capability registry,也未宣称冻结。完整矩阵、五类解析层、
消费者引擎和完成标记尚未实现。对新遇到的非已支持打包描述形态仍拒绝,
不猜测源码根;当前固定树的两份pyproject均已实跑。

所有采集在§9.2干净工作区与独立环境执行:

```text
cwd=/home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6
HEAD=43a6aa625f27da46daba190657bf62256080c68e
tree=ca9331190e878af465e7968fe56e735585a5866e
venv=/tmp/p49-a0-gate-seg2-43a6aa6
PYTHONPATH/MYPYPATH unset; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
```

`manifest-input.json`与最终同字节的`manifest-final.json`是**清单输入证据**,
不是可供SEAL消费的完成扫描。每条包含路径、git mode/OID、lstat、原字节
SHA、条目类别、上下文;两份打包描述各含路径/hash/where/include/exclude。

```text
MANIFEST_INPUT entries=846 canonical=95459861ca4d8dafd4e028b3005faa5d9dc5a1d2a6ba98d4d918743c7c41f5a8
{".": 736, "release-v1.4.0": 110}
SCAN_COMPLETION=NOT_CREATED (detector matrix not yet run)
EXIT=0
```

条目类别计数:DOC=431、OTHER_TEXT=123、CI_CONFIG=1、BINARY=4、
PY_SOURCE=272、PACKAGING=2、BUILD=13;其它E4类别为0。
release的110条全部在内,无排除、无修改。

`context-regression.json`/`.log`逐个列出SCAN-02原报告的85个重名,
每名各保留live/release解析结果。原例的ImportFrom直接从release源AST读取。

```text
DUPLICATES=85 RESOLUTIONS=170 REAL_IMPORT=PASS
CONTEXT_COUNTS={".": 736, "release-v1.4.0": 110}
REGRESSION_FALLBACK_EDGES=0
REGRESSION_MODULE_IDENTITY_AMBIGUOUS=0
FULL_CONSUMER_SCAN=NOT_RUN
EXIT=0
```

上面的两个零**仅属于这组重名回归**。全树消费边/名字兜底尚未枚举,
所以全量跨上下文回退边数、消费解析歧义数均为N/A,不以回归零值代替。
模块索引自身无同上下文重复文件;这也不等价于全部引用无歧义。

### 21.3 SCAN-03: E4 required detector与九类capability对账缺映射

**状态:CLOSED(勘误6 E6-1～E6-3);以下保留当时停止证据。**
不是OBS claim红,也不是已经实现的12b-12检查器判红;这是接注册表时
发现的权威规格未闭合,未伪造一个完整四方检查器的exit。

**原文位置**(均为本次hash的冻结稿):

| 位置 | 要求 |
|---|---|
| L2183、L2194,E4-2第5类 | BINARY的required detector为二进制记录器,完成记录即SCANNED |
| L1290,12b-3c④ | 注册表与detector capability双向精确覆盖 |
| L1298,12b-12 | 非consumer的(branch,owner)四方精确相等;并明文要求九类承担方与required_detectors(kind)对账 |
| L571–592,§1.1b九类表 | 只有ledger.seg1、scan.module/reexport/inline/proxy_callable、resolve.dynamic_attr/import_redirect、provider.unsupported;无二进制记录器承担方/分支 |
| L585–590 | 控制取材须来自该detector被指定承担的类别;新增能力必须先入权威表,实现方不得自选 |
| L325–326、L2197 | consumer.*仅原子形态表;registry仅五种命名空间,E4不新增消费者形态 |

**实测反例**:固定tree确有4个BINARY条目,见`scan03.log`完整路径与hash:

```text
docs/clang-fix-campaign/review/r14-delta/change_44.diff.gz
docs/clang-fix-campaign/review/r14-delta/fix-1.diff.gz
docs/clang-fix-campaign/review/r14-round2-delta/change_45.diff.gz
docs/clang-fix-campaign/review/r14-round2-delta/fix_1_round2.diff.gz
ACTUAL_BINARY_COUNT=4
```

按E4它们不是provider,不能塞到`provider.unsupported`并阻塞;
按第5类又必须有实际记录器给SCANNED,不能把它们删出manifest。
若自行新增例如`scan.binary_record`,它不在九类表中,12b-12差集不空;
若把它当“无capability的工具辅助动作”而跳过九类对账,则自行给
required detector增加了豁免。当前正文没有授权这两种选择。
`scan03.command.json`内的诊断只打印权威表、实际条目和缺口,exit=0表示
证据提取成功,**不表示四方对账通过**。未把binary_record伪装成任何现有能力。

**候选,只供设计方裁决**:

1. 为E4新增的记录/提取能力补齐权威承担方映射与capability分支,明确
   required edge、正控制取材及四方对账覆盖域;不动consumer二十形态。
2. 明确“扫描基础记录/提取动作”与“语义检出capability”的分界,
   给前者独立的封闭登记、覆盖与证伪规则,再明文调整12b-3c/12b-12投影。
   不能只是口头说它是辅助步骤,更不能免掉BINARY的SCANNED下界。

两方案均保留release和全部条目。名字兜底/doctest提取等E4新增detector
也应在裁决中一起核对,避免只给binary补一个临时特例。
本轮未采用任何方案;未修改正文、未扩capability分支、未跳过12b-12。

### 21.4 实测命令、控制目录和保留的失败记录

以下`R=/home/linhao/Toolchain/development/LogAnalysisSkill`,
`V=/tmp/p49-a0-gate-seg2-43a6aa6`;cwd与环境同§21.2。
完整argv、环境、工具hash和原始输出在`part3/erratum5/*.command.json`/`.log`。

```sh
"$V/bin/python" -m pytest -q -o cache_dir=/tmp/p49-seg3-pytest "$R/tests/unit/test_terminal_scan.py" --junitxml="$R/docs/clang-fix-campaign/dev_memory/stage14_p49_terminal_batch/a0-evidence/part3/erratum5/foundation-tests-final.xml"
# 35 passed in 0.05s; EXIT=0
"$V/bin/python" -m pytest -q -o cache_dir=/tmp/p49-seg3-pytest "$R/tests/unit/test_terminal_predicates.py" "$R/tests/unit/test_terminal_anchors.py"
# 111 passed in 0.22s; EXIT=0; artificial-only, no OBS producer
"$V/bin/python" -m ruff check "$R/docs/clang-fix-campaign/tools/terminal_scan.py" "$R/tests/unit/test_terminal_scan.py"
# All checks passed!; EXIT=0
"$V/bin/python" -m mypy --strict --python-version 3.12 --follow-imports=silent "$R/docs/clang-fix-campaign/tools/terminal_scan.py" "$R/tests/unit/test_terminal_scan.py"
# Success: no issues found in 2 source files; EXIT=0
```

初次ruff因import排序exit=1;初次mypy沿用生产配置的Python3.10,报tomllib
不可用及3处本工具类型标注错误,exit=1。保留`ruff.log`/`mypy.log`,后两者
`*-final.log`为修正后的实测;类型检查明确针对隔离工具环境3.12,
没有改生产配置、没有忽略错误。最初调用记录器时`python`命令不存在(exit127),
未启动测试;随后使用`python3`并成功记录以上实跑。

唯一`control_catalog.json`保留原96项不变,新增E4的12类别正例、未知mode、
docs/Makefile先于DOC共14项PASS。E5五项登记为端到端NOT_RUN,各附resolver
component PASS证据;**不能用直接调用resolve的单测冒充完整消费者边控制**。
`CTRL-INTRA-PKG-PROXY`仍NOT_RUN。第2块原子20形态/near-miss未实现、未声称通过。

### 21.5 交付边界与下一步

`immutable.log`(exit=0)核验生产源码、release、P4.5 design、既有part2证据
零diff;冻结canonical hash仍为:

```text
predicates.json canonical=8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6
measurement_exemptions.json canonical=4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945
IMMUTABLE_AND_PRODUCTION_DIFF_EXIT=0
```

| 原任务块 | 本轮状态 |
|---|---|
| 1 扫描基础 | PARTIAL/STOPPED_SCAN03;输入846条与分类/上下文已取证;matrix、解析层与completion未完成 |
| 2 消费者引擎 | NOT_RUN;完整形态控制/兜底计数N/A;E5仅resolver单测 |
| 3 台账/候选 | NOT_RUN;三段条目数及四粒度计数N/A |
| 4 八个claim | 全部NOT_RUN,没有新raw/verifier结论;item1-basis、seg1-staleness、seg2-form、commit-order、transition-map、proxy-count、intra-package-shim、item5-order均未运行 |
| 5 改前实跑 | PENDING_SEG3;30场景未采集,文件hash N/A |
| 生产全量pytest/mypy/ruff | 本轮未重跑;只报告§21.4具名工具/人工fixture检查,不借用历史全量结果 |

本轮新增停止项**1条:SCAN-03 OPEN**;SCAN-02 CLOSED,其余既有关闭项不变。
没有完成的整块,因此本次是**勘误入库+已验证基础中间态+停止报告commit**,
不是第1块完成commit。待设计方裁决后从注册表能力映射继续。
原有`.gitignore`修改、4份无关文档删除、其它untracked历史稿均不处理。
提交不包含任何生产变更、冻结predicate改动或旧OBS产出改动;push后停止。

暂存`git diff --cached --check`的exit=2仅指原始`intake.log`的git diff
空白上下文行和`scan03.log`逐行引用的空原文行。不清洗原始输出;排除这两个
日志后复跑exit=0。正文、工具、测试及其它登记文件没有空白错误。

## 22. A0 第3段续三:勘误6入库与SCAN-04停止报告

### 22.1 入库、SCAN-03关闭与中间态

勘误6批准来源:FatTank本轮任务书。旧hash为
`1c35df1cd9aeafc5511aefaa3bdd468b785af665205319d92cc6d30350be6939`,
新hash为`ccbe8923bdca5962189a458d0d7f51d32c8bb7e8af0f10fe592b2d478e4f2f0b`。
E6-1引入封闭四分支entry命名空间;E6-2规定entry kind到分支的映射;
E6-3规定三组对账及其并集,据此关闭SCAN-03。判定条件、固定被观测tree不变。
开场`git pull --ff-only origin clang-fix-campaign`输出`Already up to date.`;
基点`5d61715d9df995bc07b5e612035b514c3d03d961`。交付原件已位于目标路径,
直接采用其字节,没有重排或重写正文;与指定新hash完全一致。

本轮证据目录为`a0-evidence/part3/erratum6/`。`intake.command.json`记录
原始argv/环境/工具hash,`intake.log`保存相对上述Git基点的完整diff:

```text
APPEND_ONLY=PASS additions=41 deletions=0 insert_blocks=2
```

两个insert位置经旧版行序机械确认:旧行8之后的状态提示与旧EOF之后的勘误6。
不以diff看起来相似代替原字节SHA校验。SCAN-03的历史报告保留于§21.3,
当前状态已标CLOSED(E6-1～E6-3)。

实施拆文件计划补充(A03/A04/A09/A10):`T/terminal_registry.py`承载三组对账
与E4/E6机械映射;`T/terminal_python.py`与`T/terminal_commands.py`分别承载
Python参与点与命令载荷解析,由`T/terminal_consumers.py`统一编排。
候选检测在`T/terminal_candidates.py`,由`T/terminal_scan.py`与
`T/shim_inventory.py`共用。对应新增测试为同名`U/test_terminal_*.py`。
这些只是代码分文件,不减少§2.2任何交付与控制义务。
本次仅保留`terminal_registry.py`及其人工fixture测试的部分实现;
上述其它新模块未创建。`terminal_scan.py`只更新权威hash。

E4/E6正文机械导出的12类分支映射保存为`entry-kind-branches.json`;
六命名空间和32分支(consumer20/entry4/ledger1/provider1/resolve2/scan4)
可由`registry-corrected.log`复核。该文件是**映射证据**,不是已经完成的
B-8逐条detector矩阵。`load_registry`尚未接入扫描器,也未生成正式
`capability_registry.json`;原entry/provider注册文件未改成假完成状态。

### 22.2 SCAN-04:固定tree的内建compile参与点无原子形态承接

**状态:CLOSED(勘误7 E7-1/E7-2);以下为当时的停止记录。** 不是OBS claim判红;是在实现/接线前,
以真实输入做受监控调用闭集可满足性预检时发现的`UNKNOWN_CAPABILITY`。
预检不是完整消费者识别引擎,没有声称跑完第1/2块。

**权威位置**(当前ccbe8923正文):

| 位置 | 原文要求 |
|---|---|
| L330–345,§1.1参与点与受监控名字 | 每个解析到受监控名字的Call均为参与点;内建集合明确含`compile` |
| L350–354 | 零命中/多命中为`UNKNOWN_CAPABILITY`;不得最近形态归类;解除的唯一途径为勘误扩表 |
| L407–426,原子形态表 | 封闭二十形态;无任何调用谓词承接内建`compile` |
| E6-1/E6-3 | 新增entry分支只承接条目级检查,不新增consumer形态,不能借entry绕过上述阻塞 |

**实测位置**:固定HEAD `43a6aa625f27da46daba190657bf62256080c68e`,tree
`ca9331190e878af465e7968fe56e735585a5866e`中的
`docs/clang-fix-campaign/tools/check_design_doc.py:187`,
函数`_check_python_contracts`:

```python
compile(block.body, f"<design.md:L{line_no}>", "exec")
```

源码SHA `66e797e062cddfd02cbdb9c1e35c73e0c83edd10dedb337b51da0c5fd3d67b72`。
AST为`Call(Name('compile'), ...)`;symtable实测global=True/referenced=True,
assigned=False/imported=False/parameter=False;模块没有compile绑定,无星号导入。
因此不是同名局部函数/参数遮蔽。它是live上下文的tracked PY_SOURCE,
不因位于docs目录而豁免;Call也不是注释或提示语中的名字。

`scan04-final.log`逐行打印二十形态及每条不匹配原因,`scan04.json`保存
源码、AST、作用域与零命中结果;诊断程序全文保存在对应command.json中。
它直接读取固定tree,没有import或执行被观测模块,没有调用OBS producer。

```text
TRACKED_LEAVES=846
CONTEXT_COUNTS={".": 736, "release-v1.4.0": 110}
SCAN-04 UNKNOWN_CAPABILITY: builtins.compile; matched_forms=0; STOP
EXIT=1
```

**困难与候选裁决**:按现行规则必须阻塞,不能将compile放进`C5b`
(封闭为`__import__`)或`C8b`(进程启动族),也不能未经形态承接就仅记为
`DYNAMIC_UNRESOLVED`并继续。建议设计方依L354出勘误:新增承接compile
的原子形态/capability,明确代码载荷非静态时的处理,配正控制与near-miss;
并核对同一受监控闭集中exec/eval等是否也需同时处理。该建议不是实施规则,
本轮没有采用、扩表、缩小受监控集合或人工放行。

### 22.3 保留部分实现的验证与控制登记

所有实跑cwd为§9.2干净工作区,HEAD/tree如上,隔离venv
`/tmp/p49-a0-gate-seg2-43a6aa6`;运行前断言git status为空。
清除PYTHONPATH/MYPYPATH/PYTEST_ADDOPTS/PYTEST_PLUGINS,
禁自动加载pytest插件,设置PYTHONDONTWRITEBYTECODE=1。
新工具以主工作树绝对路径加载并记录其hash;被观测输入仍固定为43a6aa6。
以下R为主仓绝对路径,V为上述venv;完整命令/环境/exit/输出均落同目录。

```sh
"$V/bin/python" -m pytest -q -o cache_dir=/tmp/p49-seg3-pytest "$R/tests/unit/test_terminal_scan.py" "$R/tests/unit/test_terminal_registry.py" --junitxml="$R/docs/clang-fix-campaign/dev_memory/stage14_p49_terminal_batch/a0-evidence/part3/erratum6/foundation-tests-final.xml"
# 48 passed in 0.11s; EXIT=0 (35既有+13新增,人工fixture)
"$V/bin/python" -m pytest -q -o cache_dir=/tmp/p49-seg3-pytest "$R/tests/unit/test_terminal_predicates.py" "$R/tests/unit/test_terminal_anchors.py"
# 111 passed in 0.22s; EXIT=0; 无真实producer
"$V/bin/python" -m ruff check "$R/docs/clang-fix-campaign/tools/terminal_scan.py" "$R/docs/clang-fix-campaign/tools/terminal_registry.py" "$R/tests/unit/test_terminal_scan.py" "$R/tests/unit/test_terminal_registry.py"
# All checks passed!; EXIT=0
"$V/bin/python" -m mypy --strict --python-version 3.12 --follow-imports=silent "$R/docs/clang-fix-campaign/tools/terminal_scan.py" "$R/docs/clang-fix-campaign/tools/terminal_registry.py" "$R/tests/unit/test_terminal_scan.py" "$R/tests/unit/test_terminal_registry.py"
# Success: no issues found in 4 source files; EXIT=0
```

人工投影正常对照`registry-corrected.log`exit0;删除entry.binary_record的
人工registry由`missing-entry.log`实测`ENTRY_THREE_WAY`且exit1。
这些只验证登记集合比较,不是把人为标记当作detector执行证据。
`control_catalog.json`新增E6八条实际detector控制及一条对账控制登记,
均维持端到端NOT_RUN,最后一条附上述component红证据。E5五条的resolver
证据保留但端到端仍NOT_RUN,停因由SCAN-03更新为SCAN-04。
CTRL-INTRA-PKG-PROXY、20形态正控制/near-miss均未运行。

目录登记更新后再次合并运行以上四个测试文件,
`artificial-tests-final.log`为`159 passed in 0.32s; EXIT=0`;
完整argv在同名command.json。它仍全是工具/人工fixture测试,
不包含OBS producer和§6改前实跑。

保留首跑失败与修正:registry-projection.log的NINE_TABLE_PARSE来自
工具初版将表后说明的命名空间通配字样也读入表行;已限定Markdown表行。
registry-projection-final.log虽exit0,但初版错误把BINARY括注中的
“名字命中兜底”当作required detector;修正为只解析括注外的detector清单,
补`BINARY == [entry.binary_record]`测试,最终以registry-corrected.log为准。
这两项是本工具实现错误,不是设计裁决。首次ruff/mypy分别因长行、类型标注
问题exit1,已修正并保留原始日志,以ruff-final/mypy-final的exit0为准。

### 22.4 交付边界与未运行项

| 项 | 本轮结果 |
|---|---|
| scan_manifest输入 | 846条;live736/release110;完整扫描矩阵未完成,completion不存在 |
| 4个真实BINARY | 输入枚举可见;entry.binary_record的真实SCANNED尚未执行,不冒报通过 |
| E5上下文 | 固定输入两上下文不变;上轮85重名resolver回归证据保留;本轮完整端到端未运行 |
| 全树跨上下文回退边/歧义 | 均N/A,没有全树消费扫描输出;不得以resolver单测的0替代 |
| 台账三段/候选四级 | NOT_RUN;计数N/A |
| 8个claim | item1-basis、seg1-staleness、seg2-form、commit-order、transition-map、proxy-count、intra-package-shim、item5-order全部NOT_RUN |
| §6改前30场景 | PENDING_SEG3;未采集,结果文件hash N/A |
| 全量生产测试/mypy/ruff | 本轮未跑;上节只有具名工具与人工fixture检查,不是全仓验收 |

`immutable.log`exit0:生产源码、release、P4.5 design.md、既有part2与
erratum5证据均零diff。冻结canonical hashes仍为:

```text
predicates.json=8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6
measurement_exemptions.json=4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945
IMMUTABLE_AND_PRODUCTION_DIFF_EXIT=0
```

没有整块完成,本次为**勘误6入库+保留中间态+SCAN-04停止报告commit**,
不是第1块完成commit。push后等待设计方裁决,不继续第1–5块。
无关.gitignore修改、4份文档删除、其它untracked稿件继续保留不处理。

暂存`git diff --cached --check`的exit=2仅来自原始`intake.log:15`的
git diff空白上下文行;为保留原始输出不清洗该日志。排除该日志后的
`git diff --cached --check`须exit0,正文/工具/测试/登记文件不豁免。

## 23. A0 第3段续四:勘误7与全树预检停止报告

### 23.1 勘误入库与SCAN-04关闭

开场读取§22与§2.2交付映射,确认当前分支clang-fix-campaign;
`git pull --ff-only origin clang-fix-campaign`输出`Already up to date.`。
本轮基点为`4662d036af56e44b640b074e150a5d3adde2089a`。
FatTank批准的原件已在目标路径,直接采用原字节,没有重新编辑正文。

| 指纹 | SHA-256 |
|---|---|
| 勘误6旧版 | `ccbe8923bdca5962189a458d0d7f51d32c8bb7e8af0f10fe592b2d478e4f2f0b` |
| 勘误7新版 | `d6496250c3f9ba80990785edab0e972c9b077fd4965a045cea31e3201bd7c032` |

`a0-evidence/part3/erratum7/intake-final.log`保留相对上述基点的完整git diff:

```text
APPEND_ONLY=PASS additions=27 deletions=0 insert_blocks=2
EXIT=0
```

新增位置为文首勘误6提示下一行与附录C旧EOF之后,无删除/替换区段。
E7-1移出compile调用/读取;E7-2新增C9承接exec/eval,据此关闭SCAN-04。
未改冻结predicate形态清单;若未来OBS-7真实遇C9判红,仍须另走勘误。

### 23.2 E7-3预检方法、完整性与结果

§2.2 A09增加前置工具`T/terminal_monitored_preflight.py`,测试
`U/test_terminal_monitored_preflight.py`;原始结果在本节erratum7目录。
该工具是**PY_SOURCE参与点预检**,不是完整消费者引擎、B-8矩阵或SEAL。
其运行早于继续第1块,结果非空后不进入本轮任务第3步。

所有采集cwd为§9.2干净工作区
`/home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6`;
HEAD=`43a6aa625f27da46daba190657bf62256080c68e`,
tree=`ca9331190e878af465e7968fe56e735585a5866e`。
独立环境`/tmp/p49-a0-gate-seg2-43a6aa6`,清除PYTHONPATH/MYPYPATH与pytest
外部插件变量;输入先通过git tree/lstat/blob比对。新工具从主工作树绝对路径
加载,其hash与权威hash逐命令入档,不向固定工作区写入代码或结果。

遍历包括release的全部PY_SOURCE,按词法import binding、简单别名、局部遮蔽
与函数默认值所在的外层作用域解析;默认参数/类型注解/关键字实参中的
非调用读取不豁免。监控调用、裸读取、sys.modules操作和每个import alias
逐点记录;doctest拼块、静态exec/eval与-c/input片段按Python解析。
`compile`实际命中记录进入excluded_compile,不再成为参与点。
遇阻塞继续收集其它条目,不存在首错早退。

```text
PY_SOURCE_SET_EQUAL=PASS 272/272
tracked_entries=846; contexts: live=736, release-v1.4.0=110
python_entries=272; python_contexts: live=177, release-v1.4.0=95
participants=2825; zero_matches=27; multiple_matches=0; parse_errors=0
excluded_compile=1
PREFLIGHT=BLOCKED
EXIT=1
```

`preflight-final.json`包含逐条输入(路径/mode/blob/hash/上下文)、全部参与点、
所有阻塞及原始源码片段;其SHA-256为
`9014a099dd8d163c8964975c8b27e19c40509b7bd6be37efeff01af033fb93e7`。
`preflight-final.log`为完整stdout,相邻command.json含命令、环境、exit与工具hash。
完整27行清单由JSON机械生成至
[blockers.md](a0-evidence/part3/erratum7/blockers.md),每行都有文件/行/列、
限定名、上下文、命中数和原因;其中live17处、release10处。

交叉核对`cross-check.log`/`.json`(exit0):独立AST筛取subprocess.run/Popen
非Call位置,所得25处与预检清单精确相等,父节点分布为
arguments19、keyword2、Assign2、Subscript2。两处loader的.py路径由源码
赋值链确定,仅调用stdlib的spec_from_file_location构造元数据,确认
SourceFileLoader与其exec_module归属;**没有调用module_from_spec或exec_module**,
未导入或执行被观测源码。这是预检证据,不是OBS producer。

### 23.3 SCAN-05:两类未被封闭形态承接的参与点

**状态:CLOSED,由勘误8 E8-1/E8-2/E8-3解决;实测闭合见§24。**
原停止项1条,内含两类27个site。以下保留当时事实,非OBS claim判红。
以下位置引用本轮d6496250正文,不沿用勘误前行号。

| 设计原文 | 现状与不可继续之处 |
|---|---|
| L334–336:②′明确包含每个受监控名字的非调用读取,并明写没有形态承接即阻塞 | 25处subprocess.run/Popen读取;19处函数默认值、2处关键字传递、2处保存真实函数、2处类型注解;均非C8a/C8b的Call |
| L345–347:importlib含全部子模块下的可调用对象;L418 C5d仅五个具名函数 | tests/unit/test_design_drift_ledger.py:18、tests/unit/test_workflow.py:28的spec.loader.exec_module均来自SourceFileLoader,不在C5d或其它闭集 |
| L351–355:零/多命中必须阻塞,唯一解除途径为勘误扩表 | 不能将默认值读取归作一次subprocess调用,也不能把loader.exec_module归到“最相近”的module_from_spec |
| E7-1/E7-2 L2285–2296 | compile已排除,C9只覆盖exec/eval内建调用,不覆盖上述两类 |

例一:`tizen-ci-triage/scripts/ci_triage/runner.py:76`:

```python
subprocess_runner: SubprocessRunner = subprocess.run,
```

例二:`tests/unit/test_design_drift_ledger.py:14–18`:

```python
spec = importlib.util.spec_from_file_location("design_drift_ledger_for_test", path)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
```

Popen注解即使受future annotations影响也未自行排除:正文②′是AST参与点
口径,未授权类型位置豁免。快照中的10处同样不跳过,未改release文件。

**候选,仅供裁决**:按L355扩充非调用引用的承接规则,明确默认值/注解/回调
传递/别名的边与未决处理;为具来源证明的源码loader调用补承接及正/near-miss
控制。若设计方选择收窄受监控集合或增加排除,同样须通过勘误明确安全边界。
本轮未实施上述候选,未放宽判据、未把零命中改成无消费。

### 23.4 验证命令、失败留痕与停点

下列R为主仓绝对路径,V为上述独立venv;命令实际在固定工作区运行。
每个argv、环境与exit的完整记录在同目录`*.command.json`。

```sh
"$V/bin/python" "$R/docs/clang-fix-campaign/tools/terminal_monitored_preflight.py" --root "$PWD" --rules-root "$R" --output "$R/docs/clang-fix-campaign/dev_memory/stage14_p49_terminal_batch/a0-evidence/part3/erratum7/preflight-final.json"
# 272条目、27零/0多; EXIT=1 (预期阻塞,并非工具崩溃)
"$V/bin/python" -m pytest -q -o cache_dir=/tmp/p49-seg3-pytest "$R/tests/unit/test_terminal_monitored_preflight.py" "$R/tests/unit/test_terminal_scan.py" "$R/tests/unit/test_terminal_predicates.py" "$R/tests/unit/test_terminal_anchors.py" --junitxml="$R/docs/clang-fix-campaign/dev_memory/stage14_p49_terminal_batch/a0-evidence/part3/erratum7/tests-final.xml"
# 176 passed in 0.29s; EXIT=0 (30预检+35扫描基础+111人工predicate/anchor fixture)
"$V/bin/python" -m ruff check "$R/docs/clang-fix-campaign/tools/terminal_scan.py" "$R/docs/clang-fix-campaign/tools/terminal_monitored_preflight.py" "$R/tests/unit/test_terminal_monitored_preflight.py"
# All checks passed!; EXIT=0
"$V/bin/python" -m mypy --strict --python-version 3.12 --follow-imports=silent "$R/docs/clang-fix-campaign/tools/terminal_scan.py" "$R/docs/clang-fix-campaign/tools/terminal_monitored_preflight.py" "$R/tests/unit/test_terminal_monitored_preflight.py"
# Success: no issues found in 3 source files; EXIT=0
```

预检单测覆盖compile调用/读取near-miss、C9分类与嵌入片段、monitored裸读取、
别名/遮蔽、sys.modules闭集、loader来源与同名非loader反例、收全错误不早退、
词法绑定多形态阻塞和doctest跨行绑定。它们不是完整消费者边控制,
不把sentinel的Import节点存在冒充实际消费边已产出。

保留调试失败:首轮预检25零命中漏了loader返回对象的来源解析,补静态来源链
后为27;没有把25报作最终结果。doctest单测首跑1 failed/27 passed,
原因是把每个提示符例子分开解析丢失前行import;改为按冻结规则拼代码块,
最终30项通过。ruff/mypy首跑各exit1(长行/局部变量类型),修正后全绿。
intake首跑机械照搬上轮“旧行8”导致断言失败;最终改为定位旧勘误6提示行,
确认只在它之后及EOF追加。原始日志均保留,未清洗失败痕迹。

| 第3段原交付 | 本轮状态 |
|---|---|
| 第1块完整扫描/B-8/completion | 未继续;预检覆盖272 Python条目不等于全846条目的扫描完成;completion未生成 |
| E6映射/三组对账、4真实BINARY | 原中间态保留;未继续detector集成或真实SCANNED |
| 消费者形态控制、E5端到端、CTRL-INTRA-PKG-PROXY | NOT_RUN;C9引擎接入与control_catalog正式登记属预检为空后的步骤,本次未进入 |
| 全树回退边 | N/A;预检不产完整消费者边,不能报0 |
| MODULE_IDENTITY_AMBIGUOUS | 打包模块索引实测0;完整消费者解析中的歧义计数尚未采集 |
| 三段台账/四粒度候选 | NOT_RUN,计数N/A |
| 八个claim | item1-basis、seg1-staleness、seg2-form、commit-order、transition-map、proxy-count、intra-package-shim、item5-order均NOT_RUN |
| 改前30场景 | PENDING_SEG3,未采集,hash N/A |
| 全量生产pytest/mypy/ruff | 本次未跑,上表仅为具名工具与人工fixture验证 |

`immutable.log`exit0:生产、release、P4.5 design、既有OBS及勘误6证据零diff;
predicate canonical仍为`8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6`,
exemptions仍为`4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`。
本commit仅勘误入库、预检工具/测试/证据与状态登记;不是第1块完成commit。
原有.gitignore修改、4份无关文档删除及untracked历史稿不动;push后停止等裁决。

暂存`git diff --cached --check`的exit2仅来自intake-final.log的原始diff
空白上下文行与preflight-tests.log的pytest原始失败输出尾空格;不清洗证据。
排除这两个原始日志后检查exit0,正文/工具/测试不作豁免。

## 24. 勘误8入库、E8-6零阻塞、续跑停止SCAN-06

### 24.1 输入与批准

FatTank批准来源:本轮用户指令(2026-10-07)。`git pull --ff-only origin
clang-fix-campaign` exit0,`Already up to date.`;起始主树HEAD为`8046ecc`。
交付原件已在权威路径,没有另取附件副本或重排字节。

- 旧版 SHA-256: `d6496250c3f9ba80990785edab0e972c9b077fd4965a045cea31e3201bd7c032`。
- 新版 SHA-256: `66b33ef6c365c3da835529756d60ee43626768a0d361eb47dbeea86177f6db3c`。
- 证据目录 `a0-evidence/part3/erratum8/`(以下 E8 路径均相对它)。
- `intake.log`保留 `git diff --unified=0 8046ecc -- <权威路径>` 全文;
  两hunk分别是顶部新增状态行、Appendix C末尾新增勘误8,删除行0;
  去除两处插入后旧版字节全部保留。exit0。
- SCAN-05 CLOSED:旧27处逐点对照 `scan05-closure.json`,23处落C8c,
  2处落C5f,2处由E8-1标注位置排除。没有删掉原报告或旧证据。

### 24.2 全树预检与固定点证据

采集仍在§9.2干净工作区,HEAD固定`43a6aa625f27da46daba190657bf62256080c68e`,
tree固定`ca9331190e878af465e7968fe56e735585a5866e`;独立环境
`/tmp/p49-a0-gate-seg2-43a6aa6`。命令记录逐项保存argv/cwd/env/输入hash/exit。
AST只读,未import/执行任何被观测模块;未调用OBS producer。

`terminal_alias_preflight.py`计算C8c有限绑定不动点;函数体局部重赋值不消去别名,
未重绑定的嵌套作用域继承;具名参数沿静态def/import/re-export绑定传递;
其它去向落未决。C5f保留同作用域唯一C5d来源,不执行loader。
`terminal_monitored_preflight.py`按批准表23形态校验并覆盖全部PY_SOURCE,
未遇首个阻塞即退出。annotation中的调用仍参与,compile仍排除。

```text
tracked_entries=846; contexts: .=736, release-v1.4.0=110
python_entries=272; python_contexts: .=177, release-v1.4.0=95
participants=2943; zero_matches=0; multiple_matches=0; parse_errors=0
alias_bindings=67; alias_calls=25; fixed_point_rounds=6
excluded_annotations=2; excluded_compile=1
new DYNAMIC_UNRESOLVED: C8c_ESCAPE=0, ALIAS_PAYLOAD=25, C5f=0
PREFLIGHT=ZERO_BLOCKERS; EXIT=0
```

本轮预检零阻塞,但25条动态记录未销账,不是consumer closure绿。
完整输出 `preflight-final.json`,SHA-256:
`87a80a16e6012fb709fe096e7a95da0bf040b50a72eca8bdcf14c2ed1ec25e44`。
`preflight-summary.md`逐条列出绑定/来源读取/经别名调用,以及25条动态记录;
JSON保留原文span、上下文、签名族与载荷失败原因。
`preflight-crosscheck.log`证明与E7全部PY_SOURCE集合相等、旧27处闭合、绑定键唯一。
模块索引无歧义;本轮alias-def resolver记录36次LOCAL、跨上下文回退0、歧义0。
这不是完整消费者E5回退边计数,后者尚未采集,不得把0移作全树闭合结论。

### 24.3 SCAN-06:非入口工具配置的名字命中

**状态:CLOSED,由勘误9 E9-1/E9-2解决,实测见§25。以下保留当轮停止事实。** Python预检通过后,恢复第1块required detector
落地核对,在OTHER_TEXT名字兜底上发现真实输入没有合法形态/排除出口。
详细原文行号、候选证明、四处命中与待裁决方案见 `E8/blockers.md`。

见证:包根 `tizen_convergence_judge/__init__.py` 的`check_convergence`
为显式re-export且在`__all__`内,属于§1.1c粒度②发现范围;
其模块名在`.importlinter:8/:22/:32/:57`命中。
E4-2明确`.importlinter`为OTHER_TEXT;四处非解释器命令,不属DOC,
也不属C7a/C7b/C7c/C7d。§1.1 L371要求其余一律UNKNOWN_CAPABILITY,
L356禁止实现方逐条放行。不能用包入口保留策略提前裁掉binding候选。

`scan06.log`/`scan06-witness.json`是独立单见证检查,exit1;
没有声称完成全部非Python名字兜底,没有把真实红改绿。
待裁:封闭新增工具配置形态与控制,或由设计方明确封闭排除规则及上界;
实现方均未采用。此处停止,不推进第2–5块。

### 24.4 测试、控制登记与尚未完成的范围

| 命令/原始输出 | 实测 | 边界 |
|---|---|---|
| `preflight-final.command.json` / `.log` | exit0,上列完整272条目 | E8-6预检,非full scan |
| `tests-preflight.command.json` / `.log` | pytest `226 passed`,exit0 | 67预检组件+35扫描基础+13注册投影+111判据/anchors人工fixture |
| `preflight-controls-verbose.command.json` / `.log` | pytest `67 passed`,exit0 | 逐nodeid的E7/E8组件控制输出 |
| `typing-preflight.command.json` / `.log` | mypy `Success: no issues found in 4 source files`,exit0 | 预检两脚本与两测试文件 |
| `ruff-preflight.command.json` / `.log` | `All checks passed!`,exit0 | 上述四件及terminal_scan |
| `py-compile.command.json` / `.log` | exit0,空输出 | 3工具+2测试,pycache定向/tmp |
| `immutable.command.json` / `.log` | exit0,生产/旧证据零diff,固定工作区status空 | frozen predicates/exemptions字节不变 |

E8-5的12项控制已登记到control_catalog,原子形态归属为C8c/C5f;
各行component_check引用本轮已绿的预检测试。**全引擎控制status仍NOT_RUN**:
解析出sentinel载荷不是完整消费边闭合证明。SEAL-16b与12b-10按23形态的
正式五方对账尚未完成,不得拿组件测试冒充。C9正控制的消费边验收也仍待完成。
CTRL-INTRA-PKG-PROXY、E5端到端、4个BINARY的正式SCANNED记录同样未完成。

复现预检(实际argv与环境详见command.json):

```bash
R=/home/linhao/Toolchain/development/LogAnalysisSkill
V=/tmp/p49-a0-gate-seg2-43a6aa6
cd /home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6
env -u PYTHONPATH -u MYPYPATH -u PYTEST_ADDOPTS -u PYTEST_PLUGINS \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  "$V/bin/python" "$R/docs/clang-fix-campaign/tools/terminal_monitored_preflight.py" \
  --root "$PWD" --rules-root "$R" --output /tmp/p49-e8-preflight-recheck.json
```

首次工具命令在主shell使用`python`时报exit127(未启动采集),改为`python3`
启动记录器;实际执行解释器始终为独立环境绝对路径。
`tests-first.log`保留1 failed/66 passed:更新doctest near-miss样本时漏改其import,
修正人工样本后全绿。`quality-initial.log`与`typing-initial.log`保留首次ruff/mypy
输出(缺strict与静态类型标注);已修工具注解/zip显式strict,未改冻结判据。
初次与最终全树预检均保留,最终计数无变化。

未完成项:第1块矩阵/完成标记、第2块完整引擎、第3块台账/候选、第4块8个claim
均未宣告完成;before_run=PENDING_SEG3,30场景未采集、hash=N/A。
没有运行新增OBS,没有改既有OBS与设计正文,本轮不重跑生产全量测试。
既有.gitignore改动、4份删除、其余untracked历史稿不动。
提交仅勘误8原字节、预检工具/测试/证据、控制记账与progress/INDEX;push后停等裁决。

## 25. 勘误9入库、C7e局部实跑与全量预检缺口

本节 E9 = `a0-evidence/part3/erratum9/`。开场读取§24后,
`git pull --ff-only origin clang-fix-campaign`输出`Already up to date.`。
主分支基点为`8338889d2090cb660ddeaa16542e6721f4cac654`。
本轮采集/测试均由独立环境在§9.2固定工作区运行,主工作树只提供批准后的
工具/规则/测试,产物写回E9;没有把主树当作被测tree。

### 25.1 原字节勘误与SCAN-06关闭

收到新版已在目标路径,不重新拼装正文;`intake-and-registry.log`保存完整
`git diff --unified=0 8338889 -- docs/clang-fix-campaign/p49-terminal-batch-design-v1.31-FROZEN.md`。

```text
old_sha256=66b33ef6c365c3da835529756d60ee43626768a0d361eb47dbeea86177f6db3c
new_sha256=b5c2dce6568b722a70ceb92ed7860ecda4417ca8895310df4bdbf7ae9158cec3
insertion_hunks=2 deleted_lines=0
@@ -11,0 +12 @@
@@ -2364,0 +2366,58 @@
EXIT=0
```

两处分别是顶部勘误9状态行与附录C末尾58行;原文全部保留。
SCAN-06 **CLOSED**,依据E9-1/E9-2:新增IMPORT_LINTER在BUILD后、DOC前;
模块位归C7e、仅消费模块。原四处见证现均C7e,不把`check_convergence`
binding误判为消费。旧E8见证文件不改,新的处理结果另存。

### 25.2 A03/A04/A09工具与控制映射

| 映射 | 本轮产出 | 边界 |
|---|---|---|
| A03/A04 | `terminal_scan.py`;`entry_registry.json`;`terminal_registry.py`;`capability_registry.json` | 13条目类别,24 consumer+8非consumer/entry旧分支+4 entry=36;E4/E6/E9正文机械生成required分支映射;不是实际detector矩阵完成 |
| A09 | 新增`terminal_import_linter.py` | 从完整固定tree取IMPORT_LINTER条目,ConfigParser解析,逐token定位/解析/模块边;名字命中参数来自调用方,本轮仅接SCAN-06见证 |
| A09 | `terminal_monitored_preflight.py` | 正文表形态计数由23同步24,包括C7e;未改Python参与点判据 |
| A13 | `test_terminal_import_linter.py`;`control_catalog.json` | E9-4十项组件控制25个参数化用例;全引擎status仍NOT_RUN,component_check=PASS |
| A05/A06 | 未产出 | 四级候选/三段台账缺口如§25.4;不得拿模块索引当候选 |

控制十项:root_packages、layers兄弟、containers相对名、ignore_imports两端、
wildcard、根/docs条目分类;near-miss为注释、name、未知键、binding只得模块边。
另外测试非法节/INI、可选括号/冒号/多个container、闭合registry等边界。
registry五方投影仍须结合真实全扫描记录,本轮没有发放SEAL-16b或12b-10通过。
CTRL-INTRA-PKG-PROXY与E5端到端仍NOT_RUN,不改旧状态伪造补测。

### 25.3 固定树.importlinter实跑

命令原文/环境/exit在`import-linter-real.command.json`,完整stdout在同名log。
可复现命令(输出另用/tmp避免覆盖证据):

```bash
R=/home/linhao/Toolchain/development/LogAnalysisSkill
V=/tmp/p49-a0-gate-seg2-43a6aa6
cd /home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6
env -u PYTHONPATH -u MYPYPATH -u PYTEST_ADDOPTS -u PYTEST_PLUGINS \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  "$V/bin/python" "$R/docs/clang-fix-campaign/tools/terminal_import_linter.py" \
  --root "$PWD" --rules-root "$R" \
  --scan06-witness "$R/docs/clang-fix-campaign/dev_memory/stage14_p49_terminal_batch/a0-evidence/part3/erratum8/scan06-witness.json" \
  --output /tmp/p49-e9-import-linter-recheck.json
```

```text
HEAD=43a6aa625f27da46daba190657bf62256080c68e
TREE=ca9331190e878af465e7968fe56e735585a5866e
manifest_entries=846; live=736; release-v1.4.0=110
IMPORT_LINTER entries=1; tokens=49; module_edges=49; binding_edges=0
resolution LOCAL=49; CROSS_CONTEXT_FALLBACK=0; MODULE_IDENTITY_AMBIGUOUS=0
excluded_comment_lines=4; excluded_name_values=6
C7e DYNAMIC_UNRESOLVED=0
SCAN-06 hits=4, all C7e; EXIT=0
```

`import-linter-tokens.md`逐个列出49 token、源行列/节/键、解析结果、目标路径,
另列4条注释与6条name排除。JSON保存manifest、全部原始解析事件与见证输入hash。
`import-linter-real.json` SHA-256:
`88b40069af9f0e777a14c7d71cfd54a940e8ff02be3f78dc7f9acae7c57e5776`。
这里的fallback/歧义/动态0仅指C7e此次解析,不是全树消费者结果。

### 25.4 E9-5输入缺口与SCAN-07停止报告

**E9-5尚未执行全量预检,不是“预检为空”。** 非Python文本范围570条:
DOC431 / OTHER_TEXT122 / BUILD13 / PACKAGING2 / CI_CONFIG1 / IMPORT_LINTER1;
PTH和SHELL为0。每条记录见`non-python-preflight-inputs.json`,SHA-256:
`07e4eb02c9e2c9ced6dbdab38991aa28acf20551efc4285307952eaa15093868`。
按E9-5最后一句如实列缺:MODULE、REEXPORT+all/span/guard、INLINE+lexical scope、
PROXY(含四种假阴形态)发现均没有完整产物。`shim_inventory.py`/`raw_findings.json`
尚未实现;只有模块索引和SCAN-06单binding见证。完整名字/解释器兜底引擎亦未落地。
不能用部分candidate发出570条目全量绿;UNKNOWN、多去处和全树新增动态计数均N/A。
本缺口是已授权实现尚未完成,不是请求新增排除规则。

**SCAN-07 OPEN:扩展回归暴露预期差异门禁的文档来源锚失配。**
`terminal_expected_diff.py:23/:96`和`expected_diff.json:20`起仍钉勘误3
`7b8531fd...`,路径已是当前`b5c2dce6...`正文。实际51条SOURCE_HASH失败。
两文件相对8338889未改,旧66b33ef6也已不同于所钉hash;未重放旧提交全套测试。
原文位置、失败nodeid、候选处置见`E9/stop-report.md`与`source-anchor-mismatch.json`。
不自行更新旧来源锚或改为读取Git旧blob,待设计方确定寻址/同步口径。
停止报告计**1条来源锚问题+1项候选前置缺口**,未收集到全树UNKNOWN结论。

### 25.5 测试与保全

| 命令(完整argv在同名command.json)/输出 | 实测 | 范围 |
|---|---|---|
| `python -m pytest -vv -p no:cacheprovider ...`;`scanner-regression.log` | 253 passed,exit0 | 扫描/注册/E7/E8/E9及判据/anchor人工fixture七文件 |
| 同命令增加`test_terminal_expected_diff.py`;`tests-final.log` | 51 failed,288 passed,exit1 | 扩展八文件回归;所有失败均SOURCE_HASH,不是全绿 |
| `python -m mypy --python-version 3.12 --follow-imports=silent --cache-dir=/tmp/p49-e9-mypy ...`;`mypy-verified.log` | Success: no issues found in 6 source files,exit0 | 4工具+2测试 |
| `python -m ruff check ...`;`ruff-verified.log` | All checks passed!,exit0 | 同上6文件 |
| `python -X pycache_prefix=/tmp/p49-e9-pycache -m py_compile ...`;`py-compile.log` | 空输出,exit0 | 同上6文件 |
| 控制目录更新后同七文件pytest;`controls-post-catalog.log` | 253 passed,exit0 | 再验控制登记未破坏既有组件 |
| `immutable.command.json` / `immutable.log` | exit0;旧证据376/376字节相等;受保护路径ZERO_DIFF | 入库仍2处追加/0删除,固定工作区clean |

首次`controls-initial.log`的2 failed/73 passed为实现的箭头分词错误,修正后
75/75及上述253/253绿;未改设计判据。首次mypy误沿仓库Python3.10配置检查
tomllib且新测试缺类型标注,第二次暴露返回Any;补注解/cast并显式按既定A0环境
Python3.12检查后绿。原失败输出不覆盖。主shell初用`python`曾exit127,改用
python3启动记录器;被测解释器始终为独立环境。

predicates canonical=`8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6`;
measurement_exemptions canonical=`4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`。
二者、旧OBS、旧E1–E8证据、生产与release未改;固定工作区无改动。
第1块矩阵/completion未产出,第2–5块不继续;8个claim仍NOT_RUN,
before_run=PENDING_SEG3,30场景未采集。未重跑生产全量,不宣称整体回归绿。
本commit仅提交勘误原件、工具/注册/控制组件、证据与状态登记;既有.gitignore、
4份文档删除及其它untracked草稿保持不动。push后停止。
暂存区`git diff --cached --check`因pytest原始失败log/XML保留的尾空格返回2;
不清洗原始证据。限定到工具/测试/正文/进度/INDEX时同检查空输出、exit0。

暂存diff空白检查exit2仅为`erratum8/tests-first.log:15`的pytest原始错误输出尾空格;
不清洗原始证据。仅排除该原始日志后的`git diff --cached --check`为exit0。

## 26. SCAN-07裁决落实与四级候选前置停止报告

本轮无勘误。开场核对§25后,`git pull --ff-only origin clang-fix-campaign`
返回`Already up to date.`;开始HEAD=`524e4153048132d66538e0aa1fec3cfdcc30dd78`。
所有本轮取证/正式回归命令cwd仍为§9.2固定工作区,HEAD/tree不变。
新证据目录(以下简称R):`a0-evidence/part3/scan07-resume/`。
主工作树的既有`.gitignore`修改、四份无关文档删除及untracked历史稿未处理。

### 26.1 已闭合裁决与输入保全

| ID/映射 | 当前状态 | 实现/证据 |
|---|---|---|
| SCAN-07 / A01 | CLOSED | `terminal_expected_diff.Sources.read`按勘误3入库commit的blob读取DOC,旧SHA强核对;当前正文quote逐字存在及E4+生效范围检查;R/scan07-*.log |
| C7E_VALUE_PROVENANCE / A09 | 已落实组件修正 | `terminal_import_linter.inspect`追加UNKNOWN_CAPABILITY记录后continue;保留section/key/parsed_values/source_rows,后续合法token继续解析;全仓测试包含其控制 |
| A05/A06四级候选前置 | STOPPED_SCAN08 | R/stop-report.md;只做真实输入的ID可满足性探查,未交付台账或候选全集 |
| E9-5 / A09 | NOT_RUN | 570条非Python文本范围确认;不能用部分候选声称全量 |

SCAN-07的历史来源:

```text
commit=cbd3a22ae6fdb6454ecc5a55254304f72a17ecd1
path=docs/clang-fix-campaign/p49-terminal-batch-design-v1.31-FROZEN.md
sha256=7b8531fdd9bcb4b2ecf8f3576eab6285f09f4b22fb1b212775939dbe72d19200
current_authority_sha256=b5c2dce6568b722a70ceb92ed7860ecda4417ca8895310df4bdbf7ae9158cec3
scenarios=30
UNCHANGED_REGISTRATIONS_VALID / CURRENT_QUOTES_PRESENT / LATER_SCOPES_CLEAR
EXIT=0
```

每次读取当前权威,先核对附录C中E4起各勘误生效范围。当前E4..E9均不触及
§3/4/5/6、勘误1..3或预期差异门禁。引用仍按旧blob的SHA/quote校验,
另要求所有DOC quote在当前正文逐字存在。没有更新expected_diff的sha/quote,
也没有改旧值、消息派生规则、predicates、exemptions或旧OBS。
修复只改变文档寻址与增加防漂移检查,不放宽比较规则。

构造式控制(命令/环境/脚本原文在R同名command.json):

| R输出 | 人工控制 | 实际输出与exit |
|---|---|---|
| scan07-normal.log | 真实已登记30场景来源核验 | 上述三项PASS,exit0 |
| scan07-quote.log | 篡改引用quote | `REJECTED: SOURCE_QUOTE`,exit1 |
| scan07-current-quote.log | 旧blob不变,仅人工当前视图删除该quote | `REJECTED: CURRENT_SOURCE_QUOTE`,exit1 |
| scan07-scope.log | 人工追加E10且生效范围含§6 | `REJECTED: LATER_ERRATUM_AFFECTS_DIFF: E10: §6。`,exit1 |

单元测试另覆盖§3/4/5/6、勘误1..3/勘误2、预期差异门禁及缺scope的反例。
上述控制及C7e继续收集控制已登记control_catalog;E9完整引擎控制及
CTRL-INTRA-PKG-PROXY不改为PASS,仍待后续实际实现/运行。

### 26.2 全仓回归与环境

本轮执行不再只测扫描组件。独立环境为`/tmp/p49-a0-regression-43a6aa6`;
系统`python3 -m venv`首次因ensurepip未安装失败,随后以既有`.venv`的pip
`--python /tmp/p49-a0-regression-43a6aa6/bin/python3`安装到独立环境。
没有向固定worktree执行editable install;生产路径从固定worktree的
`sorted(glob('*/scripts'))`派生,完整PYTHONPATH在command.json中。
测试文件来自主工作树当前tests(包含本轮工具测试),被采集代码固定43a6aa6;
有测试按__file__取主树源码,故另对所有生产/release文件与固定树逐字节核验。
没有把工具代码放进固定tree。软件版本完整见R/environment.log。

可复现主命令(完整展开的argv/env/输入hash见command.json):

```bash
V=/tmp/p49-a0-regression-43a6aa6
R=/home/linhao/Toolchain/development/LogAnalysisSkill
cd /home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6
# 使用full-regression-final.command.json中记录的PYTHONPATH与隔离环境
"$V/bin/python" -m pytest -vv -p no:cacheprovider "$R/tests"
```

```text
collected 1292 items
1291 passed, 1 skipped
failed=0
EXIT=0
```

| R原始输出 | 命令 | 实测 |
|---|---|---|
| full-regression.log; full-regression-final.log | 全仓pytest,逐nodeid | 两轮1291 passed/1 skipped/0 failed,exit0 |
| ruff.log | `python -m ruff check`本轮两工具+两测试 | `All checks passed!`,exit0 |
| mypy.log | `python -m mypy --python-version 3.12 --follow-imports=silent`同四文件,外置cache | `Success: no issues found in 4 source files`,exit0 |
| py-compile.log | `python -X pycache_prefix=/tmp/p49-scan07-pycache -m py_compile`同四文件 | 空输出,exit0 |
| integrity.log | 既有证据逐字节、生产/release对固定树、冻结输入hash及worktree检查 | 见原文,exit0 |

今后每次冻结稿入库也必须复跑全仓测试并记录passed/failed,不再以局部扫描
组件绿代替全仓回归。mypy/ruff本轮范围如表,不宣称它们是全仓静态检查。

### 26.3 SCAN-08 CLOSED(E10-1至E10-3;以下保留原停止记录)

规范与原始见证见R/stop-report.md及R/anonymous-callable-id.json。
F:1022-1028规定任一纯委托callable入候选;F:1038-1048的PROXY ID只有
路径+lexical qualname且禁行号;F:1117要求全局唯一。固定树中
`tizen-gbs-log-analysis/scripts/gbs_analyzer/analyze.py:110/116`分别纯委托
同包另两个模块,实参全为Name;编译器给两者同一个
`analyze_buildlog.<locals>.<lambda>`。它们没有可用来区分的具名binding,
不是同一binding的互斥producer。把宿主可变状态标为SCAN_UNRESOLVED也
不能解决“每个candidate须先有唯一ID”的问题。

按完整272 PY_SOURCE逐项检查,含release,结果:

```text
contexts={'.':736,'release-v1.4.0':110}
lambda_sites=121
direct_import_call_id_collision_groups=5
non_python_text_entries=570
EXIT=0
```

这里5是“direct-call且有导入来源的重名形状组”,不是5个已裁定shim或完整
PROXY候选数。报告采用:110/:116简单实参的最小见证,不靠含复杂表达式的
其它lambda推断纯度。探查用AST+compile取得code object,不执行被观测代码。
探查结果SHA=`3fe6bade0f09a43efa483d5825b9a387ec7bd427addf3e7a112cd0fb26bd384e`。

候选处理:设计方明定匿名callable的非行号唯一化规则,例如词法宿主+AST
field/index路径,并明确名字形态及碰撞控制;或显式调整匿名callable发现域
并给出覆盖承担方。两者都未实施。不能自行略过lambda、添加编号/hash或
将不同callable合并以凑全集。停止报告计1项(SCAN-08)。

### 26.4 未运行项与停点

- A05三段shim_inventory和A06四级候选全集尚未交付,计数N/A。
- 四级正控制/near-miss及CTRL-INTRA-PKG-PROXY尚未完成,不报通过数。
- E9-5仍NOT_RUN,全量UNKNOWN/多去处/DYNAMIC_UNRESOLVED/跨上下文
  回退边/MODULE_IDENTITY_AMBIGUOUS数均N/A,不写0。
- scan_manifest仍只有既有输入枚举,没有发放detector完成标记或seal。
- 原第3段第4块8个claim仍NOT_RUN;before_run=PENDING_SEG3,
  30场景未采集。本轮没有运行任何OBS producer。
- predicates canonical仍`8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6`;
  exemptions仍`4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`。
- 提交已授权修复、控制、原始证据与停止报告后push,等待SCAN-08裁决。

## 27. 勘误10入库、SCAN-08关闭、候选span全树反查

本轮开始HEAD=`72337e79ae53a1d97887afae27c405a038971dec`;
`git pull --ff-only origin clang-fix-campaign`返回`Already up to date.`。
先核对§26及§2.2交付映射。新证据目录R=`a0-evidence/part3/erratum10/`。
观测/测试cwd始终为§9.2干净工作区,HEAD/tree不变;独立环境继续用
`/tmp/p49-a0-regression-43a6aa6`。本轮没有运行任何OBS producer或门禁改前实跑。

### 27.1 入库与SCAN-07回归

用户交付原件已替换到目标路径,未编辑其正文。`admission.command.json`保存
取证程序与完整命令;`admission.log`保存完整`git diff --unified=0`及机械核验:

```text
old_sha256=b5c2dce6568b722a70ceb92ed7860ecda4417ca8895310df4bdbf7ae9158cec3
SHA256=37862f4acdc330caa1ebb563885037814256746ae87663e51a64685fe21ccc01
hunks=2 added_lines=38 deleted_lines=0 ORIGINAL_PREFIX_PRESERVED
SCAN07_GREEN: current quotes present; E4..E10 scopes clear; 30 registrations valid
EXIT=0
```

去掉新增状态行后,新文件完整以前版原字节为前缀,剩余部分仅勘误10。
`terminal_scan.RULES_SHA`同步当前权威,未改扫描判据。SCAN-07测试中旧的
“最后勘误为9/伪造下一条为10”改为从当前标题序列确定,反向仍严格要求
`LATER_ERRATUM_AFFECTS_DIFF`,没有把红因换成序列错误。入库后立即跑全仓:
`full-regression-admission.log`:1291 passed/1 skipped/0 failed,exit0。

### 27.2 SCAN-08 CLOSED与E10组件

E10-1/E10-2/E10-3解决SCAN-08。新增`T/terminal_callable_ids.py`及
`U/test_terminal_callable_ids.py`,对A06/A07补足身份组件,不冒充完整扫描器:

- 编译/反汇编而不执行被观测模块,以code object的`co_qualname`为依据;
  通过LOAD_CONST源码位置对齐AST,具名定义另以编译器定义位置核对。
- lambda按已消歧父作用域及原始起点排序,自外向内替换每个lambda段;
  编译器父作用域处理默认参数lambda,不把它误归入外层lambda函数体。
- 模块/类简单赋值记录名字n并生成binding形态;未绑定lambda只有模块形态,
  非打包文件按E5不发明点分模块名。具名callable ID不变,匿名不走N1归并。
- `<locals>`者附E10-2机械证据四项,仅作用于将来被发现为PROXY的该callable;
  模块/类lambda不据此拒绝。这里的AST四坐标是源码定位metadata,
  **不是**擅自替换§1.1c的五字段`candidate.spans`。

固定树重复扫描输出(完整命令/程序在`candidate-span-stop.command.json`):

```text
E10: five collision groups resolved; 121 lambda IDs unique; two full scans identical
all_callable_sites=3183 code_location_issues=0
python_entries=272 context_counts={'.': 736, 'release-v1.4.0': 110}
```

5组逐ID证据在`callable-id-scan.json/log`;新旧ID集合比对、重复运行、名字形态
与局部证据在`candidate-span-stop.json`。3183是callable定位数,121是lambda数,
均非PROXY候选数量。已登记9项单元控制及独立重号负控制到唯一目录
`D/control_catalog.json`;没有把CTRL-INTRA-PKG-PROXY改为PASS。

| 控制证据 | 实测 |
|---|---|
| `ids-controls-final.log` | 9 passed,exit0;覆盖E10-3各要求及同一行/default参数/N1边界 |
| `e10-collision-negative.log` | 正常不同序号绿;人为同序号后`SEAL-7`红,exit1 |
| `callable-id-scan.log` | 固定树5组旧冲突唯一化,匿名碰撞0、定位未决0,exit0 |

### 27.3 SCAN-09 CLOSED:被勘误11取代(E11-5)

2026-10-07关闭;原发现与证据保留如下。以下“停止/未完成”是第27节当时的状态,
不再构成A/B前置。该机制未修复,也未通过完整发现门禁,是E11显式停用。

正式报告:`R/stop-report.md`。F:1015-1021/1042-1045要求逐binding候选;
F:1097-1103及1118要求行级五字段span不能跨ID重复。真实旧址
`ci_triage/report.py:3/5`在同一行导出三名字,分别对应三个ID但相同span;
N1不能合并不同名字。此问题独立于E10编号,不能靠补ordinal解决。

不是遇首例即停:全272 PY_SOURCE(含release)同型排查完成:

```text
raw_same_line_multi_binding_groups=225
by_kind={'import_stmt': 219, 'all_entry': 6}
explicit_reexport_groups=23
explicit_by_context={'release-v1.4.0': 9, '.': 14}
cross_statement_import_groups=0
same_line_assignment_groups=0
same_line_callable_groups=0
SEAL-7 RED: distinct candidate IDs share the frozen five-field span; N1 cannot merge distinct binding names
EXIT=1
```

225为原始同型语法组,23组有直接导出证据,其余202不作shim裁定;
完整逐项清单见`candidate-span-stop.json`与`span-feasibility-probe.json`。
候选方案为设计侧增精确span身份,或显式定义共享语句的binding所有权及删除耦合;
均未实现。停止项数1(SCAN-09),不扩字段、不合并不同binding、不修改源码排版。

### 27.4 回归、边界与余账

可复现命令的完整argv、环境、输入SHA、cwd、exit在R各`*.command.json`;
命令使用固定工作区scripts路径,测试来自主树当前tests,生产/release与固定树
逐字节检查另见`integrity-final.log`。没有editable install到固定树。

```bash
V=/tmp/p49-a0-regression-43a6aa6
R=/home/linhao/Toolchain/development/LogAnalysisSkill
cd /home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6
# 使用full-regression-final.command.json记录的环境
"$V/bin/python" -m pytest -vv -p no:cacheprovider "$R/tests"
```

```text
collected 1301 items
1300 passed, 1 skipped
failed=0
EXIT=0
```

| 原始证据 | 命令与范围 | 实际结果 |
|---|---|---|
| `full-regression-admission.log` | 入库后全仓pytest | 1291 passed/1 skipped/0 failed,exit0 |
| `full-regression-final.log` | E10九项新增测试后全仓pytest | 1300 passed/1 skipped/0 failed,exit0 |
| `ruff.log` | ruff check本轮两工具+两测试 | All checks passed!,exit0 |
| `mypy.log` | mypy --python-version 3.12 --follow-imports=silent同四文件 | Success: no issues found in 4 source files,exit0 |
| `py-compile.log` | 同四文件py_compile,cache放/tmp | 空输出,exit0 |
| `integrity-final.log` | 旧证据/冻结输入/生产与release/fixed tree/nodeid集合 | 440份旧证据不变、233生产与快照文件一致、1292既有nodeid无缺失或状态变化、新增9,exit0 |

静态检查范围如表,不称全仓mypy/ruff。开发中的首轮静态检查曾报两处行长及
类型注解/Optional问题,修正后才取得表中正式绿输出。未清洗失败证据或改断言。
完整性诊断的首次调用漏传`check_frozen_hashes`实参而exit1,保留在
`integrity.log`/`integrity.command.json`;只修诊断程序调用,未改verifier,
成功复跑为`integrity-final.*`。

- A05三段台账、A06四级候选全集仍未交付,计数N/A;不得拿callable定位数或
  原始语法组数替代。CTRL-INTRA-PKG-PROXY与四级发现能力控制仍未完成。
- E9-5仍NOT_RUN。范围确认为570非Python文本条目;UNKNOWN、多去处命中、
  新增DYNAMIC_UNRESOLVED、跨上下文回退边/MODULE_IDENTITY_AMBIGUOUS均N/A,
  不报0。现有contexts条目数为live736/release110。
- 第3段后续8个claim未运行;before_run=PENDING_SEG3,30场景尚未采集。
  不发放scanner completion/seal。
- predicates canonical仍`8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6`;
  exemptions仍`4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`。
- 不改既有OBS、expected_diff旧值/quote/消息派生规则或生产源码;
  无关dirty/untracked保持原样。提交本轮产物并push后停止等SCAN-09裁决。

## 28. 勘误11:两阶段计划、专用枚举与停止报告(2026-10-07)

### 28.1 入库与计划替换

证据目录 `R=a0-evidence/phase1/erratum11/`。开场重新读取本文件,
`git pull --ff-only origin clang-fix-campaign` 输出 `Already up to date.`。
输入已由用户替换在权威路径,本轮未改其任何字节。

| 项 | 实测输出/状态 | 证据 |
|---|---|---|
| 旧版SHA | `37862f4acdc330caa1ebb563885037814256746ae87663e51a64685fe21ccc01` | `R/admission.log` |
| 勘误11 SHA | `b9d720028164faec8c91d87a02cfa75475e1f8e1fff86e8244a2c0ef55bedaf0` | 同上 |
| 原字节差异 | `hunks=2 additions=65 deletions=0` | 顶部状态行+附录C末尾;完整`git diff --unified=0`在同上 |
| SCAN-07 | `SCAN07=PASS STRUCTURE_SOURCES=PASS scenarios=30`,exit0 | 同上;E11生效范围检查与当前quote逐字存在检查均运行 |
| SCAN-09 | CLOSED,**被勘误11取代** | F E11-5;第27.3节原证据保留 |

下表取代第2.2节及其它旧计划中与E11冲突的前置;旧记录不回写为“已通过”。

| 阶段/顺序 | 交付与必须满足的前置 | 当前状态 |
|---|---|---|
| 第一阶段前置1 | E11-2专用AST枚举器及控制;复用item3/item4 PASS,产出item5且冻结verifier绿 | 枚举/控制完成;item5因PHASE1-01未运行 |
| 第一阶段前置2 | 固定43a6aa6上§6全部30场景改前实跑,封闭schema/登记旧值一致 | `before_run=PENDING_SEG3`,未运行 |
| 第一阶段前置3 | 全仓pytest+mypy(CI包)+ruff+lint-imports绿 | pytest红(PHASE1-02),不声称前置满足 |
| 第一阶段A | 项4 timeout;改后登记差异逐项相等,其它字段相等,全仓绿后独立commit+push | NOT_STARTED |
| 第一阶段B | 项3+项5;同样验收后独立commit+push | NOT_STARTED |
| 第二阶段准备 | E11-3(a/b/c)登记删除清单+四类调用方表+E11-4范围/拟删nodeid理由;改前OBS-5绿 | NOT_STARTED;不进行删除 |
| 第二阶段人工闸门 | 设计方审阅、FatTank批准上述清单后才开始C首组 | PENDING_APPROVAL |
| C各组与D | 旧址宿主文件分组,改调用方+删壳同commit;删除后五项验证,失败整组回退并停;最后逐项收口 | 本轮不进入 |

E11-2列明的旧scan_manifest、消费者引擎、四级候选全集、E9-5、SEAL、
admission及其OBS均非A/B前置;E11-5停用项按“不适用”而非“验证完成”登记。
已有工具保留,没有继续修SCAN-09。第二阶段遇OTHER也必须停报。

### 28.2 专用AST枚举(仅枚举,非OBS判定)

新增 `T/protected_marker_readers.py` 与
`tests/unit/test_terminal_protected_marker_readers.py`。
从固定tree的git blob枚举,用现有条目分类/打包上下文识别live PY_SOURCE,
排除非live上下文,不排除tests;函数体只匹配Name/Attribute,
按E11仅排除`mark_worktree_protected`,字符串/注释不匹配。
输出 `R/B-1-anchors.json`,每个函数附路径、行号、签名、完整源区段及命中点。

```text
live_py_source=177 excluded_non_live=95 protected_marker_readers=14
EXIT=0
```

4项人工控制全部通过:新增Name/Attribute函数、注释/字符串/签名near-miss、
不擅自排除测试和其它写入方、嵌套/async函数体覆盖。
`R/reader-controls.log`: `4 passed in 0.03s`,exit0。
control_catalog登记为E11专用枚举控制,不恢复旧SEAL五方门禁。

### 28.3 停止项(2项,不自行修订范围或放宽判据)

正式报告: [stop-report.md](a0-evidence/phase1/erratum11/stop-report.md)。

| 编号 | 原文/代码锚 | 困难与证据 | 待设计方裁决的候选 |
|---|---|---|---|
| PHASE1-01 CLOSED,见§29.2 | F E11-2②:2481-2483;predicates v1.2 B-1:192-208;F §6:1535-1539 | 原问题:14函数含10个测试函数,同一中断态的调用契约未规定;原证据保留 | 2026-10-07提示词裁决:live、tests外;worktree_path独立副本。实测4函数,item5冻结verifier PASS |
| PHASE1-02 CLOSED,见§29.1/29.4 | F E11-2③、E11-3(5)/E11-5;terminal_scan.py:30、terminal_registry.py:31-34 | 原问题:全仓14个RULES_SHA失败;旧失败日志保留 | 2026-10-07提示词裁决:不可变blob+当前稿逐字包含;原pin不改,14个失败恢复 |

未产出item5 output/verifier结论;未执行30场景;未编写A/B生产实现;
未进入第二阶段,OBS-5未运行。停止项不是claim判红,不伪造verifier结果。

### 28.4 命令、实际结果与边界

R中每个`*.command.json`记录完整argv、cwd、环境、固定HEAD/tree、输入hash与exit;
对应`*.log`为未截断原始输出。运行环境沿独立环境
`/tmp/p49-a0-regression-43a6aa6`,生产路径只由固定worktree的`*/scripts`派生。
测试取本轮主树tests;没有editable install固定worktree。

```bash
V=/tmp/p49-a0-regression-43a6aa6
M=/home/linhao/Toolchain/development/LogAnalysisSkill
W=/home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6
cd "$W"
# 环境完整值见R/whole-repo-pytest.command.json
"$V/bin/python" -m pytest "$M/tests" -vv -p no:cacheprovider
```

```text
collected 1305 items
14 failed, 1290 passed, 1 skipped in 23.36s
EXIT=1
```

全仓红后立即停止后续实施;不把旧静态工具“非门禁”解释为可忽略全仓失败。
CI包mypy、全仓ruff及lint-imports本轮未运行,不声称E11-2③通过。
枚举器/新增测试的定向ruff已实跑`All checks passed!`,exit0;
定向控制exit0不能替代全仓红。首个记录器启动用了环境不存在的`python`,
shell exit127且未生成证据;改用`python3`启动记录器,受检命令仍为独立venv的python。
本轮没有改冻结predicates/exemptions、expected_diff及既有OBS;
生产/release零改动,旧草稿及无关dirty/untracked不处理。

control_catalog落盘后复跑全仓,`R/whole-repo-final.log`原文:

```text
14 failed, 1290 passed, 1 skipped in 23.34s
EXIT=1
```

`R/integrity-final.log`机械核对:1301旧nodeid全保留、新增4且全PASS,
14个旧PASS转FAILED逐项列出;472份旧证据、6项受保护输入均与HEAD字节一致;
233个生产/release文件与HEAD及固定43a6aa6逐字节一致。
`INTEGRITY=PASS; REGRESSION=FAIL (14 existing statuses changed, not suppressed)`。
完整性诊断首次`integrity.log`为exit1:nodeid解析用`\S+`漏掉参数中空格;
修正诊断解析为整段nodeid后复跑exit0,未改pytest结果或任何门禁判据。
定向ruff的命令与原文现已保存为`R/ruff-enumerator.*`,exit0。
暂存区`git diff --cached --check`对pytest原始traceback日志报尾随空格(exit2);
保持原始日志字节及其hash,不为格式检查清洗证据。排除`*.log`后的同项检查
exit0;这不改变全仓pytest失败结论。

## 29. 提示词裁决、第一阶段前置取证与停止报告(2026-10-07)

### 29.1 权威与不可变来源

本轮无勘误,F逐字未改,SHA仍
`b9d720028164faec8c91d87a02cfa75475e1f8e1fff86e8244a2c0ef55bedaf0`。
开场pull为`Already up to date.`;本节取代§28中的当前进度,不清洗历史失败。
证据根`R=a0-evidence/phase1/prompt-rulings/`;每个`*.command.json`
含完整argv、环境、固定HEAD/tree、输入hash、exit和原始输出hash;
同名`*.log`保存stdout/stderr原文。cwd均为§9.2固定43a6aa6,
独立环境`/tmp/p49-a0-regression-43a6aa6`,生产模块只取固定树scripts。

`T/terminal_authority.py`读取不可变git blob并核原pin;当前稿须按原顺序
包含历史完整字节行,不规范化、不折叠空白。只允许追加,删字/改字/重排红。
全仓冻结稿SHA常量与间接读取处清单如下(`R/integrity.log`有完整commit/hash):

| 读取处 | 不可变来源 | pin | 当前逐字包含 |
|---|---|---|---|
| terminal_scan.fixed_inputs/historical_rules; terminal_registry.authority/required_from_authority; terminal_monitored_preflight及fixed_inputs消费者 | E10 `8e72c34:F` | `37862f4a…cc01` | PASS |
| verify_anchors.guard | E1 `27fb460:F` | `d4458459…3c3f` | PASS;未重跑item3/4 |
| protected_marker_readers.collect | E11 `ab4779e:F` | `b9d72002…daf0` | PASS |
| terminal_expected_diff.Sources(DOC); build_terminal_diff_data经该入口 | E3 `cbd3a22:F` | `7b8531fd…9200` | PASS;保留SCAN-07 quote/生效范围检查 |
| terminal_expected_diff.Sources(TABLE) | `43a6aa6:skill-5 v1.3.2` | `0e2de5ff…55f27` | PASS |

历史数据/OBS的hash、旧值、消息规则均不改。新增6项来源控制,
覆盖合法追加、删字/改字/重排红、blob hash错红。PHASE1-02 CLOSED,
不是跳过旧静态测试。批准的轻量流程已写入methodology专节。

### 29.2 PHASE1-01与item5

枚举范围live、tests外PY_SOURCE,排除具名写入方mark_worktree_protected。
125条扫描、95条非live排除、52条tests排除,恰得:
`clean_repository_preserving_markers / release_worktree_protection / is_protected / _exclude_private_files`。
独立锚为`a0-evidence/B-1-anchors.json`;tests引用near-miss已加入,
旧“测试不得排除”控制由本提示词裁决取代,control_catalog留历史证据链接。

`T/terminal_marker_observation.py`只产item5事实。两个SIGINT现场各自生成,
每个读取方复制独立worktree,以`worktree_path=副本`调用;不共享副本。
记录返回repr或异常类型全名;子进程exit=-2。call_order为verify→exclude→write。

| 场景 | protected marker | 按上述函数顺序的返回repr |
|---|---|---|
| EXCLUDE_INTERRUPTED | ABSENT | `None / False / False / None` |
| MARKER_WRITE_INTERRUPTED | PARTIAL,SHA `87c1f578e028105c6c36684cdffaee0863ed2459bcf45e872bba090e66cd3a54` | `None / True / True / None` |

事实`R/item5/raw.json`,claim `R/item5/output.json`;producer exit0。
冻结verifier命令见`R/item5-verifier.command.json`,exit0,输出原文:

```json
[
  {
    "claim_id": "OBS-1.item5-order",
    "verdict": "PASS"
  }
]
```

PHASE1-01 CLOSED。predicates canonical仍
`8271f1d000a73808f1fa9787b90e868dd99038098eab192b26372e4eeaf694f6`,
exemptions canonical仍
`4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`。
未运行其它OBS producer。

### 29.3 §6改前实跑

`before_run=DONE`;权威产出`R/before-verified/before.json`,SHA:
`a0eb4b107bbb7401a9ab3bf0e8dd29267a40e0386d582c049952d30352dfc133`。
`T/terminal_before_run.py`是门禁采集器,不是OBS producer。逐场景子进程,
同fixture/同调用点注入TimeoutExpired且改前不传timeout,中断场景实发信号。
已有临时路径先备份、结束恢复;固定生产树不写入。clock作为固定fixture输入,
不掩码输出。§5现场真实git init,使读取方执行git与item5同类fixture一致。

封闭schema、每条登记旧值、全部OBS调用轨迹、timeout原始结果、item5
marker状态/hash/逐读取方结果全部相等;读取方按身份逐项对账,不依赖枚举顺序。
`consistency.json`为`{"scenarios":30,"failures":[]}`。
`R/before-run-verified.log`原文:

```text
BEFORE=PASS scenarios=30 sha256=a0eb4b107bbb7401a9ab3bf0e8dd29267a40e0386d582c049952d30352dfc133
EXIT=0
```

`R/before/`是较早有限检查(未含item5交叉核对),不作为完整验收。
`before-run-final`因新代码在采集前引用结果而KeyError,未执行场景;
修正顺序后才有上述完整绿输出。所有失败日志保留。
正式取证后只补工具类型注解与`__file__ is None`拒绝检查;
`R/executed-sources/*.py.txt`保留实跑版本,与当时enumerator/producer/collector
hash逐一相等,由`integrity.log`验证。既有产出未改写成新版本重跑。

### 29.4 回归与静态检查

| R中的日志 | 实际命令范围 | 输出/exit |
|---|---|---|
| whole-repo-final.log | `python -m pytest <main>/tests -vv -p no:cacheprovider`;固定cwd与生产路径,本轮完整tests | `1314 passed, 1 skipped in 23.83s`,0 |
| mypy-ci-complete.log | CI列明10个生产包 | `Success: no issues found in 88 source files`,0 |
| mypy-current-tools-py312.log | 本轮9工具,实际解释器3.12,follow-imports=silent | `Success: no issues found in 9 source files`,0 |
| ruff-fixed-tree.log | 固定树`ruff check .` | `All checks passed!`,0 |
| ruff-current-tools.log | 主树本轮完整tools/与tests/ | `All checks passed!`,0 |
| lint-imports.log | 固定树`lint-imports --no-cache` | `Contracts: 6 kept, 0 broken.`,0 |
| integrity.log | 不可变pins/实跑源码/旧证据/生产/固定树/nodeids | 全PASS,0 |

1305旧nodeid保留(批准的范围控制改名映射1项),新增10;原14失败恢复,
原skip不变。490份旧证据、233生产/release文件、8项受保护输入未变;
固定worktree保持干净。完整命令与环境见同名command.json。

失败留痕:初次控制因误删subprocess import报54失败,恢复import后
`controls-fixed.log`为147 passed;不改断言。新工具初轮mypy报5处注解问题,
修正后绿。独立环境缺types-PyYAML导致首次CI mypy红,
安装`types-PyYAML==6.0.12.20260906`后绿;工具mypy初次沿项目3.10目标
找不到tomllib,按工具实际3.12复跑绿,生产CI目标未放宽。
首次ruff错误扫入主树untracked历史脚本而报53错;这些文件git ls-files
零命中,未修改。正式范围为干净固定树全仓+本轮tools/tests,两部分均绿。
不清洗失败记录,不声称首轮通过。

### 29.5 新停止项与当前计划

报告:[PHASE1-03](a0-evidence/phase1/prompt-rulings/stop-report.md)。

| 编号 | 原文位置 | 困难/实测证据 | 待裁决候选 |
|---|---|---|---|
| PHASE1-03 CLOSED,见§30 | F §6:1526、§7:1568、E11-2:2487;terminal_expected_diff.py:667/687 | 原冲突:分提交实施与即时完整终态门禁不相容,原构造证据保留 | 设计方提示词批准候选1:A按登记来源机械投影,排除项3字段必须保持改前;B完整终态。两负控制与A实际30场景均已实跑 |

这是规格可满足性诊断,不是实际生产改后运行。停止项1条。
前置:专用枚举/item5 PASS、30场景改前DONE、全仓及静态检查PASS。
A/B均NOT_STARTED;第二阶段清单/归类/项2/OBS-5均NOT_STARTED。
生产零改动;冻结稿、predicates/exemptions、expected_diff/manifest/schema与既有OBS
零修改;无关dirty/untracked保持原样。提交前置与停止报告,push后等裁决。

## 30. PHASE1-03裁决与commit A:六面timeout

### 30.1 批准前提和投影

设计方按轻量流程在提示词批准候选1;无勘误,不改F/冻结predicates/
expected_diff/manifest/schema。投影只读登记项`new.source`:
来源文件须为F且节为§3或E2-1,不将skill-5的§3.2误认为项3。
投影不读取实际差异;排除字段与改前精确相等,其它登记必须兑现,
未登记字段仍严格相等。B默认FULL,不使用投影。

证据根`A=a0-evidence/phase1/commit-a/`。`item3-projection.json`
保存每项完整来源file/hash/section/quote,机械结果:

| 场景 | 路径 | 来源 |
|---|---|---|
| DANGLING_SYMLINK | /exception_type | F §3 预期差异 |
| DANGLING_SYMLINK | /exception_code | F §3 预期差异 |
| DANGLING_SYMLINK | /exception_message | F 附录C/E2-1 |

人工控制仅假产出,不是OBS或改后实跑:

```text
projection-normal: PHASE_A=PASS; EXIT=0
projection-premature-item3: GATE_REJECTED: DIFF_PATHS: extra=['/exception_type'] missing=[]; EXIT=1
projection-missing-item4: GATE_REJECTED: DIFF_PATHS: extra=[] missing=['/calls/0/kwargs/timeout']; EXIT=1
projection-tests: 103 passed in 5.30s; EXIT=0
```

原始逐命令stdout/exit/argv/env均在对应`.log`/`.command.json`,
control_catalog登记两条必红与正常对照。PHASE1-03 CLOSED。

### 30.2 实施与实际改后

仅改三生产文件:skill-3 gerrit、skill-5 gerrit_submit、shared/workspace。
六面timeout kw-only默认None,经调用链明确下传;只捕获TimeoutExpired:
fetch用FETCH_TIMEOUT、submit git用GIT_TIMEOUT,消息str(exc);
remote用固定warning;shared用`GIT_TIMEOUT: `+str(exc),不添code字段。
新增GerritSubmitError(code,message);fetch外层不吞FETCH_TIMEOUT。
SIGINT/SIGTERM未捕获,无清理/回滚新逻辑。项3判定与项5写入顺序未改。

在`/tmp/p49-terminal-implementation-be73825`独立worktree只应用本轮三件
生产diff,与主树逐文件hash核对;原固定43a6aa6仍干净、不改动。
门禁采集cwd仍为固定树,改后模块从该实现副本导入;每次记录code_root与
全部生产源码hash。非OBS producer,复用旧item3/4/5与旧before文件。

`A/after/after.json` SHA:
`828f4df93cd5b9cbddf59f429168f2d92c6413240ef3bb9b471f74c5486bbb6a`。
`A/after-a.log`:

```text
AFTER=PASS phase=A scenarios=30 sha256=828f4df93cd5b9cbddf59f429168f2d92c6413240ef3bb9b471f74c5486bbb6a
EXIT=0
```

`A/after/comparison.json`含before/after hash与排除来源清单。
非修改源码的信号场景仍实际子进程注入。新增18个六面异常控制,
既有query/git超时与默认timeout测试按新契约更新,不删原行为断言。
三个测试名称随契约更新,旧→新映射逐条入`A/integrity.log`。

### 30.3 验收与停点

| 证据 | 命令范围 | 结果 |
|---|---|---|
| full-regression-final.log | pytest全tests,固定cwd+实现副本生产路径 | 1338 passed / 1 skipped,exit0 |
| mypy-ci.log | CI生产10包 | 88 files无问题,exit0 |
| mypy-tools.log | 修改的3个门禁工具,Python3.12 | 3 files无问题,exit0 |
| ruff-code.log | 实现副本全仓 | All checks passed!,exit0 |
| ruff-tools-tests.log | 主树本轮tools/tests | All checks passed!,exit0 |
| lint-imports.log | 实现副本模块+同一.importlinter | 6 kept / 0 broken,exit0 |
| integrity.log | 集合保留/代码副本相等/受保护输入/固定树 | PASS,exit0 |

A提交后继续B;第二阶段尚未开始,任何新门禁红/OTHER/规格缺口即停报。
轻量裁决不改变安全边界,全量最终登记保留,未启用任何忽略字段或掩码。

## 31. commit B:悬空链接与marker失败态

前置A已独立提交并push:`5213c5d`。本节证据根
`B=a0-evidence/phase1/commit-b/`,各命令完整argv/env/exit在同名command.json,
原始输出在log,不是复用历史测试数字。

生产只改gerrit `_reset_generated_source_dir` 的判定:
`path.exists() and path.is_symlink()` → `path.is_symlink()`。
按F §3在skill-3正文对应Errors/分支表回写行为记录;history保留抽取时快照,
不伪装为抽取期原始契约。终止F与所有冻结机器数据原字节不变。
项5生产零改动,仍verify→exclude→write,两场景登记仍NO_DIFF。

新测试`tests/unit/test_terminal_marker_failures.py`逐点固化:

| 注入点 | 磁盘与顺序断言 | 四读取方(各独立副本) |
|---|---|---|
| exclude执行中KeyboardInterrupt | cleanup验证已完成;workdir字节不变;exclude仅部分内容;protected不存在 | None/False/False/None |
| protected Path.write_text中KeyboardInterrupt | exclude完成;workdir字节不变;protected为实际部分JSON原字节,SHA与改前相同 | None/True/True/None |

两测试均断言原异常对象原样抛出,无自动回滚;clean/release/is_protected/exclude
读取相互隔离,不以第一次读取的副作用污染后续读取。

完整§6改后采集复用固定43a6aa6改前文件,**phase=FULL,不用A投影**:

```text
AFTER=PASS phase=FULL scenarios=30 sha256=adef6922978fe5e63f99bbcad411e542e6cac28d6f5364447490648d3013ad71
EXIT=0
```

`B/after/after.json`与comparison.json保存全部结果与前后hash。
仅项3登记和A已兑现项4登记发生变化,未登记字段全等;两个项5场景零差异。

| 证据 | 命令范围 | 实测结果 |
|---|---|---|
| targeted.log | pytest marker失败态+gerrit文件 -vv | 40 passed,exit0 |
| full-regression.log | pytest全tests -vv | 1340 passed/1 skipped,exit0 |
| mypy-ci.log | CI所列生产包 | 88 source files无问题,exit0 |
| ruff-code.log | 独立实现worktree全仓 | All checks passed!,exit0 |
| ruff-tools-tests.log | 当前tools/与tests/ | All checks passed!,exit0 |
| lint-imports.log | 实现副本import-linter | 6 kept/0 broken,exit0 |
| integrity.log | nodeid映射/保护输入/副本/固定树 | old=1339 retained=1339 renamed=1 added=2 lost=0 changed_status=0;1072保护文件不变,exit0 |

唯一改名为dangling测试从旧FileExistsError名称到rejects_dangling_symlink,
保留链接/缺失目标/git未执行断言,改断言为批准的新异常契约。
阶段一A/B完成;第二阶段仅准备人工审批材料,尚未删除任何兼容壳或测试。
当前无新停止项,冻结稿/判定条件不改;所有无关dirty/untracked保持原样。

## 32. 第二阶段只读准备与PHASE2-01停止

A `5213c5d`、B `c1ea4ef`分别提交并push;B后全仓1340/1,
FULL30验收通过。第二阶段证据根`a0-evidence/phase2/`。

固定树43a6aa6只读草案:13宿主、183转出绑定、11抽取跃迁;
全846 tracked文件字面复扫(4二进制)619个候选×形态命中,路径粗分
485 HISTORICAL / 30 REWRITE / 104 RELEASE / 0 OTHER。
完整输入、逐项来源与源码诊断程序在`preparation.command.json`
及`preparation/*.json`,归类用途复核未完成,不是最终审批材料。

实测发现活动bridge的三条旧workspace路径为历史表键,按REWRITE替换
后`consumed=0 produced=0`,出现3个UNMAPPED_SOURCE;原键3/3无verdict。
该构造exit1与原文逐行位置见[停止报告](a0-evidence/phase2/stop-report.md),
无需改生产即可复现,未改工具/判据/冻结表迁就结果。

| 编号 | 原文位置 | 实测与困难 | 候选处置 |
|---|---|---|---|
| PHASE2-01 CLOSED,见§33 | F E11-3(2)/(4):2497-2509;bridge:35-63,436-440;step-0表:236-238 | 历史停止证据保留;设计方按轻量流程批准候选1 | 新增逐项HISTORICAL_KEY,不按目录豁免;宿主位置/用途/历史输入文件与hash/保留理由必须齐全 |

真实依赖与排除:quickbuild_log.FailedPackage有5处本地读取,不能删import;
skill副本三类型与新包根/release保留。runner env兼容行未在E11封闭来源内,
只登记差异,不自行补来源。项2/拟删nodeid/OBS-5尚未完成,
因新缺口停下;人工闸门NOT_READY,无删除。

停止后仅复跑全仓用于本次留档交付,未继续其它实施。所有既有证据和
冻结F/predicates/expected_diff不变,无关工作树改动仍不处理。

```text
pytest /home/linhao/Toolchain/development/LogAnalysisSkill/tests -vv -p no:cacheprovider
======================= 1340 passed, 1 skipped in 26.03s =======================
EXIT=0
```

完整命令、隔离env与原始输出:`a0-evidence/phase2/full-regression.command.json`
和`full-regression.log`。mypy/ruff/lint仍使用B同一生产字节,
其exit0证据见§31;阶段二未产生任何生产或测试diff。

## 33. A/B审查补漏与PHASE2-01轻量裁决

设计方确认A/B生产改动符合§3及勘误1–3,skill-3行为记录合规。
本轮不出勘误,终止F仍为`b9d720028164faec8c91d87a02cfa75475e1f8e1fff86e8244a2c0ef55bedaf0`。

### 33.1 独立纯文档补漏

对tizen-ci-shared、tizen-gerrit-fetch、tizen-gerrit-submit全部README*/SKILL.md
逐一搜索timeout/interruption/cancellation/symlink。tracked文件只有:

```text
tizen-gerrit-fetch/SKILL.md
tizen-gerrit-submit/SKILL.md
```

三个目录没有README,shared没有SKILL.md,不凭空新增文件。
fetch文档改为timeout默认None逐调用下传,FETCH_TIMEOUT保留str(exc)及cause;
有效与悬空symlink均SOURCE_DIR_UNSAFE,不删链接/目标;query失败目标不动,
git阶段留下阶段残留。submit文档改为GIT_TIMEOUT双参异常与固定
target_head_unknown:timeout warning;两者明确不捕获SIGINT/SIGTERM、不自动回滚。
不把这些说明写成CLI新增参数或包根新增导出,仅反映实际函数契约。

```text
git diff --stat -- tizen-gerrit-fetch/SKILL.md tizen-gerrit-submit/SKILL.md 'tizen-*/scripts/**' tests/
 tizen-gerrit-fetch/SKILL.md  | 44 ++++++++++++++++++++++++++------------------
 tizen-gerrit-submit/SKILL.md | 24 ++++++++++++++++--------
 2 files changed, 42 insertions(+), 26 deletions(-)

pytest /home/linhao/Toolchain/development/LogAnalysisSkill/tests -vv -p no:cacheprovider
======================= 1340 passed, 1 skipped in 25.87s =======================
EXIT=0
```

完整argv/隔离环境/生产副本字节核对/逐nodeid原始输出:
[doc-alignment-regression.md](a0-evidence/phase2/doc-alignment-regression.md)。
本提交只含markdown文档,生产与测试零改动。

### 33.2 后续准备的批准规则

PHASE2-01 CLOSED:采候选1,新增HISTORICAL_KEY,仅适用于活动代码中的
冻结历史表主键,不是import/patch/入口。每项必须登记宿主文件:行、读取用途、
不可变历史输入文件与sha256、保留理由;不按文件或目录整体豁免。
删除后残留允许HISTORICAL/RELEASE/已登记HISTORICAL_KEY。
E11-3(1)(b)扩大到step-0 closeout已登记兼容壳,同判据核对runner
discover_sibling_pythonpath,真实依赖须排除并附证据。
继续用途复核、项2范围/拟删nodeid、OBS-5改前产出,全部完成后停等人工闸门;
任何新缺口仍停报,当前没有授权删除。

## 34. PHASE2-02: 项2包根特殊名字边界停止

文档补漏 `f65949f` 已独立提交并推送;该提交1340/1,生产/测试零改动。
继续准备时发现新口径缺口,按协议停止,不出勘误、不改冻结稿与判据。

| 编号 | 原文位置 | 实测与困难 | 候选处置 |
|---|---|---|---|
| PHASE2-02 CLOSED,见§35 | F E11-4:2514-2516; test_package_metadata.py:1/5; gbs_analyzer/__init__.py:3 | 历史停止证据保留;设计方已澄清dunder不在项2范围,包根直接定义也是规范定义位置 | 按轻量裁决执行,不改冻结稿 |

固定43a6aa6上全部52个tests/ Python文件的ImportFrom定向核对,
按包根/已登记兼容绑定筛选命中1项,实际导入得`__version__=0.5.0-dev`。
此诊断不是最终项2全集。初轮粗筛多列runner._safe_pkg_dir,
随后按绑定粒度纠正(它是本地定义,不是discover兼容行),原始证据都保留。
runner.discover原位只有1个import、0个Load,本轮来源扩展后判为兼容壳,
应进入下一版清单;当前没有删除。

[停止报告](a0-evidence/phase2/private-scope-stop.md)含文件:行、候选处置、
完整命令及证据路径。事实文件与诊断程序:
`a0-evidence/phase2/private-scope-binding-refinement/facts.json`、
`private-scope-binding-refinement.command.json`与同名log。

准备汇总仍沿用**上轮未定稿草案**:13宿主/183绑定/11跃迁,
619候选乘形态命中(485 HISTORICAL/30 REWRITE/104 RELEASE)。
本轮runner与逐项HISTORICAL_KEY尚未合入,不冒称最终清单。
PHASE2-01已关闭,新增PHASE2-02未关闭;用途归类、项2拟删nodeid、
OBS-5未完成/未运行,人工闸门NOT_READY,无删除。

仅复跑交付留档回归:

```text
pytest /home/linhao/Toolchain/development/LogAnalysisSkill/tests -vv -p no:cacheprovider
======================= 1340 passed, 1 skipped in 25.68s =======================
EXIT=0
```

完整命令/env/逐nodeid原文见`a0-evidence/phase2/rulings-stop-full-regression.*`。
本次只提交准备诊断证据和记账文件,不改变生产/测试/既有OBS/冻结输入。
等待设计方轻量裁决,不继续其它准备以绕开停止项。

## 35. PHASE2-02裁决落实与人工审批包

### 35.1 已批准口径

PHASE2-02 CLOSED:项2的下划线名字限定私有名字,`__name__` 形式的dunder
(`__version__`/`__all__`)排除。私有件若直接定义在包根 `__init__`,从该包根
取用已经是直取定义模块,记入表但不移除。此前版本接口用例保留不改。

第二阶段准备期间采用设计方批准的保守默认:分类/归属/范围边界若不涉及
删测试、不改变行为且可归入现有类别,保留不改,逐项PENDING_REVIEW送人工
审批,不单独停止。仅(a)会导致删除测试、(b)会改变行为、(c)无现有类别可归
时停报。本轮9个待审条目均未改写,不是永久残留豁免。冻结稿/判定条件不改。

### 35.2 准备完成,尚未批准

[审批包](a0-evidence/phase2/gate-package/README.md)包含删除清单、最终归类、
HISTORICAL_KEY逐项来源、项2最终范围、拟删测试、PENDING_REVIEW与13组计划。
清单/用途表从主分支b3e0a95的Git tree读取,不读取用户dirty/untracked文件;
OBS-5严格从固定43a6aa6改前树实跑,两者不混淆。

- 来源登记14宿主/184绑定;拟清理13宿主/183绑定。runner.discover已加入;
  quickbuild_log.FailedPackage因5处真实本地Load排除,新包根/skill类型依赖/
  release也明确排除。没有为了数字与旧草案一致而保留错误范围。
- 1973 tracked条目中4个二进制,字面匹配6944条候选乘形态出现:
  REWRITE18 / HISTORICAL6806 / HISTORICAL_KEY3 / RELEASE108 / PENDING_REVIEW9,
  OTHER0。另有一个有限f-string调用点展开3个旧模块目标,独立附表。
- 历史键仅bridge:37/46/55三条源三元组,每条均有固定43a6aa6中的step-0
  表文件/sha256/行号、读取用途及理由。其余活动工具旧键不整体豁免。
- 项2解析68个tracked tests/Python文件,20处私有名import中4处是skill-4
  义务,均已直取定义模块;6个包根私有函数为包根真实定义,相关5处属性读取
  保留;dunder1处明确排除。有限identity循环已复核,项2无未解待审项。
- 拟删4个nodeid仅是legacy identity,全函数原文/hash/理由入册,本轮仍在且
  全绿。其它用例全部保留;不得按整文件删除。跨宿主identity只在首次相关
  组经批准去除一次。每组均须通过E11-3(4)五项验证,失败回退该组并停报。
- PENDING_REVIEW9条逐项说明用途,包括纯shim结构校验的后续转档边界;
  相关组须先获明确处置批准。HISTORICAL_KEY不是按工具文件或目录豁免。

### 35.3 OBS-5 与回归

新增只读工具`tools/terminal_entry_observation.py`,只枚举与入口冒烟产事实。
独立全集`a0-evidence/B-5-entries.json`,sha256
`9a9d8d1f7131776525ee09832b7c85c8bd5a9fe1179db485d9a222ed90059bfe`。
31入口(live16/release15;PACKAGE_MAIN10/SKILL_MD_COMMAND21/console0)
逐一独立进程--help均exit0,不依赖tests/、不执行真实git/gbs操作;
旧OBS与predicates/exemptions不改。冻结verifier:

```text
[{"claim_id": "OBS-5.entry-consumers", "verdict": "PASS"}]
EXIT=0
pytest tests -vv -p no:cacheprovider
1343 passed, 1 skipped in 25.55s; EXIT=0
NODEIDS old=1341 current=1344 lost=0 status_changes=0 added=3
mypy CI: Success: no issues found in 88 source files; EXIT=0
mypy producer: Success: no issues found in 1 source file; EXIT=0
ruff tools/tests: All checks passed!; EXIT=0
lint-imports: Contracts: 6 kept, 0 broken.; EXIT=0
py_compile OK; EXIT=0
```

完整argv/env/sha/逐nodeid原文为`a0-evidence/phase2/gate-*.command.json/.log`,
OBS-5原始事实在`gate-package/obs5/`,全部entry控制3个新增用例单列全绿。
早期诊断的源码子串匹配、all(generator)识别及含空格nodeid解析问题已修正,
原始调试输出保留;完整集合证明以`regression-set-proof.full.json`为准。
仅新增观测工具/控制测试/证据文档,生产与既有测试无diff。

状态 **E11_PHASE2_GATE_READY, NOT_APPROVED**。本轮新增停止项0,
PENDING_REVIEW9,人工删除授权仍为0。到此停止,等待设计方与FatTank审批;
不开始C、不删除兼容壳或测试、不修改9条待审引用。

提交前最终复跑`gate-full-final.log`:1343 passed/1 skipped,25.57s,exit0。
`gate-integrity.log`:119个生产文件与独立回归副本一致,既有测试零diff,
固定树clean,冻结F/predicate/exemption hash不变,OBS-5脚本hash与产出一致,
清单/分组/分类汇总核对通过,exit0。

## 36. 人工闸门批准、C01 回退与停止报告

### 36.1 本轮批准与执行边界

FatTank 已按74ff34c审批包原样批准:13宿主/183绑定、调用方归类表、4个完整
拟删nodeid、C01至C13顺序。原审批包不覆盖,其NOT_APPROVED是批准前历史状态;
本节及 `a0-evidence/phase2/execution/approval.json` 记录本轮批准与各输入hash。

9项待审处置均已明确,不再等待人工归类:

- 8项转HISTORICAL_KEY,原样保留。逐项位置、用途、对应43a6aa6不可变输入文件
  与sha256、保留理由见 `execution/historical-keys.approved.json`;
  连同此前bridge的3条历史键共11条,不是按工具文件或目录整体豁免。
  symbol_audit:1772负fixture未改。
- PR-02的授权为“纯shim或逐项命中批准清单的已删除态”;清单外缺失、残留
  实现须各有必红控制,计划随C10落地。本轮在C01停下,该实现和控制尚未执行。
- 仅当audit/bridge因旧址缺失无法读取历史拓扑时,才可在所属组改读43a6aa6
  不可变blob,断言不改。本轮失败不是旧址缺失,没有使用此兜底。

主树既有 `.gitignore` 改动及4个docs删除未处理、未提交。F、predicate、
exemption、既有OBS均未改。冻结F sha256仍为
`b9d720028164faec8c91d87a02cfa75475e1f8e1fff86e8244a2c0ef55bedaf0`。

### 36.2 C01 提交与提交后实测

C01 `a214187141bd8bf1712ed9464baf4f0906160dc5`:只去除
`ci_triage/verify/__init__.py`批准的16个转出及其`__all__`,保留包和docstring。
无调用方需翻转、无测试删除、未触及其它壳。对应独立干净worktree为
`/tmp/p49-terminal-C01`,测试使用该commit的代码和测试,不是43a6aa6改前代码。

完整命令、环境、commit/tree、原始stdout/stderr在 `execution/C01/*.command.json`
及相邻`.log`。执行器原文随命令记录,使用独立venv
`/tmp/p49-a0-regression-43a6aa6`,PYTHONPATH按该组worktree的scripts目录派生,
清MYPYPATH、禁pytest插件自动装载。实测如下:

```text
python -m pytest tests -vv -p no:cacheprovider
1343 passed, 1 skipped in 25.16s
EXIT=0
mypy <CI十个包,完整argv见mypy.command.json>
Success: no issues found in 88 source files
EXIT=0
ruff check .
All checks passed!
EXIT=0
lint-imports --no-cache
Contracts: 6 kept, 0 broken.
EXIT=0
python docs/clang-fix-campaign/tools/symbol_audit.py
INCOMPLETE: GerritSubmitError in tizen_gerrit_submit/gerrit_submit.py: present in source but not audited
INCOMPLETE: <top-level-count> in tizen_gerrit_submit/gerrit_submit.py: expected 23, measured 24
SUMMARY | 197 SYMBOL OK | 4 MODULE-SCOPE OK (48 SYMBOLS COVERED) | 0 MISMATCH | 2 INCOMPLETE
EXIT=1
```

### 36.3 PHASE2-03: 旧门禁清单未随项4新增异常类型同步

状态 **OPEN / STOPPED**。E11-3(4)第一项要求既有设计门禁全绿,但:

| 位置 | 事实/冲突 |
|---|---|
| `tools/symbol_audit.py:71` | submit顶层计数仍钉23 |
| `tools/symbol_audit.py:260` | GERRIT_SUBMIT_SYMBOLS未登记GerritSubmitError |
| `tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:31` | 新异常类型真实存在 |
| 同文件`:384` | `_run_git`超时路径抛出该异常 |
| `5213c5d` | 末批commit A加入该类型,非本轮C01新增;原diff留在 `execution/GerritSubmitError-origin.diff` |

按“任一项失败回退该组”执行:

```text
git revert --no-edit a214187141bd8bf1712ed9464baf4f0906160dc5
[clang-fix-campaign 864c778] Revert "refactor(ci-triage): remove verify package compatibility exports (P4.9 terminal C01)"
git diff 74ff34c 864c778 --
(空输出,exit 0)
```

回退commit `864c778a505fb9e71f1981ade447f2f9aedc4dfe`的tracked内容与批准前
74ff34c逐字节一致。独立回退worktree `/tmp/p49-terminal-C01-reverted` 仅做
故障/回退确认,未继续后续删除验证。相同audit命令再次exit1,两份完整stdout
逐字节相等;证明不是C01删除造成的清单漂移。回退后全量:

```text
python -m pytest tests -vv -p no:cacheprovider
1343 passed, 1 skipped in 25.19s
EXIT=0
C01 total=1344 passed=1343 skipped=1 removed=0 added=0 changed=0
C01-reverted total=1344 passed=1343 skipped=1 removed=0 added=0 changed=0
REVERT all tracked files equal approval commit 74ff34c; git diff empty
AUDIT before/after revert stdout byte-identical; both exit=1, two INCOMPLETE
```

逐nodeid证明/诊断程序见 `execution/C01-stop-proof.json`,回退复跑原文见
`execution/C01-reverted/`。批准的4个拟删测试本轮一个也未删除。

候选处置(未执行):由设计方明确将项4已批准新增的GerritSubmitError同步到
权威归属登记、SPECS及其机械桥,并按实际完整集合更新计数,保留集合等价
护栏;同步后先复跑完整审计再重新执行C01。不能只抬计数、不补册,不能把
当前实现换成历史源码以掩盖新增能力。本轮不自行改冻结表或审计判据。

### 36.4 停点

C01 **REVERTED**;C02-C13 **NOT_STARTED**;D **NOT_STARTED**。
第一项门禁转红后,bridge/其它后续设计门禁、31入口、import-all、删除后
名字复扫、打包安装/入口help均 **NOT_RUN**。没有冒称残留只剩允许类别,
没有生成DONE收口文档。PR-02的C10实现仍待执行,不是放弃控制。
本轮新增停止项1(PHASE2-03);保留本轮人工批准与11条历史键登记,等待设计方
对上述清单同步缺口裁决。不得在失败组内修补后继续。

## 37. PHASE2-03 补登记与全套门禁复核

设计方轻量裁决:根因是末批commit A验收漏列既有设计门禁,
GerritSubmitError自5213c5d起未登记。PHASE2-03的补登记处置已获批准:
在GERRIT_SUBMIT_SYMBOLS补该类型、精确顶层数24;skill-5 v1.3.2权威表补行
并注明终止稿§4/勘误1–3的行为变更来源。集合等价/归属判据不改,
不改生产实现、不改末终止冻结稿或predicates,不回写历史快照。

本补登记提交独立于C组。提交后以其HEAD的干净worktree运行全部既有设计
checker与CI验证(含coverage),每条命令/env/exit/原文分别留档。其它A/B遗漏
若只需补登记则按本轮授权单列处理;涉及行为改变则停报。
仅全部通过后才重启C01→C13,每组仍按E11-3(4)提交后验证、失败回退停报。
当前状态:PHASE2-03 **补登记完成,待提交后全门禁复核**;C组未重启,D未开始。

### 37.1 补登记后的首次全checker复跑

补登记commit `1cf3ee2` 已推送,在 `/tmp/p49-terminal-REG03` 复跑现行checker
及其控制。symbol与bridge均为198符号+4模块全绿,design.md主检查也绿。
明文E11-5停用的静态发现工具未重新升为门禁,由全量单测覆盖其既有语义;
没有运行新OBS producer。命令全集与原文见 `execution/REG03/checkers/`。

本轮补登记配套修正(非生产行为修改):

- skill-5正文原“以下23行”引导句的删改触发了既有来源逐行包含校验;
  恢复该句为明确标注的抽取期原文引用,当前表单独标注末批补登记,新类型
  行及行为来源说明不变。既有来源读取/逐行包含断言和expected_diff不改。
- skill-5 ledger的target_sha256同步实际新正文hash,仅该字段更新;
  历史语料、8个binding、期望命中与全部判据不改。此为版本钉定的机械补登,
  不是bootstrap重算或从扫描结果反推基线。
- 首轮执行器误调用了skill-6 ledger不存在的admission配置,该命令exit2
  不是设计缺陷。skill-6准入实际由branch_inventory admission-v17承载,
  已实跑exit1且required=2/2。后续命令清单纠正此调用,保留原失败日志。
- 首轮terminal负控制虽exit1但被上游来源缺失挡住,不能证明各负例被正确
  捕获;配套修正后须全部重跑并核对红因,不得将首轮这些exit1记作通过。

另外发现两类历史fixture问题,不属于本次符号补登记,待完整取证后停报:
文档checker的v1.5.2历史样本未入库;symbol的两个旧report拓扑fixture读取的
当前旧址已是shim,固定43a6aa6该旧址也已是shim。未选择其它历史SHA替代,
未改symbol_audit的负fixture或断言。C01尚未重启。

### 37.2 提交后实跑结果(2026-10-07)

本轮已推送的独立补登记提交:

- `1cf3ee2bff7dcd0412fa4246ebc99af95de8873e`:GerritSubmitError入SPECS/正文,
  精确顶层数24,集合等价/归属判据未改。
- `787b8040245907c3c849d80478e30961d26a4ed2`:历史来源原文保留、当前表
  与历史计数语境分开、ledger目标正文hash同步。不是C组提交。

完整复跑锚定后者,工作树 `/tmp/p49-terminal-REG03b`,tree
`1041a73fc09811b144b3851ea5819c95b012db6d`。独立venv沿用
`/tmp/p49-a0-regression-43a6aa6`,Python3.12.3。原样CI工作流另由GitHub
Actions在Python3.11实跑,与本地结果分列,不得互相替代。
全部90条checker/控制的命令、实际/预期exit、逐项stdout链接见
[门禁逐项表](a0-evidence/phase2/execution/REG03b/gate-results.md);
原始argv/env/程序/输出hash见同目录 `checkers/commands.json`。

```text
python -m pytest tests/ -v -p pytest_cov --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
Required test coverage of 80% reached. Total coverage: 94.62%
1343 passed, 1 skipped in 29.47s
EXIT=0
mypy <ci.yml列出的十个包>
Success: no issues found in 88 source files
EXIT=0
ruff check .
All checks passed!
EXIT=0
lint-imports --no-cache
Contracts: 6 kept, 0 broken.
EXIT=0
python docs/clang-fix-campaign/tools/symbol_audit.py
SUMMARY | 198 SYMBOL OK | 4 MODULE-SCOPE OK (48 SYMBOLS COVERED) | 0 MISMATCH | 0 INCOMPLETE
EXIT=0
```

bridge亦为198符号+4模块全绿,exit0。design.md主检查exit0。
skill-4 check/admission/47个OUT_OF_SCOPE/22个per-binding、skill-6 ledger
及branch_inventory 69/0、parser24/24、v1.7准入2/2均符合各自预期exit。
skill-5准入与8个per-binding符合预期,但check未通过,详见PHASE2-06。
terminal predicate冻结hash核对exit0;expected_diff正常exit0、各反向exit1;
phase A投影正常exit0、两反向exit1。本轮未运行任何新OBS producer。

nodeid机械集合证明(`REG03b/nodeid-proof.json`,生成命令与源码留档):

```text
NODEIDS baseline=1344 current=1344 removed=0 added=0 verdict_changes=0
APPROVED_DELETIONS still_present_and_passed=4 deleted=0
CHECKERS commands=90 unexpected=4
```

90项中86项符合预期,4条不符合预期。负控制虽输出MISMATCH,若红因错误或
退出值不符则仍算FAIL,不能拿它抵销失败。已批准4个拟删测试全部仍通过。

远端CI run `37612769455` (HEAD `787b804`):checkout/setup-python/系统依赖/
Python依赖/Lint/Type check均success;Tests失败。状态API不提供成功步骤的
数字exit,不伪造逐步exit0;失败步骤原文明确exit1。完整日志/状态在
`REG03b/ci-log.log`、`ci-status.log`,读取命令与环境各有command.json。

```text
git ... fetch --no-tags --prune --no-recurse-submodules --depth=1 origin +787b8040245907c3c849d80478e30961d26a4ed2:refs/remotes/origin/clang-fix-campaign
ValueError: AUTHORITY_GIT_BLOB: fatal: path 'docs/clang-fix-campaign/p49-terminal-batch-design-v1.31-FROZEN.md' exists on disk, but not in '8e72c345afc18efd118dd5880cd8ebd6b96e7bb1'
106 failed, 1237 passed, 1 skipped in 44.37s
Process completed with exit code 1.
```

注意:上面git/错误行仅摘去CI时间前缀;全长原文以日志为准。
`gh run view --log` exit0只表示下载成功,不是CI通过。

### 37.3 新停止项(全部 OPEN,待裁决)

PHASE2-03原“未登记异常类型”缺口已补录并经双道验证;不等于其要求的
全门禁闸门已通过。本轮发现以下4组阻塞,不改生产、不放宽历史断言:

| 编号 | 文件:行与实际失败 | 困难/边界 | 候选处置(未执行) |
|---|---|---|---|
| PHASE2-04 | `tools/symbol_audit.py:1773/:1827/:2039` 两个旧report拓扑fixture失效:duplicate-spec-root-mismatch实际exit0(预期1),twin-both-binary-key实际exit1(预期0) | 当前旧址是shim,`43a6aa6`旧址也是shim,均没有_attrs_to_map定义;不是“旧址文件缺失”。前轮明确禁止改此负fixture,只授权缺文件时取43a6aa6,不能擅选更早SHA | 设计方批准一个抽取前不可变拓扑输入及适用fixture范围;仅替换取证输入,保持二元组/skill-root断言。不能改断言接受definition-not-found作为正确红因 |
| PHASE2-05 | `tools/check_design_doc.py:773-799` self-test exit1,37/38;historical-v1.5.2样本未入库 | `git ls-files`该样本空;主工作树同名untracked草稿不是获准输入,不得擅自纳入 | 确认并批准该历史样本的原字节/来源hash入库,或指定已有不可变输入;不跳过历史控制、不改expected_counts |
| PHASE2-06 | `tools/design_drift_ledger.py:1046-1047` skill5 check exit2:`target design differs from the configured final corpus document`;数据文件`:2062/:2091-2093` | PHASE2-03正文已变更,目标hash已同步,但最后语料仍是原v1.3.2。该语料也参与原始diff/span/候选台账,不止一个目标hash | 批准对应语料与其源diff登记同步的口径,保留原历史Git锚,按既有规则复核台账;不得改成跳过字节比较,不得bootstrap从本次扫描反推期望集 |
| PHASE2-07 | `.github/workflows/ci.yml:13` checkout默认浅历史;实跑日志第92行`--depth=1`,Tests exit1,106失败 | 不可变blob取证依赖8e72c345/cbd3a22等历史提交,浅克隆拿不到;本地完整仓库绿不能替代CI | 补齐CI历史输入(例如checkout fetch-depth:0)后原样复跑CI,保留blob hash与逐字包含校验,不回退读取当前正文、不放宽单测 |

symbol两项失败原文:

```text
NEGATIVE_FIXTURE | duplicate-spec-root-mismatch | MISMATCH: definition _attrs_to_map not found in ci_triage/gbs_report.py
EXIT=0 (expected=1)
KEY_FIXTURE | twin-both-binary-key | ci_triage/gbs_report.py:_attrs_to_map | consumers=() | internal=() | MISMATCH: definition _attrs_to_map not found in ci_triage/gbs_report.py
EXIT=1 (expected=0)
```

完整原文在 `REG03b/checkers/symbol-key-twin-both-binary-key.log`。
固定43旧址的实际blob见 `REG03b/old-topology.log`;历史样本tracked查询见
`historical-sample-tracked.log`;正文与语料的纯新增diff见 `corpus-diff.log`。
没有改旧fixture、没有补一个伪造历史文件、没有重算候选/判据凑绿。

### 37.4 本轮停点

**STOPPED / 4组新停止项**。C01-C13 **NOT_RESTARTED**;D **NOT_STARTED**。
不生成DONE收口文档,不声称名字残留复扫已通过;31入口/import-all/删除后
名字复扫/打包入口help尚未作为本轮删除后验证运行(本轮没有删除)。
补登记与证据保存均独立于C组,无需回退不存在的C组实施。

`git diff --exit-code 6b456c9 HEAD -- 'tizen-*/scripts/**' tests <末终止冻结稿> <predicates.json> <measurement_exemptions.json>`
为空且exit0,完整命令见 `REG03b/protected-zero-diff.command.json`。
symbol_audit改动仅新增一个SPECS行与count23→24,完整diff在
`REG03b/symbol-changes.log`,包括被禁止修改的负fixture在内的其它逻辑零改动。
主工作树既有无关改动和untracked草稿均未处理。

原始CI日志及原始git diff输出保留原字节(含尾随空格),因此包含这些证据的
`git diff --cached --check` 返回2并报告日志空白;不清洗已取证stdout。
手写文档/JSON单独的diff空白检查通过;这不是pytest或设计门禁结论。

## 38. PHASE2-04～07 裁决执行与来源前检(2026-10-08)

本轮 `git pull --ff-only`:Already up to date。按设计方新裁决,门禁对照固定
`43a6aa625f27da46daba190657bf62256080c68e` 的90条原样命令,不再把基线已存在的
失败误认本批回归。主工作树无关改动不处理,固定基线工作树起跑前status为空。
基线完整argv/exit/原文/运行器源码在
`a0-evidence/phase2/execution/BASE43/checkers/commands.json` 及其相邻90份日志。

### 38.1 基线与遗留

```text
python /tmp/p49-checker-matrix.py /home/linhao/Toolchain/development/LogAnalysisSkill-a0-43a6aa6 BASE43
SUMMARY commands=90 unexpected=20 regressions=BASELINE
EXIT=0
```

运行器exit0表示基线采集完成,不是90条都通过。20条基线不符全部逐条登记
在 [carried-over-issues.md](carried-over-issues.md),包含命令、基线与当前exit
和原因。当前对照为REG03b (`787b804`,与本轮起点checker实现相同):

- PHASE2-04 **CLOSED_AS_CARRIED**:duplicate-spec-root-mismatch 两树exit0
  (预期1)、twin-both-binary-key 两树exit1(预期0);均因旧report已是shim。
- PHASE2-05 **CLOSED_AS_CARRIED**:check_design_doc --self-test 两树exit1,
  37/38,均缺未入库v1.5.2历史样本。未把untracked稿加入交付面。
- 另17条在43a6aa6不存在的末批工具调用均exit2,当前均符合原预期。
  按要求登记其基线事实,标RESOLVED,不冒充当前未修问题。
- 当前仍OPEN_CARRIED **3条**;全部遗留登记行 **20条**。
- skill5 ledger check基线exit0、当前exit2,仍是必须处理的回归,
  不纳入非阻塞遗留。PHASE2-06尚未关闭。

### 38.2 PHASE2-07 CI 输入补齐

`.github/workflows/ci.yml` 仅在 checkout 增加 `with: fetch-depth: 0`,其它
workflow步骤不动;无生产代码改动。用于使原样测试拿到已有的不可变Git
blob,不更改blob hash或任何断言。提交后等待远端CI,以run的Tests实际结果
判定PHASE2-07,不得用本地pytest代替。远端run以本提交SHA查询,未预填结果。

### 38.3 PHASE2-08: skill-4 签批 tree 不含当前 ledger 必需语料

状态 **OPEN / STOPPED**。改读取逻辑之前按已立“真实输入可满足性”要求
枚举三批所有当前语料/目标路径,逐个向各自签批commit做git show并核hash:

| 批次 | 签批commit | 语料+目标读取项 | 缺失/不符 |
|---|---|---:|---:|
| skill-4 | `8ed758801dcf61b2763b6d89212efe9042bf4b54` | 15 | 1 |
| skill-5 | `81ada5408a0e05e86aa54346cdc0be822be4b608` | 7 | 0 |
| skill-6 | `53e1bad73fa5df06b34e601abdb82f1d1e7c6328` | 10 | 0 |

skill5目标hash按指定签批稿核对为0e2de5ff...f27,不是本轮补登记正文9c9e4c...937;
这是取证前检,尚未修改工具或data。完整32项命令/exit/hash和生成程序见
`a0-evidence/phase2/execution/BASE43/history-input-probe.json`。

```text
git cat-file -e 8ed7588:docs/clang-fix-campaign/history/skill4/p49-skill4-build-verify-design-v1.12-FROZEN.md
fatal: path 'docs/clang-fix-campaign/history/skill4/p49-skill4-build-verify-design-v1.12-FROZEN.md' exists on disk, but not in '8ed7588'
EXIT=128
```

冲突位置:

- 当前 `tools/design_drift_ledger.json:8047-8049` 强制该语料入序列,
  hash=`c0f730ab378b97b1f0a5483e508c9003d864248c7225db2405c71e955f618408`。
- 该路径在skill-4实现期更名后,直到skill-5的 `a8620f1` 才因三段版本规则
  恢复入库;`git log -- <path>` 可复核。skill4签批时仅13份语料,当前14份。
- 当前expected_matches为84项,签批旧data为83项;把整份data回退为签批版
  会改期望集,违反本轮“断言、期望集、计数一律不改”。不能这样修。
- 严格从8ed7588读现有全部语料会产生基线不存在的缺文件失败,也不能
  将其算作carried-over。未实施该替换,未修改checker/数据/期望集。

候选处置(未执行):只对此一语料批准
`a8620f1ba7caea6ea083b042596830be54bd2fd6:<该路径>` 的不可变blob,
保留当前钉定hash、14版序列与84个期望项;其余skill4稿仍取8ed7588。
已向设计方请求这个单文件来源例外,未获回复前不自行选择。

### 38.4 本轮边界

本轮独立提交不属C组;落实基线、遗留记账与CI历史输入补齐。
历史工具blob迁移/篡改引用负控制 **PENDING_PHASE2-08** (未声称已实现)。
C01-C13未重启,D未开始;4个批准删除测试仍保留,未执行删除后残留/打包验证。
先前冻结稿、predicates、OBS和全部判据保持原样。本轮新停止项1(PHASE2-08),
它不是43a6aa6已有失败,不能按基线规则自动豁免。

## 39. PHASE2-08 内容哈希定位裁决(2026-10-08)

PHASE2-08 **CLOSED_BY_RULING**:历史输入按数据文件中每个(path, SHA-256)
在完整Git历史内定位blob,不再指定签批提交,不增逐文件例外。找不到或历史
不完整即红。§38.3的签批提交缺语料问题由此解决,不是修改期望集。

本独立提交(非C组)实现 `tools/historical_inputs.py`;接入
`design_drift_ledger.py`、`branch_inventory.py` 的历史文档输入及
`terminal_expected_diff.py` 的skill5历史映射表。实现侧AST枚举、当前
symbol_audit/table_audit_bridge仍读当前代码/正文;OBS输入和产出不改。
ledger原始diff改用找到的原字节,候选路径/span/断言保持原样。
skill5 `target_sha256` 恢复为
`0e2de5ff80c7f36940e455ec75f4f6872caa4fd93be360ad0fcfd0e59c755f27`;
除此字段不改三批数据,不改期望集、版本数和计数。

新增 `test_historical_inputs.py` 对每个改动工具核验错hash和错路径均红,
并测试本地内容变异不影响历史读取、skill4 v1.12语料自然定位。
定向预检实际输出:

```text
env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /tmp/p49-a0-regression-43a6aa6/bin/python -m pytest tests/unit/test_historical_inputs.py tests/unit/test_design_drift_ledger.py tests/unit/test_terminal_expected_diff.py -q
112 passed in 4.98s
EXIT=0
/tmp/p49-a0-regression-43a6aa6/bin/python -m mypy docs/clang-fix-campaign/tools/historical_inputs.py docs/clang-fix-campaign/tools/design_drift_ledger.py docs/clang-fix-campaign/tools/branch_inventory.py docs/clang-fix-campaign/tools/terminal_expected_diff.py
Success: no issues found in 4 source files
EXIT=0
/tmp/p49-a0-regression-43a6aa6/bin/python -m ruff check docs/clang-fix-campaign/tools/historical_inputs.py docs/clang-fix-campaign/tools/design_drift_ledger.py docs/clang-fix-campaign/tools/branch_inventory.py docs/clang-fix-campaign/tools/terminal_expected_diff.py tests/unit/test_design_drift_ledger.py tests/unit/test_historical_inputs.py
All checks passed!
EXIT=0
```

提交后在独立工作树记录 `a0-evidence/phase2/execution/HASH08/`:
历史blob定位结果、90项相对BASE43比较、全仓pytest逐nodeid、mypy/ruff/lint、
远端CI。完整验收 **PENDING**;通过后才从C01重启,不预报通过。

### 39.1 独立提交验证完成

实现提交 `f196f5536b4e6b479320d182b8cd3fa558049712`,已push。
干净工作树 `/tmp/p49-terminal-HASH08`,逐命令/环境/exit/原输出见
`a0-evidence/phase2/execution/HASH08/`。实跑摘要:

```text
python3 /tmp/p49-checker-matrix.py /tmp/p49-terminal-HASH08 HASH08
SUMMARY commands=90 unexpected=3 regressions=[]
EXIT=0
pytest tests/ -v -p pytest_cov --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
1351 passed, 1 skipped in 29.77s; coverage 94.62%; EXIT=0
mypy: Success: no issues found in 114 source files; EXIT=0
ruff check .: All checks passed!; EXIT=0
lint-imports: Contracts: 6 kept, 0 broken.; EXIT=0
history-proof: HISTORY_INPUTS=34 CONTROLS=4 RED_AS_EXPECTED; EXIT=0
```

两种变异在ledger/branch四次真实命令均exit2且HISTORY_NOT_FOUND;
expected-diff两控制由新增单测覆盖。skill4 v1.12固定语料自然定位到
`a8620f1`中相同sha的blob,34项各自commit/blob/hash见history-proof.log;
这些commit是检索结果而非工具选择规则。
远端 [CI 37713176965](https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37713176965)
整体success,Tests success;原始job/log见remote-ci及remote-ci-log。
PHASE2-06/07/08均 **CLOSED**;20条遗留记录中17已解决、3仍carried,
不把历史失败改称通过。用户既有无关工作树改动仍未纳入任何提交。

## 40. C组逐组实施

### 40.1 C01 第二次实施

前置为§39.1本地及远端无新增失败。按已批准gate-package去除
`ci_triage/verify/__init__.py`16条兼容绑定与其__all__,保留docstring和包。
本组不删测试,不改业务逻辑。提交后五项验证记录到
`a0-evidence/phase2/execution/C01R/`;结果 **PENDING**。
只有本组验证通过才进入C02;新增失败/行为变化/OTHER即回退本组并停报。

C01 `f8a289a` 五项 **PASS**:full-tests 1351/1,nodeids lost=0/changed=0;
90 checkers regressions=[];mypy/ruff/lint exit0;31/31 smoke;213/213 live
Python files import(包含工具/测试的独立解释器加载);residual 853 HISTORICAL,
OTHER=0;wheel构建和新venv安装exit0,console_scripts=0,另5个安装后模块入口
--help均exit0。命令和输出在C01R对应日志。
打包环境两次准备失败原样保留:禁build-isolation时缺setuptools(固定43原样
同exit2,BASEENV日志),系统缺ensurepip。最终采用pyproject声明的隔离构建,
venv --without-pip加已有pip --python安装,不改仓库或生产代码使其通过。

### 40.2 C02

删除登记的quickbuild.py纯shim(17绑定),将test_ci_triage的6个HTTP import
直取shared/quickbuild_http;测试内容与断言不改。本组不删nodeid。
五项验证记录位置 `a0-evidence/phase2/execution/C02R/`,结果 **PENDING**。

C02 `1c42957` 五项 **PASS**:1351/1、lost=0/changed=0;90 checkers
regressions=[];mypy/ruff/lint exit0;smoke31/31;import-all212/212;
residual HISTORICAL=6783/RELEASE=29/OTHER=0;wheel/install及5模块help exit0。

### 40.3 C03

只去runner中的discover_sibling_pythonpath兼容import,业务函数不动;
规范定义shared/env不动,本地零Load证据沿用批准清单。无测试删除。
五项验证 `a0-evidence/phase2/execution/C03R/` **PENDING**。

C03 `ac26333` 五项 **PASS**:1351/1、lost=0/changed=0;90 checkers
regressions=[];mypy/ruff/lint exit0;smoke31/31;import-all212/212;
residual HISTORICAL=39741/RELEASE=33/OTHER=0;wheel/install及5模块help exit0。
残留原始stdout从C01R起无损gzip保存(`residual.log.gz`),避免后续扫描反复
嵌套历史输出;每份解压后hash必须等于相邻command.json的output_sha256。
C01R/C02R/C03R此次机械转换三份全部相等,扫描范围和命中分类不改。

### 40.4 C04

删除旧gerrit.py15条兼容绑定;仅删除批准nodeid
`tests/unit/test_gerrit_fetch.py::test_legacy_module_reexports_implementation_and_types_by_identity`。
skill副本三行类型import为真实依赖,原样保留。其它行为/包根测试不改。
五项验证 `a0-evidence/phase2/execution/C04R/` **PENDING**。

C04 `99add0d` 五项 **PASS**:1350/1,仅少批准Gerrit identity一例,其它nodeid
状态不变;90 checkers regressions=[];mypy/ruff/lint exit0;smoke31/31;
import-all211/211;residual HISTORICAL=7704/RELEASE=37/OTHER=0;
wheel/install及5模块help exit0。

### 40.5 C05

删除sources.py登记的4绑定纯shim;真实实现qb-discover不动,无测试删除。
五项验证 `a0-evidence/phase2/execution/C05R/` **PENDING**。

C05 `d8e8d85` 五项 **PASS**:1350/1、累计只少获批1例;90 checkers
regressions=[];mypy/ruff/lint exit0;smoke31/31;import-all210/210;
residual HISTORICAL=9086/HISTORICAL_KEY=1/RELEASE=44/OTHER=0;
wheel/install及5模块help exit0。

### 40.6 C06

删除verify/convergence.py登记的8绑定纯shim;公共别名和skill中的真实定义
均不动,同一性契约测试保留,无新删nodeid。
五项验证 `a0-evidence/phase2/execution/C06R/` **PENDING**。

C06 `b54e749` 五项 **PASS**:1350/1,累计只少获批1例;90 checkers
regressions=[];mypy/ruff/lint exit0;smoke31/31;import-all209/209;
residual hits=10196/OTHER=0;wheel/install及5模块help exit0。

### 40.7 C07

删除verify/build_verify.py的29绑定兼容壳;删除获批nodeid
`tests/unit/test_build_verify_legacy_wiring.py::test_legacy_shims_preserve_all_migrated_symbol_identities`。
该文件只有此唯一用例,无其它测试/fixture,故一并移除空宿主文件;
其它skill行为、路径锚与包根测试原样保留。后续C08/C09不重复删该用例。
五项验证 `a0-evidence/phase2/execution/C07R/` **PENDING**。

C07 `f962093` 五项 **PASS**:1349/1,累计只少获批2例,其它状态不变;
90 checkers regressions=[];mypy/ruff/lint exit0;smoke31/31;
import-all207/207;residual hits=13139/OTHER=0;wheel/install及5模块help exit0。

### 40.8 C08

删除verify/edit_spec_guard.py的12绑定纯shim;skill实现在原处保留,
不合并EDIT_SPEC_SCHEMA,本组无测试删除。
五项验证 `a0-evidence/phase2/execution/C08R/` **PENDING**。

C08 `9da38e6` 五项 **PASS**:1349/1,累计只少获批2例,其它状态不变;
90 checkers regressions=[];mypy/ruff/lint exit0;smoke31/31;
import-all206/206;residual hits=15005/OTHER=0;wheel/install及5模块help exit0。

### 40.9 C09

删除verify/workspace.py的21绑定组合shim,shared与build-verify两侧真实实现
不动,本组无测试删除。历史归属键保留,不将它们误作生产import。
五项验证 `a0-evidence/phase2/execution/C09R/` **PENDING**。

C09 `0e6507e` 五项 **PASS**:1349/1,累计只少获批2例,其它状态不变;
90 checkers regressions=[];mypy/ruff/lint exit0;smoke31/31;
import-all205/205;residual hits=18319/OTHER=0;wheel/install及5模块help exit0。

### 40.10 C10 / PR-02

删除verify/failure_classify.py的13绑定兼容壳。module-scope判据只新增已批准
的缺失状态:按内容hash读批准清单,逐项匹配MODULE旧址,同时确认不在Git索引且
磁盘不存在(悬空symlink也拒绝)。旧址仍存在时保持原纯re-export结构检查,
任何def/class或非转出语句仍红。不修改已有负fixture或归属/计数判据。

新增两个人工负fixture及参数化测试:unapproved-deleted-shim、
legacy-shim-residual-implementation,分别要求exit1与正确红因。
PR-02的旧址键仍承担获批缺失状态查询,按PHASE2-01定义逐项登记HISTORICAL_KEY:
symbol_audit.py原356行,来源为批准清单原字节hash;不是新的import/patch/入口,
不是增加删除授权。加上既有11条键共12条登记,原8项裁决及负fixture未改。
本组不删测试,新增2个防滥用测试。五项验证位置 `execution/C10R/` **PENDING**。

### 40.11 C10 回退 / PHASE2-09 停止报告

C10尝试提交 `6e27fec28d0e9c41ad46a19140b0034ee1b25259` 未通过新增工具的
定向类型检查,按批准协议回退该组并停止;不是既有问题,不纳入carried-over豁免。
测试虽1351 passed/1 skipped(新增2控制),90条既有checker无新增失败,不能
覆盖另一项类型检查的真实失败。两条新负fixture均exit1且红因正确,完整输出
保留在 `execution/C10R/`;后续import-all/残留/打包未完成,不记PASS。

同一命令在三棵干净树的实测(同venv,mypy2.4.0):

```text
/tmp/p49-a0-regression-43a6aa6/bin/mypy docs/clang-fix-campaign/tools/symbol_audit.py
43a6aa6: Success: no issues found in 1 source file; EXIT=0
0e6507e (C09): Success: no issues found in 1 source file; EXIT=0
6e27fec (C10): Found 5 errors in 1 file (checked 1 source file); EXIT=1
```

原文位置(以失败commit `6e27fec` 为准):symbol_audit.py:1819/:1831/:1833/:1834。
原因:本轮新增分支的`spec`/`result`被推断为ModuleScopeSpec/ModuleScopeResult,
与同函数既有fixture分支的SymbolSpec/AuditResult复用名字冲突。这是实现方
本轮引入的类型错误,不是设计冲突,不修改基线或期望集来放行。
候选处置:在新分支改用独立`module_spec`/`module_result`后重新实施C10及其
全部验证;**本轮没有实施该修复**,等待放行续跑。

回退范围仅C10的classifier壳删除、审计工具/两控制测试/PR-02历史键登记;
C09验证记录与C10失败记录保留。回退后生产、测试、工具与C09逐字节一致。
执行状态 **STOPPED_NEW_REGRESSION**:C01-C09完成,C10回退,C11-C13未执行,
D未开始,不得声称终止批次完成。原8项HISTORICAL_KEY与原负fixture未改。
停止报告新增1条(PHASE2-09);遗留表仍20行/3项OPEN_CARRIED,本条不混入。

最新完整通过组C09:全仓1349/1(批准4例已删2例,其余未删),90checker无新增
失败,mypy/ruff/lint退出0;31入口/205文件import/残留OTHER0/打包与5help通过。
C09远端CI SUCCESS,Tests成功:
https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37715508991 。

回退提交 `63e9a7796ad6f2248c9ed16641e274bcd2679395` 已推送。独立干净树
`/tmp/p49-terminal-C10STOP`复验,完整命令/env/逐nodeid/输出见
`a0-evidence/phase2/execution/C10STOP/`:

```text
git diff --exit-code 0e6507e -- ':(glob)tizen-*/scripts/**' tests/ docs/clang-fix-campaign/tools/
(empty output); EXIT=0
python -m pytest tests/ -v -p pytest_cov --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
1349 passed, 1 skipped in 30.97s; EXIT=0
nodeids: base=1352 current=1350 lost=2(均在批准清单) changed={} added=[]; EXIT=0
mypy docs/clang-fix-campaign/tools/symbol_audit.py: Success: no issues found in 1 source file; EXIT=0
mypy: Success: no issues found in 107 source files; EXIT=0
ruff check .: All checks passed!; EXIT=0
lint-imports: Contracts: 6 kept, 0 broken.; EXIT=0
```

回退HEAD远端CI SUCCESS,包括Tests步骤:
https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37715804408 。
此处停止是履行新增失败回退协议,不是把C10标完成;失败版本与证据仍在Git中。
回退源码比较采用Git显式glob路径规范,复跑记录为C10STOP/code-equality-explicit-glob;
原code-equality记录保留,不以含糊的目录通配写法作为生产范围证明。
release/P4.5 design/terminal冻结稿/predicates/exemptions本轮零diff;
终止冻结稿sha256仍为`b9d720028164faec8c91d87a02cfa75475e1f8e1fff86e8244a2c0ef55bedaf0`。
主树原有无关改动保留。尚未建立D收口文档或改变五项义务为已全部销账。

## 41. PHASE2-09 裁决与 C10 续做

2026-10-08 设计方轻量裁决批准按候选修复续做。§40.11的停止项
**CLOSED_BY_RULING**:新fixture分支仅把`spec`/`result`改为独立的
`module_spec`/`module_result`;`_approved_legacy_deletion`及两条控制不变。
失败原文保留在`execution/C10R/mypy-deletion-guard.log`,43a6aa6/C09对照
仍保留;修正diff与重跑记录落`execution/C10S/`,不覆盖第一次失败证据。
按原批准范围恢复C10的13绑定壳删除及PR-02历史键登记。

常设规则:若某组失败仅因本组新增或修改的工具/测试自身类型、lint、格式问题,
且与删除行为及调用方改写无关,允许同组修正并重跑全部组验证,证据必须包括
失败原文、修正diff和重跑结果,无需停止。删除或调用方改写导致的失败仍须
回退该组并停报;行为变化和OTHER同样不能据此放行。本规则不改基线期望集。

### 41.1 C10 重做

新fixture变量名独立,控制原文和获批删除判据不变。无新增测试删除,
新增的两条防滥用测试沿用首次C10原字节。提交后E11-3(4)五项验证
位于`execution/C10S/`,结果 **PENDING**;通过才推进C11。

C10重做 `1282005` 五项 **PASS**:1351 passed/1 skipped,累计只少获批2例,
新增2控制且其余状态不变;90 checkers regressions=[];mypy(106files)/
工具定向mypy/ruff/lint exit0;smoke31/31;import-all205/205;
residual hits=19816/OTHER=0;wheel/install及5模块help exit0。
`fixture-fix-diff.log`仅两局部变量改名;`controls-unchanged.log`为空且exit0;
`unapproved-deleted-shim.log`/`legacy-shim-residual-implementation.log`均exit1,
分别报未获批缺失、非转出FunctionDef。PHASE2-09 **CLOSED_VERIFIED**。

### 41.2 C11

删除verify/gerrit_submit.py的23绑定纯shim。只删除获批完整nodeid
`tests/unit/test_tizen_gerrit_submit.py::test_legacy_shim_preserves_all_symbol_identities`,
保留包根公开契约、分支/timeout/无push行为测试。旧MODULE_OWNERS键按原批准
HISTORICAL_KEY保留不改。五项验证`execution/C11R/` **PENDING**。

C11 `b2ec945` 五项 **PASS**:1350/1,累计只少获批3例,新增2控制保留且其余
状态不变;90 checkers regressions=[];mypy(105files)/ruff/lint exit0;
smoke31/31;import-all204/204;residual hits=21991/OTHER=0;
wheel/install及5模块help exit0。C10远端CI SUCCESS见C10S/remote-ci.log。

### 41.3 C12

删除gbs_report.py的21绑定纯shim,triage-report真实实现与qb-discover同名件
均不动。仅删除获批完整nodeid
`tests/unit/test_tizen_triage_report.py::test_triage_report_legacy_shims_preserve_all_symbol_identities`;
其包根/四fixture/arch/行为测试全部保留。旧拓扑fixture与bridge历史键按原
批准保留,不改symbol_audit原1772行负fixture。五项验证`execution/C12R/` **PENDING**。

C12 `8aed0b8` 五项 **PASS**:1349/1,累计只少获批4例,新增2控制保留且其余
状态不变;90 checkers regressions=[];mypy(104files)/工具定向mypy/ruff/lint
exit0;smoke31/31;import-all203/203;residual hits=23821/OTHER=0;
wheel/install及5模块help exit0。C11远端CI SUCCESS见C11R/remote-ci.log。

### 41.4 C13

删除report.py的3绑定纯shim;跨两个旧址的identity用例已在C12按批准删除,
本组不再删测试。真实report实现、公开包根与历史MODULE_OWNERS键不改。
五项验证`execution/C13R/` **PENDING**;全组通过后才准备D收口材料。

C13 `de9099ef51edad0f1f3cc920c109e7282da0a313` 五项 **PASS**:
1349 passed/1 skipped,累计只少获批4例,新增2控制,其余nodeid状态不变;
90 checkers regressions=[];mypy(103files)/工具定向mypy/ruff/lint exit0;
smoke31/31;import-all202/202;residual hits=24788/OTHER=0;
wheel/install及5模块help exit0。原始输出及argv/env/hash见C13R各command.json。

## 42. D 收口材料 / 实现终态待签批

### 42.1 结论和边界

五项义务逐项结论见[末批closeout](../../review/p49-terminal-closeout.md)与
[阶段总账](../../review/p49-extraction-phase-summary.md#p49-terminal-batch-ledger)。
A `5213c5d`落实项4;B `c1ea4ef`落实项3及项5的现状锁定;C01-C13落实
项1/项2。D只归档证据与状态,不再改实现、不运行新OBS producer、不自行签批。
人工输入:FatTank批准`74ff34c`原审批包13宿主/183绑定、4个完整nodeid及
分组顺序;9个PENDING_REVIEW已按批准逐项处置,并未授予目录级豁免。

`execution/C13R/final-proof.log`原始结论:

```text
hosts=13 bindings=183
production_changes_exactly_approved_hosts=true
other_existing_test_bodies_unchanged=true
protected_input_files_unchanged=27
base=1352 current=1350 lost=4 changed={} added=2
PASSED=1349 SKIPPED=1
HISTORICAL=24671 HISTORICAL_KEY=12 RELEASE=105 OTHER=0
guard_and_control_semantics_unchanged=true
FINAL_PROOF=PASS
EXIT=0
```

以上字段摘自原JSON,不是新运行输出格式。全部13组的9项正向记录及90条
checker比较也在该证明中按原始输出hash核对。真实依赖
`quickbuild_log.FailedPackage`与skill gerrit的三类型import原字节保留;
11个MODULE旧址已删除,2个BINDING宿主仅删批准转出,其def/class AST不变。
release快照、P4.5 design、冻结predicate/exemption、既有OBS事实与审批包不改。

### 42.2 精确相等与历史输出说明

§6改前状态为**DONE**,证据`phase1/prompt-rulings/before-verified/before.json`,
30场景逐条过schema/旧值/OBS一致性;A按PHASE1-03来源投影验收,B按完整登记。
`phase1/commit-b/after-b.log`为`AFTER=PASS phase=FULL scenarios=30`,exit0。
结构CLI仍打印旧提示`REAL_BEFORE=PENDING_SEG3`,它不读取实际双跑产物,
不能作为本轮采集状态;真实完成状态只由上述采集器证据给出。

精度澄清:§31曾简称“项5两场景登记仍NO_DIFF”,意指marker失败态字段不变。
勘误2/E2-2已使经过新签名的调用各自登记timeout kwarg,所以当前完整清单是
30个DIFF_SET、0个NO_DIFF、53条登记,不是两整场景NO_DIFF。marker存在状态、
原字节sha256、每个读取方结果均在未登记字段内精确相等,无全局掩码或字段忽略。

### 42.3 验证、挂账与停点

本轮C10/C11/C12/C13分别为`1282005`/`b2ec945`/`8aed0b8`/`de9099e`。
全仓基线从HASH08的1351/1,只删批准4例并新增2条护栏控制,成为1349/1。
失败原文、变量改名diff、判据与测试原字节一致证明及重跑见C10R/C10S,
不覆盖失败记录。PHASE2-09 **CLOSED_VERIFIED**,不是carried-over豁免。

遗留表20条基线记录中17条已符合预期,仅3条OPEN_CARRIED,无新增失败;
五项末批义务无新增DEFERRED。当前审计198 SYMBOL + 4 MODULE-SCOPE,
bridge同量且差异0;这些当前门禁仍读当前文件。历史ledger按内容hash读原文,
不以新计数或扫描结果修正期望集。

远端CI逐组结果见C10S/C11R/C12R/C13R的`remote-ci.log`。最终实现验收
已经完成,现在停下等待**设计方核验 + 一家评审**。D与本报告由所在Git commit
外部锚定,文件内不写自身SHA;签批前不将READY_FOR_REVIEW改为CLOSED。
