# M7 Test Guide: packet_assembler

## Environment Requirements

- Python 3.10+
- Editable install: `pip install -e .`
- Development dependencies: `pip install -r requirements-dev.txt`

## Quick Start

```bash
pytest tests/unit/test_packet_assembler.py -v
pytest tests/functional/test_full_match_fixtures.py -v
```

## Full Validation

```bash
ruff check .
mypy gbs_analyzer
pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
```

## Manual Packet Check

```bash
python - <<'PY'
from gbs_analyzer.evidence import Evidence
from gbs_analyzer.full_match import FullMatchResult, Verdict
from gbs_analyzer.packet_assembler import assemble_packet

scan = {
    "buildlog_path": "buildlog",
    "failed_phase": "%build",
    "commands": [{"id": "C001", "argv_short": "gcc -c foo.c"}],
    "events": [{"id": "E001", "kind": "compiler", "message": "error", "command_id": "C001"}],
    "degraded_reasons": [],
}
rank = {"root_cause_candidates": [{"rank": 1, "event_id": "E001", "summary": "compiler error"}]}
evidence = Evidence(
    collector="compile",
    level=2,
    granted_budget=600,
    data={"source_snippet": {"path": "/home/user/src/foo.c", "text": "error"}},
    contains={"source_snippet"},
)
match = FullMatchResult(
    verdict=Verdict.DIRECT_TIER2,
    pattern_id="demo",
    matched_tier="tier2",
    direct_answer="check source",
)
print(assemble_packet(scan, rank, evidence, match))
PY
```

## Expected M7 Signals

- BudgetPool conservation remains exactly 1400/1400.
- `assemble_packet()` returns storage JSON with raw paths preserved.
- `prompt` and `render_packet_markdown()` are redacted for LLM use.
- Missing evidence produces `evidence.fallback_context` and degraded status.
- M8 should consume `assemble_packet()` rather than rebuilding packet shape.

## Acceptance Criteria

- [ ] 20+ M7 unit tests pass.
- [ ] BudgetPool conservation is 100%.
- [ ] `packet_assembler.py` coverage is above 85%.
- [ ] Full validation passes.
- [ ] M7 dev_memory and performance baselines are updated.
