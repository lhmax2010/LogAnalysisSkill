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

## P4.9 skill-2 addition

20. **Do not sacrifice independence in a bidirectional audit for convenience.**
    If the body-to-inventory bridge obtains `definition` from SPECS, both sides
    share one source and the check collapses into self-proof. The skill-2 v1.3
    ruling instead added explicit definition columns to all three frozen
    authorities and keyed both independently by `(definition, symbol)`.
    Missing columns fail closed with `PARSE_ERROR`; there is no name-only
    fallback that could silently reintroduce same-name collisions.
21. **Prove a rule change at the assertion layer instead of merely describing it.**
    Every tool or rule change needs an assertion that necessarily fails under
    the old implementation; otherwise the change has no existence proof.
    Skill-2 assertion d is the reference pattern: binary-key indexing is green
    for two same-named definitions, while the name-only implementation is
    reproduced as red.

## P4.9 skill-3 addition

22. **Synchronize all three explicit entry-point lists for every new top-level
    package.** Package installation/discovery in `pyproject.toml`, CI type-check
    coverage in `.github/workflows/ci.yml`, and source-tree `PYTHONPATH` guidance
    in `README.md` are independent, explicitly enumerated lists; none is derived
    from the others. Missing any one silently drops installation, verification,
    or documented source execution. Every later skill design and DoD must carry
    this three-entry checklist. Historical release snapshots remain read-only
    unless a release batch explicitly supersedes them.
23. **A degenerate production example cannot prove a generalized contract.**
    When the real case collapses two distinct roles into the same spelling, as
    in `_run_git as _run_git`, a defective implementation may still pass. The
    fixture must exercise the non-degenerate form, such as
    `from A import S as LocalS` with `LocalS != S`, and must be shown red under
    the old implementation before it can prove alias-aware attribution. Keep the
    degenerate real case as a regression test, not as the existence proof.
24. **Capture comparative evidence before the compared paths converge.** A
    migration parity check is meaningful only while the legacy and extracted
    implementations are still distinguishable. Once a re-export shim makes both
    imports resolve to the same object, output comparison becomes self-proof.
    Record source equality and independent-path behavior before the shim switch;
    after the switch, object identity proves wiring only. Skill-1 and skill-2
    used post-shim comparisons, so their behavior confidence rests primarily on
    source `cmp` evidence and full regression runs. The pre-shim parity pattern
    is mandatory from skill-3 onward.
25. **Self-test every mechanical DoD command against a known-green analogue.**
    Before admitting a command into a DoD, run it against the corresponding
    shape in a completed batch. Different delivery files may encode the same
    package with different spellings (for example, a hyphenated source path
    versus an underscored import package), so each probe must match the file's
    actual semantics instead of reusing one token everywhere. If the command is
    red on a known-green sample, treat the command as defective rather than the
    delivery. This rule applies to every mechanical DoD command from skill-3
    onward.
26. **Reconcile every summary and appendix against the current body before
    freezing.** An authoritative but stale summary is more dangerous than no
    summary: it can cause an implementer to omit a later decision while still
    believing the design was followed. After every multi-round revision,
    restate each appendix boundary from the current body instead of retaining
    an early-version slogan. The freeze checklist must compare the appendix,
    commit plan, DoD, and all accepted decisions item by item. This is the third
    recurrence of the same family after skill-1's stale §7 DoD and “only
    criterion change” appendix, so appendix/body decision-surface consistency
    is a mandatory pre-freeze check for skill-3 and every later skill design.
27. **Reconcile every quantitative statement across the full design before
    freezing.** Search every expression such as “N assertions,” “N symbols,”
    “N registrations,” “N contracts,” and “N items,” then verify it against the
    current rules and accepted decisions at every occurrence. The rule from
    revision-7a says counts are derived from rules and must never bend them;
    this complementary rule says every derived count must be refreshed when
    the rule changes. Skill-3's three intra-document drifts were all stale
    count expressions, so count reconciliation is a separate mandatory item in
    the freeze checklist from skill-3 onward.
28. **Give design counts a single textual source.** Repeated literals for
    assertion counts, negative-control counts, registration counts, contract
    counts, or symbol counts create independent stale copies. Starting with
    skill-4, state each count once in its definition section; commit plans,
    DoDs, summaries, and appendices must reference that section and say “all”
    rather than restating the number. This is the documentation analogue of
    deriving configuration instead of maintaining parallel explicit lists:
    removing duplicated counts removes the drift surface. Skill-3 retains its
    explicit cross-checks as the transition batch.
29. **Prove verification scaffolding and delivery discovery separately.** A
    temporary `PYTHONPATH` or `MYPYPATH` can prove that newly extracted code and
    tests work before packaging metadata lands, but it cannot prove that users
    or CI can discover the package through the supported installation path.
    Every new installable unit needs a second green run after refreshing the
    editable/install mapping and explicitly removing all temporary path
    scaffolding. Record the commands and results for both phases separately;
    neither is evidence for the other. This has the same evidence-timing shape
    as pre-shim parity versus post-shim identity.
30. **Move behavioral test ownership with an extracted skill.** Every extracted
    skill needs a dedicated behavior-test file that imports its public package
    directly and closes the contract-to-test map locally. Orchestration tests
    should retain only integration wiring, while legacy-path and shim-identity
    tests must be labeled separately because they prove compatibility wiring,
    not behavior. Mixing these categories obscures which tests may disappear
    with a shim and forces closeout evidence to span unrelated owners. Record a
    targeted skill-test run and the full regression run separately; neither
    substitutes for the other.
31. **A green tool run is evidence only when its output names the changed
    authority.** Re-running a checker after adding or renaming a document does
    not prove that the checker read that document. The acceptance evidence must
    contain entries attributable to the changed object, not merely an unchanged
    green summary. When planned inventory cannot yet exist, use a parser-only
    design-phase check and reserve full body-to-inventory agreement for the
    implementation phase; label the two results separately and never let one
    stand in for the other. Skill-3 established this rule when the existing
    bridge stayed green while having no path to the reviewed design.
32. **“Non-authoritative” lowers evidence weight, not the correctness bar.**
    Historical and raw evidence still has to describe the observed facts
    accurately; a false annotation is worse than no annotation because later
    readers will treat it as the fact recorded at that time. When a revision
    corrects a class of findings, check applicability symbol by symbol or item
    by item instead of pasting the same explanation across superficially
    similar entries. Skill-3 established this rule after an import-binding
    explanation for `_run_git` was incorrectly copied onto the independently
    defined `SubprocessRunner` twin.

33. **Define a regression baseline as set preservation, not a frozen total.**
    Adding required tests must increase the total. Acceptance means every
    pre-existing nodeid is still collected after explicitly mapped relocations,
    none fails or becomes a new skip, and every net-new nodeid passes. Skill-3
    preserved all 848 pre-B nodeids and added 36, legitimately moving the
    baseline from 847/1 to 883/1.
34. **State diff limits in terms of the protected surface.** “Only two files”
    was intended to prohibit production changes, not the evidence ledger that
    proves the prohibition. A scope rule must explicitly name the protected
    production namespaces, allowed test files, and allowed evidence documents;
    otherwise faithful recordkeeping appears to violate the safety rule.
35. **Make symbol-count commands syntactically exact and self-test them.** A
    probe for a function must terminate the name, for example
    `^def _run_git\(`, rather than matching longer prefixes accidentally. Run
    the final command against the current known state and record its output
    before treating it as a DoD gate.
36. **Preserve evidence at the phase where it is true.** Record the exact
    command, exit status, output, and topology of the measured phase. Do not
    rewrite a pre-shim behavior result as post-shim identity, or a temporary
    path run as installed-entry evidence. The evidence annotation is part of
    the claim and must remain factually exact.
37. **Apply parity masks only to explicitly named path-bearing fields.** Mask
    destination differences independently in argv elements, `src_root`, and
    symlink targets; never perform global payload substitution. Pair one
    destination-only positive sample with non-path error, order, and status
    negatives so the normalizer proves both usefulness and restraint.
38. **Require a bridge to identify the changed authority in its output.** A
    zero-difference summary can stay green while a new design path is omitted.
    Acceptance therefore requires the bridge output to contain the expected
    `(definition, symbol)` rows for the newly connected authority; skill-3
    pinned this condition with all 12 Gerrit rows.
39. **Review comment semantics after every byte-for-byte migration.** A source
    copy preserves comments as faithfully as code, but wording such as “shim,”
    “temporary,” or “will be deleted” can become false at the new authoritative
    location. Audit those comments separately before closeout, and distinguish
    stale wording from real imports or definitions that must remain. Skill-3's
    shared-type imports established this rule: they are signature dependencies
    in the extracted skill even though their inherited comments call them
    P4.9 shims.

## P4.9 skill-4 addition

40. **Require an admission falsification for every gate and every registered
    item (campaign method 18).** A green checker run is not proof that its
    predicates can reject drift. Before admission, the full gate must fail on a
    known-bad authority, and each retained pattern, binding, or mechanical
    ignored category must independently fail under a mutation constructed for
    that item. Skill-4 required the v1.9 design to reproduce its known drifts,
    all 22 bindings to reject their own mutations, and all 47 `OUT_OF_SCOPE`
    entries to reject an in-scope span.
41. **Place an integrity anchor outside the object being checked (campaign
    method 19).** A document, report, or ledger cannot stably contain its own
    hash or other write-sensitive identity. Pin the checked object's digest in
    a different artifact and anchor the complete artifact set with the
    containing Git commit. The skill-4 ledger follows this rule, and the sixth
    lifecycle closeout commit is likewise identified by Git rather than by a
    self-referential SHA inside `result.md`.
42. **Make the first post-freeze implementation action a satisfiability test on
    real input.** Review can miss constraints that are mutually impossible in
    the actual parser, import system, or repository topology. Skill-4 exposed
    two such cases immediately: the first ledger partition could not satisfy
    complete raw-diff coverage, and a package-root `build_verify` function made
    dotted-string patching of the same-named submodule impossible. Test the
    frozen mechanism against real inputs before broad implementation work; if
    it fails, stop and revise the authority rather than coding around it.

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
