# SKEL-RESTORE-16 离线实现与门禁

基线40e4d9d,本目录只含离线/本机测试证据。没有真实QuickBuild读取或登录。
裁定全文与实现说明见stage21 progress第40节;旧RESTORE-13/15证据未覆盖。

## 实现范围

| 位置 | 变化 |
| --- | --- |
| `tizen-qb-verify/scripts/tizen_qb_verify/qb_redact.py:407` | 单项/复合Welcome登记,同页完整配对补全;原始HTML值区间替换 |
| `../discovery-capture/capture_archive.py:53` | 私有根与权限、原始字节/解码文本保存、失败保留与离线重做 |
| `../discovery-capture/capture_archive.py:115` | 浏览器清理后登记与归档,封闭阶段失败,全目录身份扫描,成功删除 |
| `../discovery-capture/redact_capture.py:15` | worker协议与不联网的--replay入口 |
| `../discovery-capture/capture.mjs:221` | 读取只store;259/267行关闭检查后finish;网络/安全检查不变 |

生产代理、驱动、sandbox-submit、qb-trigger、qb-result-fetch、review-submit、
安全核心和冻结稿没有变化,hash记录在inputs.json的protected中。
代理完整hash:`431b27137c857f5089053737b320ea35f2317d66493892b3dec5f7608db2e26c`;
前缀hash:`1708c9567418043345c6f8a1e875aff93e1f21ce627540583f734fc5eeafb2ed`。

## 定向覆盖

`focused/pytest.xml`:43 passed,0 failed,0 skipped(22.87s)。
27个Session/字节保护用例、15个私有归档用例、1个浏览器包装(内部10个Node测试)。

| 裁定要求 | 测试位置 |
| --- | --- |
| 单账号、单显示名、复合形式 | `test_restore_capture_redaction.py::test_single_and_compound_welcome_are_complete`;`test_restore_capture_archive.py::test_private_first_permissions_zero_residue_and_delete` |
| 同页配对补全,不登记其它用户/注释别名 | `test_pair_completes_only_matching_text_and_attribute_values`;`test_session_identity_must_not_be_inferred_from_other_users` |
| 标签/属性名不误改,CR原字节保留 | `test_identity_fragments_never_rewrite_html_names`;`test_private_first_permissions_zero_residue_and_delete` |
| Welcome缺失或空 | `test_missing_welcome_retains_private_originals` |
| 其它五阶段固定失败与敏感输出扫描 | `test_closed_stage_failures_preserve_raw_and_hide_exception` |
| 0700/0600,仓内无原文,成功删除 | `test_private_first_permissions_zero_residue_and_delete` |
| 整目录残留阻断,保留后离线重做 | `test_whole_directory_scan_blocks_then_offline_replay` |
| 浏览器/profile清理之前不得脱敏 | `test_no_offline_redaction_before_cleanup`;Node每次close前断言输出目录为空 |
| 私有根不在仓内,禁止符号链接 | `test_private_directory_must_not_be_in_repository`;`test_private_directory_symlink_is_rejected` |
| 脱敏失败不打断三页读取 | `offline.test.mjs` no-welcome:三页均到假服,然后IDENTITY_EMPTY,正文零归档 |
| 原网络失败规则 | 同Node套件foreign、307、attachment用例保持对应拒绝;只允许唯一主帧请求 |

## 门禁与完整性

每项command.json包含argv、UTC起止、exit、loadavg与CPU前十(只记名称/占用)。
`run_gates.py`运行完整pytest,不加-x。最终结果汇总见summary.json。
全仓**3453 passed,0 failed,1既有skip**,1152.14s;loadavg前2.43/2.57/2.29,
后5.52/4.17/3.58,20核。C5a六参数、C8调查、字段窗口与四组安全测试封装均通过,
无计时敏感重跑、无新增失败观测。mypy169源码通过、ruff通过、7项import合约通过,
design检查0 problem。`cleanup.json`:P5Q进程/profile均0,没有真机私有run。
暂存diff检查只报C5a响应HTML原字节的23处行尾空格,保留不格式化;
其它文件检查exit0,清单见`diff-check.json`。
`inputs.json`为门禁开始时全部已有源码及本轮新源码hash;
`integrity-after.json`核对门禁期间未改实现。
`archive-scan.json`对整个discovery-capture目录进行历史身份残留检查:44文件,残留0,
身份仅在内存读取,未输出或改变旧正文。未来真机仍需重新登记当前会话并扫描。

下一步是等待用户确认“开始”,不是立即执行真机。仅允许剩余三页的单次取证,
之后仍按RESTORE-08四条件分叉,不把本轮离线成功当作取证事实齐备。
