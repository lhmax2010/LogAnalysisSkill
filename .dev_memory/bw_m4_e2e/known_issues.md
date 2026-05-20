# Known Issues for BW-M4

## Watch Points

- FallbackSuggester currently keeps a hard-coded `SUPPORTED_PRIMARY_KINDS` set. Future new Suggesters must update this set or replace it with dynamic registry-derived support.
- LinkerMissingSuggester remains low confidence because v0.1 has no Tizen repository knowledge.
- Cline integration is an example contract only; this repository does not deploy a live Cline environment.

## Out of Scope

- No auto-apply or auto-retry.
- No analyzer/build-skill behavior changes.
