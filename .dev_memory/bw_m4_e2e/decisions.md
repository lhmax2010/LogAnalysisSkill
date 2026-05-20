# Decisions for BW-M4: E2E + Cline integration

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-20 | BW-M4 owns real A/B/C/D workflow validation and unknown fallback validation. | BW-M3 review; `docs/build_workflow/DESIGN.md` §7. | BW-M3 intentionally limited validation to unit-level routing; v0.1 acceptance requires workflow-level proof. | BW-M4 dev_memory records real ffmpeg workflow results and E2E tests. |
