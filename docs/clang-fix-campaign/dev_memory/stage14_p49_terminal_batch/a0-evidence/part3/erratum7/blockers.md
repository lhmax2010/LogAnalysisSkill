# E7-3 全树 PY_SOURCE 预检阻塞清单

来源:固定 HEAD `43a6aa625f27da46daba190657bf62256080c68e`,tree `ca9331190e878af465e7968fe56e735585a5866e`;权威 SHA `d6496250c3f9ba80990785edab0e972c9b077fd4965a045cea31e3201bd7c032`。

以下表由 preflight-final.json 机械生成,不是手工豁免清单。

| 文件:行:列 | 上下文 | 被调限定名/读取对象 | 命中数 | 原因 |
|---|---|---|---|---|
| `release-v1.4.0/tizen-ci-triage/scripts/ci_triage/gerrit.py:64:42` | `release-v1.4.0` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `release-v1.4.0/tizen-ci-triage/scripts/ci_triage/gerrit.py:155:42` | `release-v1.4.0` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `release-v1.4.0/tizen-ci-triage/scripts/ci_triage/runner.py:74:42` | `release-v1.4.0` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42` | `release-v1.4.0` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:75:42` | `release-v1.4.0` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `release-v1.4.0/tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:83:42` | `release-v1.4.0` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `release-v1.4.0/tizen-gbs-build/scripts/gbs_build_skill/runner.py:286:36` | `release-v1.4.0` | `subprocess.Popen` | 0 | 非调用读取,正文②′无形态承接 |
| `release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/analyzer_runner.py:35:42` | `release-v1.4.0` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:98:42` | `release-v1.4.0` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:177:42` | `release-v1.4.0` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `tests/integration/test_build_verify_real_git.py:203:26` | `.` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `tests/unit/test_design_drift_ledger.py:18:4` | `.` | `importlib.machinery.SourceFileLoader.exec_module` | 0 | 受监控调用,不在任何形态封闭被调者集合 |
| `tests/unit/test_tizen_build_verify.py:400:26` | `.` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `tests/unit/test_tizen_build_verify.py:573:15` | `.` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `tests/unit/test_tizen_build_verify.py:599:15` | `.` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `tests/unit/test_workflow.py:28:4` | `.` | `importlib.machinery.SourceFileLoader.exec_module` | 0 | 受监控调用,不在任何形态封闭被调者集合 |
| `tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42` | `.` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py:151:42` | `.` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `tizen-ci-triage/scripts/ci_triage/runner.py:76:42` | `.` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:83:42` | `.` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `tizen-gbs-build/scripts/gbs_build_skill/runner.py:286:36` | `.` | `subprocess.Popen` | 0 | 非调用读取,正文②′无形态承接 |
| `tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/analyzer_runner.py:35:42` | `.` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:98:42` | `.` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:177:42` | `.` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py:36:42` | `.` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py:127:42` | `.` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |
| `tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:75:42` | `.` | `subprocess.run` | 0 | 非调用读取,正文②′无形态承接 |

汇总: `{"contexts": {".": 736, "release-v1.4.0": 110}, "excluded_compile": 1, "multiple_matches": 0, "parse_errors": 0, "participants": 2825, "python_contexts": {".": 177, "release-v1.4.0": 95}, "python_entries": 272, "tracked_entries": 846, "zero_matches": 27}`。

本预检不是完整消费者引擎/B-8/completion,不产生 OBS claim;后续块未执行。
