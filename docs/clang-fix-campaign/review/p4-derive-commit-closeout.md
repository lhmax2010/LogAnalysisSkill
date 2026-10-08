# P4 Derive Commit Closeout

日期:2026-10-08。状态:**READY_FOR_REVIEW**,未自行签批CLOSED。

权威:`../design.md` v1.5.19-FROZEN §3.4/§4.2/§7 Phase 4。
基线为P3 `0910f34`;本期只新增`ci_triage/derive_commit.py`及测试/取证/记账,
不改既有API、design.md或状态库行为。本提交由Git外部锚定。

## DoD 对照

| 条文 | 结论 | 证据 |
|---|---|---|
| derive完整输入参与派生,包含committer_identity | PASS | `test_each_derivation_input_participates_in_identity`七参数例;同输入返回同SHA;正例检查实际parent/作者/提交者/两日期 |
| 派生后tree等于输入tree_sha | PASS | 主正例在index tree与输入tree不同条件下通过;`test_tree_postcondition_is_enforced`伪造读回值必拒,非可被-O禁用的assert |
| 消息模板/trailer快照 | PASS | `test_tree_parent_identities_message_snapshot_and_worktree_index_unchanged`比较原始commit message;`test_hook_identity_goes_to_final_trailer_without_auxiliary_line`以Git解析trailer验证 |
| 不checkout、不碰工作区/index | PASS | 已暂存/未暂存/未跟踪/symlink均保留;权限、mtime、内容、index原字节、HEAD/refs快照相同;非法tree失败路径同样不变 |
| P2移交:真实hook生成ID后组装最终message并derive | PASS | `run_real_hook_derive.py`:真实登记hook输出合法ID,最终message逐字相等,恰一个Change-Id trailer且无辅助key行,tree相等;strace网络调用0 |
| 全仓回归、mypy、ruff、lint-imports | PASS | 1457 passed/1 skipped;各exit0;106源文件mypy成功、6契约全绿 |
| 相对基线无新增设计门禁失败 | PASS | 90项checker/控制逐条exit不变;三项历史偏差保留,未改判据 |

## 命令与证据

证据根:[stage18 evidence](../dev_memory/stage18_p4_derive_commit/evidence/)。
逐条命令、完整环境路径、exit、原始输出与sha256:
`baseline/commands.json`、`current/commands.json`及同目录日志。
全套复现命令与输出摘录见[progress §3](../dev_memory/stage18_p4_derive_commit/progress.md#3-dod与证据)。

```text
$ .venv/bin/python -m pytest tests/unit/test_derive_commit.py -v
============================== 17 passed in 0.64s ==============================
exit=0
```

全量1440/1 → 1457/1,新增17例,旧1441 nodeid全保留且结果不变。
`comparison.json`:missing_nodeids/changed_outcomes/exit_changes均空;
新模块/测试/取证脚本摘要与受验版本绑定。
双道198符号+4模块域全绿,6个import契约全绿。
远端CI在本期独立提交推送后查验,对应run由GitHub外部锚定并在交付回报给出链接。

真实hook信息与逐字最终消息见`real-hook-derive.json`。实跑结果:

```text
Change-Id: I8e91478cf9cd759b9b15412bb1b9dcb789ed8095
commit=394865306a0938d64042fffbfdb0c055e79bc928
input_tree=actual_tree=117b8ac7b07e6b56f3191d5f49ff82fc74234b4c
change_id_trailers=1; auxiliary_lines=0; workspace/index/HEAD unchanged; exit=0
network_syscalls=0
```

上段commit/tree为JSON字段摘要,stdout原文见`real-hook-derive.log`。
登记hook SHA仍为`3c7e9b5fbe0b7ed945abd74248913c912ee0464abb416c18278bc5811dbb6f50`。
P2移交本期的一项已销账;P5/P5R两项尚未实施,没有混作本期已验。

## 实现口径与遗留

- 消息组装仍由调用方负责(§3.4顺序/P5);本期不新增formatter API或发明溯源字段。
  快照覆盖冻结subject前缀、正文与Change-Id trailer,真实hook完成移交验收。
- 身份格式采用Git `Name <email>`,tree/parent取完整SHA、日期显式传入;
  Git运行/校验异常直接抛出,不发明新的CLI错误码。具体留痕见progress §2。
- 环境路由与配置隔离确保指定worktree及显式身份/日期生效;不运行commit-msg hook,
  不更新refs/index,只允许commit对象写入。状态记录与主arch路径选择归调用方。
- 首轮测试快照先于其自身write-tree导致index差异,修正取证顺序后通过;
  失败原文与独立复现实证均保留,见progress §5。无生产行为修补或断言放宽。
- 三条既有checker问题沿用P2/P3:design-doc-controls、duplicate-spec-root-mismatch、
  twin-both-binary-key,基线/当前exit分别1/1、0/0、1/1。未新增、未伪称已修。

待设计方核验与评审,状态维持READY_FOR_REVIEW。
