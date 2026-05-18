---
name: tizen-gbs-log-analysis
description: Analyze Tizen gbs build logs and produce compact Evidence Packets for LLM root-cause diagnosis.
---

# Tizen gbs Log Analysis

Use this skill when the user provides or references a Tizen `gbs` build log and asks
for root-cause analysis, a minimal fix direction, or an Evidence Packet suitable for
another LLM or build-monitoring agent.

## Triggers

Invoke the analyzer when any of these are true:

- The user mentions `gbs`, Tizen packaging, RPM spec build phases, or `buildlog`.
- The input contains compiler, linker, dependency-resolution, patch, install, or RPM
  script failure output from a Tizen build.
- The user asks to compact a large build log before feeding it to an LLM.

## Required Workflow

1. Identify the build log path. If the path is unknown, ask for it.
2. Run the wrapper through the stable entry point:

   ```bash
   python -m gbs_analyzer analyze /path/to/buildlog \
       --src-root /path/to/source \
       --max-tokens 1800 \
       --output-format both \
       --output-dir .gbs_analysis
   ```

3. Read `.gbs_analysis/evidence_packet.json` for machine decisions.
4. Read `.gbs_analysis/evidence_packet.md` when preparing a human-facing explanation.
5. Read `.gbs_analysis/perf_report.json` when reporting runtime, token use, fast-path
   status, or BudgetPool conservation.
6. If the packet says `verdict: direct_answer`, return the direct answer and cite the
   matched tier.
7. If the packet says `verdict: needs_llm`, use the packet `prompt` or markdown as the
   only analysis context unless the user explicitly asks to expand.

## Expand Contract

The packet may list `expand` in `allowed_next_actions`. The `expand` subcommand is a
reserved follow-up contract for retrieving more raw context after MVP. If a user asks
for expansion before it is implemented, explain that the current MVP packet already
contains the available compact evidence and ask which raw files or log region they
want inspected manually.

## Output Contract

The wrapper writes files and keeps stdout quiet:

- `evidence_packet.json`: storage JSON with raw paths preserved.
- `evidence_packet.md`: LLM-facing markdown with workspace/user/host redaction.
- `perf_report.json`: schema `perf_report/v1` with timing, token, and decision data.
- `trace.jsonl` and `trace.log`: structured and human-readable debug traces.

Exit codes:

- `0`: analysis succeeded, including degraded packets.
- `1`: fatal analyzer error and no valid packet.
- `2`: argument error.
- `3`: build log unreadable.
- `124`: timeout convention for external callers.

## Disclaimer

This skill produces evidence and likely root-cause guidance from build logs. It does
not guarantee that a suggested package, source, or spec-file change is safe to apply.
Review generated fixes against the package history, target profile, and maintainer
policy before committing changes.
