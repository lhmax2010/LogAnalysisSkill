# 第 1.1 批交付与证据索引

依据 HLD v0.5.2、Downloads 中第 1.1 批任务以及 B1.1-Q01 裁定。范围仅为既有本线读取侧修复、离线验收脚本和本线文档；未访问内网、浏览器或 P4。完整真实报告仍待构建机执行脚本验证。

## 输入归位及设计方裁定

五份输入的来源文件名与复制后摘要见 `evidence/file-placement.json`；Downloads 原件未改动。HLD 复制原件 SHA256 `7a054e9a7e0bbcec77177c31e58df5ddefb3b177d6aace41e25a474b2a897916`，仅第 571 行追加指定 HTML 豁免注释后为 `255746d16ac88b9c7c4f429575f1b493b6da85295c9307ae9b5b14d91509f830`。逐字节校验及授权记录见 `evidence/hld-comment-exemption.json`。原始预检拦截是历史记录 `evidence/prepush-input-check.json`，最终提交检查见 `evidence/prepush-final.json`。

## 逐项核验

| 任务 | 实现及对应文件 | 主要测试（test_real_format.py，另注明者除外） |
|---|---|---|
| 1 汇总表 | report.py 的 count_label 去 Packages 后缀；config.sample.json 使用真实标题前缀。Export 标题仍待首次真实出现核实。 | test_real_format_complete_summary_suffix_and_unquoted_link；test_summary_case_whitespace_and_counts_still_reconcile |
| 2 真实格式夹具 | Document 处理省略的 p 结束标签；fixtures/real_format 保留真实头部与汇总布局，补完小规模明细；minimal 原报告保留，新增独立配置。 | test_nested_paragraph_headers_do_not_merge；test_supplied_head120_snippets_never_count_as_complete；既有 test_reports.py 全部保留 |
| 3 执行状态与配置 | backends.py 只认首个 title 状态元素；保存子结果、行号、顺序、摘要；新配置结构校验并拒绝旧 complete_markers。 | test_own_failed_title_precedes_successful_promotion；test_running_queued_and_all_terminal_words；test_unknown_or_absent_title_never_falls_through_or_uses_text；test_configured_regex_does_not_select_a_later_status；test_new_status_schema_accepts_and_rejects_malformed_old_or_overlap |
| 4 其它扩展错误格式 | models/report 保留消息与标记；groups 禁止其被确定阻塞覆盖，要求人工确认；watch 写待办，列数和路径错误仍结构未知。 | test_other_message_is_preserved_complete_manual_only_and_todo；test_mixed_known_and_other_messages_require_both_covered；test_same_signature_other_format_cannot_inherit_standard_blocker；test_other_format_does_not_mask_bad_column_count_or_path；test_unknown_format_todo_is_written_by_watch |
| 5 验收脚本 | scripts/verify_b1_real.sh → verify_b1_real.py → src/vd_cosmos_core/verify.py。源路径全参数化、复制到专用 data_root 新目录；独立解析 rows/links，Counter 多重集合比对；结果经已有 export 分块。 | VerifyScriptTests：test_verify_pass_export_reassembly_and_source_immutability；test_verify_wrong_commit_stops_before_any_output_directory；test_verify_rows_cl_shelve_and_duplicate_replacements_rejected；test_verify_links_multiplicity_and_version_checked；test_verify_unknown_execution_and_header_mismatch_fail；test_verify_real_counts_cannot_use_fixture_override；test_verify_credentials_block_copy_and_never_echo_content；test_difference_list_is_limited_and_retains_total_count |
| 6 设计依据及真实片段进分支 | docs/enhance/vd-cosmos-loganalyzer-hld-v0.5.2.md、batch1/real-snippets 两份。v0.2 保留；未跟踪 v0.5/v0.5.1 按指令删除。 | 输入摘要与 HLD 单行差异证据；真实片段只验证标题/汇总可读且不会误判完整 |

## 完整测试

命令：`bash vd-cosmos-core/scripts/run_tests.sh`。Python 3.10.12，78 项测试通过；两条本线 import 约束通过，标准库及 Python 3.10 语法检查通过。完整 stdout/stderr：`evidence/test-output.txt`。

SHA256：`cc0d8ee5349068635e8c44a8f8153d58d7891f1e9885911f2d8c4d7c27eabacd`。

首次开发运行发现旧测试迁移时的字符串引号错误，已修复；上述完整运行包含全部既有和新增测试，无跳过。

## 构建机运行配置本地加载

`evidence/real-config-load.json`：Downloads 中真实 config.json 通过新加载器，退出码 0。data_root 在本机不存在；向上四层找到现有父目录，通过原有文件系统检查（类型 ext2/ext3），未创建 data_root、未放宽校验。配置未复制、未记录其字段值、未联网，原件摘要不变。

## 离线验收脚本回放

脚本：`vd-cosmos-core/scripts/verify_b1_real.sh`，SHA256 `1182226b1e6331ba456da2f9bb835ece5e0aa419c656f2b6228beb7bc1f87e1b`。构建机命令与全部参数见 core/README.md。脚本实现的 Python 模块摘要同时见 `evidence/source-sha256.json`。

独立回放使用 real_format 小规模夹具，结论 PASS：arm 4/1/0/2/1，x86 2/1/0/0/1；两架构完整、结果失败、header 一致、执行已结束/failed；rows 与 links 多重集合完全相等；其它格式消息 1 条，保留待办及人工确认标记。

- 原始终端输出（先 HEAD、再 JSON 分块清单）：`evidence/offline-verify-console.txt`。
- 已导出结果的逐字节副本：`evidence/offline-verify/result.json`。
- 分块清单与原块：`evidence/offline-verify/export/manifest.json`、同目录 part 文件。
- 完整解析与临时 manifest 副本：`evidence/offline-verify/` 下 observe/packages/inputs/groups/manifest.json。

这次开发回放打印的 HEAD 为前一提交 d93987c，执行的是本次未提交工作树；不能把它称作该旧提交的实现结果。本次被测试源码的完整摘要见 source-sha256.json，与本次交付源码逐项核对。构建机正式运行时必须传入本批最终、经审核的完整提交号。

## 挂账及范围保护

- 完整真实报告未在开发机提供，真实 2244/43 计数与独立基线验收仍待构建机运行；head120 片段不是完整验收证据。
- x86 期望包集合明确标“自基线，未独立核验”；只有失败清单参与独立 links.txt 比对。arm 包名来自报告，路径/CL/shelve 来自独立基线。
- 两份相同副本模拟稳定性，不证明源站实际相隔轮询时间抓取一致。
- Export 非零页面的真实标题与结构待首次出现核实。
- 对账失败仍记“部分”，保持安全拒绝；第 2 批前裁定是否新增状态，本批不改。
- 本批未实现网络访问、日志下载、真实浏览器、P4 或提交协议。其它根目录文件的既有改动未动，范围保护证据见 evidence/protected-files.json。
