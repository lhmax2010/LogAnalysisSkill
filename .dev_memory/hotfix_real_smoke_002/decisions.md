# Decisions

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-19 | PR1 is limited to Fix 1/Fix 2/Fix 3. | `docs/real_smoke/hotfix_002_design.md`; user PR1 instruction. | The fixes are separable from scanner/ranker/linker-confidence changes and should be reviewed independently. | Only packet assembler/full_match behavior should change in PR1. |
| d002 | 2026-05-19 | A remaining `needs_llm` after PR1 is expected. | Hotfix_002 PR1 validation patch. | PR1 does not change linker confidence; it only removes abnormal degraded/truncation state and exposes near-match data. | PR1 validation checks A transparency/state, not tier2 verdict. |
| d003 | 2026-05-19 | B and D are mandatory no-regression real-smoke gates for each PR. | Hotfix_002 PR validation matrix. | B and D were clean in the initial smoke run and cover tier1 depsolve plus tier2 spec behavior. | Any B/D regression blocks continuation. |
