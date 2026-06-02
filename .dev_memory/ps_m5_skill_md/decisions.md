# Decisions for PS-M5 Skill Metadata

| ID | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- |
| d001 | Describe patch-suggest as a context preparer, not a patch generator. | Frozen design D2/D3 and user PS-M5 confirmation. | The skill writes `context.md`; the outer Claude generates candidate patches after reading it. | Reduces the chance Claude expects the subprocess to produce or apply patches. |
| d002 | Split Required Workflow into `Run the skill` and `After the skill finishes`. | User PS-M5 confirmation. | Patch-suggest is a two-stage workflow and needs explicit handoff instructions. | Claude can call the skill first, then read `context.md` and generate a patch itself. |
| d003 | Missing `--src-root` does not trigger a question. | PS-M2 semantics and user PS-M5 confirmation. | Source root is optional because Level B advisory is a designed fallback; Claude can read `file:line` after context generation. | Missing source root omits `--src-root` rather than blocking the user. |
| d004 | Do not expose `--buildlog` as a usable command. | PS-M4 boundary. | Buildlog convenience mode is not implemented yet. | SKILL.md stays aligned with actual argparse. |

