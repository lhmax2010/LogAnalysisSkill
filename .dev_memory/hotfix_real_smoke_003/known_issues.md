# Known Issues for Hotfix Real Smoke 003

## Watch Points

- Historical `.dev_memory/*` entries still mention repo-root `patterns/`. They are not batch-edited because they are historical records.
- `templates/` remains repo-root documentation/template material; analyzer runtime does not load it.

## Out of Scope

- No pattern content changes.
- No analyzer logic changes.
- No `importlib.resources` migration.
