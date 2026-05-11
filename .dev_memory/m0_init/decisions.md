# Decisions for M0: init

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-11 | Keep M0 to scaffolding only. | `docs/CODEX_PROMPT.md` M0 task list | Avoid starting Layer 0+1 before M0 review. | M1 code modules remain unimplemented. |
| d002 | 2026-05-11 | Use `0.5.0.dev0` for Python package metadata and `0.5.0-dev` for runtime `__version__`. | Python packaging rules and README project status | PEP 440 package versions need `.dev0`, while the project docs name the dev version as `0.5.0-dev`. | Editable install works while runtime version remains human-readable. |
| d003 | 2026-05-11 | Add a minimal smoke test so `pytest tests/` exits successfully during M0. | M0 acceptance | Pytest exits non-zero when no tests are collected. | The baseline test validates package import only. |
