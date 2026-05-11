# M0 Test Guide: Project Initialization

## Environment Requirements

- Python 3.10+
- git
- Optional for future milestones: `universal-ctags`

## Quick Start

```bash
pip install -e .
pytest tests/
```

## Validation Commands

```bash
ruff check .
mypy gbs_analyzer
pytest tests/ -v --cov=gbs_analyzer --cov-report=term-missing --cov-fail-under=80
```

## Acceptance Criteria

- [ ] Editable install succeeds.
- [ ] `pytest tests/` exits 0.
- [ ] Lint and type checks pass.
- [ ] M0 dev_memory is present.
- [ ] No M1 analyzer implementation has started.

## Troubleshooting

- If `pytest tests/` reports no tests collected, confirm `tests/unit/test_package_metadata.py`
  exists.
- If editable install fails, confirm `pyproject.toml` is present at the repository root.
