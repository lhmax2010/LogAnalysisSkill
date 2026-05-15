# Decisions for M3: rank_causes

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-15 | Start M3 from merge commit `77c7ad5` after M2 review approval. | v0.5 §7, §8 | Keeps the handoff pointer aligned with reviewed `main`. | M3 branch starts from latest merged baseline. |
| d002 | 2026-05-15 | Store the 8 semantic classes in `patterns/error_semantics.yaml` and load them through `SemanticClassifier`. | v0.5 §3.3, §4.3, Appendix C | Keeps scoring constants and regex hints reviewable without mixing them into ranking control flow. | M3 ranking uses data-driven semantic config; future changes must update tests and dev_memory. |
| d003 | 2026-05-15 | Apply `generic_error` gating only from Layer 0/1 scan context: `command_id`, `raw_offset`, failed phase match, and non-cascade event kind. | v0.5 §3.3 | M3 must not depend on M5 evidence collectors, but the v0.5 base 0.45 to 0.70 gating rule still needs deterministic context. | Generic raw errors can reach medium-high confidence only when scan context is sufficient. |
| d004 | 2026-05-15 | Fold parented `make_cascade` events to score 0.1 and apply parent/cascade penalties before Top-K selection. | v0.5 §3.3 | Cascades should explain propagation but should not outrank the direct diagnostic that caused them. | Top-1 fixtures prefer direct compiler/linker diagnostics over make cascades. |
| d005 | 2026-05-15 | Keep M3 output to ranked candidates and structured confidence reasons only. | v0.5 milestone boundaries | Evidence collection, spec parsing, and patch/install collectors belong to later milestones. | No M4/M5 modules were added in M3. |
