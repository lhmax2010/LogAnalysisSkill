# Known Issues for Hotfix Real Smoke 003

## Watch Points

- Historical `.dev_memory/*` entries still mention repo-root `patterns/`. They are not batch-edited because they are historical records.
- `templates/` remains repo-root documentation/template material; analyzer runtime does not load it.
- The system `python3 -m venv` command is unavailable on this machine because
  `python3.12-venv` / `ensurepip` is missing. Clean install validation used
  `uv venv` plus `uv pip install --python ...` instead.
- PR #19 is still open and not merged into `main`; this hotfix branch was created
  from current `main`, so full regression is 389 tests after adding two hotfix tests,
  not the 397-test BW-M4 branch count.

## Out of Scope

- No pattern content changes.
- No analyzer logic changes.
- No `importlib.resources` migration.
