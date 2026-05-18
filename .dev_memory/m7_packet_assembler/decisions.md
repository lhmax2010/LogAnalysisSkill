# Decisions for M7: packet_assembler

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-18 | Start M7 from merge commit `3159fd1` after M6 review approval and merge. | v0.5 §7, §8 | Keeps the handoff pointer aligned with reviewed `main`. | M7 branch starts from the latest merged baseline. |
| d002 | 2026-05-18 | Treat M6 tier2 evidence requirements as extraction-method independent. | M6 review follow-up, v0.5 §3.5 | `Evidence.contains` carries semantic completeness such as `source_snippet` or `symbol_context`; `extraction_methods` records whether ctags/regex/window produced it. Happy ctags and fallback evidence should both satisfy tier2 when not degraded. | Added happy-ctags tier2 fixture coverage in M7 startup; no M6 d007 caveat is needed. |
