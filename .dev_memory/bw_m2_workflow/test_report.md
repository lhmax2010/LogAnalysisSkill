# BW-M2 Test Report

Date: 2026-05-20
Branch: `feature/bw-m2-workflow`

## Status

Completed.

## Unit / CI Gates

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer gbs_build_skill gbs_workflow` | pass | 36 source files checked. |
| `.venv/bin/pytest tests/unit/suggesters/test_depsolve.py tests/unit/test_workflow.py --cov=gbs_workflow --cov-report=term-missing -q` | pass | 18 passed; `gbs_workflow` coverage 93%. |
| `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=96` | pass | 371 passed; analyzer coverage 96.01%. |

## Real Workflow Validation

Command used:

```bash
/home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python -m gbs_workflow \
  --conf /home/linhao/Toolchain/gbs.conf \
  --arch armv7l \
  --include-all \
  --src-root /home/linhao/Toolchain/development/ffmpeg \
  --output-dir /tmp/loganalysis_bw_m2/workflow_B \
  --timeout 1800
```

| Case | Branch | Workflow exit | Analyzer result | Suggestions | Patch check | Result |
| --- | --- | ---: | --- | ---: | --- | --- |
| B depsolve | `real_smoke/B_20260519_171554` | 1 | `direct_answer` / `fast_path` / `tier1` / `depsolve` / `degraded=false` / `332 tokens` | 1 patch + 1 md | `git apply --check` pass | pass |

Files produced:

- `/tmp/loganalysis_bw_m2/workflow_B/compiler.log`
- `/tmp/loganalysis_bw_m2/workflow_B/analyzer_output/evidence_packet.json`
- `/tmp/loganalysis_bw_m2/workflow_B/analyzer_output/evidence_packet.md`
- `/tmp/loganalysis_bw_m2/workflow_B/analyzer_output/perf_report.json`
- `/tmp/loganalysis_bw_m2/workflow_B/suggestions/001_depsolve_add_buildrequires_for_pkgconfig_nonexistent_pkg_.patch`
- `/tmp/loganalysis_bw_m2/workflow_B/suggestions/001_depsolve_add_buildrequires_for_pkgconfig_nonexistent_pkg_.md`
- `/tmp/loganalysis_bw_m2/workflow_B/workflow_summary.md`

The ffmpeg tree was restored to `tizen` after validation.
