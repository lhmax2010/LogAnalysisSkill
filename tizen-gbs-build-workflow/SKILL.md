---
name: tizen-gbs-build-workflow
description: "Runs the full local Tizen GBS build workflow: build the package, analyze failures, and generate suggestion patches or advisory markdown. Use when the user asks to build and diagnose a Tizen package, run the complete gbs workflow, find the root cause after building, or produce fix suggestions after a failed gbs build."
compatibility: Requires a local environment with the gbs command, valid gbs.conf, access to the Tizen package source tree, and either installed gbs_build_skill and gbs_analyzer Python packages or sibling tizen-gbs-build and tizen-gbs-log-analysis skill folders. Built for local AI assistants such as Claude Code or Cline.
---

# Tizen gbs Build Workflow

Use this skill when the user wants an end-to-end local workflow: run a Tizen `gbs`
build, analyze the failure if the build fails, and generate suggestion files for
manual review.

This skill does not automatically apply patches or retry the build. It only writes
suggestion files. The user decides what to apply.

## Triggers

Invoke the workflow when any of these are true:

- The user asks to build a Tizen package and diagnose the failure if it fails.
- The user asks for the complete `gbs` workflow, including root-cause analysis and
  suggestions.
- The user wants generated patch or advisory files under `.gbs_workflow/`.
- The user asks for Cline or Claude Code to run the build-analysis loop locally.

## Examples

### Example 1: User wants the complete workflow

User says: "Run the GBS workflow for ffmpeg and tell me what to fix if it fails."

Actions:

1. Run `python -m gbs_workflow` if installed, or `scripts/run_workflow.py` when using
   sibling skill folders, with the source root, `gbs.conf`, architecture, and output
   directory.
2. Read `.gbs_workflow/workflow_summary.md`.
3. Report the Top-1 root cause and point the user to generated suggestions.

Result: The build was run, the failure was analyzed, and suggestions were written for
manual review.

### Example 2: User wants to inspect suggestions after failure

User says: "The workflow failed; show me what suggestions it generated."

Actions:

1. Read `.gbs_workflow/workflow_summary.md`.
2. Read each generated `suggestions/*.md`.
3. If a `.patch` file exists, tell the user it is optional and must be reviewed before
   running `git apply`.

Result: The user sees the recommended patch or advisory steps without automatic source
changes.

## Required Workflow

1. Identify the source tree, `gbs.conf`, target architecture, output directory, and
   timeout.
2. Run the workflow through one of the stable entry points.

   If `gbs_workflow`, `gbs_build_skill`, and `gbs_analyzer` are installed in the
   current Python environment:

   ```bash
   python -m gbs_workflow \
       --conf /path/to/gbs.conf \
       --arch armv7l \
       --include-all \
       --src-root /path/to/source \
       --output-dir .gbs_workflow \
       --timeout 1800
   ```

   If using the three skill folders directly without installing the Python packages,
   place `tizen-gbs-build`, `tizen-gbs-log-analysis`, and
   `tizen-gbs-build-workflow` next to each other and run:

   ```bash
   python /path/to/tizen-gbs-build-workflow/scripts/run_workflow.py \
       --conf /path/to/gbs.conf \
       --arch armv7l \
       --include-all \
       --src-root /path/to/source \
       --output-dir .gbs_workflow \
       --timeout 1800
   ```

   If the sibling folders are not next to each other, set
   `TIZEN_GBS_BUILD_SKILL_DIR` and `TIZEN_GBS_LOG_ANALYSIS_SKILL_DIR` to the build
   and analyzer skill roots.

3. Read `.gbs_workflow/workflow_summary.md`.
4. If the build succeeded, report success and stop.
5. If the build failed, read `.gbs_workflow/analyzer_output/evidence_packet.md` for the
   diagnosis and read `.gbs_workflow/suggestions/*.md` for suggested follow-up.
6. If a suggestion includes a `.patch` file, explain that it is not auto-applied and
   the user must review it before running `git apply`.

## Output Contract

The workflow writes a `.gbs_workflow/` directory:

```text
.gbs_workflow/
├── compiler.log
├── analyzer_output/
│   ├── evidence_packet.json
│   ├── evidence_packet.md
│   ├── perf_report.json
│   └── trace.jsonl
├── suggestions/
│   ├── 001_{suggester}_{id}.patch
│   ├── 001_{suggester}_{id}.md
│   └── ...
└── workflow_summary.md
```

Notes:

- `compiler.log`: combined build stdout and stderr from `gbs_build_skill`.
- `analyzer_output/`: created when the build fails and analysis runs.
- `suggestions/`: contains generated `.md` files and optional `.patch` files.
- `workflow_summary.md`: the primary file to read first.

Exit behavior:

- If the build succeeds, the workflow exits `0` and writes a success summary.
- If the build fails, the workflow usually returns the original build exit code after
  writing analyzer output and suggestions.
- Workflow-internal errors use dedicated non-zero codes; read `workflow_summary.md`
  for the exact failure.

## Relationship to Other Skills

Use this skill when the task is the full loop of build, failure analysis, and suggestion
generation. If the user only wants to run `gbs build` and capture a log, use
`tizen-gbs-build`. If the user already has a build log and only wants analysis or a
compact Evidence Packet, use `tizen-gbs-log-analysis`.

Direct folder usage requires `tizen-gbs-build` and `tizen-gbs-log-analysis` to be
installed in the same Python environment or discoverable as sibling skill folders.

## Disclaimer

This skill generates suggestions and optional patch files, but it never applies them
automatically. Review each suggestion against package history, target profile, and
maintainer policy before applying patches or editing source files.
