# Known Issues

## Out of Scope For PR1

- C patch failure still ranks as `rpm_phase`; this is Fix 4 / PR2.
- A linker undefined-reference confidence still lands around 0.84; this is Fix 5 / PR3.
- A therefore correctly remains `verdict=needs_llm` and `matched_tier=null` in PR1, while exposing the near-match metadata needed by downstream LLM consumers.

## Watch Points

- If BudgetPool partial state has multiple sources beyond cumulative collector grants, stop and ask before redesigning the state machine.
- If final truncation cannot reach `max_tokens` after all safe fields are removed, record `packet_could_not_truncate_to_budget` rather than unsafe raw string truncation.

## PR1 Validation Notes

- A validation must use the ffmpeg injection branch `real_smoke/A_20260519_144141` for `--src-root`; clean `tizen` lacks the injected symbol and causes unrelated `symbol_context_unavailable`.
- Full analyzer outputs were generated locally under `perf_baselines/pr1_A`, `pr1_B`, and `pr1_D`, but raw trace/evidence JSON outputs are ignored by repository rules. The committed baseline is the summarized PR1 validation table.
