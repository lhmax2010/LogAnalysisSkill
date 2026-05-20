# Decisions for BW-M1: gbs_build_skill

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-20 | Keep BW-M1 production code limited to `gbs_build_skill/`. | User BW-M1 instruction; `docs/build_workflow/DESIGN.md` §3. | BW-M1 should introduce only the standalone build runner and avoid coupling to analyzer/workflow concerns. | Packaging/CI integration outside this package is deferred unless explicitly authorized. |
