# Stage 01 Plan: Design Convergence

## Goal

Converge the P4.5 campaign repair contract before implementation: append-only
state, invocation uniqueness, crash recovery, deterministic PASS attribution,
frozen wrapper ordering, and executable API/checker gates.

## Inputs

- `../../design.md`
- `../../design_changes/change_32.md` through `change_40.md`
- External and Claude findings recorded in those change documents
- Seven SQLite probe transcripts embedded in changes 32-38

## Exit Criteria

- One frozen design is the only runtime contract authority.
- DDL, branch table, nine-step wrapper order, and API signatures agree.
- Guard rules are executable and reproduce their founding failures.
- Any contradiction is handled by stop-and-report, not silent correction.
