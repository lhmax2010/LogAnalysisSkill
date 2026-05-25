# Decisions for three_skills_restructure

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-25 | Maintain three independent local skills, each with its own `SKILL.md` under the owning package directory: build, analyzer, and workflow. | User request; local skill structure review. | The three capabilities can be triggered independently: build-only, analyze-existing-log, or full build-analyze-suggest workflow. The workflow is also a skill because it is the real user-facing entry point for Cline/Claude Code. Placing each `SKILL.md` under its package keeps the monorepo structure symmetric and makes ownership clear. | Adds `gbs_build_skill/SKILL.md` and `gbs_workflow/SKILL.md`, moves analyzer skill metadata to `gbs_analyzer/SKILL.md`, and documents relationships among the three skills without changing Python behavior. |
