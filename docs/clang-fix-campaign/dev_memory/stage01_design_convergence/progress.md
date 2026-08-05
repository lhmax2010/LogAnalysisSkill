# Stage 01 Progress: Design Convergence

1. `change_32` tightened convergence uniqueness and evidence tuple integrity.
2. `change_33` found the crash-recovery ordering dead end and moved orphan
   backfill behind PASS relinking.
3. `change_34` froze one `BEGIN IMMEDIATE` reconciliation API and recovery
   priority.
4. `change_35` added per-round pairing and deterministic PASS payload rebuild.
5. `change_36` supplied PASS-to-round attribution through edit-spec identity.
6. `change_37` separated historical ledger repair from current success exits
   and rejected impossible multi-round attribution as corruption.
7. `change_38` restored identity binding before reconciliation and added the
   all-round link-to-CONVERGENCE integrity precheck.
8. `change_39` made API/index checker rules executable and consolidated prompt
   authority.
9. `change_40` corrected the API checker from `ast.parse` to `compile`, because
   only the latter catches duplicate function arguments.

The process deliberately stopped when checker reality contradicted the text;
the intermediate worktree was preserved until each numbered change supplied a
new ruling.
