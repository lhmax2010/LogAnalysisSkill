# Known Issues

## Out of Scope For PR1

- A linker undefined-reference confidence still lands around 0.84; this is Fix 5 / PR3.
- A therefore correctly remains `verdict=needs_llm` and `matched_tier=null` in PR1, while exposing the near-match metadata needed by downstream LLM consumers.

## Resolved In PR2

- C patch failure no longer ranks as `rpm_phase`; it now hits fast-path tier1 as `patch`.

## Deferred To v0.6

- `matched_patterns` near-match entries currently carry both `id` and `pattern_id` with the same
  value. This is intentional PR2 compatibility glue: v0.5 consumers may read `id`, while PR1 already
  emitted `pattern_id`. v0.6 should decide whether to keep both long term or deprecate one field.
- Evidence degradation is currently a single boolean used for both method-level fallback and
  packet-level reliability. PR3 d012 removed this boolean from the tier2 hard gate because
  `contains_all(required)` is the actual safety check. v0.6 should introduce explicit hard/soft
  degradation categories if future collectors need finer verdict policy.
- `event.tool` is unreliable in make/ninja/CMake-driven builds because it often records the top-level
  build driver instead of the real compiler/linker. PR3 d013 adds a narrow `undefined_reference`
  exception; v0.6 should consider scanner or command-parser improvements rather than broadening the
  exception to other categories.

## Watch Points

- If BudgetPool partial state has multiple sources beyond cumulative collector grants, stop and ask before redesigning the state machine.
- If final truncation cannot reach `max_tokens` after all safe fields are removed, record `packet_could_not_truncate_to_budget` rather than unsafe raw string truncation.
- PR3 resolved the linker undefined-reference confidence rule and the make-driven `tool_in` boundary.

## PR1 Validation Notes

- A validation must use the ffmpeg injection branch `real_smoke/A_20260519_144141` for `--src-root`; clean `tizen` lacks the injected symbol and causes unrelated `symbol_context_unavailable`.
- Full analyzer outputs were generated locally under `perf_baselines/pr1_A`, `pr1_B`, and `pr1_D`, but raw trace/evidence JSON outputs are ignored by repository rules. The committed baseline is the summarized PR1 validation table.

## PR2 Validation Notes

- C validation uses the archived C real buildlog and clean ffmpeg `tizen` source tree; fast-path patch matching does not depend on the injection branch source contents.
- Full analyzer outputs were generated locally under `perf_baselines/pr2_C`, `pr2_B`, and `pr2_D`, but raw trace/evidence JSON outputs are ignored by repository rules. The committed baseline is the summarized PR2 validation table.
