# 第 3a-1.1 批 Checkpoint A 交付与证据

设计：HLD v0.9.18（冻结）；基线 `1b090b17b4029f3cccf3e2c1447b253b4a12c11d`。设计方 Claude，FatTank 批准。仅 A1–A3：读取/快照修复、Python 3.10 运行兼容与构建机只读验收脚本；不实施 §8.8 / §8.9，不使用浏览器、真实 Cosmos 或真实 P4。离线测试使用回环 HTTP/TLS、假 p4 和进程隔离；开发依赖仅安装在忽略的 `.devtools/` 两个 venv。

## 附录 O 对照

下表 `core/` = `vd-cosmos-core/`，`analyze/` = `vd-fix-analyze/`。测试函数均在 `core/tests/`；新函数默认位于 `test_batch3a11.py`。

| 附录 O # | 修改与依据 | 文件 | 测试 |
|---|---|---|---|
| 1 | 接受真实 @SCL 与同义 @=SCL，记录 notation；规模夹具用真实写法 | core/src/vd_cosmos_core/build_inputs.py；test_batch3a1.py | test_real_shelve_notation_synonym_and_root_validation；Inputs3a1Tests.test_appendix_i_2245_base_545_shelve_and_credential_variable_never_written |
| 2 | 可配置去掉每行一层时间前缀；保留其后空白；按冻结 §6.1 的相邻三行、归属受限判断、内容先于列号、字节制表符和行尾空白规则核对 | analyze/src/vd_fix_analyze/source_check.py、snapshot.py；core/src/vd_cosmos_core/defaults.py；config.sample.json | SourceLineTests 全部 6 项，含带/不带行号栏、note/半行/孤立诊断/同位置不同源码、非 ASCII/制表符 |
| 3 | 相对路径单独记无法定位（相对路径），不用作外部依赖证据 | analyze/.../snapshot.py | test_relative_paths_not_external_dependencies |
| 4 | 附录 I 真实 CL、base CL、2/1/32 文件数与真实时间线；plusplayer 当前摘要确认才放行；原交付只追加更正 | core/tests/test_batch3a1_extra.py；docs/enhance/batch3a-1/DELIVERY.md | test_appendix_i_real_timelines_plusplayer_requires_current_digest_confirmation；原 confirm-input 当前摘要校验测试 |
| 5 | 单次递归 files -m，校验包根，达到上限拒绝，删除记录剔除，不再 dirs 遍历 | core/.../p4.py、build_inputs.py、defaults.py；fixtures/p4/fake_p4.py | test_single_recursive_listing_limit_and_escaped_return_paths；test_real_shelve_notation_synonym_and_root_validation |
| 6 | 附录 O 已记已结清；不改变变量/报告比对规则，不冒称重新做真实侦察 | 无新增比对规则 | 原变量页身份、白名单、不可变输入与逐项核对测试 |
| 7 | Adapter 登记 P4 返回路径，显式 encoded 标记的后续命令原样使用；外来路径仍做 P4 转义（包括字面文件名中本来就有 %40 的情况），日志与 inventory 比较统一形式 | core/.../p4.py；analyze/.../snapshot.py；fixtures/p4/fake_p4.py | test_single_recursive_listing_limit_and_escaped_return_paths（含 @ # % *） |
| 8 | 保留 merge 返回码；通知写冲突 N 处，127 另记达到计数上限 | analyze/.../snapshot.py | test_final_budget_does_not_count_merge_inputs_and_conflict_count；原 0/1/127/128/255/信号/工具错误测试 |
| 9 | caret 行闭合集合，成对识别同栏位 gutter，不因出现一个 ^ 就取源码 | analyze/.../source_check.py | test_prefix_gutter_pair_caret_and_preserved_whitespace；test_half_lines_duplicate_position_line_mapping_and_orphan_source |
| 10 | 三份 merge 输入各查单文件限制，最终内容才计总预算；仍保留 merge 输入证据 | analyze/.../snapshot.py | test_final_budget_does_not_count_merge_inputs_and_conflict_count |
| 11 | 第一个 tick 的请求到达时发信号并等待释放；第二个 tick 返回后才放行首个响应，不再依赖 150ms | core/tests/test_batch21.py | Workflow21Tests.test_round_contention_three_skips_one_todo_and_real_two_process_ticks |
| 12 | §9.2 不是仅文档：按时长完成后的人工确认必须等待新的人工窗口，旧日志回执失效；按时长最终日志和闸门分开 | core/.../stability.py；test_batch3a11.py | TimestampTests.test_elapsed_manual_confirmation_waits_for_new_window；原 elapsed_final / elapsed_then_running 测试 |
| 13 | 来源标签改版本确定（base 清单）；记录 list_cl_equals_build_time / vd_practice、profile/build_conf 范围；不符或范围变化待复核，edits 不可用，旧产物保留 | analyze/.../snapshot.py、api.py | test_base_label_basis_and_review_blocks_edits |

## Python 3.10 审计

`evidence/python-api-audit.json` 列出本线全部 src/scripts/tests/fixtures Python 文件、SHA256、3.10 语法检查和有关 API 位置；最终测试运行后更新为实际交付源码摘要。

- `datetime.fromisoformat`：集中到 core/dates.py；明确将报告/P4 的紧凑时区 +0900 和 Z 转换成 3.10 可读形式。journal 原来吞掉 ValueError 的位置改为 report_start_time_invalid 待办，经 write_todos 落库。snapshot 的 shelveUpdate、报告 Start Time、日志时间，以及状态窗口时间都使用同一转换入口。测试：test_py310_compact_offset_and_parse_failure_is_recorded；原 running_but_stable 回归。
- `datetime.UTC`、tomllib、ExceptionGroup/except*、asyncio.TaskGroup、typing.Self/TypeAliasType/TypeVarTuple/Unpack、StrEnum、add_note：本线运行代码未使用。
- pathlib 新增 walk/is_junction、relative_to(walk_up=)、glob(case_sensitive=)：未使用；现用 resolve/relative_to/rglob/glob 都支持 3.10；测试中的 is_relative_to 自 3.9 可用。
- str.removeprefix（transport.py）要求 3.9，3.10 可用；字典合并、内置泛型要求 3.9，联合类型要求 3.10。
- itertools.batched、hashlib.file_digest、os.path.isdevdrive、subprocess process_group：未使用。现用 capture_output/text/timeout、os.waitstatus_to_exitcode（测试）、sys.stdlib_module_names（导入检查）、ast.parse(feature_version=10) 均支持 3.10。
- Unicode 显示转换与宽度、strptime 时区、marshal、sqlite、flock、HTTP/TLS、PTY、进程信号通过两个真实解释器运行测试；不把语法检查当成运行证据。
- import-linter==2.3 仅是开发工具；run_tests.sh 以测试用 python3 执行 lint 入口并核对版本，运行代码仍仅标准库。

## 测试证据

两份全文输出第 1 行是实际 Python 版本；两个完整运行串行执行、均退出 0。import-linter==2.3 来自各自开发 venv，核心运行代码未增加依赖。

| 解释器 | 结果 | unittest 耗时 | 全文 | SHA256 |
|---|---|---|---|---|
| Python 3.10.12 | 172 PASS；3 kept / 0 broken | 426.175 s | `evidence/test-output-python310.txt` | `121768277e3837cf6bc252151d8aa741744844f2db371c4ca765d8029205973e` |
| Python 3.12.3 | 172 PASS；3 kept / 0 broken | 380.018 s | `evidence/test-output-python312.txt` | `355cfe292d94f7a0a08553c1917c1a4ff5d75928457f25ce0bf91f75468940ee` |

运行命令（在独立工作树根目录，分别将 VENV 设为 `vd-cosmos-core/.devtools/py310` 和 `vd-cosmos-core/.devtools/py312`）：

```bash
nice -n 19 env PYTHONDONTWRITEBYTECODE=1 PATH="$PWD/$VENV/bin:/usr/local/bin:/usr/bin:/bin"   bash vd-cosmos-core/scripts/run_tests.sh
```

完整测试之后，凭据预检命中新验收器拒绝名单的凭据字段名称定义（不含凭据值）。仅给该定义行追加 `# credential-test-sample` 注释；修改前后 AST 完全相同，摘要及准确范围见 `evidence/credential-definition-annotation.json`。两种解释器随后各重跑 AcceptanceScriptTests 6 项，输出 `evidence/test-output-annotation-regression.txt`。最终 `owned-source-manifest.json` 记录加注释后的源码摘要；完整运行对应的唯一原始摘要差异在注释记录中明确列出，不冒称测试后字节没有变化。


## A3 构建机验收脚本

文件：`vd-cosmos-core/scripts/verify_b3a11_real.sh`、`.py`，实现 `vd-cosmos-core/src/vd_cosmos_core/verify_b3a11.py`。

1. shell 与 Python 两层核对人工审核的完整提交号等于 HEAD；检查六个本线源码目录干净。版本、HEAD 写 stderr；stdout 单个 JSON。
2. 逐个运行实际存在的 `vd-*/scripts/run.py --help`，验证返回 JSON 和 commands；以同一解释器运行完整 run_tests.sh（包含 import-linter 2.3）。所有临时文件位于新数据根；不自动安装包。
3. 复用 verify_b2 的读取侧 A–F，固定 19091860、真实规模、独立 rows/links 和保存页面。F 参与结论；D 未提供进行中构建时明确跳过。A/B/C/E/F 任一失败就不取 P4 快照。
4. P4 login -s / info 前置检查；变量页取得并核对不可变 base/shelve 清单；对 B 段 7 个唯一失败包调用 snapshot，继续使用 §3.6 参数/环境隔离。未登录/票据不足只输出给 FatTank 的登录命令并停止 P4 步骤；不执行登录。历史输入不可还原照实写仅诊断，不声称快照错误代表分析准确性失败。
5. result.json 与 summary.md 列出逐包源码行核对、路径类别、shelve 处理和最终状态。每次新建原 data_root 下 verification/b3a11-随机串目录，不修改/复用原轮次；原配置不变。要贴回的终端输出和结果先过凭据模式检查，原始子进程异常不直接回显；中途登录失效时保留已完成的包行、剩余包标未执行。运行配置复制前还检查秘密字段名，不依赖正则表恰好覆盖该名字。

构建机运行前，将该提交检出到专用且干净的工作目录，使用现有 Python 3.10.12 开发/验收 venv（已装 import-linter==2.3，PATH 首位是其 bin）。确认本机配置里的 p4.port、p4.user、p4.expected_server_address、票据路径与不存在的 client 名已经按构建机实测填写，不能使用 example.invalid / configure-user 占位值；本次仅加载 PASS 不证明连接参数可用。由 FatTank/ClineSR 使用第 2.1 批留存的原始 baseline；不得用当前读取器重新生成所谓独立基线。所需文件为保存目录中的 report_armv7l.html、report_x86_64.html、probe_3bed7e8c.html，以及独立 rows.txt 和 arm-only links.txt。

准确调用形式（EXPECTED_COMMIT 用本批回报的完整提交号，不能临时取当前 HEAD 来绕过审定；其余变量填构建机现有文件的绝对路径）：

```bash
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11_real.sh "$EXPECTED_COMMIT" \
  --config "$VD_CONFIG" \
  --saved-dir "$B21_SAVED_DIR" \
  --rows "$B21_ROWS" \
  --links "$B21_LINKS"
```

脚本不需要用户填写真实值到仓库。D 段可另加 `--live-build-id <已知进行中构建号>`；没有就如实跳过。输出目录会包含测试全文、A–F、变量页白名单制品、快照和安全汇总。退出码沿用 HLD §4.4：0 完成，2 参数，3 人工处理，4 规则拒绝，5 后端/进程失败，6 前置条件不满足（含提交不符、测试不通过）。

## 设计裁定、差异与边界

- B3a11-Q01 已闭合（设计方 2026-11-14）：输出展开的 P4 登录命令；允许内部名字和路径，凭据仍禁止。未实现间接读配置的登录命令。登录命令同样经过凭据模式检查。
- A1 #5 的参数位置遵循 P4/HLD：`files -m N <root>/...@CL`；不是把选项放在 filespec 后面。只有代码构造的这一种递归查询可以通过通配符禁用门。
- A3 要求打印表格与版本，HLD §4.4 要求 stdout 单个 JSON：人读表格和版本放 stderr，表格另写 summary.md，stdout 返回结构化摘要。
- 附录 O #6 是已经结清的实测事实；本次不重复内网验证。#12 需要新人工窗口优先的代码修正；#13 需要来源依据与复核接口，均非仅文档修改。
- 19091860 只用于读取/快照验收，不恢复为 §11 分析准确性验收样本。plusplayer 的真实历史无法还原仍可能产生仅诊断；这不是自动确认输入的理由。
- 本次不运行真实构建机 A3；需 FatTank/ClineSR 执行上述命令。未取得构建机结果之前，只能报告离线通过；本次脚本对接通过入口/编排/隔离的离线测试，网络 A–F 复用原回环测试，真实 P4 七包整体结果仍待构建机。
- 源码显示测试按冻结 HLD 与已记录报告结构构造；本机没有 Clang 22，不声称重新运行 Clang 22 生成了金样。构建机真实日志核对将提供实际结果。
- 接收器、任务包、完整人工复核结论/同步流程变化登记属后续批次；本次 manifest 的 basis/basis_scope/basis_review/edits_eligible 与 basis_review_interface 提供接口，已有争议不会自动清除。Checkpoint B（§8.8 / §8.9）未开始。


### 测试过程记录

首轮 Python 3.10.12 全量执行 168 项，167 通过，1 项旧 `test_sigterm_and_sigint_clean_exit_release_instance_lock` 在 `communicate(timeout=3)` 超时；该测试依赖请求后睡眠 40ms。现改为子进程进入 loop 睡眠阶段后用 pipe 明确通知父进程，再发送 SIGTERM/SIGINT，另有失败清理，不依赖时间窗口。该项与新增回归的定向执行通过，最终全量结果以两份最终输出为准。

本机配置仅加载：`evidence/config-load-check.json`，Python 3.10.12 PASS；原件摘要 `e774c86a9f90ec1841f906aae52f1d4e89d3ac7d721ec626966c3409fbcd7caf`，未移动、未复制、未改动，未输出连接值、未联网。不存在的 data_root 沿父目录做文件系统检查，校验没有放宽。


验收器编排回归：`AcceptanceScriptTests.test_hash_gate_before_config_or_network_and_all_help_contracts`、`test_offline_suite_same_interpreter_owned_tmp_and_output_gate`、`test_seven_snapshots_login_failure_stops_without_login`、`test_acceptance_orchestration_fresh_roots_and_expanded_login_output`、`test_offline_failure_prevents_real_reads_and_p4`、`test_mid_snapshot_login_expiry_retains_completed_rows_and_secret_keys_block`。前者真实执行所有入口 help；编排部分用受控替身验证顺序、全新根、配置原件不变、停止边界与输出，P4 部分另有假可执行文件的协议测试。没有把编排替身称为真实构建机整体验收。

## Checkpoint B1（HLD v0.9.18，无浏览器部分）

基线 `bf5acb49ee6947faa66de474a5d0af365341a6fc`（Checkpoint A 已由设计方接受）。工作树仍为 `/home/toolchain/development/LogAnalysisSkill-vdcosmos`；不进入主工作树。B3a11-Q01 的冲突规则继续适用。新增 `vd-cosmos-submit`，运行依赖仅标准库；没有浏览器、点击、登录、提交或真实 P4 操作。

### HLD → 实现 → 测试

下表省略 `vd-cosmos-core/src/vd_cosmos_core/` 前缀；测试位于 `vd-cosmos-core/tests/test_batch3a11b1.py`、`test_batch3a11b1_transport.py`。

| HLD 条目 | 文件与实现 | 测试名 |
|---|---|---|
| §8.9 1–2：主证据、旁证、三档结论 | bm_pages.py：唯一 build-header、强自身身份、紧邻 Hub Link、严格 https/主机/路径、推广块本页编号对/引用；bm_reader.py：overview 旁证冲突，不把唯一候选当身份保证 | test_hub_identity_and_side_evidence_closed_shapes；test_multiple_links_reference_and_overview_conflict；test_unique_conflict_missing_and_no_negative_cache |
| §8.9 3：匿名读取、分页与覆盖 | bm_transport.py：内存匿名会话、只走管理端直连、历史同路径逐跳检查、固定错误；bm_reader.py：每页范围/总数/时间、首屏锚点、重叠/N 变化、补扫旧锚点、快照三遍详情读取、预算、已结束有 Hub Link 才缓存 | test_anonymous_in_memory_session_redirects_and_no_body_artifacts；test_page_shapes_from_evidence_and_error_no_snippet；test_history_overlap_topup_anchor_and_retention_wording；test_history_gap_repeated_page_reorder_anchor_lost_limits；test_locate_three_pass_snapshot_prioritizes_late_group_and_budget；test_cache_only_ended_hub_and_unread_pending_not_dropped；test_reader_budget_spans_pre_scan_and_transport_failure_is_error；test_candidates_filter_detail_reads_reruns_use_live_overview |
| §8.9 3、§8.8 1：时间与 doctor | bm_pages.py / bm_transport.py / submit_doctor.py：ZoneInfo、Date 中点偏差/RTT、时钟跳变、时长解析、最短运行样本；默认不联网，只查询本机包/配置，不启动浏览器；php 包数未知或非零不报通过 | test_clock_skew_timezones_and_duration_samples；test_time_skew_margin_preserves_utc_and_clock_unknown；test_doctor_offline_cli_non_tty_and_via_hub_B2_error |
| §8.9 4：lookup | vd-cosmos-submit/scripts/run.py、src/vd_cosmos_submit/cli.py：无登录查号、可选 since、输出清单行数/解析摘要，结果不改请求/绑定；--via-hub 明确 requires_B2_browser | test_lookup_readonly_does_not_resolve_uncertain；test_unique_conflict_missing_and_no_negative_cache；test_doctor_offline_cli_non_tty_and_via_hub_B2_error |
| §8.8 2、7–8：请求、重复保护、resolve | submit_model.py / state.py：全表单摘要（base 按解析结果）、复用、无时限重复保护、最近请求、原始意图/暴露不确定保护、目标会话唯一约束、人工重跑挂起及归属后计数；已提交与观察任务同事件事务落库，不生成点击 | test_digest_reuse_duplicate_round_and_uncertainty_cross_request；test_target_session_unique_and_explicit_uncertainty；test_unresolved_raw_click_cannot_be_bypassed_and_config_invalid；test_resolve_atomic_tasks_manual_time_and_pending_rerun；test_not_submitted_no_observation_and_lookup_absence_refused；test_pre_click_snapshot_failure_and_abandon_not_duplicate_bypass |
| §8.8 8、§8.7 5：绑定后的报告核对 | submit_projection.py / observation.py / vd-cosmos-workflow：使用 HTTPReportReader 的统一 build_ref；绑定变量页核对之后，完整报告逐行与冻结清单核对，不一致停止推进；重跑谨慎标记进入 workflow，旧绑定由 bind.previous_build 标过期 | test_binding_uses_reader_identity_report_mismatch_blocks_workflow；test_failed_build_later_new_hub_other_account_rerun_and_rebind |
| §8.8 3a、§8.9 5、§14 23：属性与 cmp-v1 | submit_config.py / defaults.py / config.sample.json：18 项、未登记可保留；bm_pages.py：显式变量名单、原样取值形状、仓库 URL 去凭据、凭据拦截；cmp-v1 去行尾空白和末尾空行、不抹缩进和内部空行，文本未确认不与请求硬比，PACKAGE_LIST 始终按解析结果 | test_cmp_v1_and_unregistered_text_and_parsed_base；test_enum_unobserved_and_variable_whitelist_never_returns_secret；test_variable_raw_shape_preserves_template_layout；test_variable_two_cells_and_fixed_enum_original_case |
| §8.9 5：人工认领 | submit_claim.py：候选而不自动绑定；H_pre 和点击前时钟取样接口、未知不补写；身份/配置/时间/归属硬检查；两个确认词独立；确认后只重读选定详情/变量并核对最新扫描依据 | test_candidate_only_and_both_words_hpre_unknown_and_hard_checks；test_attest_outside_candidates_hard_guards_and_words_independent；test_known_Hpre_confirmation_matrix_and_no_replacement；test_confirmation_basis_changes_but_not_anchor_and_version_race；test_candidate_membership_change_requires_new_confirmation；test_concurrent_attest_only_one_binding |
| §8.9 5–6：锁、版本、观察任务 | locks.py / submit_model.py / submit_watch.py：观察锁跨扫描/睡眠，网络在请求锁外，合并核对版本；心跳单独追加操作事件，不伪装候选变化；任务、锚点、待核对集合、已见记录、补充观察起点持久化 | test_network_outside_lock_version_change_discards_scan；test_two_process_observation_lock_and_manual_request_lock；test_heartbeat_continues_while_scan_or_terminal_callback_waits；test_heartbeat_not_scan_duration_and_resume_gap；test_observation_cannot_authorize_and_task_persists_restart；test_watch_cli_readonly_fixture_and_no_click_events |
| §8.9 6–7：重跑与不确定范围 | submit_claim.py / submit_watch.py：同 H / 同内容旁证、其它账号同 H、保留被清理记录、失败后观察、结束时间未知不提前完成、旧映射产物过期，不自动改绑 | test_rerun_pending_retention_and_supplementary_bound；test_failed_build_later_new_hub_other_account_rerun_and_rebind；test_manual_start_lower_bound_and_observation_deadline_running |
| §0.5、§6.4：人工入口 | commands.py / submit_terminal.py / submit CLI：/dev/tty、yes、确认词、管道拒绝、祖先检查；SKILL.md 仅列只读调用，人工命令只列 FatTank 手册 | test_doctor_offline_cli_non_tty_and_via_hub_B2_error；test_watch_cli_readonly_fixture_and_no_click_events |
| §3 12、构建机 B1 验收 | check_submit_boundary.py；verify_b3a11.py（共享 ROOTS 加入新 skill）；verify_b3a11b1_real.sh/.py；verify_b3a11b1.py：HEAD、完整离线套件、在线 doctor、两个只读查号，始终新根；无安装/P4/浏览器 | test_wrong_head_stops_before_config_and_shell_reports_version；test_acceptance_isolated_roots_order_and_lookup_pairs；test_offline_failure_prevents_online_and_php_unknown_not_pass；run_tests.sh 静态边界检查 |

### 证据夹具与限制

`tests/bm_helpers.py` 从 recon15 的 overview 表头、Summary/历史行与时长写法、recon16/17 的 Showing/下一页监听与匿名会话跳转、recon18/19 的 Hub Link 关系、recon21/22 的变量行重建 HTML。使用合成名字和内容，明确不是生产原页的无损副本。TLS 测试只监听 127.0.0.1，临时自签证书只用于本地服务；验证跳转/会话/正文无落盘，不访问真实管理端。构建机完整 HTML 结构和真实查号结果仍由专用脚本验收，不能用本地合成页替代实测结论。

历史清理可能造成漏观测；按编号定位不能证明不存在更早/延迟的同 H 构建；别的账号重试并换了新 H 时不能由本账号同内容旁证发现；观察期过后出现的重跑不自动发现。所有否定措辞限定“在已读取的保留记录中”。绑定保持输入核对状态，不能拿候选确认当起轮授权。

### B2 接口与有意未实施范围

- `submit_model.create_request` / `record_outcome` 是状态层接口；B2 才接浏览器准备、提交响应。这里没有 `once` CLI、请求发送闸门、控件回调、点击路径、认证、profile 或 `--rehearse`。
- `submit_claim.pre_click_evidence` 返回 H_pre 与 Date 样本；B2 在点击意图事务中冻结，不允许后补。`submit_outcome` 的 accepted 与观察任务一起追加；人工 resolve 同样建任务。
- `submit.property_map` 先完整登记 18 个槽位，默认变量/编码为空；第二十三次侦察和 B2 演练后才能确认文本形状/控件编码。未登记不等于默认值可用。
- `--via-hub` 返回退出 6、`requires_B2_browser`。§8.9 第 4 条涉及已登录浏览器的另一侧证据留 B2；本次主证据与两种旁证全部在无登录读取器里。
- 遗留会话的浏览器进程识别/关闭/profile 清理由 B2 负责。本次状态检查拒绝未解决的意图/暴露，状态唯一约束提前就位；正常关闭记录的 `normal_close=true` 仅能在 B2 已确认关闭之后写入，不能由 lookup/watch 生成。
- request 版本只随业务状态/扫描合并事件增长；独立 heartbeat 事件不改变候选依据，避免长扫描被自己的心跳持续作废。每次业务合并仍检查请求版本和全局 expected-head。
- HLD 要求终端 watch 可人工确认，用户称其为“只读 continuation”：按 B3a11-Q01 采用 HLD，默认后台只读；控制终端可经人工能力门确认。SKILL 的命令固定带 `--read-only`。确认输入期间扫描/心跳继续，人工动作不包装网络锁。
- B1 不启动浏览器取版本，doctor 如实报告配置登记版本/本地可用性，不声称实测浏览器版本；实际浏览器版本及启动验证留 B2。

### B1 测试全文与 SHA256

两套均完整运行 run_tests.sh：各 216 项 PASS（原 172 项 + 新 44 项），标准库/Python 3.10 语法检查 74 个实现入口文件、三条 import-linter==2.3 约束、B1 无浏览器/无 PHP 静态边界检查全部通过。输出第 1 行为实际解释器版本。最终两套执行的 99 文件源码摘要完全一致，见 source-manifest.json；验证摘要见 validation.json。

| 解释器 | 完整输出 | SHA256 | 结果 |
|---|---|---|---|
| Python 3.10.12 | `evidence-b1/test-output-python310.txt` | `4353a6af526515bee43feb54e233eb343d4c2599503dea398c57539f2884fe38` | 216 PASS / 45.596 秒 |
| Python 3.12.3 | `evidence-b1/test-output-python312.txt` | `f50ad1a724a6b6664a6e41443c838570c63379991ea4226c7ba38b951c5ecb90` | 216 PASS / 43.701 秒 |


### B1 测试环境与一次未通过的诊断

完整套件先在本机 ext4 的本线临时目录运行；旧 batch2.1 验收子进程超过原有 20 秒超时。独立重现见 `evidence-b1/ext4-acceptance-diagnostic.txt`（22.545 秒，TimeoutExpired），进程等待点观察到文件系统 journal commit。使用测试脚本原有 `VD_COSMOS_TEST_TMPDIR` 选项切换到用户运行目录下的全新 tmpfs 临时目录，同一个测试 1.086 秒 PASS，见 `tmpfs-acceptance-diagnostic.txt`。没有改实现、没有放宽超时或断言；先前未完成的试跑不作为 PASS 证据。最终两套测试均采用 tmpfs、顺序执行、nice 19；目录/环境记录见 `test-environment.json`，代码摘要见 `source-manifest.json`。这验证离线行为、进程锁与 SQLite 事务，不宣称验证磁盘掉电持久性。构建机脚本仍把所有临时数据放在配置 data_root 下的新根，不绕过其磁盘检查；若该机也触发原有验收超时，应保留失败输出再判断，不能把本机 tmpfs 通过当成构建机通过。

首次完整 tmpfs 套件为 215/216 PASS：旧验收器的入口发现已找到新 skill，但共享 ROOTS 洁净检查名单尚未纳入它。已把 vd-cosmos-submit 纳入共享名单（同时覆盖 A/B1 验收器），未删除或放宽原测试；失败全文保留为 `pre-registry-fix-python310.txt`，最终完整结果见上表。

### B1 构建机命令

见 `docs/enhance/batch3a-1.1/FATTANK-B1-MANUAL.md`。使用 Python 3.10.12 的现有开发/验收 venv，PATH 指向该 venv；EXPECTED_COMMIT 为本批最终回报的完整提交号，VD_CONFIG 为构建机原配置绝对路径：

```bash
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11b1_real.sh "$EXPECTED_COMMIT" --config "$VD_CONFIG"
```

顺序：HEAD/工作树检查 → 每个入口 help → 完整离线套件 → doctor --online → lookup 37491096 得 19270912 → lookup 37491058 得 19270877。任一步不通过就停止后续在线步骤；19270877 只用于误提交只读查号核验，不绑定、不分析、不作为输入。产物只写原 data_root 下的新目录；当前开发机不执行真实在线段。

本批本地配置加载证据：`evidence-b1/config-load-check.json`（Python 3.10.12；原件 SHA256 `e774c86a9f90ec1841f906aae52f1d4e89d3ac7d721ec626966c3409fbcd7caf`；PASS，未移动/复制/修改，未联网）。本批 API/源码审计（新旧本线源码、脚本、夹具和测试）：`evidence-b1/python-api-audit.json`、`source-manifest.json`；新用 ZoneInfo（3.9）、removesuffix（3.9）、标准库 CookieJar/HTTP/TLS，未新增 3.11+ 运行 API。
