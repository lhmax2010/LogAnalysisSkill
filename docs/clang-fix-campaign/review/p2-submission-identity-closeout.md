# P2 Submission Identity Closeout

日期:2026-10-08。状态:**READY_FOR_REVIEW**。本文件不是CLOSED签批。

权威:[design.md](../design.md) v1.5.19-FROZEN,§3.4/§4.2/§7 Phase 2;
[change_47](../design_changes/change_47.md)。阶段范围按设计方P2-01轻量裁决:
本期完成组件级验收,真实端到端检查具名移交P4/P5/P5R,不伪称已运行。

## 提交与证据

| 提交 | 内容 |
|---|---|
| `9b7754e` | 原字节设计入库,DDL/CHECK/固定向量入库前验证 |
| `3d48877` | submission_identity、新表及缓存API、组件测试与基线证据 |
| `3e1ea18` | 实现远端CI成功与此前hook缺失的历史记录 |
| 本收口提交 | 登记真实hook摘要、真实冒烟与HEAD变体证据、候审收口;由Git外部锚定,文件内不自记SHA |

证据根目录记为
`docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/`。
下表相对路径均从该目录起算;测试函数均在`tests/unit/`。
[progress](../dev_memory/stage16_p2_submission_identity/progress.md)保留逐步命令、输出与裁决,
本轮最新记录见§10。

## Phase 2 DoD 逐条结论

按冻结稿§7的原始DoD顺序核对;含后续阶段依赖的条目只给P2组件结论,
其未运行部分单列下节,不以本期单测替代端到端验收。

| # | DoD条文/范围 | 结论 | 用例与证据 |
|---|---|---|---|
| 1 | 两个key的段数/成分,unit含build_id、identity不含 | PASS | `test_submission_identity.py::test_keys_fixed_vectors_and_dimensions`及`test_keys_json_encoding_avoids_slash_collision_and_keeps_unicode`;定向日志全部通过 |
| 2 | 委托既有build_submission_key,同输入字节一致 | PASS | `test_compute_key_delegates`;固定向量为64位小写hex;progress §2.2记录入库前原始向量 |
| 3 | 缓存二次不生成;两连接并发一行同值;不同key同ID冲突;hook_sha256/created_at落库;hook升级复用原值 | PASS | `test_campaign_change_ids.py::test_cached_identity_reused_across_builds_hook_upgrades_and_derive`、`test_two_connections_first_get_insert_one_row_and_return_same_value`、`test_change_id_collision_rolls_back_without_replacing_existing`;`real-hook/targeted.log` |
| 4 | generate=None只读:空表/删行均拒绝且不写库;review-submit删行拒绝不push | PASS_COMPONENT / APPROVED_TRANSFER | `test_read_only_cache_miss_does_not_write`、`test_deleted_cache_without_derive_read_only_refuses`;review-submit真实入口移交P5R |
| 5 | hook失败统一错误且不写库;非法身份/摘要/超时/非零/零行/两行/格式;CRLF为41字符;已验证副本抗替换;业务仓库不变;成功失败临时目录删除 | PASS | `test_reject_existing_identity_before_reading_hook`、`test_invalid_hook_output_does_not_write_cache`、`test_crlf_output_is_stored_as_41_characters`、`test_hash_mismatch_and_missing_hook`、`test_verified_bytes_execute_after_original_hook_replaced`、`test_timeout_kills_process_group_and_removes_temporary_directory`、`test_git_configuration_and_business_repository_are_isolated`;shared temporary_dirs fixture断言清理;超时测试缩短至0.5秒,生产上限30秒 |
| 6 | 新表CHECK拒绝非法change_id/source/submission_key/hook_sha256;固定向量64位小写hex | PASS | `test_new_table_rejects_invalid_values`覆盖22参数例;progress §2.2内存执行原始DDL与22个非法值;NULL由NOT NULL拒绝 |
| 7 | previous仅有apply_failed/analyzer_failed的n_a事件回退REPRODUCE而非HELD | PASS | `test_campaign_repair_step.py::test_previous_only_na_outcomes_fall_back_to_reproduce`两参数例,既有生产行为未改 |
| 8 | DERIVE+无缓存禁止生成;跨build缓存优先;生成期间另一连接写DERIVE则插入拒绝;sandbox重推删行拒绝不push | PASS_COMPONENT / APPROVED_TRANSFER | `test_deleted_cache_with_derive_never_regenerates`验证generate=None/函数两种且零调用/零写库;`test_derive_inserted_by_other_connection_during_generate_refuses`、`test_cache_race_winner_takes_precedence_over_new_derive`;sandbox端到端移交P5 |
| 9 | 同message不同submission_key产生不同ID;derive最终message无辅助行且恰一个Change-Id | PASS_COMPONENT / APPROVED_TRANSFER | `test_submission_key_is_hook_input_and_head_exists`、`test_hook_returns_only_id_without_mutating_message`;真实derive最终消息移交P4 |
| 10 | 身份行大小写/空格变体与Gerrit Link拒绝;普通Link不误拒 | PASS | `test_reject_existing_identity_before_reading_hook`参数例及`test_hook_returns_only_id_without_mutating_message`正例 |
| 11 | HOME内reviewUrl/createChangeId=false与外部GIT_DIR不影响结果/业务仓库 | PASS | `test_git_configuration_and_business_repository_are_isolated`、`test_process_environment_is_exact_whitelist`;真实冒烟保存实际隔离env于`real-hook/result.json` |
| 12 | 无git/不可写临时目录统一错误;临时目录删除失败仍返回且WARN | PASS | `test_no_git_in_path_maps_to_hook_error`、`test_unwritable_temporary_directory_maps_to_hook_error`、`test_hook_process_start_failure_maps_and_cleans`、`test_cleanup_failure_warns_without_changing_success` |
| 13 | FatTank登记真实hook在一次性仓库恰一行合法ID,不访问Gerrit;不处理无HEAD的变体在空初始commit后成功 | PASS | `real-hook/smoke.log`/`result.json`:真实与变体exit0;变体无初始commit负例exit1;`network.trace`/`network-check.json`:网络系统调用0;原hook、输入message不变,临时目录均删除 |

结论:§7全部P2组件义务已验证,**本期实施PENDING为0**;
上述三项端到端检查为获批移交,不计作已通过。状态维持READY_FOR_REVIEW。

## 真实Hook与HEAD变体

配置:[real-hook-config.json](../dev_memory/stage16_p2_submission_identity/real-hook-config.json)。
文件:`/home/linhao/gerrit-hook/commit-msg`(Gerrit Code Review 3.10.5)。

```text
$ sha256sum /home/linhao/gerrit-hook/commit-msg
3c7e9b5fbe0b7ed945abd74248913c912ee0464abb416c18278bc5811dbb6f50  /home/linhao/gerrit-hook/commit-msg
exit=0
```

从仓库根复现(不改生产代码、不下载hook、不访问Gerrit):

```sh
E=docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/real-hook
env -u PYTHONPATH -u MYPYPATH strace -f -e trace=network -o "$E/network.trace" .venv/bin/python "$E/run_smoke.py"
```

实测输出摘录:

```text
Change-Id: I79e948ab08b03dc50822a0c798ba01c77a0c6360
real_hook: valid_change_id_lines=1; initial_commits=1; initial_tree_entries=0; exit=0
no_head_variant_without_initial_commit: exit=1; change_id_lines=0
head_required_variant: Change-Id: I79e948ab08b03dc50822a0c798ba01c77a0c6360; exit=0
original_hook_unchanged=true; input_message_unchanged=true; temporary_directories_removed=true
```

生成器仍执行既有§4.2实现;观察包装调用原函数,不替换实际执行。
在清理前读取message文件,验证仅一行合法ID;检测HEAD恰一commit且tree为空。
variant仅删除真实hook的无HEAD兜底,改为强制`git rev-parse --verify HEAD`成功。
无HEAD对照stderr为`fatal: Needed a single revision`,退出1;同一variant经
生产生成器返回合法ID,退出0。完整替换片段与实际argv/env均入`result.json`。
这里的负例不是另一个真实hook,也不替代真实文件冒烟。

`strace`跟踪后代进程,网络系统调用数为0;不依赖仅看shell命令的推测。
本轮ID是一次运行输出,不是固定向量;后续复跑可因commit时间身份不同而变化。
此前缺失hook的`real-hook-presence.log`保留为历史,不再作为当前状态。

## 回归与改动边界

实现基线:`f9dedce`的1349 passed/1 skipped;
实现`3d48877`为1410 passed/1 skipped,新增61,原1350个nodeid全部保留、结果不变。
证据:`comparison.json`中`missing_nodeids=[]`、`changed_outcomes=[]`;
`baseline/pytest.xml`和`current/pytest.xml`保留逐例结果。

本轮只补配置、证据脚本与文档;生产源码、现有测试、权威设计零改动。
本轮实际重跑(命令及exit见`real-hook/validation.json`):

```text
$ env -u PYTHONPATH -u MYPYPATH .venv/bin/python -m pytest tests/unit/test_submission_identity.py tests/unit/test_campaign_change_ids.py tests/unit/test_campaign_state.py tests/unit/test_campaign_repair_step.py -v
============================= 135 passed in 9.09s ==============================
exit=0
$ env -u PYTHONPATH -u MYPYPATH .venv/bin/python -m pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
Required test coverage of 80% reached. Total coverage: 94.62%
======================= 1410 passed, 1 skipped in 32.32s =======================
exit=0
```

本轮还在独立工作树`/tmp/p2-hook-closeout-3e1ea18`复验交付内容:
`real-hook/clean-validation.json`保存实际命令与环境,`clean-*.log`保存原文。
ruff exit0、mypy exit0(`104 source files`)、lint-imports exit0(`6 kept, 0 broken`)、
symbol_audit/bridge各exit0(`198 SYMBOL OK / 4 MODULE-SCOPE OK`),
全量`1410 passed, 1 skipped in 31.25s`,exit0。
主工作树的`ruff check .`曾因四份untracked历史审计脚本报53条错误(exit1),
失败原文和未跟踪状态留在`real-hook/ruff.log`/`workspace-only-ruff.json`。
这些文件未改动、不在交付面;独立树全量ruff通过,不增加P2工具遗留项。

实现阶段的完整门禁锚定于`3d48877`,非本轮伪称重跑:
`current/commands.json`保留94条命令及exit(4项全仓验证+90项既有设计门禁/控制),
相对基线`exit_changes=[]`。mypy/ruff/lint-imports各exit0;
双道审计198符号+4模块域,零差异。旧93函数/类AST与21个schema对象不变,
见`production-scope.json`;新表仅附自身的两个隐式约束索引,没有ALTER旧表。

实现远端CI [37740889109](https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37740889109)
success: `1410 passed, 1 skipped in 48.83s`;
原始metadata与日志位于`remote-ci.json`、`remote-ci.log.gz`。
本收口提交的远端结果由GitHub运行记录外部锚定,不在提交内部自记自身SHA。

## P2-01移交清单

| 未运行的端到端义务 | 目标阶段 | 关门条件与本期对价 |
|---|---|---|
| derive最终commit message无X-Campaign-Submission-Key且恰一个Change-Id trailer | P4 | 实际derive实现后验证最终commit消息;P2只证明生成器返回ID而不修改输入message |
| sandbox重推(已有DERIVE)删缓存行后拒绝且不push | P5 | 真实sandbox-submit入口执行;P2覆盖DERIVE+无缓存时零generate/零写库 |
| review-submit删缓存行后拒绝、不重新生成、不push | P5R | 真实review-submit入口执行;P2覆盖generate=None的只读失败与已有DERIVE双参数分支 |

以上按2026-10-08设计方P2-01裁决移交,不修改DAG、不实现假入口,
不得将组件测试写成推送端到端已通过。

## 遗留项

既有设计工具问题三条(相对P2基线无新增失败);后续工具维护需修复,
本期不放宽断言/修改历史输入以取得名义全绿。未指定后续实施阶段,
交评审确认归属,不冒称已经修复。原始命令与日志见`baseline/`和`current/`。

| 命令(均以`.venv/bin/python docs/clang-fix-campaign/tools/`为前缀) | 期望exit | 基线/实现exit | 原因/证据 |
|---|---|---|---|
| `check_design_doc.py --self-test` | 0 | 1 / 1 | 历史v1.5.2样本或prompt未入库,clean tree缺样本;`design-doc-controls.log`为37/38 passed |
| `symbol_audit.py --negative-fixture duplicate-spec-root-mismatch` | 1 | 0 / 0 | 删除旧gbs_report路径后fixture红因变为definition file not found,非预期root归属规则;`symbol-negative-duplicate-spec-root-mismatch.log` |
| `symbol_audit.py --key-fixture twin-both-binary-key` | 0 | 1 / 1 | fixture仍访问已删除的ci_triage/gbs_report.py定义;`symbol-key-twin-both-binary-key.log` |

真实hook缺失项已在本轮关闭,没有替换为mock或skip。
审查停点:**READY_FOR_REVIEW**,等待设计方核验及评审结论;本次不写最终签批。
