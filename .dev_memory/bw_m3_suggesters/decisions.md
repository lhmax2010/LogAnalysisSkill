# Decisions for BW-M3: remaining Suggesters

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-20 | BW-M3 treats the B depsolve duplicate BuildRequires case as a required guard, not a workflow change. | BW-M2 review; `.dev_memory/bw_m2_workflow/known_issues.md`. | The workflow should still route depsolve by `primary_error.kind`, but the Suggester must avoid creating a useless duplicate patch. | `DepsolveSuggester` will emit advisory guidance when the dependency is already declared. |
