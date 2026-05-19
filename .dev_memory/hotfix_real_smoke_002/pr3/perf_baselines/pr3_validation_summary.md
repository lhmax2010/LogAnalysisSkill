# Hotfix Real Smoke 002 - PR3 Validation Summary

Date: 2026-05-19
Branch: `hotfix/real-smoke-002-pr3`

## Gates

| Case | verdict | via | tier | kind | confidence | degraded | tokens | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A linker undef | `direct_answer` | `full_path` | `tier2` | `linker_undef` | `0.90` | `false` | `1594/1800` | pass |
| B depsolve | `direct_answer` | `fast_path` | `tier1` | `depsolve` | `0.96` | `false` | `332/1800` | pass |
| C patch failed | `direct_answer` | `fast_path` | `tier1` | `patch` | `0.95` | `false` | `338/1800` | pass |
| D `%install` | `direct_answer` | `full_path` | `tier2` | `rpm_phase` | `0.38` | `false` | `1134/1800` | pass |

## Notes

- A validation used ffmpeg branch `real_smoke/A_20260519_144141` so source evidence includes the
  injected undefined reference call. The ffmpeg tree was restored to `tizen` afterward.
- B/C/D validation used the clean ffmpeg `tizen` source tree.
- Raw analyzer outputs live under `pr3_final_{A,B,C,D}/` locally and are ignored by repository rules.

## Hotfix_002 Final Outcome

The A/B/C/D real-smoke matrix now produces direct answers for all four archived real buildlogs:

- PR1 removed abnormal packet state and exposed near-match transparency.
- PR2 fixed patch failure cascade/ranking.
- PR3 completed linker undefined-reference semantics across ranking, tier2 degraded evidence, and
  make-driven `tool_in` handling.
