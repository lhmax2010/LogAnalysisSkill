# M6 Test Guide: full_match

## Environment Requirements

- Python 3.10+
- Editable install: `pip install -e .`
- Development dependencies: `pip install -r requirements-dev.txt`

## Quick Start

```bash
pytest tests/unit/test_full_match.py -v
pytest tests/functional/test_full_match_fixtures.py -v
pytest tests/unit/test_quick_filter.py -v
```

## Full Validation

```bash
ruff check .
mypy gbs_analyzer
pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
```

## Manual Full-Match Check

```bash
python - <<'PY'
from pathlib import Path
from subprocess import CalledProcessError

from gbs_analyzer.evidence.router import collector_for_candidate
from gbs_analyzer.full_match import full_match
from gbs_analyzer.scan_and_extract import scan_buildlog

def failing_ctags(_):
    raise CalledProcessError(1, "ctags")

fixture = Path("tests/fixtures/evidence_link_undef")
scan = scan_buildlog(fixture / "buildlog")
event = scan.as_dict()["events"][0]
candidate = {"event_id": event["id"], "kind": event["kind"]}
collector = collector_for_candidate(
    candidate,
    scan,
    src_root=fixture / "src",
    spec_path=fixture / "demo.spec",
    buildlog_path=fixture / "buildlog",
    ctags_runner=failing_ctags,
)
evidence = collector.collect(candidate, 900)
print(full_match(scan, candidate, evidence).as_dict())
PY
```

## Expected M6 Signals

- `quick_filter` still loads only the 7 tier1 fast-path patterns.
- `full_match` loads all 12 patterns from `patterns/gbs_errors.yaml`.
- Flat `tier: tier1` + `fix_template` remains valid shorthand for `direct_answer_tier1`.
- Tier2 direct answers require `Evidence.contains_all(evidence_required)`.
- Degraded evidence always returns `NEEDS_LLM`.

## Acceptance Criteria

- [ ] 10+ M6 unit tests pass.
- [ ] At least 3 tier2 fixture cases hit.
- [ ] `gbs_analyzer/full_match.py` coverage is above 85%.
- [ ] Full-match runtime is under 50ms per evaluation.
- [ ] M6 dev_memory and performance baselines are updated.
