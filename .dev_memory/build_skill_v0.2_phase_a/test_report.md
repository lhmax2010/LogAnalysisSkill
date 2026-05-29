# Test Report for build_skill v0.2 Phase A

Status: passed.

## Commands

| Check | Command | Result |
| --- | --- | --- |
| Build runner focused tests | `.venv/bin/pytest tests/unit/test_build_runner.py -q` | `15 passed` |
| Build + workflow compatibility tests | `.venv/bin/pytest tests/unit/test_build_runner.py tests/unit/test_workflow.py -q` | `28 passed` |
| Ruff | `.venv/bin/ruff check . && .venv/bin/ruff check . --select I --preview` | pass |
| Mypy | `.venv/bin/mypy tizen-gbs-build/scripts/gbs_build_skill tizen-gbs-log-analysis/scripts/gbs_analyzer tizen-gbs-build-workflow/scripts/gbs_workflow` | pass; `43 source files` |
| Full regression | `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | `409 passed`, coverage `96.01%` |

## Real Validation

### ffmpeg success (`tizen`)

Command shape:

```bash
python -m gbs_build_skill \
  --conf /home/linhao/Toolchain/gbs.conf \
  --arch armv7l \
  --include-all \
  --src-dir /home/linhao/Toolchain/development/ffmpeg \
  --output-log /tmp/build_skill_v02_phase_a_success_api/compiler.log \
  --timeout 1800
```

Python API result:

```text
exit 0
log_path /tmp/build_skill_v02_phase_a_success_api/compiler.log
failure_log_path None
analysis_log_path /tmp/build_skill_v02_phase_a_success_api/compiler.log
package_name None
timed_out False
```

### ffmpeg failure (`real_smoke/E_compile_20260520`)

CLI stderr:

```text
exit=1
gbs_build_skill: build failed (exit 1)
gbs_build_skill: compiler log written to /tmp/build_skill_v02_phase_a_E/compiler.log
gbs_build_skill: failure log: /home/linhao/GBS-ROOT-TOOLCHAIN-GCC-PATCHES2/local/repos/tizen_unified_standard/armv7l/logs/fail/ffmpeg-8.0.1-0/log.txt
gbs_build_skill: recommended for analysis: /home/linhao/GBS-ROOT-TOOLCHAIN-GCC-PATCHES2/local/repos/tizen_unified_standard/armv7l/logs/fail/ffmpeg-8.0.1-0/log.txt
gbs_build_skill: package: ffmpeg-8.0.1-0
```

Extractor confirmation:

```text
failure_extract_pkg ffmpeg-8.0.1-0
failure_extract_exists True
```

### Fallback without `Leaving the logs in`

Constructed fake failure output without a structured GBS path:

```text
fallback_exit 9
fallback_log_path /tmp/build_skill_v02_phase_a_fallback/compiler.log
fallback_failure_log_path None
fallback_analysis_log_path /tmp/build_skill_v02_phase_a_fallback/compiler.log
fallback_package_name None
```

## Workspace Notes

- ffmpeg was restored to branch `tizen`.
- Existing untracked `/home/linhao/Toolchain/development/ffmpeg/compiler_Solution.log`
  was present before validation and was not modified.
- Local untracked `docs/reports/` in this repository was not included.
