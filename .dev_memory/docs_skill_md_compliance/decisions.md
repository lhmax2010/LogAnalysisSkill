# Decisions for docs_skill_md_compliance

| ID | Date | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- | --- |
| d001 | 2026-05-25 | Update `SKILL.md` frontmatter and examples to make local skill triggering explicit. | User request; Anthropic Skill specification check. | The existing skill body already described workflow, exit codes, and disclaimers, but the frontmatter `description` only described what the skill does. Local assistants rely on description text to decide when to load a skill, so it must include both what the skill does and when to use it. | Adds trigger-oriented description text, a local-environment `compatibility` field, and concrete examples without changing runtime code or existing workflow/disclaimer sections. |
