# Decisions for M6: full_match

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-18 | Start M6 from merge commit `b134492` after M5 review approval and merge. | v0.5 §7, §8 | Keeps the handoff pointer aligned with reviewed `main`. | M6 branch starts from the latest merged baseline. |
| d002 | 2026-05-18 | Preserve M2 flat tier1 patterns as `direct_answer_tier1` shorthand and add optional nested tier fields. | M2 decision d003, v0.5 §3.5, §4 | Rewriting all M2 patterns would break quick_filter history and add review noise. The full_match loader can normalize both shapes. | Existing `tier: tier1` + `fix_template` patterns remain valid; tier2 patterns use `direct_answer_tier2`. |
| d003 | 2026-05-18 | Make `quick_filter` ignore non-tier1 patterns in the shared pattern library. | v0.5 §3.2, §3.5 | M6 introduces tier2 patterns into `patterns/gbs_errors.yaml`, but Layer 4a must continue evaluating only tier1 fast-path patterns. | M2 behavior stays scoped to 7 tier1 patterns while M6 can load all 12 patterns. |
| d004 | 2026-05-18 | Reject direct answers when evidence is degraded for both tier1 and tier2. | v0.5 §3.5 | v0.5 explicitly removed degraded direct_answer paths; uncertain evidence should go to LLM. | `determine_verdict()` returns `NEEDS_LLM` when `Evidence.degraded` is true. |
| d005 | 2026-05-18 | Add five tier2-only pattern definitions and two tier2 fields on existing tier1 patterns. | v0.5 §4, §9.4 | M6 needs at least 3 tier2 fixture hits and a full schema path for later direct-answer coverage. | Default library now has 12 total patterns: 7 tier1-evaluable patterns and 7 tier2-capable direct-answer definitions. |
