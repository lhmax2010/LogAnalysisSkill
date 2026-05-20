# BW-M1 Real gbs Validation

Date: 2026-05-20
Environment:
- `gbs 2.0.6`
- conf: `/home/linhao/Toolchain/gbs.conf`
- source: `/home/linhao/Toolchain/development/ffmpeg`
- command: `/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python -m gbs_build_skill`

## Results

| Case | Branch | Exit | Log size | Log marker |
| --- | --- | ---: | ---: | --- |
| Success | `tizen` | 0 | 98,715 bytes | `info: Done` |
| Failure B depsolve | `real_smoke/B_20260519_171554` | 1 | 2,412 bytes | `nothing provides pkgconfig(nonexistent-pkg-xxxyzz)` |

## Local Output Paths

These files were generated locally and are not committed:

- `/tmp/loganalysis_bw_m1/ffmpeg_success.log`
- `/tmp/loganalysis_bw_m1/ffmpeg_failure_B.log`

The ffmpeg tree was restored to `tizen` after validation.
