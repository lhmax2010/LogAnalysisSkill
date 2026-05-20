# Decisions for BW-M2: workflow + DepsolveSuggester

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-20 | BW-M2 registers only `DepsolveSuggester`. | User BW-M2 instruction; `docs/build_workflow/DESIGN.md` §6. | The revised design has seven Suggester classes overall, but six belong to BW-M3. | Registry starts small and must not silently include advisory Suggesters. |
