# Hotfix Real Smoke 002 - Cross-error tier2/truncation/cascade fixes

## Trigger

2026-05-19 real buildlog coverage testing for A/B/C/D exposed four engineering bugs plus one design-level confidence issue.

- A: linker undefined reference
- B: depsolve failure
- C: patch failed
- D: `%install` spec script failure

B and D behaved correctly. A and C exposed production-blocking gaps in tier2 matching, BudgetPool/truncation state, and patch failure ranking.

## Four-case Result Summary

| Type | Top-1 root cause | Verdict | Tier | Tokens | Main issue |
|------|------------------|---------|------|--------|------------|
| A linker undef | correct | `needs_llm` | `null` | 1453 | tier2 did not trigger; degraded flag was unexpected |
| B depsolve | correct | `direct_answer` | `tier1` | 237 | passed |
| C patch failed | classified as `rpm_phase` | `direct_answer` | `tier2` | 2106 | patch root cause lost to rpm phase; truncation failed |
| D `%install` | correct | `direct_answer` | `tier2` | 795 | passed |

## Fix 1: Re-evaluate BudgetPool Partial State After Reclaim

### Bug

A reported:

- `level_achieved = 3`
- `downgrade_reason = budget_pool_partial`

Those two facts are contradictory. The collector ultimately achieved the preferred level, so the packet should not be degraded for partial budget.

### Likely Root Cause

`BudgetPool` marks a collector grant as partial when the first request has insufficient remaining balance. After reclaim, if the collector accumulates enough total budget for its preferred level, the partial marker is not cleared.

### Fix

- Track partial grants per collector, for example `partial_grants: dict[str, bool]`.
- Re-evaluate after each budget request.
- If cumulative granted budget for a collector reaches the preferred budget, clear the partial marker.
- Set `downgrade_reason` only when final `level_achieved < level_preferred`.

### Expected Impact

For A, `degraded` should become `false` once the linker collector achieves Level 3.

## Fix 2: H6 Truncation Must Use `limit_with_prompt`

### Bug

Observed from real smoke:

- A used 1453 tokens under the requested 1800-token limit but still recorded `packet_truncated_to_token_budget`.
- C used 2106 tokens over the requested 1800-token limit and still did not truncate below the limit.

### Likely Root Cause

The final guard appears to compare against `BudgetPool.total` or evidence-pool limit, around 1400, instead of wrapper `max_tokens` / `limit_with_prompt` 1800. The C result suggests truncation can also mutate the packet without re-estimating tokens to verify that the new packet is actually under budget.

### Fix

- Trigger final truncation only when `packet_tokens > max_tokens`.
- Use `limit_with_prompt`, not evidence pool size, as the final packet cap.
- After each truncation pass, re-run `TokenEstimator`.
- Repeat truncation until either `packet_tokens <= max_tokens` or all safe-to-drop fields are exhausted.
- If all safe fields are exhausted and the packet still exceeds the limit, keep the packet but append `packet_could_not_truncate_to_budget`.

### Truncation Order

1. `evidence.fallback_context.extra_log_window`: reduce 50 lines to 30 lines, then remove.
2. `evidence.fallback_context.primary_error_excerpt`: reduce 50 lines to 30 lines.
3. `cascade_summary` soft-reserve content.
4. `source_snippets` content while preserving metadata.

### Expected Impact

- A should no longer record truncation.
- C should end with `packet_tokens <= 1800`.

## Fix 3: `full_match` Must Record Matched Patterns Even Below Tier2 Threshold

### Bug

A had candidate confidence 0.84, just below tier2 threshold 0.85. `matched_patterns` was empty even though the linker undefined-reference pattern appears to be semantically applicable.

### Root Cause

`full_match.py` likely returns early when confidence is below the tier2 threshold and does not record a near-match.

### Fix

Record matched pattern metadata even when the final verdict remains `needs_llm`.

The packet should expose:

- pattern id
- captures
- actual confidence
- failed requirement, for example `confidence_below_tier2_threshold`

### Expected Impact

Downstream LLM consumers can see that the pattern nearly matched, instead of receiving an opaque `matched_patterns: []`.

## Fix 4: `patch_failed` Must Rank Ahead of Derived `rpm_phase`

### Bug

C buildlog contains a clear patch failure:

- `can't find file to patch`
- `Skipping patch`
- `1 out of 1 hunk ignored`

The analyzer ranked the terminal `%prep` `Bad exit status` as Top-1 `rpm_phase`, so quick_filter never saw the patch failure as the primary candidate.

### Root Cause

Scanner creates patch-failure evidence and terminal rpm-phase failure as independent events. Ranker gives terminal events enough priority that the derived `Bad exit status` hides the real patch failure.

### Fix

Scanner layer:

- Detect patch failure lines such as:
  - `can't find file to patch`
  - `Hunk #N FAILED`
  - malformed patch variants
  - `1 out of N hunk ignored`
- When a subsequent `Bad exit status from ... (%prep)` follows, mark it as a cascade child of the patch event.

Ranker layer:

- Give patch failure events in the failed phase a small priority boost, for example `+0.10`.
- Keep quick_filter unchanged; it should naturally see the correctly ranked patch candidate.

### Expected Impact

C should become:

- `primary_error.kind = patch`
- `via = fast_path`
- `matched_tier = tier1`
- `verdict = direct_answer`

## Fix 5: Linker Undefined Reference Confidence Needs a Link-specific Rule

### Problem

A candidate confidence was 0.84:

- undefined_reference base: 0.85
- cascade penalty: `0.20 * 0.3 = -0.06`
- command bonus: `+0.05`
- no location bonus, because real linker errors usually do not include source file/line

This lands just below the tier2 threshold 0.85.

### Design Options

Option A: do not apply cascade penalty to `linker_undef`.

```python
if event.kind == "linker_undef":
    pass
else:
    score -= semantic.cascade_probability * 0.3
```

Option B: give linker undefined-reference events a `has_symbol_context` bonus, similar to `has_location`.

Option C: lower the global tier2 threshold to 0.80.

### Recommendation

Use Option A. It is the narrowest change and reflects linker semantics: undefined reference events are already terminal linker failures, and the generic cascade penalty is not a good fit.

### Expected Impact

A should pass tier2 confidence:

- base 0.85
- command bonus 0.05
- no cascade penalty
- final score around 0.90

## Scope

Do not implement:

- `expand` subcommand
- v0.6 / M9 / full-stage collectors
- broad fixture rewrites
- broad `docs/DESIGN.md` restructuring

Fix 5 may require a narrow decision record, but not a full v0.5 design rewrite.

## PR Split

### PR1

Fix 1 + Fix 2 + Fix 3.

Boundaries:

- Touch only `gbs_analyzer/packet_assembler.py` and `gbs_analyzer/full_match.py`, plus focused tests and dev_memory.
- Do not touch scanner, ranker, or patterns.

Validation:

- 20 M8 E2E fixtures pass with zero regression.
- Add focused unit tests for Fix 1, Fix 2, and Fix 3.
- Re-run A real buildlog and confirm:
  - `degraded=false`
  - tier2 direct answer triggers after Fix 5 is implemented, or at minimum matched-pattern near-miss is visible before Fix 5
  - `packet_tokens <= 1800`

### PR2

Fix 4.

Boundaries:

- Touch scanner/ranker behavior for patch failures only.
- Do not change packet assembler.

Validation:

- Re-run C real buildlog and confirm patch fast-path tier1.
- Ensure B and D still pass.

### PR3

Fix 5.

Boundaries:

- Linker undefined-reference ranking semantics only.
- Do not lower global tier2 threshold unless explicitly approved.

Validation:

- Re-run A real buildlog and confirm tier2 direct answer.
- Ensure existing linker fixtures still pass.

## Final Acceptance

After all PRs, re-run A/B/C/D.

| Type | Expected verdict | Expected tier | Tokens | Degraded |
|------|------------------|---------------|--------|----------|
| A linker undef | `direct_answer` | `tier2` | `<= 1800` | `false` |
| B depsolve | `direct_answer` | `tier1` | `<= 1800` | `false` |
| C patch failed | `direct_answer` | `tier1` | `<= 1800` | `false` |
| D `%install` | `direct_answer` | `tier2` | `<= 1800` | `false` |

Regression gates:

- M8 E2E fixtures pass.
- Overall coverage remains at or above 96%.
- No unrelated v0.6 work starts.
