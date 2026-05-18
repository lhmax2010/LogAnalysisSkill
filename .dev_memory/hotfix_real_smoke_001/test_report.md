# Test Report

## PR1 H1/H2

```text
ruff check scan/test files: pass
mypy gbs_analyzer: pass
pytest tests/e2e/test_m8_wrapper_e2e.py -q: 21 passed
pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=96: 308 passed, 96.40%
```

Existing 20 fixture buildlogs do not contain GBS timestamps or ANSI escapes;
normalization is a no-op on them, so they remain green by design.

## PR2 H3/H6

Targeted checks:

```text
ruff check selected PR2 files: pass
mypy gbs_analyzer: pass
pytest tests/unit/test_scan_and_extract.py tests/unit/test_evidence_collectors.py tests/unit/test_packet_assembler.py tests/unit/test_source_to_object.py -q: 109 passed
pytest tests/e2e/test_m8_wrapper_e2e.py -q: 21 passed
pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=96: 316 passed, 96.25%
```

Real ffmpeg smoke:

```text
commands: 73
failed_phase: %build
Top-1: E017 compiler libavcodec/arm/h264cmc_neon.S:43
cascade_summary: make cascade: ffbuild/common.mak:93: libavcodec/arm/h264cmc_neon.o -> E018
packet_tokens: 1674 / 1800
degraded_reasons: ["packet_truncated_to_token_budget"]
```

The cascade links to `E018` because the assembler emits the same file/line diagnostic twice;
Top-1 `E017` and cascade parent `E018` describe the same root cause location.
