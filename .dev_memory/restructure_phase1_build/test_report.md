# Test Report for Restructure Phase 1

Status: passed

## Environment Notes

- Local `.venv` was refreshed with `uv pip install -e .` after the package move so editable package discovery used the new `tizen-gbs-build/scripts/` location.
- A stale untracked root `gbs_build_skill/__pycache__/` from earlier local runs was removed; it is not part of the repository and is not included in this PR.

## Commands

| Check | Command | Result |
| --- | --- | --- |
| Installed mode build CLI | `cd /tmp && /tmp/phase1_build_pip/bin/python -m gbs_build_skill --help` | pass; help text printed |
| Installed mode workflow import | `cd /tmp && /tmp/phase1_build_pip/bin/python -c "from gbs_workflow.workflow import run_workflow; from gbs_build_skill.runner import BuildOptions; print('installed-workflow-build-import=OK')"` | pass |
| Direct folder mode launcher | `cd /tmp && env PYTHONPATH= /usr/bin/python3 /tmp/phase1_skill_layout/tizen-gbs-build/scripts/run_build.py --help` | pass; help text printed |
| Local workflow import | `.venv/bin/python -c "from gbs_build_skill.runner import BuildOptions; from gbs_workflow.workflow import run_workflow; print('workflow-build-import=OK')"` | pass |
| Focused build tests | `.venv/bin/pytest tests/unit/test_build_runner.py -q` | `7 passed` |
| Lint | `.venv/bin/ruff check tizen-gbs-build/scripts/run_build.py tizen-gbs-build/scripts/gbs_build_skill pyproject.toml` | pass |
| Type check | `.venv/bin/mypy tizen-gbs-build/scripts/gbs_build_skill tizen-gbs-build/scripts/run_build.py` | pass |
| Full regression | `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | `399 passed`, coverage `96.01%` |

## Mode 2 Isolation

The direct folder check copied only `tizen-gbs-build/` into `/tmp/phase1_skill_layout/` and ran with `PYTHONPATH=` from `/tmp`. This verifies `scripts/run_build.py` used its own sibling `scripts/` directory rather than an installed package or the repository root.
