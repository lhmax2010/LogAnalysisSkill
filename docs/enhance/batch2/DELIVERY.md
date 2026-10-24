# 第 2 批交付与核验索引

本批以 HLD v0.5.3 和设计方 2026-10-24 对 B2-Q01 的答复为准。基点是 `8ca13b3fd37d53af6dbc5c084e976bfc5bc78843`；以下测试在本批未提交工作区运行，源文件摘要见 [tested-source-sha256.json](evidence/tested-source-sha256.json)。实现、证据、HLD 与 STATUS 同批提交。实际交付提交可用 `git log -1 --format=%H -- docs/enhance/dev_memory/STATUS.md` 查询。

未访问真实报告服务、内网或浏览器。HTTP 测试和 A～E 回放只使用 127.0.0.1 标准库服务器；Git 收尾仅普通 push。配置、运行资产、reference-local 和根目录既有修改不入提交；8567 个受保护文件摘要未变。

## 证据入口

| 材料 | 路径 / SHA256 |
|---|---|
| 权威 HLD，保持原件 | [v0.5.3](../vd-cosmos-loganalyzer-hld-v0.5.3.md)；`279a96f2e0b50fc91ff983cc37bc2fc588df18307ea07958463f5cf565237b65` |
| 完整测试输出：100 项，三条 import 约束 | [test-output.txt](evidence/test-output.txt)；`60be2e43bcf43c22e6889835222b30b5af237d73c412d7deeea67e2fc971b57b` |
| 构建机验收脚本 | [verify_b2_real.sh](../../../vd-cosmos-core/scripts/verify_b2_real.sh)；`576e418bf19ca147279155ad8b64f834562445a829ebef4b603a0098721526b2` |
| 离线 A～E stdout | [offline-A-E-output.txt](evidence/offline-A-E-output.txt)；`c22dbbcb870cd48fadad773aea440a4be6a06933f1df6b1881fd9f33dd3d381c` |
| 离线 A～E 结果 | [result.json](evidence/offline-verify/result.json)；`daeb5be9bb662c94b2835cf6c92bca549a9681f5fed01a8dbc9c68208fb2c0af` |
| 原命令、请求路径、源文件不变、仅两次日志请求 | [offline-A-E-run.json](evidence/offline-A-E-run.json)；stderr 为 [空文件](evidence/offline-A-E-stderr.txt) |
| 1 块导出及逐块摘要 | [manifest.json](evidence/offline-export/manifest.json)、[part-00001.txt](evidence/offline-export/part-00001.txt) |
| 真实配置本地加载 | [real-config-load.json](evidence/real-config-load.json)：缺 fetch 段使用默认值，data_root 不存在时向上查文件系统，源文件未变、未复制 |
| 开工摘要、B2-Q01 关闭记录 | [preflight.json](evidence/preflight.json)、[STATUS.md](../dev_memory/STATUS.md) |
| 范围保护、SKILL 验证 | [protected-files-check.json](evidence/protected-files-check.json)、[skill-validation.json](evidence/skill-validation.json) |

离线证据中的绝对路径指向本机保留的 data_root，完整 verification 文件已逐字复制到本目录供审阅；路径没有伪改为部署路径。回放是 arm 4 / x86 2 的合成规模，失败日志 1+1，不宣称真实 2244/43、6/1 已在本机验收。真实规模由脚本 real 模式固定要求。A/C 的明细分别在 [A](evidence/offline-verify/A) 和 [C](evidence/offline-verify/C)，包括 observe/packages/inputs/groups；摘要不含分组成员清单。

## 1. 报告状态拆分

实现：[report.py](../../../vd-cosmos-core/src/vd_cosmos_core/report.py)、[observation.py](../../../vd-cosmos-core/src/vd_cosmos_core/observation.py)、[baselines.py](../../../vd-cosmos-core/src/vd_cosmos_core/baselines.py)。稳定的计数、重复键、分类交叉、架构不符单列“对账失败”；未稳定仍“部分”；结构未知优先。package_coverage 独立汇总为不一致/未核/一致，缺基线不再破坏完整性，非法基线报 2。对账待办保留最多 20 行原文与行号，覆盖待办缺少/多出各 20 条；不为正常等待生成待办。

对应 [test_http_workflow.py](../../../vd-cosmos-core/tests/test_http_workflow.py)：

- `HTTPTests.test_changing_then_stable_inconsistent_report`
- `HTTPTests.test_missing_expected_package_is_coverage_only_invalid_baseline_is_argument_error`
- `HTTPTests.test_aggregate_all_priority_branches`

既有 [test_reports.py](../../../vd-cosmos-core/tests/test_reports.py) 的 duplicate_row、category_intersection、closed_build_status_set、export_nonzero、header_mismatch 等反例继续通过。终态闸门与只读结果拉取条件分别保留。

## 2. 验收口径与导出大小

实现：[verify.py](../../../vd-cosmos-core/src/vd_cosmos_core/verify.py)。links 只比 arm 编译失败包多重集合；x86 只比失败数量自基线，覆盖为未核；arm 由独立 rows 比较路径/CL/shelve，必须覆盖一致。结果只导出计数、状态、比对摘要与差异前 20 条、前 15 个签名及成员数；完整明细留本地。B1 脚本复用相同 evaluate 逻辑。修正 real_format/links.txt 为 arm-only。

对应 [test_real_format.py](../../../vd-cosmos-core/tests/test_real_format.py) 的 `VerifyScriptTests.test_verify_pass_export_reassembly_and_source_immutability`、`test_verify_rows_cl_shelve_and_duplicate_replacements_rejected`、`test_verify_links_multiplicity_and_version_checked`、`test_difference_list_is_limited_and_retains_total_count`，以及 B2 的 `test_b2_script_A_to_E_and_summary_size`。独立回放实际导出 1 块；不是对任意超长错误文本作两块的强制保证。

## 3. HTTP ReportReader

实现：[http_reader.py](../../../vd-cosmos-core/src/vd_cosmos_core/http_reader.py)、[config.py](../../../vd-cosmos-core/src/vd_cosmos_core/config.py)、[read_ops.py](../../../vd-cosmos-core/src/vd_cosmos_core/read_ops.py)、watch/fetch 的公开 api.py 与 CLI。默认 TLS 校验及附加 CA；只用配置代理，后缀与字面 IP 网段直连；无 CookieHandler；限制重定向、超时与大小。报告凭据检查在落盘前，详情原文只在内存判读，共用 detail_state；日志越界拒绝、限并发、截断、命中凭据标禁止导出、校验缓存后跳过。HTTP 模式无需 manifest。

`HTTPTests` 逐项证据：

- `test_http_states_no_cache_headers_coverage_and_detail_evidence`
- `test_404_requires_readable_bucket_index`
- `test_500_timeout_proxy_page_size_limit_and_cross_host_redirect`
- `test_same_host_redirect_limit_and_no_cookie_storage_or_return`
- `test_detail_session_parameters_never_persist_raw`
- `test_page_credentials_refused_without_file_and_with_todo`
- `test_logs_boundary_truncation_credential_flag_cache_and_concurrency`
- `test_log_redirect_refused_tampered_cache_redownloaded_and_export_error_included`
- `test_proxy_config_only_and_tls_defaults`
- `test_fetch_defaults_template_validation_and_real_cli`
- `test_packages_error_exit_and_original_detail_title`

真实配置加载只检查接受性和本地文件系统，没有构造 HTTPTransport、没有访问配置中的任何地址、没有创建其 data_root。

## 4. 只读 workflow 与 B2-Q01

新增 [vd-cosmos-workflow](../../../vd-cosmos-workflow/SKILL.md)，实现 tick/loop/status/inbox，仅调用 watch/fetch 公开读取函数。意图先落库；产物原子落盘后提交唯一结果；动作失败保留审计。通知待办先写、推进结果后写，崩溃重做时去重，避免已完成但缺通知。观察失败可重试，四种人工处理条件退出 3；到“结果已拉取”即结束，不要求执行已结束。

实例 flock 全生命周期持有，轮次 flock 和写事务不跨睡眠；手工命令没有实例锁。信号只请求结束，tick 完成后干净退出，内核释放锁。B2-Q01 来源已原样写入 STATUS 人工裁决，HLD 未改。

`WorkflowTests`：

- `test_workflow_each_stop_condition_and_three_failures_todo`
- `test_crash_after_intent_redoes_action_and_has_one_result`
- `test_notification_result_failure_recovers_without_duplicate_or_missing_todo`
- `test_views_do_not_append_and_stale_event_and_duplicate_result_rejected`
- `test_sleep_allows_manual_tick_instance_lock_still_excludes_second_loop`
- `test_sigterm_and_sigint_clean_exit_release_instance_lock`

## 5. 离线与依赖约束

[http_helpers.py](../../../vd-cosmos-core/tests/http_helpers.py) 用 ThreadingHTTPServer 只监听 127.0.0.1，real_format 提供合成内容。HTTP 单测拒绝非 loopback DNS；子进程使用同一 loopback 配置。没有启动浏览器、访问真实服务或执行 P4。运行源代码只用 Python 3.10 标准库。自有脚本 [run_tests.sh](../../../vd-cosmos-core/scripts/run_tests.sh) 跑语法/标准库检查及本线三条 import-linter 约束：workflow → watch/fetch → core；watch/fetch 独立；workflow 不依赖写后端。根 CI、根 import 配置与其它 skill 未改。

## 6. 构建机验收 A～E

[verify_b2_real.sh](../../../vd-cosmos-core/scripts/verify_b2_real.sh) 首参数逐字核对完整 HEAD，错误即 6，尚未加载配置或创建输出。实现位于 [verify_b2.py](../../../vd-cosmos-core/src/vd_cosmos_core/verify_b2.py)。A 两次 HTTP 抓取与保存页摘要比对；B 下载失败日志；C 保存页面按修正口径核对；D 可选 live 构建只观察，结果不设 PASS；E loop 最多四次、核对通知与日志复用。脚本只写 data_root，结果经统一导出流程。

测试名：`WorkflowTests.test_b2_script_A_to_E_and_summary_size` 和 `test_b2_wrong_commit_stops_before_loading_or_writing`。独立回放 A/B/C/E 均 PASS；A 的 HTTP 与保存页摘要相同；D 为合成未发布报告并记录详情状态；E 达到结果已拉取、只有一个“2 个失败包待分析”待办，日志摘要与 B 相同且没有重新下载。

构建机使用设计方审核后的本批完整提交号，不能把当前 HEAD 动态填作预期值：

```bash
bash --noprofile --norc vd-cosmos-core/scripts/verify_b2_real.sh EXPECTED_COMMIT \
  --config CONFIG --build-id N --saved-dir SAVED_DIRECTORY \
  --rows ROWS --links LINKS --live-build-id M
```

## 留待下一批 / 实机验证

无待裁决的本批设计问题。真实网络、代理/CA 部署环境与进行中详情页还需构建机 A～E 证据；Export Error 真实表头仍待样本，未知结构继续拒绝。第 3 批分析与人工处置、其它架构独立包集合来源以及后续浏览器/P4/提交协议均未实现。真实日志数 6/1 和 2244/43 包不能由本次小规模回放代替。
