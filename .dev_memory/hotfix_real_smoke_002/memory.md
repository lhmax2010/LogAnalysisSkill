# Hotfix Real Smoke 002 - PR1

Status: pr2_completed

## Scope

Real A/B/C/D smoke testing exposed cross-error issues after MVP and hotfix 001. The full
hotfix_002 scope is documented in `docs/real_smoke/hotfix_002_design.md`.

PR1 implements only:

- Fix 1: BudgetPool partial state must be re-evaluated after reclaim.
- Fix 2: final truncation must use the wrapper `max_tokens` / `limit_with_prompt`.
- Fix 3: `full_match` must record near-match patterns even when confidence is below tier2.

## Explicit Non-Scope

PR1 must not implement:

- Fix 4 patch cascade/ranking changes.
- Fix 5 linker undefined-reference confidence changes.
- scanner, ranker, pattern library, or design baseline changes.

## Starting State

- Branch: `hotfix/real-smoke-002-pr1`
- Base: `main` at latest remote state before PR1 implementation.
- Required files to inspect:
  - `gbs_analyzer/packet_assembler.py`
  - `gbs_analyzer/full_match.py`
  - existing unit/e2e tests for packet assembler and full match
  - `docs/real_smoke/reports/A_report.md`
  - `docs/real_smoke/reports/B_report.md`
  - `docs/real_smoke/reports/D_report.md`

## PR1 Validation Targets

A real buildlog after PR1:

- `degraded=false`
- `packet_tokens <= 1800`
- `matched_patterns` includes `linker_undefined_reference_tier2`
- near-match has confidence around 0.84 and failure reason
- `verdict=needs_llm`
- `matched_tier=null`

B/D must remain non-regressed after every PR.

## PR1 Completion Summary

Implemented Fix 1/Fix 2/Fix 3 only.

- Fix 1: `BudgetPool` now tracks preferred/cumulative grants and clears partial state when the final achieved level reaches the preferred level. Packet-level degradation is now driven by explicit `degraded_reasons`, avoiding reasonless `degraded=true`.
- Fix 2: final token guard uses `max_tokens`/`limit_with_prompt`, re-estimates after shrink passes, can compact prompt content, and has a final prompt-only truncation fallback before declaring an unshrinkable packet.
- Fix 3: `full_match` records structured near-match pattern metadata for `needs_llm` packets, including pattern id, captures, candidate confidence, and failure reason.

Real-smoke PR1 validation:

- A linker undef: expected PR1 state reached (`needs_llm`, `matched_tier=null`, `degraded=false`, 1786/1800 tokens, near-match recorded at confidence 0.84).
- B depsolve: no regression (`direct_answer`, `fast_path`, `tier1`, `degraded=false`).
- D `%install`: no regression (`direct_answer`, `full_path`, `tier2`, `degraded=false`).

Implementation note: A validation must run with the ffmpeg source tree on
`real_smoke/A_20260519_144141`; validating against clean `tizen` cannot collect the injected
symbol context because the injected source line is absent.

## PR2 Completion Summary

Implemented Fix 4 plus the PR1 review follow-up.

- Review follow-up: near-match entries now include both `id` and `pattern_id` so consumers that read
  `matched_patterns[*].id` see the real pattern id.
- Scanner: real patch failure lines such as `can't find file to patch at input line 3` and
  `1 out of 1 hunk ignored` now produce `patch` events. The latter is canonicalized as
  `Hunk #1 FAILED: ...` so the existing tier1 hunk pattern can match without changing the pattern
  library.
- Scanner: a subsequent `%prep` `Bad exit status` rpm-phase event is marked as a cascade child of the
  latest patch failure event in `%prep`.
- Ranker: patch events in the failed phase receive a small `patch_failed_phase` boost, while the
  derived rpm-phase child receives the existing parent penalty.

Real-smoke PR2 validation:

- C patch failed: fixed (`direct_answer`, `fast_path`, `tier1`, `primary_error.kind=patch`,
  `degraded=false`, 338/1800 tokens).
- B depsolve: no regression (`direct_answer`, `fast_path`, `tier1`, `degraded=false`).
- D `%install`: no regression (`direct_answer`, `full_path`, `tier2`, `degraded=false`).
