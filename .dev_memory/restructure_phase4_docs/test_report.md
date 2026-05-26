# Test Report for Restructure Phase 4

Status: passed.

## Commands

| Check | Command | Result |
| --- | --- | --- |
| Launcher help | `.venv/bin/python tizen-gbs-build/scripts/run_build.py --help`; `.venv/bin/python tizen-gbs-log-analysis/scripts/run_analyzer.py --help`; `.venv/bin/python tizen-gbs-build-workflow/scripts/run_workflow.py --help` | pass; help text written for all three launchers |
| Cline JSON syntax | `json.loads()` for `integrations/cline/analyze_gbs.json` and `integrations/cline/build_workflow.json` | pass |
| Active old-path grep | `rg -P "(?<!scripts/)\\bgbs_analyzer/|(?<!scripts/)\\bgbs_build_skill/|(?<!scripts/)\\bgbs_workflow/" ...` on active docs/integrations/tests | pass; remaining hits are new `scripts/<package>/` layout or `.gbs_workflow` output paths |
| Clean install setup | `uv venv --seed /tmp/phase4_clean_install` then `/tmp/phase4_clean_install/bin/python -m pip install .` | pass; `python3 -m venv` unavailable on this machine due missing `ensurepip`, so seeded `uv` venv supplied pip |
| Clean install import | from `/tmp`, import `gbs_analyzer`, `gbs_build_skill`, `gbs_workflow` using `/tmp/phase4_clean_install/bin/python` | pass; all loaded from site-packages |
| Package data | inspect `Path(gbs_analyzer.__file__).parent / "patterns"` in clean install | pass; `README.md`, `error_semantics.yaml`, `gbs_errors.yaml`, `schema.json` present |
| Installed module help | from `/tmp`, run `/tmp/phase4_clean_install/bin/python -m gbs_build_skill --help`, `python -m gbs_analyzer --help`, and `python -m gbs_workflow --help` | pass |
| Unit/regression smoke | `.venv/bin/pytest tests/ -q` | pass; `401 passed in 4.24s` |
| Full regression with coverage | `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | pass; `401 passed`, coverage `96.01%` |

## Notes

- `python3 -m venv` failed because the system Python lacks `ensurepip`; this is an
  environment package issue (`python3.12-venv` missing), not a project packaging
  failure. Validation used `uv venv --seed` and then standard `python -m pip install .`.
- Historical snapshots intentionally still contain old path references.
