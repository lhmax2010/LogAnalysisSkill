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
