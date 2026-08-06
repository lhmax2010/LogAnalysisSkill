# P4.5 Close-out Report: campaign-repair-step

Date: 2026-08-06 (Asia/Shanghai)

Branch: `clang-fix-campaign`

Implementation baseline: `85310ef` (`P0 contract`)

Implementation/RC evidence head: `9bc5fd2`

Verdict: **READY FOR HUMAN REVIEW**

## 1. Executive conclusion

P0, M1, M2, M3, RA, RB, and RC are complete. The implementation exposes one
locked repair-step entrypoint, stores campaign state append-only, reconciles
interrupted PASS records and invocation outcomes in one immediate transaction,
and reaches real protected PASS records through GBS 2.0.6 and Clang/LLVM
22.1.8. RD reran the complete campaign set and repository suite:

```text
campaign state/reconcile/repair: 70 passed in 7.82s
full repository suite:            820 passed, 1 skipped in 18.03s
ruff:                             All checks passed!
mypy:                             Success: no issues found in 26 source files
P0 checker self-test:             33/33 passed
frozen design checker:            OK: 0 problem
```

No Gerrit push, QuickBuild request, production-source edit, or PR merge is part
of this close-out. Human PR review remains the final gate.

## 2. P2 contract checklist

The design column refers to `design.md`; code locations refer to the
implementation at `9bc5fd2`.

| P2 item | Status | Design | Code evidence |
|---|---|---|---|
| Nine-step order and authoritative round binding before success | [x] | §4.1, lines 1146-1413 | `campaign_repair_step.py:146-168` lock/metadata; `:209-228` materialize + create/revalidate round; `:232-277` reconcile exits; `:279-302` previous preflight + HELD; `:304-313` consume; `:315-369` build + 6a/6b dispatch |
| Per `(unit, arch_norm)` nonblocking process lock | [x] | §4.1 step 0 | `campaign_repair_step.py:1102-1115`: `<workspace_root>/.repair_step.lock`, `LOCK_EX|LOCK_NB`, finally unlock; busy is exit 5 at `:171-181` |
| Reconcile is the only read/classify/write boundary | [x] | §4.1 step 3; §4.2 | `campaign_state.py:841-1043`: one `_immediate_transaction`; wrapper calls only this API at `campaign_repair_step.py:232-240`; transaction-internal link primitive at `campaign_state.py:1046-1115` |
| a0 exact link-to-PASS binding is first | [x] | §4.1 a0 | `campaign_state.py:860-874` runs before round/attribution classification; exact cardinality and unit/round/arch/result/verdict/invocation checks at `:1118-1168`; HELD is inserted and returned, not raised |
| PASS attribution by failure key, arch, and edit-spec round | [x] | §4.1 attribution ①-④ | `campaign_state.py:896-913`, `:1187-1220`: zero match becomes `non_campaign`, one match is grouped, multiple matches return state-inconsistent HELD |
| a/b/b'/c/d branch table, deterministic reconstruction, exit priority | [x] | §4.1 a-d and exit priority | `campaign_state.py:925-1041`; reconstruction uses `git diff --name-only --no-renames -z` and POSIX normalization at `:1247-1363`; c records ORPHAN+HELD, d backfills only proven empty groups, current success never hides orphan state |
| Billing and invocation receipt semantics | [x] | §4.1 steps 4-6; §4.2 | `campaign_state.py:772-805` inserts before returning `InvocationReceipt`; no refund API exists; wrapper consumes only after recovery/preflight at `campaign_repair_step.py:304-345`; every substantive outcome receives `receipt.event_id` |
| Conditional result/verdict/invocation binding | [x] | §3.4 event contract; §4.2 | `campaign_state.py:1888-2138` validates payload shape, conditional enums, promoted columns, and referenced BUILD_INVOCATION identity in the same transaction; DDL uniqueness is at `:127-129` |
| Secondary primary-first boundary | [x] boundary verified | §3.3 lines 371-382; Phase 6 DoD lines 2815-2819 | P4.5 consumes already-written REPRODUCE events. Its adoption API accepts only `different_failure` and atomically compares bound evidence (`campaign_state.py:469-566`). The producer-side `REJECTED_PRIMARY_BASELINE_MISSING` CLI is explicitly allocated to Phase 6, not implemented or claimed by this P4.5 PR; see Known Risks |
| Rebaseline authorization is exact latest HELD + reason + arch | [x] | §4.2 `append_status`/rebaseline | `campaign_state.py:601-667`: arch-scoped HELD reasons require a whitelisted `arch_norm`; authorization requires the latest row to be HELD, `previous_evidence_missing`, and the requested arch |
| Terminal protected copies are retained | [x] | §4.1 terminal-state table | Repair-step contains no cleanup path. PASS links the record and leaves the build-verify protected marker; RC E2/E3/E6 verified retained clean protected copies. `verify/build_verify.py` stayed byte-unchanged |

### Phase-boundary note

The authoritative prompt repeats the producer-side secondary primary-first
error code in P1/P2, while the frozen design assigns its executable CLI and
DoD to Phase 6. P4.5 has no `baseline-reproduce` producer command and therefore
cannot expose a producer-side bypass. This report marks the boundary as
verified, not the future Phase 6 command as implemented. Phase 6 must wire
`REJECTED_PRIMARY_BASELINE_MISSING` and its no-event negative test before that
phase can close.

## 3. DoD-to-test mapping

| DoD family | Green-path tests | Counterfactual/reverse proof |
|---|---|---|
| Uniqueness: PASS/substantive outcomes and legal orphan retry | `test_convergence_index_rejects_second_outcome_for_same_invocation` (pass/substantive), `test_convergence_index_allows_orphan_then_new_invocation_outcome` | `test_convergence_index_reverse_validation_allows_duplicate_when_dropped` drops the index and proves duplicate outcomes become insertable |
| Invocation binding four negatives | `test_convergence_binding_accepts_receipt_and_rejects_four_mismatches` | Each nonexistent/non-BUILD/cross-unit/cross-round-arch case is rejected before insert; the reference receipt is accepted |
| Crash recovery and branch ordering | `test_reconcile_relinks_current_pass_in_one_transaction_and_rebuilds_paths`, `test_linked_current_branch_still_backfills_other_orphan_invocations`, `test_historical_relink_repairs_ledger_without_granting_current_success`, `test_linked_recovery_runs_before_missing_previous_precheck` | `test_reconcile_uses_transaction_internal_link_primitive` forbids nested public link; `test_a0_half_state_is_held_before_orphan_backfill_can_mask_it` demonstrates why a0 must precede d; RC E3 proves no rebuild/re-charge across a killed process |
| a0 exact binding | `test_a0_half_state_is_held_before_orphan_backfill_can_mask_it`, `test_a0_rejects_single_pass_bound_to_wrong_round_invocation` | `test_a0_rejects_duplicate_pass_binding_that_weak_exists_check_would_accept` constructs a shape a weak `EXISTS` query would accept and proves exact cardinality rejects it |
| Attribution zero/one/many | `test_non_campaign_pass_is_reported_without_events_or_held_status`, `test_reconcile_relinks_current_pass_in_one_transaction_and_rebuilds_paths`, `test_multiple_passes_are_all_recorded_and_freeze_the_round` | `test_multiple_round_attribution_is_state_inconsistent_when_guard_is_bypassed` bypasses the round UNIQUE constraint and proves fail-closed HELD |
| Round identity before success | `test_pass_runs_frozen_order_and_emits_fixed_schema` | `test_new_round_with_old_hash_dies_in_create_round_before_reconcile` proves reconcile is never called for the old-hash/N+1 request |
| Locking | `test_lock_busy_returns_exit_five_without_creating_round`, `test_reconcile_busy_lock_is_retryable_and_writes_nothing`, `test_consume_maps_immediate_lock_timeout_to_busy_without_writing` | RC E4 ran two real processes: loser exit 5, zero round/event/status writes and zero invocation charge |
| Fingerprint and changed-path parity | `test_reconcile_relinks_current_pass_in_one_transaction_and_rebuilds_paths` uses real Git paths containing spaces and quotes and compares exact sorted paths | RC E6 independently rebuilt/analyzed historical/fresh unknown-warning-option logs and two rich C++ candidate-list failures; each pair produced byte-identical fingerprints |
| Fixed stdout schema and deterministic arrays | `test_pass_runs_frozen_order_and_emits_fixed_schema`, `test_reconciliation_arrays_use_objects_and_deterministic_sorting`, `test_non_campaign_record_is_reported_as_sorted_structured_warning` | `test_python_m_campaign_repair_step_emits_one_json_document` parses process stdout as exactly one JSON document; tuple leakage would fail schema assertions |
| CHECK, HELD reachability, CLI | `test_campaign_unit_half_empty_evidence_tuple_is_blocked_by_check`, `test_previous_precheck_writes_arch_scoped_held_and_enables_rebaseline`, `test_campaign_repair_step_help_uses_dedicated_parser`, process CLI smoke | `test_campaign_unit_check_reverse_validation_fails_when_check_is_removed` removes CHECK; `test_removing_precheck_status_write_makes_rebaseline_unreachable` removes the status write and proves the recovery authorization becomes unreachable |

The three campaign files collect exactly 70 tests: state 29, reconciliation
20, repair-step 21.

## 4. Reverse validation: green and red states

The reverse tests intentionally weaken a guard in an isolated test database or
monkeypatched call path. A reverse test itself is green when it proves the
prohibited state becomes reachable after the guard is removed; that reachable
unsafe state is the requested red state.

Exact command:

```bash
PYTHONPATH=tizen-ci-triage/scripts:tizen-gbs-log-analysis/scripts:tizen-gbs-patch-suggest/scripts \
  .venv/bin/pytest -vv \
  tests/unit/test_campaign_state.py::test_campaign_unit_half_empty_evidence_tuple_is_blocked_by_check \
  tests/unit/test_campaign_state.py::test_campaign_unit_check_reverse_validation_fails_when_check_is_removed \
  tests/unit/test_campaign_state.py::test_convergence_index_rejects_second_outcome_for_same_invocation \
  tests/unit/test_campaign_state.py::test_convergence_index_allows_orphan_then_new_invocation_outcome \
  tests/unit/test_campaign_state.py::test_convergence_index_reverse_validation_allows_duplicate_when_dropped \
  tests/unit/test_campaign_repair_step.py::test_previous_precheck_writes_arch_scoped_held_and_enables_rebaseline \
  tests/unit/test_campaign_repair_step.py::test_removing_precheck_status_write_makes_rebaseline_unreachable \
  tests/unit/test_campaign_repair_step.py::test_new_round_with_old_hash_dies_in_create_round_before_reconcile \
  tests/unit/test_campaign_reconcile.py::test_a0_rejects_duplicate_pass_binding_that_weak_exists_check_would_accept \
  tests/unit/test_campaign_reconcile.py::test_multiple_round_attribution_is_state_inconsistent_when_guard_is_bypassed
```

Observed output:

```text
collected 11 items
11 passed in 0.40s
```

| Guard | Green state | Red state proven by reverse validation |
|---|---|---|
| CI evidence tuple CHECK | Half tuple rejected | Drop CHECK, same malformed row inserts |
| One convergence per invocation | Second PASS/substantive outcome rejected | Drop partial UNIQUE index, duplicate outcomes insert |
| HELD write before preflight exit | Rebaseline authorized only for exact reason/arch | Remove status write, rebaseline stays permanently false |
| Round-first wrapper order | N+1 with old hash rejected before reconcile | A reconcile-first order could return prior success; current spy proves reconcile was not reached |
| a0 exact cardinality | Duplicate/wrong binding produces HELD | Weak verification-id existence predicate would accept the constructed duplicate binding |
| Round attribution uniqueness | Constraint-preserving input has at most one round | Drop/bypass UNIQUE and a multi-round attribution is detected as state inconsistent |

## 5. Reproducible verification commands

### Campaign and repository tests

```bash
PYTHONPATH=tizen-ci-triage/scripts:tizen-gbs-log-analysis/scripts:tizen-gbs-patch-suggest/scripts \
  .venv/bin/pytest -q tests/unit/test_campaign_state.py \
  tests/unit/test_campaign_reconcile.py tests/unit/test_campaign_repair_step.py
# 70 passed in 7.82s

PYTHONPATH=tizen-ci-triage/scripts:tizen-gbs-log-analysis/scripts:tizen-gbs-patch-suggest/scripts \
  .venv/bin/pytest -q
# 820 passed, 1 skipped in 18.03s
```

An initial collection probe omitted `PYTHONPATH` and failed to import
`ci_triage`; it produced no accepted test result. The commands above are the
exact successful reruns and are the reproducible contract for this repository
layout.

### Static and contract gates

```bash
.venv/bin/ruff check tizen-ci-triage/scripts/ci_triage \
  tests/unit/test_campaign_state.py tests/unit/test_campaign_reconcile.py \
  tests/unit/test_campaign_repair_step.py
# All checks passed!

.venv/bin/mypy tizen-ci-triage/scripts/ci_triage
# Success: no issues found in 26 source files

python3 docs/clang-fix-campaign/tools/check_design_doc.py --self-test
# -- self-test: 33/33 passed --

python3 docs/clang-fix-campaign/tools/check_design_doc.py \
  docs/clang-fix-campaign/design.md
# -- OK: 0 problem --

PYTHONPATH=tizen-ci-triage/scripts:tizen-gbs-log-analysis/scripts:tizen-gbs-patch-suggest/scripts \
  .venv/bin/python -m ci_triage campaign-repair-step --help
# exit 0; dedicated required options displayed
```

P0 additionally archived SHA/cmp and independent signature evidence in
`p0-signature-audit-v1.5.16.md`: checker 33/33, historical 5+1+6 regression,
design 0 problem, and signature audit 4/4.

## 6. Zero-modification proof

The implementation evidence range is frozen at `85310ef..9bc5fd2`; the later
RD commit contains documentation only.

```bash
git diff 85310ef..9bc5fd2 --stat
```

Observed summary:

```text
44 files changed, 20277 insertions(+)
```

The range is additive: the only pre-existing runtime file touched is `cli.py`
to register the new command. The implementation adds
`campaign_state.py`, `previous_evidence.py`, and `campaign_repair_step.py`, plus
three new test files and audit documents.

Explicit zero-mod query:

```bash
git diff --name-status 85310ef..9bc5fd2 -- \
  tizen-ci-triage/scripts/ci_triage/state/db.py \
  tizen-ci-triage/scripts/ci_triage/state/keys.py \
  tizen-ci-triage/scripts/ci_triage/state/records.py \
  tizen-ci-triage/scripts/ci_triage/verify/build_verify.py \
  tizen-ci-triage/scripts/ci_triage/verify/edit_spec_guard.py \
  .clinerules/workflows/ci-triage-batch-full.md \
  .clinerules/workflows/explore-unavailable.md \
  .clinerules/workflows/repair-verify-submit.md
```

Observed output: **empty**. No existing workflow file or existing safety-core
file changed. No pre-existing test file was modified; all P4.5 tests are new
files.

## 7. RC evidence and adjudications

RC's full commands, hashes, process output, timing, and state-DB postmortem are
in `e2e-smoke-report-v1.md`. The completed matrix includes:

- zlib real synthetic arc: R1 `advance`, R2 PASS;
- SIGKILL after PASS record and before link: re-entry relinked with no rebuild
  and no second invocation charge;
- real concurrent process lock, budget terminal, and HELD reachability;
- historical multi-assistant: historical/fresh fingerprint parity and a
  dual-compiler-safe spec repair PASS;
- accepted cynara snapshot: two real rich C++ diagnostic runs with identical
  fingerprints and one-round repair PASS.

### Implementation discretion: orphan PASS error code

The frozen branch result distinguishes `orphan_pass_held` from
`state_inconsistent_held`, but §4.3 defines no separate orphan error code. The
wrapper therefore preserves the detailed branch in `convergence_reason` and
the reconciliation arrays while consolidating both exit-4 outcomes under the
registered `REJECTED_STATE_INCONSISTENT` code
(`campaign_repair_step.py:257-270`). This avoids inventing an unregistered
error code and keeps the stdout reason auditable.

### change_41

Closed with no design change. Raw GBS logs are immutable audit artifacts;
analyzer JSON is the only fingerprint/evidence input. The successful analyzer
rerun command is recorded verbatim in the RC report.

### change_42

Closed with no design change. Public CLI accepts raw QuickBuild architecture
`standard-armv7l`; internal DB/workspace/GBS uses normalized `armv7l`. The bad
runbook argument incidentally proved exit 4, identity rejection, zero DB
writes, and zero invocation charge in a real process.

### change_43

Closed with no design change. The supplied cynara HEAD had no clean baseline,
so fault injection stopped. One authorized retry used accepted snapshot
`9add176`, established a clean baseline, then completed the rich-diagnostic
case. No source or packaging was fabricated.

## 8. Known risks and non-blocking boundaries

1. Producer-side `baseline-reproduce`, including
   `REJECTED_PRIMARY_BASELINE_MISSING`, belongs to Phase 6 and is not delivered
   by this P4.5 PR. It must close before secondary reproduction is automated.
2. Patch-suggest can emit formatter-valid `insert_after`, while the frozen
   campaign edit-spec guard accepts exact `file/old/new` replacements. The
   mismatch fails closed; multi-assistant passed after representing the same
   semantic edit as an exact replacement. No guard was weakened.
3. Terminal protected copies are intentionally retained. Explicit cleanup is
   outside P4.5; disk growth is operationally visible rather than silently
   reclaimed.
4. `united-servvice.log` had no matching source/packaging and remains a paused
   input, not a fabricated validation case.

## 9. Handoff

The branch is ready for a draft PR titled
`[P4.5] clang-fix-campaign repair step`. Reviewers should focus on the
single-transaction reconciliation branch table, exact a0 binding, wrapper
order, append-only/physical guards, and the named Phase 6/integration
boundaries above. No merge is authorized by this report.
