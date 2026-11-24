# 第 3a-2 批交付记录

## C1 任务包、证据清单、适配层

| HLD | 实现 | 测试 |
|---|---|---|
| §6.1 第 2 条 | `analysis_tools.py` 调用已有 LogAnalyzer JSON 接口，保留原始路径，编译器/Werror 才调用 patch-suggest。阶段与命令线索分别记录。 | `test_actual_adapter_preserves_path_and_uses_patch_context_only_for_compiler` |
| §6.1 第 3–5 条、§4.5、§9.2 | `task_package.py` 核对状态库日志与快照凭据，记录整文件覆盖的原始字节区间及摘要，按种类标段；历史工件与登记状态分离，只读输入，有限重试。团队规则用冻结 HLD 附录 A，R08 骨架由本线生成。 | 上述测试及 `test_attempt_limit_and_tampered_input`、`test_wrong_build_and_unregistered_raw_log_refused` |

- B3a2-Q01 assumed: 没有显式最终日志摘要关联的历史快照保留为诊断材料；不据此产生可编辑来源。新快照登记日志摘要，精确匹配才沿用可编辑标记。
- B3a2-Q02 assumed: 任务包的自由文本只作为参考；工具事实只能引用经登记的包与通知字段或已核验字节切片。备选工具输出和分析结论不得升格为工具事实。

## C2 结果接收与修改守卫

| HLD | 实现 | 测试 |
|---|---|---|
| §6.2–§6.3、§9.2 | `analysis_result.py` 校验封闭 schema、证据 ID、当前 attempt 和输入、拒绝重复接收，凭据及注入文字只留拒绝原因。 | `test_receive_once_without_authorization_events`、`test_extra_duplicate_truncated_size_and_foreign_evidence_fail`、`test_injection_and_symlink_rejected_without_echo`、`test_changed_final_log_expires_prior_attempt` |
| §7.5 / 附录 A R08、R28 | 只接收登记的可编辑原文片段；生成 edit spec、调用现有 formatter 验证候选补丁；R08 检查 spec，R28 检查已人工定性的真 bug，不把 AI 的 false 当裁决。 | `test_repair_formats_checked_candidate_without_modifying_snapshot`、`test_r08_and_r28_reject_unsafe_or_unconfirmed_edits`、`test_edits_only_on_exact_editable_sources` |

- B3a2-Q03 assumed: 无案例检索阶段的 `knowledge_refs` 必须为空；带未知位置或不唯一原文的候选修改一律拒收。
- B3a2-Q04 assumed: 已人工定性的真 bug 才触发 R28 拒收；结果里 AI 的是/否均无裁决权限。待定性和位置粒度在 C3 接入。

## C3 诊断族、位置与方案对比

| HLD | 实现 | 测试 |
|---|---|---|
| §6.3 诊断族、位置, §11 | `diagnosis.py` 只从编译诊断行提取规范化选项，逐位置登记上下文摘要；按 base primary repodata 的完整 Clang 版本-发布号导入清单。缺版本或清单时告警，未知的强制档子标志临时升档。 | `test_version_release_exact_match_and_prefix_only_upgrades` |
| §6.3、§9.8 | `analysis_result.py` 按位置的人工定性与数据摘要计算状态；`analysis_comparison.py` 分列 AI 主张、批准、实际 CL 与验证。 | `test_comparison_table_labeling_and_escaped_text` |

- B3a2-Q05 assumed: 本批无 base 仓库下载或源码包下载；精确的已获取 primary repodata 放入轮次输入（也可用 `--primary-repodata` 指定数据根下的同份文件），缺失时标未核实并开启临时升档。没有运行 sudo、chroot 或真实 diagtool。
- B3a2-Q06 assumed: R28 的已定性真 bug 在一个包内保守拦截选项类候选；不同输入的所有定性重新判定。人工写定性命令仍属 3a-3。

## C4 工作区、命令守卫、待办与 tick

| HLD | 实现 | 测试 |
|---|---|---|
| §6.4、§4.5 | `analysis_workspace.py` 安装并登记只读独立 skill，登记可选金丝雀与全局配置摘要。接收时拒绝目录变化、额外 skill 和摘要变化，作废旧 attempt。 | `test_sealed_skill_and_modified_skill_permanently_invalidate_attempt`、`test_canary_inventory_does_not_open_existing_skill_files` |
| §6.4、§0.5 | 人工/外部写命令和 submit lookup 走进程祖先检查。接收器仍只追加分析收/拒事件。 | `test_human_ancestor_guard_is_applied_before_prompt` 和已有 non-TTY/伪进程表测试 |
| §6.4、§9.2 | tick 从当前最终日志与已登记快照生成一个任务；投影与读取阶段分列；登记独立的待分析任务数，分析接收后清掉已处理的提醒。 | `test_tick_projects_tasks_and_accepted_results_and_updates_inbox` |

- B3a2-Q07 assumed: 扩展模式由 FatTank 负责监督，生成器只记录可复核的金丝雀存在性、清单摘要和配置摘要，默认隔离未验证。已有 round 的分析 skill 与登记不符时拒绝使用；不自动覆盖、放开目录或启用自动批准。
- B3a2-Q08 assumed: tick 只消费已下载并验证的最终日志和已登记快照，不自动做新 P4 读取。跨包转交只关联已有可信任务；目标尚无可信输入时另列待办，不从分析者的文本制造目标快照。

## C5 构建机分析验证及 FatTank 手册

| HLD | 实现 | 测试 |
|---|---|---|
| §6.1–§6.4、§11 | `verify_b3a2_real.sh`/.py 核对 HEAD，读取原状态库文件的稳定副本，把已下载、已登记工件复制到隔离位置，验证所有分段清单，并接收一个手写 fixture。 | `test_verifier_copies_existing_inputs_and_only_accepts_fixture_in_scratch`、`test_missing_snapshot_refuses_without_fetch`、`test_wrapper_refuses_wrong_head_before_loading_config` |

- B3a2-Q09 assumed: 验证器找不到唯一构建、已登记的完整失败日志或匹配快照就停止，不进行任何补拉、P4 或浏览器操作。fixture 回执不会进入正式轮次投影。
- B3a2-Q10 assumed: 接收时只核对实际登记任务的 SHA256；外部扩展提供的 prompt 摘要属于来源声明，工具本身未看到该模型会话。金丝雀与 ClineSR 实际演练由 FatTank 现场复核。

- B3a2-Q11 assumed: 已确认真 bug 的修改须在真实新增注释中写 `PLEASE CHECK` 与有值的 Before / Why（也可用“原来 / 原因”）；语义仍由人工核实。替换的快照与新最终日志一样使输入过期，无需等到新任务生成。

运行命令及监督步骤见 [FATTANK-3A2-MANUAL.md](FATTANK-3A2-MANUAL.md)。每个检查点两套 unittest、导入合同、静态检查及凭据预检在 `evidence-c1/` 至 `evidence-c5/`。每个目录的 `test-summary.json` 登记日志路径与 SHA256。真实构建验证未由本机执行。

## B3a2.1 构建机 v12 复测修补

`e7bdf9b` 的构建机 Python 3.10.12 缺少 `_lzma`。诊断模块在 CLI 启动时导入该扩展，A/B1/B2 在合同阶段退出 5，C 在模块加载时退出 1。

- repodata 解码器按后缀载入所需模块。常规输入继续用 `.gz`；读取 `.xz` 而 LZMA 不可用时退出 6，并带待办 `use the .gz repodata or a Python built with liblzma`。BZip2 缺失也有独立待办。SQLite、TLS、文件锁和浏览器子进程的可选扩展在操作边界处理。
- 合同失败记录 `stage`、`command`、`exception_type` 和通过凭据预检的 `first_line`。`doctor.optional_stdlib` 报告 `lzma`、`bz2`、`sqlite3`、`ssl` 能否实际导入。
- `run_tests.sh` 先执行标准套件，再禁用 `_lzma` 和 `_bz2` 执行完整套件。测试也向每一个 CLI 合同子进程传入禁用扩展的钩子。详细输出和摘要见 `evidence-b3a21/`。
