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
   A claim that a rule needs "no change" also requires a dry-run against the
   planned target topology; inspection alone did not expose the stale
   multi-consumer premise before the convergence skill's v1.3 layering ruling.
7. **Make the rule reproduce the incident it claims to prevent.** Every guard
   change needs a fixture proving that the original incident fails under the
   new rule. A guard that cannot catch its founding incident does not exist.
8. **Cover every declared cardinality dimension.** A matrix claim such as
   arch x round x concurrency is untested when fixtures exercise only one
   point. R14 found a unit-round identity BLOCKER after 820 green tests because
   every wrapper fixture and real smoke used one architecture. The FIX-1 gate
   therefore requires two architectures to share one unit-level round and both
   enter build.
9. **Prove disposition claims against authoritative text.** A change record
   states intent; the current design body states the contract. Every `Closed`
   finding must include the body line, before/after excerpt, and a reproducible
   grep. If the ledger and body disagree, the body wins and the finding stays
   open. R14 round two established this after two independent reviewers found
   D3/D10 marked closed while their required body edits were absent.

## P4.9 step-0 additions

10. **Mechanically audit ownership cuts.** Attribution tables are proposals
    until source/AST measurement proves definitions, consumers, internal
    access, and public-surface completeness; `symbol_audit.py` was introduced
    after repeated hand-drawn consumer-map drift. The public-surface guard must
    follow a module across the boundary in the same change; revision-6 exposed
    the false completeness of guarding quickbuild/types but not workspace,
    classify, and state.
11. **Give a shared layer its own dependency direction.** Shared code is not a
    flat dumping ground: types < HTTP/env < state/workspace/classify is enforced
    by layers, independence, and no-uplink contracts in `.importlinter`.
12. **Make the contract body explicitly enumerable.** Every inventory symbol
    must appear in the authoritative tables and vice versa; revisions 4/5
    replaced “etc./x2” shorthand before `table_audit_bridge.py` could close the
    body-to-inventory gap. A closed module-scope row is also enumerable because
    its physical top-level surface is measured; counts are derived from the
    rule and must never be used to bend the rule, as revision-7a demonstrated.
    The filename is part of that authority: after an in-place revision, its
    version must match the document title so path-based discovery cannot select
    the wrong generation. Path constants in audit tools count as document
    references and may be updated non-semantically in the same commit, but the
    tool must rerun green against the renamed authority.
13. **Never make an artifact record its own mutable fingerprint.** The failed
    design/report self-SHA attempts established that integrity belongs in an
    external immutable anchor, here the containing Git commit.
14. **A guard exists only after its own tool proves green and red.** Four
    import-linter contracts were each run positively and deliberately broken;
    configuration prose alone was not accepted as evidence.
15. **Match audit rules to symbol structure without creating exemptions.**
    Data types, capability functions, and temporary composition shells need
    different checks, and every new category requires a structural anti-abuse
    assertion. Module-scope therefore requires a physical shared module, a
    deleted or pure-shim legacy location, and zero per-symbol overlap; the
    abandoned GBS shell design and revision-7a exposed this distinction.
16. **Treat transition states as debts with promotion gates.** `to-be-created`
    and `to-be-refactored` are deferrals, not passes; each needs a visible count,
    a conversion commit, and full checks after conversion.
17. **Close all three migration closures before crossing a boundary.** Type,
    input-data, and called/output closures must move or be explicitly retained;
    the SourceFetchResult type chain and two successive marker-signature fixes
    exposed missing type, data, and returned-path dependencies.
18. **Write the inherited constraint list before deferring work.** Moving GBS
    report extraction out of step-0 preserved seven concrete constraints in
    the frozen design, so the later triage-report batch starts from named risks
    rather than repeating the same discovery cycle.

## P4.9 skill-1 addition

19. **Derive evolving path and membership sets instead of maintaining them.**
    A hard-coded list plus repository evolution is a silent mismatch: C21's
    five script roots omitted the newly extracted convergence skill and passed
    only because the target environment masked it. Repository `*/scripts`
    roots are now discovered mechanically. The deferred `runner.py` sibling
    list is the same failure class and must be removed by its owning batch.

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
