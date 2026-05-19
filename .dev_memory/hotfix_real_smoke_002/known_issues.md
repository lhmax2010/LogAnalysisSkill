# Known Issues

## Out of Scope For PR1

- C patch failure still ranks as `rpm_phase`; this is Fix 4 / PR2.
- A linker undefined-reference confidence still lands around 0.84; this is Fix 5 / PR3.

## Watch Points

- If BudgetPool partial state has multiple sources beyond cumulative collector grants, stop and ask before redesigning the state machine.
- If final truncation cannot reach `max_tokens` after all safe fields are removed, record `packet_could_not_truncate_to_budget` rather than unsafe raw string truncation.
