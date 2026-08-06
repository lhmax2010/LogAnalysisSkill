# Stage 03 Plan: M1 State Layer

## Goal

Implement the frozen seven-table campaign schema and append-only APIs that all
later reconciliation and wrapper behavior depends on.

## Safety Inputs

- `ux_convergence_per_invocation` must physically prohibit a second outcome.
- The CI evidence triple must be all-null or all-non-null.
- Status writes carry `arch_norm` where the frozen reason requires it.
- Budget consumption and PASS linking are transactionally guarded.

## Exit Criteria

Positive behavior and reverse tests must both prove that the physical guards,
not only Python conditionals, enforce the contract.
