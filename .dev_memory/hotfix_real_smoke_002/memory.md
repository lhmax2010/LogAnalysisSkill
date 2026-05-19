# Hotfix Real Smoke 002 - PR1

Status: in_progress

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
