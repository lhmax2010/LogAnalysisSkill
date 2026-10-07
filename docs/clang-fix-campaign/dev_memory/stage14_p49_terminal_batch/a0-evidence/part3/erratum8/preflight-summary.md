# 勘误 8 E8-6 全树预检

范围:固定 43a6aa6 的全部 PY_SOURCE;不是完整扫描闭合证明。

## 汇总

```json
{
  "tracked_entries": 846,
  "contexts": {
    ".": 736,
    "release-v1.4.0": 110
  },
  "python_entries": 272,
  "python_contexts": {
    ".": 177,
    "release-v1.4.0": 95
  },
  "participants": 2943,
  "zero_matches": 0,
  "multiple_matches": 0,
  "parse_errors": 0,
  "excluded_compile": 1,
  "excluded_annotations": 2,
  "alias_bindings": 67,
  "alias_calls": 25,
  "fixed_point_rounds": 6,
  "dynamic_unresolved": {
    "C8c_ESCAPE": 0,
    "ALIAS_PAYLOAD": 25,
    "C5f": 0
  }
}
```

## 别名不动点

| 绑定(路径:作用域行:名称) | 来源读取 | 经别名调用点 |
|---|---|---|
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/gerrit.py:61 query_change_for_commit.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/gerrit.py:64:42 subprocess.run; release-v1.4.0/tizen-ci-triage/scripts/ci_triage/gerrit.py:155:42 subprocess.run; release-v1.4.0/tizen-ci-triage/scripts/ci_triage/runner.py:74:42 subprocess.run | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/gerrit.py:80:20 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/gerrit.py:150 fetch_source_for_commit.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/gerrit.py:155:42 subprocess.run; release-v1.4.0/tizen-ci-triage/scripts/ci_triage/runner.py:74:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/gerrit.py:255 _run_git.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/gerrit.py:155:42 subprocess.run; release-v1.4.0/tizen-ci-triage/scripts/ci_triage/runner.py:74:42 subprocess.run | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/gerrit.py:261:4 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/runner.py:71 run_triage.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/runner.py:74:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/runner.py:319 _run_analyzer.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/runner.py:74:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/runner.py:345 _run_patch_suggest.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/runner.py:74:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/runner.py:368 _run_checked.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/runner.py:74:42 subprocess.run | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/runner.py:378:8 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:105 build_verify.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:515 _run_git_diff_check.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:467 _actual_changed_paths.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:549 _git.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:557 _git_stdout.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:349 _run_gbs_build.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:483 _tracked_worktree_mutated.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:317 _format_and_apply_patch.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:526 _canonical_diff_sha256.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:572 _run.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42 subprocess.run | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:580:11 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:72 gerrit_submit.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:75:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:247 _verification_mismatch.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:75:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:264 _dirty_reason.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:75:42 subprocess.run | 无 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:274 _target_warnings.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:75:42 subprocess.run | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:284:20 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:341 _run_git.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:75:42 subprocess.run | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:348:11 |
| release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:332 _git_stdout.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:75:42 subprocess.run | 无 |
| release-v1.4.0/tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:78 run_workflow.subprocess_runner | release-v1.4.0/tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:83:42 subprocess.run | release-v1.4.0/tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:147:8 |
| release-v1.4.0/tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:278 maybe_write_patch_context.subprocess_runner | release-v1.4.0/tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:83:42 subprocess.run | release-v1.4.0/tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:311:8 |
| release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/analyzer_runner.py:29 run_analyzer_for_buildlog.subprocess_runner | release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/analyzer_runner.py:35:42 subprocess.run | release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/analyzer_runner.py:67:8 |
| release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:95 format_patch.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42 subprocess.run; release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:98:42 subprocess.run | 无 |
| release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:171 build_patch_text.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42 subprocess.run; release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:98:42 subprocess.run; release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:177:42 subprocess.run | 无 |
| release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:544 _run_git_apply_check.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42 subprocess.run; release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:98:42 subprocess.run | release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:552:20 |
| release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:500 _run_git_diff_no_index.subprocess_runner | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:108:42 subprocess.run; release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:98:42 subprocess.run; release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:177:42 subprocess.run | release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:509:20 |
| tests/unit/test_tizen_build_verify.py:567 test_analyzer_nonzero_exit_returns_no_evidence_and_preserves_worktree.real_run | tests/unit/test_tizen_build_verify.py:573:15 subprocess.run | tests/unit/test_tizen_build_verify.py:578:15 |
| tests/unit/test_tizen_build_verify.py:593 test_analyzer_success_without_evidence_returns_none_and_preserves_worktree.real_run | tests/unit/test_tizen_build_verify.py:599:15 subprocess.run | tests/unit/test_tizen_build_verify.py:604:15 |
| tizen-build-verify/scripts/tizen_build_verify/build_verify.py:316 _format_and_apply_patch.subprocess_runner | tests/integration/test_build_verify_real_git.py:203:26 subprocess.run; tests/unit/test_tizen_build_verify.py:400:26 subprocess.run; tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42 subprocess.run | 无 |
| tizen-build-verify/scripts/tizen_build_verify/build_verify.py:104 build_verify.subprocess_runner | tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42 subprocess.run | 无 |
| tizen-build-verify/scripts/tizen_build_verify/build_verify.py:514 _run_git_diff_check.subprocess_runner | tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42 subprocess.run | 无 |
| tizen-build-verify/scripts/tizen_build_verify/build_verify.py:466 _actual_changed_paths.subprocess_runner | tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42 subprocess.run | 无 |
| tizen-build-verify/scripts/tizen_build_verify/build_verify.py:548 _git.subprocess_runner | tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42 subprocess.run | 无 |
| tizen-build-verify/scripts/tizen_build_verify/build_verify.py:556 _git_stdout.subprocess_runner | tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42 subprocess.run | 无 |
| tizen-build-verify/scripts/tizen_build_verify/build_verify.py:348 _run_gbs_build.subprocess_runner | tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42 subprocess.run | 无 |
| tizen-build-verify/scripts/tizen_build_verify/build_verify.py:482 _tracked_worktree_mutated.subprocess_runner | tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42 subprocess.run | 无 |
| tizen-build-verify/scripts/tizen_build_verify/build_verify.py:571 _run.subprocess_runner | tests/integration/test_build_verify_real_git.py:203:26 subprocess.run; tests/unit/test_tizen_build_verify.py:400:26 subprocess.run; tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42 subprocess.run | tizen-build-verify/scripts/tizen_build_verify/build_verify.py:579:11 |
| tizen-build-verify/scripts/tizen_build_verify/build_verify.py:525 _canonical_diff_sha256.subprocess_runner | tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42 subprocess.run | 无 |
| tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py:146 campaign_repair_step.subprocess_runner | tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py:151:42 subprocess.run | 无 |
| tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py:216 _run_locked.subprocess_runner | tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py:151:42 subprocess.run | 无 |
| tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py:722 _build_options.subprocess_runner | tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py:151:42 subprocess.run | 无 |
| tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py:782 _validate_source_identity.subprocess_runner | tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py:151:42 subprocess.run | 无 |
| tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py:1273 _git_stdout.subprocess_runner | tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py:151:42 subprocess.run | tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py:1278:16 |
| tizen-ci-triage/scripts/ci_triage/runner.py:73 run_triage.subprocess_runner | tizen-ci-triage/scripts/ci_triage/runner.py:76:42 subprocess.run | 无 |
| tizen-ci-triage/scripts/ci_triage/runner.py:307 _run_analyzer.subprocess_runner | tizen-ci-triage/scripts/ci_triage/runner.py:76:42 subprocess.run | 无 |
| tizen-ci-triage/scripts/ci_triage/runner.py:333 _run_patch_suggest.subprocess_runner | tizen-ci-triage/scripts/ci_triage/runner.py:76:42 subprocess.run | 无 |
| tizen-ci-triage/scripts/ci_triage/runner.py:356 _run_checked.subprocess_runner | tizen-ci-triage/scripts/ci_triage/runner.py:76:42 subprocess.run | tizen-ci-triage/scripts/ci_triage/runner.py:366:8 |
| tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:78 run_workflow.subprocess_runner | tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:83:42 subprocess.run | tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:147:8 |
| tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:278 maybe_write_patch_context.subprocess_runner | tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:83:42 subprocess.run | tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:311:8 |
| tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/analyzer_runner.py:29 run_analyzer_for_buildlog.subprocess_runner | tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/analyzer_runner.py:35:42 subprocess.run | tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/analyzer_runner.py:67:8 |
| tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:95 format_patch.subprocess_runner | tests/integration/test_build_verify_real_git.py:203:26 subprocess.run; tests/unit/test_tizen_build_verify.py:400:26 subprocess.run; tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42 subprocess.run; tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:98:42 subprocess.run | 无 |
| tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:171 build_patch_text.subprocess_runner | tests/integration/test_build_verify_real_git.py:203:26 subprocess.run; tests/unit/test_tizen_build_verify.py:400:26 subprocess.run; tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42 subprocess.run; tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:98:42 subprocess.run; tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:177:42 subprocess.run | 无 |
| tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:544 _run_git_apply_check.subprocess_runner | tests/integration/test_build_verify_real_git.py:203:26 subprocess.run; tests/unit/test_tizen_build_verify.py:400:26 subprocess.run; tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42 subprocess.run; tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:98:42 subprocess.run | tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:552:20 |
| tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:500 _run_git_diff_no_index.subprocess_runner | tests/integration/test_build_verify_real_git.py:203:26 subprocess.run; tests/unit/test_tizen_build_verify.py:400:26 subprocess.run; tizen-build-verify/scripts/tizen_build_verify/build_verify.py:107:42 subprocess.run; tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:98:42 subprocess.run; tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:177:42 subprocess.run | tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:509:20 |
| tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py:33 query_change_for_commit.subprocess_runner | tizen-ci-triage/scripts/ci_triage/runner.py:76:42 subprocess.run; tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py:36:42 subprocess.run; tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py:127:42 subprocess.run | tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py:52:20 |
| tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py:122 fetch_source_for_commit.subprocess_runner | tizen-ci-triage/scripts/ci_triage/runner.py:76:42 subprocess.run; tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py:127:42 subprocess.run | 无 |
| tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py:227 _run_git.subprocess_runner | tizen-ci-triage/scripts/ci_triage/runner.py:76:42 subprocess.run; tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py:127:42 subprocess.run | tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py:233:4 |
| tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:72 gerrit_submit.subprocess_runner | tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:75:42 subprocess.run | 无 |
| tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:247 _verification_mismatch.subprocess_runner | tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:75:42 subprocess.run | 无 |
| tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:264 _dirty_reason.subprocess_runner | tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:75:42 subprocess.run | 无 |
| tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:274 _target_warnings.subprocess_runner | tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:75:42 subprocess.run | tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:284:20 |
| tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:341 _run_git.subprocess_runner | tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:75:42 subprocess.run | tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:348:11 |
| tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:332 _git_stdout.subprocess_runner | tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:75:42 subprocess.run | 无 |

## 新增未决(未销账)

| 类别 | 位置 | 原因 |
|---|---|---|
| ALIAS_PAYLOAD | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/gerrit.py:80:20 | argv is not statically normalizable |
| ALIAS_PAYLOAD | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/gerrit.py:261:4 | argv is not statically normalizable |
| ALIAS_PAYLOAD | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/runner.py:378:8 | command binding contains unpacking |
| ALIAS_PAYLOAD | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/build_verify.py:580:11 | argv is not statically normalizable |
| ALIAS_PAYLOAD | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:284:20 | argv is not statically normalizable |
| ALIAS_PAYLOAD | release-v1.4.0/tizen-ci-triage/scripts/ci_triage/verify/gerrit_submit.py:348:11 | argv is not statically normalizable |
| ALIAS_PAYLOAD | release-v1.4.0/tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:147:8 | command binding contains unpacking |
| ALIAS_PAYLOAD | release-v1.4.0/tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:311:8 | command binding contains unpacking |
| ALIAS_PAYLOAD | release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/analyzer_runner.py:67:8 | command binding contains unpacking |
| ALIAS_PAYLOAD | release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:552:20 | argv is not statically normalizable |
| ALIAS_PAYLOAD | release-v1.4.0/tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:509:20 | argv is not statically normalizable |
| ALIAS_PAYLOAD | tests/unit/test_tizen_build_verify.py:578:15 | command binding contains unpacking |
| ALIAS_PAYLOAD | tests/unit/test_tizen_build_verify.py:604:15 | command binding contains unpacking |
| ALIAS_PAYLOAD | tizen-build-verify/scripts/tizen_build_verify/build_verify.py:579:11 | argv is not statically normalizable |
| ALIAS_PAYLOAD | tizen-ci-triage/scripts/ci_triage/campaign_repair_step.py:1278:16 | argv is not statically normalizable |
| ALIAS_PAYLOAD | tizen-ci-triage/scripts/ci_triage/runner.py:366:8 | command binding contains unpacking |
| ALIAS_PAYLOAD | tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:147:8 | command binding contains unpacking |
| ALIAS_PAYLOAD | tizen-gbs-build-workflow/scripts/gbs_workflow/workflow.py:311:8 | command binding contains unpacking |
| ALIAS_PAYLOAD | tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/analyzer_runner.py:67:8 | command binding contains unpacking |
| ALIAS_PAYLOAD | tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:552:20 | argv is not statically normalizable |
| ALIAS_PAYLOAD | tizen-gbs-patch-suggest/scripts/gbs_patch_suggest/formatter.py:509:20 | argv is not statically normalizable |
| ALIAS_PAYLOAD | tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py:52:20 | argv is not statically normalizable |
| ALIAS_PAYLOAD | tizen-gerrit-fetch/scripts/tizen_gerrit_fetch/gerrit.py:233:4 | argv is not statically normalizable |
| ALIAS_PAYLOAD | tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:284:20 | argv is not statically normalizable |
| ALIAS_PAYLOAD | tizen-gerrit-submit/scripts/tizen_gerrit_submit/gerrit_submit.py:348:11 | argv is not statically normalizable |

## 零/多命中

zero_matches=[]; multiple_matches=[]。

旧 SCAN-05 的 27 处:23 处 C8c、2 处 C5f、2 处标注位置排除;逐条见 scan05-closure.json。
第 1 块继续核对后新发现 SCAN-06,见 blockers.md;未宣告 full scan completion。
