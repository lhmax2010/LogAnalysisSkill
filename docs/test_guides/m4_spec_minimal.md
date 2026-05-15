# M4 Test Guide: spec_minimal

## Environment Requirements

- Python 3.10+
- Editable install: `pip install -e .`
- Development dependencies: `pip install -r requirements-dev.txt`

## Quick Start

```bash
pytest tests/unit/test_spec_minimal.py -v
pytest tests/functional/test_spec_fixtures.py -v
```

## Full Validation

```bash
ruff check .
mypy gbs_analyzer
pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
```

## Manual Spec Check

```bash
python - <<'PY'
from pathlib import Path
from gbs_analyzer.tizen.spec_minimal import SpecMinimalParser

fixture = Path("tests/fixtures/spec_basic")
parser = SpecMinimalParser(fixture / "demo.spec", buildlog_path=fixture / "buildlog")
print(parser.extract_buildrequires())
print(parser.extract_patches())
print(parser.extract_sources())
print(parser.extract_section_failure_context("%build"))
print(parser.get_parse_status())
PY
```

## Expected M4 Signals

- `find_spec_file` finds exact package specs and rejects ambiguous source roots.
- BuildRequires, Patch, and Source declarations are extracted as raw spec data.
- `%prep`, `%build`, `%install`, and other top-level sections can be extracted by name.
- Failure context reports the last `+ ` shell command and its output within the requested phase.
- `get_parse_status` always marks macro expansion, conditional evaluation, and subpackage resolution as not performed.
- The uncertainty prompt text is stored under `templates/` for M7 packet assembly.

## Acceptance Criteria

- [ ] 15+ M4 unit tests pass.
- [ ] 5 spec fixtures extract successfully.
- [ ] Spec extraction runtime is under 200ms.
- [ ] M3 review follow-ups remain covered.
- [ ] M4 dev_memory and performance baselines are updated.
