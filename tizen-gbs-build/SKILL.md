---
name: tizen-gbs-build
description: Runs local Tizen gbs builds, streams stdout and stderr into a build log, preserves the real exit code, and locates the structured failure log when GBS reports one. Use when the user asks to build or compile a Tizen package, run "gbs build", capture a buildlog, get the failure log or structured failure log, verify whether a package builds, or produce compiler.log without analyzing the failure.
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

1. Confirm the source tree and architecture. If the user did not provide a
   `gbs.conf` path, ask: "Where is your gbs.conf file?"
2. If the user did not provide the target architecture, ask:
   "Which target architecture? (e.g. armv7l, aarch64)"
3. If the user did not specify an output log path, use `./compiler.log`.
4. Run `python -m gbs_build_skill` if the package is installed, or
   `scripts/run_build.py` when using the skill folder directly.
5. Report the exit code and log path.

Result: A build log exists on disk and the original GBS exit code is preserved.

### Example 2: User omits required build parameters

User says: "Run a gbs build for this package."

Actions:

1. Ask the user for the `gbs.conf` path before running any command; do not guess
   or invent one.
2. Ask for the target architecture if it is not provided.
3. Use `./compiler.log` as the output log path unless the user asks for a
   different path.
4. Run `python -m gbs_build_skill` if the package is installed, or
   `scripts/run_build.py` when using the skill folder directly.
5. Report the exit code and log path.

Result: The build runs only after the required `gbs.conf` path and architecture
are known, while the log path defaults to `./compiler.log`.

### Example 3: User only needs a buildlog

User says: "Just compile it and give me the compiler.log; do not analyze it yet."

Actions:

1. Ask for `gbs.conf` and target architecture if either is missing.
2. Use `./compiler.log` if the user did not specify a log path.
3. Run the build skill.
4. Do not call `gbs_analyzer`.
5. Tell the user whether the build passed and where the log was written.

Result: The user receives a buildlog that can later be analyzed separately.

### Example 4: User wants the GBS failure log path

User says: "Run the ffmpeg build and tell me which log should be analyzed if it fails."

Actions:

1. After the required `gbs.conf` path and target architecture are known, run the
   build skill from any directory with `--src-dir /path/to/ffmpeg`.
2. Read the stderr summary after the command exits.
3. If the build failed and GBS printed a structured failure log path, report that
   `analysis_log_path` points to the structured `logs/fail/{package}/log.txt` file.

Result: The user gets both the compiler log path and the recommended analysis log path.

## Required Workflow

1. Identify the Tizen package source tree. Run the command from that tree unless the
   user gives a different working directory.
2. Identify the `gbs.conf` path. If the user did not provide it, ask:
   "Where is your gbs.conf file?" Do not guess, search blindly, or invent a
   configuration path.
3. Identify the target architecture. If the user did not provide it, ask:
   "Which target architecture? (e.g. armv7l, aarch64)"
4. Identify optional `--src-dir` and timeout. If the user did not specify
   `--src-dir`, omit it and run from the current working directory.
5. If the user did not specify an output log path, use `./compiler.log` without
   asking.
6. Run the build runner through one of the stable entry points. The CLI still
   requires `--conf`, `--arch`, and `--output-log`; Claude should ask for
   `--conf` and `--arch` when missing and fill `--output-log ./compiler.log`
   when the user omitted it.

   If `gbs_build_skill` is installed in the current Python environment:

   ```bash
   python -m gbs_build_skill \
       --conf /path/to/gbs.conf \
       --arch armv7l \
       --include-all \
       --src-dir /path/to/source \
       --output-log ./out/compiler.log \
       --timeout 1800
   ```

   If using the skill folder directly without installing the Python package:

   ```bash
   python /path/to/tizen-gbs-build/scripts/run_build.py \
       --conf /path/to/gbs.conf \
       --arch armv7l \
       --include-all \
       --src-dir /path/to/source \
       --output-log ./out/compiler.log \
       --timeout 1800
   ```

7. Read the process exit code.
8. Report the exit code and the output log path. If the build failed, do not infer the
   root cause unless the user asks to analyze the log.

## Output Contract

The build runner writes one combined log file and returns path metadata:

- `--output-log`: combined `gbs build` stdout and stderr, streamed while the build runs.
- `failure_log_path`: structured GBS failure log path when the build failed and the
  `Leaving the logs in .../logs/fail/{package}/log.txt` line points to an existing file.
- `analysis_log_path`: recommended log for later analysis. Successful builds use
  `--output-log`; failed builds use `failure_log_path` when available, otherwise
  `--output-log`.
- `package_name`: package name parsed from `failure_log_path`, when available.

The runner prints a short status summary to stderr with the compiler log, failure
log when found, and recommended analysis log. The returned exit code is the build
result contract for callers.

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
