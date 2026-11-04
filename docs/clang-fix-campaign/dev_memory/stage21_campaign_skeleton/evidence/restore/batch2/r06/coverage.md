# 恢复第2批覆盖对照

基线f5f748e;SKEL-RESTORE-01/02/04/06合并验收。全仓nodeid从3164到3410,
新增246、删除0;原有测试文件与断言未修改。具体nodeid见nodeids-added-final.txt。

| 条文/场景 | 测试文件与函数 | 新增数 |
| --- | --- | --- |
| Phase8存储/查询、RESTORE-06 seed | `tests/unit/test_campaign_kb.py` | 83 |
| CLI、RESTORE-04 import参数与原始字节 | `tests/unit/test_campaign_kb_cli.py` | 25 |
| RESTORE-01第二.3.c同步与第二.5报告 | `tests/unit/test_campaign_kb_sync.py` | 35 |
| RESTORE-01第二.4与RESTORE-04八字段 | `tests/unit/test_campaign_propose_fix.py` | 61 |
| RESTORE-04第二D2E补修 | `tests/unit/test_diff_format_patch_restore.py` | 35 |
| RESTORE-02审核资格 | `tests/unit/test_review_restore_t1.py` | 7 |

## Phase8与seed

- `test_seed_hardcoded_hash_vectors`:3个写死的SHA256,含null位置、Unicode NFC与中文UTF-8。
- `test_seed_normalized_summary_dedupe_and_null_identity`:空白/NFC同正文同id,不同正文不同id,
  JSONL实例字段为null,seed不进入T1。
- `test_seed_invalid_input_rejected`、CLI的`test_seed_cli_append_contract`:双null/空正文拒绝,
  CLI exit2且不创建KB。
- `test_process_concurrency_append_and_promote_no_loss`:6进程同时append相同seed与不同instance,
  并交错promote,最终一条seed且无记录丢失。
- `test_ordinary_seven_part_formula_and_imported_raw_utf8`:普通七元原式与imported原始diff槽位;
  CLI的`test_import_crlf_hashes_original_bytes_and_supplied_ci`另覆盖CRLF不改写。
- `test_normalizer_golden_parity`:6向量与convergence现行归一化逐字节相同,不调用私有生产函数。
- `test_t1_requires_every_key`:7个匹配键逐一改变/缺失的拒绝;
  `test_t1_baseline_not_key_warning_set_confidence_and_display_url`:baseline不是硬键,
  warning按集合、confidence不影响资格、展示URL不执行。
- `test_t2_priority_stability_limit_and_new_excluded`:四层优先级、同分稳定、限流5、NEW不参与。
- `test_append_promote_noop_identity_order_and_read_only_query`:单向晋级、同态与重复append不写,
  行序不变、query免锁且只读。
- `test_promote_keyword_contract`:第4.2节公开API的`to_status`关键字可调用。
- `test_atomic_publish_order_and_failure_cleanup`:fsync文件、rename、fsync父目录及发布前故障清理。
- `test_corrupt_database_fails_closed_every_operation`:损坏JSONL的9种形态,三操作均拒绝,不覆盖损坏文件。
- `test_query_ten_thousand_rows_under_one_second`:真实万行读取/校验/筛选低于1秒。
- `test_describe_real_analyzer_packet`:真实gbs_analyzer输出与诊断提取。

测试seed为合成夹具,不是已审定的生产知识;本批不向仓库提交或自动安装实际KB数据。

## 导入、同步与报告

- `test_import_requires_valid_baseline_before_analyzer`:缺参/非法40位hex均exit2,analyzer不启动。
- `test_real_analyzer_import_dedupe_and_different_diff`:真实解析、同diff重复id、不同diff各存一条。
- `test_bad_import_arguments_never_write`:change-ref、QuickBuild编号、profile及空值负例。
- `test_legacy_and_package_invalid_args_same`:ci_triage与新包共享解析,JSON/退出码一致。
- `test_append_new_complete_bound_provenance_and_byte_stable_repeat`:成功sandbox后的完整溯源与幂等审计。
- `test_only_latest_request_latest_result_pass_promotes`、`test_latest_result_fail_overrides_prior_pass_without_status_inference`:
  不以旧PASS或unit状态代替最新请求结果。
- `test_unverified_provenance_refused_without_kb_or_database_writes`、`test_pass_binding_cannot_promote_other_result`:
  PUSH/DERIVE/verification/回显/构建绑定错误零写入。
- `test_cross_file_crash_retries_same_record_and_single_audit`:append/promote/审计后注入异常,
  DB回滚,重跑同KB记录与唯一审计,不新增状态。
- `test_concurrent_sync_locks_out_duplicate_audit`:复用unit锁防重复审计。
- `test_report_db_only_source_and_precedent_match_bound_round`:报告两列来自状态库,
  不打开KB或结果文件、不串轮次、库字节不变。

## 建议与审核

- `test_real_kb_dataclass_query_and_all_three_paths`:真实KB接口的T1本地diff、change_ref与无先例三路径。
- `test_change_ref_uses_derived_remote_and_isolated_git`、`test_imported_diff_never_uses_even_valid_change_ref_or_poisoned_url`:
  假SSH、本地裸库,URL只从配置和匹配project派生,不执行gerrit_url。
- `test_invalid_ref_downgrades_without_transport`、`test_fetch_failure_downgrades_and_cleans_transport`:
  无效ref/取材失败降级,无残留传输库。
- `test_t1_conversion_downgrades_without_partial_spec`:不支持diff降级,无部分edit_spec。
- `test_later_round_uses_convergence_instead_of_ci_or_baseline`与同架构/缺失/摘要错误用例:
  第一轮CI锚点,后续previous_evidence,不静默回退。
- `test_baseline_drift_report_is_not_a_t1_gate`:三种路径均记录基线差异,不作为匹配硬键。
- 所有成功建议用例共同断言八键集合、mode/needs_generation/source/context一致性。
- `test_non_suppressing_t1_qb_pass_reproduced_pushes`及6个拒绝参数:
  T1非抑制可审核;含抑制、forbidden、未复现、未知来源、双向策略不一致拒绝。
  拒绝均断言零push、远端refs不变、零REVIEW;既有26个审核测试原样保留。

## D2E与全仓

`test_actual_format_patch_and_real_guard`使用真实git单/多文件format-patch,
含邮件头与Signed-off-by并通过真实guard。版本号正负例、终端签名位置负例与
latin-1 unsupported_encoding另覆盖;既有64个D2E用例原样保留。

最终结果与负载以`full-final/command.json`和`full-final/stdout.log`为准,不加-x。
`full/`保留最后两项接口/固定错误提示补测前的首轮全仓结果,不覆盖。
既有四条离线端到端位于`tests/unit/test_campaign_batch3_e2e.py`,全仓原样执行;
发现到KB再到审核的新编排全链按原任务留恢复第4批,本批不提前改剧本。
