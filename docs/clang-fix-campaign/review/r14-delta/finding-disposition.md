# R14 finding disposition

## Design change_44

| ID | Disposition | Evidence |
|---|---|---|
| D1 | Closed | §4.1 freezes unit-level canonical ref and per-arch build copies; X1 test enters both builds. |
| D2 | Closed | PASS/rebaselined anchors are explicit; resolver scans backward without crossing either. |
| D3 | Closed | a0 and attribution ambiguity write HELD and return; clean writes retain existing priority. |
| D4 | Closed for P4.5 | Wrapper writes `ROUNDS_EXHAUSTED` with exact `rounds`/`budget`; P10 owns executable release APIs and its whitelist acceptance remains named in dev_memory. |
| D5 | Closed | §4.2 records WAL/FK/busy-timeout premise; raw-SQL reverse test proves invalid link succeeds only with FK disabled. |
| D6 | Closed | §4.1 outer fence is four backticks; checker uses one variable-length CommonMark scanner; self-test is 35/35. |
| D7 | Closed | Residual copy is marker-cleaned only when unprotected and not PASS-bound; protected/PASS-bound cases HELD. |
| D8 | Closed | Dedicated orphan code, ambiguity exception, registered errors and no-slot orphan reason are wired. |
| D9 | Closed | n_a field shapes and rebaseline null invocation rule are frozen and validated. |
| D10 | Closed | Event/derive/stdout/status text was reconciled, including repair-step nonzero exits 4/5 only. |
| D11 | Closed | Latest unit status must be `REPAIR_ROUND_RUNNING`; HELD and terminal states fail before round creation. |

## FIX-1 implementation

| ID | Disposition | Code/test evidence |
|---|---|---|
| X1 | Closed | `campaign_repair_step.py:_run_locked`; dual-arch same-round test at `test_campaign_repair_step.py:1050`. |
| X2 | Closed | Top-level catch-all, JSON-only argparse parser, O_EXCL materialization and residual recovery; direct exception plus subprocess exit 4/5 tests. |
| X3 | Closed | a0 requires a non-bool integer invocation id; NULL corruption test at `test_campaign_reconcile.py:497`. |
| X4 | Closed | General `append_event` rejects PASS; tests create PASS only through atomic link API. |
| X5 | Closed | `_evidence_truncated` checks both packet and `error_clusters.truncated`; adoption fixture covers nested flag. |
| X6 | Closed | `previous_evidence.resolve`; n_a-over-PASS and n_a-over-rebaseline tests at lines 893/956. |
| X7 | Closed | Exact terminal status/reason tests at wrapper test lines 1101/1125. |
| X8 | Closed | Read-only identity gate checks executable latest status before create_round. |
| X9 | Closed | Preoccupied convergence slot raises `StateInconsistent`; failed link leaves zero campaign link rows. |
| X10 | Closed | Order spy now covers lock/identity/create/reconcile/resolve/consume/build/link; precheck asserts zero invocation rows and count. |
| X11 | Closed | a0 query is unit-scoped; malformed state in another unit cannot freeze the target. |
| X12 | Closed | Rebaselined payload with non-null invocation is rejected. |
| X13 | Closed | HELD reason whitelist rejects an invented reason. |
| X14 | Closed | Blank/whitespace refs fail before `realpath`, with zero round rows. |
| X15 | Closed | `AmbiguousQbReference` is raised for one QB build bound to two units. |
| X16 | Closed | Adoption/general append map SQLite integrity failures to `StateInconsistent`; stale raw-exception assertion updated. |
| X17 | Closed | Raw SQL separately proves unique verification id and unique `(unit, arch, round)` guards. |
| X18 | Closed | Injected link collision records `ORPHAN_PASS(link_failed)` plus HELD and returns exit 4. |
| X19 | Closed | `orphan_pass_held` serializes as `REJECTED_ORPHAN_PASS_HELD`. |

## Nonblocking ledger

C8, C9, C15 and C18-C23 are recorded in
`../../dev_memory/methodology.md` with P4.9 closure targets. Gate-view and
campaign lifecycle release APIs remain later milestones; FIX-1 does not claim
or implement those modules.
