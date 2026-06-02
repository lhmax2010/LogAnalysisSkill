# Decisions for PS-M4 Buildlog Mode

| ID | Decision | Source | Rationale | Impact |
| --- | --- | --- | --- | --- |
| d001 | Use an argparse mutually exclusive required group for `--evidence` and `--buildlog`. | User PS-M4 confirmation. | Avoid ambiguous priority rules and keep existing evidence mode explicit. | Users must provide exactly one input source. |
| d002 | Run analyzer via subprocess CLI, not Python imports. | User PS-M4 confirmation and workflow precedent. | Analyzer remains an independent skill/product; subprocess mode matches workflow's tested boundary. | Patch-suggest does not couple to analyzer internals. |
| d003 | Keep analyzer subprocess helper local to patch-suggest instead of importing workflow. | User PS-M4 confirmation. | Workflow discovery/env code is product-specific; importing it would make patch-suggest depend on workflow. | Patch-suggest stays independent while preserving the proven PYTHONPATH strategy. |
| d004 | Do not expose analyzer `--max-tokens` in patch-suggest. | User PS-M4 confirmation. | Patch-suggest only needs evidence; analyzer's default 1800-token packet is enough and keeps CLI simpler. | Buildlog mode omits `--max-tokens` and uses analyzer defaults. |
| d005 | Missing `--src-root` is passed to neither analyzer nor resolver. | PS-M5 parameter semantics and user PS-M4 confirmation. | Source root is optional; analyzer can use its own auto default and patch-suggest can still degrade to Level B. | No guessing or prompting for source root in buildlog mode. |
| d006 | Store internally generated evidence under output-dir `analyzer_output/`. | User PS-M4 confirmation. | Keeping analyzer artifacts avoids temporary-directory opacity and mirrors workflow output layout. | `meta.json` records the generated evidence path and buildlog input. |

