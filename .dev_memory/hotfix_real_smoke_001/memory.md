# Hotfix Real Smoke 001 - ffmpeg ARM assembler mis-rank

Status: completed

## Scope

Real GBS buildlog smoke testing on `ffmpeg` exposed scanner misses caused by real RPM/GBS line formatting:

- GBS timestamp prefixes like `[  213s] ` prevented command, phase, and diagnostic regexes from matching.
- Real RPM phase markers use `Executing(%build): ...`, while MVP fixtures mostly used `+ %build`.
- The analyzer selected an early recovered `pristine-tar` raw error instead of the intended assembler failure.
- The generated packet exceeded the requested `--max-tokens 1800` cap.

This hotfix is split into two reviewable PRs:

1. `fix/scanner-real-gbs-prefix`: H1/H2 scanner root-cause fixes.
2. `fix/assembler-diagnostic-and-token-cap`: H3/H6 presentation and budget fixes.

## PR1 - Scanner Root Cause

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

## PR2 - Assembler Diagnostic And Token Cap

`fix/assembler-diagnostic-and-token-cap` implements H3/H6:

- Reuse `kind: compiler` for assembler diagnostics with uppercase `Error:` / `Warning:`.
- Add `details.is_assembler` and best-effort `details.tool` from the current command.
- Support `.s` as a source suffix in source-to-object cascade helpers.
- Add a final packet token guard in `assemble_packet()`.
- Record `packet_truncated_to_token_budget` when final truncation is required.

Real ffmpeg smoke after H3/H6:

```text
commands: 73
failed_phase: %build
primary_error: E017 compiler libavcodec/arm/h264cmc_neon.S:43
primary_details: {"is_assembler": true, "tool": "make"}
cascade_summary: make cascade: ffbuild/common.mak:93: libavcodec/arm/h264cmc_neon.o -> E018
packet_tokens: 1674 / 1800
evidence_collector: compile
source_snippet.extraction_method: line_window
```

H4 is not needed because the assembler diagnostic naturally wins Top-1 after H3.
H5 is not needed because existing suffix mapping links the make cascade to an assembler
event. The duplicate assembler diagnostic means the cascade links to `E018` while Top-1 is
`E017`; both point to the same `libavcodec/arm/h264cmc_neon.S:43` root cause.

PR2 regression results:

```text
ruff check .: pass
mypy gbs_analyzer: pass
pytest tests/e2e/test_m8_wrapper_e2e.py -q: 21 passed
pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=96: 316 passed, 96.25%
```

## Closure Summary

`hotfix_real_smoke_001` closed the MVP's first real-environment failure in a small,
reviewable hotfix cycle. Across PR #11 and PR #12, the analyzer now handles four root
causes exposed by the real ffmpeg GBS buildlog:

- real GBS timestamp/ANSI prefixes no longer hide commands, phases, or diagnostics;
- real RPM `Executing(%build):` phase markers set `failed_phase`;
- assembler diagnostics are classified as `kind: compiler` with source file and line;
- final packets respect the requested token cap.

The same real ffmpeg buildlog now produces the intended root cause:

```text
Top-1: E017 compiler libavcodec/arm/h264cmc_neon.S:43
packet_tokens: 1674 / 1800
```

No H4/H5/v0.6 scope was added because H3 made Top-1 correct and existing `.S -> .o`
suffix mapping linked the cascade automatically.
