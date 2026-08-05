# Stage 02 Plan: P0 Contract Gates

## Goal

Turn the frozen document into an executable implementation input before code
consumes it.

## Inputs

- v1.5.16 frozen design and snapshot
- Authoritative P4.5 implementation prompt
- `change_31`, `change_39`, and `change_40`
- Four-signature independent audit

## Exit Criteria

- Every Python fence compiles.
- Bare pseudo-signatures are absent.
- Prompt index tokens are a non-empty subset of design indexes.
- Cross-reference and Mermaid declaration-order checks pass.
- Frozen snapshot is byte-identical and prompt SHA is exact.
