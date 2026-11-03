# Batch 2 Coverage

Scope: skeleton v1.3 sections 5.1, 5.2, 5.4 and applicable section 6(1),
SKEL-B2-01/03/05 plus FatTank's bound-without-RESULT clarification.
All paths below are relative to `tests/unit/`. Parameterized cases count separately.
Exact collected nodeids: `nodeids-final.txt`; additions: `nodeids-added.txt`.
Results come from `focused/pytest.xml` and the final full-suite XML, not this table.

## Section 6(1) Mapping

| Requirement | Test file and function | Result |
|---|---| --- |
| Intake first clone, SSH origin, three-key marker, shared identity, idempotent DB | test_campaign_batch2_intake.py::test_intake_ssh_clone_marker_identity_and_idempotence | PASS (focused + full) |
| Absolute local remote rejected before source publication (SKEL-B2-03 supersedes original local-path positive) | test_campaign_batch2_intake.py::test_intake_absolute_remote_rejected_in_staging | PASS (focused + full) |
| Existing HEAD/origin/marker/extra marker key rejected, no repair/deletion | test_campaign_batch2_intake.py::test_existing_source_identity_never_repaired | PASS (focused + full) |
| Extra marker key rejected by repair-step and sandbox-submit | test_campaign_batch2_barriers_cli.py::test_extra_marker_key_rejected_by_existing_entries | PASS (focused + full) |
| Changed log preserves canonical bytes | test_campaign_batch2_intake.py::test_evidence_changed_log_preserves_old_bytes | PASS (focused + full) |
| Analyzer failure preserves canonical, does not create unit | test_campaign_batch2_intake.py::test_analyzer_failure_preserves_evidence_without_unit | PASS (focused + full) |
| Two intake processes, busy does not remove active staging | test_campaign_batch2_intake.py::test_intake_lock_preserves_other_staging | PASS (focused + full) |
| Crash after evidence/unit/clone/checkout/marker and staging recovery | test_campaign_batch2_intake.py::test_intake_crash_resume | PASS (focused + full) |
| Two publisher processes, equal/different bytes, no overwrite | test_campaign_batch2_intake.py::test_evidence_concurrent_hardlink_publication | PASS (focused + full) |
| Hard-link failure, no rename fallback | test_campaign_batch2_intake.py::test_hardlink_failure_is_not_rename_fallback | PASS (focused + full) |
| Unsupported arch, no analyzer/source | test_campaign_batch2_intake.py::test_rejected_arch_has_no_analyzer_or_source | PASS (focused + full) |
| Intake invalid args and clone tooling error | test_campaign_batch2_intake.py::test_intake_invalid_cli_json; test_clone_failure_cleans_staging | PASS (focused + full) |
| Fake SSH upload/receive and command/root/.. /symlink rejection | test_campaign_fake_ssh.py (7 existing cases, rerun) | PASS (focused + full) |
| Three architectures, real analyzer/fake gbs, synthetic file, uncharged builds | test_campaign_batch2_baseline.py::test_baseline_three_arches_real_analyzer_and_fake_gbs | PASS (focused + full) |
| Primary PASS/different failure terminates | test_campaign_batch2_baseline.py::test_primary_not_reproduced | PASS (focused + full) |
| Secondary requires primary before events; primary PASS gives no matching reference | test_campaign_batch2_baseline.py::test_secondary_requires_primary_before_any_event; test_secondary_different_failure_and_primary_pass | PASS (focused + full) |
| Identity/conf/CI-anchor validation | test_campaign_batch2_baseline.py::test_baseline_inputs_validated_before_build; test_baseline_anchor_tamper_refused | PASS (focused + full) |
| Baseline per-arch lock, zero-copy abandon barrier | test_campaign_batch2_baseline.py::test_baseline_abandoned_and_lock | PASS (focused + full) |
| Abandon injected after baseline check, before copying, is busy | test_campaign_batch2_baseline.py::test_abandon_cannot_interleave_after_baseline_check | PASS (focused + full) |
| Timeout, missing gbs, analyzer failure, cleanup | test_campaign_batch2_baseline.py::test_baseline_tooling_failures_cleanup | PASS (focused + full) |
| Keep-copy and stale baseline cleanup event | test_campaign_batch2_baseline.py::test_keep_copy_and_residual_cleanup_event | PASS (focused + full) |
| Reproduce phase/identity and count drift | test_campaign_batch2_baseline.py::test_reproduce_ignores_count_but_compares_phase_and_identity | PASS (focused + full) |
| Finish six release states and reconciliation | test_campaign_batch2_lifecycle.py::test_finish_terminal_releases_both_sources_idempotently; test_terminal_release_reconciles_reappeared_marker | PASS (focused + full) |
| Finish two empty states without release API | test_campaign_batch2_lifecycle.py::test_finish_empty_terminal_does_not_call_release | PASS (focused + full) |
| Finish three retained states and explicit held release | test_campaign_batch2_lifecycle.py::test_finish_retained_and_explicit_release | PASS (focused + full) |
| Nonterminal finish/manual release refusal, terminal abandon refusal | test_campaign_batch2_lifecycle.py::test_nonterminal_finish_and_manual_release_rejected; test_abandon_terminal_without_barrier_rejected | PASS (focused + full) |
| Link + ORPHAN enumeration, unrelated copy unchanged, later PASS report abandoned | test_campaign_batch2_lifecycle.py::test_abandon_enumerates_and_report_wins_over_later_pass | PASS (focused + full) |
| Barrier crash and last-marker crash, retry event reconciliation | test_campaign_batch2_lifecycle.py::test_abandon_crash_reconciliation | PASS (focused + full) |
| Exact abandoned reason, released event alone is not barrier | test_campaign_batch2_lifecycle.py::test_abandoned_release_is_not_barrier; test_campaign_batch2_barriers_cli.py::test_qb_abandoned_release_is_not_barrier | PASS (focused + full) |
| Abandon conflicts with sandbox and three repair locks, no barrier event | test_campaign_batch2_lifecycle.py::test_abandon_busy_has_no_barrier | PASS (focused + full) |
| Empty confirmation rejected | test_campaign_batch2_lifecycle.py::test_empty_confirmation_rejected | PASS (focused + full) |
| Terminal/held crash correction and release failure | test_campaign_batch2_lifecycle.py::test_release_crash_reconciliation_and_failed_correction | PASS (focused + full) |
| Missing registered copy counted; later orphan after PASS released on retry | test_campaign_batch2_lifecycle.py::test_abandon_accounts_missing_copy_and_new_copy_after_pass | PASS (focused + full) |
| Latest request/latest RESULT, bound without RESULT, Markdown/JSON, DB byte stability, no result-file read | test_campaign_batch2_lifecycle.py::test_report_latest_request_latest_result_pure_database | PASS (focused + full) |
| Abandoned sandbox unit: zero push/hook, fresh read after lock | test_campaign_batch2_barriers_cli.py::test_sandbox_abandoned_zero_push_and_hook; test_sandbox_barrier_reloaded_after_lock | PASS (focused + full) |
| Abandoned single QB unit: zero browser/request | test_campaign_batch2_barriers_cli.py::test_qb_abandoned_zero_start_and_request | PASS (focused + full) |
| Three-unit QB batch, abandoned middle unit zero commands | test_campaign_batch2_barriers_cli.py::test_qb_batch_abandoned_unit_zero_commands | PASS (focused + full) |
| Abandon cannot interleave with QB after barrier check | test_campaign_batch2_barriers_cli.py::test_qb_after_barrier_check_abandon_is_busy | PASS (focused + full) |
| Four old/new CLI handlers share parser, invalid args JSON/exit identical | test_campaign_batch2_barriers_cli.py::test_shared_cli_parser_identical_json_and_exit (4 x 3) | PASS (focused + full) |

## Explicitly Deferred

- All review-submit checks, review-submit concurrency and post-abandon push assertions: batch 3.
- Startup-check comparisons and preflight branches: batch 3. The original local-path
  intake success expectation is superseded by SKEL-B2-03; no shared identity rule was changed.
- Offline full end-to-end and orchestration script guards: batch 3.
- Real gbs and all live services: not run in this batch.

## Gate Evidence

- `focused/`: 106 passed, 0 failed, 0 skipped (99 new + 7 approved fake SSH).
- `safety/`: four loopback-only safety groups, all pass; pytest wrapper 1 passed.
- `full/`: full-suite raw output, XML and before/after load metadata.
- `mypy/`, `mypy-all/`, `imports/`, `design/`: type, dependency and design checks.
- `ruff/diagnostics-summary.json`: dirty workspace diagnostic locations/counts.
  Original stdout stays local to avoid committing unrelated draft source excerpts.
- `ruff-candidate-2/`: all existing tracked Python plus new Batch 2 Python,
  respecting repository excludes; unrelated untracked drafts are not part of delivery.
- `integrity.json`: protected files compared byte-for-byte to 8326fb4 and agent prefix hash.
