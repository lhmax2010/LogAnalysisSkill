---
name: tizen-gbs-log-analysis
description: Analyzes Tizen gbs build logs and produces compact Evidence Packets for LLM root-cause diagnosis. Use when the user provides or references a Tizen gbs build log, mentions "gbs", "buildlog", or RPM spec build phases, or asks to find the root cause of a Tizen build failure (compiler, linker, dependency-resolution, patch, install, or RPM script errors), or to compact a large build log before passing it to an LLM.
compatibility: Requires a local environment with the gbs command, the gbs_analyzer Python package installed, and access to the Tizen package source tree. Built for local AI assistants such as Claude Code or Cline.
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

## Examples

### Example 1: User has a failed gbs build
User says: "My ffmpeg gbs build failed, can you find out why?"
Actions:
1. Ask for the build log path if it is not provided.
2. Run the analyzer wrapper (see Required Workflow).
3. Read `evidence_packet.json`; if `verdict` is `direct_answer`, report the root cause and cite the matched tier.
Result: Root cause identified, e.g. "linker_undef: undefined reference to `X` at `libavcodec/utils.c:109`", with a minimal fix direction.

### Example 2: User wants to compact a log for another LLM
User says: "This buildlog is huge, give me something I can paste into another model."
Actions:
1. Run the analyzer with `--max-tokens 1800`.
2. Return `evidence_packet.md` (the LLM-facing, redacted markdown).
Result: A compact, redacted Evidence Packet within the token budget.

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

## Relationship to Other Skills

Use this skill when a build log already exists and the task is to analyze or compact
that log. If the user only wants to run a Tizen `gbs build` and capture the log, use
`tizen-gbs-build`. If the user wants the full loop of build, failure analysis, and
suggestion generation, use `tizen-gbs-build-workflow`.

## Disclaimer

This skill produces evidence and likely root-cause guidance from build logs. It does
not guarantee that a suggested package, source, or spec-file change is safe to apply.
Review generated fixes against the package history, target profile, and maintainer
policy before committing changes.
