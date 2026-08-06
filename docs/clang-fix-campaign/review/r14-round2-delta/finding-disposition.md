# R14 finding disposition

> Round-2 correction (change_45): a `Closed` disposition is justified by the
> authoritative design body and executable tests, not by a change record alone.
> The exact body matches for the corrected findings are archived in
> `../r14-round2-delta/body-grep-proof.md`.

## Design change_44

| ID | Disposition | Evidence |
|---|---|---|
| D1 | Closed | §4.1 freezes unit-level canonical ref and per-arch build copies; X1 test enters both builds. |
| D2 | Closed by change_45 body diff | §4.1 now anchors `rebaselined` at the latest REPRODUCE at/before the event and explicitly falls back to the latest REPRODUCE when no substantive event exists; resolver tests cover PASS and rebaseline barriers. |
| D3 | Closed by change_45 body diff | §4.1 now says a0 and attribution multi-match commit only HELD and return immediately without b/b'/c/d; the priority formula is expressly limited to c and clean groups coexisting. |
| D4 | Closed for P4.5 by change_45 body diff | Wrapper writes `ROUNDS_EXHAUSTED` with exact `rounds`/`budget`; terminal cleanup is consistently named `release_terminal_worktrees`, while executable release APIs remain a later milestone. |
| D5 | Closed by change_45 body diff | §4.2 records WAL/FK/busy-timeout premise; DoD now includes the pragma-off reverse case proving the drift-link FK guard is physical rather than only procedural. |
| D6 | Closed by change_45 body diff | §4.1 comment prefixes are restored; the checker validates real-document Python fences and rejects an unclosed CommonMark fence. Self-test is 38/38. |
| D7 | Closed | Residual copy is marker-cleaned only when unprotected and not PASS-bound; protected/PASS-bound cases HELD. |
| D8 | Closed by change_45 body diff | Dedicated orphan code is mapped at both exits; no-slot b' names `no_free_invocation_slot`; append-event documents all five event types; §7.13 searches non-REJECTED error names too. |
| D9 | Closed by change_45 body diff | CONVERGENCE restores `at`, verdict/previous-basis enums, FAIL evidence requirements, invalid-combination `PayloadSchemaError`, and the rebaseline null-invocation rule. |
| D10 | Closed by change_45 body diff | Event-type SQL comments include CONVERGENCE/SECONDARY_TARGET_ADOPTED; adopted fingerprint is singular; terminal release naming and repair-step exit semantics are consistent. |
| D11 | Closed with explicit recovery boundary | Latest unit status must be `REPAIR_ROUND_RUNNING`; `previous_evidence_missing` HELD alone has an in-CLI rebaseline path. Orphan/state-inconsistent HELD is terminal until an out-of-band audited state transition. |

## FIX-1 implementation

| ID | Disposition | Code/test evidence |
|---|---|---|
| X1 | Closed | `campaign_repair_step.py:_run_locked`; dual-arch same-round test at `test_campaign_repair_step.py:1050`. |
| X2 | Closed, strengthened in FIX-1 round 2 | Top-level catch-all and JSON-only argparse remain; canonical materialization now writes and fsyncs a unique temporary file, atomically publishes with `os.link`, and accepts EEXIST only after hash comparison. Three race/failure tests cover the primitive. |
| X3 | Closed | a0 requires a non-bool integer invocation id; NULL corruption test at `test_campaign_reconcile.py:497`. |
| X4 | Closed | General `append_event` rejects PASS; tests create PASS only through atomic link API. |
| X5 | Closed | `_evidence_truncated` checks both packet and `error_clusters.truncated`; adoption fixture covers nested flag. |
| X6 | Closed, strengthened in FIX-1 round 2 | `previous_evidence.resolve`; the rebaseline test now places an older substantive FAIL before the anchor, so the pre-fix traversal would select the wrong evidence and the corrected resolver selects the anchored REPRODUCE. |
| X7 | Closed | Exact terminal status/reason tests at wrapper test lines 1101/1125. |
| X8 | Closed with lifecycle boundary recorded | Read-only identity gate checks executable latest status before create_round. Until a lifecycle command owns the transition, non-executable status recovery requires an audited out-of-band transition; the wrapper does not silently reset it. |
| X9 | Closed | Preoccupied convergence slot raises `StateInconsistent`; failed link leaves zero campaign link rows. |
| X10 | Closed, strengthened in FIX-1 round 2 | Order spy covers lock/identity/create/reconcile/resolve/prepare/consume/build/link; residual workspace checks run before invocation consumption, and rejection tests assert no new charge. |
| X11 | Closed, strengthened in FIX-1 round 2 | Target unit has a valid linked PASS while another unit contains malformed payload JSON; target reconciliation remains `linked_already`, proving the a0 query is unit-scoped. |
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
