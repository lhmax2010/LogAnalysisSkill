# Known Issues for Hotfix Real Smoke 003

## Watch Points

- Historical `.dev_memory/*` entries still mention repo-root `patterns/`. They are not batch-edited because they are historical records.
- `templates/` remains repo-root documentation/template material; analyzer runtime does not load it.
- The system `python3 -m venv` command is unavailable on this machine because
  `python3.12-venv` / `ensurepip` is missing. Clean install validation used
  `uv venv` plus `uv pip install --python ...` instead.
- `.dev_memory/current.yaml` is a single shared status file, so parallel feature
  and hotfix branches inevitably conflict when both update milestone state. This
  was resolved manually during the PR #20 rebase onto BW-M4. Consider per-milestone
  status files in v0.6 workflow improvements if this pattern continues.

## Out of Scope

- No pattern content changes.
- No analyzer logic changes.
- No `importlib.resources` migration.
