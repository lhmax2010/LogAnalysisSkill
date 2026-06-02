# Memory for PS-M5 Skill Metadata

## Status

Completed; ready for review.

## Scope

PS-M5 replaces the placeholder `tizen-gbs-patch-suggest/SKILL.md` with formal
Anthropic-style skill instructions:

- What/when description and compatibility
- triggers and examples
- two-phase required workflow: run the skill, then read `context.md` and generate
  patch candidates as the outer assistant
- parameter-missing behavior for `--evidence`, `--src-root`, and `--output-dir`
- output contract, relationships, and disclaimer

No Python code, resolver logic, renderer logic, workflow integration, analyzer behavior,
or existing three-skill behavior changed.

## Baseline

- Starting branch: `main`
- Starting commit: `6864a5f` (`Merge pull request #39`)
- Branch: `feature/ps-m5-skill-md`

## Validation

- Frontmatter YAML parses successfully.
- Description length is 394 characters.
- No XML angle brackets appear in `SKILL.md`.
- Full regression passed: `432 passed`, coverage `95.97%`.

