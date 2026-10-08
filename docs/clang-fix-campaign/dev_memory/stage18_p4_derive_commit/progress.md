# Stage18 P4 derive_commit

日期:2026-10-08。状态:**READY_FOR_REVIEW**。

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
