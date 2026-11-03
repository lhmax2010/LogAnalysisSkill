# Batch 3 Coverage

Authority: skeleton v1.3, SKEL-B3-01, SKEL-B3-03, SKEL-B3-05.
Baseline: 43c2c99. Tests below are new; existing assertions/nodeids are unchanged.
Every shortened test name is under `tests/unit/`. Results are in `full/pytest.xml`;
the first focused run (58 cases, before the two supersession cases) is retained
in `focused/`. The final collection contains 60 new cases.

| Contract | Test file / test name | Cases |
|---|---|---:|
| B3-05 complete baselines, first-round advancement | test_campaign_batch3_handoff.py / test_complete_baseline_enters_first_round | 1 |
| B3-05 missing arch, primary mismatch, round 2, existing round, HELD, terminal: no new round/budget, byte-identical DB | same / test_first_round_preconditions_leave_database_unchanged | 6 |
| B3-05 crash after advancement before create_round, replay | same / test_crash_after_transition_before_create_round_resumes | 1 |
| B3-05 two processes, one first-round transition | same / test_two_processes_first_round_lock_advances_once | 1 |
| B3-05 same suppress-policy parser and invalid JSON/exit contract | same / test_suppress_policy_shared_parser_invalid | 4 |
| 5.3 / 6.1 six revalidation gates, zero ref changes/REVIEW on rejection | test_campaign_batch3_review.py / test_six_revalidation_refusals[aggregate,qb_bytes,edit_bytes,policy,a2,toctou] | 6 |
| 5.3 hook-cached Change-Id, real local refs/for push, idempotent retry, null review_url with trace | same / test_success_cached_change_id_and_retry | 1 |
| 5.3 latest request / latest RESULT: superseded file | same / test_two_level_latest_result_supersedes_old_file | 2 |
| B3-03 exact request-specific pending message, no manual fallback | same / test_pending_exact_request_message_no_manual_fallback | 1 |
| 5.3 locks through push; abandon injected after barrier before TOCTOU, and during push | same / test_abandon_cannot_interleave_with_review | 2 |
| 5.3 abandon holds lock, review busy with zero push | same / test_abandon_lock_blocks_review | 1 |
| 5.3 missing file/schema keys/types/echo/marker/status/per-arch/acceptance/cache/branch | same / test_gate_and_identity_hard_failures | 11 |
| 5.3 failed push writes no REVIEW; no manual CLI option | same / test_push_failure_has_no_review; test_cli_invalid_arguments_no_manual_option | 2 |
| 5.5 five startup checks, full SSH project address | test_campaign_batch3_start.py / test_all_five_checks_full_ssh_project | 1 |
| 5.5 each check failure, config vs reachability | same / test_each_start_failure | 5 |
| 5.5 missing/invalid project rejected before subprocess | same / test_bad_project_precedes_subprocess | 5 |
| B3-01.4 local path: add-unit identity rejection with no artifact; startup PREFLIGHT_FAILED | same / test_local_path_both_commands_reject | 1 |
| 6.2 successful offline chain, release and report | test_campaign_batch3_e2e.py / test_success_full_offline_chain | 1 |
| 6.2 STALLED chain and terminal release | same / test_stalled_finish_offline_chain | 1 |
| 6.1/6.2 QB_TRIGGERED abandon, late PASS, review barrier, no WORKTREE_LOST, abandoned report | same / test_triggered_abandon_then_late_pass_offline_chain | 1 |
| 6.1 actual suppression edit accepted for sandbox but fails review A2 | same / test_suppress_edit_passes_sandbox_but_fails_review_a2 | 1 |
| 6.3 executable-block whitelist, shared state_root, 3 forbidden red examples | test_campaign_batch3_script.py / test_orchestration_commands_and_shared_state_root; test_script_forbidden_command_red_examples | 4 |
| B3-05 policy forbidden cannot fall through (remove && red example) | same / test_policy_forbidden_cannot_fall_through_to_repair | 1 |
| Total | | 60 |

All review rejection tests compare the local bare ref listing before/after and
assert no REVIEW event. The A2 suppression end-to-end test uses a real policy
evaluation; no verdict is stubbed to reach the refusal. New latest-request
fixtures use distinct build IDs and valid BUILD_BOUND events before RESULT.

## Offline Chains

Production command implementations are called with real SQLite, workspace copies,
the production analyzer and real local Git upload/receive-pack through the approved
fake SSH (`ssh://gerrit.invalid:29418`). gbs is the only compilation fake.
QuickBuild commands use the production Python driver with the existing fake JSON
agent and modified archived page fixtures; no QuickBuild network request is made.
Every repair invocation first calls the shared production suppress-policy function.

Actual sequences (`focused/stdout.log`, lines 1-3):

1. Success: DISCOVERED → CI_EVIDENCE_READY → BASELINE_RUNNING (three entries,
   one per architecture) → BASELINE_REPRODUCED → REPAIR_ROUND_RUNNING →
   LOCAL_3ARCH_PASS → SANDBOX_PUSHING → SANDBOX_PUSHED → QB_REQUESTED →
   QB_TRIGGERED → SANDBOX_QB_PASS → REVIEW_PUSHING → REVIEW_PUSHED.
2. STALLED: same prefix through REPAIR_ROUND_RUNNING → STALLED. finish-unit
   releases registered copies; report retains STALLED.
3. Abandon: same success prefix through QB_TRIGGERED; the abandonment barrier
   is a WORKSPACE_RELEASE event, not a status transition. A subsequent fetch
   writes SANDBOX_QB_PASS. Review refuses REJECTED_UNIT_ABANDONED, no REVIEW
   event, and the report's workspace column remains 已放弃.

The extra initial DISCOVERED and repeated BASELINE_RUNNING entries are existing
intake/baseline behavior; no production state writer was changed to align a list.

## P11 Carryover

`tizen-clang-campaign/SKILL.md` retains input fail-closed behavior, generated/suppress
source kinds, policy precheck, MAX_ROUNDS and invocation budgets, the repair-only
compile entry, no fabricated iter paths, FetchContent ambiguity handling, A2,
pending reporting and credential non-persistence. Its final section quotes the
applicable P11 clauses. Removed KB/D2E/T1/manual fallback are not reintroduced.
The startup template provides a single shared STATE_ROOT; no new config key or
review-submit parameter is introduced.

## Integrity

`audit.json` compares frozen/agent/core/P5Q bytes with 43c2c99 and records nodeids.
`nodeids-added.txt` lists exactly the 60 additions. Existing test changes: none.
Agent and qb-trigger unchanged: no separate four-safety-group rerun is required
by SKEL-B3-01. Any such tests included by the full suite remain unmodified.
