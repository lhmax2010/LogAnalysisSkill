# PR2 Real-Smoke Validation Summary

Date: 2026-05-19

| Case | verdict | via | matched_tier | primary kind | degraded | packet_tokens | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C patch failed | `direct_answer` | `fast_path` | `tier1` | `patch` | `false` | `338/1800` | `Bad exit status (%prep)` is parented to the preceding patch failure. |
| B depsolve | `direct_answer` | `fast_path` | `tier1` | `depsolve` | `false` | `332/1800` | No regression. |
| D `%install` | `direct_answer` | `full_path` | `tier2` | `rpm_phase` | `false` | `1134/1800` | No regression. |

## Scanner Cascade Check

From the archived C real buildlog:

- `E001 patch` at line 171: `error: patch failed: can't find file to patch at input line 3`
- `E002 patch` at line 181: `Hunk #1 FAILED: 1 out of 1 hunk ignored`
- `E003 rpm_phase` at line 182: parent `E002`, details include `derived_from=patch_failed`

## Ignored Local Outputs

The full local analyzer outputs were generated under:

- `.dev_memory/hotfix_real_smoke_002/perf_baselines/pr2_C/`
- `.dev_memory/hotfix_real_smoke_002/perf_baselines/pr2_B/`
- `.dev_memory/hotfix_real_smoke_002/perf_baselines/pr2_D/`

`evidence_packet.json`, `perf_report.json`, and trace outputs are ignored by repository rules, so this
summary is the committed baseline record for PR2.
