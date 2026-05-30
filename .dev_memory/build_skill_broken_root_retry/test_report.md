# Test Report for build skill broken-root clean retry

## Commands

| Command | Result | Notes |
| --- | --- | --- |
| `.venv/bin/pytest tests/unit/test_build_runner.py -q` | pass | `24 passed`; covers marker detection, clean retry, stdin EOF, timeout no-retry, and v0.2 failure-log extraction after retry. |
| `.venv/bin/ruff check .` | pass | Full lint check. |
| `.venv/bin/mypy tizen-gbs-build/scripts/gbs_build_skill` | pass | Strict mypy for build skill package. |
| `.venv/bin/mypy` | pass | Full project mypy; `44 source files`. |
| `.venv/bin/pytest tests/ -q --cov=gbs_analyzer --cov-fail-under=95` | pass | `417 passed`; coverage `96.01%`. |

## Focused Scenarios

- `build_command(clean=True)` appends `--clean` after existing args.
- Broken-root marker detection uses the fixed phrase `Your build system is broken`.
- Normal failed builds without the marker do not retry.
- Timeout failures do not retry, even if the marker appears before timeout.
- Broken-root failures retry once with `--clean`.
- Clean retry success returns exit `0` and records the final `--clean` command.
- Clean retry failure does not retry again and still uses v0.2 structured failure-log extraction.
- GBS subprocess stdin is `DEVNULL`, observed as EOF by a fake GBS process.

## Real Validation

No local broken scratch-root state was available to reproduce the exact GBS
prompt. The retry behavior is validated through fake GBS executables running
through the real subprocess/streaming path.
