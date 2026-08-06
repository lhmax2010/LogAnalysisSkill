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
8. **Cover every declared cardinality dimension.** A matrix claim such as
   arch x round x concurrency is untested when fixtures exercise only one
   point. R14 found a unit-round identity BLOCKER after 820 green tests because
   every wrapper fixture and real smoke used one architecture. The FIX-1 gate
   therefore requires two architectures to share one unit-level round and both
   enter build.

## R14 deferred cleanup ledger

These findings are intentionally non-blocking for FIX-1 but retain names and
closure stages:

- C8, denied-short-circuit ordering under a rare race: revisit in P4.9
  orchestration refactor.
- C9, canonical edit-spec materialization timing: revisit in P4.9 after delta
  review confirms the unit-level identity contract.
- C15, source-substring assertions in tests: replace with structural assertions
  in P4.9 test cleanup.
- C18-C23, six review NITs: batch with the P4.9 refactor unless a production
  trial makes one behavioral.
- gate-view and lifecycle release APIs remain later milestones, not P4.5
  deliverables. Before P5 push gates, explicitly close the
  `ROUNDS_EXHAUSTED` release-whitelist acceptance test in that owner module.

## Earlier Prelude

`change_36.md` also records two earlier, separately numbered lessons: a human
handoff needs a real recovery edge, and fail-closed behavior should reject
uncertainty rather than merely rare but deterministic cases. They predate the
canonical seven-item ledger above and remain useful context.
