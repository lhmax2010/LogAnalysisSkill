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


## Checkpoint B1.1（设计方 2026-11-14 裁定）

基线 c9d8eb5bbb0e843eda002e13df7d948c16f19712。HLD v0.9.18 原件不改；本节记录设计方将合入下一版的修正。recon24 的三列表头结论来自本次设计方答复（6 个构建含 19091860），本机没有访问构建机。

### A / C：实现与测试

| 要求 | 实现文件（core/src/vd_cosmos_core/ 前缀省略） | 回归测试 |
|---|---|---|
| Name / Display Name / Value 真实表 | variable_pages.py 的共享纯解析器；build_inputs.variables 与 bm_pages.variables 均按 Name/Value 表头映射，仅取 Value；pre 内容不人为补尾换行，Display Name 不拼接 | test_three_columns_nonempty_display_pre_shared_callers_exact_value；原 test_appendix_i_2245_base_545_shelve_and_credential_variable_never_written 改为真实三列 |
| 缺失/异常/重复表头不猜列 | 表头唯一、Name/Value 必须唯一，Display Name 可选，允许列重排；拒绝未知额外表头、跨列、宽度不符、多个候选表、重复变量；FlowError 5 + todo | test_header_mapping_reorder_legacy_two_columns_and_bad_headers |
| 两列历史兼容选择 | 只显式支持有 Name / Value 表头的两列；无表头的旧 fixture 不再支持。全部变量页生成器改三列（含非空 Display Name、pre），只保留一个正向两列兼容夹具及其负向变形 | 同上；bm_helpers.variable_table、test_batch3a1.py、test_batch3a1_extra.py、B1 两组测试 |
| 第一次读取即冻结 | variable_pages.remember：按管理端主机/端口、B、变量名保存不可变值与完整 SHA256，变量未列出也记缺失；新增白名单字段在第一次实际读取时补记。只冻结凭据检查/仓库 URL 去凭据后的字段，不存 HTML、未选值或 Display Name；锁只包文件读写 | test_first_read_before_report_validation_and_changes_preserve_authority；test_claim_first_read_restart_absence_new_names_and_digest_tampering；test_simultaneous_first_reads_cannot_overwrite_and_secret_blocks_before_store |
| 变量变化 | 后续读取按值摘要比较，拒绝覆盖，退出 3；“变量页已变化”待办只记字段/摘要，写 inputs/variable-first-read/<构建摘要>/issues/；lookup 返回 todo，watch 合并待办；原值仍权威，不自动继续使用新值 | test_lookup_and_watch_propagate_changed_variable_todo |
| A 读取器真实 Hub Link 兼容 | build_inputs.py：原 A 身份检查会把已登记 Hub Link 当外域自身链接；失败时只允许 B1 严格关系解析器验证强身份/配置/合格 Hub Link，任意其它异域链接仍拒绝 | test_three_columns_nonempty_display_pre_shared_callers_exact_value（同时通过真实 Hub Link 头部）；原身份拒绝测试保留 |
| 同 H 多 B | bm_reader.py / submit_claim.py：关系证据一致时“重跑链”，列每个 B/开始时间/状态，auto_selected=null；认领不同 H 的多个候选写“多个候选”，不谎称关系冲突；Hub/推广块/overview 真正不一致仍“冲突”；无自动绑定 | test_same_hub_multiple_consistent_builds_chain_never_select_or_bind；test_genuine_inconsistency_still_conflict_and_claim_chain_is_manual |
| 文本比较 / 配置 | 初次 C3 限制已由下方 recon25 追补裁定替代：已登记 variable/encoding 使用 cmp-v1，未登记仍未核验；PACKAGE_LIST 按解析结果，默认 18 项仍未登记 | test_registered_text_compares_and_shipped_map_stays_unregistered；test_recon25_registered_cmp_v1_without_old_flag_and_unregistered |
| 读取器保密 | 修改原 TLS 集成测试：允许安全首读值制品，仍逐文件断言没有 HTML、匿名 cookie、密码变量或错误响应片段 | test_anonymous_in_memory_session_redirects_and_no_body_artifacts |

新增测试位于 vd-cosmos-core/tests/test_batch3a11b11.py。变量记录跨调用方共享，既用于本轮 base/shelve，也用于认领比较；B2 的 --base-from-hub 源值应走同一 Reader.variables/remember 接口。本次没有实现 once 或浏览器路径。已有 c9d8eb5 以前的运行目录没有“当时首次读取”的证据，不能追溯虚构；升级后第一次通过新读取器时才建立记录。构建机验收使用全新根。

### 所有 HTML 表读取器的列假设审计

检索本线全部 vd-* 的 Python/HTML（排除开发 venv、运行目录），表解析实现集中在下列文件。其它 skill 调用它们，没有独立 HTML 表解析器。

| 读取器 | 检查结果 |
|---|---|
| build_inputs.variables | 原固定第 2 列错误；已替换为共享 Name/Value 表头解析 |
| bm_pages.variables | 原 Name 后所有列拼接错误；已替换为共享解析 |
| bm_pages.columns / detail Summary | 按 Id/Status/Begin Date/Duration 表头建字典，非固定索引；重复必要表头拒绝，身份另核对 |
| bm_pages.listing overview | 登记的完整 11 列表头必须一致，值按表头键取，不把新增列猜作旧列 |
| bm_pages.listing history / doctor 时间样本 | 识别 Version/Begin Date/Duration，按名称映射；不是变量页，未套用三列表 |
| report._header_and_counts | 报告头键值行要求恰好两格且左格是登记字段名；汇总支持严格两格键值或五个已知分类表头后的一行计数，五列按表头配对，不猜 Value |
| report.parse_report 编译/扩展/Export 明细 | 已登记报告格式为包名/路径/状态三列，严格 len==3；没有通用变量表逻辑。多出 Display Name 列或路径不可解析会记结构未知，不接受为完整结果；新增 test_other_report_fixed_schema_rejects_added_display_column |
| report.table_titles / table_rows / cells；variable_pages.own_rows | 辅助定位标题/直接单元格；共享变量解析明确不遍历嵌套 table 的数据行，避免外包装表重复命中 |

没有声称任何未来未知列布局都可兼容；未登记结构应停止，而非猜测。报告明细仍是登记过的固定三列契约，不擅自扩大本次重构范围。

### B：脚本归档与证据等级

B3a11-Q02 已闭合（设计方 2026-11-14）：原件独立保存为 docs/enhance/evidence/scripts/recon23.py，SHA256 为 b8781bd49d91512f0d2c0b6b8a4e92a0900658aa04487f54b1bca7152232ff81，字节与 Downloads 原件完全相同。recon_scripts.txt 保持本批基线原样，不追加。脚本未执行；recon23.txt 未读取、未复制、未用作证据；现已有下方 recon25/recon26 经核验追补证据。初次三列表事实来自设计方对 recon24 的答复，现以 recon25 四构建记录补证。

登记文件 docs/enhance/evidence/archive-exemptions.json 保存路径、完整文件摘要、第 45 行、精确命中文本/规则、原因、日期和批准人。仅仓库 prepush 的 archive_precheck.py 读取登记：必须位于 evidence/scripts/、路径规范且非符号链接、全文件摘要/行/文本/规则均相同才排除此命中。任何字节变化均阻断，不能通过添加行内样例标记绕过。JSON 内等号用 Unicode 转义存储，解码后仍是精确命中文本，避免登记元数据本身重复触发扫描；没有放宽凭据模式。运行时 check_content、export、verifiers、配置及其它预检保持原规则。

新增 vd-cosmos-core/tests/test_archive_precheck.py：

| 要求 | 测试 |
|---|---|
| 已登记原件及真实 prepush CLI 通过 | test_registered_original_hash_line_text_rule_passes_repository_cli |
| 一字节修改、加样例标记、删命中文本均阻断 | test_one_byte_change_and_inline_marker_cannot_keep_exemption |
| 同文本未登记文件、目录外、符号链接阻断 | test_same_text_in_unregistered_file_or_wrong_path_is_blocked |
| 真正会话值继续阻断 | test_real_session_value_still_blocked_and_never_exempted |
| 行/文本/规则必须一致，不能掩盖另一规则 | test_each_constraint_required_and_unapproved_other_match_not_hidden |
| 运行时导出和验收检查不读取登记且仍阻断 | test_registry_never_changes_runtime_export_or_verifier |

### C：18 项映射提案（proposed, awaiting FatTank confirmation）

依据：HLD §8.8 3a 的字段名单及 recon20.txt 98.6 秒的 18 控件（行 373–392）。recon20 证明表单标签/控件，不证明变量页 Name；recon25 现已确认三列表头且 Display Name 全为空。因此下表仍是建议检索/核对的配对，不是已批准的控件映射，尤其带推测的字段名不能直接写进配置；EMAIL_CC 已据变量清单更正为“变量页不列出”。其它配对仍待 FatTank 确认。所有 shipped variable/encoding 保持 null。

| 序号 | 表单属性 | 建议变量 Name | 依据/待核 |
|---|---|---|---|
| 0 | BUILD_TYPE | BUILD_TYPE | 同名提案；枚举编码待核 |
| 1 | BASE_REPOS | BASE_REPOS | 同名；已有五变量读取名单 |
| 2 | BUILD_CONF | BUILD_CONF | 同名；已有五变量读取名单 |
| 3 | PRODUCT_REPOS | PRODUCT_REPOS | 同名；已有五变量读取名单 |
| 4 | ARCH | ARCH | 同名提案；枚举待核 |
| 5 | PACKAGE_LIST | PACKAGE_LIST | 同名；按解析结果 |
| 6 | GITURL | GITURL | 同名提案；显示标签与实际值待核 |
| 7 | SHELVE_LIST | SHELVE_LIST | 同名；当前提交范围必须空 |
| 8 | KS_LIST | KS_LIST | 同名提案；双列表/recorder 编码待核 |
| 9 | Product Version (ks) | PRODUCT_VERSION | 推测，须用 Display Name/对照值确认 |
| 10 | rpm Add & Delete | RPM_ADD_DELETE | 推测，含 ks/Image 标签语义待核 |
| 11 | PACKAGE_LIST (DELETE) | PACKAGE_LIST_DELETE | 推测，后缀实际写法待核 |
| 12 | PACKAGE_LIST (x86 arch) | PACKAGE_LIST_X86 | 推测，后缀实际写法待核 |
| 13 | Ignore package build failure? | IGNORE_PACKAGE_BUILD_FAILURE | 推测，复选框布尔编码待核 |
| 14 | Keep 'Full' build type | KEEP_FULL_BUILD_TYPE | 推测，复选框布尔编码待核 |
| 15 | Image Skip? | IMAGE_SKIP | 推测，yes/no 与变量编码待核 |
| 16 | EMAIL_CC | 变量页不列出 | recon25 变量名单；不影响构建比较 |
| 17 | EXTRA_BUILD_PARAMETER | EXTRA_BUILD_PARAMETER | recon25 D2 确认词表值；登记后启用 cmp-v1，映射仍待确认 |

### D：同一会话 A + B1 构建机验收

选择“准确两条命令”方案，不新增编排入口。命令见 FatTank 手册新增 B1.1 节；下列 && 确保 A 失败时不继续 B1。EXPECTED_COMMIT 必须用本次交付的完整提交号；VD_CONFIG、B21_SAVED_DIR、B21_ROWS、B21_LINKS 使用构建机已有原配置及独立基线绝对路径，不向仓库写真实配置。

```bash
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11_real.sh "$EXPECTED_COMMIT"   --config "$VD_CONFIG" --saved-dir "$B21_SAVED_DIR"   --rows "$B21_ROWS" --links "$B21_LINKS" &&
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11b1_real.sh "$EXPECTED_COMMIT"   --config "$VD_CONFIG"
```

两条均要求同一完整 HEAD、本线源码干净、同解释器离线套件全绿；只在各自新建 data_root 子目录写产物。A 只读报告与 P4（不代登录），B1 无登录 HTTP doctor/两次查号；均不打开浏览器/不提交。19270877 只作第二次只读查号，不取作输入。真实构建机结果仍待执行。

### B1.1 完整测试与证据

两种解释器完整套件各 232 项 PASS（B1 216 项 + B1.1 10 项 + Q02 6 项）；三条 import 约束、76 个源码/入口 Python 3.10 语法/标准库检查、B1 静态边界检查通过。输出第一行是实际解释器版本。继续使用 import-linter==2.3、nice 19、串行执行和支持的 tmpfs 临时目录选项；不改原超时。新证据统一放 evidence-b11/，不覆盖 B1/A 历史证据。


| 解释器 | 全文 | SHA256 | 结果 |
|---|---|---|---|
| Python 3.10.12 | `evidence-b11/test-output-python310.txt` | `7b4d98d12b33fe5a150ec2572a65c229de0dd5a2f6ba33be243fb39dc31c1f4d` | 232 PASS / 43.403 秒 |
| Python 3.12.3 | `evidence-b11/test-output-python312.txt` | `5529f26b3a0e163b95f1bad3d170f231aa9b519b99e8a3c601ad6418c54211d9` | 232 PASS / 42.485 秒 |

源码清单 source-manifest.json 含 103 个本线源码/脚本/配置/夹具文件，最终运行后字节不变；validation.json 记录结论。本机构建机配置仅本地加载 PASS（config-load-check.json），不输出值、不移动、不改配置、不联网。未进行真实 A/B1 构建机验收。旧运行根的 build-lists 不会迁移或覆盖；历史归一化值与新原样 Value 不同也会停止，需人工核对，不能虚构升级前的首次原值。

Q02 前的 226 项日志保留为 evidence-b11/before-q02-python310.txt 与 before-q02-python312.txt；prepush-before-q02.json 仅是当时阻塞的历史记录，已由裁定和 prepush-final.json 取代。本次最终验证以上表 232 项日志为准。recon23-archive.json 记录脚本及登记摘要；全部变更文件的仓库凭据预检通过。

## B1.1 追补：recon25 / recon26 已核实证据（设计方 2026-11-14）

基线 b6cb3724c4348e89cdd54112e698310fd7f0360f。本节替代初次 B1.1 C3 的临时限制；HLD 原件不改。五份材料均从 Downloads 逐字节归档，归档前后摘要相同；本机没有运行侦察脚本或访问真实服务。原 recon_scripts.txt 不动。

| 归档路径（相对 docs/enhance/evidence/） | SHA256 |
|---|---|
| recon25.txt | a7e8145af95c6b7ab29ca2be63ebbb8eb4555c5f04eaa0eb6c4a7ec99a6e9929 |
| recon26.txt | ebaaa9c526dbf9261b1e79799ec936b35711b7c25f3ed0114a810cab8f8712c9 |
| scripts/recon24.py | b9d17e547354f1050c136b56a98333c87ed5e093a9ab5a3a69b27e46975bf128 |
| scripts/recon25.py | 6fd9ccd174dae8a1bb264213fe460b812387d9d9742b06a3aaf173573777202d |
| scripts/recon26.py | e8b6a8be6de243b5c82b4a3928664fdf7c7d24021afe4c916f87e3ac1de61cf4 |

archive-exemptions.json 按 B3a11-Q02 为 recon25.py / recon26.py 的第 38 行增加精确登记，recon24.py 无豁免。旧 recon23 登记保留；运行时凭据检查及配置不变。

| 追补裁定 / 证据 | 实现或处置 | 回归测试 |
|---|---|---|
| 撤回“变量页改变”判断：recon25 D3 的 19206687、19270912、19287341 的 PACKAGE_LIST/SHELVE_LIST 与 recon22 相同 | 首读冻结仅保留为防御设计，不再把历史变化作为事实；原 immutable 实现不改 | 原首读相同/变化/并发/篡改测试保留；test_recon25_empty_display_column_four_builds_and_exact_shapes |
| recon25 D：四构建表头 Name/Display Name/Value，显示名全空 | bm_helpers.variable_table 默认空显示名，Value 放 pre；单独保留非空显示名防错用例；内容用合成占位值 | test_recon25_empty_display_column_four_builds_and_exact_shapes；test_three_columns_nonempty_display_pre_shared_callers_exact_value |
| recon25 D/D2：精确检查 True，单行形状 L0T0W0；解除初次 C3 限制 | bm_pages.compare 对已登记 variable/encoding 使用 cmp-v1；旧 request_text_verified 标志不再阻挡文本；未登记/未列出/缺失仍未核验；枚举 observed_values 限制保留，PACKAGE_LIST 按解析结果 | test_recon25_registered_cmp_v1_without_old_flag_and_unregistered；test_cmp_v1_and_unregistered_text_and_parsed_base；test_enum_unobserved_and_variable_whitelist_never_returns_secret |
| recon26：完整窗口内 105 构建，37432138 对应 19238877（12:05:41）和 19241462（15:42:50），日期 2026-11-05 | 已实现重跑链逻辑沿用，不自动选择；补真实编号/时间回放（状态与包内容为合成，未伪称真实） | test_recon26_same_hub_two_real_ids_and_start_times_no_auto_selection；原真实证据冲突/人工选链测试 |
| EMAIL_CC 不在变量名单 | 上方映射提案改为“变量页不列出”；默认 shipped map 仍未登记，未擅自登记其余配对 | test_registered_text_compares_and_shipped_map_stays_unregistered |
| 两份脚本第 38 行正则归档豁免 | 仅登记原字节/原路径/原行/精确文本与规则；不执行脚本 | test_recon24_25_26_archives_exact_scope_and_runtime_still_blocks；原 Q02 六项测试 |

recon25 E 当时未覆盖窗口（in window 0），不能用作重跑否定证据；本次重跑事实依据 recon26（162 页、4860 条读取，窗口内 105 构建）。首读防御与“本次证据未发现变化”不矛盾。18 项映射提案仍须 FatTank 确认，此次确认比较规则不等于确认全部控件配对或浏览器编码。真实 A+B1 构建机验收仍待执行，命令仍是本节之前 D 的两条命令，EXPECTED_COMMIT 换成本次交付完整 hash。

追补全量测试（import-linter==2.3、三条约束、76 文件标准库/3.10 语法及 B1 静态边界均通过；nice 19 串行，临时目录沿用 tmpfs，未调整超时）：

| 解释器 | 完整输出 | SHA256 | 结果 |
|---|---|---|---|
| Python 3.10.12 | `evidence-b11-followup/test-output-python310.txt` | `28b4f074092f038aeaad1d38f765513962e3b1ebc6fb8e5c59ad9a43e4bfc6b9` | 236 PASS / 42.88 秒 |
| Python 3.12.3 | `evidence-b11-followup/test-output-python312.txt` | `2d528b1a6092a2f545bd5da3314bab5a739b164bc89b89005cc3fc99d9590964` | 236 PASS / 43.014 秒 |

本次新增四项回归，原测试按新裁定更新；validation.json、source-manifest.json 和 archive-verification.json 位于 evidence-b11-followup/，保留上一批日志不覆盖。原真实 config.json 仅本地加载，未更改或提交；加载留证 config-load-check.json。凭据预检记录 prepush-final.json。无未闭合阻塞问题；本机未执行构建机验收，FatTank 仍需按 D 的两条命令验收本次完整提交。

归档保真说明：git diff --check 仅对 recon25.txt 原件的 126 行报行尾空格；为保持指定 SHA256 原样保留，未修改 Git 配置。其余文件空白检查通过。这是原证据格式，不是凭据豁免。

## B1.2：首次构建机验收反馈修复（设计方 2026-11-14）

基线 ba12cba3c58b9f600370db80b4b612d42316cd99。设计方反馈首次真实 A+B1 运行的是 b6cb372：A 退出 5，7 包均为 p4_incomplete_output；B1 退出 5，doctor/lookup 为 bm_table_unrecognized。真实机的离线套件、contracts、读取侧检查、变量页 base 清单均已通过。以上是设计方交付的真实运行结论，本机没有访问构建机。diag27 补充核实旧配置仅有 config_file/env，P4 失败为 exit 1 / 空 stdout / 文本 stderr，及真实页面多表布局。此反馈不等于 A/B1 整体通过；修复后仍须真实重验。

证据原件：docs/enhance/evidence/diag27.txt，SHA256 1922925ca406a43936ed2590e6d86829b0c2286d8c411b6a0f84a017d00c831e；原脚本 docs/enhance/evidence/scripts/diag27.py，SHA256 f0ed943e308d21035d0b0ff7f7494edec5db84c9963356b5b5450b4015934a9b。均与 Downloads 原件逐字节相同、未执行脚本。第 11 行正则归档登记按 B3a11-Q02；第 7 行词表字面量（规则索引 3）由 B3a11-Q03 明确批准，同样精确登记；不改变原字节或凭据规则。原因：credential-name word list used for redaction; no credential value。登记 JSON 使用 Unicode 转义表示精确文本/规则，解码值不变，不对登记文件本身加豁免。

| 要求 | 文件与行为 | 新回归测试（vd-cosmos-core/tests/test_batch3a11b12.py） |
|---|---|---|
| 1 overview 三表/队列八列 | submit_config.py 与 config.sample.json 改八列默认；listing 既有逻辑只校验匹配队列表，排除 schedule 与 builds 表；bm_helpers.py 重建三张顶层表和类名 | test_real_overview_three_tables_queue_eight_headers_only（旧 11 列配置必失败） |
| 1 history 五表/嵌套 | bm_helpers.py 重建 6 行 settings（两嵌套 table）、空 table、6 列列表；已知类名使用 diag27 输出，嵌套类名只用记录中可见前缀，不猜被省略后缀 | test_real_history_five_tables_nested_settings_do_not_become_rows |
| 2 P4 文本错误 | p4.py 非零/空 stdout/有 stderr 分 connect_failed 与 text_error；整段凭据检查后仅首行 message + FatTank todo；乱码/截断仍 incomplete；fake_p4.py 新模式 | test_p4_plain_stderr_connection_text_and_incomplete_protocol；test_p4_stderr_credentials_blocked_before_message_or_todo |
| 3 使用点校验 | defaults.py 去除三个连接参数静默默认；p4.validate_config 在适配器构造和 doctor 调用，verifiers 通过这些使用点校验；旧配置仍能加载/读报告；sample config_file 改 fix_config_file | test_p4_missing_placeholder_validation_only_at_use_sites；test_p4_legacy_config_loads_read_side_and_doctor_gives_migration |
| 4 A 前置只失败一次 | verify_b3a11.snapshots：info → login -s 在包循环之前；前置失败附 stage=p4_preflight，无重复 7 行错误；登录提示保留；每包快照自己的上下文核验不删 | test_preflight_info_failure_once_before_any_package_or_fetch；test_preflight_info_then_login_failure_with_command；test_a_preflight_failure_summary_has_single_reason_and_no_seven_errors |
| 5 B1 子命令诊断 | verify_b3a11b1 保留经过凭据检查的原 P4 配置供 doctor；failed_command 记 doctor 或 lookup+hub_id、错误和子错误，stdout/result.json 相同；command helper 保留安全 child_details | test_b1_child_failure_keeps_doctor_or_lookup_hub_and_error_in_both_outputs；test_child_command_keeps_credential_checked_details |

样例的占位连接参数仍必须替换；测试统一给假 P4 显式 127.0.0.1/fixture-user 参数，假程序绝不连接 socket。未改真实 config.json。原构建机配置应迁移后再验收，报错只列键名和固定说明，不回显敏感值。B2 未开始；A+B1 构建机命令及参数不变（本文件 D 节），EXPECTED_COMMIT 用本次交付完整提交号。

B1.2 全量测试：Python 3.10 语法/标准库检查、三条 import 约束（import-linter==2.3）及 B1 静态边界均通过；nice 19 串行，tmpfs 临时目录，未调整超时。

| 解释器 | 完整输出 | SHA256 | 结果 |
|---|---|---|---|
| Python 3.10.12 | `evidence-b12/test-output-python310.txt` | `cb7e5a219a9a700fb848b7fb923e02e0f7261cb376d8d4b2e7334419f993cc0f` | 247 PASS / 46.163 秒 |
| Python 3.12.3 | `evidence-b12/test-output-python312.txt` | `e94de79163ab7d9a1e66a91596911f50fb7768a956d921fd5dcc802018859ea4` | 247 PASS / 43.849 秒 |

新增 11 项回归。evidence-b12/config-load-check.json 证明真实旧配置共享加载 PASS、P4 使用点报预期 p4_config_legacy_format；未改原件、未执行 P4。validation.json/source-manifest.json 记录源码和运行结果。B3a11-Q03 已闭合：diag27.py 第 7 行词表字面量（规则索引 3）和第 11 行会话删除正则（规则索引 2）分别获批且精确登记，最终凭据预检通过；A+B1 命令仍不变。旧 prepush-before-q03.json 仅保存裁定前历史阻塞，最终以 prepush-final.json 为准。

设计方常设授权（2026-11-14）：对设计方提供且声明 SHA256 的证据脚本，可直接登记用于检测、过滤或脱敏凭据的正则/词表字面量命中；严格沿用 Q02 精确约束，每条列入 DELIVERY，无需再次询问。命中像实际票据、口令、Cookie、token 或会话值，或脚本并非设计方提供且声明摘要时，必须停止询问。此授权不适用于运行时检查或其它文件。

## Checkpoint B2a — 浏览器之前（2026-11-14）

基线 e5d4afa；本阶段不启动浏览器。实现 once 的参数/外部写能力门、控制终端/祖先进程检查、来源白名单首读冻结与报告头提取、来源认定、跨请求保护、目标 profile 锁和会话恢复。

| HLD | 文件 | 测试（test_batch3a11b2a.B2aTests） |
|---|---|---|
| §8.8 1/1a，§6.4 | submit_once.py、submit_source.py、submit_terminal.py、submit CLI | test_cli_non_tty_and_argument_shelve_rejections、test_fake_ancestor_table_blocks_cline_and_unreadable、test_source_whitelist_header_only_and_no_bind_round_or_shelve_artifact、test_source_invalid_identity_missing_values_and_confirmation_never_create_request |
| §8.8 2 | submit_sessions.py、commands.py、submit_claim.py | test_profile_lock_and_session_unique_and_mode、test_recovery_alive_unknown_and_pre_exposure、test_exposed_no_click_survives_cleanup_crash_and_manual_override、test_click_crash_uncertain_and_accepted_crash_keeps_result、test_duplicate_parsed_list_and_wrong_resubmit_reference |

B3a11-Q04 — assumed: 配置未显式给全 18 项表单值时拒绝准备，不猜测第一次演练前尚未确认的默认值；属性对应表仍未确认，非演练退出 4 并产生待办。
B3a11-Q05 — assumed: 来源认定每次都重新回显并确认，暂不复用旧认定；这是比允许复用更保守的选择。来源读取仅取显式变量白名单和报告头，禁止把来源构建送入轮次/分析队列。

测试证据：evidence-b2a/python310.txt、python312.txt；完整摘要见 evidence-b2a/validation.json。后续 B2b 接入浏览器，目前准备完成后明确返回 browser_driver_unavailable。

## Checkpoint B2b — 窄浏览器适配器与单次协议

| HLD | 文件 | 测试 |
|---|---|---|
| §8.8 3/3a/4/5 | submit_gate.py、submit_browser_contract.py、playwright_driver.py、browser_scripts.py | GateTests 全部；test_form_extra_control_wrong_target_and_sensitive_form_rejected；test_browser_settings_env_and_static_negatives |
| §8.8 6/7 | submit_flow.py、submit_model.py | test_intent_rechecks_version_session_duplicate_and_foreign_exposure；test_result_crash_is_uncertain_no_second_click；test_accepted_records_mapping_task_and_final_readback_blocks_change |
| 演练/恢复 | submit_flow.py、fixture_driver.py、browser_child.py | test_rehearsal_never_clicks_and_closes_profile；test_confirmation_refusal_and_last_readback_change_never_click；test_manual_action_resolution_preserves_history |

Playwright 只允许在 submit 的单一适配器中延迟导入，核心保持标准库。浏览器使用配置指定的现有可执行文件，经父进程死亡监视启动器运行；不安装浏览器。profile 0700、禁用密码保存、清除调试环境、禁用 service worker / WebSocket / 弹窗，关闭确认后才清理本次 profile。外部异常只返回固定码。固定脚本 SHA256 在 browser_scripts.DIGEST；不接受选择器或脚本文本。Fetch 请求与响应逐跳暂停；普通 route 仅作弹窗/子框架第二道门，不能替代 Fetch。提交响应禁止跳转，accepted 落库后关窗。

B3a11-Q06 — assumed: §8.8 的逐跳网络暂停优先于 §8.6 一般 CDP 禁令，仅允许适配器通过 Playwright 管道调用固定 Fetch、主框架识别和窗口状态方法；无远程调试端口、无任意 CDP/Runtime 方法。静态检查固定允许集合。跨源 MFA 子框架尚无可证明的独立逐跳拦截，全部拒绝；需要这种认证的站点当前不能完成登录，不能以放宽闸门绕过。
B3a11-Q07 — assumed: 本机现有 Chrome 在 /opt/google/chrome/chrome，但两套开发解释器均缺 Playwright；不联网安装。真实浏览器测试保留并明确跳过，构建机 B2 验收强制执行且缺依赖即失败。这不构成真实浏览器验收已通过。
B3a11-Q08 — assumed: 认证 host/path/method 与静态资源名单默认空，不猜实际链路；Run 只允许录制后确认的 GET Wicket listener 和一次数字页面跳转，无法识别的 Run 形状拒绝。首次表单目标路径只认固定 breadcrumb/breadcrumbs 节点；实页不匹配时拒绝、不得泛读页面。首次演练输出候选指纹/安全模式，由 FatTank 确认后人工登记配置，工具不自动修改配置。
B3a11-Q09 — assumed: 未登记 checkbox/KS 编码的演练可以回读并输出离线序列化的字段长度/摘要，但 verified=false；正式提交必须确认映射、模式、指纹及所有编码。未知的 200 错误页保守记 uncertain，尚无已确认反馈面板规则，不猜 rejected。浏览器网络层自身可能重发的限制仍存在，闸门只保证一次应用层请求令牌。

当前限制：lookup --via-hub 仍明确拒绝（requires_B2_browser）；没有将匿名查号替换成浏览器路径。固定脚本读取、真实请求计数、Chrome API 兼容性需 B2c/构建机证明，不能用本阶段假驱动结果代替。运行时凭据检查没有读取归档豁免。

完整输出与 SHA256：evidence-b2b/python310.txt、python312.txt、validation.json。

## Checkpoint B2c — 负向测试与真实浏览器计数入口

新增 test_batch3a11b2_headless.HeadlessGateTests（只监听 127.0.0.1）：人工 GET/POST/弹窗/iframe 零请求；录制回调与提交零请求；精确回调最多两次；真实 FormData 单令牌只收到一次 POST 且不跟随结果跳转；错误正文零请求；同源登录/跨源 MFA 拒绝；认证回调到未登记业务页不跟随；WebSocket/service worker 零请求。计数来自服务端，而非驱动提供的人工/工具标签。

本机这 8 项因 Playwright Python runtime unavailable 跳过（Chrome 已存在）。VD_REQUIRE_HEADLESS=1 时缺运行时改为测试失败；B2d 验收必须带此设置。当前不能声称逐跳拦截已获真实浏览器证明；也不能声称覆盖了 §8.8 9 的全部实际页面组合（完整 Run 双步导航、MFA 放行、Wicket 编码仍待实页演练）。

其余负向检查：test_password_autofill_flag_and_rehearsal_never_arms；test_fixed_script_registered_digest_and_exception_redaction；test_browser_settings_env_and_static_negatives；test_second_process_profile_lock_never_starts_session。两进程锁测试用父进程持锁期间同步等待子进程结果，不依赖竞争时间窗。固定脚本摘要改为代码中显式登记常量，源码改动不再自动更新登记。提交结果仅接收同一 Fetch requestId 的响应，避免其它回调覆盖结果。

完整输出与 SHA256：evidence-b2c/python310.txt、python312.txt、validation.json。

## Checkpoint B2d — 构建机离线验收与交付边界

文件：vd-cosmos-core/scripts/verify_b3a11b2_real.sh / .py，vd-cosmos-core/src/vd_cosmos_core/verify_b3a11b2.py。

- 完整 HEAD 必须等于审定值；本线源码有未提交改动即拒绝。显示解释器与 HEAD。
- 只创建配置 data_root 下新的 verification/b3a11b2-* 目录；执行 --help contract、静态检查、完整离线套件。VD_REQUIRE_HEADLESS=1；Chrome/Playwright 缺失导致 FAIL，不会跳过后给 PASS。
- 不调用在线 doctor、lookup、真实 P4、once 或 live rehearse。验收输出先过运行时凭据检查再落盘。
- test_batch3a11b2_verifier：test_wrong_head_never_reads_config_or_creates_output、test_requires_real_browser_tests_in_fresh_root_no_live_calls、test_missing_browser_suite_fails_and_preserves_safe_reason、test_config_auth_or_static_cannot_whitelist_business_endpoints。
- 复核 recon20 后将 18 个控件名与 6 个已观察文本回调显式加入种子；均保持未确认。KS 控件必须恰为 recorder/choices/selection 三件；浏览器启动器兼容已由 Playwright 建立进程组的情形，监视子进程不持有浏览器通信管道。

构建机准确命令（现有 run/venv 已在 PATH；EXPECTED_COMMIT 使用本次最终回报的完整 hash，VD_CONFIG 与 VD_CHROME 指向构建机现有文件）：

```bash
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11b2_real.sh "$EXPECTED_COMMIT" --config "$VD_CONFIG" --chrome "$VD_CHROME"
```

稍后 FatTank 亲自做的真实演练，不属于本次实现者执行范围：

```bash
nice -n 19 python3 vd-cosmos-submit/scripts/run.py once --config "$VD_CONFIG" --backend real --base-from-hub 37376237 --bm-build 19206687 --reason "FatTank B2 live rehearsal" --rehearse
```

前提与恢复命令见 FATTANK-B2-MANUAL.md；没有写进任何 SKILL.md。实际配置需登记认证/资源路径与完整表单值，否则保守拒绝。真实 config.json 只读加载通过、原字节不变：evidence-b2d/config-load-check.json。

**未验证/保守拒绝项**：本机未执行真实浏览器请求计数（8 SKIP）；未执行构建机验收或 live rehearsal；跨源 MFA iframe、非 GET/未识别的 Run、未知表单目标节点、未知错误面板、未登记编码均拒绝或 uncertain；lookup --via-hub 仍未开放。正式提交映射仍为 proposed, awaiting FatTank confirmation，默认退出 4。没有把这些限制描述为已完成生产验证。Q04–Q09 均为周末 assumed 决策，待设计方复核。

全量测试文件与 SHA256 见本节后表及各 evidence-b2*/validation.json；每份输出第一行均为实际解释器版本。B2a/B2b/B2c 已分阶段普通推送，B2d 在同一提交更新本状态说明。

| 阶段 | Python | 总数 / 结果 | 完整输出 | SHA256 |
|---|---|---|---|---|
| b2a | Python 3.10.12 | 256 / 256 PASS | `evidence-b2a/python310.txt` | `d0e2e34a88b26c7e446b9c1484cd198796af55cc4ffc7def10b1faf69b21ee70` |
| b2a | Python 3.12.3 | 256 / 256 PASS | `evidence-b2a/python312.txt` | `d2d3168ff206fe313d0f05d69afa8f1fb8967062e84a227b90d4e7efb95c0507` |
| b2b | Python 3.10.12 | 271 / 271 PASS | `evidence-b2b/python310.txt` | `eb2fcd1c66993520922bd082b2fc29b5a750d2c1b0e0ae3b736b0b6c86dcb18f` |
| b2b | Python 3.12.3 | 271 / 271 PASS | `evidence-b2b/python312.txt` | `65d4d2f73eebb7994b74a6f87e6210e915ee53b5319732ce28b78b4cc48ebdfb` |
| b2c | Python 3.10.12 | 282 / 274 PASS + 8 SKIP | `evidence-b2c/python310.txt` | `db77d150b62ebb42fbb6308969a98188d7934aa1180399497ad7bf7777bbbe64` |
| b2c | Python 3.12.3 | 282 / 274 PASS + 8 SKIP | `evidence-b2c/python312.txt` | `55d84e6a2498461665868da7b1894c428c76856ef3e48c47840b95475e0801c1` |
| b2d | Python 3.10.12 | 286 / 278 PASS + 8 SKIP | `evidence-b2d/python310.txt` | `2626a856f7c84a3ba83a6e2b816ee14c706124c99a5b6f84c0f5a489a15da601` |
| b2d | Python 3.12.3 | 286 / 278 PASS + 8 SKIP | `evidence-b2d/python312.txt` | `6a1ab9ced0c3b5fefa57462564545f02d73f6103596ef79f7e95554395fb2ff1` |

## B1.3 — v3 构建机反馈与 diag28–30b（2026-11-16）

基线 13cf93f5d8c95a4dad20e0031f24dceb7d964169。仅独立工作树离线实施；不访问 Cosmos/Hub/P4，不打开浏览器，不执行诊断归档脚本。

### 新设计裁定与实现

1. 详情身份按本次设计方裁定替代 HLD §8.9 #1 / §5.4 #11：唯一 build-header 和其中排除 promotion 后唯一状态元素；历史导航不作自身链接；页面 nav-link 至少两条合法 build tab、编号都等于请求；页面配置 nav-link 恰好一个 distinct id。重复同一配置号仍是一个 distinct id，不拒绝；第二个不同号或缺失拒绝。Hub 主证据只认 build-dashboard 内 html-content.description 的唯一指定 h3/唯一合法链接；其它位置忽略；promotion 旁证冲突规则不变。Summary 允许额外列。observe 与管理端解析共享 tab_identity，旧单一头部自身链接不再构成强身份。
2. 读取/快照按架构自己的 PACKAGE_LIST_<arch> / SHELVE_LIST_<arch>；缺项才回退，空/坏项不回退，记录“回退到总清单”。总 PACKAGE_LIST 的每个条目（包键、原样路径、CL）必须出现在至少一个所选架构清单。回退的总 shelve 清单按本架构报告包键配对，另一架构的条目不误报为本架构多余；所有报告中都不存在的总 shelve 条目仍拒绝。总 PACKAGE_LIST / SHELVE_LIST 保持原样冻结，仍用于 source/request 比较，绝不把各架构合并结果当提交输入。架构变量的首读值和缺失都冻结。快照通过 for_arch 选择 base 版本；旧人工绑定 manifest 沿用原总清单格式。
3. lookup 完整结果写 artifact，stdout 只保留结果/原因/候选摘要/重跑链/覆盖/计数/首个失败页与产物路径；page_errors 逐次记录 kind/build_id/reason，保留所有无法识别的页面。
4. 构建机 child 非零且没有 error 时，保留 child_result/child_reason/child_artifact，经既有 failed_command 路径进入 B1 result.json 与 stdout。

| 要求 | 文件 | 测试（test_batch3a11b13） |
|---|---|---|
| 真实详情页、三种身份依据、运行状态 | bm_pages.py、detail_identity.py、observation.py、versions.py | test_real_details_states_hubs_configs_and_trusted_observation；test_hub_h3_missing_duplicate_wrong_host_and_outside_ignored；test_tab_and_config_identity_mutations_ignore_history_buttons |
| 真实 overview/history 结构 | fixtures/real_pages/ 七 HTML、README、manifest | test_real_overview_history_rows_and_fixture_hash_manifest |
| 架构变量白名单、首读冻结、清单核对 | build_inputs.py、bm_pages.py | test_diag28_arch_extras_reconcile_total_stays_submission_input；test_arch_specific_shelve_cl_does_not_cross_arch_and_total_coverage_required；test_missing_arch_list_fallback_but_empty_or_wrong_list_not_fallback；test_arch_whitelist_first_read_change_and_unselected_secret_not_stored |
| 快照架构 base 版本 | vd-fix-analyze/src/vd_fix_analyze/snapshot.py | test_snapshot_selects_arch_base_revision_not_total_revision |
| 精简 stdout、完整 artifact 与失败定位 | bm_reader.py、submit CLI | test_scan_page_errors_first_failure_and_summary_excludes_rows；test_lookup_cli_one_small_object_full_artifact |
| 非零无 error 子结果 | verify_b3a11.py（A/B1 共用 command） | test_verifier_nonzero_without_error_keeps_result_reason_artifact；test_b1_verifier_persists_result_reason_artifact_without_error |
| 归档与精确豁免 | evidence/scripts、archive-exemptions.json | test_archived_diag_hashes_and_exact_exemptions；原 test_archive_precheck 全套 |

旧合成详情夹具相应改成新 tab 结构；不伪称历史测试是新实页证据。B1.1 首读个数测试从 5 调整到 9（增加两架构四项缺失记录）。真实回归结果：19270912→37491096 failed ended；19206687→37376237 successful ended；19238877→37432138 failed ended；19091860→37174546 failed ended；19344434→37619264 running、未结束；配置均为 4362。overview 39 行均含 Hub ID，history 30 行且有 next。

### 证据、脱敏与 Q10

七页入站去空白 SHA256 与任务值全部相同。GitHub issue 展开 tab 导致原件中的逐页字节 SHA256 注释失效，不能把它们用于现有 HTML。B3a11-Q10 已闭合（设计方 2026-11-16）：仅 whole-token 替换剩余两种真实主机，Hub 共 10 处、BM 共 2 处，其余字节完全不变。测试显式使用 bm.example.invalid/hub.example.invalid 及占位 URL 模板。每页入站去空白摘要、次数、提交字节摘要见 fixtures/real_pages/README.md 与 manifest.json；独立变换核验见 evidence-b13/fixture-verification.json。历史 HLD/证据中的主机不在本批清理范围。新的常设授权写入 STATUS，不改变凭据规则。

归档原件（不执行、不改字节）：

| 路径（docs/enhance/evidence/ 下） | SHA256 | Q03 豁免 |
|---|---|---|
| scripts/diag28.py | 9cb35b2540ddc193041871ff422f03158b6341f0ebd610538d7cd810a1a4e13d | 第 19 行检测/脱敏正则，规则 2 |
| scripts/diag29.py | 0e20d3586acb12161c15485eedb78a1ec0eb089e7bf0bc115ce99f45434a9df0 | 第 14 行会话标识删除正则，规则 2 |
| scripts/diag30b.py | 63f11711e972fd1b479e85f6dca1b911ca87af2fecc9239f8a238bd5ee4688be | 第 48 行会话标识检测正则，规则 2 |
| diag29.txt | 357a32a2218401ffe7bd747b71d0fca6f1672eb29c3de20eed8ca5541b7b5a83 | 无 |

归档 registry 继续限定原路径、完整字节摘要、行号、精确文本/规则；JSON Unicode 转义只避免登记内容重复触发检查，解码值不变。无实际凭据豁免，运行时检查不变。

### 构建机命令

A+B1+B2 的入口与参数保持不变；将 EXPECTED_COMMIT 改为本次最终回报的完整提交号。使用现有 run/venv；VD_CONFIG / B21_SAVED_DIR / B21_ROWS / B21_LINKS / VD_CHROME 填构建机现有绝对路径，不把配置放进仓库。

```bash
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11_real.sh "$EXPECTED_COMMIT" --config "$VD_CONFIG" --saved-dir "$B21_SAVED_DIR" --rows "$B21_ROWS" --links "$B21_LINKS" &&
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11b1_real.sh "$EXPECTED_COMMIT" --config "$VD_CONFIG" &&
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11b2_real.sh "$EXPECTED_COMMIT" --config "$VD_CONFIG" --chrome "$VD_CHROME"
```

本地没有执行真实验收；B2 原有 8 项真实浏览器测试仍因缺 Playwright 而跳过，构建机 B2 要求它们执行，不能当作已通过。B1.3 不扩大 B2 点击能力，属性映射仍未确认。development-python310.txt 是修复过程中旧测试预期失败的历史日志；最终验证以 python310.txt / python312.txt 和 validation.json 为准。

B1.3 最终完整套件（import-linter 2.3、语法/标准库与静态边界全部通过；串行 nice 19，tmpfs 临时目录）：

| 解释器 | 结果 | 完整输出 | SHA256 |
|---|---|---|---|
| Python 3.10.12 | 300 项：292 PASS，8 SKIP（本机缺 Playwright） | `evidence-b13/python310.txt` | `2c99ceac28889c0bf18a9bc45a6e00f1b5f23991be912730ef7964975ebd3d37` |
| Python 3.12.3 | 300 项：292 PASS，8 SKIP（本机缺 Playwright） | `evidence-b13/python312.txt` | `fcac82d70d83ec0b06cc8cc6ed61d29b1def2e8b7927123c49c0a70932c0b370` |

源码摘要 source-manifest.json；原始归档核对 archive-verification.json；实际配置只读加载 config-load-check.json；最终凭据预检 prepush-final.json，均位于 evidence-b13/。Q10 已闭合，无未答复设计问题。

归档格式说明：git diff --cached --check 仅对七份原始 HTML 的末尾空行告警；按 Q10“其它字节不动”保留。其余变更无空白错误，不修改 Git 配置或文件摘要来消除此原件格式。


## Checkpoint B2.1 — 浏览器短临时目录与启动诊断（2026-11-16）

基线 `5f27d8a5f1ab967a1ff6d4898001462e77bba247`。设计方提供的 v5 构建机结果：Ubuntu 24.04、Chrome 156.0.8078.47、Playwright 1.64.1、Python 3.10.12；300 项中 292 PASS，8 个 headless 测试在 setUp 报 browser_start_failed。diag31（设计方本地诊断，未提供归档原件）表明默认 /tmp 下可启动，长验证目录 TMPDIR 导致 SingletonSocket 路径超限。本机未复现该真实环境，以下修复按设计方已定位的原因实施。

### 实现与测试对应

| 要求 | 实现文件 | 测试 |
|---|---|---|
| 独立短 TMPDIR；XDG 所有者、0700、字节长度检查；回退 /tmp；超限退出 6 | `vd-cosmos-core/src/vd_cosmos_core/browser_temp.py` | `test_batch3a11b21.BrowserTempTests.test_private_owned_xdg_preferred_and_environment_child_only`、`test_xdg_missing_public_long_relative_and_symlink_fall_back`、`test_xdg_wrong_owner_falls_back`、`test_socket_length_is_bytes_strictly_under_100_and_refuses_before_launch` |
| 只改浏览器子进程 TMPDIR/TMP/TEMP，父环境保持；成功 close 清理 | `vd-cosmos-submit/src/vd_cosmos_submit/playwright_driver.py` | `test_successful_launch_passes_private_env_and_close_removes_temp` |
| 崩溃恢复/finish；进程关闭核验先于删除；身份不一致保留供恢复 | `browser_temp.py`、`vd-cosmos-core/src/vd_cosmos_core/submit_sessions.py` | `test_finish_and_recovery_close_processes_before_removing_short_temp`、`test_failed_process_cleanup_keeps_marker_and_temp_for_recovery`、`test_cleanup_identity_mismatch_refuses_then_valid_cleanup_is_idempotent` |
| 六个阶段、异常类型、最多三行；整段先检查凭据、命中不输出 | `playwright_driver.py` | `test_each_launch_stage_is_reported_and_failed_launch_cleans_temp`、`test_three_lines_only_with_full_message_credential_check`、`test_forced_launch_failure_with_credential_withholds_detail` |
| 长于 120 字符的继承 TMPDIR 下启动真实 Chrome | `vd-cosmos-core/tests/test_batch3a11b2_headless.py` | `HeadlessTempTests.test_long_inherited_tmpdir_starts_with_short_browser_only_temp`（本机缺 Playwright，SKIP；构建机强制执行） |
| 测试与验收器共用浏览器选择规则，记录 executable | `vd-cosmos-core/src/vd_cosmos_core/browser_executable.py`、`verify_b3a11b2.py`、headless 测试 | `test_executable_override_and_default_use_resolved_wrapper`；原 `test_requires_real_browser_tests_in_fresh_root_no_live_calls` |

未写完整模块名的新增测试位于 `vd-cosmos-core/tests/test_batch3a11b21.py`。

短目录创建前先检查 XDG_RUNTIME_DIR 为当前 UID 所有的规范目录且 mode=0700（符号链接/非规范路径保守回退）；创建后再次检查 `os.fsencode(<dir>/.org.chromium.Chromium.XXXXXX/SingletonSocket)` 长度严格小于 100。目录始终 mode=0700。恢复用的 `browser-temp.json` 位于既有私有 profile 下，在浏览器启动前原子记录目录路径/device/inode/uid；恢复不依赖新进程的 XDG 环境，先确认浏览器进程已关闭，再核对目录身份后删除。旧 profile 没有该记录时仍可按原流程清理。目录身份不符或进程未关闭则保留目录和记录、拒绝继续清理。

异常细节仅来自 about:blank 启动阶段：start / launch_persistent_context / new_page / route / cdp / fetch_enable。保留 `FlowError(5, browser_start_failed)`，details 包含 exception_type、stage、detail。先对完整错误做运行时 check_content，再截前三行（每行最多 600 字符）并复检；查询/fragment URL、Cookie、密码等赋值和 profile JSON 诊断另作保守拦截。命中或检查失败统一 detail withheld；不读取 profile 内容，也不改任何运行时凭据配置或豁免。

验收器与测试都优先显式 --chrome / VD_COSMOS_CHROME，否则解析已安装 google-chrome（含 google-chrome-stable）wrapper，最后才查已有 Chromium 路径；不再把 /opt/google/chrome/chrome 当默认。测试分别记录 selected 与真正成功 launched 的 executable，避免把选择当成启动成功。本机选择 `/home/toolchain/.local/bin/google-chrome`，因缺 Playwright 没有 launched 记录。构建机显式传 `/opt/google/chrome/google-chrome` 时整套测试使用其解析路径。

附带修正验收汇总的一处既有类型错误：offline_tests 返回 artifact 字典，原代码把整个字典交给 Path；现从 artifact['path'] 计算摘要。原 verifier 测试改为模拟真实 artifact 返回类型，避免浏览器测试通过后汇总仍报错。无新增配置、无安装、无 PHP、无真实服务/提交/演练。无新增 B3a11-Q11 问题或假设。

### 完整验证与构建机重跑

两解释器串行运行 `vd-cosmos-core/scripts/run_tests.sh`，nice 19，临时测试目录在本机 tmpfs；每份输出第 1 行为真实解释器版本，包含 import-linter==2.3 三条约束与浏览器静态边界检查。共新增 12 个普通测试和 1 个真实浏览器测试。

| 解释器 | 结果 | 完整输出 | SHA256 |
|---|---|---|---|
| Python 3.10.12 | 313 项：304 PASS、9 SKIP | `evidence-b21/python310.txt` | `c5d6a10c396dcfbda1c127d6241b263af4a17d3afa6910deb1053d100a425822` |
| Python 3.12.3 | 313 项：304 PASS、9 SKIP | `evidence-b21/python312.txt` | `a036197fca98286afc419005a55a1a13e64d3966b3d534517e010bafa4d11520` |

9 项 SKIP 为原有 8 个本地服务器 headless 闸门测试及新增长 TMPDIR 测试，均仅因当前两套解释器缺 Playwright。它们没有被声明为通过；`VD_REQUIRE_HEADLESS=1` 将缺依赖改为失败，构建机 B2 verifier 已强制该标志。源码清单见 `evidence-b21/source-manifest.json`，结果索引 `validation.json`，最终凭据检查 `prepush-final.json`。

A/B1/B2 验收入口参数不变。使用构建机现有 run/venv，将 EXPECTED_COMMIT 填为本次回报的完整提交号，VD_CONFIG 为真实配置绝对路径；本次 B2 回归命令：

```bash
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11b2_real.sh "$EXPECTED_COMMIT" --config "$VD_CONFIG" --chrome /opt/google/chrome/google-chrome
```

该入口只跑 contract、静态检查和完整离线套件（强制 9 项真实 headless 本地测试），不连接真实 Cosmos/Hub/P4，也不调用 live once/rehearse。B2 属性映射未确认的既有限制保持。


## Checkpoint B2.2 — 回调不等待、测试看门狗、验收进程清理与沙箱（2026-11-17）

基线 `2d2fc7c7446999b58f77e4fd6fc7c6b04949ae37`。设计方 v6 构建机反馈：B2.1 已解决长 TMPDIR 启动问题；隔离运行时长 TMPDIR 测试通过，WebSocket 测试在同步回调里的 close() 卡住，A 完整套件达到 3600 秒。此前只杀 shell，留下 unittest/Chrome；Chrome 默认带 no-sandbox。此为设计方提供的实测结论，本机没有访问构建机或重新执行真实服务检查。

### 回调审计与实现

`vd-cosmos-submit/src/vd_cosmos_submit/playwright_driver.py` 顶部明确：注册回调不得调用同步 Playwright 方法，主流程才允许等待。

| 注册位置 / 回调 | 处理方式 |
|---|---|
| context.route / _route | 只读缓存的 request/frame 属性，调度 coroutine abort/continue 后立即返回 |
| context.route_web_socket / _websocket | 不连接、不 close、不读帧；保持 mocked/unconnected。CDP Fetch 的拒绝规则仍保留 |
| context.on('page') / _new_page | 非主页面只调度 coroutine close，不同步关闭 |
| CDP Fetch.requestPaused / _paused | 原闸门计算与请求归属保持；CDP continue/fail 只调度，不在回调等待 |
| asyncio Task done / _deferred_done | 仅检查已结束任务是否失败；失败记固定 browser_callback_dispatch_failed，不保存异常文本 |

同步 API 没有公开的 fire-and-forget 入口，因此仅在适配器 `_defer` 中使用 Playwright coroutine implementation 的 `_impl_obj` / `_loop.create_task` 桥接；只允许 abort/continue_/close/send，要求实现方法为 coroutine 且循环运行中。不兼容时记固定失败、保持请求阻断，绝不退回同步回调调用。静态检查同时约束 deferred CDP 方法白名单。脚本化异步实现测试证明回调返回时没有调用 sync facade、调度动作随后执行；真实 Playwright 1.64.1 上的回调桥仍由构建机强制测试验证。

所有 launch（headless/headed）显式 `chromium_sandbox=True`。明确 sandbox/zygote/namespace 启动错误映射为 `FlowError(6, browser_sandbox_unavailable)`，带 B2.1 凭据检查后的阶段诊断；其它启动错误保留 browser_start_failed。没有不带沙箱的重试或降级。新增真实测试从本 profile 的进程开始，沿 /proc 父子关系检查整棵浏览器树的 argv 不含 no-sandbox。

### 有界测试和验收器

`vd-cosmos-core/tests/headless_watchdog.py` 将每个真实浏览器测试（含 setUp、测试方法、tearDown/cleanups）放在独立解释器进程运行，90 秒硬限，85 秒先 faulthandler 打印全部 Python 线程栈；普通失败/异常也打印全部线程栈。正常失败仍执行 unittest 的 Driver.close 清理。卡住则外部父进程执行 TERM/KILL 清理整个组和逃出组的浏览器，失败消息明确 watchdog expired；不会再次在卡死的同步 API 中尝试关窗。超时后的 profile 临时目录登记也进入清理。依赖缺失仍可 SKIP；构建机 VD_REQUIRE_HEADLESS=1 时必须失败，不能跳过。

`vd-cosmos-core/src/vd_cosmos_core/verification_process.py` 为 A/B1/B2 共用：

- suite/skill CLI/static 子进程用 start_new_session=True；记录独立验证目录标记。超时 TERM 整个组，最多等 10 秒，再 KILL 整个组并回收直接子进程。
- /proc 扫描限当前 UID，按环境或 argv 中验证目录、profile、登记的短 temp 路径边界匹配，发信号前再核对 PID start time；捕获浏览器 wrapper setsid 后脱离原组的进程。环境/argv 内容不落盘、不打印；无关进程不匹配。
- stdout/stderr 用 selector 持续消费，按完整行、检查累计文本后才 flush 到 artifact；不完整行留在内存，EOF/超时时检查后再写。不会把拆成多个 read 的凭据先写一部分值到磁盘。超时仍返回 acceptance_process_timeout 与已检查 transcript 的路径/大小/SHA256。
- offline-tests.txt 在运行期间可读，A/B1/B2 超时结果包含 output_artifact/test_output。普通 CLI 留 command-*.txt；B2 static 留 static-scan.txt。A 复用的 verify_b2 E-loop 也改为同一执行器，留 E-loop.txt/E-loop.json。Git 本地元数据读取同样独立 session。

实现的运行时依赖仍仅标准库；浏览器 coroutine 桥留在唯一 optional adapter 内。未运行真实服务或 live once/rehearse，属性映射未确认限制不变，无新增设计问题或 B3a11-Q12 假设。

### 测试对应

新增普通测试均在 `vd-cosmos-core/tests/test_batch3a11b22.py`：

| 要求 | 测试名 |
|---|---|
| 回调不用 sync facade，异步动作仍执行 | test_callbacks_never_invoke_sync_facade_and_coroutines_complete |
| 桥缺失 / coroutine 错误拒绝继续 | test_missing_async_bridge_and_async_failure_fail_closed |
| 注册回调不含同步调用或 WebSocket connect | test_registered_callbacks_have_no_sync_calls_or_websocket_connection |
| 显式开启沙箱，无降级；sandbox 错误退出 6 | test_launch_enables_sandbox_and_known_sandbox_failure_is_exit_6 |
| 普通孙进程 + setsid 孙进程忽略 TERM；KILL 清理；超时前输出可读 | test_timeout_kills_group_and_detached_browser_and_preserves_stream |
| 分段凭据不写文件 | test_streaming_never_persists_split_credential |
| 套件超时 artifact 传给验收结果 | test_timeout_artifact_propagates_through_offline_suite |
| 只凭 profile argv 定位逃逸进程、不选无关进程 | test_detached_path_only_match_does_not_select_unrelated_process |
| 故意卡住的测试有 deadline、栈输出、明确 failure | test_hung_test_has_deadline_stack_dump_and_failure |

真实测试 `test_batch3a11b2_headless.HeadlessGateTests.test_service_worker_and_websocket_cannot_open_channels` 保留 server request count=0 判据；新增 `test_browser_process_tree_never_disables_sandbox`。该模块全部 10 项走同一 watchdog；本机缺 Playwright，因此这 10 项未实际运行。B2.1 的 12 个普通测试、三个 verifier 原有测试均包含在完整套件。

### 完整套件与构建机命令

串行 nice 19、tmpfs 测试目录，运行 run_tests.sh；每份输出首行为真实解释器版本，含 import-linter==2.3 三条约束和浏览器静态检查。子进程的单测试汇总也保留，最终统计看文件末尾 323 项汇总。

| 解释器 | 结果 | 完整输出 | SHA256 |
|---|---|---|---|
| Python 3.10.12 | 323 项：313 PASS、10 SKIP | `evidence-b22/python310.txt` | `8fb2be519ecd35f68a68f73a1c4f4d58a50d63eec7a5aa6fc73dad4eefdf1b67` |
| Python 3.12.3 | 323 项：313 PASS、10 SKIP | `evidence-b22/python312.txt` | `4728cdcbe71c35b16a41ba2e4a1ffc83312829456dc3ce923dd4ef2fba234795` |

源码摘要 `evidence-b22/source-manifest.json`；结果索引 `validation.json`；最终凭据预检 `prepush-final.json`。10 项 SKIP 都因本机缺 Playwright，不声称真实 WebSocket 或沙箱检查通过。构建机使用现有 run/venv（已有 Playwright/Chrome），EXPECTED_COMMIT 替换为本次回报完整 hash；A/B1/B2 命令参数保持不变：

```bash
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11_real.sh "$EXPECTED_COMMIT" --config "$VD_CONFIG" --saved-dir "$B21_SAVED_DIR" --rows "$B21_ROWS" --links "$B21_LINKS" &&
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11b1_real.sh "$EXPECTED_COMMIT" --config "$VD_CONFIG" &&
nice -n 19 bash vd-cosmos-core/scripts/verify_b3a11b2_real.sh "$EXPECTED_COMMIT" --config "$VD_CONFIG" --chrome /opt/google/chrome/google-chrome
```

B2 会强制全部 10 项真实 headless 本地测试。这里只提供 FatTank 构建机执行命令，本机没有运行这些真实验收步骤。
