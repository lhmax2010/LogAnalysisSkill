# M5 Test Guide: evidence collectors

## Environment Requirements

- Python 3.10+
- Editable install: `pip install -e .`
- Development dependencies: `pip install -r requirements-dev.txt`
- Optional: `universal-ctags` for real ctags extraction; tests also cover ctags failure fallback.

## Quick Start

```bash
pytest tests/unit/test_ctags_loader.py -v
pytest tests/unit/test_evidence_base.py -v
pytest tests/unit/test_evidence_collectors.py -v
pytest tests/functional/test_evidence_fixtures.py -v
```

## Full Validation

```bash
ruff check .
mypy gbs_analyzer
pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
```

## Manual Collector Check

```bash
python - <<'PY'
from pathlib import Path
from gbs_analyzer.scan_and_extract import scan_buildlog
from gbs_analyzer.evidence.router import collector_for_candidate

fixture = Path("tests/fixtures/evidence_compile_no_member")
scan = scan_buildlog(fixture / "buildlog")
event = scan.as_dict()["events"][0]
collector = collector_for_candidate(
    {"event_id": event["id"], "kind": event["kind"]},
    scan,
    src_root=fixture / "src",
)
print(collector.collect({"event_id": event["id"], "kind": event["kind"]}, 900).as_dict())
PY
```

## Expected M5 Signals

- `EvidenceCollector` exposes `estimate(candidate)` and `collect(candidate, granted_budget)`.
- Router returns collectors only for compile, link, spec, and deps events.
- patch, install, and generic/raw events are not routed in M5.
- Compile and link source-context extraction records `ctags`, `regex_brace`, or `line_window`.
- ctags failure triggers deterministic fallback tests.
- Spec and deps collectors continue to work when a failing ctags runner is supplied because they do not depend on source symbol extraction.

## Acceptance Criteria

- [ ] 30+ M5 unit tests pass.
- [ ] Each M5 collector has at least 2 fixtures.
- [ ] ctags fallback is triggered by at least 1 fixture.
- [ ] Collector runtime is under 500ms.
- [ ] M5 dev_memory and performance baselines are updated.
