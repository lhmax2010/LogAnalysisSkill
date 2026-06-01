# Decisions for PS-M2 Source Context

| ID | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- |
| d001 | `--src-root` is explicit only; no default auto search. | User PS-M2 confirmation and analyzer src-root audit. | Evidence-only mode has no buildlog path, so analyzer's `auto -> buildlog parent` default is not meaningful here. | Missing `--src-root` keeps file:line diagnostics at Level B advisory. |
| d002 | Use basename prefilter followed by path-segment suffix matching. | PS-M2 design D16. | Segment matching avoids false positives such as `mylibavcodec/utils.c` for `libavcodec/utils.c`; basename prefilter keeps search cheaper. | Unique real submodule paths can upgrade to Level A without broad fuzzy matching. |
| d003 | Skip `.git`, `GBS-ROOT*`, `build`, `.gbs_workflow`, `.gbs_patch_suggest`, and `node_modules`. | PS-M2 design D17. | These directories are heavy or not intended as source roots for patch context. | Search remains bounded under src-root and avoids common artifact trees. |
| d004 | Upgrade to Level A only on a unique match; zero or multiple matches stay Level B. | PS-M2 design D18. | Patch-suggest must not guess source context. | Ambiguous matches are exposed as candidates for the outer assistant/user to inspect. |
| d005 | Absolute paths are only read when they are inside src-root. | User PS-M2 edge-case confirmation. | Avoid crossing the trusted source-root boundary or reading arbitrary files from evidence. | Absolute paths outside src-root degrade to Level B. |
