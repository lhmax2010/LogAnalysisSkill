# M2 Test Guide: quick_filter

## Environment Requirements

- Python 3.10+
- Editable install: `pip install -e .`
- Development dependencies: `pip install -r requirements-dev.txt`

## Quick Start

```bash
pytest tests/unit/test_quick_filter.py -v
pytest tests/functional/test_quick_filter_fixtures.py -v
```

## Full Validation

```bash
ruff check .
mypy gbs_analyzer
pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
```

## Manual Fast-Path Check

```bash
python - <<'PY'
from pathlib import Path
from gbs_analyzer.scan_and_extract import scan_buildlog
from gbs_analyzer.quick_filter import quick_filter

scan = scan_buildlog(Path("tests/fixtures/fast_path_missing_lib/buildlog"))
result = quick_filter(scan)
print(result.hit)
print(result.match.minimal_packet if result.match else None)
PY
```

## Expected M2 Signals

- Only tier1-allowed categories may produce direct answers:
  `depsolve_failure`, `patch_failed`, `linker_missing_lib`, `install_file_missing`.
- Forbidden categories do not hit fast path:
  `undefined_reference`, `compile_error`, `werror_triggered`, `rpm_phase_failure`,
  `spec_script_error`.
- Tier1 fix templates are conservative, length-limited, and mention `expand`.
- Required context and negative patterns are enforced.
- Warning-block detection prevents unsafe linker-missing fast-path hits.

## Acceptance Criteria

- [ ] 20+ M2 unit tests pass.
- [ ] 4 Fast-Path fixtures hit.
- [ ] Quick-filter runtime is under 100ms.
- [ ] M1 review follow-up densified scan test passes.
- [ ] M2 dev_memory and performance baselines are updated.
