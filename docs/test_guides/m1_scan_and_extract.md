# M1 Test Guide: scan_and_extract

## Environment Requirements

- Python 3.10+
- Editable install: `pip install -e .`
- Development dependencies: `pip install -r requirements-dev.txt`

## Quick Start

```bash
pytest tests/unit/test_scan_and_extract.py -v
pytest tests/functional/test_scan_fixtures.py -v
```

## Full Validation

```bash
ruff check .
mypy gbs_analyzer
pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
```

## Scan a Buildlog Manually

The public CLI is introduced later. For M1, call the scanner from Python:

```bash
python - <<'PY'
from pathlib import Path
from gbs_analyzer.scan_and_extract import scan_buildlog

result = scan_buildlog(Path("tests/fixtures/scan_compile_error/buildlog"))
print(result.as_dict())
PY
```

## Expected M1 Signals

- Phase markers such as `+ %build` are recorded in `result.phases`.
- Command boundaries starting with `+ ` are recorded in `result.commands`.
- Plain text and `.gz` buildlogs are supported.
- Diagnostic event kinds include:
  `compiler`, `linker_undef`, `linker_missing`, `patch`, `spec_script`,
  `depsolve`, `install_missing`, `werror`, `make_cascade`, `rpm_phase`, and `raw_error`.
- Make cascade targets are linked to parent compiler events only when suffix matching is unique.

## Acceptance Criteria

- [ ] 30+ unit tests pass.
- [ ] 5 scanner fixtures pass.
- [ ] Coverage is at least 85% for M1 code.
- [ ] 100 MB single-pass scan completes in under 8 seconds.
- [ ] M1 dev_memory and performance baseline are updated.
