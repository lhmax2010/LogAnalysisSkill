# Decisions for M8: wrapper_and_e2e

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-18 | Start M8 from merge commit `18e4d33` after M7 review approval and merge. | v0.5 §7, §8, §13 | Keeps the MVP acceptance branch aligned with reviewed `main`. | M8 branch starts from the latest merged baseline and owns wrapper/e2e delivery. |
| d002 | 2026-05-18 | The M8 wrapper grants Level 2 (600 tokens) by default even when a collector estimates Level 3 as preferred. | v0.5 §3.4, §5, §10.3; M5 d005 | Existing tier2 MVP patterns mostly require Level 2 evidence, and Level 2 avoids post-hoc `budget_pool_partial` degradation after the assembler accounts for soft reserves. | E2E tier2 direct answers stay non-degraded for compile/spec/deps/missing-lib cases; Level 3-only symbol-context scenarios still fall through to LLM unless future BudgetPool preallocation is added. |
