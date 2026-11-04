# 恢复第1批用例对照

权威:SKEL-RESTORE-01第一批、design.md第3.4/4.1节及Phase7 DoD。
实现:core.diff_to_edit_spec转换,repair.diff_cli共享JSON命令入口;
`python -m tizen_campaign_repair diff-to-edit-spec`与旧`ci_triage`入口调用同一函数。
不调用git apply、不修改源码,不以修订guard放行;层级歧义与不精确hunk均拒绝。

测试文件统一为`tests/unit/test_diff_to_edit_spec.py`,下表nodeid前缀相同。

| 条目 | 用例 | 数量 |
|---|---|---:|
| 普通/Git/P4/OBS/时间戳头,真实guard通过,源码字节不变 | test_headers_and_real_guard | 5 |
| 唯一-p层级,两个现存路径时拒绝而不按内容猜测 | test_unique_strip_level_and_ambiguity | 1 |
| 同文件多hunk不重叠,重复old补line | test_multiple_hunks_and_duplicate_old_anchor | 1 |
| 多文件与唯一old不加line | test_multifile | 1 |
| 无末尾换行原文保留 | test_no_final_newline | 1 |
| P4双路径重命名/binary明确拒绝,同路径不同revision通过 | test_p4_metadata_not_discarded、test_p4_same_path_revision_pair | 3 |
| 重命名/复制/二进制两种/模式变更/新建/删除 | test_unsupported_git_shapes | 7 |
| /dev/null新建删除、不同文件名、上下文错、偏移/模糊、纯插入空old、行数错、重叠、无修改、空diff | test_no_guessing_unsupported_shapes | 13 |
| 绝对/父目录逃逸/.git/不存在/目录 | test_unsafe_paths_and_nonfiles | 8 |
| 符号链接未越界通过,越界由真实guard拒绝 | test_symlinks_inside_allowed_outside_rejected | 1 |
| 真实guard schema/必填字段/line/路径/非普通文件/无line重复old/单行锚点/重叠全部拒绝 | test_real_guard_rejection_matrix | 18 |
| 发布前guard拒绝不覆盖已有输出;临时文件清理;共享入口exit4 | test_cli_publication_and_shared_entry | 1 |
| 新旧入口同参数错误逐字JSON与exit2一致 | test_invalid_args_same_json_and_exit | 3 |
| 禁止覆盖输入,空patch_name参数错 | test_input_hashes_unchanged_and_empty_patch_name | 1 |
| 合计 | | 64 |

`focused/`为最初61个定向用例归档,后补3个P4元数据用例,`focused-final/`为64 passed;
`full-final/`为最终3163 passed/0 failed/1既有skip,全部新增用例通过。
原3100个nodeid全部保留。guard、代理、审核、安全核心与冻结稿均未修改。
纯插入且hunk无上下文时old为空,与guard非空old契约不兼容,明确unsupported,不凭空补源码。
CLI成功时原子发布已校验JSON;失败JSON含error_code与reason,unsupported为exit4,参数/IO为exit2。
