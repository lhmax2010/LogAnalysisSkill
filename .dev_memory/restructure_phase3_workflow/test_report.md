# Test Report for Restructure Phase 3

Status: passed

## Real Workflow Scenario

- Source root: `/home/linhao/Toolchain/development/ffmpeg`
- Failure branch used for failure-path validation: `real_smoke/B_20260519_171554`
- Restored branch after validation: `tizen`
- Expected outcome: depsolve failure, analyzer direct-answer fast path, `DepsolveSuggester` advisory suggestion.

## Commands

| Check | Command | Result |
| --- | --- | --- |
| Installed mode setup | `cd /tmp && uv venv phase3_workflow_pip && uv pip install --python /tmp/phase3_workflow_pip/bin/python /home/linhao/Toolchain/development/LogAnalysisSkill` | pass; package built and installed |
| Installed mode package imports | import `gbs_workflow`, `gbs_build_skill`, and `gbs_analyzer` from `/tmp/phase3_workflow_pip` | pass; all from site-packages |
| Installed mode success path | `cd /tmp && /tmp/phase3_workflow_pip/bin/python -m gbs_workflow ... --output-dir /tmp/phase3_mode1_workflow` on ffmpeg `tizen` | pass; build success, no analyzer run |
| Installed mode failure path | `cd /tmp && /tmp/phase3_workflow_pip/bin/python -m gbs_workflow ... --output-dir /tmp/phase3_mode1_workflow_B` on ffmpeg `real_smoke/B_20260519_171554` | pass; build exit `1`, primary `depsolve`, verdict `direct_answer`, via `fast_path`, tier `tier1`, suggestion `001_depsolve_*.md` |
| Direct mode isolation | `cd /tmp && env PYTHONPATH= /usr/bin/python3 -c "import gbs_workflow/gbs_build_skill/gbs_analyzer"` | expected fail for all three packages |
| Direct mode failure path | `cd /tmp && env PYTHONPATH= /usr/bin/python3 /tmp/phase3_skill_layout/tizen-gbs-build-workflow/scripts/run_workflow.py ... --output-dir /tmp/phase3_mode2_workflow_B` | pass; build exit `1`, primary `depsolve`, verdict `direct_answer`, via `fast_path`, tier `tier1`, suggestion `001_depsolve_*.md` |
| Env-var discovery | non-sibling workflow folder plus `TIZEN_GBS_BUILD_SKILL_DIR` and `TIZEN_GBS_LOG_ANALYSIS_SKILL_DIR`, then `run_workflow.py --help` | pass |
| Focused workflow tests | `.venv/bin/pytest tests/unit/test_workflow.py -q` | `13 passed` |
| Lint | `.venv/bin/ruff check . && .venv/bin/ruff check . --select I --preview` | pass |
| Type check | `.venv/bin/mypy tizen-gbs-log-analysis/scripts/gbs_analyzer tizen-gbs-build-workflow/scripts/gbs_workflow tizen-gbs-build-workflow/scripts/run_workflow.py` | pass |
| Full regression | `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | `401 passed`, coverage `96.01%` |

## Mode 2 Subprocess Validation

The direct mode validation started with an empty `PYTHONPATH` and confirmed all three
packages were not importable in system Python. `run_workflow.py` then discovered sibling
skill folders, imported workflow/build/analyzer in the parent process, and passed sibling
scripts paths to the analyzer child process through a copied subprocess environment.
The presence of `/tmp/phase3_mode2_workflow_B/analyzer_output/evidence_packet.json`
confirms `python -m gbs_analyzer` worked in the child process.
