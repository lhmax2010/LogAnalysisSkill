# PR1 Real-Smoke Validation Summary

Date: 2026-05-19

| Case | verdict | via | matched_tier | primary kind | degraded | packet_tokens | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A linker undef | `needs_llm` | `full_path` | `null` | `linker_undef` | `false` | `1786/1800` | Near-match `linker_undefined_reference_tier2`, confidence `0.84`, `failure_reason=confidence_below_tier2_threshold`. |
| B depsolve | `direct_answer` | `fast_path` | `tier1` | `depsolve` | `false` | `332/1800` | No regression. |
| D `%install` | `direct_answer` | `full_path` | `tier2` | `rpm_phase` | `false` | `1134/1800` | No regression. |

## Source Branch Note

A was validated with `/home/linhao/Toolchain/development/ffmpeg` temporarily checked out to
`real_smoke/A_20260519_144141`, then restored to `tizen`. The injected symbol is absent on clean
`tizen`, so A source-context validation requires the injection branch.

## Ignored Local Outputs

The full local analyzer outputs were generated under:

- `.dev_memory/hotfix_real_smoke_002/perf_baselines/pr1_A/`
- `.dev_memory/hotfix_real_smoke_002/perf_baselines/pr1_B/`
- `.dev_memory/hotfix_real_smoke_002/perf_baselines/pr1_D/`

`evidence_packet.json`, `perf_report.json`, and trace outputs are ignored by repository rules, so this
summary is the committed baseline record for PR1.
