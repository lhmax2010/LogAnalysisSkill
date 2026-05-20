# BW-M4 Test Report

Date: 2026-05-20
Branch: `feature/bw-m4-e2e`

## Status

Completed.

## Unit / CI Gates

| Command | Result | Notes |
| --- | --- | --- |
| `python3 -c "from gbs_workflow.suggesters.fallback import FallbackSuggester; print('OK')"` | pass | Confirmed BW-M3 review syntax concern was a display artifact. |
| `.venv/bin/ruff check gbs_workflow/suggesters/fallback.py` | pass | Fallback file check. |
| `python3 -m json.tool integrations/cline/build_workflow.json` | pass | Cline workflow JSON is valid. |
| `.venv/bin/ruff check gbs_workflow/suggesters/compile_error.py tests/e2e/test_build_workflow_e2e.py` | pass | Focused checks during implementation. |
| `.venv/bin/pytest tests/unit/test_workflow.py tests/e2e/test_build_workflow_e2e.py -q` | pass | 16 passed; structured log and workflow E2E coverage. |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer gbs_build_skill gbs_workflow` | pass | 43 source files checked. |
| `.venv/bin/pytest tests/unit/suggesters/test_depsolve.py tests/unit/suggesters/test_bw_m3_suggesters.py tests/unit/test_workflow.py tests/e2e/test_build_workflow_e2e.py --cov=gbs_workflow --cov-report=term-missing -q` | pass | 44 passed; `gbs_workflow` coverage 95%. |
| `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | pass | 397 passed; analyzer coverage 96.01%. |

## Real Workflow Validation

Output root: `/tmp/loganalysis_bw_m4_v2`

| Case | Branch | Workflow exit | Analyzer result | Suggestion | Result |
| --- | --- | ---: | --- | --- | --- |
| A linker_undef | `real_smoke/A_20260519_144141` | 1 | `direct_answer` / `full_path` / `tier2` / `linker_undef` / `%build` / `1594 tokens` / `degraded=false` | `LinkerUndefSuggester` advisory | pass |
| B depsolve existing BuildRequires | `real_smoke/B_20260519_171554` | 1 | `direct_answer` / `fast_path` / `tier1` / `depsolve` / `332 tokens` / `degraded=false` | `DepsolveSuggester` advisory, no duplicate patch | pass |
| C patch failed | `real_smoke/C_20260519_171941` | 1 | `direct_answer` / `fast_path` / `tier1` / `patch` / `%prep` / `338 tokens` / `degraded=false` | `PatchFailedSuggester` advisory | pass |
| D rpm_phase | `real_smoke/D_20260519_173333` | 1 | `direct_answer` / `full_path` / `tier2` / `rpm_phase` / `%install` / `1170 tokens` / `degraded=false` | `SpecScriptSuggester` advisory | pass |
| Unknown fallback | synthetic packet | 1 | `raw_error` packet | `FallbackSuggester` advisory | pass |

The ffmpeg tree was restored to `tizen` after validation.

## D Case Finding

The first D workflow run analyzed the outer `compiler.log` and produced
`raw_error -> FallbackSuggester`. Running analyzer directly on the GBS structured
`/logs/fail/.../log.txt` produced the expected `rpm_phase`. BW-M4 therefore adds
workflow selection of the structured failure log when present.
