# PS-M6 Decisions

## d001: Patch-suggest is an optional, non-fatal workflow stage

Source: D5 requires workflow to produce context only and leave patch generation
to the outer Claude/Cline assistant.

Rationale: Patch context improves compile-error follow-up, but it must not
change workflow's established build/analyze/suggest contract. A context
generation failure should not mask the original build failure or alter the
existing exit code.

Impact: `gbs_patch_suggest` failures are recorded in `workflow_summary.md` as
non-fatal. Workflow still returns the same exit code it would have returned
without PS-M6.

## d002: Workflow calls patch-suggest by subprocess, never import

Source: Patch-suggest is an independent skill and workflow subprocess cannot
call the outer LLM.

Rationale: Subprocess invocation preserves product boundaries and mirrors the
existing analyzer call pattern. It also makes direct-folder sibling discovery
the only integration mechanism needed.

Impact: Workflow invokes `python -m gbs_patch_suggest --evidence ...` and
passes extra PYTHONPATH only when direct-folder discovery provides it. There is
no `import gbs_patch_suggest` in workflow code.

## d003: Reuse existing analyzer evidence, do not rerun analyzer

Source: Workflow already produces `.gbs_workflow/analyzer_output/evidence_packet.json`.

Rationale: Patch-suggest only needs the structured evidence packet. Reusing it
keeps M6 a pure append stage and avoids duplicated analyzer cost or divergent
packet contents.

Impact: Patch context command uses `--evidence`, not `--buildlog`.

## d004: Patch context participates in downstream token estimates

Source: Downstream token reporting tracks material workflow recommends Claude
read.

Rationale: `patch_context/context.md` is exactly the LLM-facing material the
outer assistant reads after workflow completes. Counting it makes the baseline
token estimate more useful.

Impact: Downstream token estimates include role `patch_context_md` when the
context file exists. JSON files remain excluded from the total.
