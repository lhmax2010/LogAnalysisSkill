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
