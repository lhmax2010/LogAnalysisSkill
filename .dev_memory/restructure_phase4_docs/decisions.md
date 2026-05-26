# Decisions for Restructure Phase 4

| ID | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- |
| d001 | Remove `"."` from setuptools package discovery after all three runtime packages moved under skill `scripts/` directories. | Phase 4 user instruction and Phase 1 review note. | The repository root no longer contains runtime Python packages; keeping `"."` widens discovery unnecessarily. | Packaging now discovers `gbs_build_skill`, `gbs_analyzer`, and `gbs_workflow` only from their publish-layout script roots. |
| d002 | Update only active docs and integration entrypoints; keep `.dev_memory/`, `docs/archive/`, real-smoke design records, and historical reports unchanged. | User confirmation during Phase 4 start. | Historical records are snapshots of prior repository state. Rewriting them would weaken traceability. | Grep output may still contain old paths in historical snapshots; active user/developer surfaces are synchronized. |
| d003 | Keep Cline JSON examples in installed mode and document direct folder mode in `integrations/cline/README.md`. | User Phase 4 confirmation. | A single JSON command is easiest for Cline-style consumers; the README can show both supported runtime modes without inventing nonstandard JSON structure. | `analyze_gbs.json` and `build_workflow.json` remain simple `python -m ...` examples; direct launchers are documented beside them. |

