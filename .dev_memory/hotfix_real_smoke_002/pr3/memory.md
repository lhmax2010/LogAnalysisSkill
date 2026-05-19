# Hotfix Real Smoke 002 - PR3

Status: completed

## Scope

PR3 implements the linker undefined-reference completion path:

- Fix 5: `linker_undef` ranking should not receive the generic cascade penalty.
- Fix 6: tier2 verdicts should not be blocked by method-level degraded evidence when required
  evidence is complete.
- Fix 7: `undefined_reference` patterns should treat `tool_in` as advisory in make-driven builds.

## PR2 Review Follow-Up

PR3 also carries two small review follow-ups before Fix 5:

- Guard hunk-ignored canonicalization so already-canonical `Hunk ... FAILED` text is not wrapped again.
- Record that `matched_patterns` near-match entries currently duplicate `id` and `pattern_id`; v0.6 should decide long-term schema shape.

## Explicit Non-Scope

- Do not change tier2 threshold.
- Do not change `patterns/error_semantics.yaml` confidence values.
- Do not change pattern library, scanner behavior beyond the review follow-up, or packet assembler.
- Do not start v0.6/M9 work.

## PR3 Validation Targets

A real buildlog after PR3:

- `verdict=direct_answer`
- `via=full_path`
- `matched_tier=tier2`
- `primary_error.kind=linker_undef`
- `degraded=false`
- `packet_tokens <= 1800`
- Top-1 confidence rises from about `0.84` to about `0.90`

B/C/D must remain non-regressed.

## Completion Notes

The initial Fix 5 implementation raised A's confidence to `0.90`, but real validation found two
additional implementation blockers:

- `evidence.degraded=true` from ctags fallback still blocked tier2 even though
  `contains_all(required)` was satisfied.
- `tool_in` remained a hard gate while the real linker event was attached to `make -j40`.

Fix 6 and Fix 7 address those blockers narrowly in `full_match.py` without changing patterns or
scanner tool extraction.

Final validation:

- A: `direct_answer`, `full_path`, `tier2`, `linker_undef`, confidence `0.90`, `degraded=false`,
  `1594/1800` tokens.
- B: `direct_answer`, `fast_path`, `tier1`, `depsolve`, `degraded=false`.
- C: `direct_answer`, `fast_path`, `tier1`, `patch`, `degraded=false`.
- D: `direct_answer`, `full_path`, `tier2`, `rpm_phase`, `degraded=false`.
