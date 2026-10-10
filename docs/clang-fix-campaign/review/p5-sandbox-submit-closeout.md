# P5 sandbox-submit 收口

日期:2026-10-10。状态:**CLOSED**。设计方已核对37e27b1与第二轮三条裁定一致,FatTank批准签收;两轮代码评审已用满,不再评审。签收记录见§8。

## 1. 权威与提交

权威:[P5 v1.3.1](../p5-sandbox-submit-design-v1.3.1.md),取代v1.2冻结稿,
包含附录D及P5-D-02验收归类裁定。批准输入SHA256:
`f027f8b4057d4d617f9265968765f01940ce1396e588a65b28e95326e89258e6`;
P5-D-02后SHA256:`83383877f6b8c0deac8606d29fec8a446c1e5520813e714f881855886f888d3b`。
design.md已按附录A.3照录同步至v1.5.21,检查器0 problem,不改变检查器。

| 提交 | SHA | 范围 | 全量结果 |
|---|---|---|---|
| C0 | 38c076f | 冻结、附录A同步 | 1496 passed / 1 skipped |
| C1 | 8c89de4 | 日期、hook hash、发布fsync、DERIVE不可变字段 | 1527 passed / 1 skipped |
| C2 | 1f3141e | 全文件suppress_policy与CLI | 1701 passed / 1 skipped |
| C3 | 68338dc | gate_view与只读查询 | 1724 passed / 1 skipped |
| C4 | 33fcf68 | sandbox-submit、CLI、共用化、Git安全边界 | 1845 passed / 1 skipped |
| C5(首轮收口) | 72a5806 | 本文初版、progress、INDEX、复验 | 1845 passed / 1 skipped |
| 评审文档同步 | c71aa3c | v1.3.1原字节入库、design.md v1.5.21 | checker 0 problem |
| 评审代码修复 | f9a6bc5 | 附录D、D-02用例与变异、完整回归 | 1927 passed / 1 skipped |
| 第一轮评审收口 | e61b6f7 | 本文、progress、INDEX、复验 | 1927 passed / 1 skipped |
| 第二轮代码修复 | 37e27b1 | 格式兼容、归属查找、递归深度;新增10例 | 1937 passed / 1 skipped |
| 第二轮收口更新 | b0ecda4 | 本文、progress、INDEX、复验 | 见§7.2 |

全程未访问真实Gerrit,未做真实业务推送。远端写入测试均为临时本地裸仓库。
原同名远端拒绝测试在传输前即拒绝。新增竞态测试使用SSH形状remote,但以本地
Python包装直接执行git-upload-pack/receive-pack,预期/错误两端均为临时裸仓库,不联网。

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
| v1.3.1按值识别、生成器表达式、真实路径归组 | DONE | §3.1新增12-16行、§7变异原文;POLICY_RULES_VERSION=p5-policy/v2 |
| v1.3.1隔离传输、缩短读事务、统一异常出口 | DONE | §3.3新增28-30行;两端ref、锁与无额外写库断言 |
| 第二轮设计方三条裁定 | DONE | §7.2逐条处置,sha1参数记录/格式不等拒绝、2000命令同hit、64/65/2000层与CLI |
| 收口状态与已知事项 | CLOSED | §4限制保留;设计方核对、FatTank批准,最终签收见§8 |

P4.5遗留的`suppress_policy`与`gate_view`已在P5交付,分别锚定C2 `1f3141e`
与C3 `68338dc`;评审修订与最终验收见§7/§8,不再作为未完成项移交。

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
| §6.1.12按值解码、列表、括号参数、genex整体/递归/闭集 | `test_review_cmake_value_rejection`; `test_review_cmake_value_allowed`; `test_review_genex_nested_closed_rules`; `test_review_if_recursive_rejection` |
| §6.1.12 P5-D-02字面IF回归对照(非退化必红) | `test_review_if_literal_regression` |
| §6.1.12对象库路径相对/绝对(归传输验收) | S:`test_review_transport_objects_path` |
| §6.1.13数字分隔符、游离单引号、pragma前缀 | `test_review_source_apostrophes`; `test_review_pragma_prefixes_and_inline_separator`; `test_review_source_apostrophe_near_misses` |
| §6.1.14真实路径分类/别名归组与重叠 | `test_review_symlink_category_and_grouping`; `test_review_alias_overlap`; `test_review_alias_nonoverlap_and_real_docs` |
| §6.1.15跨模块定位等价 | `test_review_guard_location_equivalence` |
| §6.1.16规则版本 | `test_review_policy_version` |
| 第二轮2-1命令归属表/2000命令/输出不变 | `test_review2_cmake_2000_commands` |
| 第二轮2-2深度边界/CLI/RecursionError兜底 | `test_review2_genex_depth`; `test_review2_genex_deep_cli`; `test_review2_genex_recursion_error_fails_closed` |

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
| §6.3.28隔离传输/对象路径/格式/重建/清理 | `test_review_transport_config_race`; `test_review_transport_objects_path`; `test_review_transport_residue_recreated`; `test_review_transport_sha256`; `test_review_transport_cleanup_warning_does_not_change_result` |
| §6.3.29路径与架构守卫、PolicyInputError、读事务范围 | `test_review_toctou_record_path_same_tree`; `test_review_toctou_policy_input_error`; `test_review_toctou_transaction_ends_before_copies` |
| §6.3.30 CLI统一异常出口、锁释放、成功后补账 | `test_review_cli_unexpected_database_error` |
| 第二轮F1 sha1 init无object-format/格式拒绝/清理 | `test_review2_transport_sha1_omits_object_format`; `test_review2_transport_format_rejects`; `test_review_transport_sha256` |
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
10. 跨命令变量拼接,如`set(A "-Wno" "-unused")`后`add_compile_options(${A})`,
    不在识别范围,两个片段本身都不是完整选项token。
11. 三合字母`??=pragma`不识别;已支持BOM、二合字母`%:`及垂直空白,不扩大至三合字母。

**P5-C4-01指定私有接口事项:**`suppress_policy`引用
`tizen_build_verify.edit_spec_guard._validate_target_path`和`_locate_edit`,
两个消费方均已在symbol_audit登记。原因是策略重绑定必须复用与实际edit应用相同的
路径安全与定位规则,避免两套定位语义漂移。可选后续方案为把原语提为公开接口,
或在策略模块内实现同一定位规则并增加等价回归;本轮不选择、不修改接口。
本轮按v1.3.1新增`test_review_guard_location_equivalence`,比较实际替换区间及生成内容;
今后定位语义变化须同步维护此测试。

P2的跨unit带外删除共享缓存行仍是既有边界,本批只销sandbox重推所属unit的移交项。
review-submit对应移交仍归P5R;真实SSH/sandbox推送、P8.5预检不以本地裸仓库测试冒充。
3个既有checker遗留保持原样,不因本次收口消失,详见§5比较与stage14遗留表。

## 5. 初版验收与证据(历史)

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

## 6. 评审与签收流程

代码评审两轮已用满。设计方已核对第二轮三条裁定的落实与证据,FatTank批准签收,
不再安排第三轮代码评审。冻结稿不变,已知限制见§4,第二轮处置见§7.2。
§7保留当时READY_FOR_REVIEW的取证记录,当前状态以§8最终签收为准。

## 7. 代码评审修订

### 7.1 第一轮

Claude Code、ChatGPT代码评审结论为需修改;按FatTank提供的v1.3.1附录D实施。
文档同步提交`c71aa3c`,以下代码/测试及D-02文档修订统一在`f9a6bc5`。
证据根:[review-code-final](../dev_memory/stage19_p5_sandbox_submit/evidence/review-code-final),
[mutations](../dev_memory/stage19_p5_sandbox_submit/evidence/review-v131/mutations)。

| 发现/来源 | 处置 | 实测证据 |
|---|---|---|
| 原文扫描漏CMake转义、续行、列表、括号参数 | 解码参数值后识别,保留位置映射与转义分号 | `old-raw-cmake.log`:旧实现10 failed;新用例全绿 |
| 生成器表达式拼接/计算型/未列名与递归输出 | 整体闭集解析,IF各输出递归;不可解释一律cmake_genex_unparsed | `old-if-recursion.log`:3 failed;`old-if-literal-control.log`:1 passed |
| source数字分隔符与游离单引号误吞后续内容 | pp-number分隔符不进字符字面量;单引号无同一行闭合仅跳本字符 | pytest.log中§6.1.13参数化正反全绿 |
| pragma前缀漏识别 | 支持首字符BOM、%:、垂直制表和换页 | `test_review_pragma_prefixes_and_inline_separator`全绿 |
| symlink文档别名可绕过实际文件类型 | resolve后分类/归组,跨别名区间重叠以alias_overlap拒绝 | §6.1.14三函数全绿 |
| 主副本remote配置竞态改变传输目标 | 每次重建bare传输目录,对象格式一致,alternates真实路径,cat-file预检 | `old-primary-transport.log`:4 failed;新实现两端ref断言通过 |
| CLI意外异常缺统一JSON出口 | Busy=4,其他INTERNAL_ERROR=5,traceback到stderr,catch不写库 | 四注入点乘两异常共8例通过,锁释放、无PUSH(failed)、重跑补账 |
| TOCTOU事务包围耗时文件/git/hook | 读事务仅1/2/3/6,关闭连接后执行其它检查 | 第二连接事件写入成功;结论不变 |
| TOCTOU PolicyInputError归因 | HELD(edit_spec_rebind_mismatch) | 独立注入测试通过 |
| 同tree同保护标记的路径替换缺实证 | 保留路径/架构守卫并做删除变异 | `removed-path-guard.log`:1 failed,实际pushed而应held |
| 私有定位接口/规则版本 | 加跨模块等价;升p5-policy/v2;限制见§4 | §6.1.15/16通过 |

P5-D-02仅调整验收归类:字面IF样本是新旧均forbidden的回归对照。
三新增IF样本(续行、转义、拼接)旧实现都漏检,无需再次改列;不以版本字段差异冒充退化。
变异源码来自`72a5806`,运行于隔离树,finally恢复精确字节;脚本/命令/退出码/失败原文全部入库。

```text
$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/review-v131/run_mutations.py /tmp/p5-v131-review
current: exit=0, failed=0, passed=60
old-raw-cmake: exit=1, failed=10, passed=0
old-if-recursion: exit=1, failed=3, passed=0
old-if-literal-control: exit=0, failed=0, passed=1
removed-path-guard: exit=1, failed=1, passed=0
old-primary-transport: exit=1, failed=4, passed=0
exact_source_restoration=PASS
restored-policy: exit=0, failed=0, passed=60
restored-sandbox: exit=0, failed=0, passed=23
exit=0
```

review selector中的sandbox 23含一个既有review-ref case,本轮实际新增22,另策略新增60。
总计新增82,全量1845/1变为1927/1,旧nodeid与结果零缺失。

```text
$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py /tmp/p5-v131-review docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/review-code-final
pytest / mypy / ruff / lint-imports / symbol / bridge / design-doc: exit=0
completed=94 unexpected=3
exit=0
================== 1927 passed, 1 skipped in 63.25s (0:01:03) ==================

$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/compare_validation.py docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/review-code-final /tmp/p5-v131-review
exit_changes={}; missing_nodeids=[]; changed_outcomes={}
added_nodeids=431; identical_tested_sources=6
baseline_comparison=PASS
exit=0
C5_to_review nodeids_before=1846 nodeids_after=1928 added=82 missing=0 outcome_changes=0 PASS
```

94条逐命令exit与原输出hash见`review-code-final/commands.json`,基线比较见
[review-code-final-comparison.json](../dev_memory/stage19_p5_sandbox_submit/evidence/review-code-final-comparison.json)。
3项历史异常与§5相同,无新增失败;没有修改检查器判据或期望。

**真实hook本机passed原文**(`review-code-final/pytest.log:72`,不是skip):

```text
tests/integration/test_derive_commit_real_hook.py::test_registered_real_hook_then_derive PASSED [  3%]
```

SHA-256对象格式用例亦PASSED。所有传输测试仅使用本地仓库,未访问真实Gerrit。

映射表按§3四个新模块测试文件的AST函数全集与表内函数名集合双向比较:
`new_module_test_functions=105 missing_from_mapping=[] unknown_test_names=[]`,exit 0。
不存在缺用例名或虚构用例名。

远端CI:
- 文档同步[c71aa3c run 38014808074](https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/38014808074):SUCCESS。
- 代码修复[f9a6bc5 run 38016194029](https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/38016194029):SUCCESS。

本收口更新为单独文档/证据提交,不改代码或测试。其远端CI由推送后的交付回报锚定,
不在未发生时预填成功;状态维持READY_FOR_REVIEW,等待设计方与评审签批。

收口独立复验(干净工作树HEAD=f9a6bc5):

```text
$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py /tmp/p5-v131-closeout docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/review-closeout
pytest / mypy / ruff / lint-imports / symbol / bridge / design-doc: exit=0
completed=94 unexpected=3
exit=0
================== 1927 passed, 1 skipped in 67.19s (0:01:07) ==================

$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/compare_validation.py docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/review-closeout /tmp/p5-v131-closeout
exit_changes={}; missing_nodeids=[]; changed_outcomes={}
added_nodeids=431; identical_tested_sources=0
baseline_comparison=PASS
exit=0
code_to_closeout nodeids=1928 added=0 missing=0 outcome_changes=0 PASS
```

原文与逐nodeid结果:[review-closeout](../dev_memory/stage19_p5_sandbox_submit/evidence/review-closeout),
比较:[review-closeout-comparison.json](../dev_memory/stage19_p5_sandbox_submit/evidence/review-closeout-comparison.json)。
真实hook与SHA-256传输用例再次PASSED;94条门禁无新增失败,3条历史异常不变。

### 7.2 第二轮

结论:Claude Code可签收(一次要、一建议);ChatGPT需修改(一重要)。设计方直接裁定,
三项均在`37e27b1`落实。冻结稿零diff,SHA仍为§1所列83383877值,规则版本保持v2。

| 发现/裁定 | 处置 | 用例与证据 |
|---|---|---|
| 重要F1:sha1传输init无条件传--object-format | sha1省略,sha256显式指定,其它格式ValueError;创建后读取传输仓库格式比较,不等ValueError;两者均经_TransportFailure并清理 | `test_review2_transport_sha1_omits_object_format`记录argv;`test_review2_transport_format_rejects`两case断言原因、push=0、远端空、目录清理;既有sha256用例PASSED |
| 次要2-1:参数归属重复遍历命令 | 建{id(参数):命令}索引,查询结果不变 | `test_review2_cmake_2000_commands`:同一夹具与完整hit快照,改前1.356749秒/改后0.051016秒;二者均一条count=2000 |
| 建议2-2:递归嵌套无界 | 显式depth,第65层抛generator expression too deep,出口捕获ValueError和RecursionError并记cmake_genex_unparsed | `test_review2_genex_depth`64正常、65/2000拒绝;`test_review2_genex_deep_cli`子进程exit 4且无traceback;`test_review2_genex_recursion_error_fails_closed`模拟兜底 |

证据:[review-round2/before](../dev_memory/stage19_p5_sandbox_submit/evidence/review-round2/before)、
[review-round2/after](../dev_memory/stage19_p5_sandbox_submit/evidence/review-round2/after),
含精确命令、代码/测试SHA、原始输出、JUnit结果。新旧测试文件SHA相同,hit全字段相同。
性能改前已低于5秒,不虚称该例旧实现必红。本机git 2.43.0,以init调用记录验证参数契约,
不将其表述为真实git 2.26二进制实跑。

```text
$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/review-round2/run_targeted.py before .
8 failed, 2 passed, 365 deselected in 5.59s
pytest_exit=1
recorder_exit=0

$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/review-round2/run_targeted.py after .
10 passed, 365 deselected in 1.26s
pytest_exit=0
recorder_exit=0
same_test_source_sha256=PASS; same_hit_payload=PASS

$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py /tmp/p5-round2-code docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/review-round2-code
pytest / mypy / ruff / lint-imports / symbol / bridge / design-doc: exit=0
completed=94 unexpected=3
exit=0
================== 1937 passed, 1 skipped in 65.66s (0:01:05) ==================

$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/compare_validation.py docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/review-round2-code /tmp/p5-round2-code
exit_changes={}; missing_nodeids=[]; changed_outcomes={}
added_nodeids=441; identical_tested_sources=4
baseline_comparison=PASS
exit=0
round1_to_round2 old_nodeids=1928 new_nodeids=1938 added=10 missing=[] outcome_changes={} PASS
```

新增10例全部通过,既有1928个nodeid与结果全部保留。94条门禁的3条历史异常仍与
cd7f8dd一致,无新增失败。完整命令/exit原文:
[review-round2-code/commands.json](../dev_memory/stage19_p5_sandbox_submit/evidence/review-round2-code/commands.json);
[基线比较](../dev_memory/stage19_p5_sandbox_submit/evidence/review-round2-code-comparison.json)。

真实hook本机passed原文(同目录pytest.log:72):

```text
tests/integration/test_derive_commit_real_hook.py::test_registered_real_hook_then_derive PASSED [  3%]
```

第二轮代码CI实测(exit 0):

```text
$ gh run view 38019264989 --json status,conclusion,url,headSha
{"conclusion":"success","headSha":"37e27b1d8fc4d531a131e7c9c356e418e2804ec7","status":"completed","url":"https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/38019264989"}
```

[代码CI SUCCESS](https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/38019264989)。
独立文档提交的CI在推送后核验,不在本文件预填结果。

独立收口复验(干净工作树37e27b1,只复制本文修订):

```text
$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage16_p2_submission_identity/evidence/review-minors/run_validation.py /tmp/p5-round2-closeout docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/review-round2-closeout
pytest / mypy / ruff / lint-imports / symbol / bridge / design-doc: exit=0
completed=94 unexpected=3
exit=0
================== 1937 passed, 1 skipped in 68.61s (0:01:08) ==================

$ .venv/bin/python docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/compare_validation.py docs/clang-fix-campaign/dev_memory/stage19_p5_sandbox_submit/evidence/review-round2-closeout /tmp/p5-round2-closeout
exit_changes={}; missing_nodeids=[]; changed_outcomes={}
added_nodeids=441; identical_tested_sources=0
baseline_comparison=PASS
exit=0
code_to_closeout nodeids=1938 added=0 missing=0 outcome_changes=0 PASS
```

原文及逐nodeid:[review-round2-closeout](../dev_memory/stage19_p5_sandbox_submit/evidence/review-round2-closeout);
[比较](../dev_memory/stage19_p5_sandbox_submit/evidence/review-round2-closeout-comparison.json)。
真实hook再次PASSED;3条历史异常不变。映射表实跑:
`mapped_functions=120 required_functions=111`,
`missing_from_table=[]`, `unknown_in_table=[]`, `rule_test_mapping=PASS`;
可复现命令见[progress §19](../dev_memory/stage19_p5_sandbox_submit/progress.md#19-代码评审第二轮)。

第二轮收口提交b0ecda4仅含文档与证据,当时保持READY_FOR_REVIEW;最终签收见下节。

## 8. 最终签收

日期:2026-10-10。批准依据为FatTank本轮签收通知,不是实现方自行关闭。

| 项目 | 签收记录 |
|---|---|
| 设计冻结与修订链 | v1.2-FROZEN(C0 `38c076f`) → v1.3.1(文档同步`c71aa3c`);实施裁定P5-C0-01、P5-C2-01、P5-C2-02、P5-C4-01、P5-D-02均已登记并落实,详见stage19 progress |
| 第一轮代码评审 | Claude Code、ChatGPT结论为需修改;全部发现由`f9a6bc5`修复,收口证据`e61b6f7`,逐项见§7.1 |
| 第二轮代码评审 | Claude Code可签收(一次要、一建议),ChatGPT需修改(一重要);设计方三条裁定由`37e27b1`修复,收口证据`b0ecda4`,逐项见§7.2 |
| 设计方核对 | 已核对`37e27b1`与第二轮三条裁定一致;第一轮全部发现与第二轮三条均已修复 |
| 最终验收 | 1937 passed / 1 skipped;94条验收相对cd7f8dd无新增失败,3条历史异常不变;原始输出见§7.2及review-round2-closeout |
| FatTank批准 | 已批准P5签收;代码评审两轮已用满,不再评审 |

最终代码版本`37e27b1`,收口证据版本`b0ecda4`。两者CI均通过:
[代码CI](https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/38019264989)、
[收口CI](https://github.com/lhmax2010/LogAnalysisSkill/actions/runs/38019591063)。
本次只登记签收,不修改代码、测试、冻结设计或历史验收输出。

状态:**P5 CLOSED**。P4.5遗留的`suppress_policy`与`gate_view`已在P5交付。
P5Q移交事项集中于[stage19 §21](../dev_memory/stage19_p5_sandbox_submit/progress.md#21-p5q移交清单),
EF-5缺口与两项业务裁定仍未关闭;真实Gerrit sandbox首次推送仍按EF-6放在P12。
