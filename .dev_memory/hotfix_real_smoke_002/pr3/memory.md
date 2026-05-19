# Hotfix Real Smoke 002 - PR3

Status: in_progress

## Scope

PR3 implements Fix 5 only: `linker_undef` ranking should not receive the generic cascade penalty.

## PR2 Review Follow-Up

PR3 also carries two small review follow-ups before Fix 5:

- Guard hunk-ignored canonicalization so already-canonical `Hunk ... FAILED` text is not wrapped again.
- Record that `matched_patterns` near-match entries currently duplicate `id` and `pattern_id`; v0.6 should decide long-term schema shape.

## Explicit Non-Scope

- Do not change tier2 threshold.
- Do not change `patterns/error_semantics.yaml` confidence values.
- Do not change pattern library, scanner behavior beyond the review follow-up, packet assembler, or full_match.
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
