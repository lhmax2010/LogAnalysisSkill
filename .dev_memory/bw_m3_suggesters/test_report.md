# BW-M3 Test Report

Date: 2026-05-20
Branch: `feature/bw-m3-suggesters`

## Status

Completed.

## Unit / CI Gates

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/ruff check .` | pass | All checks passed. |
| `.venv/bin/mypy gbs_analyzer gbs_build_skill gbs_workflow` | pass | 43 source files checked. |
| `.venv/bin/pytest tests/unit/suggesters/test_depsolve.py tests/unit/suggesters/test_bw_m3_suggesters.py tests/unit/test_workflow.py --cov=gbs_workflow --cov-report=term-missing -q` | pass | 34 passed; `gbs_workflow` coverage 95%. |
| `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | pass | 387 passed; analyzer coverage 96.01%. |

## Suggester Coverage Matrix

| Packet kind | Suggester | Output | Patch |
| --- | --- | --- | --- |
| `depsolve` missing BuildRequires | `DepsolveSuggester` | BuildRequires patch + md | yes |
| `depsolve` already declared | `DepsolveSuggester` | repository/provider advisory | no |
| `linker_missing` | `LinkerMissingSuggester` | low-confidence BuildRequires candidate + guidance | yes |
| `linker_undef` | `LinkerUndefSuggester` | symbol/object/library guidance | no |
| `patch` | `PatchFailedSuggester` | `.rej` / patch refresh guidance | no |
| `spec_script` / `rpm_phase` | `SpecScriptSuggester` | spec phase command guidance | no |
| `compiler` | `CompileErrorSuggester` | source location / semantic class guidance | no |
| unsupported kind | `FallbackSuggester` | generic packet review guidance | no |

## Real Validation Scope

No real gbs run was performed in BW-M3. Per `docs/build_workflow/DESIGN.md` §6-§7,
BW-M4 owns A/B/C/D/unknown end-to-end fixture validation and Cline integration.
