# Hotfix Real Smoke 001 - ffmpeg ARM assembler mis-rank

## Scope

Real GBS buildlog smoke testing on `ffmpeg` exposed scanner misses caused by real RPM/GBS line formatting:

- GBS timestamp prefixes like `[  213s] ` prevented command, phase, and diagnostic regexes from matching.
- Real RPM phase markers use `Executing(%build): ...`, while MVP fixtures mostly used `+ %build`.
- The analyzer selected an early recovered `pristine-tar` raw error instead of the intended assembler failure.
- The generated packet exceeded the requested `--max-tokens 1800` cap.

This hotfix is split into two reviewable PRs:

1. `fix/scanner-real-gbs-prefix`: H1/H2 scanner root-cause fixes.
2. `fix/assembler-diagnostic-and-token-cap`: H3/H6 presentation and budget fixes.

## Current PR

`fix/scanner-real-gbs-prefix` implements only H1/H2:

- Preserve `LogLine.raw_text` and `LogLine.gbs_seconds`.
- Normalize `LogLine.text` by stripping the minimal real GBS prefix set.
- Support exactly four RPM `Executing(...)` build phase markers.
- Keep existing `+ %build` style markers working.

H3/H6 remain out of scope for this PR. H4/H5 are deferred unless H1/H2/H3 prove insufficient on the real ffmpeg buildlog.

## Verification Plan

- Existing 20 M8 E2E fixtures must remain green.
- Full suite must remain green.
- Real ffmpeg scanner smoke must show `commands > 0` and `failed_phase == "%build"`.
- Full Top-1 correctness is expected after H3, not after this scanner-only PR.

## Verification Results

Scanner-only real ffmpeg smoke after H1/H2:

```text
commands: 73
failed_phase: %build
events: 20
primary after wrapper: libavcodec/arm/h264cmc_neon.S:43 as raw_error
packet_tokens after wrapper: 3342
```

The scanner root cause is fixed. H3 remains necessary so the assembler diagnostic is
classified as `kind: compiler` with file/line fields, allowing cascade linking and compile
evidence collection. H6 remains necessary because the final packet still exceeds
`--max-tokens 1800`.

Regression results:

```text
ruff check scan/test files: pass
mypy gbs_analyzer: pass
pytest tests/e2e/test_m8_wrapper_e2e.py -q: 21 passed
pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=96: 308 passed, 96.40%
```
