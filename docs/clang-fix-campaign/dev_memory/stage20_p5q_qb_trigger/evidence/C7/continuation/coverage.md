# C7 Continuation Coverage

Authority: v1.8-FROZEN plus P5Q-C7-03. All browser traffic in this directory is
synthetic loopback HTTPS. No real QuickBuild session, Gerrit operation or live DB
write was performed. Old `C7/stop-report.md` and the 31-second probes are retained
as historical evidence, not used as the new acceptance criteria.

## Implementation

All paths below are relative to the repository. Python modules are under
`tizen-ci-triage/scripts/ci_triage/` unless specified otherwise.

| Authority | Implementation |
|---|---|
| 5.5 identity, direct-child heading, six columns, 50 rows | `qb_result_html.py:158` |
| 5.5 two modes, W, candidates, timing, fixed trace, private-page discard | `qb_discovery.py:83` |
| 5.2 shared parent checks and single binding transaction | `qb_binding.py:87`, `qb_binding.py:105`, `qb_result_fetch.py:229` |
| 4.3 baseline and two error templates | `qb_trigger.py:310`, `qb_discovery.py:25` |
| 4.3 unknown landing, driver failure, no automatic resubmission | `qb_trigger.py:502`, `qb_browser.py:170` |
| 4.2 already_requested; 4.3 unavailable mid-batch | `qb_trigger.py:596` |
| 5.1 unbound recovery, input order, continued result read | `qb_result_fetch.py:519` |
| 5.3 evidence numbering and private-page archive policy | `qb_evidence.py:8`, `qb_discovery.py:230` |
| 3.2 driver provenance, 60/150-second response caps | `qb_browser.py:170`, `qb_browser.py:346` |
| 3.1 termination records after close, non-overriding trace write | `qb_trigger.py:301`, `qb_browser.py:448` |
| C7-03 authorized agent edits | `qb_browser_agent.mjs:643`, `qb_browser_agent.mjs:716` |
| 5.3.4b snapshot stop guidance | `qb_result_fetch.py:63` |
| Appendix A v1.6 additions | `docs/clang-fix-campaign/design.md:5`, `:2757`, `:3483` |

## Tests

Names in this table are pytest node names in `tests/unit/test_qb_discovery.py`
unless another file is specified. Parameterized cases exercise the listed modes
independently. Final per-file totals and all individual node IDs are recorded in
`delivery-audit.json` and the JUnit files. Synthetic HTML parameter IDs are replaced
by their SHA256, consistently in JUnit and the current collection list.

| Requirement | Tests |
|---|---|
| First/second round match; direct build unchanged | `test_trigger_unknown_finds_and_binds_without_extra_parent_reads`, `test_appears_second_round`; existing `test_qb_trigger.py` |
| Ten zero-cost rounds and slower reads; strict deadline | `test_rounds_deadline_zero_cost_ten_and_slow_fewer` |
| 50 slow candidates, unfinished matching round, overview deadline | `test_deadline_includes_candidate_completeness_and_binding_read` |
| Missing/duplicate notes, HTTP, redirected or wrong-ID candidates; no diagnostic storage | `test_temporarily_unreadable_retried_without_diagnostic` |
| Empty/different marker cache; bound IDs excluded; W versus read mode | `test_different_marker_is_not_reread`, `test_bound_to_other_request_excluded`, `test_baseline_excludes_old_build_but_read_mode_finds` |
| Multiple matches and full manual binding checks | `test_multiple_matches_do_not_bind`, `test_matching_marker_still_requires_full_manual_checks` |
| Configuration identity/table errors in three modes | `test_bad_configuration_all_modes`, `test_51_rows_rejected`, `test_baseline_failure_cli_has_no_form_or_writes`, `test_configuration_read_failure_modes` |
| Real C6b title structure includes history/rss | `test_actual_configuration_heading_with_history_rss` |
| Agent exits/trusted failure on second candidate | `test_second_candidate_read_failure_archives_configuration` |
| Every driver-produced unknown, including missing process/broken pipe | `test_real_driver_synthesized_unknown_never_looks_up`, `test_real_driver_transport_failure_cli_never_looks_up`; `test_qb_driver_budget.py::test_driver_unknown_is_internal_and_not_serialized` |
| Unbound PASS/PENDING, continuation numbering, bound path no config | `test_unbound_fetch_continues_pass_or_pending_and_sequences` |
| Unbound inconsistent/superseded state refused before agent | `test_unbound_inconsistent_state_does_not_start_agent` |
| Three-request batch, input order and slow recovery window | `test_requests_file_mixed_input_order_and_slow_eviction` |
| Unknown Owner identity is not discovered; known identity count only; no candidate archive | `test_unregistered_owner_counter_limit_and_never_archived` |
| Registered Requested By/Triggered By corruption fails post-write, deletes file, no binding | `test_configuration_postwrite_identity_failure_deleted` |
| Concurrent binding/retrigger transaction recheck | `test_binding_transaction_rechecks_after_lookup` |
| Unavailable mid-batch: no restart, preserve original unit, idempotent entries unchanged | `test_batch_unavailable_no_restart_remaining_units_and_idempotent` |
| Closing trace write failure cannot override result | `test_close_termination_trace_write_failure_does_not_override` |
| Five CDP hangs, read/submit timeouts, CLI error mapping, no lookup after timed-out submit | `test_qb_driver_budget.py::test_cdp_hang_driver_deadline`, `::test_cdp_hangs_through_cli_mapping_and_termination_trace` |
| Real 60-second production read cap | `test_qb_driver_budget.py::test_read_default_60_seconds_real_clock`; measured output in `focused-01/output.log` |
| Virtual 149/150-second submit boundary and real 35-second close timeout | `test_qb_driver_budget.py::test_submit_default_budget_boundary_with_virtual_wait`, `::test_close_waits_35_seconds_then_records_one_termination`; `wait-boundaries-final/` |
| Explicit navigation budget and submit budgets, six RED mutations | `test_qb_driver_budget.py::test_budget_static_contract_and_mutations`; `focused-01/output.log` |
| Existing source assertions and individual RED mutations | `tests/node/test_qb_agent_source_guards.mjs`; `node-01/output.log` |
| Real CLI/browser local HTTPS, delayed appearance, unbound read recovery | `tests/unit/test_p5q_c5a_integration.py::test_real_cli_browser_submit_bind_pending_pass`; modes build/error-created/error-no-build/no-navigation/delayed-build/late-build |
| All four interception safety groups | `tests/node/p5q_c2b_safety.mjs`; `safety-01/output.log` |

## Evidence Notes

- `run_checks.py` records argv, UTC times, exit code, input hashes and the exact
  two-edit agent comparison before and after every gate.
- `full-01` was interrupted with SIGINT to finish the two missing local HTTPS
  cases before the final full run. Exit 2 is an incomplete run, not acceptance.
- `focused-01` has 164 passing cases, real read timeout timing and six RED budget
  mutations. The final full run additionally includes three process/pipe cases
  and two local HTTPS cases added afterwards.
- `full-final` passed 2878 cases with one existing platform-specific skip. Three
  extra boundary tests added after that collection passed in `wait-boundaries-final`.
  Their disjoint union covers all 2882 currently collected cases exactly:
  2881 passed, zero failed, one skipped. This is not a claim of 2881 in one invocation.
- `integration-added/cli-artifacts/` holds the delayed-build and read-recovery
  protocol transcripts separately from actual server requests. Final complete
  six-mode artifacts are in `full-final/cli-artifacts/`.
- Polling uses a test-only monotonic clock. The production entry has no timing
  flags and retains 60/150-second driver limits. The real 60-second case uses the
  ordinary wall clock and no browser or network.
- `ruff-delivery-final` checks the complete staged tree exported by `git checkout-index`.
  Unrelated pre-existing drafts and the user's unstaged deletions are excluded;
  they are not silently changed to make the gate pass.
- CDP and other local framework calls have no agent-side budgets, as explicitly
  accepted by C7-03. Driver deadlines are the hard response caps. Carry this
  residual into C8, together with the ten-build recovery window and the fact
  that identity counts cannot discover an unknown account-bearing column.
- Appendix A is copied literally: the old `(v1.5.23)` outside the quoted
  replacement remains before the inserted `(v1.5.24)` text in design 4.5.6.
  Neither frozen design was edited.
- Artifact checks initially rejected synthetic HTML in pytest parameter IDs and
  JSON-escaped HTML in the safety log. Parameter IDs now use stable hashes; safety
  JSON encodes angle brackets as Unicode escapes without changing decoded facts.
  `audit_delivery.py` checks bytes and decoded JSON strings with the unchanged
  production redactor and verifies the collected/JUnit case sets are identical.
- Raw synthetic HTML retains its whitespace. `git diff --cached --check` reports
  only these archived HTML lines; excluding just `**/qb_evidence/*.html` passes.
  The audit records and asserts that limited exception set.
