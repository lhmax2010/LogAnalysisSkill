# Stage 04 Progress: M2 Reconciliation

- Added `reconcile_pass_and_invocations` to `campaign_state.py`.
- Rebuilt PASS payload fields deterministically from verification records and
  Git state.
- Implemented current relink, historical relink, linked-already, orphan PASS,
  non-campaign PASS warning, residual invocation backfill, and A0 integrity
  branches.
- Used savepoints/transaction-local helpers so a failed event insert cannot
  leave a half-link.
- Sorted result arrays deterministically for the wrapper JSON contract.
