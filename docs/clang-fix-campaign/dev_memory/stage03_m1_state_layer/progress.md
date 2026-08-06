# Stage 03 Progress: M1 State Layer

- Added `campaign_state.py` with schema creation and public append-only APIs.
- Implemented unit/round identity, invocation receipts, event payload binding,
  verification links, adoption, status, and QuickBuild request/result state.
- Used `BEGIN IMMEDIATE` for mutation races and mapped lock contention to the
  frozen busy failure.
- Split transaction-internal validation/write primitives from public
  transaction-opening wrappers so later reconciliation can reuse logic without
  nesting transactions.
- Added reverse validation that drops the unique index or CHECK and proves the
  prohibited rows then become insertable.
