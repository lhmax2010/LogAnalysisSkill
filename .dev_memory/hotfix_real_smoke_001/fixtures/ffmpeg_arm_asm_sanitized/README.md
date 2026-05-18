# ffmpeg ARM Assembler Real Smoke Fixture

Sanitized excerpt from the user's local ffmpeg GBS failure.

The intentionally injected root cause is an invalid ARM assembler instruction:

`libavcodec/arm/h264cmc_neon.S:43: Error: bad instruction`

The early `pristine-tar` error is recovered by the build flow and should not win Top-1 after the full hotfix.

Acceptance targets:

- Scanner command count is greater than zero.
- `failed_phase == "%build"`.
- Final Top-1 points at `libavcodec/arm/h264cmc_neon.S:43`.
- Packet token count stays within `--max-tokens 1800`.
