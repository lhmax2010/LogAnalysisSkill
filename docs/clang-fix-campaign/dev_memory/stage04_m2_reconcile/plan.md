# Stage 04 Plan: M2 Reconciliation

## Goal

Implement the frozen a0/a/b/b-prime/c/d reconciliation table as one atomic
operation over PASS records, links, invocations, and convergence outcomes.

## Key Constraints

- Re-read all sets inside one `BEGIN IMMEDIATE` transaction.
- Reuse link validation without starting a nested transaction.
- Apply A0 integrity validation before orphan backfill can mask corruption.
- Historical relinks are visible but do not grant current success.
- Exit priority is deterministic and fail-closed.
