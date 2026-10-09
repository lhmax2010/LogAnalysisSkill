# P5 sandbox-submit 收口

日期:2026-10-09。状态:**READY_FOR_REVIEW**。未自行签批CLOSED。

## 1. 权威与提交

权威:[P5 v1.2-FROZEN](../p5-sandbox-submit-design-v1.2-FROZEN.md),
包含P5-C0-01、P5-C2-01、P5-C2-02、P5-C4-01轻量裁定;
现SHA256:`432f0e62b1f836622012559c3c35e3cd57021423786d18da337d096c0d2de95b`。
design.md已按附录A同步至v1.5.20,外部章节引用使用“第x节”,不改变检查器。

| 提交 | SHA | 范围 | 全量结果 |
|---|---|---|---|
| C0 | 38c076f | 冻结、附录A同步 | 1496 passed / 1 skipped |
| C1 | 8c89de4 | 日期、hook hash、发布fsync、DERIVE不可变字段 | 1527 passed / 1 skipped |
| C2 | 1f3141e | 全文件suppress_policy与CLI | 1701 passed / 1 skipped |
| C3 | 68338dc | gate_view与只读查询 | 1724 passed / 1 skipped |
| C4 | 33fcf68 | sandbox-submit、CLI、共用化、Git安全边界 | 1845 passed / 1 skipped |
| C5 | 本收口提交由Git外部锚定,不自记SHA | 本文、progress、INDEX、最终复验 | 见§5 |

全程未访问真实Gerrit,未做真实业务推送。远端写入测试均为临时本地裸仓库。
同名远端拒绝测试仅在本地配置SSH形式的名字,在任何传输发生前即被拒绝。

## 2. DoD结论

| 事项 | 结论 | 证据 |
|---|---|---|
| 冻结输入与附录A同步 | DONE | [progress §3](../dev_memory/stage19_p5_sandbox_submit/progress.md#3-c0已完成的文档工作与证据),C0 checker exit 0 |
| §5四项加固 | DONE | C1命令/原输出;§6.4映射见下表;真实hook本机PASSED |
| §2全文件比较与移除hit形状 | DONE | C2定向174 passed;公式不变,C2-01错例改forbidden,C2-02输出形状按裁定 |
| §3同快照视图与只读查询 | DONE | C3定向23 passed;读取间第二连接写入控制 |
| §1共用unit_hash/src_clean等价 | DONE | C4逐定义AST source segment字节比较,旧repair-step用例全部保留 |
| §4锁、POLICY/DERIVE/缓存顺序、TOCTOU、单sandbox ref | DONE | C4定向121 passed;正常/崩溃/重跑/边界控制;全部action逐字段JSON快照 |
| §4.4配置来源与统一Git环境 | DONE | C4-01四类要求,另有worktree scope、多行配置值不回显控制 |
| P2移交的sandbox重推删缓存 | DONE | `test_deleted_cache_rejects_without_regeneration`:HELD primary arch、hook=0、push=0、缓存不重建 |
| 三架构保护标记保持 | DONE | `test_normal_path_and_idempotent_rerun`:全部保护文件仍在 |
| 全量集合不缩小、既有门禁无新增失败 | DONE | 各C阶段commands.json、pytest.xml及comparison.json;固定基线cd7f8dd |
| 收口状态与已知事项 | READY_FOR_REVIEW | §4限制完整登记,由设计方核验与评审决定签批 |

## 3. 规则条目与用例双向映射

用例编号采用真实pytest函数名,括号内参数化case见各阶段`pytest.xml`完整nodeid。
同一行同时定义“规则→用例”和“用例→规则”关系,可按右列函数名反查左列;
一个用例可覆盖多条规则。以下文件代号仅缩短路径,不是另造测试编号:

- P: `tests/unit/test_suppress_policy.py`
- G: `tests/unit/test_campaign_gate_view.py`
- S: `tests/unit/test_sandbox_submit.py`
- T: `tests/unit/test_sandbox_git.py`
- D: `tests/unit/test_derive_commit.py`
- R: `tests/unit/test_campaign_repair_step.py`
- H: `tests/integration/test_derive_commit_real_hook.py`

### 3.1 §6.1策略

| 规则条目 | 用例编号(文件P) |
|---|---|
| §6.1.1 token边界 | `test_token_boundaries` |
| §6.1.2 kind正反、pragma/字面量/注释 | `test_option_kinds`; `test_wholesale_options_have_no_scope_key`; `test_pragma_kinds`; `test_source_near_misses` |
| §6.1.3作用域、文件分类、续行 | `test_cmake_scopes`; `test_cmake_comments`; `test_automake_assignment`; `test_file_category_precedence`; `test_quoted_cmake_continuation_and_unchanged_targets` |
| §6.1.4全文件计数退化守卫 | `test_whole_file_migration_and_activation`; `test_scope_keyword_only_edit_uses_entire_command_span`; `test_fragment_replacement_and_adjacent_edits`; `test_same_scope_reorder_and_unchanged_suppression` |
| §6.1.5逐文件移除判据 | `test_no_cross_file_offset_for_werror_or_targets`; `test_werror_removed_count_and_fixed_fields`; `test_target_removed_fixed_fields`; `test_pop_removal_fixed_fields_and_suppression_removal_offset`; `test_pure_deletion_fixed_fields` |
| §6.1.6原样保留 | `test_same_scope_reorder_and_unchanged_suppression` |
| §6.1.7 source_kind优先级 | `test_source_kind_strategy_precedence` |
| §6.1.8输入拒绝 | `test_policy_input_errors` |
| §6.1.9独立CLI | `test_cli_stdout_exactly_matches_evaluate`; `test_cli_subprocess_exit_codes`; `test_cli_invalid_input_has_exit_two` |
| §6.1.10确定性与位置映射 | `test_determinism_reordering_length_changes_and_no_mutation`; `test_new_span_mapping_continuations_line_anchor_and_doc_mixture`; `test_sort_order_and_minimal_touching_edit` |
| §6.1.11 C2-02逐字段输出 | `test_werror_removed_count_and_fixed_fields`; `test_werror_removed_once_per_token_with_both_count_terms`; `test_target_removed_fixed_fields`; `test_pop_removal_fixed_fields_and_suppression_removal_offset`; `test_pure_deletion_fixed_fields`; `test_multiple_removals_use_declared_output_shape`; `test_removed_instance_old_interval_not_new_interval` |

### 3.2 §6.2只读视图

| 规则条目 | 用例编号(文件G) |
|---|---|
| §6.2.1 reproduced | `test_reproduced_depends_on_primary_and_all_three_arches`; `test_primary_latest_reproduce_overrides_old_matched` |
| §6.2.2按event_id取最新、push分ref | `test_latest_payload_uses_event_id_not_timestamp`; `test_push_classes_have_independent_latest_event`; `test_latest_derive_allows_changed_commit_but_not_changed_identity` |
| §6.2.3 QB两级最新 | `test_qb_two_level_latest_does_not_fall_back_to_old_request` |
| §6.2.4 DERIVE五字段 | `test_gate_view_detects_each_immutable_derive_field_across_all_rows`; `test_derive_write_side_rejects_committer_change` |
| §6.2.5一致快照 | `test_gate_view_uses_one_snapshot_across_queries` |
| §6.2.6空/不存在unit | `test_empty_unit_and_missing_unit` |
| §6.2.7查询不写入 | `test_latest_policy_is_round_specific_and_read_only`; `test_lookup_change_id_hit_and_miss_never_generate_or_write` |

### 3.3 §6.3提交

| 规则条目 | 用例编号(默认文件S) |
|---|---|
| §6.3.1正常路径/缓存先行/消息/保护 | `test_normal_path_and_idempotent_rerun` |
| §6.3.2幂等 | `test_normal_path_and_idempotent_rerun` |
| §6.3.3补账两例 | `test_remote_success_missing_bookkeeping` |
| §6.3.4远端改动 | `test_remote_ref_changed_is_forced_back` |
| §6.3.5缓存丢失 | `test_deleted_cache_rejects_without_regeneration` |
| §6.3.6参数零写入 | `test_invalid_parameters_are_zero_write`; `test_cli_snapshot_and_malformed_args` |
| §6.3.7分支名 | `test_branch_rejected_before_writing`; `test_ref_classes` |
| §6.3.8选定零写入 | `test_selection_errors_do_not_freeze_unit` |
| §6.3.9四锁/重读 | `test_four_locks_are_shared_and_nonblocking`; `test_lock_selection_is_reread_and_repair_step_contends` |
| §6.3.10聚合 | `test_aggregate_rejection_before_policy` |
| §6.3.11重绑定 | `test_rebinding_before_evaluate` |
| §6.3.12 forbidden审计记录/无派生 | `test_forbidden_policy_is_recorded_without_derive` |
| §6.3.13存量POLICY | `test_stored_gate_tampering_is_held[policy]` |
| §6.3.14副本现场/多份坏副本 | `test_copy_scene_is_held_with_arch` |
| §6.3.15副本缺失 | `test_missing_copy_is_worktree_lost_not_held` |
| §6.3.16 src_clean | `test_src_identity_rejected_without_held` |
| §6.3.17 TOCTOU、远端紧前变化 | `test_toctou_each_snapshot_component`; `test_toctou_db_queries_share_snapshot`; `test_remote_mutation_after_toctou_and_post_toctou_config_guard` |
| §6.3.18 A12带外行 | `test_stored_gate_tampering_is_held[derive]` |
| §6.3.19 hook失败恢复 | `test_hook_hash_failure_then_retry` |
| §6.3.20推送失败/读取/超时 | `test_push_failure_then_recovery` |
| §6.3.21隐式路径 | `test_follow_tags_disabled_and_only_one_refspec`; `test_submodule_remote_untouched`; `test_unsafe_config_prevents_commands_and_preserves_remotes`; `test_named_remote_is_rejected`; `test_mandatory_overrides_disable_hook_and_fsmonitor` |
| §6.3.22九窗口 | `test_nine_crash_windows_converge` |
| §6.3.23敌对环境 | `test_hostile_git_environment_is_removed`; T:`test_every_call_has_isolated_environment_and_overrides` |
| §6.3.24复用存量参数 | `test_normal_path_and_idempotent_rerun` |
| §6.3.25 HELD架构与锁内写入 | `test_held_requires_arch_and_lock_remains_held_during_write`; `test_deleted_cache_rejects_without_regeneration`; `test_stored_gate_tampering_is_held`; `test_copy_scene_is_held_with_arch`; `test_toctou_each_snapshot_component` |
| §6.3.26全部action快照 | `test_all_action_json_snapshots`; `test_cli_snapshot_and_malformed_args` |
| §6.3.27 C4-01来源/版本 | `test_include_and_old_git_reject_via_command`; T:`test_fresh_repository_ignores_only_command_overrides`; `test_local_config_rejected_even_when_overridden`; `test_include_config_rejected`; `test_old_git_rejected_before_scope_query`; `test_worktree_scope_is_not_exempt`; `test_multiline_config_value_never_echoed` |
| §1共用化等价 | `test_repair_primitives_moved_without_source_changes`; R:`test_source_identity_joint_check_rejects_each_mismatch` |

### 3.4 §6.4移交加固

| 规则条目 | 用例编号 |
|---|---|
| §6.4.1日期ASCII与有效日历 | D:`test_non_ascii_or_impossible_dates_refuse_before_git_and_payload`; `test_real_dates_with_timezone_can_derive` |
| §6.4.2真实hook与缺失/错hash | H:`test_registered_real_hook_then_derive`; `test_real_hook_digest_mismatch_is_failure`; `test_missing_real_hook_inputs_remain_skip` |
| §6.4.3三成功发布路径及错误恢复 | R:`test_edit_spec_all_success_paths_fsync_parent`; `test_edit_spec_filesystem_failure_is_uncounted_and_retryable`; `test_conflicting_edit_spec_never_fsyncs_parent` |
| §6.4.4 committer写入不可变 | G:`test_derive_write_side_rejects_committer_change` |

## 4. 已知限制与事项

按§2.5/§2.8保留,未擅自扩大实现:

1. 属性命令中COMPILE_OPTIONS之后的其它属性值若含-Wno-*也会被识别为target_property;
   该写法没有编译效果,不构成全局抑制。
2. `target_compile_options(t PRIVATE ${MY_FLAGS} -Wno-x)`因段归属不确定而保守拒绝,
   需要人工处理。
3. edit_spec只能替换既有文件内容,不能表达删除源文件。
4. 从CMake源文件列表中移除单个`.c`不在检测范围。
5. 纯删行(包括移除未使用变量整行)被pure_deletion拦截,须人工处理。
6. 新增调用在本次edit外定义的抑制宏不会被识别,只有宏定义处的_Pragma被识别。
7. 跨文件搬动-Werror或target声明会被拦截,须人工处理。
8. doc类不识别;仓库若从.md/.rst读取编译选项则不会被检出。
9. rules_version升级若改变结论,已有POLICY与本轮重算不一致将挂起,
   即使单元尚未推送;须人工重置,不以版本号一致替代结论比较。

**P5-C4-01指定私有接口事项:**`suppress_policy`引用
`tizen_build_verify.edit_spec_guard._validate_target_path`和`_locate_edit`,
两个消费方均已在symbol_audit登记。原因是策略重绑定必须复用与实际edit应用相同的
路径安全与定位规则,避免两套定位语义漂移。可选后续方案为把原语提为公开接口,
或在策略模块内实现同一定位规则并增加等价回归;本轮不选择、不修改接口。

P2的跨unit带外删除共享缓存行仍是既有边界,本批只销sandbox重推所属unit的移交项。
review-submit对应移交仍归P5R;真实SSH/sandbox推送、P8.5预检不以本地裸仓库测试冒充。
3个既有checker遗留保持原样,不因本次收口消失,详见§5比较与stage14遗留表。

## 5. 验收与证据

统一证据根:[stage19/evidence](../dev_memory/stage19_p5_sandbox_submit/evidence)。
每阶段commands.json保存完整argv、cwd、PYTHONPATH/MYPYPATH、exit及原始输出hash;
同目录`.log`为原文,`pytest.xml`保留逐nodeid结果。C4新增121,基线累计新增349,
原1497个nodeid(1496 passed/1 skipped)全部保留且结果不变。

```text
$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py /tmp/p5-c4-68338dc docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C4
pytest / mypy / ruff / lint-imports / symbol / bridge / design-doc: exit=0
completed=94 unexpected=3
exit=0
1845 passed, 1 skipped in 57.28s

$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/compare_validation.py docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C4 /tmp/p5-c4-68338dc
exit_changes={}; missing_nodeids=[]; changed_outcomes={}
added_nodeids=349; identical_tested_sources=8
baseline_comparison=PASS
exit=0
```

上述门禁行是摘录,完整原文见commands.json与log。三项历史期望不符的当前/基线exit
均为:design-doc-controls 1;symbol-negative-duplicate-spec-root-mismatch 0;
symbol-key-twin-both-binary-key 1。未放宽任何checker或修改期望。

**真实hook本机passed原文**(不是skip,C4/pytest.log:72):

```text
tests/integration/test_derive_commit_real_hook.py::test_registered_real_hook_then_derive PASSED [  3%]
```

C5独立复跑:证据[C5/commands.json](../dev_memory/stage19_p5_sandbox_submit/evidence/C5/commands.json),
[C5-comparison.json](../dev_memory/stage19_p5_sandbox_submit/evidence/C5-comparison.json)。

```text
$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py /tmp/p5-c5-33fcf68 docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C5
pytest: exit=0 expected=0
mypy: exit=0 expected=0
ruff: exit=0 expected=0
lint-imports: exit=0 expected=0
symbol: exit=0 expected=0
bridge: exit=0 expected=0
design-doc: exit=0 expected=0
completed=94 unexpected=3
exit=0
1845 passed, 1 skipped in 57.36s

$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/compare_validation.py docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/C5 /tmp/p5-c5-33fcf68
added_nodeids=349; identical_tested_sources=0
baseline_comparison=PASS
exit=0
C4_to_C5 nodeids=1846 added=0 missing=0 outcome_changes=0
exit=0
```

C5的真实hook同样在pytest.log:72显示PASSED。映射表机器复核:
`new_module_test_functions=83 missing_from_mapping=[] unknown_test_names=[]`,exit 0。
所有代码与测试来自C4提交,C5源码diff为空。

远端CI:C0-C4均成功;最近一次为
[C4 run 37912146491](https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/37912146491),
headSha=`33fcf68241b4ada6fcfd8b03df8d026ef14d82a8`,conclusion=`success`。
C5自己的CI须在本提交推送后核验并回报,此处不预填结果。

## 6. 评审请求

请核对实现与冻结稿及轻量裁定一致,尤其是策略全文件比较、缓存/DERIVE顺序、
TOCTOU读事务、Git配置来源过滤和唯一sandbox ref推送;确认已知限制可接受。
本文件只提交READY_FOR_REVIEW,不代表设计方或评审已签批。
