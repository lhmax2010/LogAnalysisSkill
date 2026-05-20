# Hotfix Real Smoke 003 Test Report

Date: 2026-05-20
Branch: `hotfix/real-smoke-003-package-data`

## Status

Completed.

## Unit / CI Gates

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer gbs_build_skill gbs_workflow` | pass | 43 source files checked. |
| `.venv/bin/pytest tests/unit/test_quick_filter.py tests/unit/test_semantic_classifier.py tests/unit/test_full_match.py -q` | pass | 103 passed; covers default package-anchored loads. |
| `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | pass | 389 passed; analyzer coverage 96.01%. |

## Required Validation

| Validation | Command shape | Result | Notes |
| --- | --- | --- | --- |
| Arbitrary cwd analyzer | `cd /tmp && .venv/bin/python -m gbs_analyzer analyze ...` | pass | Exit 0; packet written to `/tmp/h3_v1`; `primary_error.kind=compiler`, `tokens=1477`. |
| Pip-installed analyzer | clean `/tmp/h3_test` venv, install repo, run from `/tmp` | pass | Exit 0; packet written to `/tmp/h3_v2`; installed package contains `gbs_analyzer/patterns/{README.md,error_semantics.yaml,gbs_errors.yaml,schema.json}`. |
| Full regression | `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | pass | 389 passed; coverage 96.01%. |

## Additional Workflow Smoke

Ran `python -m gbs_workflow` from `/home/linhao/Toolchain/development/ffmpeg`
with output `/tmp/h3_workflow_ffmpeg`.

| Field | Value |
| --- | --- |
| Workflow exit | 1 |
| Analyzer result | `needs_llm` / `full_path` / `compiler` |
| Primary location | `libavcodec/utils.c:109` |
| Message | `implicit declaration of function 'av_temp_lss'` |
| Suggestion | `001_compile_error_inspect_compiler_error_at_libavcodec_utils_c_109.md` |

This confirms the analyzer subprocess can run from the user project cwd and still
load packaged pattern data.

## Environment Note

`python3 -m venv /tmp/h3_test` failed before package installation because the
machine lacks `python3.12-venv` / `ensurepip`. The pip-install validation used:

```bash
uv venv /tmp/h3_test
uv pip install --python /tmp/h3_test/bin/python /home/linhao/Toolchain/development/LogAnalysisSkill
```

The package was installed into `/tmp/h3_test/lib/python3.12/site-packages/gbs_analyzer`.
