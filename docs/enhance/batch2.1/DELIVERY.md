# 第 2.1 批交付与证据索引

依据 HLD v0.5.4、第 2.1 批任务及 B2-Q01 裁定。仓库实现基点 `3ff18e4c86c578e19622d37fb96b306b40a23bf6`。本批只修改四个本线目录及 docs/enhance；不访问真实服务、不使用浏览器、不执行 P4。HLD 原件保持 SHA256 `8fdcb3c9b8c26e592bad0695db59736709b02790adeae9ba87386cfd1b26f2f8`。

## 证据入口

| 材料 | 路径 / 结论 |
|---|---|
| 完整测试输出 | [evidence/test-output.txt](evidence/test-output.txt)：Python 3.10.12，125 tests，OK；三条 import 约束通过，TLS 未跳过 |
| 测试输出 SHA256 | `da09291c175dfaaa9afd85925141c89d436b655c349a72afd50dd4a17e64cb31` |
| 验收脚本 | `vd-cosmos-core/scripts/verify_b2_real.sh`，SHA256 `b59d5bbceba8921087726722b3ab552197bf9003bf8d2f9724ee6e2f216022d6` |
| A～F 完整 stdout / stderr | [offline-A-F-output.txt](evidence/offline-A-F-output.txt)、[offline-A-F-stderr.txt](evidence/offline-A-F-stderr.txt)（stderr 为空） |
| A～F 结果与明细 | [offline-verify/result.json](evidence/offline-verify/result.json)、同目录 A-first.json、A/、C/、E-loop.json |
| 导出 | [offline-export/manifest.json](evidence/offline-export/manifest.json)，一块；可重组核对 source_sha256 |
| 回放来源与源码对应 | [offline-run.json](evidence/offline-run.json)，命令、快照提交、每个本线文件 SHA256、15 次请求、两条日志各一次 |
| 真实配置仅加载 | [real-config-load.json](evidence/real-config-load.json)：接受；源文件不变，未复制、未联网；data_root 不存在时检查已有父目录 |
| SKILL 校验 | [skill-validation.json](evidence/skill-validation.json)：watch/fetch/workflow 三项通过 |
| 输入与范围 | [preflight.json](evidence/preflight.json)、[protected-files-check.json](evidence/protected-files-check.json) |
| 提交前检查 | [prepush-check.json](evidence/prepush-check.json)：凭据命中须为零；本地词表仅告警 |

测试命令：`bash vd-cosmos-core/scripts/run_tests.sh > docs/enhance/batch2.1/evidence/test-output.txt 2>&1`。测试不改根 CI / .importlinter / pyproject.toml；运行时保持标准库。openssl 生成的证书和私钥仅在测试临时目录中，未纳入材料。

A～F 使用单独初始化的临时干净源码快照，快照提交为 `001735ee2a9e33c05a03bc7cfdb85d2078c08865`，不是本仓库交付提交；`offline-run.json` 的逐文件摘要与交付源码核对一致。这样在交付提交之前也实际执行了脚本的“完整 HEAD + 本线工作树干净”检查。源码树记录摘要 `d8d7d0008766dea7585f6a0d50aefbbd84ecbb84caeced0df4392da4903f417e`；提交前另外核对暂存树相等。本批只有 fixture 证据，来源标记为 http-fixture，不能用作真实构建机验收。

结果：A/B/C/E PASS；D 未提供 live 构建而跳过；F 只记录、不设通过条件，目录指纹和详情身份均通过。合成规模为 arm 4 包 / x86 1 包，共两个失败日志，E 本次窗口执行 observe/logs/notify，分析待办恰一条（2 包），日志不重复下载。真实规模的 7 包验收必须在构建机执行，不声称本地已完成。

## A. 抓取层

实现：`core/src/vd_cosmos_core/transport.py`（此处 core 指 vd-cosmos-core）、`http_reader.py`。报告/索引/详情拒绝全部 3xx；日志逐跳检查协议、主机、有效端口及解码规范化目录，最多三跳。总 deadline 贯穿 DNS、连接、TLS、跳转和正文；每次底层 receive 重新缩短等待，空闲 timeout 独立。系统 CA 加可选 ca_file、主机名校验和 CONNECT 代理；只用显式代理配置。固定失败类别，记录每次请求响应证据；中断正文不保存、不进缓存，失败请求仅保存净化后的元数据。主动限长另有 truncated/transfer_complete 标记。

测试均在 `vd-cosmos-core/tests/test_batch21.py`，除特别注明外：

- `Batch21Tests.test_all_document_redirects_refused_before_target_request_and_index_fingerprint`：3xx、同主机登录页、目录指纹/代理页，目标请求数为 0。
- `Batch21Tests.test_log_redirect_port_host_and_path_refused_with_zero_target_requests`：越界端口/主机/路径不发请求。
- `Batch21Tests.test_content_length_chunked_interruptions_no_cache_and_true_timeouts`：长度偏大、chunked 断流、真实空闲超时与总时限。
- `Batch21Tests.test_response_evidence_log_active_truncation_differs_from_incomplete`：完整响应字段、主动截断、断流元数据及缓存不更新。
- `Batch21Tests.test_rule_errors_are_not_swallowed_and_instance_scopes_do_not_mix`：仅吞 FlowError(5)，规则拒绝照常抛出。
- TLS 测试同时覆盖 HTTPS→HTTP 跳转拒绝和目标 0 次请求；原 `test_http_workflow.HTTPTests` 继续覆盖最大跳数、cookie 不保存、显式代理、内容凭据拒绝。

## B. 定型与报告状态

实现：`stability.py`、`versions.py`、`http_reader.py`、`backends.py`、`report.py`、`observation.py`、workflow `api.py`。连续记录独立于 50 条审计历史；所有重置条件落实。页面按全 SHA256 去重；先定型再判断结构/对账，缺头/缺汇总有固定检查项。跨架构 header 只在全部定型后核对。watch 停止条件返回 3；loop 继续低频观察，内容改变记依据变化并重判；404 等待只受预期时长约束。

- `Batch21Tests.test_unsettled_malformed_running_then_terminal_or_settle_deadline`
- `Batch21Tests.test_truncated_structure_to_full_and_missing_summary_settled`
- `Batch21Tests.test_continuous_reset_failure_404_change_config_clock_and_history_bound`
- `Batch21Tests.test_header_only_after_both_settled_and_coverage_projection_pure`
- `Workflow21Tests.test_stopped_loop_reobserves_changed_report_and_detail_failure_does_not_block`
- `Workflow21Tests.test_monitor_404_timeout_live_disk_and_versioned_todo_identity`

## C. 包集合

实现：`baselines.py` 纯函数投影及 `observation.py`。路径/CL/shelve 多重集合，排序后各取 20 条差异且保留总数。重复投影删除自身旧 issue 后重算、不改缓存。覆盖与结果分开；manual_file 不一致停止、即使一致也不满足闸门。预留 request/previous_report/人工接受；本批只生成 manual_file/none。

- `Batch21Tests.test_header_only_after_both_settled_and_coverage_projection_pure`：CL 差 1 不一致，结果仍为失败、重复投影不变。
- `test_http_workflow.HTTPTests.test_missing_expected_package_is_coverage_only_invalid_baseline_is_argument_error`
- `test_real_format.VerifyScriptTests.test_verify_rows_cl_shelve_and_duplicate_replacements_rejected`：独立基线多重集合，重复项不能替代缺失项。
- `test_reports.ReportTests.test_expected_package_set_required_and_extra_packages_rejected`：parse_report 不再产生旧 expected_package_set_missing。

## D. 详情页

实现：`observation.py::detail_state` 与 `HTTPReportReader.detail`。可见构建号核对，最多 20 个候选、选中元素及原因、规则版本、页面摘要和响应。字段凭据命中整项替换“未保留”，不存页面原文。抓取/身份失败和 title 未匹配区分；未知不填旧终态，报告处理独立。详情单独计数，三次一待办、成功清零。

- `Batch21Tests.test_detail_failure_counts_identity_all_candidates_recovery_and_report_failure`
- `Workflow21Tests.test_stopped_loop_reobserves_changed_report_and_detail_failure_does_not_block`：详情 500 不阻断报告和结果拉取。
- `test_http_workflow.HTTPTests.test_detail_session_parameters_never_persist_raw`
- `test_real_format.RealFormatTests.test_own_failed_title_precedes_successful_promotion`

## E. 状态库与 workflow

实现：`state.py`、`journal.py`、`versions.py` 和 `vd-cosmos-workflow/src/vd_cosmos_workflow/api.py`。实例标识和所有读取目录统一到 build_ref 摘要；按构建索引过滤事件、投影仅读取最新观察/日志产物。坏产物重新观察并留待办；日志先重观测，缓存和完成记录绑定版本。下次 tick 仅清理有意图无结果的本线 attempt。SQLite WAL/2 秒忙等、固定错误类别；loop 只在限定条件重试追加，动作不重做，显式 expected-event 不重试。三次轮次锁跳过退出 6；版本化待办、实时磁盘水位。

- `Workflow21Tests.test_wal_reader_error_wrapping_and_other_build_history_not_loaded`：读事务、错误封装、1 万条其它构建事件、SQL 查询计划使用构建索引且投影不读其它构建产物。
- `Workflow21Tests.test_completed_baseline_change_invalidates_and_missing_artifact_recovers`
- `Workflow21Tests.test_logs_refresh_report_and_cache_bound_to_report_and_limit`
- `Workflow21Tests.test_actual_child_crash_after_observe_logs_notify_result_unique_and_cleanup`：子进程在三步动作后真实退出，再恢复结果唯一。
- `Workflow21Tests.test_append_retry_other_build_only_constraint_same_build_and_explicit_no_retry`
- `Workflow21Tests.test_tick_concurrent_other_build_append_retries_without_repeating_action`
- `Workflow21Tests.test_round_contention_three_skips_one_todo_and_real_two_process_ticks`
- `Workflow21Tests.test_three_log_failures_have_one_todo`
- `Workflow21Tests.test_monitor_404_timeout_live_disk_and_versioned_todo_identity`
- 原 `test_http_workflow.WorkflowTests.test_sleep_allows_manual_tick_instance_lock_still_excludes_second_loop` 与 signal 测试继续通过。

## F. 验收脚本

实现：`verify_b2.py`、`verify_b2_real.sh`，B1 共用 `verify.py` 独立基线处理。完整提交、本线干净工作树和 real 主机检查在写产物前执行；每次新数据根，原配置不变。来源记录包含 run_id、起止时间、源码树/脚本/配置/基线摘要、实例、后端、命令和产物摘要。A/B 反例不能被总 verdict 掩盖，E 按本次动作事件、完成状态、待办数量和日志复用判断，F 仅记录环境识别证据。

- `Acceptance21Tests.test_clean_snapshots_repeated_independent_A_to_F_and_unrelated_changes`
- `Acceptance21Tests.test_direct_commit_dirty_source_and_real_loopback_rejected_before_output`
- `Acceptance21Tests.test_saved_page_difference_fails_A`
- `Acceptance21Tests.test_truncated_incomplete_and_html_logs_fail_B`

## G. TLS 及未实现项

`TLS21Tests.test_tls_self_signed_extra_ca_hostname_and_downgrade_refused` 使用 openssl 即时生成证书，真实握手验证自签名拒绝、额外 CA 接受、主机名不符拒绝、CONNECT 代理以及降级跳转不发下一跳。证书只在临时目录，测试输出无私钥。

附录 G 的 1～36 逐项实现/测试映射见 [STATUS.md](../dev_memory/STATUS.md)“第 2.1 批附录 G 落实表”。G#5 的 accept-coverage 人工命令按设计明确留第 3 批，本批只保留模型和闸门限制；G#6 的 request/previous_report 来源按任务留第 4 批。G#16 的 HTTP 前提与 G#18 的配置补齐已按权威设计和 README 记录，不加入未经授权的硬拒绝。其余要求本批落实，无新增待裁决设计问题。

旧构建机 rounds/<数字构建号>/ 不读取、不迁移、不删除。真实服务 F 段识别、7 个失败日志与完整独立基线的构建机验收仍待设计方运行；本地合成 PASS 不代替它。浏览器、P4 写入、分析者/人工裁决和提交协议依后续批次任务实施。
