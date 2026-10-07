# E11 第一阶段停止报告

日期:2026-10-07。权威SHA `b9d720028164faec8c91d87a02cfa75475e1f8e1fff86e8244a2c0ef55bedaf0`。
固定HEAD `43a6aa625f27da46daba190657bf62256080c68e`;
tree `ca9331190e878af465e7968fe56e735585a5866e`。
SCAN-09依E11-5已被取代关闭,本报告不继续旧静态候选工作。

## PHASE1-01:枚举全集与调用契约未闭合

原文:冻结稿E11-2②:2481-2483要求live全部PY_SOURCE中,除
mark_worktree_protected外引用PROTECTED_FILENAME的全部函数。
判定条件v1.2 B-1:192-208要求每个中断场景逐一记录全集的实际返回/异常;
冻结稿§6:1535-1539要求记录读取该protected marker的结果。

实跑命令与原始输出: `reader-enumeration.command.json` / `reader-enumeration.log`。
完整函数体、参数、引用点及逐文件扫描记录: `B-1-anchors.json`。

```text
live_py_source=177 excluded_non_live=95 protected_marker_readers=14
EXIT=0
```

| 文件(固定tree相对路径) | 函数:行 | 参数 |
|---|---|---|
| tests/integration/test_build_verify_real_git.py | test_protected_marker_is_transparent_to_real_git_dirty_checks:360 | tmp_path |
| tests/unit/test_tizen_build_verify.py | test_pass_writes_verification_record_and_commits_before_build:208 | tmp_path |
| tests/unit/test_tizen_build_verify.py | test_marker_write_exception_propagates_before_db_write_and_leaves_clean_copy:619 | tmp_path, monkeypatch |
| tests/unit/test_tizen_build_verify.py | test_db_write_exception_propagates_after_marker_and_preserves_protected_copy:640 | tmp_path, monkeypatch |
| tests/unit/test_tizen_gerrit_submit.py | _record:129 | tmp_path |
| tests/unit/test_tizen_gerrit_submit.py | test_gerrit_submit_all_subprocess_paths_omit_timeout:223 | tmp_path |
| tests/unit/test_tizen_gerrit_submit.py | test_gerrit_submit_converts_ls_remote_timeout_to_unverified_warning:385 | tmp_path |
| tests/unit/test_tizen_gerrit_submit.py | test_release_verified_worktree_removes_protection:497 | tmp_path |
| tests/unit/test_tizen_gerrit_submit.py | test_release_verified_worktree_reports_not_protected:520 | tmp_path |
| tests/unit/test_verify_workspace.py | test_mark_worktree_protected_writes_audit_marker_and_is_status_transparent:167 | tmp_path |
| tizen-ci-shared/scripts/tizen_ci_shared/workspace/__init__.py | clean_repository_preserving_markers:55 | worktree_path |
| 同上 | release_worktree_protection:130 | worktree_path |
| 同上 | is_protected:140 | worktree_path |
| 同上 | _exclude_private_files:209 | worktree_path |

不是漏匹配或只遇首例即停:全部live PY_SOURCE已枚举,10个函数在测试文件内。
例如`_record:129-166`自行创建repo/DB并在:162写入完整marker;
集成测试:360-374也自行create_worktree并mark_worktree_protected;
build-verify测试:208起从_options创建环境再执行build_verify。
它们不是接收已有中断worktree的查询函数。其余4个生产函数也含释放/清理/
exclude写操作,不能默认共用同一份可变fixture后顺序调用而不规定隔离。

缺口:未给出如何将各函数的tmp_path/monkeypatch绑定到两个中断场景,
亦未规定fixture自建/写入副作用与被观测失败态的关系。
直接无参调用取TypeError可满足result_kind语法,但不是读取marker;
把tests从枚举中排除又违反当前E11范围。两种做法均未执行。

候选(均待裁决):
1. 明确生产读取方的可执行selector、角色及调用输入,并同步第7条全集来源;
   不能仅由实现方把14项缩成某个手选集合。
2. 保持14项全集,规定逐函数调用适配、测试fixture绑定及独立失败态副本,
   确保记录的是对应中断marker的观测,不是新建环境的测试结果。

item5 producer/verifier未运行;没有人为构造PASS或声称claim已红。

## PHASE1-02:全仓回归被旧静态工具hash钉定阻塞

原文:E11-2③要求全仓回归全绿;E11-3(5)/E11-5停用旧静态机制门禁但保留工具。
`terminal_scan.py:30`仍钉E10 `37862f4a...`;`terminal_registry.py:31-34`
从当前权威路径读取并强制等于该hash。新权威E11无法同时满足。

全仓命令与逐nodeid原文: `whole-repo-pytest.command.json` / `whole-repo-pytest.log`。

```text
collected 1305 items
14 failed, 1290 passed, 1 skipped in 23.36s
EXIT=1
```

全部14失败均为`terminal_scan.ScanError: RULES_HASH`,来自
test_terminal_registry与test_terminal_import_linter,完整失败清单在日志末尾。
未改任何生产代码,未skip/删旧测试,未更新旧工具pin以掩盖失败。

候选(待裁决):将停用工具的历史回归锚定E10不可变blob;或明确允许机械更新pin,
以含全部历史文本的E11为载体继续运行旧工具单测。二者的后续维护语义不同,
本轮不擅自选择。全仓红后停止A/B及后续阶段,CI包mypy/全仓ruff/lint未运行。

## 已完成与未做

- 入库对比:两个追加hunk、65新增、0删除;hash精确匹配;SCAN07及结构来源绿。
- 枚举器人工正控制/near-miss与覆盖控制:4 passed,exit0。
- 冻结判据、exemptions、预期差异表、既有OBS均未修改。
- 30场景改前实跑仍PENDING_SEG3;A/B零生产改动;第二阶段清单/OBS5未开始。
- 本轮提交仅勘误、枚举器及控制、登记和完整停止证据,不是第一阶段完成提交。
