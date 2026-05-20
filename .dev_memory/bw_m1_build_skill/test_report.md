# BW-M1 Test Report

Date: 2026-05-20
Branch: `feature/bw-m1-build-skill`

## Status

Completed.

## Unit / CI Gates

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer gbs_build_skill` | pass | 29 source files checked. |
| `.venv/bin/pytest tests/unit/test_build_runner.py --cov=gbs_build_skill --cov-report=term-missing -q` | pass | 6 passed; `gbs_build_skill` coverage 90%. |
| `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=96` | pass | 352 passed; existing analyzer coverage 96.01%. |

## Real gbs Validation

Commands used `/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python -m gbs_build_skill`
from the ffmpeg source tree.

| Case | Branch | Exit | Log path | Log size | Result |
| --- | --- | ---: | --- | ---: | --- |
| Success | `tizen` | 0 | `/tmp/loganalysis_bw_m1/ffmpeg_success.log` | 98,715 bytes | pass |
| Failure B depsolve | `real_smoke/B_20260519_171554` | 1 | `/tmp/loganalysis_bw_m1/ffmpeg_failure_B.log` | 2,412 bytes | pass |

Failure B log tail includes:

```text
nothing provides pkgconfig(nonexistent-pkg-xxxyzz)
error: <gbs>some packages failed to be built
```

The ffmpeg tree was restored to `tizen` after validation.
