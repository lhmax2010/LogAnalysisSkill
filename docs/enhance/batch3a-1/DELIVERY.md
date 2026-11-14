# 第 3a-1 批交付与核对索引

日期：2026-11-03。设计依据：`docs/enhance/vd-cosmos-loganalyzer-hld-v0.9.5.md` 正文及设计方对 **B3a1-Q01** 的答复。设计文档未修改；旧版本保留。

HLD 已用 `mv` 归位并单独普通推送，提交 `3616628442cd037e7c519eb2efa4c9128d521a17`；原件与仓库文件 SHA256 均为 `5989620912fcb86cab5b399e3a66d868616092570916a6e38433ece659f17f63`。Downloads 中该原件已不存在。开工基点为 `b6b7c094c1ed4fcd6b0c5d9b919a1bfb300636cd`。

本段只完成读取侧、输入清单、P4 只读访问、源码快照和四种人工命令。未执行真实服务访问、真实 P4、浏览器或构建提交。所有新测试使用生成的页面、仓库假 p4、回环 HTTP/TLS、PTY 或受控替身。附录 I 只作为合成夹具的结构依据，不能把这些测试称为构建机真实验收。

## 证据

- `evidence/test-output.txt`：从仓库根运行 `bash vd-cosmos-core/scripts/run_tests.sh` 的完整 stdout/stderr。
- `evidence/validation.json`：上述输出 SHA256、测试数、import 约束、实现文件摘要与测试方法索引。
- `evidence/config-load-check.json`：只加载 Downloads 的真实配置，不联网、不创建其 data_root、不修改或移动原件；只记录摘要与结果，不记录配置值。
- `evidence/skill-validation.txt`：两个新 SKILL 的校验输出。
- `evidence/prepush-check.json`：本批提交文件的凭据预检，只记命中索引，不记录原文。
- `evidence/preflight.json`、`evidence/baseline-test-output.txt`：保留初次开工和提出 B3a1-Q01 时的历史现场；基线 125 项通过，不代表本段最终实现。

以下测试名称可在完整输出中逐字搜索，也可查 `validation.json` 的路径和行号。测试的主要位置为 `vd-cosmos-core/tests/test_batch3a1.py` 与 `test_batch3a1_extra.py`，原读取侧测试一并回归。

## A. 读取侧加固

实现：core 的 `stability.py`、`observation.py`、`http_reader.py`、`backends.py`、`transport.py`、`receipts.py`、`journal.py`、`state.py`、`versions.py`、`network_proof.py`、`verify_b2.py`，以及 workflow 的 `api.py`。watch/fetch 的现有入口通过公共库获得上述行为。

| HLD | 实现与产物 | 对应测试 |
|---|---|---|
| §5.4.3、§8.1.1 | 连续内容记录与 `terminal_epoch` / `unknown_since` 持久化；窗口用 max 起点，至少两次窗口内观察；运行/排队不走时长路径。人工窗口只因任一期望架构摘要变化或撤回失效 | `test_terminal_epoch_unknown_since_restart_and_running_never_elapsed`；`test_manual_window_survives_running_failure_and_expires_on_digest_or_withdraw` |
| §5.4.3、§9.2、B3a1-Q01 | elapsed 定型后重取的完整日志为最终日志，回执终态依据为空，闸门关闭；首次可信终态或运行使当前完成失效；重新取到相同摘要保留结果，变化则输入过期。日志按内容与回执依据保存版本，旧产物不被覆盖 | `test_elapsed_final_gate_closed_terminal_invalidates_revalidation_result_identity`；`test_elapsed_then_running_rejects_old_snapshot_and_changed_log_expires_result` |
| §5.4.11 | 唯一完整 class 词 `build-header`；排除推广块；头部内唯一状态；自身链接按页面 URL 解析并核对主机/构建路径；strong / weak / identity_mismatch；旧 header_rule 拒绝加载 | `test_header_identity_three_levels_promotion_class_tokens_and_resolved_links` |
| §5.4.1 | 实际日志下载路径拒绝认证/代理 HTML；严格 chunk、trailer、CRLF；无长度且非 chunked 的日志只能临时；保留响应对端、本端 IP；变量页 HTTPS、无重定向 | `test_wire_strict_trailers_close_delimiting_and_production_not_a_log`；原 `test_batch21.py`、`test_http_workflow.py` 的 TLS/重定向/中断测试 |
| §5.4.12、§9.6 | 连续未发布计时、内容连续变化计时、running_but_stable 分开；等定型不会按旧轮询次数误报；详情失败只由 detail.json 计数；完成后低频观察，可信终态观察期限持久化，elapsed 继续观察 | `test_three_stall_conditions_without_old_poll_count_false_alarm`；原 `test_batch21.py` 的待办与恢复测试 |
| §9.2 | 完成状态重新核验日志存在、大小、摘要、当前定型与终态依据；评估摘要包含日志上限、解析源码摘要；版本常量与默认 User-Agent 共用单一来源 | `test_completed_log_tamper_invalidates_and_max_limit_changes_evaluation`；B3a1-Q01 两项测试 |
| §9.3 | SQLite 读取错误按真实原因分类；build_key 统一为 build_ref 摘要；任何跳过创建 contention_id，不计数的事件争用短重试，loop_starved 提示；计数段不被不计数跳过清零，成功后清零；abandon/后继绑定结束旧 loop | `test_loop_uncounted_and_counted_segments_starvation_and_fatal_errors`；`test_manual_entrypoints_non_tty_and_closed_database_are_classified`；原并发/睡眠中手工 tick 测试 |
| §11 | 解析地址排除本机/回环/映射地址；报告与详情要求直连，记录实际 peer/local IP；F 参与 real 结论；时间预算包含 settle_s | `test_resolved_local_and_mapped_addresses_are_rejected_without_connection`；原构建机验收脚本本地回放测试 |

“已有结果”接口是 `task_input_digest(final_log_sha256, snapshot_manifest_sha256, segment_manifest_sha256, rules_version)` 与 `accepted_result_state(result, package, input_digest)`；本段没有结果接收器，也没有创建任何分析授权事件。

## B. 本轮输入清单

实现：`vd-cosmos-core/src/vd_cosmos_core/build_inputs.py`，通过 `python3 vd-cosmos-fetch/scripts/run.py base-list --config <配置> --backend fixture|real ...` 调用。

- 变量页模板恰好含一个 `{build_id}`，路径固定为 `/build/{build_id}/variables`，HTTPS 且与详情同主机。身份复用 A 的头部规则。
- 只抽取五个白名单变量。同名重复拒绝；其它变量不写入产物、错误或证据。整页只在内存处理。仓库 URL 去掉用户信息后检查；清单命中凭据模式就停止。
- `PACKAGE_LIST`、`SHELVE_LIST` 与受核验的三个报告头变量存入 `rounds/<build_key>/inputs/build-lists/`，manifest 记录各摘要，后续改变或篡改拒绝。
- 配对只去掉整段分支标记、合并重复斜杠；取文件保留原始路径。普通行按路径/CL，shelve 按包键/路径/SCL；重复、歧义、缺项拒绝，多出的 base 包单独记录。
- `bind-base-list` 可同时给两份清单，或只给 base；后一种明确记录未取得原始 shelve 清单。

测试：`test_appendix_i_2245_base_545_shelve_and_credential_variable_never_written`、`test_pairing_exact_segments_duplicate_cross_branch_and_shelve_tuple_mismatch`、`test_variables_template_https_exact_placeholder_and_credential_block`、`test_input_binding_and_inbox_done_are_human_events_and_immutable`。大夹具生成 2245 / 545 行、报告覆盖 2244 行；递归扫描数据根目录，断言额外凭据变量的名称和值均未落盘。

## C. P4 只读访问层

实现：`vd-cosmos-core/src/vd_cosmos_core/p4.py`；可执行假后端：`vd-cosmos-core/fixtures/p4/fake_p4.py`。

- 所有调用固定 `-G -p <port> -u <user> -c <不存在的 client>`。环境为白名单；P4CONFIG 使用不存在的唯一文件名并检查父目录，P4ENVIRO 为 `/dev/null`，P4TICKETS 固定。不读取用户 P4 配置内容。
- 快照前登录期限与 info 的 userName/serverAddress/clientName/clientRoot 核对；快照后再查期限并提示余量。覆盖票据模式不生成登录命令，不执行 login/logout/set/client 写操作。
- 先看信号、超时与 marshal 流完整性，再按版本 code0 表分类，退出码只校验一致性。默认四个编号与 HLD 附录 I 的 2026.1 实测一致。
- 已提交 CL 或没有 shelved 标记的完整描述视为历史输入不可还原，即使描述含文件列表；空流/残缺流不能冒充历史输入消失。历史不可还原的相同输入快照可复用；未分类错误连续计数落库，默认第三次后停止重做，由 inbox done 恢复。
- 路径转义 @/#/%/*，禁止传入递归省略号；列目录用代码生成的单层通配。清单版本上的 delete / move-delete 记录视为文件不存在。

测试：`test_fake_p4_context_protocol_real_error_shapes_signal_partial_unknown_and_forbidden`、`test_info_mismatch_ticket_short_and_override_does_not_offer_login`、`test_persisted_unknown_retry_counter_and_manual_done_reset`、`test_confirm_input_checks_current_describe_and_unknown_retry_gate_recovers`、`test_deleted_base_is_absent_for_shelve_add_and_interval_uses_earliest_cl`。假 p4 真实启动子进程并写 marshal，包括被杀、残缺、未知 code0、未登录、已提交 CL 仍带文件行等情况。

## D. 源码快照

新 skill：`vd-fix-analyze`，本段入口为 `snapshot`。文件产物位于 `rounds/<build_key>/snapshots/<attempt>/`；轮次报告为 `rounds/<build_key>/reports/source-snapshots.md`。

- §6.1.1/1a 的四类路径、日志中 BUILDROOT / 大小写前缀推断、包根边界、最后两级目录加文件名回退、实际压缩包判据、文件数/单文件/总量限制、symlink 仅记目标均落实。
- 普通行按报告 CL；shelve 从请求 base 清单取本轮版本。来源依据与源码行核对分别记录，源码行相同不升级来源。无清单时 lower 取 SCL 与提供的 `known_sync_cls` 最小值，upper 取 Last-Modified 或首次失败观察时间加余量，并转成 P4 服务器时区；两端相同仍只记区间内一致。
- 同分支按 edit/add/delete/move 成对/其它动作处理；跨包文件只记录；跨分支以相对路径标记受影响的 base 文件，不跨 depot 比较 rev 或合并。
- edit 的基础版本落后时三份输入均 print -k，代码固定“本轮、祖先、shelve”顺序调用 git merge-file；0、1～127、其余失败分别处理，非 0 不接收结果；合并关键字不展开。
- shelveUpdate 按服务器时区与 Start Time 分钟比较；只有绑定当前摘要的 confirm-input 可以放行此近似判定；内容 MD5 对 describe digest；前后 describe 改变则本次失败。
- Clang 源码行做精确比较：ANSI、匹配的可选行号栏、CR、制表符、UTF-8/非法字节显示；不压缩空白。主错误不可靠、行不一致/无法核对等均仅诊断。
- 合并及不能合并的通知写 stderr、manifest、轮次报告、提示类 inbox；同一输入摘要不重复通知。任务包中的工具证据段由 `task_notice_interface` 留给 3a-2。
- 快照入口只接受本包且仍对应当前观察的最终日志回执；报告/终态变化后的旧回执拒绝。

测试：`test_shelve_overlay_merge_conflict_advanced_add_delete_move_and_cross_branch`、`test_move_pair_other_actions_cross_package_and_mid_snapshot_mutation`、`test_keywords_merge_keeps_unexpanded_input_and_corrupt_digest_fails`、`test_history_time_confirm_digest_keyword_and_exact_nonascii_line_rules`、`test_paths_limits_symlink_and_merge_tool_error`、`test_archive_requires_actual_source_and_interval_stays_diagnostic`、`test_deleted_base_is_absent_for_shelve_add_and_interval_uses_earliest_cl`。附录 I 三个 shelve 样本的 2 / 1 / 32 个 edit、同分支、无跨包、无实际压缩包由 `test_appendix_i_three_shelve_samples_2_1_32_edits_overlay_without_archive` 合成验证，结果均原样叠加。

## E. 本段人工命令

新 skill：`vd-fix-register`；四个命令全部登记为人工裁决类，非控制终端退出 2，使用轮次锁和期望事件号。统一入口、参数和 JSON 回执见该目录 SKILL.md。

| 命令 | 限定 |
|---|---|
| confirm-terminal | 按全部期望架构绑定摘要，未发布用明确标记；可信运行/排队必须 override-running、回显并输入构建号；withdraw 留痕，点击后只记撤回事实 |
| confirm-input | 精确包键、当前 describe 摘要；不接受过期摘要 |
| bind-base-list | 两份或仅 base 两种退路、同样唯一对应与不可变核验 |
| inbox done | 关闭指定待办；未分类 P4 错误按包恢复连续计数 |

测试：`test_confirm_terminal_pty_override_echoes_build_and_records_withdraw`（真实 PTY 正反路径）、`test_manual_entrypoints_non_tty_and_closed_database_are_classified`、`test_confirm_input_checks_current_describe_and_unknown_retry_gate_recovers`、`test_input_binding_and_inbox_done_are_human_events_and_immutable`。人工确认读写使用分开的 `/dev/tty` 句柄，stdout 保持一个 JSON 对象。

## 新配置与迁移

所有新增项均有默认值，见 `vd-cosmos-core/config.sample.json` 与 `src/vd_cosmos_core/defaults.py`。加载旧真实配置的 PASS 只证明本地 schema / 路径 / 文件系统检查，不证明占位连接参数可用于真实 P4。

| 配置 | 默认/作用 |
|---|---|
| cosmos.status_source.header_rule | unique-build-header-with-own-link；显式旧规则拒绝，提示迁移 |
| cosmos.variables_url_template | 从详情主机推导 HTTPS `/build/{build_id}/variables`；无详情来源需显式配置才可读取 |
| cosmos.variables_whitelist | PACKAGE_LIST、SHELVE_LIST、BASE_REPOS、BUILD_CONF、PRODUCT_REPOS，仅这五项 |
| cosmos.branch_markers | `[INT]`、`[FET]`、`[COSMOS]`，整段匹配 |
| poll.arch_lag_s / post_terminal_watch_s / retry_after_event_s | 14400 / 7200 / 5 秒 |
| loop.max_uncounted_skip_s | 1800 秒 |
| p4.port / user / expected_server_address | example.invalid:1666 / configure-user / example.invalid:1666；构建机须填写自身值 |
| p4.no_client_name / unknown_client_marker / read_config_name | vd-cosmos-noclient / *unknown* / 每个适配器生成不存在的唯一名 |
| p4.tickets_file / executable / output_protocol / version | 用户默认票据路径 / p4 / -G / 2026.1；fixture 强制仓库假可执行文件 |
| p4.code0_table | 2026.1 四项实测编号、severity 与退出码关系；版本改变需重新录制 |
| p4.min_ticket_minutes / unclassified_retry_limit / timeout_s | 60 分钟 / 3 次 / 120 秒 |
| snapshot.merge_tool / merge_timeout_s / clock_margin_s | git-merge-file / 60 秒 / 300 秒；不接受任意合并命令 |
| analyzer.snapshot_max_files / snapshot_max_file_bytes / snapshot_max_total_bytes | 20 个错误文件 / 2097152 字节 / 20971520 字节；spec/包根脚本另计入总量 |

## 附录 H、J～N 的 3a 条目分段落实

以 v0.9.5 正文最终规则为准。例如 J-7 的旧降级方式已由 K/L 的合并规则取代；K-7 的旧非 ASCII 口径已由 L-5 取代。

| 附录 | 本段落实 | 后续段 |
|---|---|---|
| H | 1～6、10～25、28、29：见 A～D 及回归测试 | 7 隔离、8 诊断族/定性、27 已有分析器 venv 依赖锁：3a-2；8 人工定性命令、9 准确性：3a-3。26/30 是 3b |
| J | 1～8、13～19、22；21 的覆盖票据禁止登录提示和假 p4 失效部分 | 9 族表、10 位置模型、12 任务包防泄漏、20 隔离：3a-2；10 裁决、11/12/21 完整准确性验收：3a-3；23 是 3b |
| K | 1～8、13、14、17；11 的覆盖票据处理 | 9/12 诊断族与隔离：3a-2；10 分段防泄漏由 3a-2/3a-3 接续；11 实验脚本：3a-3；15 是 3b |
| L | 1～5、7～10 | 6 分段清单/防泄漏：3a-2/3a-3；11 诊断族：3a-2；15 是 3b |
| M | 1～4、8～10；5 的包+输入摘要判断函数；13 的持久化重试计数 | 5 任务包/结果接收、6 分段、13 诊断族版本：3a-2；7/12 准确性验收：3a-3；11 属开工前侦察 |
| N | 1：统一 unknown_since 设置与持久化 | 无 |

未标 3a 的文档/种子修订不在本段重新修改。

## 3a-2 / 3a-3 接续接口与保留条件

- 3a-2 接 `create_snapshot` 的 manifest（来源、行核对、edits_eligible、只诊断模式、内容摘要）、`task_notice_interface`、包键和任务输入摘要；生成任务包后接收器仍须拒绝不可靠辅助文件的 edits。当前 `snapshot` 不调用分析器，不生成任务包，不接收分析结果。
- 3a-2 任务分段、ClineSR 隔离、诊断族、已有工具适配/venv 锁；3a-3 其它人工命令、处置账本、准确性脚本均未开工。
- 旧轮次 loop 的后继绑定判断接收绑定事件中的 `previous_build=<旧 build_key>`；正式提交/绑定流程留后续批次，不伪造绑定。
- §14.14 的 shelve 包实际同步方式仍待构建机证据，按设计保留“请求 base（待确认）”与“已合并”的来源标注，不把离线测试当作该问题结清。
- 当前无新增待裁定的阻塞项；B3a1-Q01 已闭合。真实配置未入库，真实 P4/网络验收留构建机按设计执行。完整测试运行环境版本见输出开头；Python 3.10 兼容性由语法/导入检查覆盖，本机实际解释器版本不冒称 3.10。


## 更正记录（2026-11-14，第 3a-1.1 批 Checkpoint A）

保留上文作为 c25babac 的历史交付记录。附录 O #4 指出的“3 个 shelve 样本均原样叠加”结论不成立：旧测试用虚构的早期 shelveUpdate，不能证明构建 19091860 的历史输入。附录 I 的 AT-HUB / aria-engine 最后 shelve 时间为 2026-09-28 17:47，plusplayer 为 2026-10-23 20:28，晚于报告开始 2026-10-22 13:26 +0900。新回归按这三个时间线构造：前两个可原样叠加；plusplayer 未确认或确认旧摘要时仅诊断，确认当前 shelve 描述摘要后才原样叠加。具体修改、测试与证据见 `docs/enhance/batch3a-1.1/DELIVERY.md`。

旧“请求 base（待确认）”标签在冻结 HLD v0.9.18 中已被“版本确定（base 清单）”及两类 basis 取代；旧 Python 3.12.3 测试通过不等于 Python 3.10 运行通过。这两项的本批核验同见上述交付记录，不追改原测试输出。
