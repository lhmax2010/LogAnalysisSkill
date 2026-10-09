# P4 Derive Commit Closeout

日期:2026-10-09。状态:**CLOSED**,PM核对通过,FatTank批准签收。
首次实现及评审修复证据保留;签收记录见末尾“最终签收”。

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

此处为首次候审记录,当时状态READY_FOR_REVIEW;最终状态见末尾签收。

## 远端验收补丁

首次远端run 37752238528在新增测试的Git日期显示断言失败:
Git 2.55.0显示UTC为`Z`,本机2.43.0显示`+00:00`,结果1 failed/1456 passed/1 skipped。
补丁不改生产代码,日期断言改核对原始commit头的身份、epoch与时区,
避免依赖显示版本。原始失败记录、原因与补丁复跑证据见
[progress §7](../dev_memory/stage18_p4_derive_commit/progress.md#7-远端日期断言兼容性修正)。
`current/`为首次本机记录,`ci-date/`为补丁后的独立完整复跑,不覆盖旧证据。
补丁全量1457 passed/1 skipped,四项主验收exit0;94条exit与P3基线逐条不变,
详见`ci-date-comparison.json`。补丁远端run单独核对,不以首次失败run冒充通过。

## 评审修复

2026-10-09按PM轻量裁决落实;修复提交时状态FIXES_APPLIED,不修改design.md,
待P5设计修订统一同步。此前READY_FOR_REVIEW为历史停点。

| 发现 | 处置 | 证据路径(stage18) |
|---|---|---|
| 日期接受相对/无时区输入 | 唯一COMMIT_DATE_RE,derive与DERIVE payload共用;非法输入在Git前拒绝 | `evidence/review-fixes/targeted.log`:两字段四类非法输入均通过;PayloadSchemaError对应校验 |
| 环境TZ导致不确定性 | Git env固定UTC,Shanghai/UTC同SHA;带偏移固定SHA与改前一致 | 同上timezone与sha_snapshot测试 |
| 普通子目录向上发现仓库 | GIT_CEILING_DIRECTORIES=resolve().parent,CalledProcessError且outer对象数量/字节不变 | 同上inner_directory测试 |
| 真实hook未纳pytest | 新integration用例复用P2配置与hash,原脚本保留;最终message/tree/现场断言全部通过 | 同上`test_registered_real_hook_then_derive PASSED`;`current/pytest.log`同样PASSED |
| createChangeId=always建议 | 不采纳,P2已拒绝`^[a-z]+! `首行并说明原因,维持原hook契约 | progress §8/§9,submission_identity无diff |

真实hook缺配置/文件或hash不符时skip。**skip不算已验证**;
本机实跑为passed,不是skipped,完整log见上表。远端缺私有hook时的skip不替代此证据。
本次40项定向exit0;全仓1457/1→1480/1(+23),mypy/ruff/lint-imports各exit0。
相对固定4a6873d,94命令exit无变化,既有用例无缺失/结果变化;
90门禁的三条历史偏差原样保留。完整命令与对照在
[progress §8](../dev_memory/stage18_p4_derive_commit/progress.md#8-评审修复与pm轻量裁决2026-10-09)
及`evidence/review-fixes/comparison.json`。本提交远端CI由GitHub run外部锚定,
推送后实查并在交付回报给出链接。

## 最终签收

| 项目 | 日期 | 记录 |
|---|---|---|
| 签收commit | 2026-10-09 | `2ba0e0d`,P4评审修复后的版本 |
| 单家评审结论 | 2026-10-09登记 | P4需修改;按PM裁定修复后由PM核对,不冒称原评审直接通过或进行第二轮评审 |
| 修复commit | 2026-10-09 | `2ba0e0d`:日期格式与UTC、仓库查找边界、真实hook integration用例 |
| PM核对结论 | 2026-10-09 | 已核对修复与裁定一致,通过 |
| FatTank批准 | 2026-10-09 | 批准P4签收,不再进行第二轮评审 |

**状态:P4 CLOSED @ `2ba0e0d`。** 本文档签收登记提交由Git外部锚定,不自记SHA。
该版本[远端CI](https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37879648575)
success;真实hook本机PASSED证据保留,skip不作已验证。

签收同时将两项加固移交P5,统一登记在
[stage16 §5移交清单](../dev_memory/stage16_p2_submission_identity/progress.md#5-p2-01裁决与移交清单):
日期增加re.ASCII与datetime.fromisoformat解析,派生及状态库写入同步;
真实hook摘要不符由skip改fail,配置/文件不存在仍skip。
**这两项尚未实施**,不把当前正则匹配或摘要不符skip记成已加固。
设计待同步措辞见stage18 §9;本次不改design.md、不改代码。
