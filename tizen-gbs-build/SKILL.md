---
name: tizen-gbs-build
description: Runs local Tizen gbs builds and streams stdout and stderr into a build log while preserving the real exit code. Use when the user asks to build or compile a Tizen package, run "gbs build", capture a buildlog, verify whether a package builds, or produce a compiler.log without analyzing the failure.
compatibility: Requires a local environment with the gbs command, a valid gbs.conf, and access to the Tizen package source tree. Built for local AI assistants such as Claude Code or Cline.
---

# Tizen gbs Build

Use this skill when the user wants to run a local Tizen `gbs build` and capture the
resulting build log. This skill only builds; it does not analyze the log or suggest
fixes.

## Triggers

Invoke the build runner when any of these are true:

- The user asks to build, compile, or smoke-test a Tizen package.
- The user mentions `gbs build` and wants a build log or exit code.
- The user wants to verify whether the current source tree builds.
- The user explicitly asks to run the build without analyzing the result.

## Examples

### Example 1: User wants to build a package

User says: "Run a gbs build for this package and save the log."

Actions:

1. Confirm the source tree, `gbs.conf`, architecture, and output log path.
2. Run `python -m gbs_build_skill` if the package is installed, or
   `scripts/run_build.py` when using the skill folder directly.
3. Report the exit code and log path.

Result: A build log exists on disk and the original GBS exit code is preserved.

### Example 2: User only needs a buildlog

User says: "Just compile it and give me the compiler.log; do not analyze it yet."

Actions:

1. Run the build skill with `--output-log`.
2. Do not call `gbs_analyzer`.
3. Tell the user whether the build passed and where the log was written.

Result: The user receives a buildlog that can later be analyzed separately.

## Required Workflow

1. Identify the Tizen package source tree. Run the command from that tree unless the
   user gives a different working directory.
2. Identify the `gbs.conf` path, target architecture, output log path, and timeout.
3. Run the build runner through one of the stable entry points.

   If `gbs_build_skill` is installed in the current Python environment:

   ```bash
   python -m gbs_build_skill \
       --conf /path/to/gbs.conf \
       --arch armv7l \
       --include-all \
       --output-log ./out/compiler.log \
       --timeout 1800
   ```

   If using the skill folder directly without installing the Python package:

   ```bash
   python /path/to/tizen-gbs-build/scripts/run_build.py \
       --conf /path/to/gbs.conf \
       --arch armv7l \
       --include-all \
       --output-log ./out/compiler.log \
       --timeout 1800
   ```

4. Read the process exit code.
5. Report the exit code and the output log path. If the build failed, do not infer the
   root cause unless the user asks to analyze the log.

## Output Contract

The build runner writes one combined log file:

- `--output-log`: combined `gbs build` stdout and stderr, streamed while the build runs.

The runner prints a short status line to stderr with the log path. The returned exit
code is the build result contract for callers.

Exit codes:

- `0`: build succeeded.
- non-zero: `gbs build` failed; the original GBS exit code is preserved, commonly `1`.
- `124`: build timed out.
- `127`: `gbs` command was not found.

## Relationship to Other Skills

Use this skill when the task is only to compile and capture a log. If the user already
has a build log and wants root-cause analysis or a compact Evidence Packet, use
`tizen-gbs-log-analysis`. If the user wants the full loop of build, failure analysis,
and suggestion generation, use `tizen-gbs-build-workflow`.

## Disclaimer

This skill runs a local build command and records its output. It does not interpret
the build failure, modify source files, apply patches, or retry the build. Review the
log and exit code before taking follow-up action.
