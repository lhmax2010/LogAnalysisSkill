# R14 round-2 body grep proof

Date: 2026-08-06 (Asia/Shanghai)

Authority: `../../design.md` at v1.5.18-FROZEN and the implementation/tests
in commits `a12d683` and `bb4af36`. A change record is not closure evidence on
its own. The rows below point to the authoritative body or executable proof.

The line numbers were captured with:

```bash
rg -n "<proof token>" docs/clang-fix-campaign/design.md
rg -n "<symbol or test name>" tizen-ci-triage/scripts/ci_triage \
  tests/unit/test_campaign_state.py tests/unit/test_campaign_reconcile.py \
  tests/unit/test_campaign_repair_step.py
```

## Design findings

| ID | Before / disputed text | v1.5.18 authoritative-body grep proof |
|---|---|---|
| D1 | Round identity and build-copy scope could be conflated. | `design.md:1162-1193` freezes one unit-level canonical edit spec and per-arch build copies; `test_campaign_repair_step.py:1147` proves two arches enter build for one round. |
| D2 | Rebaseline text said to search after the anchor and omitted the no-substantive fallback. | `design.md:1489-1502` now selects the latest REPRODUCE at/before `rebaselined` and falls back to the latest REPRODUCE when no substantive event exists. |
| D3 | The write-all/priority paragraph could be read as allowing b/b'/c/d after a0 or attribution ambiguity. | `design.md:1236`, `1268`, `1367-1377` now require HELD plus immediate return and limit the priority formula to c and clean groups coexisting. |
| D4 | Terminal release naming was split between a bare protection release and campaign lifecycle release. | `design.md:1031`, `1649`, `2240`, `2309` consistently name `release_terminal_worktrees`; `ROUNDS_EXHAUSTED` remains an explicit terminal state at `1019`. |
| D5 | FK behavior was described but the pragma-off reverse proof was absent. | `design.md:2054-2057` states the FK premise; DoD `design.md:2772-2773` requires the same raw SQL to succeed with `foreign_keys=OFF`. |
| D6 | Comment prefixes were lost and checker fixtures did not prove real-document/unclosed-fence behavior. | Prefixes are restored around `design.md:1394-1400`, `1431-1437`, `1576-1580`; gate 7g at `3024` names real-document Python and unclosed-fence checks. Checker self-test is 38/38. |
| D7 | Residual copy recovery risked deleting protected or PASS-bound evidence. | `design.md:1399-1403` keeps cleanup limited to unprotected, non-PASS-bound copies and puts it before charging; wrapper tests at `1268`, `1291`, `1325` cover all three cases. |
| D8 | Orphan error mapping/no-slot reason/non-REJECTED error grep were incomplete. | `design.md:1345` names `no_free_invocation_slot`; exits at `1578` and `2040` map `REJECTED_ORPHAN_PASS_HELD`; error registry at `2470`; gate search at `3022` includes non-REJECTED names. |
| D9 | The CONVERGENCE rewrite had dropped required fields/enums and the invalid-combination fallback. | The table row at `design.md:833` restores `at`, all enums, FAIL evidence, null rules, and `PayloadSchemaError`; DoD checks are at `2791-2800`. |
| D10 | Event comments omitted two event types, release names diverged, and adopted fingerprint was plural. | `design.md:533` lists CONVERGENCE/SECONDARY_TARGET_ADOPTED; `834` and `838` use singular `adopted_fingerprint`; terminal release references are the D4 locations above. |
| D11 | HELD was called recoverable without distinguishing terminal reasons. | `design.md:1034`, `1137-1139`, `1248`, `2806-2809` make only `previous_evidence_missing` recoverable through rebaseline; orphan/state-inconsistent HELD requires an audited out-of-band transition. |

## FIX-1 findings

| ID | Executable grep proof |
|---|---|
| X1 | `_run_locked` is at `campaign_repair_step.py:216`; the same-round dual-arch test is `test_campaign_repair_step.py:1147`. |
| X2 | Atomic materialization is `campaign_repair_step.py:1156-1188` (`mkstemp`, flush/fsync, `os.link`, EEXIST hash verification); race/failure tests are at `1049`, `1071`, `1094`. |
| X3 | a0 malformed/null invocation checks are exercised by `test_campaign_reconcile.py:463` and `497`. |
| X4 | PASS is atomic through `campaign_state.py:840`; event validation tests start at `test_campaign_state.py:544` and `584`. |
| X5 | Truncated-evidence adoption rejection is `test_campaign_state.py:718`. |
| X6 | Resolver tests are `test_campaign_repair_step.py:785`, `866`, `896`, `959`; the rebaseline case contains an older substantive FAIL so crossing the anchor is observable. |
| X7 | Exact round/invocation terminal statuses are tested at `test_campaign_repair_step.py:1198` and `1222`. |
| X8 | Non-executable status fails before round creation at `test_campaign_repair_step.py:1244`; recovery responsibility is explicitly out-of-band except for previous-evidence rebaseline. |
| X9 | Atomic adoption/link rollback tests are `test_campaign_state.py:768`, `861`, `891`. |
| X10 | Frozen-order spy is `test_campaign_repair_step.py:316`; workspace preparation now precedes invocation consumption at `campaign_repair_step.py:331-354`; residual rejection tests assert no new charge. |
| X11 | `test_campaign_reconcile.py:539` gives the target a valid linked PASS and corrupts payload JSON in a different unit; target reconciliation remains unit-scoped. |
| X12 | Rebaseline conditional-field rejection is in `test_campaign_state.py:584`. |
| X13 | HELD reason whitelist rejection is `test_campaign_state.py:630`. |
| X14 | Blank/whitespace refs fail before realpath in `test_campaign_state.py:386`. |
| X15 | Ambiguous QB-to-unit lookup is `test_campaign_state.py:1087`. |
| X16 | Transaction integrity failures are covered by rollback tests at `test_campaign_state.py:768`, `891` and reconcile savepoint test `test_campaign_reconcile.py:756`. |
| X17 | Raw-SQL unique and FK guards are `test_campaign_state.py:922` and `992`. |
| X18 | Link failure records orphan plus HELD at `test_campaign_repair_step.py:1399`. |
| X19 | Dedicated orphan rejection serialization is `test_campaign_repair_step.py:1419`. |

## Mechanical gates

```text
check_design_doc.py --self-test: 38/38 passed
check_design_doc.py design.md: OK, 0 problem
design.md vs v1.5.18-FROZEN snapshot: byte-equal
```
