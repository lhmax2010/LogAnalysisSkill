# Stage18 P4 derive_commit

日期:2026-10-09。状态:**CLOSED**,PM核对通过,FatTank批准签收。
§1-7保留首次实现及其历史验收;评审裁决与证据见§8-9,最终签收见§10。

## 1. 权威、范围与计划

- `../../design.md` v1.5.19-FROZEN,§4.2 derive_commit、§3.4确定性与§7 Phase 4。
- P2已CLOSED;接收stage16移交的最终message验收,使用已登记的真实hook。
- 只新增`ci_triage/derive_commit.py`、测试与证据;不更改既有API、状态库或design.md。
- 计划:真实Git输入检验 → commit-tree派生 → tree/身份/时间/message与现场不变测试
  → 真实hook移交验收 → 全量及设计门禁对比 → 独立提交/CI → READY_FOR_REVIEW。
- 主arch副本的选择、A12字段首写/复用与DERIVE事件写入由后续编排完成,
  本函数只消费传入值,不选择record、不写state DB、不更新refs、不push。

## 2. 实现细节(轻量流程)

- 身份用Git惯例`Name <email>`分解,拒绝缺失/多行;tree/parent须完整小写对象ID,
  不接受revision表达式或命令选项;日期必须显式非空,具体格式交Git校验。
- 调用`git commit-tree`并用`git rev-parse <sha>^{tree}`验证tree等式;
  等式不成立抛RuntimeError,不依赖可被`python -O`关闭的assert。
- 清除继承GIT_*路由/配置注入,显式设置作者、提交者与日期;禁自动签名、
  replace对象与lazy fetch,固定消息编码UTF-8。不会checkout/提交index/运行commit-msg hook。
- 传入message经stdin原样交给Git;消息组装属于调用方(设计§3.4固定顺序与P5)。
  本阶段不新建formatter API或杜撰溯源trailer字段清单;快照锁定已冻结的
  `Fix build error for clang compiler: <brief>`前缀、正文与Change-Id trailer。
- 新模块Git失败保持CalledProcessError/启动异常,参数非法为ValueError,
  不借用未冻结的新CLI错误码。既有模块和接口行为不变。

## 3. DoD与证据

| DoD | 用例与结论 |
|---|---|
| 派生tree等式 | `test_tree_parent_identities_message_snapshot_and_worktree_index_unchanged`:PASS,输入tree特意不同于现场index;`test_tree_postcondition_is_enforced`:反向伪造结果必拒 |
| parent/作者/提交者/两日期 | 上述正例逐项核对Git对象;`test_each_derivation_input_participates_in_identity`七参数例证明每一输入参与结果,同输入重复SHA相等 |
| 消息模板与trailer快照 | 主正例断言cat-file原始消息字节;`test_hook_identity_goes_to_final_trailer_without_auxiliary_line`断言Git解析后的唯一trailer及无辅助行 |
| 不checkout、不碰工作区/index | 主正例含已暂存但未验证、未暂存内容、未跟踪文件和symlink,前后比较内容/权限/mtime/index原字节/HEAD/refs;失败路径同样不变 |
| 真实hook移交(P2→P4) | `evidence/run_real_hook_derive.py`真实hook+derive实跑:tree相等、唯一Change-Id trailer、无X-Campaign-Submission-Key、现场不变、零网络调用 |
| 全量与质量门禁 | 基线P3 `0910f34`1440/1 → 本期1457/1,新增17例,原1441 nodeid无缺失/结果变化;类型/lint/import及90设计门禁无新增失败 |

用例文件:`tests/unit/test_derive_commit.py`。基线与候选分别在干净工作树
`/tmp/p4-baseline-0910f34`、`/tmp/p4-derive-0910f34`;
后者只增加本阶段模块/测试/取证脚本,不带主树杂项。

```sh
R=docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py
E=docs/clang-fix-campaign/dev_memory/stage18_p4_derive_commit/evidence
.venv/bin/python "$R" /tmp/p4-baseline-0910f34 "$E/baseline"
.venv/bin/python "$R" /tmp/p4-derive-0910f34 "$E/current"
.venv/bin/python -m pytest tests/unit/test_derive_commit.py -v
env -u PYTHONPATH -u MYPYPATH strace -f -e trace=network -o "$E/network.trace" .venv/bin/python "$E/run_real_hook_derive.py"
```

完整argv、cwd、路径环境、exit和原文摘要在两树`commands.json`,各日志保存stdout/stderr。
实际摘录(各命令exit0):

```text
============================== 17 passed in 0.64s ==============================
======================= 1457 passed, 1 skipped in 32.75s =======================
Success: no issues found in 106 source files
All checks passed!
Contracts: 6 kept, 0 broken.
SUMMARY | 198 SYMBOL OK | 4 MODULE-SCOPE OK (48 SYMBOLS COVERED) | 0 MISMATCH | 0 INCOMPLETE
SUMMARY | 198 SYMBOL OK | 4 MODULE-SCOPE OK | 0 MISSING_FROM_INVENTORY | 0 MISSING_FROM_BODY | 0 OWNER_MISMATCH | 0 PARSE_ERROR
```

`comparison.json`:missing_nodeids/changed_outcomes/exit_changes均为空。
94条命令包含4项全仓验收与90项既有门禁/控制;历史问题仍三条,
design-doc-controls=1、duplicate-spec-root-mismatch=0、twin-both-binary-key=1,
与基线逐条相同。不修改历史checker或期望,原因见P2收口遗留表。
comparison.json另钉定本轮三个代码/测试/取证文件摘要。

## 4. P2移交真实验收

直接读取stage16登记的`real-hook-config.json`,实跑前核对文件摘要:
`3c7e9b5fbe0b7ed945abd74248913c912ee0464abb416c18278bc5811dbb6f50`。
调用真实`generate_change_id_via_hook`,不是替身hook;在独立临时业务仓库派生,
没有远端/网络操作。生成hook前后业务对象库文件集合不变,随后derive仅写新commit对象。

```text
hook_sha256=3c7e9b5fbe0b7ed945abd74248913c912ee0464abb416c18278bc5811dbb6f50
Change-Id: I8e91478cf9cd759b9b15412bb1b9dcb789ed8095
commit=394865306a0938d64042fffbfdb0c055e79bc928; input_tree=117b8ac7b07e6b56f3191d5f49ff82fc74234b4c; actual_tree=117b8ac7b07e6b56f3191d5f49ff82fc74234b4c
change_id_trailers=1; auxiliary_lines=0; workspace/index/HEAD unchanged; exit=0
network_syscalls=0
```

原始取证:`real-hook-derive.json`含message输入/最终原文/trailer/输入与输出tree/调用列表;
`real-hook-derive.log`为stdout,`smoke-command.json`为命令与exit;
`network.trace`/`network-check.json`证明跟踪子进程的网络系统调用为0。
本次SHA/Change-Id仅为实跑锚,真实hook结果可随初始commit时间变化,不作固定向量。
P2移交P4的义务已完成;P5 sandbox与P5R review端到端删缓存拒绝仍归原阶段。

## 5. 初次失败与修正记录

首次定向为1 failed/16 passed:测试在`before`快照之后执行`git write-tree`,
该准备命令自身更新index的cache-tree扩展。未修改derive行为来迁就测试,
仅将快照放到准备命令之后;`index-observation.json`独立复现实证:
`test_write_tree_changed_index=true`, `derive_changed_index=false`。
失败原文与exit1保留于`initial-targeted.log`/`initial-checks.json`。
修正diff:两相邻行由`before = _snapshot(path); assert _git(..., "write-tree") != tree`
换为`assert _git(..., "write-tree") != tree; before = _snapshot(path)`。
另首次ruff对两个subprocess调用报UP022,改为等价`capture_output=True`,
原文保留于`initial-ruff.log`;重跑结果见第3节,无遗留失败。

## 6. 收口与停点

收口:`../../review/p4-derive-commit-closeout.md`,状态仅READY_FOR_REVIEW。
没有待裁决的新行为/安全边界缺口;第2节为非行为补足的轻量留痕。
本阶段不推进P5/P5R,不宣称它们的端到端验证已完成。
前序P3远端CI success,run 37751385388,完整metadata在`evidence/p3-remote-ci.json`。
P4独立提交与其远端CI由Git/GitHub外部锚定,推送后实查结果并给出run链接,
文件内不自记提交SHA,不把P3 CI替代P4验收。

## 7. 远端日期断言兼容性修正

P4实现提交`9a65e0d`的首次远端CI(run 37752238528)结果:
`1 failed, 1456 passed, 1 skipped in 48.30s`,Tests exit1;Lint/Type check通过。
失败仅在本期新增测试的日期显示断言:
`assert '2026-10-08T00:00:00Z' == '2026-10-08T00:00:00+00:00'`。
远端Git为2.55.0,本机为2.43.0。原始日志与metadata保留于
`evidence/initial-remote-ci.log`、`evidence/initial-remote-ci.json`。

根因是测试把Git的ISO显示形式当作存储契约;两种显示代表相同UTC时间。
修正只触及新增测试:从`cat-file commit`原始头逐字核对
`author/committer <identity> <epoch seconds> +0000`,epoch由显式输入日期计算。
仍验证身份、时间戳和时区,没有归一化生产消息、放宽tree或现场不变断言。
生产`derive_commit.py`零改动,按轻量流程登记,不修改design.md。

修正版本在干净工作树`/tmp/p4-ci-date-9a65e0d`重跑同一94命令集合,
完整命令/exit/原始输出位于`evidence/ci-date/`。
首次本机证据`current/`原样保留;补丁独立提交,不改写已经推送的P4提交。

```sh
.venv/bin/python docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py /tmp/p4-ci-date-9a65e0d docs/clang-fix-campaign/dev_memory/stage18_p4_derive_commit/evidence/ci-date
```

```text
======================= 1457 passed, 1 skipped in 32.92s =======================
Success: no issues found in 106 source files
All checks passed!
Contracts: 6 kept, 0 broken.
completed=94 unexpected=3
```

四项主验收exit0;三条unexpected仍为原有checker遗留。
`ci-date-comparison.json`:94条exit无变化,missing_nodeids/changed_outcomes为空,
较P3基线仅增加原定17例,两个代码/测试文件摘要与实测工作树一致。

## 8. 评审修复与PM轻量裁决(2026-10-09)

单家评审结论P4需修改;以下按本轮PM明确裁决执行,不改design.md。

| 发现/裁决 | 处置与验收 |
|---|---|
| Git接受相对日期/无时区日期,结果可能依赖环境 | `derive_commit.COMMIT_DATE_RE`唯一正则,严格fullmatch指定ISO 8601带时区形态;derive失败抛ValueError且零subprocess;campaign_state._validate_derive复用同一正则,拒绝为PayloadSchemaError |
| 继承TZ及向上查找仓库的边界 | 两次Git调用均显式TZ=UTC、GIT_CEILING_DIRECTORIES=worktree.resolve().parent;inner普通子目录不能写入outer对象库,check=True抛CalledProcessError |
| 真实hook证据只在独立脚本 | 断言主体迁写为`tests/integration/test_derive_commit_real_hook.py::test_registered_real_hook_then_derive`,integration marker;读取P2原配置及hash,原evidence脚本保留原字节 |
| 建议createChangeId=always | **不采纳**。P2对首行`^[a-z]+! `已有显式拒绝和成因报错,保持现状;未修改submission_identity或hook参数 |

正则位于编排层`ci_triage.derive_commit`,campaign_state同层复用,不改变shared/skill
依赖契约。只有PM明确授权的DERIVE日期校验被收紧;其它事件/schema/API无改动。
日期按指定正则检查形态,不另增设计外格式或时区规则。

定向共40项,包括两日期各自四个非法输入且subprocess.run未调用、
payload同样拒绝、Z/UTC/非零偏移正例、TZ=Asia/Shanghai与UTC同SHA、
上层对象数量及原字节不变、既有快照、真实hook。
修复前原derive实跑固定向量得SHA=`dd37c1d8fbcc4685bdc174b67569e82eab3c4405`,
parent=`760d5d7be3b5dbfa088f8c348097f059ee53c006`,空tree=`4b825dc642cb6eb9a060e54bf8d69288fbee4904`;
固定身份、消息、带时区日期及该SHA已固化在`test_explicit_timezone_sha_snapshot_is_unchanged`,
修复后通过,未改既有带时区对象结果。

真实hook配置:`stage16_p2_submission_identity/real-hook-config.json`,
SHA256=`3c7e9b5fbe0b7ed945abd74248913c912ee0464abb416c18278bc5811dbb6f50`。
本机定向及全仓均为**PASSED,不是SKIPPED**。缺配置/文件或hash不符时明确skip;
**skip不算已验证**,远端若无私人hook文件,不能以其skip替代本机实测。
断言涵盖最终唯一Change-Id trailer/无辅助行、tree相等、工作区/index/HEAD不变、
生成ID不修改业务对象库、hook文件原字节不变。

### 8.1 实跑证据

证据根:`evidence/review-fixes/`。基线干净树`/tmp/p34-review-baseline-4a6873d`,
候选干净树`/tmp/p4-review-fixes-89a45b0`,只复制本轮四个生产/测试文件。
主树无关草稿及旧文档删除未带入。实际命令:

```sh
R=docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py
E=docs/clang-fix-campaign/dev_memory/stage18_p4_derive_commit/evidence/review-fixes
.venv/bin/python "$R" /tmp/p34-review-baseline-4a6873d "$E/baseline"
.venv/bin/python "$R" /tmp/p4-review-fixes-89a45b0 "$E/current"
.venv/bin/python -m pytest tests/unit/test_derive_commit.py tests/integration/test_derive_commit_real_hook.py -v
.venv/bin/python "$E/compare_validation.py" "$E/baseline" "$E/current" /tmp/p4-review-fixes-89a45b0 tizen-ci-triage/scripts/ci_triage/derive_commit.py tizen-ci-triage/scripts/ci_triage/campaign_state.py tests/unit/test_derive_commit.py tests/integration/test_derive_commit_real_hook.py
```

```text
============================== 40 passed in 0.74s ==============================
tests/integration/test_derive_commit_real_hook.py::test_registered_real_hook_then_derive PASSED [100%]
======================= 1480 passed, 1 skipped in 33.03s =======================
Success: no issues found in 106 source files
All checks passed!
Contracts: 6 kept, 0 broken.
completed=94 unexpected=3
```

各命令的完整argv、路径环境、exit、原始输出与hash在`baseline/commands.json`、
`current/commands.json`及同目录日志;定向exit0原文`targeted.log`。
比较脚本exit0,产物`comparison.json`:94条exit_changes={}、missing_nodeids=[]、
changed_outcomes=[],基线1457/1→1480/1,新增23项。90条既有设计门禁无新增失败,
三条历史偏差仍design-doc-controls=1、duplicate-spec-root-mismatch=0、
twin-both-binary-key=1,不修改判据/期望,不把它们写成全绿。
初次ruff仅新增测试与证据比较器的长行E501,已换行修正;最终ruff exit0。
comparison.json钉定受验四文件SHA,提交前与主树逐字节比对。
远端CI须以本修复提交对应run核验,在交付回报列出链接与结果,不以旧run替代。

## 9. 设计正文待同步(P5设计修订时)

1. §4.2 derive_commit:author_date/committer_date必须匹配PM指定带时区ISO 8601正则,
   不合格ValueError且不运行Git;env固定TZ=UTC。
2. §3.4/§4.2 campaign_state:DERIVE payload两日期复用同一正则,拒绝非法形态。
3. §4.2 derive_commit:仓库发现上界为worktree.resolve().parent,非仓库根由Git
   check=True拒绝,不得向上层仓库写对象。
4. §7 Phase 4:真实hook移交断言纳入integration pytest;skip不算完成验证,
   本机必须有passed原文证据。签收版本缺配置/文件/hash不符均skip;
   **P5待实施**:hash不符改为fail,仅缺配置或文件仍skip(见stage16 §5)。
5. P2 hook的createChangeId保持现状,不采always;首行`^[a-z]+! `的前置拒绝继续有效。
6. **P5待实施**:COMMIT_DATE_RE增加re.ASCII,在正则之外用datetime.fromisoformat
   解析校验,拒绝不存在的日期;derive和状态库DERIVE写入两处同步(见stage16 §5)。

以上是PM本轮直接裁决的待同步文本,本轮design.md零diff,未推进P5实现。

## 10. 最终签收(2026-10-09)

- 单家评审原结论:P4需修改;不改写为原评审直接通过。
- 签收版本与修复commit:`2ba0e0d`;PM已核对修复与裁定一致。
- FatTank已批准签收,按轻量流程不再进行第二轮评审。
- 状态:**P4 CLOSED**;详见[最终签收](../../review/p4-derive-commit-closeout.md#最终签收)。
- P2→P4最终消息移交项完成,本机真实hook PASSED证据保留。
- 新增两项P5加固统一登记在[stage16 §5](../stage16_p2_submission_identity/progress.md#5-p2-01裁决与移交清单),
  本节只确认移交;§9明确区分当前已实现与P5尚未实施,本次不改代码或design.md。
