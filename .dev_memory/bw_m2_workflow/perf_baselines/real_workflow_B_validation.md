# BW-M2 Real Workflow Validation: ffmpeg B Depsolve

Date: 2026-05-20

## Environment

- Skill root: `/home/linhao/Toolchain/development/LogAnalysisSkill`
- Source root: `/home/linhao/Toolchain/development/ffmpeg`
- Branch: `real_smoke/B_20260519_171554`
- Output dir: `/tmp/loganalysis_bw_m2/workflow_B`

## Command

```bash
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python -m gbs_workflow \
  --conf /home/linhao/Toolchain/gbs.conf \
  --arch armv7l \
  --include-all \
  --src-root /home/linhao/Toolchain/development/ffmpeg \
  --output-dir /tmp/loganalysis_bw_m2/workflow_B \
  --timeout 1800
```

## Results

| Field | Value |
| --- | --- |
| Workflow exit | 1 |
| Build status | failed as expected |
| Analyzer verdict | direct_answer |
| Analyzer via | fast_path |
| Analyzer tier | tier1 |
| Primary kind | depsolve |
| Packet tokens | 332 |
| Packet degraded | false |
| Suggestions generated | 1 patch + 1 markdown |
| Patch apply check | pass |

## Artifact Sizes

| File | Bytes |
| --- | ---: |
| `compiler.log` | 2,412 |
| `analyzer_output/evidence_packet.json` | 1,276 |
| `workflow_summary.md` | 998 |
| depsolve patch | 370 |
| depsolve markdown | 651 |

## Notes

- The synthetic B branch already contains the missing `BuildRequires` line that
  triggers depsolve failure, so the generated patch duplicates that entry in this
  validation run.
- The patch is still valid git diff output and passed `git apply --check`.
- The ffmpeg tree was restored to `tizen` after validation.
