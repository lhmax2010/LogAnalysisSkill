# M3 Test Guide: rank_causes

## Environment Requirements

- Python 3.10+
- Editable install: `pip install -e .`
- Development dependencies: `pip install -r requirements-dev.txt`

## Quick Start

```bash
pytest tests/unit/test_semantic_classifier.py -v
pytest tests/unit/test_rank_causes.py -v
pytest tests/functional/test_rank_fixtures.py -v
```

## Full Validation

```bash
ruff check .
mypy gbs_analyzer
pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
```

## Manual Ranking Check

```bash
python - <<'PY'
from pathlib import Path
from gbs_analyzer.scan_and_extract import scan_buildlog
from gbs_analyzer.rank_causes import rank_causes

scan = scan_buildlog(Path("tests/fixtures/rank_missing_lib/buildlog"))
result = rank_causes(scan)
print(result.as_dict()["root_cause_candidates"][0])
PY
```

## Expected M3 Signals

- The semantic classifier recognizes the 8 v0.5 semantic classes.
- `generic_error` uses base confidence 0.45 and only gates to 0.70 when scan context is sufficient.
- Parented `make_cascade` events do not outrank their direct parent diagnostic.
- Top-K candidates include `confidence_reason` entries explaining semantic class, cascade probability, and bonuses or penalties.
- Ranking does not invoke spec parsing, evidence collectors, or M4/M5 modules.

## Acceptance Criteria

- [ ] 15+ M3 unit tests pass.
- [ ] Top-1 accuracy on ranking fixtures is >= 80%.
- [ ] Ranking runtime is under 50ms.
- [ ] M2 review follow-ups remain covered.
- [ ] M3 dev_memory and performance baselines are updated.
