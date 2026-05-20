# Known Issues for BW-M3

## Watch Points

- `LinkerMissingSuggester` has no Tizen repository knowledge in v0.1. Any BuildRequires patch it emits is low confidence and must explain candidate risk.
- `FallbackSuggester` is intentionally generic and should be last in the registry.
- BW-M4 must validate A/B/C/D/unknown cases end to end; BW-M3 uses unit-level routing and rendering tests.

## Out of Scope

- No analyzer/build-skill modifications.
- No E2E/Cline integration.
- No auto-apply or auto-retry behavior.
