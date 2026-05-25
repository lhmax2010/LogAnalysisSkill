# Test Report for Restructure Phase 2

Status: passed

## Real Log

- Buildlog: `/tmp/h3_rev_workflow/compiler.log`
- Source root: `/home/linhao/Toolchain/development/ffmpeg`
- Expected primary error: `compiler libavcodec/utils.c:109`

## Commands

| Check | Command | Result |
| --- | --- | --- |
| Installed mode setup | `cd /tmp && uv venv phase2_analyzer_pip && uv pip install --python /tmp/phase2_analyzer_pip/bin/python /home/linhao/Toolchain/development/LogAnalysisSkill` | pass; package built and installed without duplicate-package errors |
| Installed mode package data | inspect `Path(gbs_analyzer.__file__).parent / "patterns"` in `/tmp/phase2_analyzer_pip` | pass; `README.md`, `error_semantics.yaml`, `gbs_errors.yaml`, `schema.json` present |
| Installed mode analyzer | `cd /tmp && /tmp/phase2_analyzer_pip/bin/python -m gbs_analyzer analyze /tmp/h3_rev_workflow/compiler.log --src-root /home/linhao/Toolchain/development/ffmpeg --max-tokens 1800 --output-dir /tmp/phase2_mode1` | pass; Top-1 `compiler libavcodec/utils.c:109`, tokens `1438` |
| Direct mode isolation | `cd /tmp && env PYTHONPATH= /usr/bin/python3 -c "import gbs_analyzer"` | expected fail; confirms system Python does not already have `gbs_analyzer` |
| Direct mode analyzer | `cd /tmp && env PYTHONPATH= /usr/bin/python3 /tmp/phase2_skill_layout/tizen-gbs-log-analysis/scripts/run_analyzer.py analyze /tmp/h3_rev_workflow/compiler.log --src-root /home/linhao/Toolchain/development/ffmpeg --max-tokens 1800 --output-dir /tmp/phase2_mode2` | pass; Top-1 `compiler libavcodec/utils.c:109`, tokens `1064` using local token fallback |
| Workflow analyzer import dependency | `.venv/bin/python -c "from gbs_analyzer.tizen.spec_minimal import SpecMinimalParser; print('workflow analyzer import dependency ok')"` | pass |
| Workflow analyzer subprocess entry | `cd /tmp && /home/linhao/Toolchain/development/LogAnalysisSkill/.venv/bin/python -m gbs_analyzer analyze /tmp/h3_rev_workflow/compiler.log --src-root /home/linhao/Toolchain/development/ffmpeg --max-tokens 1800 --output-dir /tmp/phase2_subprocess_entry` | pass; Top-1 `compiler libavcodec/utils.c:109`, tokens `1438` |
| Lint | `.venv/bin/ruff check .` | pass |
| Type check | `.venv/bin/mypy tizen-gbs-log-analysis/scripts/gbs_analyzer tizen-gbs-log-analysis/scripts/run_analyzer.py` | pass |
| Full regression | `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | `399 passed`, coverage `96.01%` |
| CI import-order follow-up | `.venv/bin/ruff check . && .venv/bin/ruff check . --select I --preview` | pass |
| Full regression after CI import-order follow-up | `.venv/bin/pytest tests/ -q` | `399 passed` |

## Mode 2 Isolation

The direct folder check copied only `tizen-gbs-log-analysis/` into `/tmp/phase2_skill_layout/`
and ran with `PYTHONPATH=` from `/tmp`. A separate system Python import check confirmed
`gbs_analyzer` was not installed in that interpreter, so `scripts/run_analyzer.py` exercised
its local `scripts/` path insertion.

## CI Follow-up

After package discovery started treating `gbs_analyzer` as a first-party package from
`tizen-gbs-log-analysis/scripts/`, GitHub ruff required import block spacing in workflow
suggesters and analyzer-focused tests. This was a formatting-only follow-up; runtime
behavior is unchanged.
