# P4.9 末终止批次 · OBS claim 判定条件(v1.2,A₀ 输入)

> **v1.2 修订(回应 Codex 编码前停止报告 PRED-04/05,见 stage14 `progress.md` §10.2)**:
> ①**给出完整的 schema 记法**(§1"schema 记法"):封闭记录、可选字段、数组、动态键映射、带判别字段的并集五种形式;
> 共用字段 `evidence` 的元素定义为两种变体的并集;**15 个 claim 的 `output_schema` 全部改写为完整结构化形式**,
> 不再用缩写(PRED-04);`exception_code` 改为按 `state` 区分的并集,`state=ABSENT` 时不得带 `value`、`state=VALUE` 时必须带;
> ②**`OBS-1.item3-predicate` 第 5 条的 LIVE 分支显式加上 `eq(@/exception_code/state,"VALUE")`**,与旁注一致(PRED-05)。
> **分工**:schema 只管结构(有哪些字段、什么类型、能否缺省);取值范围(枚举、正则、数量)一律只写在 predicate 里,不在两处重复。
> 其余条件与 v1.1 逐字相同。

> **v1.1 修订(回应 Codex 编码前停止报告 PRED-01/02/03,见 stage14 `progress.md` §9.3)**:
> ①**G4 改为显式节点**:新增 `schema_closed()`,每个 claim 的 predicate 都带一个;不再有"不写节点、由 verifier 另行检查"的条件(PRED-01);
> ②**补求值语义**:可选字段缺失时的比较、短路求值、求值错误一律判红(§1 末"求值语义");`OBS-1.item3-predicate` 第 5 条
> 改写为按 `state` 显式分支,不再依赖"缺失再取反"(PRED-03);
> ③**`OBS-6.intra-package-shim` 第 3 条改为可执行条件**;"发现面没有排除同包兼容壳"这一覆盖义务改由一条具名正控制承担,写入 §4(PRED-02)。
> 其余条件与 v1.0 逐字相同。

- **性质**:冻结稿 `p49-terminal-batch-design-v1.31-FROZEN.md` §8-2 与附录 B 规定"每个被引用的 claim 默认为 `ASSERTION`,
  其结构化 predicate 在 A₀ 首跑前登记并冻结带 hash;禁止实现方补写 `expected`"。本文就是这 15 个 claim 的 predicate 来源,
  **由设计方书写、FatTank 批准**。它不修改冻结稿的任何条款,只填冻结稿明确留给 A₀ 的空位。
- **适用范围**:附录 B 的 15 个 claim(B-1…B-7)。豁免清单 `measurement_exemptions` = ∅(冻结稿 §8-2 已实例化),故 15 个全为 `ASSERTION`。
- **编码与冻结流程**:
  1. Codex 按 §1 的语言把 §3 每条逐条编码进 `docs/clang-fix-campaign/tools/p49_terminal_data/predicates.json`,
     **一条要求对应一个节点,不增、不减、不改写**;某条无法编码或无法求值 → 停止报告,不得自行替换为近似条件;
  2. 设计方逐条核对编码与本文一致,FatTank 批准;
  3. 以单独 commit 冻结 `predicates.json` 与 `measurement_exemptions.json`(`[]`),记录 canonical hash;**此后才允许首次运行 producer**;
  4. 冻结后改动任何一条,走冻结稿第 3 条的勘误流程。
- **predicate 是要求,不是陈述**:下文所有常量都来自冻结文档(类二/类三),**不含任何需要对当前树运行命令才能得到的值**。
  若某条要求在当前树上不成立,说明冻结稿的前提与现实不符 —— 这正是本组 claim 要拦下的情形,**停止报告,不得改 predicate 迁就结果**。

---

## §1 predicate 语言(封闭)

**文档**:JSON。每个 claim 一个对象:`{claim_id, type:"ASSERTION", subject, quantifier, output_schema, predicate}`。

**路径**:JSON Pointer(RFC 6901)指向该 claim 的 producer 输出;`*` 表示数组全部元素;
`@` 表示 `forall`/`exists` 当前元素,`@/x` 为其子路径;`$ref(<claim_id>, <pointer>)` 引用另一 claim 的 producer 输出;
`$file(<相对路径>, <pointer>)` 引用 A₀ 的其它机器产物(只读;`E/` = `docs/clang-fix-campaign/dev_memory/stage14_p49_terminal_batch/a0-evidence/`,
与 Codex 在 stage14 `progress.md` §2.1 登记的路径约定一致;所引产物的字段名以本文为准,产物 schema 须提供这些字段);
`$ctx.<名>` 引用运行上下文(见下)。集合类节点(`set_eq`、`subset`、`in`)的参数可以是路径,也可以是常量数组。

**节点(封闭集合,不得扩充,扩充走勘误)**:

| 节点 | 含义 |
|---|---|
| `all[...]` / `any[...]` / `not(x)` | 逻辑组合 |
| `present(p)` | 路径存在且值不为 `null` |
| `eq(p, c)` / `ne(p, c)` | 等于 / 不等于常量 |
| `eq_path(p, q)` | 两路径值相等 |
| `in(p, [c...])` | 值属于常量集合 |
| `matches(p, "regex")` | 字符串匹配(Python `re.search` 语义) |
| `nonempty(p)` | 数组/对象/字符串非空 |
| `count(p) <op> n` | 元素个数比较,`<op>` ∈ {`==`,`>=`,`<=`} |
| `count_eq(p, q)` | 两处元素个数相等 |
| `set_eq(p, q)` / `subset(p, q)` | 值集合相等 / 包含(`p ⊆ q`) |
| `seq_eq(p, [c...])` | 数组按顺序逐项等于常量序列 |
| `keys_eq(p, [c...])` | 对象的键集合恰为常量集合 |
| `forall(p, node)` / `exists(p, node)` | 对数组每个 / 至少一个元素求值 `node` |
| `implies(a, b)` | 若 a 则 b |
| `sum_eq(p, q)` | `p` 下数值之和等于 `q` 的值 |
| `in_path(p, q)` | `p` 的值属于 `q` 所指的值集合 |
| `union(p, q, …)` | 多处值的集合并;只能作为 `set_eq`/`subset` 的参数 |
| `keys(p)` / `values(p)` | 对象的键数组 / 值数组;只能作为其它节点的参数 |
| `$value(p)` | 取路径 `p` 的标量值;只能作为 `eq`、`count(…) <op>` 的右侧 |
| `schema_closed()` | producer 输出(含各层嵌套对象与数组元素)的字段集合恰为本 claim `output_schema` 所声明:必填字段全部存在、不出现未声明字段;标 `?` 的字段可缺省 |

**schema 记法(v1.2)** —— 每个 claim 的 `output_schema` 用下列五种形式写成,`schema_closed()` 按它逐层核对:
| 记法 | 含义 |
|---|---|
| `str` / `int` / `bool` | 标量类型;**不含取值约束**(取值约束只写在 predicate) |
| `{a: T, b?: T}` | **封闭记录**:恰含所列字段;`?` 标记的字段可缺省,其余必填;出现未列字段即红 |
| `[T]` | 数组,每个元素都须符合 `T`;可以为空(需非空时由 predicate 写 `nonempty`) |
| `map<str, T>` | **动态键映射**:键为任意字符串,每个值都须符合 `T`;键的取值约束只写在 predicate |
| `A \| B` | **带判别字段的并集**:每个分支都是封闭记录,且含同名判别字段,其类型为字符串常量(如 `state: "ABSENT"`);按判别字段选中分支后按该分支核对;判别字段取值不属任何分支即红 |
共用定义:
```
Evidence = {kind: "COMMAND", command: str, cwd: str, exit_code: int, output_sha256: str}
         | {kind: "FILE", path: str, sha256: str, selector: str}
Common   = claim_id: str, snapshot: str, evidence: [Evidence]      ← 每个 claim 的顶层记录都含这三项
CodeState = {state: "ABSENT"} | {state: "VALUE", value: str}
MarkerState = {state: str, sha256?: str}                          ← state 取值由 predicate 约束
```
下文各 claim 的 `output_schema` 写作 `{Common, …}`,表示顶层封闭记录由 Common 三项与所列字段组成。

**求值语义(v1.1)**:
- **缺失(MISSING)**:路径不存在即 MISSING。只有标 `?` 的可选字段可以合法缺失;必填字段缺失由 `schema_closed()` 判红。
- **除 `present` 外,任何节点在其参数路径为 MISSING 时都是【求值错误】**;求值错误不是 `false`,**不被 `not`、`any`、`implies` 吸收,
  直接使整个 claim 判红**,并在 verifier 输出中记录出错节点与路径。
- **短路,自左向右**:`all` 遇第一个 `false` 即停;`any` 遇第一个 `true` 即停;`implies(a,b)` 在 `a` 为 `false` 时不求值 `b`;
  未被求值的子节点不会产生求值错误。**因此对可选字段的比较,必须先用一个分支条件把"该字段应当存在"的情形筛出来**(见 `OBS-1.item3-predicate` 第 5 条)。
- `forall` 对空数组为 `true`,`exists` 对空数组为 `false`;需要非空时另写 `nonempty`。

**运行上下文 `$ctx`**(由 verifier 注入,属类二快照标识):`tree`(本次运行固定的 git tree hash)、`head`(commit SHA)、`run_id`。

**canonical serialization**:UTF-8、对象键按字典序、无多余空白、数组保持原序;hash = 其 SHA-256。
**renderer**:把每个节点渲染为一行中文,产物进 generated block,带 `renderer_version`;规则见冻结稿 §8-2。
**producer 输出纪律**:只输出原始事实;**输出中不得出现 pass/fail、ok、verdict 一类判定字段**;
每个 claim 的 `output_schema` 是封闭的,**出现未声明字段即红**。

---

## §2 所有 claim 共用的条件(每条 predicate 都以这四项开头)

- **G1**:`eq(/claim_id, <本 claim_id>)`;
- **G2**:`eq_path(/snapshot, $ctx.tree)` —— 产出必须来自本次固定的 tree,旧快照即红;
- **G3**:`nonempty(/evidence)`,且 `forall(/evidence/*, any[ all[present(@/command), present(@/exit_code), present(@/output_sha256)],
  all[present(@/path), present(@/sha256), present(@/selector)] ])` —— 每条证据要么是"命令 + 退出码 + 输出 hash",要么是"文件 + hash + 机械定位";
- **G4**:`schema_closed()` —— 输出字段集合恰为本 claim `output_schema` 声明的字段集合(v1.1 改为显式节点)。

下文各 claim 只列 G1–G4 之外的条件。

---

## §3 各 claim 的判定条件

### B-1 · `OBS-1.item1-basis` —— 项 1 的依据:step-0 §6.2 清单
- **subject**:step-0 v2.1-FROZEN §6.2 的 shim 删除清单作为台账第一段的来源;**quantifier**:∀
- **output_schema**:`{Common, source: {path: str, sha256: str, heading: str}, entries: [{entry_id: str, text_sha256: str, kind: str, mapped_ledger_keys: [str]}]}`
- **条件**:
  1. `eq(/source/path, "docs/clang-fix-campaign/p49-step0-design-v2.1-FROZEN.md")`;
  2. `matches(/source/heading, "^### 6\\.2 ")`;
  3. `nonempty(/entries)`;
  4. `forall(/entries/*, in(@/kind, ["REEXPORT_SURFACE","SYMBOL_GROUP","PACKAGE_REEXPORT","NEGATIVE"]))` ——
     `NEGATIVE` 指"不含某模块 / 不留 shim"这类否定条目;
  5. `forall(/entries/*, implies(ne(@/kind,"NEGATIVE"), nonempty(@/mapped_ledger_keys)))` —— 每个肯定条目都落到至少一个台账 key;
  6. `subset(/entries/*/mapped_ledger_keys/*, $file(E/ledger_inventory.json,/seg1/*/ledger_key))` —— 映射到的 key 都真实进了第一段台账。

### B-1 · `OBS-1.item2-scope` —— 项 2 的范围:skill-4 私有件义务
- **subject**:skill-4 v1.12.1-FROZEN 登记的测试私有件义务与 `private_consumption.json` 的对应;**quantifier**:∀
- **output_schema**:`{Common, obligation_source: {path: str, sha256: str, heading: str}, obligations: [{obligation_id: str, text_sha256: str}],
  consumption_ref: {path: str, sha256: str}, mapping: [{obligation_id: str, consumption_ids: [str], status: str}], unmapped_consumption_ids: [str]}`
- **条件**:
  1. `eq(/obligation_source/path, "docs/clang-fix-campaign/p49-skill4-build-verify-design-v1.12.1-FROZEN.md")`;
  2. `nonempty(/obligations)`;
  3. `set_eq(/mapping/*/obligation_id, /obligations/*/obligation_id)` —— 每条义务都有去向;
  4. `forall(/mapping/*, in(@/status, ["HAS_CONSUMERS","NO_CURRENT_CONSUMER"]))`;
  5. `forall(/mapping/*, implies(eq(@/status,"HAS_CONSUMERS"), nonempty(@/consumption_ids)))`;
  6. `forall(/mapping/*, implies(eq(@/status,"NO_CURRENT_CONSUMER"), count(@/consumption_ids) == 0))`;
  7. `eq(/consumption_ref/path, "docs/clang-fix-campaign/dev_memory/stage14_p49_terminal_batch/a0-evidence/private_consumption.json")`;
  8. 扫描发现而不在任何义务下的消费条目必须显式列出(不得丢弃):
     `set_eq($file(E/private_consumption.json,/entries/*/id), union(/mapping/*/consumption_ids/*, /unmapped_consumption_ids/*))`。

### B-1 · `OBS-1.item3-predicate` —— 项 3 的现状:源目录安全检查
- **subject**:`ANCHOR-3` 的现状判定式与四个相邻输入下的现状行为;**quantifier**:∀
- **output_schema**:`{Common, anchor: {file: str, function: str, selector: str, matched_count: int, expr_kind: str, operand_calls: [str], same_receiver: bool, span_sha256: str},
  scenarios: [{scenario_id: str, exception_type?: str, exception_code: CodeState, destination_after: str}]}`
  —— `exception_type` 仅在该场景抛出异常时出现;未抛异常时缺省,且 `exception_code` 为 `{state: "ABSENT"}`。
- **条件**:
  1. `eq(/anchor/file, "tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py")`;
  2. `eq(/anchor/matched_count, 1)` —— selector 恰命中一处,零处或多处即红;
  3. `eq(/anchor/expr_kind, "BoolOp.And")`、`subset(["exists","is_symlink"], /anchor/operand_calls)`、`eq(/anchor/same_receiver, true)`;
  4. `set_eq(/scenarios/*/scenario_id, ["DANGLING_SYMLINK","LIVE_SYMLINK_TO_DIR","REAL_DIR","ABSENT"])`;
  5. 现状前提(冻结稿 §3 与 skill-5 §3.2 的设计前提):
     `forall(/scenarios/*, implies(eq(@/scenario_id,"LIVE_SYMLINK_TO_DIR"), all[eq(@/exception_type,"GerritError"), eq(@/exception_code/state,"VALUE"), eq(@/exception_code/value,"SOURCE_DIR_UNSAFE")]))`
     (v1.2 补 `eq(@/exception_code/state,"VALUE")`,与下方旁注一致);
     `forall(/scenarios/*, implies(eq(@/scenario_id,"DANGLING_SYMLINK"), all[present(@/exception_type), in(@/exception_code/state, ["ABSENT","VALUE"]),
     any[eq(@/exception_code/state,"ABSENT"), all[eq(@/exception_code/state,"VALUE"), ne(@/exception_code/value,"SOURCE_DIR_UNSAFE")]]]))`
     —— 悬空链接现状**不**进入 `SOURCE_DIR_UNSAFE`(无 code,或有 code 但不是它);若已进入,项 3 的前提不成立,停止报告。
     (v1.1:按 `state` 显式分支;`state` 为 `ABSENT` 时 `value` 不被求值,为 `VALUE` 时 `value` 缺失即求值错误、判红);
     同理,上一条中 `LIVE_SYMLINK_TO_DIR` 的 `exception_code/value` 为必达字段:`state` 不为 `VALUE` 或 `value` 缺失均判红;
  6. `forall(/scenarios/*, present(@/destination_after))` —— 每个场景都记录执行后目标路径状态。

### B-1 · `OBS-1.item4-anchors` —— 项 4 的输入:skill-5 §3.2 映射表与六个调用面
- **subject**:skill-5 v1.3.2-FROZEN §3.2 映射表的行与顺序、六个调用面的定位、以及三处残留格的现状观测;**quantifier**:∀
- **output_schema**:`{Common, table_source: {path: str, sha256: str, heading: str},
  rows: [{surface: str, timeout_cell: str, interrupt_cell: str, residual_cell: str}],
  call_sites: [{anchor_no: int, file: str, function: str, selector: str, matched_count: int}],
  residual_obs: [{anchor_no: int, injected_at: str, destination_unchanged?: bool, workdir_marker?: MarkerState, protected_marker?: MarkerState, exclude_completed?: bool}]}`
  —— `rows` 各字段是表格单元格原文;`residual_obs` 中 fetch 两面(1、2)记 `destination_unchanged`,workspace 面(6)记两个 marker 与 `exclude_completed`,
  不适用的字段缺省;某面**应当**有的字段由第 8 条的 predicate 要求(缺失即求值错误)。
- **条件**:
  1. `eq(/table_source/path, "docs/clang-fix-campaign/p49-skill5-gerrit-submit-design-v1.3.2-FROZEN.md")`、`matches(/table_source/heading, "^### 3\\.2 ")`;
  2. `count(/rows) == 6`;
  3. 行顺序与调用面(按表中顺序):`matches(/rows/0/surface,"query 阶段")`、`matches(/rows/1/surface,"git 阶段")`、
     `matches(/rows/2/surface,"本 skill .*_run_git")`、`matches(/rows/3/surface,"ls-remote")`、
     `matches(/rows/4/surface,"shared/workspace .*_run_git")`、`matches(/rows/5/surface,"_exclude_private_files")`;
  4. 超时格:`matches(/rows/0/timeout_cell,"FETCH_TIMEOUT")`、`matches(/rows/1/timeout_cell,"FETCH_TIMEOUT")`、
     `matches(/rows/2/timeout_cell,"GerritSubmitError.*GIT_TIMEOUT")`、`matches(/rows/3/timeout_cell,"target_head_unknown:timeout")`、
     `matches(/rows/4/timeout_cell,"GIT_TIMEOUT:")`、`matches(/rows/5/timeout_cell,"GIT_TIMEOUT")`;
  5. `forall(/rows/*, matches(@/interrupt_cell,"^传播$"))`;
  6. 残留格:`matches(/rows/0/residual_cell,"destination 不动")`、`matches(/rows/1/residual_cell,"阶段残留")`、
     `matches(/rows/5/residual_cell,"protected marker 尚未写入")` —— 第三条即冻结稿 §5 要求"A₀ 须核对该残留格";
  7. `count(/call_sites) == 6`、`seq_eq(/call_sites/*/anchor_no, [1,2,3,4,5,6])`、`forall(/call_sites/*, eq(@/matched_count, 1))`;
  8. 现状残留观测(在现状代码上以注入故障取得,不依赖尚未实现的 timeout 参数):
     `forall(/residual_obs/*, implies(eq(@/anchor_no,1), eq(@/destination_unchanged, true)))` —— query 阶段失败时 destination 不动;
     `exists(/residual_obs/*, eq(@/anchor_no,2))` —— git 阶段至少一个注入点有观测记录;
     `forall(/residual_obs/*, implies(eq(@/anchor_no,6), all[eq(@/workdir_marker/state,"PRESENT"), eq(@/protected_marker/state,"ABSENT"), eq(@/exclude_completed,false)]))`;
     `set_eq(/residual_obs/*/anchor_no, [1,2,6])`。
  任一不成立 → 映射表与现状代码不一致,**按冻结稿 §5 阻塞、退回设计方**。

### B-1 · `OBS-1.item5-order` —— 项 5 的现状:protected marker 写入序与读取方
- **subject**:`mark_worktree_protected` 的调用顺序、两个中断时点的失败态、既有读取方对其的结果;**quantifier**:∀
- **output_schema**:`{Common, call_order: [str], scenarios: [{scenario_id: str, protected_marker: MarkerState,
  readers: [{reader: str, result_kind: str, result_value_or_type: str}]}]}`
  —— `result_value_or_type`:返回时为返回值的 `repr`,抛异常时为异常类型全名。
- **条件**:
  1. `seq_eq(/call_order, ["_verify_cleanup_handle","_exclude_private_files","write_protected_marker"])`
     —— `write_protected_marker` 是步骤标签,指 `mark_worktree_protected` 内对 `PROTECTED_FILENAME` 的写入调用;`call_order` 只记录这三个步骤的实际发生次序;
  2. `set_eq(/scenarios/*/scenario_id, ["EXCLUDE_INTERRUPTED","MARKER_WRITE_INTERRUPTED"])`;
  3. `forall(/scenarios/*, implies(eq(@/scenario_id,"EXCLUDE_INTERRUPTED"), eq(@/protected_marker/state,"ABSENT")))`;
  4. `forall(/scenarios/*, implies(eq(@/scenario_id,"MARKER_WRITE_INTERRUPTED"), in(@/protected_marker/state, ["ABSENT","PARTIAL"])))`;
  5. `forall(/scenarios/*, implies(eq(@/protected_marker/state,"PARTIAL"), present(@/protected_marker/sha256)))`;
  6. `forall(/scenarios/*, all[nonempty(@/readers), exists(@/readers/*, eq(@/reader,"is_protected"))])`;
  7. 读取方全集来自独立枚举,不是人工挑选:`forall(/scenarios/*, set_eq(@/readers/*/reader, $file(E/B-1-anchors.json,/protected_marker_readers/*)))`
     —— 该枚举 = 仓库内除写入方 `mark_worktree_protected` 外、引用 `PROTECTED_FILENAME` 的全部函数(由名字命中兜底同一引擎产出);
  8. `forall(/scenarios/*/readers/*, in(@/result_kind, ["RETURN","EXCEPTION"]))`。
  读取方的**具体结果不设期望值** —— 它是现状,供 §6 的 `NO_DIFF` 比对使用;本 claim 只要求它被完整记录。

### B-2 · `OBS-2.seg1-staleness` —— 第一段各条目的时效
- **subject**:step-0 §6.2 每个条目在当前树上是否仍然成立;**quantifier**:∀
- **output_schema**:`{Common, entries: [{entry_id: str, staleness: str, current_fact: {exists: bool, shape: str}}]}`
- **条件**:
  1. `set_eq(/entries/*/entry_id, $ref(OBS-1.item1-basis,/entries/*/entry_id))` —— 与 item1-basis 逐条对应;
  2. `forall(/entries/*, in(@/staleness, ["CURRENT","STALE"]))` —— 不允许"未知";
  3. `forall(/entries/*, all[present(@/current_fact/exists), present(@/current_fact/shape)])` —— 否定条目同样要对当前树取证(冻结不得固化过期否定项)。

### B-2 · `OBS-2.seg2-form` —— 第二段各批 closeout 的贡献形态
- **subject**:step-0 与 skill-1…6 共七份 closeout 中 shim 相关条目的形态与可用性;**quantifier**:∀
- **output_schema**:`{Common, sources: [{batch: str, path: str, sha256: str, form: str, usable_as_coverage: bool, entry_count: int}]}`
- **条件**:
  1. `set_eq(/sources/*/batch, ["step-0","skill-1","skill-2","skill-3","skill-4","skill-5","skill-6"])`;
  2. `forall(/sources/*, matches(@/path, "^docs/clang-fix-campaign/review/p49-(step0|skill[1-6])-closeout\\.md$"))`;
  3. `forall(/sources/*, in(@/form, ["STRUCTURED_TABLE","PROSE","NONE"]))`;
  4. `forall(/sources/*, implies(eq(@/usable_as_coverage, true), eq(@/form, "STRUCTURED_TABLE")))` —— 只有结构化表格可作覆盖面依据,散文不可;
  5. `forall(/sources/*, implies(eq(@/form,"NONE"), eq(@/entry_count, 0)))`。

### B-3 · `OBS-3.commit-order` —— skill-3 批次的提交次序
- **subject**:skill-3 批次登记的抽取提交、测试提交,以及使旧址模块变为 shim 的提交;**quantifier**:∀
- **output_schema**:`{Common, batch: str, registered_extraction_sha: {value: str, source_path: str, source_sha256: str}, test_commit_shas: [str],
  shim_creations: [{old_path: str, creating_sha: str, pre_def_count: int, post_def_count: int}], relations: [{a: str, b: str, relation: str}]}`
- **条件**:
  1. `eq(/batch, "skill-3")`、`eq(/registered_extraction_sha/source_path, "docs/clang-fix-campaign/review/p49-skill3-closeout.md")`、`matches(/registered_extraction_sha/value, "^[0-9a-f]{40}$")`;
  2. `nonempty(/shim_creations)`、`forall(/shim_creations/*, all[matches(@/creating_sha,"^[0-9a-f]{40}$"), not(eq(@/pre_def_count, 0)), eq(@/post_def_count, 0)])`
     —— 即"由有顶层 def/class 变为零 def/class"的判据逐条成立;
  3. `forall(/relations/*, in(@/relation, ["ANCESTOR","DESCENDANT","SAME","UNRELATED"]))` —— 次序只能由祖先关系给出,不得用提交序号或时间。

### B-3 · `OBS-3.transition-map` —— 现存旧址 shim 的逐模块溯源
- **subject**:当前树中每个旧址整模块 shim 由哪一批、哪一个提交创建;**quantifier**:∀
- **output_schema**:`{Common, modules: [{path: str, creating_batch: str, creating_sha?: str, pre_def_count: int, post_def_count: int, uncovered_class: str}]}`
  —— `creating_sha` 仅在 `creating_batch` 不为 `UNREGISTERED` 时出现;是否必须出现由第 3 条要求。
- **条件**:
  1. `forall(/modules/*, in(@/creating_batch, ["step-0","skill-1","skill-2","skill-3","skill-4","skill-5","skill-6","UNREGISTERED"]))`;
  2. `forall(/modules/*, implies(ne(@/creating_batch,"UNREGISTERED"), all[not(eq(@/pre_def_count,0)), eq(@/post_def_count,0)]))`;
  3. `forall(/modules/*, implies(ne(@/creating_batch,"UNREGISTERED"), in_path(@/creating_sha, $file(E/B-2-sources.json,/registered_extraction_shas/*))))`
     —— 非 `UNREGISTERED` 的创建提交必须是各批登记的实际抽取提交;
  4. `forall(/modules/*, in(@/uncovered_class, ["NONE","a","b","b'","c","d","e","f","g","h"]))` —— 对应冻结稿 §1.1b 不覆盖九类;
  5. `set_eq(/modules/*/path, $file(E/raw_findings.json,/module_granularity_old_location_paths/*))` —— 与扫描发现的旧址整模块候选逐一对应,两侧都不许多、不许少。

### B-4 · `OBS-4.owner-attribution` —— 被导入符号的 canonical owner
- **subject**:每个 A=是 的 binding 候选(`#REEXPORT`/`#INLINE`)所导入符号的定义位置;**quantifier**:∀
- **output_schema**:`{Common, records: [{candidate_id: str, symbol: str, owner_module: str, definition_sites: [{path: str, selector: str}], owner_outside_host?: bool}]}`
  —— `owner_outside_host` 仅在定义位置唯一时出现;是否必须出现由第 3 条要求。
- **条件**:
  1. `set_eq(/records/*/candidate_id, $file(E/B-15-disposition_evidence.json,/a_true_binding_candidates/*))`;
  2. `forall(/records/*, count(@/definition_sites) >= 1)`;
  3. `forall(/records/*, implies(count(@/definition_sites) == 1, present(@/owner_outside_host)))`;
  4. 多处定义不得选一个了事:`forall(/records/*, implies(not(count(@/definition_sites) == 1), eq(@/owner_module, "AMBIGUOUS")))`。

### B-5 · `OBS-5.entry-consumers` —— 已文档化入口与其消费关系
- **subject**:仓库全部已文档化入口(打包入口、包的 `__main__`、各 SKILL.md 中写明的命令)及其 smoke 结果;**quantifier**:∀
- **output_schema**:`{Common, entries: [{entry_id: str, kind: str, target: str, documented_in: [str], consumers: [str], smoke_command: str, smoke_exit: int}]}`
- **条件**:
  1. `forall(/entries/*, in(@/kind, ["CONSOLE_SCRIPT","PACKAGE_MAIN","SKILL_MD_COMMAND"]))`;
  2. `set_eq(/entries/*/entry_id, $file(E/B-5-entries.json,/independent_enumeration/*))` —— 入口全集来自独立枚举(打包描述 ∪ tracked `__main__.py` ∪ SKILL.md 命令),不是人工挑选;
  3. `forall(/entries/*, all[nonempty(@/documented_in), present(@/smoke_command), eq(@/smoke_exit, 0)])` —— 基线上每个入口 smoke 必须通过;
  4. `forall(/entries/*, not(matches(@/smoke_command, "(^|\\s)tests/")))` —— smoke 不得依赖 `tests/` 下的文件(冻结稿 §1.1a:冒烟入口须独立于被删测试集)。

### B-6 · `OBS-6.proxy-count` —— 粒度④ 候选数
- **subject**:当前树上的 `PROXY_CALLABLE` 候选;**quantifier**:计数
- **output_schema**:`{Common, count: int, candidate_ids: [str], by_form: map<str, int>}` —— `by_form` 的键为形态名、值为该形态的候选数;键的取值由第 3 条约束。
- **条件**:
  1. `count(/candidate_ids) == $value(/count)`;
  2. `set_eq(/candidate_ids, $file(E/raw_findings.json,/proxy_candidate_ids/*))`;
  3. `subset(keys(/by_form), ["DIRECT","PARTIAL_FORWARD","METHOD_LEVEL","DECORATOR_GENERATED","HOST_SIDE_EFFECT"])`、`sum_eq(/by_form, /count)`。

### B-6 · `OBS-6.intra-package-shim` —— 同顶层包内的兼容壳
- **subject**:宿主与委托目标位于同一顶层包的兼容壳;**quantifier**:∃/¬∃ 如实记录
- **output_schema**:`{Common, records: [{candidate_id: str, host_top_package: str, target_top_package: str}]}`
- **条件**:
  1. `forall(/records/*, eq_path(@/host_top_package, @/target_top_package))`;
  2. `subset(/records/*/candidate_id, $file(E/raw_findings.json,/all_candidate_ids/*))` —— 只能是扫描实际发现的候选;
  3. `set_eq(/records/*/candidate_id, $file(E/raw_findings.json,/same_top_package_candidate_ids/*))`
     —— 报告不得挑选:扫描发现的全部"宿主与委托目标同属一个顶层包"的候选都要列出,一个不少(v1.1)。
     `same_top_package_candidate_ids` 由扫描产物按每个候选的宿主模块与委托目标模块字段机械导出,不由本 claim 的 producer 自报。
  本 claim 不设"必须为空 / 必须非空"。**"发现面没有用跨顶层包条件排除同包兼容壳"这一覆盖义务由 §4 的具名正控制 `CTRL-INTRA-PKG-PROXY` 承担**,
  不由本 claim 承担 —— claim 只能证明"报告了扫描发现的全部",证明不了"扫描没漏";后者只能靠已知答案的构造样本。

### B-7 · `OBS-7.falsification-samples` —— §2 准入证伪样本
- **subject**:三份前批 ledger 中登记的现存漏检样本,以及消费者引擎对它们的命中;**quantifier**:∀
- **output_schema**:`{Common, sources: [{path: str, sha256: str}], samples: [{sample_id: str, form: str, file: str, selector: str}], hits: [{sample_id: str, consumer_edge_id: str}]}`
- **条件**:
  1. `nonempty(/samples)` —— 样本集为空即红(冻结稿 §2:样本集为空视为未完成,阻塞 A₀);
  2. `set_eq(/hits/*/sample_id, /samples/*/sample_id)` —— 每个样本都被命中,一个都不许漏;
  3. `forall(/samples/*, in(@/form, ["C1","C4","C5a","C2a","C2b","C3","C6a","C6b","C5b","C5c","C5d","C5e","C6c","C6d","C8a","C8b","C7a","C7b","C7c","C7d"]))`
     —— 形态取值即冻结稿 §1.1 原子形态表;
  4. `nonempty(/sources)`。

### B-7 · `OBS-7.class-c-projection` —— §2 (c) 类投影
- **subject**:按 §2 三分规则落入 (c) 类(不可判定)的测试;**quantifier**:计数
- **output_schema**:`{Common, count: int, test_ids: [str], reasons: map<str, str>}` —— `reasons` 的键为 test_id、值为原因;键集与取值由第 3、4 条约束。
- **条件**:
  1. `count(/test_ids) == $value(/count)`;
  2. `set_eq(/test_ids, $file(E/private_consumption.json,/class_c_test_ids/*))`;
  3. `set_eq(keys(/reasons), /test_ids)` —— 每个 test_id 恰有一条原因;
  4. `forall(values(/reasons), in(@, ["GRAPH_NOT_CLOSED","SEMANTICS_AMBIGUOUS","DYNAMIC_CALL_UNRESOLVED"]))` —— 即冻结稿 §2 (c) 的三种来源。

---

## §4 构造式证伪(随 predicate 一起交付,计入 B-11 `G-SEAL-15`)

冻结稿 §8-2 已规定 `ASSERTION` 四条(翻转 predicate / 交换 subject / 旧 snapshot / round-trip 不一致)、型别三条、豁免上界四条。
**在此基础上,每个 claim 至少再配一条"改坏一个事实即红"的控制**:把该 claim producer 输出中与上文某一条件直接相关的一个值改掉
(例如 `OBS-1.item4-anchors` 删掉第 6 行的"protected marker 尚未写入"、`OBS-7.falsification-samples` 删掉一个命中),verifier 必须转红;
控制条目进 `control_catalog.json`,与其它控制分开计数。

**v1.1 另加三组控制**:
- **求值语义控制**(verifier 单元测试):①必填字段缺失 → `schema_closed()` 红;②多出未声明字段 → 红;
  ③对可选字段缺失的比较位于未被短路的分支 → 求值错误、整条红(不得被 `not`/`any`/`implies` 吸收);
  ④同一可选字段缺失、但所在分支被短路 → 不报错;⑤`forall` 空数组为真、`exists` 空数组为假。
- **`OBS-1.item3-predicate` 第 5 条的四个输入**:悬空场景 `state=ABSENT` → 绿;`state=VALUE, value="SOURCE_DIR_UNSAFE"` → 红;
  `state=VALUE` 而 `value` 缺失 → 红;`state=VALUE, value` 为其它码 → 绿。
  **(v1.2 补)LIVE 场景**:`state=ABSENT` 且带 `value="SOURCE_DIR_UNSAFE"`(Codex 报告的反例)→ 红(`schema_closed()` 拒绝:`ABSENT` 分支不含 `value`);
  `state=VALUE, value="SOURCE_DIR_UNSAFE", exception_type="GerritError"` → 绿;`state=ABSENT` 不带 `value` → 红(第 5 条)。
- **schema 记法控制(v1.2)**:①`Evidence` 两种变体各一例 → 绿;`kind` 取第三个值 → 红;`COMMAND` 变体缺 `exit_code` → 红;
  `FILE` 变体多出 `command` → 红;②`map<str, int>` 值为字符串 → 红,空映射 → 绿(非空要求只由 predicate 施加);
  ③可选字段缺省 → 绿,可选字段出现但类型错 → 红;④嵌套记录多出字段 → 红。
- **`CTRL-INTRA-PKG-PROXY`(归 B-11 `G-DETECTOR`,是真实扫描器的正控制,不是 verifier 测试)**:在隔离 fixture 中构造一个
  宿主与委托目标同属一个顶层包的纯委托 callable,扫描器必须产出对应 `PROXY_CALLABLE` 候选,且该候选出现在 `same_top_package_candidate_ids` 中;
  near-miss:同包但函数体含委托之外的逻辑 → 不产出纯委托候选(按冻结稿粒度④落 `SCAN_UNRESOLVED` 或不成候选)。
