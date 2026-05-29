# Test Report for build_skill v0.2 Phase B

Status: passed.

## Commands

| Check | Command | Result |
| --- | --- | --- |
| Reference grep | `grep -rn "select_analysis_log\|GBS_FAILURE_LOG_PATTERN" --include="*.py" --exclude-dir=build .` | `select_analysis_log` absent; `GBS_FAILURE_LOG_PATTERN` only in build skill runner |
| Focused workflow tests | `.venv/bin/pytest tests/unit/test_workflow.py -q` | `12 passed` |
| Ruff | `.venv/bin/ruff check . && .venv/bin/ruff check . --select I --preview` | pass |
| Mypy | `.venv/bin/mypy tizen-gbs-build/scripts/gbs_build_skill tizen-gbs-log-analysis/scripts/gbs_analyzer tizen-gbs-build-workflow/scripts/gbs_workflow` | pass; `43 source files` |
| Full regression | `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | `408 passed`, coverage `96.01%` |

## Real Workflow Validation

All cases ran against `/home/linhao/Toolchain/development/ffmpeg` using
`/home/linhao/Toolchain/gbs.conf`, `armv7l`, and `--include-all`.

| Case | Branch | analysis_log_path | Verdict / Route | Suggestion | Tokens | Degraded |
| --- | --- | --- | --- | --- | --- | --- |
| A linker undef | `real_smoke/A_20260519_144141` | `/home/linhao/GBS-ROOT-TOOLCHAIN-GCC-PATCHES2/local/repos/tizen_unified_standard/armv7l/logs/fail/ffmpeg-8.0.1-0/log.txt` | `direct_answer / full_path / tier2 / linker_undef` | `linker_undef` | `1594` | `False` |
| B depsolve | `real_smoke/B_20260519_171554` | `/tmp/build_skill_v02_phase_b_B_api/compiler.log` | `direct_answer / fast_path / tier1 / depsolve` | `depsolve` advisory | `332` | `False` |
| C patch failed | `real_smoke/C_20260519_171941` | `/home/linhao/GBS-ROOT-TOOLCHAIN-GCC-PATCHES2/local/repos/tizen_unified_standard/armv7l/logs/fail/ffmpeg-8.0.1-0/log.txt` | `direct_answer / fast_path / tier1 / patch` | `patch_failed` | `338` | `False` |
| D rpm phase | `real_smoke/D_20260519_173333` | `/home/linhao/GBS-ROOT-TOOLCHAIN-GCC-PATCHES2/local/repos/tizen_unified_standard/armv7l/logs/fail/ffmpeg-8.0.1-0/log.txt` | `direct_answer / full_path / tier2 / rpm_phase` | `spec_script` | `1173` | `False` |
| E compile | `real_smoke/E_compile_20260520` | `/home/linhao/GBS-ROOT-TOOLCHAIN-GCC-PATCHES2/local/repos/tizen_unified_standard/armv7l/logs/fail/ffmpeg-8.0.1-0/log.txt` | `needs_llm / full_path / compiler at libavcodec/utils.c:109` | `compile_error` | `1512` | `False` |

## Notes

- D and E both used the structured failure log provided by build skill
  `analysis_log_path`, preserving the BW-M4 routing behavior without workflow's
  local selector.
- The total test count is lower than Phase A because Phase B intentionally
  removes two tests for the deleted `select_analysis_log` helper and replaces
  them with workflow-level contract coverage.
