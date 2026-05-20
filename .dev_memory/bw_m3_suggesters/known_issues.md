# Known Issues for BW-M3

## Watch Points

- `LinkerMissingSuggester` has no Tizen repository knowledge in v0.1. Any BuildRequires patch it emits is low confidence and must explain candidate risk.
- `FallbackSuggester` is intentionally generic and should be last in the registry.
- BW-M4 must validate A/B/C/D/unknown cases end to end; BW-M3 uses unit-level routing and rendering tests.
- Suggestion filename slugs still use the generic 48-character title slug from BW-M2. This can produce
  verbose names for long dependency strings. Consider dependency-specific slugs in a future polish pass.
- Depsolve and linker-missing patches are generated with `difflib` git-style unified diffs and no
  `index` line. `git apply --check` passes; `git am` compatibility is not a v0.1 requirement.

## Out of Scope

- No analyzer/build-skill modifications.
- No E2E/Cline integration.
- No auto-apply or auto-retry behavior.
