# Dev Memory

`dev_memory` is the handoff record for each milestone. It lets another AI or human
continue from the current state without relying on chat history.

Read order for a handoff:

1. `.dev_memory/current.yaml`
2. `docs/DESIGN.md`
3. `docs/CODEX_PROMPT.md`
4. The latest milestone directory under `.dev_memory/`
5. `git log --oneline -30`
6. `pytest tests/`

Every milestone PR must include:

- `memory.md`
- `decisions.md`
- `test_report.md`
- `known_issues.md` when anything is intentionally deferred or blocked
