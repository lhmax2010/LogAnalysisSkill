# P4.5 Methodology Ledger

These seven rules are transcribed from the numbered ledger in
`change_37.md` through `change_40.md`. They are process safeguards learned
during design convergence.

1. **Isolate incidental judgment.** A side correction or "small optimization"
   must have its own change section and rationale so review attention is not
   hidden behind the primary change.
2. **Validate probe preconditions.** Before constructing a counterexample,
   prove that the frozen DDL permits it. A state reachable only by bypassing
   constraints is corruption evidence, not a valid workflow path.
3. **Separate ledger repair from exit semantics.** Repairing historical state
   does not grant success to the current invocation unless the contract says
   so explicitly.
4. **Re-review a judgment when its premise disappears.** A later change that
   removes the reason for an earlier ordering or policy decision must trigger
   a fresh review of that decision.
5. **Bind scope inputs before they drive a success exit.** Caller-provided
   round/hash values cannot define the "current group" until DB authority has
   validated them.
6. **Run every checker rule against real input before freezing it.** A checker
   is code; a rule change without a real-document trial output is incomplete.
7. **Make the rule reproduce the incident it claims to prevent.** Every guard
   change needs a fixture proving that the original incident fails under the
   new rule. A guard that cannot catch its founding incident does not exist.

## Earlier Prelude

`change_36.md` also records two earlier, separately numbered lessons: a human
handoff needs a real recovery edge, and fail-closed behavior should reject
uncertainty rather than merely rare but deterministic cases. They predate the
canonical seven-item ledger above and remain useful context.
