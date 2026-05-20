# Known Issues for BW-M1: gbs_build_skill

## Watch Points

- `pyproject.toml` currently discovers only `gbs_analyzer*`. BW-M1 will not change root packaging
  unless explicitly authorized; `python -m gbs_build_skill` works from the repository root during
  this milestone.
- Real gbs validation may be environment-dependent. If `gbs` behaves differently than expected
  regarding exit codes, output encoding, or timeout behavior, stop and ask before designing a
  compatibility layer.

## Out of Scope

- No Suggester implementation.
- No analyzer invocation.
- No source patch application or build retry.
