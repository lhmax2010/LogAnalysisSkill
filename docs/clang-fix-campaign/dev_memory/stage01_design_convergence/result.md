# Stage 01 Result: Design Convergence

## Conclusion

- Final contract: `design.md` v1.5.16-FROZEN.
- Frozen snapshot SHA-256:
  `ff73f5e3c6d54a75ae60771b98eadcfc1a4d1422ca8faf337a3de09eee4346ff`.
- Snapshot and working design were byte-identical at RA audit time.
- Authoritative P4.5 prompt SHA-256:
  `e214d1fb8b806e1ebc12e6e8cfafc57d71cbffcf0340d94c26396ef87816a3fb`.
- Design/checker landing commit: `85310ef`.

## Decisions That Matter to Implementers

- Success exits occur only after DB-authoritative round identity binding.
- Reconciliation owns one immediate transaction and uses transaction-internal
  write primitives; it must not nest a second transaction.
- Historical relinking repairs the ledger without granting current success.
- A0 integrity failure and attribution ambiguity are HELD, never guessed.
- The wrapper order is lock, identity, create round, reconcile, precheck,
  consume, build, outcome, unlock.

## Record Differences

- The original standalone Claude review ledger referenced by remediation was
  absent. Review history is reconstructed in
  `../../review/claude-review-ledger.md` from machine-resident change files.
- `change_36` contains two pre-ledger methodology lessons while `change_37`
  restarts numbering at 1. The requested canonical 1-7 ledger follows
  changes 37-40; the earlier two are retained as a prelude.

## Remaining TODO

- Complete three-way final review (RB).
- Validate the frozen semantics against real GBS/filesystem behavior (RC).
