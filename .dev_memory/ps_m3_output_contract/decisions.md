# Decisions for PS-M3 Output Contract

| ID | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- |
| d001 | Add a short output `README.md` beside `context.md` and `meta.json`. | Frozen design §4 and user PS-M3 confirmation. | The output directory should tell the outer assistant what diagnostic was processed and which file to read first without duplicating the full context. | Patch-suggest runs now produce the full three-file output contract. |
| d002 | Use one generic patch-generation guide instead of semantic-class-specific templates. | User PS-M3 confirmation. | `semantic_class` is useful as a hint, but class-specific guidance would add maintenance and strategy complexity before real PS-M7 feedback. | Context prompts stay stable and tell Claude to treat semantic class as a hint, not proof. |
| d003 | Keep Level B guidance split by unavailable vs ambiguous source context. | User PS-M3 confirmation. | Zero-match and multi-match cases need different human/Claude actions: find the file vs choose among candidates. | `context.md` gives targeted next steps without guessing source content. |
| d004 | Keep the D13/D14 `Instructions — MUST follow` block as the final context section. | Frozen design §9ter. | The most important constraints should be the last instructions the outer assistant reads. | Existing no-apply/no-source-write guard remains prominent. |

