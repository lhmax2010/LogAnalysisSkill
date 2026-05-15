# Decisions for M2: quick_filter

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-12 | Start M2 from merge commit `c6dbec9` after M1 review approval. | v0.5 §7, §8 | Keeps the handoff pointer aligned with reviewed `main`. | M2 branch starts from latest merged baseline. |
| d002 | 2026-05-12 | Include approved M1 review follow-ups in M2. | User review instruction | The follow-ups improve scanner confidence but do not alter M2 architecture. | First M2 commits cover realistic perf and edge-case tests. |
| d003 | 2026-05-15 | Use a flattened tier1-only pattern schema in M2 as staged implementation. | M2 review follow-up, v0.5 §3.2, §4 | M2 only consumes Layer 4a tier1 direct-answer patterns; implementing the full tier1/tier2 nested full_match schema early would pull M6 concerns into M2. | M6 should preserve current `tier: tier1` / `fix_template` as shorthand for `direct_answer_tier1` and add optional `direct_answer_tier2` fields instead of rewriting M2 patterns. |
| d004 | 2026-05-15 | Add `event_kinds` to tier1 patterns as an implementation extension. | M2 review follow-up, v0.5 §3.2 | Prefiltering by scan event kind avoids unnecessary regex work and prevents unrelated events from matching a broad pattern. | `event_kinds` remains a performance/safety guard; semantic constraints still live in `required_context` and pattern regexes. |
