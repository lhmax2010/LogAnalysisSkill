# BW-M4 Real Workflow Validation

Date: 2026-05-20

Output root: `/tmp/loganalysis_bw_m4_v2`

## Results

| Case | Branch | Exit | Primary kind | Verdict | Via | Tier | Failed phase | Tokens | Suggestion |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | --- |
| A | `real_smoke/A_20260519_144141` | 1 | linker_undef | direct_answer | full_path | tier2 | %build | 1594 | linker_undef advisory |
| B | `real_smoke/B_20260519_171554` | 1 | depsolve | direct_answer | fast_path | tier1 | n/a | 332 | depsolve advisory, no patch |
| C | `real_smoke/C_20260519_171941` | 1 | patch | direct_answer | fast_path | tier1 | %prep | 338 | patch_failed advisory |
| D | `real_smoke/D_20260519_173333` | 1 | rpm_phase | direct_answer | full_path | tier2 | %install | 1170 | spec_script advisory |
| unknown | synthetic packet | 1 | raw_error | n/a | n/a | n/a | %build | n/a | fallback advisory |

## Notes

- A/B/C/D used real ffmpeg branches and real `gbs_workflow` invocations.
- D initially failed when analyzer consumed the outer wrapper log; after workflow
  selected the structured GBS failure log, D routed to `SpecScriptSuggester`.
- Unknown fallback used a synthetic analyzer packet because no real unknown GBS
  branch exists in the ffmpeg smoke set.
- The ffmpeg worktree was restored to `tizen`.
