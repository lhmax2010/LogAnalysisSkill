# Known Issues for BW-M2

## Watch Points

- `docs/build_workflow/archive/DESIGN_v0.1_initial.md` is referenced by the revised design but is not
  present in the local main worktree at BW-M2 start. The initial design was read through
  `git show 42cee36:docs/build_workflow/DESIGN.md`.
- If real analyzer depsolve packets do not provide `primary_error.message` in the expected
  `nothing provides ...` format, stop and ask instead of adding ad hoc parsing.
- If generated git diffs do not apply cleanly to a real spec, stop and ask.

## Out of Scope

- No non-depsolve Suggesters.
- No E2E/Cline integration.
- No analyzer or build-skill changes.
