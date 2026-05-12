# Decisions for M2: quick_filter

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-12 | Start M2 from merge commit `c6dbec9` after M1 review approval. | v0.5 §7, §8 | Keeps the handoff pointer aligned with reviewed `main`. | M2 branch starts from latest merged baseline. |
| d002 | 2026-05-12 | Include approved M1 review follow-ups in M2. | User review instruction | The follow-ups improve scanner confidence but do not alter M2 architecture. | First M2 commits cover realistic perf and edge-case tests. |
